# Rigor pass: check every panel before it is published

Carlo, 2026-10-12, on a panel that compared 2007–12, 2013–22 and 2023–26 losses: "The years are not the
same number of years, so it's not a like-for-like example … this skill should, on each panel, back up and
make sure that what it's showing is statistically and scientifically rigorous. That data visualization is
misleading."

What was wrong with that panel, so the pattern is recognisable:
- periods of 6, 10 and ~3.7 years compared side by side;
- the partial year 2026 (data to 31 August) divided as if it were a full year, while 51% of losses since
  2007 came from fires starting September–December;
- each bar dominated by one year (2018 = 39% of 2013–22; 2025 = 67% of 2023–26) but shown as a steady rate;
- a heavy-tailed quantity (destroyed per fire) summarised by means and decomposed between periods;
- "no further rise" claimed from 3 full years, with no interval;
- two sources (IMSR, ICS-209-PLUS) and two period definitions in one caption;
- an interval for a share running past 100% (69%–109%) shown without comment.

## The checklist (every panel, before screenshots)

Go through it for each chart, table and map panel. **Fix the design first** (equal windows, full years
only, a per-year view, a robust statistic); only what cannot be fixed becomes a caveat. Record what you
checked with `vk.card(..., checks=[...])` (shown under the panel as "How this panel was checked").

1. **Like for like.** Compared groups cover equal spans (equal-length periods, or one bar per year), the
   same population, the same source and the same definitions. No partial period next to full ones:
   drop it, or show it separately and say what share of a normal year it covers. Never annualise a
   partial year by dividing by a whole year.
2. **Right denominator.** Counts versus rates: say which and why. Rates need the right exposure (per
   exposed building, per fire, per year of data). Pooled ratios weight big units: say so, or show per-unit.
3. **Heavy tails and dominance.** When one fire, year or place can dominate (fire losses usually can),
   show it: the largest unit's share, and the result without it. Prefer counts above thresholds, medians
   and quantiles over means; don't decompose differences of means of heavy-tailed data without a
   robustness check.
4. **Uncertainty from the independent unit.** Resample fires (or years), not buildings. Event counts get
   Poisson intervals. Shares stay within 0–100%; an interval outside that range means the method is wrong.
5. **Small n.** Show n. Don't call a trend from 3–4 points; grey out or drop cells below a stated floor.
6. **How the data were made.** Inclusion rules (e.g. fires with ≥ 10 destroyed), reporting changes
   over time, reports vs inspections, labels vs model calls, imagery dates. Each must be stated on the
   panel if it could change the reading.
7. **Encoding.** Bars start at zero; comparable panels share scales; stacked parts must sum to something
   meaningful; bins are consistent and stated; colour scales match meaning (rules in house-style.md).
8. **Claims match evidence.** Every sentence in a title or caption is supported by what the panel shows,
   including its interval. "No rise", "stable", "drives" need an interval that rules out the alternative;
   otherwise say "can't tell yet".

If a panel can't pass, don't publish it as is: redesign it, or replace it with the honest statement
("too few years to tell").
