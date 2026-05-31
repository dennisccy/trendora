# Goal Iteration 10 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future-iter-10
**Date:** 2026-05-31
**Written by:** developer

---

## Features Implemented

- **Backtest / Time-Machine workspace (`/backtest`)**: A new page in the sidebar (between *Scanner Runs*
  and *System Health*) where you pick any past scan date and see two things for that date — the as-of scan
  summary and a forward-test scorecard.
- **As-of scan summary**: For the chosen date, the page re-shows that day's market regime (label + 0–100
  score), candidate counts, top sectors, top themes, and the ranked stock cohort. These come from the same
  existing endpoints the Dashboard, Stocks, Sectors, and Themes pages already use — so the numbers match
  exactly (nothing is recomputed for this page).
- **Per-date forward-test scorecard**: A table that answers "did that date's ranked cohort actually pay
  off?" For each forward window (1, 5, 10, 20, 60 trading days) it shows the top-ranked cohort's realized
  mean return, how much it beat/lagged SPY, QQQ and its own sector, plus a random same-sector control and
  the SPY/QQQ/sector-ETF benchmarks. Every figure shows its sample size `n`.
- **Honest gaps**: Windows that have not fully elapsed in the frozen data show "—" (NA) with `n=0` — never
  a fabricated 0%. The latest date (which has no future data yet) shows an all-NA scorecard with an
  explanatory empty state.
- **Survivorship-bias banner + "Viewing as-of D" indicator**: The page always shows the honest caveat that
  the evidence is measured on the current-membership universe, and a clear badge of which date you are
  viewing (and whether it is the latest or a historical date).

---

## Changed Behavior

- **System Health page**: No visible change. Its return-formatting helpers (percent formatter, green/red
  grading, sample-size tag) were moved into one shared module that both System Health and the new Backtest
  page now use, so the two pages format returns identically. Behaviour is unchanged.

---

## Backend-Only Items

- None. Every backend capability added this iteration (the `/api/backtest` endpoint and the per-date
  scorecard) is reachable through the new `/backtest` page.

---

## Incomplete Items

- None for this iteration's scope. The scorecard is intentionally cohort + excess + control-group only;
  by-bucket / by-setup cross-date breakdowns remain System Health's job (out of scope here).
- **VCP detection (J-16)** and the **config-backed glossary / `/methodology` (J-12)** are explicitly out of
  scope — they are the next iterations.

---

## Config and Environment Changes

- None. No new environment variables, no config-file changes, no schema/table changes. The scorecard reuses
  the existing `walk_forward` config values (horizons, `min_sample`, control-group `top_n`/`seed`) and the
  existing append-only `forward_returns` table.

---

## Known Limitations

- **Frozen-seed window**: Recent dates legitimately show NA for the longer horizons because the committed
  offline seed has no price bars after its latest date — this is correct, honest behaviour, not a bug.
- **Survivorship bias**: As surfaced in the banner, the forward-test evidence is measured on the
  current-membership universe, so realized returns can be overstated. Read the edge as an upper bound.
- **Two date controls visible on `/backtest`**: The page has its own as-of date picker (by design,
  independent of the global top-bar switcher). The global top-bar switcher remains visible but does not
  drive the Backtest page; only the page's own picker does.
- **Browser QA runner**: The dedicated browser-QA step has historically skipped on a CORS/port flap
  (runner-owner issue, not product scope). The backend endpoint and the page build are verified by unit/API
  tests and a clean production build; on-disk evidence captures should be reconciled if the browser step
  skips again.
