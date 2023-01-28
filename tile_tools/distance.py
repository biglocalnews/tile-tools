import math

from tile_tools.common.types import Point

# Average radius of earth, in meters
R = 6_371_000


def haversine(p0: Point, p1: Point, r: int = R) -> float:
    """Smallest distance between two points on the globe.

    Args:
        p0 - (lon, lat) in degrees
        p1 - (lon, lat) in degrees
        r - Radius of earth in meters

    Returns:
        Approximate distance on the earth in meters.
    """
    lon0 = math.radians(p0[0])
    lon1 = math.radians(p1[0])
    lat0 = math.radians(p0[1])
    lat1 = math.radians(p1[1])

    a = math.sin((lat1 - lat0) / 2) ** 2
    a += math.cos(lat1) * math.cos(lat0) * (math.sin((lon1 - lon0) / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c
