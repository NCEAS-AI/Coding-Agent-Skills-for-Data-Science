# Review: what to check before every publish

Each check below caught a real problem on the source pages. Do all of them every round, including copy-only rounds.

## 1. Automatic checks

```bash
python3 $SKILL/scripts/build_site.py SPEC.json OUT_DIR/        # schema, ids, anchors, paths, unsafe HTML, unfinished text, sums
python3 $PAGES/scripts/check_page.py OUT_DIR/PAGE.html          # what publish.py will enforce
```
Expected check_page output: `WARN no dark-mode styles` (light only by design). Anything else is a real problem: fix
it. check_page does not look at the contact email: build_site refuses placeholder addresses (`example.org`, `.test`)
unless `--draft`, and a `--draft` page carries a "Draft for review" bar that must never reach a publish (check_page,
and so publish.py, stops on it as unfinished text; verify_gate.py refuses it too).

## 2. Screenshots, and look at them

```bash
mkdir -p shots                                                   # screenshot.py does not create folders
python3 $PAGES/scripts/screenshot.py PAGE.html shots/full --full --sizes desktop,tablet,phone --wait 8
python3 $PAGES/scripts/screenshot.py PAGE.html shots/top --sizes desktop,laptop,phone --wait 8          # the header as a reader first sees it
python3 $PAGES/scripts/screenshot.py PAGE.html shots/map --hash map --sizes desktop,phone --wait 20    # the map on its own
python3 $PAGES/scripts/screenshot.py PAGE.html shots/partner --hash partner --sizes desktop,phone      # a section below the map
```
- Sizes: desktop 1400 × 900, tablet 820 × 1180, phone 390 × 844 @2x. Exit status 1 = JS errors or the page scrolls
  sideways on a phone (it prints the widest elements).
- **Full-page captures of a page with a tall map iframe repeat the top of the page after the map section** (a
  capture artifact, also seen on the live wildfire page): check sections below the map with `--hash SECTION_ID`, and on
  phones prefer `--hash` captures to `--full` (a full phone capture also stretches the map to 76% of the whole page).
- **The map is judged only on its own `--hash map --wait 20` shot.** The iframe loads lazily, so a `--full` capture
  often shows an empty grey frame even when the map works (and can show a drawn map when a later load fails). In the
  map shot, check that the base map, the buildings and the dashed frame are drawn; only then is an empty frame in the
  full capture a timing artifact.
- Open every image (`Read` the PNGs) and check: logo row, nav, CTA pill and Lock button fit on one line at desktop
  (1400) and laptop (1280), nothing cut off at the right, the CTA right-aligned next to Lock (from 1241 px a locked
  page shows its first 5 section links, an open page its first 7; below that only the CTA pill); hero has no stats; map frame and tiles in one row; weak tile is purple
  with its flag; chart labels do not collide (annotation, gap label, x labels); tiles in a row, no big white gaps;
  alternating backgrounds; cards equal height in a row; footer complete; on the phone, nothing cut off or overlapping.

## 3. Interactions (on a test copy)

Copy the page to `_test_PAGE.html`, serve the folder (`python3 -m http.server`), and check by hand or with a short
script (screenshot.py `--eval` runs one JS expression): a map tile click moves the map (the embed answers
`{goPlace}`); the weak tile opens the pop-up; the pop-up's close button works and it does not cover the map's place
list; a tap tooltip never covers the pop-up; "See the numbers" opens; anchors scroll to their section. Delete the test
copies before publishing.

A page without a map still has tooltips, anchors and (maybe) a table to check; one command does it on the plain file:

```bash
python3 $PAGES/scripts/screenshot.py PAGE.html shots/tip --sizes desktop --eval "(() => { const t = document.querySelector('.dotted, .stat, .col'); if (t) t.dispatchEvent(new PointerEvent('pointermove', {pointerType: 'mouse', clientX: 300, clientY: 300, bubbles: true})); const d = document.querySelector('details'); if (d) d.open = true; return {tip: document.getElementById('tip').classList.contains('on'), anchors: [...document.querySelectorAll('a[href^=\"#\"]')].every(a => document.getElementById(a.getAttribute('href').slice(1)))} })()"
```

## 4. The claims pass

`references/content-and-claims.md`, "The claims pass": two independent adversarial checkers per claim against the
primary source, a refute pass, every confirmed fix applied and re-checked. Look especially for: scope missing from a
number, pooled vs per-case not labelled, comparisons across different measures, "first / complete / under way" not
matching the status record, causes stated as fact, a proposal described as practice, a count that differs from the
publisher's, a partner named before they agreed.

## 5. The lock (locked pages)

`references/lock-screen.md`: `verify_gate.py` (branded, no leaks, decrypts with `--expect`), `test_lock.py`
(fresh-browser unlock, re-open without prompt, no console errors), lock-screen screenshots at desktop and phone.

## 6. After publishing

Live checks from `lock-screen.md` and the link click-through from `publishing.md`; then the handoff note.

## Checklist (copy into the round's notes)

- [ ] build_site OK, check_page only the expected warnings
- [ ] desktop / tablet / phone screenshots looked at; no sideways scroll; sections below the map checked with --hash
- [ ] header at desktop and laptop looked at (nothing cut off; locked pages: 5 links, CTA next to Lock); map checked in its own --hash map shot
- [ ] interactions tested on a test copy (deleted)
- [ ] claims pass done; every fix applied and re-checked
- [ ] every number has a `src`; no private path, partner record or pending partner name on the page
- [ ] lock: verify_gate PASSED, test_lock PASSED, lock screenshots looked at (or: user said the page is public)
- [ ] no newer edits by anyone else; published with --wait; LIVE
- [ ] live: verify_gate on the downloaded page, test_lock on the URL, every link clicked
- [ ] link handed over; nothing emailed; handoff written
