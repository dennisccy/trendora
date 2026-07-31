# Iteration State — ops-hardening

**After iteration:** 39 · **Date:** 2026-07-31 · **Verdict:** ESCALATE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-08 J-09) · 1 partial (J-07, 5th straight) · 0 failing · 0 unknown — 8 total. All 8 re-verified with THIS-iteration evidence (J-04 finally got its real `kill -9`/restart). Ledger: 36 findings, **15 unresolved, 0 critical** (iter-38/s + iter-38/t RESOLVED; new iter-39/u /v /w /x).

## Active blockers

- **dev — THE J-07 BLOCKER, and it is ONE change (iter-39/v).** `_missing_data_diagnostic` (`apps/backend/app/engine/data_manager.py:271`) buffers ~3.3M `(symbol, date)` rows into one Python list before the loop body runs — traceback at `runs/goal-ops-hardening-iter-39/mem-drill/trial3-2650mb-wedge-evidence.txt:17-29` (`loading.py:220 chunks` → `result.py:580 _raw_all_rows`). Falsifies J-07's "no unbounded whole-table ORM materialization on the warm or serving path"; live on BOTH the ingest finalize path and `/api/data` compute (`:936`). FIX: bounded `yield_per` — output-identical, grouping loop unchanged. Also correct the comment at `:262-274` that claims "no unbounded whole-table scan" (true of the query's SCOPE, false of its MATERIALIZATION). Named independently by developer, reviewer AND auditor.
- **dev, iter-39/u — unretired process wedge.** At a 2650 MB throwaway cap the job persisted `status: ok`, then the SAME process stopped answering `/api/health` for 7+ min (curl `000`, zero new log lines, 14 threads in `futex_do_wait`, host 15 GiB free). Falsifies J-07's "never leaves the process wedged". Dying thread NEVER identified — the `backfill_workers` attribution was RETRACTED by dev and the retraction confirmed by the auditor. Likely downstream of the blocker above; re-test ONCE after it, throwaway DB, via `scripts/start-backend.sh`.
- **dev, iter-39/w (AG-3):** after `kill -9` the `/data` Run History row reads `dates_done 2/18` while the process had reached `18/18` in memory — a user sees ~11% of the work. Checkpoint per date, or relabel as "last saved checkpoint".
- **dev, small + written down:** correct `reports/perf-budgets.md:4996`'s RETRACTED wedge attribution in place; teach `merge_ui_test_results.parse_rows` a `BLOCKED` class so the merged HEADLINE cannot read PASS for an all-BLOCKED run (iter-39/x — machine gate already safe).
- **dev, deferred a 4th time (iter-33/g):** Regime Lab cold `view=pooled` needs the background dispatch `/api/backtest` got at iter-32.
- **dev, carried minor, untouched:** iter-29/b + `warmup.py:194` badge wording (9 iterations unmade); iter-31/e; iter-32/f (WATCH only); iter-35/k; iter-36/n; iter-37/o /q.
- **OWNER, settle BEFORE any achievement run:** iter-34/j — `/api/health` ≤ 0.1 s budget missed a **6th** time, **3 of 68** polls in budget (min/mean/max 0.0953/0.2267/1.2970 s) during step 2's own scenario; 4 evaluators have called it his. Ratify honest-WARN · rescope for the bounded compute window · commission the cached-snapshot fix. Also iter-33/i (`start-frontend.sh` → `HOST_GUARD_MARKER_FILES`) — note `host-guard.env` was re-parameterized by the OWNER this window (`1130a36b`, CPU mask `0-3,8-11`→`0-15`); launch SCRIPTS byte-identical, memory cap unchanged, AG-10 still passes.

## Last 2 verdicts

- iter 39: ESCALATE — J-07 step 4 finally PROVEN live at the named handler, but two of its acceptance clauses were falsified by this iteration's own honest drill. Audit #1 returned FAIL on defects review AND QA both passed (3rd iteration running) — keep the auditor.
- iter 38: ESCALATE — J-07 `partial` a 4th time; step 4 never ran (drill re-calibrated away from pressure); replay lane reported 6 false FAILs against a downed backend.

## Do not redo

- **J-07 steps 1, 2 (HTTP-200 half), 3, 4 are CLOSED** — `runs/goal-ops-hardening-iter-39/fault-drill/`: named per-horizon handler fired live (`logs/backend.log:148264`), isolation proven (`aggregates_refreshed` omits `forward_aggregates`, later categories completed), 68/68 health 200, 1,246/1,246 cached `/api/backtest` 200 with literal abort containment, PID unchanged, VmPeak 49.27% of cap. Do NOT re-run to re-prove. **Do NOT resume cap-tuning** — 3 probes was already the wrong-direction signal; the sanctioned test hook is the vehicle.
- **Replay lane repaired AND working:** `BLOCKED` class + `/api/health` probe in `demo_runner.py`, rc 7 routing in `replay-lane.sh`, `goal_gate.py:89,151` blocks achievement on any BLOCKED cell. 7/7 PASS live, seven distinct screenshot md5s (collision did not recur). Residual is the merged HEADLINE only.
- **J-04 live `kill -9`/restart (TC-8) and J-05 cold-boot coverage-from-storage (TC-9) are DONE** (`runs/goal-ops-hardening-iter-39/live-restart/`). Do not re-schedule.
- **Settled, do not re-open:** env-toggle truthy guard, root-logger config + duplicate-write filter, `read_pool()` in-situ measurement (16 calls, 2.85 ms mean), `_compute_one_isolated` worker-thread `MemoryError` isolation — all tested with negative controls, recorded in `reports/perf-budgets.md`.
- **Byte-frozen:** `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched`. **AG-10 launch scripts: zero diff, never weaken.**
- **Never make evidence capture an iteration's goal.** Ride-along only: J-07's `[NEW]` walkthrough (9 iterations unrecorded; demo lane SKIPPED again).
