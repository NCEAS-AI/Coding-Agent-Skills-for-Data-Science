# House style for every deck we present

The team's standing preferences for slide decks, collected from Carlo Broderick's feedback on the wildfire
structure-loss deck (24 Sep – 7 Oct 2026, 74 slides), the Parafire simulation deck (23 Oct 2026) and his
request for this skill (23 Oct 2026). Every deck made with wri-html-decks follows this file, **and** the page
skill's `references/house-style.md` (titles, audience, numbers, hovers, colour, who made it), which applies to
decks too. When the user corrects a deck, the correction belongs here (or in deckkit / the archetype) so the next
deck gets it right. Each rule says why, so edge cases can be judged rather than pattern-matched.

The archetype shows these rules applied (open data, shareable with anyone):
https://wri-science.github.io/public_publication/publication_htmls/style_archetypes/deck-archetype-palmer-penguins-species-sex-island-2026-10-23.html

## The deck is real slides, published like every other visual

- **Real 16:9 slides you page through, not a long page** (2026-10-23, on the Parafire deck that was a scrolling
  page: "it wasn't real slides"). deckkit draws every slide on a fixed 1920 x 1080 canvas, scaled to the window;
  arrow keys, space, swipe or a click move; F is full screen; the PDF button prints one slide per page.
- **Pushed as HTML to GitHub, every time, and linked** (2026-10-23: "have it be similar to the other skills in
  that it pushes it as HTML to GitHub repetitively"). A deck is published and linked exactly like a page: no asking
  whether to push, the link in every reply about it, open by default (PIN only on request).
- **One deck, one link, kept up to date** (2026-09-28: "is the presentation up to date? Please update it";
  2026-10-06: "this presentation doesn't look updated"). The deck keeps its start date in its title and file name,
  so each rebuild updates the same link; the change history sits in the Contents panel, not on the slides.
- **No speaker notes** (2026-10-23: "I don't need speaker notes at all"). What a reader needs goes in a hover tip
  or the (i); deckkit has no notes field.

## Where you are in the deck

- **A progress strip at the top of every slide** (2026-09-24: "an indicator of how many slides there are and how
  far through the entire slide deck we are at the top ... slide by slide"), plus "n / N" at the top right.
- **Grouped into sections, each in its own colour** (2026-09-28): one pill per slide; slides already seen in full
  colour, the current one taller, the ones to come faint; other sections not greyed out but less vibrant; each
  group has a small title, the current section's bigger and stronger (2026-09-28: "the section we're in should have
  a bigger and more prominent title"). deckkit draws it from `Deck.section(...)`; hover a pill for the slide's
  title, click a pill or a section name to go there.
- **One holistic theme** (2026-10-23): the same layout, type and colours on every slide; the colours may change by
  project, the structure does not. The title sits at the same place on every slide, so it never jumps. A deck has
  one designed palette for a screen or projector, not a light / dark switch (the page check's "no dark-mode
  styles" warning is expected); dark statement slides give it contrast.

## One idea per slide, shown rather than written

- **Not dense** (2026-10-23, on the Parafire deck: "too dense"). One idea per slide; a title that states it; a
  one-line lede at most; about 60 words of text or fewer (shoot_deck.py warns above that). When there is more, use
  two slides (2026-09-28: "if we need two slides to communicate this all, we should use two slides").
- **Iconography and pictures over paragraphs** (2026-09-28: "there's a lot of text ... viewers will have a lot of
  trouble associating or understanding things without more iconography or data visualizations"): numbered steps,
  flowcharts, icons for repeated concepts, real images, charts.
- **Flowcharts like a tournament bracket for how things combine** (2026-09-28: bands → indices → scores → model):
  `dk.bracket`. Put a big diagram on its own slide right after the slide that describes it.
- **Numbered circle badges for repeated concepts** (2026-09-28: circles, not flames, with the number clearly
  visible): `dk.badge(1, colour)`.
- **A statement slide when the story turns** (2026-09-28: a slide that only says "Why is this important?"), and
  **end a section with the one sentence to remember** (2026-09-29: "a big sentence, or maybe an infographic, that
  communicates the big deliverable"): `Deck.statement`.
- **Results, not our internal process** (2026-09-29: "that's information between you and me. That information
  should not leak into this presentation"). No build chatter, "caught a bug" strips or options we dropped.
- **Plain language** (2026-09-19: "explain in plain language"). Name things once and keep the name everywhere;
  explain every term the first time (2026-09-28, of "tree only version": "I don't understand ... explain that").

## Colour means something

- **One colour per concept, on every slide** (2026-09-24, 2026-09-28): a dataset, a model, a group keeps its
  colour through the whole deck, in charts, text and boxes.
- **Outline or shade a box in the colour of what it describes** (2026-09-24: "outlined by their associated colour
  so that people can associate each one"; "maybe just make the box shaded in those colours"): `dk.card(color=,
  fill=)`.
- **Tint a whole slide when it is about one concept** (2026-09-24: the first-call slides light green, the
  second-call slides dark green; 2026-09-29: the neural-network slides "a little bit more blue tones"):
  `Deck.slide(tint=colour)`.
- **Icons filled in the concept's colour** (2026-09-24: the map outline "should be filled in the whole same colour
  as the line has").
- **Keys big and friendly** (2026-09-28): `dk.key`, above or beside the chart, with text labels.

## Hover: every part explains itself, and the cursor never changes

- **Hover tips on everything that needs explaining** (2026-09-28: "every part of that tree should have hover
  tooltips"), **with a satisfying highlight** on the hovered thing (2026-09-28).
- **The cursor never changes** (2026-09-28: "I totally hate the question mark cursor change ... keep my cursor the
  exact same thing"; again 2026-10-23: "I just want my cursor to stay the same as the object is highlighted"). deckkit
  keeps the normal arrow everywhere on a slide (a real link gets the hand) and refuses a slide that sets a cursor.
- **Every number can be hovered to see how it was calculated** (2026-09-29). shoot_deck.py lists numbers without
  one; a table column is covered by a tip on its heading.
- **Every named cohort says exactly which cut it is and why** (2026-10-01: "when you say Carlson 199 or CAL FIRE 8
  ... let me hover over it and tell me exactly what cut of fires it is and why we are using it").
- **Tips add information or don't exist** (2026-09-29: "a lot of the times the hover tooltips just reiterate the
  text that's under them. If there's no useful additional information, don't put it"). shoot_deck.py counts tips
  that only repeat their label. Think ahead about what a reader will want (2026-09-29: the burn-indices tip should
  have listed and briefly explained each index).
- **Plain first, technical on a switch**, per slide (page house style, 2026-10-12 and 2026-10-15): a slide with
  technical text gets its own Plain | Technical switch beside the (i).
- **The (i) at the bottom right of every slide, never on top of content** (2026-09-29: "put it at the bottom
  right-hand side of every slide and just make sure that placement doesn't overlap with anything else"). It holds
  how to read the slide and the method in detail (2026-09-29: "explain that in detail ... under the information
  section").

## Charts that fit the slide

- **Drawn for the slide** (2026-10-23, on the Parafire deck: the charts and maps didn't fit): deckkit's charts are
  sized in slide pixels with labels of 22 px or more; nothing shrinks to fit (a chart that does not fit is an error,
  so split the slide).
- **Values printed on the bars, percentages where shares matter** (2026-09-29: "add percentages for the horizontal
  bar chart ... design it a little bit better so it's more intuitive").
- **Two bars per row when comparing two models or groups** (2026-09-29), each in its concept colour.
- **No grey "everything else" bar hiding the detail** (2026-09-28: "can we eliminate that gray section?"): break it
  into categories.
- **A threshold as a line on the chart, with the split it makes** (2026-09-28), and **a spectrum with class bands
  and heavy dividers** to show where cases fall (2026-09-29): `dk.scale`.
- **Text never overlaps lines or shapes** (2026-09-29, three times: "the text still runs over the lines of the
  circles"; "make sure the titles are within each area and not obscured by or close to the lines"). shoot_deck.py
  fails a slide where text overlaps text or a control.
- **Diagrams look like the thing** (2026-09-29: burned areas drawn as fire-like shapes, not circles; when a circle,
  a true circle, not an oval).
- **The rigor pass applies to every chart slide** (page skill `references/rigor.md`): like-for-like comparisons,
  full periods, the right denominator, uncertainty from the independent unit, claims no stronger than the evidence.

## Maps on slides

- **A still picture, not a map to scroll around in during the talk** (2026-09-28: "don't have it be dynamic, and
  don't let me scroll around. I just want ... a representative area ... and then maybe have a link to an HTML map").
  `dk.Frame` + `Frame.basemap()` + `dk.image(layers=...)`, and `dk.link_button` to the interactive map page made
  with the page skill.
- **Tabs between two or three places of interest** (2026-09-29: "I would like a couple of tabs with different
  places of interest from that same fire"): `dk.tabs`.
- **Each source in its own colour, toggled on and off** (2026-09-24: "one colour for the footprint and one colour
  for what our model has said ... a toggle to turn on and off those overlays"): `dk.key(toggle=)`.
- **Show the outline of what a result covers** (2026-09-29: the outline of the cells the model calls a building).
- Say which base map and imagery date it is in the footer (`Frame.credit()`).
