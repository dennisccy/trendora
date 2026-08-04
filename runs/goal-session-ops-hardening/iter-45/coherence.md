# Iteration 45 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-45
**Date:** 2026-08-04
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

The only Data Contract row this iteration's diff touches is "Membership timeline / research hot-key
caches" (blueprint.md:404: canonical module `app.engine.data_manager` — `_membership_timeline`,
`_excluded_counts_by_date`, `membership_timeline_cached`; canonical tables `membership_timeline_cache`,
`event_study_cache`; serving paths `/data`, `/sectors`, `/themes`, `/research/*`, `/evidence`). The
iter-45 spec's "Data-contract additions" field states "None" — this is an implementation-only change to
that already-registered row, and the diff bears that out.

All four new functions the diff adds live inside `app.engine.data_manager` and are private helpers that
feed the SAME canonical entry point, never a parallel one:

- `_parse_membership_stamp` (data_manager.py, new) — decomposes the existing `_membership_dataset_version`
  stamp string; pure parsing, no independent computation of membership/exclusion values.
- `_membership_bars_are_forward_only` (data_manager.py, new) — a precondition check (audit fix B4) that
  gates when the fast path is safe; reads `DailyPrice` only to prove non-interference, does not compute
  `excluded`/`entries`/`exits` itself.
- `_membership_timeline_incremental` (data_manager.py, new) — the append-forward fast path. Its own
  docstring states it is "byte-identical to `_membership_timeline`... for the SAME dates"; it reuses every
  cached point verbatim and calls the SAME `_excluded_counts_by_date`/`resolve_with_reasons` chain only
  for new dates. This is the fast branch of the existing canonical function, not a second producer.
- `_log_isolation_failure` (data_manager.py, new) — a logging-safety wrapper, not a data-value computation.

`membership_timeline_cached` (data_manager.py:816-869 in the diff) is edited to try the incremental path
first and fall back to the pre-existing, unchanged `_membership_timeline(session, cfg, snapshot_dates)`
call on any non-append-forward case (first compute, historical gap-fill, missing cached date, or a
`min_history_bars` re-basis) — confirmed by reading the diff hunk directly (`/tmp` scratch copy of
`git diff 63cb40b7... -- apps/backend/app/engine/data_manager.py`, hunk at old line 662). No second
endpoint, no second table, no schema change, no new field on the served payload (`candidate_pool_count`,
`points`, `labels` — unchanged shape). `grep -n "^+.*def \|^+.*@app\.\|^+.*@router" ` over the diff
confirms zero new route/endpoint definitions.

The only other product-code touch is `_log_isolation_failure`'s substitution for bare `logger.exception()`
calls across ~16 existing per-item isolation handlers inside `_refresh_ingest_aggregates`,
`_persist_per_date_coverage_snapshots`, `_do_backfill`, `_run_job`, and `_fail_unlaunched_job` (closing the
reviewer/audit's third `MemoryError`-in-logging escape). This changes failure-handling/logging behavior
only — it does not touch any Data Contract row's computed value.

The non-product changes (`incredible_auto_dev/scripts/automation/lib/demo_runner.py`'s PNG-provenance
stamping for evidence screenshots, `journey-scripts/J-07.json`'s anchor refresh `n=8878→14647` /
`3508→2532`) are QA-tooling/test-fixture artifacts, not served Data Contract values — matches this
session's own established iter-18/23/33 precedent (recorded in blueprint.md) that pipeline artifacts are
out of Data Contract scope.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Membership timeline (size/entries/exits/excluded per date) | OK | `apps/backend/app/engine/data_manager.py` — new helpers feed the same `membership_timeline_cached`; fallback still calls the unchanged `_membership_timeline` |
| research hot-key caches (`event_study_cache`) | OK (untouched) | not touched by this diff |
| Job history / `aggregates_refreshed` | OK (untouched) | only the logging call sites inside the existing per-item handlers changed |

## Information Architecture check

Iter-45 spec: "Frontend Present: no" / "UI surface changes: None." `git diff --stat` against the
snapshot SHA confirms zero frontend files changed (only `apps/backend/app/engine/data_manager.py`,
`apps/backend/tests/test_data_manager.py`, and
`incredible_auto_dev/scripts/automation/lib/demo_runner.py`).
`reports/phase-goal-ops-hardening-iter-45-ui-surface-map.md` independently states "N/A — Backend-only
phase (Frontend Present: no) / No UI surfaces affected." No new page, route, or nav entry was introduced,
so there is nothing to check against `sidebar.tsx`/the router.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — backend-only iteration) | OK | ui-surface-map.md confirms no UI surfaces changed; git diff --stat shows no frontend files touched |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The iteration's own audit (`docs/handoffs/goal-ops-hardening-iter-45-audit.md`) returned a hard **FAIL**
  on functional grounds — J-05 and J-07 both failed live, and the audit notes the new fast path was never
  actually exercised in the live run because the finalize hook is unreachable for a job that dies with an
  uncaught `MemoryError` first. That is a goal-achievement finding for the evaluator, not a coherence
  finding: the fast path itself, as built, still routes through the single registered canonical module and
  introduces no second source, so it does not trigger a Data Contract or IA violation regardless of
  whether it was exercised live this iteration.
- The blueprint's Data Contract row (blueprint.md:404) still carries the iter-45 entry as "TARGETED this
  iteration, not yet built" pending live proof at scale — consistent with the audit's finding that the
  fast path has only 4-date fixture coverage so far, not a live ~2,860-date exercise. Nothing to fix on
  this pass; the next iteration's decomposer/evaluator should keep the tag until a genuine append-forward
  ingest is observed live.
