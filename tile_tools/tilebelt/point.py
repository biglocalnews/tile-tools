import math
from typing import Union

import tile_tools.settings
from tile_tools.common.types import FTile, Point, Tile

# Universal constants
pi = math.pi
_2pi = 2 * pi
# Constant to convert degrees to radians
d2r = pi / 180.0
# Constant to convert radians to degrees
r2d = 180.0 / pi


def point_to_tile_fraction(
    point: Point,
    z: int,
    precision: int = tile_tools.settings.DEFAULT_PRECISION,
    clamp: bool = True,
) -> FTile:
    """Convert lng/lat point to a fractional tile coordinate.

    Args:
        point - Point as (lon, lat) degrees
        z - Zoom level
        precision - Decimal places to round to.
        clamp - Whether to enforce bounds in the range [0, 2**z). Disabling
        this allows negative and positive overflows, which can be useful for
        doing math around the meridian.

    Returns:
        Tile as (x, y, z) where x and y are floating point numbers.
    """
    lon, lat = point
    sin = math.sin(lat * d2r)
    _2z = 2**z
    x = _2z * (lon / 360.0 + 0.5)
    y = _2z * (0.5 - 0.25 * math.log((1 + sin) / (1 - sin)) / pi)

    if clamp:
        x = x % _2z
        if x < 0:
            x += _2z

    return (round(x, precision), round(y, precision), z)


def point_to_tile(point: Point, z: int) -> Tile:
    """Find the tile that covers a given point.

    Args:
        point - Point as (lon, lat) degrees
        z - Zoom level

    Returns:
        Tile as (x, y, z) integers.
    """
    fx, fy, _ = point_to_tile_fraction(point, z)
    return (int(math.floor(fx)), int(math.floor(fy)), z)


def tile_to_point(
    tile: Union[Tile, FTile], precision: int = tile_tools.settings.DEFAULT_PRECISION
) -> Point:
    """Convert (x, y, z) tile to (lng, lat) coordinate.

    Args:
        tile - Tile as (x, y, z) tuple (either integer or fractional)
        precision - Number of decimal places to round to.

    Returns:
        Point as (lon, lat) coordinate in degrees
    """
    x, y, z = tile
    _2z = math.pow(2, z)

    lon = 360.0 * x / _2z - 180.0

    n = pi - _2pi * y / _2z
    lat = r2d * math.atan(0.5 * (math.exp(n) - math.exp(-n)))

    return (round(lon, precision), round(lat, precision))
