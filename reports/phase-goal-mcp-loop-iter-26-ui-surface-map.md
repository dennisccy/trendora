# Phase goal-mcp-loop-iter-26 — UI Surface Map

**Phase:** goal-mcp-loop-iter-26
**Date:** 2026-07-10
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

No frontend source file changed this iteration. The rows below are not code changes to these
surfaces — they are the surfaces whose DISPLAYED or TIMED behavior is downstream of the backend
compute-path change (bounded scoring window + warm-up cache-scope fix) and therefore need targeted
regression verification, per the phase's own Testing Requirements (J-16 target journey + the
required-still-passing replay list).

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | Job-progress panel (Backfill / warm-up run status) | Changed behavior (backend perf, no UI code touched) | `warmup.py`'s `backfill_forward_returns` call now runs inside the shared `bar_cache` session (was a separate uncached session) and `scoring.py` now windows each stock's history to ~320 bars before indicator computation — the underlying job runs 78–89% faster per the developer's measurements, so the panel's on-screen job duration will visibly shorten | Start a Backfill job (or warm-up) from `/data`, watch the progress counter's `done/total` value increment step-by-step across multiple ticks rather than jumping straight from a low number to "done" or 100%, and confirm the job finishes noticeably sooner than a pre-iteration timing of the same job on the same host |
| `/data` | Cold-start job-progress + storage card (first request after a backend restart) | Regression check (iter-24 cold-path OOM lesson) | The warm-up's forward-return backfill now shares the cadence loop's `bar_cache` session, changing memory-allocation timing during a cold boot's first `/data` load | Stop the backend, cold-start it in prod mode (`start-backend.sh`, not `dev.sh`), load `/data` as the very first HTTP request at least twice in a row, and confirm the page renders the job-progress panel and storage card normally with no crash and no out-of-memory error |
| `/data` | Storage card + availability legend | No visual/value change (regression check) | The forward-return rows written via the now-cache-aware `close_on`/`bars_after` in `prices.py` are asserted byte-identical to the pre-iteration raw-query path (`test_forward_testing.py`'s new cache-awareness tests) | Load `/data`, read the storage card's row counts and the availability legend's labels/colors, and confirm they match a pre-iteration capture of the same page (no new/changed/missing rows or labels) |
| `/stocks` | Stock list score / bucket / pattern-flag columns | No visual/value change (regression check — byte-identity gated) | `scoring.py`'s `score_stocks` (`_raw_components` and the pass-3 detector block) now slices each member's `bars_asof` series to `max_lookback_bars` (320) before computation, but `test_scoring_window.py` proves 0 output diffs across 3 real dates × the full pool | Open `/stocks`, pick 3–5 tickers spanning both long-history and recently-listed (short-history) symbols, and confirm each one's displayed score, bucket, and pattern flags match what they showed before this iteration (an exact-value comparison, not just "a number is present") |
| `/stocks/[ticker]` | Ticker detail score/indicator display | No visual/value change (regression check — byte-identity gated) | Same `score_stocks` compute path as above serves the ticker detail page's score data via the same existing `GET /api/stocks/{ticker}` endpoint (unchanged shape) | Open a known ticker's detail page and confirm every displayed score/indicator value is identical to a pre-iteration capture of the same ticker and as-of date |

<!-- Change Type key used above: "Changed behavior (backend perf, no UI code touched)" | "Regression check" | "No visual/value change (regression check — byte-identity gated)" -->

---

## Backend-Only Changes (No UI Impact)

- `config.yaml` (`indicators.max_lookback_bars: 320`) — new validated config value bounding the
  scoring engine's input window — not exposed in any settings UI, no UI surface affected.
- `apps/backend/app/config.py` (`IndicatorsCfg.max_lookback_bars` field + two new
  `model_validator` sanity-guard checks) — config-schema validation only — no UI surface affected.
- `apps/backend/app/engine/scoring.py` (bounded window slice at both `bars_asof` call sites in
  `_raw_components` and the pass-3 detector block) — internal compute-path change to the shared
  `score_stocks` module; output is byte-identity-proven unchanged (see surface-map rows above for
  the regression-verification surfaces this feeds) — no NEW UI surface affected.
- `apps/backend/app/engine/prices.py` (`close_on`/`bars_after` made cache-aware; new
  `_BarCache.bars_after` method) — internal read-path optimization for the forward-return backfill —
  output byte-identity-proven unchanged — no UI surface affected beyond the `/data` job-timing
  regression rows above.
- `apps/backend/app/engine/warmup.py` (`backfill_forward_returns` call moved inside the `bar_cache`
  session, passed `session` not `engine`) — job-orchestration timing change only — feeds the `/data`
  job-progress timing row above, no other UI surface affected.
- `apps/backend/tests/test_scoring_window.py` (new), `test_forward_testing.py`,
  `test_warmup.py`, `test_config.py`, `test_config_engine.py`, `test_indexes.py`, `test_sectors.py`,
  `test_themes.py` (all test-only changes) — developer-facing verification only, no UI surface
  affected.
- `reports/perf-budgets.md` (new "Item F" section: before/after job timings + peak-RSS figures) — a
  committed engineering report living in the repository, not rendered anywhere in the running
  product — no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 14 files (2 config, 3 engine modules, 8 test files, 1 committed report) —
  all with 0 code-level UI impact; 5 existing UI surfaces (`/data` panel x3, `/stocks`,
  `/stocks/[ticker]`) require behavior/timing regression verification only, per the table above
