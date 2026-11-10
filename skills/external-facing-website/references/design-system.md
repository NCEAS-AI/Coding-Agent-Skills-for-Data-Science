# Design system

The look of both source pages, as shipped in `assets/site.css` (read it for the exact rules). The brief: approachable,
high-end, calm. Change the look here and in `site.css`, never with one-off inline styles in a spec.

## Tokens (`:root` in site.css)

| Token | Value | Use |
|---|---|---|
| `--bg` / `--paper` | `#ffffff` / `#f7f5f0` | white sections and cards / warm alternate sections, footer, chips |
| `--ink` / `--muted` / `--faint` | `#15212b` / `#5b6670` / `#8a949c` | text / ledes, card text / source lines under stats |
| `--line` / `--line-2` | `#e6e2da` / `#d6d1c6` | hairlines, card borders / buttons, logo separators |
| `--navy` / `--navy-2` / `--navy-hover` / `--navy-soft` | `#003660` / `#1d4f7c` / `#0a4a80` / `#e8eef4` | title, CTAs, numbers, bars / links, focus / hover / icon tiles |
| `--gold` / `--gold-ink` / `--gold-soft` | `#febc11` / `#8a6400` / `#fff6dc` | bullets, second bar series, flow arrow / **gold text** (AA on white) / callouts |
| `--right` | `#2f8f5b` | good-result numbers on map tiles |
| `--flag` / `--flag-ink` | `#7C3AED` / `#6D28D9` | the weak case: tile top border, number, flag label, pop-up border (purple, so it never reads as an error alarm and never as "good" green) |
| `--wrong` | `#b3261e` | errors only |
| hatch | `#fdecb4` / `#fffaf0` | chart "gap" columns (not in the record) |
| `--radius` / `--radius-s` | 16px / 10px | cards / small tiles; pills 999px |
| `--wrap` / `--read` | 1180px / 42rem | content width / section-head reading width |

Map categories (set in the map embed, not the page): hit `#C2410C`, miss `#7C3AED`, false alarm `#FACC15`, correct
standing `#38BDF8`, other `#9AA3AD`. Keep classes few and explained on hover.

## Type

- **Source Serif 4** 600 for the title, h2, card titles, big numbers and avatars; **Inter** 400-700 for everything else.
  Both are inlined as base64 (latin subsets, SIL OFL), so nothing loads from outside.
- Body 17px / 1.65. Title `clamp(2rem, 3.6vw, 3.25rem)` navy, max 20ch (the owner asked for a smaller title).
  h2 `clamp(2rem, 3.6vw, 2.9rem)`. Program line and eyebrows: Inter 600 uppercase gold-ink; eyebrows .9rem / .12em
  (enlarged from .76rem at the owner's request).
- Numbers: tabular figures. `text-wrap: balance` on headings.

## Layout

- Header: logo row (UCSB | NCEAS | Wildfire Resilience Index at matched visual weight: 15 / 30 / 28 px tall), nav
  pills, the CTA as a navy pill last, a Lock button on locked pages.
- Hero on white; then sections **strictly alternate** paper / white (the builder does it); footer on paper.
- Sections pad `clamp(64px, 9vw, 112px)`; cards pad `clamp(22px, 3vw, 32px)`; cards on paper lose the border and get
  a soft shadow.
- Tiles **in a row**, never one per row on desktop (one per row leaves large white gaps).

Breakpoints: from 1241 (the nav is tighter and right-aligned; a locked page shows its first 5 section links, the
CTA pill and Lock; an open page its first 7 and the CTA), 1240 (tablet: nav shows only the CTA pill, right-aligned), 1060 (4-up tiles → 2), 1020 (4 who-it-helps cards → 2),
960 (steps → 1), 900 (team of 3 → 1), 860 (two-up cards → 1, stats → 2 × 2), 820 (4 map tiles → 2), 760 (rows of 3
tiles / cards / map tiles → 1 (never 2 + 1); map 76vh, chart compact: 210 px tall, odd x labels hidden, gap label
hidden), 700 (pop-up full width), **640 phone** (nav hidden, first logo on its own row, Lock button top right,
tiles → 1, team of 2 → 1), 620 (map tiles → 1), 600 (who-it-helps → 1), 560 (bar rows stack), 400 (chart
annotation wraps).

## Components (spec type → classes)

| Spec | Classes | Notes |
|---|---|---|
| hero | `.hero .program .bigtitle #lede .ctas .btn(.solid) .pill` | |
| map | `.mapframe(.dashed) iframe#mapiframe .whypop .under .sqcard(.flagged) .flag .go details.checks .maplegend` | Pop-up sits inside the frame, top right, clear of the map's own place list; full width on phones. |
| tiles / pipeline | `.steps(.tiles) .step.card .ico .k .chips details.places .placelist .flowtitle .nw .arrow` | Flow title halves never wrap (`.nw`). |
| chart | `.card.yrchart .ctop .tot .plot(--n) .yax .area .grid .cols .col(.gap) .ann .gaplab .xax .key details` | Pure HTML/CSS; columns are not tab stops, the "See the numbers" table is the accessible version; `.plot` has `role="img"` + a sentence. |
| cards | `.uses .use.card` | Gold-dot bullets. |
| stats | `.stats .stat b span em`, `.card.acc .mkey .mrow .mname .bars .bar` | Navy = first series, gold = second. |
| prose | `.limits-text` (alias `.prose`) | Max 54rem, `<b>` in ink. |
| cta | `.two.partner .card.pcard ol .rel .btn` | |
| team | `.team .person.card .avatar .role .plinks` | |
| refs | `.card.refbox .reflist` or `details.places` | |
| footer | `footer .logos .disc` | |

Also in site.css, unused by the builder but generic: research-phase tabs (`.phase-tabs`, ARIA tabs), a stacked share
band (`.bands`), a scatter card (`.scatter`, `.callout`), "today vs next" lists (`.covers`), a dark navy band
(`.fund`), `details.why`, `table.data`, `.notyet`. Add a builder section type before using them on a page. The `.fund`
band must never carry a price or a funding ask (`content-and-claims.md`, rule 18): use it for a partnership call only.

**Never use the bare class `card` alone** (`class="card"`): wri-html-pages' check_page treats that as a chart card
and warns about missing chart tools. Every card here has a second class.

## Behaviour (inline script, no libraries)

- One `#tip` element: mouse shows at the cursor (flipped to stay on screen), touch shows on tap (not on links or
  clickable map tiles), keyboard focus shows it under the element; Escape, scroll and clicks hide it. Each tip is
  also a hidden `aria-describedby` copy for screen readers.
- Map tiles: click / Enter / Space → `postMessage({goPlace})` to the iframe's origin; the weak tile also opens the
  pop-up, and a `{placeShown}` message from the map does the same.
- Lock button: clears the session key (`slp_key_v2`, `slp_pin`) and reloads to the lock screen.

## Do and don't

- Do keep it light only (`color-scheme: light`; check_page's "no dark-mode styles" warning is expected).
- Do inline every image and font (a web-font stylesheet stalled the lock screen in testing).
- Do grey the map's satellite base map (saturation -1, brightness-max ~0.82) so data colours stand out, and draw
  each area's edge as a white dashed line with a dark halo (navy is invisible on grey).
- Don't put stats in the hero; don't stack tiles one per row on desktop; don't box explanations under the map
  (put colour meanings in hover tips); don't use green for a weak result; don't add a second accent colour.
- Don't put media rules before the base rule they override (a phone pop-up was clipped that way).
