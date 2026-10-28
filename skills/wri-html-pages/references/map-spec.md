# build_map.py spec reference

A spec is one JSON file. Paths are relative to it. Text fields marked (HTML) are inserted as HTML,
so they may hold `<b>`, `<a>`, `<i>`. They are written by us, never copied from data.

```jsonc
{
  "eyebrow": "Project · topic",                 // small caps line above the title
  "title": "Penguin records around Palmer Station · 2026-10-13",
                                                // REQUIRED: short, specific, build date at the END.
                                                // Browser title + panel heading + file name (when OUT is a folder).
  "subtitle": "Palmer Archipelago, Antarctica · 13,114 GBIF records of three penguin species, by kind of record",
                                                // REQUIRED (HTML): the detail the title leaves out, built from the data
  "lede": "One sentence of context (optional, HTML).",
  "how_to_read_tech": "(HTML) technical version; any *_tech field adds a Plain / Technical switch to the key",
  "panel_title": "Fires: key and layers",       // only for a map panel in a chart page (vk.map_panel); there the
                                                // title, subtitle, lede, sources and byline are left to the page
  "how_to_read": "<p>Each dot is …</p>",        // (HTML) folded box; omit for none
  "basemap": "satellite",                       // satellite | aerial | map | hybrid  (first one shown)
  "basemaps": ["satellite", "aerial", "map", "hybrid"],   // which switcher buttons, in order
  "vector_style": "liberty",                    // OpenFreeMap style for "map"/"hybrid": liberty | positron | bright | dark
  "basemap_notes": {"satellite": "When the photo was taken and whether that is before or after the fire."},
  "sites": [                                    // "Places to look" tabs (a "Whole area" tab is added first)
    {"name": "Torgersen Island", "bounds": [w, s, e, n], "note": "(HTML) what to look at here"}
  ],
  "whole_label": "Whole fire",                  // label of the first tab (default "Whole area")
  "bounds": [w, s, e, n],                       // optional; default = all layers with "fit" not false
  "max_fit_zoom": 17,
  "hash": true,                                 // URL remembers the view (#view=zoom/lat/lon) so links share a view
  "precision": 6,                               // decimal places kept in coordinates (5 ≈ 1 m)
  "noindex": false,                             // true adds a robots noindex meta (gated folders get one anyway)
  "layers": [ … ],                              // drawn in order: later layers on top
  "author": "Caitlin Fong",                     // optional: byline author when not the default in identity.json
  "affiliation": "NCEAS",                       // optional, with "author"
  "brand": true,                                // NCEAS / WRI logos + WRI GitHub links at the foot of the panel
  "sources": ["(HTML) one line per dataset: citation, link, licence"],
  "footer": "(HTML) Built YYYY-MM-DD by path/in/repo/script.py",    // repository-relative path only
  "back_link": {"href": "../../page.html", "label": "Back to the page"},   // optional: a link (and a Copy link button) under the title; standalone map only. vk.map_panel sets it on the map's own page
}
```

## Layers

Common fields: `id` (letters, digits, `-`, `_`), `name` (shown in the key), `kind`
(`point` | `polygon` | `line` | `raster`), `file`, `description` (HTML, under the name in the key),
`visible` (default true), `minzoom` / `maxzoom`, `fit` (include in the start extent; default true;
set false for e.g. a region outline far bigger than the fire), `in_key` (false hides it from the key),
`show_count` (false hides the feature count), `keep` (extra property names to keep in the page),
`allow_empty`, `description_tech` (technical version of the description).

### Colour

Single colour: `"style": {"color": "#E8432A"}`.

By category (the key gets one tick box and a count per class; **the first class listed draws on top**,
so list the important class first):
```json
"color_by": {"type": "categorical", "field": "condition", "other_color": "#9AA3AD",
  "categories": [{"value": "Burned", "label": "Burned", "color": "#E8432A", "edge": "#4A0B04"},
                 {"value": "Not burned", "label": "Not burned", "color": "#BDEBCB", "edge": "#3D6B4E"}]}
```
By value (gradient key):
```json
"color_by": {"type": "continuous", "field": "p", "label": "Model score",
  "stops": [[0, "#1A9850"], [0.5, "#FEE08B"], [1, "#D73027"]], "min_label": "0", "max_label": "1",
  "nodata_color": "#9AA3AD"}
```

### Style by kind

- point: `radius` as zoom stops `[[10, 1.8], [13, 3.4], [16, 7]]`, `opacity`, `outline` (default white),
  `outline_width` (0.7)
- polygon: `fill_opacity` (0.55), `outline` (defaults to the fill colour), `outline_width` (1)
- line: `color`, `width` (2), `dash` e.g. `[4, 3]`, `halo` (true: a dark casing so white lines read on
  imagery), `halo_color`, `opacity`
- raster: `"image": "tree_cover.png", "bounds": [w, s, e, n]`, `opacity` (0.75), `resampling`
  (`nearest` for classes, `linear` for smooth surfaces). Make the PNG with `scripts/raster_to_png.py`,
  which reprojects to Web Mercator so the image lines up exactly.

### Hover card (`tooltip`)

```json
"tooltip": {
  "title": "Fire perimeter",                 // fixed title, or
  "title_field": "address",                  // title from a property (default: the category label)
  "text": "(HTML) one sentence that explains this layer",
  "text_tech": "(HTML) technical version of text, shown when the reader switches to Technical",
  "fields": [
    {"field": "p", "label": "Model score", "format": "num2"},
    {"field": "share", "label": "Tree cover", "format": "pct", "decimals": 0},
    {"field": "cls", "label": "Class", "labels": {"1": "Single-family", "2": "Mobile home"}},
    {"field": "n", "label": "Buildings", "format": "int", "suffix": " in the cell"}
  ],
  "html_field": "card"                       // or: a property holding ready-made card HTML (built in Python)
}
```
Formats: `text` (default), `int`, `num0`…`num9`, `pct` (0–1 → %), `pct100` (already 0–100). Empty
values are left out of the card. A layer with no `tooltip` does not respond to hover.

## Size

Inline data is simplest and is covered by the PIN gate. Keep a page under ~25 MB: keep only the
fields the card needs (build_map drops the rest), round coordinates (`precision`), simplify polygons
in GeoPandas (`.simplify(0.5)` in metres before reprojecting), or split per fire. `--sidecar` moves
data to `data/*.geojson` next to the page, which loads lazily but is **public even in a gated folder**.
