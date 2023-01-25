import geojson

from tile_tools.common.types import Geom, Tile
from tile_tools.tilebelt import tile_to_geojson

from .tiles import ZoomInput, tiles


def geojson_tiles(geom: Geom, zoom: ZoomInput) -> geojson.FeatureCollection:
    """Get a FeatureCollection of tile features that cover the geometry.

    Args:
        geom - Geometry to cover
        zoom - Zoom level(s) to cover

    Returns:
        FeatureCollection with all covering tiles as Features.
    """
    fts = [tile_to_feature(t) for t in tiles(geom, zoom)]
    return geojson.FeatureCollection(features=fts)


def tile_to_feature(tile: Tile) -> geojson.Feature:
    """Convert a tile to a GeoJSON feature.

    Args:
        tile - Tile as (x, y, z) tuple

    Returns:
        GeoJSON feature with the tile's geometry and no properties.
    """
    return geojson.Feature(geometry=tile_to_geojson(tile))
