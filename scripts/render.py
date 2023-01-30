import io
import os
import shutil
import subprocess
import sys
from typing import Optional, Union

import click
import geojson
import geopandas as gpd
import matplotlib.pyplot as plt
import tqdm

from tile_tools.common.set import CapturingSet
from tile_tools.common.types import Geom, Tile
from tile_tools.cover.gj import tile_to_feature
from tile_tools.cover.tiles import tiles

# Temporary directory to store rendered output
BASE_DIR = ".render"

# Palette to use for rendering
BASE_PALETTE = {
    "shape_stroke": "#F55C47",
    "shape_fill": "#f66d58",
    "tile_stroke": "#4aa96c",
    "tile_fill": "#5bba7d",
}


def get_geom(f: Union[Geom, geojson.Feature]) -> Geom:
    """Get the geometry from a fixture.

    The fixture is either a geojson.Geometry or a geojson.Feature.

    Args:
        f - either a geojson.Geometry or a geojson.Feature

    Returns:
        geojson.Geometry
    """
    return f.geometry if hasattr(f, "geometry") else f


def get_simple_log(tileset: CapturingSet) -> list[set[Tile]]:
    """Get a simplified log from the Capturing set.

    Args:
        tileset - Tile set with captured log

    Returns:
        List of tileset change snapshots with duplicates removed.
    """
    reduced = list[set[Tile]]()

    prev: Optional[set] = None
    for snapshot in tileset.log:
        if snapshot == prev:
            continue
        prev = snapshot
        reduced.append(snapshot)

    return reduced


def gen_geojson(geo, ts: set[Tile]) -> geojson.FeatureCollection:
    """Generate a FeatureCollection with the given tileset and original geom.

    Args:
        geo - Original geometry
        ts - Tile set
        palette - Colors to use for render

    Returns:
        GeoJSON FeatureCollection
    """
    # Feature with the original outline
    fts = [geojson.Feature(geometry=geo)]

    # Tile features
    tile_fts = [tile_to_feature(t) for t in ts]

    fts += tile_fts

    return geojson.FeatureCollection(features=fts)


def render_image(geo, ts: set[Tile], dest: str, palette=BASE_PALETTE):
    """Render a tileset as an image at the given destination.

    Args:
        ts - tileset
        dest - location of output file
    """
    with io.StringIO() as stream:
        gj = gen_geojson(geo, ts)
        geojson.dump(gj, stream)
        stream.seek(0)
        pgj = gpd.read_file(stream)
        fig = pgj.plot(
            edgecolor=palette["shape_stroke"], alpha=0.5, facecolor="white"
        ).get_figure()
        fig.savefig(dest)
        plt.close(fig)


def render_gif(frames: list[str], out: str, last_pause: int = 30):
    """Render a gif from the given frames.

    Depends on ImageMagick's `convert` utility.

    Args:
        frames - List of images on disk containing frames, in order
        out - Output file path
        last_pause - Number of times to repeat last frame to add a pause
    """
    frames = frames + frames[-1:] * last_pause
    subprocess.run(["convert", *frames, out])


@click.command()
@click.option("--zmin", "-z", type=int, default=0)
@click.option("--zmax", "-Z", type=int)
@click.option("--out", "-o", type=str)
def run(*, zmin: int, zmax: int, out: str):
    """Render a visualization of the algorithm covering the given tiles.

    Args:
        zmin - Minimum zoom
        zmax - Maximum zoom
        out - Output file
    """
    if not zmin:
        zmin = zmax

    print("Parsing feature ...", file=sys.stderr)
    ft = geojson.load(sys.stdin)

    print("Generating covering tileset ...", file=sys.stderr)
    tileset = CapturingSet()
    geo = get_geom(ft)
    tiles(geo, (zmin, zmax), original_tiles=tileset)

    print("Reducing log ...", file=sys.stderr)
    log = get_simple_log(tileset)

    print("Rendering frames ...", file=sys.stderr)
    frames = list[str]()
    shutil.rmtree(BASE_DIR, ignore_errors=True)
    os.makedirs(BASE_DIR, exist_ok=True)
    for i, ts in enumerate(tqdm.tqdm(log, unit="frames")):
        name = os.path.join(BASE_DIR, f"frame{i}.png")
        render_image(geo, ts, name)
        frames.append(name)

    print("Rendering animation ...", file=sys.stderr)
    render_gif(frames, out)

    print("Cleaning up ...", file=sys.stderr)
    shutil.rmtree(BASE_DIR)

    print("Done!", file=sys.stderr)


if __name__ == "__main__":
    run()
