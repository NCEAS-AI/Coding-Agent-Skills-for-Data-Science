#!/usr/bin/env python3
"""Archetype living page: a penguin exploration built up over three requests, newest panel on top.

WHY THIS EXISTS
    The reference for iterative work with the wri-html-pages skill. Each "step" below is what one request in a
    working session does: read the current page, add panels on top, update or remove old ones (with a reason),
    write it back. Every panel shows when it was added; removed panels are listed in the page history. Step 3
    is also a rigor fix: "body mass by island" compares species, not islands (Gentoo, the heaviest, were measured
    only on Biscoe), so it is replaced by island comparisons within one species. Open data only (Palmer
    Penguins, CC0; penguin_data.py downloads it once).

RUN (needs pandas and numpy)
    python3 penguin_living_demo.py OUT_DIR
    -> OUT_DIR/<dated title slug>.html
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import penguin_data as P  # noqa: E402
import vizkit as vk  # noqa: E402

# ============================================================================ settings
BOOT, SEED = 4000, 20261013
C_ISLAND, C_F, C_M = "var(--s7)", "var(--s1)", "var(--s5)"
SP = {k: v["label"] for k, v in P.SPECIES.items()}
# ============================================================================

out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=True)
d = pd.DataFrame(P.penguins())
d["season"] = d.year.map(lambda y: f"{y}–{str(y + 1)[-2:]}")
m = d.dropna(subset=["body_mass_g"])
seasons = sorted(d.season.unique())
rng = np.random.default_rng(SEED)
title = f"Exploration archetype: Palmer penguins, built step by step · {vk.today()}"
page_path = out / f"{vk.slug(title)}.html"
season_tip = vk.tip("Breeding season", "Southern summer, November to January.", tech="palmerpenguins `year` = first year of the season.")


def boot_ci(x):
    x = np.asarray(x, float)
    b = x[rng.integers(0, len(x), size=(BOOT, len(x)))].mean(1)
    return np.percentile(b, [2.5, 97.5])


# ---------------- step 1: the first request starts the page with two panels
ct = d.groupby(["season", "species"]).size().unstack(fill_value=0).reindex(seasons)
p_seasons = vk.panel(
    vk.columns(seasons, [{"name": SP[k], "color": P.SPECIES[k]["var"], "values": ct[k].tolist(),
                          "tip": vk.tip(SP[k], P.SPECIES[k]["latin"])} for k in SP],
               tips=[vk.tip(s, f"{int(r.sum())} penguins", ", ".join(f"{SP[k]} {int(r[k])}" for k in SP)) for s, r in ct.iterrows()],
               x_title="Breeding season", y_title="Penguins measured", x_tip=season_tip,
               y_tip=vk.tip("Penguins measured", "Birds measured at their nests; set by the study design.")),
    title="Penguins measured each season", id="per-season",
    caption="About 110–120 penguins each season, all three species every time.",
    checks=["Counts of birds measured (study design), not population sizes."])
isl_rows = []
for isl, g in m.groupby("island"):
    x = g.body_mass_g / 1000
    lo, hi = boot_ci(x)
    isl_rows.append({"label": isl, "sub": f"{len(g)} birds", "v": x.mean(), "values": {"mass": {
        "v": x.mean(), "lo": lo, "hi": hi, "tip": vk.tip(isl, f"average {x.mean():.2f} kg ({len(g)} birds)")}}})
isl_rows.sort(key=lambda r: -r["v"])
p_island = vk.panel(
    vk.hbar(isl_rows, [{"key": "mass", "name": "Average body mass", "color": C_ISLAND}], unit=" kg", decimals=2,
            domain=(0, 6), axis_title="Average body mass", show_legend=False,
            axis_tip=vk.tip("Average body mass", "All birds measured on the island, any species.")),
    title="Average body mass by island", id="mass-by-island",
    caption="Penguins on Biscoe are the heaviest.",
    checks=["Bootstrap intervals over birds."])
html = vk.living_page(None, title=title,
                      subtitle="A living page: each request adds its panels on top, every panel shows when it was added, and "
                               "panels taken off are listed in the page history at the foot. Data: the "
                               f"{len(d)} Palmer Archipelago penguins, {seasons[0]} to {seasons[-1]}.",
                      eyebrow="Exploration archetype · open ecological data",
                      sources=["Gorman, K.B., Williams, T.D., Fraser, W.R. (2014) PLoS ONE 9(3): e90081, "
                               "<a href=\"https://doi.org/10.1371/journal.pone.0090081\">doi:10.1371/journal.pone.0090081</a>; "
                               "data via palmerpenguins, <a href=\"https://doi.org/10.5281/zenodo.3960218\">doi:10.5281/zenodo.3960218</a> "
                               "(CC0 1.0)."],
                      footer="Made with the wri-html-pages skill: examples/penguin_living_demo.py.",
                      add=[p_seasons, p_island])
page_path.write_text(html)
time.sleep(2)

# ---------------- step 2: a later request adds a panel; it goes on top
sexed = m.dropna(subset=["sex"])
rows = []
for k in SP:
    vals = {}
    for sx, key in (("female", "f"), ("male", "m")):
        x = sexed[(sexed.species == k) & (sexed.sex == sx)].body_mass_g / 1000
        lo, hi = boot_ci(x)
        vals[key] = {"v": x.mean(), "lo": lo, "hi": hi, "tip": vk.tip(f"{SP[k]} · {sx}s", f"average {x.mean():.2f} kg ({len(x)} birds)",
                                                                       f"Range we can trust: {lo:.2f}–{hi:.2f} kg")}
    rows.append({"label": SP[k], "values": vals})
p_species = vk.panel(
    vk.hbar(rows, [{"key": "f", "name": "Females", "color": C_F}, {"key": "m", "name": "Males", "color": C_M}],
            unit=" kg", decimals=2, domain=(0, 6), axis_title="Average body mass",
            axis_tip=vk.tip("Average body mass", "Weight at the nest, kilograms; bars start at zero.")),
    title="Body mass by species and sex", id="mass-species-sex",
    caption=vk.dual("Gentoo are much heavier than the other two species, and males outweigh females in all three.",
                    f"Means with 95% percentile bootstrap intervals, {BOOT} resamples within species × sex."),
    checks=["Within a species and sex each bird is from a different nest, so birds are independent.",
            f"{len(m) - len(sexed)} birds of unknown sex left out."])
page_path.write_text(vk.living_page(page_path, add=[p_species]))
time.sleep(2)

# ---------------- step 3: replace the misleading island panel with island comparisons within one species
ad = m[m.species == "Adelie"]
cells, isl_order = [], ["Biscoe", "Dream", "Torgersen"]
for isl in isl_order:
    x = ad[ad.island == isl].body_mass_g / 1000
    lo, hi = boot_ci(x)
    cells.append({"label": isl, "sub": f"{len(x)} Adélie", "values": {"a": {
        "v": x.mean(), "lo": lo, "hi": hi, "tip": vk.tip(f"Adélie on {isl}", f"average {x.mean():.2f} kg ({len(x)} birds)",
                                                       f"Range we can trust: {lo:.2f}–{hi:.2f} kg")}}})
spread = max(c["values"]["a"]["v"] for c in cells) - min(c["values"]["a"]["v"] for c in cells)
p_within = vk.panel(
    vk.hbar(cells, [{"key": "a", "name": "Adélie", "color": P.SPECIES["Adelie"]["var"]}], unit=" kg", decimals=2, domain=(0, 6),
            axis_title="Average body mass of Adélie penguins", show_legend=False,
            axis_tip=vk.tip("Average body mass", "Adélie only: the one species measured on all three islands.")),
    title="Body mass by island, within one species", id="mass-island-adelie",
    caption=vk.dual(f"Compared like for like, Adélie penguins weigh about the same on all three islands (averages within "
                    f"{spread * 1000:.0f} g, intervals overlapping). Biscoe looked heavy only because the Gentoo live there.",
                    f"Adélie means by island with 95% bootstrap intervals; max − min = {spread * 1000:.0f} g."),
    checks=["Like for like: one species (Adélie, the only one on all three islands).",
            "Bootstrap intervals over birds; bars start at zero; same axis as the panel above."])
page_path.write_text(vk.living_page(page_path, add=[p_within], remove={
    "mass-by-island": "it compared species, not islands: Gentoo, the heaviest, were measured only on Biscoe; replaced by "
                      "'Body mass by island, within one species'"}))
print("wrote", page_path)
