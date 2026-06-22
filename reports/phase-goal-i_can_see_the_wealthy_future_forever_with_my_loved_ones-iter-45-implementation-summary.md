# Goal Iteration 45 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45
**Date:** 2026-06-22
**Written by:** developer

---

## Features Implemented

- **Severity-velocity × Regime study (J-103)**: A new Research lab answers "does rising or falling market
  stress under a given regime predict the market's next move?" It shows a grid where the rows are the
  market-regime family (risk-on / neutral / risk-off "red") and the columns are the direction of stress
  (rising / flat / falling). Each cell reports the average forward market (S&P 500 / SPY) return, the
  win-rate, and how many observations it is based on. It lives at its own page, `Research → Severity-velocity
  × Regime`, reached from the new Research hub.
- **Honest verdict on the study**: The page states, in plain language, that on the loaded data the
  hypothesis is NOT supported — rising stress under a "red" regime was historically followed by a bounce,
  not a further decline — and openly flags that the sample is survivorship-biased, bull-dominated, and
  underpowered for sustained crashes until deeper history is loaded.
- **Drill-down on every number**: Clicking any "n=" sample-count chip in the grid opens, in a new tab, the
  exact list of dates and returns behind that number — and the count always matches the published figure.
- **Research is now a hub of fast, individual labs (J-104)**: The Research section used to be one long page
  that loaded every heavy analysis at once (which was slow and sometimes failed). It is now a simple menu
  (hub) that links to seven labs, each on its own page that loads only its own analysis — so any one page
  does at most one heavy computation.
- **The slow labs are now cached (J-104)**: The two analyses that previously recomputed from scratch on
  every visit (Multi-factor combination, Regime × Setup × Pattern) now reuse a stored result, so repeat
  visits are fast. The numbers shown are exactly the same as before.

---

## Changed Behavior

- **Research navigation**: Previously `/research` showed all six labs stacked on one page. Now `/research`
  is a hub menu; each lab opens on its own page (e.g. `/research/event-study`). Every lab is still reachable
  in at most two clicks and every page link is bookmarkable.
- **Research page speed/reliability**: Previously visiting Research fired four heavy analyses at once (slow,
  occasional load failures). Now each page runs at most one heavy analysis, and the two heaviest analyses
  are cached after their first run.
- All displayed figures across the relocated labs are unchanged (byte-identical) — this is a speed and
  layout change, not a numbers change.

---

## Backend-Only Items

- None — every new backend capability (the severity-velocity study, its endpoint, and its sample drill-down)
  is wired to the new `/research/severity-velocity` page and the existing Research Samples page.

---

## Incomplete Items

- None of the in-scope items are deferred. (The study's empirical strength for deep market crashes improves
  later when pre-2021 history is loaded — that is explicitly out of scope and non-blocking; the study is
  fully built and correct on the current data.)

---

## Config and Environment Changes

- `config.yaml` → new `research.severity_velocity` section: it defines the three regime families (risk-on /
  neutral / risk-off) by grouping the existing regime labels, and the three stress-direction labels (rising
  / flat / falling). No code change is needed to retune these — they live in config. Default values ship in
  the file.
- No database migration. The study reuses the existing results cache table; no new tables were added.
- No new environment variables.

---

## Known Limitations

- The severity-velocity study does not offer the "Episodes vs Pooled" toggle the other labs have. That
  toggle de-duplicates repeated signals for the same stock; this study looks at one market-wide (S&P 500 /
  SPY) observation per date, so there is nothing to de-duplicate and the toggle would do nothing. The
  point-in-time "As of date" mode is fully supported.
- The Recovery-Turn Edge lab was given its own page too (in addition to the five pages named in the plan),
  so that it is not orphaned and the "one heavy analysis per page" rule holds.
- The heavy Research analyses are slow the very first time they run (while the result cache is empty and the
  app is still warming up its history). That first run fills the cache; later visits are fast. This is the
  exact slowness the caching work addresses. The analyses should not be opened all at once.
- The full automated backend test suite was running at the time this summary was written and is the
  pipeline's gate to confirm green; the targeted tests for this iteration's new code all pass, and the new
  page builds and type-checks cleanly. The live page render is verified by the browser-QA step.
