# goal-ops-hardening-iter-20 Dev Handoff

**Phase:** goal-ops-hardening-iter-20
**Date:** 2026-07-24
**Agent:** developer
**Status:** complete

## What Was Built

- **The SECOND `/backtest` cold-recompute path is closed (J-06/J-07/J-08).** The historical
  (`is_latest == False`) carve-out in `GET /api/backtest` and MCP `query_backtest` no longer calls
  `forward_aggregates_ingest_cached` synchronously in a loop on the request thread. Instead it calls a new
  `ensure_historical_forward_aggregates_dispatched(session, as_of, config)`
  (`apps/backend/app/engine/forward_testing.py`), which triggers a **single-flight-guarded background
  dispatch** and returns immediately — the request serves whatever `resolved_forward_aggregate_evidence`
  already found (the honest interim state: `"refreshing"` or `"not_yet_computed"`), never a fresh compute.
  Live UT-04 evidence (iter-19/iter-20 spec) showed this synchronous path stalling 9.6–54s; the new
  request-thread cost is sub-millisecond (measured 0.2–14ms across my own tests, see below).

- **The new outer dispatch guard, keyed and released exactly as the spec requires (DoD's own ask):**
  - **Keyed on `(asof_key, dataset_version)`** — the SAME identity `resolved_forward_aggregate_evidence`
    already resolves by (iter-16's own lesson: "enumerate the ways the identity can move, not just the
    ways the value can go stale"). A module-level `_HIST_DISPATCH_LOCK` (`threading.Lock`) guards a plain
    `set[tuple[str, str]]` (`_HIST_DISPATCH_INFLIGHT`) of identities currently being computed.
  - **Cannot duplicate work:** a request thread acquires the lock only for a tiny check-and-insert
    (sub-millisecond); if the key is already present, it is a pure no-op — no thread spawned, no lock
    touched further, the already-running dispatch will land on its own. Only the FIRST caller for a key
    ever spawns a background `threading.Thread` (daemon, its own `Session(engine)` — mirrors the
    established `data_manager.start_data_job` / `warmup.start_warmup` thread-plus-own-session idiom, per
    the pump note's own instruction to follow that precedent). Proven under real concurrency by TC-3
    (below): 5 concurrent first-touch requests for the same date invoke `compute_forward_aggregates`
    exactly `len(horizons)` times total, never `5×`.
  - **Cannot wedge:** the background worker (`_run_historical_forward_aggregates_dispatch`) releases the
    guard (`_HIST_DISPATCH_INFLIGHT.discard(key)`) in a `finally`, on success AND on an owner exception
    (any exception is caught + logged via a new `trendora.forward_testing` logger, mirroring
    `warmup.py`'s own non-fatal convention — never left to crash silently or propagate to the request
    thread that triggered the dispatch). Proven by TC-7 (below): a forced owner failure on the first call
    still lets a subsequent request re-dispatch and eventually reach `"ready"`.
  - **The engine for the background session is `session.get_bind()`** (the SAME engine the calling
    request's session is bound to — mirrors `data_manager.py`'s own `session.get_bind()` idiom), not a
    hardcoded `get_engine()` global. This matters for test correctness (this codebase's unit tests bind a
    private per-test SQLite engine, never the process singleton) and is also correct in production (the
    calling session is always bound to the real process engine there).
  - **The per-horizon lock inside `forward_aggregates_ingest_cached` is completely untouched** — the
    background worker calls it exactly as the old synchronous loop did, so the cutover-pruning
    completeness contract, the persistence, and the byte-identity guarantee are all reused verbatim (no
    second producer).

- **`ensure_loop_ms` is REPURPOSED, not renamed.** Per the spec's own instruction to check
  `test_backtest_timing.py`'s regex before landing: I kept the literal log field name `ensure_loop_ms`
  (so that file's regex and its two `ensure_loop_ms`-asserting tests keep matching verbatim — confirmed by
  running that file unchanged, 5/5 pass) but changed what it measures: now the sub-millisecond
  dispatch-DECISION cost (the lock-check-and-maybe-spawn call), never a compute-wait duration. This is a
  deliberate, logged interpretation of "rename/repurpose" in the spec/plan — documented here and in the
  module docstrings rather than silently decided; the alternative (an actual field rename) would have
  required editing `test_backtest_timing.py`, which the plan's own "Files to Create/Modify" list does not
  include, and the spec's "check the regex still matches" instruction reads most naturally as "verify this
  choice, don't necessarily change the test."

- **MCP `query_backtest` mirrors the identical change** (`apps/backend/app/mcp/tools.py`) — same dispatch
  function, same gate, same non-re-resolve behavior. Byte-identical to the HTTP endpoint for the same
  inputs (TC-6, proven by the pre-existing `test_backtest_route_and_mcp_tool_serve_evidence_asof_
  identically`-style tests, which still pass unmodified).

- **Frontend copy audit (TC-8/TC-9):** `RefreshingEvidenceBanner` and the `not_yet_computed` `EmptyState`
  on `/backtest` now branch on `backtest.is_latest` (an already-fetched field — no new API field, no new
  component, no new fetch) to state the TRUE cause for each: the LATEST view's copy is unchanged (a
  dataset change / "reload after the next ingest" is still literally accurate there — the LATEST branch
  never dispatches anything itself); the HISTORICAL view's copy now says the compute was started by
  viewing this page and to reload shortly — never claims an ingest is involved when none is. See the
  frontend handoff for the exact before/after text.

## Files Changed

- `apps/backend/app/engine/forward_testing.py` -- new `ensure_historical_forward_aggregates_dispatched` +
  `_run_historical_forward_aggregates_dispatch` + `_HIST_DISPATCH_LOCK`/`_HIST_DISPATCH_INFLIGHT` (inserted
  between the existing `forward_aggregates_ingest_cached` and `_utc_isoformat`); new module logger
  (`trendora.forward_testing`). `compute_forward_aggregates` and `resolved_forward_aggregate_evidence` are
  BYTE-UNCHANGED (confirmed via `git diff` — the only hunks touch imports, the new logger, and the new
  function block; TC-16).
- `apps/backend/app/api/backtest.py` -- historical branch replaces its synchronous
  `for h in horizons: forward_aggregates_ingest_cached(...)` loop + re-resolve with one call to
  `ensure_historical_forward_aggregates_dispatched(session, run.asof_date, cfg)`; `evidence` is no longer
  reassigned after the dispatch call (the request returns the PRE-dispatch read); module docstring and
  `_log_backtest_timing`'s docstring updated to describe the new mechanism and `ensure_loop_ms`'s
  repurposed meaning.
- `apps/backend/app/mcp/tools.py` -- identical mirror of the above in `query_backtest`.
- `apps/backend/tests/test_forward_testing_serving_split.py` -- updated
  `test_historical_asof_keeps_pre_iter16_create_once_and_cache_behavior` and
  `test_historical_asof_still_computes_once_even_when_older_fallback_evidence_exists` (TC-10) to assert an
  honest PRE-dispatch interim read on the first call, then poll (bounded, new `_poll_until_ready` helper)
  for the dispatched background compute to land before re-asserting the SAME
  compute-count/byte-identity/no-short-circuit guarantees these tests have always encoded. Neither test's
  core claim was weakened.
- `apps/backend/tests/test_forward_testing_concurrency.py` -- two new tests (TC-3, TC-7):
  - `test_iter20_concurrent_first_touch_historical_requests_dispatch_exactly_once` — 5 concurrent
    first-touch requests for the same never-warmed historical date invoke `compute_forward_aggregates`
    exactly `len(horizons)` times total and every request returns in well under 0.5s, against a fixture
    CALIBRATED (via a live pre-check, not assumed) to make a single uncontended compute take ≥1.0s — so
    the "never blocks" claim is a real, measurable proof, not a coincidence of a tiny fixture. The heavy
    100,000-row volume is spread across 10 SEPARATE older "filler" runs (never attached to the requested
    run itself) — see the Known Issues section below for why.
  - `test_iter20_historical_dispatch_owner_failure_releases_guard_and_allows_redispatch` — a forced
    `RuntimeError` on the dispatch's first call is followed by a poll loop that keeps re-triggering the
    dispatch; it converges to `"ready"` iff the guard was actually released (never a permanent wedge).
- `apps/backend/tests/test_api_backtest.py` -- updated `test_backtest_evidence_is_as_of_scoped_expanding_
  window` to poll (bounded, 10s) for the oldest date's dispatched background compute to land before
  asserting the SAME `n_runs`/`asof_dates <= D` expanding-window/no-lookahead guarantees (TC-11, AG-5). Added
  `import time`. **Not executed this session** — see Known Issues.
- `apps/frontend/app/backtest/page.tsx` -- `RefreshingEvidenceBanner` gains an `isLatest: boolean` prop
  (from the already-fetched `backtest.is_latest`) and branches its copy; the `not_yet_computed` `EmptyState`
  description also branches on `backtest.is_latest`. See the frontend handoff for full detail.
- `docs/handoffs/goal-ops-hardening-iter-20-dev.md` / `-frontend.md` -- this handoff pair.

## Tests Run

Command (host-guard-confined per this session's standing constraint — `taskset -c 0-3,8-11`,
`OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=4`, scoped files only, never the
full suite, never concurrent pytest runs):

```
cd apps/backend
taskset -c 0-3,8-11 env OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 \
  .venv/bin/python -m pytest \
  tests/test_forward_testing_serving_split.py \
  tests/test_forward_testing_concurrency.py \
  tests/test_backtest_timing.py \
  tests/test_backtest_scorecard.py \
  -q
```

Result: **59 passed, 0 failed** (25 in `test_forward_testing_serving_split.py` [23 pre-existing + the 2
updated tests, both now asserting the new contract]; 9 in `test_forward_testing_concurrency.py` [7
pre-existing + 2 new: TC-3, TC-7]; 5 in `test_backtest_timing.py` [all pre-existing, UNCHANGED — confirms
`ensure_loop_ms`'s kept field name still matches its regex/assertions verbatim]; 20 in
`test_backtest_scorecard.py` [all pre-existing, unaffected]).

Additionally ran `test_forward_testing_aggregates_streaming.py` (32 passed) — the file that directly proves
`compute_forward_aggregates`'s byte-identity/streaming behavior, confirming it is genuinely untouched
(TC-16).

**Flake check:** ran the 2 new `test_forward_testing_concurrency.py` tests 5 additional times in isolation
(`-k iter20`) — 5/5 passed, ~5.6–5.7s each, no hang, no flake.

**Genuine TDD RED/GREEN verification performed, not just claimed:**
`git stash push -- apps/backend/app/engine/forward_testing.py apps/backend/app/api/backtest.py
apps/backend/app/mcp/tools.py` to revert ONLY the three source files to their pre-iteration state, then:
- `test_forward_testing_serving_split.py`'s two updated tests: **FAILED** as expected — one shows
  `AssertionError` with `- refreshing / + ready` (the old code serves `"ready"` synchronously on the first
  call; the new test expects the honest interim state), the other analogous.
- `test_forward_testing_concurrency.py`'s TC-7: **FAILED** with
  `AttributeError: module 'app.engine.forward_testing' has no attribute
  'ensure_historical_forward_aggregates_dispatched'` (the function does not exist pre-iteration).
- `test_forward_testing_concurrency.py`'s TC-3: **FAILED** cleanly and instructively — with my fixture
  correctly isolating the slow path, the old code's `ensure_loop_ms` alone measured ~1.8s per request (all
  5 concurrent requests blocked on it, matching the calibration exactly), assertion `max(elapsed_times) <
  0.5` failed as expected. Total run time for this one test under the OLD code was ~5.3s (clean, isolated)
  — an earlier draft of this fixture (heavy rows attached to the requested run itself) produced a
  confounded ~43s failure instead; see Known Issues for why I redesigned it.

`git stash pop` restored the fix; re-ran the full scoped suite above — 59/59 pass again (the numbers
quoted in the Result line above are from this POST-restore run).

`py_compile` clean on all five changed backend files. `cd apps/frontend && npx tsc --noEmit -p
tsconfig.json` — **0 errors**.

**App import sanity check** (no service started/stopped — a plain Python import, safe under AG-10):
`python -c "import main; ..."` confirms `main.app` constructs cleanly (46 routes) and that
`app.api.backtest.ensure_historical_forward_aggregates_dispatched` and
`app.mcp.tools.ensure_historical_forward_aggregates_dispatched` are both the SAME function object as
`app.engine.forward_testing.ensure_historical_forward_aggregates_dispatched` (confirms the import wiring,
not a copy).

## Known Issues

1. **`test_api_backtest.py` was edited but NOT executed this session.** Its `loaded_engine` fixture is
   `scope="session"` and takes ~80 minutes to build on this host (the phase spec's own explicit carve-out:
   "cite it, do not run wholesale"). I reasoned the edit through carefully and pattern-matched it against
   the two analogous tests in `test_forward_testing_serving_split.py` that I DID run and confirm both RED
   and GREEN for — the polling technique is identical (poll `client.get(...)` until
   `evidence_status == "ready"`, bounded at 10s). **Recommend QA/reviewer run this one file** (with a
   larger time budget, off this constrained box) before scoring this iteration's DoD "no regressions"
   bullet as fully confirmed for this specific file.
2. **TC-5 (`GET /api/health` stays responsive during a dispatched background warm) has no dedicated new
   unit test.** The plan's own "Files to Create/Modify" list does not name a new test file/function for
   it, and by design it should hold structurally: the background compute runs in a daemon thread with its
   own DB session (SQLite WAL mode already permits concurrent readers per `app/db.py`'s pragmas), and
   nothing in the dispatch path touches `/api/health`'s own code path. I did not independently measure
   this live this session (no service start/stop permitted, per the pump note) — flagging for QA/operator
   confirmation via TC-12's live browser walk or a `curl` capture, consistent with how TC-13/TC-14 are
   already carried as operator items below.
3. **Pre-existing, ALREADY-FLAGGED, out-of-scope concurrency hazard re-confirmed (not new, not fixed):**
   while building TC-3's fixture, my first draft (heavy row volume attached to the SAME run being
   requested) reproduced the iter-19 dev handoff's own flagged "Known Issue" —
   `_insert_run_forward_returns`'s mid-loop autoflush can raise an uncaught `IntegrityError` under genuine
   concurrent first-touch requests for a run with many observable-horizon symbols, because the existing
   `_commit_forward_returns_concurrency_safe` guard only wraps the FINAL explicit commit, not an
   in-loop autoflush triggered by a later `close_on()` read. I did **not** fix this (iter-19 flagged it as
   requiring restructuring `_insert_run_forward_returns`'s flush behavior, out of scope for this iteration's
   spec/plan) — I redesigned my OWN test fixture to avoid triggering it (kept `observable_days == 0` for
   the requested run, matching the iter-19 zero-write-guard fast path, and moved the heavy aggregate volume
   onto separate older "filler" runs instead). Flagging again for whichever iteration picks up that
   restructuring; this is genuine reproduction evidence under a DIFFERENT trigger shape (5-way concurrent
   `/backtest` GETs, not iter-19's own barrier-forced scenario) if that's useful corroboration.
4. **`ensure_loop_ms`'s field NAME is unchanged** (see "What Was Built" above for the full reasoning) — its
   MEANING changed from a compute-wait duration to a dispatch-decision cost. Flagging as a design decision,
   not a defect: if a future consumer of `logs/backend.log` needs to distinguish old vs. new semantics by
   timestamp, note that this iteration's diff landed 2026-07-24.
5. **TC-13 (concurrent-ingest-overlay re-measurement) and TC-14 (disruptive J-04 kill/restart replay)** are
   OPERATOR-gated (AG-10 ingest-trigger classifier), carried since iter-17/18/19 and iter-15 respectively —
   not attempted this session, per the pump note's explicit instruction not to attempt them.

## Operator Items (per the pump note — I cannot start/stop services or launch a raw uvicorn, AG-10)

- **Restart the backend** to load this iteration's fix (`scripts/start-backend.sh`, host-guard-confined).
- **Re-measure a historical-first-view latency** (read-only, host-guard-confined): a first `GET
  /api/backtest?as_of=<never-viewed-date>` should now return promptly with `ensure_loop_ms` sub-millisecond
  in `logs/backend.log`, `evidence_status` in `{"refreshing","not_yet_computed"}`, and the compute
  happening in the background — a SECOND request for the same date afterward should show `"ready"`. This
  is the live confirmation of TC-1/TC-4 beyond my own unit-test evidence.
- TC-13/TC-14 as listed in Known Issues above.
- TC-12 (live browser walk of a first-ever historical `/backtest` view) — QA-stage, not mine to run.
