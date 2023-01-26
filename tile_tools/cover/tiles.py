import math
from typing import Optional, Tuple, Union

import geojson

from tile_tools.common.types import Geom, Point, Tile
from tile_tools.tilebelt.point import point_to_tile, point_to_tile_fraction

# Tuple of (min_zoom, max_zoom). Max zoom should be greater than min zoom.
ZoomRange = Tuple[int, int]

# Zoom input parameter, which can either be fixed or a (min, max) range.
ZoomInput = Union[int, ZoomRange]

# List of (x, y) tile coords
Ring = list[Tuple[int, int]]

# Line coordinates
LineCoords = list[Union[Point, list[float]]]

# Polygon coordinates
PolygonCoords = list[LineCoords]

# Set containing tiles. The original algorithm uses a set of reversible hashes
# of tiles. In Python it's easier and probably as fast (or faster) to just keep
# the original tuples in a set. The name `TileHash` has been kept from the
# original algorithm for easier reference.
TileHash = set[Tile]


def tiles(geom: Geom, zoom: ZoomInput) -> list[Tile]:
    """Get minimal set of tiles covering a geometry at given zoom level(s).

    Args:
        geom - geojson Geometry to cover
        zoom - Zoom level (or range) to compute tiles for

    Returns:
        List of (x, y, z) tiles
    """
    tiles = list[Tile]()
    tile_hash = TileHash()

    min_zoom, max_zoom = _parse_zoom(zoom)

    match type(geom):
        case geojson.Point:
            lng, lat = geom.coordinates
            tile_hash = cover_point((lng, lat), max_zoom)
        case geojson.MultiPoint:
            for point in geom.coordinates:
                phash = cover_point((point[0], point[1]), max_zoom)
                tile_hash |= phash
        case geojson.LineString:
            tile_hash, _ = line_cover(geom.coordinates, max_zoom)
        case geojson.MultiLineString:
            for line in geom.coordinates:
                lhash, _ = line_cover(line, max_zoom)
                tile_hash |= lhash
        case geojson.Polygon:
            tile_hash, tiles = polygon_cover(geom.coordinates, max_zoom)
        case geojson.MultiPolygon:
            for poly in geom.coordinates:
                phash, ptiles = polygon_cover(poly, max_zoom)
                tile_hash |= phash
                tiles += ptiles
        case _:
            raise NotImplementedError(f"Unsupported geometry type {type(geom)}")

    # Sync hash tiles into the tile list.
    tiles = _merge_tile_data(tile_hash, tiles)

    # Interpolate coverage within the zoom range if requested.
    if min_zoom != max_zoom:
        tiles = _extrapolate_zoom_range(tiles, (min_zoom, max_zoom))

    return tiles


def _extrapolate_zoom_range(tiles: list[Tile], zoom: ZoomRange) -> list[Tile]:
    """Extrapolate a set of tiles from max zoom to min zoom.

    Args:
        tiles - A list of tiles at the maximum zoom range
        zoom - Tuple of (min_zoom, max_zoom)

    Returns:
        List of input tiles plus their corresponding tiles extrapolated across
        the entire zoom range.
    """
    # NOTE: the JavaScript library tries to optimize by passing in the original
    # tile hash as an argument. In practice it doesn't make a difference here
    # because the tile hash needs to be extended to cover the entire tile list
    # anyway. So creating the set here should have similar performance.
    tile_hash = set(tiles)
    final_tiles = list[Tile]()

    min_zoom, max_zoom = zoom
    z = max_zoom
    while z > min_zoom:
        parent_tile_hash = set[Tile]()
        parent_tiles = list[Tile]()
        for t in tiles:
            if t[0] % 2 == 0 and t[1] % 2 == 0:
                t2 = (t[0] + 1, t[1], z)
                t3 = (t[0], t[1] + 1, z)
                t4 = (t[0] + 1, t[1] + 1, z)

                if t2 in tile_hash and t3 in tile_hash and t4 in tile_hash:
                    tile_hash.remove(t)
                    tile_hash.remove(t2)
                    tile_hash.remove(t3)
                    tile_hash.remove(t4)

                    parent = (t[0] >> 1, t[1] >> 1, z - 1)
                    if z - 1 == min_zoom:
                        final_tiles.append(parent)
                    else:
                        parent_tiles.append(parent)
                        parent_tile_hash.add(parent)

        for t in tiles:
            if t in tile_hash:
                final_tiles.append(t)

        tile_hash = parent_tile_hash
        tiles = parent_tiles
        z -= 1

    return final_tiles


def _parse_zoom(z: ZoomInput) -> ZoomRange:
    """Normalize zoom input.

    Args:
        z - Either a fixed zoom integer or a range as a tuple.

    Returns:
        Tuple of (zmin, zmax) integers where zmin <= zmax.

    Raises:
        ValueError if a tuple is past where zmax < zmin
        TypeError if neither an int or a tuple is passed
    """
    match z:
        case int():
            return (z, z)
        case tuple():
            zmin, zmax = z
            if zmin > zmax:
                raise ValueError(
                    f"Min zoom {zmin} can't be greater than max zoom {zmax}"
                )
            return (zmin, zmax)
        case _:
            raise TypeError(f"Not sure how to interpret zoom of type {type(z)}")


def _merge_tile_data(tile_hash: TileHash, tile_array: list[Tile]) -> list[Tile]:
    """Merge the tile set and tile list.

    Args:
        tile_hash - Set of tiles
        tile_array - List of (x, y, z) tiles.

    Returns:
        Merged list of tiles
    """
    return tile_array + list(tile_hash)


def cover_point(point: Point, z: int) -> TileHash:
    """Get a set containing the tile that covers the given point.

    Args:
        point - Coordinate as (lon, lat) degrees
        z - Zoom level

    Returns:
        The covered tile. The tile is returned in a set, for
        consistency with other methods.
    """
    tile = point_to_tile(point, z)
    return {tile}


def polygon_cover(coords: PolygonCoords, zoom: int) -> Tuple[TileHash, list[Tile]]:
    """Get all the tiles covering a polygon.

    Args:
        coords - Polygon coordinates, as a list of lines (which are a list of
        lng/lat coordinates).
        zoom - Current zoom level

    Returns:
        A tuple with a set of tiles and a list of covered tiles. The tile set
        and the tile list should be merged eventually, but are kept distinct
        for performance reasons here.
    """
    tile_hash = TileHash()
    intersections = list[Tuple[int, int]]()
    tile_array = list[Tile]()

    for line in coords:
        line_hash, ring = line_cover(line, zoom)
        tile_hash |= line_hash

        for m in range(len(ring)):
            k = m - 2
            j = m - 1

            ky = ring[k][1]
            y = ring[j][1]
            my = ring[m][1]
            # Check that y is not a local min, not a local max, and is not a
            # duplicate. If all that is true, it is an intersection.
            if (y > ky or y > my) and (y < ky or y < my) and y != my:
                intersections.append(ring[j])

    # Sort the (x,y) tuples by (y,x)
    intersections.sort(key=lambda t: (t[1], t[0]))

    for i in range(0, len(intersections), 2):
        y = intersections[i][1]
        x = intersections[i][0] + 1
        while x < intersections[i + 1][0]:
            if (x, y, zoom) not in tile_hash:
                tile_array.append((x, y, zoom))
            x += 1

    return tile_hash, tile_array


def line_cover(line: LineCoords, zoom: int) -> Tuple[TileHash, Ring]:
    """Get a list of tiles covering a line.

    Args:
        line - List of [lng,lat] coordinates.
        zoom - Current zoom level

    Returns:
        Tuple with set of covered tiles and the coordinates ring as a list. The
        ring can be used for computing polygon cover.
    """
    tile_hash = TileHash()
    ring = Ring()
    prev_x: Optional[int] = None
    prev_y: Optional[int] = None

    for i in range(len(line) - 1):
        # NOTE: we assume line coords are well-formed. It's unfortunately
        # common for line coords to have too few or too many coordinates, in
        # which case we might get an opaque error here.
        x0, y0, _ = point_to_tile_fraction((line[i][0], line[i][1]), zoom)
        x1, y1, _ = point_to_tile_fraction((line[i + 1][0], line[i + 1][1]), zoom)
        dx = x1 - x0
        dy = y1 - y0

        if dx == 0 and dy == 0:
            continue

        sx = 1 if dx > 0 else -1
        sy = 1 if dy > 0 else -1
        x = int(math.floor(x0))
        y = int(math.floor(y0))

        tmax_x = math.inf if not dx else abs(((1 if dx > 0 else 0) + x - x0) / dx)
        tmax_y = math.inf if not dy else abs(((1 if dy > 0 else 0) + y - y0) / dy)
        # Note JavaScript automatically treats 0-div as infinity, while Python
        # raises an Exception. Presumably the original authors intended inf.
        tdx = abs(sx / dx) if dx != 0 else math.inf
        tdy = abs(sy / dy) if dy != 0 else math.inf

        if x != prev_x or y != prev_y:
            tile_hash.add((x, y, zoom))
            ring.append((x, y))
            prev_x = x
            prev_y = y

        while tmax_x < 1 or tmax_y < 1:
            if tmax_x < tmax_y:
                tmax_x += tdx
                x += sx
            else:
                tmax_y += tdy
                y += sy

            tile_hash.add((x, y, zoom))
            if y != prev_y:
                ring.append((x, y))
            prev_x = x
            prev_y = y

    if ring and y == ring[0][1]:
        ring.pop()

    return tile_hash, ring
