# goal-ops-hardening-iter-72 Execution Plan

## Context

Target journeys: J-05, J-07 (return to `passing`). Required-still-passing (widened, ESCALATE
carry-over): J-01, J-03, J-04, J-06, J-08, J-09. Depth: **full** (mandatory — prior verdict
ESCALATE). Frontend Present: **no** — no page/badge/banner changes this round.

iter-71 measured a real live outage on `scripts/dev.sh` under concurrent heavy load: 58/900
health polls got NO answer (longest gap 165s) and one `GET /api/data` 500 from
`sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 20 reached, timeout 30.00`.
Two causes, one fix each, plus a launcher-parity gap:

1. **Pool starvation:** `config.yaml`'s `database.pool_size`(10) + `max_overflow`(20) = 30 <
   `server.limit_concurrency`(64). The comment claiming it "comfortably covers" 64 is false.
2. **Self-inflicted stall:** iter-71's own staleness-bound fallback in
   `app.engine.readiness.get_readiness_and_preflight` calls a **synchronous**
   `compute_readiness`/`compute_preflight` once the cache ages past `max_stale_intervals ×
   refresh_interval_seconds` (1.5s default) — under pool starvation this serialized every
   caller behind `_TICK_LOCK`, self-amplifying the stall.
3. **Launcher mismatch:** the drill ran on `scripts/dev.sh`, which (unlike
   `scripts/start-backend.sh`) never applies `--limit-concurrency`/`--timeout-keep-alive`/
   `--timeout-graceful-shutdown` and writes no persistent `logs/backend.log` — violating J-04/
   J-06's own "never `dev.sh`" measurement requirement and denying this round evidence to
   diagnose a future dev-mode drill.

This plan builds exactly the 5 backend changes in the spec's IN SCOPE list, re-measures J-07 on
the production launcher, and confirms J-05 returns to passing. No frontend work — the existing
`/data` honest-fallback message (`apps/frontend/app/data/page.tsx:528`) is pre-existing and only
needs a fault-injected screenshot as evidence (TC-10), not a code change.

## What to Build

- **Pool resize** (`config.yaml`): raise `database.pool_size` + `database.max_overflow` so their
  sum is ≥ `server.limit_concurrency` (64). Keep `database.pragmas.mmap_size_bytes: 0` untouched
  (iter-24 audit — mmap stays disabled regardless of pool size). Fix the now-false "comfortably
  covers" comment at `config.yaml:119-120`. Suggested split: something with real headroom above
  the razor edge (e.g. `pool_size: 24` / `max_overflow: 44` = 68, or similar) — exact numbers are
  the developer's call as long as the sum invariant holds; do not touch any AG-10 cap value in
  the same file.
- **Serve-stale readiness fix** (`apps/backend/app/engine/readiness.py`,
  `get_readiness_and_preflight`): past `max_stale_intervals × refresh_interval_seconds`, serve
  the aged cache entry AS-IS with its real, now-uncapped `stale_for_s` — **remove** the
  synchronous `compute_readiness`/`compute_preflight` fallback iter-71 added for this branch.
  The cold-start path (`cache is None` — no tick has EVER published in this process) is
  **unchanged**: still a synchronous compute, still `stale_for_s: 0.0`. This is a net
  *removal* of a code path (the past-threshold branch collapses to "return the cache dict with
  a real age"), not new logic.
- **Post-lock recheck** (`_tick_and_cache`): immediately after acquiring `_TICK_LOCK`, re-read
  `_READINESS_CACHE`'s `computed_at`. If another thread already published an entry fresh enough
  while this caller was queued on the lock, reuse that entry instead of recomputing redundantly.
  Same producers, same lock, no interface/return-shape change.
- **Reviewer NOTE** (`readiness.py`, near the `_tick_and_cache` call site inside
  `get_readiness_and_preflight`, ~line 623): doc-only comment explaining the honesty-over-
  availability choice — why disclosed-stale-serve beats block-and-recompute when the
  synchronous fallback itself would be slow under exactly the load that caused staleness.
- **`scripts/dev.sh` launcher parity** (backend subshell ONLY — never the `next dev` frontend
  subshell): extend the existing single Python read (which already fetches
  `memory_cap_mb`/`malloc_arena_max` from `get_config()`) to also pull `limit_concurrency` /
  `timeout_keep_alive_seconds` / `graceful_timeout_seconds`, and pass them as
  `--limit-concurrency`/`--timeout-keep-alive`/`--timeout-graceful-shutdown` on the `exec
  uvicorn` line (config-derived, no magic numbers — same source `start-backend.sh` already
  reads). Add the SAME append-only persistent logfile pattern `start-backend.sh` uses: write to
  the existing fixed path `logs/backend.log` (the SAME file `test_start_backend_script.py`'s
  `LOG_FILE` constant already points at — do not introduce a second log path), a
  `"dev.sh: launching at ..."` boot header line, then redirect the uvicorn process's own
  stdout/stderr into that file (`>> "$LOG_FILE" 2>&1`) so a dev-mode crash also ends the log
  abruptly, mirroring `start-backend.sh`'s exact pattern (append, never truncate, across
  restarts).

## Agents Required

- backend-data: yes — all 5 in-scope items are backend/config/launcher-script work.
- frontend-ux: no — zero frontend file changes; TC-10 only captures evidence of pre-existing
  behavior via browser QA fault injection, no code change.

## Frontend Present: no

## Files to Create/Modify

- `config.yaml` -- resize `database.pool_size`/`max_overflow` (sum ≥ 64), fix the stale
  "comfortably covers" comment.
- `apps/backend/app/engine/readiness.py` -- `get_readiness_and_preflight`: collapse the
  past-threshold branch to disclosed-stale-serve (remove the synchronous fallback call added
  iter-71); `_tick_and_cache`: add the post-lock cache-freshness recheck; add the honesty-over-
  availability NOTE comment near the call site.
- `apps/backend/tests/test_readiness.py` -- rewrite
  `test_readiness_cache_falls_back_to_synchronous_compute_past_the_staleness_bound` (iter-71,
  ~line 1030) into a serve-stale assertion (age > threshold still served, real uncapped
  `stale_for_s`, zero synchronous compute calls via the SAME call-count instrumentation
  pattern already in the file); keep
  `test_readiness_cache_serves_fresh_entry_with_stale_for_s_below_threshold` (still correct,
  no change needed) and
  `test_readiness_cache_staleness_bound_never_raises_when_the_fallback_tick_also_fails` (adapt
  if its premise — "fallback also fails" — no longer applies once there's no fallback call on
  this branch; a cold-start-fails-too case may need to move under the TC-1 cold-start tests
  instead). Add a new post-lock-recheck test (TC-4): two racing callers while the cache is
  aged and a tick is mid-flight; assert neither blocks on the other's compute and a fresh
  publish is reused, not recomputed twice.
- `apps/backend/tests/test_db.py` or `test_config.py` -- new unit test asserting
  `database.pool_size + database.max_overflow >= server.limit_concurrency` for the real
  `config.yaml` (TC-1). Consider also adding a `Config`-level `model_validator(mode="after")`
  boot check (the codebase's pervasive convention for cross-field invariants elsewhere in
  `config.py`) raising a clear `ValueError` if the sum invariant is violated, with its own
  positive/negative test — this gives runtime enforcement, not just a test pinning today's
  numbers.
- `scripts/dev.sh` -- backend subshell: extend the config read, add the 3 uvicorn flags, add
  the persistent-logfile boot line + output redirect. Frontend (`next dev`) subshell: byte-
  unchanged (TC-6).
- `apps/backend/tests/test_start_backend_script.py` -- new `dev.sh` guard-mirroring tests
  mirroring the existing `test_start_backend_wires_server_ops_cfg_flags_into_uvicorn_cmdline`
  (TC-5: uvicorn cmdline carries the 3 flags with config-matching values) and
  `test_start_backend_writes_persistent_logfile_with_boot_events` (TC-5: `logs/backend.log`
  gets a `dev.sh` boot line); a TC-6 test confirming the frontend subshell's cmdline/env is
  unaffected (extend the existing `test_dev_script_applies_host_guard_caps_to_backend_only`-
  style frontend-untouched assertions if convenient, or add alongside it).
- `apps/backend/tests/test_data_manager.py` or a dedicated fault-injection test -- TC-10: a test
  hook forcing `GET /api/data` to raise, confirming the honest fallback message renders (this
  may already exist from J-07's own convention — check before adding a duplicate).
- `docs/handoffs/goal-ops-hardening-iter-72-dev.md` -- dev handoff (required by DoD).
- `reports/perf-budgets.md` -- new dated addendum: prod-launcher (`scripts/start-backend.sh` +
  `scripts/start-frontend.sh`) poll-count/non-answer/ceiling-breach statistics vs iter-71's
  58-of-900/165s figures, full distribution (not just a headline — iter-63's lesson: breach
  count, p90, p99, non-answers), launcher used, plus J-06's outstanding page-timing carry item
  (iter-71/h).

## UI Evolution

N/A — Frontend Present: no. No new capability, no new information displayed, no new user
actions, no UI surface or navigation changes this round (spec's own "Product surface delta:
None visible to a user this round in steady state").

## Key Test Scenarios

- TC-1: `config.yaml` loads with `database.pool_size + database.max_overflow >= 64`
  (`server.limit_concurrency`), asserted by a unit test.
- TC-2 (browser-qa, TC-7 in spec): launched via `scripts/start-backend.sh` +
  `scripts/start-frontend.sh` (never `dev.sh`), reproduce iter-71's concurrent load (full-
  horizon `factor_lab_all_warm` finalize + a J-09 background dispatch mid-warm), poller armed
  ≥2s before the job-start command, 1Hz `GET /api/health` polling throughout: zero non-answers,
  zero non-200s, zero polls exceed the rescoped ≤2s during-warm ceiling, zero
  `QueuePool ... overflow ... timeout` lines in `logs/backend.log`.
- TC-3: a test-hook-backdated cache entry past `max_stale_intervals × refresh_interval_seconds`
  is served AS-IS immediately with a real uncapped `stale_for_s`; call-count instrumentation
  proves `compute_readiness`/`compute_preflight` were NOT invoked synchronously for this call.
- TC-4: two callers race `get_readiness_and_preflight` while the cache is aged and a tick is
  mid-flight; neither blocks behind `_TICK_LOCK` waiting on the other's compute — both return
  within the same budget as a fresh-cache read; the post-lock recheck is proven (by call-count
  instrumentation) to skip a redundant compute when another thread already refreshed the cache.
- TC-5: `scripts/dev.sh`'s backend subshell launches uvicorn with
  `--limit-concurrency 64 --timeout-keep-alive 65 --timeout-graceful-shutdown 120`
  (config-derived) and `logs/backend.log` receives a `dev.sh` boot line.
- TC-6: the SAME `dev.sh` change leaves the frontend (`next dev`) subshell's cmdline/env
  byte-unchanged — no `--limit-concurrency`, no logfile redirect, no memory/CPU restriction.
- J-05 step 4 (health responsiveness during the SAME heavy job) and J-07 (full drill) both
  return to `passing` under this round's fixes, measured on the prod launcher.
- Required-still-passing (J-01, J-03, J-04, J-06, J-08, J-09) show no regression — the pool
  resize is process-wide and could plausibly shift timing on any DB-backed endpoint, so this is
  the full passing set, not a rotating smoke subset.
- `git status --porcelain -- config.yaml project-extensions/ scripts/` shows ONLY the pool-
  sizing lines in `config.yaml` and the guard-mirroring lines in `scripts/dev.sh` — no
  HOST-GUARD block or `memory_cap_mb`/`malloc_arena_max` value touched (TC-12).
- TC-10: a test-hook-forced `GET /api/data` failure still renders `/data`'s existing honest
  fallback message, never a blank crash overlay; screenshot filed as evidence.
- TC-11: `reports/perf-budgets.md` gains the dated addendum described above.

## Out of Scope (do not build)

- B-1107 (bounding concurrent heavy background computes) — owner-deferred.
- Rendering `stale_for_s` on the badge/banner — deferred, would be this cycle's first UI change.
- Any change to `compute_forward_aggregates` or the warm-path computation itself.
- Any AG-10 cap VALUE change (`memory_cap_mb`, `malloc_arena_max`, `host-guard.env`).
- A background-refresh-thread watchdog/restart mechanism.
- Regime Lab (iter-33/g) — deferred again.
- iter-71/e (QA citation defect) — framework-scope, not product.
