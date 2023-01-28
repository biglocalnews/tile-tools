"""Test the tile_tools/tilebelt module.

Tests include everything from @mapbox/tilebelt to ensure compatibility, with
only very small changes.
https://github.com/mapbox/tilebelt/blob/74fd365a9459a312382e6a7a811a7cba0cc713c3/test.js
"""
import geojson

import tile_tools.tilebelt as tilebelt

tile1 = (5, 10, 10)


def test_tile_to_geojson():
    gj = tilebelt.tile_to_geojson(tile1)
    assert gj == geojson.Polygon(
        coordinates=[
            [
                [-178.2421875, 84.73838712095339],
                [-178.2421875, 84.7060489350415],
                [-177.890625, 84.7060489350415],
                [-177.890625, 84.73838712095339],
                [-178.2421875, 84.73838712095339],
            ]
        ]
    )


def test_tile_to_bbox():
    ext = tilebelt.tile_to_bbox(tile1)
    assert ext == (-178.242188, 84.706049, -177.890625, 84.738387)


def test_get_parent():
    parent = tilebelt.get_parent(tile1)
    assert parent == (2, 5, 9)


def test_get_siblings():
    siblings = tilebelt.get_siblings(tile1)

    assert siblings == [
        (4, 10, 10),
        (5, 11, 10),
        (4, 11, 10),
    ]


def test_has_siblings():
    tiles1 = [
        (0, 0, 5),
        (0, 1, 5),
        (1, 1, 5),
        (1, 0, 5),
    ]
    tiles2 = [
        (0, 0, 5),
        (0, 1, 5),
        (1, 1, 5),
    ]

    assert tilebelt.has_siblings((0, 0, 5), tiles1)
    assert tilebelt.has_siblings((0, 1, 5), tiles1)
    assert tilebelt.has_siblings((0, 0, 5), tiles2) is False
    assert tilebelt.has_siblings((0, 1, 5), tiles2) is False


def test_has_tile():
    tiles1 = [
        (0, 0, 5),
        (0, 1, 5),
        (1, 1, 5),
        (1, 0, 5),
    ]

    assert tilebelt.has_siblings((2, 0, 5), tiles1) is False
    assert tilebelt.has_siblings((0, 1, 5), tiles1)


def test_get_quadkey():
    key = tilebelt.tile_to_quadkey((11, 3, 8))
    assert key == "00001033"


def test_quadkey_to_tile():
    key = "00001033"
    assert tilebelt.quadkey_to_tile(key) == (11, 3, 8)


def test_point_to_tile():
    tile = tilebelt.point_to_tile((0, 0), 10)
    assert tile == (512, 512, 10)


def test_point_to_tile_verified():
    tile = tilebelt.point_to_tile((-77.03239381313323, 38.91326516559442), 10)
    assert tile == (292, 391, 10)
    assert tilebelt.tile_to_quadkey(tile) == "0320100322"


def test_point_and_tile_back_and_forth():
    tile = tilebelt.point_to_tile((10, 10), 10)
    assert tile == tilebelt.quadkey_to_tile(tilebelt.tile_to_quadkey(tile))


def test_check_key_03():
    quadkey = "03"
    assert tilebelt.quadkey_to_tile(quadkey) == (1, 1, 2)


def test_bbox_to_tile_big():
    bbox = (-84.72656249999999, 11.178401873711785, -5.625, 61.60639637138628)
    tile = tilebelt.bbox_to_tile(bbox)
    assert tile == (1, 1, 2)


def test_bbox_to_tile_no_area():
    bbox = (-84, 11, -84, 11)
    tile = tilebelt.bbox_to_tile(bbox)
    assert tile == (71582788, 125964677, 28)


def test_bbox_to_tile_dc():
    bbox = (
        -77.04615354537964,
        38.899967510782346,
        -77.03664779663086,
        38.90728142481329,
    )
    tile = tilebelt.bbox_to_tile(bbox)
    assert tile == (9371, 12534, 15)


def test_bbox_to_tile_crossing_0_lat_lng():
    bbox = (-10, -10, 10, 10)
    tile = tilebelt.bbox_to_tile(bbox)
    assert tile == (0, 0, 0)


def test_tile_to_bbox_verify_bbox_order():
    tile = (13, 11, 5)
    bbox = tilebelt.tile_to_bbox(tile)
    assert bbox[0] < bbox[2], "east is less than west"
    assert bbox[1] < bbox[3], "south is less than north"

    tile = (20, 11, 5)
    bbox = tilebelt.tile_to_bbox(tile)
    assert bbox[0] < bbox[2], "east is less than west"
    assert bbox[1] < bbox[3], "south is less than north"

    tile = (143, 121, 8)
    bbox = tilebelt.tile_to_bbox(tile)
    assert bbox[0] < bbox[2], "east is less than west"
    assert bbox[1] < bbox[3], "south is less than north"

    tile = (999, 1000, 17)
    bbox = tilebelt.tile_to_bbox(tile)
    assert bbox[0] < bbox[2], "east is less than west"
    assert bbox[1] < bbox[3], "south is less than north"


def test_point_to_tile_fraction():
    tile = tilebelt.point_to_tile_fraction((-95.93965530395508, 41.26000108568697), 9)
    assert tile == (119.552490, 191.471191, 9)


def test_point_to_tile_cross_meridian():
    # X axis
    # https://github.com/mapbox/tile-cover/issues/75
    # https://github.com/mapbox/tilebelt/pull/32
    assert tilebelt.point_to_tile((-180, 0), 0) == (0, 0, 0), "[-180, 0] zoom 0"
    assert tilebelt.point_to_tile((-180, 85), 2) == (0, 0, 2), "[-180, 85] zoom 2"
    assert tilebelt.point_to_tile((180, 85), 2) == (0, 0, 2), "[+180, 85] zoom 2"
    assert tilebelt.point_to_tile((-185, 85), 2) == (3, 0, 2), "[-185, 85] zoom 2"
    assert tilebelt.point_to_tile((185, 85), 2) == (0, 0, 2), "[+185, 85] zoom 2"

    # Y axis
    # Does not wrap Tile Y
    assert tilebelt.point_to_tile((-175, -95), 2) == (0, 3, 2), "[-175, -95] zoom 2"
    assert tilebelt.point_to_tile((-175, 95), 2) == (0, 0, 2), "[-175, +95] zoom 2"
    assert tilebelt.point_to_tile((-175, 95), 2) == (0, 0, 2), "[-175, +95] zoom 2"

    # BBox
    # https://github.com/mapbox/tilebelt/issues/12
    assert tilebelt.bbox_to_tile((-0.000001, -85, 1000000, 85)) == (0, 0, 0)
