# Assets: sources and licences

Extracted 2026-11-09 by decoding the `data:` URIs in two NCEAS landing pages (the open National Wildfire Structure
Loss Record page and a PIN-locked research-program page, design only) and their branded lock screens. No page text,
data or results are in these files. build_site.py inlines all of them into every page as data URIs.

| File | What it is | Licence / terms |
|---|---|---|
| `fonts/Inter-var-latin.woff2` (48 KB) | Inter, variable weight 400-700, Latin subset (Google Fonts distribution, unmodified). Body text. | SIL Open Font License 1.1. Copyright 2016 The Inter Project Authors. See `fonts/OFL.txt`. |
| `fonts/SourceSerif4-600-latin.woff2` (52 KB) | Source Serif 4 SemiBold (600), Latin subset (Google Fonts distribution, unmodified). Titles, big numbers. | SIL Open Font License 1.1. Copyright 2014-2023 Adobe, with Reserved Font Name 'Source'. See `fonts/OFL.txt`. Ship it unmodified under its upstream name; a re-subset or modified copy needs another family name. |
| `fonts/OFL.txt` | Full SIL OFL 1.1 text with both copyright lines. | (licence text) |
| `logos/ucsb-logo-navy.svg`, `logos/ucsb-logo-white.svg` | "UC SANTA BARBARA" wordmark, navy for the page, white for the lock-screen photo panel. | UC Santa Barbara trademark. Not open-licensed: use only on pages by UCSB / NCEAS teams, unaltered. |
| `logos/nceas-logo-dark.svg`, `logos/nceas-logo-white.svg` | NCEAS mark + wordmark, for light and dark backgrounds. | NCEAS (UC Santa Barbara) logo. Not open-licensed: NCEAS-affiliated pages only. |
| `logos/wri-logo.png` | Wildfire Resilience Index flame, 119 × 140 px, shown beside the two-line wordmark. | Wildfire Resilience Index (NCEAS) mark. Not open-licensed: WRI / NCEAS pages only. |
| `favicon.png` | WRI flame favicon, 64 × 64 px (same file as wri-html-pages `assets/wri-flame-icon.png`). | Same terms as the WRI mark. |
| `lock-aerial-naip.jpg` (194 KB) | Plain aerial photo of residential streets and lakes, 1080 × 1200 px, re-encoded from the source pages' copy (293 KB) at lower JPEG quality: it is shown under a navy gradient. No overlays, predictions or EXIF text. | USDA Farm Service Agency, National Agriculture Imagery Program (NAIP), Manatee County, Florida. U.S. Government work, public domain. Credit line on the lock screen: "Aerial photo: USDA National Agriculture Imagery Program, Manatee County, Florida." |
| `site.css` | The shared stylesheet. | Written for this skill (CC0 with the rest of the skill). |
| `site-spec.schema.json` | JSON Schema of the site spec. | CC0. |

Other teams: put your own logos next to your personal `~/.config/external-facing-website/site.json` and list them
in its `logo_row`; never use the UCSB, NCEAS or WRI marks for work that is not theirs. The link-preview image
(`og:image`) is a hosted URL set in `site.json`, not a file here.
