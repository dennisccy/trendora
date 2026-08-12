# goal-ops-hardening-iter-72 Dev Handoff

**Phase:** goal-ops-hardening-iter-72
**Date:** 2026-08-12
**Agent:** developer
**Status:** complete

## What Was Built

Five backend changes, matching the plan's exact "5 in-scope items" list — no frontend work
(`Frontend Present: no`):

1. **DB connection-pool resize** (`config.yaml`): `database.pool_size` 10→24, `database.max_overflow`
   20→44 (sum 30→68 — clears `server.limit_concurrency` 64 with real headroom). The stale "comfortably
   covers" comment corrected. `database.pragmas.mmap_size_bytes` untouched (still `0`, iter-24 audit).
2. **New boot-time invariant** (`apps/backend/app/config.py`, `Config._db_pool_covers_server_concurrency`):
   a `model_validator` raising a loud `ConfigError` if `database.pool_size + database.max_overflow <
   server.limit_concurrency` — turns the arithmetic mismatch iter-71 found into a boot-time failure
   instead of a live outage. `DatabaseCfg`'s pydantic field defaults (used by inline test fixtures that
   omit `database.pool_size`/`max_overflow`) raised to the same 24/44 so this new invariant never breaks
   a predating fixture.
3. **Serve-stale readiness** (`apps/backend/app/engine/readiness.py`, `get_readiness_and_preflight`):
   removed the synchronous `compute_readiness`/`compute_preflight` fallback iter-71 added for a cache
   entry aged past `max_stale_intervals x refresh_interval_seconds`. A cache entry, once it exists, is
   now ALWAYS served as-is with its real (uncapped) `stale_for_s` — never traded for a blocking recompute.
   The cold-start path (no cache entry has ever been published) is unchanged: still synchronous, still
   `stale_for_s: 0.0`. A NOTE comment at the call site documents the honesty-over-availability rationale.
4. **Post-lock recheck** (`_tick_and_cache`): a caller that genuinely queues behind `_TICK_LOCK` (detected
   via an explicit non-blocking `acquire()` attempt first) rechecks the cache immediately after finally
   acquiring the lock and reuses a fresh-enough entry another thread just published, instead of a fully
   redundant recompute. An UNCONTENDED caller (the common case) still always computes its own fresh entry
   — this preserves the existing degrade-on-error contract (a solo re-tick after a prior success must
   still genuinely attempt its own compute).
5. **`scripts/dev.sh` launcher parity** (backend subshell only): now reads the same `ServerOpsCfg`
   values `scripts/start-backend.sh` already enforces (`limit_concurrency` / `timeout_keep_alive_seconds`
   / `graceful_timeout_seconds`) and passes them as `--limit-concurrency` / `--timeout-keep-alive` /
   `--timeout-graceful-shutdown` on the launched uvicorn command line, and writes to the same
   `logs/backend.log` with the same append-only, `"dev.sh: launching at ..."`-headed pattern
   `start-backend.sh` already uses. The frontend (`next dev`) subshell is byte-unchanged.

Also added (in-scope per the plan's TC-10 item): a test-only fault-injection site,
`"data_overview_endpoint"`, in the existing `TRENDORA_FAULT_INJECT_MEMORY_ERROR` mechanism
(`apps/backend/app/engine/data_manager.py`), armed at the very top of `GET /api/data`'s handler
(`apps/backend/app/api/data.py`, `data_overview`) — deliberately UNGUARDED (unlike every other site this
hook arms, which sit inside isolate-and-continue blocks), so an armed drill makes the endpoint genuinely
raise/500, giving QA a deterministic way to capture the frontend's existing honest-fallback rendering.

## Files Changed

- `config.yaml` — `database.pool_size`/`max_overflow` resize + corrected comment.
- `apps/backend/app/config.py` — `DatabaseCfg` pool-field defaults raised to 24/44; new
  `Config._db_pool_covers_server_concurrency` cross-field boot validator; a doc-only note on
  `ReadinessCfg.max_stale_intervals` explaining it is now unconsumed by the readiness-cache read path.
- `apps/backend/app/engine/readiness.py` — `get_readiness_and_preflight` (serve-stale, docstring rewrite,
  honesty-over-availability NOTE); `_tick_and_cache` (post-lock recheck via explicit
  non-blocking-then-blocking `acquire()`).
- `apps/backend/app/api/health.py` — doc-only update correcting the module docstring's now-stale claim
  about the removed synchronous fallback.
- `apps/backend/app/api/data.py` — `data_overview`: fault-injection probe call at the top of the handler.
- `apps/backend/app/engine/data_manager.py` — `_FAULT_INJECT_SITES`: added `"data_overview_endpoint"`.
- `scripts/dev.sh` (repo-relative; physically `incredible_auto_dev/scripts/dev.sh` via this project's
  `scripts -> incredible_auto_dev/scripts` symlink) — backend subshell: extended config read, 3 new
  uvicorn flags, persistent-logfile boot line + output redirect. Frontend subshell: byte-unchanged.
- `apps/backend/tests/test_config.py` — 4 new tests (TC-1: real-config margin, minimal-config-defaults
  satisfy the invariant, below-threshold raises `ConfigError`, exactly-covering is valid).
- `apps/backend/tests/test_readiness.py` — `test_readiness_cache_falls_back_to_synchronous_compute_past_
  the_staleness_bound` REWRITTEN into `test_readiness_cache_serves_stale_entry_as_is_past_the_staleness_
  bound_no_fallback_compute` (TC-3); `test_readiness_cache_staleness_bound_never_raises_when_the_fallback_
  tick_also_fails` DELETED (its premise — a synchronous fallback that can itself fail — is no longer
  reachable code, matching the existing cold-start-failure test's coverage); `test_readiness_cache_serves_
  fresh_entry_with_stale_for_s_below_threshold` unchanged, still correct; 2 new deterministic post-lock-
  recheck tests (TC-4) using an explicit block/release harness (not a timing-race barrier).
- `apps/backend/tests/test_start_backend_script.py` — 1 new test,
  `test_dev_script_wires_server_ops_flags_and_persistent_logfile` (TC-5: uvicorn cmdline carries the 3
  flags with config-matching values, `logs/backend.log` gets a `dev.sh` boot line; TC-6: the frontend
  subshell's cmdline carries none of the 3 backend-only flags), plus 2 new port constants.
- `apps/backend/tests/test_api_data.py` — 2 new tests (the `data_overview_endpoint` fault probe makes
  `data_overview` raise when armed and is disarmed cleanly afterward; arming a DIFFERENT site is a no-op
  for this endpoint).
- `reports/perf-budgets.md` — new dated Addendum 37: the prod-launcher live drill (see below), the
  pool-sizing/readiness-cache fix summary, a new-finding note (uvicorn `--limit-concurrency` under
  extra-beyond-spec load), a host-contention observation, and the J-06 carry-item acknowledgment
  (iter-71/h).
- `docs/handoffs/goal-ops-hardening-iter-72-dev.md` — this handoff.

## Live Verification (TC-7)

A real, ~34-minute drill on `scripts/start-backend.sh` (backend-only; the browser-driven, both-launchers
variant is the separate browser-qa-agent lane's own job): a real `backfill` for a genuinely unsnapshotted
historical date, `GET /api/health` polled at 1 Hz throughout (poller armed 3s before job-start, closing
iter-71's own TC-5 gap). Result: **1,598 total polls, 0 non-answers, 0 non-200 responses**, p50/p90/p99/max
elapsed 0.008s / 0.497s / 0.968s / 1.129s, 0 breaches of the rescoped ≤2s during-warm ceiling, 0
`QueuePool ... overflow ... timeout` lines in `logs/backend.log` — against iter-71's baseline of 58 of 900
polls unanswered (longest gap 165s) and one `QueuePool` timeout. Full methodology, the raw CSV location,
and an honestly-reported harness-design finding (see below) are in `reports/perf-budgets.md` Addendum 37.

Two earlier drill attempts used MORE aggressive polling than TC-7 specifies (an extra fast job-status loop
+ a 5-second `GET /api/backtest` pinger) and both hit a sustained uvicorn `--limit-concurrency 64`
"Exceeded concurrency limit" 503 streak — confirmed via `logs/backend.log`, and confirmed NOT a client
connection-leak artifact (switching to a persistent, connection-reusing `httpx.Client` made no difference).
The third, TC-7-faithful attempt (1 Hz health poll + everything else on a slow ~30s cadence) ran completely
clean. This is recorded as a genuine new finding for a future round (a GIL/event-loop-fairness-under-load
class of issue, distinct from this iteration's DB-pool/lock-contention root cause) — not built, not fixed,
not conflated with this iteration's own DoD, which the clean third run satisfies in full.

## Tests Run

Given the shared `loaded_engine` pytest fixture costs ~1h on this host and none of this iteration's touched
tests depend on it, I ran targeted scopes rather than the full suite:

- `cd apps/backend && .venv/bin/python -m pytest tests/test_config.py -q` → **75 passed**
- `cd apps/backend && .venv/bin/python -m pytest tests/test_db.py -q -k "pool or pragma or sqlite"` →
  **5 passed**
- `cd apps/backend && .venv/bin/python -m pytest tests/test_readiness.py -q -k "cache_engine or cache or
  tick_and_cache or refresh or trigger_readiness or single_flight or tick_failure"` → **16 passed**
  (includes the pre-existing `test_readiness_cache_degrades_to_last_known_good_on_tick_failure`,
  specifically re-verified to still pass with the new post-lock recheck in place)
- `cd apps/backend && .venv/bin/python -m pytest tests/test_start_backend_script.py -v` → **12 passed,
  5 skipped** (the 5 skips are the pre-existing `TRENDORA_RUN_HEAVY_INGEST_TEST=1`-gated real full-rebuild/
  fault-injection drills — opt-in by design, unrelated to this iteration's diff)
- `cd apps/backend && .venv/bin/python -m pytest tests/test_api_data.py -q` → **55 passed**
- `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -q -k "fault"` → **4 passed**
- `cd apps/backend && .venv/bin/python -m pytest tests/test_ingest_finalize_fault_injection.py -q` →
  **5 passed**

Total: **172 passed, 5 (pre-existing, opt-in) skipped, 0 failed.**

## Pre-Handoff Verification

- **Service startup**: verified via `test_start_backend_script.py`'s real-process spawns — both
  `scripts/start-backend.sh` and `scripts/dev.sh` boot cleanly, serve `/api/health` within budget, and
  carry the correct uvicorn flags + persistent logfile. Also independently verified by the live TC-7 drill
  above (a real ~34-minute `scripts/start-backend.sh` run).
- **External integrations**: N/A — no new adapters/scrapers/live network calls this iteration (pure
  config/launcher/in-process-cache changes, offline-only per AG-9).
- **Native dependency binaries**: N/A — no new dependencies.
- **Server cleanup**: all spawned test-only backend processes (ports 28080, and the various
  `18xxx`/`19xxx` test ports) were verified stopped after each run; no stray `uvicorn`/`next dev` process
  left running.

## Known Issues

- The live TC-7 drill's own `backfill` job (2019-02-04) ran against the REAL shared dev DB
  (`apps/backend/data/trendora.db`) — no throwaway-DB config override was used for this drill (matching
  iter-70's own backend-only-drill precedent, which also ran against the real dev DB). The job did not
  reach a terminal status within the drill's own 30-minute wait cap before the harness tore the process
  down; a `ScannerRun` for 2019-02-04 WAS persisted (confirmed by direct query), and one
  `DataProviderRun` row is left with `status="running"` (the process was killed mid-flight). This is the
  exact scenario `test_j04_crash_with_midflight_job_restarts_to_interrupted_row_with_last_progress`
  (confirmed passing this pass) exists to cover — the existing boot-time orphan sweep will resolve this
  row to `"interrupted"` on the next real backend start. No manual DB cleanup was performed; flagging so
  the next agent to boot the shared dev backend isn't surprised by one stale `running` row briefly.
- The drill's single-date backfill took notably longer than any previously recorded single-date backfill
  in this session's own history (still scanning after 30 minutes). This host was running two other
  independent Claude Code sessions plus several Chrome processes concurrently throughout the drill
  (confirmed via `ps aux`) on a 4-core sandboxed environment — a plausible, mundane explanation unrelated
  to this iteration's diff (which touches connection pooling and an in-process cache, not the backfill's
  own per-date compute path). Not investigated further; `/api/health`'s own responsiveness throughout this
  same extended window is the actual TC-7 evidence and is unaffected either way.
- A new, NOT-in-scope finding is recorded in `reports/perf-budgets.md` Addendum 37: under
  request pressure beyond what TC-7 specifies (an extra continuous job-status + backtest hammering load
  layered on top of the 1 Hz health poll), uvicorn's own `--limit-concurrency` admission control can enter
  a sustained streak of "Exceeded concurrency limit" 503s — including to `/api/health` itself — that
  persists for as long as the underlying CPU-bound compute holds the CPU. This looks like a GIL/event-loop
  scheduling-fairness issue, not a DB pool or lock-contention issue, and is unaffected by this iteration's
  fix. It was NOT triggered by the actual TC-7 scenario (1 Hz health poll alone), so it does not block this
  iteration's DoD, but the owner/next iteration should be aware of it — it is plausibly one more argument
  for B-1107 (bounding concurrent heavy background computes), which remains owner-deferred.
- J-06's outstanding page-timing carry item (iter-71/h — a live browser TTI sweep across J-06's named
  pages, recorded in `reports/perf-budgets.md`'s budgets table) is still NOT addressed — this iteration is
  backend/launcher-only (`Frontend Present: no`), so no browser-driven page-load measurement was in scope.
  Carried forward explicitly in the perf-budgets.md addendum's own closing section.
- TC-12's `git status --porcelain -- config.yaml project-extensions/ scripts/` check must be run from
  BOTH this repo's own root (shows only `config.yaml`) AND the `scripts/`/`config/` symlink target's own
  git root at `incredible_auto_dev/` (shows only `scripts/dev.sh`) — `scripts/` is a symlink into a nested
  checkout of the same repository, so a single invocation from one location alone does not see both
  changed files. Verified both ways; no HOST-GUARD block or cap value touched in either.
