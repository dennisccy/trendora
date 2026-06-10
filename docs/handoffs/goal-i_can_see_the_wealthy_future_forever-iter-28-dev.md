# goal-i_can_see_the_wealthy_future_forever-iter-28 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-28
**Date:** 2026-06-10
**Agent:** developer
**Status:** complete

## What Was Built

J-40 (fast-ready boot + background warm-up + honest readiness) and J-41 (boot resilience —
concurrency-safe idempotent warm-up, non-fatal failures).

- **Split the FastAPI `lifespan` into fast-synchronous + background warm-up.** The boot now does only the
  minimal synchronous work before `yield` (config → tables → seed → persist ONLY the latest as-of
  snapshot), then begins serving. The full historical walk-forward cadence (`bootstrap_runs` historical
  dates + `backfill_forward_returns`) moved to a **background daemon-thread warm-up** launched after
  `yield`. The warm-up calls the SAME canonical engines (`scanner.run_scan`,
  `forward_testing.backfill_forward_returns`) — only the scheduling moved.
- **Single readiness producer + single serving endpoint.** `app.engine.readiness:compute_readiness`
  returns one honest state ∈ {`ready`, `initializing`, `unavailable`} plus warm-up `{done, total, status,
  message}`. Served on the EXTENDED `GET /api/health` (chosen as the single readiness home — no second
  `/api/readiness`). `ready` requires the latest snapshot servable AND the historical warm-up complete; a
  still-warming backend is `initializing` (never `unavailable`); DB-down / no-latest-snapshot is
  `unavailable`.
- **Concurrency-safe `run_scan` create.** Added catch-and-return-existing guards at BOTH the
  `session.flush()` (the `scanner_runs` INSERT — where SQLite surfaces the race) and the
  `session.commit()`: a duplicate-insert `IntegrityError` / `UNIQUE constraint failed:
  scanner_runs.asof_date` rolls back and returns the existing immutable row. Never raises, never
  duplicates, never overwrites.
- **Concurrency-safe forward-returns INSERT.** Added `_commit_forward_returns_concurrency_safe` (rolls
  back on a duplicate-key `IntegrityError`) used by both `_backfill` and `backfill_run_forward_returns`.
  INSERT-only + idempotent + concurrency-safe.
- **Non-fatal warm-up.** The background worker catches any exception, logs it
  (`logger.exception`), marks the job `failed`, and never re-raises out of the thread — the server keeps
  serving persisted snapshots and the next boot completes the idempotent remainder.
- **All startup tunables in config.** New typed, boot-validated `StartupCfg` (`config.startup`):
  `readiness_budget_seconds`, `warmup_batch_size`, `health_poll_interval_seconds`,
  `health_poll_idle_interval_seconds`. No startup/poll/budget literal lives in `main.py`,
  `readiness.py`, or `warmup.py`.
- **Frontend three-state readiness badge + warming states** — see the frontend handoff.

## Files Changed

- `apps/backend/main.py` — split `lifespan`: minimal sync (config/db/seed/`ensure_latest_snapshot`)
  before `yield`; `start_warmup` background task after; soft readiness-budget logging.
- `apps/backend/app/engine/warmup.py` (new) — `ensure_latest_snapshot`, `start_warmup` (daemon thread
  reusing `data_manager.JobProgress` + `_JOBS`), `_run_warmup` worker (non-fatal), `_warmup_dates`,
  `warmup_total`, `get_warmup`.
- `apps/backend/app/engine/readiness.py` (new) — `compute_readiness` (single honest readiness producer).
- `apps/backend/app/engine/scanner.py` — `IntegrityError` guards on the flush + commit of `run_scan`.
- `apps/backend/app/engine/forward_testing.py` — `_commit_forward_returns_concurrency_safe` on both
  backfill commit paths.
- `apps/backend/app/api/health.py` — extended with `readiness` + `warmup` + config-derived
  `poll_interval_seconds` / `poll_idle_interval_seconds`.
- `apps/backend/app/config.py` — new `StartupCfg`, registered on `Config` as `startup`.
- `config.yaml` — new `startup` block.
- `apps/backend/tests/test_warmup.py` (new) — J-40/J-41 + invariant proofs (12 tests).
- `apps/backend/tests/test_health.py` — assert the readiness + warmup + poll fields.
- `apps/backend/tests/test_config.py`, `test_config_engine.py`, `test_sectors.py`, `test_themes.py` —
  added the now-required `startup` block to the four inline config fixtures.
- `apps/frontend/lib/api.ts` — `ReadinessState` / `WarmupProgress` types; extended `HealthStatus`.
- `apps/frontend/components/readiness-provider.tsx` (new) — single client readiness poll (config-derived
  cadence) shared by the badge + analytics pages.
- `apps/frontend/components/health-badge.tsx` — three honest states with live "history n/m".
- `apps/frontend/components/warming-state.tsx` (new) — the "warming up (n/m)" card + `shouldShowWarming`.
- `apps/frontend/app/layout.tsx` — mount `ReadinessProvider` in the shell.
- `apps/frontend/app/backtest/page.tsx`, `apps/frontend/app/research/page.tsx` — render the warming state
  while `initializing`; auto-populate on the readiness flip.
- `runs/.../state/blueprint.md` — recorded the concrete readiness Data-Contract choice (`GET /api/health`).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v` (run in subsets to respect the ~14-min
single-run discipline; never two concurrent pytest invocations).

Result (subsets, all green):
- `test_warmup.py` — 12 passed (J-40 fast-boot lifecycle, readiness states, warm-up completion, J-41
  concurrency race under 2 sessions AND real threads, forward-returns idempotency, non-fatal warm-up +
  recovery, empty-DB `unavailable`, the byte-identical "scheduling-only" invariant).
- `test_config.py` + `test_config_engine.py` + `test_health.py` + `test_no_magic_numbers.py` +
  `test_db.py` + `test_sectors.py` + `test_themes.py` + `test_scanner.py` — 106 passed.
- `test_api_engine.py` + `test_api_backtest.py` + `test_backtest_scorecard.py` + `test_asof_resolver.py`
  + `test_data_manager.py` — see the QA full-suite run (started green at handoff time).
- Frontend `npx tsc --noEmit` — clean (0 errors).

Live integration verification (port-scoped, never broad pkill):
- Warm live DB boot: `Application startup complete` near-instant; `GET /api/health` →
  `readiness: ready`, `warmup history 10/10`; `GET /api/dashboard` → 200.
- **Fresh/cold DB boot (the J-40 keystone):** server became reachable at ~30 s (the single
  latest-snapshot step, NOT the full backfill); `GET /api/health` reported `initializing` with live
  progress `history 0/6 → 1/6 → … → 5/6 → 6/6`; `GET /api/dashboard` returned **200 WHILE warming**;
  readiness then flipped to `ready history 6/6`. No "Backend unavailable" wait.

## Known Issues

- **The per-date scan is genuinely slow** (~12–40 s per snapshot on the real seed; one latest-snapshot
  compute ≈ 29 s, near the 30 s readiness budget; a full cold warm-up ≈ 4+ min). This is the documented
  cost the goal's capability #33 (memoized/vectorized scan engine) targets — explicitly OUT OF SCOPE this
  iteration. J-40/J-41 are satisfied WITHOUT it: a cold boot serves the latest within ~one snapshot
  compute and warms the rest in the background. Capability #34 (committed precomputed snapshot seed) was
  also deferred per spec and is NOT needed to hit readiness — flagged here, not built.
- **Because the warm-up is real and slow, `test_warmup.py` is heavy** (~10–11 min for the warmed-engine +
  non-fatal tests, which run real cold warm-ups; the concurrency tests use a fast early date). It pays the
  full warm-up once via a module-scoped fixture. Do NOT run it concurrently with the rest of the suite.
- **`run_scan`'s concurrency guard handles `IntegrityError` only** (the documented `UNIQUE constraint`
  race). Under extreme SQLite write contention a `database is locked` `OperationalError` is theoretically
  possible (the engine sets no `busy_timeout`); that is an environmental contention condition, not the
  J-41 correctness failure, and was not observed in the threaded race test.
- **J-35/J-37/J-38/J-39** (the four `partial` Data-Manager browser-capture flows) were intentionally NOT
  touched (operator harness-wiring blocker, per the iter-27 STALLED). **J-22/J-23/J-24** (Yahoo-429
  data-walled) were not re-probed. No code change to any of their paths.

## Resume Verification (2026-06-10, re-dispatch — no implementation change)

This iteration was re-dispatched to the developer after the first dispatch was interrupted post-dev. The
working-tree implementation was VERIFIED and CONFIRMED INTACT — nothing was re-implemented or reverted, and
no source changed (the full backend suite remains the QA gate's single run). Evidence gathered this pass:

- **Source coherence confirmed** on every changed/new file: the lifespan split (`main.py`), the single
  warm-up controller (`warmup.py`) and single readiness producer (`readiness.py`), the `run_scan`
  `IntegrityError` guards at BOTH flush + commit (`scanner.py`), the forward-returns concurrency guard on
  both backfill paths (`forward_testing.py`), the extended `GET /api/health` (single readiness reader), the
  boot-validated `StartupCfg` + `config.yaml startup` block, and the four config fixtures all match the
  descriptions above. Frontend: single `ReadinessProvider` mounted in the shell, three-state badge, shared
  warming card on `/backtest` + `/research`, config-derived poll cadence, no new date state (J-18).
- **Fast deterministic test subsets re-run green** (the slow module-scoped `warmed_engine` J-40 tests were
  intentionally DESELECTED — they are the QA gate's single full-suite run, ~10–11 min): `test_config.py` +
  `test_config_engine.py` + `test_sectors.py` + `test_themes.py` + `test_health.py` +
  `test_no_magic_numbers.py` + `test_db.py` → **96 passed**; the J-41 fast proofs from `test_warmup.py`
  (`run_scan` race under two sessions AND real threads, forward-returns idempotency, non-fatal warm-up +
  recovery, empty-DB `unavailable`) → **5 passed**. Frontend `npx tsc --noEmit` → **clean (exit 0)**.
- **Live service-startup check** (port-scoped, never broad pkill): booted `main:app` on a throwaway port
  against the warm live DB (94 runs / 162 symbols / latest 2026-06-08). `Application startup complete`
  near-instant; `GET /api/health` → 200 with `readiness: ready`, `warmup history 10/10` (status `ok`),
  config-derived `poll_interval_seconds: 2.0` / `poll_idle_interval_seconds: 30.0`; `GET /api/dashboard`
  and `GET /api/stocks` → 200 (J-40: core read pages serve the latest snapshot on a fast boot). The boot
  was idempotent + non-mutating on the warm DB (run already present → `run_scan` returned the existing
  immutable row; warm-up found all 10 cadence snapshots present and inserted nothing; DB mtime unchanged).
  Server stopped cleanly by PID; port freed.

## Fix Notes (2026-06-10, QA-FAIL fix cycle — second QA turnaround)

**Mode:** FIX (QA verdict FAIL — `~48–60+` API tests failed when the suite was run together, yet passed
in isolation; the run crawled 69 min to ~19%). No product behavior changed — this is purely a
test-harness-determinism + boot-resilience seam.

### Confirmed root cause (from a real failure trace, not the hypothesis alone)

Reproduced by running two TestClient-based files TOGETHER (`tests/test_api_runs.py tests/test_api_watchlist.py`):

```
tests/test_api_runs.py:30  assert len(runs) >= 2  →  AssertionError: assert 1 >= 2
tests/test_api_runs.py:74  assert latest["asof_date"] != oldest["asof_date"]  →  '2026-05-28' != '2026-05-28'
tests/test_api_runs.py:88  expected a seeded Risk-off run in the history  →  assert []
```

The DB held only **1** run (`2026-05-28`, the latest) instead of the full cadence. The cause is exactly the
diagnosed scheduling seam: the API suite had an implicit determinism contract with the OLD **synchronous**
lifespan (which ran `bootstrap_runs` + `backfill_forward_returns` before the first request, so the shared
session DB deterministically held the FULL historical cadence — a test even comments "counted AFTER lifespan
bootstrap, so the counts are stable"). The new fast-ready lifespan persists ONLY the latest snapshot and
spawns the cadence warm-up in a **background daemon thread**, so (a) tests assert against an **incomplete,
concurrently-mutating** DB, and (b) `start_warmup` had **no single-flight guard** — EVERY `TestClient(main.app)`
entry (15–33 per file) spawned ANOTHER full warm-up thread over the one SQLite test DB, so N concurrent
daemons contended for the write lock → the 69-min crawl. (Verified the warmup `JobProgress` does NOT leak into
any `/api/data` listing: `recent_runs`/`resumable_imports`/`unfinished_imports` read DB tables, never the
in-memory `_JOBS` registry; the `test_api_data` failure was DB write-contention, not a payload leak — so no
listing change was needed.)

### The two fixes (no product-value change; same canonical engines; only scheduling + concurrency)

1. **Single-flight guard in `start_warmup`** (`apps/backend/app/engine/warmup.py`). A module-level
   `_WARMUP_LOCK` + `_WARMUP_THREAD` reference: while a warm-up's daemon thread is still alive, a
   re-invocation returns the existing `WARMUP_JOB_ID` and does NOT spawn a duplicate concurrent worker; a
   re-launch AFTER the prior warm-up settled (ok/failed) is allowed (the next boot finishes the idempotent
   remainder). This is the J-41 re-spawn behavior the spec names (readiness-probe re-spawn / `--reload`
   double-fire) AND it removes the per-TestClient-entry thread storm. Covered by a new unit test
   (`test_start_warmup_is_single_flight_no_duplicate_concurrent_worker`): a gated worker is held alive while
   5 re-invocations all return the same job id and exactly ONE `warmup-*` thread stays alive; after it
   settles a fresh `start_warmup` is allowed again.

2. **Pre-warm the shared session DB once in `conftest.loaded_engine`** (`apps/backend/tests/conftest.py`).
   After loading the seed, the fixture now calls the SAME canonical engines the warm-up uses
   (`bootstrap_runs(engine, config)` + `backfill_forward_returns(engine, config)`) ONCE, up-front and
   synchronously, restoring the fully-warm-DB contract the API suite depends on — WITHOUT weakening the
   product's fast boot (the lifespan itself is unchanged). `test_warmup.py`'s "scheduling-only" invariant
   already proves this is byte-identical to what the background warm-up produces (no second compute path).
   With the DB already warm, the TestClient lifespan's single-flight-guarded warm-up is an idempotent no-op.

### Files changed in this fix cycle

- `apps/backend/app/engine/warmup.py` — `_WARMUP_LOCK` + `_WARMUP_THREAD`; single-flight check-and-spawn in
  `start_warmup` (returns the existing job id while a warm-up is alive).
- `apps/backend/tests/conftest.py` — `loaded_engine` pre-warms the shared session DB once via
  `bootstrap_runs` + `backfill_forward_returns` (the canonical engines).
- `apps/backend/tests/test_warmup.py` — added the single-flight regression test (13 tests total now).

### Verification

- `tests/test_api_runs.py tests/test_api_watchlist.py` (the reproducer) → **15 passed** (188 s) — was 3 failed.
- `tests/test_api_engine.py tests/test_api_data.py tests/test_api_backtest.py tests/test_api_research.py`
  (the four previously-failing API files together) → **102 passed** (268 s).
- `tests/test_warmup.py::test_start_warmup_is_single_flight_no_duplicate_concurrent_worker` → **1 passed**.
- **FULL suite once at the QA gate (the DoD):**
  `cd apps/backend && .venv/bin/python -m pytest tests/ -q` → **621 passed, 4 skipped, 0 failed in
  1971.46s (0:32:51)**, exit code 0. The 4 skips are the offline external-network integration tests
  (expected offline). The 69-min-at-19% crawl is GONE — the suite now completes deterministically in ~33
  min (dominated by `test_warmup.py`'s real ~10-min warm-up + the accepted per-snapshot scan cost), with
  NO concurrent-warm-up write contention. This was a single run (never two concurrent pytest invocations).
