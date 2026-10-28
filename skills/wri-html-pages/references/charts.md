# Charts: chart pages in our house style

Pages we share should read as one system: same type, colours, keys, tooltips, "how to read" box and
footer, and they must work on a phone. This skill builds them with `scripts/vizkit.py` (plain
HTML/CSS + one tiny tooltip script, no chart library) and publishes them (`references/publishing.md`).

## Before writing anything

1. Read `references/house-style.md`. It is the team's standing preferences (audience, numbers,
   hovers, colours, layout) with the reason for each. It applies to maps too.
2. Look at the archetype, which shows every component in use:
   `examples/penguin_chart_demo.py` → https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/chart-archetype-palmer-penguins-size-species-sex-2026-10-27.html
   When the user says "like the archetype but …", start from that script.

## Workflow

1. **Get the numbers from files the pipeline wrote.** The page script reads the data and computes
   every number it prints. No typed-in values, no demo data. Note the exact cohort (which fires,
   which years, which cut) because the page must name it.
2. **Write one page script** (in the project repo, e.g. `scripts/pages/<topic>_page.py`, or the
   scratchpad for a one-off) that imports vizkit:
   ```python
   import sys; sys.path.insert(0, "SKILL/scripts")   # SKILL = this skill's base directory
   import vizkit as vk
   ```
   Decide the concept → colour mapping first (`C_BURNED = "var(--s4)"` …) and use it on every chart.
3. **Title and subtitle** (house-style.md, "Titles, subtitles and links"): a short, specific title with
   the date at the end, `f"Penguin body mass by species and sex · {vk.today()}"` (vk.today(): the date in the team's time zone), and a subtitle built
   from the data with the detail (cohort, size, years, measure, split, what is new in this iteration).
   Write the page with `vk.write_page(OUT_DIR / f"{vk.slug(title)}.html", page)` (not `write_text`: it also writes each
   panel's own page), so the file name and link carry the title.
4. **Arrange the page:** `vk.page(title, body, subtitle=, eyebrow=, lede=, how_to_read=, tiles=, sources=, footer=)`
   with `vk.section(...)` blocks, each holding `vk.card(chart, title=, caption=)`.
5. **Check it renders** at phone and desktop width (see "Screenshots" below) and look at the images:
   overlapping text, clipped labels, empty charts, and unreadable phone layouts are the usual faults.
6. **Publish** (`references/publishing.md`; it runs the pre-publish checks, gates if needed, pushes,
   and confirms the live link). End the reply with the `[title](live URL)` line it prints.

## Components (vizkit)

| Function | Use for | Notes |
|---|---|---|
| `stat_tiles([{value, label, sub, tip}])` | headline numbers under the lede | value is pre-formatted text |
| `hbar(rows, series, unit="%", ref=, ref_label=, domain=)` | comparisons across groups; one or several series per row | value printed at bar end; `lo`/`hi` draw a CI whisker; `ref` draws a dashed line; stacks labels on phones |
| `columns(labels, series, tips=)` | counts over time or ordered groups | stacked when several series; value labels when ≤12 columns |
| `line_chart(x, series, tips=, ref=, phone=)` | trends, several series | SVG; `phone="fit"` (narrow redraw) or `"scroll"` |
| `heatmap(rows, cols, cells, ramp=, domain=, row_groups=, extra_cols=, extra=, phone=)` | two-way tables (state × year, decile × region) | cell = big number + small number; `{"empty": True}` greys a cell with too few cases; `phone="scroll"` or `"cards"` |
| `ramp_key(lo, hi, ramp, empty_label=)` | key above a heatmap | |
| `map_panel(spec, base=, height=, name=, standalone_spec=)` | an interactive map as one panel of the page, plus the same map as its own page | same spec as a standalone map (map-spec.md); see "Map panels" and "Every panel has its own page" below |
| `write_page(dest, page_html)` | write the page and the panel pages beside it | use it instead of `dest.write_text(page)` |
| `table(cols, rows, numeric=, phone=, shade=, col_tips=)` | exact values, top-N lists | right-aligns numeric columns; `phone="scroll"` or `"cards"` |
| `legend(items)`, `note(title, html)`, `card(..., checks=[...])`, `section(...)` | layout pieces | `checks` = the rigor pass for that panel (rigor.md), shown as "How this panel was checked" |
| `tip("Heading", "line", ..., meaning=, tech=)` | the `data-tip` text for any element | first line bold; `meaning` adds "What it suggests: …" (plain); `tech` is the technical version |
| `dual(plain, technical, block=)` | captions, notes, ledes with two versions | the card (or note, section, header) holding it gets its own Plain / Technical switch |
| `shade_key(lo, hi, scale=, better=, flag=, tip=, flag_tip=)` | key above a shaded table | |
| `fint`, `fpct`, `fnum`, `ramp_color`, `RAMPS`, `SERIES` | formatting and colour | `fpct(0.123) → "12%"` |
| `slug(title)` | the file name from the short dated title | `"Penguin records · 2026-10-13" → "penguin-records-2026-10-13"` |

Something vizkit lacks (scatter, flow diagram, small multiples)? Write the HTML/SVG by hand inside a
`vk.card`, using the CSS variables (`var(--ink)`, `var(--line)`, `var(--s1)`…) so both themes work,
and `data-tip` for hovers. If it will be needed again, add it to vizkit and to the archetype.

## Living pages (the default for iterative work)

```python
html = vk.living_page(existing,                     # path or HTML of the current page (publish.py --pull), or None to start
                      title="Short title · 2026-10-12",   # only when starting; kept afterwards
                      subtitle=..., eyebrow=..., sources=[...],   # page settings; kept unless passed again
                      add=[vk.panel(chart_html, title="…", id="burned-per-year", caption=..., checks=[...])],
                      remove={"mean-per-fire": "why it came off the page"})
vk.write_page(path, html)                           # the page plus panels/<page-slug>/ (not path.write_text)
```
- New panels go on top, in the order given; a panel whose `id` is already on the page is updated in place
  ("Added … · updated …"). Give every panel a short explicit `id`.
- `remove` takes panels off and records the reason in the page history; nothing is deleted silently.
- The page carries its own panels and settings (a JSON block in the head), so any session can pull the
  published page and continue. Example: `examples/penguin_living_demo.py` (three requests in a row).
- A one-off page with a fixed story (like the chart archetype) can still use `vk.page` with sections.

## Explaining every part (hover tips, plain and technical)

Every component takes tips: bars and points (`"tip"` in their dicts), series (`"tip"` → legend entry),
axes (`x_title`/`y_title` with `x_tip`/`y_tip` on columns and line charts; `axis_title`/`axis_tip` on
bars), reference lines (`ref_tip`), heatmap headers (`col_tips`, `row_tips`, `extra_tips`), table
headers (`col_tips`), keys (`tip=`), chart titles (`card(tip=)`). Write them from the data. Plain tips
end with an interpretation (`meaning=`); add `tech=` where the method matters. Captions can be
`vk.dual(plain, technical)`. The cursor never changes; tipped labels get a faint dotted underline.

The Plain / Technical switch is per panel: the page script finds every `.card`, `.note`, living
`section.panel`, `section.sec` and the `header` that holds technical text (a `.tech` element or a tip with
`tech=`) and gives it its own switch, top right. Text and tips follow their nearest such container, so
keep a chart's technical text inside its card. Old pages pick this up when they are rebuilt.

## Shading tables

`table(..., shade={col: {"scale": "good_bad", "better": "low"}})` tints a column's cells subtly (the
number stays). Cells can be dicts `{"text", "v", "tip", "flag"}`; `flag` draws a red box (rare; say why).
Scales: `good_bad` (green → red; set `better`), `blues` / `heat` (size, no judgement), `diverging`
(with `mid`, e.g. 0). Put a `shade_key` above the table.

## Every panel has its own page (Carlo, 2026-10-27)

(`<page-slug>` below is the page's file name without `.html`; `write_page` creates the folder.) So that one plot can be sent on its own, every `vk.card` and `vk.panel` (and so every map panel) is also built as a page of
its own, and the card shows two buttons above the chart: **Full screen** (opens that page in a new tab: full width,
taller charts, the map filling the window) and **Copy link** (copies that page's web address; it resolves the relative link
against the page's own address, so it gives the published URL once the page is published). What you do:

```python
page = vk.page(title, body, subtitle=..., sources=[...], footer=...)        # or vk.living_page(...)
vk.write_page(dest, page)          # NOT dest.write_text(page): also writes panels/<page-slug>/<panel>.html
```

- **Give every card a specific title.** It becomes the panel page's browser tab and link-preview text ("<card title> — <page
  title> · <date>"); an untitled card is called "Panel 1", "Panel 2". Names are fixed when `vk.write_page` runs, in page order:
  cards with a `panel_id=` first, then by title (`vk.card(..., title="How often inspectors and the model agree",
  panel_id="agreement")` gives `agreement.html`); duplicates get -2, -3. **Untitled or same-titled cards get names that depend on
  their order, so give them a `panel_id=`.** A living panel's own page is named from its id and keeps that name when the panel is
  updated; a removed panel's name is never reused. The names carry no date, so a link copied earlier still shows the panel after
  the page is updated. Panel pages carry the page's sources, footer and byline, a link back, and their own Plain / Technical
  switch. A relative link or image inside a card (to a sibling page, say) is rebased for the panel page automatically.
- A card with a map uses the map's own page, titled "<card title> — <page title> · <date>" unless you pass `standalone_title=`
  (a title that does not end with a date gets " — <page title> · <date>" added). `vk.map_panel(..., name="short-name",
  standalone_title=..., standalone_spec=...)` names it and lets it carry more than the panel (for example a heavy building-outline
  layer, a few MB, that would bloat the page; **that page has the chart page's access, so keep private or internal-only layers
  out of it**). The map's own page has its own Copy link button.
- `vk.card(..., standalone=False)` leaves the buttons off a card that is not a visualization. Notes, tiles and section
  intros never get them.
- `publish.py` publishes `panels/<page-slug>/` with the page, with the page's access (a gated page gets gated panel pages), and
  keeps the READMEs to one line per page. `publish.py --pull PAGE` fetches the page **and its panel pages**, so a new session can
  keep building. When a panel is removed from a living page, vizkit deletes its local panel page and prints the
  `--remove panels/<page-slug>/<name>.html` argument to add to the publish command (`publish.py --folder F PAGE.html --remove
  panels/<slug>/<name>.html --execute -m "..."`); the published copy stays live until you do. `publish.py --remove PAGE.html`
  takes the panel pages in the page's own `panels/<file stem>/` folder with it. Do not edit the page's HTML between `vk.page()`
  and `vk.write_page()` (a warning says the panel pages would show the original card); a map's own page shows the map's data as
  they were when `vk.map_panel()` ran.
- `check_page.py`: a panel page that is missing, or from another build than the link to it (the page was rebuilt with
  `dest.write_text`), is an error (rebuild with `vk.write_page`); a card without the buttons is a warning, except a card made with
  `standalone=False`; a map embedded by an older vizkit (no own-page marker) is a warning: re-add the panel with the same id.
- Build the cards and write the page in the same process (the panels are registered in memory until `write_page`). A script
  that builds a page but never calls `write_page` gets a warning at exit. On a local file (before publishing) Copy link copies
  nothing and says "Publish first". Full screen on a PIN-gated page opens the panel already unlocked after a plain click; a tab
  opened with Ctrl or the middle button asks for the PIN again.

## Map panels

A chart page can hold an interactive map as one of its panels: `vk.card(vk.map_panel("map_spec.json"),
title=..., caption=...)`, or `vk.map_panel(spec_dict, base=folder_with_the_geojson)`. The spec is the same
as for a standalone map (`references/map-spec.md`): layers, colours, hover cards, places-to-look tabs,
base maps. In the panel the title, subtitle and sources are left to the page (put the map's data and
base-map credits in the page's `sources`); `panel_title` names the key. Two fingers on a phone or Ctrl +
scroll on a desktop move the map, so the page scrolls past it normally; it has a fullscreen button; the
key folds into a bar on a phone; the page's light / dark switch and the Plain / Technical switch of the card holding it carry into it.

Use a panel when the map is one view among several (where the fires are, next to charts of what burned).
Use a standalone map page (maps.md) when the map is the main thing. A heavy map (more than a few MB of data) goes in the
map's own page only: pass `standalone_spec=` with the extra layers and keep the panel light.

## Phone layout: decide per chart

There is no single phone rule; choose for each chart what reads best at 390 px, then check the phone
screenshot. Light touches are automatic everywhere: short numbers (21.6k) on column labels, two stat
tiles per row, tighter table cells, bar labels stacked over their bars. The choices:

| Option | Use when | Example |
|---|---|---|
| **fit** (`line_chart` default) | a trend or shape is the point; exact x labels can thin out | exposures by year |
| **scroll with frozen panes** (`heatmap`/`table` default) | columns are a sequence read across (years, deciles), or many rows are compared down a column; the first column and header stay frozen | state × year heatmap |
| **cards** (`phone="cards"`) | each row is a record read on its own (a fire, a site), few columns | top-10 fires |
| **move detail into the hover** | a secondary number (n, CI) crowds the phone view | `sub` numbers in cells |
| **split or simplify** | a chart has too many series or columns for any phone layout: show the top N, or one chart per group | 30 states → top 12 |

Scrolling is fine when it is natural (a wide table with its labels frozen); it is not fine for the page
itself, which must never scroll sideways. `screenshot.py --eval` can report overflow:
`--eval "document.documentElement.scrollWidth - document.documentElement.clientWidth"` should be 0.

## Rules that are easy to miss

- Tooltips must add information, not repeat the label. Every non-obvious number says how it was computed.
- Percentages come with their counts. Cohorts are named exactly, with a hover giving the cut.
- Never `cursor: help`. Never an absolute `/home/...` path on the page; the provenance line uses a
  repository-relative script path.
- Captions say what to notice ("A third of the fires hold 93% of the loss"), computed from the data, not
  hard-coded. If the data changes the sentence must still be true, so build it from the numbers.

## Screenshots

```bash
python3 $SKILL/scripts/screenshot.py PAGE.html /tmp/.../shot --full --wait 4
```
Desktop and phone captures of the whole page, sliced into readable pieces, plus any JavaScript
errors (exit status 1). Look for overlapping or clipped text, empty charts, and phone layouts that
overflow.

## When the user critiques a page

Change the page script, and if the critique is a general preference (not specific to this page),
also update `references/house-style.md` and, where it is a component behaviour, `vizkit.py` and the
archetype, then republish the archetype so it stays the reference.
