from typing import Tuple

from tile_tools.common.types import BBox, Tile

from .point import point_to_tile, tile_to_point
from .traverse import MAX_ZOOM


def tile_to_bbox(tile: Tile) -> BBox:
    """Convert tile to bounding box.

    Args:
        tile - Tile as (x, y, z) tuple

    Returns:
        Bounding box as (w, s, e, n) tuple with degree coords.
    """
    x, y, z = tile

    w, n = tile_to_point((x, y, z))
    e, s = tile_to_point((x + 1, y + 1, z))

    return (w, s, e, n)


def bbox_to_tile(bbox: BBox) -> Tile:
    """Convert bounding box to a tile.

    Args:
        bbox - Bounding box as (w, s, e, n) degree coordinates

    Returns:
        Tile as (x, y, z) tuple
    """
    zmax = 32
    w, s, e, n = bbox
    tmin = point_to_tile((w, s), zmax)
    tmax = point_to_tile((e, n), zmax)
    tbox = (tmin[0], tmin[1], tmax[0], tmax[1])

    z = _get_tbox_zoom(tbox)
    if z == 0:
        return (0, 0, 0)

    # Note: javascript algorithm uses unsigned right shift explicitly, which is
    # not required in Python.
    x = tbox[0] >> (zmax - z)
    y = tbox[1] >> (zmax - z)
    return (x, y, z)


def _get_tbox_zoom(tbox: Tuple[int, int, int, int]) -> int:
    """Given a tuple of bounding tile coords, return the fitting zoom.

    Args:
        tbox - Tile coordinate box as (x0, y0, x1, y1)

    Returns:
        Integer zoom level. Might be 0.
    """
    x0, y0, x1, y1 = tbox

    z = 0
    while z < MAX_ZOOM:
        mask = 1 << (32 - (z + 1))
        if ((mask & x0) != (mask & x1)) or ((mask & y0) != (mask & y1)):
            return z
        z += 1

    return MAX_ZOOM
