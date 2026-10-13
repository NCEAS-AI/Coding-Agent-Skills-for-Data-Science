# Maps: interactive maps in our house style

Every map we share should look and behave the same way, on a phone and on a desktop. A map can be a
page of its own (this guide) or one panel of a chart page (`vk.map_panel`, charts.md "Map panels"),
built from the same spec. This skill fills
one tested template (`assets/map_template.html`, MapLibre GL JS 5.24.0) from a JSON spec with
`scripts/build_map.py`, then publishes it (`references/publishing.md`).

## Before writing anything

1. Read `references/house-style.md`, the team's standing
   preferences for every page (audience, numbers, hovers, colours, layout). Its "Maps specifically"
   section is the short list for maps.
2. Look at the archetype, which uses every feature:
   `examples/penguin_map_demo.py` → https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/map-archetype-penguin-records-around-palmer-station-2026-10-13.html
   When the user says "like the archetype but …", start from that script.
3. Spec fields: `references/map-spec.md`.

## Workflow

1. **Prepare layers from files the pipeline wrote** (GeoPandas → GeoJSON in EPSG:4326), keeping only
   the properties the key and hover cards need, with human-readable values ("Burned", not "B").
   Prepare in a page script in the project repo (or the scratchpad for a one-off). Read big tables
   with column and row filters; on shared storage, one heavy read at a time.
2. **Write the spec** (see `references/map-spec.md`):
   - `title`: short and specific, date at the end: `"Penguin records around Palmer Station · 2026-10-13"`.
     It becomes the browser title, the panel heading, the file name and the link text;
   - `subtitle`: the detail, built from the data (place, dates, cohort and counts, split, what is new in
     this iteration); `lede` (optional) for a sentence of context (house-style.md, "Titles, subtitles and links");
   - base map `satellite` for a fire, `map` with `"vector_style": "positron"` for an overview of many fires;
     note in `basemap_notes` when the imagery was taken relative to the fire;
   - one layer per source or zone, categorical colours with outlines, **most important class first**
     (it draws on top);
   - hover cards that add information (dates, scores, source, sizes), never just the class name again;
   - two or three `sites` ("places to look") picked from the data (e.g. densest loss, a mixed area, an
     edge case), with a note saying what to look at;
   - `sources` with citations and licences; `footer` with the date and a repository-relative script path.
3. **Build:** `python3 $SKILL/scripts/build_map.py spec.json OUT_DIR/`
   (a folder: the file is named from the title's slug; build_map refuses a title not ending in the date,
   or a missing subtitle, and records the generation time in the file).
   It refuses missing fields, projected coordinates and empty layers, and warns about values with no
   class in the key and about pages over 25 MB.
4. **Screenshot** at desktop and phone size and look at the images (see Screenshots below).
5. **Publish** (`references/publishing.md`) and end the reply with the `[title](live URL)` line it prints. If the folder is
   PIN-gated, keep the data inline (sidecar files are public).

## Rasters

`$SKILL/scripts/raster_to_png.py IN.tif OUT.png --ramp heat --vmin 0 --vmax 1` (or `--classes "1=#hex,2=#hex"`)
reprojects to Web Mercator, colours it, makes no-data transparent, caps the size, and prints the
`bounds` to put in the spec. Run it with a Python that has `rasterio` (on Aurora: the structure-loss pipeline venv). For "show the cells and the
outline of the structure they form", polygonise the cells in GeoPandas (dissolve by group) and add the
outline as a `polygon` layer with `fill_opacity: 0` above the raster.

## Screenshots

```bash
python3 $SKILL/scripts/screenshot.py PAGE.html /tmp/.../shot --wait 12 [--full] [--hash view=15/39.95/-105.16]
```
It loads the page in headless Chrome (warm-up load first), captures desktop (1400×900) and phone
(390×844 @2x), slices tall `--full` captures into readable pieces, and prints any JavaScript error;
exit status 1 means the page logged errors. Read the PNGs and look for: an important class buried
under a common one, white lines invisible on light imagery, a key too long for a phone, a start view
that is too wide. `--hash view=ZOOM/LAT/LON` captures a close-up. On a phone the key starts folded to
its title bar; that is intended.

## Behaviour built into the template (change it there, not per page)

- Panel on the left (desktop) or a bottom drawer (phone, starts folded); hover cards on desktop,
  tap → bottom sheet on a phone; Esc closes.
- Base maps: Esri World Imagery (satellite), USDA NAIP via USGS (aerial, most recent flight), OpenFreeMap
  street map, hybrid labels; falls back to imagery only if the street style cannot load.
- Key = layer control: a tick box per layer and per class, counts beside each class.
- Scale bars in miles/feet and km/m; credits folded; the URL remembers the view for sharing.
- Feature highlight on hover; pointer cursor only over features that open a card.

When the user critiques a map, change the spec or page script. If it is a general preference, also
change the template (and `house-style.md`), rebuild the archetype and republish it so it stays the reference.
