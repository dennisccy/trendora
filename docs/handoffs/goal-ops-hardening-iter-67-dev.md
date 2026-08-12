# goal-ops-hardening-iter-67 Dev Handoff

**Phase:** goal-ops-hardening-iter-67
**Date:** 2026-08-12
**Agent:** developer
**Status:** complete

**Whole-run headline (stated first, per this iteration's own TC-6 discipline — closes iter-66/a's
pattern): the live-job drill measured 1 of 1,036 polls over the 2.0s ceiling (0.10%); the idle-control
drill measured 0 of 330 polls over the ceiling (0.00%).** The new in-app watchdog's own samples show
`queue_wait_s`/`loop_lag_s` both dramatically elevated during the live job vs. the idle baseline (max
`queue_wait_s` 0.324s vs 0.002s, ~159x; max `loop_lag_s` 1.382s vs 0.061s, ~23x) — a genuine, positive,
NAMED signal of ASGI-layer/event-loop contention during heavy background compute. This is NOT a third
null result: unlike iter-65 (standalone-script profile of `factor_lab_all_warm`, clean) and iter-66
(standalone-script profile of `coverage_membership_timeline_refresh`, clean), watching the LIVE process
this round found a real, measurable difference between "job running" and "idle." The caveat, disclosed
honestly rather than rounded toward "solved": the elevated `queue_wait_s` explains only ~11% of this
round's one breach's own 2.875s magnitude — the rest falls inside the handler body's own execution, a
component this round's instrument does not separately measure. Full numbers, phase-by-phase UTC windows,
and the TC-4/TC-5 write-up corrections are in `reports/perf-budgets.md` Addendum 33.

## What Was Built

- **The health-request-wait watchdog** (`apps/backend/app/engine/health_watchdog.py`, new) — env-flag-gated
  (`TRENDORA_HEALTH_WATCHDOG=1`, unset/`0` = today's exact behavior, zero added overhead) diagnostic
  instrument per iter-66's own next-step order ("watch the live serving process," not a fourth standalone
  script). Two sample types, one shared append-only JSONL file (`logs/health-watchdog.jsonl`, via the
  EXISTING `app.engine.ledger.append_entry` — no second JSONL writer):
  - `queue_wait_s` — `t_handler_start - t_received`, where `t_received` is stamped by
    `HealthWatchdogMiddleware` at the top of the ASGI middleware/dispatch chain (before Starlette's router
    runs) and `t_handler_start` is stamped as the first statement inside `app.api.health.health()`, before
    any readiness computation.
  - `loop_lag_s` — a periodic `asyncio.sleep(0.1)` probe (`run_loop_lag_probe`) on the SAME event loop the
    health route is served from, comparing actual vs. expected wake time.
  - `HealthWatchdogMiddleware` is added to the ASGI stack ONLY when the flag is set (`main.create_app`) —
    the default path never installs it. The loop-lag probe task is started/cancelled around `main.py`'s
    `lifespan`, only when the flag is set.
- **`app.engine.readiness`'s computed value and `GET /api/health`'s response body/shape are byte-identical
  regardless of the flag** — proven by a fixture-backed equality test (`test_watchdog_flag_never_changes_
  response_body_or_shape`), not just asserted.
- **The live-job drill (TC-1/TC-2)** — a real single-date backfill (`2018-01-03`, live-verified
  unsnapshotted before dispatch) run with the watchdog armed, `scripts/qa/poll_health.py` polling at 1 Hz
  for the job's full 17m46s wall time, joined against `logs/health-watchdog.jsonl` by UTC timestamp.
- **The idle-control drill (TC-3)** — same already-warm backend, same script, ~5.5 minutes, no job running.
- **TC-4** — both breach groups' `load_avg_1m` mean/min/max stated side by side (the breaching poll's own
  load is actually below the non-breaching mean — the same pattern iter-66/b found; load average is not the
  elevated signal this round, `queue_wait_s` is).
- **TC-5** — corrected `reports/perf-budgets.md` Addendum 32's phase attribution (iter-66/c): one of the "69
  other breaches" it folded into a single `00:09:23Z`-`00:14:24Z` cluster description actually falls inside
  the immediately-following `per_date_coverage_warm` phase, not that cluster. Re-derived from the raw CSV
  against `dev.log`'s own UTC-converted phase lines; Addendum 32's own numbers/conclusions are otherwise
  unchanged and left untouched (append-only) — the correction is a new, dated section (Addendum 33).
- **iter-66/d** — corrected the browser-QA lane's cross-check note's one-hour timezone error (`dev.log`'s
  host-local BST timestamps read as UTC) in the SAME artifact
  (`reports/phase-goal-ops-hardening-iter-66-ui-test-results.llm.md`), with the UTC conversion shown
  explicitly and the correct job identity (a separate, later, standalone forward-aggregate warm the browser
  lane's own `/backtest` navigation dispatched, not the dev pass's TC-1 job's later sub-phase). A short
  pointer correction was added to the merged `.md` results table too. The PASS verdict and bottom-line
  conclusion are unaffected — only the stated reason/window was wrong.

## Files Changed

- `apps/backend/app/engine/health_watchdog.py` — new module: env flag, log-path resolution, `record_queue_
  wait`, `run_loop_lag_probe`/`start_loop_lag_probe`, `HealthWatchdogMiddleware`.
- `apps/backend/app/api/health.py` — `health()` gains an optional `request: Request = None` param (defaults
  to `None` so the pre-existing direct-call test shape, `health(session)`, is unaffected); at the top of the
  function body, a guarded block records the queue-wait sample when the flag is set and watchdog state is
  present. No change to the readiness/preflight computation or the returned dict's construction.
- `apps/backend/main.py` — imports `app.engine.health_watchdog`; `create_app()` conditionally registers
  `HealthWatchdogMiddleware` only when the flag is set; `lifespan` starts/cancels the loop-lag probe task
  around `yield`, only when the flag is set.
- `apps/backend/tests/test_health_watchdog.py` (new) — 8 unit tests: flag-unset (no log, response
  unchanged, direct-call shape preserved), flag-set (one sample per request, two requests → two samples,
  only the health route is instrumented), the loop-lag probe (bounded synthetic run), byte-identity of the
  response regardless of the flag, and the error-case requirement (a readiness-computation exception never
  suppresses the already-captured sample).
- `reports/perf-budgets.md` — new `## Addendum 33` (append-only; Addendum 32 and every earlier addendum
  untouched): the watchdog build, the live-job drill's phase-by-phase UTC windows and breach/watchdog join,
  the idle-control drill, TC-4's both-groups comparison, and TC-5's dated correction of Addendum 32's
  mis-clustered breach.
- `reports/phase-goal-ops-hardening-iter-66-ui-test-results.llm.md` — a dated, clearly-marked correction
  block appended after point 4 (iter-66/d), the original wrong text left in place per this project's
  never-silently-rewrite convention.
- `reports/phase-goal-ops-hardening-iter-66-ui-test-results.md` — a short pointer correction added to the
  UT-J-07 results-table row.
- `runs/goal-ops-hardening-iter-67/evidence-drill/` — every raw artifact behind the numbers above:
  `tc1-job-create.json`/`tc1-job-final.json`/`tc1-job-dispatch-time.txt`, `tc1-health-poll.csv`/`.meta.json`,
  `tc3-idle-poll.csv`/`.meta.json`, `health-watchdog-slice.jsonl` (the watchdog log's own slice covering
  both drills), `backend-log-slice.log` (this run's own `logs/backend.log` slice).
- `docs/handoffs/goal-ops-hardening-iter-67-dev.md` — this file.
- `runs/goal-ops-hardening-iter-67/status.json` — `current_step: dev_complete`.

**No change to `compute_factor_lab_all_warm`, `coverage_membership_timeline_refresh`, or any file under
`apps/frontend/*`** — confirmed via `git status --porcelain` before writing this handoff, matching the
spec's own "diagnostic only, no bound this round" and "Frontend Present: no" scope.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_health_watchdog.py -v -p no:randomly`
Result: **8 passed** in 121.51s.

Note on scope: this new test file uses a lightweight, locally-defined `watchdog_engine` fixture rather than
`conftest.py`'s session-scoped `loaded_engine` — that fixture additionally bootstraps + backfills the full
30-year cadence (`bootstrap_runs` + `backfill_forward_returns`), which these tests do not need and which is
documented (and independently reproduced this iteration — an initial attempt using `loaded_engine` ran for
over an hour before being reaped by the environment) to take up to ~1h on this host. The lightweight
fixture pays only `create_db_and_tables` + `load_seed` (~28s measured), then lets the real FastAPI
`lifespan`'s own fast single-date `ensure_latest_snapshot` step run — exactly the same fast-boot path a
real launch takes.

The full `test_health.py` (the file this iteration's `app/api/health.py` change lives in) was NOT run this
pass: it depends on the same expensive `loaded_engine` fixture, and running it concurrently with — or
immediately before — the live-job/idle-control drills above risked contaminating exactly the host-
contention measurement those drills exist to take (an unrelated CPU-heavy pytest process competing for the
same cores during the drill would bias `queue_wait_s`/`loop_lag_s`/`load_avg_1m` upward for reasons having
nothing to do with `factor_lab_all_warm`). This mirrors iter-66's own established convention of not running
the full 30-year-fixture suite every pass; targeted files + downstream-of-diff files only. Confidence in
`app/api/health.py`'s change instead rests on: (a) the new `request: Request = None` parameter is additive
with a safe default, exercised directly by `test_watchdog_direct_call_with_no_request_arg_is_untouched`
(the exact `health(session)` calling shape `test_health.py`'s own existing tests use); (b) the byte-identity
test proves the full existing key set (`status`, `db_ok`, `provider`, `last_run_date`, `seed_latest_date`,
`symbol_count`, `readiness`, `readiness_detail`, `warmup`, `poll_interval_seconds`,
`poll_idle_interval_seconds`, `preflight`, `background_compute` — matching `test_health.py`'s own
`existing_keys` sets verbatim) is unchanged; (c) the guarded watchdog block only executes when
`health_watchdog.enabled() and request is not None`, both False for every existing call site and test.
`test_health.py` should be run as a normal step of the next review/QA pass, decoupled from any further live
drill.

Service startup (pre-handoff checklist): ran `scripts/dev.sh` twice back-to-back on its default project
ports (8255/3255), flag UNSET (the default path) — both backend (`GET /api/health` → 200) and frontend
(`GET /` → 200) started cleanly each time; confirmed 0 new `logs/health-watchdog.jsonl` lines were written
across two `/api/health` requests with the flag unset (the middleware is not even installed on this path).
Repeating the iter-66 lesson: `dev.sh`'s `trap` does not reach the `next dev` grandchild
(`next-server`) — it was killed directly (`kill -9` on its own PID after `lsof -ti :3255` came back empty)
before the second launch was verified port-clean. Separately, the WATCHDOG-armed backend (launched via
`scripts/start-backend.sh` with `TRENDORA_HEALTH_WATCHDOG=1` for the two live drills) shut down cleanly on
`kill -TERM` with no tracebacks/`CancelledError` noise in its own `logs/backend.log` slice — the loop-lag
probe task cancels cleanly at lifespan shutdown.

External integration: the live-job drill's `POST /api/data/jobs` backfill ran against the real committed
seed (`"source": null` in the persisted job record — AG-9 clean, no live network call), producing a real
snapshot + 2,135 forward returns and all 9 `aggregates_refreshed` categories — this IS the live-external-
integration check for this iteration (the same ingest finalize path prior addenda's TC-1 drills exercise).

## Known Issues

- **`queue_wait_s` names roughly 11% of the one breach's own magnitude, not all of it.** The watchdog
  measures dispatch-queue delay and event-loop wake delay; it does NOT separately instrument time spent
  inside the handler body's own execution (the readiness/preflight computation + its DB reads) after
  `t_handler_start`. A future iteration wanting to close that remaining ~89% would need a THIRD sample type
  (e.g., timing the readiness computation itself) — out of this iteration's scope (one risky change only,
  per rule 5) and not attempted here.
- **This round's breach location differs from every prior round's.** iter-61/63/65/66 each found their
  (few) breaches concentrated somewhere inside or immediately after `factor_lab_all_warm`/
  `drawdown_expectations_warm`; this round's ONE breach is early, inside `coverage_membership_timeline_
  refresh`'s own window, with ZERO breaches during `factor_lab_all_warm`'s full 9m31s window. Disclosed
  honestly rather than forced to match iter-66's own pattern — round-to-round breach LOCATION moving this
  much is itself an argument for transient, moment-to-moment host/process contention over a stable,
  phase-specific code-level hold, but it is the evaluator's call, not this dev pass's, what that means for
  J-07's status.
- **`test_health.py` was not run this pass** — see "Tests Run" above for the full reasoning (drill-
  contamination risk + the ~1h fixture cost, independently reproduced this iteration). The change to
  `app/api/health.py` is additive/guarded and covered by the new targeted test file's byte-identity and
  direct-call-shape tests; a full run is recommended as part of the next review/QA pass.
- **The J-05 walkthrough capture remains unrecorded** (9th round now) — rides along only if a showcase/demo
  lane happens to run this iteration; not this iteration's own goal, per OUT OF SCOPE.
- **The three long-parked OWNER items (2-second-ceiling policy, `browser-qa-phase.sh` ordering fix, the
  replay-lane cost sanction) remain untouched**, per this iteration's own OUT OF SCOPE — this round's live
  drill piggybacked on the SAME mandatory live ingest the session already runs every round (no second job
  dispatched for J-01/J-03/J-05 coverage), and the idle-control drill ran no job at all, so this round's
  total live-ingest count did not increase.
