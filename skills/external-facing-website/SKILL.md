---
name: external-facing-website
description: "Make an outward-facing landing page for a research program or project (for partners, agencies, funders, the public) as one polished, self-contained HTML file in the WRI / NCEAS landing-page style: serif title, one-paragraph pitch, framed map with an honest weak case, why-it-matters tiles and chart, what you get, who it helps, accuracy with scope, limits, partner call, team. PIN-locked by default behind a branded login screen, checked on desktop and phone, published with the wri-html-pages skill and handed back as a link. Use whenever the user asks for an external-facing, public-facing, partner or funder website, landing page, program or project page, outreach site, microsite or pitch page, a PIN-locked page with a branded login screen, a site like the wildfire structure-loss page, or critiques or updates one. Not for a team's main website or data-exploration chart pages (wri-html-pages)."
license: CC0-1.0 for code and text; fonts in assets/fonts are SIL OFL 1.1 (assets/fonts/OFL.txt); the logos in assets/logos are not covered (see README.md); the aerial photo is USDA NAIP imagery (public domain)
compatibility: Needs the wri-html-pages skill 1.13.0 or newer in the same skills folder (check_page.py, screenshot.py, pin_gate.py, publish.py, build_map.py), Python 3.9+, cryptography for the PIN lock, Chrome or Chromium and websocket-client for screenshots and the lock test, and git push access to the GitHub Pages site. The builder itself is standard library only. Map embeds load MapLibre and tiles from the internet.
metadata:
  version: "1.0.0"
  author: "Carlo Broderick (NCEAS, UC Santa Barbara)"
  source: "https://github.com/NCEAS-AI/Coding-Agent-Skills-for-Data-Science"
  requires: "wri-html-pages>=1.13.0"
---

# external-facing-website: program landing pages, PIN-locked, published by link

Version 1.0.0 (2026-11-09). A page made with this skill looks and reads like the team's National Wildfire Structure
Loss Record page and its PIN-locked sibling program page: a slim logo bar, a serif title, short sections alternating
white and warm paper, soft cards, hover tips, light only, and a branded lock screen. It tells an outside reader what
the program does now, what it gives them, how well it works, where it is weak, and how to work with the team.

`SKILL` below is this skill's folder. `PAGES` is the wri-html-pages skill installed next to it;
`python3 $SKILL/scripts/efw.py --where` prints both, the page skill's version and the settings file in use.

## When to use it

- A page about a program or project for people outside the team: partners, agencies, funders, the public.
- Updating, critiquing or re-publishing such a page (keep its address; see `references/publishing.md`).
- Not for: data-exploration maps and charts (wri-html-pages), slide decks (wri-html-decks), or the team's main website.

## Access: one rule

- **A new address is PIN-locked** behind the branded lock screen (the owner's default for this skill, 2026-11-09; it
  replaces the earlier "open unless asked" default for program overviews). Build with the lock-screen blocks and
  publish with `--gate`.
- **If the request says "public" or "open"**, that can mean "for outsiders" or "unlocked": before the first publish,
  ask once, in one sentence: "Open to anyone, or behind the PIN screen?" Then follow the answer.
- **An address that was ever locked stays locked**, because publishing a locked address open, even briefly, exposes
  it. publish.py will not stop you: `--open` silently makes a page public, and a new page (an alias) in a gated
  folder goes out OPEN with only a note. Pass `--gate` explicitly, read the dry run for the word OPEN, and check
  the live file with `verify_gate.py`.
- publish.py's own help says pages are open by default and `--gate` is used only when asked. **This skill overrides
  that on purpose**: `--gate` is the default here.
- Never write, echo or commit the PIN: it comes from `$SLP_PIN` in the session or the publisher's secure PIN source.
  Ask the user for it only if neither exists.

## Read first

1. `references/content-and-claims.md`: the honesty rules and section patterns. **Read all of it every time**; every
   round of the source pages surfaced new overclaims.
2. `references/site-spec.md`: the spec format, with a full annotated example.
3. At the step that needs it: `references/review.md` (step 4), `references/lock-screen.md` (step 5),
   `references/publishing.md` (steps 6 and 7), `references/design-system.md` (changing the look or adding a component).

## The workflow

1. **Gather the facts, a source for every number.** Read the program's own result notes, papers and data
   documentation. Write each number down with where it came from (document and section). Compute nothing new unless
   the computation is recorded and re-runnable; when an outside publisher's count differs from yours, use theirs and
   footnote the difference. Ask the owner for anything missing (team titles, contact, what may be shown) and, for a
   program outside the Wildfire Resilience Index, **which institutions it belongs to**: the default logo row, lock-screen
   text and footer links name UCSB, NCEAS and WRI (change them in the spec's `gate` and `footer` or in `site.json`).
2. **Write the site spec** (one JSON file). Start with
   `python3 $SKILL/scripts/new_site.py SPEC.json --title "Program name" --sections hero,tiles,cards,prose,cta,team,footer`
   (only the sections you have content for; the default adds map, pipeline and stats too; `chart` and `refs` on
   request) or from `examples/wildfire-structure-loss-record.json`. Build the structure around **why an outside reader
   would care**; the owner's own structure always wins over the skeleton (3 tiles, no chart, no map are fine). Every
   number slot is `FILL:` text until a sourced number replaces it; put the source in `src`. A map, if any, is built
   first as its own page with `$PAGES/scripts/build_map.py` (`references/publishing.md`, "Maps").
3. **Build:** `python3 $SKILL/scripts/build_site.py SPEC.json OUT_DIR/` writes
   `OUT_DIR/<slug-of-title>-<date>.html` (one file: fonts, logos, favicon and lock-screen photo inlined; folders are
   made). It stops on missing fields, unfinished text (`FILL:`, TODO, TBD), a placeholder contact, unsafe HTML, local
   paths, broken `#anchors` and totals that do not add up. For a review copy while facts are still missing (the owner
   asked for "TBD"), add `--draft`: those only warn, and the page carries a "Draft for review" bar and cannot pass
   `verify_gate.py`, so it is never published. Add `--no-gate-blocks` only for a page that will be published open.
4. **Check** (`references/review.md`):
   - `python3 $PAGES/scripts/check_page.py PAGE.html` (the "no dark-mode styles" warning is expected: light only by design).
   - `mkdir -p shots`, then `python3 $PAGES/scripts/screenshot.py PAGE.html shots/full --full --sizes desktop,tablet,phone`,
     the header at `--sizes desktop,laptop,phone` and the map alone with `--hash map --wait 20`; then **look** at every
     image. Exit status 1 means JS errors or sideways scroll on a phone. Use `--hash SECTION` below a tall map.
   - A **claims pass**: an independent, adversarial fact-check of every sentence with a number or a claim against its
     source (subagents when you have them; `references/content-and-claims.md` says how), then fix and re-check.
     Every round, including copy-only changes.
5. **Lock it** (`references/lock-screen.md`): `SLP_PIN=... python3 $PAGES/scripts/pin_gate.py --gate PAGE.html PAGE.gated.html`,
   then `python3 $SKILL/scripts/verify_gate.py PAGE.gated.html --expect "a heading"` (branded, no content on the
   unencrypted screen, decrypts) and `python3 $SKILL/scripts/test_lock.py PAGE.gated.html --wrong-pin` (fresh
   browser: lock screen, PIN opens it, opens again without a prompt, no console errors). Screenshot the lock screen at
   desktop, tablet and phone. Delete the local `.gated` copy afterwards; publish.py gates again itself.
6. **Publish** with wri-html-pages (`references/publishing.md`): dry run first,
   `python3 $PAGES/scripts/publish.py --folder FOLDER --describe "one public line" --gate PAGE.html [MAP_EMBED.html]`
   (`--describe` only for a new folder; it is public), read it all, then add
   `--execute --wait -m "Program site: what a reader now sees" -m "Co-Authored-By: ..."`. The dry run already talks to
   GitHub (it fast-forwards publish.py's local clone) but changes nothing there. Map embeds go in the same call so they
   get the same access. Pages built here keep a dated `<title>`, so `--site-page` is not needed.
7. **Verify live, then hand over the link.** After `--wait` reports LIVE: download the live page
   (`curl -s URL > live.html`) and run `verify_gate.py live.html --expect ...`, then `test_lock.py URL` (it also checks
   that the gated map embed opens inside the page without a second PIN prompt). Click every link once. Only then give
   the user `[Title · date](live URL)`, say what changed and that nothing was emailed.

## Rules that apply every time

- **Say what the program does now, never what it does not do yet.** Model outputs are "research estimates, not
  inspections / official results", in the hero and the footer disclaimer, because a model's call is sometimes wrong
  and readers act on what a page claims. A program with no results yet says what it will produce, and no more.
- **Lead with the cases it is built for, and show one weak case honestly**: a flagged tile with a pop-up headed
  "Likely reasons" (never "Why" unless proven on that case's own data) and "What would help", linking to the partner
  section. An honest Limits section in plain prose, no statistics. Hiding weak cases costs trust; leading with them
  undersells the work.
- **Every number carries its scope** (which cases, where, when, which class), how it was tested (held out?) and how
  it was summarized (pooled or per-case; show both when they differ), because fact-checks kept finding numbers that
  read as the whole population. Never compare numbers measured differently.
- **Every number traces to a primary source** (`src` in the spec; build_site writes it as an HTML comment, public in
  the page source, so cite documents, never private paths). Citing your own page is not a source.
- **Nothing private on a public page or on the lock screen**, because both are readable by anyone with the link (the
  lock screen is not encrypted): no licensed partner records (only attributed aggregates), no pending partner names,
  no links from an open page to locked pages, no data paths, no PINs. The lock screen holds names, logos, links, a
  contact and a public-domain photo only. The file name, `<title>`, meta description, commit message and folder
  README are public even when the page is locked.
- **Structure from the audience**: hero (one compact paragraph, no Q-and-A opener, no stats), then the map or main
  visual, then why it matters, what you get, who it helps, accuracy, limits, work with us, team. The owner rejected a
  page that copied another page's structure, so start from what this program's readers need. Sections alternate
  paper and white; the nav follows the order; "Work with us" is the navy pill.
- **Far fewer words**: about one sentence per card; define jargon on first use; US spelling; plain specific terms.
  Every round of feedback asked for fewer words.
- **One file, nothing loaded from outside** except the map iframe (a web-font stylesheet once stalled the lock screen).
- **Keep addresses working**: update the page in place (its title keeps its start date); an emailed address gets an
  alias copy republished with every change, in its original lock state (`references/publishing.md`), because
  people keep and forward links.
- **Nothing is emailed or sent** as part of building a site; email drafts stay drafts. Sending is the owner's call.
- **Check before every publish** that no one else (e.g. another agent) pushed newer edits; never race another
  publish, or one round silently overwrites the other.
- **Fix what is reversible yourself**; ask the owner only about real choices (titles that differ from the roster,
  deleting files, open vs locked when the request is ambiguous, wording of a claim you cannot source), because
  the owner wants fixes, not questions, for anything that can be undone.

## Files

| Path | What it is |
|---|---|
| `scripts/build_site.py` | Spec → one self-contained HTML page (+ the branded lock-screen blocks). Validates the spec. |
| `scripts/new_site.py` | Starts a spec with every section in the recommended order and `FILL:` markers. |
| `scripts/verify_gate.py` | Checks a gated file: branded, no content on the lock screen, decrypts and holds `--expect` text. |
| `scripts/test_lock.py` | Fresh-browser unlock test (types the PIN from `$SLP_PIN`), local file or live URL. |
| `scripts/efw.py` | Finds wri-html-pages and the settings; `--where` prints them. |
| `assets/site.css` | The shared stylesheet (tokens, components, breakpoints). |
| `assets/site-spec.schema.json` | JSON Schema of the spec (build_site validates against it). |
| `assets/fonts/`, `assets/logos/`, `assets/favicon.png`, `assets/lock-aerial-naip.jpg` | Inlined into every page; licences in `assets/SOURCES.md`. |
| `references/site.json` | Default settings (contact, logo row, lock-screen photo); personal copy in `~/.config/external-facing-website/site.json`. |
| `references/*.md` | The guides named above. |
| `examples/wildfire-structure-loss-record.json` | The open wildfire page as a spec (public wording only). |

Settings: `~/.config/external-facing-website/site.json` (or `$EFW_SITE_CONFIG`) overrides `references/site.json` key by
key; put the partner contact there (`{"contact": {"name": "...", "email": "..."}}`). Logos for another team go next to it.
Never put a PIN there. `$EFW_PAGES_SKILL` points at wri-html-pages if it is not next to this skill.
