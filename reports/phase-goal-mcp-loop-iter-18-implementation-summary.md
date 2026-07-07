# goal-mcp-loop-iter-18 — Implementation Summary

**Phase:** goal-mcp-loop-iter-18
**Date:** 2026-07-06 (fix dispatch 10 — closeout)
**Written by:** developer

---

## Features Implemented

- **30-year price history**: The product now carries ~30 years of daily prices for a ~590-name universe
  (previously ~5 years / ~122 names). A long-tenured stock's chart and backtest reach back toward 1996 (or
  the stock's real first trading day); a recent IPO honestly shows only its short real history — no invented
  earlier prices.
- **Chart range control (Stock Detail)**: Each stock's price chart has a "Recent / Full history" toggle. The
  default view shows a bounded recent window (so a deep 30-year chart never loads every bar by default); the
  "Full history" option shows the whole real history, thinned to weekly points beyond a set age so it stays
  responsive. A caption discloses the stock's real first available date.
- **Regenerated evidence ledger (the sanctioned reset)**: Because the price basis changed, every previously
  "proven" edge was re-measured from scratch on the new 30-year data. None survived — so every "proven"
  claim across the product now honestly reads "Not yet proven" / a failed verdict. This is the evidence
  system working as designed (an edge that only held on the old, shorter data is correctly retired).
- **Recency / staleness exclusion (J-12)**: A stock whose data ends too long before the analysis date is now
  excluded from the point-in-time universe with a new, named reason ("stale series"), surfaced in the
  Methodology and Data diagnostics and in the membership-timeline counts.
- **Broadened point-in-time universe**: The leaderboard and membership timeline now reflect the wider
  ~548-name candidate pool across the deep history (entries and exits over time), not the old static ~122.

---

## Changed Behavior

- **Evidence badges**: Previously several edges showed "Proven" with specific numbers (e.g. +21.34%,
  p=0.0004998). Now every evidence surface reads "Not yet proven" / an honest FAIL with recomputed numbers
  and a new register date (2026-07-03). No retired value appears anywhere.
- **Price chart / backtest depth**: Previously charts floored around 2021 and backtests used ~2 years. Now
  charts reach each stock's real first bar (back toward 1996) and backtests use ~30 years (honestly floored
  at 2005-02-25, the benchmark's first committed trading day).
- **Ticker validation for charts / watchlist**: Previously only the ~122 configured names were servable. Now
  any broadened-pool member (or any stock with real stored bars) is servable; only a truly unknown ticker
  returns "not found".
- **Chart / watchlist performance (dispatch 9)**: Validating a ticker on every chart request and every
  watchlist add previously re-read and re-parsed the candidate-pool file from disk each time. It is now read
  once per boot and reused — the displayed result is unchanged, just faster.

---

## Backend-Only Items

- The deep world-index and macro series carried in the seed (`_SPX` / `_NDX` / `_DJI` / `_VIX` and the FRED
  macro proxies) remain loaded/committed but are NOT surfaced in any chart or page — surfacing them is a
  later iteration (J-14).
- Broadened-pool stocks have no sector label yet (the sector map covers the original ~122 names); their rows
  render honestly with no sector rather than a fabricated one. Wiring pool sectors is a later iteration
  (J-13 / J-14).

---

## Incomplete Items

- **Recent-window snapshot density (disclosed bounding)**: The point-in-time scanner snapshots use a bounded
  cadence — monthly across 2005→2026 plus daily only for the last trading month (and a residual daily stretch
  in early 2021). The originally-planned dense daily window proved too slow to compute in one pass on this
  host and was bounded via config and disclosed, not skipped. It can be densified later by widening one config
  value and running one backfill.

The full backend test suite run and both of its fix-verification passes are now fully complete (see Known
Limitations below for counts) — nothing test-related remains open from this phase.

---

## Config and Environment Changes

- `walk_forward.history_years`: 2 → 30 (backtest as-of window depth).
- `universe.filters.max_staleness_days`: 10 (new — the staleness exclusion threshold).
- `scanner.snapshot_cadence` (new): `deep_cadence: monthly`, `daily_start: 2026-06-01` — the disclosed bounded
  snapshot cadence.
- `scanner.bootstrap_dates`: added `2008-11-21` (GFC) and `2020-03-20` (COVID) regime dates.
- `chart_bars` (new): `default_years: 5`, `downsample_beyond_years: 8`, weekly interval — the chart range /
  downsample spans.
- No new secrets or credentials. No environment variables added.

---

## Known Limitations

- **Every "proven" edge is currently dark**: All seven historical claims failed re-certification on the deep
  multi-regime data, so the product shows statuses everywhere and confident numbers nowhere. This is the
  intended honest state after a data-basis change, not a defect. A future iteration may propose a new-basis
  claim through the normal certification gate.
- **Backtest floor is 2005-02-25**: Charts reach ~1996 per stock, but the backtest as-of window is honestly
  floored at the benchmark's first committed trading day (2005-02-25), not 1996.
- **Test-suite runtime (test-only, not the product)**: The 30-year data makes the full backend test suite
  very slow (~11.5 hours across two sequential chunks) because shared test fixtures warm the entire 30-year
  history up front. The running PRODUCT is unaffected — it boots fast and warms history in the background. The
  full suite has now COMPLETED with real counts: **1364 passed, 4 skipped, and 10+ failures, every one a stale
  test expectation the deep basis exposed — no product bug**. Those failures fall into two groups, all fixed:
  (1) six earlier failures fixed in dispatch 9 (data-floor edge dates, a memory guardrail raised for the
  30-year reality, a missing-sector allowance); (2) nine more the completed run newly exposed — a background
  "warm-up" test timeout that was set for the old, smaller universe (raised so the now-larger warm-up finishes)
  and a coverage count that was compared against the old ~122-name list instead of the new ~548-name pool
  (corrected). None of these change any product behavior or any displayed number; they only align the tests
  with the intended 30-year / 548-pool basis. **Both chained re-verification runs have now finished, confirming
  every fix, with zero failures remaining**: the first (9 tests, including the fixed "warm-up" date test)
  finished in 2h17m; the second (14 tests covering the background warm-up timeout and coverage-count fixes)
  finished in 5h17m. The full backend suite is closed out with no open test failures.
