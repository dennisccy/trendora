# Phase goal-mcp-loop-iter-13 — UI Surface Map

**Phase:** goal-mcp-loop-iter-13
**Date:** 2026-07-01
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|---|---|---|---|---|
| `/research/factor-combination` | `CombinationEvidenceBadge` on the composite cohort row (`data-testid="combination-row-composite"`) | New component | The certified rs_spy_3m × high_proximity combination edge must show a referee-gated status badge on the composite row | At `/research/factor-combination` with horizon set to 20, set leg 1 to rs_spy_3m / top / quintile and leg 2 to high_proximity / top / tertile — the composite row badge (`[data-testid="combination-evidence-badge"]`) must show "Proven" and its `data-proven` attribute must be `true`; then change leg 2 to atr_pct and confirm the badge text changes to "Not yet proven" and `data-proven` is `false` with no `<a>` link present |
| `/research/factor-combination` | `CombinationLab` / `CombinationTable` | Changed behavior | The combination lab now fetches the served `GET /api/evidence` claims to power the composite-row badge; the rest of the table is unchanged | Load `/research/factor-combination` and confirm the combination table renders with all its cohort rows and cell data intact; confirm the composite row still shows the NA/low-sample cells that existed before alongside the new badge |
| `/evidence` | 6th `ClaimRow` for the rs_spy_3m × high_proximity combination | New item in existing list | `claimSurface` / `claimAnchorId` now handle a `kind=combination` claim, so the row renders with a correct title and linkback instead of the prior "Unmapped signal" fallback | On `/evidence`, scroll to the last claim row and confirm it carries `id="combination-high_proximity-rs_spy_3m-h20"`, shows hypothesis chips with both `condition` legs (`rs_spy_3m:top:quintile` and `high_proximity:top:tertile`) and `horizon=20`, displays the PASS verdict and holdout edge +4.69%, shows "Backs: Multi-factor combination lab →" as its linkback text (not "Unmapped signal"), and that the five rows above it are unchanged |
| `/evidence` → `/research/factor-combination` | Deep-link from the combination claim's "Backs: Multi-factor combination lab →" linkback | Changed behavior | The combination claim row previously had no specific linkback (fallback "Unmapped signal"); it now has a functioning linkback | On `/evidence`, click "Backs: Multi-factor combination lab →" on the 6th row and confirm the browser navigates to `/research/factor-combination` |
| `/research/factor-combination` → `/evidence#combination-high_proximity-rs_spy_3m-h20` | "Proven" badge deep-link | New user action | The badge provides a direct audit path from the combination lab to the backing evidence row | On `/research/factor-combination` with the certified selection (rs_spy_3m + high_proximity at h20), click the "Proven" badge and confirm the browser scrolls to the correct anchor on `/evidence` — the 6th row with the combination claim should be visible in the viewport |

---

## Backend-Only Changes (No UI Impact)

- `apps/frontend/lib/evidence.test.ts` — +10 combination unit tests for `resolveCombinationEvidence`, `combinationCohortFromClaim`, `claimAnchorId`, and `claimSurface`; no UI surface affected
- `apps/backend/tests/test_evidence.py` — new test-only fixture and combination-payload assertion confirming the 6th canonical ledger entry is served correctly; no UI surface affected
- `apps/backend/tests/test_staging_ledger_routing.py` — two frozen golden assertions updated from 5 to 6 entries to reflect the gate-appended row; no UI surface affected
- `docs/handoffs/goal-mcp-loop-iter-13-dev.md` / `goal-mcp-loop-iter-13-frontend.md` — developer and frontend handoff documentation; no UI surface affected

---

## Summary

- **Frontend surfaces changed:** 2 routes (`/research/factor-combination`, `/evidence`)
- **New pages/routes:** 0 (both routes already existed)
- **Modified components:** 3 (`CombinationLab`, `CombinationTable` in `_labs.tsx`; `ClaimRow` on `/evidence` gains a new row via `lib/evidence.ts` combination branch; new `CombinationEvidenceBadge`)
- **Navigation changes:** no (no new top-level nav link; deep-links exist within existing routes)
- **Backend-only changes:** 4 (2 frontend test files, 2 backend test files — no app code changed)
