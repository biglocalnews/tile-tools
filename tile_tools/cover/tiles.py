import math
from dataclasses import dataclass
from typing import Tuple, Union

import geojson

from tile_tools.common.types import Geom, Point, Tile
from tile_tools.tilebelt.point import point_to_tile, point_to_tile_fraction
from tile_tools.tilebelt.traverse import get_parent, get_siblings

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
# the original tuples in a set.
TileSet = set[Tile]


@dataclass
class Edge:
    """Represent edge information for parity polygon fill algorithm."""

    y_min: int
    x: float
    y_max: int
    im: float


def tiles(geom: Geom, zoom: ZoomInput) -> list[Tile]:
    """Get minimal set of tiles covering a geometry at given zoom level(s).

    If a range of zoom levels is given, the minimal covering set will begin at
    the finest zoom level and simplify using coarser tiles wherever possible.

    Args:
        geom - geojson Geometry to cover
        zoom - Zoom level (or range) to compute tiles for

    Returns:
        List of (x, y, z) tiles
    """
    tiles = TileSet()

    min_zoom, max_zoom = _parse_zoom(zoom)

    match type(geom):
        case geojson.Point:
            lng, lat = geom.coordinates
            tiles |= point_cover((lng, lat), max_zoom)
        case geojson.MultiPoint:
            for point in geom.coordinates:
                tiles |= point_cover((point[0], point[1]), max_zoom)
        case geojson.LineString:
            tiles |= line_cover(geom.coordinates, max_zoom)
        case geojson.MultiLineString:
            for line in geom.coordinates:
                tiles |= line_cover(line, max_zoom)
        case geojson.Polygon:
            tiles |= polygon_cover(geom.coordinates, max_zoom)
        case geojson.MultiPolygon:
            for poly in geom.coordinates:
                tiles |= polygon_cover(poly, max_zoom)
        case _:
            raise NotImplementedError(f"Unsupported geometry type {type(geom)}")

    # Interpolate coverage within the zoom range if requested.
    if min_zoom != max_zoom:
        tiles = _simplify_tileset(tiles, (min_zoom, max_zoom))

    return [_norm_tile(t) for t in tiles]


def _norm_tile(t: Tile) -> Tile:
    """Clamp (x, y) bounds of tile to bounds defined by z.

    Args:
        t - Tile to normalize

    Returns:
        Normalized tile
    """
    x, y, z = t
    tmax = 1 << z

    if x < 0:
        x += tmax
    if y < 0:
        y += tmax

    return (x % tmax, y % tmax, z)


def _simplify_tileset(tiles: TileSet, zoom: ZoomRange) -> TileSet:
    """Reduce a tileset size by replacing coarser covering tiles if possible.

    Args:
        tiles - A set of tiles at the maximum zoom range
        zoom - Tuple of (min_zoom, max_zoom)

    Returns:
        The simplified tiles list.
    """
    final_tiles = set[Tile]()

    min_zoom, max_zoom = zoom
    z = max_zoom
    # Widen the zoom range and replace children with parents if the parents
    # cover all of the children.
    while z > min_zoom:
        parent_tiles = set[Tile]()
        for t in list(tiles):
            if t[0] % 2 == 0 and t[1] % 2 == 0:
                sibs = set(get_siblings(t))
                # If t and all its siblings are contained in the tile set,
                # then delete them and replace them with the parent tile.
                if sibs.issubset(tiles):
                    tiles.difference_update(sibs)
                    tiles.remove(t)

                    parent = get_parent(t)
                    if (z - 1) == min_zoom:
                        final_tiles.add(parent)
                    else:
                        parent_tiles.add(parent)

        final_tiles |= tiles
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


def point_cover(point: Point, z: int) -> TileSet:
    """Get a set containing the tile that covers the given point.

    Args:
        point - Coordinate as (lon, lat) degrees
        z - Zoom level

    Returns:
        Set containing the tile containing the point.
    """
    return {point_to_tile(point, z)}


def _scan_edges(scanline: int, all_edges: list[Edge], active_edges: list[Edge]):
    """Activate edges at the current scanline.

    Mutates both `all_edges` and `active_edges`. Expects `all_edges` to be
    sorted by `y_min`.

    Args:
        scanline - Current scanline
        all_edges - List of all available edges
        active_edges - List of activated edges
    """
    # Find the index where the current scanline stops. The all_edges list is
    # sorted by y_min so this should be quick.
    i = 0
    while i < len(all_edges):
        if all_edges[i].y_min > scanline:
            break
        i += 1

    # Update slices in place
    active_edges += all_edges[:i]
    all_edges[:] = all_edges[i:]


def polygon_cover(coords: PolygonCoords, zoom: int) -> TileSet:
    """Get all the tiles covering a polygon.

    Adapted from https://www.cs.rit.edu/~icss571/filling/how_to.html

    Args:
        coords - Polygon coordinates, as a list of lines (which are a list of
        lng/lat coordinates).
        zoom - Current zoom level

    Returns:
        Set of tiles that cover the polygon.
    """
    tiles = set[Tile]()
    all_edges = list[Edge]()
    for line in coords:
        # Add line cover to ensure full coverage around the perimeter.
        tiles |= line_cover(line, zoom)

        # Compute edge data for polygon fill
        n = len(line)
        for i in range(n - 1):
            p0 = line[i]
            x0, y0, _ = point_to_tile_fraction((p0[0], p0[1]), zoom, clamp=False)
            p1 = line[(i + 1) % n]
            x1, y1, _ = point_to_tile_fraction((p1[0], p1[1]), zoom, clamp=False)

            # Don't add edges where slope is 0
            if int(y0) == int(y1):
                continue

            # Calculate inverse slope of edge
            im = round((x1 - x0) / (y1 - y0), 6)

            # Choose minimum y
            if y0 < y1:
                all_edges.append(Edge(y_min=int(y0), x=x0, y_max=int(y1), im=im))
            else:
                all_edges.append(Edge(y_min=int(y1), x=x1, y_max=int(y0), im=im))

    # Sort on the edges now sorts by (min-y, min-x).
    all_edges.sort(key=lambda e: (e.y_min, e.x))

    if not all_edges:
        return tiles

    # Initialize scanline as minimum y value.
    active_edges = list[Edge]()
    scanline = all_edges[0].y_min
    _scan_edges(scanline, all_edges, active_edges)

    while active_edges:
        parity = False
        # Draw all active edges with odd parity
        for i in range(len(active_edges) - 1):
            parity = not parity
            if parity:
                x0 = active_edges[i].x
                x1 = active_edges[i + 1].x
                for x in range(int(x0), int(x1) + 1):
                    tiles.add((x, scanline, zoom))
        # Increment scanline
        scanline += 1
        # Remove edges where y-max is at the new scanline
        active_edges[:] = [edge for edge in active_edges if edge.y_max != scanline]
        # Increment x values
        for edge in active_edges:
            edge.x += edge.im
        # Transfer edges along the new scanline into the active edges list.
        _scan_edges(scanline, all_edges, active_edges)
        # Re-sort the active edges
        active_edges.sort(key=lambda e: e.x)

    assert not all_edges and not active_edges, "All edges should have been consumed"

    return tiles


def line_cover(line: LineCoords, zoom: int, ring: bool = False) -> TileSet:
    """Generate complete minimal set of tiles covering a line.

    Args:
        line - Line coordinates
        zoom - Zoom level
        ring - Treat the line as a closed linear ring

    Returns:
        Set of covering tiles as (x, y, z) tuples.
    """
    tiles = set[Tile]()

    # If this is a ring, need to interpolate between the last coord and the
    # first coord. If it's a normal line, reduplicate the endpoint so the
    # algorithm finishes in the right spot.
    if not ring:
        line = line + [line[-1]]

    n = len(line)
    r = range(n if ring else n - 1)

    for i in r:
        # NOTE: when computing tiles, we disable bounds checking. This means
        # that the x-tile bounds may be negative or greater than 2**zoom.
        # We'll have to normalize those later, but in the meantime it makes it
        # so we don't have to deal with the meridian crossing nightmare.
        p0 = line[i]
        x0, y0, _ = point_to_tile_fraction((p0[0], p0[1]), zoom, clamp=False)

        # The tile that contains the original point must be added.
        xa, ya = int(x0), int(y0)
        tiles.add((xa, ya, zoom))

        # Get the adjacent point.
        p1 = line[(i + 1) % n]
        x1, y1, _ = point_to_tile_fraction((p1[0], p1[1]), zoom, clamp=False)
        xb, yb = int(x1), int(y1)

        # If the points are in the same or adjacent tiles, we can move on.
        dx = xb - xa
        dy = yb - ya
        if (abs(dx) <= 1 and abs(dy) == 0) or (abs(dx) == 0 and abs(dy) <= 1):
            continue

        # Otherwise we need to interpolate somehow.
        x_delta = -1 if dx < 0 else 1
        y_delta = -1 if dy < 0 else 1

        # If the interpolation is purely horizontal or vertical then we can
        # handle it very quickly.
        if xa == xb:
            tiles |= {(xa, y, zoom) for y in range(ya, yb, y_delta)}
            continue

        if ya == yb:
            tiles |= {(x, ya, zoom) for x in range(xa, xb, x_delta)}
            continue

        # If the interpolation involves a diagonal, we need to do a Manhattan-
        # style walk up from p0 to p1. To do this, we'll iteratively compute
        # the next y-intercept and x-intercept along tile boundaries. Whichever
        # point is closer tells us which tile we need to load. Then, we jump
        # to that closest intercept and test again, until we've reached the
        # destination tile.
        #
        # This is basically the DDA algorithm used in raycasting. It should
        # accomplish the same thing, but I figured it out before I read about
        # DDA. The big difference is that we know where the "collision" will
        # occur and we never actually care about the length.
        slope = (y1 - y0) / (x1 - x0)
        xti, yti = xa, ya
        xi, yi = x0, y0

        # Check points at the left and top of the tile. If the initial point
        # starts here, thne offset the initial starting position very slightly
        # so that the intercept math still works out.
        if xi == xti and x_delta < 0:
            xi += 1e-5
        if yi == yti and y_delta < 0:
            yi += 1e-5

        while xti != xb or yti != yb:
            # 1) Find where the line will intersect the next longitude bound.
            next_x_bound = round(xi + x_delta, 6)
            if x_delta > 0:
                next_x_bound = math.floor(next_x_bound)
            else:
                next_x_bound = math.ceil(next_x_bound)
            # The y-coord is given by y = mx.
            yd = math.copysign(slope * (next_x_bound - xi), y_delta)

            # 2) Find where the line will intersect the next latitude bound.
            next_y_bound = round(yi + y_delta, 6)
            if y_delta > 0:
                next_y_bound = math.floor(next_y_bound)
            else:
                next_y_bound = math.ceil(next_y_bound)
            # The x-coord is given by x = y / m.
            xd = math.copysign((next_y_bound - yi) / slope, x_delta)

            # If the longitudinal intercept is closer than the latitudinal one,
            # then we're traveling vertically.
            if abs(xd) <= abs(next_x_bound - xi):
                if yti != yb:
                    yti += y_delta
                yi = next_y_bound
                xi = round(xd + xi, 6)
                tiles.add((xti, yti, zoom))

                # If x happens to land on an endpoint and we're headed left,
                # then load the adjacent horizontal tile as well.
                if xi == xti and x_delta < 0 and xti != xb:
                    xti += x_delta
                    tiles.add((xti, yti, zoom))
            else:
                if xti != xb:
                    xti += x_delta
                xi = next_x_bound
                yi = round(yd + yi, 6)
                tiles.add((xti, yti, zoom))

                # If y happens to land on an endpoint and we're headed up,
                # then load the adjacent vertical tile as well.
                if yi == yti and y_delta < 0 and yti != yb:
                    yti += y_delta
                    tiles.add((xti, yti, zoom))

    return tiles
