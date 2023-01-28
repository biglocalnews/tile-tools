import geojson
from test_cover_tiles import fixture

from tile_tools.cover.gj import geojson_tiles
from tile_tools.cover.tiles import ZoomInput


def gen_geojson(name: str, zoom: ZoomInput, output: str = "out.geojson"):
    """Generate geojson from a given fixture, save to output file.

    Args:
        name - Name of fixture
        zoom - Zoom range
        output - Destination file
    """
    r = fixture(name)
    geo = r.geometry if hasattr(r, "geometry") else r
    g = geojson_tiles(geo, zoom)
    g.features.append(
        geojson.Feature(
            geometry=geo,
            properties={
                "name": "original",
                "stroke": "#f44",
                "fill": "#f44",
            },
        ),
    )

    with open(output, "w") as fh:
        geojson.dump(g, fh, indent=2)
