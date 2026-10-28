# Examples: the scripts behind the archetype pages

These scripts build the reference pages from open ecological data that anyone can download, so they run
anywhere and can be shared with anyone. Every number on the pages is computed from the data, which makes
them the best worked examples of the skill's building blocks. Read them for patterns, and rebuild them
when the house style changes, so they stay the reference.

| Script | Page it builds | What it shows |
|---|---|---|
| `penguin_map_demo.py` | [Map archetype](https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/map-archetype-penguin-records-around-palmer-station-2026-10-13.html) | A standalone map: two point layers with species filters and counts, ready-made hover cards, "places to look" tabs, base maps, Plain / Technical text, layer descriptions written from the data |
| `penguin_chart_demo.py` | [Chart archetype](https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/chart-archetype-palmer-penguins-size-species-sex-2026-10-27.html) | A chart page with every component: tiles, stacked columns, a heatmap with empty cells, a map panel, bars with bootstrap intervals, a line chart, shaded tables, one merited red box (Simpson's paradox), and a rigor check under each panel |
| `penguin_living_demo.py` | [Exploration archetype](https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/exploration-archetype-palmer-penguins-built-step-step-2026-10-27.html) | A living page built over three requests: new panels on top, and a misleading panel (body mass by island, which compares species) removed with its reason kept in the page history |
| `penguin_data.py` | | Downloads and caches the data below (standard library only) |

## Running them

```bash
python3 examples/penguin_map_demo.py OUT_DIR       # standard library only
python3 examples/penguin_chart_demo.py OUT_DIR     # needs pandas and numpy
python3 examples/penguin_living_demo.py OUT_DIR    # needs pandas and numpy
```

Each writes `OUT_DIR/<dated title slug>.html` and, for the chart and exploration pages, `OUT_DIR/panels/<page slug>/`: one page per chart card and the map's own page, the targets of each panel's Full screen and Copy link buttons. Publish the page with `scripts/publish.py` as usual; the panel pages go with it. The data are
downloaded on the first run into `~/.cache/wri-html-pages/example-data` (or `$EXAMPLE_DATA`) with the date
they were fetched; delete a file there to fetch it again.

## The data

| Data | What it is | Licence |
|---|---|---|
| [Palmer Penguins](https://allisonhorst.github.io/palmerpenguins/) (`penguins.csv`, `penguins_raw.csv`) | Bill, flipper and body-mass measurements of 344 adult Adélie, Chinstrap and Gentoo penguins at nests on three islands near Palmer Station, Antarctica, 2007–2009. Gorman, Williams & Fraser (2014), [doi:10.1371/journal.pone.0090081](https://doi.org/10.1371/journal.pone.0090081); packaged by Horst, Hill & Gorman (2020), [doi:10.5281/zenodo.3960218](https://doi.org/10.5281/zenodo.3960218) | CC0 1.0 |
| [GBIF](https://www.gbif.org) occurrence records | Records of the same three species around the Palmer Archipelago, open licences only; each page lists every dataset used, for attribution | CC0 1.0 and CC BY 4.0 records |
| [SCAR Composite Gazetteer of Antarctica](https://data.aad.gov.au/aadc/gaz/scar/) | Positions of Torgersen Island, Dream Island and Biscoe Point, the three study sites | open (Australian Antarctic Data Centre) |

What the examples teach about rigor, from these data:

- **The independent unit:** penguins were measured as pairs at nests, so partners are not independent.
  Within one species and sex each bird is from a different nest, so the bars compare within sex.
- **Confounding:** Gentoo were measured only on Biscoe and Chinstrap only on Dream, so "by island" is
  really "by species". The living page removes that panel for this reason.
- **Simpson's paradox:** bill length and depth rise together within every species but fall together
  when the species are pooled. The chart page flags the pooled number with the red box.
- **Where data come from:** GBIF dots show where people recorded penguins (eBird birders, research
  counts, published studies), not where penguins are; the map says so.
