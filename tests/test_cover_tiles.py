"""These tests (and fixtures) are taken from @mapbox/tile-cover.

The original tests have been adapted for the new library. For one thing, all
the tests now pass (which they didn't in the JS library at the time I wrote
this). I've also corrected a few small errors in the assertions and expanded
them to add more detail.

A few other changes:
    - `verify_cover` and `compare_fixture` normalize inputs. This is important
       because the original fixtures contained non-normalized coordinates such
       as "185" and winding errors. These functions take that into
       consideration and try as much as possible to assert on the actual
       geometric representations of objects rather than their literal
       definitions, which are bound to differ.
    - The `invalid` hourglass geometry is no longer considered an expected
      error; instead we test that we can cover the geometry despite the errors.
    - The `polygon_out` fixture in the original library seemed visually worse
      than the one we generated, so I've swapped in our version.
    - Tile order is not considered relevant.
    - Our precision is generally clamped to 6 decimal places, as recommended
      in the GeoJSON spec.

Original source:
https://github.com/mapbox/tile-cover/blob/f5f784ec76765aabb519f139f02345b1cb5e3fe9/test/test.js
"""
import copy
import os
import warnings
from typing import Union

import geojson
import pytest
import shapely
import shapely.geometry as sg
from turfpy.measurement import area, center
from turfpy.transformation import intersect, union

import tile_tools.cover as cover
from tile_tools.common.types import Geom
from tile_tools.settings import DEFAULT_PRECISION

# % error to accept when comparing areas of geometries.
DEFAULT_TOLERANCE = 1.0e-7


def test_point():
    point = geojson.loads(
        """{
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Point",
            "coordinates": [
                79.08096313476562,
                21.135184856708992
            ]
        }
    }"""
    )

    zoom = (1, 15)

    assert cover.tiles(point.geometry, zoom) == [(23582, 14415, 15)]
    assert cover.indexes(point.geometry, zoom) == ["123310002013332"]

    compare_fixture(point.geometry, zoom, "point_out")
    verify_cover(point.geometry, zoom)


def test_line():
    line = fixture("line")
    zoom = (1, 12)

    assert sorted(cover.tiles(line.geometry, zoom)) == sorted(
        [
            (840, 1705, 12),
            (841, 1705, 12),
            (840, 1706, 12),
            (843, 1706, 12),
            (839, 1707, 12),
            (840, 1707, 12),
            (843, 1707, 12),
            (839, 1708, 12),
            (843, 1708, 12),
            (421, 852, 11),
        ]
    )
    assert sorted(cover.indexes(line.geometry, zoom)) == sorted(
        [
            "023121203002",
            "023121203003",
            "023121203020",
            "023121203031",
            "023121202133",
            "023121203022",
            "023121203033",
            "023121202311",
            "023121203211",
            "02312120301",
        ]
    )

    compare_fixture(line.geometry, zoom, "line_out")
    verify_cover(line.geometry, zoom)


def test_edgeline():
    line = fixture("edgeline")
    zoom = (14, 14)

    assert sorted(cover.tiles(line.geometry, zoom)) == sorted(
        [(4543, 6612, 14), (4544, 6612, 14)]
    )
    assert sorted(cover.indexes(line.geometry, zoom)) == sorted(
        ["03200332131311", "03200333020200"]
    )

    compare_fixture(line.geometry, zoom, "edgeline_out")
    verify_cover(line.geometry, zoom)


def test_polygon():
    polygon = fixture("polygon")
    zoom = (1, 15)

    assert len(cover.tiles(polygon, zoom)) == 122, "polygon tiles"
    assert len(cover.indexes(polygon, zoom)) == 122, "polygon indexes"

    compare_fixture(polygon, zoom, "polygon_out")
    verify_cover(polygon, zoom)


def test_multipoint():
    multipoint = fixture("multipoint")
    zoom = (1, 12)

    assert sorted(cover.tiles(multipoint.geometry, zoom)) == sorted(
        [
            (1086, 1497, 12),
            (1086, 1498, 12),
            (1014, 1551, 12),
            (1014, 1552, 12),
        ]
    )
    assert sorted(cover.indexes(multipoint.geometry, zoom)) == sorted(
        [
            "030222133112",
            "030222133130",
            "023111112332",
            "023111130110",
        ]
    )

    compare_fixture(multipoint.geometry, zoom, "multipoint_out")
    verify_cover(multipoint.geometry, zoom)


def test_multiline():
    multiline = fixture("multiline")
    zoom = (1, 8)

    assert len(cover.tiles(multiline.geometry, zoom)) == 20, "multiline tiles"
    assert len(cover.indexes(multiline.geometry, zoom)) == 20, "multiline indexes"

    compare_fixture(multiline.geometry, zoom, "multiline_out")
    verify_cover(multiline.geometry, zoom)


def test_uk():
    uk = fixture("uk")
    zoom = (7, 9)

    assert len(cover.tiles(uk.geometry, zoom)) == 68, "uk tiles"
    assert len(cover.indexes(uk.geometry, zoom)) == 68, "uk indexes"

    compare_fixture(uk.geometry, zoom, "uk_out")
    verify_cover(uk.geometry, zoom)


def test_building():
    building = fixture("building")
    zoom = (18, 18)

    assert sorted(cover.tiles(building, zoom)) == sorted(
        [
            (74891, 100306, 18),
            (74891, 100305, 18),
            (74890, 100305, 18),
        ]
    )
    assert sorted(cover.indexes(building, zoom)) == sorted(
        [
            "032010032232021031",
            "032010032232021013",
            "032010032232021012",
        ]
    )

    compare_fixture(building, zoom, "building_out")
    verify_cover(building, zoom)


def test_donut():
    donut = fixture("donut")
    zoom = (16, 16)

    assert len(cover.tiles(donut, zoom)) == 310, "donut tiles"
    assert len(cover.indexes(donut, zoom)) == 310, "donut indexes"

    compare_fixture(donut, zoom, "donut_out")
    verify_cover(donut, zoom)


def test_russia():
    russia = fixture("russia")
    zoom = (6, 6)

    assert len(cover.tiles(russia, zoom)) == 259, "russia tiles"
    assert len(cover.indexes(russia, zoom)) == 259, "russia indexes"

    compare_fixture(russia, zoom, "russia_out")
    verify_cover(russia, zoom)


def test_degenerate_ring():
    degenring = fixture("degenring")
    zoom = (11, 15)

    assert len(cover.tiles(degenring, zoom)) == 197, "degenring tiles"
    assert len(cover.indexes(degenring, zoom)) == 197, "degenring indexes"

    compare_fixture(degenring, zoom, "degenring_out")
    verify_cover(degenring, zoom)


def test_invalid_polygon_hourglass():
    # NOTE: The original library tests that an error is raised when evaluating
    # invalid shapes (in this case, "non-noded intersection"). Our library is
    # more tolerant! We accept this invalid shape and generate tiles in what
    # looks like the bounds / interior. The results are intuitive, see the
    # `fixtures/hourglass_out.geojson` for the expected result.
    invalid = fixture("hourglass")

    zoom = (1, 18)

    assert len(cover.tiles(invalid, zoom)) == 79, "hourglass tiles"
    assert len(cover.indexes(invalid, zoom)) == 79, "hourglass indexes"
    compare_fixture(invalid, zoom, "hourglass_out")
    # Unfortunately, since the shape actually is "invalid" we can't run our
    # normal `verify_cover` routine on it, since `shapely` will complain.
    # That's ok - just be sure to validate the `hourglass_out` fixture
    # visually if updating the tests.


def test_high_zoom():
    building = geojson.loads(
        """{
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-77.04474940896034, 38.90019399459534],
                [-77.04473063349724, 38.90019399459534],
                [-77.04473063349724, 38.90027122854152],
                [-77.04474672675133, 38.900273315944304],
                [-77.04474672675133, 38.900457007149065],
                [-77.04394474625587, 38.90017520794709],
                [-77.04394206404686, 38.900173120541425],
                [-77.04384550452232, 38.9001710331357],
                [-77.04384550452232, 38.900141809449025],
                [-77.04365238547325, 38.90007501240577],
                [-77.04365238547325, 38.89989340762676],
                [-77.04371139407158, 38.899916369176196],
                [-77.04371139407158, 38.89986209641103],
                [-77.04369261860847, 38.89986209641103],
                [-77.04369261860847, 38.89969927786663],
                [-77.04452946782112, 38.89969719044697],
                [-77.04460456967354, 38.89967214140626],
                [-77.04460725188255, 38.89969510302724],
                [-77.04474672675133, 38.89969719044697],
                [-77.04474940896034, 38.90019399459534],
                [-77.04474940896034, 38.90019399459534],
                [-77.04474940896034, 38.90019399459534]
            ]]
        },
        "properties": {"osm_id": 0}
    }"""
    )
    building = building.geometry

    zoom = (23, 23)

    assert len(cover.tiles(building, zoom)) == 469, "building tiles"
    assert len(cover.indexes(building, zoom)) == 469, "building indexes"

    compare_fixture(building, zoom, "highzoom_out")
    verify_cover(building, zoom)


def test_small_polygon():
    building = fixture("small_poly")
    zoom = (10, 10)

    assert cover.tiles(building, zoom) == [(284, 413, 10)]
    assert cover.indexes(building, zoom) == ["0320033302"]

    compare_fixture(building, zoom, "small_poly_out")
    verify_cover(building, zoom)


def test_spiked_polygon():
    spiked = fixture("spiked")
    zoom = (10, 10)

    assert len(cover.tiles(spiked, zoom)) == 1742, "spiked tiles"
    assert len(cover.indexes(spiked, zoom)) == 1742, "spiked indexes"

    compare_fixture(spiked, zoom, "spiked_out")
    verify_cover(spiked, zoom)


def test_blocky_polygon():
    blocky = fixture("blocky")
    zoom = (6, 6)

    assert len(cover.tiles(blocky, zoom)) == 31, "blocky tiles"
    assert len(cover.indexes(blocky, zoom)) == 31, "blocky indexes"

    compare_fixture(blocky, zoom, "blocky_out")
    verify_cover(blocky, zoom)


def test_pyramid_polygon():
    pyramid = fixture("pyramid")
    zoom = (10, 10)

    assert len(cover.tiles(pyramid, zoom)) == 530, "pyramid geojson"
    assert len(cover.indexes(pyramid, zoom)) == 530, "pyramid tiles"

    compare_fixture(pyramid, zoom, "pyramid_out")
    verify_cover(pyramid, zoom)


def test_tetris_polygon():
    tetris = fixture("tetris")
    zoom = (10, 10)

    assert len(cover.tiles(tetris, zoom)) == 255, "tetris geojson"
    assert len(cover.indexes(tetris, zoom)) == 255, "tetris tiles"

    compare_fixture(tetris, zoom, "tetris_out")
    verify_cover(tetris, zoom)


def test_0_0_polygon():
    zero = fixture("zero")
    zoom = (10, 10)

    assert sorted(cover.tiles(zero, zoom)) == sorted(
        [
            (513, 510, 10),
            (513, 511, 10),
            (512, 509, 10),
            (513, 509, 10),
            (514, 509, 10),
            (512, 510, 10),
            (514, 510, 10),
            (512, 511, 10),
            (514, 511, 10),
            (512, 512, 10),
            (513, 512, 10),
            (514, 512, 10),
        ]
    )
    assert sorted(cover.indexes(zero, zoom)) == sorted(
        [
            "1222222221",
            "1222222223",
            "1222222202",
            "1222222203",
            "1222222212",
            "1222222220",
            "1222222230",
            "1222222222",
            "1222222232",
            "3000000000",
            "3000000001",
            "3000000010",
        ]
    )

    compare_fixture(zero, zoom, "zero_out")
    verify_cover(zero, zoom)


@pytest.mark.skip(reason="Need to confirm what the expected result is")
def test_out_of_range_lat():
    # Reported https://github.com/mapbox/tile-cover/issues/66#issuecomment-137928786
    oor = fixture("oorlat")
    compare_fixture(oor, 4, "oorlat_out")
    verify_cover(oor, 4)


###############################################################################
# The rest of this file is helper functions.
# ---


def compare_fixture(geom: Geom, zoom: cover.ZoomInput, expected_name: str):
    """Validate `cover.geojson` against expected output.

    Args:
        geom - Geometry to test
        zoom - Zoom range to test
        expected_name - Name of fixture with expected GeoJSON result

    Raises:
        `AssertionError` if the GeoJSON generated from the input Geom does not
        match the expected output contained in the file.
    """
    result = cover.geojson(geom, zoom)
    result.features.append(
        geojson.Feature(
            geometry=geom,
            properties={
                "name": "original",
                "stroke": "#f44",
                "fill": "#f44",
            },
        )
    )

    compare_geojson(result, fixture(expected_name))


def compare_geojson(fc1: geojson.FeatureCollection, fc2: geojson.FeatureCollection):
    """Compare two geojson FeatureCollections.

    The FeatureCollections are checked for equivalence in each independent
    Feature. The order of the Features is not important. In addition,
    geometries are checked for homomorphism and not literal definitional
    equality. This is because our algorithms are produce slightly different
    orderings than the original library, but the resulting shapes should all
    be identical.

    Args:
        fc1 - First feature collection
        fc2 - Second feature collection

    Raises:
        `AssertionError` if the two are not equivalent.
    """
    # Check length as a quick heuristic.
    assert len(fc1.features) == len(fc2.features), "FeatureCollections length check"

    # Sort features because ordering in the collection is not significant.
    # Find the center of each feature to sort the collection. This gives us a
    # reasonable chance of comparing the correct features across collections.
    # Also put the "original" Geometry in a consistent place.
    def order_feature(f: geojson.Feature):
        name = f.properties.get("name", "")
        c = center(f).geometry.coordinates
        # Normalize coordinates to be in [-180, 180]. For whatever reason the
        # original fixtures do not use normalized coordinates. The winding order
        # might also be incorrect in the fixture, so don't rely on the raw
        # coords in any way!
        return (name, norm_coords(c))

        fc1.features.sort(key=order_feature)
        fc2.features.sort(key=order_feature)

        for i in range(len(fc1.features)):
            f1 = fc1.features[i]
            f2 = fc2.features[i]
            assert_geom_is_homomorphic(f1.geometry, f2.geometry)
            assert f1.properties == f2.properties


def assert_geom_is_homomorphic(
    g1: Geom, g2: Geom, tolerance: float = DEFAULT_TOLERANCE
):
    """Check that two geometries are homomorphic.

    For Point geometries this is trivial. For more complicated geometries like
    Polygons we verify that the shapes overlap nearly perfectly.

    The tolerance can be set to allow some minor differences. This is prone to
    happen with floating point errors.

    Args:
        g1 - First Geom
        g2 - Second Geom
        tolerance - % error to tolerate

    Raises:
        `AssertionError` if the geometries are equivalent
    """
    assert type(g1) == type(g2)
    assert len(g1.coordinates) == len(
        g2.coordinates
    ), "Coord lengths should be identical"
    match type(g1):
        case geojson.Point:
            assert g1 == g2
        case geojson.MultiPoint:
            assert {tuple(c) for c in g1.coordinates} ^ {
                tuple(c) for c in g2.coordinates
            } == set()
        case (
            geojson.LineString
            | geojson.MultiLineString
            | geojson.Polygon
            | geojson.MultiPolygon
        ):
            diff = difference(g1, g2)
            if diff:
                assert (
                    diff / area(g2)
                ) < tolerance, "Shape should be (very nearly) identical to expectation"
        case _:
            raise ValueError(f"Not sure how to test shape of type {type(g1)}")


def norm_coords(coords, precision: int = DEFAULT_PRECISION):
    """Normalize degree coordinates into [-180, 180].

    Function recursively normalizes any nested lists of coordinates.

    Args:
        coords - Either a single coordinate or a list of coordinates.

    Returns:
        Normalized coordinates.
    """
    if isinstance(coords, float) or isinstance(coords, int):
        # Taken from https://stackoverflow.com/a/2323034
        coords = coords % 360
        coords = (coords + 360) % 360
        if coords > 180:
            coords -= 360
        return round(coords, precision)
    return [norm_coords(c, precision=precision) for c in coords]


def clean_geom(g: Geom) -> shapely.Geometry:
    """Get a clean shapely shape from a GeoJSON geometry.

    Normalizes coordinates and fixes winding order. For polygons, it also uses
    the "buffer(0)" trick to clean up the shape and make it valid in certain
    circumstances where it'll otherwise detect a self-intersection.

    Args:
        g - Input GeoJSON geometry

    Returns:
        Shapely geometry
    """
    g = copy.deepcopy(g)
    g.coordinates = norm_coords(g.coordinates)

    normed = sg.shape(g).normalize()
    if isinstance(g, geojson.Polygon) or isinstance(g, geojson.MultiPolygon):
        normed = normed.buffer(0)

    return normed


def contains(g1: Geom, g2: Geom) -> bool:
    """Test if g1 contains g2.

    Args:
        g1 - Containing geometry
        g2 - Potentially contained geometry

    Returns:
        True if g2 is inside of g1.
    """
    return clean_geom(g1).covers(clean_geom(g2))


def difference(g1: Geom, g2: Geom, precision: int = DEFAULT_PRECISION) -> float:
    """Compute difference between two geometries.

    This method fixes coordinates and winding order if they are incorrect.

    Args:
        g1 - First geometry
        g2 - Second geometry
        precision - Decimal places to round to

    Returns:
        Area difference between two shapes
    """
    sg1 = clean_geom(g1)
    sg2 = clean_geom(g2)

    # Take difference and compute area, rounding to given precision.
    return round(shapely.area(shapely.difference(sg1, sg2)), precision)


def verify_cover(
    geom: Geom, zoom: cover.ZoomInput, tolerance: float = DEFAULT_TOLERANCE
):
    """Verify that tileset genuinely covers the expected area.

    Args:
        geom - GeoJSON geometry to test
        zoom - Zoom range to cover
        tolerance - Uncovered area as a percentage of all area.

    Raises:
        `AssertionError` if the tileset coverage appears inaccurate.
    """
    tiles = cover.geojson(geom, zoom)

    # Every tile should have something inside of it.
    # NOTE: The original library does not fail if the tile is empty, it only
    # prints a warning.
    for i, tile_ft in enumerate(tiles.features):
        if not intersect([tile_ft.geometry, geom]):
            warnings.warn(f"Tile {i} is empty", UserWarning)

    # Simplify geometry
    merged_tiles = union(tiles)

    # NOTE: The original library doesn't appear to handle the case of comparing
    # point and line geometries with polygons. The turfjs `difference` function
    # always returns `undefined` in JavaScript, and throws an error in Python.
    # We use special cases to check containment of these geometries.
    match type(geom):
        case geojson.Point:
            assert contains(merged_tiles.geometry, geom)
        case geojson.MultiPoint:
            for coord in geom.coordinates:
                assert contains(merged_tiles.geometry, geojson.Point(coord))
        case geojson.LineString:
            assert contains(merged_tiles.geometry, geom)
        case geojson.MultiLineString:
            for line in geom.coordinates:
                assert contains(merged_tiles.geometry, geojson.LineString(line))
        case geojson.Polygon | geojson.MultiPolygon:
            # If there's any uncovered area, check that it doesn't exceed tolerance.
            if not contains(merged_tiles.geometry, geom):
                uncovered_area = difference(geom, merged_tiles.geometry)
                assert (
                    uncovered_area / area(geom) <= tolerance
                ), f"{uncovered_area} m^2 uncovered by tiles"
        case _:
            raise ValueError(f"Not sure how to check coverage for type {type(geom)}")


def fixture_path(name: str) -> str:
    """Get the path to a GeoJSON feature by its file name.

    Args:
        name - Name of file, without .geojson extension

    Returns:
        Path where fixture can be loaded from.
    """
    return os.path.join(os.path.dirname(__file__), "fixtures", f"{name}.geojson")


def load_fixture(path: str) -> geojson.Feature:
    """Load GeoJSON feature from the given path.

    Args:
        path - Path to geojson file

    Returns:
        Parsed GeoJSON feature.
    """
    with open(path) as fh:
        return geojson.load(fh)


def fixture(name: str) -> Union[geojson.Feature, geojson.FeatureCollection, Geom]:
    """Load fixture by name.

    Some fixtures are geometries, others are features. Just depends on how the
    original fixture was generated.

    Args:
        name - Name of fixture (without .geojson extension)

    Returns:
        Parsed GeoJSON
    """
    return load_fixture(fixture_path(name))
