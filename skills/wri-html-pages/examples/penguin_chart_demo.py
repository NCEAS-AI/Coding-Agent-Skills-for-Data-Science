#!/usr/bin/env python3
"""Archetype chart page: the Palmer penguins, size by species and sex, and why pooling species misleads.

WHY THIS EXISTS
    The reference chart page for the wri-html-pages skill. It uses open ecological data anyone can download
    (penguin_data.py: Palmer Penguins, CC0) and exercises every vizkit component: stat tiles, stacked columns,
    a heatmap with empty cells, a map panel, bars with bootstrap intervals, a line chart, a shaded table with
    one merited red box (a Simpson's-paradox correlation), and a rigor check under every panel. Every number
    is computed here from the data.

RUN (needs pandas and numpy; data are downloaded once into the example-data cache)
    python3 penguin_chart_demo.py OUT_DIR
    -> OUT_DIR/<dated title slug>.html, plus panels/<page slug>/: one page per chart card and the map's own page (the targets of each panel's Full screen and Copy link buttons)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import penguin_data as P  # noqa: E402
import vizkit as vk  # noqa: E402

# ============================================================================ settings
BOOT = 4000                     # bootstrap resamples per group
SEED = 20261013
C_F, C_M = "var(--s1)", "var(--s5)"          # female, male: the same two colours on every chart of the page
SP = {k: v["label"] for k, v in P.SPECIES.items()}
SPC = {k: v["var"] for k, v in P.SPECIES.items()}
# ============================================================================

out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=True)
d = pd.DataFrame(P.penguins())
raw = pd.DataFrame(P.penguins_raw())
assert len(raw) == len(d) and (raw.Species.str.split().str[0] == d.species).all(), "penguins and penguins_raw rows differ"
d["nest"] = raw["studyName"] + "/" + raw["Island"] + "/" + raw["Individual ID"].str.extract(r"(N\d+)", expand=False)
d["season"] = d.year.map(lambda y: f"{y}–{str(y + 1)[-2:]}")
seasons = sorted(d.season.unique())
measured = d.dropna(subset=["body_mass_g"])
sexed = measured.dropna(subset=["sex"])
n_unsexed = len(measured) - len(sexed)
per_nest_sex = sexed.groupby(["nest", "sex"]).size()
assert per_nest_sex.max() == 1, "a nest has two birds of one sex in a season: resampling birds would not be resampling nests"
pairs = int((sexed.groupby("nest").sex.nunique() == 2).sum())
rng = np.random.default_rng(SEED)
print(f"{len(d)} penguins, {len(measured)} measured, {n_unsexed} sex unknown, {pairs} nests with both partners")


def boot_ci(x):
    x = np.asarray(x, float)
    m = x[rng.integers(0, len(x), size=(BOOT, len(x)))].mean(1)
    return np.percentile(m, [2.5, 97.5])


# ---- tiles
mass = measured.groupby("species").body_mass_g.mean()
tiles = vk.stat_tiles([
    {"value": vk.fint(len(d)), "label": "penguins measured", "sub": f"{seasons[0]} to {seasons[-1]} breeding seasons",
     "tip": vk.tip("Penguins measured", f"{len(d)} adult penguins at their nests; {len(d) - len(measured)} have no measurements.",
                   tech=f"rows = {len(d)}; complete body measurements = {len(measured)}")},
    {"value": "3", "label": "species", "sub": ", ".join(f"{SP[k]} {int((d.species == k).sum())}" for k in SP),
     "tip": vk.tip("Species", "Adélie, Chinstrap and Gentoo: the three brush-tailed penguins (genus Pygoscelis).")},
    {"value": vk.fint(pairs), "label": "nests with both partners measured",
     "sub": "birds come in pairs", "tip": vk.tip("Pairs", f"At {pairs} nests both the male and the female were measured.",
                                                 meaning="partners share a nest and a season, so they are not fully independent; "
                                                         "the charts compare within one sex to keep each bird independent",
                                                 tech="nest = season × island × N-number from Individual ID (penguins_raw)")},
    {"value": f"{mass['Gentoo'] / 1000:.1f} kg", "label": "average Gentoo, the largest",
     "sub": f"Adélie {mass['Adelie'] / 1000:.1f} kg, Chinstrap {mass['Chinstrap'] / 1000:.1f} kg",
     "tip": vk.tip("Body mass", "Average weight of each species, males and females together.",
                   tech=", ".join(f"{SP[k]} mean {v:.0f} g" for k, v in mass.items()))},
])
sp_legend_tip = {k: vk.tip(f"{SP[k]} penguin", f"Pygoscelis {P.SPECIES[k]['latin'].split()[1]}") for k in SP}

# ---- who was measured: per season, stacked by species
ct = d.groupby(["season", "species"]).size().unstack(fill_value=0).reindex(seasons)
season_tip = vk.tip("Breeding season", "Southern summer, November to January; each bird is counted in its season.",
                    tech="palmerpenguins `year` = first year of the season (PAL0708 = 2007).")
per_season = vk.card(
    vk.columns(seasons, [{"name": SP[k], "color": SPC[k], "values": ct[k].tolist(), "tip": sp_legend_tip[k]} for k in SP],
               tips=[vk.tip(s, f"{int(r.sum())} penguins", ", ".join(f"{SP[k]} {int(r[k])}" for k in SP)) for s, r in ct.iterrows()],
               x_title="Breeding season", y_title="Penguins measured", x_tip=season_tip,
               y_tip=vk.tip("Penguins measured", "How many birds were measured, set by how many nests were studied.",
                            tech="Row counts by season and species.")),
    title="Penguins measured each season",
    checks=["Counts of birds measured, fixed by the study design; they are not population sizes or trends.",
            "All three species in every season, so seasons can be compared like for like."],
    caption=vk.dual("Roughly the same number of each species every season: the study followed a set of nests each summer.",
                    "Counts per season × species; sampling effort (nests followed) sets n, not abundance."))

# ---- which species where: island x species counts (empty = none measured)
isl_order = ["Biscoe", "Dream", "Torgersen"]
xs = pd.crosstab(d.species, d.island).reindex(index=list(SP), columns=isl_order, fill_value=0)
cells = [[({"v": v / xs.values.max(), "text": str(v), "tip": vk.tip(f"{SP[sp]} · {isl}", f"{v} penguins measured")}
           if v else {"empty": True, "tip": vk.tip(f"{SP[sp]} · {isl}", "None measured here.")}) for isl, v in row.items()]
         for sp, row in xs.iterrows()]
where = vk.card(
    vk.ramp_key("fewer", "more penguins", "blues", empty_label="none measured", tip=vk.tip("Colour", "Darker = more birds measured.")) +
    vk.heatmap([SP[k] for k in xs.index], isl_order, cells, ramp="blues", domain=(0, 1),
               caption="Number of penguins measured, by species and island.",
               col_tips=[vk.tip(i, f"{int(xs[i].sum())} penguins measured", P.islands()[i]["place"]) for i in isl_order],
               row_tips=[vk.tip(SP[k], f"{int(xs.loc[k].sum())} penguins") for k in xs.index], phone="scroll"),
    title="Which species were measured where",
    checks=["Island and species are entangled: Gentoo only on Biscoe, Chinstrap only on Dream. Island comparisons are "
            "therefore mostly species comparisons, so the charts below compare species, and islands only within Adélie."],
    caption=vk.dual("Only Adélie penguins were measured on all three islands. A chart of islands would really be a chart of species.",
                    "Species × island contingency table; two structural zeros per row for Gentoo and Chinstrap (complete confounding)."))

# ---- map panel: the three sites
work = out / "_build_charts"
work.mkdir(parents=True, exist_ok=True)
isl = P.islands()
feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [s["lon"], s["lat"]]},
          "properties": {"site": s["place"], "n": int((d.island == c).sum()),
                         "who": ", ".join(f"{SP[k]} {int(xs.loc[k, c])}" for k in SP if xs.loc[k, c])}} for c, s in isl.items()]
(work / "sites.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
map_spec = {"panel_title": "Study sites", "basemap": "satellite", "basemaps": ["satellite", "map"], "vector_style": "positron",
            "max_fit_zoom": 10,
            "layers": [{"id": "sites", "name": "Palmer Penguins study sites", "kind": "point", "file": "sites.geojson",
                        "description": "Where the penguins were measured.", "show_count": False,
                        "description_tech": "SCAR Composite Gazetteer positions (arc-minute precision).",
                        "style": {"color": "#FFFFFF", "radius": [[6, 7], [10, 10]], "opacity": .9, "outline": "#1B2430",
                                  "outline_width": 2},
                        "tooltip": {"title_field": "site", "text": "A Palmer Penguins study site.",
                                    "fields": [{"field": "n", "label": "Penguins measured", "format": "int"},
                                               {"field": "who", "label": "By species"}]}}]}
def km(a, b):                                    # great-circle distance between two sites
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


spread = max(km(a, b) for a in isl.values() for b in isl.values())
site_map = vk.card(vk.map_panel(map_spec, base=work, height=420, phone_height=360, label="Map of the three study sites"),
                   title="Where the three sites are",
                   checks=["Positions from the SCAR gazetteer, good to about a kilometre: enough to show the sites, not colonies."],
                   caption=f"The three sites are at most {spread:.0f} km apart, around Palmer Station on Anvers Island. Hover over or tap a ring for "
                           "who was measured there; use two fingers (or Ctrl + scroll) to move the map.")

# ---- body mass by species and sex, 95% bootstrap intervals
rows = []
for k in SP:
    vals = {}
    for sx, key in (("female", "f"), ("male", "m")):
        x = sexed[(sexed.species == k) & (sexed.sex == sx)].body_mass_g / 1000
        lo, hi = boot_ci(x)
        vals[key] = {"v": x.mean(), "lo": lo, "hi": hi,
                     "tip": vk.tip(f"{SP[k]} · {sx}s", f"average {x.mean():.2f} kg ({len(x)} birds)",
                                   f"Range we can trust: {lo:.2f}–{hi:.2f} kg",
                                   tech=[f"mean {x.mean() * 1000:.0f} g, sd {x.std() * 1000:.0f} g, n = {len(x)}",
                                         f"95% percentile CI from {BOOT} bootstrap resamples of birds (one per nest)"])}
    rows.append({"label": SP[k], "sub": f"{int((sexed.species == k).sum())} birds", "values": vals})
gap = {k: sexed[(sexed.species == k) & (sexed.sex == "male")].body_mass_g.mean() /
          sexed[(sexed.species == k) & (sexed.sex == "female")].body_mass_g.mean() - 1 for k in SP}
mass_bars = vk.card(
    vk.hbar(rows, [{"key": "f", "name": "Females", "color": C_F, "tip": vk.tip("Females", "Birds sexed as female.")},
                   {"key": "m", "name": "Males", "color": C_M, "tip": vk.tip("Males", "Birds sexed as male.")}],
            unit=" kg", decimals=2, domain=(0, math.ceil(sexed.body_mass_g.max() / 1000)),
            axis_title="Average body mass",
            axis_tip=vk.tip("Average body mass", "Weight at the nest, in kilograms; bars start at zero.",
                            tech="Arithmetic mean of body_mass_g / 1000 per species × sex.")),
    title="Body mass by species and sex",
    checks=["Within a species and sex every bird is from a different nest (checked in the script), so resampling birds "
            "resamples independent nests.",
            f"{n_unsexed} measured birds of unknown sex are left out of this chart.",
            "Bars start at zero; one axis for all species."],
    caption=vk.dual(f"Gentoo are by far the heaviest. In every species males outweigh females, by "
                    f"{min(gap.values()):.0%} to {max(gap.values()):.0%}; the whiskers don't overlap, so the gaps are real.",
                    f"Means with 95% percentile bootstrap intervals ({BOOT} resamples within species × sex). "
                    "Male/female mean ratio − 1: " + ", ".join(f"{SP[k]} {v:.3f}" for k, v in gap.items()) + "."))

# ---- flipper length by season (no trend claimed from three seasons)
fl = measured.groupby(["species", "season"]).flipper_length_mm.agg(["mean", "std", "size"])
lo_y, hi_y = 5 * math.floor(fl["mean"].min() / 5) - 5, 5 * math.ceil(fl["mean"].max() / 5) + 5
flip = vk.card(
    vk.line_chart(list(range(len(seasons))),
                  [{"key": k, "name": SP[k], "color": SPC[k], "values": [round(fl.loc[(k, s), "mean"], 1) for s in seasons],
                    "tip": sp_legend_tip[k]} for k in SP],
                  x_labels=seasons, unit=" mm", y_domain=(lo_y, hi_y),
                  tips={k: [vk.tip(f"{SP[k]} · {s}", f"average {fl.loc[(k, s), 'mean']:.1f} mm ({int(fl.loc[(k, s), 'size'])} birds)",
                                   tech=f"sd {fl.loc[(k, s), 'std']:.1f} mm") for s in seasons] for k in SP},
                  x_title="Breeding season", y_title="Average flipper length", x_tip=season_tip,
                  y_tip=vk.tip("Flipper length", "Wing (flipper) length in millimetres. The axis does not start at zero, "
                               "to show the gaps between species; it is the same for all three.")),
    title="Flipper length, by season",
    checks=["Three seasons: too few to call a trend, and none is claimed.",
            f"Axis runs {lo_y}–{hi_y} mm (not from zero) so the species gaps are visible; stated on the axis hover."],
    caption=vk.dual("Each species keeps its size from season to season; the differences are between species, not years.",
                    "Season means per species, n per point in the hover; season-to-season changes are within a few mm."))

# ---- Simpson's paradox: bill length vs depth, pooled vs within species
def corr_row(x, y):
    r = float(np.corrcoef(x, y)[0, 1])
    z, se = math.atanh(r), 1 / math.sqrt(len(x) - 3)
    return r, math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se), len(x)


pooled = corr_row(measured.bill_length_mm, measured.bill_depth_mm)
within = {k: corr_row(g.bill_length_mm, g.bill_depth_mm) for k, g in measured.groupby("species")}
flip_sign = all(math.copysign(1, w[0]) != math.copysign(1, pooled[0]) for w in within.values())


def r_cell(r, lo, hi, n, label, flag=False):
    c = {"text": f"{r:+.2f}", "v": r, "tip": f"{label}: r = {r:+.2f} (95% interval {lo:+.2f} to {hi:+.2f}, {n} birds)"}
    if flag:
        c["flag"] = "opposite in sign to the correlation inside every species"
    return c


trows = [["<b>All penguins together</b>", str(pooled[3]), r_cell(*pooled, "Pooled", flag=flip_sign),
          f"{pooled[1]:+.2f} to {pooled[2]:+.2f}", "Longer bills look shallower"]]
for k, (r, lo, hi, n) in within.items():
    trows.append([SP[k], str(n), r_cell(r, lo, hi, n, SP[k]), f"{lo:+.2f} to {hi:+.2f}", "Longer bills are deeper"])
simpson = vk.card(
    vk.shade_key("negative", "positive", scale="diverging", better="high", flag="misleading: opposite to every species" if flip_sign else "",
                 tip=vk.tip("Shading", "Red = negative correlation, blue = positive; pale = near zero."),
                 flag_tip=vk.tip("Red box", "The pooled number points the opposite way to every species: Simpson's paradox.",
                                 tech="Flag rule: pooled r has the opposite sign to all within-group r.")) +
    vk.table(["Group", "Birds", "Correlation (r)", "95% interval", "What it says"], trows, numeric=(1, 2, 3),
             shade={2: {"scale": "diverging", "better": "high", "domain": (-1, 1), "mid": 0}},
             col_tips=[vk.tip("Group", "All birds together, or one species."), vk.tip("Birds", "Birds with both bill measurements."),
                       vk.tip("Correlation", "How closely bill length and bill depth rise together: +1 in step, 0 unrelated, "
                              "−1 opposite.", tech="Pearson r."),
                       vk.tip("95% interval", "The range of correlations the data are consistent with.",
                              tech="Fisher z interval, birds treated as independent (partners share a nest, so slightly narrow)."),
                       vk.tip("What it says", "The plain reading of the correlation.")],
             phone="cards"),
    title="Bill length and depth: together they point the wrong way",
    checks=["Correlation computed within each species and pooled; the pooled one is flagged because it reverses every species.",
            "Intervals treat birds as independent; partners from one nest are not, so the intervals are a little narrow, "
            "far less than the sign flip.",
            "Red box rule set before looking: pooled sign opposite to all species."],
    caption=vk.dual(f"Within every species, penguins with longer bills also have deeper bills (r = {min(w[0] for w in within.values()):+.2f} "
                    f"to {max(w[0] for w in within.values()):+.2f}). Pool the species and it seems to reverse (r = {pooled[0]:+.2f}), "
                    "because Gentoo have long but shallow bills. Always compare within species.",
                    "Simpson's paradox: the between-species association (Gentoo: long, shallow bills) dominates the pooled Pearson r "
                    "and has the opposite sign to every within-species r."))

# ---- size table: species x sex
agg = sexed.groupby(["species", "sex"]).agg(n=("body_mass_g", "size"), bl=("bill_length_mm", "mean"), bd=("bill_depth_mm", "mean"),
                                            fl=("flipper_length_mm", "mean"), bm=("body_mass_g", "mean"))
cols = {"bl": (1, "Bill length (mm)"), "bd": (1, "Bill depth (mm)"), "fl": (0, "Flipper (mm)"), "bm": (0, "Body mass (g)")}
srows = [[SP[sp], sx, str(int(r.n))] + [{"text": f"{r[c]:,.{dp}f}", "v": r[c], "tip": f"{SP[sp]} {sx}s: average {lab.lower()} {r[c]:,.{dp}f}"}
                                        for c, (dp, lab) in cols.items()] for (sp, sx), r in agg.iterrows()]
size_table = vk.card(
    vk.shade_key("smaller", "larger", scale="blues", better=None, tip=vk.tip("Shading", "Darker = larger. Size only: no colour means good or bad.")) +
    vk.table(["Species", "Sex", "Birds"] + [lab for _, lab in cols.values()], srows, numeric=(2, 3, 4, 5, 6),
             shade={i: {"scale": "blues", "better": None} for i in (3, 4, 5, 6)},
             col_tips=[vk.tip("Species", "Adélie, Chinstrap or Gentoo."), vk.tip("Sex", "Determined from blood samples."),
                       vk.tip("Birds", "Birds of known sex with measurements.")] +
                      [vk.tip(lab, "Average for the group; each column shaded on its own.") for _, lab in cols.values()],
             phone="cards"),
    title="Average size by species and sex",
    checks=["Averages only; the bars above show how certain the body-mass averages are.",
            "Each column is shaded on its own blue scale: size only, no judgement."],
    caption="Gentoo are the largest on every measure except bill depth, where they are the smallest.")

title = f"Chart archetype: Palmer penguins, size by species and sex · {vk.today()}"
subtitle = (f"Bill, flipper and body-mass measurements of {len(d)} adult Adélie, Chinstrap and Gentoo penguins at three sites in "
            f"the Palmer Archipelago, Antarctica, {seasons[0]} to {seasons[-1]}: differences by species and sex with bootstrap "
            "intervals, and why pooling the species misleads.")
body = (vk.section("Who was measured", per_season + where + site_map) +
        vk.section("How big", mass_bars + flip + size_table,
                   lede=f"Gentoo average {mass['Gentoo'] / 1000:.1f} kg, about a third heavier than the other two species.") +
        vk.section("A trap", simpson))
page = vk.page(
    title, body, subtitle=subtitle, eyebrow="Chart archetype · open ecological data", tiles=tiles,
    how_to_read="<p>Hover over, tap or tab to any bar, dot, cell, tile, axis title, legend entry or column heading for what it "
                "means and its exact numbers. The <b>Plain language / Technical</b> switch at the top changes the explanations "
                "from plain readings to the statistical detail.</p><p>Colours mean the same thing on every chart: "
                "<b style='color:var(--s2)'>orange</b> is Adélie, <b style='color:var(--s6)'>pink</b> is Chinstrap, "
                "<b style='color:var(--s3)'>green</b> is Gentoo; <b style='color:var(--s1)'>blue</b> is females and "
                "<b style='color:var(--s5)'>light blue</b> males.</p>",
    sources=["Gorman, K.B., Williams, T.D., Fraser, W.R. (2014) Ecological sexual dimorphism and environmental variability within a "
             "community of Antarctic penguins (genus <i>Pygoscelis</i>). PLoS ONE 9(3): e90081, "
             "<a href=\"https://doi.org/10.1371/journal.pone.0090081\">doi:10.1371/journal.pone.0090081</a>. Palmer Station "
             "Antarctica LTER.",
             "Data via Horst, A.M., Hill, A.P., Gorman, K.B. (2020) palmerpenguins: Palmer Archipelago (Antarctica) penguin data, "
             "<a href=\"https://doi.org/10.5281/zenodo.3960218\">doi:10.5281/zenodo.3960218</a> (CC0 1.0).",
             "Site positions: SCAR Composite Gazetteer of Antarctica, Australian Antarctic Data Centre.",
             "Map base layers: Esri World Imagery; OpenStreetMap contributors via OpenFreeMap (ODbL)."],
    footer="Made with the wri-html-pages skill: examples/penguin_chart_demo.py.")
dest = out / f"{vk.slug(title)}.html"
for f in vk.write_page(dest, page):        # the page and, beside it, one page per panel (panels/<page slug>/)
    print("wrote", f, f"{f.stat().st_size / 1e3:.0f} kB")
