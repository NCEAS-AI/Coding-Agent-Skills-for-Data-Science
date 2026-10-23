#!/usr/bin/env python3
"""Screenshot every slide of a deck and check its layout the way a reader would meet it.

WHY THIS EXISTS
    The structure-loss deck reached the owner with text running over the lines of a diagram, an (i) badge sitting
    on content, boxes cut off at the bottom, slides with a paragraph where a picture was wanted, tooltips that
    only repeated the label, and numbers nobody could trace (Carlo, 2026-09-28 to 2026-10-01). A Parafire deck
    reached him as a long scroll, too dense to present (2026-10-23). Each of those is measurable on the rendered
    slide, so this script measures them on every slide before anything is published, and saves a picture of each
    slide plus contact sheets to look at.

WHAT IT CHECKS, PER SLIDE (rendered at 1920 x 1080 in headless Chrome)
    ERROR  content outside the slide, or a box whose text is cut off (scrollHeight beyond its height)
    ERROR  two pieces of text overlapping, or text overlapping the (i) / Plain | Technical controls
    ERROR  content in the top band (the progress strip) or the bottom band (footer row)
    ERROR  JavaScript errors on the page
    WARN   more than 60 words of visible text (prose, not chart labels): split the slide or turn text into a picture
    WARN   text smaller than 22 px
    WARN   numbers in the text without a hover saying how they were calculated
    WARN   tips that repeat the text they sit on (a tip must add information or not exist)

USAGE (needs websocket-client and Chrome or Chromium, like the page skill's screenshot.py)
    shoot_deck.py DECK.html OUT_DIR [--slides 1,4,7-9] [--lang es] [--wait 6] [--per 0.5] [--no-sheet] [--phone]
    -> OUT_DIR/slide_01.png ... (1920 x 1080), OUT_DIR/sheet_1.png ... (12 slides each, for a quick look),
       a report on stdout. Exit status 1 when any ERROR was found.
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import tempfile
import time
import shutil
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import PAGES  # noqa: E402  (finds the page skill)

sys.path.insert(0, str(PAGES / "scripts"))
from screenshot import CHROME, Tab, free_port  # noqa: E402

WORDS_WARN, MIN_PX = 60, 22

CHECK_JS = r"""(() => {
const s = document.querySelector('.deck.active .slide.on'); if (!s) return {err: ['no slide shown']};
const R = s.getBoundingClientRect(), k = R.width / 1920;
const out = {errors: [], warns: [], words: 0, untipped: [], repeat: 0, small: []};
const name = e => (e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : '') +
  ' "' + (e.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40) + '"');
const vis = e => { const st = getComputedStyle(e); if (st.display === 'none' || st.visibility === 'hidden' || +st.opacity === 0) return false;
  const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
const inChrome = e => e.closest('.strip, .count, .info, .mode');
const all = [...s.querySelectorAll('*')].filter(e => !e.closest('template, aside, .pane[hidden]') && vis(e));
// 1. outside the slide / cut-off text
for (const e of all) {
  if (inChrome(e) || e.closest('svg') && e.tagName !== 'svg') continue;
  const r = e.getBoundingClientRect();
  const ox = Math.max(R.left - r.left, r.right - R.right), oy = Math.max(R.top - r.top, r.bottom - R.bottom);
  if ((ox > 2 || oy > 2) && !(e.parentElement && e.parentElement !== s && (() => { const p = e.parentElement.getBoundingClientRect();
        return Math.max(R.left - p.left, p.right - R.right, R.top - p.top, p.bottom - R.bottom) > 2; })()))
    out.errors.push('outside the slide by ' + Math.round(Math.max(ox, oy) / k) + ' px: ' + name(e));
  const st = getComputedStyle(e);
  if ((st.overflow === 'hidden' || st.overflowY === 'hidden') && e.scrollHeight > e.clientHeight + 3 && e.textContent.trim() && !e.closest('.pic, .livemap'))
    out.errors.push('text cut off at the bottom (' + Math.round((e.scrollHeight - e.clientHeight) / k) + ' px hidden): ' + name(e));
}
for (const c of s.querySelectorAll('svg.chart')) {      // a chart drawn smaller than it was built
  const r = c.getBoundingClientRect(), hw = +c.getAttribute('height');
  if (hw && r.height / k < hw - 2) out.errors.push('chart squeezed to ' + Math.round(r.height / k) + ' of ' + hw + ' px tall: split the slide or make the chart smaller');
}
// 2. text leaves: elements with their own text, plus SVG text
const leaves = all.filter(e => !inChrome(e) && ([...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) || e.tagName === 'text'))
  .filter(e => !(e.tagName !== 'text' && e.closest('svg')));
// glyph boxes of each leaf's own text (not its padding or underline), so a dotted-underlined term does not "touch" the next line
const rects = leaves.map(e => { if (e.tagName === 'text') return [e.getBoundingClientRect()];
  const rr = []; for (const n of e.childNodes) if (n.nodeType === 3 && n.textContent.trim()) { const g = document.createRange(); g.selectNodeContents(n); rr.push(...g.getClientRects()); }
  // a font's glyph box includes its built-in leading above and below the letters: trim 15% off each side
  return (rr.length ? rr : [e.getBoundingClientRect()]).map(r => ({left: r.left, right: r.right, top: r.top + r.height * .15, bottom: r.bottom - r.height * .15})); });
const area = (a, b) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
let ov = 0;
for (let a = 0; a < leaves.length && ov < 6; a++) for (let b = a + 1; b < leaves.length && ov < 6; b++) {
  if (leaves[a].contains(leaves[b]) || leaves[b].contains(leaves[a])) continue;
  let hit = 0; for (const ra of rects[a]) for (const rb of rects[b]) hit = Math.max(hit, area(ra, rb));
  if (hit / (k * k) > 40) { out.errors.push('text overlaps text: ' + name(leaves[a]) + ' / ' + name(leaves[b])); ov++; }
}
const ctl = [...s.querySelectorAll('.info, .mode')].map(e => e.getBoundingClientRect());
for (let a = 0; a < leaves.length; a++) for (const c of ctl) for (const ra of rects[a])
  if (area(ra, c) / (k * k) > 20 && !leaves[a].closest('.sl-foot')) { out.errors.push('content under the (i) / switch: ' + name(leaves[a])); break; }
for (let a = 0; a < leaves.length; a++) {
  const r = leaves[a].getBoundingClientRect(), top = (r.top - R.top) / k, bot = (r.bottom - R.top) / k;
  const isFoot = leaves[a].closest('.sl-foot, .cover-logos, .cover-img, .stmt');
  if (top < 92 && !isFoot) out.errors.push('content in the progress-strip band (top ' + Math.round(top) + ' px): ' + name(leaves[a]));
  if (bot > 1000 && !isFoot) out.errors.push('content in the footer band (bottom ' + Math.round(bot) + ' px): ' + name(leaves[a]));
}
// 3. words, small text, numbers without tips, tips that repeat their text
const prose = leaves.filter(e => !e.closest('svg, .chart, .hbar, .tbl, .key, .sl-foot, .count, .strip, .cover-logos, .srcs, .prov'));
out.words = prose.map(e => [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join(' '))
  .join(' ').split(/\s+/).filter(w => /[A-Za-zÀ-ÿ0-9]/.test(w)).length;
for (const e of leaves) { const px = parseFloat(getComputedStyle(e).fontSize) ; if (px < 21.5 && !e.closest('.strip')) out.small.push(Math.round(px) + 'px ' + name(e)); }
const numRe = /\d[\d,.]*\s*%?/;
for (const e of leaves) {
  if (e.closest('[data-tip], .sl-foot, .count, .strip, .tick, .cover-in, .srcs, .prov, .key')) continue;
  const td = e.closest('td');           // a table number is explained by a tip on its column heading
  if (td) { const th = td.closest('table').querySelectorAll('th')[td.cellIndex]; if (th && th.hasAttribute('data-tip')) continue; }
  const own = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join(' ');
  const m = own.match(/(?<![A-Za-z])\d[\d,.]*%?/g);
  if (m && m.some(x => x.replace(/[^0-9]/g, '').length >= 2 && !/^(19|20)\d\d$/.test(x))) out.untipped.push(name(e));
}
const toks = t => new Set((t.toLowerCase().match(/[a-zà-ÿ]{3,}/g) || []).filter(w => !['the','and','for','with','from','that','this','are','was','its','per','not','but','has','one','two','los','las','del','que','con','por','una'].includes(w)));
for (const e of s.querySelectorAll('[data-tip]')) {
  if (e.closest('.strip')) continue;
  const raw = (e.getAttribute('data-tip') || '').split('\n@@tech\n')[0].split('\n').slice(1).join(' ');
  const b = toks(raw), v = toks(e.textContent || ''); if (!b.size) { out.repeat++; continue; }
  let hit = 0; b.forEach(w => { if (v.has(w)) hit++; }); if (hit / b.size >= 0.7) out.repeat++;
}
out.title = s.getAttribute('data-title'); out.id = s.getAttribute('data-id');
return out; })()"""


FONT_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36")


def inline_font_css(href: str) -> str:
    """The Google Fonts stylesheet at href with its latin font files inlined (cached), or "" if it can't be fetched."""
    import hashlib
    import re
    cache = Path.home() / ".cache" / Path(__file__).resolve().parents[1].name / "fonts"
    cache.mkdir(parents=True, exist_ok=True)

    def get(url):
        f = cache / hashlib.sha1(url.encode()).hexdigest()
        if not f.is_file():
            req = urllib.request.Request(url, headers={"User-Agent": FONT_UA})
            f.write_bytes(urllib.request.urlopen(req, timeout=30).read())
        return f.read_bytes()
    try:
        css = get(href).decode()
        blocks = re.findall(r"/\* ([\w-]+) \*/\s*(@font-face\s*\{[^}]*\})", css)
        out = []
        for subset, block in blocks:
            if subset not in ("latin", "latin-ext"):
                continue
            for u in re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", block):
                block = block.replace(u, "data:font/woff2;base64," + base64.b64encode(get(u)).decode())
            out.append(block)
        return "\n".join(out)
    except Exception as e:                                   # noqa: BLE001 - fall back to the page's own loading
        print(f"WARN could not fetch fonts ({e}); the pictures may use fallback fonts")
        return ""


def parse_slides(spec: str, n: int):
    if not spec:
        return list(range(1, n + 1))
    out = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return [x for x in out if 1 <= x <= n]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("out_dir")
    ap.add_argument("--slides", default="", help="which slides (1-based), e.g. 1,4,7-9; default all")
    ap.add_argument("--lang", default="", help="language of a multi-language deck (default: its first)")
    ap.add_argument("--wait", type=float, default=6.0, help="seconds to let the page (fonts, maps) settle first")
    ap.add_argument("--per", type=float, default=0.6, help="seconds per slide (maps get 4 s more)")
    ap.add_argument("--no-sheet", action="store_true")
    ap.add_argument("--phone", action="store_true", help="also capture slide 1 on a 390 px phone screen")
    a = ap.parse_args()
    if not CHROME:
        sys.exit("google-chrome not found (set CHROME=/path/to/chrome)")
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    url = a.deck if "://" in a.deck else Path(a.deck).resolve().as_uri()
    if a.lang:
        url += ("&" if "?" in url else "?") + "lang=" + a.lang
    port, prof = free_port(), tempfile.mkdtemp(prefix="deck_")
    proc = subprocess.Popen([CHROME, "--headless=new", "--no-sandbox", "--hide-scrollbars", "--mute-audio",
                             "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-first-run",
                             "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
                             "--disable-backgrounding-occluded-windows",
                             f"--remote-debugging-port={port}", f"--user-data-dir={prof}", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    n_err = 0
    shots = []
    try:
        for _ in range(100):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=2))
                ws_url = next(t["webSocketDebuggerUrl"] for t in tabs if t.get("type") == "page")
                break
            except Exception:
                time.sleep(0.2)
        else:
            sys.exit("Chrome did not start")
        tab = Tab(ws_url)
        for dom in ("Page", "Runtime", "Log"):
            tab.call(f"{dom}.enable")
        # 1920 x 1136: the stage is the window minus the 56 px control bar, so the slide renders at exactly 1:1
        tab.call("Emulation.setDeviceMetricsOverride", width=1920, height=1136, deviceScaleFactor=1, mobile=False)
        tab.call("Emulation.setFocusEmulationEnabled", enabled=True)
        # The first page load after Chrome starts is unreliable (the page skill's screenshot.py found the same): load
        # once to warm up, then again for real, and retry if the deck's script has not run.
        n = 0
        for attempt in range(3):
            tab.call("Page.navigate", url="about:blank")
            tab.pump(0.3)
            tab.call("Page.navigate", url=url)
            tab.pump(a.wait if attempt else 2.0)
            n = tab.call("Runtime.evaluate", expression="document.querySelectorAll('.deck.active .slide').length",
                         returnByValue=True)["result"].get("value", 0)
            if n and attempt:
                break
        tab.errors.clear()       # errors from the warm-up load are not this page's
        if not n:
            sys.exit("the deck's script did not run (no .deck.active): open it in a browser and check the console")
        # Fonts load without blocking the deck. Headless Chrome on some servers never finishes the Google Fonts request
        # (Aurora, 2026-10-23), so fetch the deck's fonts here and hand them to the page: the pictures and the layout
        # checks then use the real type, as a reader's browser does.
        links = tab.call("Runtime.evaluate", returnByValue=True,
                         expression="[...document.querySelectorAll('link[rel=stylesheet][href*=\"fonts.googleapis\"]')].map(l => l.href)")["result"].get("value") or []
        css = "".join(inline_font_css(h) for h in links)
        if css:
            tab.call("Runtime.evaluate", expression=f"document.head.insertAdjacentHTML('beforeend', {json.dumps('<style>' + css + '</style>')})")
        fonts_js = "document.fonts.status === 'loaded' && [...document.fonts].some(f => f.status === 'loaded')"
        for _ in range(int(a.wait * 4)):
            if not links or tab.call("Runtime.evaluate", expression=fonts_js, returnByValue=True)["result"].get("value"):
                break
            tab.pump(0.5)
        else:
            print("WARN web fonts did not load: the pictures use fallback fonts, so line breaks may differ from a browser")
        want = parse_slides(a.slides, n)
        print(f"{a.deck}: {n} slides; checking {len(want)}")
        for k in want:
            tab.call("Runtime.evaluate", expression=f"location.hash='#{k}'")
            has_map = tab.call("Runtime.evaluate", expression="!!document.querySelector('.deck.active .slide.on iframe')",
                               returnByValue=True)["result"].get("value")
            tab.pump(a.per + (4 if has_map else 0))
            r = tab.call("Runtime.evaluate", expression=CHECK_JS, returnByValue=True)["result"].get("value") or {}
            box = tab.call("Runtime.evaluate", expression="(()=>{const r=document.getElementById('frame').getBoundingClientRect();"
                           "return [r.left,r.top,r.width,r.height]})()", returnByValue=True)["result"]["value"]
            png = base64.b64decode(tab.call("Page.captureScreenshot", format="png",
                                            clip={"x": box[0], "y": box[1], "width": box[2], "height": box[3], "scale": 1})["data"])
            f = out / f"slide_{k:02d}.png"
            f.write_bytes(png)
            shots.append(f)
            lines = [f"ERROR {e}" for e in dict.fromkeys(r.get("errors", []))]
            if r.get("words", 0) > WORDS_WARN:
                lines.append(f"WARN {r['words']} words of text (aim for 60 or fewer: split it, or show it as a picture)")
            if r.get("small"):
                lines.append(f"WARN text under {MIN_PX} px: " + "; ".join(r["small"][:3]))
            if r.get("untipped"):
                lines.append(f"WARN {len(r['untipped'])} text block(s) with numbers but no hover saying how they were calculated: "
                             + "; ".join(r["untipped"][:3]))
            if r.get("repeat"):
                lines.append(f"WARN {r['repeat']} tip(s) only repeat the text they sit on (add information or drop the tip)")
            n_err += sum(1 for x in lines if x.startswith("ERROR"))
            status = "ok" if not lines else ("ERRORS" if any(x.startswith("ERROR") for x in lines) else "warnings")
            print(f"slide {k:>2} [{r.get('id', '?')}] {r.get('title', '')!s:.60}: {status} ({r.get('words', 0)} words)")
            for x in lines:
                print("    " + x)
        if a.phone:
            tab.call("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
            tab.call("Runtime.evaluate", expression="location.hash='#1';window.dispatchEvent(new Event('resize'))")
            tab.pump(1.2)
            sw = tab.call("Runtime.evaluate", expression="[document.documentElement.scrollWidth, document.documentElement.clientWidth]",
                          returnByValue=True)["result"]["value"]
            (out / "phone.png").write_bytes(base64.b64decode(tab.call("Page.captureScreenshot", format="png")["data"]))
            print(f"phone: {out / 'phone.png'}" + (f"  ERROR page scrolls sideways ({sw[0]} > {sw[1]} px)" if sw[0] > sw[1] + 1 else ""))
            n_err += sw[0] > sw[1] + 1
        for e in dict.fromkeys(tab.errors):
            print(f"ERROR page: {e}")
            n_err += 1
        tab.ws.close()
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(prof, ignore_errors=True)
    if shots and not a.no_sheet:
        try:
            from PIL import Image
            per, tw, th = 12, 640, 360
            for si in range(0, len(shots), per):
                grp = shots[si:si + per]
                sheet = Image.new("RGB", (tw * 3, th * ((len(grp) + 2) // 3)), (14, 20, 24))
                for j, f in enumerate(grp):
                    sheet.paste(Image.open(f).convert("RGB").resize((tw - 8, th - 8)), ((j % 3) * tw + 4, (j // 3) * th + 4))
                p = out / f"sheet_{si // per + 1}.png"
                sheet.save(p)
                print(f"contact sheet: {p} (slides {grp[0].stem[6:]}–{grp[-1].stem[6:]})")
        except ImportError:
            print("PIL not installed: no contact sheets")
    print(f"{'FAILED' if n_err else 'passed'}: {n_err} error(s); pictures in {out}")
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
