#!/usr/bin/env python3
"""PIN gate v2 for the staged websites (2026-10-07, lane DEMO-SITE; owner bug report "lock screen flashes").

Why v2
    v1 encrypted every page with its own random PBKDF2 salt and remembered the PIN in sessionStorage. Every page first
    painted the PIN form, then re-derived the key (PBKDF2-SHA256, 100,000 rounds) from the remembered PIN and replaced
    itself, so the form flashed on every navigation and the slow derivation ran on every page.

What v2 does
    * One site-wide salt (SITE_SALT, not secret), so the derived AES-256-GCM key is the same for every page. Each page
      still has its own random 96-bit IV.
    * A synchronous script in <head> checks sessionStorage for the derived key before first paint. If one is present the
      page shows only a neutral placeholder in the site background (a small spinner appears after 300 ms) and decrypts
      with the stored key; the PIN form is shown only when no key is stored or decryption fails (wrong or changed PIN,
      different salt).
    * The derived key is stored (base64 raw key, sessionStorage, this browser session only) under KEY_NAME. The PIN is
      also kept under the v1 name `slp_pin` so pages still on the v1 wrapper keep opening. No PIN is written into any
      served file.

This copy (wri-html-pages skill, 2026-10-12) is byte-compatible with structure-loss-pipeline/scripts/pin_gate_v2.py:
same salt, iterations and key name, so one PIN entry opens every gated page on wri-science.github.io in a session.

CLI
    SLP_PIN=... python pin_gate.py --gate IN.html OUT.html       # encrypt one plaintext page
    SLP_PIN=... python pin_gate.py --ungate IN.html OUT.html     # decrypt one gated page (to check or edit it)
    SLP_PIN=... python pin_gate.py DIR [DIR ...] [--execute]     # re-wrap existing v1/v2 pages (dry run by default)
"""
from __future__ import annotations

import argparse
import base64
import os
import re
import secrets
import sys
from pathlib import Path

SITE_SALT_B64 = "O3n8bt4F9vMq/xf+AAavRw=="   # site-wide PBKDF2 salt (public by design; fixed 2026-10-07)
ITERATIONS = 100000
KEY_NAME = "slp_key_v2"

HEAD = """<!DOCTYPE html><!-- pin-gated v2 -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive,nosnippet"><meta name="googlebot" content="noindex,nofollow,noarchive">
<title>Protected page</title>
<script>try{if(sessionStorage.getItem("__KEY__"))document.documentElement.className="k";}catch(e){}</script>
<style>
:root { --bg:#F5F7F9; --ink:#13202C; --muted:#5A6570; --line:#D9D6CC; --acc:#2E6A8A; --bad:#C4502B; color-scheme:light; }
@media (prefers-color-scheme: dark) { :root { --bg:#0D1217; --ink:#E7EAE6; --muted:#9AA29D; --line:#323834; --acc:#6FB0CF; --bad:#EF7D74; color-scheme:dark; } }
html,body { margin:0; height:100%; background:var(--bg); color:var(--ink); font-family:system-ui,-apple-system,"Segoe UI",sans-serif; }
.wrap { min-height:100%; display:flex; align-items:center; justify-content:center; padding:16px; box-sizing:border-box; }
.box { width:100%; max-width:340px; border:1px solid var(--line); border-radius:14px; padding:28px 24px; text-align:center; }
h1 { font-size:20px; margin:0 0 6px; } p { color:var(--muted); font-size:14px; margin:0 0 18px; }
input { width:100%; box-sizing:border-box; font-size:28px; letter-spacing:10px; text-align:center; padding:10px; border-radius:10px;
        border:1px solid var(--line); background:transparent; color:var(--ink); }
button { margin-top:14px; width:100%; font-size:16px; padding:10px; border-radius:10px; border:0; background:var(--acc); color:#fff; font-weight:600; }
.err { color:var(--bad); min-height:20px; margin-top:10px; font-size:14px; }
.shake { animation:sh .35s; } @keyframes sh { 25% { transform:translateX(-8px); } 75% { transform:translateX(8px); } }
#ph { display:none; position:fixed; inset:0; align-items:center; justify-content:center; }
#ph i { width:22px; height:22px; border-radius:50%; border:2px solid var(--line); border-top-color:var(--acc); opacity:0;
        animation:sp .8s linear infinite, fi .2s .3s forwards; }
@keyframes sp { to { transform:rotate(360deg); } } @keyframes fi { to { opacity:1; } }
html.k #ph { display:flex; } html.k .wrap { display:none; }
@media (prefers-reduced-motion: reduce) { #ph i { animation:fi .2s .3s forwards; } }
</style></head><body><div id="ph" aria-busy="true" aria-label="Opening page"><i></i></div>
<div class="wrap"><form class="box" id="f" autocomplete="off">
<h1>Enter PIN</h1><p>This page is shared privately.</p>
<input id="pin" inputmode="numeric" type="password" maxlength="12" aria-label="PIN">
<button type="submit">Open</button><div class="err" id="err" role="alert"></div></form></div>
<script>
"""
TAIL = """
function u8(s) { return Uint8Array.from(atob(s), function(c) { return c.charCodeAt(0); }); }
function b64(a) { var s = ""; a = new Uint8Array(a); for (var i = 0; i < a.length; i++) s += String.fromCharCode(a[i]); return btoa(s); }
function show(html) {
  // document.open() is ignored while the gate page itself is still being parsed,
  var go = function() { document.open(); document.write(html); document.close(); };
  // and writing during DOMContentLoaded can leave a parser-blocking <script src> in the new page stalled: wait for load
  if (document.readyState === "complete") setTimeout(go, 0);
  else window.addEventListener("load", function() { setTimeout(go, 0); });
}
function lockForm() { document.documentElement.className = ""; try { document.getElementById("pin").focus(); } catch (e) {} }
async function withKey(raw) {
  var key = await crypto.subtle.importKey("raw", u8(raw), {name:"AES-GCM"}, false, ["decrypt"]);
  return new TextDecoder().decode(await crypto.subtle.decrypt({name:"AES-GCM", iv:u8(I)}, key, u8(C)));
}
async function gateOpen(pin) {
  var km = await crypto.subtle.importKey("raw", new TextEncoder().encode(pin), "PBKDF2", false, ["deriveKey"]);
  var key = await crypto.subtle.deriveKey({name:"PBKDF2", salt:u8(S), iterations:N, hash:"SHA-256"}, km, {name:"AES-GCM", length:256}, true, ["decrypt"]);
  var pt = await crypto.subtle.decrypt({name:"AES-GCM", iv:u8(I)}, key, u8(C));
  var raw = b64(await crypto.subtle.exportKey("raw", key));
  try { sessionStorage.setItem("__KEY__", raw); sessionStorage.setItem("slp_pin", pin); } catch (e) {}
  return new TextDecoder().decode(pt);
}
document.getElementById("f").addEventListener("submit", function(e) {
  e.preventDefault();
  gateOpen(document.getElementById("pin").value).then(show, function() {
    var f = document.getElementById("f"); f.classList.remove("shake"); void f.offsetWidth; f.classList.add("shake");
    document.getElementById("err").textContent = "That PIN did not work.";
  });
});
(function() {
  var raw = null; try { raw = sessionStorage.getItem("__KEY__"); } catch (e) {}
  if (raw) { withKey(raw).then(show, function() { try { sessionStorage.removeItem("__KEY__"); } catch (e) {} lockForm(); }); }
  else { lockForm(); }
})();
</script></body></html>""".replace("__KEY__", KEY_NAME)
HEAD = HEAD.replace("__KEY__", KEY_NAME)


def derive(pin: str, salt: bytes, n: int) -> bytes:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    return PBKDF2HMAC(hashes.SHA256(), 32, salt, n).derive(pin.encode())


_KEY_CACHE: dict = {}


def gate(plain: str, pin: str) -> str:
    """Encrypt one page under the site key (derived once per process) with a fresh IV."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt = base64.b64decode(SITE_SALT_B64)
    k = _KEY_CACHE.get(pin) or _KEY_CACHE.setdefault(pin, derive(pin, salt, ITERATIONS))
    iv = secrets.token_bytes(12)
    ct = AESGCM(k).encrypt(iv, plain.encode("utf-8"), None)
    b = lambda x: base64.b64encode(x).decode()
    return HEAD + f'var S="{SITE_SALT_B64}", I="{b(iv)}", C="{b(ct)}", N={ITERATIONS};' + TAIL


def ungate(gated: str, pin: str) -> str:
    """Decrypt a v1 or v2 gated page (per-page salt in the page)."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    m = re.search(r'var S="([^"]+)", I="([^"]+)", C="([^"]+)", N=(\d+)', gated)
    if not m:
        raise ValueError("not a gated page")
    S, I, C, N = m.groups()
    k = derive(pin, base64.b64decode(S), int(N))
    return AESGCM(k).decrypt(base64.b64decode(I), base64.b64decode(C), None).decode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="*")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--gate", nargs=2, metavar=("IN", "OUT"))
    ap.add_argument("--ungate", nargs=2, metavar=("IN", "OUT"))
    a = ap.parse_args()
    pin = os.environ.get("SLP_PIN")
    if not pin:
        sys.exit("set SLP_PIN (ask the user for the PIN; never write it into a file)")
    if a.gate:
        txt = Path(a.gate[0]).read_text()
        if "<!-- pin-gated" in txt[:200]:
            sys.exit(f"{a.gate[0]} is already gated")
        Path(a.gate[1]).write_text(gate(txt, pin))
        print(f"gated {a.gate[0]} -> {a.gate[1]}")
        return
    if a.ungate:
        Path(a.ungate[1]).write_text(ungate(Path(a.ungate[0]).read_text(), pin))
        print(f"ungated {a.ungate[0]} -> {a.ungate[1]}")
        return
    n = 0
    for d in a.dirs:
        for f in sorted(Path(d).rglob("*.html")):
            txt = f.read_text()
            if "<!-- pin-gated" not in txt[:200]:
                continue
            plain = ungate(txt, pin)
            if a.execute:
                f.write_text(gate(plain, pin))
            n += 1
    print(f"{'re-wrapped' if a.execute else 'would re-wrap'} {n} gated pages")


if __name__ == "__main__":
    main()
