#!/usr/bin/env python3
"""Public penguin data for the example pages, downloaded once and cached.

WHY THIS EXISTS
    The example pages show the skill with real, openly licensed ecological data that anyone can download:
    the Palmer Penguins measurements (Gorman et al. 2014, via Horst et al. 2020), GBIF records of the same three
    penguin species around Palmer Station, and the SCAR gazetteer positions of the three places where the Palmer
    birds were measured. Each source is fetched once into a cache folder with the URL and the date it was fetched,
    so every page can say exactly what it used. Standard library only.

    Cache: env EXAMPLE_DATA, default ~/.cache/wri-html-pages/example-data. Delete a file there to fetch it again.

USE
    import penguin_data as pd_
    rows = pd_.penguins()            # list of dicts, one per bird (Palmer Penguins), "NA" -> None
    raw = pd_.penguins_raw()         # the fuller table (nest IDs), same row order
    isl = pd_.islands()              # {"Torgersen": {"place", "lon", "lat", "note"}, ...}
    g = pd_.gbif()                   # {"fetched", "query_url", "records": [...], "datasets": {...}}
"""
from __future__ import annotations

import csv
import io
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

# ============================================================================ settings
CACHE = Path(os.environ.get("EXAMPLE_DATA", Path.home() / ".cache" / "wri-html-pages" / "example-data")).expanduser()
UA = {"User-Agent": "wri-html-pages-examples/1.0 (+https://github.com/NCEAS-AI/Coding-Agent-Skills-for-Data-Science)"}
PP = "https://raw.githubusercontent.com/allisonhorst/palmerpenguins/main/inst/extdata/"
# The three species, with one colour each used on every example page (Okabe–Ito, close to the palmerpenguins palette)
SPECIES = {
    "Adelie":    {"label": "Adélie",    "latin": "Pygoscelis adeliae",     "gbif": 2481663, "hex": "#E69F00", "edge": "#6B4A00", "var": "var(--s2)"},
    "Chinstrap": {"label": "Chinstrap", "latin": "Pygoscelis antarcticus", "gbif": 2481664, "hex": "#CC79A7", "edge": "#5E2A4A", "var": "var(--s6)"},
    "Gentoo":    {"label": "Gentoo",    "latin": "Pygoscelis papua",       "gbif": 2481666, "hex": "#009E73", "edge": "#00402E", "var": "var(--s3)"},
}
# Palmer Penguins "island" -> the SCAR gazetteer place where those birds were measured (Gorman et al. 2014)
ISLAND_PLACES = {"Torgersen": "Torgersen Island", "Dream": "Dream Island", "Biscoe": "Biscoe Point"}
SCAR_WFS = ("https://data.aad.gov.au/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature"
            "&typeName=aadc:SCAR_CGA_PLACE_NAMES_SIMPLIFIED&outputFormat=application/json&CQL_FILTER=")
GBIF_BOX = (-66.0, -65.5, -62.0, -63.5)                 # west, south, east, north: the Palmer Archipelago and around it
GBIF_LICENSES = ("CC0_1_0", "CC_BY_4_0")                # openly reusable records only (no NC)
GBIF_PAGE = 300
# ============================================================================


def _today() -> str:
    """Today in the team's time zone (vizkit / identity.json), so fetch dates match the pages' dates."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
        import vizkit
        return vizkit.today()
    except Exception:                                    # noqa: BLE001 - used outside the skill: plain local date
        return date.today().isoformat()


def _get(url: str, tries: int = 4) -> bytes:
    for k in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except Exception:                                # noqa: BLE001 - network hiccup: back off and retry
            if k == tries - 1:
                raise
            time.sleep(2 * (k + 1))


def _cached(name: str, make) -> Path:
    """Return CACHE/name, creating it with make() -> bytes the first time (plus name.meta.json: when and from where)."""
    f = CACHE / name
    if not f.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        data, src = make()
        f.with_suffix(f.suffix + ".tmp").write_bytes(data)
        f.with_suffix(f.suffix + ".tmp").replace(f)
        (CACHE / f"{name}.meta.json").write_text(json.dumps({"fetched": _today(), "source": src}, indent=1))
        print(f"penguin_data: fetched {name} ({len(data) / 1e3:.0f} kB)")
    return f


def fetched_on(name: str) -> str:
    m = CACHE / f"{name}.meta.json"
    return json.loads(m.read_text())["fetched"] if m.exists() else ""


def _csv(name: str) -> list[dict]:
    f = _cached(name, lambda: (_get(PP + name), PP + name))
    rows = list(csv.DictReader(io.StringIO(f.read_text(encoding="utf-8"))))
    return [{k: (None if v in ("NA", "") else v) for k, v in r.items()} for r in rows]


def penguins() -> list[dict]:
    """One dict per bird: species, island, bill_length_mm, bill_depth_mm, flipper_length_mm, body_mass_g, sex, year
    (numbers as float/int, missing as None)."""
    out = []
    for r in _csv("penguins.csv"):
        for k in ("bill_length_mm", "bill_depth_mm", "flipper_length_mm", "body_mass_g"):
            r[k] = float(r[k]) if r[k] is not None else None
        r["year"] = int(r["year"])
        out.append(r)
    return out


def penguins_raw() -> list[dict]:
    """The fuller Palmer table (same birds, same order): studyName (season), Individual ID (N<nest>A<1|2>), ..."""
    return _csv("penguins_raw.csv")


def islands() -> dict:
    """SCAR Composite Gazetteer of Antarctica positions of the three Palmer Penguins sites."""
    def make():
        out = {}
        for isl, place in ISLAND_PLACES.items():
            url = SCAR_WFS + urllib.parse.quote(f"place_name_mapping='{place}'")
            f = json.loads(_get(url))["features"][0]
            lon, lat = f["geometry"]["coordinates"][:2]
            out[isl] = {"place": place, "lon": lon, "lat": lat, "note": f["properties"].get("narrative", "")}
        return json.dumps(out, indent=1).encode(), SCAR_WFS + "place_name_mapping=…"
    return json.loads(_cached("palmer_islands.json", make).read_text())


def gbif_query_url(offset: int = 0, limit: int = GBIF_PAGE, taxa=None) -> str:
    """The GBIF search for the three species (or `taxa`, a list of taxon keys) in GBIF_BOX, open licences only."""
    w, s, e, n = GBIF_BOX
    poly = f"POLYGON(({w} {s},{e} {s},{e} {n},{w} {n},{w} {s}))"
    q = [("taxonKey", t) for t in (taxa or [v["gbif"] for v in SPECIES.values()])] + [("license", lic) for lic in GBIF_LICENSES] + [
        ("geometry", poly), ("hasCoordinate", "true"), ("hasGeospatialIssue", "false"),
        ("occurrenceStatus", "PRESENT"), ("limit", limit), ("offset", offset)]
    return "https://api.gbif.org/v1/occurrence/search?" + urllib.parse.urlencode(q)


def gbif() -> dict:
    """GBIF occurrence records of the three species inside GBIF_BOX (open licences only), with each dataset's title,
    publisher and licence for attribution."""
    keep = ("key", "species", "decimalLatitude", "decimalLongitude", "year", "basisOfRecord", "datasetKey",
            "individualCount", "license", "coordinateUncertaintyInMeters")

    def make():
        # One query per species: GBIF's search slows to minutes per page beyond ~10,000 records into one query.
        recs = []
        for sp in SPECIES.values():
            off = 0
            while True:
                page = json.loads(_get(gbif_query_url(off, taxa=[sp["gbif"]])))
                recs += [{k: r.get(k) for k in keep} for r in page["results"]]
                off += GBIF_PAGE
                if page.get("endOfRecords") or off >= page["count"]:
                    break
                time.sleep(0.3)                          # be gentle with the public API
        ds = {}
        for k in sorted({r["datasetKey"] for r in recs}):
            d = json.loads(_get(f"https://api.gbif.org/v1/dataset/{k}"))
            org = d.get("publishingOrganizationKey")
            pub = json.loads(_get(f"https://api.gbif.org/v1/organization/{org}")).get("title", "") if org else ""
            ds[k] = {"title": d.get("title", k), "publisher": pub, "license": d.get("license", ""),
                     "doi": d.get("doi", ""), "n": sum(r["datasetKey"] == k for r in recs)}
        return (json.dumps({"query_url": gbif_query_url(0, GBIF_PAGE), "count": len(recs), "records": recs,
                            "datasets": ds}).encode(), gbif_query_url(0, GBIF_PAGE))
    g = json.loads(_cached("gbif_pygoscelis_palmer.json", make).read_text())
    g["fetched"] = fetched_on("gbif_pygoscelis_palmer.json")
    return g


if __name__ == "__main__":
    p, isl, g = penguins(), islands(), gbif()
    print(f"{len(p)} penguins; islands {list(isl)}; {g['count']:,} GBIF records from {len(g['datasets'])} datasets "
          f"(fetched {g['fetched']}); cache {CACHE}")
