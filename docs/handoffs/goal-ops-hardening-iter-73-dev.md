# goal-ops-hardening-iter-73 Dev Handoff

**Phase:** goal-ops-hardening-iter-73
**Date:** 2026-08-13
**Agent:** developer
**Status:** complete (measurement PARTIAL — see Known Issues; honest per the spec's own escape hatch)

## What Was Built

This is a measurement-only lean iteration (`Frontend Present: no`) — the goal was to re-measure J-07 step
3's real peak memory (VmPeak) under iter-72's resized 68-connection DB pool at realistic concurrency, and
either confirm the margin is comfortable or tune `pragmas.cache_size`/`pool_size`/`max_overflow` if thin.

1. **New live-drill instrument** (`apps/backend/tests/test_start_backend_script.py`):
   `test_start_backend_forward_aggregate_warm_under_realistic_pool_pressure` — reuses the existing
   `_MemSampler` (`/proc/<pid>/status` VmPeak, the same instrument iter-32/iter-38 used) and `_HealthPoller`
   (extended with a new `interval` constructor param, default 2.0 unchanged for every existing caller; this
   test passes `interval=1.0` to match TC-4's committed 1 Hz cadence) around the SAME live `rebuild` job the
   sibling `test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap` test already drives,
   adding `_POOL_PRESSURE_WORKERS` concurrent threads (`_pool_pressure_worker`) issuing real read requests
   across 6 DB-backed endpoints (`/api/backtest`, `/api/watchlist`, `/api/sectors`, `/api/themes`,
   `/api/stocks`, `/api/data/availability`) throughout — real, realistic concurrent DB-pool pressure, not a
   second measurement instrument.
2. **A calibration study** (`runs/goal-session-ops-hardening/iter-73/pool-pressure-calibration.md`) that
   determined the worker count actually driven by the test, empirically, on this host.
3. **`reports/perf-budgets.md` Addendum 38** — the full write-up: context, what the drill found (both the
   confound and a completed pressure-free arm), the no-config-change decision and why, and the honestly
   re-recorded J-07 step 3 status.
4. **No production code changed.** `config.yaml` is byte-unchanged — see Known Issues for why.

## What The Live Drill Actually Found (read this before assuming "just re-run it")

Three independent, full-length, real live attempts on this host (worker counts 10, then 8, then 5 — each
with the SAME real `rebuild` job running concurrently) **all** reproduced a sustained
`logs/backend.log` "Exceeded concurrency limit" 503 streak — including to `GET /api/health` itself —
before completing. This is the SAME already-disclosed, out-of-scope uvicorn admission-control finding
`reports/perf-budgets.md` Addendum 37 recorded, but triggered here at a much lower worker count than
iter-72's own drill needed. `uptime` confirmed this host's ambient load swung between 0.51 and 4.74
(1-minute load average) across the session — multiple OTHER concurrent Claude Code sessions plus several
Chrome renderer processes were confirmed running throughout via `ps aux`. A 90-second-window calibration
study found a clean 10-worker boundary in isolation, but none of the three FULL-LENGTH attempts against
the real multi-minute rebuild job completed cleanly on this occasion — the ambient contention is real and
variable, not a design flaw in the worker-count choice alone.

A fourth, pressure-free attempt (same job, only the 1 Hz health poller) ran clean for its own 26-minute
window (1,063/1,063 health polls HTTP 200, VmPeak 2,390,872 kB, 71.5% margin) but did not itself reach the
job's finalize tail (the historically memory-heaviest phase) before hitting its own 1,800s bound — today's
committed dev DB has grown to ~8.4 GB (vs. the 811 MB "ground truth" figure recorded in `docs/goal.md` for
2026-07-18), and the `rebuild` job kind runs the FULL 2005-02-25 → 2026-08-03 range unconditionally
(confirmed via the job's own persisted `start`/`end` fields, regardless of the `2024-01-01`/`2024-01-01`
request parameters) — dramatically slower than the historical ~16-34 min figures on record for this exact
call.

Full write-up, the calibration table, and the honest historical-figure comparison are in
`reports/perf-budgets.md` Addendum 38.

## Files Changed

- `apps/backend/tests/test_start_backend_script.py` — new
  `test_start_backend_forward_aggregate_warm_under_realistic_pool_pressure` (marked
  `xfail(strict=False)`, full live-result write-up in its own docstring/decorator reason), new
  `_pool_pressure_worker` + `_poll_job_to_terminal_resilient` helpers, `_HealthPoller.__init__` gained an
  `interval` param (default unchanged), module docstring updated.
- `reports/perf-budgets.md` — new Addendum 38.
- `runs/goal-session-ops-hardening/iter-73/pool-pressure-calibration.md` — new, the calibration data
  backing the worker-count choice cited from the test's own comments.
- `docs/handoffs/goal-ops-hardening-iter-73-dev.md` — this handoff.
- `runs/goal-ops-hardening-iter-73/status.json` — new.

`config.yaml` is byte-unchanged (confirmed via `git diff HEAD -- config.yaml` — empty). No other backend
source file was touched.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_start_backend_script.py -q -k "not
heavy_ingest and not pool_pressure and not gap_insert and not factor_lab"`
Result: **12 passed, 1 skipped** (unaffected sibling tests in this module; the `_HealthPoller.interval`
addition is backward-compatible — every existing call site is unchanged and still uses the default 2.0s
cadence).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_config.py -q`
Result: **75 passed** (the pool-invariant tests — `test_real_config_db_pool_covers_server_concurrency`,
`test_db_pool_below_server_concurrency_raises`, `test_db_pool_exactly_covering_server_concurrency_is_valid`,
`test_minimal_config_defaults_satisfy_pool_invariant` — all still pass; `config.yaml` is unchanged so this
is an unaffected-regression check, not new coverage).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_start_backend_script.py --collect-only
-q`
Result: **18 tests collected** (no collection errors from the new test/decorator).

The new `test_start_backend_forward_aggregate_warm_under_realistic_pool_pressure` itself is opt-in
(`TRENDORA_RUN_HEAVY_INGEST_TEST=1`-gated, like its siblings) and marked `xfail(strict=False)` — it was
run live four times this session (see "What The Live Drill Actually Found" above); none of the three
pressure-added attempts reached a passing assertion state on this host during this session, so it is
expected to `xfail` if re-run under similar ambient conditions, and will `XPASS` (never error the suite)
the moment a quieter host / a completed run proves it clean end to end.

## Pre-Handoff Verification

- **Service startup**: verified repeatedly via the live drills themselves — `scripts/start-backend.sh`
  booted cleanly on every one of the 4+ live attempts this session, applied the declared `memory_cap_mb`/
  `malloc_arena_max` caps (confirmed via the boot header in `logs/backend.log` each time), and served
  `/api/health` within budget on cold start every time.
- **External integrations**: N/A — no new adapters/scrapers/live network calls; every drill's job carried
  `"source": null` (offline, committed-seed-only, AG-9).
- **Native dependency binaries**: N/A — no new dependencies.
- **Server cleanup**: all spawned backend processes across every attempt (including the two that had to be
  killed after the pytest driver process either crashed or was manually terminated) were verified stopped;
  `lsof`/`ps aux` confirmed no stray `uvicorn`/`start-backend.sh` process remained after this session's own
  work. See Known Issues for a process-hygiene incident during one attempt.

## Known Issues

- **TC-1's primary ask — a complete, clean VmPeak measurement under realistic pool pressure — was NOT
  obtained this round.** Three independent live attempts (10, 8, 5 pressure workers) all collided with the
  separately-disclosed uvicorn admission-control 503 finding before completing, correlated with this host's
  own fluctuating ambient multi-session load (confirmed via `uptime`/`ps aux`, not assumed). Per the
  iteration spec's own NOTES ("if the concurrency-generating load itself cannot cleanly reach a realistic
  fraction of the ceiling without confounding results... record that honestly... rather than forcing a
  number"), this is disclosed rather than papered over with a forced or estimated final figure presented as
  measured fact.
- **No config.yaml change was made.** Neither TC-2 ("margin ≥20%, no change") nor TC-3 ("margin <20%, lower
  cache_size/pool_size/max_overflow") can be honestly invoked without a completed measurement. A rough,
  explicitly-labeled ESTIMATE (applying iter-38's own historical finalize-tail delta, ~229 MB, to this
  round's fresh 2,390,872 kB scan-phase reading) suggests a comfortable ~67-68% estimated margin — but this
  is disclosed as an estimate, never as this round's own proven measurement, and is not the basis for any
  config change.
- **J-07 step 3 stays `partial`**, now anchored to this round's fresh (if incomplete) real evidence instead
  of iter-32/iter-38's stale, smaller-basis durability claim — matching the spec's own DoD escape hatch
  ("never silently re-carried as before"). Named remaining action for the next round (three options,
  detailed in Addendum 38): (a) re-run on a quieter host window with a materially longer time budget (the
  DB basis has grown ~10x since the last completed full-warm measurement); (b) instrument the finalize-tail
  phases with structured phase timers to get phase-level VmPeak deltas without one uninterrupted end-to-end
  run; or (c) accept the isolated (no-pressure) figure as the interim TC-1 record and treat the concurrency
  question as a separate problem requiring host isolation this sandboxed environment cannot currently
  guarantee.
- **Process-hygiene incident, disclosed:** during the second live attempt, an over-broad `pkill -f` cleanup
  command (aimed at a stalled pytest driver) also matched and killed that SAME drill's own still-legitimately
  -computing uvicorn backend process (18+ minutes / 48+ CPU-minutes of real rebuild work in progress) before
  it reached a terminal job status. No data corruption resulted (a throwaway DB copy, discarded either way)
  and no production system was affected, but the in-progress measurement for that specific attempt was lost
  and had to be re-attempted. Recorded so the pattern (verify an exact PID before any broad
  process-pattern kill, especially when a long-running real computation might be in flight) is not silently
  repeated by a future session.
- **A separate, out-of-scope finding, disclosed but not this round's job:** today's committed dev DB (~8.4
  GB) makes even the per-date SCANNING phase of a full `rebuild` job take well over 26 minutes without
  completing — dramatically slower than the historical ~16-34 min figures on record for the same call. This
  is real capacity drift as the deep basis grows, separate from the DB-pool/memory question this round
  targets; flagged for the owner/next round, not fixed here (out of this round's one risky action).
- **Required-still-passing journeys** (J-01, J-03, J-04, J-05, J-06, J-08, J-09) were not re-verified via
  browser/deterministic-replay by this developer pass — that is QA-lane work per the pipeline's own
  division of labor, and this iteration made no production-code change that could plausibly regress them
  (the only diffs are one new opt-in test and one report addendum).
