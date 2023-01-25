# Tile Tools

Collection of tools useful for navigating Mapbox (and similar) tiles.

Most of these tools were written by Mapbox is JavaScript, ported with minimal modification.

## Contents

### `tilebelt`

Python port of Mapbox's [@mapbox/tilebelt](https://github.com/mapbox/tilebelt/).

This is a complete port with only minor differences and corrections.
See the [submodule readme](tile_tools/tilebelt/README.md) for more details.

### `cover`

Python port of Mapbox's [`@mapbox/tile-cover`](https://github.com/mapbox/tile-cover/)

Currently these functions operate on a fixed zoom level, and not a range, as the original JavaScript functions do.

#### `cover.tiles(geom: Geom, zoom: int) -> list[Tile]`

Given a GeoJSON Geometry and a zoom level, generate the minimal set of Mapbox `(x, y, zoom)` tiles that cover this geometry.

#### `cover.indexes(geom: Geom, zoom: int) -> list[str]`

Same as `cover.tiles`, but returning tiles as quadkey string indexes.

#### `cover.geojson(geom: Geom, zoom: int) -> geojson.FeatureCollection`

Same as `cover.tiles`, but returning tiles as a geojson FeatureCollection.

### `coords`

#### `coords.tilecoords2lnglat`

Transform Mapbox relative tile (x, y) coordinates into longitude/latitude degrees.


## Development

Set up the environment with `poetry`:

```zsh
poetry install --with dev
poetry run pre-commit install
```
