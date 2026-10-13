#!/usr/bin/env python3
"""vizkit — building blocks for our HTML data-visualization pages (wri-html-pages skill).

WHY THIS EXISTS
    The pages we share should read as one system: the same type, colours, tooltips, "how to read"
    box, key style, and footer, and they must work on a phone. vizkit returns HTML strings for the
    pieces we use over and over, so a page script only has to compute numbers and arrange them.
    Everything is plain HTML/CSS plus one small tooltip script: no chart library, no build step,
    one self-contained file.

USE
    import sys; sys.path.insert(0, "<skill base directory>/scripts")
    import vizkit as vk
    body = vk.section("Title", vk.hbar(rows, series, unit="%"))
    Path("page.html").write_text(vk.page("Page title", body, lede="...", sources=[...], footer="..."))

    Components: page, section, note, stat_tiles, legend, hbar, columns, line_chart, heatmap, table.
    Helpers:    fint, fpct, fnum, ramp_color, RAMPS, SERIES.
    Tooltips:   any element with data-tip="Heading\\nline 2\\nline 3" gets a styled tooltip on hover,
                keyboard focus or tap. The first line is bold. The cursor never changes.

    All text arguments are HTML (trusted, written by the page author). Escape data-derived strings
    with vk.esc() before passing them.
"""
from __future__ import annotations

import html
import math
from typing import Iterable, Sequence

esc = html.escape
_SKILL = __import__("pathlib").Path(__file__).resolve().parents[1]


# ============================================================================ who made it (identity.json)
def identity_path():
    """Where the author, organisations and publishing site come from. Personal settings win over the bundled
    ones, so updating the skill never overwrites them: $WRI_HTML_PAGES_IDENTITY, then
    ~/.config/<skill folder>/identity.json, then the bundled references/identity.json (the WRI team's)."""
    import os
    from pathlib import Path
    for p in (os.environ.get("WRI_HTML_PAGES_IDENTITY"), Path.home() / ".config" / _SKILL.name / "identity.json"):
        if p and Path(p).expanduser().is_file():
            return Path(p).expanduser()
    return _SKILL / "references" / "identity.json"


def load_identity() -> dict:
    """Author, organisations and GitHub shown on every page (see identity_path for where it is read from)."""
    import json
    return json.loads(identity_path().read_text())


def generated_iso(tz: str | None = None) -> str:
    """Machine-readable generation time for <meta name="generated">, e.g. '2026-10-12T10:22:05-07:00'."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo(tz or load_identity().get("timezone", "UTC"))).isoformat(timespec="seconds")


def built_at(tz: str | None = None) -> str:
    """Build timestamp in the team's time zone, e.g. '2026-10-12 17:24 PDT'."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo(tz or load_identity().get("timezone", "UTC"))).strftime("%Y-%m-%d %H:%M %Z")


def today(tz: str | None = None) -> str:
    """Today's date in the team's time zone (identity.json), for the date at the end of a title, so the title and
    the byline agree even when the server runs on UTC."""
    return built_at(tz)[:10]


def byline(author: str | None = None, affiliation: str | None = None, when: str | None = None) -> str:
    """'By <author>, <affiliation> · <timestamp>'. Defaults from identity.json; pass author= for someone else."""
    idt = load_identity()
    a = author or idt["author"]
    aff = affiliation if author else (affiliation or idt.get("affiliation"))
    return (f'<p class="byline">By <b>{esc(a)}</b>{", " + esc(aff) if aff else ""} · '
            + " · ".join(f'<time>{esc(w)}</time>' for w in (when or built_at()).split(" · ")) + '</p>')   # each part wraps whole


def _logo(org: dict) -> str:
    import base64
    f = identity_path().parent / org["logo"]          # a personal identity.json can sit next to its own logos
    if not f.is_file():
        f = _SKILL / "assets" / org["logo"]
    if f.suffix == ".svg":
        return f.read_text().replace("<svg ", '<svg class="logo" ', 1)
    mime = "image/png" if f.suffix == ".png" else "image/jpeg"
    return f'<img class="logo" alt="{esc(org["short"])} logo" src="data:{mime};base64,{base64.b64encode(f.read_bytes()).decode()}">'


def brand_strip() -> str:
    """Linked NCEAS and WRI logos plus the WRI GitHub links (inline, so the page stays one file)."""
    idt = load_identity()
    orgs = "".join(f'<a class="org" href="{esc(o["url"])}" target="_blank" rel="noopener">{_logo(o)}'
                   f'<span><b>{esc(o["short"])}</b><small>{esc(o["name"])}</small></span></a>' for o in idt["orgs"])
    gh = idt.get("github") or {}
    ghl = ""
    if gh:
        short = gh["url"].split("github.com/")[-1]
        ghl = f'<p class="gh">{esc(gh["label"])}: <a href="{esc(gh["url"])}" target="_blank" rel="noopener">github.com/{esc(short)}</a>'
        if gh.get("pages_repo"):
            ghl += f' · pages: <a href="{esc(gh["pages_repo"])}" target="_blank" rel="noopener">{esc(gh["pages_repo"].split("github.com/")[-1])}</a>'
        ghl += "</p>"
    return f'<div class="brand">{orgs}{ghl}</div>'

_STOP = {"a", "an", "the", "of", "in", "on", "with", "for", "and", "to", "from", "by", "at", "all", "its", "as"}


def slug(title: str, max_len: int = 200) -> str:
    """File name stem from a page's full title (team rule 2026-10-12: the link carries the title).
    '2026-10-13 · Penguin records around Palmer Station (1898–2026): 13,114 GBIF records' ->
    '2026-10-13-penguin-records-around-palmer-station-1898-2026-13114-gbif-records'. Drops filler words, keeps
    numbers, cuts at a word boundary under max_len."""
    import re as _re
    import unicodedata as _ud
    t = _re.sub(r"[\u2010-\u2015\u2212]", "-", _re.sub(r"<[^>]+>", " ", title))      # en/em dashes, minus -> '-'
    t = _ud.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    t = _re.sub(r"(?<=\d),(?=\d{3})", "", t).replace("&", " and ").replace("%", " pct ")
    words = [w for w in _re.split(r"[^a-z0-9.]+", t) if w and w not in _STOP]
    words = [w.strip(".") for w in words if w.strip(".")]
    out = ""
    for w in words:
        if len(out) + len(w) + 1 > max_len:
            break
        out = f"{out}-{w}" if out else w
    return out

# ============================================================================ palette
# Categorical series (Okabe–Ito, colour-blind safe). Use the SAME colour for the same concept on
# every chart of a page (and across a project's pages): pass color="var(--s1)" etc. or a hex.
SERIES = ["var(--s1)", "var(--s2)", "var(--s3)", "var(--s4)", "var(--s5)", "var(--s6)", "var(--s7)"]
RAMPS = {
    # sequential, light -> dark (colour-blind safe); for counts, shares, intensities
    "heat": ["#FFF5D6", "#FEE3A2", "#FEC771", "#FDA54F", "#F67F3A", "#E5582C", "#C73A23", "#9E2418", "#6E1610"],
    "blues": ["#EFF5FB", "#D3E4F3", "#AFCDE8", "#84B1DA", "#5A93CA", "#3A76B6", "#245B9C", "#16427A", "#0E2C55"],
    "viridis": ["#440154", "#482878", "#3E4A89", "#31688E", "#26828E", "#1F9E89", "#35B779", "#6DCD59", "#B4DE2C", "#FDE725"],
    # good -> bad (green -> yellow -> red), as on the canopy validation page: 0 = good. Always pair
    # with printed numbers; red-green alone fails for colour-blind readers.
    "good_bad": ["#1A9850", "#60B85D", "#A6D96A", "#D2DC7A", "#FEE08B", "#FEC776", "#FDAE61", "#F88E52", "#F46D43", "#E64E35", "#D73027"],
    # diverging around a midpoint (blue = below, red = above)
    "diverging": ["#2166AC", "#4393C3", "#92C5DE", "#D1E5F0", "#F7F7F7", "#FDDBC7", "#F4A582", "#D6604D", "#B2182B"],
}

CSS = r"""
:root{
  --bg:#F5F7F9; --surface:#FFFFFF; --raised:#FBFCFD; --ink:#13202C; --ink-2:#465667; --ink-3:#768494;
  --line:#E1E6EB; --line-2:#CBD3DB; --accent:#1B4F8A; --accent-ink:#FFFFFF; --accent-soft:#E7EFF8; --empty:#ECEFF2; --flag:#C62828;
  --s1:#0072B2; --s2:#E69F00; --s3:#009E73; --s4:#D55E00; --s5:#56B4E9; --s6:#CC79A7; --s7:#8A949E;
  --shadow:0 1px 2px rgba(16,24,40,.06),0 8px 24px rgba(16,24,40,.12);
  --f-sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --f-mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace; color-scheme:light;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#0D1217; --surface:#141B22; --raised:#18212A; --ink:#E7EDF3; --ink-2:#A8B5C2; --ink-3:#7B8895;
  --line:#243039; --line-2:#33414D; --accent:#7EB2EE; --accent-ink:#0D1217; --accent-soft:#18283A; --empty:#1E2730; --flag:#FF6B5E;
  --s1:#4AA3E0; --s2:#F2B33D; --s3:#2EC496; --s4:#F07B3F; --s5:#86CDF2; --s6:#E59CC8; --s7:#8D99A6;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px rgba(0,0,0,.45); color-scheme:dark; }}
:root[data-theme="dark"]{
  --bg:#0D1217; --surface:#141B22; --raised:#18212A; --ink:#E7EDF3; --ink-2:#A8B5C2; --ink-3:#7B8895;
  --line:#243039; --line-2:#33414D; --accent:#7EB2EE; --accent-ink:#0D1217; --accent-soft:#18283A; --empty:#1E2730; --flag:#FF6B5E;
  --s1:#4AA3E0; --s2:#F2B33D; --s3:#2EC496; --s4:#F07B3F; --s5:#86CDF2; --s6:#E59CC8; --s7:#8D99A6;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px rgba(0,0,0,.45); color-scheme:dark; }
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:400 16px/1.6 var(--f-sans);-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-underline-offset:3px;text-decoration-thickness:1px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:3px}
.wrap{max-width:1080px;margin:0 auto;padding:32px 20px 72px}
.topbar{display:flex;justify-content:space-between;align-items:center;gap:12px}
.eyebrow{font:500 12px/1.2 var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3)}
h1{font-size:clamp(26px,3.4vw,36px);line-height:1.2;letter-spacing:-.015em;margin:10px 0 0;font-weight:600}
h1.long{font-size:clamp(21px,2.4vw,27px);line-height:1.3;max-width:62ch}
.subtitle{font-size:clamp(16.5px,1.6vw,18.5px);color:var(--ink);max-width:70ch;margin:10px 0 0;line-height:1.5}
.lede{font-size:clamp(16px,1.5vw,17.5px);color:var(--ink-2);max-width:64ch;margin:14px 0 0}
h2{font-size:22px;line-height:1.3;letter-spacing:-.01em;margin:0;font-weight:600}
h3{font-size:16.5px;line-height:1.35;margin:0;font-weight:600}
section.sec{margin-top:52px}
.sec-lede{color:var(--ink-2);max-width:70ch;margin:8px 0 0}
p{max-width:75ch}
.note{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:10px;padding:14px 18px;margin:24px 0 0}
.note h3{font-size:15px;margin-bottom:4px}
.note p{margin:6px 0;color:var(--ink-2);font-size:15px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin-top:16px}
.cap{font-size:14px;color:var(--ink-2);margin:4px 0 0}
.src{font-size:12.5px;color:var(--ink-3);margin:12px 0 0}
.muted{color:var(--ink-2)} .faint{color:var(--ink-3)} .num{font-variant-numeric:tabular-nums}
.nw{white-space:nowrap}
.tech{display:none}
html[data-lang="tech"] .tech{display:revert} html[data-lang="tech"] .plain{display:none}
.btns{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}
.ax-y{font-size:12.5px;color:var(--ink-2);margin:8px 0 6px;width:fit-content}
.ax-x{font-size:12.5px;color:var(--ink-2);margin:6px auto 0;width:fit-content}
.legend .k[data-tip],.ax-y[data-tip],.ax-x[data-tip],.axis-t[data-tip],h3[data-tip],th[data-tip]{text-decoration:underline dotted var(--ink-3);text-underline-offset:3px}
.themebtn{white-space:nowrap;flex:none;font:500 13px var(--f-sans);border:1px solid var(--line-2);background:var(--surface);color:var(--ink-2);border-radius:999px;padding:6px 12px}
/* stat tiles */
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,180px),1fr));gap:12px;margin-top:24px}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.tile .v{font:600 30px/1.1 var(--f-sans);letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.tile .l{font-size:14.5px;margin-top:6px}
.tile .s{font-size:13px;color:var(--ink-3);margin-top:2px}
/* legend: big, friendly keys */
.legend{display:flex;flex-wrap:wrap;gap:8px 20px;margin:12px 0 14px;font-size:14.5px}
.legend .k{display:inline-flex;align-items:center;gap:4px 8px;flex-wrap:wrap;max-width:100%}
.legend .sw{width:18px;height:14px;border-radius:4px;flex:none}
.legend .ln{width:22px;height:0;border-top:2px dashed var(--ink-2)}
/* horizontal bars */
.hb{display:grid;grid-template-columns:minmax(96px,max-content) minmax(0,1fr);gap:12px 14px;align-items:center;margin-top:14px}
.hb .lab{font-size:14.5px;line-height:1.25;text-align:right}
.hb .lab small{display:block;color:var(--ink-3);font-size:12.5px}
.hb .area{position:relative;margin-right:72px;display:grid;gap:3px}
.hb .grid{position:absolute;top:-6px;bottom:-6px;width:0;border-left:1px solid var(--line)}
.hb .ref{position:absolute;top:-6px;bottom:-6px;width:0;border-left:2px dashed var(--ink-2);z-index:1}
.hb .brow{position:relative;height:20px}
.hb .bar{position:relative;height:20px;border-radius:0 4px 4px 0;min-width:2px;transition:filter .15s,box-shadow .15s;z-index:2}
.hb .bar:hover,.hb .bar:focus{filter:brightness(1.12);box-shadow:0 0 0 2px var(--ink)}
.hb .val{position:absolute;top:50%;transform:translateY(-50%);font:500 13px var(--f-mono);white-space:nowrap;color:var(--ink);background:var(--surface);padding:0 3px;border-radius:3px;z-index:4}
.hb .ci{position:absolute;top:50%;height:10px;transform:translateY(-50%);border-left:1.5px solid var(--ink);border-right:1.5px solid var(--ink);z-index:3}
.hb .ci::before{content:"";position:absolute;left:0;right:0;top:50%;border-top:1.5px solid var(--ink)}
.hb .axis{position:relative;height:18px;margin-right:72px;font:400 12px var(--f-mono);color:var(--ink-3)}
.hb .axis span{position:absolute;transform:translateX(-50%);white-space:nowrap}
.axis-t{font-size:13px;color:var(--ink-2);text-align:center;margin:4px 72px 0 0}
@media (max-width:560px){
  .hb{grid-template-columns:minmax(0,1fr);gap:4px}
  .hb .lab{text-align:left;margin-top:8px}
  .hb .lab small{display:inline;margin-left:6px}
  .hb .area,.hb .axis{margin-right:64px}
}
/* columns (e.g. one per year) */
.cols{display:flex;align-items:flex-end;gap:3px;height:240px;margin-top:30px;border-bottom:1px solid var(--line-2);position:relative}
.ax-y + .cols{margin-top:40px}   /* room for the top tick label under the axis title */
.cols .c{flex:1 1 0;min-width:0;height:100%;display:flex;flex-direction:column;justify-content:flex-end;position:relative}
.cols .seg{width:100%;transition:filter .15s}
.cols .c:hover .seg,.cols .c:focus .seg{filter:brightness(1.12)}
.cols .c .seg:first-child{border-radius:3px 3px 0 0}
.cols .cv{position:absolute;left:50%;transform:translateX(-50%);font:500 11.5px var(--f-mono);white-space:nowrap;color:var(--ink-2)}
.xl{display:flex;gap:3px;margin-top:6px}
.xl span{flex:1 1 0;min-width:0;text-align:center;font:400 11.5px var(--f-mono);color:var(--ink-3);white-space:nowrap;overflow:visible}
.cols .gl{position:absolute;left:0;right:0;border-top:1px dashed var(--line);font:400 11px var(--f-mono);color:var(--ink-3)}
.cols .gl span{position:absolute;top:-16px;left:0}
.cols .short{display:none}
/* line chart: a wide drawing for desktop and a narrow one for phones, so nothing scrolls sideways */
.svgwrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
.svgwrap svg{display:block;width:100%;height:auto}
.svgwrap svg.narrow{display:none}
.svgwrap svg.keep{min-width:600px}
.svgwrap text{font-family:var(--f-mono);font-size:calc(12.5px * var(--k, 1));fill:var(--ink-3)}
.svgwrap .gridl{stroke:var(--line);stroke-width:1}
.svgwrap .axisl{stroke:var(--line-2);stroke-width:1}
.svgwrap .pt{transition:r .15s}
.svgwrap .pt:hover,.svgwrap .pt:focus{r:7}
/* heatmap table */
.scroll{overflow:auto;-webkit-overflow-scrolling:touch;margin-top:8px;max-height:78vh}
/* frozen panes: header row and first column stay put while a big table scrolls */
.scroll table thead th{position:sticky;top:0;z-index:2;background:var(--surface)}
.scroll table tbody th:first-child,.scroll table tbody td:first-child,.scroll table thead th:first-child{position:sticky;left:0;z-index:1;background:var(--surface)}
.scroll table thead th:first-child{z-index:3}
.scroll table.tb tbody tr:hover td:first-child{background:var(--raised)}
table.hm{border-collapse:separate;border-spacing:3px;font-variant-numeric:tabular-nums}
table.hm caption{text-align:left;font-size:13px;color:var(--ink-2);padding:0 0 6px}
table.hm thead th{font:500 12px var(--f-mono);color:var(--ink-3);padding:2px 4px;white-space:nowrap}
table.hm th.rl{text-align:right;font-weight:400;padding-right:10px;white-space:nowrap;font-size:14px}
table.hm tr.grp th{text-align:left;font:500 11.5px var(--f-mono);letter-spacing:.07em;text-transform:uppercase;color:var(--ink-3);padding:14px 0 3px;border-bottom:1px solid var(--line)}
table.hm td.c{min-width:58px;height:50px;text-align:center;border-radius:5px;line-height:1.15;padding:3px 4px;transition:box-shadow .15s}
table.hm td.c:hover,table.hm td.c:focus{box-shadow:0 0 0 2px var(--ink)}
table.hm td.c b{display:block;font-size:16px;font-weight:600}
table.hm td.c i{display:block;font-style:normal;font-size:10.5px;margin-top:2px;opacity:.85}
table.hm td.c.dk{color:#0B0B0B} table.hm td.c.lt{color:#FFFFFF}
table.hm td.c.empty{background:var(--empty);color:var(--ink-3)}
table.hm td.x{font-size:13px;color:var(--ink-2);padding:0 8px;text-align:right;white-space:nowrap}
.ramp{display:inline-flex;vertical-align:middle;margin:0 8px;border-radius:3px;overflow:hidden}
.ramp i{width:18px;height:14px}
/* phone="cards" layouts (chosen per chart; see charts.md, "Phone layout") */
.hm-m{display:none}
.hm-g{font:500 11.5px var(--f-mono);letter-spacing:.07em;text-transform:uppercase;color:var(--ink-3);margin:14px 0 2px;padding-bottom:3px;border-bottom:1px solid var(--line)}
.hm-r{padding:9px 0;border-bottom:1px solid var(--line)}
.hm-r:last-child{border-bottom:0}
.hm-rh{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:6px}
.hm-rh b{font-size:15px}
.hm-rh span{font-size:12.5px;color:var(--ink-2);text-align:right}
.hm-cells{display:grid;grid-template-columns:repeat(auto-fill,minmax(42px,1fr));gap:4px}
.hm-c{border-radius:5px;text-align:center;padding:3px 2px 4px;line-height:1.12;font-variant-numeric:tabular-nums}
.hm-c small{display:block;font:400 9.5px var(--f-mono);opacity:.8}
.hm-c b{display:block;font-size:14.5px;font-weight:600;margin-top:1px}
.hm-c i{display:block;font-style:normal;font-size:9.5px;opacity:.85;margin-top:1px}
.hm-c.dk{color:#0B0B0B} .hm-c.lt{color:#FFFFFF} .hm-c.empty{background:var(--empty);color:var(--ink-3)}
/* an interactive map as a panel in a chart page (map_panel) */
.mapframe{display:block;width:100%;height:var(--h,520px);border:1px solid var(--line);border-radius:10px;background:var(--bg);margin-top:10px}
@media (max-width:560px){.mapframe{height:var(--ph,440px)}}
/* shaded table cells (table(shade=...)) and flagged cells (a cell dict with "flag") */
table.tb td.sh{font-variant-numeric:tabular-nums}
table.tb td.flag{box-shadow:inset 0 0 0 2px var(--flag);font-weight:600}
table.hm td.c.flag{outline:2.5px solid var(--flag);outline-offset:-2.5px}
.legend .flagsw{width:18px;height:14px;border-radius:3px;box-shadow:inset 0 0 0 2px var(--flag)}
/* the rigor pass under a panel */
details.checks{margin-top:12px;font-size:13px;color:var(--ink-2);border-top:1px solid var(--line);padding-top:8px}
details.checks summary{font:500 12px var(--f-mono);letter-spacing:.04em;color:var(--ink-3);list-style:none;display:flex;align-items:center;gap:6px}
details.checks summary::-webkit-details-marker{display:none}
details.checks summary::marker{content:""}
details.checks summary::before{content:"";width:6px;height:6px;border-right:1.5px solid var(--ink-3);border-bottom:1.5px solid var(--ink-3);transform:rotate(-45deg);transition:transform .15s}
details.checks[open] summary::before{transform:rotate(45deg)}
details.checks ul{margin:6px 0 0;padding-left:18px} details.checks li{margin:3px 0}
/* living pages: each panel carries when it was added / updated; page history at the foot */
.pstamp{float:right;margin:0 0 6px 12px;font:400 11.5px var(--f-mono);color:var(--ink-3);white-space:nowrap}
@media (max-width:560px){.pstamp{float:none;display:block;margin:0 0 4px}}
section.panel{margin-top:22px}
details.history{margin-top:40px;font-size:13.5px;color:var(--ink-2)}
details.history summary{font:500 12px var(--f-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3)}
details.history li{margin:3px 0}
/* plain tables */
table.tb{border-collapse:collapse;width:100%;font-size:14.5px;font-variant-numeric:tabular-nums}
table.tb th,table.tb td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
table.tb thead th{font:500 12px var(--f-mono);letter-spacing:.05em;text-transform:uppercase;color:var(--ink-3);border-bottom:1px solid var(--line-2)}
table.tb td.n,table.tb th.n{text-align:right;white-space:nowrap}
table.tb tbody tr:hover{background:var(--raised)}
/* tooltip */
#tip{position:fixed;z-index:50;pointer-events:none;max-width:300px;background:var(--surface);color:var(--ink);border:1px solid var(--line-2);
  border-radius:8px;padding:9px 11px;font-size:13px;line-height:1.45;box-shadow:var(--shadow);display:none}
#tip b{display:block;margin-bottom:2px;font-size:13.5px}
#tip .mean{margin-top:5px;padding-top:5px;border-top:1px solid var(--line);color:var(--ink)}
[data-tip]{cursor:default}
footer.site{margin-top:64px;padding-top:20px;border-top:1px solid var(--line);font-size:13.5px;color:var(--ink-2)}
footer.site h3{font:500 12px/1.2 var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);margin:0 0 8px}
footer.site ul{padding-left:18px;margin:0 0 12px} footer.site li{margin:4px 0}
@media (max-width:560px){
  /* phones: reflow charts to the width instead of scrolling them sideways */
  .svgwrap svg.wide{display:none} .svgwrap svg.narrow{display:block}
  .cols .full{display:none} .cols .short{display:inline}
  .cols.dense .cv{display:none} .xl.dense span.alt{visibility:hidden}
  .tiles{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
  .tile{padding:11px 12px} .tile .v{font-size:23px} .tile .l{font-size:13.5px} .tile .s{font-size:12px}
  /* phone="cards": heatmap rows and table rows become cards */
  .hm-desk{display:none} .hm-m{display:block}
  .scroll.tb-cards-box{overflow:visible;max-height:none}
  table.tb.tb-cards thead{display:none}
  table.tb.tb-cards,table.tb.tb-cards tbody{display:block;width:100%}
  /* compact card: the first cell is the heading, the rest sit three across with the label above the value */
  table.tb.tb-cards tr{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px 10px;border:1px solid var(--line);
    border-radius:10px;padding:9px 12px;margin:0 0 8px;background:var(--surface)}
  table.tb.tb-cards td,table.tb.tb-cards td.n{position:static;display:block;border:0;padding:0;text-align:left;white-space:normal;background:none}
  table.tb.tb-cards td::before{content:attr(data-label);display:block;color:var(--ink-3);font:500 10.5px var(--f-mono);text-transform:uppercase;letter-spacing:.04em}
  table.tb.tb-cards td:first-child{grid-column:1/-1;font-weight:600;font-size:15.5px}
  table.tb.tb-cards td:first-child::before{content:none}
  /* phone="scroll" (default for tables): tighter cells; the scroll box keeps row labels and headers frozen */
  table.hm{border-spacing:2px}
  table.hm td.c{min-width:40px;height:42px;padding:2px}
  table.hm td.c b{font-size:14px} table.hm td.c i{font-size:9.5px}
  table.hm th.rl{font-size:13px;padding-right:6px}
  table.hm thead th{font-size:11px;padding:2px}
  table.hm td.x{font-size:12px;padding:0 5px}
  table.tb{font-size:13.5px} table.tb th,table.tb td{padding:7px 8px}
  .wrap{padding:22px 14px 56px}
  .card{padding:14px 12px}
  table.hm td.c{min-width:46px;height:46px}
  table.hm td.c b{font-size:15px}
  table.hm th.rl{font-size:13px;padding-right:6px}
}
/* byline and the NCEAS / WRI / GitHub strip (identity.json) */
.byline{margin:10px 0 0;font-size:14px;color:var(--ink-2)}
.byline time{font-family:var(--f-mono);font-size:13px;white-space:nowrap}
.brand{display:flex;flex-wrap:wrap;align-items:center;gap:14px 26px;margin-top:18px;padding-top:16px;border-top:1px solid var(--line)}
.brand .org{display:inline-flex;align-items:center;gap:10px;color:var(--ink);text-decoration:none;transition:transform .18s ease}
.brand .org:hover,.brand .org:focus-visible{transform:translateY(-2px) rotate(-1.5deg)}
.brand .logo{height:40px;width:auto;flex:none;display:block}
.brand svg.logo{color:var(--ink)}
.brand .org b{display:block;font-size:14px;line-height:1.2}
.brand .org small{display:block;font-size:12px;color:var(--ink-3);line-height:1.3;max-width:24ch}
.brand .gh{flex-basis:100%;margin:0;font-size:13px;color:var(--ink-2)}
.brand .gh{max-width:none}
.brand .gh a{font-family:var(--f-mono);font-size:12.5px;white-space:nowrap}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
"""

TIP_JS = r"""
(function(){
  const tip = document.getElementById('tip');
  let pinned = null;
  const tech = () => document.documentElement.dataset.lang === 'tech';
  function fill(el){ tip.textContent = ''; const parts = el.dataset.tip.split('\n@@tech\n');
    const txt = (tech() && parts[1]) ? parts[1] : parts[0];
    txt.split('\n').forEach((t, i) => { const n = document.createElement(i ? 'div' : 'b');
      if(i && t.startsWith('What it suggests: ')){ n.className = 'mean'; }
      n.textContent = t; tip.appendChild(n); }); }
  function place(el){ const r = el.getBoundingClientRect(); tip.style.display = 'block';
    const w = tip.offsetWidth, h = tip.offsetHeight;
    let x = r.right + 10, y = r.top + r.height / 2 - h / 2;
    if(x + w > innerWidth - 8) x = r.left - w - 10;
    if(x < 8){ x = Math.min(Math.max(8, r.left + r.width / 2 - w / 2), innerWidth - w - 8); y = r.bottom + 8;
      if(y + h > innerHeight - 8) y = r.top - h - 8; }
    tip.style.left = x + 'px'; tip.style.top = Math.max(8, Math.min(y, innerHeight - h - 8)) + 'px'; }
  function show(el){ fill(el); place(el); }
  function hide(){ tip.style.display = 'none'; pinned = null; }
  document.querySelectorAll('[data-tip]').forEach(el => {
    if(!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '0');
    el.addEventListener('mouseenter', () => show(el));
    el.addEventListener('mouseleave', () => { if(pinned !== el) tip.style.display = 'none'; });
    el.addEventListener('focus', () => show(el));
    el.addEventListener('blur', () => { if(pinned !== el) tip.style.display = 'none'; });
    el.addEventListener('click', e => { e.stopPropagation(); if(pinned === el){ hide(); return; } pinned = el; show(el); });
  });
  document.addEventListener('click', hide);
  addEventListener('scroll', () => { if(!pinned) tip.style.display = 'none'; else place(pinned); }, {passive:true});
  document.addEventListener('keydown', e => { if(e.key === 'Escape') hide(); });
  // keep SVG chart text the same size on screen when the chart is drawn narrower than its viewBox
  function fitText(){ document.querySelectorAll('.svgwrap svg').forEach(svg => {
    const vb = svg.viewBox.baseVal.width, w = svg.getBoundingClientRect().width || vb;
    svg.style.setProperty('--k', Math.min(1.4, Math.max(1, vb / w)).toFixed(3)); }); }
  fitText(); addEventListener('resize', fitText);
  // map panels follow the page's light / dark and plain / technical switches
  function syncFrames(){ const r = document.documentElement, msg = {};
    if(r.dataset.theme) msg.theme = r.dataset.theme; msg.lang = r.dataset.lang || 'plain';
    document.querySelectorAll('iframe.mapframe').forEach(f => { try { f.contentWindow.postMessage(msg, '*'); } catch(e){} }); }
  // plain language / technical switch (shown only on pages that have both versions); remembered per reader
  const lb = document.getElementById('langbtn');
  function setLang(l){ document.documentElement.dataset.lang = l; if(lb){ lb.textContent = l === 'tech' ? 'Technical' : 'Plain language';
    lb.setAttribute('aria-pressed', String(l === 'tech')); } hide(); syncFrames(); try { localStorage.setItem('vk_lang', l); } catch(e){} }
  if(lb){ let l0 = 'plain'; try { l0 = localStorage.getItem('vk_lang') || 'plain'; } catch(e){}
    setLang(l0); lb.addEventListener('click', () => setLang(tech() ? 'plain' : 'tech')); }
  document.querySelectorAll('iframe.mapframe').forEach(f => f.addEventListener('load', syncFrames));
  const tb = document.getElementById('themebtn');
  if(tb) tb.addEventListener('click', () => { const r = document.documentElement;
    const dark = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    r.dataset.theme = dark ? 'light' : 'dark'; syncFrames(); });
})();
"""

FONTS = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&"
         "family=IBM+Plex+Sans:wght@400;500;600;700&display=swap")


# ============================================================================ formatting
def fint(x) -> str:
    """12,345"""
    return f"{int(round(x)):,}"


def fpct(x, d: int = 0, ratio: bool = True) -> str:
    """0.123 -> '12%' (ratio=True) or 12.3 -> '12%' (ratio=False)."""
    v = x * 100 if ratio else x
    return f"{v:,.{d}f}%"


def fnum(x, d: int = 1) -> str:
    return f"{x:,.{d}f}"


TECH_MARK = "@@tech"   # separates the plain and the technical text inside one data-tip


def tip(*lines, meaning: str | None = None, tech=None) -> str:
    """Attribute value for data-tip. The first line is the bold heading.
    meaning: a plain-language reading ("What it suggests: …"), shown in plain mode.
    tech:    technical lines (str or list), shown instead when the reader switches the page to Technical;
             the heading is repeated. Without tech, the same text shows in both modes."""
    plain = [str(t) for t in lines if t is not None and t != ""]
    if meaning:
        plain.append("What it suggests: " + meaning)
    out = "\n".join(plain)
    if tech:
        tl = [tech] if isinstance(tech, str) else list(tech)
        out += f"\n{TECH_MARK}\n" + "\n".join(([plain[0]] if plain else []) + [str(t) for t in tl if t])
    return esc(out, quote=True)


def dual(plain_html: str, tech_html: str, block: bool = False) -> str:
    """Text with a plain-language and a technical version (captions, notes, ledes); the page's
    Plain / Technical switch shows one of them. Plain should say what the result suggests."""
    tag = "div" if block else "span"
    return f'<{tag} class="plain">{plain_html}</{tag}><{tag} class="tech">{tech_html}</{tag}>'


def _ta(t) -> str:
    """ data-tip attribute from a vk.tip(...) string (or plain text), or nothing."""
    return f' data-tip="{str(t).replace(chr(34), "&quot;")}"' if t else ""


def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def ramp_color(v, lo, hi, ramp="heat"):
    """Linear interpolation along a named ramp (or a list of hex colours)."""
    cs = RAMPS[ramp] if isinstance(ramp, str) else ramp
    t = 0.0 if hi == lo else min(1.0, max(0.0, (v - lo) / (hi - lo)))
    f = t * (len(cs) - 1)
    i = min(int(f), len(cs) - 2)
    a, b = _hex(cs[i]), _hex(cs[i + 1])
    k = f - i
    return "#%02X%02X%02X" % tuple(round(a[j] + (b[j] - a[j]) * k) for j in range(3))


def _is_light(hexc):
    r, g, b = (x / 255 for x in _hex(hexc))
    lin = [(c / 12.92) if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2] > 0.33


def _nice_ticks(lo, hi, n=5, cover=False):
    """Round tick values from lo to hi. cover=True adds one more tick when the last one falls short of hi,
    so an axis built on the ticks always contains the data (columns used to clip their tallest bar)."""
    span = hi - lo
    if span <= 0:
        return [lo]
    step = 10 ** math.floor(math.log10(span / n))
    for m in (1, 2, 2.5, 5, 10):
        if span / (step * m) <= n:
            step *= m
            break
    first = math.ceil(lo / step) * step
    out, v = [], first
    while v <= hi + 1e-9:
        out.append(round(v, 10))
        v += step
    if cover and out and out[-1] < hi - 1e-9:
        out.append(round(out[-1] + step, 10))
    return out


def _compact(v) -> str:
    """Short number for narrow screens: 21622 -> '21.6k', 200000 -> '200k', 1500000 -> '1.5M'."""
    a = abs(v)
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if a >= div:
            x = v / div
            return (f"{x:.0f}" if abs(x) >= 100 or abs(x - round(x)) < 0.05 else f"{x:.1f}") + suf
    return f"{v:,.0f}" if abs(v - round(v)) < 1e-9 else f"{v:,.1f}"


def _tick_label(v, unit, compact: bool = False):
    if compact:
        return _compact(v) + ("%" if unit == "%" else "")
    s = f"{v:,.0f}" if abs(v - round(v)) < 1e-9 else f"{v:,.1f}"
    return s + ("%" if unit == "%" else "")


# ============================================================================ page shell
def page(title: str, body: str, *, subtitle: str = "", eyebrow: str = "", lede: str = "", how_to_read: str = "",
         tiles: str = "", sources: Iterable[str] = (), footer: str = "", noindex: bool = False,
         theme_toggle: bool = True, author: str | None = None, affiliation: str | None = None,
         byline_when: str | None = None, extra_head: str = "") -> str:
    """A full, self-contained page. (For iterative work use living_page(), which builds on this.)
    title:    short, date at the end (vk.today()): "Penguin body mass by species and sex · 2026-10-13".
    subtitle: the detail (cohort, counts, years, measure, split, what is new in this iteration).
    `how_to_read` is shown as a callout under the lede. The generation time is written into the file
    (<meta name="generated">, a comment on line 2) and shown in the byline."""
    gen_iso, gen_txt = generated_iso(), built_at()
    plain_sub = __import__("re").sub(r"<[^>]+>", "", subtitle)
    head_note = note("How to read this page", how_to_read) if how_to_read else ""
    src = "".join(f"<li>{s}</li>" for s in sources)
    robots = '<meta name="robots" content="noindex,nofollow">' if noindex else ""
    toggle = '<button type="button" class="themebtn" id="themebtn" aria-label="Switch light or dark">Light / dark</button>' if theme_toggle else ""
    has_tech = any(('class="tech"' in x) or (TECH_MARK in x) for x in (body, tiles, how_to_read, subtitle, lede))
    if has_tech:
        toggle = ('<button type="button" class="themebtn" id="langbtn" aria-pressed="false" '
                  'aria-label="Switch between plain-language and technical explanations">Plain language</button>') + toggle
    return f"""<!doctype html>
<!-- Generated {gen_txt} ({gen_iso}) -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>{robots}
<meta name="description" content="{esc(plain_sub, quote=True)}">
<meta name="generated" content="{gen_iso}">{extra_head}
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<style>{CSS}</style></head>
<body><div class="wrap">
<header><div class="topbar"><div class="eyebrow">{eyebrow}</div><div class="btns">{toggle}</div></div>
<h1{' class="long"' if len(title) > 90 else ''}>{title}</h1>{f'<p class="subtitle">{subtitle}</p>' if subtitle else ''}{byline(author, affiliation, byline_when or gen_txt)}{f'<p class="lede">{lede}</p>' if lede else ''}{head_note}{tiles}</header>
{body}
<footer class="site">{f'<h3>Sources</h3><ul>{src}</ul>' if src else ''}<div class="faint">{footer}</div>{brand_strip()}</footer>
</div><div id="tip" role="tooltip"></div><script>{TIP_JS}</script></body></html>
"""


def section(title: str, body: str, *, lede: str = "", id: str | None = None) -> str:
    sid = f' id="{esc(id)}"' if id else ""
    return f'<section class="sec"{sid}><h2>{title}</h2>{f"<p class=sec-lede>{lede}</p>" if lede else ""}{body}</section>'


def note(title: str, html_body: str) -> str:
    return f'<div class="note"><h3>{title}</h3>{html_body}</div>'


def card(body: str, *, title: str = "", caption: str = "", source: str = "", tip: str = "",
         checks: Sequence[str] | None = None) -> str:
    """White panel around one chart: optional title (tip= explains the chart as a whole on hover), a caption
    (may be vk.dual(plain, technical)), a source line, and checks=: the rigor pass for this panel
    (references/rigor.md), one line per point checked, shown under the panel as "How this panel was checked"."""
    t = f"<h3{_ta(tip)}>{title}</h3>" if title else ""
    c = f'<p class="cap">{caption}</p>' if caption else ""
    s = f'<p class="src">{source}</p>' if source else ""
    ck = ""
    if checks:
        ck = ('<details class="checks"><summary>How this panel was checked</summary><ul>' +
              "".join(f"<li>{x}</li>" for x in checks) + "</ul></details>")
    return f'<div class="card">{t}{c}{body}{s}{ck}</div>'


def stat_tiles(tiles: Sequence[dict]) -> str:
    """tiles: [{value, label, sub?, tip?}]  — value is pre-formatted text."""
    out = []
    for t in tiles:
        tp = f' data-tip="{t["tip"]}"' if t.get("tip") else ""
        sub = f'<div class="s">{t["sub"]}</div>' if t.get("sub") else ""
        out.append(f'<div class="tile"{tp}><div class="v">{t["value"]}</div><div class="l">{t["label"]}</div>{sub}</div>')
    return f'<div class="tiles">{"".join(out)}</div>'


def legend(items: Sequence[dict]) -> str:
    """items: [{label, color, tip?}] or [{label, line: True, tip?}] for a dashed reference line."""
    ks = []
    for it in items:
        mark = '<span class="ln"></span>' if it.get("line") else f'<span class="sw" style="background:{it["color"]}"></span>'
        ks.append(f'<span class="k"{_ta(it.get("tip"))}>{mark}{it["label"]}</span>')
    return f'<div class="legend">{"".join(ks)}</div>'


# ============================================================================ charts
def hbar(rows: Sequence[dict], series: Sequence[dict], *, unit: str = "%", decimals: int = 0,
         domain: tuple | None = None, ref: float | None = None, ref_label: str = "",
         axis_title: str = "", show_legend: bool = True, axis_tip: str = "", ref_tip: str = "") -> str:
    """Horizontal bars, one group per row, one bar per series, value printed at the bar end.
    Tips: each bar's "tip"; series "tip" (on its legend entry); axis_tip (axis title); ref_tip (dashed line).

    rows:   [{"label": "California", "sub": "602,678 structures",
              "values": {"direct": {"v": 41.2, "lo": 39.8, "hi": 42.6, "tip": "..."}, ...}}]
            v/lo/hi are in display units (e.g. percent 0-100 when unit="%"); lo/hi draw a CI whisker;
            "color" overrides the series colour for one bar (e.g. faded for too few cases).
    series: [{"key": "direct", "name": "Direct exposure", "color": "var(--s4)"}]
    ref:    a dashed reference line (e.g. the overall rate), labelled in the legend with ref_label.
    """
    vals = [d["v"] for r in rows for d in r["values"].values() if d and d.get("v") is not None]
    his = [d["hi"] if d.get("hi") is not None else d["v"] for r in rows for d in r["values"].values()
           if d and d.get("v") is not None]                     # a bar may have no interval (hi None)
    lo, hi = domain or (0, max(his + ([ref] if ref is not None else [])) * 1.02 if vals else 1)
    ticks = _nice_ticks(lo, hi)
    hi = max(hi, ticks[-1])
    pos = lambda v: (v - lo) / (hi - lo) * 100
    grid = "".join(f'<i class="grid" style="left:{pos(t):.2f}%"></i>' for t in ticks)
    refl = f'<i class="ref" style="left:{pos(ref):.2f}%"></i>' if ref is not None else ""
    cells = []
    for r in rows:
        sub = f"<small>{r['sub']}</small>" if r.get("sub") else ""
        bars = []
        for s in series:
            d = r["values"].get(s["key"])
            if not d or d.get("v") is None:
                bars.append('<div class="bar" style="width:0;background:transparent"></div>')
                continue
            label = f"{d['v']:,.{decimals}f}" + ("%" if unit == "%" else (f" {unit}" if unit else ""))
            t = d.get("tip") or tip(f"{esc(r['label'])} · {esc(s['name'])}", label)
            # Whisker and value are placed on the row's own axis (not as a share of the bar), so a bar at or
            # near zero still gets a correct whisker (was: divided by the bar width -> absurd widths).
            clamp = lambda x: min(max(x, 0.0), 100.0)
            ci = ""
            if d.get("lo") is not None and d.get("hi") is not None:
                a, b = clamp(pos(d["lo"])), clamp(pos(d["hi"]))
                ci = f'<i class="ci" style="left:{a:.2f}%;width:{max(b - a, 0):.2f}%"></i>'
            end = clamp(max(pos(d["v"]), pos(d["hi"]) if d.get("hi") is not None else pos(d["v"])))
            bars.append(f'<div class="brow"><div class="bar" style="width:{clamp(pos(d["v"])):.2f}%;background:{d.get("color") or s["color"]}" data-tip="{t}"></div>'
                        f'{ci}<span class="val" style="left:calc({end:.2f}% + 6px)">{label}</span></div>')
        cells.append(f'<div class="lab">{r["label"]}{sub}</div><div class="area">{grid}{refl}{"".join(bars)}</div>')
    axis = "".join(f'<span style="left:{pos(t):.2f}%">{_tick_label(t, unit)}</span>' for t in ticks)
    leg = ""
    if show_legend and (len(series) > 1 or ref is not None or any(s.get("tip") for s in series)):
        leg = legend([{"label": s["name"], "color": s["color"], "tip": s.get("tip")} for s in series] +
                     ([{"label": ref_label, "line": True, "tip": ref_tip}] if ref is not None and ref_label else []))
    at = f'<div class="axis-t"><span{_ta(axis_tip)}>{axis_title}</span></div>' if axis_title else ""
    return (f'{leg}<div class="hb">{"".join(cells)}<div></div><div class="axis">{axis}</div></div>{at}')


def columns(labels: Sequence[str], series: Sequence[dict], *, tips: Sequence[str] | None = None,
            unit: str = "", label_every: int | None = None, value_labels: bool | None = None,
            height: int = 240, show_legend: bool = True, x_title: str = "", y_title: str = "",
            x_tip: str = "", y_tip: str = "") -> str:
    """Vertical columns (stacked when several series), e.g. one column per year.
    x_title / y_title name the axes (x_tip / y_tip explain them on hover); series "tip" goes on its legend entry.

    series: [{"name": "Burned", "color": "var(--s4)", "values": [..one per label..]}]
    tips:   one data-tip string per column (use vk.tip(...)).
    On a phone the value labels switch to short form (21.6k); with more than 8 columns they are left to
    the hover, and every other x label is hidden, so the chart fits the width without scrolling.
    """
    n = len(labels)
    totals = [sum((s["values"][i] or 0) for s in series) for i in range(n)]
    top = _nice_ticks(0, max(totals) * 1.05, cover=True)[-1] or 1
    label_every = label_every or (1 if n <= 12 else 2 if n <= 24 else 5)
    value_labels = (n <= 12) if value_labels is None else value_labels
    dense = " dense" if n > 8 else ""
    cols = []
    for i in range(n):
        segs = "".join(f'<div class="seg" style="height:{(s["values"][i] or 0) / top * 100:.2f}%;background:{s["color"]}"></div>'
                       for s in reversed(series))
        cv = (f'<span class="cv" style="bottom:calc({totals[i] / top * 100:.2f}% + 3px)"><span class="full">{totals[i]:,.0f}{unit}</span>'
              f'<span class="short">{_compact(totals[i])}{unit}</span></span>' if value_labels else "")
        tp = f' data-tip="{tips[i]}"' if tips else ""
        cols.append(f'<div class="c"{tp}>{segs}{cv}</div>')
    gl = "".join(f'<div class="gl" style="bottom:{t / top * 100:.2f}%"><span><span class="full">{t:,.0f}</span>'
                 f'<span class="short">{_compact(t)}</span></span></div>' for t in _nice_ticks(0, top)[1:])
    shown = [i for i in range(n) if i % label_every == 0]
    xl = "".join(f'<span{" class=alt" if i in shown and shown.index(i) % 2 else ""}>{labels[i] if i in shown else ""}</span>'
                 for i in range(n))
    leg = (legend([{"label": s["name"], "color": s["color"], "tip": s.get("tip")} for s in series])
           if show_legend and (len(series) > 1 or any(s.get("tip") for s in series)) else "")
    yt_ = f'<div class="ax-y"{_ta(y_tip)}>{y_title}</div>' if y_title else ""
    xt_ = f'<div class="ax-x"{_ta(x_tip)}>{x_title}</div>' if x_title else ""
    return (f'{leg}{yt_}<div class="cols{dense}" style="height:{height}px">{gl}{"".join(cols)}</div>'
            f'<div class="xl{dense}">{xl}</div>{xt_}')


def line_chart(x: Sequence[float], series: Sequence[dict], *, x_labels: Sequence[str] | None = None,
               y_domain: tuple | None = None, unit: str = "", ref: float | None = None, ref_label: str = "",
               tips: dict | None = None, width: int = 1000, height: int = 320, show_legend: bool = True,
               phone: str = "fit", x_title: str = "", y_title: str = "", x_tip: str = "", y_tip: str = "",
               ref_tip: str = "") -> str:
    """Lines with points. series: [{"name", "color", "values": [...], "key"?}]; values may contain None (gap).
    tips: {series_key_or_name: [tip per point]}.
    phone: "fit" (a second, narrow drawing with short axis labels and fewer x labels is shown on phones, so
    the chart fits the screen) or "scroll" (one drawing that scrolls sideways on a phone; for long series
    where every x label matters). Decide per chart."""
    ys = [v for s in series for v in s["values"] if v is not None] + ([ref] if ref is not None else [])
    lo, hi = y_domain or (min(0, min(ys)), max(ys) * 1.05)
    yt = _nice_ticks(lo, hi)
    hi = max(hi, yt[-1])
    labs = x_labels or [str(v) for v in x]
    x0, x1 = min(x), max(x)

    def draw(W, H, compact, every, r, cls):
        padl = 16 + (9 if compact else 11) * max(len(_tick_label(t, unit, compact)) for t in yt)
        padr, padt, padb = (14 if compact else 18), 14, 34
        X = lambda v: padl + (v - x0) / ((x1 - x0) or 1) * (W - padl - padr)
        Y = lambda v: padt + (1 - (v - lo) / ((hi - lo) or 1)) * (H - padt - padb)
        g = [f'<line class="gridl" x1="{padl}" x2="{W - padr}" y1="{Y(t):.1f}" y2="{Y(t):.1f}"/>'
             f'<text x="{padl - 8}" y="{Y(t) + 4:.1f}" text-anchor="end">{_tick_label(t, unit, compact)}</text>' for t in yt]
        cw = 6.6 if compact else 7.4                     # rough label character width: keep end labels inside the chart
        anchor = lambda xv, lab: ("end" if xv + cw * len(lab) / 2 > W - 2 else
                                  "start" if xv - cw * len(lab) / 2 < 2 else "middle")
        g += [f'<text x="{X(v):.1f}" y="{H - 8}" text-anchor="{anchor(X(v), labs[i])}">{esc(labs[i])}</text>'
              for i, v in enumerate(x) if i % every == 0]
        g.append(f'<line class="axisl" x1="{padl}" x2="{W - padr}" y1="{Y(lo):.1f}" y2="{Y(lo):.1f}"/>')
        if ref is not None:
            g.append(f'<line x1="{padl}" x2="{W - padr}" y1="{Y(ref):.1f}" y2="{Y(ref):.1f}" stroke="var(--ink-2)" stroke-width="1.5" stroke-dasharray="5 4"/>')
        for s in series:
            segs, cur = [], []
            for xv, yv in zip(x, s["values"]):
                if yv is None:
                    if cur:
                        segs.append(cur)
                    cur = []
                else:
                    cur.append(f"{X(xv):.1f},{Y(yv):.1f}")
            if cur:
                segs.append(cur)
            g += [f'<polyline points="{" ".join(c)}" fill="none" stroke="{s["color"]}" stroke-width="2.4" stroke-linejoin="round"/>' for c in segs]
            tl = (tips or {}).get(s.get("key", s["name"]))
            for i, (xv, yv) in enumerate(zip(x, s["values"])):
                if yv is None:
                    continue
                t = tl[i] if tl else tip(f"{esc(s['name'])} · {esc(labs[i])}", _tick_label(yv, unit))
                g.append(f'<circle class="pt" cx="{X(xv):.1f}" cy="{Y(yv):.1f}" r="{r}" fill="{s["color"]}" stroke="var(--surface)" stroke-width="1.5" data-tip="{t}"/>')
        return f'<svg class="{cls}" viewBox="0 0 {W} {H}" role="img">{"".join(g)}</svg>'

    n = len(x)
    if phone == "scroll":
        wide, narrow = draw(width, height, False, 1 if n <= 12 else 2 if n <= 24 else 5, 4, "keep"), ""
    else:
        wide = draw(width, height, False, 1 if n <= 12 else 2 if n <= 24 else 5, 4, "wide")
        narrow = draw(360, 250, True, 1 if n <= 5 else 2 if n <= 10 else 3 if n <= 15 else max(1, n // 5), 3.5, "narrow")
    leg = ""
    if show_legend and (len(series) > 1 or ref is not None or any(s.get("tip") for s in series)):
        leg = legend([{"label": s["name"], "color": s["color"], "tip": s.get("tip")} for s in series] +
                     ([{"label": ref_label, "line": True, "tip": ref_tip}] if ref is not None and ref_label else []))
    yt_ = f'<div class="ax-y"{_ta(y_tip)}>{y_title}</div>' if y_title else ""
    xt_ = f'<div class="ax-x"{_ta(x_tip)}>{x_title}</div>' if x_title else ""
    return f'{leg}{yt_}<div class="svgwrap">{wide}{narrow}</div>{xt_}'


def heatmap(row_labels: Sequence[str], col_labels: Sequence[str], cells: Sequence[Sequence[dict | None]], *,
            ramp="heat", domain: tuple = (0, 1), caption: str = "", row_groups: dict | None = None,
            extra_cols: Sequence[str] = (), extra: Sequence[Sequence[str]] | None = None,
            phone: str = "scroll", col_tips: Sequence | None = None, row_tips: Sequence | None = None,
            extra_tips: Sequence | None = None) -> str:
    """Coloured table. cells[r][c] = {"v": number for colour, "text": big label, "sub": small label,
    "tip": data-tip, "empty": bool} or None. Use "empty" (greyed, '–') when n is too small to trust.
    row_groups: {row_index: "Group heading"} inserts a heading row before that row.
    extra_cols / extra: trailing plain columns (e.g. n, average) per row.
    phone: "scroll" (cells tighten; a wide table scrolls with row labels and header frozen; best when the
    columns are a sequence read across, like years) or "cards" (one card per row with wrapping cells; best
    when each row is read on its own). Decide per chart (charts.md, "Phone layout")."""
    ct, rt, et = list(col_tips or []), list(row_tips or []), list(extra_tips or [])
    head = ("".join(f"<th{_ta(ct[j] if j < len(ct) else None)}>{c}</th>" for j, c in enumerate(col_labels)) +
            "".join(f"<th{_ta(et[j] if j < len(et) else None)}>{c}</th>" for j, c in enumerate(extra_cols)))
    body, mob = [], []
    for r, lab in enumerate(row_labels):
        if row_groups and r in row_groups:
            body.append(f'<tr class="grp"><th colspan="{1 + len(col_labels) + len(extra_cols)}">{row_groups[r]}</th></tr>')
            mob.append(f'<div class="hm-g">{row_groups[r]}</div>')
        tds, mcs = [], []
        for j, c in enumerate(cells[r]):
            cl = col_labels[j]
            if not c or c.get("empty"):
                tp = f' data-tip="{c["tip"]}"' if c and c.get("tip") else ""
                tds.append(f'<td class="c empty"{tp}>–</td>')
                mcs.append(f'<div class="hm-c empty"{tp}><small>{cl}</small><b>–</b></div>')
                continue
            col = ramp_color(c["v"], domain[0], domain[1], ramp)
            cls = "dk" if _is_light(col) else "lt"
            sub = f'<i>{c["sub"]}</i>' if c.get("sub") else ""
            tp = f' data-tip="{c["tip"]}"' if c.get("tip") else ""
            if c.get("flag"):
                cls += " flag"
                tp = f' data-tip="{(c.get("tip") or "")}{"&#10;" if c.get("tip") else ""}Flagged: {esc(c["flag"], quote=True)}"'
            tds.append(f'<td class="c {cls}" style="background:{col}"{tp}><b>{c["text"]}</b>{sub}</td>')
            mcs.append(f'<div class="hm-c {cls}" style="background:{col}"{tp}><small>{cl}</small><b>{c["text"]}</b>{sub}</div>')
        ex = "".join(f'<td class="x">{v}</td>' for v in (extra[r] if extra else []))
        body.append(f'<tr><th class="rl"{_ta(rt[r] if r < len(rt) else None)}>{lab}</th>{"".join(tds)}{ex}</tr>')
        exm = " · ".join(f"{n} {v}" for n, v in zip(extra_cols, extra[r])) if extra else ""
        mob.append(f'<div class="hm-r"><div class="hm-rh"><b>{lab}</b><span>{exm}</span></div>'
                   f'<div class="hm-cells">{"".join(mcs)}</div></div>')
    cap = f'<p class="cap">{caption}</p>' if caption else ""
    desk = (f'<div class="scroll{" hm-desk" if phone == "cards" else ""}"><table class="hm"><thead><tr><th></th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')
    return cap + desk + (f'<div class="hm-m">{"".join(mob)}</div>' if phone == "cards" else "")


def ramp_key(lo_label: str, hi_label: str, ramp="heat", steps: int = 9, empty_label: str = "", tip: str = "") -> str:
    cs = RAMPS[ramp] if isinstance(ramp, str) else ramp
    sw = "".join(f'<i style="background:{ramp_color(i / (steps - 1), 0, 1, cs)}"></i>' for i in range(steps))
    e = (f'<span class="k"><span class="sw" style="background:var(--empty)"></span>{empty_label}</span>' if empty_label else "")
    return (f'<div class="legend"><span class="k"{_ta(tip)}><span class="nw">{lo_label}</span><span class="ramp">{sw}</span>'
            f'<span class="nw">{hi_label}</span></span>{e}</div>')


def map_panel(spec, base=None, *, height: int = 520, phone_height: int = 440, label: str = "Interactive map") -> str:
    """An interactive map as one panel of a chart page, next to the bars, lines and tables.

    spec: path to a map spec JSON (the same format as a standalone map: references/map-spec.md; file paths
          inside it are relative to the spec), or a spec dict with base= the folder its paths are relative to.
          title / subtitle / sources are not shown in the panel: put the title and caption on the card around
          it (vk.card) and the map's data sources in the page's sources. Optional "panel_title" names the key.
    The map is built by build_map in panel mode and inlined (iframe srcdoc), so the page stays one file and
    a PIN gate covers the map too. In the panel: two fingers (phone) or Ctrl + scroll (desktop) move the map,
    so the page scrolls past it normally; a fullscreen button; the key folds away on a phone; the page's
    light / dark switch carries into the map. Keep embedded maps light (a few MB): for a heavy map, publish a
    standalone map page and link to it from a card instead.
    """
    import json
    import sys as _sys
    from pathlib import Path as _P
    here = str(_P(__file__).resolve().parent)
    if here not in _sys.path:
        _sys.path.insert(0, here)
    import build_map
    if isinstance(spec, (str, _P)):
        sp = _P(spec).resolve()
        spec, base = json.loads(sp.read_text()), sp.parent
    doc, _layers, warns = build_map.build_page(spec, _P(base or "."), embed=True)
    for w in warns:
        print("map_panel: WARNING:", w)
    return (f'<iframe class="mapframe" title="{esc(label, quote=True)}" allow="fullscreen" allowfullscreen '
            f'style="--h:{height}px;--ph:{phone_height}px" srcdoc="{esc(doc, quote=True)}"></iframe>')


def _num(x):
    """A cell's number: its "v", or parsed from its text ('55%', '16,493', '-0.3 pts'); None if not a number."""
    import re as _re
    if isinstance(x, dict):
        if x.get("v") is not None:
            return x["v"]
        x = x.get("text", "")
    m = _re.search(r"[-+−]?\d[\d,]*\.?\d*", _re.sub(r"<[^>]+>", "", str(x)))
    return float(m.group(0).replace(",", "").replace("−", "-")) if m else None


def shade_color(v, *, scale="good_bad", better="low", domain=None, mid=None):
    """Colour for a value on a table shading scale. scale: "good_bad" (green → yellow → orange → red),
    "blues"/"heat"/"viridis" (magnitude, no judgement), "diverging" (around mid, e.g. 0), or a list of hex.
    better: "low" or "high" says which end is good (for good_bad and diverging); None leaves the ramp as is."""
    cs = list(RAMPS[scale] if isinstance(scale, str) else scale)
    if better == "high" and (scale in ("good_bad", "diverging") or not isinstance(scale, str)):
        cs = cs[::-1]
    lo, hi = domain
    return ramp_color(v, lo, hi, cs)


def table(columns: Sequence[str], rows: Sequence[Sequence], *, numeric: Iterable[int] = (), caption: str = "",
          phone: str = "scroll", shade: dict | None = None, strength: float = 0.30,
          col_tips: Sequence | None = None) -> str:
    """Plain table; `numeric` = column indexes to right-align.

    Cells are HTML strings, or dicts {"text": html, "v": number, "tip": "...", "flag": "why"}.
    shade: {column_index: {"scale": "good_bad" | "blues" | "heat" | "diverging" | [hex...],
                           "better": "low" | "high" | None, "domain": (lo, hi) or None, "mid": number or None}}
        tints each value cell of those columns (subtly: `strength` of the colour) so the eye finds high and
        low values at a glance; the number is always printed. domain defaults to the column's min..max
        (symmetric around `mid` when given). Pick the scale by meaning (charts.md, "Shading tables").
    flag: on rare cells that merit it (a value that fails a target, a clear outlier, the headline) a red box
        is drawn and the reason is added to the cell's hover. Explain the red box in the caption or key.
    phone: "scroll" (scrolls inside its box with the header row and first column frozen; best for many
    rows compared down a column) or "cards" (each row becomes a card: first cell as heading, then
    label/value lines; best when each row is a record read on its own). Decide per table."""
    import re as _re
    num, shade = set(numeric), (shade or {})
    plain = [esc(_re.sub(r"<[^>]+>", "", c), quote=True) for c in columns]
    doms = {}
    for j, spec in shade.items():
        vals = [v for v in (_num(r[j]) for r in rows) if v is not None]
        if not vals:
            continue
        lo, hi = spec.get("domain") or (min(vals), max(vals))
        if spec.get("mid") is not None:
            m, half = spec["mid"], max(abs(lo - spec["mid"]), abs(hi - spec["mid"])) or 1
            lo, hi = m - half, m + half
        doms[j] = (lo, hi)
    ct = list(col_tips or [])
    th = "".join(f'<th{" class=n" if i in num else ""}{_ta(ct[i] if i < len(ct) else None)}>{c}</th>' for i, c in enumerate(columns))
    trs = []
    for r in rows:
        tds = []
        for i, c in enumerate(r):
            text = c.get("text", "") if isinstance(c, dict) else c
            cls, style, tipl = (["n"] if i in num else []), "", []
            if isinstance(c, dict) and c.get("tip"):
                tipl.append(c["tip"])
            v = _num(c) if i in doms else None
            if v is not None:
                sp = shade[i]
                col = shade_color(v, scale=sp.get("scale", "good_bad"), better=sp.get("better", "low"), domain=doms[i])
                style = f' style="background:color-mix(in srgb, {col} {strength * 100:.0f}%, transparent)"'
                cls.append("sh")
            if isinstance(c, dict) and c.get("flag"):
                cls.append("flag")
                tipl.append("Flagged: " + c["flag"])
            head_txt = _re.sub(r"<[^>]+>", "", columns[i]) + " · " + _re.sub(r"<[^>]+>", "", str(text))
            tp = f' data-tip="{tip(head_txt, *tipl)}"' if tipl else ""
            ca = f' class="{" ".join(cls)}"' if cls else ""
            tds.append(f'<td{ca}{style}{tp} data-label="{plain[i]}">{text}</td>')
        trs.append("<tr>" + "".join(tds) + "</tr>")
    cap = f'<p class="cap">{caption}</p>' if caption else ""
    cards = phone == "cards"
    return (f'{cap}<div class="scroll{" tb-cards-box" if cards else ""}"><table class="tb{" tb-cards" if cards else ""}">'
            f'<thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>')


def shade_key(lo_label: str, hi_label: str, *, scale="good_bad", better="low", flag: str = "",
              strength: float = 0.30, steps: int = 7, tip: str = "", flag_tip: str = "") -> str:
    """Key for a shaded table: the subtle colour run from lo_label to hi_label, plus the red box if used."""
    sw = "".join(f'<i style="background:color-mix(in srgb, {shade_color(k / (steps - 1), scale=scale, better=better, domain=(0, 1))} '
                 f'{strength * 100:.0f}%, transparent)"></i>' for k in range(steps))
    fl = f'<span class="k"{_ta(flag_tip)}><span class="flagsw"></span>{flag}</span>' if flag else ""
    return (f'<div class="legend"><span class="k"{_ta(tip)}><span class="nw">{lo_label}</span><span class="ramp">{sw}</span>'
            f'<span class="nw">{hi_label}</span></span>{fl}</div>')


# ============================================================================ living pages (iterative work)
# A living page is one analysis built up over many requests: new panels go on top, older ones move down,
# obsolete or wrong ones are removed with a reason, and every panel shows when it was added. The page is its
# own store: its panels and settings are kept inside the HTML, so any later session can pull the published
# page (publish.py --pull) and keep adding to it.

_PANEL_RX = None


def panel(body: str, *, title: str, id: str | None = None, caption: str = "", source: str = "", tip: str = "",
          checks: Sequence[str] | None = None) -> dict:
    """One panel for living_page(): a card (title, caption, checks, source as in card()) plus an id.
    Give a short explicit id ("burned-per-year"): it is how the panel is updated (reuse the id) or removed
    later. Without one, the id is a slug of the title (filler words dropped)."""
    pid = id or slug(title, 60) or "panel"
    return {"id": pid, "title": title,
            "html": card(body, title=title, caption=caption, source=source, tip=tip, checks=checks)}


def _iso_to_txt(iso: str) -> str:
    from datetime import datetime
    from zoneinfo import ZoneInfo
    try:
        return datetime.fromisoformat(iso).astimezone(ZoneInfo(load_identity().get("timezone", "UTC"))).strftime("%Y-%m-%d %H:%M %Z")
    except Exception:
        return iso


def _render_panel(pid: str, title: str, inner: str, created: str, updated: str | None) -> str:
    stamp = f"Added {_iso_to_txt(created)}" + (f" · updated {_iso_to_txt(updated)}" if updated else "")
    inner = inner.replace('<div class="card">', f'<div class="card"><span class="pstamp">{stamp}</span>', 1)
    upd = f' data-updated="{updated}"' if updated else ""
    return (f'<section class="panel" data-panel="{esc(pid, quote=True)}" data-title="{esc(title, quote=True)}" '
            f'data-created="{created}"{upd}>{inner}</section><!--/panel:{pid}-->')


def read_living_page(src) -> tuple[dict, list[dict]]:
    """(page settings, panels newest first) from a living page's HTML (path or text); ({}, []) if none."""
    import json
    import re as _re
    from pathlib import Path as _P
    if src is None:
        return {}, []
    txt = _P(src).read_text() if isinstance(src, _P) or (isinstance(src, str) and len(src) < 4096 and _P(src).exists()) else str(src)
    if "<!-- pin-gated" in txt[:200]:
        raise ValueError("this page is PIN-gated: pull it with publish.py --pull (SLP_PIN set) to get the plaintext")
    m = _re.search(r'<script type="application/json" id="vk-living">(.*?)</script>', txt, _re.S)
    meta = json.loads(m.group(1).replace("<\\/", "</")) if m else {}
    panels = []
    for pm in _re.finditer(r'<section class="panel" data-panel="([^"]+)" data-title="([^"]*)" data-created="([^"]+)"'
                           r'(?: data-updated="([^"]+)")?>(.*?)</section><!--/panel:\1-->', txt, _re.S):
        pid, title, created, updated, inner = pm.groups()
        inner = _re.sub(r'<span class="pstamp">.*?</span>', "", inner, count=1)
        panels.append({"id": pid, "title": html.unescape(title), "html": inner, "created": created, "updated": updated})
    return meta, panels


def living_page(existing=None, *, title: str | None = None, add: Sequence[dict] = (), remove: dict | None = None,
                **page_kwargs) -> str:
    """Build or extend a living page and return its HTML.

    existing: the current page (path or HTML text, e.g. from publish.py --pull), or None to start one.
    title:    needed when starting; kept afterwards (it carries the start date). Other page settings
              (subtitle, eyebrow, lede, how_to_read, tiles, sources, footer, author) are kept from the page
              unless passed again here.
    add:      new panels (vk.panel(...)), put on top in the order given. A panel whose id is already on the
              page replaces it in place and is stamped "updated".
    remove:   {panel_id: "why"}: take panels off the page (wrong, obsolete, no longer needed); the reason
              goes into the page history at the foot.
    """
    import json
    meta, panels = read_living_page(existing)
    now = generated_iso()
    if not meta:
        if not title:
            raise ValueError("starting a living page needs title= (short, ending in the date)")
        meta = {"title": title, "created": now, "history": []}
    keep = {k: v for k, v in page_kwargs.items() if k in
            ("subtitle", "eyebrow", "lede", "how_to_read", "tiles", "sources", "footer", "author", "affiliation", "noindex")}
    meta.setdefault("settings", {}).update({k: (list(v) if k == "sources" else v) for k, v in keep.items()})
    by_id = {p["id"]: p for p in panels}
    for pid, why in (remove or {}).items():
        if pid not in by_id:
            raise ValueError(f"no panel {pid!r} on this page (have: {list(by_id)})")
        meta["history"].append({"when": now, "action": "removed", "id": pid, "title": by_id[pid]["title"], "why": why})
        panels = [p for p in panels if p["id"] != pid]
        del by_id[pid]
    new_top = []
    for np_ in add:
        if np_["id"] in by_id:                                          # same chart, new version: update in place
            old = by_id[np_["id"]]
            old.update(html=np_["html"], title=np_["title"], updated=now)
            meta["history"].append({"when": now, "action": "updated", "id": np_["id"], "title": np_["title"]})
        else:
            new_top.append({"id": np_["id"], "title": np_["title"], "html": np_["html"], "created": now, "updated": None})
            meta["history"].append({"when": now, "action": "added", "id": np_["id"], "title": np_["title"]})
    panels = new_top + panels
    hist = "".join(f"<li>{_iso_to_txt(h['when'])}: {h['action']} <b>{esc(h['title'])}</b>"
                   f"{(': ' + esc(h['why'])) if h.get('why') else ''}</li>" for h in reversed(meta["history"]))
    body = ("".join(_render_panel(p["id"], p["title"], p["html"], p["created"], p.get("updated")) for p in panels) +
            f'<details class="history"><summary>Page history</summary><ul>{hist}</ul></details>')
    st = meta["settings"]
    store = json.dumps(meta, ensure_ascii=False).replace("</", "<\\/")
    when = f"started {_iso_to_txt(meta['created'])} · updated {_iso_to_txt(now)}"
    return page(meta["title"], body, byline_when=when,
                extra_head=f'<script type="application/json" id="vk-living">{store}</script>',
                **{k: v for k, v in st.items() if k != "noindex"}, noindex=st.get("noindex", False))
