"""Common types used in the package."""
from typing import Tuple, Union

import geojson

# Point coordinate as (lon, lat) in degrees
Point = Tuple[float, float]

# Tile as (x, y, z) integers
Tile = Tuple[int, int, int]

# Tile where (x, y) are fractional and z is integer
FTile = Tuple[float, float, int]

# Bounding box as (w, s, e, n) degree coordinates
BBox = Tuple[float, float, float, float]

# Supported geometries. This is all that @mapbox/tile-cover supports.
Geom = Union[
    geojson.Point,
    geojson.MultiPoint,
    geojson.LineString,
    geojson.MultiLineString,
    geojson.Polygon,
    geojson.MultiPolygon,
]
