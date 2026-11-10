#!/usr/bin/env python3
"""Open a PIN-gated page in a fresh headless Chrome, type the PIN, and prove the real page appears.

WHY THIS EXISTS
    A gated page can be byte-perfect and still fail a reader: a double gate that locked users out, a white flash, a
    lock screen that never shows the form. The owner's acceptance test for every gated release is a fresh browser:
    the lock screen renders, the PIN opens it, the real content replaces it, it opens again without a second prompt,
    there are no console errors, and a gated map embed inside the page opens without a second prompt. wri-html-pages' screenshot.py cannot type a PIN, so this does it,
    driving Chrome the same way (it reuses screenshot.py's DevTools client). Run it on the locally gated file before
    publishing and on the live URL after publishing.

USAGE (needs Chrome or Chromium and websocket-client; the PIN comes from $SLP_PIN and is never printed)
    SLP_PIN=... python3 test_lock.py PAGE.gated.html|URL [--expect "text on the real page"] [--wrong-pin] [--shot OUT.png]
    --wrong-pin   also check that a wrong PIN is refused with a message
    Exit status 1 if any step fails.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import efw  # noqa: E402

STATE = """(() => ({lock: !!document.querySelector('.gb-art'), form: !!document.getElementById('pin'),
  title: document.title, h1: (document.getElementById('bigtitle') || {}).textContent || '',
  err: (document.getElementById('err') || {}).textContent || '', text: document.body ? document.body.innerText.slice(0, 200000) : ''}))()"""

FRAME = """(() => { const f = document.getElementById('mapiframe'); if (!f) return 'none';
  try { const d = f.contentDocument; if (!d || !d.body) return 'cross-origin';
        const p = d.getElementById('pin'); if (p) return p.offsetParent ? 'prompt' : 'still opening'; return d.body.children.length ? 'ok' : 'empty'; }
  catch (e) { return 'cross-origin'; } })()"""


def ev(tab, js):
    return tab.call("Runtime.evaluate", expression=js, returnByValue=True, awaitPromise=True).get("result", {}).get("value")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("page")
    ap.add_argument("--expect", action="append", default=[])
    ap.add_argument("--wrong-pin", action="store_true")
    ap.add_argument("--shot", type=Path, help="save a screenshot of the unlocked page")
    ap.add_argument("--wait", type=float, default=6.0, help="seconds to allow for the PIN key derivation and the page to load")
    a = ap.parse_args()
    sys.path.insert(0, str(efw.pages_dir() / "scripts"))
    try:
        import screenshot as shot  # (Tab, CHROME, free_port) imported here so --help works without websocket-client
    except ImportError as e:
        sys.exit(f"test_lock: {e}; install websocket-client (pip install websocket-client)")
    pin = os.environ.get("SLP_PIN")
    if not pin:
        sys.exit("test_lock: set SLP_PIN in the environment (ask the user; never write it to a file)")
    if not shot.CHROME:
        sys.exit("test_lock: Chrome or Chromium not found (set CHROME=/path/to/chrome)")
    url = a.page if "://" in a.page else Path(a.page).resolve().as_uri()
    port, prof = shot.free_port(), tempfile.mkdtemp(prefix="lock_")
    proc = subprocess.Popen([shot.CHROME, "--headless=new", "--no-sandbox", "--hide-scrollbars", "--mute-audio", "--no-first-run",
                             "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--disable-background-timer-throttling",
                             "--disable-renderer-backgrounding", f"--remote-debugging-port={port}", f"--user-data-dir={prof}", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    fails = []

    def check(ok, msg):
        print(("ok    " if ok else "FAIL  ") + msg)
        if not ok:
            fails.append(msg)
    try:
        for _ in range(100):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=2))
                ws_url = next(t["webSocketDebuggerUrl"] for t in tabs if t.get("type") == "page")
                break
            except Exception:  # noqa: BLE001
                time.sleep(0.2)
        else:
            sys.exit("test_lock: Chrome did not start")
        tab = shot.Tab(ws_url)
        for dom in ("Page", "Runtime", "Log"):
            tab.call(f"{dom}.enable")
        tab.call("Emulation.setDeviceMetricsOverride", width=1400, height=900, deviceScaleFactor=1, mobile=False)
        tab.call("Page.navigate", url=url)
        tab.pump(2.5)
        s = ev(tab, STATE)
        check(s["form"], "lock screen shows the PIN form (fresh browser, nothing stored)")
        check(s["lock"], f"lock screen is the branded one (tab title: {s['title']})")
        check(not s["h1"], "page content is not shown before the PIN")
        if a.wrong_pin:
            ev(tab, "document.getElementById('pin').value='000000';document.getElementById('f').requestSubmit();")
            tab.pump(a.wait / 2)
            s = ev(tab, STATE)
            check(bool(s["err"]) and not s["h1"], f"a wrong PIN is refused ({s['err'] or 'no message'})")
        ev(tab, f"document.getElementById('pin').value={json.dumps(pin)};document.getElementById('f').requestSubmit();")
        tab.pump(a.wait)
        s = ev(tab, STATE)
        check(bool(s["h1"]) and not s["form"], f"the PIN opens the page (title: {s['title']!r}, h1: {s['h1'][:60]!r})")
        for e in a.expect:
            check(e in s["text"] or e in (s["title"] or ""), f"the opened page shows {e!r}")
        if a.shot:
            a.shot.write_bytes(base64.b64decode(tab.call("Page.captureScreenshot", format="png")["data"]))
            print(f"      screenshot of the opened page: {a.shot}")
        # a gated map embed published in the same call must open inside the page without its own PIN prompt
        ev(tab, "(() => { const f = document.getElementById('mapiframe'); if (f) { f.loading = 'eager'; f.scrollIntoView(); } })()")
        tab.pump(a.wait)
        fr = ev(tab, FRAME)
        if fr == "prompt":
            check(False, "the map embed inside the page asks for a PIN again (it was gated with another PIN or not in the same call)")
        elif fr == "ok":
            check(True, "the map embed opens inside the page without a second PIN prompt")
        elif fr == "still opening":
            check(False, "the map embed inside the page is still on its lock screen after --wait (raise --wait or check its access)")
        elif fr != "none":
            print(f"note  map embed not checked ({fr}: another site, e.g. a local file framing the live map; it is checked on the live URL)")
        tab.call("Page.navigate", url=url)
        tab.pump(a.wait / 2)
        s = ev(tab, STATE)
        check(bool(s["h1"]) and not s["form"], "it opens again in the same session without asking for the PIN")
        errs = list(dict.fromkeys(tab.errors))
        check(not errs, "no console errors" + ("" if not errs else ": " + "; ".join(errs[:5])))
        tab.ws.close()
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(prof, ignore_errors=True)
    print(("FAILED" if fails else "PASSED") + f"  {a.page}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
