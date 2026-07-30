# goal-ops-hardening-iter-34 Dev Handoff

**Phase:** goal-ops-hardening-iter-34
**Date:** 2026-07-30
**Agent:** developer
**Status:** complete

## What Was Built

This iteration closes J-07's two remaining unexecuted acceptance steps (step 2: health-poll latency
during the step-1 warm; step 4: the induced-memory-pressure abort drill, deferred since iter-14). No
production code was changed — both deliverables are real, live measurements plus one new permanent
regression test. `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, and
`ensure_historical_forward_aggregates_dispatched` are byte-frozen (confirmed by `git diff` showing zero
change to any file under `apps/backend/app/`).

### J-07 step 2 — `GET /api/health` latency during the live full-deep-basis warm
- Booted the real backend (`scripts/start-backend.sh`, real committed-seed DB, prod caps) and reproduced
  iter-32's exact warm-trigger scenario (`GET /api/backtest?as_of=2026-07-16`, an uncached historical date
  under the current `dataset_version`, which dispatches the SAME background 5-horizon forward-aggregate
  warm).
- Extended the existing 1 Hz `/api/health` poll (a real `curl -w %{time_total}` client-side measurement,
  not a server-side timer) to record LATENCY, not just HTTP status, across 85 polls spanning boot-tail +
  the full 82.21 s warm + post-warm serving.
- Result: 85/85 HTTP 200, min 0.107 s / median 0.134 s / max 1.132 s — an honest **WARN** against the
  `<=0.1 s` budget (every poll, including 8 pre-warm baseline polls, exceeded it). Root-caused live to
  host-level CPU contention from the co-resident `tapeology` project's uvicorn process, which
  `host-guard.env`'s own 2026-07-29 changelog records moved onto trendora's SAME `HOST_GUARD_CPU_LIST`
  mask after reset #6 — confirmed via `ps`/`uptime` at measurement time (tapeology ~115% CPU,
  `load average: 2.12, 2.70, 2.66`). The budget line itself was NOT amended (binding "Do not redo").
  Full write-up: `reports/perf-budgets.md`, "Iteration 34 — J-07 step 2" section.

### J-07 step 4 — induced-memory-pressure drill
- Built a throwaway, synthetic SQLite DB (`runs/goal-ops-hardening-iter-34/mem-drill/seed_throwaway_db.py`)
  sized so `_refresh_ingest_aggregates`'s forward-aggregate per-horizon loop specifically needs more
  virtual memory than a tightened, still-safely-bootable `server.memory_cap_mb` allows — the real deep-basis
  DB cannot reproduce this (iter-32 measured ZERO `VmPeak` growth from the warm at that scale; tightening
  the cap far enough to matter there fails BOOT itself, not the warm specifically).
- Launched the throwaway process ONLY via `scripts/start-backend.sh` (host-guard caps confirmed applied,
  `taskset -cp` -> `0-3,8-11`), with `TRENDORA_CONFIG` pointing at a scratch config (the project's existing
  sanctioned test-seam lever, `app/config.py:572`) with exactly two lines changed —`database.url` and
  `server.memory_cap_mb` — so `scripts/start-backend.sh` enforces the SAME tightened cap through its
  existing, unmodified `ulimit -v` logic. No script code changed.
- At `memory_cap_mb=970` (baseline ~898 MB, ~73 MB margin), the live drill produced a genuine,
  non-monkeypatched `MemoryError` caught by the EXACT iter-8 `except MemoryError` branch inside
  `_refresh_ingest_aggregates`'s `forward_aggregates` per-horizon loop (log line
  `"ingest forward-aggregate warm aborted at horizon 1 — memory pressure..."`) — the specific mechanism the
  binding iter-30 lesson requires, not a substituted easier-to-trigger failure mode. Verified live:
  - `GET /api/health` kept returning 200 immediately after and repeatedly thereafter, same PID, no restart.
  - `GET /api/backtest` (a pure read, `is_latest` branch, never triggers a compute) served the
    PRE-SEEDED, previously-cached evidence (`evidence_status:"refreshing"`, `evidence_asof` = the seeded
    run's date, `evidence_by_horizon` carrying all 5 horizons with the exact seeded values) — proving a
    previously-cached read survives the abort untouched.
  - `logs/backend.log` independently corroborates both the abort and the continued serving (per the
    iter-26/iter-28 lesson: verified from the log, not a narrative summary — saved verbatim at
    `runs/goal-ops-hardening-iter-34/mem-drill/pass6/drill-log-excerpt.txt`).
  - The throwaway process was cleanly terminated after evidence capture; port confirmed free.
  - Full write-up + the per-TC table: `reports/perf-budgets.md`, "Iteration 34 — J-07 step 4" section.
- **New permanent regression test** — `apps/backend/tests/test_ingest_finalize_memory_pressure.py`: a
  REAL (non-monkeypatched) `ulimit -v` subprocess induction against `_refresh_ingest_aggregates` directly
  (mirrors `test_forward_testing_concurrency.py`'s established TC-3 pattern), with a calibrated TIGHT cap
  that reproducibly aborts `forward_aggregates` cleanly (no crash) and a CONTROL test at a generous cap
  proving the SAME fixture completes normally — the DoD's explicit "control assertion... caught as a
  test-setup failure rather than silently passing" requirement. 2 passed, ~191 s (`.venv/bin/python -m
  pytest tests/test_ingest_finalize_memory_pressure.py -v`).

## Files Changed

- `reports/perf-budgets.md` -- two new dated sections: J-07 step 2 (health-poll latency during the warm)
  and J-07 step 4 (the induced-memory-pressure drill, full per-TC table).
- `apps/backend/tests/test_ingest_finalize_memory_pressure.py` -- new file: real subprocess induction +
  control test for `_refresh_ingest_aggregates`'s forward_aggregates MemoryError catch.
- `runs/goal-ops-hardening-iter-34/mem-drill/seed_throwaway_db.py` -- the throwaway-DB builder used for
  the live drill (kept as a reusable, documented artifact; the DB files themselves are gitignored/deleted).
- `runs/goal-ops-hardening-iter-34/mem-drill/seed-summary.json`, `pass6/drill-log-excerpt.txt` -- evidence
  artifacts cited by the perf-budgets.md write-up.
- `runs/goal-ops-hardening-iter-34/health-latency/poll_health.sh`, `health-latency.csv` -- the 1 Hz
  latency-poll script and its raw captured data, cited by the perf-budgets.md write-up.
- No `apps/backend/app/**` changes. No frontend changes (none anticipated per the iter spec; none made).
- No `runs/goal-session-ops-hardening/state/blueprint.md` edit needed — the iter-34 narrative-history
  paragraph and the "Page performance budgets" Data Contract row's additive sentence were already appended
  by the decomposer when this iteration was planned (confirmed present, unedited going forward per this
  file's append-only-narrative-history convention — prior iterations' own paragraphs, e.g. iter-30's, are
  never retroactively rewritten after being built either).

## Tests Run

### New dedicated test file
Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_ingest_finalize_memory_pressure.py -v`
Result: **2 passed** in 190.98s (`test_tight_cap_aborts_forward_aggregates_with_caught_memory_error_and_recovers`,
`test_control_generous_cap_completes_forward_aggregates_normally`).

### Byte-frozen confirmation (TC-7)
`git diff --stat -- apps/backend/app/engine/forward_testing.py apps/backend/app/engine/data_manager.py`
and `git status --short apps/backend/app/` both show **zero diff** — structural proof no accidental scope
creep touched `compute_forward_aggregates` / `resolved_forward_aggregate_evidence` /
`ensure_historical_forward_aggregates_dispatched` or any other production file.

### Live functional evidence (in lieu of re-running the full pytest suite — see Known Issues)
Two independent real end-to-end backend-process passes this iteration (health-latency pass, PID 2140378;
memory-drill pass, PID 2072993) each independently exercised `_refresh_ingest_aggregates`,
`forward_aggregates_ingest_cached`, `compute_forward_aggregates`, and `resolved_forward_aggregate_evidence`
multiple times, live, against real HTTP requests, with correct results each time (documented in full in
`reports/perf-budgets.md`).

## Known Issues

- **The broader `test_forward_testing*.py` regression suite was NOT re-run this turn.** Two attempts
  (the full `test_forward_testing.py` + 3 sibling files, then a `-k finalize_hook` subset of
  `test_data_manager.py`) both exceeded a ~10-minute turn-time budget without completing, consistent with
  this project's own documented lesson ("30y test suite slow, not the product" — some fixtures in this
  suite are real-committed-seed-scale and legitimately take a long time on this host). Given (a) `git diff`
  structurally proves zero production code was touched this iteration, (b) this iteration's own new test
  file passes cleanly, and (c) two independent live drills exercised the exact same functions successfully
  multiple times, I judged re-running the full suite an unjustified use of turn time rather than a gap in
  correctness — but the reviewer/QA stage should still run it if a fuller CI-style guarantee is wanted.
- **The throwaway drill's `GET /api/backtest` "latest" run resolved to a boot-warmup-created date
  (`2025-04-04`), not the drill's own seeded R2 (`2020-01-03`).** This throwaway DB's own boot warm-up
  (`warmup.status:"ok", "history 4/4"`) independently created 4 additional cadence-anchor `ScannerRun` rows
  — an honest, unplanned-but-harmless artifact of launching through the real boot path rather than a
  bespoke harness. It does not change any TC's outcome (documented in full in perf-budgets.md's TC-4 row);
  flagging it here so a future drill on this same throwaway-process pattern isn't surprised by it.
- **The `/api/health` `<=0.1 s` budget WARN this iteration measured is now partly attributable to a NEW,
  cross-project contention source** (the co-resident `tapeology` project sharing trendora's host-guard CPU
  mask since 2026-07-29's reset-#6 fix) rather than only same-project browser/ingest load as previously
  documented. This is disclosed honestly in perf-budgets.md; no action taken (out of this iteration's
  scope — the budget line is binding "never amended," and host-level cross-project scheduling is an
  owner/framework concern, not a product code path).
- No other gaps. J-07's four acceptance steps now all have first-hand, live evidence (steps 1/3 from
  iter-32, steps 2/4 from this iteration) — the evaluator's call on scoring the whole journey, per the
  iter spec's own NOTES ("this iteration deliberately does not attempt a GOAL_ACHIEVED verdict").
