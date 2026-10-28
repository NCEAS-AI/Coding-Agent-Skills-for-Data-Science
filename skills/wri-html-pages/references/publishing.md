# Publishing: put pages on the team's GitHub Pages site for collaborators

The team wants every page we make pushed to GitHub so collaborators can view it by link.
`scripts/publish.py` does the whole publish the same way every time, dry run first.

## Publishing is automatic (Carlo, 2026-10-12)

Every visualization this skill makes is published without asking: dry run, fix any check errors, then
`--execute --wait`, then the link. The user should never have to say "push it". Choose the folder
yourself (the project's existing folder, or a new snake_case one) and name it in the reply.
Private data is the exception: data the user calls private, embargoed, personal or
internal-only (WRI team: Overture-derived layers) are not published openly without asking (SKILL.md).

## The site

- The site is `github.pages_repo` in identity.json (personal `~/.config/wri-html-pages/identity.json`, else
  the bundled `references/identity.json`); publish.py derives the SSH remote and
  the Pages URL from it (`github.pages_site` overrides the URL for a custom domain, `github.pages_root`
  the pages folder, `github.pages_remote` the git remote for HTTPS logins). For the WRI team: repo `WRI-Science/public_publication` (needs SSH push access to
  the WRI-Science GitHub organisation), served at
  `https://wri-science.github.io/public_publication/publication_htmls/<folder>/<file>`.
- A new site needs a repo with at least one commit on `main` and GitHub Pages turned on for `main`
  (Settings → Pages → Deploy from a branch → main, / (root)). publish.py creates the folders and READMEs.
- One folder per project or paper under `publication_htmls/` (snake_case: `structure_loss_pipeline`,
  `de_space_canopy_validation`). A new project or paper gets a new folder; a page for an existing one
  goes in that folder. Ask only when it is genuinely unclear which project a page belongs to.
- Each folder has a `README.md` with a line per page and its live link, and an `**Access:**` line.
  `publication_htmls/README.md` lists the folders. publish.py maintains both.
- **File names are the page's short title as a slug, date at the end** (Carlo, 2026-10-12), e.g.
  `penguin-records-around-palmer-station-2026-10-13.html`; the detail lives in the page's
  subtitle (house-style.md, "Titles, subtitles and links"). publish.py refuses a NEW page whose name
  has no date or fewer than three words, or whose `<title>` does not end with the date; existing pages
  from before the rule can still be updated. A living page keeps its name (its start date) while panels
  are added; a new dated page is for a new analysis.
- `publish.py --pull FILE --folder F --to PATH` fetches the current published page, and its panel pages beside it (ungated
  with SLP_PIN if it is gated), so a new session can keep adding to it. Always give `--to` a folder other than the one holding a
  page you just rebuilt (the default writes `./FILE` and would overwrite it). Describe iterations in plain words; an internal tag (`v5`)
  may appear only next to the plain description. Only a folder's `index.html` is exempt.

## Panel pages travel with their page (Carlo, 2026-10-27)

A chart page built with `vk.write_page` has a folder of panel pages beside it, `panels/<page-slug>/`, one per chart card
and map panel (the targets of each panel's **Full screen** and **Copy link** buttons). `publish.py PAGE.html` finds them (every
link marked `data-companion`) and publishes them with the page, with the same access: open, or PIN-gated when the page is (a panel
page is never more public than the page that links it, even a new one added to an already-gated page; publish.py says how many
in a NOTE). They are not listed in the READMEs one by one and they are exempt from the dated-name rule (their titles still end with the date).
**Full screen** on a PIN-gated page opens the panel already unlocked in the same browser session; a person who is sent a **Copy link**
is asked for the PIN (a plain click on Full screen carries the key; Ctrl-click or the middle button does not). A panel page that
lives under another path than `panels/<slug>/<name>.html` is refused, and a page that links panel pages cannot be renamed at
publish (`FILE:NEW_NAME`): rebuild it under the new name with `vk.write_page`. Panel pages link back with `../../<page>.html`;
check_page resolves that against the published folder. If the panel pages are on the site but not in your folder, the page is
refused when it is gated and they are open, or when they come from another build: `publish.py --pull PAGE --folder F` fetches the
page with its panel pages. In the reply, link the page; each panel's own link is on the page (and Copy link gives it). To retire
one panel: add `--remove panels/<page-slug>/<name>.html` to the publish command (vizkit prints it when it deletes the local
copy); `publish.py --remove PAGE.html` takes the panel pages in its own `panels/<file stem>/` folder with it (panel pages it
links in another folder are kept, with a NOTE).

## Access: open by default, PIN only when asked (Carlo, 2026-10-12)

- **Every page is published open** (anyone with the link can view it) unless the user specifically asks
  for a PIN gate. Don't ask about it; don't gate because a folder's other pages are gated.
- **When the user asks for a PIN gate**, pass `--gate`: each page is AES-encrypted and opens in the
  browser after the site PIN. The PIN comes from the environment variable `SLP_PIN`; if it is not set,
  ask the user to run `export SLP_PIN=...` in the session (or add it to `~/.bashrc`). Never write the PIN
  into a file, a commit message, a page, or a chat summary.
- **A page that is already PIN-gated on the site stays gated** when it is updated (someone asked for that
  before); pass `--open` only if the user asks to make it public. publish.py prints a NOTE whenever a
  page goes out open in a folder whose other pages are gated; mention that note to the user in one line.
- Only HTML pages are encrypted. Sidecar files (`data/*.geojson`, images) are public even for a gated
  page, so keep data inline in gated pages.
- `scripts/pin_gate.py --gate IN OUT` / `--ungate IN OUT` encrypt or decrypt a single page; it is
  byte-compatible with the pipeline's `pin_gate_v2.py`, so one PIN entry opens every gated page.

## Workflow

1. **Build the page outside the clone** (project repo or scratchpad). Screenshot it at phone and
   desktop width and look before publishing (see maps.md / charts.md).
2. **Dry run** and read the output:
   ```bash
   python3 $SKILL/scripts/publish.py --folder FOLDER PAGE.html [more files]
   ```
   It syncs its own sparse clone (`~/.cache/public_publication`), works out the folder's access,
   runs `check_page.py` on the plaintext, and prints what it would write and the live URLs.
   Add `--describe "One line"` for a new folder; `--gate` only if the user asked for a PIN; `file.html:new-name.html`
   to publish under another name (not for a page that links panel pages); `--subdir maps` for a subfolder; `--remove old.html`
   to delete one (with the panel pages in its own `panels/<file stem>/` folder).
3. **Fix every check error** (they are real problems: a `/home/...` path, a broken link, an
   unfilled template slot, `cursor: help`, no viewport, a file over 95 MB) and rerun.
4. **Publish** with a commit message in the site's style (the page or folder, then what a reader
   will now see, in a plain sentence), followed by the attribution trailer from the system prompt:
   ```bash
   python3 $SKILL/scripts/publish.py --folder FOLDER PAGE.html --execute --wait \
     -m "Canopy validation page: name each grid by what it is compared with" \
     -m "Co-Authored-By: ..."
   ```
   `--wait` polls each live URL until GitHub Pages serves exactly the committed bytes (usually 1–3 min).
5. **Give the user the link(s), always**, only after `--wait` reports LIVE: the script prints one
   `[title](live URL)` line per page; paste those lines into the reply, as they are, each followed by
   the page's subtitle. From then on, **every reply about that page ends with its link** (SKILL.md,
   "The link goes in every reply"); `publish.py --links` prints the latest link per page if needed. If it reports
   NOT LIVE, say so; a GitHub Actions hiccup is usually fixed by an empty commit to re-trigger Pages.

## Guard rails (built into publish.py; don't work around them)

- Commits only the named files and READMEs, never `git add -A`; never force-pushes; rebases once if
  someone else pushed first.
- Refuses a dirty or diverged clone, a mismatch between `--open`/`--gate` and the folder's access,
  a page name listed in the folder's `.publish-ignore` (retired pages), and any check error.
- A folder's `.publish-forbid` (regular expressions, one per line) blocks internal terms on its pages.
- Deleting published pages (`--remove`) only when the user asked for it.
- Don't publish from a personal checkout of the repo: publish.py keeps its own clean clone, so a
  stale or half-edited checkout can never leak into the site.
