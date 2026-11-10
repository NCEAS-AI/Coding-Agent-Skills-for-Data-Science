# The site spec: one JSON file per landing page

`scripts/build_site.py SPEC.json OUT` turns one spec into one page. The schema is
`assets/site-spec.schema.json` (build_site validates against it and then checks the rules below); point your editor
at it with `"$schema"` (new_site.py writes the right relative path) for completion. A full, real spec is
`examples/wildfire-structure-loss-record.json`; a blank one with every section comes from `scripts/new_site.py`.

## Conventions

- **Text fields are HTML snippets, checked against an allow-list**: tags `b strong i em a br span sup sub abbr small
  code u s`; attributes `href class data-tip title style target rel lang`; `href` only to http(s), mailto, a
  `#anchor` or a relative path; `style` only `color` / `background(-color)` / `font-weight` / `font-style` /
  `white-space` / `text-decoration` with a colour, `var(--token)` or keyword (`<span style="color:#7C3AED">`).
  `<span class="dotted" data-tip="...">term</span>` is a term with a hover definition (the tip is checked the same
  way). Everything else (other tags, `on...=` handlers, `javascript:` links, `<!-- comments -->`) is refused. Write
  plain `'` and `"` freely; entities like `&rarr;` and `&#8217;` work; a literal `<` before a letter is `&lt;`.
- **Keys starting with `_` are comments** (`"_why": "..."`) and are ignored everywhere.
- **`src`** (a string or a list) can sit on any number-bearing object (stat, tile, map tile, bar row, chart,
  section). It is written as `<!-- SRC: ... -->` next to the element so a fact-checker can trace it. It **is** in the
  page source (public on an open page), so cite documents and sections ("USGS data release doi:..., per-year counts";
  "results note 2026-10-01, Summary"), never a private path; build_site refuses local paths. `--no-src` leaves them out.
- **`tip`** fields become hover / tap / focus tooltips (HTML allowed). Put the exact definition of a number there.
- **`FILL:`**, TODO, TBD, TBC, FIXME, XXX, PLACEHOLDER and lorem anywhere stop the build, and so does a placeholder
  contact (`example.org`, `example.com`, `.test`). `--draft` turns these into warnings for a review copy (a
  "Draft for review" bar on the page; `verify_gate.py` refuses it). Use `TBD` freely in a draft the owner asked for.
- Every `href="#x"` must point at a section `id`. Section ids may not be ones the page uses itself (`tip`, `logos`,
  `logos2`, `lede`, `bigtitle`, `mapiframe`, `lockbtn`, `whypop`, `pin`, `f`, `err`, `ph`, `tipd-N`).

## Top level

| Key | Required | What |
|---|---|---|
| `page.title` | yes | Program name, at least 3 words (publish.py refuses vaguer titles). `<title>` becomes `title · date`; the file name `slug-of-title-date.html`. |
| `page.date` | yes | `YYYY-MM-DD`, the page's start date. Keep it when updating, so the address never changes. |
| `page.description` | yes | 20-300 characters. Meta description and folder README line: **public even when locked**. |
| `page.program_line` | no | Gold line above the title (default `site.json` `program_line`, "An NCEAS Research Program"). |
| `page.built` | no | Date in the footer (default today). |
| `page.og_title`, `og_description`, `og_image`, `og_image_alt`, `site_name`, `lang` | no | Link-preview overrides. |
| `contact` | for `cta` | `{name, email}` for the partner button and the lock screen. Default: `site.json` contact. |
| `gate` | no | The branded lock screen, below. Ignored with `--no-gate-blocks`. |
| `sections` | yes | The page, in order. `hero` first and `footer` last if present (added if missing). |

`gate`: `tagline` (one public sentence; default: `page.description`), `title` (default page title), `tab_title`
(default "title · NCEAS"), `eyebrow`, `button` ("Open the map"), `access_text` / `access_text_short` (the "shared
privately" sentence, long and phone versions), `photo`, `photo_credit`, `contact`, `links` [{label, href}],
`fine_print`, `lock_button` (Lock button in the page header; default true). **No numbers or results** in any of it:
the lock screen is not encrypted (build_site refuses percentages and scores in any `gate` text or the contact on a
locked build).

## Sections

Every section except `hero` and `footer` takes the common keys: `id` (anchor, `^[a-z][a-z0-9-]*$`), `nav` (label in
the top nav; omit to leave it out), `nav_cta` (true on one section: shown as the navy pill, last), `eyebrow` (gold
label), `heading`, `lede`, `lede_size` (`sm` default, `md`, `lg`), `wide` (head runs full width), `background`
(`auto` alternates paper/white starting with paper after the hero; `paper` or `white` forces one and the
alternation continues from it), `src`.

| `type` | Required | Optional | Renders |
|---|---|---|---|
| `hero` | `lede` [1-3 paragraphs] | `title`, `program_line`, `ctas` [{label, href, style solid/outline}] (max 2), `pill` | Program line, big navy serif title, the pitch. No statistics here. |
| `map` | `id`, `heading`, `iframe` {src, title} | `iframe.height` / `phone_height` (a CSS length such as `640px`, `76vh` or `min(80vh, 740px)`; default `min(80vh, 740px)` / `76vh`), `frame` (`plain` / `dashed`), `caption`, `legend` [{color (`#hex`, `var(--token)` or a colour name), label, tip}], `tiles` [max 4], `popup`, `how` {summary, items}, `hint` | Framed map iframe; place tiles under it (click moves the map); the weak-case pop-up; "How this map was made". One map per page. |
| `tiles` | `id`, `heading`, `tiles` [2-4 {title, body, icon, link, src}] | `chart` (a chart object, drawn above the tiles) | "Why it matters": head, chart card, tiles in one row (4 → 2 → 1 columns). |
| `chart` | `id`, `heading`, `chart` | `note` | A chart card on its own. |
| `pipeline` | `id`, `steps` [2-4] | `flow` {in, out} (title "X in → Y out"; else `heading`) | Numbered step cards; `chips` [{label, href, tip}] (data sources) and `list` {summary, items [{name, href, detail}]} (a collapsible reference list). |
| `cards` | `id`, `heading`, `cards` [2-4 {title, icon, bullets [1-3] or body}] | | "Who it helps". |
| `stats` | `id`, `heading`, `stats` [2-4 {value, label, scope, tip, src}] | `bar_cards` [max 2], `footnote` | Big numbers strip, each with its scope line; paired-bar cards with a key and "How these results were checked". |
| `prose` | `id`, `heading`, `paragraphs` [1-6] | | Limits: plain paragraphs, `<b>` for the key phrases, no statistics. |
| `cta` | `id`, `heading` | `steps_card` {title, steps [1-5]}, `contact_card` {title, body, button_label} | The partner call; the button is `mailto:` the contact. |
| `team` | `id`, `heading`, `people` [1-6 {name, role, line, initials, links [max 3]}] | | Initials avatars (navy disc, gold serif), role, one line, pill links. |
| `refs` | `id`, `heading`, `refs` [{name, href, detail}] | `collapsed`, `summary` | A reference list (or a collapsible one). |
| `footer` | `disclaimer` | `credits`, `links` [{label, href}], `built` | Logo row, disclaimer, data credits, "Page built date · links". |

Icons (`icon`): clock, patch, gap, house, sat, table, flame, shield, flask, city, map, doc, people, chart, handshake,
globe, leaf, drop, search, check.

**Map tile** (`map.tiles[]`): `title`, `value` (the big number, a string such as `"97%"`), `text` (what the number is,
with counts "3,973 of 4,078"), `place` (exactly the map's place-button label: clicking posts `{goPlace: place}` to the
iframe, which a wri-html-pages map embed with the place hook answers), `tip`, `flagged` (the weak case: purple top
border and number, a `flag_label`, default "Where it struggles"), `go_label`, `color` (`right` green default, `navy`,
`flag`), `src`. **Popup** (`map.popup`): `place` (must match a tile), `title` ("Why the model misses in X"), `lead`
(what happened, with that case's own numbers), `reasons` (under "Likely reasons"), `helps` (under "What would help";
end with a link to `#partner`). It opens when its tile is clicked or the map reports `{placeShown: place}`.

**Chart object** (`tiles.chart`, `chart.chart`): one series of columns, values from the spec, no dual axes.

| Key | What |
|---|---|
| `title`, `subtitle` | Title, and the scope line ending "Hover or tap a year." |
| `aria_label` | One full sentence for screen readers (what, range, peak). Required. |
| `categories` [{label, value, gap, tip, cols}] | One per column, in order. `gap: true` draws a hatched "no data" column (years not in a record). `cols` adds table columns (`{"Fires": 4}`). Default tip: "**label** value value_label". |
| `value_label` | Noun used in default tips ("destroyed buildings"). |
| `ymax`, `ytick_step`, `ytick_format` (`k`, `plain`, `pct`) | Axis; defaults are computed from the largest value. |
| `label_every` | Show every n-th x label; every other shown label is hidden on phones. |
| `annotations` [{at, text, detail}] | Max 3, at a category label (the outlier, e.g. one big event). |
| `gap_label` {text, detail} | Label over the hatched run. |
| `totals` [{value, label, gap, assert_sum}] | Up to 3 big numbers top right. `assert_sum: true` fails the build unless `value` equals the sum of the values. |
| `key` [{label, kind bar/gap}] | The legend under the chart. |
| `table` {label_header, value_header, note, summary, split} | "See the numbers": the accessible version, split into up to 4 side-by-side tables. |

## A complete small example (annotated)

```json
{
  "$schema": "../assets/site-spec.schema.json",
  "page": {"title": "Coastal Marsh Carbon Atlas", "date": "2026-12-01",
           "description": "An NCEAS research program mapping carbon stored in coastal marshes from public imagery, tested against field cores."},
  "contact": {"name": "the research team", "email": "team@example.org"},
  "gate": {"tagline": "Mapping the carbon stored in coastal marshes from public imagery.", "button": "Open the atlas"},
  "sections": [
    {"type": "hero", "lede": ["One paragraph: what it does now, what it is trying to do, who it is for, that the maps are research estimates, where they are weaker, and that partners' cores close the gaps."]},
    {"type": "map", "id": "map", "nav": "See it", "eyebrow": "See it on real marshes", "heading": "Three marshes, plot by plot",
     "iframe": {"src": "marsh-map-embed-2026-12-01.html", "title": "Interactive map: three marshes"},
     "tiles": [
       {"title": "Marsh A · 2025", "place": "Marsh A · 2025", "value": "91%", "text": "of field cores within the estimate's range (82 of 90)",
        "src": "validation note 2026-11-20, table 2"},
       {"title": "Marsh C · 2025", "place": "Marsh C · 2025", "value": "48%", "text": "of field cores within range (12 of 25)", "flagged": true,
        "src": "validation note 2026-11-20, table 2"}],
     "popup": {"place": "Marsh C · 2025", "title": "Why the estimates miss in Marsh C", "lead": "Only 12 of 25 cores fell in range.",
               "reasons": ["Deep peat below what the imagery can see (likely; checked on Marsh C's own cores)."],
               "helps": ["More cores from deep-peat marshes. <a href=\"#partner\">Share yours</a>."]}},
    {"type": "stats", "id": "accuracy", "nav": "Accuracy", "eyebrow": "Tested against field cores", "heading": "Close where it counts",
     "stats": [{"value": "0.84", "label": "R² against field cores, all cores pooled (0.79 averaged per marsh)", "scope": "3 marshes, 2024-2025",
                "tip": "Each marsh scored by a model fitted without it.", "src": "validation note 2026-11-20, Summary"},
               {"value": "115", "label": "field cores used for testing", "scope": "3 marshes, 2024-2025", "src": "validation note, table 1"}]},
    {"type": "prose", "id": "limits", "nav": "Limits", "eyebrow": "Where it struggles", "heading": "Where we still need to improve",
     "paragraphs": ["It does worse in <b>deep-peat marshes</b> ... <a href=\"#partner\">we would like to work with you</a>."]},
    {"type": "cta", "id": "partner", "nav": "Work with us", "nav_cta": true, "eyebrow": "Work with us", "heading": "Test it on your marsh",
     "steps_card": {"title": "A validation-only pilot", "steps": ["<b>You share cores</b> under your terms.", "<b>We run the unchanged model.</b>", "<b>You get a plot-by-plot comparison.</b>"]},
     "contact_card": {"title": "A map for your coast", "body": "We welcome introductions to agencies and funders."}},
    {"type": "footer", "disclaimer": "Scientific research shared for information only. Results are research estimates, not official assessments."}
  ]
}
```

What the builder adds without being asked: the logo bar and nav from `nav` labels, alternating backgrounds, the
tooltip script (mouse, touch and keyboard; every tip also gets a hidden `aria-describedby` copy), tile → map
messages, the pop-up behaviour, the favicon and link-preview tags, `<meta name="generated">`, and (unless
`--no-gate-blocks`) the four lock-screen blocks plus a Lock button in the header.
