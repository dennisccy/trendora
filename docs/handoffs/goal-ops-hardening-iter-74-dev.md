# goal-ops-hardening-iter-74 Dev Handoff

**Phase:** goal-ops-hardening-iter-74
**Date:** 2026-08-13
**Agent:** developer
**Status:** complete — J-07 step 3 CLOSED (complete, clean, comfortable-margin measurement obtained; the
binding TC-5 stop rule did NOT fire)

## What Was Built

This is a measurement-only lean iteration (`Frontend Present: no`) — the goal was to get J-07 step 3's real
peak-memory (VmPeak) margin by joining telemetry the codebase already produces (`_MemSampler` +
`_refresh_ingest_aggregates`'s existing per-phase timing log lines) into a phase-by-phase profile, since
iter-73's four full-length live-drill attempts all failed to produce a complete, realistic-pressure
reading (`reports/perf-budgets.md` Addendum 38).

1. **The join itself** (`apps/backend/tests/test_start_backend_script.py`): `_local_asctime_to_epoch`,
   `_parse_phase_timing_lines`, `_vmpeak_at`, `_join_phase_vmpeak` — combines `_MemSampler`'s
   `/proc/<pid>/status` samples with `_refresh_ingest_aggregates`'s existing `"J-05 finalize-tail phase
   timing"` / `"...sub-phase timing"` log lines (`data_manager.py`) into a per-phase VmPeak-at-completion
   profile, durable through an interrupted/timed-out drill (a phase whose log line was never written is
   simply absent from the result, never guessed).
2. **Four fast, deterministic unit tests** (no live server) proving the join is correct in isolation:
   round-trip timezone conversion (iter-66's lesson, proven not assumed — passes under BST or GMT), parsing
   (including the per-horizon `forward_aggregates_warm` sub-phase lines, in written order, ignoring other
   jobs' lines), the VmPeak-at-or-before lookup, and — the core property — durability through a partial
   (3-of-9-phase) log. All four were ALSO sanity-checked against a real, already-on-disk completed
   finalize-tail run in `logs/backend.log` (job `1273b81dcb9d4616bc4a260d80fbc89d`) before any new live
   drill was attempted; the recovered epoch matched that job's own DB-persisted UTC timestamp exactly.
3. **One live drill** (`test_start_backend_phase_by_phase_vmpeak_profile_under_pool_pressure`, opt-in
   `TRENDORA_RUN_HEAVY_INGEST_TEST=1`-gated, `xfail(strict=False)`): triggers the SAME finalize tail via a
   `backfill` of one genuinely unsnapshotted date instead of iter-73's `rebuild` (see "Method" below) under
   the SAME `_POOL_PRESSURE_WORKERS=5` realistic concurrent load. **Run live this session — see Results.**
4. **`reports/perf-budgets.md` Addendum 39** — full write-up: context, method rationale, the complete
   9-phase (+5-per-horizon) results table, the margin decision, health/process-hygiene evidence, and the
   J-07 step 3 status.
5. **Two disclosed documentation corrections** (both ordinary developer-correctable, per
   `runs/goal-session-ops-hardening/state/assumptions.md` iter-74 entry — journeys/anti-goals untouched):
   - Addendum 38's "72 tests ... all still pass" claim corrected in place to the true 18 collected / 12
     passed / 1 skipped (confirmed by a fresh `pytest --collect-only -q`).
   - `docs/goal.md`'s "Ground truth (measured 2026-07-18)" block: DB size corrected to the freshly measured
     7,978.3 MiB / 8,365,871,104 bytes (~8.37 GB), and the fact that `rebuild` runs the full committed
     2005-02-25 → 2026-08-03 range regardless of requested dates is now stated (cited to iter-73's
     Addendum 38 finding). **Restricted to exactly this named block** — no Must-have journey or Anti-goal
     text touched (verified via `git diff -- docs/goal.md`, below).
6. **No config.yaml change** — the measured margin (42.3%) is comfortably above the 20% threshold, so per
   TC-4 the file is left byte-unchanged (confirmed via `git diff` — empty).

## Results — the live drill (run 2026-08-13, this session)

**Method:** all four of Addendum 38's attempts used `rebuild`, whose per-date scan runs unconditionally
over the FULL committed range regardless of requested dates and now takes 30-45+ minutes on today's
~8.4 GB DB — the thing that defeated every attempt before the finalize tail ever started. This drill
instead used a `backfill` of one genuinely unsnapshotted date (`_pick_unsnapshotted_trading_day`, the same
helper an existing sibling test already uses). This is not a scope reduction: `_refresh_ingest_aggregates`
runs identically regardless of which job kind or date range triggered it — every finalize-tail warm
computation reads the full committed universe/history, not just the triggering job's own range. Confirmed
before committing to the approach (not assumed): a real single-date backfill job had already run earlier
this session and produced real, substantial finalize-tail times (`factor_lab_all_warm` 568.51s,
`drawdown_expectations_warm` 343.69s) — the same order of magnitude a `rebuild`-triggered warm would
produce.

**Outcome: a complete, clean, 9-of-9-phase profile — the first complete realistic-pressure J-07 step 3
measurement in this session's history.**

- Job `95e1d3fc7eb34f20a2c55913f4de4ff7` (`backfill`, throwaway DB copy of the real ~8.37 GB dev DB,
  launched via `scripts/start-backend.sh` with host-guard caps applied, `pool_size=24`/`max_overflow=44`)
  reached status **`ok`** with all nine `aggregates_refreshed` categories, under 5 concurrent
  pool-pressure worker threads throughout.
- **All 9 finalize-tail phases + all 5 `forward_aggregates_warm` horizons captured** with real elapsed
  times and a joined VmPeak-at-completion reading each (full table in Addendum 39).
- **Overall peak VmPeak: 4,837,420 kB = 4,724.0 MB. Margin against `memory_cap_mb` (8192 MB): 42.3%**
  (57.7% of cap used) — comfortably above the 20% threshold, so **no config change** (TC-4).
- The peak was reached at t+134.7s (during pool-connection warm-up + the backfill's brief scan), BEFORE
  the finalize tail even began, then held flat for the rest of the 33-minute drill (VmPeak is the kernel's
  own monotonic non-decreasing high-water mark) — every phase shows the identical figure; verified against
  the raw sample CSV as a real finding, not a join bug.
- **Health: 1,795/1,795 `GET /api/health` polls (1 Hz) HTTP 200, zero non-200s, max latency 1.987s**
  (inside the relaxed ≤2s bounded-background-compute-window ceiling — bonus corroboration of J-07 step 2).
- **Zero real HTTP 503s / QueuePool timeouts anywhere in the drill's log window** — 8,898 total logged
  requests (health, job-status, and the 5 pool-pressure endpoints actually exercised), every one HTTP 200.
  This is materially cleaner than any of Addendum 38's three pressure attempts.
- Both spawned processes (pytest driver, throwaway backend) exited on their own via the existing fixture's
  exact-PID SIGTERM/SIGKILL teardown when the test completed — no manual kill needed, no `pkill -f`
  pattern used anywhere this round (iter-73/d's disclosed process-hygiene defect stayed closed by simply
  never needing to intervene).

Full per-phase table, per-horizon breakdown, and complete methodology write-up: `reports/perf-budgets.md`
Addendum 39. Raw evidence: `runs/goal-session-ops-hardening/iter-74/phase-vmpeak-samples.csv` (7,876
samples), `...-health.csv`, `...-phase-vmpeak.json` (the joined profile + full job record).

**J-07 step 3 status: CLOSED.** TC-1/TC-2/TC-4 are all met with complete, real, comfortable-margin
evidence. Steps 1/2/4 remain carried on their own prior durable evidence per this iteration's own testing
requirements (step 2 additionally now has this round's own clean corroborating 1 Hz poll evidence). The
binding TC-5 stop rule did not fire — this was the phase-by-phase method's first attempt this round, and
it succeeded, so no owner two-way choice is needed for J-07 step 3.

## Files Changed

- `apps/backend/tests/test_start_backend_script.py` — new join helpers (`_local_asctime_to_epoch`,
  `_parse_phase_timing_lines`, `_vmpeak_at`, `_join_phase_vmpeak`, `_FINALIZE_TAIL_PHASES`,
  `_PHASE_TIMING_LOG_RE`, `_SUBPHASE_TIMING_LOG_RE`), 4 new fast unit tests, 1 new live drill
  (`test_start_backend_phase_by_phase_vmpeak_profile_under_pool_pressure`, `xfail(strict=False)`), `import
  json` added. 18 → 23 tests collected.
- `reports/perf-budgets.md` — new Addendum 39 (full write-up); Addendum 38's test-count claim corrected in
  place (TC-6).
- `docs/goal.md` — "Ground truth" block corrected (DB size + `rebuild` range fact only; verified via `git
  diff` that no journey/anti-goal text changed).
- `docs/handoffs/goal-ops-hardening-iter-74-dev.md` — this handoff.
- `runs/goal-ops-hardening-iter-74/status.json` — new.
- `runs/goal-session-ops-hardening/iter-74/phase-vmpeak-samples*.{csv,json}`,
  `runs/goal-session-ops-hardening/iter-74/live-drill.log` — raw evidence from the live drill (new).

`config.yaml` is byte-unchanged (`git diff HEAD -- config.yaml` empty; `git status --porcelain --
config.yaml project-extensions/ scripts/` shows no changes anywhere in this iteration's diff — TC-4/TC-9).
No production/application code was touched — this iteration only adds test instrumentation and
documentation/report corrections.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_start_backend_script.py --collect-only -q`
Result: **23 tests collected** (18 pre-existing + 4 new fast unit tests + 1 new live drill; no collection
errors).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_start_backend_script.py -q -k "asctime
or parse_phase_timing or vmpeak_at or join_phase_vmpeak"`
Result: **4 passed** (the new deterministic join-logic unit tests).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_start_backend_script.py -q -k "not
heavy_ingest and not pool_pressure and not gap_insert and not factor_lab and not phase_by_phase_vmpeak"`
Result: **16 passed, 1 skipped** (all pre-existing non-heavy-ingest tests + the 4 new unit tests, unaffected
by this iteration's changes; the skip is the same pre-existing opt-in-gated skip iter-73 recorded).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_config.py -q`
Result: **75 passed** (pool-invariant boot tests — unaffected, `config.yaml` unchanged, run as a regression
check since TC-3's config-tune branch did not fire).

Command (the live drill itself): `cd apps/backend && TRENDORA_RUN_HEAVY_INGEST_TEST=1
TRENDORA_HEAVY_INGEST_SAMPLER_CSV=<path> .venv/bin/python -m pytest
tests/test_start_backend_script.py::test_start_backend_phase_by_phase_vmpeak_profile_under_pool_pressure -s -v`
Result: **1 xpassed in 1983.54s (33:03)** — completed cleanly, all assertions passed (see Results above).

## Pre-Handoff Verification

- **Service startup**: verified with two independent start/stop/restart cycles against the real committed
  dev DB (not the throwaway copy), on an isolated port (`CHAIN_BACKEND_PORT=18960`): both boots served
  `GET /api/health` HTTP 200 within 1-2s, the boot header in `logs/backend.log` confirmed
  `memory_cap_mb`/`malloc_arena_max`/host-guard caps applied each time, and each stop (by exact PID via
  `SIGTERM`) freed the port cleanly before the next start — no port conflicts. Also exercised extensively
  and repeatedly (correctly) by the live drill itself (throwaway-DB fixture start/stop, clean both times).
- **External integrations**: N/A — no new adapters/scrapers/live network calls; the drill's job carried
  `"source": null` (offline, committed-seed-only, AG-9).
- **Native dependency binaries**: N/A — no new dependencies.
- **Server cleanup**: confirmed via exact-PID `ps`/`lsof` checks after every start/stop cycle and after the
  live drill — no stray `uvicorn`/`start-backend.sh`/pytest-driver process remained; no `pkill -f` pattern
  used anywhere this session.

## Known Issues

- **None blocking.** This iteration's one risky action (the live phase-by-phase drill) succeeded cleanly
  on the first attempt — the binding TC-5 stop rule did not fire, so there is no owner two-way choice to
  present for J-07 step 3 this round.
- **`forward_aggregates_warm`'s per-horizon breakdown is captured (TC-1's explicit ask); a similar
  finer-grained per-CLAIM breakdown for `drawdown_expectations_warm` was discovered live in this session's
  own log (`"...sub-phase timing: ... phase=drawdown_expectations_warm claim=<claim> elapsed=..."`) but was
  NOT part of TC-1's ask and is not parsed/reported by this iteration's join** (only the whole-phase total
  for `drawdown_expectations_warm` is reported, which the existing phase-level log line already gives in
  full). Flagged here in case a future round wants that finer breakdown too — not a gap in this round's own
  deliverable.
- **Out-of-scope items explicitly NOT touched this round** (per the spec's own OUT OF SCOPE section, rule
  5 against bundling risky changes): the QA frontend intermittently serving unstyled/asset-less pages
  (queued as the very next round's target); the uvicorn admission-control 503 finding (not reproduced this
  round — see Results — but still an open, separately-disclosed item if it recurs); `stale_for_s` on the
  badge; B-1107; the 2-second health-ceiling policy question; `browser-qa-phase.sh`'s ordering-bug fix; the
  cost-budget question (now 14 consecutive over-budget rounds if this one counts — an owner-facing question
  this spec does not resolve).
- **Required-still-passing journeys** (J-01, J-03, J-04, J-05, J-06, J-08, J-09) were not re-verified via
  browser/deterministic-replay by this developer pass — that is QA-lane work per the pipeline's division of
  labor. This iteration's only production-adjacent change is test instrumentation + two documentation
  corrections (no application code path changed), so no plausible regression mechanism exists for those
  journeys, but the QA lane should still confirm on fresh evidence per the spec's TC-8.

## Owner items still open (carried, not this round's job to resolve)

The 2-second health-ceiling policy (long vs. short jobs), B-1107 (limiting concurrent heavy computes), the
`browser-qa-phase.sh` ordering-bug fix permission, and the cost-budget question — named here per the
spec's NOTES so they keep being asked in writing, not silently dropped.
