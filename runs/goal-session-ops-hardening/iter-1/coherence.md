# Iteration 1 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-1
**Date:** 2026-07-19
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Backfill run-summary contract — `dates_total` (redefined), `calendar_days`, `non_trading_days`, `already_snapshotted`, `error_other` | OK | Computed once in `_do_backfill`: `apps/backend/app/engine/data_manager.py:2549-2551,2557,2581,2733`. Served two ways from the SAME `prog` fields, never re-derived: live via `JobProgress.to_dict()` (`data_manager.py:1780-1786` per diff) and persisted via `_run_detail()` (`data_manager.py:3004,3017,3024-3027`) → `summarize_provider_run()` (`data_manager.py:3598` region, per diff lines 410-416). Matches blueprint.md's registered canonical module (`app.engine.data_manager` / `_do_backfill`) exactly. |
| Job history & per-date exclusion reasons | OK | Same evidence as above — `GET /api/data` (`apps/frontend/lib/api.ts:2621-2623`, `fetchDataCoverage`) serves the persisted `runs` list; `GET /api/data/jobs/{job_id}` (`api.ts:2719-2722`, `fetchDataJob`) serves the live poll. Frontend: `state.data.runs` feeds both `RunHistoryPanel` (`apps/frontend/app/data/page.tsx:580`, pre-existing) and the new `JobProgressPanel`'s `runs` prop (`page.tsx:559`) → `LastRunSummary` reads `runs[0]` (`page.tsx:2607`). `job` state is populated from `fetchDataJob`'s poll (unchanged call site). No new fetch call was added anywhere in the diff — confirmed via `git diff --stat` on `apps/frontend/lib/api.ts` (interface-only additions, no new exported function). |
| Candidate second-source check: `dates_total` | OK — not a violation | `grep -rn "dates_total\s*="` across `apps/backend/app/` (excluding tests) also matches `apps/backend/app/engine/warmup.py:133` and `:210`. Inspected: this is the pre-existing (iter-28, J-40/J-41) boot-time historical warm-up job, `kind="warmup"` (`warmup.py:44,208`), a distinct, unrelated job registered under a sentinel `start=end=date_cls.min` (`warmup.py:208`) — not `backfill`/`both`/`rebuild`, never surfaced through `GET /api/data`'s persisted `runs` list (only the Data Manager job kinds populate `data_provider_runs`). `warmup.py` is untouched by this iteration's diff. This is a pre-existing, conceptually distinct reuse of the same struct/field name for an unrelated concept (boot cadence catch-up count vs. this iteration's backfill run-summary), not a duplicate computation of the registered "Backfill run-summary contract" value. |
| New value check | OK — none unregistered | All four new fields (`calendar_days`, `non_trading_days`, `already_snapshotted`, `error_other`) are pre-registered in `blueprint.md`'s Data Contract as `[TARGET, iter-1 building]` rows; this iteration builds exactly what was already contracted, nothing extra. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` — Job progress panel fallback (`LastRunSummary`), breakdown display (`BackfillBreakdown`), zero-work badge/note, chunk progress for backfill | OK | No new route. `git diff --stat` confirms zero changes to `apps/frontend/components/sidebar.tsx` or `apps/frontend/app/layout.tsx`. All new components live inside the existing `apps/frontend/app/data/page.tsx` and reuse the page's existing `Card`/`PanelTitle`/`Badge` primitives (`page.tsx:2513-2577`) — no parallel shell. Matches blueprint.md's IA row: Data Manager (`/data`) is already the canonical home for J-01/J-03, and the iteration spec's "Blueprint conformance" field confirms "no new page, no nav change." |
| `/scanner-runs` — gains newly-visible dates | OK | Consequential only: the page/component itself has zero diff (confirmed via `git diff --stat`, not in the changed-file list); it now renders rows for dates the backfill fix actually created snapshots for. Same existing route, same existing data-fetch path. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The zero-work explanatory paragraph (`data-testid="zero-work-note"`, `apps/frontend/app/data/page.tsx` in the live `JobProgressPanel` branch) renders only in the live in-session job view — it is not repeated in `LastRunSummary`'s reduced fallback view or in `RunHistoryPanel`'s compact table rows. The essential fact (this was zero-work, not a failure) IS consistently conveyed everywhere via the shared `runStatusVariant`/`runStatusLabel` badge helpers (`page.tsx:460-491`), so this is a defensible depth-of-explanation choice for a compact/secondary surface rather than drift — noted for awareness only, no fix required.
