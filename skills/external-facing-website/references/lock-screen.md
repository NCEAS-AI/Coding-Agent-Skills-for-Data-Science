# The branded lock screen

Every locked page opens on the branded screen, never the plain "Enter PIN" box: the owner asked for the branded
screen on every locked page, including alias copies.

## How it works

wri-html-pages' `pin_gate.py` (1.13.0+) encrypts the whole page (AES-GCM, key from the PIN by PBKDF2; one site-wide
salt, so one PIN entry opens every locked page on the site in that browser session) and writes an unencrypted lock
screen in front of it. If the page's plaintext contains these four blocks, `brand_lock_screen()` copies them onto
that screen; `build_site.py` writes them right after the `<title>` unless `--no-gate-blocks`:

```html
<meta name="gate-title" content="Program name · NCEAS">            <!-- browser tab on the lock screen -->
<meta name="gate-button" content="Open the map">                    <!-- button text -->
<script type="text/x-gate-brand"> <style>fonts + lock CSS</style> photo panel, logos, title, "Enter your access PIN",
  <label for="pin">Access PIN</label> </script>
<script type="text/x-gate-foot"> "Need access? Contact NAME at EMAIL", institution links, fine print </script>
```

The blocks stay inside the encrypted copy too, so re-wrapping the page later keeps the branding.

Layout (from the source pages): desktop, a fixed photo panel on the left half (the public-domain USDA NAIP aerial under
a navy gradient) with the white logo row on top and the gold program line, white serif title, one-sentence tagline
and photo credit at the bottom; the form on the right (gold "Restricted access", navy serif "Enter your access PIN",
a "shared privately" line, the PIN field, a navy pill button). Under 900 px the photo becomes a band on top; under
640 px the tagline and credit hide and the short "Shared privately." text shows. A wrong PIN shakes only the field and
button (shaking the form would move the fixed photo panel).

Spec keys: `gate.tagline`, `button`, `eyebrow`, `title`, `tab_title`, `access_text`, `access_text_short`, `photo`,
`photo_credit`, `contact`, `links`, `fine_print`, `lock_button` (`references/site-spec.md`). Defaults come from
`site.json` (`lock_screen`, `contact`, `logo_row`).

## What may be on it (it is NOT encrypted)

Only: the program name, a one-sentence public description, logos, institution links, a contact name and email, a
public-domain photo with its credit. **Never** numbers, results, maps, partner names, screenshots of the page, or
anything not already public. build_site refuses a locked build when any `gate` text or the contact holds a
percentage or a score (F1, AUC, 0.93), and refuses a `</script` or any tag outside its allow-list there; `verify_gate.py`
fails when page content (dated title, hero paragraph, headings, headline numbers) is readable on the lock screen,
when any part of the branded screen is missing (photo panel, heading, PIN label, contact footer), and on a `--draft`
build.

**Also public even when the page is locked:** the file name and URL, the `<title>` text (publish.py copies it into the
folder README), the meta description, the commit message, `--describe` text, and every non-HTML file published with
it (only `.html` is encrypted; keep data inline). For a private program, write the title and description so they are
safe to show, and publish a map embed as `.html` in the same `--gate` call so it is locked too.

## Checking it

1. Locally, before publishing (use the real PIN from `$SLP_PIN`; for practice runs any test PIN works):
   ```bash
   SLP_PIN=... python3 $PAGES/scripts/pin_gate.py --gate PAGE.html PAGE.gated.html
   SLP_PIN=... python3 $SKILL/scripts/verify_gate.py PAGE.gated.html --expect "Four fires, building by building" --expect "map-embed"
   SLP_PIN=... python3 $SKILL/scripts/test_lock.py PAGE.gated.html --wrong-pin --expect "Who we are"
   mkdir -p shots && python3 $PAGES/scripts/screenshot.py PAGE.gated.html shots/lock --sizes desktop,tablet,phone --wait 3
   ```
   Look at both screenshots: photo panel, white logos, title, form, contact line. Compare with the previous release.
   Delete `PAGE.gated.html` afterwards (publish.py gates the plaintext again itself).
2. Live, after `publish.py --wait` reports LIVE: `curl -s URL > live.html`, run `verify_gate.py live.html --expect ...`,
   then `test_lock.py URL` (fresh browser: lock screen, PIN opens it, real content, the gated map embed inside it
   opens without a second prompt, opens again without a prompt, no console errors). The embed check only runs on
   the live URL: a local file cannot look inside the live embed. HTTP 200, a byte match or a visible form alone prove nothing; if this fails, the release is
   broken: say so and fix access before anything cosmetic.
3. `verify_gate.py --keychain-service NAME` reads the PIN from the macOS Keychain without printing it, if the
   publisher keeps it there. Never put the PIN in a file, a command line you save, a commit, a page or a message.

## Keeping addresses locked

- **An address that had a lock keeps the lock**, because publishing a locked address open, even briefly, exposes it.
  Do not rely on publish.py to stop you: it keeps an already-gated page gated only when neither `--gate` nor `--open`
  is passed; `--open` silently makes any page public, and a NEW page (such as an alias) in a gated folder goes out
  OPEN with only a note. So pass `--gate` explicitly for every address that was ever locked, read the dry run for
  the word OPEN, and run `verify_gate.py` on the live file afterwards.
- **Aliases** (a second address people were emailed): republish the alias every time the page changes, in the
  alias's original lock state, with the branded blocks (build with gate blocks even when the canonical page is open,
  so a locked alias gets the branded screen). See `publishing.md`.
- A Lock button in the header (default on locked pages) clears the session key and reloads to the lock screen.

## Known gate bugs on sibling sites (fixed in pin_gate; re-check on every release)

- The plain lock card overflowed on phones (fixed with `box-sizing: border-box`; the brand CSS sets it too).
- A white flash on unlock when the page loads an external stylesheet (fixed by preloading; these pages inline all CSS).
- A double gate (an old in-page PIN form inside a newly gated page) locked users out: never gate an already gated
  file (`pin_gate.py --gate` refuses one that starts with the pin-gated marker; build from the plaintext spec).
