# House style for every page we share (maps and charts)

The team's standing preferences (set by Carlo Broderick, project lead), collected from their feedback on the structure-loss site, the slide
deck, the demo site and the canopy validation page (Sept–Oct 2026). Every map and chart page made with
the wri-html-pages skill follows this file. When the user corrects a page, the correction belongs here (or in the
archetype it applies to) so the next page gets it right. Each rule says why, so edge cases can be
judged rather than pattern-matched.

The archetypes show these rules applied (built from open ecological data, so they can be shared with anyone);
open them before building something new:
- Map: https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/map-archetype-penguin-records-around-palmer-station-2026-10-13.html
- Charts: https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/chart-archetype-palmer-penguins-size-species-sex-2026-10-13.html
- A page built over several requests: https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/exploration-archetype-palmer-penguins-built-step-step-2026-10-13.html

## Titles, subtitles and links (Carlo, 2026-10-12)

We run many analyses and many iterations of each, so "Data analysis" or "Map" is useless a week later,
but a title that holds every detail is too much to read. So:

- **Title: short and specific, with the build date at the end.** A few words naming what the page
  shows: *"Penguin records around Palmer Station · 2026-10-13"*. The same title is the
  browser tab, the visible heading, the file name (`penguin-records-around-palmer-station-2026-10-13.html`,
  via `slug()`), the README line and the link text Claude gives the user.
- **Subtitle: the detail,** directly under the title: place and dates, the cohort with its size and
  years, what is measured and how it is split, and what is new in this iteration (*"Palmer Archipelago,
  western Antarctic Peninsula · 13,114 GBIF records of Adélie, Chinstrap and Gentoo penguins, split into
  field observations and records from publications"*). Numbers in it come from the data.
- **The file records when it was generated:** `<meta name="generated" content="2026-10-12T10:22:05-07:00">`
  and a comment on line 2, plus the visible byline timestamp. vizkit and build_map write all three.
- **Iterations live on one page** (Carlo, 2026-10-12): new panels go on top of the current page, older
  ones move down, each panel shows when it was added; panels that are wrong or obsolete come off with the
  reason in the page history. A new dated page only for a new analysis or when asked.
- **The link is in every reply:** every reply about a page ends with `[title](live URL)` of its newest
  live version, unasked, for as long as the page is being worked on (one line per page in play).
- **Open by default:** pages are public by link; the PIN gate is used only when the user asks for it.
- **Published automatically:** every visualization goes to the WRI-Science GitHub site in its project's
  folder without the user having to ask; the reply names the folder and gives the link.

## Who reads it

- **A scientist arriving fresh.** Someone with statistics and a general idea of the project, but none of
  our history. "The language needs to be for a general audience who's just coming to this fresh."
  So: plain sentences, no internal code names, model tags, run IDs, version chatter, or "we fixed a
  bug" strips. What we tried and dropped stays between Claude and the user; the page shows results.
- **Explain terms once, simply.** If a term like recall, F1, or "direct exposure" is needed, say what
  it means in a clause the first time ("recall: of the buildings that really burned, the share we caught").
- **Tone is serious and professional,** especially on anything public-facing: say what the numbers are
  for and not for (e.g. "a scientific estimate, not an official damage assessment; do not use for
  emergency, insurance or legal decisions"). No cheerleading.

## Numbers

- **Every panel passes the rigor pass** (`references/rigor.md`, Carlo 2026-10-12): like-for-like
  comparisons, full periods only, single-event dominance shown, uncertainty from the independent unit,
  claims no stronger than the evidence. A pretty panel that misleads is worse than no panel.

- **Every element must tell the reader something on its own; cut anything that needs decoding** (Carlo, 2026-10-12,
  on stat tiles reading "16% → 16%": "they're just not very informative … you kind of have to read in, so you should
  take out stuff like that"). Use stat tiles only when each figure is a plain, self-explanatory headline ("1,736
  destroyed buildings inspected"), never a ratio, arrow or pair that only makes sense after reading the caption.
  When in doubt, leave it out: the lede sentence and the charts carry the finding.

- **Real data only.** Every number on a page is computed by the script that builds the page, from a
  file the pipeline wrote. Never type a number from memory, never fill in demo or placeholder data.
  If a value is missing, show it as missing and say why.
- **Raw counts next to percentages.** "Raw numbers are hard to understand" on their own, and a bare
  percentage hides its base. Write "33% (55,416 of 170,412)" or put the counts in the hover.
- **Say what the comparison is.** Name the source each number is compared with ("Versus lidar",
  "Compared with CAL FIRE inspections"), not "truth". Lead with the quantity the reader cares about
  (e.g. "how far off, in points") and give the two values being compared second.
- **Name every cohort exactly, with a hover that states the cut.** "The 191 Carlson fires" gets a
  tooltip saying which fires and why ("2016–2022, Sentinel-2 scenes, at least 10 burned"); "the 344
  Palmer penguins" says who they are ("adults measured at their nests on three islands, 2007–2009"). Never
  "all fires" or "all penguins" for a subset.
- **Show uncertainty where it exists.** Intervals come from resampling the independent unit (usually
  fires, not buildings); say so in the caption. Grey out cells with too few cases to trust, and say
  what the threshold is.
- **Report the standard breakdowns** when the page is about model performance: structure type, fire
  size (1–9 / 10–100 / >100 destroyed), region, state, and year.
- **Format:** thousands separators (12,345); percentages as "48%"; a few significant digits, not six;
  ranges with an en dash (2016–2022); tabular figures in tables.

## Hover, tap and interaction

- **Everything explains itself on hover** (Carlo, 2026-10-12): every bar, point, cell, tile, axis title,
  legend entry, reference line, column heading and colour key has a tip saying what it is and what it
  shows, in more detail than the label. The page check warns about any chart without tips.
- **Plain language first, technical on a switch.** Plain tips and captions say what a value means and
  **suggest an interpretation** ("What it suggests: not clearly different from the other states").
  Where a reader may want the method (intervals, estimators, definitions, fields), add a technical
  version; the page then shows a **Plain language / Technical** switch (vizkit `tip(meaning=, tech=)`,
  `dual(plain, technical)`; maps: `*_tech` spec fields). Use judgement: not every tip needs both.
- **Hover tips add information or don't exist.** A tip that repeats the label under it is noise
  (Carlo: "if there's no useful additional information … don't put it"). Good tips: the exact count
  and base, how a number was calculated, the cut behind a cohort, what a category means.
- **Every number that needs explaining gets a tip saying how it was calculated.**
- **The cursor never changes on hover-only elements.** No `cursor: help`, the question-mark cursor
  ("really annoys me"). The checker blocks it. A pointer over things that are actually clickable
  (map features that open a card, buttons) is fine.
- **Hover should feel responsive:** a subtle highlight (outline or brightness) on the hovered bar,
  cell or map feature.
- **Everything works by tap and keyboard too.** Tips open on tap and focus; maps open a bottom
  sheet on a phone.

## Colour and keys

- **One colour per concept across every chart on a page, and across a project's pages.** If
  "first call" is green on one chart it is green everywhere; the archetype uses vermillion for burned,
  blue for directly exposed, light blue for indirectly exposed.
- **Colour-blind safe.** Categorical colours: Okabe–Ito (vizkit `SERIES`). Ordered classes (not
  destroyed → destroyed, grades): a green-to-red ramp is fine because Carlo likes it, but always
  print the number or label as well; colour is never the only cue. Map marks carry an outline so
  light colours read on imagery.
- **Keys are big and friendly,** placed above the chart, with text labels, not a tiny legend in a
  corner. On maps the key *is* the layer control: tick a class to hide it, with counts beside every class.
- **Large tables of values get subtle shading** (Carlo, 2026-10-12): tint value cells so the eye finds
  highs and lows at once; numbers stay printed. Choose the scale by meaning: green → yellow → orange →
  red when there is a good and a bad end (say which end is good), a single-hue scale for size without
  judgement, a diverging scale centred on 0 for changes. Don't shade identifiers or years.
- **A red box, rarely:** flag a cell only when a value truly merits attention (fails a target, a clear
  outlier, the headline finding), at most a few per table, with the reason in its hover and the box
  explained in the key.
- **Ordered categories read as a scale:** red → orange → yellow → green with clear dividers, and the
  "no call / no data" categories kept in a separate group so they are not read as a point on the scale.

## Layout

- **Phone and desktop both, decided chart by chart.** Every page is checked at 390 px and 1280+ px
  wide. For each chart pick what reads best on a phone (Carlo, 2026-10-12: "use your best judgment
  each time … a dynamic decision based on what's best case by case"): redraw it narrower, turn rows
  into compact cards, or let a big table scroll with its first column and header frozen. Scrolling a
  wide table is fine; the page itself never scrolls sideways. Don't shrink text to make things fit
  (charts.md, "Phone layout").
- **Light and dark both** (system setting, plus a toggle on chart pages). Dark is welcome.
- **Text never overlaps lines or shapes.** Labels sit outside bars and whiskers; diagrams leave room.
- **A "How to read this" box** for anything non-obvious: what one mark is, what the colours mean,
  what to hover. Short.
- **Iconography and pictures over paragraphs** where a picture explains it: flowcharts for pipelines,
  small icons for repeated concepts (numbered circle badges ① ② for first and second call; house icons
  for building classes). Many short visual blocks beat one wall of text.
- **Self-contained single file** where possible (inline data, CSS and JS; fonts from Google Fonts,
  libraries pinned to an exact version on jsDelivr).

## Every page carries who made it (Carlo, 2026-10-12)

- **Byline under the subtitle:** author, affiliation and the build timestamp in Pacific time
  ("By Carlo Broderick, NCEAS, UC Santa Barbara · 2026-10-12 10:21 PDT"). The default author and the
  logos, links and GitHub details live in identity.json (a personal `~/.config/wri-html-pages/identity.json`,
  else the bundled `references/identity.json`); a page can name another author.
- **Logo strip at the foot:** the NCEAS and WRI (Wildfire Resilience Index) logos, each linking to its
  website, plus the WRI-Science GitHub links. vizkit and build_map add both automatically.

## Every page ends with

- **Sources:** each dataset with its citation, DOI or URL, and licence.
- **A provenance line:** the build date, and the script that built the page *as a repository-relative
  path*. Never an absolute path from this machine (`/home/...`), which the checker blocks.

## Maps specifically

- **Satellite by default for a fire,** with a switcher for aerial (NAIP), street map and hybrid. An
  overview or landing map that shows many fires uses a plain light map, not satellite.
- **Say when the imagery is from.** For damage work, whether the photo is before or after the fire
  changes what the reader sees; note it under the base-map switcher.
- **"Places to look" tabs:** two or three sites of interest in the same fire, one click each.
- **A map can be a panel in a chart page** (Carlo, 2026-10-12) when it is one view among several; the
  page carries the title and sources, and the map must not trap the page's scrolling.
- **Toggle overlays on and off,** each source in its own colour (e.g. footprints vs our model's outlines).
- **Outline the area a result applies to** (fire perimeter, validation domain), with a hover on the
  line saying what it is.
- **Raster results:** show the cells, and where cells group into a structure, the outline of the group.
