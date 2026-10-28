#!/usr/bin/env python3
"""Publish pages to the team's GitHub Pages site and print their live links.

The site is `github.pages_repo` in references/identity.json (for the WRI team: WRI-Science/public_publication).

WHY THIS EXISTS
    Collaborators see our maps and charts by link, from GitHub Pages. Doing that by hand has gone
    wrong in specific ways: pages copied over from a stale or dirty clone, `git add -A` sweeping
    in other people's work, retired pages coming back, a path off this machine in a published page,
    a page left ungated in a gated folder, a deploy that silently never happened. This script does
    the publish the same way every time and stops on each of those.

WHAT IT DOES (dry run by default; --execute to write, commit and push)
    1. Keeps its own sparse clone (default ~/.cache/<repo name>; env PUBREPO overrides) and
       fast-forwards it to origin/main. Only the files being published and the READMEs are checked
       out, so a folder of 1 GB of maps costs nothing to publish into.
    1b. Finds the panel pages a chart page links with data-companion (panels/<page file stem>/*.html, written by
       vk.write_page: one per chart card, plus each map's own page) and publishes them with it. They are checked like
       any page (and must carry the same build id as the link), take the access of the page that links them (a gated
       page gets gated panel pages; panel pages on the site but not in your folder STOP the publish when they would end up
       less private than their page), are exempt from the dated-name rule, and are not listed in the READMEs or the links
       log. A page that links panel pages cannot be renamed with FILE:NEW_NAME. --pull fetches the panel pages with the page;
       --remove PAGE.html takes the panel pages in its own panels/<file stem>/ folder with it.
    2. Pages are OPEN by default (Carlo, 2026-10-12: "default non-PIN-gated unless I specifically ask").
       --gate encrypts this call's pages behind the site PIN, only when the user asked. A page that is
       already PIN-gated on the site stays gated when updated, unless --open is passed.
    3. Runs check_page.py on the PLAINTEXT of every page (errors stop the publish).
    4. Gates pages with the site PIN when the folder is gated (env SLP_PIN; never written anywhere).
    5. Adds each new page to the folder README (with its live link) and a new folder to
       publication_htmls/README.md (needs --describe).
    6. Commits ONLY the named paths, pushes (rebasing once if someone else pushed first), and with
       --wait polls each live URL until GitHub Pages serves exactly the committed bytes.
    7. Logs every published page (time, title, live URL) to ~/.cache/wri-html-pages/links.tsv;
       `publish.py --links [--folder F]` prints the latest link for each page, newest first.

USAGE
    python publish.py --links [--folder FOLDER]           # latest live link per page, newest first
    python publish.py --pull FILE.html --folder FOLDER [--to PATH]   # current published page, as plaintext, plus its panel pages, to keep building on
    python publish.py --folder FOLDER [--subdir maps] [--gate | --open] [--describe "One line"]
                      [-m "Title: what a reader now sees"] [--execute] [--wait] [--remove OLD.html ...]
                      FILE[:NEW_NAME] [FILE[:NEW_NAME] ...]
    FILE may be .html or a sidecar (.geojson .json .png .jpg .svg .csv .css .js .pdf .webp).
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_page  # noqa: E402

# ============================================================================ settings
def site_config():
    """The publishing site from identity.json (vizkit.identity_path): github.pages_repo (https://github.com/OWNER/REPO), and
    optionally github.pages_site (if served from a custom domain), github.pages_root (folder of pages) and
    github.pages_remote (the git remote, if not SSH: https://github.com/OWNER/REPO.git for HTTPS logins)."""
    from vizkit import load_identity      # personal ~/.config/<skill>/identity.json first, then the bundled one
    gh = load_identity().get("github", {})
    m = re.match(r"https://github\.com/([^/]+)/([^/?#]+?)(?:\.git)?/?$", gh.get("pages_repo", ""))
    if not m:
        sys.exit("publish: STOP: set github.pages_repo in identity.json (https://github.com/OWNER/REPO)")
    owner, name = m.groups()
    site = gh.get("pages_site") or (f"https://{name.lower()}" if name.lower() == f"{owner.lower()}.github.io"
                                    else f"https://{owner.lower()}.github.io/{name}")
    remote = gh.get("pages_remote") or f"git@github.com:{owner}/{name}.git"      # pages_remote: e.g. the HTTPS URL
    return remote, site.rstrip("/"), gh.get("pages_root", "publication_htmls"), name


REPO, SITE, ROOT, _REPO_NAME = site_config()
CLONE = Path(os.environ.get("PUBREPO", Path.home() / ".cache" / _REPO_NAME))
OK_EXT = {".html", ".geojson", ".json", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".csv", ".css", ".js", ".pdf", ".txt"}
WAIT_S, POLL_S = 600, 15
LINKS_LOG = Path.home() / ".cache" / "wri-html-pages" / "links.tsv"   # every published page: when, title, URL
# ============================================================================


def die(msg):
    sys.exit(f"publish: STOP: {msg}")


def git(*args, check=True):
    r = subprocess.run(["git", "-C", str(CLONE), *args], capture_output=True, text=True)
    if check and r.returncode:
        die(f"git {' '.join(args)} failed:\n{r.stderr.strip() or r.stdout.strip()}")
    return r.stdout.strip()


def set_sparse(patterns):
    """Non-cone sparse checkout written directly, so it behaves the same on every git version."""
    git("config", "core.sparseCheckout", "true")
    git("config", "core.sparseCheckoutCone", "false")
    info = CLONE / ".git" / "info"
    info.mkdir(parents=True, exist_ok=True)
    (info / "sparse-checkout").write_text("\n".join(patterns) + "\n")


def sync_clone(patterns):
    if not (CLONE / ".git").exists():
        CLONE.parent.mkdir(parents=True, exist_ok=True)
        print(f"publish: cloning {REPO} (sparse, no blobs) into {CLONE}")
        r = subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout", REPO, str(CLONE)],
                           capture_output=True, text=True)
        if r.returncode:
            die(r.stderr)
        set_sparse(patterns)
        git("checkout", "-q", "main")
    if git("status", "--porcelain"):
        die(f"the publishing clone {CLONE} has uncommitted changes; look at them (git -C {CLONE} status) before going on")
    git("fetch", "-q", "origin", "main")
    if int(git("rev-list", "--count", "origin/main..HEAD") or 0):
        die(f"{CLONE} has commits that are not on GitHub; push or drop them deliberately first")
    set_sparse(patterns)
    git("checkout", "-q", "-B", "main", "origin/main")
    git("sparse-checkout", "reapply")


def access_of(folder_rel: str, dest: Path):
    rd = dest / "README.md"
    if rd.exists():
        m = re.search(r"^\W*Access\W*\s*(PIN[- ]gated|open)\b", rd.read_text(), re.M | re.I)
        if m:
            return "gated" if m.group(1).lower().startswith("pin") else "open"
    names = [n for n in git("ls-tree", "--name-only", "origin/main", folder_rel + "/").splitlines() if n.endswith(".html")]
    if not names:
        return None
    heads = [git("show", f"origin/main:{n}")[:200] for n in names[:3]]
    gated = sum("<!-- pin-gated" in h for h in heads)
    return "gated" if gated == len(heads) else "open" if gated == 0 else "mixed"


def pull_page(folder: str, sub: str, name: str, to: Path | None):
    """Fetch the published page as it is on GitHub now (the living page to keep adding to), with its panel pages
    (panels/<page-slug>/...) beside it, so a rebuild with vk.write_page sees what is already published."""
    base = f"{ROOT}/{folder}/{sub + '/' if sub else ''}"
    rel = f"{base}{name}"
    sync_clone(["/README.md", f"/{ROOT}/README.md", f"/{rel}"])
    if not (CLONE / rel).exists():
        die(f"{rel} is not published")
    pin = os.environ.get("SLP_PIN")

    def plain(txt: str) -> str:
        if "<!-- pin-gated" in txt[:200]:
            if not pin:
                die("that page is PIN-gated: set SLP_PIN to pull its plaintext")
            import pin_gate
            try:
                return pin_gate.ungate(txt, pin)
            except Exception:
                die("SLP_PIN does not open that page (wrong PIN?)")
        return txt
    txt = plain((CLONE / rel).read_text(encoding="utf-8"))
    comps = [c for c in dict.fromkeys(re.findall(r'data-companion="([^"]+)"', txt))
             if re.fullmatch(r"panels/[A-Za-z0-9_-][A-Za-z0-9._-]*/[A-Za-z0-9_-][A-Za-z0-9._-]*\.html", c)]
    if comps:
        sync_clone(["/README.md", f"/{ROOT}/README.md", f"/{rel}"] + [f"/{base}{c}" for c in comps])
    out = (to or Path(name)).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(txt, encoding="utf-8")
    got = 0
    for c in comps:
        f = CLONE / base / c
        if f.exists():
            (out.parent / c).parent.mkdir(parents=True, exist_ok=True)
            (out.parent / c).write_text(plain(f.read_text(encoding="utf-8")), encoding="utf-8")
            got += 1
    print(f"publish: pulled {rel} -> {out}" + (f" and {got} panel page(s) (panels/...)" if comps else ""))


def show_links(folder: str | None):
    """Latest live link per page from the publish log, newest first (for putting the link in a reply)."""
    if not LINKS_LOG.exists():
        print("publish: no pages published from this machine yet")
        return
    seen, rows = set(), []
    for ln in reversed(LINKS_LOG.read_text().splitlines()):
        f = ln.split("\t")
        if len(f) < 6 or (folder and f[1] != folder) or f[4] in seen:
            continue
        seen.add(f[4])
        rows.append(f)
    for when, fold, _name, title, link, acc in rows[:40]:
        print(f"{when[:16]}  {fold}{'  (PIN-gated)' if acc == 'gated' else ''}\n[{title or _name}]({link})")


def pin_gate_ungate_or_empty(txt: str) -> str:
    """The plaintext of a gated page when SLP_PIN is set (and right), else ''."""
    pin = os.environ.get("SLP_PIN")
    if not pin:
        return ""
    import pin_gate
    try:
        return pin_gate.ungate(txt, pin)
    except Exception:
        return ""


def title_of(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def subtitle_of(html: str) -> str:
    m = re.search(r'<meta name="description" content="([^"]*)"', html)
    return __import__("html").unescape(m.group(1)).strip() if m else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--folder", help="folder under publication_htmls/, snake_case")
    ap.add_argument("--links", action="store_true", help="print the latest live link per page (from the log) and stop")
    ap.add_argument("--pull", metavar="FILE", help="write the current published FILE and its panel pages (ungated if needed) to --to and stop")
    ap.add_argument("--to", type=Path, help="where --pull writes (default: ./FILE)")
    ap.add_argument("--subdir", default="")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--gate", action="store_true", help="PIN-gate these pages (only when the user asked)")
    g.add_argument("--open", action="store_true", help="publish open even where the page was PIN-gated before")
    ap.add_argument("--describe", default="", help="one line for a NEW folder (both READMEs)")
    ap.add_argument("-m", "--message", action="append", default=[])
    ap.add_argument("--remove", action="append", default=[], help="published file name to delete (explicit); a page's own panels/<file stem>/ pages go with it; repeat for more")
    ap.add_argument("--no-readme", action="store_true", help="leave the READMEs alone (only for folders that have none by choice)")
    ap.add_argument("--keep-name", action="store_true", help="skip the dated-name rule (legacy pages only)")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--wait", action="store_true")
    a = ap.parse_args()

    if a.links:
        show_links(a.folder)
        return
    if not a.folder:
        die("--folder is required")
    if a.pull:
        pull_page(a.folder, a.subdir.strip("/"), a.pull, a.to)
        return
    if not re.fullmatch(r"[a-z0-9][a-z0-9_]*", a.folder):
        die("--folder must be snake_case (letters, digits, _)")
    sub = a.subdir.strip("/")
    folder_rel = f"{ROOT}/{a.folder}"
    dest_rel = f"{folder_rel}/{sub}" if sub else folder_rel
    items = []
    for f in a.files:
        src, _, name = f.partition(":")
        src = Path(src).expanduser().resolve()
        name = name or src.name
        if not src.exists():
            die(f"{src} does not exist")
        if Path(name).suffix.lower() not in OK_EXT:
            die(f"{name}: not a web file type this site serves")
        if re.search(r"[^A-Za-z0-9._-]", name):
            die(f"{name}: use letters, digits, '.', '_' and '-' only in published names (they become URLs)")
        items.append((src, name))
    # ---- a chart page's panel pages and map pages (vizkit marks each link with data-companion; they live in
    #      panels/<page-slug>/ beside the page) go out with it
    have = {n for _, n in items}
    parent_of: dict[str, set] = {}                      # panel page -> the page(s) that link it
    comps_of: dict[str, list] = {}                      # page -> every panel page it links (local or already on the site)
    builds_of: dict[str, str] = {}                      # panel page -> the build id its link carries
    for src, name in list(items):
        if name.endswith(".html"):
            txt = src.read_text(errors="ignore")
            if "<!-- pin-gated" in txt[:200]:                 # a gated page hides its panel links: read the plaintext
                pin_ = os.environ.get("SLP_PIN")
                if not pin_:
                    die(f"{src.name} is already PIN-gated; set SLP_PIN so its panel pages can be found and published with it")
                import pin_gate
                try:
                    txt = pin_gate.ungate(txt, pin_)
                except Exception:
                    die(f"SLP_PIN does not open {src.name} (wrong PIN?)")
            comps = list(dict.fromkeys(re.findall(r'data-companion="([^"]+)"', txt)))
            if comps and name != src.name:
                die(f"{src.name}: this page links panel pages whose back links name it; build it under the new name "
                    f"({name}) with vk.write_page instead of renaming it here")
            comps_of[name] = comps
            builds_of.update({c: b for c, b in re.findall(r'data-companion="([^"]+)"[^>]*?\sdata-build="([0-9a-f]+)"', txt)})
            for comp in comps:
                if re.search(r"@[0-9a-f]+-\d+@\.html", comp):
                    die(f"{name}: its panel pages were never written (the links still hold placeholders): build the page with "
                        "vk.write_page(dest, page), not dest.write_text(page)")
                if (re.search(r"[^A-Za-z0-9._/-]", comp) or "//" in comp
                        or not re.fullmatch(r"panels/[A-Za-z0-9_-][A-Za-z0-9._-]*/[A-Za-z0-9_-][A-Za-z0-9._-]*\.html", comp)):
                    die(f"{name}: unsafe companion path {comp!r} (a panel page is panels/<page-slug>/<name>.html beside the page)")
                cs = (src.parent / comp).resolve()
                if not cs.is_relative_to(src.parent.resolve()):
                    die(f"{name}: companion {comp!r} resolves outside the page's folder")
                if comp not in have and cs.exists():
                    items.append((cs, comp))
                    have.add(comp)
                if comp in have:
                    parent_of.setdefault(comp, set()).add(name)
    n_comp = sum("/" in n for _, n in items)
    if n_comp:
        print(f"publish: also publishing {n_comp} panel page(s) linked from the page(s) (panels/...)")
    if not items and not a.remove:
        die("nothing to publish")
    if a.keep_name and not a.execute:
        print("publish: --keep-name: name rule skipped for these files (only for pages published before 2026-10-12)")

    patterns = ["/README.md", f"/{ROOT}/README.md", f"/{folder_rel}/README.md", f"/{folder_rel}/.publish-*"]
    patterns += [f"/{dest_rel}/{n}" for _, n in items] + [f"/{dest_rel}/{n}" for n in a.remove]
    sync_clone(patterns)
    dest = CLONE / dest_rel
    folder = CLONE / folder_rel
    existing = set(git("ls-tree", "-r", "--name-only", "origin/main", folder_rel + "/").splitlines())
    is_new = not existing
    a.remove = list(dict.fromkeys(a.remove))
    for n in a.remove:                                   # checked now, in a dry run too, before anything is written
        if re.search(r"[^A-Za-z0-9._/-]", n) or ".." in n.split("/") or f"{dest_rel}/{n}" not in existing:
            die(f"--remove {n}: not published in {dest_rel}")
    extra_rm = []
    for n in list(a.remove):                             # a page's panel pages (same data, same map) go with it
        if n.endswith(".html") and "panels/" not in n:
            d_, base_ = os.path.split(n)
            site_txt = git("show", f"origin/main:{dest_rel}/{n}")
            if "<!-- pin-gated" in site_txt[:200]:
                site_txt = pin_gate_ungate_or_empty(site_txt)
                if not site_txt:
                    die(f"{n} is PIN-gated on the site: set SLP_PIN (the site PIN) so its panel pages can be found and removed with it")
            own = f"{d_ + '/' if d_ else ''}panels/{base_[:-5]}/"     # the page's own folder; a panel page elsewhere may belong to another page
            linked_ = set(re.findall(r'data-companion="([^"]+)"', site_txt))
            linked_ = {(d_ + "/" if d_ else "") + c for c in linked_}
            comps = {c for c in linked_ if c.startswith(own)} | {p[len(dest_rel) + 1:] for p in existing if p.startswith(f"{dest_rel}/{own}")}
            elsewhere = sorted(c for c in linked_ if not c.startswith(own) and f"{dest_rel}/{c}" in existing)
            if elsewhere:
                print(f"publish: NOTE {n} links panel pages outside {own} ({len(elsewhere)}, e.g. {elsewhere[0]}); they are kept: "
                      "remove them with --remove if they belong to this page only")
            extra_rm += [c for c in sorted(comps) if f"{dest_rel}/{c}" in existing and c not in a.remove]
    if extra_rm:
        a.remove += extra_rm
        print(f"publish: also removing {len(extra_rm)} panel page(s) of the page(s) being removed (panels/...)")
        sync_clone(patterns + [f"/{dest_rel}/{n}" for n in extra_rm])
    still_linked = {c for cs_ in comps_of.values() for c in cs_}
    for n in a.remove:
        if n in have or n in still_linked:
            die(f"--remove {n}: a page published in this call still links it")

    # ---- access, page by page: open unless the user asked for the PIN gate (--gate); a page already
    #      gated on the site keeps its gate when updated unless --open says otherwise
    folder_acc = access_of(folder_rel, folder)
    page_access, notes, kept_gated = {}, [], 0
    for _, n in items:
        rel = f"{dest_rel}/{n}"
        if not n.endswith(".html"):
            continue
        if a.gate:
            page_access[n] = "gated"
        elif a.open:
            page_access[n] = "open"
        elif rel in existing and "<!-- pin-gated" in git("show", f"origin/main:{rel}")[:200]:
            page_access[n] = "gated"
            if "/" in n:
                kept_gated += 1
            else:
                notes.append(f"{n}: already PIN-gated on the site, kept gated (pass --open to make it public)")
        else:
            page_access[n] = "open"
            if folder_acc in ("gated", "mixed") and "/" not in n:
                notes.append(f"{n}: OPEN (public). Other pages in {a.folder} are PIN-gated; pass --gate if this one should be too")
    site_only = {c for n, cs_ in comps_of.items() for c in cs_ if c not in have and f"{dest_rel}/{c}" in existing}
    for n, cs_ in comps_of.items():                       # panel pages that are on the site but not in the local folder
        for c in cs_:
            if c in site_only and page_access.get(n) == "gated" and \
                    "<!-- pin-gated" not in git("show", f"origin/main:{dest_rel}/{c}")[:200]:
                die(f"{c} is on the site OPEN but its page {n} is now PIN-gated: publish from the folder where vk.write_page wrote "
                    f"panels/ (so the panel pages are gated with the page), or fetch them first: publish.py --pull {n} --folder {a.folder}"
                    f"{' --subdir ' + sub if sub else ''} --to <folder>/{n}")
    if kept_gated:
        notes.append(f"{kept_gated} panel page(s) already PIN-gated on the site, kept gated (pass --open to make them public)")
    for c in sorted(site_only):                           # a panel page on the site must come from the same build as its link
        want = builds_of.get(c)
        if not want:
            continue
        site_txt = git("show", f"origin/main:{dest_rel}/{c}")
        if "<!-- pin-gated" in site_txt[:200]:
            site_txt = pin_gate_ungate_or_empty(site_txt)
            if not site_txt:
                notes.append(f"{c}: PIN-gated on the site and SLP_PIN is missing or wrong, so its build was not compared with the page's")
                continue
        mb = re.search(r'name="vk-build" content="([0-9a-f]+)"', site_txt[:60000])
        if mb and mb.group(1) != want:
            die(f"{c} on the site is from a different build than the page you are publishing: publish the page from the folder where "
                f"vk.write_page wrote its panels/ (so they go out together), or fetch the published ones first "
                f"(publish.py --pull ... --folder {a.folder}{' --subdir ' + sub if sub else ''} --to <folder>/<page>) and rebuild there")
    for n, cs_ in comps_of.items():
        for c in cs_:
            if c in site_only and page_access.get(n) == "open" and \
                    "<!-- pin-gated" in git("show", f"origin/main:{dest_rel}/{c}")[:200]:
                notes.append(f"{c}: PIN-gated on the site but its page is now open: fetch the panel pages (publish.py --pull) and publish them with --open too")
    inherited = 0
    for comp, parents in parent_of.items():              # a panel page is exactly as private as the page that links it
        if comp in page_access and any(page_access.get(pg) == "gated" for pg in parents) and page_access[comp] != "gated":
            page_access[comp] = "gated"
            inherited += 1
    if inherited:
        notes.append(f"{inherited} panel page(s) PIN-gated like the page that links them")
    access = "gated" if a.gate else "open"           # what a NEW folder's README records
    pin = os.environ.get("SLP_PIN")
    if "gated" in page_access.values():
        import pin_gate
        if not pin:
            die("PIN-gating needs SLP_PIN in the environment (ask the user; never write it into a file)")

    # ---- retired names
    ign = folder / ".publish-ignore"
    globs = [ln.strip() for ln in ign.read_text().splitlines() if ln.strip() and not ln.startswith("#")] if ign.exists() else []
    for _, n in items:
        hit = [gl for gl in globs if fnmatch.fnmatch(n, gl)]
        if hit:
            die(f"{n} matches retired pattern {hit[0]!r} in {a.folder}/.publish-ignore")

    # ---- names: a NEW page's file name is its dated, descriptive title (team rule 2026-10-12)
    for _, n in items:
        rel = f"{dest_rel}/{n}"
        if not n.endswith(".html") or n == "index.html" or rel in existing or a.keep_name or "/" in n:
            continue
        stem = n[:-5]
        words = [w for w in re.split(r"[-_]+", re.sub(r"\b20\d\d-[01]\d-[0-3]\d\b", "", stem)) if w]
        if not re.search(r"20\d\d-[01]\d-[0-3]\d", stem) or len(words) < 3:
            die(f"{n}: a new page's file name must be its short dated title as a slug, e.g. "
                f"penguin-records-around-palmer-station-2026-10-13.html (vizkit.slug(title) makes one)")

    # ---- check, gate, stage
    stage = Path(tempfile.mkdtemp(prefix="publish_stage_"))      # private (0700), unique; holds plaintext copies of gated pages
    __import__("atexit").register(shutil.rmtree, stage, ignore_errors=True)
    known = {p[len(dest_rel) + 1:] for p in existing if p.startswith(dest_rel + "/")} | {n for _, n in items}
    known_dir = stage / "_known"
    for k in known:
        (known_dir / k).parent.mkdir(parents=True, exist_ok=True)
        (known_dir / k).touch()
    forbid = check_page.read_forbid(folder / ".publish-forbid")
    errors, plan, pages = 0, [], []
    for src, name in items:
        out = stage / name
        if not out.resolve().is_relative_to(stage.resolve()):
            die(f"{name}: would be written outside the staging folder")
        if name.endswith(".html"):
            txt = src.read_text(encoding="utf-8")
            plain = txt
            if "<!-- pin-gated" in txt[:200]:
                if not pin:
                    die(f"{src.name} is already gated; set SLP_PIN so it can be checked")
                import pin_gate
                plain = pin_gate.ungate(txt, pin)
            if "/" in name:                          # a panel page: its relative links resolve from panels/<slug>/, as on the site
                flat = stage / "_chk" / os.path.dirname(name) / ("_plain_" + os.path.basename(name))
                roots = [str(src.parent), str(known_dir / os.path.dirname(name))]
            else:
                flat = stage / ("_plain_" + name)
                roots = [str(src.parent), str(known_dir), str(known_dir / os.path.dirname(name))]
            flat.parent.mkdir(parents=True, exist_ok=True)
            flat.write_text(plain, encoding="utf-8")
            res = check_page.check(flat, roots, forbid)
            for lvl, msg in res:
                print(f"publish: check {lvl:5} {name}: {msg}")
            errors += sum(lvl == "ERROR" for lvl, _ in res)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(pin_gate.gate(plain, pin) if page_access[name] == "gated" else plain, encoding="utf-8")
            if "/" not in name:                      # panel pages are listed through their page, not one by one
                pages.append((name, title_of(plain), subtitle_of(plain)))
        else:
            if "gated" in page_access.values():
                print(f"publish: check WARN  {name}: sidecar files are NOT encrypted by the PIN gate; anyone with the URL can read it")
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)
        rel = f"{dest_rel}/{name}"
        plan.append((rel, out, "new" if rel not in existing else "update"))
    if errors:
        die(f"{errors} check error(s); fix the page(s) and run again")

    # ---- READMEs
    url = lambda rel: f"{SITE}/{rel}"
    readme_rel = f"{folder_rel}/README.md"
    rtxt = (folder / "README.md").read_text() if (folder / "README.md").exists() else ""
    touched = []
    if a.no_readme:
        pass
    elif not rtxt:
        if not a.describe:
            die(("new folder" if is_new else f"{a.folder} has no README yet") +
                ": pass --describe 'One line saying what these pages are for' (or --no-readme to skip)")
        heading = a.folder.replace("_", " ").title()
        rtxt = f"# {heading}\n\n{a.describe}\n\n**Access:** open unless a page is marked PIN-gated\n\n## Pages\n"
    for name, title, subt in ([] if a.no_readme else pages):
        relname = f"{sub}/{name}" if sub else name
        if relname in rtxt or f"({name})" in rtxt:
            continue
        lock = " (PIN-gated)" if page_access.get(name) == "gated" else ""
        line = f"- [`{relname}`]({relname}): **{title or name}**{lock}{'. ' + subt if subt else ''} Live: <{url(f'{dest_rel}/{name}')}>\n"
        if "## Pages" not in rtxt:
            rtxt = rtxt.rstrip("\n") + "\n\n## Pages\n"
        rtxt = rtxt.rstrip("\n") + "\n" + line
    for n in a.remove:                                   # a removed page leaves the README too
        relname = f"{sub}/{n}" if sub else n
        rtxt = "".join(ln for ln in rtxt.splitlines(keepends=True) if f"({relname})" not in ln)
    old = (folder / "README.md").read_text() if (folder / "README.md").exists() else None
    if rtxt != old and not a.no_readme:
        touched.append((readme_rel, rtxt))
    top = CLONE / ROOT / "README.md"
    ttxt = top.read_text() if top.exists() else "# Published pages\n"     # a new site has no index yet
    if f"({a.folder}/)" not in ttxt and not a.no_readme:
        if not a.describe:
            die(f"{a.folder} is not listed in {ROOT}/README.md: pass --describe 'One line' to add it")
        touched.append((f"{ROOT}/README.md", ttxt.rstrip("\n") + f"\n\n### [{a.folder}/]({a.folder}/)\n{a.describe}\n"))

    # ---- report
    print(f"publish: folder {a.folder}{' (new)' if is_new else ''}; clone {CLONE}")
    for rel, out, kind in plan:
        acc_ = page_access.get(rel.removeprefix(dest_rel + "/"))
        print(f"publish: {kind:6} {rel}  {out.stat().st_size / 1e6:.2f} MB  {'PIN-gated' if acc_ == 'gated' else 'open' if acc_ else ''}  ->  {url(rel)}")
    for n_ in notes:
        print(f"publish: NOTE {n_}")
    for rel, _ in touched:
        print(f"publish: readme {rel}")
    for n in a.remove:
        print(f"publish: remove {dest_rel}/{n}")
    if not a.execute:
        print("publish: dry run: nothing written. Re-run with --execute (and -m 'Title: what a reader now sees').")
        shutil.rmtree(stage, ignore_errors=True)
        return

    # ---- write, commit, push
    if not a.message:
        die("--execute needs -m 'Page or folder: what a reader will now see' (plus the attribution trailer)")
    paths = []
    for rel, out, _ in plan:
        (CLONE / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out, CLONE / rel)
        paths.append(rel)
    for rel, txt in touched:
        (CLONE / rel).write_text(txt)
        paths.append(rel)
    for n in a.remove:
        rel = f"{dest_rel}/{n}"
        if rel not in existing:
            die(f"--remove {n}: not published in {dest_rel}")
        git("rm", "-q", "--", rel)
    if paths:
        git("add", "--", *paths)
    if not git("diff", "--cached", "--name-only"):
        print("publish: nothing changed (identical files already published)")
    else:
        msg = []
        for m in a.message:
            msg += ["-m", m]
        git("commit", "-q", *msg)
        for attempt in (1, 2):
            r = subprocess.run(["git", "-C", str(CLONE), "push", "-q", "origin", "HEAD:main"], capture_output=True, text=True)
            if not r.returncode:
                break
            if attempt == 2 or "rejected" not in (r.stderr + r.stdout):
                die(f"push failed:\n{r.stderr.strip()}")
            print("publish: someone pushed first; rebasing once")
            git("pull", "-q", "--rebase", "origin", "main")
        print(f"publish: pushed {git('rev-parse', '--short', 'HEAD')}: {a.message[0]}")
    shutil.rmtree(stage, ignore_errors=True)

    # ---- confirm the live site serves exactly these bytes
    live = [(rel, hashlib.sha256((CLONE / rel).read_bytes()).hexdigest()) for rel in paths if not rel.endswith("README.md")]
    titles = {f"{dest_rel}/{n}": t for n, t, _ in pages}

    def link_lines(rels):
        print("publish: links for the reply (paste as they are):")
        for rel in rels:
            if rel.removeprefix(dest_rel + "/").count("/"):
                continue                                        # a panel page: its page links to it
            print(f"[{titles.get(rel) or rel.rsplit('/', 1)[-1]}]({url(rel)})")

    LINKS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with LINKS_LOG.open("a") as fh:                       # the record behind `publish.py --links`
        for rel, _ in live:
            if rel.endswith(".html") and not rel.removeprefix(dest_rel + "/").count("/"):
                acc_ = page_access.get(rel.rsplit("/", 1)[-1], "open")
                fh.write("\t".join([time.strftime("%Y-%m-%dT%H:%M:%S%z"), a.folder, rel.rsplit("/", 1)[-1],
                                    (titles.get(rel) or "").replace("\t", " "), url(rel), acc_]) + "\n")
    if not a.wait:
        print("publish: not yet confirmed live (GitHub Pages rebuilds in ~1-3 min; use --wait to confirm)")
        link_lines([rel for rel, _ in live])
        return
    t0, pending = time.time(), dict(live)
    while pending and time.time() - t0 < WAIT_S:
        for rel, h in list(pending.items()):
            try:
                body = urllib.request.urlopen(urllib.request.Request(url(rel) + f"?v={int(time.time())}",
                                              headers={"Cache-Control": "no-cache"}), timeout=30).read()
                if hashlib.sha256(body).hexdigest() == h:
                    print(f"publish: LIVE {url(rel)}  ({time.time() - t0:.0f} s)")
                    del pending[rel]
            except Exception:
                pass
        if pending:
            time.sleep(POLL_S)
    for rel in pending:
        print(f"publish: NOT LIVE after {WAIT_S} s: {url(rel)} (check the repo's Actions tab; an empty commit re-triggers Pages)")
    link_lines([rel for rel, _ in live if rel not in pending])
    sys.exit(1 if pending else 0)


if __name__ == "__main__":
    main()
