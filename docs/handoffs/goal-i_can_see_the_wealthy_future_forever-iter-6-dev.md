# goal-i_can_see_the_wealthy_future_forever-iter-6 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-6
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete

## What Was Built

Two additive refinements of pages that already pass — **J-20** (Stock-Detail chart full path through latest, display-only) and **J-21** (Backtest leadership cohorts below Return Attribution, with horizon-linked realized returns). No new endpoint, no new canonical value, no nav/sidebar change.

### J-20 — display-only chart extension (Stock Detail)
- **`prices.bars_through_latest(session, symbol)`** — a new display-only accessor returning the symbol's FULL ascending bar list, NOT bounded by D (distinct from `bars_asof`). It is referenced ONLY by the chart endpoint — never by `scanner.run_scan` / `scoring.score_stocks` / `patterns.detect_vcp` (source-asserted), so post-D bars can never feed a score/bucket/setup/VCP/ranking.
- **`GET /api/stocks/{ticker}/bars?through=latest`** — an opt-in. When `through=latest`, the endpoint sources bars from `bars_through_latest`, computes the MA map over the full close series (display-only), and exposes the as-of boundary: it adds a top-level `latest_date` and a per-bar `is_forward` (`bar.date > as-of`). When `through` is omitted the response is **byte-identical to before** (bars ≤ D, no `is_forward`, no `latest_date`) so the no-lookahead default contract is obvious. The MA is a trailing `sma_series`, so the ≤ D values are identical with or without the forward extension (proven in tests).
- The chart (`/stocks/[ticker]`) opts in; the three scores + setup + VCP + invalidation still read `fetchStock` (the ≤ D snapshot) unchanged.

### J-21 — read-only leadership-return projection (Backtest)
- **`forward_testing._leadership_returns(ret_by_symbol, cfg)`** — a shared read-only projection (takes no Session, issues no query, recomputes no return — mirrors `_attribution_slices`). It derives, from the SAME `ret_by_symbol` dict the scorecard already built from the stored `forward_returns`:
  - `sectors`: one row per config sector ETF → the ETF's OWN stored return (`n` 0/1);
  - `themes`: one row per config theme slug → the equal-weight mean of member stocks' stored returns over members that HAVE a return (`n` = that count; honest NA when 0);
  - `cohort`: one row per universe ticker → the symbol's OWN stored return (`n` 0/1).
- Wired into `compute_run_scorecard`'s per-horizon loop as `leadership_returns` on each `by_horizon[*]` entry (alongside `attribution`). `GET /api/backtest` rides it verbatim — no new endpoint, no recomputed return, honest `null`/NA when a (row, horizon) lacks post-bars.
- The Backtest page reorders to **as-of scan summary (regime + counts) → forward-test scorecard → Return Attribution → Top Sectors, Top Themes, Ranked Cohort** (the three lists moved BELOW attribution), each gaining a realized-return column at the selected horizon. The horizon **view** selector's `viewHorizon` is lifted to page level so the ONE selector re-points both the attribution AND the three return columns; it remains a view selector (no refetch, no date param, no date state → J-18 preserved).

## Files Changed

- `apps/backend/app/engine/prices.py` — add `bars_through_latest` (display-only; documented as never routed into the scoring path).
- `apps/backend/app/api/stocks.py` — `stock_bars` gains opt-in `through`; `through=latest` → full series + `latest_date` + per-bar `is_forward`; default path byte-identical (≤ D).
- `apps/backend/app/engine/forward_testing.py` — add `_leadership_returns` helper; wire `leadership_returns` into each `compute_run_scorecard` `by_horizon` entry; docstring note.
- `apps/backend/tests/test_prices_asof.py` — J-20 engine tests: full-path accessor, asof++after partition, post-D bars don't change `bars_asof` (scoring input).
- `apps/backend/tests/test_bars.py` — J-20 endpoint tests: forward region + boundary, ≤ D MA matches default, latest-as-of no forward region, default contract unchanged, error contract preserved, source-seam (scoring modules never reference the full-path helper).
- `apps/backend/tests/test_backtest_scorecard.py` — J-21 tests: complete keyed projection, sector = ETF row, theme = equal-weight member mean, cohort = symbol's own row, equals a direct read of stored `forward_returns`, consistent with attribution, unobserved-horizon all-NA, recomputes-nothing keystone.
- `apps/frontend/lib/api.ts` — `PriceBar.is_forward?`, `BarsResponse.latest_date?`, `fetchStockBars(…, through?)`; `LeadershipSectorReturn`/`LeadershipThemeReturn`/`LeadershipCohortReturn`/`LeadershipReturns` types + `leadership_returns` on `BacktestScorecardHorizonRow`.
- `apps/frontend/components/price-chart.tsx` — accept `asofDate`; mute the `is_forward` candles + volume (palette tokens), place an as-of divider marker at D (`createSeriesMarkers`, lightweight-charts v5), legend "Forward — after as-of (display only)". No forward region at the latest as-of → chart visually unchanged.
- `apps/frontend/app/stocks/[ticker]/page.tsx` — chart panel opts into `through=latest`, threads `asofDate` to `PriceChart`, adds a one-line display-only caption when a forward region is present.
- `apps/frontend/app/backtest/page.tsx` — split `ScanSummarySection` into `AsOfScanSummary` (regime + counts, top) + `LeadershipListsSection` (the three lists below attribution with return columns); add `BacktestResults` holding the lifted `viewHorizon`; remove the old `BacktestAttributionSection` (inlined).
- `runs/goal-session-i_can_see_the_wealthy_future_forever/state/blueprint.md` — flip the J-20 (bars row) and J-21 (leadership-returns row) journey-home + Data-Contract notes from "target iter-6" to "built iter-6". No nav-skeleton change; no `blueprint.reapproval-requested`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_prices_asof.py tests/test_bars.py tests/test_backtest_scorecard.py -q`
Result: **42 passed** (the three files covering every changed backend surface; includes all new J-20 + J-21 tests).

Full-suite run: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` → **312 passed, 1 skipped** (16m41s). The 1 skip is the offline-skipped `@pytest.mark.integration` live-fetch test (expected without network). **No regressions** — every other test file still passes alongside the new J-20/J-21 tests.

Frontend: `cd apps/frontend && npm run build` → **compiled + typechecked successfully**, all 13 routes generated (no type errors).

Live smoke (real committed seed, backend on :8835, then stopped by port):
- `GET /api/stocks/NVDA/bars?as_of=2025-04-04&through=latest` → 1356 bars (1069 ≤ D + 287 forward, all dated > D), `latest_date`=2026-05-28; default (no `through`) → last bar = D, no `latest_date`/`is_forward`.
- `GET /api/backtest?as_of=2025-04-04` → each `by_horizon` carries `leadership_returns` (11 sectors / 11 themes / 122 cohort); XLK=+18.1% (n=1, the ETF row), NVDA cohort=+20.7% (n=1, own row), semiconductors=+23.2% (n=27, member mean); NVDA flips to +3.5% at horizon 1 (the horizon re-points the column).

## Known Issues

- **No regressions.** The full backend suite passed (312 passed, 1 skipped) alongside the targeted 3-file run (42 passed). The 1 skip is the offline live-fetch integration test (expected). The changes are additive (new helper, new optional param, new dict key) and the default `/bars` contract is asserted byte-identical.
- **No new external integration / native dependency.** Everything reads the committed offline seed; no provider/network call, no new package, no migration. The chart uses the already-installed lightweight-charts v5 (`createSeriesMarkers`).
- **Cohort projection is keyed by `cfg.universe.symbols`** (the complete stored-result set for a run), so the frontend join-by-ticker resolves every Ranked-Cohort row; this is the intended "complete keyed projection" (no row-count literal in the backend).

## Suggested Next Phase

Continue the new wave with a heavier member now that the two low-risk page refinements are in: **J-22** (expand to the ~500-name universe — a re-seed/ingest + universe-config change) is a natural prerequisite for the richer labs, OR **J-23/J-24** (multi-timeframe bars + the Stock-Detail timeframe selector) which builds directly on this iteration's chart work. The `/research` labs (J-25–J-29) remain gated on a blueprint nav re-approval (new sidebar home) and should be sequenced after the universe/bars groundwork.
