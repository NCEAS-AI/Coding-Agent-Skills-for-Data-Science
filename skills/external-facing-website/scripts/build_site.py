#!/usr/bin/env python3
"""Build one outward-facing research-program landing page from a JSON site spec.

WHY THIS EXISTS
    The team's two landing pages for outside readers (a PIN-locked research-program page and the open National
    Wildfire Structure Loss Record, Nov 2026) were each hand-built by a one-off script that copied the other's
    stylesheet, fonts and logos out of a built HTML file. The owner wanted that approachable, high-end look made
    repeatable. This script is that look, made generic: you write WHAT the page
    says in a JSON spec (references/site-spec.md; schema in assets/site-spec.schema.json) and it writes ONE
    self-contained HTML file in the shared design: slim logo bar, serif title, sections alternating white and warm
    paper, soft cards, hover tooltips, light only. Fonts, logos, favicon and the lock-screen photo are inlined, so
    the page and its PIN lock screen load nothing from outside (a web-font stylesheet once stalled the lock screen);
    the only outside request is the optional map iframe.

    It also writes the four blocks that make the wri-html-pages PIN gate (pin_gate.py >= 1.13.0) draw the BRANDED
    lock screen (photo panel, logos, program name, contact) instead of the bare "Enter PIN" box, because the owner
    asked for that screen on every locked page. Use --no-gate-blocks for a page that will be published open.

    It stops on mistakes that reached the source pages once: missing fields, a section id used twice, an #anchor
    with no target, a local file path or unfinished text (FILL:, TODO, TBD) in the copy, a placeholder contact, a
    chart total that does not add up ("assert_sum"), a weak-case pop-up for a place that has no tile. Text fields are
    HTML snippets checked against an allow-list (a few inline tags, safe attributes, http/https/mailto links), so spec
    text can never run script on the page or break out of the lock-screen blocks. --draft builds a marked review copy
    that only warns about unfinished text. Every number in the spec may carry a "src" note,
    written only as an HTML comment next to the number so a fact-checker can trace it (it is in the page source:
    cite a document and section, never a private path; --no-src leaves the notes out).

USAGE (Python 3.9+, standard library only)
    python3 build_site.py SPEC.json OUT.html             # or OUT_DIR/ -> OUT_DIR/<slug-of-title>-<date>.html
    python3 build_site.py SPEC.json OUT.html --no-gate-blocks   # open page: no lock-screen blocks, no Lock button
    python3 build_site.py SPEC.json --validate                  # check the spec (contact, assets too) only
    python3 build_site.py SPEC.json OUT_DIR/ --draft            # review copy: TBD / FILL: / placeholder contact warn only
    Then: wri-html-pages check_page.py, screenshot.py, pin_gate.py --gate (see SKILL.md).
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import re
import math
import os
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import efw  # noqa: E402

SCHEMA_PATH = efw.ASSETS / "site-spec.schema.json"

# 24px line icons, stroke 1.7 (the wildfire page's set plus a few generic ones)
ICONS = {
    "clock": '<path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z"/><path d="M12 7v5l3 2"/>',
    "patch": '<path d="M4 5h7v6H4zM13 5h7v14h-7zM4 13h7v6H4z"/>',
    "gap": '<path d="M3 17l5-5 4 4 8-8"/><path d="M16 8h4v4"/>',
    "house": '<path d="M3 11l9-7 9 7"/><path d="M5 10v9h14v-9"/>',
    "sat": '<rect x="3" y="5" width="7.5" height="14" rx="1.5"/><rect x="13.5" y="5" width="7.5" height="14" rx="1.5"/><path d="M15.5 9l3 3M18.5 9l-3 3"/>',
    "table": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M9 9v11"/>',
    "flame": '<path d="M12 21c-4 0-7-2.8-7-6.6 0-3.6 2.6-5.6 3.6-8.4.4 1.8 1.4 2.9 2.6 3.4C11.4 6.6 12.6 4.3 15 3c-.4 3.2 4 5.8 4 11.4 0 3.8-3 6.6-7 6.6z"/>',
    "shield": '<path d="M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z"/>',
    "flask": '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4a2 2 0 0 0 1.8-3l-5-9V3"/><path d="M7.5 15h9"/>',
    "city": '<path d="M3 21h18M4 10h16M12 3l8 4H4z"/><path d="M6 10v8M10 10v8M14 10v8M18 10v8"/>',
    "map": '<path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2z"/><path d="M9 4v14M15 6v14"/>',
    "doc": '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/>',
    "people": '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.5"/><path d="M16 14.2c2.9.4 5 2.8 5 5.8"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M21 20H3"/>',
    "handshake": '<path d="M3 12l4-4 4 2 3-2 4 1 3 3"/><path d="M7 8v5l4 4 2-2 2 2 2-2-5-5"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9S14.5 18.4 12 21c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/>',
    "leaf": '<path d="M5 19c0-8 5-14 15-15-1 10-7 15-15 15z"/><path d="M5 19l7-7"/>',
    "drop": '<path d="M12 3s6 6.4 6 11a6 6 0 0 1-12 0c0-4.6 6-11 6-11z"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l5 5"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.8 2.8L16.5 9"/>',
}
ARROW = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
         'aria-hidden="true"><path d="M3 8h10M9 4l4 4-4 4"/></svg>')
LOCK = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">'
        '<rect x="3" y="7" width="10" height="7" rx="1.5"/><path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2"/></svg>')
PRIVATE_PATH = re.compile(r"(/Users/|/home/|/tmp/|/mnt/|/scratch/|/var/tmp/|/private/|/Volumes/|/srv/|/opt/|/data\d*/|"
                          r"file://|(?<![\w/])~/|\b[A-Za-z]:\\|(?<![\w.-])[A-Za-z][\w.-]*:/(?!/))")
UNFINISHED = re.compile(r"\b(TODO|TBD|TBC|FIXME|XXX|PLACEHOLDER|lorem)\b|FILL:|number from a source", re.I)
PLACEHOLDER_EMAIL = re.compile(r"@(example\.(org|com|net|edu)|[\w.-]+\.(test|invalid|example|localhost))$", re.I)
EMAIL = re.compile(r"^[^@\s<>\"'&]+@[^@\s<>\"'&]+\.[A-Za-z]{2,}$")
# ids the page itself uses: a section with one of these would hijack the tooltip, the logo rows, the map or the lock
RESERVED_IDS = {"tip", "logos", "logos2", "lede", "bigtitle", "mapiframe", "lockbtn", "whypop", "whypopt", "pin", "f", "err", "ph"}

# Text fields are small HTML snippets. Everything not on these allow-lists is refused (an allow-list, because
# browsers accept far more ways to run script than a deny-list can name: /onerror=, javascript: links, <base>, ...).
SAFE_TAGS = {"b", "strong", "i", "em", "a", "br", "span", "sup", "sub", "abbr", "small", "code", "u", "s"}
SAFE_ATTRS = {"href", "class", "data-tip", "title", "style", "target", "rel", "lang"}
SAFE_DECL = re.compile(r"^\s*(color|background|background-color|font-weight|font-style|white-space|text-decoration)\s*:\s*"
                       r"(#[0-9a-fA-F]{3,8}|var\(--[a-z0-9-]+\)|[a-z-]+|[1-9]00)\s*$", re.I)
SCRIPTY = re.compile(r"[\s/\"'](on[a-z]+)\s*=|(java|vb)script\s*:", re.I)   # a second net under the parser


class SpecError(Exception):
    pass


def url_problem(u: str, iframe: bool = False) -> str | None:
    """None when a link target is safe: http(s), mailto (links only), #anchor or a relative path."""
    raw = re.sub(r"[\x00-\x20\x7f]", "", html.unescape(str(u)))       # browsers drop tabs/newlines inside a scheme
    m = re.match(r"([a-zA-Z][a-zA-Z0-9+.-]*):", raw)
    ok = ("http", "https") if iframe else ("http", "https", "mailto")
    if m and m.group(1).lower() not in ok:
        return f"{m.group(1)}: addresses are not allowed (use {', '.join(ok)}, a #anchor or a relative path)"
    return None


class _HTMLCheck(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.errs: list[str] = []
        self.data: list[str] = []

    def _tag(self, tag, attrs):
        if tag not in SAFE_TAGS:
            self.errs.append(f"<{tag}> is not allowed in text (allowed: {', '.join(sorted(SAFE_TAGS))})")
        for k, v in attrs:
            v = v or ""
            if k not in SAFE_ATTRS:
                self.errs.append(f"attribute {k!r} on <{tag}> is not allowed (allowed: {', '.join(sorted(SAFE_ATTRS))})")
            elif k == "href" and url_problem(v):
                self.errs.append(f"href {v[:40]!r}: {url_problem(v)}")
            elif k == "style" and not all(SAFE_DECL.match(d) for d in v.split(";") if d.strip()):
                self.errs.append(f"style {v[:60]!r}: only color/background/font-weight/font-style/white-space/"
                                 "text-decoration with a colour, a var(--token) or a keyword")
            elif k == "target" and v != "_blank":
                self.errs.append(f"target={v!r}: only _blank")
            elif k == "data-tip":
                self.errs += [f"in a data-tip: {e}" for e in html_problems(v)]

    handle_starttag = _tag
    handle_startendtag = _tag

    def handle_endtag(self, tag):
        if tag not in SAFE_TAGS:
            self.errs.append(f"</{tag}> is not allowed in text")

    def handle_comment(self, data):
        self.errs.append("<!-- comments --> are not allowed in text (an unclosed one hides the rest of the page)")

    def handle_decl(self, decl):
        self.errs.append("<!...> declarations are not allowed in text")

    unknown_decl = handle_decl

    def handle_pi(self, data):
        self.errs.append("<?...> is not allowed in text")

    def handle_data(self, data):
        self.data.append(data)                      # the parser hands a lone '<' over on its own: judge them joined


def html_problems(s: str) -> list[str]:
    """Why an HTML text snippet is unsafe (empty list = fine). Used for every text field, tip and setting."""
    p = _HTMLCheck()
    try:
        p.feed(s)
        p.close()
    except Exception as e:  # noqa: BLE001  (a malformed snippet the parser gives up on)
        p.errs.append(f"unreadable HTML ({e})")
    if "<!" in s:
        p.errs.append("<!-- comments --> and <!...> are not allowed in text (an unclosed one hides the rest of the page)")
    elif re.search(r"<[A-Za-z/!?]|<\s*$", "".join(p.data)):
        p.errs.append("a '<' that does not start a complete allowed tag (write &lt; for a literal <)")
    m = SCRIPTY.search(s)
    if m:
        p.errs.append(f"{m.group(0).strip()!r} looks like script")
    return list(dict.fromkeys(p.errs))


# ============================================================================ validation (JSON Schema subset)
def _resolve(sch, root):
    while "$ref" in sch:
        ref = sch["$ref"]
        assert ref.startswith("#/"), ref
        node = root
        for part in ref[2:].split("/"):
            node = node[part]
        sch = node
    return sch


def _type_ok(v, t):
    return {"string": isinstance(v, str), "number": isinstance(v, (int, float)) and not isinstance(v, bool),
            "integer": isinstance(v, int) and not isinstance(v, bool), "boolean": isinstance(v, bool),
            "array": isinstance(v, list), "object": isinstance(v, dict), "null": v is None}[t]


def validate(v, sch, root, path, errs):
    """A small JSON Schema validator (type, const, enum, lengths, pattern, ranges, required, properties,
    additionalProperties, items, oneOf dispatched on a 'type' const). Keys starting with '_' are comments."""
    sch = _resolve(sch, root)
    if "oneOf" in sch:
        branches = [_resolve(b, root) for b in sch["oneOf"]]
        consts = [b.get("properties", {}).get("type", {}).get("const") for b in branches]
        if isinstance(v, dict) and all(consts):
            if v.get("type") not in consts:
                errs.append(f"{path}.type: {v.get('type')!r} is not a section type ({', '.join(consts)})")
                return
            return validate(v, branches[consts.index(v["type"])], root, f"{path}({v['type']})", errs)
    t = sch.get("type")
    if t is not None:
        ts = t if isinstance(t, list) else [t]
        if not any(_type_ok(v, x) for x in ts):
            errs.append(f"{path}: expected {' or '.join(ts)}, got {type(v).__name__}")
            return
    if "const" in sch and v != sch["const"]:
        errs.append(f"{path}: must be {sch['const']!r}")
    if "enum" in sch and v not in sch["enum"]:
        errs.append(f"{path}: {v!r} is not one of {sch['enum']}")
    if isinstance(v, str):
        if len(v) < sch.get("minLength", 0):
            errs.append(f"{path}: empty or too short (min {sch['minLength']} characters)")
        if "maxLength" in sch and len(v) > sch["maxLength"]:
            errs.append(f"{path}: too long ({len(v)} > {sch['maxLength']} characters)")
        if "pattern" in sch and not re.search(sch["pattern"], v):
            errs.append(f"{path}: {v!r} does not match {sch['pattern']}")
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if "minimum" in sch and v < sch["minimum"]:
            errs.append(f"{path}: {v} < {sch['minimum']}")
        if "maximum" in sch and v > sch["maximum"]:
            errs.append(f"{path}: {v} > {sch['maximum']}")
        if "exclusiveMinimum" in sch and v <= sch["exclusiveMinimum"]:
            errs.append(f"{path}: {v} must be > {sch['exclusiveMinimum']}")
    if isinstance(v, list):
        if len(v) < sch.get("minItems", 0):
            errs.append(f"{path}: needs at least {sch['minItems']} item(s), has {len(v)}")
        if "maxItems" in sch and len(v) > sch["maxItems"]:
            errs.append(f"{path}: at most {sch['maxItems']} item(s), has {len(v)}")
        if "items" in sch:
            for i, x in enumerate(v):
                validate(x, sch["items"], root, f"{path}[{i}]", errs)
    if isinstance(v, dict):
        for k in sch.get("required", []):
            if k not in v:
                errs.append(f"{path}: missing required field {k!r}")
        props = sch.get("properties", {})
        for k, x in v.items():
            if k.startswith("_") or k == "$schema":
                continue
            if k in props:
                validate(x, props[k], root, f"{path}.{k}", errs)
            elif sch.get("additionalProperties") is False:
                errs.append(f"{path}: unknown field {k!r} (allowed: {', '.join(sorted(props))})")


def _strings(v, path=""):
    if isinstance(v, str):
        yield path, v
    elif isinstance(v, dict):
        for k, x in v.items():
            if not k.startswith("_"):
                yield from _strings(x, f"{path}.{k}" if path else k)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from _strings(x, f"{path}[{i}]")


def _unfinished(spec, draft, errs, warns):
    for path, s in _strings(spec):
        if path.endswith("$schema"):
            continue
        m = UNFINISHED.search(s)
        if m:
            (warns if draft else errs).append(f"{path}: unfinished text ({m.group(0)!r})"
                                              + ("" if draft else "; finish it, or build with --draft for a review copy"))


def check_spec(spec: dict, gate_blocks: bool, draft: bool = False) -> list[str]:
    """Schema + the semantic rules; raises SpecError listing every problem, returns warnings.
    draft=True turns unfinished text (FILL:, TBD, ...) and a placeholder contact into warnings (a review copy)."""
    schema = json.loads(SCHEMA_PATH.read_text())
    errs, warns = [], []
    validate(spec, schema, schema, "spec", errs)
    if errs:
        _unfinished(spec, False, errs, [])          # say which fields are still FILL: placeholders, too
        raise SpecError("\n".join(dict.fromkeys(errs)))
    try:
        dt.date.fromisoformat(spec["page"]["date"])
    except ValueError:
        errs.append(f"page.date {spec['page']['date']!r} is not a real date (YYYY-MM-DD)")
    if len(text(spec["page"]["title"]).split()) < 3:
        warns.append(f"page.title {text(spec['page']['title'])!r} has fewer than 3 words: publish.py / check_page "
                     "refuse titles that vague; use the full program name")
    secs = spec["sections"]
    ids = [s["id"] for s in secs if s.get("id")]
    for d in sorted({i for i in ids if ids.count(i) > 1}):
        errs.append(f"section id {d!r} is used more than once")
    for i in ids:
        if i.lower() in RESERVED_IDS or i.startswith("tipd-"):
            errs.append(f"section id {i!r} is used by the page itself (reserved: {', '.join(sorted(RESERVED_IDS))}, tipd-N)")
    types = [s["type"] for s in secs]
    if "hero" in types and types.index("hero") != 0:
        errs.append("the hero must be the first section")
    if "footer" in types and types.index("footer") != len(types) - 1:
        errs.append("the footer must be the last section")
    for t in ("hero", "footer", "map"):
        if types.count(t) > 1:
            errs.append(f"only one {t} section per page")
    for i, s in enumerate(secs):
        if s.get("nav") and not s.get("id"):
            errs.append(f"sections[{i}] has a nav label but no id")
    if sum(bool(s.get("nav_cta")) for s in secs) > 1:
        errs.append("only one section may be the nav call to action (nav_cta)")
    _unfinished(spec, draft, errs, warns)
    for path, s in _strings(spec):
        if path.endswith("$schema"):
            continue
        bare = re.sub(r"(https?|mailto):\S+", "", s)            # a web address may well contain /home/ or /tmp/
        if PRIVATE_PATH.search(bare):
            errs.append(f"{path}: looks like a local file path ({PRIVATE_PATH.search(bare).group(0)}); never ship one")
        key = re.sub(r"\[\d+\]$", "", path).rsplit(".", 1)[-1]
        if key == "src" and not path.endswith("iframe.src"):
            continue                                          # a source note: written inside an HTML comment
        if key in ("href", "og_image") or path.endswith("iframe.src"):
            if url_problem(s, iframe=path.endswith("iframe.src")):
                errs.append(f"{path}: {url_problem(s, iframe=path.endswith('iframe.src'))}")
            continue
        for e in html_problems(s):
            errs.append(f"{path}: {e}")
        for a in re.findall(r'href\s*=\s*["\']?#([\w-]*)', s):
            if a not in ids:
                errs.append(f"{path}: link to #{a}, but no section has that id")
    for path, s in _strings(spec):                            # hrefs were skipped above; their anchors still count
        if path.endswith(".href") and s.startswith("#") and s[1:] not in ids:
            errs.append(f"{path}: link to {s}, but no section has that id")
    m = next((s for s in secs if s["type"] == "map"), None)
    if m and m.get("popup"):
        places = [t.get("place") for t in m.get("tiles", [])]
        if m["popup"]["place"] not in places:
            errs.append(f"map.popup.place {m['popup']['place']!r} matches no tile's place ({places})")
    for s in secs:
        ch = s.get("chart")
        if not ch:
            continue
        labels = [c["label"] for c in ch["categories"]]
        for a in ch.get("annotations", []):
            if a["at"] not in labels:
                errs.append(f"chart {ch['title']!r}: annotation at {a['at']!r} is not a category")
        vals = [c["value"] for c in ch["categories"] if c.get("value") is not None and not c.get("gap")]
        if vals and not any(vals):
            warns.append(f"chart {ch['title']!r}: every value is 0, so the chart is empty")
        if ch.get("ymax") and vals and max(vals) > ch["ymax"]:
            errs.append(f"chart {ch['title']!r}: a value ({max(vals)}) is above ymax ({ch['ymax']})")
        for t in ch.get("totals", []):
            if t.get("assert_sum"):
                want = float(re.sub(r"[^\d.]", "", t["value"]) or "nan")
                if abs(want - sum(vals)) > 1e-9:
                    errs.append(f"chart {ch['title']!r}: total {t['value']} != sum of the values ({sum(vals):,})")
    if gate_blocks:
        for path, s in _strings({"gate": spec.get("gate", {}), "contact": spec.get("contact", {})}):
            if path.endswith(".href"):
                continue
            if re.search(r"\d+(\.\d+)?\s*(%|percent)|\b0\.\d+\b|\b(F1|AUC|IoU)\b", s, re.I):
                errs.append(f"{path} holds a percentage or a score: the lock screen is NOT encrypted, keep results off it")
    if "hero" not in types:
        warns.append("no hero section: a minimal one (program line + title) was added")
    if "footer" not in types:
        warns.append("no footer section: a default footer with a short disclaimer was added")
    if errs:
        raise SpecError("\n".join(errs))
    return warns


def preflight(spec: dict, cfg: dict, gate_on: bool, draft: bool = False) -> list[str]:
    """What check_spec cannot see from the spec alone: the contact actually used, the asset files and the settings
    file. --validate runs it too, so a spec that validates also builds. Raises SpecError; returns warnings."""
    errs, warns = [], []
    secs = spec["sections"]
    who = contact_of(spec, cfg)
    if any(s["type"] == "cta" for s in secs) and not who:
        errs.append("the cta section needs a contact: add \"contact\": {\"name\", \"email\"} to the spec or to "
                    "~/.config/external-facing-website/site.json (ask the user who partners should write to)")
    used = [("contact", who)] + ([("gate.contact", spec["gate"]["contact"])] if gate_on and spec.get("gate", {}).get("contact") else [])
    for where, c in used:
        if not c:
            continue
        if not EMAIL.match(c.get("email", "")):
            errs.append(f"{where}.email {c.get('email')!r} is not an email address")
        elif PLACEHOLDER_EMAIL.search(c["email"]):
            (warns if draft else errs).append(f"{where}.email {c['email']!r} is a placeholder: set the real contact "
                                              "(ask the user), or build with --draft for a review copy")
        for e in html_problems(c.get("name", "")):
            errs.append(f"{where}.name: {e}")
    names = [cfg.get("favicon", "favicon.png")] + [o[k] for o in cfg.get("logo_row", []) for k in ("logo", "logo_dark_bg") if o.get(k)]
    if gate_on:
        names.append(spec.get("gate", {}).get("photo") or cfg.get("lock_screen", {}).get("photo", "lock-aerial-naip.jpg"))
    for n in names:
        try:
            efw.asset(n)
        except SystemExit as e:
            errs.append(str(e))
    for path, s in _strings(cfg):
        key = re.sub(r"\[\d+\]$", "", path).rsplit(".", 1)[-1]
        if key in ("url", "href", "og_image"):
            if url_problem(s):
                errs.append(f"site settings {path}: {url_problem(s)}")
        elif key not in ("logo", "logo_dark_bg", "favicon", "photo", "email"):
            errs += [f"site settings {path}: {e}" for e in html_problems(s)]
    if errs:
        raise SpecError("\n".join(dict.fromkeys(errs)))
    return warns


# ============================================================================ small helpers
def attr(s) -> str:
    """Escape for an attribute value, keeping existing entities (&rarr;) intact."""
    s = re.sub(r"&(?!#?\w+;)", "&amp;", str(s))
    return s.replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def text(s) -> str:
    """Plain text from an HTML snippet (for <title>, aria labels)."""
    return html.unescape(re.sub(r"<[^>]+>", "", str(s)))


SHOW_SRC = True


def src(o) -> str:
    s = o.get("src") if isinstance(o, dict) else None
    if not s or not SHOW_SRC:
        return ""
    notes = s if isinstance(s, list) else [s]
    return "".join(f"<!-- SRC: {n.replace('--', '- -')} -->" for n in notes)


def pct(v) -> str:
    """0.965 -> '97%': half-up rounding on the decimal value (Python's round() would give 96)."""
    from decimal import Decimal, ROUND_HALF_UP
    return f'{(Decimal(str(v)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)}%'


def tip(o) -> str:
    return f' data-tip="{attr(o["tip"])}"' if isinstance(o, dict) and o.get("tip") else ""


def ico(name) -> str:
    if not name:
        return ""
    return ('<div class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg></div>')


def data_uri(p: Path) -> str:
    mime = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".woff2": "font/woff2"}[p.suffix.lower()]
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def ext_link(href, label) -> str:
    ext = href.startswith("http")
    return f'<a href="{attr(href)}"' + (' target="_blank" rel="noopener"' if ext else "") + f">{label}</a>"


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text(s).lower()).strip("-")


def n_class(n, default):
    return "" if n == default else f" n{n}"


def logo_row(cfg, dark=False) -> str:
    parts = []
    for i, o in enumerate(cfg["logo_row"]):
        f = efw.asset(o["logo_dark_bg"] if dark and o.get("logo_dark_bg") else o["logo"])
        h = o.get("height", 28) * (1.15 if dark else 1)
        cls = f'lg-{slug(o["short"])}' + (" lg-first" if i == 0 else "")
        mark = f'<span>{o["wordmark"]}</span>' if o.get("wordmark") else ""
        parts.append(f'<a class="{cls}" href="{attr(o["url"])}" target="_blank" rel="noopener">'
                     f'<img src="{data_uri(f)}" alt="{attr(o.get("alt", ""))}" style="height:{h:.0f}px">{mark}</a>')
    return '<span class="lg-sep" aria-hidden="true"></span>'.join(parts)


def head(s, flow=False) -> str:
    sz = s.get("lede_size", "sm")
    lede = f'<p class="lede {sz}">{s["lede"]}</p>' if s.get("lede") else ""
    if flow and s.get("flow"):
        h2 = (f'<h2 class="flowtitle"><span class="nw">{s["flow"]["in"]} <span class="arrow" aria-hidden="true">→</span></span> '
              f'<span class="nw">{s["flow"]["out"]}</span></h2>')
    else:
        h2 = f'<h2>{s["heading"]}</h2>' if s.get("heading") else ""
    eb = f'<p class="eyebrow">{s["eyebrow"]}</p>' if s.get("eyebrow") else ""
    return f'<div class="head{" wide" if s.get("wide") else ""}">{eb}{h2}{lede}</div>'


# ============================================================================ sections
def r_hero(s, spec, cfg):
    p = spec["page"]
    line = s.get("program_line") or p.get("program_line") or cfg.get("program_line", "")
    ledes = "".join(f"<p>{x}</p>" for x in s.get("lede", []))
    ctas = "".join(f'<a class="btn{" solid" if c.get("style", "solid" if i == 0 else "outline") == "solid" else ""}" '
                   f'href="{attr(c["href"])}">{c["label"]}</a>' for i, c in enumerate(s.get("ctas", [])))
    return (f'<div class="hero"><div class="wrap">{src(s)}\n'
            + (f'  <p class="program">{line}</p>\n' if line else "")
            + f'  <h1 class="bigtitle" id="bigtitle">{s.get("title") or p["title"]}</h1>\n'
            + (f'  <div class="intro"><div class="lede" id="lede">{ledes}</div></div>\n' if ledes else "")
            + (f'  <div class="ctas">{ctas}</div>\n' if ctas else "")
            + (f'  <p class="pill"><i></i>{s["pill"]}</p>\n' if s.get("pill") else "")
            + "</div></div>")


def r_map(s, spec, cfg):
    f = s["iframe"]
    style = "".join(f"{k}:{attr(f[j])};" for k, j in (("--map-h", "height"), ("--map-h-phone", "phone_height")) if f.get(j))
    pop = ""
    if s.get("popup"):
        q = s["popup"]
        pop = (f'<div id="whyPop" class="whypop" role="dialog" aria-labelledby="whyPopT" data-place="{attr(q["place"])}" hidden>'
               '<button type="button" class="x" aria-label="Close">&times;</button>'
               f'<h3 id="whyPopT">{q["title"]}</h3><p class="lead">{q["lead"]}</p>'
               f'<h4>{q.get("reasons_heading", "Likely reasons")}</h4><ul>{"".join(f"<li>{x}</li>" for x in q["reasons"])}</ul>'
               f'<h4>{q.get("helps_heading", "What would help")}</h4><ul>{"".join(f"<li>{x}</li>" for x in q["helps"])}</ul></div>')
    legend = ""
    if s.get("legend"):
        legend = '<div class="maplegend">' + "".join(
            f'<span{tip(x)}><i style="background:{attr(x["color"])}"></i>{x["label"]}</span>' for x in s["legend"]) + "</div>"
    tiles = ""
    if s.get("tiles"):
        pp = (s.get("popup") or {}).get("place")
        out = []
        for t in s["tiles"]:
            flagged = t.get("flagged")
            place = t.get("place")
            color = {"navy": " navy", "flag": " flagc"}.get(t.get("color", "flag" if flagged else "right"), "")
            go = t.get("go_label") or ("Show on map and why &rarr;" if place and place == pp else "Show on map &rarr;")
            a = (f' role="button" data-place="{attr(place)}" title="Show {attr(text(t["title"]))} on the map"' if place else "")
            out.append(f'{src(t)}<div class="sqcard{" flagged" if flagged else ""}"{a}{tip(t)}>'
                       + (f'<span class="flag">{t.get("flag_label", "Where it struggles")}</span>' if flagged else "")
                       + f'<strong>{t["title"]}</strong><b class="num{color}">{t["value"]}</b><span>{t["text"]}</span>'
                       + (f'<span class="go">{go}</span>' if place else "") + "</div>")
        tiles = f'<div class="under{n_class(len(out), 4)}">' + "".join(out) + "</div>"
    how = ""
    if s.get("how"):
        how = (f'<details class="checks"><summary>{s["how"].get("summary", "How this map was made")}</summary><div class="body"><ul>'
               + "".join(f"<li>{x}</li>" for x in s["how"]["items"]) + "</ul></div></details>")
    hint = f'<p class="small muted" style="margin-top:14px">{s["hint"]}</p>' if s.get("hint") else ""
    cap = f'<p class="small muted mapcap">{s["caption"]}</p>' if s.get("caption") else ""
    return (f'{head(s)}\n  <div class="mapframe{" dashed" if s.get("frame") == "dashed" else ""}"'
            + (f' style="{style}"' if style else "") + f'>{pop}'
            f'<iframe id="mapiframe" title="{attr(f["title"])}" src="{attr(f["src"])}" loading="lazy" allowfullscreen></iframe></div>\n'
            f'  {cap}{legend}{tiles}{how}{hint}')


def nice_step(mx):
    """A round tick step giving about five ticks up to mx (works below 1 too: 0.004 -> 0.001)."""
    raw = mx / 5 if mx > 0 else 0.2
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag * (1 + 1e-9):
            return float(f"{m * mag:.12g}")
    return 10 * mag


def fmt_num(v):
    """12345.6 -> '12,345.6'; 1500.0 -> '1,500'; 0.004 -> '0.004' (never scientific notation)."""
    if float(v).is_integer():
        return f"{int(v):,}"
    s = f"{v:,.6f}".rstrip("0").rstrip(".")
    return s if abs(v) >= 1 else f"{v:.6g}"


def r_chart(ch):
    cats = ch["categories"]
    n = len(cats)
    vals = [c["value"] for c in cats if c.get("value") is not None and not c.get("gap")]
    step = ch.get("ytick_step") or nice_step(max(vals) if vals else 1)
    ymax = ch.get("ymax") or float(f"{step * max(1, math.ceil(max(vals or [1]) / step - 1e-9)):.12g}")
    fmt = ch.get("ytick_format") or ("k" if ymax >= 10000 else "plain")

    def tick(v):
        if v == 0:
            return "0"
        return {"k": f"{v / 1000:g}k", "pct": f"{v:g}%", "plain": f"{v:,g}"}[fmt]
    ticks = []
    v = 0.0
    while v <= ymax + 1e-9:
        ticks.append(v)
        v += step
    unit = ch.get("value_label", "")
    cols = []
    for c in cats:
        if c.get("gap"):
            t = c.get("tip") or f"<b>{c['label']}</b><br>No data."
            cols.append(f'<div class="col gap" data-tip="{attr(t)}"></div>')
        elif c.get("value") is None:
            cols.append(f'<div class="col" data-tip="{attr(c.get("tip") or c["label"] + ": no value")}"></div>')
        else:
            t = c.get("tip") or f"<b>{c['label']}</b><br>{fmt_num(c['value'])} {unit}".strip()
            cols.append(f'<div class="col" data-tip="{attr(t)}"><i style="height:{100 * c["value"] / ymax:.2f}%"></i></div>')
    every = ch.get("label_every") or max(1, round(n / 7))
    xl, shown = [], 0
    for i, c in enumerate(cats):
        if i % every == 0:
            xl.append(f'<span class="{"odd" if shown % 2 else ""}">{c["label"]}</span>')
            shown += 1
        else:
            xl.append("<span></span>")
    anns = []
    for a in ch.get("annotations", []):
        i = [c["label"] for c in cats].index(a["at"])
        val = cats[i].get("value") or 0
        right = i < n / 3
        left = 100 * (i + (.85 if right else .15)) / n
        top = max(6, 100 - 100 * val / ymax)
        anns.append(f'<div class="ann{" r" if right else ""}" style="left:{left:.2f}%;top:{top:.2f}%">{a["text"]}'
                    + (f'<br><span>{a["detail"]}</span>' if a.get("detail") else "") + "</div>")
    gaplab = ""
    gi = [i for i, c in enumerate(cats) if c.get("gap")]
    if gi and ch.get("gap_label"):
        g = ch["gap_label"]
        gaplab = (f'<div class="gaplab" style="left:{100 * gi[0] / n:.2f}%;right:auto;width:{100 * len(gi) / n:.2f}%">{g["text"]}'
                  + (f'<span>{g["detail"]}</span>' if g.get("detail") else "") + "</div>")
    tot = "".join(f'<div{" class=" + chr(34) + "gapk" + chr(34) if t.get("gap") else ""}><b>{t["value"]}</b>{t["label"]}</div>'
                  for t in ch.get("totals", []))
    key = "".join(f'<span><i{" class=" + chr(34) + "h" + chr(34) if k.get("kind") == "gap" else ""}></i>{k["label"]}</span>'
                  for k in ch.get("key", []))
    table = ""
    if ch.get("table"):
        tb = ch["table"]
        rows = [c for c in cats if not c.get("gap") and c.get("value") is not None]
        extra = []
        for c in rows:
            extra += [k for k in c.get("cols", {}) if k not in extra]
        hdr = "<tr>" + "".join(f"<th>{h}</th>" for h in [tb["label_header"], *extra, tb["value_header"]]) + "</tr>"
        k = tb.get("split", 1)
        size = -(-len(rows) // k)
        parts = [rows[j:j + size] for j in range(0, len(rows), size)]
        table = (f'<details><summary>{tb.get("summary", "See the numbers")}</summary>'
                 + (f'<p>{tb["note"]}</p>' if tb.get("note") else "") + '<div class="tblwrap">'
                 + "".join("<table>" + hdr + "".join(
                     "<tr>" + "".join(f"<td>{x}</td>" for x in [c["label"], *[c.get("cols", {}).get(e, "") for e in extra], fmt_num(c["value"])]) + "</tr>"
                     for c in part) + "</table>" for part in parts) + "</div></details>")
    sub = f'<p class="sub">{ch["subtitle"]}</p>' if ch.get("subtitle") else ""
    return (f'{src(ch)}<div class="card yrchart">\n    <div class="ctop"><div><h3>{ch["title"]}</h3>{sub}</div>'
            + (f'<div class="tot">{tot}</div>' if tot else "") + "</div>\n"
            f'    <div class="plot" style="--n:{n}" role="img" aria-label="{attr(text(ch["aria_label"]))}">\n'
            f'      <div class="yax">' + "".join(f'<span style="bottom:{100 * t / ymax:.2f}%">{tick(t)}</span>' for t in ticks) + "</div>\n"
            f'      <div class="area">' + "".join(f'<div class="grid" style="bottom:{100 * t / ymax:.2f}%"></div>' for t in ticks[1:])
            + f'<div class="cols">{"".join(cols)}</div>{"".join(anns)}{gaplab}</div>\n'
            f'      <div class="xax">{"".join(xl)}</div>\n    </div>\n'
            + (f'    <div class="key">{key}</div>\n' if key else "") + f"    {table}\n  </div>")


def r_tile(t):
    link = (f'<p><a href="{attr(t["link"]["href"])}">{t["link"]["label"]} &rarr;</a></p>' if t.get("link") else "")
    return f'{src(t)}<div class="step card">{ico(t.get("icon"))}<h3>{t["title"]}</h3><p>{t["body"]}</p>{link}</div>'


def r_tiles(s, spec, cfg):
    chart = r_chart(s["chart"]) if s.get("chart") else ""
    return (f'{head(s)}\n  {chart}\n  <div class="steps tiles{n_class(len(s["tiles"]), 4)}">'
            + "".join(r_tile(t) for t in s["tiles"]) + "</div>")


def r_chartsec(s, spec, cfg):
    note = f'<p class="small muted chartnote">{s["note"]}</p>' if s.get("note") else ""
    return f'{head(s)}\n  {r_chart(s["chart"])}{note}'


def r_pipeline(s, spec, cfg):
    out = []
    for i, st in enumerate(s["steps"], 1):
        chips = ""
        if st.get("chips"):
            chips = '<div class="chips">' + "".join(
                (f'<a href="{attr(c["href"])}" target="_blank" rel="noopener"{tip(c)}>{c["label"]}</a>' if c.get("href")
                 else f'<span class="chip"{tip(c)}>{c["label"]}</span>') for c in st["chips"]) + "</div>"
        lst = ""
        if st.get("list"):
            lst = (f'<details class="places"><summary>{st["list"]["summary"]}</summary><div class="placelist">'
                   + "".join(f'<div><span>{ext_link(x["href"], x["name"]) if x.get("href") else x["name"]}</span>'
                             + (f'<span class="ag">{x["detail"]}</span>' if x.get("detail") else "") + "</div>"
                             for x in st["list"]["items"]) + "</div></details>")
        out.append(f'{src(st)}<div class="step card">{ico(st.get("icon"))}<p class="k">{st.get("label", f"Step {i}")}</p>'
                   f'<h3>{st["title"]}</h3><p>{st["body"]}</p>{chips}{lst}</div>')
    return f'{head(s, flow=True)}\n  <div class="steps{n_class(len(out), 3)}">' + "".join(out) + "</div>"


def r_cards(s, spec, cfg):
    out = []
    for c in s["cards"]:
        ul = "<ul>" + "".join(f"<li>{b}</li>" for b in c["bullets"]) + "</ul>" if c.get("bullets") else ""
        body = f'<p class="muted" style="font-size:.95rem">{c["body"]}</p>' if c.get("body") else ""
        out.append(f'<div class="use card">{ico(c.get("icon"))}<h3>{c["title"]}</h3>{body}{ul}</div>')
    return f'{head(s)}\n  <div class="uses{n_class(len(out), 4)}">' + "".join(out) + "</div>"


def r_stats(s, spec, cfg):
    stats = "".join(f'{src(x)}<div class="stat"{tip(x)}><b>{x["value"]}</b><span>{x["label"]}</span><em>{x["scope"]}</em></div>'
                    for x in s["stats"])
    css = n_class(len(s["stats"]), 4)
    cards = []
    for c in s.get("bar_cards", []):
        colors = ["var(--navy)", "var(--gold)"]
        key = ('<div class="mkey">' + "".join(f'<span><i style="background:var(--{k["color"]})"></i>{k["label"]}</span>' for k in c["key"])
               + "</div>") if c.get("key") else ""
        if c.get("key"):
            colors = [f'var(--{k["color"]})' for k in c["key"]] + colors[len(c["key"]):]
        rows = "".join(
            f'{src(r)}<div class="mrow"{tip(r)}><div class="mname">{r["name"]}' + (f'<em>{r["scope"]}</em>' if r.get("scope") else "")
            + '</div><div class="bars">' + "".join(
                f'<div class="bar"><i style="width:{100 * b["value"]:.1f}%;background:{colors[j]}"></i></div>'
                f'<span>{b.get("label", pct(b["value"]))}</span>' for j, b in enumerate(r["bars"]))
            + "</div></div>" for r in c["rows"])
        note = f'<p class="small muted" style="margin-top:10px">{c["note"]}</p>' if c.get("note") else ""
        chk = ""
        if c.get("checks"):
            chk = (f'<details class="checks"><summary>{c["checks"].get("summary", "How these results were checked")}</summary>'
                   '<div class="body"><ul>' + "".join(f"<li>{x}</li>" for x in c["checks"]["items"]) + "</ul></div></details>")
        cards.append(f'<div class="card acc"><h3>{c["title"]}</h3>{key}<div>{rows}</div>{note}{chk}</div>')
    grid = (f'<div class="two">{"".join(cards)}</div>' if len(cards) == 2 else "".join(cards))
    foot = f'<p class="small muted" style="margin-top:20px;max-width:75ch">{s["footnote"]}</p>' if s.get("footnote") else ""
    return f'{head(s)}\n  <div class="stats{css}">{stats}</div>\n  {grid}{foot}'


def r_prose(s, spec, cfg):
    return f'{head(s)}\n  <div class="limits-text">' + "".join(f"<p>{p}</p>" for p in s["paragraphs"]) + "</div>"


def contact_of(spec, cfg):
    c = spec.get("contact") or {}
    if c.get("email"):
        return c
    c = cfg.get("contact") or {}
    return c if c.get("email") else None


def r_cta(s, spec, cfg):
    who = contact_of(spec, cfg)
    if not who:
        raise SpecError("the cta section needs a contact: add \"contact\": {\"name\", \"email\"} to the spec or to "
                        "~/.config/external-facing-website/site.json (ask the user who partners should write to)")
    btn = (f'<div class="rel"><a class="btn" href="mailto:{attr(who["email"])}">'
           f'{(s.get("contact_card") or {}).get("button_label") or "Contact " + who["name"]} {ARROW}</a></div>')
    cards = []
    if s.get("steps_card"):
        sc = s["steps_card"]
        cards.append(f'<div class="card pcard"><h3>{sc["title"]}</h3><ol>' + "".join(f"<li>{x}</li>" for x in sc["steps"]) + "</ol></div>")
    if s.get("contact_card"):
        cc = s["contact_card"]
        body = f'<p class="small muted" style="margin:6px 0 14px">{cc["body"]}</p>' if cc.get("body") else ""
        cards.append(f'<div class="card pcard"><h3>{cc["title"]}</h3>{body}{btn}</div>')
    if not cards:
        return f"{head(s)}\n  {btn}"
    if not s.get("contact_card"):
        cards.append(f'<div class="card pcard"><h3>Get in touch</h3>{btn}</div>')
    return f'{head(s)}\n  <div class="two partner">{"".join(cards)}</div>'


def initials(name):
    w = [x for x in re.sub(r"\b(Dr|Prof|Mr|Ms|Mrs)\.?\s", "", name).split() if x[:1].isalpha()]
    return (w[0][0] + (w[-1][0] if len(w) > 1 else "")).upper()


def r_team(s, spec, cfg):
    out = []
    for p in s["people"]:
        links = "".join(ext_link(x["href"], x["label"]) for x in p.get("links", []))
        out.append(f'<div class="person card"><div class="avatar" aria-hidden="true">{p.get("initials") or initials(text(p["name"]))}</div>'
                   f'<h3>{p["name"]}</h3><p class="role">{p["role"]}</p>' + (f'<p>{p["line"]}</p>' if p.get("line") else "")
                   + (f'<div class="plinks">{links}</div>' if links else "") + "</div>")
    return f'{head(s)}\n  <div class="team{n_class(len(out), 3) if len(out) == 2 else ""}">' + "".join(out) + "</div>"


def r_refs(s, spec, cfg):
    items = [(ext_link(x["href"], x["name"]) if x.get("href") else x["name"], x.get("detail", "")) for x in s["refs"]]
    if s.get("collapsed"):
        return (f'{head(s)}\n  <details class="places"><summary>{s.get("summary", "See the references")}</summary><div class="placelist">'
                + "".join(f'<div><span>{a}</span>' + (f'<span class="ag">{d}</span>' if d else "") + "</div>" for a, d in items)
                + "</div></details>")
    return (f'{head(s)}\n  <div class="card refbox"><ul class="reflist">'
            + "".join(f"<li><span>{a}</span>" + (f'<span class="ag">{d}</span>' if d else "") + "</li>" for a, d in items) + "</ul></div>")


def r_footer(s, spec, cfg, logos):
    built = s.get("built") or spec["page"].get("built") or dt.date.today().isoformat()
    links = s.get("links") or [{"label": re.sub(r"^https?://(www\.)?|/$", "", o["url"]), "href": o["url"]} for o in cfg["logo_row"]]
    return ('<footer><div class="wrap">\n'
            f'  <div class="logos" id="logos2">{logos}</div>\n'
            f'  <p class="disc">{s["disclaimer"]}</p>\n'
            + (f'  <p>{s["credits"]}</p>\n' if s.get("credits") else "")
            + f'  <p>Page built {built} · ' + " · ".join(ext_link(x["href"], x["label"]) for x in links) + "</p>\n"
            "</div></footer>")


RENDER = {"map": r_map, "tiles": r_tiles, "chart": r_chartsec, "pipeline": r_pipeline, "cards": r_cards,
          "stats": r_stats, "prose": r_prose, "cta": r_cta, "team": r_team, "refs": r_refs}


# ============================================================================ the branded lock screen
GATE_CSS = """
:root:root { --bg:#ffffff; --ink:#15212b; --muted:#5b6670; --line:#dcd8cf; --acc:#003660; --bad:#b3261e; color-scheme:light }
html, body { background:#ffffff; color:#15212b; font-family:"Inter", system-ui, -apple-system, "Segoe UI", sans-serif; -webkit-font-smoothing:antialiased }
.wrap { flex-direction:column; align-items:stretch; justify-content:center; gap:28px; padding:48px max(24px, 6vw) 32px calc(52vw + max(24px, 6vw)); min-height:100vh }
.box { max-width:440px; width:100%; box-sizing:border-box; border:0; border-radius:0; padding:0; text-align:left; margin:0 }
.gb-art { position:fixed; inset:0 auto 0 0; width:52vw; display:flex; flex-direction:column; justify-content:space-between; padding:40px 44px 36px;
  background:linear-gradient(180deg, rgba(0,30,56,.50) 0%, rgba(0,30,56,.30) 38%, rgba(0,30,56,.90) 100%), url(__PHOTO__) center/cover no-repeat #0b2a45; color:#fff; box-sizing:border-box }
.gb-logos { display:flex; align-items:center; gap:16px; flex-wrap:wrap; background:rgba(0,30,56,.55); padding:14px 18px; border-radius:14px; align-self:flex-start; backdrop-filter:blur(4px) }
.gb-logos a { display:inline-flex; align-items:center; gap:10px; color:#fff; text-decoration:none; font:600 14px/1.15 "Inter", sans-serif }
.gb-logos img { display:block; width:auto }
@media (min-width: 761px) { .gb-logos { flex-wrap:nowrap } }
.gb-logos .lg-sep { width:1px; height:26px; background:rgba(255,255,255,.35) }
.gb-eye { font:600 12px/1 "Inter", sans-serif; letter-spacing:.14em; text-transform:uppercase; color:#febc11; margin:0 0 16px }
.gb-art h1 { font:600 clamp(34px, 4.1vw, 60px)/1.04 "Source Serif 4", Georgia, serif; letter-spacing:-.015em; color:#fff; margin:0 0 16px; max-width:11em }
.gb-art p { color:rgba(255,255,255,.86); font-size:16px; line-height:1.55; margin:0; max-width:30rem }
.gb-art small { display:block; margin-top:22px; color:rgba(255,255,255,.6); font-size:11.5px }
.gb-lock { display:inline-flex; align-items:center; gap:8px; font:600 12px/1 "Inter", sans-serif; letter-spacing:.12em; text-transform:uppercase; color:#8a6400; margin:0 0 18px }
.gb-lock svg { width:14px; height:14px }
.box h2 { font:600 34px/1.12 "Source Serif 4", Georgia, serif; letter-spacing:-.01em; color:#003660; margin:0 0 12px }
.gb-text .gb-short { display:none }
.box p.gb-text { color:#5b6670; font-size:15px; line-height:1.6; margin:0 0 28px }
.gb-label { display:block; font:600 13px/1 "Inter", sans-serif; color:#15212b; margin:0 0 8px }
.box input { border:1px solid #cfd5da; background:#fff; color:#15212b; border-radius:12px; font-size:24px; letter-spacing:14px; padding:14px; text-align:center;
  box-shadow:0 1px 2px rgba(21,33,43,.05) }
.box input:focus { outline:none; border-color:#003660; box-shadow:0 0 0 4px rgba(0,54,96,.14) }
.box button { margin-top:14px; padding:15px; background:#003660; border-radius:999px; font:600 15px/1 "Inter", sans-serif; letter-spacing:.01em; cursor:pointer }
.box button:hover { background:#0a4a80 }
.box button:focus-visible { outline:3px solid #003660; outline-offset:3px }
.gb-art a:focus-visible { outline:3px solid #febc11; outline-offset:3px }
/* a wrong PIN shakes the form; the photo panel sits inside it, so shake only the field and button (a transform on the form would re-anchor the fixed panel) */
.box.shake { animation:none } .box.shake input, .box.shake button { animation:sh .35s }
.gb-foot { max-width:440px; font-size:13px; line-height:1.6; color:#5b6670; border-top:1px solid #e6e2da; padding-top:18px }
.gb-foot a { color:#1d4f7c; text-underline-offset:3px }
.gb-foot .gb-links { display:flex; gap:6px 16px; flex-wrap:wrap; margin:6px 0 }
.gb-foot .gb-fine { display:block; margin-top:8px; color:#5b6670; font-size:12px }
@media (max-width:900px) {
  .wrap { display:block; padding:0 0 32px; min-height:0 }
  .box { max-width:none }
  .gb-art { position:relative; width:auto; min-height:min(44vh, 340px); padding:24px 22px 26px; gap:32px; margin-bottom:26px }
  .gb-art h1 { font-size:clamp(30px, 8.4vw, 44px) }
  .gb-art p { font-size:15px }
  .box > :not(.gb-art), .gb-foot { margin-left:22px !important; margin-right:22px !important; max-width:440px }
  .box input, .box button { width:min(440px, calc(100% - 44px)) }
  .gb-foot { margin-top:30px }
}
@media (min-width:641px) and (max-width:900px) {   /* tablet: centre the form column under the photo band */
  .box > :not(.gb-art), .gb-foot { margin-left:auto !important; margin-right:auto !important; width:min(440px, calc(100% - 44px)) }
  .box .gb-lock { display:flex }
  .box input, .box button { display:block }
}
@media (max-width:640px) {
  .gb-art { min-height:0; padding:20px 20px 22px; gap:22px; margin-bottom:22px }
  .gb-art h1 { font-size:clamp(28px, 7.6vw, 36px); margin-bottom:0 }
  .gb-art p, .gb-art small { display:none }
  .gb-eye { margin-bottom:10px }
  .box h2 { font-size:27px }
  .box p.gb-text { font-size:14.5px; margin-bottom:20px }
  .gb-text .gb-long { display:none } .gb-text .gb-short { display:inline }
  .gb-logos { gap:12px 14px } .gb-logos .lg-first { flex-basis:100% } .gb-logos .lg-sep:first-of-type { display:none }
}
"""


def gate_blocks(spec, cfg, fonts_css) -> str:
    """The four blocks pin_gate.brand_lock_screen() copies onto the (unencrypted) lock screen."""
    p, g, ls = spec["page"], spec.get("gate", {}), cfg.get("lock_screen", {})
    title = g.get("title") or p["title"]
    tab = g.get("tab_title") or f'{text(title)} · {cfg.get("gate_org", "NCEAS")}'
    eyebrow = g.get("eyebrow") or p.get("program_line") or cfg.get("program_line", "")
    tagline = g.get("tagline") or p["description"]
    button = g.get("button") or ls.get("button", "Open the site")
    longt = g.get("access_text") or f'This research program from {cfg.get("institutions_text", "our team")} is shared privately. '
    shortt = g.get("access_text_short") or "Shared privately. "
    photo = efw.asset(g.get("photo") or ls.get("photo", "lock-aerial-naip.jpg"))
    credit = g.get("photo_credit") or ls.get("photo_credit", "")
    who = g.get("contact") or contact_of(spec, cfg)
    links = g.get("links") or ls.get("links") or [{"label": o.get("link_label") or o.get("alt") or o["short"], "href": o["url"]}
                                                   for o in cfg["logo_row"]]
    fine = g.get("fine_print") or ls.get("fine_print", "")
    need = (f'Need access? Contact {who["name"]} at <span style="user-select:all">{who["email"]}</span>' if who
            else "Need access? Ask the person who sent you this link.")
    css = GATE_CSS.replace("__PHOTO__", data_uri(photo))
    # the blocks are <script> elements: a "</script" inside would end one early and spill the rest onto the page
    # (check_spec refuses it in text already; this is the second lock)
    nos = lambda h: re.sub(r"</(script)", r"<\\/\1", h, flags=re.I)  # noqa: E731
    return (f'<meta name="gate-title" content="{attr(tab)}">\n'
            f'<meta name="gate-button" content="{attr(text(button))}">\n'
            f'<script type="text/x-gate-brand">\n<style>\n{fonts_css}\n{css}</style>\n'
            + nos(f'<div class="gb-art">\n  <div class="gb-logos">{logo_row(cfg, dark=True)}</div>\n  <div>\n'
                  + (f'    <p class="gb-eye">{eyebrow}</p>\n' if eyebrow else "")
                  + f'    <h1>{title}</h1>\n    <p>{tagline}</p>\n'
                  + (f'    <small>{credit}</small>\n' if credit else "")
                  + '  </div>\n</div>\n'
                  f'<p class="gb-lock">{LOCK}Restricted access</p>\n<h2>Enter your access PIN</h2>\n'
                  f'<p class="gb-text"><span class="gb-long">{longt}</span><span class="gb-short">{shortt}</span>Use the PIN you were given.</p>\n'
                  '<label class="gb-label" for="pin">Access PIN</label>\n')
            + '</script>\n<script type="text/x-gate-foot">'
            + nos(f'<div class="gb-foot">{need}\n<div class="gb-links">' + "".join(ext_link(x["href"], x["label"]) for x in links) + "</div>"
                  + (f'<span class="gb-fine">{fine}</span>' if fine else "") + "</div>")
            + "</script>\n")


# ============================================================================ page script (tooltips, map tiles, pop-up, lock)
JS = r"""
const $ = s => document.querySelector(s);
const tip = $("#tip");
function showTip(html, x, y) {
  tip.innerHTML = html; tip.classList.add("on");
  const r = tip.getBoundingClientRect(), W = innerWidth, H = innerHeight;
  let left = x + 14, top = y + 14;
  if (left + r.width > W - 8) left = Math.max(8, x - r.width - 14);
  if (top + r.height > H - 8) top = Math.max(8, y - r.height - 14);
  tip.style.left = left + "px"; tip.style.top = top + "px";
}
let tipFromFocus = false, tipN = 0;
function hideTip() { tip.classList.remove("on"); tipFromFocus = false }
function bindTip(el, html) {
  el.addEventListener("pointermove", e => { if (e.pointerType === "mouse") showTip(html, e.clientX, e.clientY) });
  el.addEventListener("pointerleave", e => { if (e.pointerType === "mouse") hideTip() });
  el.addEventListener("click", e => { if (e.pointerType !== "mouse" && !e.target.closest("a") && !el.matches(".sqcard[data-place]")) { e.stopPropagation(); showTip(html, e.clientX, e.clientY) } });
  if (el.matches(".plot .col")) return;            // the chart's table ("See the numbers") is the accessible version
  if (!el.matches("a, button")) el.tabIndex = 0;
  const d = document.createElement("span"); d.id = "tipd-" + (++tipN); d.hidden = true; d.innerHTML = html; document.body.append(d);
  el.setAttribute("aria-describedby", d.id);
  el.addEventListener("focus", () => requestAnimationFrame(() => { const r = el.getBoundingClientRect(); showTip(html, r.left, r.bottom); tipFromFocus = true }));
  el.addEventListener("blur", hideTip);
}
document.querySelectorAll("[data-tip]").forEach(el => { const h = el.getAttribute("data-tip"); el.removeAttribute("data-tip"); bindTip(el, h) });
document.addEventListener("click", hideTip);
addEventListener("scroll", () => { if (!tipFromFocus) hideTip() }, { passive: true });
addEventListener("keydown", e => { if (e.key === "Escape") hideTip() });
const frame = $("#mapiframe"), pop = $("#whyPop");
const mapOrigin = frame ? new URL(frame.getAttribute("src"), location.href).origin : "";
function showWhy(place) { if (pop) pop.hidden = place !== pop.dataset.place; }
document.querySelectorAll(".sqcard[data-place]").forEach(c => {
  if (!c.tabIndex || c.tabIndex < 0) c.tabIndex = 0;
  const act = () => {
    if (frame && frame.contentWindow) frame.contentWindow.postMessage({ goPlace: c.dataset.place }, mapOrigin === "null" ? "*" : mapOrigin);
    showWhy(c.dataset.place);
  };
  c.addEventListener("click", act);
  c.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); act(); } });
});
if (pop) {
  pop.querySelector(".x").addEventListener("click", () => { pop.hidden = true; });
  pop.addEventListener("click", e => e.stopPropagation());
}
addEventListener("message", e => { if (frame && e.source === frame.contentWindow && e.data && e.data.placeShown) showWhy(e.data.placeShown); });
const lb = $("#lockbtn");
if (lb) lb.addEventListener("click", () => { try { sessionStorage.removeItem("slp_key_v2"); sessionStorage.removeItem("slp_pin"); } catch (e) {} location.reload(); });
"""


# ============================================================================ the page
DRAFT_BAR = ('<p role="note" style="margin:0;padding:8px 16px;background:#fff6dc;border-bottom:1px solid #e6e2da;'
             'font:600 .85rem/1.4 Inter,system-ui,sans-serif;color:#8a6400;text-align:center">'
             'Draft for review: unfinished text or a placeholder contact remains. Not for publishing.</p>\n')

def build(spec: dict, gate_on: bool = True, draft: bool = False) -> tuple[str, list[str]]:
    warns = check_spec(spec, gate_on, draft)
    cfg = efw.site_config()
    warns += preflight(spec, cfg, gate_on, draft)
    p = spec["page"]
    secs = list(spec["sections"])
    if secs[0]["type"] != "hero":
        secs.insert(0, {"type": "hero"})
    if secs[-1]["type"] != "footer":
        secs.append({"type": "footer", "disclaimer": "Scientific research shared for information only. Results are research "
                     "estimates, not official assessments; do not use them as the sole basis for a decision."})
    fonts = efw.ASSETS / "fonts"
    fonts_css = (f'@font-face {{ font-family: "Inter"; font-style: normal; font-weight: 400 700; font-display: swap; '
                 f'src: url({data_uri(fonts / "Inter-var-latin.woff2")}) format("woff2") }}\n'
                 f'@font-face {{ font-family: "Source Serif 4"; font-style: normal; font-weight: 600; font-display: swap; '
                 f'src: url({data_uri(fonts / "SourceSerif4-600-latin.woff2")}) format("woff2") }}')
    css = (efw.ASSETS / "site.css").read_text()
    css = re.sub(r'@font-face \{ font-family: "Inter";[^\n]*\n@font-face \{ font-family: "Source Serif 4";[^\n]*\n', fonts_css + "\n", css)
    assert "Inter-var-latin.woff2\")" not in css, "font inlining failed"
    logos = logo_row(cfg)
    lock_btn = gate_on and spec.get("gate", {}).get("lock_button", True)

    nav, cta = [], None
    for s in secs:
        if s.get("nav") and s.get("id"):
            a = f'<a href="#{s["id"]}">{s["nav"]}</a>'
            if s.get("nav_cta"):
                cta = f'<a class="cta" href="#{s["id"]}">{s["nav"]}</a>'
            else:
                nav.append(a)
    if len(nav) > 7:
        warns.append(f"{len(nav)} nav labels: the desktop header shows the first 7 plus the call-to-action pill; drop some")
    if lock_btn and len(nav) > 5:
        warns.append(f"{len(nav)} nav labels with a Lock button: only the first 5 (and the CTA pill) show in the header; "
                     "put the most useful sections first or drop some")
    nav_html = ('<nav class="links" aria-label="Sections">' + "".join(nav) + (cta or "") + "</nav>") if nav or cta else ""
    lock_html = ('<button type="button" class="lockbtn" id="lockbtn" title="Lock this page again; the PIN is needed to reopen it">'
                 f'{LOCK}<span>Lock</span></button>') if lock_btn else ""

    body, paper = [], True
    for s in secs:
        if s["type"] == "hero":
            body.append(r_hero(s, spec, cfg))
            continue
        if s["type"] == "footer":
            continue
        bg = s.get("background", "auto")
        if bg != "auto":
            paper = bg == "paper"
        idattr = f' id="{s["id"]}"' if s.get("id") else ""
        body.append(f'<section{idattr}{" class=" + chr(34) + "paper" + chr(34) if paper else ""}><div class="wrap">{src(s)}\n  '
                    + RENDER[s["type"]](s, spec, cfg) + "\n</div></section>")
        paper = not paper
    footer = r_footer(secs[-1], spec, cfg, logos)

    title = f'{text(p["title"])} · {p["date"]}'
    og_t = p.get("og_title") or text(p["title"])
    og_d = p.get("og_description") or p["description"]
    og_img = p.get("og_image") or cfg.get("og_image")
    fav = efw.asset(cfg.get("favicon", "favicon.png"))
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    page = (f'<!doctype html>\n<html lang="{p.get("lang", "en")}">\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f"<title>{html.escape(title, quote=False)}</title>\n"
            + (gate_blocks(spec, cfg, fonts_css) if gate_on else "")
            + f'<meta name="description" content="{attr(p["description"])}">\n'
            f'<meta name="generated" content="{now}">\n<meta name="color-scheme" content="light">\n'
            + ('<meta name="efw-draft" content="review copy: unfinished text or a placeholder contact; do not publish">\n' if draft else "")
            +
            f'<meta property="og:type" content="website">\n<meta property="og:title" content="{attr(og_t)}">\n'
            f'<meta property="og:description" content="{attr(og_d)}">\n'
            + (f'<meta property="og:image" content="{attr(og_img)}">\n<meta property="og:image:alt" content="{attr(p.get("og_image_alt") or cfg.get("og_image_alt", ""))}">\n' if og_img else "")
            + f'<meta property="og:site_name" content="{attr(p.get("site_name") or cfg.get("site_name", ""))}">\n'
            '<meta name="twitter:card" content="summary">\n'
            f'<link rel="icon" type="image/png" href="{data_uri(fav)}">\n'
            f"<style>\n{css}</style>\n\n"
            f'<header class="top{" has-lock" if lock_btn else ""}"><div class="wrap">\n  <div class="logos" id="logos">{logos}</div>\n  {nav_html}{lock_html}\n</div></header>\n\n'
            + (DRAFT_BAR if draft else "") + body[0] + "\n\n<main>\n\n" + "\n\n".join(body[1:]) + "\n\n</main>\n\n" + footer
            + '\n\n<div id="tip" aria-hidden="true"></div>\n<script>' + JS + "</script>\n</html>\n")
    return page, warns


def main():
    global SHOW_SRC
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("spec", type=Path)
    ap.add_argument("out", nargs="?", help="output .html file, or a folder (ends in /, exists, or has no .html suffix): "
                                           "the file is then named <slug-of-title>-<date>.html; missing folders are made")
    ap.add_argument("--no-gate-blocks", action="store_true", help="open page: leave out the lock-screen blocks and the Lock button")
    ap.add_argument("--no-src", action="store_true", help="leave the SRC comments out of the page source")
    ap.add_argument("--validate", action="store_true", help="check the spec (and the contact, assets, settings) and stop")
    ap.add_argument("--draft", action="store_true", help="review copy: unfinished text (FILL:, TBD, ...) and a placeholder "
                                                         "contact only warn; the page carries a 'Draft' bar and an efw-draft "
                                                         "meta tag, and verify_gate.py refuses it")
    a = ap.parse_args()
    SHOW_SRC = not a.no_src
    gate_on = not a.no_gate_blocks
    try:
        spec = json.loads(a.spec.read_text())
    except FileNotFoundError:
        sys.exit(f"build_site: spec file {a.spec} not found")
    except json.JSONDecodeError as e:
        sys.exit(f"build_site: {a.spec} is not valid JSON: {e}")
    if not isinstance(spec, dict):
        sys.exit(f"build_site: {a.spec} must hold one JSON object (the site spec)")
    try:
        if a.validate:
            warns = check_spec(spec, gate_on, a.draft) + preflight(spec, efw.site_config(), gate_on, a.draft)
            for w in warns:
                print("WARN ", w)
            print(f"OK    {a.spec} ({len(spec['sections'])} sections)")
            return
        if not a.out:
            ap.error("give an output file or folder (or --validate)")
        page, warns = build(spec, gate_on=gate_on, draft=a.draft)
    except SpecError as e:
        sys.exit("build_site: the spec has problems:\n  " + str(e).replace("\n", "\n  "))
    raw = a.out
    out = Path(raw)
    if raw.endswith(("/", os.sep)) or out.is_dir() or out.suffix.lower() not in (".html", ".htm"):
        out.mkdir(parents=True, exist_ok=True)
        out = out / f'{slug(spec["page"]["title"])}-{spec["page"]["date"]}.html'
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    for w in warns:
        print("WARN ", w)
    kinds = [s["type"] for s in spec["sections"]]
    print(f"wrote {out} ({len(page.encode()) / 1024:.0f} KB; sections: {', '.join(kinds)}; "
          f"lock-screen blocks: {'yes' if gate_on else 'no'}{'; DRAFT, not for publishing' if a.draft else ''})")


if __name__ == "__main__":
    main()
