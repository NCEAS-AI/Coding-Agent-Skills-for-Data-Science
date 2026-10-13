#!/usr/bin/env python3
"""Build an interactive map page (MapLibre GL JS) from a JSON spec.

WHY THIS EXISTS
    Every map we share should look and behave the same way: a satellite base map with a switcher
    (satellite / NAIP aerial / street map / hybrid), a key that is also the layer control (tick a
    category to hide it, counts beside every class), hover cards that add information, tabs for the
    places worth looking at, and a layout that works on a phone. Hand-writing that each time drifts,
    so this script fills one tested template (`../assets/map_template.html`) from a spec.

USAGE
    python build_map.py SPEC.json OUT_DIR_or_OUT.html [--sidecar]

    Owner rule 2026-10-12: "title" is SHORT with the date at the end ("Penguin records around
    Palmer Station · 2026-10-13"); "subtitle" carries the detail (place, dates, cohort, counts, split,
    what is new in this iteration). The title is the browser title, the panel heading and, when OUT is a
    folder, the file name (vizkit.slug). The generation time is written into the file. The path written
    is printed.

    --sidecar   write each vector layer to OUT_DIR/data/<id>.geojson (and raster images to
                OUT_DIR/data/) instead of inlining them. Use it when the page would pass ~25 MB.
                Sidecar files are NOT covered by the PIN gate: in a gated folder, inline instead.

    Paths in the spec are relative to the spec file. Spec reference: ../references/spec.md.
    Vector inputs: GeoJSON in EPSG:4326, or anything GeoPandas reads (.gpkg .parquet .shp .fgb),
    which is reprojected to EPSG:4326.

WHAT IT CHECKS (fails rather than drawing a misleading map)
    * every field the spec colours by or shows in a hover card exists in the data;
    * coordinates are longitude/latitude (a projected file is an error, not a blank map);
    * an empty layer is an error unless the layer says "allow_empty": true;
    * values of a categorical field that have no category in the key are reported with counts.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vizkit import brand_strip, built_at, byline, generated_iso, slug  # noqa: E402  (shared with chart pages)

# ============================================================================ settings
HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "map_template.html"
DEFAULT_PRECISION = 6          # decimal degrees kept: 6 ≈ 0.1 m, 5 ≈ 1 m
WARN_MB, FAIL_MB = 25, 95      # GitHub refuses files over 100 MB
KINDS = {"point", "polygon", "line", "raster"}
# ============================================================================


def die(msg: str) -> None:
    raise SystemExit(f"build_map: ERROR: {msg}")


def load_vector(path: Path) -> dict:
    if path.suffix.lower() in {".geojson", ".json"}:
        fc = json.loads(path.read_text())
        crs = (fc.get("crs") or {}).get("properties", {}).get("name", "")
        if crs and not re.search(r"(4326|CRS84)", crs):
            die(f"{path.name}: GeoJSON declares CRS {crs}; reproject to EPSG:4326 first")
        return fc
    try:
        import geopandas as gpd
    except ImportError:
        die(f"{path.name}: install geopandas or convert to GeoJSON (EPSG:4326)")
    gdf = gpd.read_file(path) if path.suffix.lower() != ".parquet" else gpd.read_parquet(path)
    if gdf.crs is None:
        die(f"{path.name}: no CRS; set it before mapping")
    return json.loads(gdf.to_crs(4326).to_json(drop_id=True))


def walk_coords(geom):
    t, c = geom["type"], geom.get("coordinates")
    if t == "Point":
        yield c
    elif t in ("LineString", "MultiPoint"):
        yield from c
    elif t in ("Polygon", "MultiLineString"):
        for ring in c:
            yield from ring
    elif t == "MultiPolygon":
        for poly in c:
            for ring in poly:
                yield from ring
    elif t == "GeometryCollection":
        for g in geom["geometries"]:
            yield from walk_coords(g)


def round_geom(geom, nd):
    def r(x):
        if isinstance(x, (int, float)):
            return round(x, nd)
        return [r(v) for v in x]
    if geom["type"] == "GeometryCollection":
        return {"type": "GeometryCollection", "geometries": [round_geom(g, nd) for g in geom["geometries"]]}
    return {"type": geom["type"], "coordinates": r(geom["coordinates"])}


def used_fields(L: dict) -> set[str]:
    f = set(L.get("keep", []))
    cb = L.get("color_by") or {}
    if cb.get("field"):
        f.add(cb["field"])
    t = L.get("tooltip") or {}
    for k in ("title_field", "html_field"):
        if t.get(k):
            f.add(t[k])
    f.update(x["field"] for x in t.get("fields", []))
    return f


def bounds_of(fc: dict):
    xs, ys = [], []
    for ft in fc["features"]:
        if ft.get("geometry"):
            for x, y, *_ in walk_coords(ft["geometry"]):
                xs.append(x)
                ys.append(y)
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def union(bs):
    bs = [b for b in bs if b]
    return [min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)] if bs else None


def build_page(spec: dict, base: Path, *, embed: bool = False, sidecar_dir: Path | None = None):
    """Spec -> (page HTML, layer configs, warnings). embed=True makes the panel version that a chart page
    shows inside a card (vizkit.map_panel): no title block, byline, sources or logos (the host page has
    them), two-finger / Ctrl-scroll gestures so the page still scrolls past it, a fullscreen button."""
    nd = int(spec.get("precision", DEFAULT_PRECISION))
    warnings, data_blocks, fit_bounds, layers_cfg = [], [], [], []

    for L in spec["layers"]:
        L = dict(L)
        if L.get("kind") not in KINDS:
            die(f"layer {L.get('id')}: kind must be one of {sorted(KINDS)}")
        if not re.fullmatch(r"[A-Za-z][\w-]*", L.get("id", "")):
            die(f"layer id {L.get('id')!r}: use letters, digits, - or _")
        L.setdefault("name", L["id"])

        if L["kind"] == "raster":
            img = (base / L.pop("image")).resolve()
            w, s_, e, n = L.pop("bounds")
            if sidecar_dir:
                (sidecar_dir / "data").mkdir(parents=True, exist_ok=True)
                shutil.copy2(img, sidecar_dir / "data" / img.name)
                src = f"data/{img.name}"
            else:
                mime = "image/png" if img.suffix.lower() == ".png" else "image/jpeg"
                src = f"data:{mime};base64," + base64.b64encode(img.read_bytes()).decode()
            L["image"] = {"src": src, "coordinates": [[w, n], [e, n], [e, s_], [w, s_]]}
            if L.get("fit", True):
                fit_bounds.append([w, s_, e, n])
            layers_cfg.append(L)
            continue

        fc = load_vector((base / L.pop("file")).resolve())
        feats = [f for f in fc.get("features", []) if f.get("geometry")]
        if not feats and not L.get("allow_empty"):
            die(f"layer {L['id']}: no features (real data only: an empty layer usually means a bad filter)")
        need = used_fields(L)
        have = set().union(*(f.get("properties", {}).keys() for f in feats)) if feats else set()
        missing = need - have
        if feats and missing:
            die(f"layer {L['id']}: fields {sorted(missing)} not in the data (have: {sorted(have)[:25]})")
        b = bounds_of({"features": feats})
        if b and (abs(b[0]) > 180 or abs(b[2]) > 180 or abs(b[1]) > 90 or abs(b[3]) > 90):
            die(f"layer {L['id']}: coordinates are not longitude/latitude (bounds {b}); reproject to EPSG:4326")
        slim = {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": round_geom(f["geometry"], nd),
             "properties": {k: v for k, v in (f.get("properties") or {}).items() if k in need}}
            for f in feats]}
        L["count"] = L.get("count", len(feats)) if L.get("show_count", True) else None

        cb = L.get("color_by")
        if cb and cb.get("type") == "categorical":
            seen = Counter(str(f["properties"].get(cb["field"])) for f in slim["features"])
            keys = {str(c["value"]) for c in cb["categories"]}
            for c in cb["categories"]:
                c["count"] = seen.get(str(c["value"]), 0)
            extra = {k: v for k, v in seen.items() if k not in keys}
            if extra:
                warnings.append(f"layer {L['id']}: values with no category in the key (drawn in other_color): {extra}")
        if cb and cb.get("type") == "continuous" and not cb.get("stops"):
            die(f"layer {L['id']}: continuous color_by needs stops [[value, colour], ...]")

        if L.get("fit", True):
            fit_bounds.append(b)
        txt = json.dumps(slim, separators=(",", ":"), ensure_ascii=False)
        if sidecar_dir:
            (sidecar_dir / "data").mkdir(parents=True, exist_ok=True)
            (sidecar_dir / "data" / f"{L['id']}.geojson").write_text(txt)
            L["url"] = f"data/{L['id']}.geojson"
        else:
            safe = txt.replace("</", "<\\/")      # a "</script>" inside the data would end the block
            data_blocks.append(f'<script type="application/json" id="d-{L["id"]}">{safe}</script>')
        layers_cfg.append(L)

    bounds = spec.get("bounds") or union(fit_bounds)
    if not bounds:
        die("could not work out the map extent; give spec.bounds [west, south, east, north]")
    cfg = {k: v for k, v in spec.items() if k not in {"layers", "precision", "noindex", "author", "affiliation"}}
    gen_iso, gen_txt = generated_iso(), built_at()
    if embed:
        cfg.update(embed=True, hash=False, eyebrow="", subtitle="", lede="", byline="", brand="", footer="",
                   sources=[], title=spec.get("panel_title", "Map key and layers"))
    else:
        cfg["byline"] = byline(spec.get("author"), spec.get("affiliation"), gen_txt)   # author + build time (identity.json)
        cfg["brand"] = brand_strip() if spec.get("brand", True) else ""
        cfg.setdefault("footer", f"Built {dt.date.today().isoformat()}.")
    cfg["layers"] = layers_cfg
    cfg["bounds"] = bounds

    title = spec.get("title", "") if not embed else spec.get("panel_title", "Map")
    page = TEMPLATE.read_text()
    plain_title = re.sub(r"<[^>]+>", "", title)
    plain_desc = re.sub(r"<[^>]+>", "", spec.get("subtitle", ""))[:300]
    page = (page.replace("__TITLE__", html.escape(plain_title))
                .replace("__DESCRIPTION__", html.escape(plain_desc, quote=True))
                .replace("__GENERATED_COMMENT__", f"Generated {gen_txt} ({gen_iso})")
                .replace("__GENERATED__", gen_iso)
                .replace("__ROBOTS__", '<meta name="robots" content="noindex,nofollow">' if spec.get("noindex") else "")
                .replace("__CONFIG__", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
                .replace("__DATA__", "\n".join(data_blocks)))
    return page, layers_cfg, warnings


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--sidecar", action="store_true")
    a = ap.parse_args()

    spec = json.loads(a.spec.read_text())
    base = a.spec.resolve().parent
    title = spec.get("title", "")
    if not re.search(r"\b20\d\d-[01]\d-[0-3]\d\s*$", re.sub(r"<[^>]+>", "", title)):
        die("spec title must be short and END with the build date, e.g. "
            "'Penguin records around Palmer Station · 2026-10-13'; put the detail in 'subtitle'")
    if not spec.get("subtitle"):
        die("spec needs a 'subtitle' with the detail the short title leaves out (place, dates, cohort, counts, split, iteration)")
    if len(re.sub(r"<[^>]+>", "", title)) > 90:
        print("build_map: WARNING: title over 90 characters; move detail into the subtitle")
    out = a.out.resolve()
    if out.suffix.lower() != ".html":
        out = out / f"{slug(title)}.html"
    out.parent.mkdir(parents=True, exist_ok=True)

    page, layers_cfg, warnings = build_page(spec, base, sidecar_dir=out.parent if a.sidecar else None)
    out.write_text(page)

    mb = out.stat().st_size / 1e6
    for w in warnings:
        print("build_map: WARNING:", w)
    print(f"build_map: wrote {out} ({mb:.1f} MB): " +
          ", ".join(f"{L['id']}={L.get('count', 'image')}" for L in layers_cfg))
    if mb > FAIL_MB:
        die(f"{mb:.0f} MB is over GitHub's limit; use --sidecar, fewer fields, lower precision or simpler geometry")
    if mb > WARN_MB:
        print(f"build_map: WARNING: {mb:.0f} MB is slow on a phone; consider --sidecar or simplifying")


if __name__ == "__main__":
    main()
