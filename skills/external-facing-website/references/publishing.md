# Publishing a landing page

Landing pages are published with wri-html-pages' `publish.py` to the team's GitHub Pages site
(`identity.json` `github.pages_repo`; for the WRI team, WRI-Science/public_publication: "publish this to the WRI public
GitHub" means that repo). Read `$PAGES/references/publishing.md` once; this page adds what is specific to landing pages.

## Names and folders

- The file is `slug-of-title-YYYY-MM-DD.html` (build_site names it when OUT is a folder); the `<title>` is
  `Program name · YYYY-MM-DD`. publish.py requires both (at least three words in the title). **Keep the start date
  when updating**, so the address never changes. `--site-page` exists only in newer publish.py versions and is not
  needed here, because the title carries its date.
- One folder per program (`--folder snake_case_name`, `--describe "one line"` the first time: public).
- The map embed is its own page, `*-map-embed-YYYY-MM-DD.html` with a dated `<title>`, in the **same folder**,
  referenced by relative `src`, and published **in the same call** so check_page resolves the link and both get the
  same access.

## Steps

```bash
python3 $PAGES/scripts/publish.py --folder FOLDER --describe "one public line" --gate PAGE.html MAP_EMBED.html   # 1. dry run: read it all
python3 $PAGES/scripts/publish.py --folder FOLDER --describe "one public line" --gate PAGE.html MAP_EMBED.html --execute --wait \
  -m "Program site: what a reader now sees, in one plain sentence" -m "Co-Authored-By: ..."      # 2. publish
```

- `--describe` is needed only the first time a folder is used (publish.py stops with "new folder: pass --describe").
- The dry run fetches and fast-forwards publish.py's local clone of the Pages repo (network, no push); it changes
  nothing on GitHub.
- `--gate` (PIN) is this skill's default, on purpose, although publish.py's own help calls open the default.
  `--open` only when the user confirms the page is public, and never on an address that was locked. publish.py does
  not enforce this: a new page in a gated folder goes out OPEN with only a note, so read the dry run for "OPEN". The PIN comes from `$SLP_PIN` or the publisher's secure PIN source; never type it into a saved file.
- Fix every check error and rerun; never work around a guard rail (dirty clone, `.publish-forbid`).
- Before publishing, check nobody else pushed newer edits to the same page (another agent, a teammate):
  `python3 $PAGES/scripts/publish.py --pull PAGE.html --folder FOLDER --to current.html` and diff. Never race
  another publish.
- `--wait` polls until Pages serves the committed bytes. Then run the live checks (`lock-screen.md`) and only then
  hand over `[Title · date](live URL)`; `publish.py --links --folder FOLDER` reprints links.

## Two addresses for one page (aliases)

When people were emailed an address that later changes (a new name, a new folder), keep the old address working:

- Publish a copy of the page at the **exact old path** (`PAGE.html:old-name.html`, or `--folder OLD_FOLDER`), with
  iframe `src` changed to the **absolute** URL of the embed in the canonical folder.
- **Republish the alias every time the page changes**, in the alias's original lock state (locked stays locked, with
  the branded blocks). Record both addresses in the project notes so the next round remembers.
- "Replace it completely" from the owner means overwrite; the old content stays recoverable from git (note the commit).

## Maps

Build the embed with wri-html-pages (`$PAGES/references/maps.md`, `build_map.py`, `build_page(spec, dir, embed=True)`):
light theme, a greyed satellite base map, a frames layer that draws each area's edge as a white dashed line with a dark
halo (`{"color": "#FFFFFF", "width": 2, "dash": [3, 2], "halo": true, "halo_color": "#0B1218"}`), the first place tab
being the first case (no "whole area" tab), the colour key in the map's own panel. To let the page's tiles move the map,
append a small script to the embed that listens for `message` events with `{goPlace}` from the parent (check
`event.origin`) and clicks the matching place button, and posts `{placeShown}` back when a place is chosen in the map.
Pick dense example areas (~2.7 km windows), tighten windows that are mostly empty, and keep the embed small
(4.6 MB, 0.5 MB gzipped was fine).

## When GitHub Pages stalls

- `gh run list -R OWNER/REPO --limit 5` to see the Pages deploy; a re-run can sit queued for more than 20 minutes.
- Nudge it: `gh api -X POST repos/OWNER/REPO/pages/builds`, or push an empty commit through publish.py's clone.
- Say "live" only when the live bytes match the commit (`--wait` reports LIVE). Don't wrap publish.py in a `timeout`
  command (macOS has none, and a wrapper once made a good publish "fail" with exit 1).

## Links

- Click every link on the live page once (nav anchors, tiles, partner mailto, team pills, references, footer).
- An open page must not link to a locked page; strip such links when a target becomes locked.
- check_page already fails on `#anchors` with no target and relative links to files not published alongside.

## After each round

Write a short handoff for the owner's agent (if there is one): live URL(s), commit, what changed and why, open
questions, "nothing emailed", and a request to log the round on the project's task card. Keep a backup of the spec
before each round (`SPEC.json.bak-pre-roundN`) and keep the fact-check diff.
