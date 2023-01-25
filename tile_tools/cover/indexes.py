from tile_tools.common.types import Geom
from tile_tools.tilebelt import tile_to_quadkey

from .tiles import ZoomInput, tiles


def indexes(geom: Geom, zoom: ZoomInput) -> list[str]:
    """Get a list of quadkey indexes for tiles covering a geometry.

    Args:
        geom - geojson Geometry that you wish to cover
        zoom - Zoom level(s) to cover

    Returns:
        List of quadkey indexes corresponding to tiles.
    """
    return [tile_to_quadkey(t) for t in tiles(geom, zoom)]
