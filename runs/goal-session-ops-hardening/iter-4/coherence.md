# Iteration 4 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-4
**Date:** 2026-07-20
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Backend readiness / boot phase + preflight verdict (`state`, new sibling `detail`) | OK | Same module widened in place: `apps/backend/app/engine/readiness.py:78` (`_latest_benchmark_bar_date`, a private helper — not a second producer), `:131-236` (`compute_readiness` returns the widened `{state, detail, warmup}` dict, `AWAITING_SNAPSHOT` added to the existing enum at `:62`). Same endpoint wired additively: `apps/backend/app/api/health.py:92-95` (`readiness_detail` reads `readiness.get("detail")` from the SAME `compute_readiness` call already in scope — no second call, no new route). Frontend reads the SAME payload: `apps/frontend/lib/api.ts:118` (`ReadinessState` widened, not duplicated), `apps/frontend/components/health-badge.tsx:74-84` (new render branch off the existing `useReadiness()`/`fetchHealth()` — `apps/frontend/lib/api.ts:177` confirms `fetchHealth` still hits only `/api/health`). `compute_preflight`'s `servability` derivation is untouched (`!= UNAVAILABLE` check unchanged) and is re-pinned by a new test rather than re-derived. Blueprint's Data Contract row was amended in place (`runs/goal-session-ops-hardening/state/blueprint.md`, "Backend readiness…" row) to document both fields — no new row. |
| Job history & per-date exclusion reasons (`JobProgress` heartbeat) | OK | `apps/backend/app/engine/data_manager.py:3038` (`prog.tick()` added at the start of `_refresh_ingest_aggregates`), `:3018` (bare `prog.tick()` added inside `_persist_per_date_coverage_snapshots`'s per-date loop, `prog` newly threaded as a parameter at the same call site, `:3092`), `:3102` (per-date tick in the market-phase warm loop). All three calls stamp the EXISTING `JobProgress.last_progress_at` heartbeat field the main scan loop already ticks at `data_manager.py:2863` — no new field, no new table, no second computation of job-progress state. Confirmed unregistered-value-free: `grep` for `awaiting_snapshot`/`AWAITING_SNAPSHOT` across `apps/backend` and `apps/frontend` shows it appears ONLY in `readiness.py`, `health.py`, `lib/api.ts`, `health-badge.tsx`, and their tests — one producer, one consumer path, one literal spelling everywhere. |

No other Data Contract row is touched by this iteration's diff (`git diff` against the pre-iteration snapshot SHA touches exactly: `README.md`, `apps/backend/app/api/health.py`, `apps/backend/app/engine/data_manager.py`, `apps/backend/app/engine/readiness.py`, `apps/backend/tests/test_data_manager.py`, `apps/backend/tests/test_readiness.py`, `apps/frontend/components/health-badge.tsx`, `apps/frontend/lib/api.ts`, `apps/frontend/tsconfig.json`, plus the blueprint/state/harness bookkeeping files). No new displayed value/entity outside the Data Contract was introduced (the `detail`/`readiness_detail` string is a sibling field on the already-registered readiness row, pre-declared in the iteration spec's "Data-contract additions" section and reflected in the blueprint edit before this audit ran).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Global readiness badge — new `awaiting_snapshot` 4th pill state | OK | `apps/frontend/components/health-badge.tsx` is the pre-existing, single `HealthBadge` component mounted once in the root layout (confirmed via the ui-surface-map: "mounted once in `app/layout.tsx`"); this iteration adds one `else if` render branch (`:74-84`), not a new component or page. 0 clicks (ambient, global, every page) — well within the ≤2-click bar. No new nav entry, no new route, no `blueprint.reapproval-requested` file was written (checked: absent from `runs/goal-session-ops-hardening/state/`). |
| `/data` job-progress heartbeat fix (F1) | OK | Surfaces on the pre-existing `JobProgressPanel` on `/data`, reached via the existing 1-click "Data Manager" sidebar entry (unchanged nav skeleton per `blueprint.md`'s Information Architecture section; independently confirmed in `reports/reviews/goal-ops-hardening-iter-4-review.md:28,34`). No new panel, no new page. `apps/frontend/app/data/page.tsx` has zero diff against the snapshot SHA — the fix is entirely a backend heartbeat-timing correction (`data_manager.py`), not a new frontend surface. |

`git status --porcelain apps/frontend/app/` is empty — no new route/page file was added anywhere in the frontend app directory. The ui-surface-map (`reports/phase-goal-ops-hardening-iter-4-ui-surface-map.md`) independently confirms "New pages/routes: 0" and "Navigation changes: no," and the reviewer's report confirms `navigation_updated: n/a`. This matches the iteration spec's own "Blueprint conformance" claim verbatim.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Accent-color overlap (Part C, visual only):** the new `awaiting_snapshot` pill reuses the existing `Badge` `accent` variant, which is also used by the adjacent "provider" metadata badge next to it in the header — so the two are the same color even though they are semantically distinct signals. This is exactly what the iteration spec asked for ("reuse an existing Badge variant, e.g. `accent` — no new color token"), so it is not a spec deviation; it is a cosmetic distinctiveness observation only. Already independently flagged non-blocking by the audit (finding F1) and the ux-regression reviewer's "Visual Consistency" note, and dispositioned as a future polish item in the closure verdict — carried forward here as a Part C note, not a new finding, and does not change this verdict.
- **`tsconfig.json`'s widened `include` glob** (adds `.next-alt-qa/types/**/*.ts` for a gitignored alternate QA build directory) is build-tooling only — zero product-runtime surface, no displayed value, no nav — outside this gate's scope; already noted non-blocking by the audit (finding F2).
