# Building a deck with deckkit

`scripts/deckkit.py` makes one self-contained HTML deck. Everything is in pixels on a 1920 x 1080 slide; the
content box under the title is 1664 px wide and about 600–680 px tall once a one- or two-line title is in. Read
`deck-style.md` first; the archetype script `examples/penguin_deck_demo.py` uses every block below once.

```python
import sys
sys.path.insert(0, "<skill>/scripts")
import deckkit as dk

deck = dk.Deck("Short specific title · 2026-10-23",                  # keeps its start date: same link on every rebuild
               subtitle="Place, dates, cohort and counts, what is new", # detail goes here, not in the title
               lang="en",                                             # "es" for Spanish controls
               sources=["Citation, DOI or URL, licence", ...],        # becomes the last slide, with the provenance line
               script="scripts/build_deck.py")                        # repository-relative path, never /home/...
deck.section("The record")                  # every slide after this belongs to the section (strip group + colour)
deck.cover()
deck.slide("id", "A title that states the idea", body_html, lede="One line, if needed",
           info=("How to read it", "<p>Method, definitions, caveats.</p>"), source="Short source line",
           tint=None)                       # tint=concept colour washes the slide when it is all about that concept
deck.statement("why", "Why is this important?", sub="One supporting line")
path = deck.write(OUT_DIR, previous=PULLED_COPY, change="What changed", removed={"old-id": "why it went"})
```

Two languages in one page: build one `Deck` per language with the same slide ids, then
`dk.write_page(OUT_DIR, deck_es, deck_en, previous=..., change=...)`. The first is the default; the ES | EN button
keeps the slide number. Keep Spanish and English text side by side in the script with a small `t(es, en)` helper.

## Text and layout

| Block | Use |
|---|---|
| `dk.text(html, size=32)` | One or two sentences. |
| `dk.bullets([...])` | Three or four short parallel lines; otherwise cards or a chart. |
| `dk.row(a, b, widths=[2, 1] or [px, 1])`, `dk.col(...)`, `dk.spacer()` | Layout. `spacer()` pushes what follows down (or centres when used on both sides). |
| `dk.card(title, body, color=, fill=, icon_name=, badge_n=, edge="box"/"side")` | A box in the colour of what it describes. |
| `dk.number(value, label, color=, tip=)`, `dk.numbers([...])` | Headline figures that read on their own. |
| `dk.note(html, title=, color=)` | A callout strip: the takeaway or the caveat that matters. |
| `dk.key([{label, color, swatch, toggle, tip}])` | Big friendly key; `toggle=` hides / shows `data-layer` elements on the slide. |
| `dk.badge(n, color)`, `dk.pill(text, color, filled=)`, `dk.icon(name, color)` | Repeated concepts. Icons: `sorted(dk.ICONS)`. |
| `dk.term(text, tip)` | Inline words or a number with a hover (dotted underline). |
| `dk.steps([{title, text, img or icon, tip}])` | Numbered steps left to right, with arrows. |
| `dk.bracket(columns, links)` | Flowchart: boxes in columns, elbow links merging into the next column. |
| `dk.tabs([{label, body, tip}])` | Two or three views on one slide (places to look, alternatives). |
| `dk.table(columns, rows, numeric=, shade=, col_tips=, tips=)` | At most about 8 rows; tint value cells, tip each column. |
| `dk.image(src, width=, height=, layers=[{id, svg}])` | A picture, inlined; SVG overlays in its pixel coordinates. |
| `dk.link_button(url, label)` | Out to the interactive map or full table (opens a new tab). |

## Charts (all sized for the slide, every mark with a tip)

| Chart | Call | Notes |
|---|---|---|
| Horizontal bars | `dk.hbar(rows, series, width=, label_w=, fmt=, unit=, ref=)` | Several bars per row (e.g. two models); values printed; `after` adds "n = 52". |
| Columns | `dk.columns(labels, series, stacked=)` | Grouped or stacked, values on top. |
| Lines | `dk.lines(x, series, label_at="end"/"max", marks=[...])` | Labelled in the line's colour, no legend; `marks` = vertical reference lines. |
| Estimates with intervals | `dk.dots(rows, ref=)` | Forest plot; `group` rows head each block. Say how the interval was made. |
| Scatter | `dk.scatter(points, fits=[...])` | `layer` on points / fits + `key(toggle=)` to switch groups. |
| Time spans | `dk.spans(rows, start=, end=)` | What each record covers, when; `icon` can be a filled map outline. |
| Unit grid | `dk.waffle(groups, per_row=)` | One square per unit: parts of a whole people can count. |
| Spectrum with classes | `dk.scale(bands, marks)` | Class bands with heavy dividers, cases marked where they fall. |

Tips use the page skill's format: `dk.tip("Heading", "line", meaning="what it suggests", tech=["method"])`. A slide
with any `tech=` text (or `dk.dual(plain, tech)`) gets a Plain | Technical switch.

## Maps

A still map for the talk, a live map behind a link:

```python
fr = dk.Frame((west, south, east, north), size=(1180, 640))   # Web-Mercator picture frame
base = fr.basemap("imagery")                                   # or "light"; tiles cached in ~/.cache/<skill>/tiles
x, y = fr.xy(lon, lat); d = fr.path(geojson_geometry)          # draw points / outlines in picture pixels
svg = f'<path d="{d}" fill="none" stroke="#D55E00" stroke-width="4"/>'
pic = dk.image(base, width=1180, height=640, fit="cover", layers=[{"id": "perimeter", "svg": svg, "viewbox": "0 0 1180 640"}])
body = dk.row(dk.tabs([{"label": "Site A", "body": pic}, ...]),
              dk.col(dk.key([{"label": "Perimeter", "color": "#D55E00", "swatch": "line", "toggle": "perimeter"}]),
                     dk.link_button(LIVE_MAP_URL, "Open the interactive map")), widths=[1180, 1])
source = fr.credit("imagery")                                  # put the base map in the slide's footer
```

`dk.map_live(spec, base)` embeds a live MapLibre map from the page skill's map spec, for when the audience must pan
and zoom during the talk. Keep it light; a heavy map belongs on its own page.

## Checks

- At build time deckkit refuses a slide that sets a cursor, warns about text under 22 px, and notes slides with no (i).
- `python3 <skill>/scripts/shoot_deck.py DECK.html OUT_DIR` renders every slide at 1920 x 1080 in headless Chrome
  (with the real fonts), saves `slide_NN.png` and contact sheets, and reports per slide: content outside the slide or
  cut off, squeezed charts, text overlapping text or the (i), content in the strip or footer bands (errors); more
  than 60 words, text under 22 px, numbers without a tip, tips that repeat their label (warnings).
- Look at the contact sheets and at every changed slide before publishing.
