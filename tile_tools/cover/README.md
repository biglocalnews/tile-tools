Cover
===

Python port of the JavaScript package [@mapbox/tile-cover](https://github.com/mapbox/tile-cover/).

# About

Algorithms for generating minimal tilesets given GeoJSON geometries.

The JavaScript version of this library was developed by Mapbox and released under the MIT license. See [the original license](https://github.com/mapbox/tile-cover/blob/master/LICENSE) for more information.

The algorithms have been adapted to Python largely as-is, with some minor implementation and API modifications.

## Contents

### Type reference

This module depends on [`geojson`](https://pypi.org/project/geojson/).
We support the same input geometries as the original Mapbox library.

| Type | Definition |
| ---- | ---------- |
| `Geom` | Any of the supported GeoJSON geometries we can cover: `Point, MultiPoint, LineString, MultiLineString, Polygon, MultiPolygon` |
| `Tile` | Tile as `(x, y, z)` tuple with integer coordinates | |
| `ZoomRange` | Either a fixed integer zoom level or a tuple of `(min_zoom, max_zoom)` |


### Methods

All of the methods take a `geojson.Geometry` and a `ZoomRange` and return the minimal set of tiles covering the geometry.
The only differences are in the return type.

The `ZoomRange` can either be a fixed level as an integer, or a tuple of `(min_zoom, max_zoom)`.
An error will be raised if `max_zoom < min_zoom`.

| Function | Description |
| -------- | ----------- |
| `tiles(geom: Geom, zoom: ZoomRange) -> list[Tile]` | Generate the minimal set of tiles covering the given Geometry at the given zoom level(s). |
| `indexes(geom: Geom, zoom: ZoomRange) -> list[str]` | Same as `tiles` but returning tiles as QuadKey indexes. |
| `geojson(geom: Geom, zoom: ZoomRange) -> geojson.FeatureCollection` | Same as `tiles` but returning tiles as a `FeatureCollection` |


## Benchmarks

The original library in JavaScript has benchmarks.
I haven't benchmarked this library, but it likely has similar performance characteristics, though in adapting the algorithms to Python I have used slightly different data structures.
