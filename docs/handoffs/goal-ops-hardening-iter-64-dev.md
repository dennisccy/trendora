# goal-ops-hardening-iter-64 Dev Handoff

**Phase:** goal-ops-hardening-iter-64
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete — every IN SCOPE item implemented and self-verified where the spec allows it
this dispatch; two items are explicitly deferred to a later stage per the spec's own scoping (see
"Known Issues").

## What Was Built

- **Run-time sentinel-date resolver** (`demo_runner.py`, token `{{AUTO_UNSNAPSHOTTED_DATE}}`):
  `resolve_sentinel_date()` runs a read-only sqlite query against `apps/backend/data/trendora.db` for
  the earliest trading day in a bounded window that BOTH carries a SPY bar (the benchmark every
  `scanner_runs` row is computed against) AND carries zero `scanner_runs` rows — i.e. eligible for a
  single-date backfill. `script_needs_sentinel()` / `substitute_sentinel_in_script()` /
  `resolve_and_substitute_sentinel()` detect the token anywhere in a script's JSON and substitute the
  SAME resolved date into every occurrence (fill text, expect text, click-target text, the script's own
  `name`) in one pass, recursively, never by enumerating specific field names. Wired into `run_verify`
  (per-journey, right after a golden loads/validates) and into `main()` ahead of `run_record`/`run_live`.
  A resolution failure (missing db, window exhausted) raises `RuntimeError` explicitly — `run_verify`
  turns that into a `FAIL` verdict for the affected journey; `main()` prints the error and exits 2 for
  record/live — never a silent SKIP or a reused/consumed date.
  - **Bug found and fixed mid-implementation**: the first window I chose (1996-01-01..2004-12-31,
    picked because it is barely touched by `scanner_runs`) predates SPY's own earliest bar in this
    committed seed (`2005-02-25` — a real, if unusual, property of the seed: 1996-2004 has OTHER
    symbols' bars but zero SPY bars). An unfiltered "any daily_prices row" query would have resolved
    dates a real backfill could never use as `scanner_runs.benchmark`. Caught by manually resolving
    against the live DB before wiring the drill (`1996-01-02` came back with `daily_prices` rows but
    zero for `symbol='SPY'`), fixed by filtering the query on `symbol = 'SPY'` explicitly and moving the
    window to `2005-03-01..2016-12-31` (2,195 SPY-bearing, unsnapshotted trading days measured
    2026-08-11 — years of headroom at the historical ~1-consumed-date/iteration rate). A dedicated
    regression test (`_t_resolve_sentinel_date_requires_benchmark_bar`) locks this in with a fixture
    that reproduces the exact shape (a date with some symbol's bar but no SPY bar).
- **`run_record` mutation guard**: extracted the per-step execution loop into `_record_steps(page,
  steps, base_url, default_tmo, out_dir, repo_root)` so it can be self-tested against a fake `page`
  without a real browser. Once any step's `_do_action` raises, no LATER step in the same script whose
  action is a `click` on a `role: button` target is performed — it still gets its screenshot and a
  distinct soft note naming the skip reason. A control-case test proves a click with no preceding
  failure still fires normally (the guard doesn't over-trigger).
- **`J-05.json`**: steps 2/3/13/14 and the `name` field no longer carry the hand-picked `2010-11-22` —
  every one now carries `{{AUTO_UNSNAPSHOTTED_DATE}}`. Appended one closing `_notes` entry (existing
  rotation history, iter-50 through iter-63-audit, left completely untouched) documenting the switch and
  why it closes the four-consecutive-round hand-rotation defect. Lint (`--mode lint`) reports `J-05 ok`.
- **`CHAIN_BACKEND_READY_WAIT_S` raised 60 → 90** at both sites: `common.sh:1434` (the function's own
  internal fallback default) and `replay-lane.sh:341` (the explicit call site's own `:-60` default).
  `grep -n "CHAIN_BACKEND_READY_WAIT_S:-" scripts/automation/lib/*.sh` now shows `90` at both. Per the
  spec and the iter-60 lesson, this canNOT take effect in the same run that edits it (both files are
  `source`d once at `goal-iter-lean.sh` startup) — **explicitly NOT closed this iteration**; iteration
  65 must confirm the new value fired live from its own engine log.
- **`test_missing_data_diagnostic_cooperative_yield_byte_identical` docstring corrected**: it previously
  claimed the byte-identical assertion was "Proven against a PINNED pre-fix reference oracle." That is
  true only of the row-count sanity check (11 rows, a plain yield-free `session.exec` reproducing the
  fixture's known shape) — the byte-identical assertion itself compares two POST-fix calls (tiny vs.
  default `read_batch_size`, both with the cooperative yield present; there is no pre-fix code path left
  to call, since the yield is unconditional). No assertion or logic changed — same 3 assertions, same
  fixture, same expected `sleep_calls == [0] * 5`. Re-ran the test standalone: PASSED.
- **Opt-in fault-injection drill executed** (unrun for 4 consecutive rounds):
  `TRENDORA_RUN_HEAVY_INGEST_TEST=1 pytest apps/backend/tests/test_start_backend_script.py::test_factor_lab_all_survives_repeated_memory_pressure_live -x`
  — **1 passed in 764.23s (0:12:44)**. Its own dedicated backend (`scripts/start-backend.sh`, isolated
  port 19200+offset, fault-injected `TRENDORA_FAULT_INJECT_MEMORY_ERROR=factor_lab_all`) never touched
  the shared dev DB or the shared `logs/backend.log`: that file's MemoryError count (excluding lines
  tagged `injected at fault-injection site`) was **7,127 before and 7,127 after** — confirmed by direct
  `grep -c` before dispatch and again after completion.
- **TC-1 attribution drill**: piggybacked the required 1 Hz `GET /api/health` poll onto this iteration's
  own live single-date backfill (the same ingest shape J-05/the sentinel mechanism exercises —
  `2005-06-24`, live-verified 0 `scanner_runs` rows + a real SPY bar immediately before dispatch; no
  separate/duplicate heavy job). Launched only via `scripts/dev.sh` on its deterministic project ports
  (8255/3255) — AG-10 caps confirmed live on the spawned uvicorn worker (`Max address space =
  8589934592` bytes = 8192 MB, `taskset` affinity `0-15`, `MALLOC_ARENA_MAX=2`, `OMP_NUM_THREADS=8`,
  matching the committed `config.yaml`/`host-guard.env` values, both left untouched). Poll log
  reconciled against the job's own OPEN/CLOSED phase markers and `wc -l` via
  `runs/goal-ops-hardening-iter-59/evidence-drill/reconcile_drill.py` (reused verbatim, per the iter-57
  lesson). **Result recorded as `reports/perf-budgets.md` Addendum 30: the 1→53(-ish) latency-breach
  jump REPRODUCES (59 of 930 polls breached the ≤2.0s ceiling, 58 of them inside `factor_lab_all_warm`)
  — it does NOT revert toward iter-61's near-zero baseline.** No code change to `factor_lab_all_warm` /
  `data_manager.py` / `research.py` was attempted, per the spec's own scope boundary.

## Files Changed

- `incredible_auto_dev/scripts/automation/lib/demo_runner.py` (reachable identically as
  `scripts/automation/lib/demo_runner.py` — `scripts/` is a git-tracked symlink to
  `incredible_auto_dev/scripts/`, same physical file, confirmed via `readlink -f`; `git diff` against
  the `incredible_auto_dev/...` path is the one that shows this change) -- sentinel resolver +
  substitution + wiring into `run_verify`/`main()`; `run_record`'s mutation guard (`_record_steps`
  extraction); 12 new self-test cases (`_SELF_TEST_CHECKS` now 40 entries, was 28).
- `incredible_auto_dev/scripts/automation/lib/common.sh` (same symlink note) -- `_wait_for_backend_readiness`'s
  own internal default `CHAIN_BACKEND_READY_WAIT_S:-60` → `:-90` at line 1434.
- `incredible_auto_dev/scripts/automation/lib/replay-lane.sh` (same symlink note) -- the explicit call
  site's own `CHAIN_BACKEND_READY_WAIT_S:-60` → `:-90` at line 341.
- `runs/goal-session-ops-hardening/journey-scripts/J-05.json` -- steps 2/3/13/14 and `name` switched
  from the hardcoded `2010-11-22` to the `{{AUTO_UNSNAPSHOTTED_DATE}}` sentinel token; one closing
  `_notes` entry appended; prior rotation history (iter-50 through iter-63-audit) untouched.
- `apps/backend/tests/test_data_manager.py` -- docstring-only correction on
  `test_missing_data_diagnostic_cooperative_yield_byte_identical` (TC-8); no assertion/logic change.
- `reports/perf-budgets.md` -- new Addendum 30 (append-only), the TC-1 drill's honest attribution
  result (reproduces, does not revert to baseline).
- `runs/goal-ops-hardening-iter-64/evidence-drill/` -- live drill raw artifacts (`poll_health.py`,
  `tc5-health-poll.csv`, `dev.log`, `reconciliation.md`, `reconciliation_stdout.txt`), mirroring prior
  iterations' `evidence-drill/` directories.
- `docs/handoffs/goal-ops-hardening-iter-64-dev.md` -- this file.
- `runs/goal-ops-hardening-iter-64/status.json` -- `current_step: dev_complete`.

## Tests Run

Command: `python3 scripts/automation/lib/demo_runner.py self-test`
Result: **40 passed, 0 failed** (was 28 before this iteration; 12 new cases added — 10 for the sentinel
resolver/substitution, 2 for the `run_record` mutation guard).

Command: `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-ops-hardening/journey-scripts --journeys J-01,J-03,J-04,J-05,J-06,J-07,J-08,J-09`
Result: all 8 `<J-XX> ok` (J-05 included, now sentinel-token-only, no hardcoded date).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py::test_missing_data_diagnostic_cooperative_yield_byte_identical -v`
Result: 1 passed (docstring-only change verified not to have touched behavior).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py tests/test_start_backend_script.py -q` (TC-12; heavy/opt-in cases addressed separately per TC-7)
Result: **229 passed, 5 skipped, 0 failed** in 396.40s. (`test_data_manager.py` alone: 218 passed, 0
failed, unchanged from before this iteration's docstring-only edit.)

Command: `TRENDORA_RUN_HEAVY_INGEST_TEST=1 pytest apps/backend/tests/test_start_backend_script.py::test_factor_lab_all_survives_repeated_memory_pressure_live -x` (TC-7, opt-in, executed this round)
Result: **1 passed in 764.23s (0:12:44).** Shared `logs/backend.log` MemoryError count (excluding
`injected at fault-injection site` lines): 7,127 before, 7,127 after — confirmed unchanged.

Command: (TC-1 live drill) `curl -X POST http://localhost:8255/api/data/jobs -d '{"kind":"backfill","start":"2005-06-24","end":"2005-06-24"}'` + 1 Hz `GET /api/health` poll for the job's full duration, reconciled via `reconcile_drill.py`
Result: job `status: ok`, 1 snapshot created, 815 forward returns, all 9 `aggregates_refreshed`
categories, wall time 1,032.56s (18:49:46.155Z → 19:07:09.154Z). Health poll: 930 polls, 59 breaching
the ≤2.0s ceiling (58 answered >2.0s inside `factor_lab_all_warm` + 1 non-answer), p50 0.085s / p90
1.508s / p99 3.091s / max 5.006s (slowest ANSWERED 4.445s). Full detail in `reports/perf-budgets.md`
Addendum 30.

Service startup (pre-handoff checklist): ran `scripts/dev.sh` twice back-to-back on its default project
ports (8255/3255) — both backend (`GET /api/health` → `status: ok`) and frontend (`http 200`) started
cleanly with no errors in the log; the second launch correctly reaped the first run's leftover
`next dev`/node child processes on port 3255 (confirmed via `ps`/`lsof` before and after) before binding
fresh — no port conflict. Both instances torn down cleanly (`pkill`, verified via `ps` that no `8255`/
`3255` processes remain).

## Known Issues

- **`CHAIN_BACKEND_READY_WAIT_S`'s 90s value is NOT yet self-verified** (spec's own explicit scoping,
  iter-60 lesson): this iteration's own pipeline run sourced the OLD 60s value before this edit landed.
  Iteration 65 must confirm `backend readiness == ready` inside a window consistent with the new
  constant, from its own engine log, before this item is marked closed.
- **TC-2 (J-05's golden replaying PASS via the sentinel mechanism, end-to-end through a real browser)
  is NOT run by this dev dispatch** — the deterministic replay lane runs downstream of dev+review in
  the goal-iter-lean.sh pipeline (forked right after the developer step settles), so it was outside this
  dispatch's own turn. What IS verified here: the substitution mechanism resolves and rewrites the real
  `J-05.json` correctly against the live DB (`resolve_and_substitute_sentinel` run directly against
  `apps/backend/data/trendora.db`, producing a fully-substituted script with the token gone and the
  resolved date `2005-06-24` in every original location — verified before this iteration's own drill
  consumed that exact date, so the NEXT resolution will pick a different, still-eligible date
  automatically), the file lints clean, and the unit-level self-renewal proof (TC-3) passes. The live
  end-to-end proof rides on the pipeline's own downstream replay of this golden this iteration (per
  TC-2) and, per the spec's own OUT OF SCOPE note, a second live proof-of-self-renewal replay was
  deliberately not run this round (TC-3 substitutes for it at the unit level).
- **TC-5 (showcase/demo lane never clicks a mutating control after a failed precondition, checked live
  against `data_provider_runs` for this iteration's own demo-lane wall-clock window) and TC-9 (a fresh
  J-05 showcase capture clearing the `evidence_makeup` flag) are showcase-lane checks that run in the
  demo-narrator/demo_runner `--mode record` stage downstream of this dispatch** — not exercised here.
  What IS verified here: the mutation-guard mechanism itself, at the unit level, against a fake page
  with a call-count spy (`_t_run_record_never_clicks_after_failed_precondition`), plus a control case
  proving it doesn't over-trigger when nothing failed.
- **The 1→53(-ish) `factor_lab_all_warm` latency-breach jump remains unattributed as to ROOT CAUSE** —
  this iteration confirms it is real and reproducible (two independent measurements, iter-63 and
  iter-64, both far above iter-61's baseline and within 11% of each other), per its own explicit scope
  boundary ("attribution only, no code fix attempted"). A future iteration wanting to close it should
  profile `factor_lab_all_warm` specifically (not `coverage_membership_timeline_refresh`, already
  reduced and tracked separately) under the same live concurrent-load conditions this drill used.
- **The sentinel window (`2005-03-01`..`2016-12-31`) was corrected mid-implementation** (see "What Was
  Built" above) after live-testing against the real DB surfaced that the originally-chosen window
  (1996-2004) predates SPY's own first bar in this seed. The corrected window and the SPY-presence
  filter are both covered by unit tests; no further gap is known, but this is worth a second pair of
  eyes given it was a genuine bug caught only by testing against the live data rather than by code
  review alone.
