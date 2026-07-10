# goal-mcp-loop-iter-26 Functional Test Plan

**Phase:** goal-mcp-loop-iter-26
**Date:** 2026-07-09
**Frontend Present:** yes

## Phase Goal

Make data jobs (Backfill + warmup) materially faster on the 30-year basis by bounding the scoring-input window, while every displayed score/forward-return stays byte-identical and `/data` job progress stays honest — passing J-16 and preserving J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-15.

## Test Cases

### TC-01 — Byte-identity harness: windowed vs unwindowed scoring

**Type:** api
**Preconditions:** Backend is running in prod mode; 30-year data is loaded; `indicators.max_lookback_bars` config is set; both windowed and unwindowed code paths are available for testing.

**Steps:**
1. Invoke `score_stocks` with windowing enabled (max_lookback_bars applied at `bars_asof` sites in scoring.py:113 and scoring.py:339)
2. Capture full output including all scores (Leadership, Entry Quality, Risk), buckets, setup state, and detected patterns for ≥3 real cadence dates × the full ~583-symbol pool
3. Invoke `score_stocks` with windowing disabled (e.g., huge/disabled max_lookback_bars)
4. Capture identical output structure for the same dates and symbols
5. Run byte-level diff on all output fields

**Expected outcome:** 0 differences in any field across all dates and symbols; windowed and unwindowed produce identical scores, buckets, setups, and patterns.
**Pass criteria:** Diff output is empty; every (date, symbol, field) pair matches exactly between windowed and unwindowed runs.

---

### TC-02 — Short-history symbol handling

**Type:** api
**Preconditions:** A symbol with fewer than `max_lookback_bars` bars exists in the test data; backend is running.

**Steps:**
1. Score a symbol with fewer than `max_lookback_bars` bars (e.g., a newly-added security)
2. Verify that its full (shorter) series is used, not truncated
3. Capture the score output and NA propagation for that symbol
4. Compare against the unwindowed baseline for the same symbol

**Expected outcome:** Short-history symbol keeps its full series; no artificial NAs introduced; output is byte-identical to unwindowed path.
**Pass criteria:** Short-history symbol output matches unwindowed baseline; no NA count change due to windowing.

---

### TC-03 — close_on and bars_after cache-aware behavior (long-history symbol)

**Type:** api
**Preconditions:** Backend is running; bar_cache context is active; a full-deep-history symbol (e.g., SPY, ~5300+ bars) is in the test data.

**Steps:**
1. Call `close_on(session, ticker, date)` INSIDE an active `bar_cache` context
2. Record the returned close value and query count
3. Stop the cache, disable `close_on` caching, and call `close_on(session, ticker, date)` again with a raw DB query
4. Compare results and query counts
5. Repeat steps 1-4 for `bars_after(session, ticker, date, limit=100)`

**Expected outcome:** Both cached and uncached paths return byte-identical results; cached path issues fewer DB queries.
**Pass criteria:** Results match exactly between cached and uncached; cached path query count is 1 (or minimal for multi-symbol batches), uncached path issues 1+ DB queries.

---

### TC-04 — close_on and bars_after cache-aware behavior (short-history symbol)

**Type:** api
**Preconditions:** Backend is running; bar_cache context is active; a short-history symbol (<100 bars) exists.

**Steps:**
1. Call `close_on(session, ticker, date)` and `bars_after(session, ticker, date)` INSIDE an active `bar_cache` context for the short-history symbol
2. Record results and query count
3. Disable cache and repeat with raw DB query path
4. Compare results and query counts

**Expected outcome:** Byte-identical results and same behavior (short series handled correctly); cache provides no-op graceful fallback for short histories.
**Pass criteria:** Results match exactly; query counts are consistent; no error or data loss on short series.

---

### TC-05 — Warmup forward-return cache-scope fix: backfill_forward_returns inside bar_cache

**Type:** api
**Preconditions:** Backend is running; warmup.py is updated to call `backfill_forward_returns(session, cfg)` (not engine) inside the `with bar_cache(session):` block; prices.py `close_on` and `bars_after` are cache-aware.

**Steps:**
1. Run a warmup cadence loop (e.g., 5-10 real cadence dates, full pool)
2. Monitor DB query count for `close_on`/`bars_after` calls during the `backfill_forward_returns` step
3. Record total queries and elapsed time for forward-return backfill
4. Compare query count and output against the pre-change (uncached) path
5. Verify forward-return values are byte-identical

**Expected outcome:** Query count is significantly reduced (each symbol loaded once for the entire warmup); forward-return values are byte-identical; elapsed time is measurably lower.
**Pass criteria:** Query count for forward-return step is ≤ symbol count (at most one per symbol); forward-return output matches uncached baseline byte-for-byte.

---

### TC-06 — Warmup forward-return byte-identity on _do_backfill path

**Type:** api
**Preconditions:** Backend is running; the per-date `_do_backfill` job (data_manager._do_backfill, distinct from warmup.py) is executed with cache-aware close_on/bars_after.

**Steps:**
1. Run a single per-date backfill (e.g., via data_manager._do_backfill)
2. Capture forward-return values written to the DB
3. Compare against a baseline run with the uncached path
4. Verify output is byte-identical

**Expected outcome:** Forward-return values from _do_backfill are identical before and after cache-awareness changes; no regression.
**Pass criteria:** All forward-return values match baseline; no change in count, timing, or values.

---

### TC-07 — Per-date backfill performance (real deep-history cadence date)

**Type:** artifact
**Preconditions:** Backend is running in prod mode (start-backend.sh); baseline performance measurement exists or is freshly captured; a real deep-history cadence-eligible date is chosen (not an empty 2005 range).

**Steps:**
1. Choose a real cadence-eligible date with ≥1 eligible symbol (e.g., a recent date when the market was open and backfill job ran)
2. Measure per-date backfill time with windowing DISABLED (baseline): wall-clock time, CPU time, peak RSS
3. Measure per-date backfill time with windowing ENABLED (optimized): same metrics
4. Record both measurements in `reports/perf-budgets.md` under a new iter-26 section
5. Calculate improvement: (baseline - optimized) / baseline × 100%

**Expected outcome:** Per-date backfill time with windowing enabled improves ≥30% vs baseline; peak RSS stays <6144 MB.
**Pass criteria:** Optimization is ≥30%; peak RSS confirmed <6144 MB; both measurements use the same real cadence date and full pool; baseline + optimized results recorded in `reports/perf-budgets.md`.

---

### TC-08 — Full warmup performance (representative deep-history subset or full pass)

**Type:** artifact
**Preconditions:** Backend is running in prod mode; a consistent subset of ≥10 real cadence dates (or a full 124-date warmup pass if feasible within budget) is selected and documented.

**Steps:**
1. Run full warmup (or fixed subset) with windowing DISABLED: wall-clock time, CPU time, peak RSS
2. Run full warmup (or same fixed subset) with windowing ENABLED: same metrics
3. Record both measurements in `reports/perf-budgets.md` under the new iter-26 section
4. Verify peak RSS both runs stay <6144 MB
5. Calculate improvement: (baseline - optimized) / baseline × 100%

**Expected outcome:** Full (or subset) warmup improves ≥30%; peak RSS <6144 MB for both runs.
**Pass criteria:** Optimization is ≥30%; peak RSS confirmed <6144 MB both runs; same subset used for both baseline and optimized; results recorded as never-regress budgets in `reports/perf-budgets.md`.

---

### TC-09 — Peak memory usage under cap

**Type:** api
**Preconditions:** Backend is running; memory monitoring is enabled; a warmup/backfill job is in flight.

**Steps:**
1. Start warmup or backfill job (real data, deep history)
2. Sample peak process RSS every 1-5 seconds during the job
3. Record maximum RSS observed
4. Confirm max RSS < 6144 MB (`server.memory_cap_mb`)

**Expected outcome:** Peak RSS stays under the 6144 MB cap; no memory regression introduced by windowing changes.
**Pass criteria:** Max RSS observed is <6144 MB; no OOM kill or process crash.

---

### TC-10 — No-lookahead preserved in scoring and forward returns

**Type:** api
**Preconditions:** Backend is running; scoring.py and forward_testing.py are updated; bar slicing is applied.

**Steps:**
1. For a test (symbol, as-of date) pair, capture which bars are used for scoring (should be ≤ as-of)
2. Capture which bars are used for forward-return calculation (should be > as-of)
3. Verify no forward data leaks into scoring (scoring uses bars[-N:] ≤ as-of; forward returns use bars > as-of)

**Expected outcome:** Temporal boundary between scoring and forward returns is preserved; no lookahead introduced.
**Pass criteria:** Scoring input bars all have date ≤ as-of; forward-return input bars all have date > as-of.

---

### TC-11 — Existing scoring tests remain green and unedited

**Type:** api
**Preconditions:** Scoring unit tests exist and are expected to pass; no test expectations have been manually re-baselined.

**Steps:**
1. Run test suite: `tests/test_scoring.py`, `tests/test_bar_cache.py`, `tests/test_forward_testing.py`, `tests/test_forward_testing_streaming.py`, `tests/test_forward_walk.py`
2. Capture exit status and pass/fail counts
3. Confirm no test expectation files were edited by developer (check git diff on test expectation snapshots)

**Expected outcome:** All tests pass; no expectation files were edited; tests verify windowing does not change scoring logic.
**Pass criteria:** Exit status 0; no expectation files changed; all snapshot comparisons pass.

---

### TC-12 — Data manager backfill job with cold-path /data request

**Type:** browser
**Preconditions:** Frontend is running; backend is running in prod mode; `/tmp/pytest-of-*` is cleared; cache is cleared (`rm -rf apps/frontend/.next`).

**Steps:**
1. Stop the backend service
2. Wait 2 seconds to ensure process fully exits
3. Start backend fresh (cold start)
4. IMMEDIATELY load `/data` page in the browser (do NOT make any other requests first)
5. Observe job-progress panel updating
6. Allow the page to fully load and jobs to complete
7. Stop backend again, wait 2 seconds
8. Start backend fresh again
9. Load `/data` IMMEDIATELY as the first request
10. Observe job-progress and check memory usage

**Expected outcome:** `/data` loads successfully on cold start; job-progress updates honestly and never jumps to "done early"; no OOM crash; peak RSS <6144 MB.
**Pass criteria:** `/data` renders fully; progress counter increments smoothly (ticking count); no artificial "100% done" marker before jobs actually complete; no 500 error or crash; memory <6144 MB on cold /data load.

---

### TC-13 — J-16 target journey: /data job progress honest and live

**Type:** browser
**Preconditions:** Frontend and backend are running in prod mode; `/data` page is accessible.

**Steps:**
1. Navigate to `/data` page
2. Observe the job-progress panel (Fetch / Backfill / Warmup jobs)
3. Watch progress counter update in real-time for ≥10 seconds (e.g., "Fetched 100/583 symbols")
4. Verify the counter increments smoothly and never jumps to completion prematurely
5. Wait for all jobs to complete
6. Verify the final status reflects actual completion (e.g., "Fetch 583/583", "Backfill complete")

**Expected outcome:** Job progress updates honestly and incrementally; never shows "done early" or 100% before jobs finish; final state matches actual job completion.
**Pass criteria:** Progress counter visible and ticking; no jump to 100% before ≥10 seconds of actual work; final count is accurate (e.g., 583/583).

---

### TC-14 — J-01 required journey replay: all scores show evidence status

**Type:** browser
**Preconditions:** Frontend and backend are running; `/stocks` page is accessible.

**Steps:**
1. Navigate to `/stocks`
2. Observe the leaderboard
3. For each visible score (Leadership, Entry Quality, Risk), check that an evidence badge is rendered
4. Confirm badge reads "Proven" or "Not yet proven"
5. Scroll to load more rows; repeat badge check

**Expected outcome:** Every visible score has an evidence badge; no score is presented without status.
**Pass criteria:** All scores show a visible badge; badge text is "Proven" or "Not yet proven"; no score lacks a status.

---

### TC-15 — J-03 required journey replay: unproven/noise marking visible

**Type:** browser
**Preconditions:** Frontend and backend are running; a signal with unproven or noise status exists; `/stocks` or detail page is accessible.

**Steps:**
1. Navigate to a page displaying a signal known to be unproven (e.g., via `/evidence`)
2. Observe the display for that signal on `/stocks` or detail page
3. Verify the badge or marker clearly indicates "Not yet proven" or "Noise"
4. Confirm the presentation does NOT show a confident number without a warning

**Expected outcome:** Unproven signals are marked honestly as "Not yet proven"; no false confidence.
**Pass criteria:** Unproven marker visible and clear; no confident-looking number without status qualifier.

---

### TC-16 — J-04 required journey replay: Dashboard regime rendering

**Type:** browser
**Preconditions:** Frontend and backend are running; Dashboard page is accessible.

**Steps:**
1. Navigate to `/` (Dashboard)
2. Observe regime/phase display
3. Confirm regime box, phase label, and related metadata render without error
4. Verify regime has an evidence status (if applicable)

**Expected outcome:** Dashboard regime display is byte-identical to pre-optimization; no visual regression.
**Pass criteria:** Regime box renders; no 404/500 error; metadata complete and visible.

---

### TC-17 — J-05 required journey replay: /evidence ledger all-FAIL byte-identical

**Type:** browser
**Preconditions:** Frontend and backend are running; `/evidence` page is accessible.

**Steps:**
1. Navigate to `/evidence`
2. Observe the evidence ledger
3. Verify ledger displays all-FAIL status (no certified claims, only "not yet proven" entries)
4. Scroll and verify all rows display the same state as before optimization

**Expected outcome:** Evidence ledger shows all-FAIL status and is byte-identical to pre-optimization baseline.
**Pass criteria:** Ledger displays; all-FAIL status visible; no new certified claims introduced; no 500 error.

---

### TC-18 — J-10 required journey replay: deep-history chart rendering

**Type:** browser
**Preconditions:** Frontend and backend are running; a stock detail page with a chart is accessible.

**Steps:**
1. Navigate to a stock detail page (e.g., `/stocks/SPY`)
2. Scroll to the deep-history chart
3. Verify chart loads and renders without error
4. Observe that the chart displays data for the full history (e.g., 30+ years)

**Expected outcome:** Deep-history chart renders and displays all available history; no performance regression or truncation.
**Pass criteria:** Chart renders; data points visible for deep history; no 500 error or blank chart.

---

### TC-19 — J-12 required journey replay: universe/membership counts

**Type:** browser
**Preconditions:** Frontend and backend are running; `/data` or stats page is accessible.

**Steps:**
1. Navigate to `/data` or look for universe stats display
2. Observe counts (e.g., "583 stocks in universe", membership counts)
3. Verify counts are displayed and match the backend data
4. Confirm counts do not show artificial "unknown" or loading state after data is loaded

**Expected outcome:** Universe and membership counts are accurate and byte-identical to pre-optimization.
**Pass criteria:** Counts displayed; values match backend; no "unknown" or "loading" state persists after jobs complete.

---

### TC-20 — J-13 required journey replay: /data legend byte-identical

**Type:** browser
**Preconditions:** Frontend and backend are running; `/data` page is accessible.

**Steps:**
1. Navigate to `/data`
2. Observe the legend area (storage card, availability legend, job descriptions)
3. Verify legend content is identical to pre-optimization baseline
4. Take a screenshot and compare pixel-by-pixel or text-by-text

**Expected outcome:** Legend and storage card are byte-identical to baseline; no visual change.
**Pass criteria:** Legend text and layout match baseline; storage card displays accurate byte counts; no 500 error.

---

### TC-21 — J-15 required journey replay: perf budgets / storage card / cold-path /data

**Type:** browser
**Preconditions:** Frontend and backend are running in prod mode; `reports/perf-budgets.md` is updated with new iter-26 measurements; cold-path test from TC-12 has been run.

**Steps:**
1. Navigate to `/data` after a fresh backend cold start (not a warm cache)
2. Observe the storage card (cache/data file sizes)
3. Verify storage card shows accurate byte counts for the committed database/cache
4. Check that the page loads successfully and jobs run without OOM

**Expected outcome:** Storage card is byte-identical to pre-optimization baseline (no artificial increase); perf budgets are recorded.
**Pass criteria:** Storage card displays accurate counts; no OOM crash; load time is ≥30% faster than baseline; perf measurements recorded in `reports/perf-budgets.md`.

---

### TC-22 — Config: indicators.max_lookback_bars is added and validated

**Type:** artifact
**Preconditions:** config.yaml and config.py are available.

**Steps:**
1. Check `config.yaml` for presence of `indicators.max_lookback_bars` under the `indicators:` block
2. Verify value is set to a positive integer (e.g., ~320)
3. Check `apps/backend/app/config.py` for `IndicatorsCfg` class
4. Verify `max_lookback_bars: int` field exists and is validated with positivity check in `_validate` method
5. Verify startup: run backend with `start-backend.sh` and confirm config loads without error

**Expected outcome:** Config is present, validated, and loads successfully; value is a positive int; backend starts without error.
**Pass criteria:** `indicators.max_lookback_bars` present in config.yaml; field validated in IndicatorsCfg; backend boots with HTTP-200 on `/api/health`.

---

### TC-23 — Scoring window slicing at scoring.py:113 (_raw_components)

**Type:** artifact
**Preconditions:** scoring.py is available; `bars_asof` is called at line ~113 in `_raw_components`.

**Steps:**
1. Inspect scoring.py around line 113 (_raw_components function)
2. Verify that after `bars = bars_asof(...)` call, the next line slices: `bars = bars[-cfg.indicators.max_lookback_bars:]` or equivalent
3. Confirm the slice happens BEFORE any indicator computation on `bars`
4. Verify short-history handling (if len(bars) < max_lookback_bars, keep full series)

**Expected outcome:** Slicing is present and correct; happens before indicator use; preserves short series.
**Pass criteria:** Slice operation visible in code; happens immediately after bars_asof call; no indicator runs on unsliced bars.

---

### TC-24 — Scoring window slicing at scoring.py:339 (pass-3 detectors)

**Type:** artifact
**Preconditions:** scoring.py is available; `bars_asof` is called at line ~339 in pass-3.

**Steps:**
1. Inspect scoring.py around line 339 (pass-3 detector section)
2. Verify that after `bars = bars_asof(...)` call, slicing is applied: `bars = bars[-cfg.indicators.max_lookback_bars:]`
3. Confirm slicing happens before any detector (VCP, pullback, flat-base, etc.) runs
4. Verify logic handles short-history symbols correctly

**Expected outcome:** Slicing is present and applied before detector computation; short series are preserved.
**Pass criteria:** Slice operation visible; happens before detector use; logic handles short histories.

---

### TC-25 — warmup.py backfill_forward_returns moved inside bar_cache context

**Type:** artifact
**Preconditions:** warmup.py is available; the `backfill_forward_returns` call is present.

**Steps:**
1. Inspect warmup.py around line 155 (the backfill_forward_returns call)
2. Verify the call is now INSIDE the `with bar_cache(session):` block (indentation confirms nesting)
3. Verify the call signature is `backfill_forward_returns(session, cfg)` NOT `backfill_forward_returns(engine, cfg)`
4. Confirm the with-block wraps the entire snapshot loop and forward-return call (lines ~145-152 inclusive)

**Expected outcome:** Call is moved inside the cache context; session is passed (not engine); indentation/nesting correct.
**Pass criteria:** Call is inside with-block; uses session parameter; no syntax error; passes tests.

---

### TC-26 — prices.py close_on and bars_after are cache-aware

**Type:** artifact
**Preconditions:** prices.py is available; `close_on` and `bars_after` functions exist.

**Steps:**
1. Inspect prices.py close_on function (line ~328)
2. Verify it checks `active_bar_cache(session)` first
3. If cache is active, verify it derives the result from cache's `_by_symbol`/`_dates_by_symbol` (using bisect.bisect_right idiom)
4. If no cache, verify it falls back to the existing raw DB query unchanged
5. Repeat for bars_after function (line ~344)
6. Verify both have the same cache-first, fallback-to-raw-query pattern

**Expected outcome:** Both functions are cache-aware; cache path uses bisect idiom; raw query fallback is byte-identical.
**Pass criteria:** Cache check present in both functions; fallback query is unchanged; both functions pass byte-identity tests.

---

### TC-27 — _BarCache has cache-aware bars_after method

**Type:** artifact
**Preconditions:** prices.py is available; _BarCache class is defined (~line 71).

**Steps:**
1. Inspect _BarCache class (starts ~line 71)
2. Verify it has existing methods: `bars_asof`, `trailing_count`
3. Verify a new method `bars_after` (or equivalent) is added to _BarCache
4. Inspect the method: it should derive bars_after from `_by_symbol`/`_dates_by_symbol` using bisect.bisect_right
5. Verify it returns bars strictly after the cutoff date, in ascending order, optionally with a `limit`

**Expected outcome:** _BarCache has a new bars_after method; it mirrors the bars_asof idiom; it uses bisect correctly.
**Pass criteria:** Method present and correct; uses bisect; returns correct subset; tested and passing.

---

## Summary

Total test cases: 27
- API tests: 12 (TC-01 through TC-11 plus TC-09)
- Browser tests: 9 (TC-12 through TC-21)
- Artifact checks: 6 (TC-07, TC-08, TC-22 through TC-27)

All test cases map directly to the Definition of Done and Testing Requirements in the phase spec. The byte-identity harness (TC-01, TC-02) is the primary correctness gate. Performance tests (TC-07, TC-08) validate the ≥30% improvement. Required journey replays (TC-13 through TC-21) confirm no regression and honest job progress on the faster backend.
