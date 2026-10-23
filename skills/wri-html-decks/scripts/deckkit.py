#!/usr/bin/env python3
"""Slide-deck building blocks: one self-contained HTML presentation in the house style, published by link.

WHY THIS EXISTS
    The team's best-received deck (the wildfire structure-loss deck, Sept–Oct 2026) worked because of a few
    things the owner asked for again and again: a progress strip at the top of every slide, grouped into coloured
    sections, showing where you are and how far there is to go; one idea per slide; a picture or chart instead
    of a paragraph; one colour per concept; hover tips on everything that add information, with a highlight
    and no cursor change; an (i) note at the bottom right of every slide; maps as still pictures with tabs and
    toggles plus a link to the interactive map. That deck was hand-built from one-off scripts. This file makes
    the same deck from a few calls, so every deck looks and behaves the same way, and the checks
    (shoot_deck.py) catch the mistakes that reached that deck once: text over lines, overflowing boxes, slides
    too dense to read, numbers nobody can trace.

    It reuses the sibling page skill (wri-html-pages, or a project copy such as parafire-html-pages) for who
    made it (identity.json: author, logos, time zone, publishing site), the title slug, the tip format and
    the colour scales, and publishes with that skill's publish.py. One identity, one publishing path.

USE
    import sys; sys.path.insert(0, "<this skill>/scripts"); import deckkit as dk
    d = dk.Deck("Palmer penguins: size and place · 2026-10-23", subtitle="344 adult penguins ...",
                sources=["Gorman et al. 2014 ..."], script="examples/penguin_deck_demo.py")
    d.section("The birds")                       # every slide after this belongs to the section
    d.cover()
    d.slide("counts", "Three species, measured at their nests", dk.numbers([...]),
            info=("How to read it", "Each number is ..."), source="Gorman et al. 2014")
    d.section("Size")
    d.slide("mass", "Males are heavier in every species", dk.hbar(rows, series))
    path = d.write(OUT_DIR, previous=None, change="First version")   # OUT_DIR/<slug of title>.html
    # two languages in one page (ES | EN switch): dk.write_page(OUT_DIR, deck_es, deck_en, ...)

    Sizes are pixels on a fixed 1920 x 1080 slide; the content box is 1664 x 808 (left 128, top 116).
    The guide with every block and chart is references/slides.md.
"""
from __future__ import annotations

import base64
import html
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Sequence

esc = html.escape
_SKILL = Path(__file__).resolve().parents[1]


# ============================================================================ the sibling page skill (identity, tips, publishing)
def pages_dir() -> Path:
    """The page skill this deck skill builds on: $DECK_PAGES_SKILL, else the sibling folder with the same prefix
    (wri-html-decks -> wri-html-pages, parafire-html-decks -> parafire-html-pages), else any sibling *-html-pages,
    else ~/.claude/skills/wri-html-pages."""
    env = os.environ.get("DECK_PAGES_SKILL")
    cands = [Path(env).expanduser()] if env else []
    cands.append(_SKILL.parent / _SKILL.name.replace("-html-decks", "-html-pages"))
    cands += sorted(_SKILL.parent.glob("*-html-pages"))
    cands.append(Path.home() / ".claude" / "skills" / "wri-html-pages")
    for c in cands:
        if (c / "scripts" / "vizkit.py").is_file():
            return c
    sys.exit("deckkit: the page skill (wri-html-pages) was not found next to this skill; install it or set DECK_PAGES_SKILL")


PAGES = pages_dir()
if str(PAGES / "scripts") not in sys.path:
    sys.path.insert(0, str(PAGES / "scripts"))
import vizkit as vk  # noqa: E402  (identity, slug, today, tip format, shade colours)

tip, dual, today, built_at, slug, fint, fpct, fnum = vk.tip, vk.dual, vk.today, vk.built_at, vk.slug, vk.fint, vk.fpct, vk.fnum
TECH_MARK = vk.TECH_MARK


# ============================================================================ look (one palette per deck; change it per project)
# The structure-loss deck's palette: warm paper, near-black ink, serif titles, a sans body. A deck is designed for a
# screen or projector, so it has one designed palette (no light / dark switch); dark slides are used as statements.
THEME = {
    "bg": "#F4F2EC",        # slide background
    "alt": "#FBFAF6",       # cards, keys, tables
    "card": "#FFFFFF",
    "ink": "#172026",
    "muted": "#4A5560",
    "faint": "#6A737C",     # footers, axis ticks
    "line": "#D9D6CC",
    "accent": "#C4502B",
    "dark": "#172026",      # dark statement slides
    "serif": "'Source Serif 4', Georgia, serif",
    "sans": "'IBM Plex Sans', Arial, sans-serif",
    "fonts": "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&"
             "family=Source+Serif+4:wght@400;600;700&display=swap",
}
# Section colours, in order (the structure-loss deck's six, then two more). Strong enough to read as text on paper.
SECTION_COLORS = ["#C4502B", "#4A7A3A", "#2E6A8A", "#8A6D3B", "#1F6F6B", "#7B5EA7", "#9C4F7B", "#5A6B7B"]
# Categorical series for charts (Okabe–Ito, colour-blind safe). Pick ONE colour per concept and keep it on every slide.
SERIES = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7", "#8A949E"]
W, H = 1920, 1080
BOX_L, BOX_T, BOX_W, BOX_H = 128, 116, 1664, 808      # content box (title + body) inside the margins

UI = {
    "en": {"prev": "Previous slide", "next": "Next slide", "contents": "Contents", "pdf": "PDF",
           "full": "Full screen", "hint": "arrow keys to move · O contents · F full screen", "about": "About this slide",
           "plain": "Plain", "tech": "Technical", "changes": "Changes to this deck", "started": "started",
           "updated": "updated", "by": "By", "sources_title": "Sources and how this deck was made",
           "made": "Made by", "script": "Built by", "lang": "Language", "slide": "Slide"},
    "es": {"prev": "Diapositiva anterior", "next": "Diapositiva siguiente", "contents": "Contenido",
           "pdf": "PDF", "full": "Pantalla completa", "hint": "flechas para avanzar · O contenido · F pantalla completa",
           "about": "Sobre esta diapositiva", "plain": "Sencillo", "tech": "Técnico",
           "changes": "Cambios en esta presentación", "started": "iniciada", "updated": "actualizada", "by": "Por",
           "sources_title": "Fuentes y cómo se hizo esta presentación", "made": "Hecho por", "script": "Generado por",
           "lang": "Idioma", "slide": "Diapositiva"},
}


def _hex(c: str):
    c = c.strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return [int(c[i:i + 2], 16) for i in (0, 2, 4)]


def mix(c: str, bg: str, t: float) -> str:
    """Colour c blended into bg (t = 1 is c, t = 0 is bg). Used for faded section colours and tints."""
    a, b = _hex(c), _hex(bg)
    return "#" + "".join(f"{round(x * t + y * (1 - t)):02X}" for x, y in zip(a, b))


def is_dark(c: str) -> bool:
    r, g, b = _hex(c)
    return (0.299 * r + 0.587 * g + 0.114 * b) < 128


def _ta(t) -> str:
    """data-tip attribute from a tip(...) string (already escaped) or plain text."""
    if not t:
        return ""
    return ' data-tip="' + str(t).replace('"', "&quot;") + '"'


def _style(**kw) -> str:
    """Inline style from keyword args (underscores become dashes; None values dropped; ints get px)."""
    out = []
    for k, v in kw.items():
        if v is None or v == "":
            continue
        if isinstance(v, (int, float)) and k not in ("flex", "opacity", "font_weight", "line_height", "z_index"):
            v = f"{v:g}px"
        out.append(f"{k.replace('_', '-')}:{v}")
    return ";".join(out)


def _fmt(fmt, v):
    if v is None:
        return "–"
    if fmt is None:
        return fint(v) if float(v).is_integer() and abs(v) >= 100 else (f"{v:g}" if abs(v) < 100 else fint(v))
    return fmt(v) if callable(fmt) else fmt.format(v)


def _ticks(lo: float, hi: float, n: int = 5):
    """Round axis ticks covering lo..hi."""
    if hi <= lo:
        hi = lo + 1
    raw = (hi - lo) / max(1, n)
    mag = 10 ** math.floor(math.log10(raw))
    step = next(s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= raw)
    t0 = math.floor(lo / step) * step
    out, t = [], t0
    while t <= hi + step * 0.5:
        out.append(round(t, 10))
        t += step
    return out


# ============================================================================ text and layout blocks
def text(body: str, *, size: int = 32, color: str | None = None, weight: int | None = None, width: int | None = None,
         align: str | None = None, serif: bool = False, tip=None) -> str:
    """A paragraph. Keep it to one or two sentences; a slide is not a page."""
    st = _style(font_size=size, color=color, font_weight=weight, max_width=width, text_align=align, line_height=1.38,
                font_family="var(--serif)" if serif else None)
    return f'<p style="{st}"{_ta(tip)}>{body}</p>'


def bullets(items: Sequence[str], *, size: int = 30, color: str | None = None, gap: int = 14, marker: str | None = None) -> str:
    """Short parallel lines (three or four). Prefer cards, numbers or a chart when the lines are not parallel."""
    li = "".join(f'<li style="margin:0 0 {gap}px 0">{t}</li>' for t in items)
    return (f'<ul class="bul" style="{_style(font_size=size, color=color, line_height=1.35)}"'
            + (f' data-marker="{esc(marker)}"' if marker else "") + f'>{li}</ul>')


def row(*items: str, gap: int = 32, align: str = "stretch", justify: str | None = None, widths: Sequence | None = None,
        flex: float | None = 1) -> str:
    """Side by side. widths: flex ratios ([2, 1]) or px ints per item; default equal."""
    kids = []
    for k, it in enumerate(items):
        w = widths[k] if widths and k < len(widths) else 1
        st = f"flex:0 0 {w}px;min-width:0" if isinstance(w, int) and w > 20 else f"flex:{w};min-width:0"
        kids.append(f'<div class="cell" style="{st};display:flex;flex-direction:column">{it}</div>')
    return (f'<div class="row" style="{_style(display="flex", gap=gap, align_items=align, justify_content=justify, flex=flex, min_height=0)}">'
            + "".join(kids) + "</div>")


def col(*items: str, gap: int = 24, align: str | None = None, justify: str | None = None, flex: float | None = None) -> str:
    """Stacked."""
    return (f'<div class="col" style="{_style(display="flex", flex_direction="column", gap=gap, align_items=align, justify_content=justify, flex=flex, min_height=0)}">'
            + "".join(items) + "</div>")


def spacer() -> str:
    """Pushes what follows to the bottom of the slide body."""
    return '<div style="flex:1"></div>'


def icon(name: str, color: str = "currentColor", size: int = 48, sw: float = 1.8, tip=None) -> str:
    """A small line icon (24-unit drawing, see ICONS). Use icons for repeated concepts, not decoration."""
    body = ICONS[name].replace("COL", color)
    k = size / 24
    return (f'<svg class="ic" width="{size}" height="{size}" viewBox="0 0 {size} {size}" aria-hidden="true"{_ta(tip)}>'
            f'<g transform="scale({k:g})" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round">{body}</g></svg>')


def badge(n, color: str, size: int = 44, ink: str = "#FFFFFF", tip=None) -> str:
    """Numbered circle badge (solid circle, bold white numeral): one per repeated concept, e.g. step 1, model 2
    (Carlo, 2026-09-28: circles, not flames, with the number clearly visible)."""
    fs = round(size * (0.58 if len(str(n)) == 1 else 0.46))
    return (f'<svg class="badge" width="{size}" height="{size}" viewBox="0 0 {size} {size}" role="img" aria-label="{esc(str(n))}"{_ta(tip)}>'
            f'<circle cx="{size / 2:g}" cy="{size / 2:g}" r="{size / 2 - 0.5:g}" fill="{color}"/>'
            f'<text x="50%" y="50%" dy=".35em" text-anchor="middle" font-size="{fs}" font-weight="700" fill="{ink}" '
            f'style="font-family:var(--sans)">{esc(str(n))}</text></svg>')


def pill(label: str, color: str, *, filled: bool = True, size: int = 26, tip=None) -> str:
    """A small label: filled for the emphasised one, outlined for the quieter one."""
    fs = round(size * 0.66)
    st = (f"background:{color};color:#FFFFFF;border:2px solid {color}" if filled
          else f"background:#FFFFFF;color:{color};border:2px solid {color}")
    return (f'<span class="pill" style="{st};font-size:{fs}px;height:{size}px;padding:0 {round(size * .38)}px"{_ta(tip)}>'
            f'{label}</span>')


def term(label: str, tip_text) -> str:
    """Inline words or a number with a hover tip (dotted underline). Every number that needs explaining gets one
    saying how it was calculated (Carlo, 2026-09-29); every named cohort says exactly which cut it is (2026-10-01)."""
    return f'<span class="term"{_ta(tip_text)}>{label}</span>'


def card(title: str = "", body: str = "", *, color: str | None = None, fill: str | None = None, ink: str | None = None,
         icon_name: str | None = None, badge_n=None, tip=None, size: int = 30, body_size: int = 26, pad: int = 32,
         edge: str = "box", flex: float | None = 1, extra: str = "") -> str:
    """A boxed block. color outlines it (edge="box"), marks its left edge (edge="side") or is ignored (edge="none")
    — outline a box in the colour of the thing it describes so readers link the two (Carlo, 2026-09-24).
    fill shades it (e.g. the concept colour, so the whole box reads as that concept); ink is its text colour."""
    c = color or "var(--line)"
    border = {"box": f"border:3px solid {c}", "side": f"border-left:8px solid {c}", "none": "border:none"}[edge]
    bg = fill or "var(--alt)"
    ink = ink or ("#F4F2EC" if fill and fill.startswith("#") and is_dark(fill) else None)
    head = ""
    if icon_name or badge_n is not None or title:
        lead = (badge(badge_n, color or "var(--accent)", 40) if badge_n is not None else "") + \
               (icon(icon_name, ink or color or "currentColor", 40) if icon_name else "")
        head = (f'<div style="display:flex;gap:14px;align-items:center">{lead}'
                f'<h3 style="font-size:{size}px;line-height:1.2;font-weight:600;margin:0;color:{ink or color or "inherit"}">{title}</h3></div>'
                if title else f'<div style="display:flex;gap:14px">{lead}</div>')
    bd = f'<div style="font-size:{body_size}px;line-height:1.4">{body}</div>' if body else ""
    return (f'<div class="card" style="{border};background:{bg};{"color:" + ink + ";" if ink else ""}border-radius:14px;'
            f'padding:{pad}px;display:flex;flex-direction:column;gap:14px;{"flex:" + str(flex) + ";" if flex else ""}min-width:0{extra}"{_ta(tip)}>'
            f'{head}{bd}</div>')


def number(value: str, label: str, *, color: str | None = None, tip=None, sub: str | None = None, size: int = 96) -> str:
    """A headline number with what it counts. Only figures that read on their own ("344 penguins measured"),
    never a ratio or arrow that needs the caption (house style, 2026-10-12)."""
    return (f'<div class="num"{_ta(tip)}><p style="font:700 {size}px/1 var(--serif);color:{color or "var(--ink)"};'
            f'font-variant-numeric:tabular-nums">{value}</p><p style="font-size:28px;line-height:1.3;margin-top:12px">{label}</p>'
            + (f'<p style="font-size:24px;color:var(--muted);margin-top:6px">{sub}</p>' if sub else "") + "</div>")


def numbers(items: Sequence[dict], *, gap: int = 48) -> str:
    """A row of headline numbers: items are number() keyword dicts {"value", "label", "color", "tip", "sub"}."""
    return row(*[number(**it) for it in items], gap=gap, align="flex-start", flex=None)


def note(body: str, *, title: str | None = None, color: str | None = None, icon_name: str | None = None) -> str:
    """A callout strip (what it misses, a caveat that matters, the takeaway)."""
    c = color or "var(--accent)"
    ic = icon(icon_name, c, 36) if icon_name else ""
    t = f"<b>{title}</b> " if title else ""
    return (f'<div class="note" style="border-left:8px solid {c};background:{mix(c, "#FFFFFF", .10) if c.startswith("#") else "var(--alt)"};'
            f'border-radius:10px;padding:22px 28px;display:flex;gap:18px;align-items:flex-start;font-size:26px;line-height:1.4">'
            f'{ic}<div>{t}{body}</div></div>')


def key(items: Sequence[dict], *, title: str = "Key", size: int = 24) -> str:
    """A big, friendly key (Carlo, 2026-09-28: "make the keys bigger and friendlier"), above or beside the chart.
    items: {"label", "color", "swatch": "box"|"line"|"dot"|"stripe"|"ring", "toggle": layer id (click hides /
    shows every element with data-layer=<id> on this slide), "tip"}."""
    out = []
    for it in items:
        c = it.get("color", "#888")
        sw = it.get("swatch", "box")
        if sw == "line":
            s = f'<span style="width:34px;height:0;border-top:5px solid {c};display:inline-block"></span>'
        elif sw == "dot":
            s = f'<span style="width:22px;height:22px;border-radius:50%;background:{c};border:2px solid #FFFFFF;box-shadow:0 0 0 1.5px #1B2430;display:inline-block"></span>'
        elif sw == "ring":
            s = (f'<span style="width:24px;height:24px;border-radius:50%;border:4px solid {c};display:inline-block;'
                 f'box-shadow:0 0 0 1.5px #1B2430,inset 0 0 0 1.5px #1B2430"></span>')
        elif sw == "stripe":
            s = (f'<span style="width:34px;height:22px;border-radius:5px;display:inline-block;background:repeating-linear-gradient('
                 f'45deg,{c} 0 5px,#FFFFFF 5px 9px)"></span>')
        else:
            s = f'<span style="width:30px;height:22px;border-radius:5px;background:{c};display:inline-block"></span>'
        tg = f' data-toggle="{esc(it["toggle"])}"' if it.get("toggle") else ""
        out.append(f'<span class="kitem"{tg}{_ta(it.get("tip"))}>{s}<span>{it["label"]}</span></span>')
    t = f'<b class="ktitle">{esc(title)}</b>' if title else ""
    return f'<div class="key" style="font-size:{size}px">{t}{"".join(out)}</div>'


def steps(items: Sequence[dict], *, color: str | None = None, arrows: bool = True, img_h: int = 170, size: int = 26) -> str:
    """A flow of numbered steps left to right (a pipeline, a method). items: {"title", "text", "img" (path or bytes),
    "icon", "tip", "color"}. Pictures over paragraphs: a real image per step where one exists."""
    out = []
    for k, it in enumerate(items, 1):
        c = it.get("color") or color or "var(--accent)"
        pic = ""
        if it.get("img") is not None:
            pic = f'<img src="{_data_uri(it["img"])}" alt="{esc(it.get("title", ""))}" style="width:100%;height:{img_h}px;object-fit:cover;border-radius:10px">'
        elif it.get("icon"):
            pic = f'<div style="height:{min(img_h, 96)}px;display:flex;align-items:center">{icon(it["icon"], c, 72)}</div>'
        out.append(f'<div class="step"{_ta(it.get("tip"))}>{pic}<div style="display:flex;gap:12px;align-items:flex-start">'
                   f'{badge(k, c, 40)}<p style="font-size:{size + 2}px;font-weight:600;line-height:1.2">{it["title"]}</p></div>'
                   + (f'<p style="font-size:{size - 2}px;line-height:1.38;color:var(--muted)">{it["text"]}</p>' if it.get("text") else "")
                   + "</div>")
        if arrows and k < len(items):
            out.append(f'<div class="arrow" aria-hidden="true">{icon("arrow", "#8A969C", 40, 2.2)}</div>')
    return f'<div class="steps">{"".join(out)}</div>'


def bracket(columns: Sequence[Sequence[dict]], links: Sequence[tuple], *, width: int = BOX_W, height: int = 560,
            box_w: int | None = None, gap_y: int = 18, size: int = 24) -> str:
    """A flowchart read left to right, like a tournament bracket: inputs on the left merge into what they make on
    the right (Carlo, 2026-09-28, for how bands become indices become scores become a model). columns: lists of boxes
    {"id", "title", "text", "color", "fill", "tip"}; links: (from_id, to_id). Text sits inside boxes, never on lines."""
    n = len(columns)
    bw = box_w or int((width - (n - 1) * 90) / n)
    xgap = (width - n * bw) / max(1, n - 1) if n > 1 else 0
    pos, boxes = {}, []
    for ci, colm in enumerate(columns):
        m = len(colm)
        bh = (height - (m - 1) * gap_y) / m
        x = ci * (bw + xgap)
        for ri, b in enumerate(colm):
            y = ri * (bh + gap_y)
            pos[b["id"]] = (x, y, bw, bh)
            c = b.get("color", "var(--line)")
            fill = b.get("fill") or "var(--card)"
            ink = "#F4F2EC" if fill.startswith("#") and is_dark(fill) else "var(--ink)"
            boxes.append(f'<div class="bbox" style="left:{x:.0f}px;top:{y:.0f}px;width:{bw}px;height:{bh:.0f}px;'
                         f'border:3px solid {c};background:{fill};color:{ink}"{_ta(b.get("tip"))}>'
                         f'<p style="font-size:{size}px;font-weight:600;line-height:1.2">{b["title"]}</p>'
                         + (f'<p style="font-size:{size - 3}px;line-height:1.3;opacity:.85">{b["text"]}</p>' if b.get("text") else "")
                         + "</div>")
    paths = []
    for a, b in links:
        x0, y0, w0, h0 = pos[a]
        x1, y1, w1, h1 = pos[b]
        sx, sy, tx, ty = x0 + w0, y0 + h0 / 2, x1, y1 + h1 / 2
        mx = sx + (tx - sx) / 2
        paths.append(f'<path d="M{sx:.0f} {sy:.0f}H{mx:.0f}V{ty:.0f}H{tx - 6:.0f}" fill="none" stroke="#9AA3A8" stroke-width="3"/>'
                     f'<path d="M{tx - 12:.0f} {ty - 7:.0f}L{tx:.0f} {ty:.0f}L{tx - 12:.0f} {ty + 7:.0f}" fill="none" stroke="#9AA3A8" stroke-width="3"/>')
    svg = f'<svg class="links" width="{width}" height="{height}" aria-hidden="true">{"".join(paths)}</svg>'
    return f'<div class="bracket" style="width:{width}px;height:{height}px">{svg}{"".join(boxes)}</div>'


def tabs(items: Sequence[dict], *, height: int | None = None) -> str:
    """Tabs inside one slide: two or three places to look in the same map, or alternative views
    (Carlo, 2026-09-29: "tab between three sites of interest"). items: {"label", "body", "tip"}."""
    bar = "".join(f'<button class="tab{" on" if k == 0 else ""}" data-tab="{k}"{_ta(it.get("tip"))}>{it["label"]}</button>'
                  for k, it in enumerate(items))
    panes = "".join(f'<div class="pane" data-pane="{k}"{" hidden" if k else ""}>{it["body"]}</div>' for k, it in enumerate(items))
    st = f' style="height:{height}px"' if height else ""
    return f'<div class="tabs"{st}><div class="tabbar">{bar}</div><div class="panes">{panes}</div></div>'


def link_button(url: str, label: str, *, icon_name: str = "map", color: str | None = None) -> str:
    """A link out of the deck (the interactive map page, the full table). Opens in a new tab."""
    c = color or "var(--accent)"
    return (f'<a class="lbtn" href="{esc(url, quote=True)}" target="_blank" rel="noopener" style="border-color:{c};color:{c}">'
            f'{icon(icon_name, c, 32)}<span>{label}</span></a>')


def _data_uri(src) -> str:
    if isinstance(src, (bytes, bytearray)):
        data = bytes(src)
        ext = "jpg" if data[:2] == b"\xff\xd8" else "webp" if data[8:12] == b"WEBP" else "png"
    else:
        p = Path(src)
        data, ext = p.read_bytes(), p.suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "gif": "image/gif",
            "svg": "image/svg+xml"}.get(ext, "image/png")
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def image(src, *, width: int, height: int, fit: str = "contain", alt: str = "", tip=None, radius: int = 12,
          layers: Sequence[dict] = (), caption: str | None = None, bg: str = "#FFFFFF") -> str:
    """A picture, inlined (the deck stays one file). Photos fit="cover"; screenshots and diagrams "contain".
    layers: SVG overlays in the image's own pixel coordinates (see Frame), each {"id", "svg"} — pair with key(...,
    toggle=id) so the reader turns each source on and off (Carlo, 2026-09-24)."""
    lay = ""
    if layers:
        g = "".join(f'<g data-layer="{esc(L["id"])}">{L["svg"]}</g>' for L in layers)
        vb = layers[0].get("viewbox") or f"0 0 {width} {height}"
        lay = f'<svg class="over" viewBox="{vb}" preserveAspectRatio="xMidYMid slice" width="{width}" height="{height}">{g}</svg>'
    cap = f'<p class="cap">{caption}</p>' if caption else ""
    return (f'<figure class="pic" style="width:{width}px;height:{height}px;border-radius:{radius}px;background:{bg}"{_ta(tip)}>'
            f'<img src="{_data_uri(src)}" alt="{esc(alt, quote=True)}" style="width:100%;height:100%;object-fit:{fit}">{lay}{cap}</figure>')


def table(columns: Sequence[str], rows: Sequence[Sequence], *, numeric: Sequence[int] = (), shade: dict | None = None,
          tips: Sequence[Sequence] | None = None, col_tips: Sequence | None = None, size: int = 26,
          widths: Sequence[int] | None = None, fmt=None) -> str:
    """A slide-sized table (at most about 8 rows; split or chart anything bigger). shade: {"cols": [i, ...],
    "scale": "good_bad"|"heat"|"blues"|"diverging", "better": "low"|"high", "domain": (lo, hi)} tints value
    cells (numbers stay printed). tips: per-cell tips, col_tips: per-column header tips."""
    def cell_val(v):
        return _fmt(fmt, v) if isinstance(v, (int, float)) else ("–" if v is None else str(v))
    ncls = ' class="n"'
    head = "".join(f'<th{ncls if k in numeric else ""}{_ta(col_tips[k] if col_tips else None)}'
                   + (f' style="width:{widths[k]}px"' if widths else "") + f'>{c}</th>' for k, c in enumerate(columns))
    body = []
    scols = set((shade or {}).get("cols", []))
    if shade:
        vals = [r[k] for r in rows for k in scols if isinstance(r[k], (int, float))]
        dom = shade.get("domain") or ((min(vals), max(vals)) if vals else (0, 1))
    for ri, r in enumerate(rows):
        tds = []
        for k, v in enumerate(r):
            st = ""
            if shade and k in scols and isinstance(v, (int, float)):
                bgc = vk.shade_color(v, scale=shade.get("scale", "good_bad"), better=shade.get("better", "low"), domain=dom)
                st = f' style="background:{bgc}' + (';color:#FFFFFF' if bgc.startswith("#") and is_dark(bgc) else "") + '"'
            tt = tips[ri][k] if tips and ri < len(tips) and k < len(tips[ri]) else None
            tds.append(f'<td{ncls if k in numeric else ""}{st}{_ta(tt)}>{cell_val(v)}</td>')
        body.append("<tr>" + "".join(tds) + "</tr>")
    return f'<table class="tbl" style="font-size:{size}px"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>'


# ============================================================================ charts (SVG / HTML at slide size)
def hbar(rows: Sequence[dict], series: Sequence[dict], *, width: int = 1100, label_w: int = 300, bar_h: int = 34,
         max_value: float | None = None, fmt=None, unit: str = "", ref: dict | None = None, label_size: int = 26,
         value_size: int = 26, gap: int = 8, row_gap: int = 26, value_w: int = 150) -> str:
    """Horizontal bars, one bar per series in each row (two bars per row compares two models or groups side by side;
    Carlo, 2026-09-29). Values print at the end of each bar; bars and labels carry tips.
    rows: {"label", "values": [...], "tips": [...], "label_tip", "after": [...] (small text after each value, e.g. n = 52)};
    series: {"name", "color", "stripe": bool}. ref: {"value", "label", "tip"} draws a reference line."""
    vmax = max_value or max((v for r in rows for v in r["values"] if v is not None), default=1) or 1
    track = width - label_w - value_w
    out = []
    for r in rows:
        bars = []
        for k, (v, s) in enumerate(zip(r["values"], series)):
            c = s["color"]
            fill = (f"repeating-linear-gradient(45deg,{c} 0 7px,{mix(c, '#FFFFFF', .45)} 7px 12px)" if s.get("stripe") else c)
            tt = (r.get("tips") or [None] * len(series))[k]
            nt = (r.get("after") or [None] * len(series))[k]
            wpx = 0 if v is None else max(2, track * v / vmax)
            bars.append(f'<div class="hb" style="height:{bar_h}px"{_ta(tt)}><div class="bar" style="width:{wpx:.0f}px;background:{fill}"></div>'
                        f'<span class="val" style="font-size:{value_size}px">{_fmt(fmt, v)}{esc(unit)}'
                        + (f' <small>{nt}</small>' if nt else "") + "</span></div>")
        out.append(f'<div class="hrow" style="gap:{gap}px"><p class="hl" style="width:{label_w}px;font-size:{label_size}px"{_ta(r.get("label_tip"))}>'
                   f'{r["label"]}</p><div class="tracks" style="gap:{gap}px">{"".join(bars)}</div></div>')
    refl = ""
    if ref:
        x = label_w + track * ref["value"] / vmax
        refl = (f'<div class="ref" style="left:{x:.0f}px"{_ta(ref.get("tip"))}><span>{ref.get("label", "")}</span></div>')
    return f'<div class="hbar" style="width:{width}px;gap:{row_gap}px">{refl}{"".join(out)}</div>'


def _axis_y(ticks, y_of, x0, x1, fmt, unit, size=22):
    g = []
    for t in ticks:
        y = y_of(t)
        g.append(f'<line x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}" stroke="#D9D6CC" stroke-width="1.5"/>'
                 f'<text class="tick" x="{x0 - 14}" y="{y:.1f}" dy=".34em" text-anchor="end" font-size="{size}">{_fmt(fmt, t)}{esc(unit)}</text>')
    return "".join(g)


def columns(labels: Sequence[str], series: Sequence[dict], *, width: int = 1100, height: int = 520, stacked: bool = False,
            fmt=None, unit: str = "", y_label: str = "", tips: Sequence[Sequence] | None = None,
            max_value: float | None = None, value_labels: bool = True, label_tips: Sequence | None = None,
            label_size: int = 24) -> str:
    """Vertical columns: grouped (side by side) or stacked. series: {"name", "color", "values": [...]}; tips[s][i]."""
    pad_l, pad_b, pad_t, pad_r = 92, 70, 40 if value_labels else 16, 16
    n = len(labels)
    totals = [sum((s["values"][i] or 0) for s in series) for i in range(n)]
    vmax = max_value or (max(totals) if stacked else max((v or 0) for s in series for v in s["values"])) or 1
    ticks = _ticks(0, vmax)
    vmax = max(vmax, ticks[-1])
    ih, iw = height - pad_b - pad_t, width - pad_l - pad_r
    y_of = lambda v: pad_t + ih * (1 - v / vmax)                       # noqa: E731
    gw = iw / n
    bw = gw * (0.62 if stacked else 0.78) / (1 if stacked else len(series))
    g = [_axis_y(ticks, y_of, pad_l, width - pad_r, fmt, unit)]
    for i, lab in enumerate(labels):
        gx = pad_l + gw * i + (gw - bw * (1 if stacked else len(series))) / 2
        base = 0
        for k, s in enumerate(series):
            v = s["values"][i]
            if v is None:
                continue
            x = gx if stacked else gx + k * bw
            y0, y1 = (y_of(base + v), y_of(base)) if stacked else (y_of(v), y_of(0))
            tt = tips[k][i] if tips else None
            g.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{bw - (0 if stacked else 4):.1f}" height="{max(0, y1 - y0):.1f}" '
                     f'fill="{s["color"]}" rx="3"{_ta(tt)}/>')
            if value_labels and not stacked:
                g.append(f'<text x="{x + bw / 2 - 2:.1f}" y="{y0 - 10:.1f}" text-anchor="middle" font-size="22" font-weight="600">{_fmt(fmt, v)}</text>')
            base += v if stacked else 0
        if value_labels and stacked:
            g.append(f'<text x="{gx + bw / 2:.1f}" y="{y_of(totals[i]) - 10:.1f}" text-anchor="middle" font-size="22" font-weight="600">{_fmt(fmt, totals[i])}</text>')
        lt = label_tips[i] if label_tips else None
        g.append(f'<text class="xl" x="{pad_l + gw * (i + .5):.1f}" y="{height - pad_b + 34}" text-anchor="middle" font-size="{label_size}"{_ta(lt)}>{lab}</text>')
    if y_label:
        g.append(f'<text class="tick" x="{pad_l}" y="18" font-size="22">{y_label}</text>')
    return f'<svg class="chart" width="{width}" height="{height}" role="img">{"".join(g)}</svg>'


def lines(x: Sequence[float], series: Sequence[dict], *, width: int = 1100, height: int = 520, x_labels: Sequence[str] | None = None,
          y_label: str = "", fmt=None, unit: str = "", y_min: float | None = None, y_max: float | None = None,
          end_labels: bool = True, tips: Sequence[Sequence] | None = None, label_w: int = 190, x_tips: Sequence | None = None,
          marks: Sequence[dict] = (), label_at: str = "end") -> str:
    """Lines over an ordered x, each labelled in its own colour (no legend to decode): at its right end, or with
    label_at="max" above its highest point (better for distributions that all end at zero). series: {"name",
    "color", "values", "dash": bool, "tip"}; tips[s][i] per point. marks: vertical lines {"x", "label", "tip"}."""
    at_end = end_labels and label_at == "end"
    pad_l, pad_b, pad_t, pad_r = 92, 64, 40 if label_at == "max" else 24, (label_w if at_end else 30)
    vals = [v for s in series for v in s["values"] if v is not None]
    lo = y_min if y_min is not None else min(0, min(vals))
    hi = y_max if y_max is not None else max(vals)
    ticks = _ticks(lo, hi)
    lo, hi = min(lo, ticks[0]), max(hi, ticks[-1])
    ih, iw = height - pad_b - pad_t, width - pad_l - pad_r
    x0, x1 = min(x), max(x)
    xp = lambda v: pad_l + iw * ((v - x0) / ((x1 - x0) or 1))         # noqa: E731
    yp = lambda v: pad_t + ih * (1 - (v - lo) / ((hi - lo) or 1))     # noqa: E731
    g = [_axis_y(ticks, yp, pad_l, width - pad_r, fmt, unit)]
    labs = x_labels or [_fmt(None, v) for v in x]
    step = max(1, math.ceil(len(x) / 10))
    for i, (xv, lab) in enumerate(zip(x, labs)):
        if i % step == 0 or i == len(x) - 1:
            g.append(f'<text class="tick" x="{xp(xv):.1f}" y="{height - pad_b + 34}" text-anchor="middle" font-size="22"'
                     f'{_ta(x_tips[i] if x_tips else None)}>{lab}</text>')
    for m in marks:
        xx = xp(m["x"])
        g.append(f'<g{_ta(m.get("tip"))}><line x1="{xx:.1f}" x2="{xx:.1f}" y1="{pad_t}" y2="{height - pad_b}" stroke="#8A969C" '
                 f'stroke-width="2.5" stroke-dasharray="8 6"/><text x="{xx + 8:.1f}" y="{pad_t + 22}" font-size="22" fill="#4A5560">{m.get("label", "")}</text></g>')
    ends = []
    for k, s in enumerate(series):
        pts = [(xp(xv), yp(v)) for xv, v in zip(x, s["values"]) if v is not None]
        if not pts:
            continue
        d = "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in pts)
        g.append(f'<path d="{d}" fill="none" stroke="{s["color"]}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"'
                 + (' stroke-dasharray="12 8"' if s.get("dash") else "") + f'{_ta(s.get("tip"))}/>')
        for i, (xv, v) in enumerate(zip(x, s["values"])):
            if v is None:
                continue
            tt = tips[k][i] if tips else None
            g.append(f'<circle cx="{xp(xv):.1f}" cy="{yp(v):.1f}" r="7" fill="{s["color"]}" stroke="#FFFFFF" stroke-width="2"{_ta(tt)}/>')
        ends.append([pts[-1][1], s, max(pts, key=lambda q: -q[1])])
    if end_labels and label_at == "max":
        for _, s, (px, py) in ends:
            g.append(f'<text x="{px:.1f}" y="{py - 18:.1f}" text-anchor="middle" font-size="24" font-weight="600" fill="{s["color"]}"'
                     f'{_ta(s.get("tip"))}>{s["name"]}</text>')
    elif end_labels:      # spread end labels so they never overlap, and keep them above the x axis
        ends.sort(key=lambda e: e[0])
        for j in range(1, len(ends)):
            ends[j][0] = max(ends[j][0], ends[j - 1][0] + 34)
        over = ends[-1][0] - (height - pad_b - 16) if ends else 0
        for e_ in ends:
            e_[0] -= max(0, over)
        for yv, s, _ in ends:
            g.append(f'<text x="{width - pad_r + 16}" y="{yv:.1f}" dy=".34em" font-size="24" font-weight="600" fill="{s["color"]}"'
                     f'{_ta(s.get("tip"))}>{s["name"]}</text>')
    if y_label:
        g.append(f'<text class="tick" x="{pad_l}" y="14" font-size="22">{y_label}</text>')
    return f'<svg class="chart" width="{width}" height="{height}" role="img">{"".join(g)}</svg>'


def dots(rows: Sequence[dict], *, width: int = 1100, label_w: int = 330, lo: float | None = None, hi: float | None = None,
         fmt=None, unit: str = "", ref: dict | None = None, axis_label: str = "", row_h: int = 56, label_size: int = 26) -> str:
    """Estimates with intervals, one row each (a forest plot). rows: {"label", "value", "low", "high", "color", "tip",
    "label_tip", "group" (a small heading row before this one)}. Say in the tip or caption how the interval was made."""
    vals = [v for r in rows for v in (r.get("low"), r.get("high"), r["value"]) if v is not None]
    lo = lo if lo is not None else min(vals)
    hi = hi if hi is not None else max(vals)
    ticks = _ticks(lo, hi)
    lo, hi = min(lo, ticks[0]), max(hi, ticks[-1])
    vw = 130
    iw = width - label_w - vw - 20
    xp = lambda v: label_w + 10 + iw * (v - lo) / ((hi - lo) or 1)     # noqa: E731
    n_rows = len(rows) + sum(1 for r in rows if r.get("group"))
    height = n_rows * row_h + 60
    g, y = [], 10
    for t in ticks:
        g.append(f'<line x1="{xp(t):.1f}" x2="{xp(t):.1f}" y1="0" y2="{height - 50}" stroke="#E4E1D8" stroke-width="1.5"/>'
                 f'<text class="tick" x="{xp(t):.1f}" y="{height - 18}" text-anchor="middle" font-size="22">{_fmt(fmt, t)}{esc(unit)}</text>')
    if ref:
        g.append(f'<g{_ta(ref.get("tip"))}><line x1="{xp(ref["value"]):.1f}" x2="{xp(ref["value"]):.1f}" y1="0" y2="{height - 50}" '
                 f'stroke="#4A5560" stroke-width="2.5" stroke-dasharray="8 6"/></g>')
    for r in rows:
        if r.get("group"):
            g.append(f'<text x="0" y="{y + row_h * .62:.0f}" font-size="{label_size - 2}" font-weight="700" fill="#4A5560">{r["group"]}</text>')
            y += row_h
        cy = y + row_h / 2
        c = r.get("color", "#2E6A8A")
        g.append(f'<text x="0" y="{cy:.0f}" dy=".34em" font-size="{label_size}"{_ta(r.get("label_tip"))}>{r["label"]}</text>')
        gg = []
        if r.get("low") is not None and r.get("high") is not None:
            gg.append(f'<line x1="{xp(r["low"]):.1f}" x2="{xp(r["high"]):.1f}" y1="{cy:.0f}" y2="{cy:.0f}" stroke="{c}" stroke-width="6" stroke-linecap="round" opacity=".55"/>')
        gg.append(f'<circle cx="{xp(r["value"]):.1f}" cy="{cy:.0f}" r="12" fill="{c}" stroke="#FFFFFF" stroke-width="3"/>')
        gg.append(f'<text x="{width - vw + 10}" y="{cy:.0f}" dy=".34em" font-size="24" font-weight="600">{_fmt(fmt, r["value"])}{esc(unit)}</text>')
        g.append(f'<g{_ta(r.get("tip"))}>{"".join(gg)}</g>')
        y += row_h
    if axis_label:
        g.append(f'<text class="tick" x="{label_w + 10 + iw / 2:.0f}" y="{height + 14}" text-anchor="middle" font-size="22">{axis_label}</text>')
        height += 24
    return f'<svg class="chart" width="{width}" height="{height}" role="img">{"".join(g)}</svg>'


def scatter(points: Sequence[dict], *, width: int = 900, height: int = 620, x_label: str = "", y_label: str = "",
            x_range: tuple | None = None, y_range: tuple | None = None, fits: Sequence[dict] = (), r: float = 7,
            fmt_x=None, fmt_y=None) -> str:
    """Points (one per bird, fire, site), optionally with fitted lines. points: {"x", "y", "color", "tip", "layer"};
    fits: {"x0", "y0", "x1", "y1", "color", "label", "tip", "dash", "layer"}. Use layer + key(toggle=...) to switch groups."""
    pad_l, pad_b, pad_t, pad_r = 96, 76, 20, 30
    xs, ys = [p["x"] for p in points], [p["y"] for p in points]
    xl, xh = x_range or (min(xs), max(xs))
    yl, yh = y_range or (min(ys), max(ys))
    xt, yt = _ticks(xl, xh), _ticks(yl, yh)
    xl, xh, yl, yh = min(xl, xt[0]), max(xh, xt[-1]), min(yl, yt[0]), max(yh, yt[-1])
    iw, ih = width - pad_l - pad_r, height - pad_b - pad_t
    xp = lambda v: pad_l + iw * (v - xl) / ((xh - xl) or 1)          # noqa: E731
    yp = lambda v: pad_t + ih * (1 - (v - yl) / ((yh - yl) or 1))     # noqa: E731
    g = [_axis_y(yt, yp, pad_l, width - pad_r, fmt_y, "")]
    for t in xt:
        g.append(f'<text class="tick" x="{xp(t):.1f}" y="{height - pad_b + 32}" text-anchor="middle" font-size="22">{_fmt(fmt_x, t)}</text>')
    layers: dict = {}
    for p in points:
        layers.setdefault(p.get("layer"), []).append(
            f'<circle cx="{xp(p["x"]):.1f}" cy="{yp(p["y"]):.1f}" r="{r}" fill="{p.get("color", "#2E6A8A")}" fill-opacity=".78" '
            f'stroke="#FFFFFF" stroke-width="1.2"{_ta(p.get("tip"))}/>')
    for L, els in layers.items():
        g.append(f'<g{" data-layer=" + chr(34) + esc(L) + chr(34) if L else ""}>{"".join(els)}</g>')
    for f in fits:
        lay = f' data-layer="{esc(f["layer"])}"' if f.get("layer") else ""
        g.append(f'<g{lay}{_ta(f.get("tip"))}><line x1="{xp(f["x0"]):.1f}" y1="{yp(f["y0"]):.1f}" x2="{xp(f["x1"]):.1f}" y2="{yp(f["y1"]):.1f}" '
                 f'stroke="{f.get("color", "#172026")}" stroke-width="5" stroke-linecap="round"'
                 + (' stroke-dasharray="12 8"' if f.get("dash") else "") + "/>"
                 + (f'<text x="{xp(f["x1"]) + 8:.1f}" y="{yp(f["y1"]):.1f}" dy=".34em" font-size="22" font-weight="600" '
                    f'fill="{f.get("color", "#172026")}">{f["label"]}</text>' if f.get("label") else "") + "</g>")
    g.append(f'<text class="tick" x="{pad_l + iw / 2:.0f}" y="{height - 12}" text-anchor="middle" font-size="22">{x_label}</text>')
    g.append(f'<text class="tick" transform="translate(22 {pad_t + ih / 2:.0f}) rotate(-90)" text-anchor="middle" font-size="22">{y_label}</text>')
    return f'<svg class="chart" width="{width}" height="{height}" role="img">{"".join(g)}</svg>'


def spans(rows: Sequence[dict], *, start: float, end: float, width: int = 1400, label_w: int = 300, ticks: Sequence | None = None,
          bar_h: int = 34, row_h: int = 96, label_size: int = 28) -> str:
    """Time spans on one axis (what each record covers, when): rows {"label", "from", "to", "color", "tip", "note",
    "icon" (an SVG string, e.g. a map outline filled in the row's colour), "label_tip"}."""
    iw = width - label_w - 40
    xp = lambda v: label_w + 20 + iw * (v - start) / ((end - start) or 1)  # noqa: E731
    height = len(rows) * row_h + 56
    g = []
    for t in (ticks or _ticks(start, end, 6)):
        if start <= t <= end:
            g.append(f'<line x1="{xp(t):.1f}" x2="{xp(t):.1f}" y1="0" y2="{height - 44}" stroke="#E4E1D8" stroke-width="1.5"/>'
                     f'<text class="tick" x="{xp(t):.1f}" y="{height - 12}" text-anchor="middle" font-size="22">{t:g}</text>')
    for k, r in enumerate(rows):
        y = k * row_h + 14
        c = r.get("color", "#2E6A8A")
        ic = f'<g transform="translate(0 {y - 4})">{r["icon"]}</g>' if r.get("icon") else ""
        lx = 64 if r.get("icon") else 0
        g.append(f'{ic}<text x="{lx}" y="{y + bar_h / 2:.0f}" dy=".34em" font-size="{label_size}" font-weight="600" fill="{c}"'
                 f'{_ta(r.get("label_tip"))}>{r["label"]}</text>')
        note_ = (f'<text x="{xp(r["from"]):.1f}" y="{y + bar_h + 30}" font-size="22" fill="#4A5560">{r["note"]}</text>'
                 if r.get("note") else "")
        g.append(f'<g{_ta(r.get("tip"))}><rect x="{xp(r["from"]):.1f}" y="{y}" width="{max(4, xp(r["to"]) - xp(r["from"])):.1f}" '
                 f'height="{bar_h}" rx="6" fill="{c}"/>{note_}</g>')
    return f'<svg class="chart" width="{width}" height="{height}" role="img">{"".join(g)}</svg>'


def waffle(groups: Sequence[dict], *, per_row: int = 20, cell: int = 28, gap: int = 6, unit_label: str = "") -> str:
    """A grid of squares, one per unit (or per N units): parts of a whole people can count. groups: {"label", "n",
    "color", "tip"}; the key under it lists each group with its count."""
    sq = []
    for gr in groups:
        sq += [f'<i style="background:{gr["color"]}"{_ta(gr.get("tip"))}></i>'] * int(gr["n"])
    grid = (f'<div class="waffle" style="grid-template-columns:repeat({per_row},{cell}px);gap:{gap}px;--c:{cell}px">'
            + "".join(sq) + "</div>")
    lab = key([{"label": f'{gr["label"]} · {fint(gr["n"])}{(" " + unit_label) if unit_label else ""}', "color": gr["color"],
                "tip": gr.get("tip")} for gr in groups], title="")
    return col(grid, lab, gap=18)


def scale(bands: Sequence[dict], marks: Sequence[dict] = (), *, width: int = 1500, lo: float = 0, hi: float = 1,
          fmt=None, bar_h: int = 40, cuts_label: bool = True) -> str:
    """A spectrum with class bands and markers on it: where each case falls, which class that puts it in, and how
    close it is to a threshold (Carlo, 2026-09-29: a line split into classes with heavy dividers).
    bands: {"from", "to", "color", "label", "tip"}; marks: {"value", "label", "tip", "color", "row"}."""
    xp = lambda v: 20 + (width - 40) * (v - lo) / ((hi - lo) or 1)  # noqa: E731
    rows_n = max([m.get("row", 0) for m in marks] + [0]) + 1
    top = 30 + rows_n * 44
    height = top + bar_h + 96
    g = []
    for b in bands:
        x0, x1 = xp(b["from"]), xp(b["to"])
        g.append(f'<g{_ta(b.get("tip"))}><rect x="{x0:.1f}" y="{top}" width="{x1 - x0:.1f}" height="{bar_h}" fill="{b["color"]}"/>'
                 f'<text x="{(x0 + x1) / 2:.1f}" y="{top + bar_h + 34}" text-anchor="middle" font-size="24" font-weight="600">{b["label"]}</text></g>')
    for b in bands[1:]:
        x = xp(b["from"])
        g.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top - 10}" y2="{top + bar_h + 10}" stroke="#172026" stroke-width="5"/>')
        if cuts_label:
            g.append(f'<text class="tick" x="{x:.1f}" y="{top + bar_h + 70}" text-anchor="middle" font-size="22">{_fmt(fmt, b["from"])}</text>')
    for m in marks:
        x, rr = xp(m["value"]), m.get("row", 0)
        y = 20 + rr * 44
        c = m.get("color", "#172026")
        g.append(f'<g{_ta(m.get("tip"))}><line x1="{x:.1f}" x2="{x:.1f}" y1="{y + 16}" y2="{top}" stroke="{c}" stroke-width="2.5"/>'
                 f'<circle cx="{x:.1f}" cy="{y + 8}" r="9" fill="{c}" stroke="#FFFFFF" stroke-width="2"/>'
                 + (f'<text x="{x + 14:.1f}" y="{y + 8}" dy=".34em" font-size="22">{m["label"]}</text>' if m.get("label") else "") + "</g>")
    return f'<svg class="chart" width="{width}" height="{height}" role="img">{"".join(g)}</svg>'


# ============================================================================ maps
class Frame:
    """Web-Mercator pixel frame for a still map picture: Frame(bounds=(w, s, e, n), size=(width, height)).
    frame.xy(lon, lat) -> pixel (x, y) in the picture; frame.path(geometry) -> SVG path data for a GeoJSON
    Polygon / MultiPolygon / LineString; frame.basemap() fetches and stitches the tiles under it (cached)."""

    def __init__(self, bounds: tuple, size: tuple = (1200, 760), pad: float = 0.06):
        self.W, self.H = size
        w, s, e, n = bounds
        dx, dy = (e - w) * pad, (n - s) * pad
        w, e, s, n = w - dx, e + dx, max(-85, s - dy), min(85, n + dy)
        # zoom where the bounds fill the picture; then centre the picture on the bounds' middle
        for z in range(19, 0, -1):
            x0, y0 = self._px(w, n, z)
            x1, y1 = self._px(e, s, z)
            if x1 - x0 <= self.W and y1 - y0 <= self.H:
                break
        self.z = z
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        self.ox, self.oy = cx - self.W / 2, cy - self.H / 2
        k = min(self.W / max(1, x1 - x0), self.H / max(1, y1 - y0))      # scale up to fill (<= 2x, keeps tiles sharp)
        self.k = min(2.0, max(1.0, k))
        self.ox, self.oy = cx - self.W / 2 / self.k, cy - self.H / 2 / self.k

    @staticmethod
    def _px(lon, lat, z):
        n = 256 * 2 ** z
        x = (lon + 180) / 360 * n
        la = math.radians(lat)
        y = (1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * n
        return x, y

    def xy(self, lon: float, lat: float):
        x, y = self._px(lon, lat, self.z)
        return (x - self.ox) * self.k, (y - self.oy) * self.k

    def path(self, geom: dict) -> str:
        def ring(cs, close=True):
            pts = [self.xy(*c[:2]) for c in cs]
            return "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in pts) + (" Z" if close else "")
        t, c = geom["type"], geom["coordinates"]
        if t == "Polygon":
            return " ".join(ring(r) for r in c)
        if t == "MultiPolygon":
            return " ".join(ring(r) for p in c for r in p)
        if t == "LineString":
            return ring(c, False)
        if t == "MultiLineString":
            return " ".join(ring(r, False) for r in c)
        raise ValueError(f"Frame.path: unsupported geometry {t}")

    def basemap(self, source: str = "imagery", cache: Path | None = None) -> bytes:
        """PNG of the base map under this frame. source: "imagery" (Esri World Imagery) or "light" (CARTO light,
        OpenStreetMap data). Tiles are cached; say which base map it is in the slide's footer (credit())."""
        import io
        import urllib.request
        from PIL import Image
        url = {"imagery": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
               "light": "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png"}[source]
        cache = Path(cache or Path.home() / ".cache" / _SKILL.name / "tiles" / source)
        cache.mkdir(parents=True, exist_ok=True)
        sw, sh = self.W / self.k, self.H / self.k
        tx0, ty0 = int(self.ox // 256), int(self.oy // 256)
        tx1, ty1 = int((self.ox + sw) // 256), int((self.oy + sh) // 256)
        canvas = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256), (230, 230, 226))
        n = 2 ** self.z
        for tx in range(tx0, tx1 + 1):
            for ty in range(ty0, ty1 + 1):
                if not 0 <= ty < n:
                    continue
                f = cache / f"{self.z}_{tx % n}_{ty}.png"
                if not f.is_file():
                    req = urllib.request.Request(url.format(z=self.z, x=tx % n, y=ty),
                                                 headers={"User-Agent": f"{_SKILL.name}/1.0 (+https://github.com/NCEAS-AI/Coding-Agent-Skills-for-Data-Science)"})
                    f.write_bytes(urllib.request.urlopen(req, timeout=30).read())
                im = Image.open(f).convert("RGB").resize((256, 256))
                canvas.paste(im, ((tx - tx0) * 256, (ty - ty0) * 256))
        cx0, cy0 = self.ox - tx0 * 256, self.oy - ty0 * 256
        crop = canvas.crop((round(cx0), round(cy0), round(cx0 + sw), round(cy0 + sh))).resize((self.W, self.H), Image.LANCZOS)
        out = io.BytesIO()
        crop.save(out, "JPEG" if source == "imagery" else "PNG", quality=86)
        return out.getvalue()

    @staticmethod
    def credit(source: str = "imagery") -> str:
        return {"imagery": "Base map: Esri World Imagery (Esri, Maxar, Earthstar Geographics)",
                "light": "Base map: CARTO light, © OpenStreetMap contributors (ODbL)"}[source]


def map_live(spec, base=None, *, width: int = BOX_W, height: int = 700, label: str = "Interactive map") -> str:
    """A live MapLibre map inside a slide (the page skill's map spec, references/map-spec.md there). Use it when the
    reader must pan and zoom during the talk; otherwise prefer a still picture with tabs and toggles plus
    link_button() to the published interactive map (Carlo, 2026-09-28: "don't let me scroll around")."""
    import build_map
    if isinstance(spec, (str, Path)):
        sp = Path(spec).resolve()
        spec, base = json.loads(sp.read_text()), sp.parent
    doc, _layers, warns = build_map.build_page(spec, Path(base or "."), embed=True)
    for w_ in warns:
        print("map_live: WARNING:", w_)
    return (f'<iframe class="livemap" title="{esc(label, quote=True)}" allow="fullscreen" style="width:{width}px;height:{height}px" '
            f'srcdoc="{esc(doc, quote=True)}"></iframe>')


# ============================================================================ the deck
class Deck:
    """One deck in one language. Add sections and slides in order; write() makes the page."""

    def __init__(self, title: str, *, subtitle: str = "", lang: str = "en", sources: Sequence[str] = (),
                 script: str = "", author: str | None = None, affiliation: str | None = None, theme: dict | None = None,
                 sources_slide: bool = True, footer_note: str = ""):
        self.title, self.subtitle, self.lang = title, subtitle, lang
        self.sources, self.script, self.footer_note = list(sources), script, footer_note
        self.theme = {**THEME, **(theme or {})}
        idt = vk.load_identity()
        self.author = author or idt.get("author", "")
        self.affiliation = affiliation if author else (affiliation or idt.get("affiliation", ""))
        self.sections: list[dict] = []
        self.slides: list[dict] = []
        self.sources_slide = sources_slide

    # ---------------------------------------------------------------- structure
    def section(self, name: str, color: str | None = None) -> "Deck":
        """Start a section: its name heads its group in the progress strip; slides added after it belong to it."""
        self.sections.append({"name": name, "color": color or SECTION_COLORS[len(self.sections) % len(SECTION_COLORS)]})
        return self

    def _add(self, s: dict) -> "Deck":
        if not self.sections:
            self.section("")
        s["sec"] = len(self.sections) - 1
        self.slides.append(s)
        return self

    def slide(self, id: str, title: str, body: str = "", *, kicker: str | None = None, lede: str | None = None,
              info: tuple | None = None, source: str = "", bg: str | None = None, tint: str | None = None,
              title_tip=None) -> "Deck":
        """A content slide: title at the top margin (same place on every slide), optional one-line lede, the body,
        a footer with the source, and info=(title, html) behind the (i) at the bottom right. No speaker notes
        (Carlo, 2026-10-23: "I don't need speaker notes at all"): what a reader needs goes in the (i) or a tip.
        tint: a concept colour washed into the background when the whole slide is about that concept (Carlo,
        2026-09-24: the first-call slides light green, the second-call slides dark green)."""
        return self._add(dict(kind="content", id=id, title=title, body=body, kicker=kicker, lede=lede,
                              info=info, source=source, bg=bg, tint=tint, title_tip=title_tip))

    def statement(self, id: str, text_: str, *, sub: str = "", info: tuple | None = None,
                  bg: str | None = None, source: str = "") -> "Deck":
        """One sentence, large, on the section colour (a question, a turn in the story, the pitch at the end of a
        section). Sparingly: one or two per section at most."""
        return self._add(dict(kind="statement", id=id, title=re.sub(r"<[^>]+>", "", text_), text=text_, sub=sub,
                              info=info, bg=bg, source=source))

    def cover(self, *, id: str = "cover", image_src=None, info: tuple | None = None) -> "Deck":
        """The title slide: title, subtitle, byline (who, when started, when updated) and the logos."""
        return self._add(dict(kind="cover", id=id, title=self.title, image=image_src, info=info))

    # ---------------------------------------------------------------- rendering
    def _ui(self, k):
        return UI.get(self.lang, UI["en"])[k]

    def _bg(self, s):
        sec = self.sections[s["sec"]]
        if s["kind"] == "statement":
            return s.get("bg") or mix(sec["color"], "#101418", .82)
        if s.get("bg"):
            return s["bg"]
        if s.get("tint"):
            return mix(s["tint"], self.theme["bg"], .16)
        return self.theme["bg"]

    def _render_slide(self, s, meta) -> str:
        sec = self.sections[s["sec"]]
        bg = self._bg(s)
        dark = is_dark(bg)
        info = ""
        if s.get("info"):
            it, ib = s["info"]
            info = f'<template class="sl-info"><b class="t">{it}</b>{ib}</template>'
        foot = f'<p class="sl-foot">{s["source"]}</p>' if s.get("source") else ""
        attrs = (f'class="slide{" dark" if dark else ""}" id="s-{esc(s["id"])}" data-id="{esc(s["id"])}" data-sec="{s["sec"]}" '
                 f'data-title="{esc(re.sub(r"<[^>]+>", "", s["title"]), quote=True)}" data-bg="{bg}" style="background:{bg};--sec:{sec["color"]}"')
        if s["kind"] == "cover":
            logos = "".join(f'<a class="org" href="{esc(o["url"])}" target="_blank" rel="noopener">{vk._logo(o)}'
                            f'<span><b>{esc(o["short"])}</b><small>{esc(o["name"])}</small></span></a>' for o in vk.load_identity().get("orgs", []))
            t = re.sub(r"\s*·\s*\d{4}-\d{2}-\d{2}\s*$", "", self.title)
            date = re.search(r"\d{4}-\d{2}-\d{2}\s*$", self.title)
            pic = (f'<img class="cover-img" src="{_data_uri(s["image"])}" alt="">' if s.get("image") is not None else "")
            when = f'{self._ui("started")} {meta["created"][:10]} · {self._ui("updated")} {meta["updated_txt"]}'
            inner = (f'{pic}<div class="cover-in"><p class="kicker">{esc(date.group(0) if date else "")}</p><h1>{t}</h1>'
                     f'<p class="cover-sub">{self.subtitle}</p>'
                     f'<p class="byline">{self._ui("by")} <b>{esc(self.author)}</b>{", " + esc(self.affiliation) if self.affiliation else ""}'
                     f' · <time>{esc(when)}</time></p></div><div class="cover-logos">{logos}</div>')
            return f'<section {attrs}>{inner}{info}</section>'
        if s["kind"] == "statement":
            inner = (f'<div class="stmt"><p class="kicker">{esc(sec["name"])}</p><h2>{s["text"]}</h2>'
                     + (f'<p class="stmt-sub">{s["sub"]}</p>' if s.get("sub") else "") + "</div>")
            return f'<section {attrs}>{inner}{foot}{info}</section>'
        head = ((f'<p class="kicker">{s["kicker"]}</p>' if s.get("kicker") else "")
                + f'<h2{_ta(s.get("title_tip"))}>{s["title"]}</h2>' + (f'<p class="lede">{s["lede"]}</p>' if s.get("lede") else ""))
        return (f'<section {attrs}><div class="sl-in"><header class="sl-head">{head}</header>'
                f'<div class="sl-body">{s["body"]}</div></div>{foot}{info}</section>')

    def _sources_slide(self):
        sec_items = "".join(f"<li>{s}</li>" for s in self.sources)
        idt = vk.load_identity()
        gh = idt.get("github") or {}
        prov = (f'{self._ui("script")} <code>{esc(self.script)}</code> · ' if self.script else "") + esc(built_at())
        ghl = (f' · <a href="{esc(gh["url"])}" target="_blank" rel="noopener">{esc(gh.get("label", gh["url"]))}</a>' if gh.get("url") else "")
        body = (f'<ul class="srcs">{sec_items}</ul>'
                + (f'<p class="prov">{self.footer_note}</p>' if self.footer_note else "")
                + f'<p class="prov">{self._ui("made")} {esc(self.author)}{", " + esc(self.affiliation) if self.affiliation else ""} · {prov}{ghl}</p>')
        return dict(kind="content", id="sources", title=self._ui("sources_title"), body=body, info=None,
                    source="", sec=len(self.sections) - 1, kicker=None, lede=None)

    def render_body(self, meta) -> str:
        slides = list(self.slides)
        if self.sources_slide and (self.sources or self.script):
            slides.append(self._sources_slide())
        ids = [s["id"] for s in slides]
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            raise ValueError(f"deckkit: slide ids used twice: {sorted(dup)}")
        secs = []
        for k, sec in enumerate(self.sections):
            members = [j for j, s in enumerate(slides) if s["sec"] == k]
            if members:
                secs.append({"name": sec["name"], "color": sec["color"], "start": members[0], "n": len(members)})
        order = [j for k in range(len(self.sections)) for j, s in enumerate(slides) if s["sec"] == k]
        if order != list(range(len(slides))):
            raise ValueError("deckkit: slides must be added section by section (a section's slides together)")
        self._check(slides)
        html_ = "".join(self._render_slide(s, meta) for s in slides)
        ui = json.dumps(UI.get(self.lang, UI["en"]), ensure_ascii=False)
        return (f'<div class="deck" data-lang="{esc(self.lang)}" data-title="{esc(self.title, quote=True)}" '
                f"data-sections='{esc(json.dumps(secs, ensure_ascii=False))}' data-ui='{esc(ui)}'>{html_}</div>"), [s["id"] for s in slides]

    def _check(self, slides):
        """Build-time checks (shoot_deck.py checks the rendered layout)."""
        for s in slides:
            h = s.get("body", "") + s.get("text", "") + str(s.get("info") or "")
            if re.search(r"cursor\s*:", h):
                raise ValueError(f"deckkit: slide {s['id']}: sets a cursor; the cursor never changes on hover (Carlo, 2026-09-28)")
            small = [int(m) for m in re.findall(r"font-size:\s*(\d+)px", h) if int(m) < 22]
            if small:
                print(f"deckkit: WARNING slide {s['id']}: text under 22 px ({sorted(set(small))}); it won't read on a projector")
            if s["kind"] == "content" and not s.get("title"):
                print(f"deckkit: WARNING slide {s['id']}: no title")
        bare = [s["id"] for s in slides if s["kind"] == "content" and s["id"] != "sources" and not s.get("info")]
        if bare:
            print(f"deckkit: note: no (i) note on {', '.join(bare)}; add info=(title, html) where a reader needs the method")

    def write(self, out_dir, *, previous=None, change: str = "", removed: dict | None = None) -> Path:
        """Write OUT_DIR/<slug of the title>.html. previous: the published deck (publish.py --pull) to keep its start
        date and change history; change: one line for the history ("Added the round-1 results"); removed: {slide id:
        why} for slides taken out."""
        return write_page(out_dir, self, previous=previous, change=change, removed=removed)


# ============================================================================ the page (one or more languages)
def _read_meta(previous):
    if not previous:
        return None
    p = Path(previous)
    if not p.is_file():
        print(f"deckkit: WARNING previous deck {p} not found; starting a new history")
        return None
    m = re.search(r'<script type="application/json" id="deck-meta">(.*?)</script>', p.read_text(encoding="utf-8"), re.S)
    return json.loads(m.group(1)) if m else None


def write_page(out_dir, *decks: Deck, previous=None, change: str = "", removed: dict | None = None) -> Path:
    """Write the deck page. Several decks = one page with a language switch (first = default), e.g.
    write_page(OUT, deck_es, deck_en): same slides in each language, so a slide number means the same slide."""
    main = decks[0]
    old = _read_meta(previous)
    now = vk.generated_iso()
    meta = {"title": main.title, "created": (old or {}).get("created", now), "updated": now,
            "updated_txt": built_at(), "history": list((old or {}).get("history", []))}
    bodies, ids = [], {}
    for d in decks:
        b, i = d.render_body(meta)
        bodies.append(b)
        ids[d.lang] = i
    entry = {"at": now, "change": change or ("First version" if not old else "Rebuilt")}
    if old:
        before, after = old.get("slides", {}).get(main.lang, []), ids[main.lang]
        add_, gone = [i for i in after if i not in before], [i for i in before if i not in after]
        if add_:
            entry["added"] = add_
        if gone:
            entry["removed"] = {i: (removed or {}).get(i, "") for i in gone}
            missing = [i for i in gone if not (removed or {}).get(i)]
            if missing:
                print(f"deckkit: WARNING slides removed without a reason: {missing} (pass removed={{id: why}})")
        if old.get("title") and old["title"] != main.title:
            print(f"deckkit: WARNING the title changed ({old['title']!r} -> {main.title!r}): that is a NEW link. "
                  "Keep the start date and wording to update the same deck.")
    meta["history"].append(entry)
    meta["slides"] = ids
    th = main.theme
    css = CSS.replace("__BG__", th["bg"]).replace("__ALT__", th["alt"]).replace("__CARD__", th["card"]) \
        .replace("__INK__", th["ink"]).replace("__MUTED__", th["muted"]).replace("__FAINT__", th["faint"]) \
        .replace("__LINE__", th["line"]).replace("__ACCENT__", th["accent"]).replace("__SERIF__", th["serif"]) \
        .replace("__SANS__", th["sans"])
    langs = [d.lang for d in decks]
    ui0 = UI.get(main.lang, UI["en"])
    lang_btn = (f'<button id="langBtn" aria-label="{esc(ui0["lang"])}">{" | ".join(l.upper() for l in langs)}</button>'
                if len(decks) > 1 else "")
    desc = re.sub(r"<[^>]+>", "", main.subtitle)
    meta_json = json.dumps(meta, ensure_ascii=False).replace("</", "<\\/")
    page = (f'<!doctype html>\n<!-- generated {now} by deckkit ({_SKILL.name}){" from " + main.script if main.script else ""} -->\n'
            f'<html lang="{esc(main.lang)}">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{esc(main.title)}</title>\n'
            f'<meta name="description" content="{esc(desc, quote=True)}">\n<meta name="generated" content="{now}">'
            f'{vk.head_icon_tags(main.title, desc)}\n'
            f'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            f'<link rel="stylesheet" href="{th["fonts"]}" media="print" onload="this.media=\'all\'">\n<style>{css}</style>\n</head>\n<body>\n'
            f'<div id="stage"><div id="frame">{"".join(bodies)}</div></div>\n'
            f'<div id="toc" hidden></div>\n'
            f'<nav id="bar" aria-label="Slide controls"><button id="prev">&#8592;</button><span id="count">1 / 1</span>'
            f'<button id="next">&#8594;</button><span id="title"></span>{lang_btn}'
            f'<button id="tocBtn"></button>'
            f'<button id="pdfBtn"></button><button id="fsBtn">&#x26F6;</button></nav>\n'
            f'<script type="application/json" id="deck-meta">{meta_json}</script>\n'
            f'<script>{JS}</script>\n</body>\n</html>\n')
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{slug(main.title)}.html"
    dest.write_text(page, encoding="utf-8")
    n = len(ids[main.lang])
    print(f"deckkit: wrote {dest} ({len(page) / 1e6:.1f} MB, {n} slides, {len(main.sections)} sections, languages {', '.join(langs)})")
    return dest


# ============================================================================ icons (24-unit line drawings)
ICONS = {
    "satellite": '<path d="M13 7 9 3 5 7l4 4"/><path d="m17 11 4 4-4 4-4-4"/><path d="m8 12 4 4 6-6-4-4Z"/><path d="m16 8 3-3"/><path d="M9 21a6 6 0 0 0-6-6"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "home": '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M10 21v-6h4v6"/>',
    "layers": '<path d="m12 2 10 5-10 5L2 7Z"/><path d="m2 12 10 5 10-5"/><path d="m2 17 10 5 10-5"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1" fill="COL"/>',
    "flame": '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.4-.5-2-1-3-1.1-2.1-.2-4 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.2.4-2.3 1-3.3.3 1.6 1.4 2.8 2.5 2.8Z"/>',
    "network": '<path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M12 5v13"/>',
    "tree": '<circle cx="12" cy="4" r="2"/><circle cx="6" cy="13" r="2"/><circle cx="18" cy="13" r="2"/><circle cx="3.5" cy="20.5" r="1.5"/><circle cx="8.5" cy="20.5" r="1.5"/><path d="M10.6 5.4 7.2 11.4M13.4 5.4l3.4 6M5.2 14.8 4 19M6.8 14.8 8 19"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-5-5L5 21"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5M3 12c0 1.7 4 3 9 3s9-1.3 9-3"/>',
    "scan": '<path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2"/><rect x="8" y="8" width="8" height="8" rx="1"/>',
    "listcheck": '<path d="M11 6h10M11 12h10M11 18h10"/><path d="m3 6 1.5 1.5L7 5M3 12l1.5 1.5L7 11M3 18l1.5 1.5L7 17"/>',
    "tag": '<path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8Z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "scale": '<path d="M12 3v18M7 21h10M5 7h14M5 7l-3 7a3.5 3.5 0 0 0 6 0Zm14 0-3 7a3.5 3.5 0 0 0 6 0Z"/>',
    "bands": '<path d="M4 20V10M8 20V6M12 20V12M16 20V4M20 20V8"/>',
    "wave": '<path d="M2 12c2-4 4-4 6 0s4 4 6 0 4-4 6 0 2 2 2 2"/>',
    "houses": '<path d="M2 21v-6l4-3.2 4 3.2v6Z"/><path d="M14 21v-6l4-3.2 4 3.2v6Z"/><path d="M8 11V7.5L12 4.3l4 3.2V11"/>',
    "check": '<circle cx="12" cy="12" r="10"/><path d="m8 12 3 3 5-6"/>',
    "cross": '<circle cx="12" cy="12" r="10"/><path d="m9 9 6 6M15 9l-6 6"/>',
    "alert": '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
    "map": '<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3Z"/><path d="M9 3v15M15 6v15"/>',
    "people": '<circle cx="9" cy="7" r="4"/><path d="M2 21v-2a7 7 0 0 1 14 0v2"/><path d="M16 3.1a4 4 0 0 1 0 7.8M22 21v-2a7 7 0 0 0-4-6.3"/>',
    "drop": '<path d="M12 2.7 6.3 9.4a7 7 0 1 0 11.4 0Z"/>',
    "wind": '<path d="M17.7 7.7A2.5 2.5 0 1 1 19.5 12H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "ruler": '<path d="M21.3 15.3 8.7 2.7a1 1 0 0 0-1.4 0L2.7 7.3a1 1 0 0 0 0 1.4l12.6 12.6a1 1 0 0 0 1.4 0l4.6-4.6a1 1 0 0 0 0-1.4Z"/><path d="m7.5 10.5 2-2M10.5 13.5l2-2M13.5 16.5l2-2"/>',
    "code": '<path d="m16 18 6-6-6-6M8 6l-6 6 6 6"/>',
    "arrow": '<path d="M4 12h16M14 6l6 6-6 6"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5Z"/><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/>',
}


# ============================================================================ page CSS
CSS = r"""
:root{--bg:__BG__;--alt:__ALT__;--card:__CARD__;--ink:__INK__;--muted:__MUTED__;--faint:__FAINT__;--line:__LINE__;
  --accent:__ACCENT__;--serif:__SERIF__;--sans:__SANS__;--glow:#E8A06F}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{background:#0E1418;color:var(--ink);font-family:var(--sans);overflow:hidden;-webkit-font-smoothing:antialiased}
#stage{position:fixed;inset:0 0 56px 0;display:flex;align-items:center;justify-content:center;overflow:hidden}
#frame{position:relative;width:1920px;height:1080px;flex:none;transform-origin:center center;box-shadow:0 10px 40px rgba(0,0,0,.5)}
.deck[hidden]{display:none}
.slide{position:absolute;inset:0;width:1920px;height:1080px;overflow:hidden;display:none;background:var(--bg);color:var(--ink);font-family:var(--sans)}
.slide.on{display:block}
.slide.dark{color:#F1EEE6}
/* the cursor never changes on hover (Carlo, 2026-09-28 and 2026-10-23): only real links get the hand */
.slide,.slide *{cursor:default}
.slide a,.slide a *{cursor:pointer}
.slide p,.slide h1,.slide h2,.slide h3,.slide ul,.slide figure{margin:0}
.slide aside,.slide template{display:none!important}
.sl-in{position:absolute;left:128px;top:116px;width:1664px;height:808px;display:flex;flex-direction:column;gap:22px}
.sl-head h2{font:600 70px/1.08 var(--serif);letter-spacing:-.01em}
.sl-head .lede{font-size:32px;line-height:1.38;color:var(--muted);margin-top:12px;max-width:1560px}
.slide.dark .sl-head .lede{color:#C9CFCF}
.kicker{font:700 24px/1.1 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--sec);margin-bottom:10px}
.sl-body{flex:1;min-height:0;display:flex;flex-direction:column;gap:24px}
/* blocks keep their size: a slide with too much on it overflows visibly (and shoot_deck.py flags it), never shrinks a chart */
.sl-body>*,.col>*,.cell>*{flex-shrink:0}
.slide svg.chart{flex:none;overflow:visible}
.sl-foot{position:absolute;left:128px;bottom:44px;width:1440px;font-size:22px;line-height:1.35;color:var(--faint)}
.slide.dark .sl-foot{color:#9AA5A8}
.slide a{color:inherit;text-decoration:underline;text-underline-offset:4px}
.bul{padding-left:1.1em}
.bul li::marker{color:var(--sec)}
.row>.cell{justify-content:flex-start}
.card h3{font-weight:600}
.num p{margin:0}
.pill{display:inline-flex;align-items:center;border-radius:999px;font-weight:700;white-space:nowrap;line-height:1;vertical-align:middle}
.term{border-bottom:2px dotted currentColor;padding-bottom:1px}
.key{display:flex;flex-wrap:wrap;gap:12px 28px;align-items:center;background:var(--alt);border:2px solid var(--line);border-radius:12px;padding:14px 22px;color:var(--ink)}
.key .ktitle{font-size:22px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.kitem{display:inline-flex;gap:12px;align-items:center}
.kitem[data-toggle]{padding:4px 10px;border-radius:8px;border:2px solid transparent}
.kitem[data-toggle].off{opacity:.38}
.steps{display:flex;gap:18px;align-items:stretch}
.step{flex:1;min-width:0;display:flex;flex-direction:column;gap:14px}
.steps .arrow{display:flex;align-items:center;flex:none}
.bracket{position:relative}
.bracket .links{position:absolute;inset:0}
.bbox{position:absolute;border-radius:12px;padding:14px 18px;display:flex;flex-direction:column;gap:6px;justify-content:center;overflow:hidden}
.tabs{display:flex;flex-direction:column;gap:14px;min-height:0}
.tabbar{display:flex;gap:10px}
.tab{font:600 24px var(--sans);color:var(--muted);background:#E3E0D6;border:2px solid transparent;border-radius:10px;padding:10px 22px}
.tab.on{background:#FFFFFF;color:var(--ink);border-color:var(--sec)}
.pane[hidden]{display:none}
.lbtn{display:inline-flex;gap:12px;align-items:center;border:3px solid;border-radius:12px;padding:10px 20px;font-size:26px;font-weight:600;text-decoration:none!important;align-self:flex-start;background:#FFFFFF}
.pic{position:relative;overflow:hidden;flex:none}
.pic img{display:block}
.pic .over{position:absolute;inset:0}
.pic .cap{position:absolute;left:0;right:0;bottom:0;padding:10px 16px;font-size:22px;background:rgba(23,32,38,.72);color:#F4F2EC}
.livemap{border:0;border-radius:12px;display:block}
.tbl{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
.tbl th{font-weight:600;text-align:left;border-bottom:3px solid var(--ink);padding:10px 16px}
.tbl td{border-bottom:1px solid var(--line);padding:10px 16px}
.tbl .n{text-align:right}
.chart text{fill:currentColor;font-family:var(--sans)}
.chart .tick{fill:var(--faint)}
.slide.dark .chart .tick{fill:#9AA5A8}
.hbar{position:relative;display:flex;flex-direction:column}
.hrow{display:flex;align-items:center}
.hl{flex:none;line-height:1.2}
.tracks{display:flex;flex-direction:column;flex:1;min-width:0}
.hb{display:flex;align-items:center;gap:14px}
.hb .bar{height:100%;border-radius:0 6px 6px 0;transition:transform .16s ease,filter .16s ease}
.hb:hover .bar{filter:brightness(1.08) saturate(1.1) drop-shadow(0 0 3px rgba(232,160,111,.95))}
.hb .val{font-weight:600;font-variant-numeric:tabular-nums;white-space:nowrap}
.hb .val small{font-weight:400;color:var(--muted);font-size:.85em}
.hbar .ref{position:absolute;top:-34px;bottom:-6px;border-left:3px dashed var(--muted);z-index:1}
.hbar .ref span{position:absolute;top:0;left:8px;font-size:22px;color:var(--muted);white-space:nowrap}
.waffle{display:grid}
.waffle i{display:block;width:var(--c);height:var(--c);border-radius:4px;transition:transform .12s,filter .12s}
.waffle i[data-tip]:hover{transform:scale(1.25);filter:brightness(1.12)}
/* cover and statement slides */
.cover-img{position:absolute;right:0;top:0;width:760px;height:1080px;object-fit:cover}
.cover-in{position:absolute;left:128px;top:250px;width:1180px;display:flex;flex-direction:column;gap:30px}
.cover-in h1{font:600 100px/1.04 var(--serif);letter-spacing:-.015em}
.cover-sub{font-size:34px;line-height:1.4;color:var(--muted)}
.byline{font-size:26px;color:var(--muted)}
.cover-logos{position:absolute;left:128px;bottom:72px;display:flex;gap:48px;align-items:center}
.cover-logos .org{display:flex;gap:14px;align-items:center;text-decoration:none!important;color:var(--ink)}
.cover-logos .logo{height:60px;width:auto}
.cover-logos span{display:flex;flex-direction:column;font-size:22px;line-height:1.25}
.cover-logos small{font-size:22px;color:var(--muted);max-width:380px}
.stmt{position:absolute;left:160px;top:0;bottom:0;width:1560px;display:flex;flex-direction:column;justify-content:center;gap:30px}
.stmt h2{font:600 88px/1.12 var(--serif);letter-spacing:-.01em}
.stmt .kicker{color:#F1EEE6;opacity:.75}
.stmt-sub{font-size:34px;line-height:1.4;opacity:.85;max-width:1400px}
.srcs{font-size:24px;line-height:1.45;padding-left:1.1em;display:flex;flex-direction:column;gap:10px}
.prov{font-size:22px;color:var(--muted)}
.prov code{font-size:22px}
/* progress strip (top of every slide): sections in their colours, one pill per slide */
.strip{position:absolute;left:128px;top:24px;width:1480px;height:56px;display:flex;gap:26px}
.strip .grp{display:flex;flex-direction:column;gap:8px;min-width:0}
.strip .gname{font:600 16px/24px var(--sans);letter-spacing:.5px;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.strip .grp.cur .gname{font-size:22px;font-weight:700}
.strip .pills{display:flex;gap:6px;align-items:center;height:16px}
.strip .pills i{flex:1;height:8px;border-radius:4px;display:block}
.strip .pills i.at{height:16px}
.count{position:absolute;left:1640px;top:40px;width:152px;font-size:26px;text-align:right;font-variant-numeric:tabular-nums;color:#6A737C}
.slide.dark .count{color:#9AA5A8}
/* (i) at the bottom right of every slide; the Plain | Technical switch beside it */
.info{position:absolute;left:1836px;top:996px;width:48px;height:48px;border-radius:50%;border:3px solid var(--accent);color:var(--accent);
  display:flex;align-items:center;justify-content:center;font:700 30px/1 var(--serif);background:#FFFFFF;z-index:5;box-shadow:0 2px 8px rgba(0,0,0,.15)}
.slide.dark .info{border-color:var(--glow);color:var(--glow);background:#22303A}
.mode{position:absolute;right:112px;top:1000px;display:flex;border:2px solid var(--line);border-radius:999px;overflow:hidden;background:#FFFFFF;z-index:5}
.mode button{font:600 18px var(--sans);border:0;background:none;padding:8px 16px;color:var(--muted)}
.mode button.on{background:var(--ink);color:#FFFFFF}
.slide .tech{display:none}
.slide[data-mode="tech"] .tech{display:revert}
.slide[data-mode="tech"] .plain{display:none}
/* hover: a clear, satisfying highlight on whatever has a tip (Carlo, 2026-09-28); the cursor stays the same */
.slide [data-tip],.slide [data-info],.strip i,.strip .gname,.kitem[data-toggle],.tab{transition:transform .16s ease,box-shadow .16s ease,filter .16s ease,background .16s ease}
.slide div[data-tip]:hover,.slide figure[data-tip]:hover,.slide p[data-tip]:hover,.slide td[data-tip]:hover,.slide th[data-tip]:hover,.kitem:hover,.tab:hover{
  box-shadow:0 0 0 3px rgba(232,160,111,.85),0 12px 26px rgba(0,0,0,.16);filter:brightness(1.05) saturate(1.08);border-radius:10px;position:relative;z-index:4}
.slide .card[data-tip]:hover,.slide .step[data-tip]:hover,.slide .num[data-tip]:hover,.slide .bbox[data-tip]:hover{transform:translateY(-3px) scale(1.015)}
.slide .hb[data-tip]:hover .bar{transform:scaleY(1.12)}
.slide .hb[data-tip]:hover{box-shadow:none!important;filter:none!important}
.slide svg [data-tip]:hover,.slide svg[data-tip]:hover{filter:brightness(1.12) saturate(1.15) drop-shadow(0 0 3px rgba(232,160,111,.95))}
.slide .term:hover,.slide h2[data-tip]:hover{background:rgba(232,160,111,.28);border-radius:4px}
.info:hover{transform:scale(1.12);box-shadow:0 0 0 6px rgba(232,160,111,.35)}
.strip i:hover{filter:brightness(1.15);transform:scaleY(1.4)}
#tip{position:fixed;z-index:50;max-width:400px;background:#172026;color:#F4F2EC;border:1px solid #3A4650;border-radius:12px;padding:14px 16px;
  font:15px/1.5 var(--sans);box-shadow:0 12px 32px rgba(0,0,0,.35);pointer-events:none;opacity:0;transform:translateY(4px);transition:opacity .12s,transform .12s}
#tip.show{opacity:1;transform:none}
#tip.wide{max-width:560px}
#tip b.t{display:block;color:#E8A06F;font-size:13px;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px}
#tip p{margin:0 0 6px}
#tip p.sugg{color:#CFE3C7}
#bar{position:fixed;left:0;right:0;bottom:0;height:56px;background:#172026;display:flex;align-items:center;gap:10px;padding:0 14px;border-top:1px solid #2A363E;color:#EDEAE2}
#bar button{background:#22303A;color:#EDEAE2;border:1px solid #3A4650;border-radius:8px;height:38px;min-width:44px;padding:0 12px;font:500 15px var(--sans)}
#bar button:hover{border-color:#C4502B}
#count{font:500 15px var(--sans);color:#8A969C;font-variant-numeric:tabular-nums;min-width:64px;text-align:center}
#title{flex:1;font:500 15px var(--sans);color:#8A969C;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#toc{position:fixed;inset:0 0 56px 0;background:rgba(14,20,24,.96);color:#EDEAE2;overflow:auto;padding:40px 6vw;z-index:30;font:16px/1.5 var(--sans)}
#toc h2{font:600 30px/1.2 var(--serif);margin:0 0 6px}
#toc .by{color:#8A969C;margin:0 0 26px}
#toc .sec{margin:0 0 22px}
#toc .sec b{display:block;font-size:13px;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px}
#toc ol{margin:0;padding-left:2.2em}
#toc li a{color:#EDEAE2;text-decoration:none}
#toc li a:hover{text-decoration:underline}
#toc li.at a{font-weight:700}
#toc .hist{border-top:1px solid #2A363E;margin-top:24px;padding-top:16px;color:#AEB7BA}
#toc .hist li{margin-bottom:4px}
@media (max-width:640px){#title{display:none}#bar{gap:6px;padding:0 6px}#bar button{padding:0 8px;min-width:36px}}
@media print{
  @page{size:1920px 1080px;margin:0}
  body{overflow:visible;background:#fff}
  #bar,#toc,#tip{display:none!important}
  #stage{position:static;display:block}
  #frame{transform:none!important;box-shadow:none;width:auto;height:auto}
  .deck:not(.active){display:none!important}
  .slide{position:relative;display:block!important;page-break-after:always;break-after:page}
  .info,.mode{display:none!important}
}
"""

# ============================================================================ page JS
JS = r"""
(function(){
var decks=[].slice.call(document.querySelectorAll('.deck'));
var meta=JSON.parse(document.getElementById('deck-meta').textContent);
var frame=document.getElementById('frame'),stage=document.getElementById('stage');
var count=document.getElementById('count'),toc=document.getElementById('toc');
var deck,slides,UI,secs,i=0;
function hex(c){c=c.replace('#','');return [0,2,4].map(function(k){return parseInt(c.substr(k,2),16);});}
function mix(c,bg,t){var a=hex(c),b=hex(bg);return '#'+a.map(function(x,k){var v=Math.round(x*t+b[k]*(1-t));return (v<16?'0':'')+v.toString(16);}).join('');}
function el(tag,cls,txt){var e=document.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e;}
// ---- progress strip + counter + (i) + Plain|Technical on every slide (built once, so printing keeps them)
decks.forEach(function(d){
  var S=JSON.parse(d.getAttribute('data-sections')),U=JSON.parse(d.getAttribute('data-ui'));
  var sl=[].slice.call(d.querySelectorAll('.slide')),n=sl.length;
  sl.forEach(function(s,k){
    var bg=s.getAttribute('data-bg')||'#F4F2EC',dark=s.classList.contains('dark');
    var cur=0;S.forEach(function(g,j){if(k>=g.start&&k<g.start+g.n)cur=j;});
    var strip=el('div','strip');
    S.forEach(function(g,j){
      var full=dark?mix(g.color,'#FFFFFF',0.7):g.color;
      var grp=el('div','grp'+(j===cur?' cur':''));grp.style.flex=Math.max(g.n,j===cur?8:5);
      var nm=el('p','gname',g.name);nm.style.color=j===cur?full:mix(full,bg,0.5);nm.setAttribute('data-go',g.start);
      nm.setAttribute('data-tip',g.name+'\n'+(g.start+1)+'–'+(g.start+g.n)+' / '+n);
      var pills=el('div','pills');
      for(var q=0;q<g.n;q++){
        var gi=g.start+q,p=el('i'),c;
        if(j===cur){c=gi<=k?full:mix(full,bg,0.28);if(gi===k)p.className='at';}
        else if(j<cur){c=mix(full,bg,0.55);}else{c=mix(full,bg,0.22);}
        p.style.background=c;p.setAttribute('data-go',gi);
        p.setAttribute('data-tip',(gi+1)+' / '+n+'\n'+(sl[gi].getAttribute('data-title')||''));
        pills.appendChild(p);
      }
      grp.appendChild(nm);grp.appendChild(pills);strip.appendChild(grp);
    });
    s.insertBefore(strip,s.firstChild);
    var c=el('p','count',(k+1)+' / '+n);s.appendChild(c);
    if(s.querySelector('template.sl-info')){var b=el('div','info','i');b.setAttribute('data-info','1');b.setAttribute('aria-label',U.about);s.appendChild(b);}
    var h=s.innerHTML;
    if(h.indexOf('@@tech')>=0||s.querySelector('.tech')){
      var m=el('div','mode');var b1=el('button','on',U.plain),b2=el('button','',U.tech);
      b1.setAttribute('data-mode','plain');b2.setAttribute('data-mode','tech');m.appendChild(b1);m.appendChild(b2);s.appendChild(m);
    }
  });
});
function fit(){var w=stage.clientWidth,h=stage.clientHeight;frame.style.transform='scale('+Math.min(w/1920,h/1080)+')';}
function setDeck(k,keep){
  decks.forEach(function(d,j){d.hidden=j!==k;d.classList.toggle('active',j===k);});
  deck=decks[k];slides=[].slice.call(deck.querySelectorAll('.slide'));
  UI=JSON.parse(deck.getAttribute('data-ui'));secs=JSON.parse(deck.getAttribute('data-sections'));
  document.documentElement.lang=deck.getAttribute('data-lang');
  document.getElementById('title').textContent=deck.getAttribute('data-title')+' · '+UI.hint;
  document.getElementById('tocBtn').textContent=UI.contents;
  document.getElementById('pdfBtn').textContent=UI.pdf;document.getElementById('fsBtn').title=UI.full;
  document.getElementById('prev').title=UI.prev;document.getElementById('next').title=UI.next;
  var lb=document.getElementById('langBtn');
  if(lb){lb.innerHTML=decks.map(function(d,j){var l=d.getAttribute('data-lang').toUpperCase();return j===k?'<b>'+l+'</b>':l;}).join(' | ');}
  buildToc();show(keep?i:0);
}
function show(n){
  i=Math.max(0,Math.min(slides.length-1,n));
  slides.forEach(function(s,j){s.classList.toggle('on',j===i);});
  count.textContent=(i+1)+' / '+slides.length;
  var h='#'+(i+1);if(location.hash!==h)history.replaceState(null,'',location.pathname+location.search+h);
  [].forEach.call(toc.querySelectorAll('li'),function(li){li.classList.toggle('at',+li.getAttribute('data-n')===i);});
  hide();
}
function buildToc(){
  toc.innerHTML='';
  toc.appendChild(el('h2','',deck.getAttribute('data-title')));
  toc.appendChild(el('p','by',UI.started+' '+meta.created.slice(0,10)+' · '+UI.updated+' '+meta.updated_txt));
  secs.forEach(function(g){
    var sec=el('div','sec'),b=el('b','',g.name);b.style.color=mix(g.color,'#FFFFFF',0.7);sec.appendChild(b);
    var ol=el('ol');ol.start=g.start+1;
    for(var q=0;q<g.n;q++){var li=el('li'),a=el('a','',slides[g.start+q].getAttribute('data-title'));a.href='#'+(g.start+q+1);
      li.setAttribute('data-n',g.start+q);li.appendChild(a);ol.appendChild(li);}
    sec.appendChild(ol);toc.appendChild(sec);
  });
  var hs=el('div','hist');hs.appendChild(el('b','',UI.changes));var ul=el('ul');
  meta.history.slice().reverse().forEach(function(e){
    var t=e.at.slice(0,16).replace('T',' ')+' · '+e.change;
    if(e.added)t+=' (+'+e.added.join(', ')+')';
    if(e.removed)t+=' (−'+Object.keys(e.removed).map(function(k){return k+(e.removed[k]?': '+e.removed[k]:'');}).join('; ')+')';
    ul.appendChild(el('li','',t));
  });
  hs.appendChild(ul);toc.appendChild(hs);
}
function toggleToc(){toc.hidden=!toc.hidden;}
function fullscreen(){if(!document.fullscreenElement){(document.documentElement.requestFullscreen||function(){}).call(document.documentElement);}else{document.exitFullscreen();}}
function setMode(s,m){s.setAttribute('data-mode',m);[].forEach.call(s.querySelectorAll('.mode button'),function(b){b.classList.toggle('on',b.getAttribute('data-mode')===m);});}
document.getElementById('prev').onclick=function(){show(i-1);};
document.getElementById('next').onclick=function(){show(i+1);};
document.getElementById('tocBtn').onclick=toggleToc;
document.getElementById('pdfBtn').onclick=function(){window.print();};
document.getElementById('fsBtn').onclick=fullscreen;
var lb=document.getElementById('langBtn');
if(lb)lb.onclick=function(){var k=(decks.indexOf(deck)+1)%decks.length;setDeck(k,true);
  var u=new URL(location.href);u.searchParams.set('lang',deck.getAttribute('data-lang'));history.replaceState(null,'',u.pathname+u.search+location.hash);};
toc.addEventListener('click',function(e){var a=e.target.closest('a');if(a){e.preventDefault();show(+a.getAttribute('href').slice(1)-1);toc.hidden=true;}});
document.addEventListener('keydown',function(e){
  if(e.target&&/INPUT|TEXTAREA|SELECT/.test(e.target.tagName))return;
  if(e.key==='ArrowRight'||e.key==='PageDown'||e.key===' '){e.preventDefault();show(i+1);}
  else if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();show(i-1);}
  else if(e.key==='Home')show(0);else if(e.key==='End')show(slides.length-1);
  else if(e.key==='o'||e.key==='O')toggleToc();
  else if(e.key==='f'||e.key==='F')fullscreen();
  else if(e.key==='t'||e.key==='T'){var s=slides[i];if(s.querySelector('.mode'))setMode(s,s.getAttribute('data-mode')==='tech'?'plain':'tech');}
  else if(e.key==='Escape'){toc.hidden=true;hide();}
});
var x0=null;
stage.addEventListener('touchstart',function(e){x0=e.touches[0].clientX;},{passive:true});
stage.addEventListener('touchend',function(e){if(x0===null)return;var dx=e.changedTouches[0].clientX-x0;x0=null;if(Math.abs(dx)>50)show(dx<0?i+1:i-1);});
window.addEventListener('resize',fit);
window.addEventListener('hashchange',function(){var n=parseInt(location.hash.slice(1),10);if(n)show(n-1);});
// ---- tips: every [data-tip] and the (i); plain or technical by the slide's switch
var tip=el('div');tip.id='tip';document.body.appendChild(tip);var cur=null;
function fill(elm){
  tip.innerHTML='';var s=elm.closest('.slide'),tech=s&&s.getAttribute('data-mode')==='tech';
  if(elm.hasAttribute('data-info')){
    tip.classList.add('wide');var t=s.querySelector('template.sl-info').content.cloneNode(true);
    [].forEach.call(t.querySelectorAll(tech?'.plain':'.tech'),function(x){x.remove();});
    tip.appendChild(t);return;
  }
  tip.classList.remove('wide');
  var raw=elm.getAttribute('data-tip')||'',parts=raw.split('\n@@tech\n'),txt=(tech&&parts[1])?parts[1]:parts[0];
  txt.split('\n').forEach(function(line,k){
    if(k===0){tip.appendChild(el('b','t',line));return;}
    var p=el('p',/^(What it suggests|Qué sugiere|Lectura)/.test(line)?'sugg':'',line);tip.appendChild(p);
  });
}
function place(elm){
  var r=elm.getBoundingClientRect(),Wd=innerWidth,Hd=innerHeight-56,w=tip.offsetWidth,h=tip.offsetHeight,g=16,x,y;
  var cy=Math.max(8,Math.min(Hd-h-8,r.top+r.height/2-h/2));
  if(r.width<Wd*0.45&&r.right+g+w<Wd-8){x=r.right+g;y=cy;}
  else if(r.width<Wd*0.45&&r.left-g-w>8){x=r.left-g-w;y=cy;}
  else if(r.bottom+g+h<Hd){y=r.bottom+g;x=Math.max(8,Math.min(Wd-w-8,r.left));}
  else{y=Math.max(8,r.top-g-h);x=Math.max(8,Math.min(Wd-w-8,r.left));}
  tip.style.left=x+'px';tip.style.top=y+'px';
}
function showTip(elm){cur=elm;fill(elm);tip.classList.add('show');place(elm);}
function hide(){cur=null;tip.classList.remove('show');}
document.addEventListener('mouseover',function(e){
  var t=e.target.closest&&e.target.closest('.deck [data-tip], .deck [data-info]');
  if(t&&t!==cur)showTip(t);else if(!t&&cur)hide();
});
document.addEventListener('focusin',function(e){var t=e.target.closest&&e.target.closest('[data-tip]');if(t)showTip(t);});
document.addEventListener('click',function(e){
  var t=e.target;
  if(t.closest('#bar')||t.closest('#toc'))return;
  if(t.closest('a')){e.stopPropagation();return;}
  var go=t.closest('[data-go]');if(go){show(+go.getAttribute('data-go'));e.stopPropagation();return;}
  var md=t.closest('.mode button');if(md){setMode(md.closest('.slide'),md.getAttribute('data-mode'));e.stopPropagation();hide();return;}
  var tb=t.closest('[data-tab]');
  if(tb){var box=tb.closest('.tabs'),k=tb.getAttribute('data-tab');
    [].forEach.call(box.querySelectorAll(':scope>.panes>.pane'),function(p){p.hidden=p.getAttribute('data-pane')!==k;});
    [].forEach.call(box.querySelectorAll(':scope>.tabbar>.tab'),function(b){b.classList.toggle('on',b===tb);});
    e.stopPropagation();hide();return;}
  var tg=t.closest('[data-toggle]');
  if(tg){var id=tg.getAttribute('data-toggle'),off=tg.classList.toggle('off');
    [].forEach.call(tg.closest('.slide').querySelectorAll('[data-layer="'+id+'"]'),function(g){g.style.display=off?'none':'';});
    e.stopPropagation();return;}
  var tt=t.closest('[data-tip], [data-info]');
  if(tt){e.stopPropagation();if(cur===tt)hide();else showTip(tt);return;}
  if(t.closest('.slide')){var r=stage.getBoundingClientRect();show(e.clientX-r.left<r.width/3?i-1:i+1);}
},true);
var q=new URLSearchParams(location.search),lk=0;
decks.forEach(function(d,j){if(d.getAttribute('data-lang')===q.get('lang'))lk=j;});
var n0=parseInt(location.hash.slice(1),10);     // read the slide asked for before setDeck rewrites the address
setDeck(lk);if(n0)show(n0-1);fit();requestAnimationFrame(fit);setTimeout(fit,150);window.addEventListener('load',fit);
})();
"""


if __name__ == "__main__":
    print(__doc__)
