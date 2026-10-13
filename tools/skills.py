#!/usr/bin/env python3
"""Check, package and sync the skills in this repo.

WHY THIS EXISTS
    Every skill here must load in every tool that reads Agent Skills (https://agentskills.io/specification),
    and the copy in this repo must match the maintainer's working copy. This does those three jobs the same
    way every time, with no dependencies beyond PyYAML.

USAGE
    python3 tools/skills.py check [NAME ...]          # validate skills/NAME (all skills if none named)
    python3 tools/skills.py package [NAME ...]        # validate, then write dist/NAME.skill (a zip for claude.ai)
    python3 tools/skills.py sync NAME [SOURCE_DIR]    # copy a working copy (default ~/.claude/skills/NAME)
                                                      # into skills/NAME, then check and package it
"""
from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

# ============================================================================ settings
ROOT = Path(__file__).resolve().parents[1]
SKILLS, DIST = ROOT / "skills", ROOT / "dist"
SKIP = {".git", "__pycache__", ".DS_Store", ".ipynb_checkpoints"}       # never copied or packaged
SKIP_SUFFIX = {".pyc"}
ALLOWED = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
MAX_BODY_LINES = 500
# ============================================================================


def frontmatter(md: Path) -> tuple[dict, str]:
    try:
        import yaml
    except ImportError:
        sys.exit("skills.py needs PyYAML: python3 -m pip install pyyaml")
    text = md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError("SKILL.md must start with YAML frontmatter between --- lines")
    fm = yaml.safe_load(m.group(1))
    if not isinstance(fm, dict):
        raise ValueError("frontmatter is not a mapping")
    return fm, m.group(2)


def check(d: Path) -> list[str]:
    """Problems that would stop the skill loading somewhere (empty list = fine)."""
    md = d / "SKILL.md"
    if not md.is_file():
        return [f"{d.name}: no SKILL.md"]
    try:
        fm, body = frontmatter(md)
    except Exception as e:                       # noqa: BLE001 - report any parse failure as a problem
        return [f"{d.name}: {e}"]
    errs = []
    name, desc = fm.get("name", ""), fm.get("description", "")
    if extra := set(fm) - ALLOWED:
        errs.append(f"unknown frontmatter keys {sorted(extra)} (allowed: {sorted(ALLOWED)})")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(name)) or len(str(name)) > 64:
        errs.append(f"name {name!r}: 1-64 lowercase letters, digits and single hyphens")
    if name != d.name:
        errs.append(f"name {name!r} must match the folder name {d.name!r}")
    if not isinstance(desc, str) or not 1 <= len(desc) <= 1024:
        errs.append(f"description must be 1-1024 characters (is {len(desc) if isinstance(desc, str) else 'missing'})")
    elif "<" in desc or ">" in desc:
        errs.append("description must not contain angle brackets")
    if "compatibility" in fm and not 1 <= len(str(fm["compatibility"])) <= 500:
        errs.append("compatibility must be 1-500 characters")
    if "metadata" in fm and not (isinstance(fm["metadata"], dict) and all(isinstance(v, str) for v in fm["metadata"].values())):
        errs.append("metadata must map strings to strings (quote numbers like version: \"1.0\")")
    if (n := body.count("\n")) > MAX_BODY_LINES:
        errs.append(f"SKILL.md body is {n} lines; keep it under {MAX_BODY_LINES} and move detail to references/")
    return [f"{d.name}: {e}" for e in errs]


def files(d: Path):
    for p in sorted(d.rglob("*")):
        rel = p.relative_to(d)
        if p.is_file() and not (set(rel.parts) & SKIP) and p.suffix not in SKIP_SUFFIX:
            yield p, rel


def package(d: Path) -> Path:
    DIST.mkdir(exist_ok=True)
    out = DIST / f"{d.name}.skill"
    tmp = out.with_suffix(".skill.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for p, rel in files(d):
            z.write(p, f"{d.name}/{rel.as_posix()}")
    tmp.replace(out)
    return out


def sync(name: str, src: Path) -> None:
    if not (src / "SKILL.md").is_file():
        sys.exit(f"no SKILL.md in {src}")
    dest = SKILLS / name
    wanted = {rel for _, rel in files(src)}
    if dest.exists():                            # drop files the working copy no longer has
        for p, rel in list(files(dest)):
            if rel not in wanted:
                p.unlink()
                print(f"removed {name}/{rel}")
    for p, rel in files(src):
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        if not (dest / rel).exists() or (dest / rel).read_bytes() != p.read_bytes():
            shutil.copy2(p, dest / rel)
            print(f"copied  {name}/{rel}")


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in {"check", "package", "sync"}:
        print(__doc__)
        return 2
    cmd, args = argv[0], argv[1:]
    if cmd == "sync":
        if not args:
            sys.exit("usage: skills.py sync NAME [SOURCE_DIR]")
        sync(args[0], Path(args[1]).expanduser() if len(args) > 1 else Path.home() / ".claude" / "skills" / args[0])
        cmd, args = "package", args[:1]
    dirs = [SKILLS / a for a in args] if args else sorted(p for p in SKILLS.iterdir() if p.is_dir())
    problems = [e for d in dirs for e in check(d)]
    for e in problems:
        print(f"FAIL  {e}")
    if problems:
        return 1
    for d in dirs:
        print(f"OK    {d.name}" + (f"  ->  {package(d).relative_to(ROOT)}" if cmd == "package" else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
