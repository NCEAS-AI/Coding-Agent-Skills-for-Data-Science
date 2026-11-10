#!/usr/bin/env python3
"""Check a PIN-gated landing page before (and after) it is published: branded, leak-free, and it opens.

WHY THIS EXISTS
    Three kinds of gate mistake are easy to make and hard to see: a locked address published open; a lock screen
    that falls back to the plain "Enter PIN" box (or loses part of the branded screen) instead of the branded one;
    and HTTP 200 or a byte match taken as proof that a gated page works. This script checks the three things that
    matter, on the gated file itself:
      (a) BRANDED: the lock screen has every part of the branded screen (photo panel .gb-art, the "Enter your access
          PIN" heading, the label for the PIN field, the contact footer .gb-foot) and its own tab title.
      (b) NO LEAKS: the lock screen is not encrypted, so none of the page's content may be on it: the dated <title>,
          the hero paragraph, section headings, headline numbers. (The program name, logos and contact are meant to
          be there.) Probes come from the decrypted page, from --plain FILE, and from --probe TEXT.
      (c) OPENS: with the PIN it decrypts, and the plaintext contains every --expect string (e.g. the map iframe
          address, a heading). The PIN comes from $SLP_PIN or, with --keychain-service NAME, from the macOS
          Keychain; it is never printed or written anywhere.
    It uses wri-html-pages' own pin_gate.ungate (found like every script here: efw.pages_dir()), so it decrypts
    exactly the way the page does. For a live page, download it first (curl -s URL > live.html) and run this on it;
    then do the fresh-browser test in references/lock-screen.md (a real browser, real PIN, no console errors).

USAGE
    SLP_PIN=... python3 verify_gate.py PAGE.gated.html --expect "Four fires, building by building" [--expect ...]
    python3 verify_gate.py PAGE.gated.html --keychain-service SERVICE --expect "..."
    python3 verify_gate.py PAGE.gated.html --plain PAGE.html          # (a) and (b) only, no PIN needed
    [--wri-html-pages /path/to/wri-html-pages]   Exit status 1 if any check fails.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import efw  # noqa: E402


def visible(s: str) -> str:
    s = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", s, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def lock_screen(gated: str) -> str:
    """The unencrypted part a visitor without the PIN receives, minus the ciphertext."""
    return re.sub(r'C="[A-Za-z0-9+/=]+"', 'C=""', gated)


def probes_from(plain: str) -> list[str]:
    """Content that must not appear on the lock screen: dated title, hero paragraph(s), h2 headings, stat numbers+labels."""
    out = []
    t = re.search(r"<title>(.*?)</title>", plain, re.S)
    if t:
        out.append(visible(t.group(1)))
    lede = re.search(r'<div class="lede" id="lede">(.*?)</div>', plain, re.S)
    if lede:
        out += [visible(p)[:80] for p in re.findall(r"<p>(.*?)</p>", lede.group(1), re.S)]
    body = plain[plain.find("<main"):] if "<main" in plain else plain
    out += [visible(h) for h in re.findall(r"<h2[^>]*>(.*?)</h2>", body, re.S)]
    out += [visible(f"{b} {s}")[:60] for b, s in re.findall(r'<div class="stat"[^>]*><b>(.*?)</b><span>(.*?)</span>', body, re.S)]
    return [p for p in out if len(p) >= 8]


def read_pin(service: str | None) -> str | None:
    if service:
        r = subprocess.run(["security", "find-generic-password", "-s", service, "-w"], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"verify_gate: no Keychain item for service {service!r}")
        return r.stdout.strip()
    return os.environ.get("SLP_PIN")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("gated", type=Path)
    ap.add_argument("--expect", action="append", default=[], help="text the decrypted page must contain (repeat)")
    ap.add_argument("--plain", type=Path, help="the plaintext page, for leak probes without the PIN")
    ap.add_argument("--probe", action="append", default=[], help="extra text that must NOT be on the lock screen")
    ap.add_argument("--keychain-service", help="read the PIN from this macOS Keychain service (never printed)")
    ap.add_argument("--allow-draft", action="store_true", help="do not fail on a --draft review copy (practice runs)")
    ap.add_argument("--wri-html-pages", type=Path, help="path to the wri-html-pages skill (default: found automatically)")
    a = ap.parse_args()
    if a.wri_html_pages:
        os.environ["EFW_PAGES_SKILL"] = str(a.wri_html_pages)
    gated = a.gated.read_text()
    fails, notes = [], []

    if "<!-- pin-gated" not in gated[:200]:
        print(f"FAIL  {a.gated} is not a PIN-gated page (no pin-gated marker): it would be published OPEN")
        sys.exit(1)
    lock = lock_screen(gated)
    lock_text = visible(lock)

    # (a) branded
    title = re.search(r"<title>(.*?)</title>", lock, re.S)
    title = visible(title.group(1)) if title else ""
    form = lock[lock.find('<form'):lock.find('</form>')] if '<form' in lock else ""
    parts = {"photo panel (.gb-art)": 'class="gb-art"' in form, "heading (h2)": "<h2>" in form,
             "PIN label (label for=pin)": re.search(r'<label[^>]*for="pin"', form) is not None,
             "contact footer (.gb-foot)": 'class="gb-foot"' in lock[lock.find('</form>'):] if '</form>' in lock else False}
    if not parts["photo panel (.gb-art)"]:
        fails.append("lock screen is the plain box (no .gb-art photo panel): build the page with build_site.py "
                     "WITHOUT --no-gate-blocks, and gate it with wri-html-pages >= 1.13.0")
    elif not all(parts.values()):
        fails.append("the branded lock screen is incomplete, missing: " + ", ".join(k for k, v in parts.items() if not v)
                     + " (a brand block was cut short; rebuild with build_site.py)")
    if title in ("", "Protected page"):
        fails.append(f"lock-screen tab title is {title!r}: the <meta name=\"gate-title\"> block is missing")
    if "Enter PIN" in lock_text and 'class="gb-art"' not in lock:
        notes.append("the default 'Enter PIN' heading is showing")
    if not fails:
        print(f"ok    branded lock screen (tab title: {title})")

    # (c) decrypt
    plain = None
    pin = read_pin(a.keychain_service)
    if pin:
        sys.path.insert(0, str(efw.pages_dir() / "scripts"))
        import pin_gate
        try:
            plain = pin_gate.ungate(gated, pin)
        except Exception as e:  # noqa: BLE001  (wrong PIN raises InvalidTag)
            fails.append(f"the PIN does not open this page ({type(e).__name__}); was it gated with another PIN?")
        if plain is not None:
            print(f"ok    decrypts with the PIN ({len(plain.encode()) / 1024:.0f} KB of page)")
            for e in a.expect:
                if e in plain or html.escape(e, quote=False) in plain:
                    print(f"ok    decrypted page contains {e!r}")
                else:
                    fails.append(f"decrypted page does not contain {e!r}")
            if 'name="efw-draft"' in plain and not a.allow_draft:
                fails.append("this is a --draft review copy (unfinished text or a placeholder contact): finish the spec and "
                             "rebuild without --draft before publishing (--allow-draft for a practice run)")
            if 'text/x-gate-brand' not in plain:
                notes.append("the decrypted page has no brand block, so re-wrapping it (pin_gate DIR mode) would lose the branding")
    elif a.expect:
        fails.append("--expect given but no PIN: set SLP_PIN in the environment (never on disk) or pass --keychain-service")
    else:
        notes.append("no PIN given: decryption not tested")

    # (b) leaks
    probes = list(a.probe)
    if plain:
        probes += probes_from(plain)
    if a.plain:
        ptxt = a.plain.read_text()
        probes += probes_from(ptxt)
        if 'name="efw-draft"' in ptxt and not a.allow_draft and plain is None:
            fails.append(f"{a.plain} is a --draft review copy: rebuild without --draft before publishing")
    seen = set()
    leaks = []
    for p in probes:
        if p in seen:
            continue
        seen.add(p)
        if p and p in lock_text:
            leaks.append(p)
    if leaks:
        for p in leaks:
            fails.append(f"page content is readable on the unencrypted lock screen: {p[:70]!r}")
    elif probes:
        print(f"ok    no page content on the lock screen ({len(seen)} probes: title, hero, headings, stats)")
    else:
        notes.append("no leak probes (give the PIN, --plain or --probe)")

    for n in notes:
        print("note ", n)
    for f in fails:
        print("FAIL ", f)
    print(("FAILED" if fails else "PASSED") + f"  {a.gated}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
