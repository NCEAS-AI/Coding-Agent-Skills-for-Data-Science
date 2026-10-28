# wri-html-pages: an agent skill for maps and chart pages, published by link

Version 1.10.0, 2026-10-27. Made by Carlo Broderick (NCEAS, UC Santa Barbara) with Claude, for the
Wildfire Resilience Index team. Public home: https://github.com/NCEAS-AI/Coding-Agent-Skills-for-Data-Science
(`skills/wri-html-pages/`).

With this skill installed, ask your coding agent for a map or a chart page ("map these survey sites by
species", "chart body mass by species and sex", "add a panel with the yearly totals") and it
builds the page in the team's house style, checks every panel for statistical rigor, looks at it on
desktop and phone, publishes it to the team's GitHub Pages site, and gives you the link. Further requests
add panels to the same page, newest on top. Every chart and map on a page also gets its own page, with
**Full screen** and **Copy link** buttons beside it, so one plot can be sent on its own.

See what the pages look like:
- Map: https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/map-archetype-penguin-records-around-palmer-station-2026-10-13.html
- Charts: https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/chart-archetype-palmer-penguins-size-species-sex-2026-10-27.html
- A page built up over several requests: https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/exploration-archetype-palmer-penguins-built-step-step-2026-10-27.html

## Install

The easiest way: paste the Quick Start Prompt from the repo's README into your coding agent; it
installs and personalizes the skill. By hand, copy this folder (`wri-html-pages/`, with `SKILL.md` at its
top) into your tool's skills folder, then start a new session:

| Tool | Personal (all projects) | One project |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Cursor | `~/.cursor/skills/` or `~/.agents/skills/` (also reads `~/.claude/skills/`) | `.cursor/skills/` or `.agents/skills/` |
| Codex | `~/.agents/skills/` | `.agents/skills/` |
| GitHub Copilot (VS Code, CLI) | `~/.copilot/skills/` or `~/.agents/skills/` | `.github/skills/` or `.agents/skills/` |
| Gemini CLI | `~/.gemini/skills/` or `~/.agents/skills/` | `.gemini/skills/` or `.agents/skills/` |
| Claude.ai | upload `wri-html-pages.skill` (a zip of this folder) in Settings → Capabilities → Skills | |

Locations checked against each tool's documentation on 2026-10-13; they change, so check yours. On
claude.ai pages can be built but not pushed to GitHub.

## First-time setup

1. Put **your own** name, affiliation and time zone in a personal copy of the settings,
   `~/.config/wri-html-pages/identity.json` (start from `references/identity.json`): they go in every
   page's byline. A team other than WRI also changes the logos, links and `github.pages_repo` there, and
   can keep its logo files in the same folder. The personal copy survives updates of the skill; without
   one, the bundled WRI settings are used. (`$WRI_HTML_PAGES_IDENTITY` can point at a file elsewhere.)
2. Publishing needs SSH push access to the pages repo (`ssh -T git@github.com` should greet you).
3. Pages are published open (anyone with the link can view them). If you ask for a PIN gate, the agent
   needs the site PIN in your session: `export SLP_PIN=...` (ask the site owner). It is never written to a file.

## Requirements

- Python 3.10+ with `websocket-client` and `Pillow` (screenshots); `cryptography` only for the PIN gate;
  on Windows also `tzdata` (time zones)
- Google Chrome or Chromium (screenshots); found on the PATH or in the usual macOS and Windows places,
  or set `CHROME=/path/to/chrome`
- For maps from non-GeoJSON data: `geopandas`; for raster overlays: `rasterio` and `numpy`
- `git` with push access to the pages repo: SSH keys by default; with an HTTPS login (GitHub CLI, a
  credential manager) set `github.pages_remote` to `https://github.com/OWNER/REPO.git` in identity.json

## Changing the house style

The rules live in `references/house-style.md`; the map look in `assets/map_template.html`; the chart
look in `scripts/vizkit.py`. Tell Claude what to change (for example "make the burned dots bigger on
every map") and it updates these files and rebuilds the archetypes.

## License

Code and text: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/), public domain. The logos are
not covered: `assets/nceas-logo.svg` is the logo of the National Center for Ecological Analysis
and Synthesis and `assets/wri-logo.png` that of the Wildfire Resilience Index, and `assets/wri-flame-icon.png` and `wri-flame-preview.png` are its
flame (from wildfireindex.org), used here for their own
pages. Another team replaces them with its own logos (set in its identity.json).

## Version history

- 1.10.0 (2026-10-27): every visualization has its own page. Each chart card and each map panel on a chart page
  also gets its own HTML page (`panels/<page-slug>/...`, written by `vk.write_page`) with two buttons beside it:
  **Full screen** (the panel alone, as large as the screen allows, in a new tab) and **Copy link** (copies that
  page's web address, so one plot can be sent on its own). A map's own page can carry more than the embedded map
  (`standalone_spec=`) and has a Copy link button. Panel page names carry no date and are fixed when the page is
  written (from the panel id or card title, in page order), so copied links survive updates: an updated living
  panel keeps its name, a removed panel's name is never reused, and removing a panel removes exactly its own page.
  `publish.py` publishes the panel pages with the page, gated when the page is gated (a gated map's own page now
  opens: the PIN gate no longer leaves globals behind), `--pull` fetches them, and `--remove PAGE` takes them down;
  `check_page.py` flags a missing or stale panel page (each panel page and its link carry one build id). Titles are
  no longer escaped twice, a bare `<` in a title survives, and a staging folder for gated copies is private and removed.
  Panel pages live in `panels/<page file name>/`. `slug()` now decodes HTML entities and folds letters such as ß ø æ ł
  (a title like "Fire &amp; smoke" or "Straße" gives a different slug than in 1.9.0: for an existing living page keep its
  current file name instead of recomputing it from the title). `build_map` no longer changes the spec it is given (the
  key's counts were written into the caller's copy).
- 1.9.0 (2026-10-19): every page carries the WRI flame as its browser-tab icon and as the link-preview image
  in Slack, email and social media (Open Graph / Twitter tags with the title and subtitle). Set in identity.json
  `page_icon`; the preview image is hosted at `site_assets/` on the pages site. Gated pages show only the flame.
- 1.8.0 (2026-10-15): the Plain / Technical switch is per panel, not page-wide: every chart card, note, section and header
  with technical text gets its own small switch, which changes only that panel's caption, hovers, checks and map.
- 1.7.1 (2026-10-14): panel date stamps on living pages wrap on phones.
- 1.7.0 (2026-10-13): published in NCEAS-AI/Coding-Agent-Skills-for-Data-Science, ready for other teams.
  - Example pages use open ecological data anyone can download (Palmer Penguins; GBIF penguin records around
    Palmer Station; the SCAR gazetteer), fetched and cached by `examples/penguin_data.py`, not wildfire data.
  - The publishing site comes from identity.json (`github.pages_repo`; `pages_remote` for HTTPS logins);
    personal settings in `~/.config/wri-html-pages/identity.json` override the bundled ones and survive
    updates; a new site without a pages index works.
  - Private, embargoed or internal-only data are not published openly without asking.
  - Phones: the byline and long shading-key labels wrap; screenshot.py warns when a page scrolls sideways.
  - `vk.today()` dates titles in the team's time zone; line-chart end labels stay inside the chart; column
    charts leave room under the axis title; horizontal bars keep whiskers sensible near zero.
  - screenshot.py finds Chrome on macOS and Windows (or `CHROME`); SKILL.md declares its license,
    requirements and version; install steps for Claude Code, Cursor, Codex, Copilot, Gemini CLI, claude.ai.
- 1.6.0 (2026-10-12): living pages for iterative work. New charts are added on top of the current page
  (older ones move down), each with when it was added; obsolete or wrong panels are removed with the reason
  kept in a page history; `publish.py --pull` fetches the published page so any session can continue it.
- 1.5.0 (2026-10-12): a rigor pass for every panel before it is published (`references/rigor.md`:
  like-for-like periods, no partial years, single-event dominance, uncertainty from the right unit, claims
  that match the evidence), recorded under each panel as "How this panel was checked".
- 1.4.0 (2026-10-12): hover explanations on every chart part (axes, legend entries, headers, keys) with
  a Plain language / Technical switch, plain tips suggesting an interpretation; subtle red-to-green
  shading for tables of values and a rare red box for values that merit attention; maps get technical
  text (`*_tech`) and follow the page's switch.
- 1.3.0 (2026-10-12): any data visualization request triggers the skill and is published to the
  WRI-Science GitHub site automatically (project folder chosen by Claude); pages are open by default
  (PIN gate only when asked; already-gated pages stay gated); Claude links the newest live version of
  a page in every reply about it; publish.py logs every published link (`publish.py --links`).
- 1.2.0 (2026-10-12): map panels. A chart page can hold an interactive map as one of its panels
  (`vk.map_panel`, same spec as a standalone map), with two-finger / Ctrl-scroll gestures, a fullscreen
  button, and the page's light / dark switch. The chart archetype shows the 191 fires on a map.
- 1.1.0 (2026-10-12): phone layouts chosen per chart. Line charts redraw narrow on phones; heatmaps and
  tables either scroll with the first column and header frozen or turn into compact cards; short
  numbers on column labels; two stat tiles per row; guidance on choosing (references/charts.md).
- 1.0.0 (2026-10-12): first release. Maps, chart pages, publishing with checks and PIN gate, short dated
  titles with detailed subtitles, byline with build time, NCEAS and WRI logos, WRI GitHub links.
