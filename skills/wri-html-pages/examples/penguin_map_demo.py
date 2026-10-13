#!/usr/bin/env python3
"""Archetype map: penguin records around Palmer Station, Antarctica, and the islands of the Palmer Penguins study.

WHY THIS EXISTS
    The reference map for the wri-html-pages skill. It uses only open data anyone can download (penguin_data.py):
    GBIF records of Adélie, Chinstrap and Gentoo penguins (CC0 and CC BY 4.0), the Palmer Penguins measurements
    (CC0), and the SCAR gazetteer. It exercises the template: two point layers with species filters and counts, a
    layer with ready-made hover cards, "places to look" tabs, base maps, and Plain / Technical text.

RUN (standard library only; data are downloaded once into the example-data cache, see penguin_data.py)
    python3 penguin_map_demo.py OUT_DIR
    -> OUT_DIR/<dated title slug>.html  (+ OUT_DIR/_build/ with the spec and GeoJSON it was built from)
"""
from __future__ import annotations

import collections
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import penguin_data as P  # noqa: E402
import vizkit as vk  # noqa: E402  (only for today(): the date in the team's time zone)

# ============================================================================ settings
SITE_PAD = (0.09, 0.035)        # lon, lat half-width of a "place to look" view around a study site (about 4 km)
FIELD = {"HUMAN_OBSERVATION", "MACHINE_OBSERVATION", "OBSERVATION", "OCCURRENCE"}   # everything else: specimens, samples
BUILD_MAP = Path(__file__).resolve().parents[1] / "scripts" / "build_map.py"
# ============================================================================

out = Path(sys.argv[1]).resolve()
work = out / "_build"
work.mkdir(parents=True, exist_ok=True)
g, isl, birds = P.gbif(), P.islands(), P.penguins()
by_latin = {v["latin"]: k for k, v in P.SPECIES.items()}
recs = [r for r in g["records"] if r["species"] in by_latin]
years = sorted(r["year"] for r in recs if r["year"])
print(f"GBIF: {len(recs):,} records ({g['fetched']}), {years[0]}-{years[-1]}; {len(g['datasets'])} datasets")


def short(t, n=70):
    return t if len(t) <= n else t[:n - 1].rsplit(" ", 1)[0] + "…"


def feat(r):
    sp = by_latin[r["species"]]
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [r["decimalLongitude"], r["decimalLatitude"]]},
            "properties": {"sp": P.SPECIES[sp]["label"], "yr": r["year"], "n": r["individualCount"],
                           "ds": short(g["datasets"][r["datasetKey"]]["title"]),
                           "kind": r["basisOfRecord"].replace("_", " ").lower()}}


for name, keep in (("field.geojson", lambda r: r["basisOfRecord"] in FIELD), ("published.geojson", lambda r: r["basisOfRecord"] not in FIELD)):
    (work / name).write_text(json.dumps({"type": "FeatureCollection", "features": [feat(r) for r in recs if keep(r)]}))
n_field = sum(r["basisOfRecord"] in FIELD for r in recs)


def describe(rs):
    """What a layer's records are, from the data: the main datasets and the median year."""
    top = collections.Counter(g["datasets"][r["datasetKey"]]["title"] for r in rs).most_common(2)
    yrs = sorted(r["year"] for r in rs if r["year"])
    return top, yrs[len(yrs) // 2], collections.Counter(r["basisOfRecord"] for r in rs)


f_top, f_med, f_basis = describe([r for r in recs if r["basisOfRecord"] in FIELD])
o_top, o_med, o_basis = describe([r for r in recs if r["basisOfRecord"] not in FIELD])
basis_txt = lambda c: ", ".join(f"{k} {v:,}" for k, v in c.most_common())

# ---- the three Palmer Penguins sites: a ready-made card with the birds measured there
cards = []
for code, s in isl.items():
    here = [b for b in birds if b["island"] == code]
    cnt = collections.Counter(b["species"] for b in here)
    rows = "".join(f"<tr><td>{P.SPECIES[k]['label']}</td><td style='text-align:right'>{cnt[k]}</td></tr>" for k in P.SPECIES if cnt[k])
    cards.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [s["lon"], s["lat"]]},
                  "properties": {"card": f"<b>{s['place']}</b><br>{len(here)} penguins measured, 2007–2009:"
                                         f"<table style='margin-top:4px'>{rows}</table>"}})
(work / "sites.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": cards}))

# ---- places to look: one tab per study site, with what is recorded nearby
sites = []
for code, s in isl.items():
    w, so, e, n = s["lon"] - SITE_PAD[0], s["lat"] - SITE_PAD[1], s["lon"] + SITE_PAD[0], s["lat"] + SITE_PAD[1]
    near = collections.Counter(P.SPECIES[by_latin[r["species"]]]["label"] for r in recs
                               if w <= r["decimalLongitude"] <= e and so <= r["decimalLatitude"] <= n)
    here = collections.Counter(P.SPECIES[b["species"]]["label"] for b in birds if b["island"] == code)
    sites.append({"name": s["place"], "bounds": [round(w, 4), round(so, 4), round(e, 4), round(n, 4)],
                  "note": f"Palmer Penguins measured {', '.join(f'{v} {k}' for k, v in here.items())} here. "
                          f"GBIF has {sum(near.values()):,} records in this view"
                          + (f" ({', '.join(f'{v:,} {k}' for k, v in near.most_common())})." if near else ".")})

sp_color = {"type": "categorical", "field": "sp", "categories": [
    {"value": P.SPECIES[k]["label"], "label": f"{P.SPECIES[k]['label']} penguin", "color": P.SPECIES[k]["hex"],
     "edge": P.SPECIES[k]["edge"]} for k in ("Chinstrap", "Adelie", "Gentoo")]}     # rarest on top
card = {"title_field": "sp", "fields": [{"field": "yr", "label": "Year"}, {"field": "n", "label": "Birds counted", "format": "int"},
                                        {"field": "kind", "label": "Kind of record"}, {"field": "ds", "label": "Dataset"}]}
ds_sorted = sorted(g["datasets"].values(), key=lambda d: -d["n"])
lic = collections.Counter("CC0" if "zero" in d["license"].lower() or "cc0" in d["license"].lower() else "CC BY 4.0" for d in ds_sorted)
attrib = "; ".join(f"{d['title']} ({d['publisher']}, {d['n']:,} records)" for d in ds_sorted)
spec = {
    "eyebrow": "Map archetype · open ecological data",
    "title": f"Map archetype: penguin records around Palmer Station · {vk.today()}",
    "subtitle": f"Palmer Archipelago, western Antarctic Peninsula · {len(recs):,} GBIF records of Adélie, Chinstrap and Gentoo "
                f"penguins ({years[0]}–{years[-1]}, openly licensed), split into field observations and records from publications "
                f"and collections, with the "
                f"three places where the Palmer Penguins birds were measured.",
    "how_to_read": "<p>Each dot is one record of a penguin in GBIF, coloured by species. A record can be one bird or a whole "
                   "colony count, and many records sit on the same spot.</p><p><b>Dots show where people recorded penguins, not "
                   "where penguins are.</b> Records crowd around Palmer Station, research colonies and ship landing sites; empty "
                   "areas were mostly not surveyed.</p><p>White rings mark the three sites of the Palmer Penguins study. Use "
                   "<b>Places to look</b> to fly to each one; hover over or tap anything for details.</p>",
    "how_to_read_tech": f"<p>Points: GBIF occurrence search (fetched {g['fetched']}) for taxonKeys "
                        + ", ".join(str(v["gbif"]) for v in P.SPECIES.values())
                        + f" inside lon {P.GBIF_BOX[0]}…{P.GBIF_BOX[2]}, lat {P.GBIF_BOX[1]}…{P.GBIF_BOX[3]}; hasCoordinate, no "
                          "geospatial issue, occurrenceStatus PRESENT, licences CC0 1.0 and CC BY 4.0 only. Presence-only data "
                          "with strong observer-effort bias; no duplicate removal.</p><p>Layers split by basisOfRecord: "
                          f"HUMAN/MACHINE_OBSERVATION, OBSERVATION and OCCURRENCE ({basis_txt(f_basis)}) vs the rest "
                          f"({basis_txt(o_basis)}). Rings: SCAR Composite Gazetteer positions (to the arc-minute, about 1 km).</p>",
    "basemap": "satellite", "basemaps": ["satellite", "map", "hybrid"], "vector_style": "positron",
    "basemap_notes": {"satellite": "Esri World Imagery: summer imagery; snow and sea ice differ from season to season."},
    "sites": sites, "whole_label": "Whole area",
    "layers": [
        {"id": "published", "name": "From publications and collections", "kind": "point", "file": "published.geojson",
         "description": f"Records gathered from published studies (mostly the {o_top[0][0].removeprefix('The ')}), plus museum specimens and DNA "
                        f"samples; half are from {o_med} or earlier.",
         "description_tech": f"basisOfRecord not an observation: {basis_txt(o_basis)}. Main datasets: "
                             + "; ".join(f"{t} ({n:,})" for t, n in o_top) + f". Median year {o_med}.",
         "color_by": sp_color, "tooltip": {**card, "text": "A record from a publication, specimen or sample."},
         "style": {"radius": [[6, 2.2], [9, 3.4], [13, 6]], "opacity": .9, "outline_width": .6}},
        {"id": "field", "name": "Field observations", "kind": "point", "file": "field.geojson",
         "description": f"Sightings and counts by birders, visitors and researchers (mostly {f_top[0][0].split(' – ')[0]}); "
                        f"half are from {f_med} or later.",
         "description_tech": f"basisOfRecord: {basis_txt(f_basis)}. Main datasets: "
                             + "; ".join(f"{t} ({n:,})" for t, n in f_top) + f". Median year {f_med}.",
         "color_by": sp_color, "tooltip": {**card, "text": "A sighting or count reported to GBIF."},
         "style": {"radius": [[6, 1.8], [9, 2.8], [13, 5]], "opacity": .85, "outline_width": .5}},
        {"id": "sites", "name": "Palmer Penguins study sites", "kind": "point", "file": "sites.geojson", "show_count": False,
         "description": "Where the 344 penguins in the Palmer Penguins data were measured, 2007–2009.",
         "description_tech": "Torgersen Island, Dream Island and Biscoe Point (SCAR gazetteer); Gorman et al. 2014.",
         "style": {"color": "#FFFFFF", "radius": [[6, 6], [10, 9], [13, 12]], "opacity": 0.15, "outline": "#FFFFFF",
                   "outline_width": 2.5},
         "tooltip": {"html_field": "card"}},
    ],
    "sources": [
        f"Penguin records: GBIF.org occurrence search, fetched {g['fetched']}, {len(recs):,} records from {len(ds_sorted)} datasets "
        f"({', '.join(f'{v} {k}' for k, v in lic.items())}). <a href=\"{g['query_url']}\">The query</a>. "
        f"<details><summary>All datasets, for attribution</summary>{attrib}.</details>",
        "Study sites and measurements: Gorman, K.B., Williams, T.D., Fraser, W.R. (2014) Ecological sexual dimorphism and "
        "environmental variability within a community of Antarctic penguins (genus <i>Pygoscelis</i>). PLoS ONE 9(3): e90081, "
        "<a href=\"https://doi.org/10.1371/journal.pone.0090081\">doi:10.1371/journal.pone.0090081</a>; Palmer Station LTER. "
        "Data via Horst, A.M., Hill, A.P., Gorman, K.B. (2020) palmerpenguins, "
        "<a href=\"https://doi.org/10.5281/zenodo.3960218\">doi:10.5281/zenodo.3960218</a> (CC0 1.0).",
        "Place positions: SCAR Composite Gazetteer of Antarctica, Australian Antarctic Data Centre.",
        "Base maps: Esri World Imagery; OpenStreetMap contributors via OpenFreeMap (ODbL).",
    ],
    "footer": "Made with the wri-html-pages skill: examples/penguin_map_demo.py.",
}
(work / "spec.json").write_text(json.dumps(spec, indent=1))
print(f"field {n_field:,}, published {len(recs) - n_field:,}; sites: " + " | ".join(s["note"] for s in sites))
subprocess.run([sys.executable, str(BUILD_MAP), str(work / "spec.json"), str(out)], check=True)
