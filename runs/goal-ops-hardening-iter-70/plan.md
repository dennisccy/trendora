# goal-ops-hardening-iter-70 Execution Plan

## What to Build
- A bounded-interval background-refresh cache for `compute_readiness`/`compute_preflight`'s
  combined output, living inside `app.engine.readiness` (same module, same two producer
  functions — no second producer). Implemented as a daemon thread started from the SAME
  `lifespan` boot sequence that already starts `app.engine.warmup.start_warmup`
  (`apps/backend/main.py`), reusing that daemon-thread precedent.
- New config knob `readiness.refresh_interval_seconds` in `config.yaml`'s existing `readiness:`
  block (+ `ReadinessCfg` in `apps/backend/app/config.py`) — must be well under
  `startup.health_poll_interval_seconds` (2.0s), e.g. 0.5s, so a fresh cached value always
  predates the badge's next poll.
- `GET /api/health` (`apps/backend/app/api/health.py`) reads the cached readiness+preflight
  dict instead of calling `compute_readiness`/`compute_preflight` on the request thread. The
  three existing DB reads (`func.max(DailyPrice.date)`, `_distinct_symbol_count`,
  `func.max(ScannerRun.asof_date)`) stay on the request path, unchanged — out of scope.
- Cold-start synchronous fallback: before the background thread's first tick completes (boot,
  or a direct `health(session)` call with no thread running), compute once synchronously —
  preserves today's behavior for boot and unit tests (TC-1).
- Immediate refresh trigger at the end of `_refresh_ingest_aggregates`
  (`apps/backend/app/engine/data_manager.py`, returns `refreshed` around line 4824) — the same
  finalize hook every other ingest-time aggregate already refreshes from — so a job-completion
  state flip is reflected within one tick, not up to a full period (TC-4).
- Move `record_verdict_transition`'s existing on-transition write from the request path into
  the background tick — same dedup-against-last-recorded-verdict logic, same verdict-history
  file (TC-5).
- Degrade-on-error: a tick whose `compute_readiness`/`compute_preflight` call raises keeps
  serving the cache's last-known-good value (never blanks/500s `GET /api/health`); the thread
  keeps ticking on schedule (TC-6).
- Concurrency: an atomic swap (or equivalent) between the cache read (request thread) and cache
  write (background thread tick) so no torn/partial read is ever possible — mirrors the
  single-flight/lock idiom already used at `forward_testing._FORWARD_AGG_LOCK` /
  `data_manager._COVERAGE_LOCK`. Proven by a concurrency test.
- Reporting: append a new dated addendum to `reports/perf-budgets.md` (append-only, zero
  deletions to any prior addendum) with (a) this round's phase-grouped health-poll breach table
  from the live-warm drill, and (b) two corrections: iter-69/b's mis-stated "3 additional
  records" (correct: 83 in-window records belonging to a third client) and iter-69/c's TC-6
  scorecard label (`60d`, not `65d` — `config.yaml:777`).

## Agents Required
- backend-data: yes -- all work is backend: `app/engine/readiness.py` (new cache/thread/tick
  logic), `app/api/health.py` (read cache instead of computing), `main.py` (start the refresh
  thread from lifespan), `app/engine/data_manager.py` (immediate-refresh trigger call at the
  end of `_refresh_ingest_aggregates`), `config.yaml` + `app/config.py` (new knob), plus new/
  updated unit tests (`test_readiness.py`, `test_health.py`, `test_health_watchdog.py`,
  `test_data_manager.py`) and the `reports/perf-budgets.md` addendum.
- frontend-ux: no -- zero `apps/frontend/*` files touched; `GET /api/health`'s response
  body/shape is unchanged (byte-identical fields), so `HealthBadge`, `PreflightBanner`, and the
  `/data` `BackgroundComputePanel` need no change.

## Frontend Present: no

## Files to Create/Modify
- `apps/backend/app/engine/readiness.py` -- add the bounded-interval background-refresh cache
  (module-level cache dict + generation/version for atomic swap, a `start_readiness_refresh`
  daemon-thread launcher mirroring `warmup.start_warmup`'s single-flight guard shape, a tick
  function that calls `compute_readiness`+`compute_preflight` and now also fires
  `record_verdict_transition` from inside the tick, a synchronous cold-start accessor for when
  no tick has completed yet, and a public read accessor `GET /api/health` calls).
- `apps/backend/app/api/health.py` -- replace the direct `compute_readiness`/`compute_preflight`
  calls (+ the request-path `record_verdict_transition` call) with a read from the new cache
  accessor; keep the three DB reads and the watchdog `db_reads_s`/`readiness_s`/`preflight_s`
  sub-span timing (TC-7: post-change, `readiness_s`/`preflight_s` should read near-zero, a
  cache-dict read, not a compute call).
- `apps/backend/main.py` -- start the new readiness-refresh daemon thread in `lifespan`,
  alongside the existing `start_warmup` call.
- `apps/backend/app/engine/data_manager.py` -- at the end of `_refresh_ingest_aggregates`
  (after `refreshed` is finalized, before `return refreshed`), call the new immediate-refresh
  trigger.
- `config.yaml` -- add `readiness.refresh_interval_seconds` to the existing `readiness:` block.
- `apps/backend/app/config.py` -- extend `ReadinessCfg` with the new `refresh_interval_seconds`
  field (+ validation, mirroring `StartupCfg`'s `health_poll_interval_seconds` shape).
- `apps/backend/tests/test_readiness.py` -- tests for the cache tick, cold-start fallback,
  degrade-on-error, `record_verdict_transition`-fires-once-per-transition-from-the-tick, and the
  concurrency/atomic-swap test.
- `apps/backend/tests/test_health.py` -- fixture-backed byte-identity test: served fields equal
  a live `compute_readiness`/`compute_preflight` call taken at the same instant; cold-start test
  proving the synchronous fallback still returns a valid non-empty payload.
- `apps/backend/tests/test_health_watchdog.py` -- TC-7: under the new cached-read path,
  `readiness_s`/`preflight_s` read near-zero while `db_reads_s` is unaffected.
- `apps/backend/tests/test_data_manager.py` -- test that `_refresh_ingest_aggregates` fires the
  immediate refresh trigger (TC-4).
- `reports/perf-budgets.md` -- new dated addendum (append-only); no edits to any prior addendum.
- `runs/goal-session-ops-hardening/state/blueprint.md` -- append iter-70 narrative to the
  already-registered "Backend readiness / boot phase + preflight verdict" Data Contract row's
  Notes (no new row, no new endpoint).
- `runs/goal-session-ops-hardening/state/assumptions.md` -- iter-70 entry already documents the
  in-process-cache-vs-persisted-table interpretation call (per spec background; confirm present,
  do not duplicate).
- `docs/handoffs/goal-ops-hardening-iter-70-dev.md` -- dev handoff (required by DoD).

## UI Evolution
N/A -- Frontend Present: no. No new user-facing capability, no new information displayed, no
new user actions, no UI surface changes, no navigation changes. `GET /api/health`'s response
shape is byte-identical; `HealthBadge`, `PreflightBanner`, and `/data`'s `BackgroundComputePanel`
require no code change.

## Key Test Scenarios
- TC-1: boot / no-tick-yet cold start -- `GET /api/health` returns HTTP 200 with a
  synchronously-computed `readiness.state` matching a direct `compute_readiness(session)` call
  at the same moment.
- TC-2: idle steady state, thread ticked >=1 time -- 100 polls over 60s all serve byte-identical
  fields from the last completed tick (proves cache-read, not per-request recompute).
- TC-3: live full-deep-basis forward-aggregate warm (`factor_lab_all_warm`) -- `scripts/qa/
  poll_health.py` (dev drill) + the browser-qa lane's own independent J-07 drill, unioned, show
  zero polls over 2.0s and zero non-answers within the poller's 5.0s client timeout, reported
  grouped by `logs/backend.log`'s own ingest-phase windows.
- TC-4: a finalize hook completes and flips a state -- `GET /api/health` reflects the
  post-finalize value within one `readiness.refresh_interval_seconds` tick, not a full period,
  because the finalize hook fires an immediate refresh.
- TC-5: preflight verdict changes between two ticks -- exactly one `record_verdict_transition`
  entry is appended for that transition (same dedup-against-last-recorded-verdict behavior as
  the old per-request call).
- TC-6: a tick's `compute_readiness`/`compute_preflight` call raises (simulated DB/ledger
  failure) -- the NEXT `GET /api/health` request still serves the last-known-good cached value
  with HTTP 200 (never 5xx/blank); the thread's later tick resumes normal updates once the
  failure clears.
- TC-7: `TRENDORA_HEALTH_WATCHDOG=1` watchdog sub-spans -- under the new cached-read path,
  `readiness_s`/`preflight_s` are near-zero (a cache-dict read, not a compute call) while
  `db_reads_s` is unaffected.
- TC-8: `reports/perf-budgets.md` append-only addendum states the corrected record count (83,
  not 3) and the corrected scorecard label (`60d`, not `65d`); `git diff` for that file shows 0
  deletions to any pre-existing line.
- TC-9: J-01, J-03, J-04, J-05, J-06, J-08, J-09 deterministic goldens replay clean (`passing`/
  `already_passing`, fresh byte-distinct evidence frames, no journey moves to `failing`) --
  required-still-passing regression coverage.
- Concurrency test: a cache read on the request thread never observes a torn/partial write from
  an in-flight background tick (atomic swap or equivalent).
- Unit suite regression: `test_readiness.py`, `test_health.py`, `test_health_watchdog.py`,
  `test_data_manager.py` all pass with no regressions.

## Out of Scope (per spec, do not implement)
- Bounding `factor_lab_all_warm` / `coverage_membership_timeline_refresh` by code change (the
  "Do not redo" ban stays in force this round; RELEASED only as a fallback if TC-3 still shows
  concentrated breaches after this fix).
- Re-proving flag on/off byte-identity or re-deriving pre-receive gap / watchdog write cost
  (closed, binding "Do not redo").
- Arming `TRENDORA_HEALTH_WATCHDOG` for the browser-QA/replay lane's own backend, the
  `browser-qa-phase.sh` ordering-bug fix, the 2s-ceiling policy question, and the cost-sanction
  decision -- all owner-gated, not this iteration's to decide.
- Any change to `config.yaml` caps, `project-extensions/host-guard/`, or HOST-GUARD blocks in
  launch scripts (AG-10 envelope untouched).
- Touching `_distinct_symbol_count`, `func.max(DailyPrice.date)`, `func.max(ScannerRun.asof_date)`
  (the three DB reads) -- stay on the request path unchanged.
- Re-measuring J-07 steps 3/4 (VmPeak margin, memory-pressure abort) -- warm-path code untouched
  this iteration; carried on evidence durability.
