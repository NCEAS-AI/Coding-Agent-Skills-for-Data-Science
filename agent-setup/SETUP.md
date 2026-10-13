# Coding-Agent Skills for Data Science: Interactive Setup

This repository holds skills that teach AI coding agents to do whole data-science jobs the way a
research team does them. This file is the **installer**: it puts a skill where your coding tool finds
it, checks that your machine can run it, and records your own settings (your name, your team, your
publishing site) where updates won't overwrite them.

This is a **living repo**: the skills keep improving. What you install is a snapshot, so re-run this
setup whenever you want the latest. Your personal settings carry over.

---

> ### If you are an AI coding agent
> Read this entire file, then run the setup with the user, phase by phase. Your goal: install the skill
> the user picks into the tool they are using, in that tool's correct location, with **their** settings,
> and prove it works. Install from this repo's files (clone or download them), never from memory.

> ### If you are a human
> Paste this repo's URL into your coding agent and tell it: *"Read `agent-setup/SETUP.md` and follow it
> to install a skill for me."* It will ask you a few questions and install it. Or follow the phases
> below by hand; each one says exactly what to do.

---

## Ground rules for the agent (read before starting)

- **Show before you write.** Before writing or overwriting any file, list what you will write and
  where, and get a yes. If a skill of the same name is already installed, ask before replacing it and
  offer to back it up first.
- **Say what runs.** Skills contain scripts. Before running any of them, tell the user which scripts
  and what they do (each script's header says). System checks are announced once, not asked per command.
- **Detect, then confirm.** Read objective facts yourself (OS, Python, Chrome, git, the time zone, the
  name in `git config user.name`); ask only what is genuinely the user's call.
- **One question at a time,** with the default in `[brackets]`. Accept "default" or "skip". Skip
  questions made moot by earlier answers.
- **Don't trust your memory for tool conventions.** Check the target tool's current skills folder
  against its docs before installing. The table in Phase 1 is a starting point, checked 2026-10-13.
- **Never put secrets in files.** No PINs, tokens or passwords in any file you write. The optional page
  PIN only ever comes from an environment variable.
- **Real data only.** Never make a test page from made-up data. To test publishing, use the user's own
  real data, or skip it.
- **Ask before installing software.** Offer the exact `pip install` command; don't run it unasked.
- **The user wins.** Where the user's preference differs from a default here, do what they say.

---

## Phase 0: Pick the setup mode and the skill

**A. How should I gather your system details?**
- **[Auto, recommended]** "I'll check your machine myself with read-only commands (OS, Python and its
  packages, Chrome, git, your GitHub access, your time zone) and fill in what I can, then ask only the
  questions that are yours to answer."
- **Ask me instead:** "Don't check anything; I'll tell you."

**B. Which skill?** List the folders in `skills/` with the first line of each `README.md`. Today there is
one, so propose it and confirm:

| Skill | What it does |
|---|---|
| `wri-html-pages` | Turns any data-visualization request into an interactive HTML page (maps, charts, tables) in a house style, checks it for statistical rigor and on a phone, publishes it to a GitHub Pages site, and links it. |

---

## Phase 1: Identify the tool and where its skills live

Ask: **"Which coding tool are you installing this for?"** Propose what you can infer (you are probably
running inside it; an existing `.claude/`, `.cursor/`, `.agents/`, `.github/` or `.gemini/` folder is a
hint). Then ask: **personal (all your projects) or this project only? [personal]**

Known locations, checked against each tool's documentation on 2026-10-13. **Verify before relying on
them:**

| Tool | Personal | One project | Notes |
|---|---|---|---|
| Claude Code | `~/.claude/skills/<name>/` | `.claude/skills/<name>/` | [docs](https://code.claude.com/docs/en/skills) |
| Cursor | `~/.cursor/skills/` or `~/.agents/skills/` | `.cursor/skills/` or `.agents/skills/` | Also reads the Claude and Codex folders. [docs](https://cursor.com/docs/context/skills) |
| Codex | `~/.agents/skills/` | `.agents/skills/` | [docs](https://learn.chatgpt.com/docs/build-skills) |
| GitHub Copilot (VS Code, CLI) | `~/.copilot/skills/` or `~/.agents/skills/` | `.github/skills/`, `.claude/skills/` or `.agents/skills/` | [docs](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) |
| Gemini CLI | `~/.gemini/skills/` or `~/.agents/skills/` | `.gemini/skills/` or `.agents/skills/` | [docs](https://geminicli.com/docs/cli/skills/) |
| Claude (claude.ai, desktop app) | Settings → Capabilities → Skills → upload a `.skill` zip | | Builds pages but cannot push them to GitHub. |
| Anything else | see [agentskills.io](https://agentskills.io) | | |

**Several tools?** Install once to `~/.agents/skills/` (Cursor, Codex, Copilot and Gemini CLI read it)
and, for Claude Code, also to `~/.claude/skills/` (Cursor reads that too). A symbolic link from one to
the other avoids two copies on macOS and Linux.

**How to install (ask, default first):**
- **[Copy]** a snapshot of `skills/<name>/` into the skills folder. Simple; re-run this setup to update.
- **Linked to a clone** (for people who'll update often or contribute): clone this repo somewhere
  permanent (e.g. `~/src/Coding-Agent-Skills-for-Data-Science`) and symlink `skills/<name>` into the
  skills folder. `git pull` then updates the skill. Personal settings live outside the clone (Phase 4),
  so pulls never conflict with them.

---

## Phase 2: Check what the skill needs

**If the user chose Auto:** say once that you're about to run read-only checks, then run them and
report a short table (found / missing / how to fix). **If they chose Ask me:** ask for the same facts.

For `wri-html-pages`:

| Need | Check | If missing |
|---|---|---|
| Python 3.10+ | `python3 --version` | install Python 3.10 or newer |
| `websocket-client`, `Pillow` (screenshots) | `python3 -c "import websocket, PIL"` | `python3 -m pip install --user websocket-client pillow` |
| `tzdata` (Windows only) | `python -c "import zoneinfo; zoneinfo.ZoneInfo('America/Los_Angeles')"` | `python -m pip install tzdata` |
| `cryptography` (only for PIN-gated pages) | `python3 -c "import cryptography"` | `python3 -m pip install --user cryptography` |
| `geopandas` / `rasterio` (only for maps from shapefiles, GeoPackages or rasters) | `python3 -c "import geopandas"` | install in the environment the user's project already uses |
| Chrome or Chromium (screenshots) | Linux: `command -v google-chrome chromium chromium-browser`; macOS: `ls "/Applications/Google Chrome.app"`; Windows: `Test-Path "C:\Program Files\Google\Chrome\Application\chrome.exe"` | install Chrome, or set `CHROME=/path/to/chrome` |
| git | `git --version` | install git |
| GitHub login | `ssh -T git@github.com` (greets the user by name) | SSH keys, **or** an HTTPS login (`gh auth login` or a credential manager): then use the HTTPS remote in Phase 4 |

Screenshots are how the agent checks every page on a desktop and a phone; without Chrome the skill
still builds and publishes pages but can't look at them, so say so plainly.

---

## Phase 3: Ask the user

Ask in order, one at a time, skipping what earlier answers settle.

1. **Which team's site do you publish to?**
   **[The WRI team: `WRI-Science/public_publication`]** / another team's or your own GitHub Pages site.
2. **Your name, as it should appear in every page's byline?** *(propose `git config user.name`)*
   Then **affiliation** *(free text)* and **time zone** *(propose the detected one)*.
3. *(Not the WRI team)* **Which GitHub Pages repo should pages go to?** `https://github.com/OWNER/REPO`.
   If they don't have one yet, walk them through making it (they do this in the browser): a new
   repository, public, initialised with a README; then Settings → Pages → Build and deployment →
   Deploy from a branch → `main`, `/ (root)`. Pages then appear at `https://OWNER.github.io/REPO/`.
4. *(Not the WRI team)* **Which organisations should each page credit?** For each: short name, full
   name, website, and a logo file (SVG or PNG), or none. Also the GitHub link for the footer (label and
   URL). **Never reuse the NCEAS or Wildfire Resilience Index logos for other teams' work.**
5. **Publish without asking?** **[Yes: every visualization is published and linked automatically]**
   (how the WRI team works) / ask before publishing each new page. Remind them that GitHub Pages are
   public to anyone with the link.
6. *(If they use an HTTPS login rather than SSH keys)* Confirm you'll set the HTTPS remote.
7. *(Only if they bring it up)* **PIN-gated pages:** pages can be encrypted behind a PIN when the user
   asks for it. The PIN is set per session with `export SLP_PIN=...` and is never written to a file.
   On the WRI team, ask Carlo for the site PIN.

---

## Phase 4: Assemble and install

Build this, show it all, get a yes, then write it.

1. **The skill folder.** Copy (or link, per Phase 1) `skills/<name>/` to the chosen location, so that
   `<location>/<name>/SKILL.md` exists. Get the files from a clone of this repo, or from
   `dist/<name>.skill` (a zip whose top folder is `<name>/`).
2. **Personal settings,** outside the skill folder so updates never overwrite them:
   `~/.config/wri-html-pages/identity.json` (Windows: `%USERPROFILE%\.config\wri-html-pages\identity.json`).
   Start from the skill's `references/identity.json` and change:
   - `author`, `affiliation`, `timezone` (an IANA name like `America/Denver`): from question 2.
   - *(Not the WRI team)* `orgs`: from question 4 (`logo` is a file name; put the logo files in the same
     folder as this identity.json); `github.label`, `github.url`, and `github.pages_repo`: from question 3.
   - *(HTTPS login)* `github.pages_remote`: `https://github.com/OWNER/REPO.git`.
   - Optional: `github.pages_site` if the site uses a custom domain; `github.pages_root` to publish into a
     folder other than `publication_htmls/`.
   - Keep the `_why` line; update it to say whose settings these are.
3. **Ask-before-publishing** *(only if chosen in question 5)*: in the installed `SKILL.md`, section
   "Automatic: every visualization is built, published and linked", replace
   "**publish it to GitHub automatically** (do not ask whether to push)" with
   "**ask before publishing each new page**, then publish", and add a line to the top of that section:
   "(Set at install: this user asked to confirm each new page before it is published.)" Tell the user
   this edit must be redone after an update; the setup will do it again.
4. **claude.ai:** there is no settings folder there, so build a personal zip instead: copy the skill
   folder, put the personal settings into its `references/identity.json` (and logos into `assets/`),
   zip the folder (top folder `<name>/`), name it `<name>.skill`, and give the user that file to upload.
5. Add a short note in the identity file's `_why`: installed from
   `NCEAS-AI/Coding-Agent-Skills-for-Data-Science` on `<date>`, version `<metadata.version from SKILL.md>`.

---

## Phase 5: Test it, and tell the user what you did

Run, from the installed skill folder (call it `SKILL`), telling the user what each does:

1. **Settings load:**
   `python3 SKILL/scripts/publish.py --links` (works and prints any pages already published), and
   `python3 -c "import sys; sys.path.insert(0, 'SKILL/scripts'); import vizkit, publish; print(vizkit.identity_path()); print(vizkit.byline()); print(publish.REPO, publish.SITE)"`.
   Check the byline shows **their** name and the site is **their** site.
2. **Screenshots work:**
   `python3 SKILL/scripts/screenshot.py https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/chart-archetype-palmer-penguins-size-species-sex-2026-10-13.html /tmp/skill-test --sizes phone`
   should write `/tmp/skill-test_phone.png` with no errors. Show it to the user if you can display images.
3. **Publishing access** (without publishing anything): clone the pages repo shallowly into a temporary
   folder and run `git push --dry-run origin HEAD:refs/heads/access-check` there. Success means they can
   publish; nothing is pushed. Delete the temporary folder.
4. **The tool sees the skill:** ask the user to start a new session and ask the agent "what skills do
   you have?" (or open the tool's skills panel). `wri-html-pages` should be listed.

Then tell the user plainly:
- **What** you installed, **where**, and where their personal settings are.
- **How to use it:** just ask for any chart, map or table of their data, e.g. *"map these sites"*,
  *"chart body mass by species"*, *"add a panel with the yearly totals"*. The agent builds, checks,
  publishes and links the page; later requests add panels to the same page.
- **How to change the house style:** tell the agent ("make the dots bigger on every map"); it
  edits the skill's references and templates.
- **How to update:** re-run this setup (or `git pull` if linked). Personal settings carry over.

Encourage them to read the skill's `SKILL.md` and `references/house-style.md`. They are short, they shape
every page the agent makes, and we'd really appreciate comments or corrections.

---

## Quick reference

**Always installed:** the whole skill folder (instructions, references, scripts, templates, examples).

**Asked, not assumed:** which tool and scope, copy or link, your name and affiliation, which site and
which logos, publishing without asking, HTTPS vs SSH, and installing any missing Python packages.

**Never written anywhere:** PINs, tokens, passwords.
