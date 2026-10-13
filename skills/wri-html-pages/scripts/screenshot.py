#!/usr/bin/env python3
"""Screenshot a page the way a reader sees it, on a desktop and on a phone, and report its JS errors.

WHY THIS EXISTS
    Chrome's one-shot `--screenshot` flag is unreliable for our pages: with a virtual time budget it
    often captures a map before its data or tiles arrive, and with a real-time wait it can capture a
    blank WebGL canvas. This drives headless Chrome over the DevTools protocol instead: open the
    page, wait for it to settle, capture, and print every console error and uncaught exception so a
    broken page is caught before anyone else sees it.

USAGE (needs websocket-client and Chrome or Chromium; set CHROME=/path/to/chrome if it is not found)
    screenshot.py PAGE.html|URL OUT_PREFIX [--wait 8] [--sizes desktop,phone] [--full] [--hash view=15/39.95/-105.16]
    -> OUT_PREFIX_desktop.png, OUT_PREFIX_phone.png (full-page captures are sliced into _1, _2 … pieces
       no taller than 1800 px so they can be read). Exit status 1 if the page logged errors or scrolls sideways on a phone.
    Sizes: desktop = 1400x900, laptop = 1280x800, phone = 390x844 @2x (mobile), tablet = 820x1180.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import websocket

SIZES = {"desktop": (1400, 900, 1, False), "laptop": (1280, 800, 1, False),
         "phone": (390, 844, 2, True), "tablet": (820, 1180, 2, True)}
# Chrome or Chromium: $CHROME, then the PATH (Linux), then the usual macOS and Windows install places.
CHROME = os.environ.get("CHROME") or next(
    (c for c in [*(shutil.which(n) for n in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "chrome")),
                 "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium",
                 r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                 r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"] if c and os.path.exists(c)), None)
SLICE_PX = 1800
# Page width vs screen width, and the outermost elements sticking out (scroll boxes, maps and SVGs may be wide inside).
SIDEWAYS_JS = """(() => { const cw = document.documentElement.clientWidth;
  const off = [...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > cw + 1 &&
      !e.closest('[class*=scroll],.mapframe,.maplibregl-map,svg') && !(e.parentElement && e.parentElement.getBoundingClientRect().right > cw + 1));
  return {cw, sw: document.documentElement.scrollWidth,
          off: off.slice(0, 5).map(e => e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : '') +
                                       ' "' + (e.textContent || '').trim().slice(0, 30) + '"')}; })()"""


class Tab:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=60, suppress_origin=True)
        self.n, self.errors = 0, []

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == self.n:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result", {})
            self._event(m)

    def _event(self, m):
        meth, p = m.get("method"), m.get("params", {})
        if meth == "Runtime.exceptionThrown":
            d = p.get("exceptionDetails", {})
            self.errors.append("exception: " + (d.get("exception", {}).get("description") or d.get("text", "")).split("\n")[0])
        elif meth == "Runtime.consoleAPICalled" and p.get("type") in ("error", "assert"):
            self.errors.append("console.error: " + " ".join(str(a.get("value", a.get("description", ""))) for a in p.get("args", [])))
        elif meth == "Log.entryAdded" and p.get("entry", {}).get("level") == "error":
            e = p["entry"]
            if "favicon.ico" in e.get("url", ""):          # browsers ask for one; a 404 there is harmless
                return
            self.errors.append(f"{e.get('source')}: {e.get('text')} {e.get('url', '')}".strip())

    def pump(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            self.ws.settimeout(max(0.05, end - time.time()))
            try:
                self._event(json.loads(self.ws.recv()))
            except websocket.WebSocketTimeoutException:
                pass
        self.ws.settimeout(60)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page")
    ap.add_argument("out_prefix")
    ap.add_argument("--wait", type=float, default=8.0, help="seconds to let the page settle after load")
    ap.add_argument("--sizes", default="desktop,phone")
    ap.add_argument("--full", action="store_true", help="capture the whole scrolling page, not just the first screen")
    ap.add_argument("--hash", default="", help="URL fragment to append, e.g. view=15/39.95/-105.16")
    ap.add_argument("--eval", default="", help="JS expression to print after the wait (debugging), e.g. 'document.title'")
    a = ap.parse_args()
    if not CHROME:
        sys.exit("google-chrome not found")
    url = a.page if "://" in a.page else Path(a.page).resolve().as_uri()
    if a.hash:
        url += "#" + a.hash.lstrip("#")
    port, prof = free_port(), tempfile.mkdtemp(prefix="shot_")
    proc = subprocess.Popen([CHROME, "--headless=new", "--no-sandbox", "--hide-scrollbars", "--mute-audio",
                             "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-first-run",
                             # a headless tab can count as hidden: timers and animation frames then stall and
                             # a WebGL map never draws. Keep it treated as a visible, focused tab.
                             "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
                             "--disable-backgrounding-occluded-windows",
                             f"--remote-debugging-port={port}", f"--user-data-dir={prof}", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    bad = 0
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
        # The first page load after Chrome starts is unreliable (seen 2026-10-12: MapLibre's script arrives but never
        # initialises, so the map is blank; every later load is fine). So the first size is captured twice and the
        # first capture thrown away.
        sizes = [s.strip() for s in a.sizes.split(",")]
        out = []
        for k, name in enumerate([sizes[0]] + sizes):
            warmup = k == 0
            w, h, dpr, mobile = SIZES[name.strip()]
            if a.full:
                dpr = 1          # tall captures at 2x pass Chrome's texture limit and repeat the page
            tab = Tab(ws_url)
            for dom in ("Page", "Runtime", "Log"):
                tab.call(f"{dom}.enable")
            tab.call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=dpr, mobile=mobile)
            tab.call("Emulation.setTouchEmulationEnabled", enabled=mobile)
            tab.call("Emulation.setFocusEmulationEnabled", enabled=True)
            tab.call("Page.bringToFront")
            tab.call("Page.navigate", url="about:blank")
            tab.pump(0.3)
            tab.call("Page.navigate", url=url)
            tab.pump(a.wait)
            if a.full:
                ch = tab.call("Page.getLayoutMetrics")["cssContentSize"]["height"]
                tab.call("Emulation.setDeviceMetricsOverride", width=w, height=int(min(ch, 16000)), deviceScaleFactor=dpr, mobile=mobile)
                tab.pump(1.5)
            if mobile and not warmup:     # the page itself must never scroll sideways on a phone (house-style.md)
                r = tab.call("Runtime.evaluate", expression=SIDEWAYS_JS, returnByValue=True)
                sw = r.get("result", {}).get("value") or {}
                if sw.get("sw", 0) > sw.get("cw", 0) + 1:
                    print(f"{name}: WARN page scrolls sideways: {sw['sw']} px wide in a {sw['cw']} px screen; widest: "
                          + "; ".join(sw.get("off", [])))
                    bad += 1
            if a.eval and not warmup:
                r = tab.call("Runtime.evaluate", expression=a.eval, returnByValue=True)
                print(f"{name}: eval -> {r.get('result', {}).get('value', r)}")
            png = base64.b64decode(tab.call("Page.captureScreenshot", format="png")["data"])
            if warmup:
                tab.ws.close()
                continue
            f = Path(f"{a.out_prefix}_{name}.png")
            f.write_bytes(png)
            out.append(f)
            for e in dict.fromkeys(tab.errors):
                print(f"{name}: {e}")
            bad += len(tab.errors)
            tab.ws.close()
        for f in out:
            try:
                from PIL import Image
                im = Image.open(f)
                if im.height > SLICE_PX * 1.2:
                    for i, y in enumerate(range(0, im.height, SLICE_PX), 1):
                        im.crop((0, y, im.width, min(im.height, y + SLICE_PX))).save(f.with_name(f"{f.stem}_{i}.png"))
                    print(f"{f}  ({im.width}x{im.height}, sliced into {-(-im.height // SLICE_PX)} pieces)")
                    continue
                print(f"{f}  ({im.width}x{im.height})")
            except ImportError:
                print(f)
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(prof, ignore_errors=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
