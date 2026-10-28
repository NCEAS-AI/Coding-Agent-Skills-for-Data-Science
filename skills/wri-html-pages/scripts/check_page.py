#!/usr/bin/env python3
"""Pre-publish check for an HTML page: the things a collaborator should never meet.

WHY THIS EXISTS
    Generalised from the structure-loss site's "newcomer test" (structure-loss-pipeline/scripts/
    site_newcomer_test.py). Every rule below is a mistake that has already reached a published page
    once: a path off this machine, a link to a page that was never copied, a template placeholder,
    the question-mark cursor, a file too big for GitHub. publish.py runs this on the PLAINTEXT page
    before anything is gated or committed; errors stop the publish.

    On vizkit chart pages (2026-10-27) it also checks the panel pages: a link to a panel page that was never written (or
    still holds a placeholder name) says to use vk.write_page; a panel page must carry the same build id as the link to it
    (an error when the page and a panel page come from different builds); each chart card should have the Full screen /
    Copy link buttons (warning, unless the card was made with standalone=False); an embedded map built by an older vizkit
    has no own-page marker (warning). A panel page's own title may be short: it carries the page's title.

USAGE
    python check_page.py PAGE.html [PAGE.html ...] [--site-dir DIR ...] [--forbid FILE]
    Exit status 0 = no errors (warnings allowed), 1 = errors.

    --site-dir   extra directories where relative links may resolve (e.g. the destination folder in
                 the publishing clone, so links to pages already published count as resolved)
    --forbid     file of regular expressions (one per line, # comments) that must not appear, e.g.
                 internal model tags or code names; a folder's `.publish-forbid` is read automatically
"""
from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

# ============================================================================ settings
WARN_MB, FAIL_MB = 25, 95
LOCAL_PATH = re.compile(r"(?<![\w.])/(?:home|mnt|var/tmp|tmp|Users|scratch)/[\w.\-]+")
TEMPLATE_SLOT = re.compile(r"__[A-Z][A-Z_]{2,}__|\{\{[^}]{1,40}\}\}")          # unfilled template slot, anywhere
UNFINISHED = re.compile(r"\blorem ipsum\b|\bTODO\b|\bFIXME\b|\bXXX\b|\bPLACEHOLDER\b", re.I)
EMAIL = re.compile(r"\b[\w.+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")
CURSOR_HELP = re.compile(r"cursor\s*:\s*help")
DATE = re.compile(r"\b20\d\d-[01]\d-[0-3]\d\b")
UNPINNED_CDN = re.compile(r"""(?:src|href)=["'](https://(?:cdn\.jsdelivr\.net/npm|unpkg\.com)/(?:@[\w-]+/)?[\w.-]+)(/|["'])""")
# ============================================================================


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.ids, self.title, self._in_title, self.viewport = [], set(), "", False, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a and a["id"]:
            self.ids.add(a["id"])
        if tag == "a" and a.get("name"):
            self.ids.add(a["name"])
        for k in ("href", "src"):
            v = a.get(k)
            if v and not (tag == "link" and a.get("rel") in ("preconnect", "dns-prefetch")):
                self.refs.append(v)
        if tag == "title":
            self._in_title = True
        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def visible_text(html: str) -> str:
    """Page text with <script>/<style> bodies removed (JSON data blocks are not prose)."""
    return re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)


def check(path: Path, site_dirs=(), forbid=()) -> list[tuple[str, str]]:
    out = []
    err = lambda m: out.append(("ERROR", m))
    warn = lambda m: out.append(("WARN", m))
    raw = path.read_bytes()
    mb = len(raw) / 1e6
    if mb > FAIL_MB:
        err(f"{mb:.0f} MB: GitHub rejects files over 100 MB")
    elif mb > WARN_MB:
        warn(f"{mb:.0f} MB: slow on a phone; consider sidecar data or simplifying")
    html = raw.decode("utf-8", errors="replace")
    if "<!-- pin-gated" in html[:200]:
        warn("page is already PIN-gated; checks need the plaintext (publish.py ungates it with SLP_PIN)")
        return out
    p = Links()
    p.feed(html)
    panel_page = 'name="vk-panel-page"' in html.split("</head>", 1)[0]    # a panel's own page is itself the target of the buttons
    t = re.sub(r"\s+", " ", p.title).strip()
    if not t or t.lower() in {"document", "untitled", "page"}:
        err("missing or generic <title>")
    elif path.name != "index.html" and not path.name.startswith("_plain_index.html"):
        # team rule 2026-10-12: a short, specific title ending in the build date; the detail goes in the
        # subtitle; the title also becomes the file name and the link text
        if not re.search(DATE.pattern + r"\s*$", t):
            err(f"<title> must end with the build date (… · YYYY-MM-DD): {t!r}")
        if len(re.findall(r"[A-Za-z][\w'’-]*", DATE.sub("", t))) < 3 and not panel_page:
            err(f"<title> is too vague ({t!r}); say what the page shows in a few words")
        if len(t) > 100 and not panel_page:
            warn(f"<title> is {len(t)} characters; keep it short and put the detail in the subtitle")
        if 'name="generated"' not in html:
            warn('no <meta name="generated"> recording when the file was built')
        if 'rel="icon"' not in html:
            warn("no browser-tab icon (the WRI flame); build with vizkit or build_map, which add it")
        if 'property="og:image"' not in html:
            warn("no link-preview image (og:image): Slack and email show no flame; build with vizkit or build_map")
    if not p.viewport:
        err('no <meta name="viewport">: the page will not lay out on a phone')
    for m in sorted(set(LOCAL_PATH.findall(html)))[:5]:
        err(f"absolute path off this machine: {m}")
    text = visible_text(html)
    for m in sorted(set(TEMPLATE_SLOT.findall(html)))[:5]:
        err(f"unfilled template slot: {m!r}")
    for m in sorted(set(UNFINISHED.findall(text)))[:5]:
        err(f"unfinished text: {m!r}")
    if CURSOR_HELP.search(html):
        err("cursor: help (the question-mark cursor): the team asked for the cursor never to change on hover")
    for m in sorted(set(EMAIL.findall(re.sub(r"<[^>]+>", " ", text))))[:3]:
        warn(f"e-mail address in the page: {m} (fine only if it is meant as a contact)")
    if "prefers-color-scheme" not in html:
        warn("no dark-mode styles (prefers-color-scheme)")
    for m in sorted(set(UNPINNED_CDN.findall(html)))[:3]:
        if not re.search(r"@\d", m[0]):
            warn(f"library loaded without an exact version: {m[0]}")
    cards = visible_text(html).split('<div class="card">')[1:]          # chart cards of vizkit pages (not script text)
    bare = sum('data-tip=' not in c and 'class="mapframe"' not in c for c in cards)   # a map panel has its own hover cards
    if bare:
        warn(f"{bare} chart card(s) with no hover explanations: every bar, point, cell, axis and legend entry should have one")
    unchecked = sum('class="checks"' not in c for c in cards if '<h3' in c)
    if unchecked:
        warn(f"{unchecked} chart card(s) without a rigor pass (vk.card(checks=[...]); references/rigor.md)")
    vt = visible_text(html)
    if not panel_page:
        old_maps = len(re.findall(r'<iframe class="mapframe"(?![^>]*data-own-page=)', vt))
        if old_maps:
            warn(f"{old_maps} map panel(s) built by an older vizkit have no page of their own (no data-own-page marker): "
                 "rebuild with the current vizkit.map_panel and vk.write_page (on a living page, re-add the panel with the same id)")
    plain_cards = sum('data-companion="' not in c and 'class="pcopy"' not in c and 'class="pbtn pcopy"' not in c
                      and '<!--nopanel-->' not in c for c in cards if '<h3' in c)
    if plain_cards and not panel_page:
        warn(f"{plain_cards} chart card(s) without the 'Full screen' and 'Copy link' buttons (vk.card adds them; "
             "rebuild with the current vizkit and write the page with vk.write_page; on a living page re-add the panel with the same id)")
    for rx in forbid:
        for m in sorted(set(re.findall(rx, text)))[:3]:
            err(f"forbidden term ({rx}): {m!r}")
    roots = [path.parent, *map(Path, site_dirs)]
    for m in re.finditer(r'data-companion="([^"]+)"[^>]*?\sdata-build="([0-9a-f]+)"', vt):    # a panel page and its link come from one build
        f = next((r / unquote(urlparse(m.group(1)).path) for r in roots if (r / unquote(urlparse(m.group(1)).path)).is_file()), None)
        if f is None:
            continue                                                  # a missing file is reported below
        mb = re.search(r'name="vk-build" content="([0-9a-f]+)"', f.read_text(encoding="utf-8", errors="replace")[:60000])
        if mb and mb.group(1) != m.group(2):
            err(f"the panel page {m.group(1)} is from a different build than this page (older or newer): "
                "rebuild the page with vk.write_page(dest, page) and publish all of it")
    for ref in p.refs:
        u = urlparse(ref)
        if u.scheme in ("http", "https", "mailto", "data", "javascript", "tel") or ref.startswith("//"):
            continue
        if ref.startswith("#"):
            if ref[1:] and unquote(ref[1:]) not in p.ids:
                err(f"in-page link to a missing anchor: {ref}")
            continue
        target = unquote(u.path)
        if not target:
            continue
        if not any((r / target).exists() for r in roots):
            if target.startswith("panels/") or target.startswith("@@PANELS@@"):
                err(f"panel page not written: {ref} (build the page with vk.write_page(dest, page), not dest.write_text(page))")
            else:
                err(f"relative link to a file that is not published alongside: {ref}")
    return out


def read_forbid(f: Path | None):
    if not f or not f.exists():
        return []
    return [ln.strip() for ln in f.read_text().splitlines() if ln.strip() and not ln.lstrip().startswith("#")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pages", nargs="+", type=Path)
    ap.add_argument("--site-dir", action="append", default=[])
    ap.add_argument("--forbid", type=Path)
    a = ap.parse_args()
    bad = 0
    for pg in a.pages:
        fb = read_forbid(a.forbid) + read_forbid(pg.parent / ".publish-forbid")
        res = check(pg, a.site_dir, fb)
        for lvl, msg in res:
            print(f"{lvl:5} {pg.name}: {msg}")
        bad += any(l == "ERROR" for l, _ in res)
        if not res:
            print(f"OK    {pg.name}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
