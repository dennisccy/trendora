# goal-ops-hardening-iter-70 Dev Handoff

**Phase:** goal-ops-hardening-iter-70
**Date:** 2026-08-12
**Agent:** developer
**Status:** complete

## What Was Built

- **A bounded-interval background-refresh cache** for `compute_readiness`/`compute_preflight`'s combined
  output, living inside `app.engine.readiness` (the SAME module, SAME two producer functions — no second
  producer, no new endpoint). A new daemon thread (`start_readiness_refresh`/`stop_readiness_refresh`),
  started/stopped symmetrically from the SAME `lifespan` boot sequence that already starts
  `app.engine.warmup.start_warmup` (mirrors that daemon-thread precedent; stop is new, mirroring the
  health-watchdog loop-lag probe's own start/cancel symmetry). Ticks every
  `readiness.refresh_interval_seconds` (new config knob, `config.yaml`, default `0.5s`, well under
  `startup.health_poll_interval_seconds`'s `2.0s`).
- **`GET /api/health`** now reads the cached `{"readiness": ..., "preflight": ...}` dict
  (`get_readiness_and_preflight`) instead of calling `compute_readiness`/`compute_preflight` on the
  request thread. The three existing DB reads (`func.max(DailyPrice.date)`, `_distinct_symbol_count`,
  `func.max(ScannerRun.asof_date)`) are unchanged — out of scope, iter-69's attribution never implicated
  them.
- **Cold-start synchronous fallback**: before the background thread's first tick completes (boot, or a
  direct `health(session)` call with no thread running), the accessor computes once synchronously —
  byte-identical to the pre-iteration per-request behavior (TC-1).
- **Immediate-refresh trigger**: `data_manager._refresh_ingest_aggregates` now calls
  `readiness.trigger_readiness_refresh(session, config=cfg)` at its very end (deferred import — `readiness`
  imports `warmup`, which imports `data_manager` at load time, so a top-level import would cycle) — the
  SAME finalize hook every other ingest-time aggregate already refreshes from, so a job-completion state
  flip (e.g. `awaiting_snapshot` → `ready`) is reflected within one tick rather than a full period (TC-4).
- **`record_verdict_transition`** moved from the request path into the tick — same dedup-against-last-
  recorded-verdict logic, same verdict-history file, no longer invoked per-request (TC-5).
- **Degrade-on-error**: a tick whose compute raises is caught, logged, and leaves the cache's prior
  last-known-good value untouched; the thread keeps ticking on schedule (TC-6).
- **Concurrency**: the whole `{"readiness":..., "preflight":...}` payload is built first, then published
  via one atomic dict-reference reassignment (`_READINESS_CACHE = payload`), serialized against concurrent
  writers by `_TICK_LOCK` — proven by a dedicated concurrency test that tags each tick and asserts no
  reader ever observes a mismatched tag pair.
- **Fix mid-implementation**: the first cut left the shared cache untouched across repeated `lifespan`
  entries (only the thread's own single-flight guard existed), which let one test's cached value leak into
  an unrelated later test's very first request against a freshly-booted, different engine — caught live by
  `test_health_background_compute_serves_failed_outcome_verbatim` failing on the first full test run.
  Fixed by resetting the cache to `None` whenever `start_readiness_refresh` actually spawns a fresh thread
  (never on the single-flight no-op path); zero effect on real deployment (this only matters where one
  process re-enters `lifespan` repeatedly against different engines — every `TestClient` block in the test
  suite). Documented as its own paragraph in `reports/perf-budgets.md` Addendum 36.
- **Reporting**: `reports/perf-budgets.md` Addendum 36 (append-only, 216 insertions / 0 deletions) — a
  real, freshly-run live-warm drill (17m20s, backfill of a genuinely unsnapshotted 2019-02-05, all 9
  ingest-finalize aggregate categories warmed including `factor_lab_all_warm` and
  `drawdown_expectations_warm`) grouped by ingest phase per `logs/backend.log`'s own phase-timing lines:
  **0 of 1,030 polls breached the 2.0s ceiling; 0 non-answers** (first zero-breach round in this session's
  own multi-iteration measurement history), plus the two iter-69 write-up corrections (iter-69/b: the
  "3 additional records" mis-statement, corrected to 83 records belonging to a third client; iter-69/c: the
  TC-6 scorecard label, corrected from "65d" to "60d" per `config.yaml:777`).

## Files Changed

- `apps/backend/app/engine/readiness.py` -- added the bounded-interval background-refresh cache (module-
  level `_READINESS_CACHE` + `_TICK_LOCK`, `_compute_tick`/`_tick_and_cache`/`get_readiness_and_preflight`,
  the daemon-thread launcher/stopper `start_readiness_refresh`/`stop_readiness_refresh` with single-flight
  guard + cache reset on fresh spawn, the immediate-refresh trigger `trigger_readiness_refresh`, and a test
  seam `reset_readiness_refresh_cache`).
- `apps/backend/app/api/health.py` -- replaced the direct `compute_readiness`/`compute_preflight` calls
  (and the request-path `record_verdict_transition` call) with a read from `get_readiness_and_preflight`;
  kept the three DB reads and the watchdog `db_reads_s`/`readiness_s`/`preflight_s` sub-span timing intact
  (now timing a cache read, not a compute call).
- `apps/backend/main.py` -- start `start_readiness_refresh(engine, config)` in `lifespan` alongside
  `start_warmup`; stop it symmetrically after `yield`, alongside the health-watchdog loop-lag probe's own
  cancellation.
- `apps/backend/app/engine/data_manager.py` -- at the end of `_refresh_ingest_aggregates` (after
  `refreshed` is finalized, before `return refreshed`), a deferred-imported call to
  `readiness.trigger_readiness_refresh(session, config=cfg)`.
- `config.yaml` -- added `readiness.refresh_interval_seconds: 0.5`.
- `apps/backend/app/config.py` -- extended `ReadinessCfg` with `refresh_interval_seconds: float = 0.5`
  (back-compat default, mirrors `StartupCfg`'s own convention) + a `> 0` boot-time validation.
- `apps/backend/tests/test_readiness.py` -- 10 new tests: config validation (default + rejection), cold-
  start byte-identity, cold-start never-raises-on-first-tick-failure, steady-state cache-read-not-recompute
  (call-counting), degrade-on-error/last-known-good, verdict-transition-fires-once-under-concurrent-ticks,
  the atomic-swap concurrency test (tagged-tick torn-read check), the immediate-refresh trigger, and the
  single-flight thread-start guard. Uses a new dedicated `cache_engine` fixture (tiny, fast) plus an
  autouse `_isolated_readiness_cache` fixture that stops any live thread and resets the cache before/after
  every test in the file.
- `apps/backend/tests/test_health.py` -- 2 new tests (cold-start byte-identity and steady-state cache-read-
  not-recompute at the handler level); updated `test_health_background_compute_degrades_honestly_when_
  readiness_fails`'s fault-injection target from `compute_readiness` to `get_readiness_and_preflight`
  (the request path no longer calls the former directly).
- `apps/backend/tests/test_health_watchdog.py` -- 1 new test proving `readiness_s`/`preflight_s` read
  near-zero under the cached path (TC-7); updated 2 existing tests' fault-injection targets from
  `compute_readiness` to `get_readiness_and_preflight` for the same reason.
- `apps/backend/tests/test_data_manager.py` -- 1 new test proving `_refresh_ingest_aggregates` fires the
  immediate-refresh trigger exactly once, with the correct (same) session (TC-4's finalize-hook half).
- `reports/perf-budgets.md` -- Addendum 36 (append-only, 0 deletions — `git diff` verified). **Updated by the
  iter-70 audit:** now 234 insertions / 0 deletions (was 216 / 0) after the audit corrected two coverage
  mis-statements inside this iteration's OWN new addendum text. TC-8's "0 deletions to any pre-existing
  line" is unchanged and independently re-verified (`git diff -U0 | grep '^-'` is empty).
- `docs/handoffs/goal-ops-hardening-iter-70-dev.md` -- this handoff.

Not modified (per plan, already present from the decomposer): `runs/goal-session-ops-hardening/state/
blueprint.md` (iter-70 narrative already appended to the Backend readiness Data Contract row's Notes) and
`runs/goal-session-ops-hardening/state/assumptions.md` (the iter-70 in-process-cache-vs-persisted-table
interpretation entry already present).

## iter-70 Audit Addendum (2026-08-12)

Three changes were applied on top of this handoff by the auditor — see
`docs/handoffs/goal-ops-hardening-iter-70-audit.md` for the findings and evidence:

1. `apps/backend/app/engine/readiness.py` — the three new `logger.exception(...)` calls in the tick path now
   route through a local `_log_tick_failure` guard (the SAME shape `data_manager._log_isolation_failure`
   already applies to every isolation handler inside `_refresh_ingest_aggregates`), so a logging allocation
   that itself raises under memory pressure can neither escape into the calling ingest job (discarding
   `refreshed`) nor kill the refresh thread (freezing the cache silently). Two regression tests added to
   `tests/test_readiness.py`, verified failing before the guard and passing after.
2. `reports/perf-budgets.md` Addendum 36 — corrected the drill's stated poller window and the phase-table
   `†` footnote: the poller's first row is 13:30:15.372Z, **32.1s after** the job's 13:29:43.298Z start, so
   the table's first four `0†` phase rows are a genuine coverage gap, not a 1 Hz sampling artifact. The
   0-of-1,030 / 0-non-answers headline is unaffected.
3. The drill's raw evidence (both poll CSVs + metas, the in-window watchdog slice, the job's phase-timing
   log lines) was copied out of the ephemeral pipeline `TMPDIR` into
   `runs/goal-ops-hardening-iter-70/evidence-drill/`, matching the iter-66..69 precedent — TC-3's headline
   otherwise rested on files that existed only in a scratch directory.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_readiness.py tests/test_health.py
tests/test_data_manager.py -m "not integration" -v` (280 collected; `loaded_engine` built once,
session-scoped) plus `tests/test_health_watchdog.py` run standalone (own lightweight fixture).

Result:
- `test_health_watchdog.py` alone: **16/16 passed** (118.09s).
- `test_readiness.py` + `test_health.py` + `test_data_manager.py` combined: first full run caught a real
  bug (documented above and in the perf-budgets addendum), fixed, re-run clean: **279 passed, 1 failed**
  in 1:10:53 wall-clock.
- The one remaining failure, `test_data_manager.py::test_availability_from_storage_stuck_running_row_
  from_crashed_process_still_reads_as_in_flight`, is a **pre-existing test-order-sensitivity artifact, not
  a regression from this diff**: it asserts `data_manager._JOBS == {}` as a sanity precondition, which
  trips only because this developer pass's own non-default invocation order runs `test_health.py`'s
  `TestClient(main.app)` calls (which populate the process-global `_JOBS['warmup']` registry — pre-existing
  `warmup.py` bookkeeping, untouched by this iteration) BEFORE `test_data_manager.py`. Confirmed pre-
  existing/order-only by re-running the test in isolation (passes, 0.55s); under the project's DEFAULT
  alphabetical collection order, `test_data_manager.py` runs before `test_health.py`, so this ordering
  never manifests. Not fixed — a different file/test, outside this iteration's scope.

## Live Verification (not mocked)

- **Service startup**: `scripts/dev.sh` started, stopped, and restarted cleanly — both backend (`:8255`)
  and frontend (`:3255`) came up on both the first start and the restart, with no port conflicts (the
  script's own `lsof`/`fuser` kill loop correctly cleared a stray `next-server` process left over from a
  manual `pkill` that didn't reach the full Next.js process tree — confirmed in `iter70-dev2.log`).
- **Real live-warm drill** (not a unit test): `scripts/start-backend.sh` with `TRENDORA_HEALTH_WATCHDOG=1`
  against the real dev DB (`apps/backend/data/trendora.db`, 7.8 GB, full 30-year basis), a genuine backfill
  of an unsnapshotted historical date (2019-02-05, verified unsnapshotted immediately before dispatch),
  polled at 1 Hz for the full 17m20s job. Result: **0 of 1,030 polls over the 2.0s ceiling, 0 non-answers**,
  including the full 9.4-minute `factor_lab_all_warm` phase (this session's own previously-confirmed
  96%-of-breaches phase) and the 5.7-minute `drawdown_expectations_warm` phase. `readiness_s`/`preflight_s`
  sub-spans (watchdog-instrumented): literally `0.0000s` at every percentile throughout, live-warm included.
  `bars_fetched: 0`, `source: null` (AG-9 clean — backfill computes snapshots from already-stored bars
  only, never a live fetch). Full method and numbers: `reports/perf-budgets.md` Addendum 36.
- AG-10: the drill ran through `scripts/start-backend.sh` with host-guard's declared caps intact
  (`memory_cap_mb=8192`, `malloc_arena_max=2`, `cpu_list=0-15`, `blas_threads=8`, live-read from
  `logs/backend.log`); no HOST-GUARD block, cap value, or launch script was touched (`git status
  --porcelain -- config.yaml project-extensions/ scripts/` shows only this iteration's own new
  `readiness.refresh_interval_seconds` config line).

## Known Issues

- The one pre-existing test-order-sensitivity artifact described above (`test_availability_from_storage_
  stuck_running_row_from_crashed_process_still_reads_as_in_flight`) — not this iteration's bug, not fixed
  (out of scope: a different test/file this iteration's plan does not name).
- The browser-qa lane's own independent J-07 drill (TC-3's "union of both drills") has not run as part of
  this developer pass — it is a separate downstream pipeline step. This handoff's own dev drill is complete
  and self-sufficient (0 breaches, 0 non-answers) on its own.
- `readiness.refresh_interval_seconds` is an in-process, bounded-interval cache (not a persisted DB table)
  per the iter-70 assumption-ledger entry's interpretation call — reversible to a persisted table in a
  future iteration without touching the canonical producer/endpoint again, if ever needed.
- Out of scope, unchanged this iteration (per spec): bounding `factor_lab_all_warm`/
  `coverage_membership_timeline_refresh` by code change (this round's own drill shows the RELEASED
  alternative is not currently needed — zero breaches observed); re-measuring J-07 steps 3/4 (VmPeak
  margin, memory-pressure abort — warm-path code untouched, carried on evidence durability); the owner's
  three still-open questions (2s-ceiling policy, `browser-qa-phase.sh` sign-off, cost sanction).
