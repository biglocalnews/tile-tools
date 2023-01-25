# Tile Tools

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

This is a complete Python port of Mapbox's [`@mapbox/tile-cover`](https://github.com/mapbox/tile-cover/).

See [submodule readme](tile_tools/cover/README.md) for details.


#### `cover.indexes(geom: Geom, zoom: int) -> list[str]`

Same as `cover.tiles`, but returning tiles as quadkey string indexes.

#### `cover.geojson(geom: Geom, zoom: int) -> geojson.FeatureCollection`

Same as `cover.tiles`, but returning tiles as a geojson FeatureCollection.

### `coords`

#### `coords.tilecoords2lnglat`

Transform Mapbox's relative tile `(x, y)` coordinates into longitude/latitude degrees.


## Development

Set up the environment with `poetry`:

```zsh
poetry install --with dev
poetry run pre-commit install
```
