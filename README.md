# Tile Tools

Collection of tools useful for navigating Mapbox (and similar) tiles.


## Contents

### `cover`

Python port of Mapbox's [`@mapbox/tile-cover`](https://github.com/mapbox/tile-cover/blob/master/index.js)

The port is not yet complete.
Currently only the `cover.tiles` function has been ported, and only supports a single, fixed zoom level (not a range).

#### `cover.tiles`

Given a GeoJSON Geometry and a zoom level, generate the minimal set of Mapbox `(x, y, zoom)` tiles that cover this geometry.

### `coords`

#### `coords.tilecoords2lnglat`

Transform Mapbox relative tile (x, y) coordinates into longitude/latitude degrees.


## Development

Set up the environment with `poetry`:

```zsh
poetry install --with dev
poetry run pre-commit install
```
