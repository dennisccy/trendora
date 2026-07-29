# Phase goal-ops-hardening-iter-29 — UI Surface Map

**Phase:** goal-ops-hardening-iter-29
**Date:** 2026-07-27
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/evidence` | `DrawdownExpectationsPanel` inside `ClaimRow` (`apps/frontend/app/evidence/page.tsx`); `resolveDrawdownExpectationsPanelState` + `CertifiedClaim.expectations_status` (`apps/frontend/lib/evidence.ts`) | Changed behavior (new rendered state, `"unavailable"`) | AG-8 fix: a per-claim drawdown-expectations compute failure is now caught server-side (`build_evidence_payload` in `apps/backend/app/engine/evidence.py`) and surfaced honestly instead of being silently indistinguishable from "not applicable" | Force one claim's `expectations_status` to `"unavailable"` — either by monkeypatching `compute_drawdown_expectations_cached` to raise on the backend and reloading `/evidence`, or by intercepting the `/api/evidence` network response in devtools and injecting `"expectations_status": "unavailable"` with no `expectations` key on one claim. Verify: (a) that one claim's card shows the heading "Historical drawdown & dry-spell expectations" and the exact text "Unavailable — monitored and refreshed as new data arrives." in faint/muted (not red/error) styling, with a `[data-testid="evidence-expectations-unavailable"]` element present; (b) every other claim's card still renders its own panel state (table or blank) completely unaffected. |
| `/evidence` | Full page load / all claim cards (`apps/frontend/app/evidence/page.tsx`) | Changed behavior (failure isolation — reliability) | Backend per-claim isolate-and-continue guard (Fix 2, `evidence.py`) means one claim's compute failure can no longer fail the whole `GET /api/evidence` request | Load `/evidence` against the live backend (7-claim ledger: `leadership_score`/20, `ma_stack`/20, `vcp_contraction`/20, `vcp_contraction`/60, `rs_spy_3m`/60, one combination claim, one event-study claim). Confirm HTTP 200 and all 7 claim cards render (not a blank page or Next.js error overlay). Tail `logs/backend.log` across the request window and confirm zero `MemoryError` / "Exception in ASGI application" lines. As of the developer's own last check, all 7 claims currently resolve successfully (every card shows the full expectations table, none shows "Unavailable") — treat any card unexpectedly showing "Unavailable" or a blank panel as a regression to investigate, not an expected state. |
| `/evidence` | Existing "present" panel state — full deciles-by-phase / underwater / time-to-recover / loss-streak table, on each of the 5 `kind="factor"` claim cards | No visible change (regression guard) | The panel now branches through the new `resolveDrawdownExpectationsPanelState` resolver instead of a plain null-check; the pre-existing "present" rendering path must stay byte-unchanged | Open each factor-kind claim's card on `/evidence` and confirm the full table (with decile rows, underwater stats, time-to-recover, and loss-streak figures) still renders with real numeric values exactly as before — no missing rows, no layout shift, no new note alongside the table. |
| `/research/factor-lab` | Decile table + rank-IC figures (`apps/frontend/app/research/factor-lab/page.tsx`, backed by `GET /api/research/factor-lab` → `compute_samples` → `apps/backend/app/engine/research.py:_factor_observations`) | Changed behavior (regression check only — byte-identical output required) | `_factor_observations`'s join accumulator was rewritten to process data in bounded chunks instead of one unbounded in-memory map; TC-2/TC-9 require the displayed values to be byte-identical to before | On `/research/factor-lab`, select a factor/horizon combination (e.g., `leadership_score` at horizon 20) and submit. Verify the decile table renders non-empty rows with real numeric mean-return and mean-max-drawdown values (not blank cells or zeros-only), a real rank-IC value is shown, and the browser console shows no error. Expect the request to take up to roughly a minute on the deep basis (pre-existing, uncached-by-design Factor Lab behavior, not a regression introduced this iteration) — do not treat that latency alone as a failure. |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_research_streaming.py` — new unit tests (`chunked_accumulator_engine` fixture,
  chunk-boundedness spy, byte-identity/as-of-cutoff assertions) proving the accumulator fix at the code
  level — test coverage only, no UI surface affected.
- `apps/backend/tests/test_evidence.py` — new unit test (`evidence_dd_two_claims_engine` fixture,
  monkeypatched-failure assertion) proving the per-claim isolation fix at the code level — test coverage
  only, no UI surface affected.
- `apps/frontend/lib/evidence.test.ts` — new unit test cases for `resolveDrawdownExpectationsPanelState`
  (present / unavailable / absent / distinctness) — test coverage only; the logic itself is already captured
  in the `/evidence` rows above.

<!-- research.py and evidence.py (production engine files) are intentionally NOT listed here: research.py's
     memory-bounding change and evidence.py's isolate-and-continue guard both have real (if narrow) UI
     surface consequences, captured in the rows above rather than treated as no-impact. -->

---

## Summary

- **Frontend surfaces changed:** 1 (`/evidence` — the `DrawdownExpectationsPanel` and its supporting
  resolver/type). `/research/factor-lab` is unchanged in its own code but requires regression verification
  because it shares the rewritten backend function.
- **New pages/routes:** 0
- **Modified components:** 2 (`DrawdownExpectationsPanel` in `apps/frontend/app/evidence/page.tsx`;
  `CertifiedClaim` type + new `resolveDrawdownExpectationsPanelState` helper in `apps/frontend/lib/evidence.ts`)
- **Navigation changes:** no
- **Backend-only changes:** 3 (test files only — see above)
