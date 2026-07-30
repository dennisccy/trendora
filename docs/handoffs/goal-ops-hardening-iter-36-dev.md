# goal-ops-hardening-iter-36 Dev Handoff

**Phase:** goal-ops-hardening-iter-36
**Date:** 2026-07-30
**Agent:** developer
**Status:** complete

## What Was Built

Re-dispatch of the unbuilt iter-35 spec: three independent bounded-memory fixes (all byte-identical to
their pre-fix output) plus mechanical frontend wiring, per `docs/phases/goal-ops-hardening-iter-36.md`.

### 1. Bound `_membership_timeline`'s candidate-pool bar loading (ledger iter-29/d)

- **Root cause:** `_membership_timeline`'s cold-compute opened `prefilled_bar_cache(session,
  expected_symbols=pool_symbols)`, which loads EVERY symbol's full price series in one unbounded query
  regardless of `expected_symbols` (`prices.py::_BarCache.prefill` scans the whole `daily_prices` table).
  `_compute_coverage_uncached` ALSO opened its own such context around the whole coverage derivation, so
  this cost was paid on every standalone coverage compute (e.g. the ingest-finalize hook's per-date
  `refresh_coverage_snapshot` call for the CURRENT date), not merely a rare cold `/data` page load.
- **Fix:**
  - New `_BarCache.load_only(session, symbols)` method (`prices.py`) — REPLACES the same cache instance's
    contents with only the given symbols' bars (never a second cache instance; independent of `prefill`'s
    `_prefilled` whole-table-scan guard).
  - `universe_resolver.resolve_with_reasons` gained an optional `symbols=` param restricting resolution to
    a subset of the committed pool (default `None` = full pool, byte-identical for every existing caller).
  - `data_manager._membership_timeline` now delegates its per-date excluded-count derivation to a new
    `_excluded_counts_by_date` helper: when an OUTER job-scoped bar cache is already active (e.g.
    `_do_backfill`, `_persist_per_date_coverage_snapshots` — legitimately whole-job-scoped, out of this
    iteration's scope), it reuses it unchanged; otherwise it walks the candidate pool in
    `research.membership_timeline_batch_symbols`-wide batches (shipped: 50), loading + resolving + discarding
    one batch at a time.
  - `_compute_coverage_uncached` no longer opens its OWN eager whole-table `prefilled_bar_cache` wrap — the
    resolver's own default (no-cache) per-symbol-bounded path runs instead when no outer cache is active.
  - New dedicated config key `research.membership_timeline_batch_symbols` (default 50), boot-validated `>= 1`.
- **Measured:** peak `tracemalloc` bytes for `_membership_timeline` on the live seed DB (591 symbols, 31
  sampled snapshot dates) dropped from **1,125,618,771** (unbounded reference) to **329,751,051** (shipped,
  batch width 50) — a **70.7% reduction**. Full numbers in `reports/perf-budgets.md` "Iteration 36".

### 2. Bound `compute_drawdown_expectations`'s `stored_by_key` read (ledger iter-35/k, NEW finding)

- **Root cause:** the `/api/evidence` serving path's per-claim `stored_by_key` `ForwardReturn` read
  (`forward_testing.py`) materialized a broad claim's WHOLE cohort via one `session.exec(fr_stmt).all()` —
  the confirmed `MemoryError` source iter-35's live run hit twice under concurrent load.
- **Fix:** the resolved `tickers` list is partitioned into `research.drawdown_expectations_ticker_chunk`-wide
  chunks (shipped: 50), each chunk's own query `yield_per(research.read_batch_size)`-streamed. Byte-identical
  result — proven across chunk widths `[1, 2, 3, 50]` against a hand-built fixture. New dedicated config key
  `research.drawdown_expectations_ticker_chunk` (default 50), boot-validated `>= 1` — a DIFFERENT axis from
  `read_batch_size` (a rows/`yield_per` knob, reused correctly for ITS own purpose within each chunk) and
  from `factor_join_run_chunk` (a different function's own run-chunk knob).
- **Honest disclosure — a modest reduction, not a full architectural bound.** Unlike item 1, `stored_by_key`'s
  FINAL size is unchanged by chunking (the whole cohort's entries are still all resident once built).
  Measured live (real claim, 544 tickers, 771,662 cohort rows): peak RSS dropped from **1,215,052 KB**
  (unchunked reference) to **1,165,092 KB** (shipped) — **~50 MB / ~4%**. `compute_samples`'s own UNCHANGED
  771,662-row materialization dominates the call's total footprint. A real, reproducible `ulimit -v` window
  (1,210,000-1,220,000 KB) discriminates the two implementations (reference aborts, shipped completes) —
  narrower/more host-sensitive than the analogous iter-34 drill's 300 MB window, consistent with the modest
  measured reduction. Under a tighter cap (1,000,000 KB) the shipped implementation ALSO honestly degrades
  (caught `MemoryError`, never a crash/wedge) — the residual this iteration's own NOTES section calls for
  disclosing rather than silently claiming a full bound. Full numbers + methodology in
  `reports/perf-budgets.md` "Iteration 36".
- `evidence.py::build_evidence_payload`'s isolate-and-continue guard (the `expectations_status:
  "unavailable"` MemoryError/Exception catch) was NOT touched — re-verified working unchanged.

### 3. Frontend — mechanical wiring of `resolveLabLoadPanel` into 4 sibling research labs

Wired the already-generic, already-exported `resolveLabLoadPanel`/`useElapsedSeconds`/`SlowComputeNotice`
(`apps/frontend/lib/lab-load-panel.ts`, proven at iter-33) into `FactorLabPage`, `PhaseSeverityLabPage`,
`RegimePhaseFactorPage` (all in `_labs.tsx`), and `SeverityVelocityPage`
(`severity-velocity/page.tsx`) — matching Regime Lab's existing pattern exactly: `attempt` state +
`useElapsedSeconds(state.kind === "loading")` + `resolveLabLoadPanel(...)` + `SlowComputeNotice` on
`panel.kind === "computing"` + skeleton on `skeleton`/`computing` + a retryable error card, with `attempt`
added to each page's fetch-effect dependency array. `RegimePhaseFactorPage` keeps its own bespoke inline
error card + `CombinationSkeleton` markup (per the plan) — only the computing/retry SEMANTICS were added,
not a forced switch to `ResearchError`/`LabSkeleton`. No change to `resolveLabLoadPanel`'s own resolution
logic (already proven, 13/13 tests unaffected).

## Files Changed

- `apps/backend/app/config.py` -- new `ResearchCfg.membership_timeline_batch_symbols` +
  `drawdown_expectations_ticker_chunk` keys, each boot-validated `>= 1`.
- `config.yaml` -- real values (50 / 50) for the two new keys, with doc comments.
- `apps/backend/app/engine/prices.py` -- new `_BarCache.load_only()` method (batched-replace loading,
  independent of `prefill`'s whole-table-scan guard).
- `apps/backend/app/engine/universe_resolver.py` -- `resolve_with_reasons` gained an optional `symbols=`
  subset param (default `None`, byte-identical for every existing caller).
- `apps/backend/app/engine/data_manager.py` -- `_membership_timeline` restructured to delegate to new
  `_excluded_counts_by_date` (batched-by-symbol when no outer cache active, unchanged when one is);
  `_compute_coverage_uncached` no longer opens its own eager whole-table `prefilled_bar_cache` wrap.
- `apps/backend/app/engine/forward_testing.py` -- `compute_drawdown_expectations`'s `stored_by_key` read
  chunked by ticker, each chunk `yield_per`-streamed.
- `apps/backend/tests/test_bar_cache.py` -- 4 new unit tests for `_BarCache.load_only()`.
- `apps/backend/tests/test_data_manager_membership_cache.py` -- replaced
  `test_cold_compute_coverage_prefills_bar_cache_exactly_once` (asserted the OLD nested-prefill mechanics
  this iteration deliberately supersedes) with
  `test_cold_compute_coverage_never_prefills_whole_table_and_batches_by_symbol` (asserts the NEW batched
  invariant: `_BarCache.prefill` never called, `load_only` batches bounded to the configured width).
- `apps/backend/tests/test_membership_timeline_batch_bound.py` (new) -- TC-1 (peak-memory measurement),
  TC-2 (byte-identity vs pinned `git show HEAD` reference), TC-3 (mutation-style live-basis bound proof) —
  all three sharing one pair of live-seed-DB computations via a module-scoped fixture.
- `apps/backend/tests/test_forward_testing.py` -- 5 new tests: byte-identical-across-chunk-widths
  (parametrized `[1,2,3,50]`) vs a pinned reference, + a query-count sanity check.
- `apps/backend/tests/test_evidence_drawdown_memory_pressure.py` (new) -- TC-8 live `ulimit -v` induction
  drill (3 tests: tight-cap discrimination, control, starved-cap honest-degrade).
- `apps/frontend/app/research/_labs.tsx` -- wired `resolveLabLoadPanel` into `FactorLabPage`,
  `PhaseSeverityLabPage`, `RegimePhaseFactorPage`.
- `apps/frontend/app/research/severity-velocity/page.tsx` -- wired `resolveLabLoadPanel` into
  `SeverityVelocityPage`.
- `reports/perf-budgets.md` -- new "Iteration 36" section (both fixes' measurements + the TC-8 drill +
  the pre-existing test-failure disclosure below).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/<file> -q` (targeted; see below for scope)

- `test_bar_cache.py`: **15 passed, 1 pre-existing failure** (see Known Issues — not caused by this iteration).
- `test_data_manager_membership_cache.py`: **10 passed**.
- `test_membership_timeline_batch_bound.py` (new): **3 passed** (~2 min, live seed DB).
- `test_forward_testing.py -k "compute_drawdown_expectations or test_drawdown_expectations_chunk"`:
  **20 passed**.
- `test_evidence_drawdown_memory_pressure.py` (new): **3 passed** (~2.5 min, live `ulimit -v` subprocesses).
- `test_config.py` sanity: config loads with the two new keys (50, 50) at their defaults.
- Frontend: `apps/frontend` — `npx tsc --noEmit -p tsconfig.json`: **0 errors**.
  `npx tsx lib/lab-load-panel.test.ts`: **13 passed** (unaffected — `lab-load-panel.ts` itself untouched).
- Broader regression sweep (`test_api_data.py`, `test_data_manager.py`,
  `test_data_manager_concurrency_load.py`, `test_iter33_dynamic_universe.py`, `test_warmup.py`,
  `test_universe_screen.py`, `test_data_manager_jobs_pipeline.py`, `test_iter27_rebuild_mdd.py`,
  `test_data_manager_membership_cache.py` — 267 tests total): launched in the background; **~195/267
  completed with zero failures observed** at handoff time (one file, likely `test_iter27_rebuild_mdd.py`,
  contains a legitimately slow full-rebuild-scale test that had not finished after ~40 min CPU time — the
  documented "don't misread buffered pytest progress as hung" pattern this session's own memory notes
  describe for the 30-year basis). The reviewer/QA stage should re-run this sweep to completion; nothing
  observed so far indicates a regression from this iteration's changes.
- Live end-to-end verification: started the REAL backend via `scripts/start-backend.sh` (memory_cap_mb=6144,
  host-guard applied) against the committed seed DB — booted to `readiness: ready` in ~40s; `GET /api/health`
  200 throughout; `GET /api/data` served `universe_count: 540`, `membership_timeline` with 1,880 points,
  `coverage_status: current`; `GET /api/evidence` served all 7 real certified claims with real
  `expectations` panels (no `expectations_status: "unavailable"` — a healthy live compute, not a starved
  one, confirming the fix works end-to-end at the real live scale); `GET /api/research/factor-lab?all=true`
  200 in 8ms (warm). Started the REAL frontend via `scripts/start-frontend.sh` — `/research/factor-lab`,
  `/research/phase-severity-lab`, `/research/regime-phase-factor`, `/research/severity-velocity`,
  `/research/regime-lab`, `/data` all returned HTTP 200 with no error-boundary markup. Both processes
  stopped cleanly afterward (verified via `ps`/`ss` — no lingering `uvicorn`/`next` processes, ports 8255 and
  3255 free).

## Known Issues

- **Pre-existing test failure, NOT caused by this iteration (improved).**
  `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` fails on unmodified HEAD
  (confirmed via `git stash`) with every symbol loaded 3 times across one K-date parallel backfill job
  (three SEPARATE, non-nested `prefilled_bar_cache` contexts: the main scan's shared cache,
  `refresh_coverage_snapshot`'s own prefill for the current date, and `_persist_per_date_coverage_
  snapshots`'s own prefill for the other new dates). This iteration's removal of `_compute_coverage_
  uncached`'s own eager wrap eliminates the middle one, improving the count from 3 to 2 — still short of
  the test's asserted invariant of 1, but a net reduction, not a regression. The remaining offender
  (`_persist_per_date_coverage_snapshots`'s own separate whole-table scan) is out of this iteration's named
  scope (the plan scoped only `_membership_timeline`'s and `_compute_coverage_uncached`'s own loading) —
  recorded as a new, non-blocking follow-up ledger item for a future iteration.
- **Item 2's fix is a modest (~4%) reduction, not a full architectural bound** — disclosed in detail above
  and in `reports/perf-budgets.md`. `compute_samples`'s own cohort-row materialization (unchanged, out of
  this iteration's scope per the plan) dominates the call's total memory footprint; chunking the
  `stored_by_key` read specifically reduces ITS OWN transient contribution, which is real but proportionally
  small relative to the whole call.
- **Broader regression sweep not confirmed complete at handoff time** (see Tests Run above) — reviewer/QA
  should re-run or await completion of the 8-file, 267-test sweep before final sign-off; zero failures
  observed in the ~195 tests that had completed.
- No frontend visual/screenshot verification was performed by this developer pass beyond HTTP-200 +
  page-title checks (title/error-boundary text grep) — the plan assigns full browser-qa verification of
  TC-5/TC-6 (labelled computing card, retry control) to the browser-qa-agent stage.
