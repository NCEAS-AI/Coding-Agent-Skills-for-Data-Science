# Content and claims: what a landing page may say, and how

Distilled from about a dozen rounds of owner feedback and adversarial fact-checks on the team's two landing pages
(Nov 2026): the open National Wildfire Structure Loss Record and a PIN-locked research-program page. Every rule
below was broken at least once on those pages before it was written down. Read it all before writing a spec.

## Honesty and claims

1. **Say what the program does now, and what it is trying to do; never claim what it does not do yet.** Early drafts
   promised coverage and certainty the program did not have. A model's call is an estimate that is sometimes wrong,
   and the page must read that way. A program with no results yet says what it will produce and claims nothing more.
2. **Call model outputs research estimates**, not inspections, assessments or official results, in the hero and in
   the footer disclaimer ("do not use them in an emergency or as the sole basis for a decision about a property").
3. **Lead with the cases the program is built for, and never hide where it is weak.** A draft that averaged
   everything undersold the work; the next one hid the weak cases. The answer is both: best case up front, an honest
   Limits section below that says plainly where the program has trouble.
4. **Show one weak example** on the map or tile row, flagged, with a pop-up that says why it is weak and what would
   fix it, linking to the partner section.
5. **Unproven causes are "Likely reasons", never "Why".** Never borrow a cause measured on another case: a fact-check
   refuted a cause copied from a different fire, whose own data ran the other way.
6. **State the scope next to every number**: which cases ("fires that destroyed 10 or more buildings, lower 48
   states"), the period, the class of thing counted. Numbers without scope read as the whole population.
7. **Say how each headline score was tested** (held out: "each fire scored by a model version that never saw it")
   **and summarized** (pooled vs per-case; when they differ, show both: "0.97 pooled (0.91 averaged per fire)").
8. **Never compare numbers measured differently** (a whole-system score against a one-step score; percentages with
   different denominators), and never write "measured the same way" without checking.
9. **Every number traces to a primary source.** Keep the source in the spec's `src`; compute nothing fresh unless
   the computation is recorded. Recompute derived tables from the primary file and assert the published total (a
   per-year table once summed wrong; use the chart's `assert_sum`).
10. **When a publisher's own count differs from yours, use theirs and footnote the difference** (USGS publishes
    362 fires; the point file has 361 fire IDs: the page says 362 and notes the 361).
11. **Do not imply future events nobody has committed to.** "Not in the USGS record", not "not yet recorded" (do not
    imply anyone will extend a record unless they have said so publicly).
12. **A proposal is not current practice**: "we have proposed X", not "the system does X".
13. **"Under way" and "complete" must match the status record.** A check not started is a next step; a partial or
    combined product is not a "first complete" anything.
14. **Licensed partner data is never shown record by record**, only as attributed aggregate counts; pick a
    public-domain example for anything shown in detail.
15. **Do not name a prospective partner while the request is pending**: "a state agency's field damage records",
    not the agency's name, until they have agreed to be named.
16. **Small claims get checked too**: attribution ("Europe's Sentinel-2", not "ESA's");
    "agencies record damage differently", not "each agency uses its own"; date-bound counts ("443 fires from 2013 to
    2025"); round half-up.
17. **No links from an open page to PIN-locked pages.**
18. **No price or funding amounts.** A program page is standalone, not part of the institutional website.

## Section patterns (what each section is for)

| Section | Pattern | From the source pages |
|---|---|---|
| Hero | One compact paragraph: what we do, what we are trying to do, who it is for, that outputs are research estimates, where it is weaker, that partners' data close the gaps. No question-and-answer opener (the owner rejected one), no statistics (they compete with the text). A program with no results yet: what it will produce and when. | "We are building a national record of the buildings that wildfires destroy, picking up where the U.S. Geological Survey's record ends in 2022. ... These calls are research estimates, not inspections. ..." |
| Map (second, always) | Close-in views of 3-4 real cases, one of them weak; tiles under the map with the number and its counts; click moves the map. Choose dense cases; tighten empty windows; a dashed line marks the area each tile counts; colour key on hover, not in boxes. | Four fires; Sugar flagged "Where it struggles" with "Why the model misses in Doyle". |
| Why it matters | Must not look small: a bigger lede, a chart, four tiles in a row. The problem in the reader's terms. | "Knowing what burned is slow, patchy and hard to compare"; USGS per-year chart with 2023 on hatched. |
| What you get | "Public X in → Y out": three steps, the inputs as chips with tooltips, the reference records in a collapsible list. | "Public imagery in → building losses out". |
| Who it helps | Two to four audiences, one bullet each. Use the audiences the owner names and drop any they do not want. | Fire agencies; Recovery and resilience; Researchers; Planners and policy. |
| Accuracy | Stats strip (each with scope and a tooltip definition), results by kind, results case by case, "How these results were checked", a disclaimer line. The heading scopes the claim: which kind of thing, and where it was tested (e.g. "on California-inspected fires"). | "Accurate where it counts: homes and significant buildings" (approved for that page only; it names the building class, and the stats under it name the fires). |
| Limits | Short prose, no statistics, causes merged when they share a cause, each weakness framed with how it improves (more inspected data, partners, time), ending with a link to the partner section. | "Where we still need to improve". |
| Work with us | A small concrete pilot (three numbered steps), one checked proof point, a contact button. | "Test it on your fires": a validation-only pilot. |
| Team | Initials avatar, name, role (as on the roster; ask when they disagree), one line, roster and LinkedIn pills. | Three people. |
| Footer | Disclaimer, data credits with licences, build date, institutional links. | |

A different program needs its own structure: reuse the design, but build the order around why an outside reader
would care. The owner rejected a page that copied another page's structure too closely and asked for it to be
rebuilt around its own audience. **The owner's structure always wins** over this table and over `new_site.py`'s
skeleton: three tiles, no chart, no map, no accuracy section are all fine when that is what the program has.
A research program with phases (Phase 0, 1, 2) has no builder section yet: the tab styles are in `site.css`
(`.phase-tabs`), but a `phases` section type must be added to `build_site.py` and the schema before a page can use
one; until then describe the phases in a `pipeline` section (one step per phase).

## Copy style

- **Far fewer words**: about one sentence per card (every round of feedback asked for fewer).
- **Define jargon on first use** ("significant structures: houses, apartments, businesses, schools and churches, not
  sheds, garages or outbuildings"; F1 explained in words under the bars).
- **US spelling** ("area", not "neighbourhood"); **plain, specific terms** ("inspection record", not "official
  record"; no internal project words a reader would not know).
- **Write commitments plainly**: who does what, and when ("the full dataset will be free online" becomes "we will
  publish X, free for anyone, by Y").
- **State scientific independence and that outputs are open** where the program commits to that (who decides the
  method; what will be published, under what licence).
- **Weaknesses are places to improve**, and say how they improve.
- **Use the audience words the owner chose**, in the order the owner gives.

## The claims pass (before every publish)

Run it on the built page's text, not the spec (what readers see is what counts):

1. List every sentence that carries a number, a comparison, a cause, a status ("under way", "first", "complete"), a
   capability ("we map every ...") or an attribution.
2. Two independent checkers per claim, each with the primary source, each told to refute it; then a refute pass on
   anything they disagree on. Rate: correct / overstated / wrong / unsupported. If your agent can start subagents,
   give each checker its own subagent with the page text, the claim list and the sources; if it cannot, do two
   separate passes yourself, the second one reading the sources fresh, and say in the handoff that it was a
   self-check. A page with no claims yet (a draft full of TBD) has nothing to check: say so, and run the pass when
   the numbers arrive.
3. Apply every confirmed fix, rebuild, and re-check the fixed sentences.
4. Re-run the pass **every round, including copy-only changes**: each round of the source pages surfaced new
   overclaims rated "wrong" or "must-fix".
