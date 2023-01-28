Tilebelt
===

Python port of the JavaScript package [@mapbox/tilebelt](https://github.com/mapbox/tilebelt/).

# About

Simple utilities for working with Mapbox tiles.
The original algorithms were released by Mapbox under the MIT License in 2014.
See [the original license](https://github.com/mapbox/tilebelt/blob/master/LICENSE) for more information.

The functions have been ported to Python with some minor modifications, which I've tried to note where appropriate in the documentation.


## Contents

### Type reference

The original package is limited by vague JavaScript primitives like `Array<number>`.
For the most part, I've tried to use Python primitives as well.
The most important types are just aliases of `Tuple`.
The one exception is using `geojson` for their more sophisticated types.

| Type | Definition | Comments |
| ---- | ---------- | -------- |
| `Tile` | `Tuple[int, int, int]` | A tuple of integer `(x, y, z)` coordinates. |
| `FTile` | `Tuple[float, float, int]` | A `Tile` where `x, y` are allowed to be fractional. |
| `BBox` | `Tuple[float, float, float, float]` | A tuple of `(w, s, e, n)` degree coordinates that form a bounding box. |
| `Point` | `Tuple[float, float]` | A tuple of `(lon, lat)` degree coordinates. |


### Methods

Methods available in this package, with differences from the original `@mapbox/tilebelt` noted.

| Function | Description | Comments |
| -------- | ----------- | ----------- |
| `tile_to_geojson(tile: Tile) -> geojson.Polygon` | Convert a tile to a GeoJSON geometry | The original claims to return a `Feature`, but this appears to be a typo. Our implementation returns a `Polygon` geometry to be consistent with their implementation, and we've changed the type appropriately. |
| `tile_to_bbox(tile: Tile) -> BBox` | Convert a tile to a lon/lat Bounding Box | |
| `bbox_to_tile(bbox: BBox) -> Tile` | Get the smallest Tile covering a Bounding Box | |
| `get_children(tile: Tile, zmax: Optional[int] = 28) -> list[Tile]` | Get the four children of a tile at the next finer zoom level | Max zoom is clamped to 28 by default (use `None` to disable). |
| `get_parent(tile: Tile, zmin: Optional[int] = 0) -> Tile` | Get the tile covering this one at the next coarsest zoom level | Min zoom is clamped to 0 by default (use `None` to disable). |
| `get_siblings(tile: Tile) -> list[Tile]` | Get all adjacent tiles to this one | The current tile is not included in the list of adjacent tiles. |
| `has_siblings(tile: Tile, siblings: list[Tile]) -> bool` | Test if the given siblings are the siblings of the given tile. | Our function returns true even if the tile itself is omitted from the `siblings` list. |
| `tile_to_quadkey(tile: Tile) -> str` | Get the quadkey index for a tile |  |
| `quadkey_to_tile(qk: str) -> Tile` | Get a tile from a quadkey index | Raises a `ValueError` if the quadkey is invalid. |
| `point_to_tile(point: Point, z: int) -> Tile` | Get a tile given a lon/lat point and a zoom level | Original signature was `pointToTile(lon: number, lat: number, z: number)` |
| `point_to_tile_fraction(point: Point, z: int, precision: int = 6, clamp: bool = True) -> FTile` | Same as `point_to_tile` but returning fractional (x, y) tile coordinates. The fractional values are rounded to the given `precision`. Additionally, `clamp` can be set to `False` to prevent bounds-checking (allowing negative / overflowing tile values), which simplifies math around the meridian. | Original signature was `pointToTileFraction(lon: number, lat: number, z: number)` |
| `tile_to_point(tile: Union[FTile, Tile], precision: int = 6) -> Point` | Convert a tile (either integer or fractional) to (lon, lat) coords. | This was not explicitly implemented or exported in the original. |


### Methods **not** implemented
A couple of methods from the original package were not ported, since they have idiomatic Python equivalents:

| Function | Description | Equivalent |
| -------- | ----------- | ----------- |
| `hasTile(tiles: Iterable[Tile], tile: Tile) -> bool` | Check to see if an array of tiles contains a tile | `tile in tiles` |
| `tilesEqual(tile1: Tile, tile2: Tile) -> bool` | Check to see if two tiles are the same | `tile1 == tile2` |


## Benchmarks

The original library has benchmarks that I haven't included here.
Presumably performance characteristics are similar.
There are only some minor implementation details that I've changed.
