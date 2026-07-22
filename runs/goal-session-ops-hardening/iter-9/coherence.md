# Iteration 9 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-9
**Date:** 2026-07-22
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

Diff reviewed: `git diff 16c5be6f90250020385995410958e3f9ed98c3f5` (noise-excluded) — 6 files changed:
`apps/backend/app/engine/data_manager.py`, `apps/backend/tests/test_data_manager.py`,
`apps/backend/tests/test_data_manager_jobs_pipeline.py`, `apps/backend/tests/test_start_backend_script.py`,
`incredible_auto_dev/scripts/dev.sh`, `incredible_auto_dev/scripts/start-backend.sh` (== `scripts/dev.sh` /
`scripts/start-backend.sh` at the repo root — those are symlinks into `incredible_auto_dev/`, confirmed via
`ls -la`). Zero `apps/frontend/*` files appear in the diff, matching the ui-surface-map's "Frontend surfaces
changed: 0" claim (independently confirmed: `git diff <sha> --stat -- apps/frontend` is empty).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Job history & per-date exclusion reasons (`_run_detail()` blob on `data_provider_runs.message`) | OK | New `_checkpoint_run_record()` (`apps/backend/app/engine/data_manager.py:3668-3708`, plus a second call site added at the dev handoff's own "AUDIT (F1 completion)" point before the bar-cache prefill) writes `message` by calling the pre-existing, single `_run_detail()` function (defined `data_manager.py:3573`, already the sole serializer used by `_create_run_record` and `_finalize_run_record`). No new field: `dates_done`/`dates_total`/`snapshots_created` etc. were already keys of `_run_detail()`'s dict (confirmed at `data_manager.py:3589-3592`) — this iteration only adds an additional throttled *write* of the identical derivation, mid-run instead of only at creation/finalize. Same table (`data_provider_runs`), same two read endpoints (`GET /api/data`, `GET /api/data/jobs/{job_id}`), no second derivation, no new DB column. Consistent with this row's own blueprint note ("Reads the SAME `_run_detail()`/`JobProgress` mechanism — no new DB column, no second record") and the established precedent (iter-2/iter-5/iter-7 all moved warm/write TIMING earlier through an already-registered single function). |
| Backfill run-summary contract (`aggregates_refreshed`, `dates_total`, etc.) | OK | Same `_run_detail()` path as above; the new tests (`test_data_manager_jobs_pipeline.py:+254..380`) assert the checkpointed values equal the same fields the existing contract already defines (`dates_total`, `calendar_days`, `snapshots_created`, `aggregates_refreshed is None` on an unfinalized row) — no new field, no relaxed nullability gating (`_breakdown_computed` gate at `data_manager.py:3585` untouched). |
| `_release_process_memory()` internal helper (libc `malloc_trim`) | OK — not a Data Contract value | `_resolve_libc_malloc_trim()` (`data_manager.py:2729-2739`) memoizes a process-internal cleanup helper. Not served by any endpoint, not displayed anywhere, not a row in the blueprint's Data Contract table. No violation possible. |
| AG-10 launcher caps (`taskset`/`OMP_NUM_THREADS`/etc.) | OK — not a Data Contract value | `incredible_auto_dev/scripts/start-backend.sh:+68-95` and `scripts/dev.sh:+44-79` read every value from `project-extensions/host-guard/host-guard.env` (no hardcoded numbers) and apply it only around the exec'd backend process. Launch-script/operational, explicitly out of the Data Contract per the blueprint's own iter-9 framing note. No second computation of `memory_cap_mb`/`malloc_arena_max` — `dev.sh`'s new block reads them via the same `app.config.get_config()` call `start-backend.sh` already used. |

No new displayed value/entity appears anywhere in this diff (confirmed: zero frontend files changed, so
nothing new can be rendered to a user this iteration).

## Information Architecture check

No new page, route, or nav-reachable feature this iteration (confirmed by the ui-surface-map's own summary:
"New pages/routes: 0", "Navigation changes: no" — and independently, zero files under `apps/frontend/`
appear in the diff, so no nav/sidebar/router file could have changed). All test and launch-script changes are
backend/tooling-only.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new route this iteration) | OK | n/a |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The blueprint's iter-9 update paragraph (`runs/goal-session-ops-hardening/state/blueprint.md`, the
  paragraph beginning "iter-9 update (session-closeout verification + AG-10 launcher compliance)") documents
  the test-tightening and the libc-memoization but does not mention the mid-backfill checkpoint fix
  (`_checkpoint_run_record`, `data_manager.py:3668-3708`, plus the pre-loop checkpoint call the iteration's
  own audit added) that the diff actually ships, even though the dev handoff and audit report both label it
  "F1 / J-04 step 6." This is not a Data Contract violation — it reuses the single canonical `_run_detail()`
  derivation and the single existing `message` field/table/endpoints, so no second source was created — but
  every prior iteration's blueprint paragraph in this file meticulously names each behavioral change to the
  registered rows, and this one is a gap in that pattern. Recommend the next iteration (or a quick blueprint
  edit) add one sentence to the "Job history & per-date exclusion reasons" row's Notes column: the row's
  `message` field is now also checkpointed mid-run (throttled, via the SAME `_run_detail()`), not written
  only at creation/finalize — so a future reader does not have to reconstruct this from the code diff.
- Unrelated to coherence, noted only for completeness since it surfaced while tracing evidence: the
  project's `scripts/` directory at the repo root is a symlink to `incredible_auto_dev/scripts/` (`ls -la`
  confirms), which is why `git status` shows the changed launcher scripts under
  `incredible_auto_dev/scripts/*` rather than `scripts/*` even though the iteration spec and blueprint refer
  to them by their `scripts/*` path. Both paths resolve to the identical file; no discrepancy in the actual
  change.
