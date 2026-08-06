# Iteration 50 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-50
**Date:** 2026-08-06
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

<!-- COHERENCE-WARN: only advisory issues; does NOT block GOAL_ACHIEVED -->

---

## Data Contract check

This iteration is backend-only (confirmed: `git diff` and `git status` show zero files under
`apps/frontend/` touched; the ui-impact-analyst's surface map independently confirms "0 frontend files
modified"). All changed product code (`apps/backend/app/engine/research.py`,
`apps/backend/app/engine/data_manager.py`, `apps/backend/app/engine/warmup.py`) sits inside the
already-registered **Membership timeline / research hot-key caches** row (blueprint.md Data Contract),
which explicitly names `app.engine.research`, `app.engine.forward_testing`, and
`app.engine.data_manager` as its canonical modules.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Factor Lab all-factors table (`compute_factor_lab_all` / `factor_lab_all_cached`) | OK | `apps/backend/app/engine/research.py:656-1348` (bound obs-build via new `_FactorCoreRecords`/`_FactorObsPool`/`_FactorLabAllObs` — same function, same call sites, byte-identity proven by `test_compute_factor_lab_all_matches_pinned_pre_iter50_reference`, `tests/test_research_streaming.py`); served by the SAME `GET /api/research/factor-lab?all=true` route (`apps/backend/app/api/research.py:76-126`, unchanged) |
| Drawdown-expectations warm (`compute_drawdown_expectations_cached`) | OK | `apps/backend/app/engine/data_manager.py:3785-3920` (new warm-in-progress guard) + `apps/backend/app/engine/warmup.py:1101-1145` — pure concurrency control (a `threading.Lock` + counter), no computation added, no second producer; the SAME `compute_drawdown_expectations_cached` (`app.engine.forward_testing`) is the sole call site in both callers |
| `_drawdown_expectations_ledger_needs_recompute` gate | OK | `apps/backend/app/engine/data_manager.py:174-206` — a read-only cache-HIT check against the EXISTING `EventStudyCache` table (no new table, no new derivation); only gates whether `phase_context_by_date` runs, never itself computes drawdown expectations |
| Job history / `aggregates_refreshed` | OK | Unchanged field, unchanged enum; the guard can cause `"drawdown_expectations"` to be honestly *absent* on a rare collision — same nullability contract already documented for this row |
| `by_horizon[].status` / `factors_status` (new sibling fields on `GET /api/research/factor-lab?all=true`) | UNREGISTERED (advisory) | `apps/backend/app/engine/research.py:1324`, `:1339` (per-`(factor,horizon)` `"status": "unavailable"`), `:3910` (whole-response `"factors_status": "unavailable"`) |

**On the UNREGISTERED finding:** this is a genuinely new pair of degrade-signal fields on an
already-registered endpoint, not a duplicate computation and not a second producer/endpoint — it mirrors
the precedent already registered for other rows (`evidence_status` on `/api/backtest`, `expectations_status`
on `/api/evidence`). It is not a Part-A FAIL (no second module/endpoint for any existing value) but it is
also not "just a re-format" — it is new API surface. Two things should be tidied next iteration:
1. Register `by_horizon[].status` / `factors_status` in the Data Contract's Membership timeline row, the
   same way `expectations_status` (iter-29) and `evidence_status` (J-08) were registered when they shipped.
2. The blueprint's own "iter-50 AUDIT-FIX addendum" paragraph (`runs/goal-session-ops-hardening/state/blueprint.md`,
   the paragraph beginning "iter-50 AUDIT-FIX addendum (2026-08-06...") states "no new field ... the Data
   Contract row below is unchanged" — this is factually inconsistent with the diff, which does add the two
   fields above. Correct that paragraph's claim alongside the registration in (1).

Not user-visible today: `apps/frontend/lib/api.ts:1432-1469` (`FactorHorizonDeciles` / `FactorLabAllResponse`)
declares no `status`/`factors_status` field and the frontend is unchanged this iteration (confirmed by the
ui-impact-analyst's surface map), so nothing is mis-displayed — this is a documentation-accuracy /
registration gap, not a "numbers don't match" defect.

## Information Architecture check

No new page, route, or nav entry this iteration (spec's own "Blueprint conformance" / "UI surface changes:
None" is accurate — verified against the diff, not just asserted). No file under
`apps/frontend/components/sidebar.tsx` or any router config changed.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/research/factor-lab` (existing page, reliability fix only) | OK | No new component; `apps/frontend/app/research/factor-lab/page.tsx` and `apps/frontend/components/sidebar.tsx` both untouched (`git diff` — zero hits under `apps/frontend/`) |
| `/data` (warm-guard side effect on the existing Job progress panel) | OK | Same, no new surface |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Unregistered new fields** (see Data Contract table above): `by_horizon[].status` and `factors_status`
  on `GET /api/research/factor-lab?all=true` (`research.py:1324`, `:1339`, `:3910`) should be added to the
  blueprint's Data Contract next iteration, and the blueprint's own "no new field" claim in its iter-50
  AUDIT-FIX addendum paragraph should be corrected to match.
- **Latent UX gap, not this iteration's regression** (flagged independently by the ui-impact-analyst's
  surface map, row 2): when `factor_lab_all_cached`'s new outer `MemoryError` catch degrades the whole
  response (`factors_table: []`, `factors_status: "unavailable"`), the frontend has no field to distinguish
  this from a genuinely empty store and reuses the pre-existing "No forward-tested factors" empty state,
  whose copy implies no data exists rather than "temporarily degraded under load." Cosmetic/UX, not a
  Data-Contract or IA violation — worth a follow-up once the new `factors_status` field is registered and
  wired into the frontend.
- The blueprint's Data Contract table row for "Membership timeline / research hot-key caches" still reads
  "iter-50 (TARGETED, not yet built)" in its per-row Notes cell even though the free-text changelog above the
  table already declares the same work "BUILT" (the audit-fix addendum). Minor documentation-freshness lag,
  not a rule violation — the decomposer should sync the row's own Notes cell wording on its next touch of
  this row.
