#!/usr/bin/env python3
"""Start a site spec for a new program: every section in the recommended order, with FILL: markers to replace.

WHY THIS EXISTS
    The owner's rounds of feedback on the wildfire page settled an order that works for outside readers (hero, map,
    why it matters, what you get, who it helps, accuracy, limits, work with us, team, footer) and a shape for each
    section (one compact hero paragraph, 4 tiles in a row, a small concrete pilot, limits as prose with no numbers).
    Starting from that skeleton is faster than starting from the example, and it does not drag another program's
    wording along (the owner rejected a page that copied another page's structure too closely). build_site.py refuses
    to build while any FILL: marker is left, so nothing half-written can be published. No placeholder is a plausible
    number: every number slot holds FILL text that the schema refuses until a sourced number replaces it. Delete the
    sections you have no real content for; never pad one. The owner's own structure (3 tiles, no chart, no map) always
    wins over this skeleton: pass only the sections you need with --sections.

USAGE
    python3 new_site.py OUT.json --title "Program name" [--date YYYY-MM-DD] [--contact-name NAME --contact-email EMAIL]
                        [--sections hero,map,tiles,chart,pipeline,cards,stats,prose,cta,team,refs,footer] [--open]
    Missing --title / contact are asked for when run in a terminal. --open: a public page (no lock-screen block).
    "chart" with "tiles" puts the chart above the why-it-matters tiles; alone it is a chart section of its own.
    The default leaves out the chart and the references.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

SCHEMA = Path(__file__).resolve().parents[1] / "assets" / "site-spec.schema.json"
ORDER = ["hero", "map", "tiles", "chart", "pipeline", "cards", "stats", "prose", "cta", "team", "refs", "footer"]
DEFAULT = ["hero", "map", "tiles", "pipeline", "cards", "stats", "prose", "cta", "team", "footer"]
F = "FILL: "
NUM = F + "number from a source"          # a string where a number goes: the schema refuses it until it is replaced


def sections(title: str) -> dict:
    tile = lambda i: {"icon": ["clock", "patch", "gap", "sat"][i], "title": F + "short problem, 3-6 words",  # noqa: E731
                      "body": F + "one or two sentences; bold one number with <b>...</b> and give its scope", "src": F + "document, section"}
    chart = {"title": F + "what is counted, per what", "subtitle": F + "scope: which cases, where, when. Hover or tap a bar.",
             "aria_label": F + "one sentence saying what the chart shows and its peak",
             "categories": [{"label": F + "category 1", "value": NUM}, {"label": F + "category 2", "value": NUM},
                            {"label": F + "a category not in the record (or delete)", "gap": True}],
             "value_label": F + "noun for the value", "totals": [{"value": F + "the published total", "label": F + "label", "assert_sum": True}],
             "key": [{"label": F + "series name and source", "kind": "bar"}, {"label": F + "what the hatched columns mean", "kind": "gap"}],
             "table": {"label_header": "Year", "value_header": F + "value"}, "src": F + "document, section"}
    return {
        "hero": {"type": "hero", "lede": [F + "ONE compact paragraph: what the program does now, what it is trying to do, "
                                          "who it is for; if it already produces results: that they are research estimates (not "
                                          "official results), where it is weaker, and how partners' data close the gaps. A program "
                                          "with no results yet says what it will produce and when, and claims nothing more. "
                                          "No statistics, no question-and-answer opener."]},
        "map": {"type": "map", "id": "map", "nav": "See it", "eyebrow": F + "See it on real ...", "heading": F + "the main visual, in a few words",
                "lede": F + "how to read the map in two sentences",
                "iframe": {"src": F + "map-embed-YYYY-MM-DD.html (same folder) or an absolute URL", "title": F + "Interactive map: ..."},
                "tiles": [{"title": F + f"place {i}", "place": F + f"place {i} exactly as the map's tab label", "value": NUM,
                           "text": F + "what the number is, with counts (n of N)", "tip": F + "the four counts behind it", "src": F + "document, section"}
                          for i in (1, 2, 3)] + [{"title": F + "the weak place", "place": F + "weak place as the map's tab label", "value": NUM,
                                                  "text": F + "what the number is", "flagged": True, "src": F + "document, section"}],
                "popup": {"place": F + "weak place as the map's tab label", "title": F + "Why the model misses in ...",
                          "lead": F + "what happened there, with its own numbers",
                          "reasons": [F + "a cause checked on THIS case's own data, labelled as likely"],
                          "helps": [F + "what would help", "More partners sharing their records with us. <a href=\"#partner\">Share yours</a>."]},
                "how": {"items": [F + "what is drawn and what is left off", F + "which record is truth, and the threshold"]},
                "hint": "On a computer, drag to move and hold Ctrl (⌘ on a Mac) while scrolling to zoom; on a phone, use two fingers."},
        "tiles": {"type": "tiles", "id": "why", "nav": "Why it matters", "eyebrow": "Why it matters", "wide": True, "lede_size": "md",
                  "heading": F + "the problem, in one line", "lede": F + "who needs this and why today's answer falls short",
                  "tiles": [tile(i) for i in range(4)]},
        "chart": {"type": "chart", "id": "trend", "eyebrow": F + "label", "heading": F + "heading", "chart": chart},
        "pipeline": {"type": "pipeline", "id": "what", "nav": "What you get", "eyebrow": F + "What you get for each ...", "wide": True,
                     "flow": {"in": F + "Public X in", "out": F + "Y out"},
                     "steps": [{"icon": "house", "title": F + "inputs", "body": F + "one sentence",
                                "chips": [{"label": F + "data source", "href": F + "https://...", "tip": F + "what it is, licence"}]},
                               {"icon": "sat", "title": F + "the method", "body": F + "one sentence; explain any threshold"},
                               {"icon": "table", "title": F + "the output", "body": F + "one sentence",
                                "list": {"summary": "See the reference records we learn from and test against",
                                         "items": [{"name": F + "dataset", "href": F + "https://doi.org/...", "detail": F + "publisher · scope · licence"}]}}]},
        "cards": {"type": "cards", "id": "uses", "nav": "Uses", "eyebrow": "Who it helps", "heading": F + "One X, many users",
                  "cards": [{"icon": k, "title": F + "audience", "bullets": [F + "what they get, one sentence"]}
                            for k in ("flame", "shield", "flask", "city")]},
        "stats": {"type": "stats", "id": "accuracy", "nav": "Accuracy", "eyebrow": F + "Tested against ...", "heading": F + "headline claim, honest",
                  "lede": F + "how it was tested (out-of-sample?) and what the scores do NOT cover",
                  "stats": [{"value": NUM, "label": F + "what it measures, pooled or per-case", "scope": F + "cases, years, place",
                             "tip": F + "exact definition", "src": F + "document, section"} for _ in range(4)],
                  "bar_cards": [{"title": F + "results by kind", "key": [{"color": "navy", "label": F + "first measure"}, {"color": "gold", "label": F + "second measure"}],
                                 "rows": [{"name": F + "group", "scope": F + "scope", "bars": [{"value": NUM}, {"value": NUM}], "src": F + "document, section"}],
                                 "note": F + "explain the score in words",
                                 "checks": {"items": [F + "what truth is", F + "how each case was held out", F + "what is pooled"]}}],
                  "footnote": "All results are research estimates from a model, not official assessments."},
        "prose": {"type": "prose", "id": "limits", "nav": "Limits", "eyebrow": "Where it struggles", "heading": "Where we still need to improve",
                  "paragraphs": [F + "what it does best, with jargon defined", F + "where it does worse and why (no statistics; merge causes that are the same)",
                                 F + "how each of these improves (more records, partners, time) and <a href=\"#partner\">we would like to work with you</a>."]},
        "cta": {"type": "cta", "id": "partner", "nav": "Work with us", "nav_cta": True, "eyebrow": "Work with us", "heading": F + "Test it on your ...",
                "lede": F + "the most useful help, and one checked proof point",
                "steps_card": {"title": F + "A small pilot", "steps": [F + "<b>You share ...</b> under your terms.", F + "<b>We run ...</b>", F + "<b>You get ...</b>"]},
                "contact_card": {"title": F + "the bigger idea", "body": F + "one or two sentences; who you welcome introductions to"}},
        "team": {"type": "team", "id": "team", "nav": "Team", "eyebrow": "Research team", "heading": "Who we are",
                 "lede": F + "one line naming the institutions, with links",
                 "people": [{"name": F + "Name", "role": F + "title as on the institutional roster", "line": F + "one line",
                             "links": [{"label": "NCEAS roster", "href": "https://www.nceas.ucsb.edu/about-us/our-people"}]}]},
        "refs": {"type": "refs", "id": "refs", "eyebrow": "References", "heading": "Data and papers",
                 "refs": [{"name": F + "title", "href": F + "https://doi.org/...", "detail": F + "authors, year, publisher · licence"}]},
        "footer": {"type": "footer", "disclaimer": F + "who did the research (confirm the institutions with the owner), then: shared "
                   "for information only. Results are research estimates, not official assessments; do not use them in an emergency "
                   "or as the sole basis for a decision. (Say what is true: a program with no results yet has no estimates to warn about.)",
                   "credits": F + "Data: every source with its licence."},
    }


def ask(prompt: str) -> str:
    return input(prompt).strip() if sys.stdin.isatty() else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out", type=Path)
    ap.add_argument("--title")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--description")
    ap.add_argument("--contact-name")
    ap.add_argument("--contact-email")
    ap.add_argument("--sections", default=",".join(DEFAULT), help=f"comma list from: {','.join(ORDER)}")
    ap.add_argument("--open", action="store_true", help="public page: no lock-screen block")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.out.exists() and not a.force:
        sys.exit(f"new_site: {a.out} exists (use --force to overwrite)")
    title = a.title or ask("Program name (the page title): ") or F + "Program name"
    want = [s.strip() for s in a.sections.split(",") if s.strip()]
    bad = [s for s in want if s not in ORDER]
    if bad:
        sys.exit(f"new_site: unknown section(s) {bad}; choose from {ORDER}")
    secs = sections(title)
    spec = {
        "$schema": os.path.relpath(SCHEMA, a.out.resolve().parent),
        "_how": "Replace every FILL: (build_site.py refuses to build while one is left). Every number gets a src note. "
                "Delete sections you have no real content for. Guide: references/site-spec.md and references/content-and-claims.md.",
        "page": {"title": title, "date": a.date,
                 "description": a.description or F + "one public sentence (20-300 characters): it is visible even when the page is PIN-locked"},
    }
    name = a.contact_name or ask("Contact name for partners (Enter to use site.json): ")
    email = a.contact_email or (ask("Contact email: ") if name else "")
    if name and email:
        spec["contact"] = {"name": name, "email": email}
    if not a.open:
        spec["gate"] = {"tagline": F + "one public sentence for the lock screen: names and purpose only, no numbers or results",
                        "access_text": F + "This research program from [the institutions the owner confirms] is shared privately. ",
                        "button": "Open the site"}
    if "chart" in want and "tiles" in want:          # the wildfire pattern: the chart sits above the tiles
        secs["tiles"]["chart"] = secs["chart"].pop("chart")
        want = [w for w in want if w != "chart"]
    spec["sections"] = [secs[s] for s in ORDER if s in want]
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n")
    n = json.dumps(spec).count(F)
    print(f"wrote {a.out}: {len(spec['sections'])} sections, {n} FILL: markers to replace")


if __name__ == "__main__":
    main()
