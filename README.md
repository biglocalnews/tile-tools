# Tile Tools

[![Python Tests](https://github.com/biglocalnews/tile-tools/actions/workflows/pytest.yaml/badge.svg)](https://github.com/biglocalnews/tile-tools/actions/workflows/pytest.yaml)
[![Python Lint](https://github.com/biglocalnews/tile-tools/actions/workflows/pylint.yaml/badge.svg)](https://github.com/biglocalnews/tile-tools/actions/workflows/pylint.yaml)

Collection of tools useful for navigating Mapbox (and similar) tiles.

Most of these tools were written by Mapbox in JavaScript. I've ported them into Python with minimal modification.


## Contents

### `tilebelt`

Utility functions for working with tiles.

This is a complete Python port of Mapbox's [@mapbox/tilebelt](https://github.com/mapbox/tilebelt/).

There are some minor differences in the API.
See the [submodule readme](tile_tools/tilebelt/README.md) for more details.

### `cover`

Given a GeoJSON Geometry and a zoom level, generate the minimal set of Mapbox `(x, y, zoom)` tiles that cover this geometry.

This is a re-implementation of Mapbox's [`@mapbox/tile-cover`](https://github.com/mapbox/tile-cover/).
The implementation started out as a port, however the originally library is not passing all of its own tests.
The API has been re-implemented here with a slightly different approach, and all of the equivalent tests are now passing.

See [submodule readme](tile_tools/cover/README.md) for details.

### `coords`

#### `coords.tilecoords2lnglat`

Transform Mapbox's relative tile `(x, y)` coordinates into longitude/latitude degrees.


### `distance`

#### `distance.haversine`

Compute the distance between two points on the globe using the haversine formula.

## Rendering

For debugging and general interest, the cover algorithm can be visualized with the `scripts/render.py` script.

It requires that `gdal` and `ImageMagick` are installed. Then, run:
```zsh
poetry install --with render
```

An example usage is rendering the `degenring` test fixture at zooms 1-14.
The output will be stored as a GIF in `render.gif`.

```zsh
cat tests/fixtures/degenring.geojson | poetry run python scripts/render.py --zmin 1 --zmax 13 --out render.gif
```

## Development

Set up the environment with `poetry`:

```zsh
poetry install --with dev
poetry run pre-commit install
```

### Tests

```zsh
poetry run pytest
```
