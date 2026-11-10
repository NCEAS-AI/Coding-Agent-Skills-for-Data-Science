# Example: the National Wildfire Structure Loss Record page as a site spec

`wildfire-structure-loss-record.json` rebuilds the team's open landing page, live since 2026-11-06 at
<https://wri-science.github.io/public_publication/publication_htmls/structure_loss_pipeline/national-wildfire-structure-loss-record-2026-11-06.html>,
with this skill's builder:

```bash
python3 scripts/build_site.py examples/wildfire-structure-loss-record.json OUT/example.html --draft
```

`--draft` is needed because the contact is a placeholder (see below): the build then warns instead of stopping, and the
page carries a "Draft for review" bar. Set a real contact to build it clean.

Where the content came from:

- **Every sentence and number is copied from the live, public page** (version of 2026-11-09). Nothing in it is
  unpublished. The `src` notes cite public sources (the USGS data release, CAL FIRE's open data) or say "as published
  on the live page"; the program's internal result notes behind the model scores are not public and are not cited.
  **Do not copy that habit**: "as published on the live page" stands in for private notes here only. A new page cites
  the primary document and section behind every number; citing your own page is circular.
- **Shortened**: one reference line about non-California inspection records was left out of the reference list.
- **No contact in the spec**: the live page names its real contact. The build takes yours from
  `~/.config/external-facing-website/site.json` (or a `contact` block you add to the spec) and stops if neither is set.
- **The map** is the live four-fire embed, by absolute URL
  (`four-fires-map-embed-2026-11-06.html` on the same site), built with wri-html-pages `build_map.py`. Its data are not
  in this repo. Opened from a local file, tile clicks still message the embed, which only answers pages on its own site.
- `gate.lock_button` is false because the live page is open; the spec still carries a `gate` block, so the same page
  can be published locked (with the branded lock screen) as the team's locked alias was. That is why
  `gate.access_text` says "shared privately": it describes the locked copy. For your own page, write it for the
  access that page really has, and name the institutions the owner confirms.

Built with build_site.py 1.0.0, the page matches the live one section for section (same CSS, fonts, logos and
markup patterns); it differs in the contact, the left-out reference line, the generated timestamp and the
lock-screen blocks.
