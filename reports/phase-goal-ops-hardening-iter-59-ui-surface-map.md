# Phase goal-ops-hardening-iter-59 — UI Surface Map

**Phase:** goal-ops-hardening-iter-59
**Date:** 2026-08-11
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research/regime-lab` | `RegimeLabByLabelTable` ("By regime label" panel, `data-testid="regime-lab-by-label"`) — `RegimeReturnCell`/`RegimeMddCell` in every "Fwd Xd"/"MDD Xd" column | Changed behavior | A horizon that fails to compute under memory pressure now renders as a contained "NA" with a new tooltip instead of the whole page erroring out | Restart the backend with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab` set, load `/research/regime-lab`, and confirm every cell in every "Fwd Xd"/"MDD Xd" column of the "By regime label" table shows "NA" whose `title` attribute (hover tooltip) reads exactly "Temporarily unavailable — degraded under memory pressure" — not a blank cell, not a crashed page, not the old generic NA tooltips |
| `/research/regime-lab` | `RegimeLabDecileTable` ("By regime-score decile" panel, `data-testid="regime-lab-by-decile"`) — `RegimeReturnCell`/`RegimeMddCell` in every "Fwd Xd"/"MDD Xd" column | Changed behavior | Same underlying fix as the by-label table (shared cell components) | With the same fault injected, confirm every "Fwd Xd"/"MDD Xd" cell in every `D1`..`D10` row of the "By regime-score decile" table (`data-testid="regime-decile-table"`) also shows "NA" with the tooltip "Temporarily unavailable — degraded under memory pressure" |
| `/research/regime-lab` | `RegimeLabDecileTable` — Rank-IC header row (`data-testid="regime-decile-rank-ic-row"`) | Known gap (unchanged) | The backend's `rank_ic_by_horizon[].status` field is NOT read by this row's rendering — a disclosed, intentional scope boundary | With the fault injected, hover an "NA" cell in the Rank-IC row and confirm its tooltip is the PRE-EXISTING generic text "Not enough independent observations to rank-correlate — NA, not a fabricated 0" — NOT the new "Temporarily unavailable" wording (regression/gap-confirmation check, not a defect) |
| `/research/regime-lab` | Whole page, non-degraded path (`RegimeLabPage`, `ResearchControls` header "Research — Regime Lab") | Unchanged (byte-identity proven) | The bounding refactor must not change any number when nothing is under memory pressure | With the backend started WITHOUT `TRENDORA_FAULT_INJECT_MEMORY_ERROR` set, load `/research/regime-lab` for a known as-of date and spot-check 2-3 cells' values/tooltips against a pre-phase capture (or re-run before/after the same session) — confirm no new "Temporarily unavailable" text appears anywhere and no numeric value differs |
| `/research/regime-lab` | `RegimeLabPage` error path (`ResearchError`, "Backend unavailable" card) | Changed trigger condition (component itself unchanged) | This specific memory-pressure cause of the generic error card is now avoided — the card should no longer appear for this cause, though it remains reachable for other backend-down causes | With the fault injected (all horizons degrading), confirm the page does NOT show the red "Backend unavailable" error card / "Retry" button — it must show the normal tables with per-cell NA markers instead |
| (supporting, no direct visual) | `apps/frontend/lib/api.ts` — `RegimeLabHorizonCell.status?` / `RegimeLabResponse.regime_lab_status?` TypeScript fields | Type change (additive) | Lets the two table components above read the backend's new optional fields | Covered by the row above; independently confirm via DevTools Network tab that a degraded response's JSON body contains `"regime_lab_status": "unavailable"` and `"status": "unavailable"` on the affected `by_horizon[]` entries |

<!-- Change Type key used above: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal | Known gap (unchanged) | Unchanged (byte-identity proven) -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` — `compute_regime_lab` restructured to build, aggregate, and
  release ONE horizon's observation pool at a time (instead of holding every configured horizon's pool in
  memory simultaneously), with a `time.sleep(0)` cooperative yield per horizon. This is the memory-bounding
  fix itself; it has no UI surface of its own and is only observable indirectly through the degraded-cell
  rendering captured in the rows above, and only when the underlying memory condition actually occurs.
- `apps/backend/app/engine/research.py` — `_degrade_regime_lab_horizon` (new private helper) and the
  per-horizon `try/except MemoryError` / `except Exception` isolate-and-continue wrapping. Internal
  reliability logic; surfaces to the UI only via the `status`/`regime_lab_status` fields already covered
  above.
- `apps/backend/app/engine/research.py` — `regime_lab_cached`'s new never-cache-a-degraded-payload guard
  (a degraded response is served to the caller but never persisted to `EventStudyCache`). No direct UI
  surface; it prevents a stale degraded state from being served again after memory pressure clears, which
  is a correctness property of the API, not something a user directly sees or interacts with.
- `apps/backend/app/engine/data_manager.py` — `"regime_lab"` added to `_FAULT_INJECT_SITES`, the
  test-only/env-var-gated `TRENDORA_FAULT_INJECT_MEMORY_ERROR` hook used to deterministically reproduce the
  degrade path in tests and in the manual verification steps above. No UI impact by itself — it is a test
  seam, not a product surface.
- `apps/backend/tests/test_regime_lab.py`, `apps/backend/tests/test_api_research.py` — new/changed unit and
  HTTP-level tests (byte-identity fixture, fault-injection isolate-and-continue tests, never-cache-degraded
  test). No UI impact — test code only.
- J-05 step 3 (backend `kill -9` + `scripts/start-backend.sh` restart, then a cold load of `/data`,
  `/scanner-runs`, and the home market-phase card) was executed and verified live this iteration, but **no
  frontend or backend code for those pages was changed** — this is a live verification of already-shipped,
  previously-built behavior (iter-8/iter-9), not a UI change from this phase's diff. Not included as a
  surface-map row for that reason; browser-QA's own functional test plan for J-05 covers it separately.

---

## Summary

- **Frontend surfaces changed:** 1 (`/research/regime-lab` — two tables share the same underlying cell
  components)
- **New pages/routes:** 0
- **Modified components:** 2 (`RegimeLabByLabelTable`, `RegimeLabDecileTable`, via their shared
  `RegimeReturnCell`/`RegimeMddCell`/`regimeCellIsNa`/`regimeNaTitle` functions in `_labs.tsx`) + 1
  supporting type-only file (`lib/api.ts`)
- **Navigation changes:** no
- **Backend-only changes:** 6 (memory-bounding refactor, isolate-and-continue wrapping, never-cache-degraded
  guard, fault-injection site registration, two test files, and the code-unchanged J-05 restart
  verification)
