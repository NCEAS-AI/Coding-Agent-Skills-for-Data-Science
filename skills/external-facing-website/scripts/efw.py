#!/usr/bin/env python3
"""Shared helpers for the external-facing-website skill: where things are, and the landing-page settings.

WHY THIS EXISTS
    This skill builds the landing page itself (build_site.py, standard library only) but leans on the sibling
    wri-html-pages skill for everything around it: check_page.py, screenshot.py, pin_gate.py (the PIN lock) and
    publish.py. Both skills can be installed in several places (Claude Code, other agents, an OpenClaw workspace),
    so the lookup lives in one place instead of being guessed in every script. The landing-page settings (contact,
    logo row, lock-screen photo) live in one small JSON file with a personal copy that survives updates, the same
    pattern as wri-html-pages' identity.json.

USAGE
    python3 scripts/efw.py --where        # print this skill, the page skill (and its version) and the settings used
    import efw; efw.SKILL; efw.pages_dir(); efw.site_config(); efw.asset("logos/wri-logo.png")

    Page skill lookup: $EFW_PAGES_SKILL, then a sibling wri-html-pages (or any sibling *-html-pages), then
    ~/.claude/skills/wri-html-pages, ~/.agents/skills/wri-html-pages, ~/.openclaw/workspace/skills/wri-html-pages.
    Settings: $EFW_SITE_CONFIG, then ~/.config/external-facing-website/site.json, then references/site.json here.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ASSETS = SKILL / "assets"
MIN_PAGES_VERSION = (1, 13, 0)


def pages_dir(required: bool = True) -> Path | None:
    """The wri-html-pages skill this one builds on (see the module docstring for the search order)."""
    env = os.environ.get("EFW_PAGES_SKILL")
    cands = [Path(env).expanduser()] if env else []
    cands.append(SKILL.parent / "wri-html-pages")
    cands += sorted(SKILL.parent.glob("*-html-pages"))
    home = Path.home()
    cands += [home / ".claude/skills/wri-html-pages", home / ".agents/skills/wri-html-pages",
              home / ".openclaw/workspace/skills/wri-html-pages"]
    too_old = []
    for c in cands:
        if (c / "scripts" / "pin_gate.py").is_file() and (c / "scripts" / "publish.py").is_file():
            ok, v = pages_ok(c)
            if ok:
                return c
            too_old.append(f"{c} (version {v})")          # an older copy earlier in the order must not win silently
    if required:
        sys.exit("efw: no wri-html-pages skill >= 1.13.0 was found next to this skill or in ~/.claude/skills, "
                 "~/.agents/skills, ~/.openclaw/workspace/skills"
                 + (f"; too old: {', '.join(too_old)}" if too_old else "")
                 + ". Install or update it there, or set EFW_PAGES_SKILL=/path/to/wri-html-pages")
    return None


def pages_version(pages: Path) -> str:
    m = re.search(r'^\s*version:\s*"?([0-9.]+)"?', (pages / "SKILL.md").read_text(), re.M)
    return m.group(1) if m else "unknown"


def pages_ok(pages: Path) -> tuple[bool, str]:
    """True when the page skill can draw the branded lock screen with a custom button (1.13.0+)."""
    v = pages_version(pages)
    src = (pages / "scripts" / "pin_gate.py").read_text()
    has = "def brand_lock_screen" in src and "gate-button" in src
    try:
        new_enough = tuple(int(x) for x in v.split(".")[:3]) >= MIN_PAGES_VERSION
    except ValueError:
        new_enough = has
    return (has and new_enough), v


def site_config_path() -> Path:
    env = os.environ.get("EFW_SITE_CONFIG")
    for p in ([Path(env).expanduser()] if env else []) + [Path.home() / ".config/external-facing-website/site.json"]:
        if p.is_file():
            return p
    return SKILL / "references" / "site.json"


def site_config() -> dict:
    """Bundled defaults, overlaid key by key with the personal copy (so a personal file may hold only a contact)."""
    base = json.loads((SKILL / "references" / "site.json").read_text())
    p = site_config_path()
    if p != SKILL / "references" / "site.json":
        mine = json.loads(p.read_text())
        for k, v in mine.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                base[k] = {**base[k], **v}
            else:
                base[k] = v
    base["_path"] = str(p)
    return base


def asset(name: str) -> Path:
    """A logo, photo or icon file: next to the settings file in use first, then this skill's assets/ (and logos/)."""
    here = Path(site_config_path()).parent
    for c in (here / name, ASSETS / name, ASSETS / "logos" / name, ASSETS / "fonts" / name):
        if c.is_file():
            return c
    sys.exit(f"efw: asset {name!r} not found next to {site_config_path()} or in {ASSETS}")


def main():
    if "--where" not in sys.argv:
        print(__doc__)
        return
    print("this skill        ", SKILL)
    p = pages_dir(required=False)
    if p:
        ok, v = pages_ok(p)
        print("wri-html-pages    ", p, f"(version {v}{'' if ok else ': TOO OLD, need >= 1.13.0 for the branded lock screen'})")
    else:
        print("wri-html-pages     NOT FOUND (set EFW_PAGES_SKILL)")
    print("site settings     ", site_config_path())
    c = site_config()
    who = c.get("contact") or {}
    print("contact           ", (who.get("name") or "(none: ask the user)") + (f" <{who['email']}>" if who.get("email") else ""))
    if p:
        sys.path.insert(0, str(p / "scripts"))
        try:
            import vizkit
            print("identity.json     ", vizkit.identity_path())
        except Exception as e:  # noqa: BLE001
            print("identity.json      (could not load vizkit:", e, ")")


if __name__ == "__main__":
    main()
