# Iteration 49 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-49
**Date:** 2026-08-05
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration (`Frontend Present: no`) touches only the internal implementation of two
already-registered producers behind the "Membership timeline / research hot-key caches" Data
Contract row. Both fixes are wall-clock performance bounds inside the SAME canonical modules/
endpoints, proven byte-identical against pinned pre-iteration reference oracles (120 tests,
`test_research_streaming.py` / `test_forward_testing_aggregates_streaming.py`, plus the new
`test_compute_drawdown_expectations_precomputed_phases_is_byte_identical`,
`test_factor_decile_observations_column_projected_equals_full_entity_reference[_component_kind]`,
`test_extract_factor_value_from_row_equals_extract_factor_value`).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `forward_aggregates` (canonical: `compute_forward_aggregates` / `forward_aggregates_ingest_cached`, `app.engine.forward_testing`; served by `GET /api/backtest`) | OK | `apps/backend/app/engine/forward_testing.py:626-676` (new `add_ratio`/`_accumulate_group_ratio` siblings, same module, same producer — no second computation); `apps/backend/app/engine/forward_testing.py:1303-1313` (hot loop now computes each observation's ratio once and reuses it, byte-identical per `_ExactMeanAcc.add_ratio`'s docstring and TC-3 tests) |
| `drawdown_expectations` (canonical: `compute_drawdown_expectations` / `compute_drawdown_expectations_cached`, `app.engine.forward_testing`; served by `GET /api/evidence`) | OK | `apps/backend/app/engine/forward_testing.py:2384-2385,2477-2478` (new optional `phases` kwarg, default `None` preserves every existing caller's behavior byte-identically; only the ingest-finalize warm loop passes a pre-computed value) — same function, same table (`event_study_cache`), same endpoint |
| Evidence-panel factor/decile observations feeding `drawdown_expectations` (canonical: `_factor_decile_observations`, `app.engine.research`, reached via `compute_samples`/`_factor_samples`) | OK | `apps/backend/app/engine/research.py:186-231` (new `_extract_factor_value_from_row` / `_factor_value_column` helpers) + `:576-660` (column-projected `select(ScannerResult.run_id, ScannerResult.ticker, value_col)` replacing `select(ScannerResult)`) — same function, reads the same table, no second producer; byte-identity proven by `test_factor_decile_observations_column_projected_equals_full_entity_reference` |
| Job history / Backfill run-summary contract (`status`, `aggregates_refreshed`, `message`) | OK | `apps/backend/app/engine/data_manager.py:3978-4013` (new per-horizon sub-phase logging only, `finally`-wrapped around the SAME existing call site) and `:4105-4199` (new `phase_context_by_date` single precompute + per-claim sub-phase logging, threaded into the SAME `compute_drawdown_expectations_cached` call) — no new field, no second `_run_detail()` producer |

No new UI surface fetches any of these values from a non-canonical endpoint (zero `apps/frontend/`
files changed — confirmed via `git diff <snapshot-sha> --stat -- apps/frontend/` returning empty).
No new displayed value/entity is introduced this iteration (confirmed by the iteration spec's own
"New information displayed: None new" and "Data-contract additions: None" fields, and by the
ui-surface-map's "5 observable + 3 invisible/perf-only" surfaces all mapping to fields that already
exist unchanged in shape).

## Information Architecture check

Zero new pages/routes/features — `Frontend Present: no`, confirmed by an empty
`git diff <snapshot-sha> --stat -- apps/frontend/`. The iteration spec's own "UI surface changes:
None — no new page/panel/route" and "Blueprint conformance" fields name only pre-existing homes
(`/data`, `/backtest`, `/evidence`), matching the blueprint's Information Architecture unchanged.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK | N/A — no nav file touched; sidebar/router unchanged (no frontend diff) |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The blueprint's Data Contract row update (iter-49 changelog paragraph + a note appended to the
  "Membership timeline / research hot-key caches" row, `runs/goal-session-ops-hardening/state/blueprint.md`)
  accurately reflects the diff: same computing modules, same tables, same serving endpoints, no
  schema change. No correction needed.
- The blueprint's own note discloses (correctly, as a carried/out-of-scope item, not a defect this
  gate should flag) that `_combination_observations` (`app.engine.research`) shares the same
  full-entity-read shape `_factor_decile_observations` had before this iteration's fix and is now
  the single most expensive live claim (~99s) — a legitimate candidate for a future iteration, not
  a coherence violation (no second producer was created; the existing single producer is simply not
  yet as fast as its sibling).
