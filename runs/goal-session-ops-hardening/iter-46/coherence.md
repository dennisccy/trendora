# Iteration 46 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-46
**Date:** 2026-08-04
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

<!-- COHERENCE-WARN: only advisory issues; does NOT block GOAL_ACHIEVED -->

---

## Data Contract check

Diff scope (against snapshot `5b7b30f7`): `apps/backend/app/engine/{research.py, forward_testing.py,
data_manager.py, warmup.py}` + 4 test files + `journey-scripts/J-07.json`'s anchor number. No frontend
files touched (`plan.md`/iter spec: "Frontend Present: no", confirmed by `git diff --stat`).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Membership timeline / research hot-key caches — `_combination_observations`'s `ret_by_run_symbol` | OK | `apps/backend/app/engine/research.py:783-818` — refactored to slice-and-discard via the SAME `_fr_slice_map` helper `_factor_observations` already uses; same module, same two callers (Evidence combination-kind claims, Combination Lab), no second producer. |
| Membership timeline / research hot-key caches — `compute_drawdown_expectations`'s `stored_by_key` | OK | `apps/backend/app/engine/forward_testing.py:2270-2286` (new private helper `_drawdown_ticker_slice_map`) + `:2381-2404` (fold-and-discard per chunk) — same function, same module, same endpoint (`GET /api/evidence`), no second producer. |
| Membership timeline / research hot-key caches — `event_study_cache`'s `drawdown_expectations` warm trigger | OK | `apps/backend/app/engine/warmup.py:153-216` (new `_warm_drawdown_expectations`) calls the SAME canonical `forward_testing.compute_drawdown_expectations_cached` the ingest-finalize hook already warms (iter-7) and `GET /api/evidence` already reads — this is a new *trigger* (boot-time, mirroring the already-blueprint-documented dual-trigger pattern for the sibling membership-timeline/coverage caches, row Notes iter-2: "the boot trigger is retained… as the safety net"), not a new producer or endpoint. |
| Coverage payload — `refresh_coverage_snapshot` invocation gate | OK | `apps/backend/app/engine/data_manager.py:3768-3820` — new conditional (`if not prog.new_snapshot_dates and _coverage_snapshot_is_current(...)`) changes *when* the SAME canonical `refresh_coverage_snapshot`/`_compute_coverage_uncached` runs; same module, same endpoint (`GET /api/data`), no second derivation. |
| Job history / isolation logging (`_fail_unlaunched_job`, `_fail_unlaunched_resume`) | OK — not a displayed value | `apps/backend/app/engine/data_manager.py:5102-5142` — bare `logger.exception` replaced with the module's existing `_log_isolation_failure` convention (19 other sites, iter-44/45). Internal logging only, no Data Contract row. |
| J-07 dataset-size anchor (`journey-scripts/J-07.json`) | OK | `runs/goal-session-ops-hardening/journey-scripts/J-07.json:8` — test-fixture number corrected 2532→2526; audit independently verified 2526 live (`/api/data` `coverage.gap_count`). Not a code producer change. |

No new implementation was found that independently recomputes a registered Data Contract value
outside its registered module, and no new UI surface fetches a registered value from a non-canonical
endpoint (there is no new UI surface at all this iteration).

## Information Architecture check

No new page/route/feature — the iteration is backend-only (confirmed by `git diff --stat`: zero files
under `apps/frontend/`). Nothing to check against nav/sidebar/router files.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no frontend change) | OK | - |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Two implementation additions beyond the iter-46 spec's IN SCOPE list are undocumented in the
  blueprint's iter-46 narrative** (`runs/goal-session-ops-hardening/state/blueprint.md:348`, `:406`):
  (1) the coverage zero-work redundancy gate (`data_manager.py:3768-3820`, addressing QA blockers
  1+4 / J-01/J-03 — a zero-work backfill never reaching a terminal state) and (2) the new boot-time
  `_warm_drawdown_expectations` trigger (`warmup.py:153-216`, QA blocker 3 / J-06/J-07 — closing the
  post-restart `/evidence` cold-miss). Both reuse already-registered canonical modules/endpoints with
  no second producer (see table above), so this is not a Data Contract violation — but per this
  session's own established convention (blueprint iter-9→iter-10: an undocumented-until-next-iteration
  addition was flagged as a coherence advisory, not a FAIL), the decomposer should retroactively name
  both in the blueprint's next dated update so the "Membership timeline / research hot-key caches" and
  "Coverage payload" rows' Notes columns stay a complete history of every trigger/gate touching them.
- The iter-46 dev/audit handoffs (`docs/handoffs/goal-ops-hardening-iter-46-audit.md`) record that the
  audit itself applied one further in-tree fix (`data_manager.py:3803`, tightening the same gate to
  also require `not prog.new_snapshot_dates`) plus a new test file
  (`apps/backend/tests/test_ingest_finalize_zero_work_coverage.py`). This is already reflected in the
  diff reviewed above and does not change the Data Contract/IA assessment — same module, same endpoint,
  no second producer.
- Out of this gate's scope, noted only for context: the audit report independently found the
  iteration's fix incomplete on correctness/process grounds (B2 — evidence cache invalidates on any
  concurrent ingest, so TC-4 is unmet; B3 — a third unbounded whole-cohort materialization,
  `apps/backend/app/engine/samples.py:145-156`, remains on the same `/api/evidence` path; T1/T2 —
  the only browser-QA lane on record predates the fix and violates the screenshot-uniqueness rule) and
  returned audit verdict FAIL. None of these are coherence violations (no duplicate producer, no
  non-canonical endpoint, no missing nav path) — B3 in particular is a *pre-existing* unbounded
  accumulator, not a new one this iteration introduced, so Part A's "duplicate computation" rule does
  not apply to it. Flagged here only so the next iteration's decomposer sees the coherence-auditor
  independently corroborates the audit's B3 finding is a distinct, still-open site rather than
  something this iteration's Data-Contract completion claim already covers.
