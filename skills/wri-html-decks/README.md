# wri-html-decks

Slide decks as one HTML file in the WRI / NCEAS house style, published to your team's GitHub Pages site and
handed back as a link, the same way the companion skill
[`wri-html-pages`](../wri-html-pages/) does for maps and charts. Ask your agent for a presentation ("make a deck
on the validation results for Monday", "add a slide with the new numbers", "the map slide needs tabs for the three
sites") and it builds, checks, publishes and links it.

**Reference deck (open data):**
[Deck archetype: Palmer penguins by species, sex and island](https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/deck-archetype-palmer-penguins-species-sex-island-2026-10-23.html)

## What every deck gets, without being asked

- **Real 16:9 slides**, scaled to any screen: arrow keys, space, swipe or click to move; F for full screen; a PDF
  button that prints one slide per page; a link to any slide (`#12`).
- **A progress strip at the top of every slide**, grouped into the deck's sections, each in its own colour: what
  you've seen, where you are, what's left, and the section names (the current one larger). Click to jump.
- **One idea per slide**, with blocks that show rather than tell: headline numbers, unit grids, numbered steps,
  bracket flowcharts, cards outlined in their concept's colour, statement slides.
- **Charts drawn for the slide**: bars (several per row), columns, lines labelled in place, estimates with
  intervals, scatter with fitted lines, time spans, class scales, shaded tables, all with large labels.
- **Maps as still pictures** with tabs for places to look and layers you toggle, plus a link to the interactive map.
- **Hover tips on every part, with a highlight and no cursor change**; numbers say how they were calculated; a
  Plain | Technical switch on slides that have technical text; an (i) at the bottom right of every slide.
- **One link, kept up to date**: the title keeps the deck's start date, the cover says when it was started and
  last updated, and the Contents panel (O) lists every slide and the deck's change history.
- **Two languages in one deck** when needed (ES | EN switch keeps your place).
- **Checked before it ships**: every slide rendered in headless Chrome, with errors for overflow, squeezed charts,
  overlapping text and crowded bands, and warnings for dense slides, small text and untraced numbers.

## Install

Needs the [`wri-html-pages`](../wri-html-pages/) skill in the same skills folder: decks use its identity.json (your
name, logos, time zone and publishing site), its tip format and its `publish.py`. Set that skill up first; this one
then needs no settings of its own. Copy this folder next to it (for Claude Code, `~/.claude/skills/wri-html-decks`).
A project copy of the page skill with another prefix (`<prefix>-html-pages`) is found when this folder is named
`<prefix>-html-decks`; or set `DECK_PAGES_SKILL=/path/to/page/skill`.

Requirements: Python 3.10+; Pillow (still maps); Chrome or Chromium and `websocket-client` (slide checks); internet
for base-map tiles and the fonts.

## Files

| Path | What it is |
|---|---|
| `SKILL.md` | What the agent is told to do, and when. |
| `references/deck-style.md` | The standing preferences for decks, each with who set it, when and why. |
| `references/slides.md` | Every block, chart and map call. |
| `scripts/deckkit.py` | Builds the deck. |
| `scripts/shoot_deck.py` | Renders and checks every slide. |
| `examples/penguin_deck_demo.py` | The reference deck, from open Palmer penguin and GBIF data. |

## Version history

- **1.0.0** (2026-10-23): first version, made from the wildfire structure-loss deck (Sept–Oct 2026) and the owner's
  feedback on it: sectioned progress strip, one idea per slide, colour per concept, hover tips without a cursor
  change, the (i) note, still maps with tabs and toggles, charts drawn for the slide, published and linked like
  the page skill. No speaker notes, at the owner's request.
