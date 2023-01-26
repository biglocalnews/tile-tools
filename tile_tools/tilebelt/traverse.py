from typing import Optional

from tile_tools.common.types import Tile

# Maximum zoom level used by Mapbox.
MAX_ZOOM = 28
# Minimum zoom level used by Mapbox.
MIN_ZOOM = 0


def get_children(tile: Tile, zmax: Optional[int] = MAX_ZOOM) -> list[Tile]:
    """Get the four tiles at one higher zoom level.

    Args:
        tile - Current tile as (x, y, z) tuple
        zmax - Maximum zoom level. Use `0` or `None` to disable.

    Returns:
        Four tiles at the next highest zoom level. Note that in practice, since
        zoom levels are finite, if the next highest zoom level exceeds `zmax`,
        an empty list will be returned (i.e., the tile has no children). This
        behavior can be disabled by passing `0` or `None` for `zmax`.
    """
    x0, y0, z0 = tile
    z1 = z0 + 1

    # Check zoom bounds
    if zmax and z1 > zmax:
        return []

    x1 = 2 * x0
    y1 = 2 * y0

    return [
        (x1, y1, z1),
        (x1 + 1, y1, z1),
        (x1 + 1, y1 + 1, z1),
        (x1, y1 + 1, z1),
    ]


def get_parent(tile: Tile, zmin: Optional[int] = MIN_ZOOM) -> Tile:
    """Get the tile at one coarser zoom level as the current one.

    Args:
        tile - Current tile as (x, y, z) tuple
        zmin - Minimum zoom level. Use `None` to disable.

    Returns:
        The parent tile as (x, y, z). If the new zoom would go below `zmin`,
        the null tile (0, 0, 0) is returned. Mathematically the (x, y) coords
        would go here regardless, but `z` will be not be decremented below
        the value of `zmin`. Use `None` if you'd like to arbitrarily decrement
        `z` to negative numbers in the parent.
    """
    x0, y0, z0 = tile
    z1 = z0 - 1
    if zmin is not None and z1 < zmin:
        return (0, 0, 0)

    x1 = x0 >> 1
    y1 = y0 >> 1
    return (x1, y1, z1)


def get_siblings(tile: Tile) -> list[Tile]:
    """Get all adjacent tiles to this one.

    Note the behavior differs slightly from @mapbox/tilebelt, which will return
    the current tile in the siblings list.

    Args:
        tile - Current tile as (x, y, z) tuple

    Returns:
        List of adjacent tiles
    """
    # TODO: this could be optimized. We just copied the shortcut used by the
    # original authors in @mapbox/tilebelt, and added the filter on the
    # original tile.
    all_parent_children = get_children(get_parent(tile, zmin=None), zmax=None)
    return [child for child in all_parent_children if tile != child]


def has_siblings(tile: Tile, siblings: list[Tile]) -> bool:
    """Test if a given `tile`'s siblings match given `siblings`.

    The tile itself can optionally be omitted from the siblings list and the
    test will still return True.

    Args:
        tile - Current tile as (x, y, z) tuple
        siblings - Set of three or four siblings to test

    Returns:
        True if `tile` is adjacent to every member of `siblings`.
    """
    # Optimized path for invalid inputs
    if len(siblings) < 3:
        return False

    real_sibs = set(get_siblings(tile))
    # Don't consider tile itself in this test.
    cand_sibs = {s for s in siblings if s != tile}
    # NOTE: The logic in the original implementation is a little odd. It will
    # return true as long as the real siblings are a subset of the input.
    return real_sibs.issubset(cand_sibs)
