# Phase goal-mcp-loop-iter-4 — UI Surface Map

**Phase:** goal-mcp-loop-iter-4
**Date:** 2026-06-30
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/evidence` | `ClaimRow` — regime badge | New component element | Regime-conditioned claims must be clearly labeled with the regime they hold in (J-04) | On the Evidence page, scroll to the second claim row (Breakout-watch); confirm a "Regime: Risk-on" badge is visible in the row header beside the "PASS" verdict badge |
| `/evidence` | `ClaimRow` — claim title (non-score row) | Changed behavior | The signal-null event-study claim previously showed the developer placeholder "Unmapped signal"; it must now show the subject name | On the Evidence page, locate the Breakout-watch row; confirm the row title reads "Breakout-watch setup", not "Unmapped signal" |
| `/evidence` | `ClaimRow` — claim subtitle (non-score row) | New component element | An honest framing line for regime-conditioned evidence was missing | On the Evidence page, Breakout-watch row; confirm the subtitle "Out-of-sample edge in the Risk-on regime" is visible beneath the title |
| `/evidence` | `ClaimRow` — linkback (non-score row) | Changed behavior | The old linkback "Backs: Stocks leaderboard →" was inaccurate for a setup claim that backs no score; the correct target is the Research event-study lab | On the Evidence page, Breakout-watch row; confirm the linkback reads "Backs: Research event-study lab →" and clicking it navigates to `/research/event-study`, not `/stocks` |
| `/evidence` | `ClaimRow` — leadership row (score row, regression check) | No change (regression guard) | The score row must remain byte-identical; a regime badge must NOT appear on it | On the Evidence page, confirm the first (leadership_score) row shows no "Regime:" badge, still reads "Backs: Stocks leaderboard →", and displays "+6.36%" and "PASS" unchanged |
| `/` (Dashboard) | `RegimeGlanceCard` — Evidence affordance link | New component element | Users needed a discoverable path from the current-regime display to the regime-conditioned evidence (J-04 flow) | On the Dashboard, in the Market Regime card, confirm a "See evidence proven in this regime →" link is present below the component-breakdown disclosure; confirm clicking it navigates to `/evidence` |
| `/` (Dashboard) | `RegimeGlanceCard` — regime label and number (regression check) | No change (regression guard) | The regime score (76.05) and label (Risk-on) must be unchanged by the new affordance addition | On the Dashboard Market Regime card, confirm "Risk-on" and "76.05" still display correctly alongside the new link |

---

## File Classification

| File | Category | UI Impact |
|------|----------|-----------|
| `apps/frontend/lib/evidence.ts` | frontend-direct | Direct — `regimeLabel()` and `claimSurface()` helpers drive what `ClaimRow` renders on `/evidence` |
| `apps/frontend/lib/evidence.test.ts` | backend-internal (test) | None — unit test file, not rendered to the user |
| `apps/frontend/app/evidence/page.tsx` | frontend-direct | Direct — `ClaimRow` now renders the regime badge and honest title/subtitle/linkback on `/evidence` |
| `apps/frontend/app/page.tsx` | frontend-direct | Direct — `RegimeGlanceCard` now renders the "See evidence proven in this regime →" link on the Dashboard |
| `apps/backend/tests/test_evidence.py` | backend-internal (test) | None — backend pytest assertion only; no `apps/backend/app/**` change; no endpoint or response shape changed |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_evidence.py` — added a 2-entry-ledger confirming test (`test_build_payload_regime_event_study_claim_adds_no_signal`) and the `_regime_event_study_entry()` builder; imported `_resolve_signal`. This is a regression guard asserting that the new regime claim does not enter `proven_signals` and does not overwrite `leadership_score`. No backend application source changed; `/api/evidence`'s shape and endpoint are unchanged.

---

## Summary

- **Frontend surfaces changed:** 4 (ClaimRow regime badge, ClaimRow title, ClaimRow subtitle, ClaimRow linkback on `/evidence`; RegimeGlanceCard Evidence affordance on `/`)
- **New pages/routes:** 0
- **Modified components:** 2 (`apps/frontend/app/evidence/page.tsx` `ClaimRow`, `apps/frontend/app/page.tsx` `RegimeGlanceCard`)
- **Navigation changes:** no (no new nav entries; a link within an existing card was added)
- **Backend-only changes:** 1 (test file only)
