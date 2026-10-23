#!/usr/bin/env python3
"""Deck archetype: the Palmer penguins, by species, sex and island, as a 13-slide presentation.

WHY THIS EXISTS
    The reference deck for the wri-html-decks skill, built from open ecological data anyone can download (the same
    Palmer Penguins and GBIF data as the page skill's examples), so it can be shared with anyone. It uses every
    building block once: cover, headline numbers, a one-square-per-bird grid, a still map with tabs and species
    toggles plus a link to the interactive map, grouped bars, estimates with intervals, lines, a scatter with fitted
    lines, time spans, a shaded table, numbered steps, a statement slide and the sources slide. Every number is
    computed here from the data.

USE
    python3 examples/penguin_deck_demo.py OUT_DIR       # needs Pillow (base maps); internet on the first run
    -> OUT_DIR/deck-archetype-palmer-penguins-species-sex-island-<date>.html
"""
# %% ⚙️ Settings
# ============================================================
import os
import random
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import deckkit as dk  # noqa: E402

sys.path.insert(0, str(dk.PAGES / "examples"))
import penguin_data as pdata  # noqa: E402  (downloads and caches the open data once)

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
DECK_DATE = "2026-10-23"          # the deck keeps its start date, so every rebuild updates the same link
TITLE = f"Deck archetype: Palmer penguins by species, sex and island · {DECK_DATE}"
SEED, N_BOOT = 42, 2000           # bootstrap intervals (seeded so a rebuild gives the same numbers)
LIVE_MAP = ("https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/"
            "map-archetype-penguin-records-around-palmer-station-2026-10-13.html")
SP = pdata.SPECIES                # one colour per species on every slide (the page examples' colours)
SEX_C = {"female": "#2E6A8A", "male": "#C4502B"}

# %% 1️⃣ Read the data
# ============================================================
birds = pdata.penguins()
isl = pdata.islands()
gb = pdata.gbif()
latin = {v["latin"]: k for k, v in SP.items()}
recs = [r for r in gb["records"] if r["species"] in latin and r["decimalLongitude"] is not None]
lab = {k: v["label"] for k, v in SP.items()}
n_all = len(birds)
years = sorted({b["year"] for b in birds})
by_sp = Counter(b["species"] for b in birds)
by_isl_sp = Counter((b["island"], b["species"]) for b in birds)
islands_order = sorted({b["island"] for b in birds}, key=lambda i: -sum(by_isl_sp[(i, s)] for s in SP))
sexed = [b for b in birds if b["sex"] in ("female", "male") and b["body_mass_g"] is not None]
print(f"{n_all} birds, {len(sexed)} with sex and body mass, {len(recs)} GBIF records")


def boot_ci(xs, seed=SEED):
    """95% bootstrap interval of the mean (birds resampled with replacement)."""
    rnd = random.Random(seed)
    ms = sorted(st.fmean(rnd.choices(xs, k=len(xs))) for _ in range(N_BOOT))
    return ms[int(.025 * N_BOOT)], ms[int(.975 * N_BOOT) - 1]


def group(field):
    g = defaultdict(list)
    for b in birds:
        if b["sex"] in ("female", "male") and b[field] is not None:
            g[(b["species"], b["sex"])].append(b[field])
    return g


def corr(xs, ys):
    mx, my = st.fmean(xs), st.fmean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** .5


def fit(xs, ys):
    mx, my = st.fmean(xs), st.fmean(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return b, my - b * mx


mass, flip = group("body_mass_g"), group("flipper_length_mm")
cohort_tip = dk.tip(f"The {n_all} Palmer penguins",
                    f"Adult Adélie, Chinstrap and Gentoo penguins measured at their nests on three islands near Palmer "
                    f"Station, Antarctica, in the {years[0]}–{years[-1]} breeding seasons (Gorman et al. 2014).",
                    f"{n_all - len(sexed)} have no recorded sex or body mass and are left out of the size slides.")
SRC = "Gorman et al. 2014, via the palmerpenguins package (Horst et al. 2020)"

deck = dk.Deck(TITLE, subtitle=(f"{n_all} adult penguins of three species, measured at their nests on three islands near Palmer "
                                f"Station, Antarctica, {years[0]}–{years[-1]}, and {dk.fint(len(recs))} GBIF records of the "
                               f"same species nearby. The reference deck for the wri-html-decks skill."),
               script="examples/penguin_deck_demo.py",
               sources=["Gorman, K.B., Williams, T.D., Fraser, W.R. (2014) Ecological sexual dimorphism and environmental "
                        "variability within a community of Antarctic penguins (genus <i>Pygoscelis</i>). PLoS ONE 9(3): e90081, "
                        "<a href=\"https://doi.org/10.1371/journal.pone.0090081\">doi:10.1371/journal.pone.0090081</a>. Palmer Station Antarctica LTER.",
                        "Data via Horst, A.M., Hill, A.P., Gorman, K.B. (2020) palmerpenguins, "
                        "<a href=\"https://doi.org/10.5281/zenodo.3960218\">doi:10.5281/zenodo.3960218</a> (CC0 1.0).",
                        f"GBIF.org occurrence records of the three species around Palmer Station (open licences only), fetched {gb['fetched']}: "
                        f"<a href=\"{gb['query_url']}\">the query</a>; each record's dataset and licence are kept with the data.",
                        "Site positions: SCAR Composite Gazetteer of Antarctica, Australian Antarctic Data Centre.",
                        dk.Frame.credit("imagery") + "."])

# %% 2️⃣ Section 1: the birds
# ============================================================
deck.section("The birds")
deck.cover()

grid = dk.waffle([{"label": lab[s], "n": by_sp[s], "color": SP[s]["hex"],
                   "tip": dk.tip(f"{lab[s]} penguins: {by_sp[s]} birds", f"One square per bird; {dk.fpct(by_sp[s] / n_all)} of the {n_all}.",
                                 "Islands: " + ", ".join(f"{i} {by_isl_sp[(i, s)]}" for i in islands_order if by_isl_sp[(i, s)]))}
                  for s in SP], per_row=24, cell=28, gap=6, unit_label="birds")
nums = dk.col(*[dk.number(str(by_sp[s]), f"{lab[s]} penguins", color=SP[s]["hex"], size=84,
                          tip=dk.tip(f"{lab[s]} ({SP[s]['latin']})", f"{by_sp[s]} adults measured, {dk.fpct(by_sp[s] / n_all)} of the {n_all}."))
                for s in SP], gap=28)
deck.slide("counts", f"{dk.term(str(n_all), cohort_tip)} penguins, measured at their nests", dk.row(nums, grid, widths=[420, 1]),
           lede=f"Three species on three islands, over three breeding seasons ({years[0]}–{years[-1]}).",
           info=("How to read it", "<p>One square is one bird, coloured by species. The numbers on the left count the same birds.</p>"),
           source=SRC)

# A still map per place, with GBIF records as species layers and the study site as a ring (Carlo, 2026-09-28: not a
# map you scroll around in the talk, but a picture with tabs and toggles, plus a link to the interactive map).
places = [("All three study sites", (-64.36, -64.86, -63.74, -64.70))] + \
         [(isl[k]["place"], (isl[k]["lon"] - .07, isl[k]["lat"] - .03, isl[k]["lon"] + .07, isl[k]["lat"] + .03)) for k in ("Biscoe", "Dream", "Torgersen")]
panes, counted = [], {}
for name, bounds in places:
    fr = dk.Frame(bounds, size=(1180, 640), pad=0.02)
    base = fr.basemap("imagery")
    layers, n_in = [], Counter()
    for s in SP:
        pts = []
        for r in recs:
            if latin[r["species"]] != s:
                continue
            x, y = fr.xy(r["decimalLongitude"], r["decimalLatitude"])
            if 0 <= x <= 1180 and 0 <= y <= 640:
                n_in[s] += 1
                pts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{SP[s]["hex"]}" stroke="#FFFFFF" stroke-width="1.5"/>')
        layers.append({"id": s, "svg": "".join(pts), "viewbox": "0 0 1180 640"})
    rings = []
    for k, v in isl.items():
        x, y = fr.xy(v["lon"], v["lat"])
        if 0 <= x <= 1180 and 0 <= y <= 640:
            here = sum(by_isl_sp[(k, s)] for s in SP)
            rings.append(f'<g data-tip="{dk.tip(v["place"], f"Palmer study site: {here} of the {n_all} birds were measured here.", "Position from the SCAR gazetteer, good to about a kilometre.")}">'
                         f'<circle cx="{x:.1f}" cy="{y:.1f}" r="18" fill="none" stroke="#FFFFFF" stroke-width="5"/>'
                         f'<text x="{x + 26:.1f}" y="{y + 8:.1f}" font-size="26" font-weight="700" fill="#FFFFFF" stroke="#172026" '
                         f'stroke-width="5" paint-order="stroke">{k}</text></g>')
    layers.append({"id": "sites", "svg": "".join(rings), "viewbox": "0 0 1180 640"})
    counted[name] = n_in
    panes.append({"label": name, "body": dk.image(base, width=1180, height=640, fit="cover", alt=f"Satellite image: {name}", layers=layers),
                  "tip": dk.tip(name, f"{sum(n_in.values())} GBIF records in this view: " + ", ".join(f"{lab[s]} {n_in[s]}" for s in SP) + ".")})
side = dk.col(dk.key([{"label": f"{lab[s]} records", "color": SP[s]["hex"], "swatch": "dot", "toggle": s,
                       "tip": dk.tip(f"{lab[s]} records", "Click to hide or show them on every tab.")} for s in SP]
                     + [{"label": "Palmer study site", "color": "#FFFFFF", "swatch": "ring", "toggle": "sites"}], title="Show"),
              dk.text("Each dot is one GBIF record of a penguin seen or collected there; each ring is where the Palmer birds were measured.", size=26),
              dk.spacer(), dk.link_button(LIVE_MAP, "Open the interactive map"), gap=24)
deck.slide("where", "Where they were measured, and who else saw them there",
           dk.row(dk.tabs(panes), side, widths=[1180, 1], gap=40),
           info=("About the map", "<p>Satellite base map with GBIF occurrence records (open licences only) and the three Palmer "
                                  "study sites. The tabs zoom to each site; the key turns each species on and off. Records are "
                                  "where a bird was seen or collected, not colony counts.</p>"),
           source=f"GBIF.org records fetched {gb['fetched']} · site positions: SCAR gazetteer · {dk.Frame.credit('imagery')}")

rows = [{"label": i, "values": [by_isl_sp[(i, s)] for s in SP],
         "tips": [dk.tip(f"{lab[s]} on {i}: {by_isl_sp[(i, s)]} birds",
                         f"{dk.fpct(by_isl_sp[(i, s)] / sum(by_isl_sp[(i, t)] for t in SP))} of the birds measured on {i}.") for s in SP],
         "label_tip": dk.tip(isl[i]["place"], f"{sum(by_isl_sp[(i, s)] for s in SP)} birds measured here.")} for i in islands_order]
only_all = [lab[s] for s in SP if all(by_isl_sp[(i, s)] for i in islands_order)]
deck.slide("islands", f"Only {' and '.join(only_all)} penguins were measured on all three islands",
           dk.col(dk.key([{"label": lab[s], "color": SP[s]["hex"]} for s in SP], title="Species"),
                  dk.hbar(rows, [{"name": lab[s], "color": SP[s]["hex"]} for s in SP], width=1500, label_w=260, bar_h=30)),
           info=("Why this matters", "<p>Species and island are tangled: comparing islands mostly compares species. Later slides "
                                     "compare sexes within each species instead.</p>"),
           source=SRC)

# %% 3️⃣ Section 2: size
# ============================================================
deck.section("Size")
mrows, gaps = [], []
for s in SP:
    vals, tips_, after_ = [], [], []
    for sx in ("female", "male"):
        xs = mass[(s, sx)]
        lo, hi = boot_ci(xs)
        vals.append(round(st.fmean(xs)))
        after_.append(f"n = {len(xs)}")
        tips_.append(dk.tip(f"{lab[s]} {sx}s: {dk.fint(st.fmean(xs))} g on average", f"Mean of {len(xs)} birds.",
                            meaning=f"{'heavier' if sx == 'male' else 'lighter'} than the other sex of the same species",
                            tech=[f"mean {st.fmean(xs):.0f} g, sd {st.stdev(xs):.0f} g, n {len(xs)}",
                                  f"95% bootstrap interval {lo:.0f}–{hi:.0f} g ({N_BOOT} resamples of birds, seed {SEED})"]))
    gaps.append(vals[1] - vals[0])
    mrows.append({"label": lab[s], "values": vals, "tips": tips_, "after": after_})
deck.slide("mass", "Males are heavier than females in every species",
           dk.col(dk.key([{"label": "Females", "color": SEX_C["female"]}, {"label": "Males", "color": SEX_C["male"]}], title="Sex"),
                  dk.hbar(mrows, [{"name": "Female", "color": SEX_C["female"]}, {"name": "Male", "color": SEX_C["male"]}],
                          width=1400, label_w=260, fmt=lambda v: f"{v:,.0f}", unit=" g", value_w=260),
                  dk.note("The gap is " + dk.term(f"{min(gaps)}–{max(gaps)} g", dk.tip("Male minus female average body mass",
                          ", ".join(f"{lab[s]} {g_} g" for s, g_ in zip(SP, gaps)) + ".")) + ", depending on the species.",
                          title="The difference:")),
           info=("How it was calculated", "<p>Average body mass of the birds with a recorded sex and mass. Switch to "
                                         "<b>Technical</b> for the spread and a bootstrap interval in each bar's hover.</p>"),
           source=SRC)

drows = []
for s in SP:
    for k, sx in enumerate(("female", "male")):
        xs = flip[(s, sx)]
        lo, hi = boot_ci(xs)
        drows.append({"label": f"{sx.capitalize()}s", "value": st.fmean(xs), "low": lo, "high": hi, "color": SEX_C[sx],
                      "group": lab[s] if k == 0 else None,
                      "tip": dk.tip(f"{lab[s]} {sx}s: {st.fmean(xs):.1f} mm", f"Average flipper length of {len(xs)} birds; the bar is the 95% interval.",
                                    tech=[f"95% bootstrap interval {lo:.1f}–{hi:.1f} mm ({N_BOOT} resamples of birds, seed {SEED})"])})
deck.slide("flippers", "Flipper length separates the species more than the sexes",
           dk.dots(drows, width=1500, label_w=300, fmt=lambda v: f"{v:.0f}", unit=" mm", row_h=58,
                   axis_label="Average flipper length (mm), with 95% interval"),
           info=("How to read it", "<p>Each dot is an average; the line through it is where the true average plausibly lies "
                                   "(a 95% bootstrap interval from resampling the birds).</p>"),
           source=SRC)

bins = list(range(2500, 6501, 250))
series, tips_l = [], []
for s in SP:
    xs = [b["body_mass_g"] for b in birds if b["species"] == s and b["body_mass_g"] is not None]
    cnt = [sum(1 for x in xs if lo_ <= x < lo_ + 250) for lo_ in bins]
    series.append({"name": lab[s], "color": SP[s]["hex"], "values": cnt})
    tips_l.append([dk.tip(f"{lab[s]}: {c} birds", f"Body mass {lo_:,}–{lo_ + 249:,} g.") for c, lo_ in zip(cnt, bins)])
deck.slide("spread", "Gentoo are heavier than the other two species, with little overlap",
           dk.lines(bins, series, width=1560, height=600, x_labels=[f"{b / 1000:.2g}" for b in bins], y_label="Birds per 250 g",
                    tips=tips_l, y_min=0, label_at="max"),
           lede="Birds in each " + dk.term("250 g band", dk.tip("Bands of 250 g", "2,500–2,749 g, 2,750–2,999 g and so on; "
                                                                 "each point counts the birds in one band.")) + " of body mass (kg on the axis).",
           info=("How it was made", "<p>Each point counts the birds of one species whose body mass falls in a 250 g band.</p>"),
           source=SRC)

pts, fits_ = [], []
allx = [b["bill_length_mm"] for b in birds if b["bill_length_mm"] and b["bill_depth_mm"]]
ally = [b["bill_depth_mm"] for b in birds if b["bill_length_mm"] and b["bill_depth_mm"]]
r_all = corr(allx, ally)
b_, a_ = fit(allx, ally)
fits_.append({"x0": min(allx), "y0": a_ + b_ * min(allx), "x1": max(allx), "y1": a_ + b_ * max(allx), "color": "#172026", "dash": True,
              "label": "All birds", "layer": "all",
              "tip": dk.tip("All birds together", f"Correlation {r_all:+.2f}: longer bills look shallower.",
                            meaning="a pattern that comes from mixing species", tech=[f"least-squares slope {b_:+.3f} mm per mm, n {len(allx)}"])})
r_sp = {}
for s in SP:
    xs = [b["bill_length_mm"] for b in birds if b["species"] == s and b["bill_length_mm"] and b["bill_depth_mm"]]
    ys = [b["bill_depth_mm"] for b in birds if b["species"] == s and b["bill_length_mm"] and b["bill_depth_mm"]]
    r_sp[s] = corr(xs, ys)
    bb, aa = fit(xs, ys)
    pts += [{"x": x, "y": y, "color": SP[s]["hex"], "layer": s, "tip": dk.tip(f"{lab[s]}", f"Bill {x:.1f} mm long, {y:.1f} mm deep.")}
            for x, y in zip(xs, ys)]
    fits_.append({"x0": min(xs), "y0": aa + bb * min(xs), "x1": max(xs), "y1": aa + bb * max(xs), "color": SP[s]["edge"], "layer": s,
                  "tip": dk.tip(f"{lab[s]} only", f"Correlation {r_sp[s]:+.2f}: within this species, longer bills are deeper.",
                                tech=[f"least-squares slope {bb:+.3f} mm per mm, n {len(xs)}"])})
flips = r_all < 0 and all(v > 0 for v in r_sp.values())
deck.slide("bills", ("Mixed together, longer bills look shallower; within each species they are deeper" if flips
                     else "Bill length and depth by species"),
           dk.row(dk.scatter(pts, width=1000, height=640, x_label="Bill length (mm)", y_label="Bill depth (mm)", fits=fits_),
                  dk.col(dk.key([{"label": lab[s], "color": SP[s]["hex"], "swatch": "dot", "toggle": s} for s in SP]
                                + [{"label": "All birds (fit)", "color": "#172026", "swatch": "line", "toggle": "all"}], title="Show"),
                         dk.note("All birds: correlation " + dk.term(f"{r_all:+.2f}", dk.tip("Pearson correlation, all birds",
                                 f"Bill length against bill depth for the {len(allx)} birds with both measured.")) + ". Within species: "
                                 + ", ".join(lab[s] + " " + dk.term(f"{r_sp[s]:+.2f}", dk.tip(f"Pearson correlation, {lab[s]} only",
                                             "Bill length against bill depth within this species.")) for s in SP) + ".",
                                 title="Simpson's paradox."), gap=24),
                  widths=[1000, 1], gap=48),
           info=("Why the sign flips", "<p>The species differ in both bill length and depth, so pooling them draws a line between "
                                       "species, not within them. Turn the species off one by one to see each fit.</p>"),
           source=SRC)

# %% 4️⃣ Section 3: the records and what they show
# ============================================================
deck.section("What it shows")
yr = defaultdict(list)
for r in recs:
    if r["year"]:
        yr[latin[r["species"]]].append(r["year"])
srows = [{"label": "Palmer study", "from": years[0], "to": years[-1] + 1, "color": "#172026",
          "tip": dk.tip("The Palmer study", f"{n_all} birds measured in {len(years)} breeding seasons, {years[0]}–{years[-1]}."),
          "note": f"{n_all} birds, {years[0]}–{years[-1]}"}]
for s in SP:
    ys = sorted(yr[s])
    srows.append({"label": f"{lab[s]} records", "from": ys[0], "to": ys[-1] + 1, "color": SP[s]["hex"],
                  "tip": dk.tip(f"GBIF {lab[s]} records", f"{dk.fint(len(ys))} dated records, {ys[0]}–{ys[-1]}; "
                                f"{dk.fpct(sum(1 for y in ys if y >= 2000) / len(ys))} since 2000."),
                  "note": f"{dk.fint(len(ys))} dated records, {ys[0]}–{ys[-1]}"})
y0 = min(min(v) for v in yr.values())
deck.slide("records", "Three seasons of measurements, a century of sightings",
           dk.spans(srows, start=(y0 // 10) * 10, end=2030, width=1664, label_w=330),
           info=("What each record is", "<p>The Palmer study measured birds in hand. GBIF records are sightings and specimens "
                                        "from many datasets; most are recent.</p>"),
           source=f"Gorman et al. 2014 · GBIF.org, fetched {gb['fetched']}")

trows, ttips = [], []
for s in SP:
    for sx in ("female", "male"):
        sel = [b for b in birds if b["species"] == s and b["sex"] == sx]
        def m(f):
            v = [b[f] for b in sel if b[f] is not None]
            return round(st.fmean(v), 1)
        trows.append([lab[s], sx, len(sel), round(st.fmean([b["body_mass_g"] for b in sel if b["body_mass_g"]])),
                      m("flipper_length_mm"), m("bill_length_mm"), m("bill_depth_mm")])
        ttips.append([None, None, dk.tip(f"{len(sel)} birds", f"{lab[s]} {sx}s with a recorded sex."), None, None, None, None])
deck.slide("table", "The averages in one table",
           dk.table(["Species", "Sex", "Birds", "Body mass (g)", "Flipper (mm)", "Bill length (mm)", "Bill depth (mm)"], trows,
                    numeric=[2, 3, 4, 5, 6], shade={"cols": [3], "scale": "blues"}, tips=ttips, size=30,
                    col_tips=[None, None, dk.tip("Birds", "Birds of this species and sex with a recorded sex."),
                              dk.tip("Body mass", "Average in grams; shaded from lighter (less) to darker (more)."),
                              dk.tip("Flipper", "Average flipper length in millimetres."),
                              dk.tip("Bill length", "Average bill (culmen) length in millimetres."),
                              dk.tip("Bill depth", "Average bill (culmen) depth in millimetres.")]),
           info=("How to read it", "<p>Averages per species and sex. Body mass is shaded so the heaviest groups stand out.</p>"),
           source=SRC)

deck.slide("how", "How this deck was made",
           dk.col(dk.spacer(), dk.steps([{"title": "Get the data", "text": "Downloaded once, with the date", "icon": "database"},
                                         {"title": "Compute", "text": "Every number from the files", "icon": "code"},
                                         {"title": "Build", "text": "One idea per slide", "icon": "layers"},
                                         {"title": "Check", "text": "Pictures of every slide", "icon": "listcheck"},
                                         {"title": "Publish", "text": "Same link on every update", "icon": "globe"}],
                                        color="#4A7A3A", size=30), dk.spacer(), flex=1),
           info=("The skill", "<p>Built with the wri-html-decks skill (NCEAS-AI Coding-Agent Skills for Data Science).</p>"))

isl_m = {i: st.fmean([b["body_mass_g"] for b in birds if b["species"] == "Adelie" and b["island"] == i and b["body_mass_g"]]) for i in islands_order}
sp_m = {s: st.fmean([b["body_mass_g"] for b in birds if b["species"] == s and b["body_mass_g"]]) for s in SP}
d_isl, d_sp = max(isl_m.values()) - min(isl_m.values()), max(sp_m.values()) - min(sp_m.values())
deck.statement("pitch", "Species, more than island, sets a penguin's size" if d_sp > 3 * d_isl else "Species and island both matter",
               sub=("Adélie averages differ by " + dk.term(f"{d_isl:.0f} g", dk.tip("Adélie, island to island", ", ".join(f"{i} {v:.0f} g" for i, v in isl_m.items())))
                    + " between islands; the species averages differ by " + dk.term(f"{d_sp:,.0f} g", dk.tip("Species to species", ", ".join(f"{lab[s]} {v:.0f} g" for s, v in sp_m.items())))
                    + "."),
               info=("How it was calculated", f"<p>Average body mass of Adélie penguins on each island ({', '.join(f'{i} {v:.0f} g' for i, v in isl_m.items())}) "
                                              f"against the average of each species ({', '.join(f'{lab[s]} {v:.0f} g' for s, v in sp_m.items())}).</p>"))

# %% 5️⃣ Write
# ============================================================
# DECK_PREVIOUS: the published deck (publish.py --pull), so the start date and change history carry over
path = deck.write(OUT, previous=os.environ.get("DECK_PREVIOUS"), change=os.environ.get("DECK_CHANGE", "Deck archetype: first version"))
print(path)
