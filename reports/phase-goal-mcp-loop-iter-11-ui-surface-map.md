# Phase goal-mcp-loop-iter-11 — UI Surface Map

**Phase:** goal-mcp-loop-iter-11
**Date:** 2026-07-01
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|---|---|---|---|---|
| `/research/factor-lab` | Evidence column header | Changed behavior | Column now covers all horizons, not just h20 | Confirm the column header reads "Evidence (D10 · per horizon)" — NOT "Evidence (D10 · 20d)" |
| `/research/factor-lab` | `FactorEvidenceBadge` chip strip — `vcp_contraction` h60 | New component behavior | First non-20-day proven edge promoted to canonical | Locate the `vcp_contraction` row; find the chip labeled "60d Proven" (or equivalent); confirm it is a link whose href is exactly `/evidence#factor-vcp_contraction-d10-h60` and its `data-proven` attribute reads `"true"` |
| `/research/factor-lab` | `FactorEvidenceBadge` chip strip — `vcp_contraction` h1, h5, h10 | New component behavior | Uncertified horizons must render honestly | On the `vcp_contraction` row, confirm chips for 1d, 5d, and 10d each display "Not yet proven", carry `data-proven="false"`, and have no href or link element |
| `/research/factor-lab` | `FactorEvidenceBadge` chip strip — `vcp_contraction` h20 (regression guard) | Changed behavior (unchanged content) | Existing h20 proven badge must not regress | On the `vcp_contraction` row, confirm the 20d chip displays "Proven", links to `/evidence#factor-vcp_contraction-d10-h20`, and carries `data-proven="true"` with `data-horizon="20"` |
| `/research/factor-lab` | `FactorEvidenceBadge` chip strip — all factor rows | Changed behavior | Per-horizon view replaces single-horizon view | Confirm that a factor with no certified claims (e.g. any factor other than `vcp_contraction` and `leadership_score`) shows five "Not yet proven" chips — one per horizon — with no links |
| `/research/factor-lab` | `FactorEvidenceBadge` chip strip — `leadership_score` h20 (regression guard) | Changed behavior (unchanged content) | leadership_score h20 must remain honestly "Proven" | On the `leadership_score` row, confirm the 20d chip reads "Proven" and links to `/evidence#signal-leadership_score` |
| `/evidence` | New `ClaimRow` for `vcp_contraction` D10 h60 | New component (auto-rendered) | 5th canonical ledger entry now served by the existing endpoint | On `/evidence`, locate the row titled "vcp_contraction — top decile (D10)" with subtitle containing "60-day hold"; confirm it shows PASS, holdout +8.91%, SPY control +8.91%, a registration date, forward-walk "Pending", and a "Backs: Research factor lab →" linkback |
| `/evidence` | Existing four claim rows (regression guard) | No change | Prior rows must remain unchanged and undisturbed | Confirm the first four claim rows (leadership_score PASS, Breakout-watch PASS, ma_stack FAIL, vcp_contraction h20 PASS) still render with their prior wording; confirm the h20 vcp_contraction subtitle does NOT contain "60-day hold" |

---

## Backend-Only Changes (No UI Impact)

- `apps/frontend/lib/factor-lab-evidence.test.ts` — 5 unit tests for `factorHorizonBadges()`; test file only, not rendered in browser.
- `apps/frontend/lib/evidence.test.ts` — 27 unit tests (2 new: positive h60 case + h60 `claimSurface` subtitle pin); test file only, not rendered in browser.
- `apps/backend/tests/test_evidence.py` — updated golden snapshot from 4 to 5 ledger entries and added h60 payload assertion; test file only, no change to any `app/**` code.
- `apps/backend/tests/test_staging_ledger_routing.py` — updated two golden values (`count_trials == 5`, updated `rejection_offsets`) that were broken by the gate's 5th canonical entry; test file only, no change to any `app/**` code.

---

## Summary

- **Frontend surfaces changed:** 2 (routes: `/research/factor-lab` and `/evidence`)
- **New pages/routes:** 0
- **Modified components:** 2 (`_labs.tsx` — per-horizon chip strip + `data-horizon`; `evidence.ts` — `claimSurface` h60 subtitle)
- **Navigation changes:** no
- **Backend-only changes:** 4 (all test files; no production backend code changed)
