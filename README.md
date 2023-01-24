# Tile Tools

Collection of tools useful for navigating Mapbox (and similar) tiles.

## `cover`

Python port of Mapbox's [`@mapbox/tile-cover`](https://github.com/mapbox/tile-cover/blob/master/index.js)

This is a work in progress.
So far, only the `cover.tiles` function has been ported, and only supports a single, fixed zoom level (and not a range).

## Development

Set up the environment with `poetry`:

```zsh
poetry install --with dev
poetry run pre-commit install
```
