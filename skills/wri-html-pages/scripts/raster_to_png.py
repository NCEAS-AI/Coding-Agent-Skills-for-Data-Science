#!/usr/bin/env python3
"""Turn a GeoTIFF band into a coloured, transparent PNG that lines up exactly on a web map.

WHY THIS EXISTS
    Web maps draw an image between four longitude/latitude corners, stretched in Web Mercator. A
    raster in any other projection drifts by tens of metres at fire scale, so this reprojects to
    EPSG:3857 first, colours the band (a ramp for values, a lookup for classes), makes no-data
    transparent, caps the pixel size, and prints the bounds to paste into the map spec.

USAGE (pipeline venv: rasterio + numpy + Pillow)
    raster_to_png.py IN.tif OUT.png --ramp heat --vmin 0 --vmax 1
    raster_to_png.py IN.tif OUT.png --classes "1=#E8432A,2=#F2B33D,3=#BDEBCB"
    options: --band 1  --max-size 4096  --nodata VALUE  --opacity 1.0
    Prints: {"image": "OUT.png", "bounds": [w, s, e, n], "size": [w_px, h_px]}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.warp import Resampling, calculate_default_transform, reproject, transform_bounds

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vizkit import RAMPS  # noqa: E402  (same ramps as the chart pages)


def hex_rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--band", type=int, default=1)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--ramp", help=f"one of {sorted(RAMPS)} or comma-separated hex colours")
    g.add_argument("--classes", help='value=#hex pairs, e.g. "1=#E8432A,2=#BDEBCB"')
    ap.add_argument("--vmin", type=float)
    ap.add_argument("--vmax", type=float)
    ap.add_argument("--nodata", type=float)
    ap.add_argument("--max-size", type=int, default=4096)
    ap.add_argument("--opacity", type=float, default=1.0)
    a = ap.parse_args()

    with rasterio.open(a.src) as src:
        if src.crs is None:
            sys.exit("raster has no CRS")
        nod = a.nodata if a.nodata is not None else src.nodata
        tr, w, h = calculate_default_transform(src.crs, "EPSG:3857", src.width, src.height, *src.bounds)
        k = max(1.0, max(w, h) / a.max_size)                     # downsample to the size cap
        w, h = int(round(w / k)), int(round(h / k))
        tr = tr * tr.scale(k, k)
        dst = np.full((h, w), np.nan, dtype="float64")
        reproject(rasterio.band(src, a.band), dst, src_transform=src.transform, src_crs=src.crs, src_nodata=nod,
                  dst_transform=tr, dst_crs="EPSG:3857", dst_nodata=np.nan,
                  resampling=Resampling.nearest if a.classes else Resampling.bilinear)
    valid = np.isfinite(dst)
    if not valid.any():
        sys.exit("no valid pixels after reprojection (check --nodata and the band)")
    rgba = np.zeros((h, w, 4), dtype="uint8")
    if a.classes:
        for pair in a.classes.split(","):
            v, c = pair.split("=")
            m = valid & np.isclose(dst, float(v))
            rgba[m, :3] = hex_rgb(c)
            rgba[m, 3] = int(255 * a.opacity)
    else:
        cs = RAMPS.get(a.ramp) or [c.strip() for c in a.ramp.split(",")]
        lo = a.vmin if a.vmin is not None else float(np.nanpercentile(dst, 2))
        hi = a.vmax if a.vmax is not None else float(np.nanpercentile(dst, 98))
        t = np.clip((dst - lo) / ((hi - lo) or 1), 0, 1)
        stops = np.array([hex_rgb(c) for c in cs], dtype="float64")
        f = np.where(valid, t, 0) * (len(cs) - 1)
        i = np.minimum(f.astype(int), len(cs) - 2)
        frac = (f - i)[..., None]
        rgb = stops[i] * (1 - frac) + stops[i + 1] * frac
        rgba[..., :3] = rgb.round().astype("uint8")
        rgba[..., 3] = np.where(valid, int(255 * a.opacity), 0)
    Image.fromarray(rgba, "RGBA").save(a.out, optimize=True)
    west, north = tr * (0, 0)
    east, south = tr * (w, h)
    b = transform_bounds("EPSG:3857", "EPSG:4326", west, south, east, north)
    print(json.dumps({"image": str(a.out), "bounds": [round(x, 6) for x in b], "size": [w, h]}))


if __name__ == "__main__":
    main()
