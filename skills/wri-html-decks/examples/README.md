# Examples: the script behind the archetype deck

The archetype deck is built from open ecological data anyone can download, so it runs anywhere and can be shared
with anyone. Every number on it is computed from the data. Read it for patterns, and rebuild it when the house style
changes, so it stays the reference.

| Script | Deck it builds | What it shows |
|---|---|---|
| `penguin_deck_demo.py` | [Deck archetype](https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/deck-archetype-palmer-penguins-species-sex-island-2026-10-23.html) | 13 slides in 3 sections: cover, headline numbers with a one-square-per-bird grid, a still satellite map with four "places to look" tabs and species toggles plus a link to the interactive map, grouped bars, estimates with bootstrap intervals, lines labelled at their peaks, a scatter showing Simpson's paradox with toggles, time spans, a shaded table, numbered steps, a statement slide and the sources slide |

## Running it

```bash
python3 examples/penguin_deck_demo.py OUT_DIR      # needs Pillow; internet on the first run
python3 scripts/shoot_deck.py OUT_DIR/deck-archetype-*.html /tmp/deckshots
```

It reads the data with the page skill's `examples/penguin_data.py` (Palmer Penguins, GBIF records around Palmer
Station and the SCAR gazetteer, cached in `~/.cache/wri-html-pages/example-data`), and fetches Esri World Imagery
tiles for the map once (cached in `~/.cache/wri-html-decks/tiles`). To update the published deck instead of starting
its history again, pull it first and pass it in:

```bash
python3 ../wri-html-pages/scripts/publish.py --pull deck-archetype-palmer-penguins-species-sex-island-2026-10-23.html --folder style_archetypes --to /tmp/prev.html
DECK_PREVIOUS=/tmp/prev.html DECK_CHANGE="What changed" python3 examples/penguin_deck_demo.py OUT_DIR
```
