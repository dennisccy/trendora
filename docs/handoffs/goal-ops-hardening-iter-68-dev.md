# goal-ops-hardening-iter-68 Dev Handoff

**Phase:** goal-ops-hardening-iter-68
**Date:** 2026-08-12
**Agent:** developer
**Status:** complete

**`apps/backend/tests/test_health.py` ran as an ordinary step this round (not skipped, not piggybacked on
any drill): 17 passed in 3842.23s (1:04:02), zero failures.** Whole-run breach counts (stated first, per
this session's own TC-6 discipline): the live-job drill measured **1 of 1,039 polls over the 2.0s ceiling
(0.10%)**; the idle-control drill measured **0 of 330 polls over the ceiling (0.00%)**. The new third
watchdog sample, `handler_compute_s`, matched against this round's ONE breach, names **~79.4% of its
2.543s magnitude on its own** (~80.4% combined with the same-request `queue_wait_s`/`loop_lag_s`) — the
first majority-NAMED breach in this session's J-07 work, against iter-67's own ~11%. A ~19.6% (0.497s)
residual remains genuinely unnamed even after all three samples — reported honestly, not rounded toward
"fully explained" (most likely source: pre-`t_received` overhead this instrument does not reach — TCP
accept/handshake, `CORSMiddleware`, the poll client's own `urllib` overhead — named but not measured this
round; a fourth instrument is out of this iteration's scope). Full numbers, the phase-by-phase UTC join,
and the TC-5/TC-6 write-up corrections are in `reports/perf-budgets.md` Addendum 34.

## What Was Built

- **The third watchdog sample, `handler_compute_s`** (`apps/backend/app/engine/health_watchdog.py`,
  `record_handler_compute`) — measured from `t_handler_start` (already recorded, iter-67) to immediately
  before `app.api.health.health()` constructs/returns its response, after every readiness/preflight
  computation and DB read (all already error-guarded before this iteration, so the recording point is
  always reached whenever the watchdog is active). SAME env flag (`TRENDORA_HEALTH_WATCHDOG=1`), SAME
  writer (`app.engine.ledger.append_entry`), SAME file (`logs/health-watchdog.jsonl`) — no second flag, no
  second writer. Shares its sibling `queue_wait_s` sample's exact `t_received_wall` timestamp for the SAME
  request, so a downstream join keys on it directly rather than nearest-neighbor matching.
- **`app.api.health.health()`** — `t_handler_start`/`t_received_wall` are now kept for the whole function
  body (previously scoped to the queue-wait block only) so the new sample can time against the same start
  instant; one new guarded block immediately before the `return {...}` records `handler_compute_s` when the
  watchdog is active. No change to what is computed or returned — `app.engine.readiness`'s value and
  `GET /api/health`'s response body/shape stay byte-identical regardless of the flag (unchanged, re-proven
  by the existing + extended unit tests).
- **3 new unit tests** in `apps/backend/tests/test_health_watchdog.py` (11 total, all passing, 122.09s):
  flag-unset writes no `handler_compute_s` entry; flag-set writes exactly one `handler_compute_s` record
  (`>= 0`) alongside the existing `queue_wait_s` record for the SAME request, sharing its timestamp; two
  requests write two samples. The existing error-case test
  (`test_watchdog_records_sample_even_when_readiness_computation_raises`) was extended to also assert a
  `handler_compute_s` sample is captured when `compute_readiness` raises internally (caught, degrades to
  `unavailable`) — satisfies the iter-68 error-case requirement that the watchdog never suppresses a
  captured sample.
- **`apps/backend/tests/test_health.py` run as an ordinary step** (TC-4) — the module for
  `app/api/health.py`, disclosed-skipped in iter-67's Known Issues due to drill-contamination risk. Run
  this round, decoupled from both live drills (sequentially, not concurrently — same contamination-avoidance
  reasoning iter-67 used to defer it, just applied as "run before the drills" instead of "skip"): **17
  passed**, zero failures. Confirms the `handler_compute_s` wiring did not regress any existing
  `GET /api/health` contract (readiness, preflight, background_compute, symbol_count, etc. all unchanged).
- **The live-job drill (TC-1/TC-2)** — a real single-date backfill (`2018-01-05`, live-verified
  unsnapshotted before dispatch: no `scanner_runs` row, a real SPY close of $243.408) run with the watchdog
  armed, `scripts/qa/poll_health.py` polling at 1 Hz for the job's full 17m10.4s wall time
  (`job_id=b2bbcd8699fd4937afed351e4b0249c9`, `"source": null` in the final record — AG-9 clean, no live
  network call), joined against `logs/health-watchdog.jsonl` by UTC timestamp.
- **The idle-control drill (TC-3)** — same already-warm backend (no restart), same script, 330 polls
  (~5.5 minutes), no job running, launched immediately after the live-job drill's poller stopped.
- **`reports/perf-budgets.md` Addendum 34** (append-only; Addendum 33 and every earlier addendum
  untouched) — the `handler_compute_s` build, both drills' phase-by-phase UTC windows and three-component
  breach join, the TC-3 side-by-side distribution comparison, TC-4's result, and the two dated corrections:
  - **TC-5** (closes iter-67/a): Addendum 33's claim that the drill's whole-run max `loop_lag_s` (1.382s)
    was "recorded later during `factor_lab_all_warm`" is corrected — the sample's own raw JSONL timestamp
    (`2026-08-12T03:13:54.529811Z`) lands ~2m7s BEFORE `factor_lab_all_warm`'s own logged start
    (`03:16:01.520Z`) and coincides (within 77ms) with `logs/backend.log`'s own "membership-timeline cache
    warmed" line — the BOOT warm-up thread's cache-warm step, not the live job's finalize-tail phase.
    `factor_lab_all_warm`'s own actual max `loop_lag_s`, measured across its own 3,848 in-window samples, is
    0.240048s — nearly 6x below the misattributed figure. Addendum 33's own headline conclusions are
    unchanged; only the mislocated parenthetical was wrong.
  - **TC-6** (closes iter-67/b): Addendum 33's conclusion that the moving `>2.0s` breach location argues
    against a phase-specific hold is corrected, in the same paragraph, with the fact that the full `>1.0s`
    distribution (regrouped by phase from Addendum 33's own iter-67 CSV) still puts 120 of the drill's 131
    over-1.0s polls inside `factor_lab_all_warm` — 22.2% of that phase's own 541 polls, mean `elapsed_s`
    0.596s across the whole phase vs. 0.080s in the immediately-following `drawdown_expectations_warm`. The
    `>2.0s` crossing point moved (three different phases across three different rounds now); the
    phase-level elevation underneath it did not — independently re-confirmed this round in the
    `handler_compute_s` dimension too (0.484s mean in `factor_lab_all_warm` vs. 0.043s in
    `drawdown_expectations_warm`, this iteration's own fresh drill).
- **This iteration's breach again lands in `coverage_membership_timeline_refresh`, not
  `factor_lab_all_warm`** — a second consecutive round (matching iter-67, contrasting iter-61/63/65/66),
  disclosed honestly rather than forced to fit either pattern; see Addendum 34 TC-2/TC-6 for the fuller
  read (transient crossing point vs. stable underlying phase signal, both true together).

## Files Changed

- `apps/backend/app/engine/health_watchdog.py` — `HANDLER_COMPUTE_TYPE` constant + `record_handler_compute`
  function; module docstring updated (two sample types -> three).
- `apps/backend/app/api/health.py` — `t_handler_start`/`t_received_wall` kept for the whole function body;
  one new guarded block records `handler_compute_s` immediately before the `return {...}`; docstring
  updated.
- `apps/backend/tests/test_health_watchdog.py` — `_handler_compute_entries` helper; 3 new tests (disabled
  writes nothing, enabled records alongside `queue_wait_s` with the shared timestamp, two requests -> two
  samples); the existing error-case test extended to also assert a `handler_compute_s` sample.
- `reports/perf-budgets.md` — new `## Addendum 34` (append-only; every earlier addendum untouched): the
  instrument, TC-1/TC-2/TC-3 for this round's own two drills, TC-4's result, and the dated TC-5/TC-6
  corrections of Addendum 33.
- `runs/goal-ops-hardening-iter-68/evidence-drill/` — every raw artifact behind the numbers above:
  `tc1-job-create.json`/`tc1-job-final.json`/`tc1-job-dispatch-time.txt`,
  `tc1-health-poll.csv`/`.meta.json`, `tc3-idle-poll.csv`/`.meta.json`, `health-watchdog-slice.jsonl` (this
  run's own watchdog-log slice covering both drills), `backend-log-slice.log` (this run's own
  `logs/backend.log` slice), `poll_health_tc1.log`/`poll_health_tc3.log`.
- `runs/goal-ops-hardening-iter-68/test_health.log` — the full `test_health.py` run's own log (17
  passed).
- `docs/handoffs/goal-ops-hardening-iter-68-dev.md` — this file.
- `runs/goal-ops-hardening-iter-68/status.json` — `current_step: dev_complete`.

**No change to `compute_factor_lab_all_warm`, `coverage_membership_timeline_refresh`, or any file under
`apps/frontend/*`** — confirmed via `git status --porcelain` before writing this handoff (only
`apps/backend/app/api/health.py`, `apps/backend/app/engine/health_watchdog.py`,
`apps/backend/tests/test_health_watchdog.py`, and `reports/perf-budgets.md` are modified), matching the
spec's "diagnostic only, no bound this round" and "Frontend Present: no" scope. One unrelated file,
`runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl`, gained 2 append-only lines — this is
`config.readiness.verdict_history_path`'s pre-existing DEFAULT path (a legacy name predating this session's
rename to `ops-hardening`, unrelated to `health_watchdog`), and any real live backend launch that crosses a
preflight verdict transition appends to it; not touched by this iteration's own diff/scope.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_health_watchdog.py -v -p no:randomly`
Result: **11 passed** in 122.09s (8 iter-67 tests + 3 new iter-68 tests, all green).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_health.py -v -p no:randomly`
Result: **17 passed** in 3842.23s (1:04:02) — TC-4. Uses the session-scoped `loaded_engine` fixture
(bootstraps + backfills the full 30-year cadence; ~1h on this host, matching the documented cost). Run
sequentially BEFORE the two live drills below (not concurrently, not piggybacked) to avoid the exact
contamination risk iter-67 named for running it near a drill (an unrelated CPU-heavy pytest process biasing
`queue_wait_s`/`loop_lag_s`/`handler_compute_s` for reasons unrelated to the job under test) — resolved this
round by running it as its own clean, decoupled step rather than deferring it again.

Note on scope: the full whole-repo test suite was NOT run (per this session's own established convention —
`.claude/core.md`'s "Pump: don't run the full suite" discipline and the ~10-11h wall time the 30-year basis
gives the full pytest suite). Confidence in the rest of the diff rests on: (a) the two targeted files run
above, both fully green; (b) `apps/backend/main.py` was NOT touched this iteration (the `handler_compute_s`
wiring lives entirely inside `health_watchdog.py`/`health.py`, no new middleware, no new lifespan hook); (c)
the flag-unset byte-identity re-verified live twice via `scripts/dev.sh` (below).

Service startup (pre-handoff checklist): ran `scripts/dev.sh` twice back-to-back on its default project
ports (8255/3255), flag UNSET (the default path) — both backend (`GET /api/health` -> 200) and frontend
(`GET /` -> 200) started cleanly each time; `logs/health-watchdog.jsonl`'s line count was IDENTICAL
(29,606) before the first launch, after several `/api/health` hits on the first launch, and after the
second launch — confirms the middleware genuinely never activates on the default path (0 lines written
across both runs). First shutdown was fully clean this round (`kill -TERM` on the `dev.sh` PID reaped both
the backend and the frontend's `next-server` grandchild with nothing left on either port) — the second
shutdown left one `next-server` grandchild PID briefly holding port 3255 after the parent `next dev`
process exited (repeating iter-66/iter-67's own documented lesson that `dev.sh`'s `trap` does not always
reach that grandchild); killed directly (`kill -9` on the `next-server` PID resolved from `ss -tlnp`) and
confirmed both ports clear before finishing. Separately, the WATCHDOG-armed backend (launched via
`scripts/start-backend.sh` with `TRENDORA_HEALTH_WATCHDOG=1` for the two live drills) shut down cleanly on
`kill -TERM` with no tracebacks/`CancelledError` noise in `logs/backend.log` — the loop-lag probe task and
the new `handler_compute_s` code path both complete cleanly at lifespan shutdown.

External integration: the live-job drill's `POST /api/data/jobs` backfill ran against the real committed
seed (`"source": null` in the persisted job record — AG-9 clean, no live network call), producing a real
snapshot + 2,145 forward returns and all 9 `aggregates_refreshed` categories — this IS the
live-external-integration check for this iteration (the same ingest finalize path prior addenda's TC-1
drills exercise).

## Known Issues

- **~19.6% (0.497s) of this round's one breach remains unattributed even after all three samples.** The
  three named components (`queue_wait_s`, `loop_lag_s`, `handler_compute_s`) sum to ~80.4% of the breach's
  2.543s total. The likely remaining sources — TCP connection accept/handshake before `t_received`,
  `CORSMiddleware` (registered ahead of `HealthWatchdogMiddleware` in `main.create_app`), and
  `scripts/qa/poll_health.py`'s own client-side `urllib` overhead — are named but not measured this round.
  A fourth instrument closing that remainder is explicitly out of this iteration's scope (one risky change
  only, per the spec's own rule 5) and not attempted here.
- **This round's breach again lands in `coverage_membership_timeline_refresh`, not `factor_lab_all_warm`**
  — a second consecutive round (iter-67, iter-68), with `factor_lab_all_warm` itself showing ZERO `>2.0s`
  breaches across its own full window both times, even though its `>1.0s` sub-ceiling elevation (now
  confirmed in three separate components: `elapsed_s`, and this round newly also `handler_compute_s`)
  stayed concentrated there. Whether two consecutive rounds is enough to call the `>2.0s` crossing point
  itself "moved away from `factor_lab_all_warm` for good" or still just transient/moment-to-moment host
  contention is the evaluator's call, not this dev pass's.
- **The J-05 walkthrough capture remains unrecorded** (10th round now) — rides along only if a
  showcase/demo lane happens to run this iteration; not this iteration's own goal, per OUT OF SCOPE.
- **The three long-parked OWNER items (2-second-ceiling policy, `browser-qa-phase.sh` ordering fix, the
  replay-lane cost sanction) remain untouched**, per this iteration's own OUT OF SCOPE — this round's live
  drill piggybacked on the SAME mandatory live ingest the session already runs every round (a single new
  single-date backfill, `2018-01-05`, distinct from every prior round's date so it was genuinely
  unsnapshotted), and the idle-control drill ran no job at all.
- **`runs/goal-session-mcp-loop/state/preflight-verdict-history.jsonl` gained 2 lines** as a side effect of
  running the real backend live twice (see "Files Changed" above) — pre-existing default-path behavior,
  unrelated to this iteration's own diff/scope; left as-is (a config.yaml path rename is out of scope here).
