# Iteration 43 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-43
**Date:** 2026-08-03
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration is backend/tooling-only (`Frontend Present: no`, confirmed by
`reports/phase-goal-ops-hardening-iter-43-ui-surface-map.md`: "N/A — Backend-only phase... No UI
surfaces affected"). Per the iter spec's own "Data-contract additions: None" and "Blueprint
conformance" fields, every touched value is an implementation-only change to an already-registered
row — verified directly against the diff (`git diff 9165b2eac6cb2d3d6428e913dc611da87c055b6a`):

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Job history & per-date exclusion reasons (`GET /api/data`, `GET /api/data/jobs/{job_id}`) | OK | `apps/backend/app/engine/data_manager.py:4159-4190` (`_finalize_run_record`, unchanged) is the SAME sole writer `_fail_unlaunched_job`/`_fail_unlaunched_resume` (new, ~4665-4735) call for the new thread-launch-failure path — traced: `_fail_unlaunched_job` → `_finalize_run_record` → `_run_detail()` (same function every other job status/message already serializes through, `data_manager.py:3976`). No second writer, no second endpoint. |
| Job history `summary`/`message` field | OK (reformat, not new value) | `data_manager.py` `_run_detail()` (~line 4032-4041 post-diff): on a terminal `failed` row with a `prog.message`, serves `prog.message` instead of `_final_summary(prog)` — same existing `summary` field, same function, same two serving paths (`GET /api/data`, `GET /api/data/jobs/{job_id}`); confirmed `summarize_provider_run` (`data_manager.py:4827`, the sole reader for `GET /api/data`'s history list) is untouched by this diff and reads the same persisted JSON blob. Not a new field. |
| Coverage payload / `_BarCache.prefill` (`GET /api/data`) | OK | `apps/backend/app/engine/prices.py:239-294` — reverts the iter-42 `WHERE symbol IN (...)` filter back to the pre-iter-42 unconditional whole-table scan inside the SAME `_BarCache.prefill` method; no new computing module, no new endpoint, `_SymbolColumns`/NULL-sentinel handling untouched. Matches the spec's "same computing module (`app.engine.data_manager`, `_compute_coverage_uncached`), same endpoint" framing — `prefill` is a sole internal helper, not a second producer. |
| Job launch (`POST /api/data/jobs`, `POST /api/data/jobs/{import_id}/resume`) | OK | `apps/backend/app/api/data.py:191-203, 265-272` — wraps the EXISTING `data_manager.start_data_job`/`start_resume_job` calls in `try/except (RuntimeError, MemoryError)` and raises `HTTPException(503, ...)`; no new endpoint, no new job-launch code path — same two routes, same two `data_manager` entry points. |
| Page performance budgets (`reports/perf-budgets.md`) | OK | New "## Iteration 43" section (append-only, same single artifact); no second budgets file, no code change to any measured row's producer/endpoint (verified: the section's own text describes measuring against the already-registered mechanisms, not a new one). |

No new displayed value or entity is introduced this iteration (spec's "New information displayed:
None new" is accurate against the diff — the thread-launch failure surfaces through the Job history
row's pre-existing `status`/`message` fields only, no new field name).

## Information Architecture check

No new page, route, or nav entry. Confirmed two ways:
1. The UI surface map declares this a backend-only iteration with no UI surfaces affected.
2. `git diff --stat` against the snapshot SHA touches only `apps/backend/app/api/data.py`,
   `apps/backend/app/engine/data_manager.py`, `apps/backend/app/engine/prices.py`, three backend test
   files, `apps/frontend/tsconfig.json` (a build-config include-list reorder, not a page/component —
   `test_start_frontend_script.py`'s own docstring explains this as a real `next build`'s
   auto-rewrite that the test fixture snapshot/restores), and two ops scripts
   (`incredible_auto_dev/scripts/start-frontend.sh`, `project-extensions/host-guard/host-guard.env`).
   No frontend component, page, or router file changed.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new feature/route this iteration) | OK | `reports/phase-goal-ops-hardening-iter-43-ui-surface-map.md` (no frontend files in diff to cross-check against `apps/frontend/components/sidebar.tsx`) |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. The `_run_detail()` "summary" field change is a same-field reformat (prefers
  `prog.message` over `_final_summary(prog)` only on a terminal `failed` row that already has a
  message) — traced to a single caller chain with no divergence, so it does not rise even to an
  advisory "formatting drift" note.
- `apps/frontend/tsconfig.json`'s reordering of `.next-alt-qa`/`.next-verify`/`next-env.d.ts` entries
  is mechanical build-artifact churn (per `test_start_frontend_script.py`'s own documented
  autouse-fixture snapshot/restore behavior around real `next build` runs), not a product change —
  noted only for completeness, not a coherence concern.
