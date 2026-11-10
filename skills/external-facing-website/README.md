# external-facing-website

Landing pages for a research program, made for people outside the team (partners, agencies, funders, the public),
in the look of the team's National Wildfire Structure Loss Record page: built as one self-contained HTML file,
locked behind a branded PIN screen, checked on a desktop, tablet and phone, published to your GitHub Pages site and
handed back as a link. Ask your agent for one ("make an external site for the canopy validation work", "a
partner-facing page for this program, PIN-locked", "add the new accuracy numbers to the program site") and it gathers
the facts, writes the page, checks every claim, locks it, publishes it and gives you the link.

**Reference page (open):**
[National Wildfire Structure Loss Record](https://wri-science.github.io/public_publication/publication_htmls/structure_loss_pipeline/national-wildfire-structure-loss-record-2026-11-06.html)
(rebuilt by `examples/wildfire-structure-loss-record.json`).

## What every page gets, without being asked

- **A page organised around the outside reader**: a one-paragraph pitch, the map or main visual second, why it
  matters (with a chart), what you get, who it helps, accuracy with the scope of every number, an honest limits
  section, a concrete partner call, the team and the data credits. Sections only where there is real content.
- **One honest weak case** on the map, flagged, with a "Likely reasons / What would help" pop-up.
- **A branded lock screen** (aerial photo, logos, program name, contact) instead of a bare PIN box, with nothing on
  it that is data. Open instead of locked when you say the page is public.
- **One self-contained file**: fonts, logos and icons inlined, light only, hover / tap / keyboard tooltips, no
  sideways scroll on a phone.
- **Checked before it ships**: spec validation (missing fields, broken anchors, local paths, totals that don't add
  up), wri-html-pages' page check, screenshots at three sizes, an adversarial fact-check of every claim, and a
  fresh-browser test that the PIN opens the page.

## Install

Needs the [`wri-html-pages`](../wri-html-pages/) skill **1.13.0 or newer in the same skills folder**: its
`check_page.py`, `screenshot.py`, `pin_gate.py` (the PIN lock and the branded screen), `publish.py` and
`build_map.py` do the checking, locking, publishing and maps, and its `identity.json` says where pages go. Copy this
folder next to it (for Claude Code, `~/.claude/skills/external-facing-website`; for an OpenClaw agent, the workspace
`skills/` folder). If wri-html-pages lives elsewhere, set `EFW_PAGES_SKILL=/path/to/wri-html-pages`.
`python3 scripts/efw.py --where` shows what was found.

## Setup

One optional file, `~/.config/external-facing-website/site.json` (or `$EFW_SITE_CONFIG`), overrides
`references/site.json` key by key and survives updates:

```json
{"contact": {"name": "Your Name", "email": "you@your.org"}}
```

The contact appears on the partner button and the lock screen. Teams outside UCSB / NCEAS / WRI also set `logo_row`
(their own logo files next to that site.json), `program_line`, `institutions_text` and `og_image`. The PIN is never
stored there or anywhere else: give it to the session as `SLP_PIN` when publishing a locked page.

## Requirements

- Python 3.9+ (`build_site.py`, `new_site.py`, `efw.py` use only the standard library).
- `cryptography` for the PIN lock (`pin_gate.py`, `verify_gate.py`).
- Chrome or Chromium and `websocket-client` for screenshots and `test_lock.py`.
- git push access to the GitHub Pages site (through wri-html-pages' `publish.py`).
- Map embeds load MapLibre and map tiles from the internet; nothing else on the page does.

## Files

| Path | What it is |
|---|---|
| `SKILL.md` | What the agent is told to do, and when. |
| `references/content-and-claims.md` | The honesty rules, section patterns, copy style and the claims pass. |
| `references/site-spec.md` | The spec format, with an annotated example. |
| `references/design-system.md` | Tokens, type, layout, breakpoints, components, do and don't. |
| `references/lock-screen.md` | The branded lock screen, what may be on it, how to check it, keeping addresses locked. |
| `references/publishing.md` | Publishing with wri-html-pages, aliases, maps, Pages stalls, links. |
| `references/review.md` | Screenshots, interactions, the fact-check and the release checklist. |
| `references/site.json` | Default settings (contact, logos, lock-screen photo). |
| `scripts/build_site.py` | Spec → one HTML page with the lock-screen blocks. |
| `scripts/new_site.py` | Starts a spec with every section and `FILL:` markers. |
| `scripts/verify_gate.py` | Checks a locked file: branded, nothing leaked, opens with the PIN. |
| `scripts/test_lock.py` | Fresh-browser PIN test of a local file or the live URL. |
| `scripts/efw.py` | Finds wri-html-pages and the settings. |
| `assets/` | Stylesheet, schema, fonts, logos, favicon, lock-screen photo; sources in `assets/SOURCES.md`. |
| `examples/` | The wildfire page as a spec (public wording only), with a README. |

## License

Code and text: CC0-1.0, like the rest of this repository. Fonts (`assets/fonts/`): SIL Open Font License 1.1
(`assets/fonts/OFL.txt`). The UC Santa Barbara, NCEAS and Wildfire Resilience Index logos (`assets/logos/`,
`assets/favicon.png`) are their owners' marks, not covered by CC0: use them only on those teams' pages. The aerial
photo is USDA NAIP imagery (public domain).

## Version history

- **1.0.0** (2026-11-09): first version, distilled from the team's two landing pages and the owner's rounds of
  feedback on them (Nov 2026): the PIN-locked research-program page whose design, components and branded lock screen
  it reuses (none of its content), and the open National Wildfire Structure Loss Record page, whose structure and
  wording are the example. Generic builder from a JSON spec, branded lock-screen blocks, spec validation, lock
  verification and a fresh-browser PIN test.
