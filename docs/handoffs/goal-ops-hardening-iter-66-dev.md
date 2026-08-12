# goal-ops-hardening-iter-66 Dev Handoff

**Phase:** goal-ops-hardening-iter-66
**Date:** 2026-08-12
**Agent:** developer
**Status:** complete — profiling investigation performed exactly as scoped (no product-code fix warranted
by the evidence, mirroring iter-65's own honest "no fix found" precedent); the QA/tooling item (canonical
`poll_health.py`) and both small carried items (iter-64/c, iter-64/d) shipped.

## What Was Built

This iteration's IN SCOPE list asked to (1) profile `coverage_membership_timeline_refresh`'s finalize-tail
phase to name the exact call site still holding the GIL/a lock past the 2.0s poll ceiling, (2) bound
whatever the profile names, (3) add a fixture-backed equality test for the bound, (4) preserve the existing
MemoryError-isolation handler, (5) investigate the iter-64/d duplicate-run-row pattern; and, as QA/tooling,
(6) canonicalize the per-iteration throwaway `poll_health.py` into `scripts/qa/poll_health.py` with a
host-load column, (7) correct `journey-scripts/J-05.json`'s mis-stated sentinel window (iter-64/c). Full
detail, tables, and the honesty framing are in `reports/perf-budgets.md` **Addendum 32** (new, append-only);
this section summarizes.

- **Profiling (items 1/2) — TWO independent passes, zero code change**: a solo in-process pass
  (`stall_profile_coverage.py`, 3 runs incl. one at a 5x finer 0.05s stall threshold) and a
  concurrent-with-the-real-`/api/health`-route pass (`stall_profile_coverage_concurrent.py`, 3 runs), both
  against the real committed DB inside a real `prefilled_bar_cache` context (the exact shared-cache shape a
  live ingest sets up). **Every run: 0 stalls > 0.30s (and > 0.05s), 0 health-route breaches > 2.0s** (worst
  single call 0.224s) across the entire `_compute_coverage_body` sub-chain (`_trading_days`,
  `_resolved_universe`/`resolve_with_reasons`, `_per_symbol_coverage`, `_missing_data_diagnostic`,
  `_universe_diagnostic`, `_coverage_diagnostic_absent`). iter-53's `resolve_with_reasons` bound and
  iter-63's `_missing_data_diagnostic` yield-bound both re-confirmed clean. **No call site was named to
  bound** — items 2/3 therefore have no deliverable this round, the same honest outcome iter-65's own Item Y
  reported for the sibling `factor_lab_all_warm` phase.
- **TC-1 acceptance drill (a real, full live ingest, through the canonical script)** — `POST
  /api/data/jobs` (`backfill`, `2019-02-06`, live-verified unsnapshotted with a real SPY close before
  dispatch), `scripts/qa/poll_health.py` (this iteration's own new canonical script) polling `GET
  /api/health` at 1 Hz for the job's full 19m21s wall time. **1,024 polls, 100% HTTP 200, 0 non-answers; 1
  breach (3.068s) landed inside `coverage_membership_timeline_refresh`'s own 15.65s logged window** — the
  SAME low-single-digit, round-to-round pattern this exact phase has shown since iter-61 (0-1 breach every
  round) despite two real, verified fixes already landed there (iter-53, iter-63). New this round: every
  breaching poll's `load_avg_1m` reading (1.5-2.28 on this 16-core host) is roughly double this host's
  typical near-idle baseline — the first DIRECT, positive host-load evidence for the "transient contention,
  not a code hold" theory prior addenda could only infer from absence of a code-level cause.
- **TC-3** — the existing MemoryError-distinct isolation handler (`data_manager.py` ~4339-4345) is
  byte-for-byte untouched; its existing test
  (`test_finalize_hook_coverage_membership_timeline_fault_injected_releases_memory_honestly`) passed as
  part of this iteration's full `test_data_manager.py` run (218 passed).
- **TC-4/TC-5 — canonical `scripts/qa/poll_health.py`**: promoted the per-iteration throwaway script into
  ONE checked-in file — single `urllib` client, one poll/second, no subprocess-per-poll spawn (closes the
  iter-65 Addendum 31 ~40x instrument-disagreement gap). CSV schema `timestamp, http_status, elapsed_s,
  breach_over_2s, load_avg_1m` (TC-4), every row populated including `load_avg_1m` (TC-5); `os.cpu_count()`
  (a per-run constant, not a per-poll observation) written once to a sibling `<csv>.meta.json`. This
  iteration's own dev drill (TC-1 above) is the first artifact to use it. Unit-tested (6 tests,
  `test_poll_health.py`). The J-07 browser-qa test case is asked to route its own next supplementary drill
  through this same script — the file is now checked in and discoverable for it; a dev pass cannot itself
  dispatch that agent's future run.
- **TC-6 — `journey-scripts/J-05.json`'s mis-stated sentinel window, corrected**: the note claimed
  `1996-01-01..2004-12-31`; the shipped constants (`demo_runner.py`'s `_SENTINEL_WINDOW_START`/`_END`) are
  `2005-03-01..2016-12-31` — a stray-draft-value documentation bug from the SAME commit that shipped the
  constants (confirmed via `git show` on that commit), not later drift. Corrected in place, with the
  correction itself dated and explained. Text-only; `demo_runner.py` is untouched (framework/automation
  tooling, out of this dev pass's own file scope).
- **TC-7 — the iter-64/d duplicate-run-row pattern: root-caused AND fixed (small, isolated)**. Root cause:
  a graceful 429 pause commits `ImportCheckpoint.status="resumable"` and `DataProviderRun.status="resumable"`
  in TWO SEPARATE commits; a process killed in the narrow window between them leaves a genuinely-resumable
  checkpoint paired with a run-history row still `running`, which the next boot's `sweep_orphaned_runs`
  (the ONLY writer of `interrupted`) honestly closes `interrupted`. `_run_job`'s `_has_open_run_record` gate
  then treated that row identically to a genuinely terminal one and always inserted a SECOND row on resume.
  Fix: a new `_reopen_interrupted_run_record(engine, job_id)` helper reclaims the SAME row (status back to
  `running`) when — and only when — its status is exactly `interrupted`; a genuinely terminal row
  (`ok`/`failed`/`partial`/`failed_backfill`-driven) is left untouched, preserving the documented "fresh
  Retry audit row, like J-38" behavior exactly as before.

## Files Changed

- `apps/backend/app/engine/data_manager.py` — new `_reopen_interrupted_run_record` helper + a 2-line gate
  change in `_run_job` (TC-7 fix). No other line touched — `_compute_coverage_body`'s own call chain and
  `universe_resolver.py` are completely unmodified (TC-2's own premise: nothing to bound, nothing to prove
  byte-identical).
- `apps/backend/tests/test_data_manager_jobs_pipeline.py` — two new tests:
  `test_reopen_interrupted_run_record_reuses_row_never_a_genuinely_terminal_one` (the helper in isolation)
  and `test_resume_of_a_row_left_running_by_a_kill_reopens_it_not_a_duplicate` (end to end: real 429 pause →
  forced race simulation → real boot sweep → real resume → exactly one row asserted).
- `scripts/qa/poll_health.py` (new; resolves through the `scripts` → `incredible_auto_dev/scripts` symlink,
  tracked at `incredible_auto_dev/scripts/qa/poll_health.py`) — the canonical health-poll drill script.
- `apps/backend/tests/test_poll_health.py` (new) — 6 unit tests for the canonical script (CSV schema,
  `load_avg_1m` population, breach flagging, connection-error handling, `run()`'s exact schema + meta.json,
  stop-file convention).
- `runs/goal-session-ops-hardening/journey-scripts/J-05.json` — TC-6's `_notes` text correction (no step
  behavior change).
- `reports/perf-budgets.md` — new `## Addendum 32` (append-only; every prior addendum/Item untouched) — the
  full profiling methodology, the TC-1 live-drill distribution and honest "no fix made" framing, TC-3/TC-4/
  TC-5/TC-6/TC-7 write-ups.
- `runs/goal-ops-hardening-iter-66/evidence-drill/` — every raw artifact behind the numbers above:
  `stall_profile_coverage.py`/`stall_summary_coverage.json` (solo profile), `stall_profile_coverage_
  concurrent.py`/`stall_profile_coverage_concurrent_summary.json` (concurrent profile), `tc1-job-create.
  json`, `tc1-health-poll.csv`/`.meta.json` (the canonical script's own TC-1 output), `dev.log` (this
  iteration's own `scripts/dev.sh`-launched backend's stdout/stderr — cited in place of `logs/backend.log`
  since `dev.sh` execs uvicorn with no file redirect of its own, unlike `start-backend.sh`; same content,
  different path, noted honestly in the addendum rather than silently conflated).
- `docs/handoffs/goal-ops-hardening-iter-66-dev.md` — this file.
- `runs/goal-ops-hardening-iter-66/status.json` — `current_step: dev_complete`.

**No change to `apps/backend/app/engine/research.py`, `universe_resolver.py`, `config.py`, or any file
under `apps/frontend/*`** — confirmed via `git status --porcelain` before writing this handoff (matches the
spec's own "Frontend Present: no" / "no `apps/frontend/*` file is touched this iteration").

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -q -p no:randomly`
Result: **218 passed** in 331.71s — includes
`test_finalize_hook_coverage_membership_timeline_fault_injected_releases_memory_honestly` (TC-3) unmodified
and still passing; every other pre-existing test in this file (the module my TC-7 fix touches) stays green.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager_jobs_pipeline.py -v -p no:randomly`
Result: **23 passed** in 619.15s — includes the two new TC-7 tests
(`test_reopen_interrupted_run_record_reuses_row_never_a_genuinely_terminal_one`,
`test_resume_of_a_row_left_running_by_a_kill_reopens_it_not_a_duplicate`) plus every pre-existing
resume/checkpoint/lifecycle/drift-stage test in this file, all unmodified and passing (no regression to the
"like J-38 Retry" fresh-audit-row behavior for a genuinely terminal job).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_universe_resolver.py tests/test_ingest_finalize_fault_injection.py tests/test_poll_health.py -q -p no:randomly`
Result: **37 passed** in 5.21s.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager_parallel.py tests/test_ingest_finalize_memory_pressure.py -q -p no:randomly`
Result: **8 passed, 1 failed** (`test_tight_cap_aborts_forward_aggregates_with_caught_memory_error_and_recovers`) —
investigated and confirmed a **pre-existing flake, unrelated to this iteration's diff** (see Known Issues).

Re-verified after a transport interruption mid-handoff (this dispatch): `test_poll_health.py` (6 passed,
0.03s) and the three most load-bearing job-pipeline tests by name (`test_boot_sweep_marks_orphaned_running_
as_interrupted`, `test_reopen_interrupted_run_record_reuses_row_never_a_genuinely_terminal_one`,
`test_resume_of_a_row_left_running_by_a_kill_reopens_it_not_a_duplicate`) — **3 passed** in 29.51s,
confirming the fix and its coverage survived the interruption unchanged.

The full 30-year backend suite was NOT run (this project's established convention — ~10-11h; targeted and
downstream-of-diff files only, per this iteration's own dispatch note).

Service startup (pre-handoff checklist): ran `scripts/dev.sh` twice back-to-back on its default project
ports (8255/3255) — both backend (`GET /api/health` → 200) and frontend (`GET /` → 200) started cleanly
each time. Note for future dev passes on this host: `dev.sh`'s own `trap` only signals its two direct
subshell PIDs, not the `next dev` grandchild process tree — after `kill -TERM` on the wrapper PID, the
`node .../next-server` process can survive and must be killed directly (`lsof -ti :3255 | xargs kill -9`)
before a second launch is verified port-clean. Both verification runs' processes were confirmed fully torn
down (`lsof -ti :8255`/`:3255` empty) before this handoff was written.

## Known Issues

- **No code fix was made for items 1/2/3 (the GIL-hold bound).** This is the section's most important
  entry, not a gap to bury: this iteration's own profiling — two independent techniques, one at 5x finer
  resolution than the session's binding 0.30s threshold, both against the real committed DB inside the
  real shared-cache condition a live ingest sets up — found ZERO discoverable stall anywhere in
  `coverage_membership_timeline_refresh`'s own compute chain. Reported honestly per the project's own
  convention (AG-1 / judgment-rubrics: "unknown is a first-class answer", never round toward "fixed")
  rather than inventing a speculative fourth bound with no evidence behind it. See `reports/perf-budgets.md`
  Addendum 32 for the full argument, including the NEW direct host-load evidence (this iteration's own
  `load_avg_1m` column) supporting the "transient contention, not a code hold" theory.
- **TC-1's target-journey acceptance number is still not literally met.** This round's drill found 1 breach
  (3.068s, the highest single-poll magnitude of the four rounds that have shown this pattern) inside
  `coverage_membership_timeline_refresh`'s own window. Whether J-07 should move off `partial` given four
  consecutive rounds of 0-1 breach on code now twice profiled clean, plus this round's new direct load
  evidence, is an evaluator judgment call this dev pass does not make for it (mirrors iter-65's own
  delegation).
- **The J-07 browser-qa test case has not yet been observed routing through the canonical script** — this
  dev pass ships the script and uses it for its own drill (the ask this dev pass can directly satisfy); the
  browser-qa agent's own next supplementary drill is a future pipeline stage's action, not something this
  dispatch can trigger itself.
- **`test_tight_cap_aborts_forward_aggregates_with_caught_memory_error_and_recovers`
  (`test_ingest_finalize_memory_pressure.py`) is flaky, confirmed pre-existing and unrelated to this
  iteration's diff.** Reproduced independently of my changes: it PASSED once with my changes stashed
  (clean tree), then alternated pass/fail/pass across three consecutive runs WITH my changes present,
  identical code each time. My diff never touches `forward_testing.py`, `research.py`, or the test's own
  `TIGHT_CAP_KB` calibration — the test's own failure message ("cap 750000 KB may be miscalibrated too
  tight") is an honest self-diagnosis; most likely this borderline-tight cap has become marginal as the
  committed DB has grown since it was last calibrated. Not fixed (out of this iteration's scope — a memory-
  cap recalibration would be an unrelated second risky change, against rule 5's one-risky-change
  discipline); disclosed here rather than silenced.
- **A test-run side effect briefly overwrote `runs/goal-session-ops-hardening/state/drift-report.json`**
  (the drift-stage tests in `test_data_manager_jobs_pipeline.py` do not fully redirect
  `TRENDORA_DRIFT_REPORT_PATH` in every path) — reverted via `git checkout` before this handoff; not a
  product-code defect and not shipped. Worth a future iteration's small fix if it recurs.
