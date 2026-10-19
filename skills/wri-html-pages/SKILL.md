---
name: wri-html-pages
description: "Make every data visualization as an HTML page in the WRI / NCEAS house style, publish it automatically to the team's GitHub Pages site (WRI-Science/public_publication unless identity.json names another, in the project's folder) and give the link, without being asked to push. Use whenever the user asks for any data visualization at all: a chart, graph, plot, figure, map, heatmap, table, dashboard, infographic, comparison, trend or distribution, or says show me, visualize, plot, chart or map any data, results, metrics, validation or exploratory analysis. Covers interactive scrollable maps (MapLibre: points, lines, polygons and rasters, e.g. fires, structures, survey sites, species records, model calls), chart pages (bars, columns, lines, heatmap tables, stat tiles, tables) and chart pages with a map panel. Also use when the user critiques or updates an existing map or chart page, or asks for the link to one."
license: CC0-1.0 for code and text; the NCEAS and WRI logos in assets/ are not covered (see README.md)
compatibility: Python 3.10+ and git with push access to a GitHub Pages repo (set in references/identity.json). Screenshots need Chrome or Chromium and websocket-client; maps from vector or raster files need geopandas or rasterio; the optional PIN gate needs cryptography. Map tiles and libraries load from the internet.
metadata:
  version: "1.9.0"
  author: "Carlo Broderick (NCEAS, UC Santa Barbara)"
  source: "https://github.com/NCEAS-AI/Coding-Agent-Skills-for-Data-Science"
---

# wri-html-pages: maps and chart pages in our house style, published by link

Version 1.9.0 (2026-10-19). Every page made with this skill looks and behaves the same way, works on
a phone and a desktop, carries a short dated title with a detailed subtitle, says who made it and when,
and ends up at a link collaborators can open.

`SKILL` below means this skill's base directory (printed when the skill loads; normally
`~/.claude/skills/wri-html-pages`). Commands are written as `python3 $SKILL/scripts/...`.

## Automatic: every visualization is built, published and linked (Carlo, 2026-10-12)

Any request for a data visualization, of any kind, goes all the way through without further asks:
build the page, check it, **publish it to GitHub automatically** (do not ask whether to push), and give
the link. Pages are filed on the team's GitHub Pages site, set in identity.json (`github.pages_repo`;
for the WRI team, `WRI-Science/public_publication`), under
`publication_htmls/<project folder>/`: use the project's existing folder (structure_loss_pipeline,
de_space_canopy_validation, …) or create a snake_case folder for a new project, and say in one line
which folder it went to. Ask only if it is genuinely unclear which project the page belongs to. Pages are
open (no PIN) unless the user asks for a PIN gate.

**Except private data.** If the user has said data are private, under embargo, personal, or
licensed for internal use only (on the WRI team: anything built from Overture data), don't publish a page
that shows them openly: build it locally, say why in one line, and ask (keep it local, or PIN-gate it if
the user says that is enough). When in doubt about a dataset's licence, check before publishing.

## Work iteratively on one living page (Carlo, 2026-10-12)

Most of the time we explore one analysis over many requests. **By default a new visualization is added
to the current page, not made as a new HTML:** new panels go on top, older ones move down, and each panel
shows when it was added (and updated). Remove a panel when it becomes obsolete, turns out wrong, or is no
longer needed; the page history at the foot records what was removed and why. Fix a wrong panel by
updating it (same id) or replacing it. Start a **new page** only for a genuinely different analysis or
topic, or when the user asks for one.

- The current page is the one being worked on in this conversation, or the most recent for this project
  in `publish.py --links`. In a new session, fetch it with `publish.py --pull FILE --folder F --to PATH`.
- Build with `vk.living_page(existing, add=[vk.panel(..., id="short-id")], remove={"id": "why"})`
  (charts.md, "Living pages"). The file name and title keep the page's start date; the byline shows when
  it was started and last updated.

## The link goes in every reply (Carlo, 2026-10-12)

While a page is being worked on, **every reply that has anything to do with it ends with a clickable link
to its live, newest version**, unasked, so the user never has to ask for the link or scroll up for it:

```
[Short title · YYYY-MM-DD](https://wri-science.github.io/public_publication/publication_htmls/<folder>/<file>.html)
```

- Link the version that was just published or edited, or the one being discussed; each dated version has
  its own URL, so make sure it is the newest one (not an earlier day's page) unless the user asks about
  an older one. Several pages in play → one line each.
- If an edit is not published yet, say so in a few words and link the current live version.
- Lost track? `python3 $SKILL/scripts/publish.py --links [--folder F]` prints the latest link per page.
- This holds for the rest of the conversation, not only the turn that published the page.

## Read first

1. `references/house-style.md`: the standing preferences for every page (titles, audience, numbers,
   hovers, colours, layout, maps) with the reason for each. It is short; read all of it.
2. Then the guide for the job:
   - a map someone can pan and zoom → `references/maps.md` (spec fields: `references/map-spec.md`)
   - a chart page with a map as one of its panels → `references/charts.md` ("Map panels"), same map spec
   - anything else visual (charts, tables, tiles, explainers) → `references/charts.md`
   - putting any page online and giving the link → `references/publishing.md` (always the last step)
   - **before publishing any panel → `references/rigor.md`** (the rigor pass; every panel, every time)

## The workflow in one screen

1. **Compute everything from real data files.** The page script reads the data and builds every
   number, caption and the title from it. Never typed-in numbers, never demo data.
2. **Title and subtitle:** a short, specific title ending in the date
   (`"Penguin records around Palmer Station · 2026-10-13"`; `vk.today()` gives the date in the team's time zone)
   and a subtitle with the detail
   (place, dates, cohort and counts, split, what is new in this iteration). The title's slug is the file name.
3. **Add to the current page** (living_page) unless this is a new analysis; then **build** with the scripts: maps with `scripts/build_map.py` from a JSON spec, charts with
   `scripts/vizkit.py`. Both add the byline (author, Pacific build time), the NCEAS / WRI logos and
   GitHub links, the WRI flame as tab icon and link-preview image, and record the generation time in the file.
4. **Rigor pass, panel by panel** (`references/rigor.md`): like-for-like periods and populations (no partial
   year next to full ones), right denominators, heavy tails and single-event dominance, uncertainty from the
   independent unit, small n, how the data were made, honest encoding, claims that match the evidence.
   Fix the design rather than caveat it; record what was checked with `vk.card(..., checks=[...])`. A panel
   that can't pass is redesigned or replaced by an honest "can't tell yet".
5. **Look at it:** `python3 $SKILL/scripts/screenshot.py PAGE.html /tmp/shot` (desktop + phone; JS errors
   and a page that scrolls sideways on a phone are reported). Fix overlaps, clipped text, buried
   classes, empty charts. For each chart, choose its phone
   layout case by case (fit, frozen-pane scroll, or cards: charts.md, "Phone layout").
6. **Publish:** `python3 $SKILL/scripts/publish.py --folder FOLDER PAGE.html` (dry run), then with
   `--execute --wait -m "..."`. It checks the page, updates the READMEs, pushes, and waits until the
   link is live. Pages are **open by default**; add `--gate` (PIN) only when the user asks for it.
7. **Hand over the link:** end the reply with the `[title](live URL)` line(s) publish.py prints, each
   followed by the page's subtitle, and keep linking it in every later reply about it (above).

## What is in this skill

| Path | What it is |
|---|---|
| `scripts/build_map.py` + `assets/map_template.html` | spec → interactive map page (MapLibre GL JS 5.24.0) |
| `scripts/raster_to_png.py` | GeoTIFF → coloured, Web-Mercator PNG overlay for a map |
| `scripts/vizkit.py` | chart page building blocks (page shell, tiles, bars, columns, lines, heatmaps, tables, map panels, tooltips) |
| `scripts/screenshot.py` | headless Chrome captures at desktop and phone size, with JS errors |
| `scripts/check_page.py` | pre-publish checks (dated title, no local paths, links resolve, no `cursor: help`, size) |
| `scripts/publish.py` | publish to the GitHub Pages site in identity.json (WRI-Science/public_publication) and confirm the live link |
| `scripts/pin_gate.py` | encrypt or decrypt a page behind the site PIN (only when the user asks) |
| `references/identity.json` | author, affiliation, time zone, logos and links, GitHub org and the publishing site (the WRI team's). A personal copy at `~/.config/wri-html-pages/identity.json` (or `$WRI_HTML_PAGES_IDENTITY`) wins and survives updates |
| `references/house-style.md` | the preferences every page follows |
| `examples/` | the archetype pages' build scripts (public data; `examples/README.md` lists the files they read) |

The archetypes these produce are the reference look:
- Map: https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/map-archetype-penguin-records-around-palmer-station-2026-10-13.html
- Charts: https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/chart-archetype-palmer-penguins-size-species-sex-2026-10-15.html
- A page built over several requests: https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/exploration-archetype-palmer-penguins-built-step-step-2026-10-15.html

## When the user critiques a page

Change that page's script or spec. If the critique is a general preference, also change
`references/house-style.md` and the template or vizkit, rebuild the archetype from `examples/`,
and republish it so it stays the reference.
