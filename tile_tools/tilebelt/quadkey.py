from tile_tools.common.types import Tile


def tile_to_quadkey(tile: Tile) -> str:
    """Convert an (x, y, z) tile to a quadkey.

    Args:
        tile - Input tile

    Returns:
        Quadkey index as string
    """
    x, y, z = tile
    qk = ""
    while z > 0:
        z -= 1
        b = 0
        mask = 1 << z
        if x & mask:
            b += 1
        if y & mask:
            b += 2
        qk += str(b)
    return qk


def quadkey_to_tile(qk: str) -> Tile:
    """Convert a quadkey index to an (x, y, z) tile.

    Args:
        qk - Quadkey index as string

    Returns:
        Tile as (x, y, z) tuple.
    """
    x, y, z = 0, 0, len(qk)

    i = z
    while i > 0:
        q = int(qk[z - i])
        i -= 1
        mask = 1 << i
        match q:
            case 0:
                continue
            case 1:
                x |= mask
            case 2:
                y |= mask
            case 3:
                x |= mask
                y |= mask
            case _:
                raise ValueError(f"Invalid quadkey {qk}")
    return (x, y, z)
