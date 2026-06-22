# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45
**Date:** 2026-06-22
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now explore the "Severity-velocity x Regime" study by navigating to Research in the sidebar and clicking the "Severity-velocity x Regime" lab card, which opens the study at `/research/severity-velocity`.
- Users can now read an honest, plain-language verdict on whether rising market stress under a given regime predicts the next market move — the page states directly that the hypothesis is NOT supported on the current data (rising stress under a red regime historically preceded a bounce, not a decline).
- Users can now pick a forward-return horizon (5, 10, 20, or 60 days) on the severity-velocity study and see the mean forward SPY return, win-rate, and observation count update for each regime-family x velocity-sign cell.
- Users can now switch the severity-velocity study between all-history aggregate and as-of point-in-time mode, limiting the observation set to dates on or before a chosen date.
- Users can now click any "N=" chip in the severity-velocity matrix to open, in a new tab, the exact list of dates and SPY returns behind that cell — the count in the drill-down tab always matches the published N in the matrix.
- Users can now navigate to each Research lab individually — `/research` is now a hub menu with one card per lab; clicking a card opens only that lab's analysis (no other analyses load).
- Users can now bookmark or share a direct URL to any individual Research lab (e.g. `/research/event-study`, `/research/regime-setup-pattern`, `/research/downtrend-opportunity`) and land directly on that lab.

---

## What Changed in the Visible UI

- The `/research` page is no longer a long scrolling page showing every analysis. It is now a card grid (hub) listing seven labs by name with a short description; the heavy analysis content is gone from this page.
- Seven new pages exist under `/research/*`: `factor-lab`, `factor-combination`, `event-study`, `regime-setup-pattern`, `recovery-turn-edge`, `downtrend-opportunity`, and `severity-velocity`. Each renders exactly one lab.
- A new page at `/research/severity-velocity` shows a regime-family x velocity-sign matrix (rows: Risk-on / Neutral / Risk-off "red"; columns: Rising / Flat / Falling), a horizon selector, the As-of mode toggle, the honest verdict card with survivorship/bull-dominated/underpowered caveats, and N= drill-down chips per cell.
- The Research Samples page (`/research/samples`) gains a new readable cohort description for "severity-velocity" drill-downs (previously only recognized event-study and regime-setup-pattern cohort kinds).
- The sidebar "Research" link still points to `/research`; the active-highlight on the sidebar entry now illuminates for any sub-route under `/research/*` (not just the hub itself).

---

## What Old Behavior Changed

- Research navigation: previously visiting `/research` showed all six labs stacked on a single page, firing four or more heavy backend fetches simultaneously. Now `/research` shows the hub grid only; each lab is reached by a separate click to its own URL. All existing lab figures are unchanged — this is a layout and performance change, not a numbers change.
- Research page load time for the Multi-factor Combination and Regime x Setup x Pattern labs: previously these recomputed from scratch on every visit. Now they read from a stored cache after their first computation, so repeat visits return immediately with identical figures.
- The downtrend-opportunity study's historical run scan is now bounded to dates on or before the selected as-of date; previously it scanned the full run table regardless of the as-of filter. Figures remain byte-identical for any valid as-of selection.

---

## Not Visible Yet

- None. Every new backend capability (the severity-velocity study, its endpoint, the new sample cohort kind, and the cached factor-combination / regime-setup-pattern wrappers) is wired to a user-accessible UI surface.
