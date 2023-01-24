import mercantile


def tilecoords2lnglat(
    tile: mercantile.Tile, x: int, y: int, extent: int = 4096
) -> mercantile.LngLat:
    """Convert relative tile coordinates to lng/lat degrees.

    Mapbox tile geometries are encoded as integers relative to the boundaries
    of the tile. These are not interprettable outside of the tile. This
    function transforms those coordinates into lng/lat degrees.

    See also:
    https://github.com/tilezen/mapbox-vector-tile#coordinate-transformations-for-encoding

    Args:
        tile - mercantile Tile containing coordinates
        x - horizontal integer pixel offset within tile
        y - vertical integer pixel offset within tile
        extent - pixel space represented by tile (usually 4096)

    Returns:
        mercantile.LngLat object containing degree coordinates
    """
    # Get web mercator bounds of tile
    bounds = mercantile.xy_bounds(tile)
    # Convert pixel offsets to web mercator coordinates
    # The lower left of the tile is (0, 0) and the upper right is (4096, 4096).
    mx = bounds.left + x / float(extent) * (bounds.right - bounds.left)
    my = bounds.bottom + y / float(extent) * (bounds.top - bounds.bottom)
    # Convert spherical mercator to lng/lat.
    return mercantile.lnglat(mx, my)
