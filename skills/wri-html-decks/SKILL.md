---
name: wri-html-decks
description: "Make every slide deck or presentation as one HTML deck in the WRI / NCEAS house style (real 16:9 slides, a progress strip at the top grouped into coloured sections, one idea per slide, charts and maps drawn for the slide, hover tips on everything with no cursor change, an (i) note on every slide), publish it automatically to the team's GitHub Pages site with the wri-html-pages skill's publish.py and give the link, without being asked to push. Use whenever the user asks for a presentation, deck, slides, slide deck, talk, pitch, briefing, update for a meeting or the team, or says make slides about, present, put this on the presentation, update the deck, add a slide, or critiques a slide or a deck. Covers title, statement and content slides, numbers, steps, flowcharts, tables, bars, columns, lines, intervals, scatter, time spans, unit grids, class scales, still maps with tabs and layer toggles plus a link to the interactive map, and decks in two languages."
license: CC0-1.0 for code and text; logos come from the page skill's identity and are not covered
compatibility: Needs the wri-html-pages skill (or a project copy such as parafire-html-pages) installed in the same skills folder, Python 3.10+, git push access to its GitHub Pages site. Still maps need Pillow and internet for base-map tiles; slide checks need Chrome or Chromium and websocket-client.
metadata:
  version: "1.0.0"
  author: "Carlo Broderick (NCEAS, UC Santa Barbara)"
  source: "https://github.com/NCEAS-AI/Coding-Agent-Skills-for-Data-Science"
---

# wri-html-decks: presentations as HTML decks in our house style, published by link

Version 1.0.0 (2026-10-23). Every deck made with this skill looks and behaves like the wildfire structure-loss
deck the team liked: real slides, a sectioned progress strip at the top, one idea per slide, pictures and charts
over paragraphs, hovers on everything, and one link that is kept up to date.

`SKILL` below means this skill's base directory (printed when the skill loads; normally
`~/.claude/skills/wri-html-decks`). `PAGES` is the page skill next to it (`wri-html-pages`, or the project copy
with the same prefix); deckkit finds it and uses its identity.json, tip format and publish.py.

## Automatic: every deck is built, checked, published and linked (Carlo, 2026-10-23)

Like every visualization (page skill, 2026-10-12), a deck goes all the way through without further asks: build it,
check every slide, **publish it to GitHub automatically** (do not ask whether to push), and give the link. It is
filed on the page skill's site (identity.json `github.pages_repo`) under `publication_htmls/<project folder>/`,
next to the project's maps and charts. Open by default (PIN only on request). Private or embargoed data: the page
skill's rule applies (build locally, say why, ask).

## One deck, kept up to date (Carlo, 2026-09-28 and 2026-10-06)

A deck is a living document. **Update the current deck rather than starting a new one**: new slides go where they
belong in the story (not at the top), obsolete or wrong slides come out with the reason passed in
`removed={id: why}`, and the title keeps the deck's start date so the link never changes. In a new session,
`python3 $PAGES/scripts/publish.py --pull FILE.html --folder F --to PATH` fetches the published deck; pass it as
`previous=` so its start date and change history carry over. Start a new deck only for a new talk or when asked.

## The link goes in every reply

Every reply that has anything to do with the deck ends with `[Short title · YYYY-MM-DD](live URL)` of its newest
version, unasked. Lost track? `python3 $PAGES/scripts/publish.py --links --folder F`.

## Read first

1. `references/deck-style.md`: the standing preferences for decks, each with who set it, when and why. Read all of it.
2. The page skill's `references/house-style.md` (titles, audience, numbers, hovers, colour, byline) and
   `references/rigor.md` (the rigor pass): both apply to every chart slide.
3. `references/slides.md`: every block, chart and map call, with sizes.

## The workflow

1. **Compute everything from real data files.** The deck script reads the data and builds every number, label and
   title from it. Never typed-in numbers, never demo data.
2. **Plan the story in sections** (three to six), each one sentence; one idea per slide; a statement slide where
   the story turns and one sentence to end each section. More than about 60 words on a slide → two slides or a picture.
3. **Build** with `scripts/deckkit.py` (cover, `section`, `slide`, `statement`; blocks and charts from slides.md).
   Every number gets a hover saying how it was calculated, every cohort its exact cut, every slide an (i) with how to
   read it. No speaker notes (Carlo, 2026-10-23). Maps: a still picture with tabs and toggles plus a link to an
   interactive map page made with the page skill.
4. **Rigor pass, chart by chart** (page skill `references/rigor.md`); put what was checked in the slide's (i).
5. **Check and look:** `python3 $SKILL/scripts/shoot_deck.py DECK.html /tmp/deckshots` must pass (no ERROR), and
   act on its warnings. Then look at the contact sheets and every changed slide: text on lines, crowding, a chart that
   doesn't read at a glance.
6. **Publish:** `python3 $PAGES/scripts/publish.py --folder FOLDER DECK.html` (dry run), then with
   `--execute --wait -m "Deck: what a reader now sees"`.
7. **Hand over the link** with the deck's subtitle, and keep linking it in every later reply about it.

## What is in this skill

| Path | What it is |
|---|---|
| `scripts/deckkit.py` | the deck: shell (scaling, progress strip, contents, tips, tabs, toggles, languages, PDF), blocks, charts, still maps |
| `scripts/shoot_deck.py` | every slide rendered in headless Chrome: pictures, contact sheets, layout and density checks |
| `references/deck-style.md` | the preferences every deck follows, with reasons |
| `references/slides.md` | the building blocks and how to call them |
| `examples/penguin_deck_demo.py` | the archetype deck (open Palmer penguin and GBIF data) |

The archetype is the reference look:
https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/deck-archetype-palmer-penguins-species-sex-island-2026-10-23.html

## When the user critiques a deck

Change that deck's script. If the critique is a general preference, also change `references/deck-style.md` (with
the date and the user's words) and deckkit, rebuild the archetype from `examples/`, and republish it so it stays the
reference.
