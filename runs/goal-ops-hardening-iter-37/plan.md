# goal-ops-hardening-iter-37 Execution Plan

## What to Build

- **The shared-cache fix (the one code defect):** make `_do_backfill`
  (`apps/backend/app/engine/data_manager.py:2888`) and `_persist_per_date_coverage_snapshots`
  (`apps/backend/app/engine/data_manager.py:3150`, invoked from `_refresh_ingest_aggregates` at line
  3274) share ONE `_BarCache` instance for the whole K-date backfill job instead of each opening its
  own `prefilled_bar_cache(session, expected_symbols=pool_symbols)` — today they are two SEPARATE
  whole-table loads (confirmed by reading both functions: `_do_backfill` opens one at line 3085 on the
  job's `session`; `_persist_per_date_coverage_snapshots` opens a second, independent one at line 3183
  on `agg_session`, a DIFFERENT session `_run_job` opens fresh at line 4175 after the job session has
  already closed).
  - **Design hint (verify before relying on it, do not treat as a mandate):** the pieces already exist
    to do this without touching `_compute_coverage_uncached`/`refresh_coverage_snapshot_for` at all —
    `_compute_coverage_uncached` already reuses `active_bar_cache(session)` automatically when one is
    bound to its session (the iter-35/36 fix), so it never needs to know the cache came from a
    different job stage. `apps/backend/app/engine/prices.py` already exposes `attach_shared_cache(session,
    cache)` (line 413) — a context manager that binds an EXISTING, already-prefilled `_BarCache` to a
    *different* session's id for a `with` block, with zero re-scan. The likely shape: have `_do_backfill`
    stash a reference to the `shared_cache` it built onto `prog` (a new internal/unserialized field,
    mirroring the existing `prog._backfill_per_date_seconds_sum` / `prog._backfill_concurrency` pattern
    at `data_manager.py:2044-2045`, itself declared right after the "J-53 backfill-stage scratch (NOT
    serialized...)" comment at line 2040) BEFORE its own `with prefilled_bar_cache(...)` block exits;
    `_persist_per_date_coverage_snapshots` already receives `prog` as a parameter, so it can check for a
    stashed cache and use `attach_shared_cache(session, prog._shared_bar_cache)` instead of opening its
    own `prefilled_bar_cache(...)` when one is present, falling back to today's own-prefill behavior
    when it is not (so any test that calls `_persist_per_date_coverage_snapshots` directly, without going
    through `_do_backfill` first, keeps working unchanged).
  - **Memory-lifetime nuance to get right:** `_do_backfill`'s existing `finally: _release_process_memory()`
    (line 3137-3138) currently frees the ~1.13 GB cache back toward the OS right after `_do_backfill`
    returns. If the cache is now kept alive (referenced from `prog`) so the finalize hook can reuse it,
    that release must move to AFTER `_persist_per_date_coverage_snapshots` (or `_refresh_ingest_aggregates`)
    finishes — not disappear. Null out `prog._shared_bar_cache` before that later release call so
    `gc.collect()` can actually reclaim it (a lingering reference defeats the whole point of
    `_release_process_memory`, and would regress iter-27's "second consecutive rebuild starts lean"
    guarantee). Get this ordering right — it is the part most likely to be subtly wrong.
  - Do not touch `_compute_coverage_uncached`'s own standalone (no-active-cache) call path — already
    bounded at iter-35/36, explicitly out of scope per the spec.
- **Prove the fix is real, not a rubber stamp:**
  - `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` (already exists, currently
    red per the iter-36 handoff — improved from max 3 loads/symbol to max 2; needs to reach exactly 1)
    must pass unmodified — re-verify the exact current red numbers fresh (the tree has moved since
    iter-36's measurement) rather than trusting iter-36's cited numbers blind.
  - A NEW byte-identity reference-oracle test: pin the OLD (pre-fix) body of both functions via
    `git show HEAD:apps/backend/app/engine/data_manager.py` (binding iter-29/32 lesson — pin the OLD
    code verbatim, never call the new code from both sides of the comparison) and assert the persisted
    `CoverageSnapshot` rows + the `_do_backfill`-created run payloads are byte-identical before/after
    for the same K-date backfill inputs.
  - A NEW mutation-style test that perturbs the shared-cache path (e.g. swaps which symbols the second
    call site's cache view sees) and confirms the mutation is CAUGHT as a failure — proving the oracle
    is load-bearing, not inert (binding iter-29/31/32 lesson).
  - `test_data_manager.py` / `test_api_data.py` coverage-snapshot tests re-run for regressions; J-01/J-03's
    own backfill run-summary fields (`dates_total`, exclusion breakdown, `aggregates_refreshed`)
    unchanged for the same inputs (TC-9).
- **Then actually RUN J-07's own steps 1-4 fresh, in one iteration, reflecting the current (post-fix)
  code** — per the spec, prior iterations recorded these steps in fragments across iter-32/33/34 in
  isolation; this iteration needs one coherent execution against the current tree:
  1. Full deep-basis forward-aggregate warm across every configured horizon (the ingest finalize path,
     `compute_forward_aggregates` — byte-frozen, no code change) while `GET /api/backtest` is served for
     each horizon throughout, in one long-lived process started via `scripts/start-backend.sh` (AG-10).
  2. Concurrently, poll `GET /api/health` at ~1 Hz for the whole warm; every poll HTTP 200; no gap
     between consecutive successful polls exceeds ~2.15s (TC-2 — a looser bar than the separately-tracked,
     out-of-scope ≤0.1s steady-state budget from iter-34/j).
  3. Record the process's peak VmPeak from `/proc/<pid>/status` during step 1; write the margin under
     `server.memory_cap_mb` (6144 MB, `config.yaml:1363`) into a NEW dated "Iteration 37" section of
     `reports/perf-budgets.md` — this exact step-1/step-2-concurrent scenario has never been recorded
     there before per two consecutive evaluators (iter-32's VmPeak table and iter-34's health-latency
     table were each captured separately, not from the same concurrent run).
  4. Induce memory pressure during a warm in a THROWAWAY process (tightened `server.memory_cap_mb`,
     launched via `scripts/start-backend.sh`, AG-10 — mirror iter-34's throwaway-DB approach at
     `runs/goal-ops-hardening-iter-34/mem-drill/`); confirm the existing per-item `MemoryError` catch
     (iter-8 convention) aborts the warm honestly while the SAME process keeps serving `/api/health` and
     previously-cached reads with no restart. Re-run against the paths bounded by iter-35/36 and this
     iteration's own fix, not the pre-iter-35 unbounded state.
  - Applies-to lesson (iter-34): corroborate every claim against the LIVE `logs/backend.log` with a
    bounded line range, not a trimmed excerpt.
- **Browser-qa lane ordering (binding, TC-5):** assemble the J-07 test plan so every backend-down /
  error-state assertion (step 4's throwaway process, any restart) is scheduled STRICTLY LAST, after
  every other J-07 assertion (steps 1-3) and after the smoke replay of the required-still-passing
  journeys — this is the exact ordering iter-36 got wrong (a mid-plan backend-down test stranded the
  rest of J-07's verification). If, despite this ordering, a later restart is still denied, record that
  as a new distinct process-information finding, not a silent retry loop and not a product defect
  (iter-36 evaluator precedent).
- No new UI, no new nav entry, no new API contract, no new Data Contract value. `_compute_coverage_uncached`,
  `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched` stay byte-frozen — only the two named functions'
  internal cache-loading mechanism changes.

## Agents Required
- backend-data: yes -- all work is backend (`data_manager.py`'s two named functions, new/extended unit
  tests, a `reports/perf-budgets.md` update, and live-process measurement/drill work). No schema, API
  contract, or endpoint change.
- frontend-ux: no -- zero UI/page/component changes; every served payload (`GET /api/data` coverage,
  backfill run-summary, `GET /api/backtest`) is byte-identical before and after.

Frontend Present: no

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` -- `_do_backfill` and `_persist_per_date_coverage_snapshots`
  share one `_BarCache` for the job (see design hint above); a new internal/unserialized `JobProgress`
  field to carry the reference (near `_backfill_per_date_seconds_sum` / `_backfill_concurrency`,
  `data_manager.py:2040-2045`); the later release point for `_release_process_memory()` moves to after
  the finalize hook's coverage warm completes.
- `apps/backend/tests/test_bar_cache.py` -- `test_kdate_backfill_loads_each_symbol_at_most_once` goes
  green with no change to its own assertions (it already encodes the target invariant).
- A new or extended test file (suggest `apps/backend/tests/test_backfill_coverage_shared_cache.py`,
  mirroring iter-36's `test_membership_timeline_batch_bound.py` convention of one module-scoped live-DB
  fixture shared across the byte-identity + mutation tests; the developer may instead extend
  `test_data_manager_membership_cache.py` if that fits the existing fixtures better) -- the
  `git show HEAD`-pinned byte-identity reference-oracle test and the mutation-style test for the
  shared-cache fix.
- `apps/backend/tests/test_data_manager.py` / `apps/backend/tests/test_api_data.py` -- re-run for
  regressions on coverage-snapshot / run-summary fields; extend only if a gap is found.
- `reports/perf-budgets.md` -- new dated "Iteration 37" section: J-07 steps 1-4's fresh, concurrent
  measurement (VmPeak + margin under `server.memory_cap_mb`, health-poll gap results, memory-pressure
  drill outcome).
- `docs/handoffs/goal-ops-hardening-iter-37-dev.md` -- new dev handoff (create); must name the exact
  fresh load-count numbers measured pre/post fix, the byte-identity + mutation test results, and the
  live J-07 step 1-4 evidence with file/line pointers into `logs/backend.log` and
  `reports/perf-budgets.md`.

## Frontend Present
no

## UI Evolution
N/A -- no frontend work this iteration. Spec's own "New user-facing capability: None"; "Product surface
delta: No visible product surface changes." The user-visible delta is confidence (lower peak memory,
faster backfill, a measured/recorded availability guarantee), not a rendered change.

## Visual Requirements
N/A -- no frontend work this iteration.

## Key Test Scenarios

Restating the spec's test-first contract (TC-1..TC-10) as the acceptance bar:

- TC-1/TC-2: full-horizon warm in one long-lived `scripts/start-backend.sh` process; every
  `GET /api/backtest` response HTTP 200, byte-identical to a pre-warm baseline read; concurrently,
  `GET /api/health` polled at 1 Hz throughout, every poll HTTP 200, no gap > ~2.15s.
- TC-3: peak VmPeak from `/proc/<pid>/status` during TC-1's warm, recorded with margin under
  `server.memory_cap_mb` in a new dated `reports/perf-budgets.md` section.
- TC-4: a throwaway `scripts/start-backend.sh` process with a tightened `server.memory_cap_mb`; induced
  memory pressure during a warm aborts with a logged `MemoryError`-class abort (not a crash); the SAME
  process keeps answering `GET /api/health` HTTP 200 and serving previously-cached reads, no restart.
- TC-5: the browser-qa test plan orders every backend-down/error-state J-07 assertion strictly AFTER
  every other assertion (steps 1-3 and the required-still-passing smoke replay).
- TC-6: `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` passes -- `max(load_counts
  .values()) == 1` for every symbol across a K>=3-date parallel backfill.
- TC-7: persisted `CoverageSnapshot` rows + `_do_backfill`-created run payloads byte-identical to the
  `git show HEAD`-pinned reference oracle for the same K-date inputs.
- TC-8: a mutation perturbing the shared-cache path is caught as a test failure (oracle is load-bearing).
- TC-9: J-01/J-03's own persisted run-summary fields (`dates_total`, exclusion breakdown,
  `aggregates_refreshed`) unchanged from pre-fix values for the same inputs.
- TC-10: the closure gate scores `docs/handoffs/goal-ops-hardening-iter-37-user-visible-changes.md` on
  whether it CLAIMS no visible changes, not on substring matching; if the known `closure_gate.py`
  framework false-positive recurs, record it as a repeat instance of that known defect (out of dev
  scope), not a real closure failure.

Required-still-passing journeys (J-01, J-03, J-04, J-05, J-06, J-08, J-09) must replay green
(deterministic replay + LLM fallback) -- run these as live-process/API-level and existing-page checks
since `Frontend Present: no` for this iteration's OWN new work, matching iter-32/iter-30/31 precedent:
these journeys' pages are unchanged by this iteration, so their smoke replay verifies no regression, not
new UI. QA should run these checks (curl/log-grep for J-07's own steps; existing golden-replay scripts
for the required-still-passing set) rather than skip them because no Chrome MCP pass is mandated by the
`Frontend Present` flag.

Error case (explicit in spec): a `MemoryError` raised mid-warm under a tightened `server.memory_cap_mb`
must be caught by the existing per-item handler and must NOT propagate to a crash, wedge, or require a
restart (TC-4).

## Out of Scope (flagged per spec, do not implement this iteration)

- iter-33/g -- Regime Lab's cold `view=pooled` background dispatch + the undiagnosed HTTP 200 carrying
  "Internal Server Error" (deliberately deferred, rule 5 -- next in queue).
- iter-34/j -- the `GET /api/health` <=0.1s steady-state budget, honestly missed under host CPU
  contention; owner decision, not agent-fixable. (Distinct from TC-2's looser ~2.15s no-frozen-window
  bar, which IS in scope.)
- iter-33/i -- whether `start-frontend.sh` should join `HOST_GUARD_MARKER_FILES`; owner decision.
- `warmup.py:194` badge wording after a permanently failed warm-up; iter-31/e, iter-32/f, iter-36/n
  (`_excluded_counts_by_date` duplicate-date double-count, unreachable in production); Audit B6
  (`read_pool()` re-read once per batch x date) and the stale `membership_timeline_cached` docstring
  "591 symbols" -> 548 correction -- all carried, unresolved, non-blocking; do not re-open.
- The `closure_gate.py` backend-only regex false-positive -- vendored framework tree, not this product's
  tracked scope; framework-maintainer follow-up, not a goal-mode dev task.
- J-07's `[NEW]` walkthrough capture and a J-06 budgets-table-vs-live-pages walkthrough -- ride-alongs
  only if the demo lane produces them as a side effect; never a Definition-of-Done item this iteration.
- No new UI, no new nav entry, no new Data Contract value.

No drift from `docs/goal.md` detected: this iteration is a pure correctness/resilience closure of J-07
("Heavy aggregates never take the service down") and the one remaining unbounded whole-table load on the
backfill finalize path -- directly serves the Vision's "no unbounded whole-table loads" / "computed at
ingest time" success criteria and AG-8/AG-10. Introduces no new claim, score, or UI surface; does not
touch AG-1/AG-2/AG-4 territory. Builds on the exact iter-35/36 mechanism (`attach_shared_cache`,
`active_bar_cache`) already proven in this module rather than inventing a second caching approach.
