# Iteration 40 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-40
**Date:** 2026-07-31
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration touches two ALREADY-registered rows and their supporting scaffolding only — no new
displayed value, no new endpoint, no second computing module for anything.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Coverage payload (`GET /api/data`, `app.engine.data_manager` — `_compute_coverage_uncached`/`_compute_coverage_body`) | OK | `apps/backend/app/engine/data_manager.py:271` — `_missing_data_diagnostic`'s second query switched `session.exec(select(...))` (whole-result materialize) to `.yield_per(cfg.research.read_batch_size)` (streamed). Same query, same `WHERE ... IN (universe)` scope, same grouping into `own_dates_by_symbol`, same downstream gap-diff logic — only the fetch strategy changed. Proven byte-identical by `test_diagnostic_own_dates_streamed_fetch_byte_identical_to_whole_result` (`apps/backend/tests/test_data_manager.py:4411-4451`), which replicates the OLD `.all()` path as a non-production reference and asserts equality against the NEW streamed path, plus an equality check between default and tiny (`read_batch_size=3`) batch sizes on the real function. No second producer, no new endpoint. |
| Job history & per-date exclusion reasons (`data_provider_runs`, `_checkpoint_run_record`/`_run_detail()` serializer) | OK | `apps/backend/app/engine/data_manager.py:4083` — only `_RUN_RECORD_CHECKPOINT_INTERVAL_S` changed (10.0 → 1.0). Call sites (`data_manager.py:3049`, `3134`, inside `_do_backfill`'s existing per-date loop) are unchanged — confirmed via `grep -n "_checkpoint_run_record(" apps/backend/app/engine/data_manager.py`, which shows the same two pre-existing call sites, no new one added. Same `message` field, same `_run_detail()` serializer, no new field, no second endpoint. Cadence proven by `test_checkpoint_cadence_density_and_throttle_control` (`apps/backend/tests/test_data_manager.py:4457-4547`) and live re-measured in `reports/perf-budgets.md`'s new "Iteration 40" section (12/25 in-memory vs. 11/25 persisted at kill time — a 1-date gap, down from iter-39's order-of-magnitude gap). |
| Page performance budgets (`reports/perf-budgets.md`) | OK | Notes-column-only edits: the trial-3 row and its "Recommendation" paragraph (around line 4996/5019) each gain an inline `**[RETRACTED …]**` note pointing to the new "Iteration 40" section; a new dated section documents the post-fix wedge-recurrence drill and the checkpoint re-measurement. No second budgets file, no new producer. |
| QA-tooling merge headline (`incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py`) | OK (not a Data Contract row) | `parse_rows`/`compute_overall` gain a `BLOCKED` verdict class mirroring `demo_runner.py`'s existing `compute_regression_verdict` priority (FAIL > BLOCKED > PASS > SKIP). This is pipeline/QA tooling that operates on markdown test-result artifacts, not a value the product displays — consistent with the blueprint's own iter-18/23/33 precedent ("a test artifact is not a Data Contract row"). Proven by new unit tests `t_blocked_all_headlines_blocked` (TC-6) and `t_fail_still_wins_over_blocked` (TC-7). |

No new value is displayed anywhere in this iteration (confirmed by the ui-surface-map and the spec's own "New information displayed: None"), so Data Contract rule 4/5 (duplicate-of-existing / unregistered-new) does not apply.

## Information Architecture check

No new page, route, or nav entry. `git diff <snapshot-sha> --stat -- apps/frontend` returns empty —
zero frontend files touched. `reports/phase-goal-ops-hardening-iter-40-ui-surface-map.md` confirms
"Frontend surfaces changed: 0 / New pages/routes: 0 / Navigation changes: no" and lists three
already-shipped, unchanged surfaces (`/data` Run History panel, `/data` Coverage panel, the global
readiness badge) used read-only during live drills — no code or behavior change to any of them beyond
the backend field-cadence/fetch-strategy changes already covered in the Data Contract check above.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| N/A — no new/changed route this iteration | OK | `apps/frontend` diff empty; no nav/sidebar/router file changed |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. This is a clean backend-only correctness/hardening iteration: both touched Data Contract rows
(Coverage payload, Job history) keep their single existing computing module and single existing
serving endpoint, byte-identity is fixture-proven for the diagnostic fetch-strategy change, the
checkpoint-cadence change is a timing-only edit to an already-registered field, and the two tooling/doc
corrections (`merge_ui_test_results.py`, `reports/perf-budgets.md`) are outside the Data Contract by
the session's own established precedent. No IA surface was touched.
