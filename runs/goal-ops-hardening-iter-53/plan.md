# goal-ops-hardening-iter-53 Execution Plan

## What to Build

Extend iter-52's proven cooperative-scheduling fix (`_cooperative_sorted` / `_cyclic_gc_paused`,
`apps/backend/app/engine/research.py:143-204`, applied to `compute_factor_lab_all`) to the two
finalize-tail phases Addendum 14 named as the last live sources of connection-level `GET /api/health`
non-answers (2 of 1,285 in the concurrent drill):

- **Profile, then bound `coverage_membership_timeline_refresh`.** Call chain:
  `_refresh_ingest_aggregates` (`data_manager.py:4050-4106`) → `refresh_coverage_snapshot` (`:1378`) →
  `_compute_coverage_uncached`/`_compute_coverage_body` (`:1109`/`:1150`) → `membership_timeline_cached`
  (`:815`) → on cache MISS: `_membership_timeline`/`_membership_timeline_incremental` (`:524`/`:731`) →
  `_excluded_counts_by_date` (`:612`) → `universe_resolver.resolve_with_reasons`. Profile this chain
  live (Addendum 14 methodology) to find the actual GIL-hold call — do not assume it is a `sorted()` by
  analogy to `compute_factor_lab_all` (iter-48's lesson: profile, don't guess). Apply
  `_cooperative_sorted` / `_cyclic_gc_paused` or an equivalent chunked/bounded construct at the real
  site.
- **Profile, then bound `market_phase_warm`.** The OUTER per-date loop already lives in
  `_refresh_ingest_aggregates` (`data_manager.py:4124-4151`, one iteration per `prog.new_snapshot_dates`
  entry, already yields `time.sleep(0)` + has a `MemoryError` isolate-and-continue handler — do not
  touch that outer shape). The likely GIL-hold is INNER: `market_phase.market_phase_cached` (`:888`) →
  on cache MISS: `compute_market_phase` (`market_phase.py:701`), which loops `_severity_reading(session,
  run, cfg)` once per `_stored_runs_through(session, as_of)` entry (~2,900 runs on the live 30y basis)
  before `_filtered_bear_path` runs over the full causal vector — a per-run compute loop with the same
  shape as `compute_factor_lab_all`'s per-entry loop. Profile to confirm before treating; a bare
  `time.sleep(0)` at the outer per-date loop's top cannot interrupt whatever this inner loop holds the
  GIL on (the exact iter-52 lesson that motivated the sort/GC fix in the first place).
- **Fault-injection sites (TC-5).** Neither phase has a `_fault_inject_memory_error` site today (only
  `forward_aggregates`, `drawdown_expectations`, `backfill_worker`, `factor_lab_all` exist,
  `data_manager.py:3256-3258`). Add two new site names to `_FAULT_INJECT_SITES` (e.g.
  `"coverage_membership_timeline"`, `"market_phase"`) and call `_fault_inject_memory_error(site)`
  inside the actual treated loop (not just at the phase-level call), mirroring `factor_lab_all`'s
  convention (injected deep inside `compute_factor_lab_all`, not at its call site) so the test exercises
  the real treated code path. `market_phase.py` has no existing import of `data_manager` (it would be
  circular — `data_manager.py:60` imports `market_phase` at module level); use a lazy, function-scoped
  import, mirroring the exact same trick `research.py:1391-1395` and `forward_testing.py:2607-2608` already
  use for the identical reason.
- **New unit tests (TC-3, TC-5)** proving byte-identical output (object-identity or value-equality,
  matching `test_cooperative_sorted_is_byte_identical_to_sorted_across_the_chunk_boundary`'s convention,
  `test_research_streaming.py:2078`) between the treated and untreated computation, plus a
  fault-injection isolate-and-continue test mirroring the existing MemoryError tests already in
  `test_data_manager.py` (coverage-persist loop `:1753-1832`, market-phase-warm loop `:1843-1899`) —
  those test the OUTER loop's existing contract already; the new tests must additionally prove the newly
  treated INNER call preserves it.
- **Re-run the Addendum 14 concurrent-drill methodology** against the shipped tree (spawned backend via
  `scripts/start-backend.sh` under AG-10 caps, a dedicated 1/s `/api/health` poller process, a dedicated
  heavy-research-request stream, one real `POST /api/data/jobs` backfill, 40s hold past terminal) and
  append a new dated addendum (next number after Addendum 14, i.e. Addendum 15) to
  `reports/perf-budgets.md` disclosing honestly: non-answer count for the two treated phases (target
  zero, down from 2/1,285), >2.0s poll count/percentage, and the finalize-tail total (expected to
  **likely still read over the 1,200s budget** — `forward_aggregates_warm` and
  `drawdown_expectations_warm`, the two largest contributors, are deliberately untouched this
  iteration; do not claim that budget closed).
- **J-04 evidence capture only** (steps 3-5: badge/banner initializing detail + n/m progress, distinct
  crashed/unreachable presentation, persistent logfile truncation after a simulated kill) — this
  behavior already shipped and is proven; browser-qa captures its first screenshot/DOM/log evidence.
  No code change anticipated for this journey.

**Deliberately out of scope this iteration** (do not expand into these — mirrors the spec's own rule-6
narrowing):
- `forward_aggregates_warm`'s untreated GIL-hold (largest slow-poll contributor by count, but zero
  connection-level non-answers — lower severity than the two phases above).
- The Regime Lab `/research/regime-lab` MemoryError (`compute_regime_lab` →
  `_regime_lab_members_by_horizon`) and `J-06`'s heading-only assertion — a separate, undiagnosed
  defect in a different module; bundling it here stacks a second undiagnosed risky change onto this
  iteration.
- Moving heavy compute to a separate process/worker boundary (open owner question, unanswered since
  iter-50/51).
- Any edit to `config.yaml`, `project-extensions/host-guard/host-guard.env`,
  `scripts/start-backend.sh`, `scripts/dev.sh`, `scripts/start-frontend.sh` (AG-10 frozen surfaces —
  `memory_cap_mb`/`malloc_arena_max` stay untouched; this is a scheduling-only fix per iter-50's lesson
  that bounding memory cannot fix a scheduling problem).

## Agents Required
- backend-data: yes -- profile and treat both finalize-tail phases (data_manager.py, market_phase.py),
  add fault-injection sites, write/extend unit tests, run the concurrent drill, append the perf-budgets
  addendum, write the dev handoff.
- frontend-ux: no -- zero frontend files touched. Browser-qa observes EXISTING UI only (badge, banner,
  `/data` job-history panel) to capture J-04's previously-unobserved evidence and to replay J-05/J-07/
  J-01/J-03/J-08/J-09 — no new component, page, or nav entry.

## Frontend Present
Frontend Present: no

Note for QA/pipeline automation: "Frontend Present: no" reflects zero frontend CODE changes only. It
must NOT be read as "skip browser QA" -- the standing 8-journey browser/replay lane (browser-qa-agent,
driven by this spec's own Target/Required-still-passing journeys) still runs and is mandatory (TC-6,
TC-7). Goal mode's `detect_frontend_in_plan` already forces the lane on whenever
`CHAIN_GOAL_TARGET_JOURNEYS` is non-empty, regardless of this line.

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` -- profile + bound `coverage_membership_timeline_refresh`'s
  real GIL-hold site (candidates: `_membership_timeline`/`_excluded_counts_by_date`'s per-date resolver
  loop); add the `"coverage_membership_timeline"` fault-injection site + call at the treated loop.
- `apps/backend/app/engine/market_phase.py` -- profile + bound `compute_market_phase`'s per-run loop
  (`_severity_reading` over `_stored_runs_through`); add a lazy `from app.engine import data_manager`
  import + `data_manager._fault_inject_memory_error("market_phase")` call at the treated loop.
- `apps/backend/tests/test_data_manager_membership_cache.py` -- new byte-identity test for the treated
  coverage/membership-timeline call (TC-3).
- `apps/backend/tests/test_data_manager.py` -- new fault-injection isolate-and-continue test(s) for both
  newly-treated phases (TC-5), alongside the existing MemoryError tests at `:1753-1899`.
- `apps/backend/tests/test_market_phase.py` -- new byte-identity test for treated `compute_market_phase`
  (TC-3).
- `reports/perf-budgets.md` -- new dated addendum (Addendum 15) with the re-run solo + concurrent drill
  results (TC-1, TC-2), stated honestly whether or not each ceiling is met.
- `docs/handoffs/goal-ops-hardening-iter-53-dev.md` -- dev handoff naming both treated phases, the
  specific profiled GIL-hold call in each, and the concurrent-drill result honestly (TC-9).
- `runs/goal-session-ops-hardening/state/assumptions.md` -- append only if a new judgment call arises
  during implementation (the iter-53 decomposer entry already logs the 2-vs-3-phase scoping call).

**Do not modify:** `config.yaml`, `project-extensions/host-guard/host-guard.env`,
`scripts/start-backend.sh`, `scripts/dev.sh`, `scripts/start-frontend.sh` (TC-8 requires an empty `git
diff --stat`/`git status --porcelain` over exactly these five paths).

## UI Evolution
N/A -- Frontend Present: no. No new capability, information, action, surface, or nav change. J-04's
badge/banner/logfile behavior is already-shipped, unchanged code; this iteration only captures its first
evidence.

## Visual Requirements
N/A -- Frontend Present: no.

## Key Test Scenarios
- **TC-1/TC-2 (primary):** concurrent drill (Addendum 14 methodology) measures zero `/api/health`
  connection-level non-answers attributable to `coverage_membership_timeline_refresh` and
  `market_phase_warm` specifically (down from 2/1,285); results recorded honestly in a new
  `reports/perf-budgets.md` addendum whether or not fully met.
- **TC-3:** a new unit test proves the treated function's output is identical (object-identity/
  value-equality) to the untreated computation for the same fixture inputs, for both phases.
- **TC-4:** a solo (non-concurrent) ingest job still lists `coverage`, `membership_timeline`, and
  `market_phase` in `aggregates_refreshed` exactly as before, zero new `MemoryError` in
  `logs/backend.log`.
- **TC-5:** `_fault_inject_memory_error` armed on either newly-treated phase stops only that phase's
  loop, calls `_release_process_memory()`, and every item that already succeeded earlier in the same
  loop stays honestly reported -- process never crashes, `/api/health` keeps answering 200.
- **TC-6 (browser-qa):** J-04 steps 3-5 get their first evidence capture -- badge/banner initializing
  detail (phase + n/m) during a pre-ready poll window; distinct crashed/unreachable presentation after a
  simulated kill; persistent logfile shows boot entries with no clean-shutdown entry after the kill.
- **TC-7/TC-9 (binding sequencing rule -- broken 6 of 7 rounds this session, must not repeat):** the
  8-journey deterministic-replay + browser-qa lane (J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09) is
  dispatched LAST, against a tree FROZEN after this iteration's code lands -- every lane result file's
  mtime must be strictly after the newest `apps/backend/**` mtime. If the auditor subsequently finds a
  defect needing a code change, it files a note for iter-54 in the audit report -- it must NOT apply a
  code-changing fix this round (a post-lane code change invalidates the very evidence the lane just
  produced, which is exactly what made iter-52 unscoreable). J-01/J-03/J-08/J-09 must replay PASS
  (regression guard).
- **TC-8 (anti-goal):** `git diff --stat` / `git status --porcelain` empty over the 5 frozen AG-10
  surfaces; every `data_provider_runs` row created by this iteration's drills reads `provider='seed'`
  (AG-9 -- no live network call).
- Full existing backend test suite: no regressions (do not run the full suite locally as the pump/dev
  agent per this project's standing lesson -- targeted files only; the reviewer/QA stage verifies the
  broader suite).
