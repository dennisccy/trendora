# goal-market-compass-iter-21 Dev Handoff

**Phase:** goal-market-compass-iter-21
**Date:** 2026-08-27
**Agent:** developer
**Status:** complete

## Terminal vocabulary (docs/goal.md item 14, INCOMPLETE state)

```
J-11 STAGE D EXECUTED: YES
J-11 STAGE E COMPLETE: YES
J-11 STAGE F COMPLETE: YES
J-11 STAGE G VERIFIED: NO
J-11 INCIDENT STATUS: NOT REPAIRED — ATTEMPT INCOMPLETE
J-11 MAINTENANCE BOUNDARY: ACTIVE
J-11 LIVE PRE-BOOT GUARD: ARMED
```

Stage G (the only stage that may declare the incident fully repaired) was explicitly out of scope this
iteration and was not attempted. Nothing above claims otherwise.

## What Was Built

- **`app.engine.j11_stage_f_execute`** (new module) — J-11 Stage F: dependency-aware derived-cache
  classification and deletion over the seven `dataset_version`-bearing cache tables. Composes, never
  reimplements: `j11_stage_d_execute.recheck_maintenance_boundary_and_guard`,
  `j11_stage_e_execute.check_engine_identity_matches_stage_d`/`confirm_manifests_unchanged`,
  `research._dataset_version`/`_membership_dataset_version`, `indexes.index_series_dataset_version`,
  `data_manager._membership_bars_are_forward_only`/`_parse_membership_stamp`,
  `j11_maintenance.capture_full_table_sweep`/`diff_full_table_sweeps`. New Stage-F-specific functions:
  `derive_cache_table_inventory` (genuine runtime introspection over `SQLModel.metadata`, never a
  hardcoded list — TC-3), `confirm_stage_e_complete_and_unrestamped`,
  `derive_stage_d_execution_start_instant`, `capture_cache_table_snapshot`,
  `confirm_no_cache_row_at_or_after_stage_d_start`, `stage_f_preflight_gate_verdict`,
  `evaluate_membership_timeline_incremental_reuse_safety`, `compute_live_stamp_for_table`,
  `classify_cache_table`, `execute_stage_f_cache_disposition`, `live_verify_cache_dispositions`,
  `build_stage_f_mutation_accounting`, `stage_f_execution_outcome`.
- **`scripts/run_j11_stage_f_execute.py`** (new CLI) — `--confirm`/`--evidence-dir`-gated executable,
  mirroring `run_j11_stage_e_execute.py`'s idiom exactly (no DB interaction of any kind without
  `--confirm`; evidence persisted before the write; the outcome written unconditionally last).
- **Fixture-scoped tests** — `tests/test_j11_stage_f_execute.py` (56 tests, module-level unit/integration
  + one full end-to-end fixture via `app.db.make_engine`) and
  `tests/test_j11_stage_f_execute_cli_script.py` (19 tests, mock-based CLI control-flow) — 75 tests total,
  never touching `apps/backend/data/trendora.db`.
- **The live, `--confirm`-gated execution** against `apps/backend/data/trendora.db` — see Live Execution
  Results below.

## The two substantive findings this iteration resolved

1. **`availability_cache` correctness risk (docs/goal.md BACKGROUND finding 4).**
   `data_manager.availability_from_storage`'s "row exists, stamp mismatched, no ingest job in flight"
   branch (`data_manager.py:1741-1747`/`:1760-1763`) serves the stored row with `stale: False`. Verified
   live BEFORE deletion (via a fixture reproducing the exact stored row) that this branch is real:
   `served_dataset_version` echoed the STALE pre-incident stamp with `stale: False`. After Stage F's
   deletion, the same call returns the honest `_availability_not_yet_computed_payload()` sentinel
   (`stale: False`, `served_dataset_version: None`, `cells: []`) — proven both in a fixture test
   (`test_tc10_availability_from_storage_honest_after_deletion`) and structurally, by the post-write live
   `COUNT(*) == 0` on `availability_cache`.
2. **`membership_timeline_cache` incremental-reuse tradeoff (docs/goal.md BACKGROUND finding 5).** Proved
   live, read-only, BEFORE choosing a disposition: the stored row's cached date list (3,121 dates, tail
   `2026-08-12`) against the live `scanner_runs.asof_date` set (3,128 dates) yields exactly 7 new dates
   (`2026-05-13` through `2026-08-05`), 0 missing dates, `append_forward == False` (the new dates are all
   earlier than the cached tail, not later), and `bars_are_forward_only == True` (reusing
   `data_manager._membership_bars_are_forward_only` directly — `daily_prices` is unchanged, so this holds
   trivially and correctly). This proves `membership_timeline_cached`'s own MISS-repair logic
   (`data_manager.py:894-963`) would take the CHEAP "historical gap-insert" branch on the next real
   request, never the documented >300s full cold-compute sweep. Disposition:
   `preserve_for_incremental_reuse` — the row was left untouched (0 rows deleted from
   `membership_timeline_cache`; verified unchanged `dataset_version`/`created_at` before and after).

## No-tautology verification (docs/goal.md DoD item, iter-20's three named checks)

Every boolean this module computes is traceable to a live- or fixture-derived value. Explicitly checked
against iteration 20's three named tautological patterns:

- **Not `population_a_pre_was_zero`-style (a hardcoded literal compared to itself):** the decisive
  `all_rows_created_before_stage_d_start` check compares a LIVE `MAX(created_at)` (or `MAX(computed_at)`
  for `coverage_snapshot`) against a LIVE-derived `stage_d_execution_start_instant` — neither side is a
  constructed constant. Mutation-checked directly: I temporarily changed the classification branch to gate
  on `stamp_matches_live` instead of `all_rows_created_before_stage_d_start` (the exact anti-pattern the
  collision-trap test exists to catch) and re-ran `test_tc7_stamp_collision_still_classified_stale_via_
  created_at` — it FAILED (`AssertionError: 'prove_unaffected_leave_alone' == 'explicit_delete'`). Reverted
  (confirmed byte-identical via `diff` against a pre-mutation backup); the full suite is green again.
- **Not `population_b_never_decreased`-style (`all()` over a structurally-empty collection):**
  `confirm_no_cache_row_at_or_after_stage_d_start` and `confirm_stage_e_complete_and_unrestamped` both
  fail closed on an empty input (`bool(per_table) and all(...)`, mirroring the pattern the iter-20 audit
  itself praised as sound) — proven by dedicated tests
  (`test_late_row_check_fails_closed_on_empty_snapshots`,
  `test_stage_e_check_fails_closed_on_empty_expected_map`). The membership-timeline `new_dates`/
  `missing_dates` lists are real per-run query results, not construction-time literals, and both a
  non-empty and an ambiguous/append-eligible case are exercised (TC-9's two branches).
- **Not `population_c_latest_run_observable_ceiling_respected`-style (narrow accidental coverage):** the
  mutation-accounting subset check (`changed_tables_subset_of_explicit_delete_set`) was mutation-checked
  too — hardwiring it to `True` did NOT break my first two "fails when X" tests (they were independently
  caught by the sibling `out_of_scope_tables_zero_fingerprint_change` check, revealing those two tests
  didn't isolate this specific check). I added a THIRD test,
  `test_mutation_accounting_fails_when_a_wholly_unrelated_table_changed` (a table — e.g. `stocks` — that is
  in NEITHER `OUT_OF_SCOPE_TABLES` NOR any cache-table disposition), which the mutation DOES break, and
  confirmed it fails red under the mutation and passes green after reverting. This is exactly the kind of
  narrow-coverage gap iteration 20's audit found — caught here before merge, not after.

Every "fails when X" scenario in the test suite constructs a genuinely different DB state (real fixture
rows with real timestamps/counts), not a mocked boolean, with three exceptions that are legitimately pure
compositions tested with synthetic dicts by design (`build_stage_f_mutation_accounting`,
`stage_f_execution_outcome`, `stage_f_preflight_gate_verdict` — mirroring
`j11_stage_e_execute.build_stage_e_mutation_accounting`'s own established, audited-sound idiom).

## Live Execution Results (independently re-verified against `apps/backend/data/trendora.db`)

Preflight (all six checks passed; `proceed: true`, `blocking_reasons: []`):
- Boundary/guard recheck: `ok=true`, all 11 incident dates blocked.
- Stage E end-state check: all 11 incident runs present, unrestamped (ids 3148–3158, identity
  `53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55`), each `ForwardReturn` count matching
  iteration 20's own recorded per-run-id outcome exactly (2771, 2769, 2216, 2215, 1659, 1658, 1103, 1103,
  549, 549, and run 3158's own recorded `0` — never treated as a gap).
- Engine identity: fresh `53d2ffd10c...` matches Stage D's frozen value.
- Manifests: live dump byte-identical to the iteration-16 certified baseline (24 rows).
- Inventory: `derive_cache_table_inventory()` found exactly the 7 expected tables (introspected live from
  `SQLModel.metadata`, not a hardcoded list).
- Late-row hygiene: `MAX(created_at)`/`MAX(computed_at)` on all 6 scanner-run-dependent cache tables is
  `2026-08-23` at the latest — strictly earlier than Stage D's execution-start instant
  `2026-08-26T10:52:55.552946+00:00` (re-derived live as `MIN(created_at)` over Stage D's own recorded
  incident run ids — this value happens to match the iteration-state digest's citation exactly, confirming
  it independently rather than trusting it).

Classification (7 of 7 tables, each with a live-recomputed stamp + full stored-stamp/timestamp evidence
in `runs/goal-market-compass-iter-21/j11-stage-f-execute-dispositions.json`):

| Table | Live stamp | Stored rows | Disposition |
|---|---|---|---|
| `event_study_cache` | `r3158-f6814320` | 18 (9 distinct stale stamps) | `explicit_delete` |
| `market_phase_cache` | `r3158-f6814320` | 1,290 (117 distinct stale stamps) | `explicit_delete` |
| `forward_aggregate_cache` | `r3158-f6814320` | 333 (34 distinct stale stamps) | `explicit_delete` |
| `availability_cache` | `r3158-rc3128-b2026-08-12-bc3310374-h200` | 1 | `explicit_delete` |
| `coverage_snapshot` | `r3158-rc3128-b2026-08-12-bc3310374-h200` | 1 | `explicit_delete` |
| `index_series_cache` | `d2026-08-12-c60699` | 1 (stamp MATCHES live) | `prove_unaffected_leave_alone` |
| `membership_timeline_cache` | `r3158-rc3128-...` | 1 (stamp differs, proof holds) | `preserve_for_incremental_reuse` |

Execution: `total_rows_deleted = 1643` (18 + 1290 + 333 + 1 + 1). Peak memory `479.9 MB` — well within
`server.memory_cap_mb: 8192` (margin `7712.1 MB`).

Live post-write verification: all 5 `explicit_delete` tables read `COUNT(*) == 0`; both preserved tables
(`index_series_cache`, `membership_timeline_cache`) read unchanged row counts, `dataset_version`, and
`created_at`.

Mutation accounting (`all_checks_pass: true`): `changed_existing_tables` = exactly the 5 `explicit_delete`
table names; `no_unexpected_new_tables`/`no_unexpected_removed_tables` both empty;
`daily_prices_unchanged`/`data_provider_runs_unchanged`/`watchlist_unchanged`/`manifests_unchanged`/
`maintenance_boundary_unchanged` all `true`.

**Independent re-verification I performed myself, separately from the module's own evidence**, via
read-only `sqlite3 "file:...?mode=ro"` queries before AND after the write:
- Before: confirmed live broad stamp `r3158-f6814320`, narrow stamp
  `r3158-rc3128-b2026-08-12-bc3310374-h200`, and that every one of the 7 cache tables' stored rows
  predates these values — matching the module's own subsequent findings exactly.
- After: `event_study_cache`/`market_phase_cache`/`forward_aggregate_cache`/`coverage_snapshot`/
  `availability_cache` all read `0` rows; `index_series_cache` and `membership_timeline_cache` each still
  hold their original single row, byte-identical `dataset_version`/`created_at`.
- `daily_prices` (3,310,374 rows, max date 2026-08-12), `scanner_runs` (3,128 rows, max id 3158),
  `forward_returns` (6,814,320), `next_session_manifests` (24) — all unchanged from the pre-run figures.
- `maintenance_boundaries`: still `active=1`, still exactly the 11 canonical incident dates.
- Main DB file size/mtime unchanged (8,365,871,104 bytes) — the write landed in the WAL sidecar (grew from
  0 to 284,312 bytes), the expected signature for a bounded WAL-mode write, never a full-file rewrite.

## Files Changed

- `apps/backend/app/engine/j11_stage_f_execute.py` — new; Stage F execution module.
- `apps/backend/scripts/run_j11_stage_f_execute.py` — new; `--confirm`/`--evidence-dir`-gated CLI.
- `apps/backend/tests/test_j11_stage_f_execute.py` — new; 56 fixture-scoped tests.
- `apps/backend/tests/test_j11_stage_f_execute_cli_script.py` — new; 19 mock-based CLI control-flow tests.
- `runs/goal-market-compass-iter-21/j11-stage-f-execute-*.json` — new; 16 live-run evidence artifacts.

Untouched (verified via `git status --porcelain -uall`): `scoring.py` (J-01), `compass.py` (J-04),
`data_manager.py` (J-10's recovery code — this iteration reads `availability_from_storage`/
`coverage_from_storage`'s documented behavior and `_membership_bars_are_forward_only` but modifies no line
of the file), and every other production file. No canonical producer/serving function's code was modified.

## Tests Run

Command: `apps/backend/.venv/bin/python -m pytest tests/test_j11_stage_f_execute.py
tests/test_j11_stage_f_execute_cli_script.py -v` (run from `apps/backend/`)
Result: 75 passed, 0 failed (56 + 19). Never against `apps/backend/data/trendora.db` — fresh `sqlite://`
in-memory engines and one `app.db.make_engine`-backed tmp-file engine only.

Per CLAUDE.md/project-template.md discipline, the full backend suite was NOT run (never sanctioned for a
pipeline agent on this repo — the 30-year fixture takes ~10-11h). No two pytest processes ran concurrently.

## Maintenance isolation (held for the whole iteration)

No backend boot, no frontend boot, no browser-qa-agent, no replay lane, no Data Manager, no ordinary API
request, no normal warmup — verified before starting (`ss -ltnp` showed no listeners on 8000/3000) and
never started during this iteration. `CHAIN_MAINTENANCE_ISOLATION=true` and `CHAIN_REQUIRE_FULL_DEPTH=true`
were confirmed present in-process before any work began (owner ruling item 13) and re-confirmed
immediately before the live write. The live CLI invocation ran in the foreground (per the coordinator
note's operational guidance) and was not blocked by the auto-mode classifier.

## Resource discipline (AG-10)

Live peak process memory during the Stage F execution: 491,444 kB (479.9 MB) VmPeak — far below
`server.memory_cap_mb: 8192` and `HOST_GUARD_MEMORY_HIGH: 12G`. Host `free -h` immediately before the run:
5.0Gi free / 18Gi available, consistent with the three-goal-mode-engine host-sharing baseline noted in the
dispatch. No eager cache regeneration was performed (explicitly out of scope) — the deleted caches will
repopulate lazily through their existing, already-safe canonical producers only after the app is genuinely
allowed to boot post-Stage-G.

## Known Issues

- None discovered that are in scope for this iteration. The two framework notes carried forward
  unchanged per owner instruction (the ordinary-request-path/Data-Manager write-path guard gaps, and
  `goal_gate.py`'s duplicate-journey-heading defect) were not touched, as directed.
- Stage G (the only stage that may declare the incident fully repaired) remains for a future iteration.
  Until Stage G passes, normal Market Compass work (J-01–J-09) stays blocked per the existing
  loop-mechanics rule, and the maintenance boundary stays `active=1`.
