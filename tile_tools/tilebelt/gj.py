import geojson

from tile_tools.common.types import Tile

from .bbox import tile_to_bbox


def tile_to_geojson(tile: Tile) -> geojson.Polygon:
    """Get a GeoJSON representation of a tile.

    Args:
        tile - Tile as (x, y, z) tuple

    Returns:
        GeoJSON polgyon
    """
    bbox = tile_to_bbox(tile)
    return geojson.Polygon(
        coordinates=[
            [
                [bbox[0], bbox[3]],
                [bbox[0], bbox[1]],
                [bbox[2], bbox[1]],
                [bbox[2], bbox[3]],
                [bbox[0], bbox[3]],
            ]
        ]
    )
