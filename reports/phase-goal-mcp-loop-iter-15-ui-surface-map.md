# Phase goal-mcp-loop-iter-15 — UI Surface Map

**Phase:** goal-mcp-loop-iter-15
**Date:** 2026-07-01
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|---|---|---|---|---|
| `/evidence` | 7th `ClaimRow` — `rs_spy_3m` D10 h60 | New data row | Canonical gate appended row 7 to the ledger; the existing `ClaimRow` `factor` branch renders it automatically | Scroll to the bottom of `/evidence` and confirm a 7th row appears titled "rs_spy_3m — top decile (D10)" with subtitle "Out-of-sample edge — factor top decile · 60-day hold"; confirm the displayed edge reads "+21.34%", the p-value reads "0.0004998" (or equivalent rendering), the registration date reads "2026-07-01", and a "Backs: Research factor lab →" link is present |
| `/evidence` | Deep-link anchor `#factor-rs_spy_3m-d10-h60` | Changed behavior | The new row's `claimAnchorId` is `factor-rs_spy_3m-d10-h60`; inbound deep-links from the factor lab must resolve to this row | Navigate directly to `/evidence#factor-rs_spy_3m-d10-h60` and confirm the browser scrolls to the `rs_spy_3m` D10 h60 row, not to a different factor's row or the page top |
| `/research/factor-lab` | `rs_spy_3m` factor row — h60 evidence chip | Changed behavior | `resolveCohortEvidence` now finds a PASS entry for `rs_spy_3m` h60 in the 7-entry ledger, changing the chip state from muted to proven | Select the `rs_spy_3m` factor on the factor lab; locate the h60 column cell and confirm the chip reads "Proven" (a proven-checkmark pill), not "Not yet proven"; confirm the chip carries `data-proven="true"` or equivalent attribute |
| `/research/factor-lab` | `rs_spy_3m` factor row — h60 chip deep-link | Changed behavior | The proven chip now carries `href=/evidence#factor-rs_spy_3m-d10-h60` (previously no proven-link existed for this factor/horizon) | Click the "Proven" chip in the `rs_spy_3m` h60 cell; confirm the browser navigates to `/evidence#factor-rs_spy_3m-d10-h60` and the page scrolls to the `rs_spy_3m` row (not the page top or another factor's row) |
| `/research/factor-lab` | `rs_spy_3m` factor row — h1, h5, h10, h20 evidence chips | Unchanged display (regression check) | `resolveCohortEvidence` finds no PASS rows for these horizons; confirming no cross-horizon leak from the h60 certification | Select the `rs_spy_3m` factor on the factor lab; confirm all four cells — h1, h5, h10, and h20 — display the muted "Not yet proven" state and do not show a "Proven" chip or any proven-style badge |
| `/stocks` | Per-stock inline score badges (all three score columns) | Unchanged display (regression check) | `rs_spy_3m` is not in the three score columns; `proven_signals` must stay `{leadership_score}` | Load `/stocks` and confirm that no stock entry shows a new score badge or evidence indicator associated with `rs_spy_3m`; confirm the proven-signals set still contains only `leadership_score` (visible in the Evidence panel or verifiable via `GET /api/evidence` `proven_signals` field) |

---

## Backend-Only Changes (No UI Impact)

- `apps/frontend/lib/evidence.test.ts` — TEST-ONLY. Added unit test cases (ee, ff) asserting the general `resolveCohortEvidence` matcher resolves `rs_spy_3m` h60 to "Proven" and h1/h5/h10/h20 to "Not yet proven" against the 7-entry ledger fixture; reconciled negative case (o). No source code change; no user-visible effect.
- `apps/backend/tests/test_evidence.py` — TEST-ONLY golden-fixture refresh. Updated the `test_canonical_ledger_frozen_golden` snapshot from 6 to 7 entries (statuses, divisors `[1..7]`, `rs_spy_3m` h60 verdict bytes, payload count). No `app/**` change; no user-visible effect.
- `apps/backend/tests/test_staging_ledger_routing.py` — TEST-ONLY golden-fixture refresh. Updated two live-canonical read assertions from count 6 to count 7 (`[1,2,4,5,6]`→`[1,2,4,5,6,7]`). Staging-ledger determinism assertions untouched. No user-visible effect.
- `runs/goal-session-mcp-loop/state/certified-claims.jsonl` — Row 7 appended by the pre-build referee gate (not developer code). This data change is what drives the UI changes above via the existing `GET /api/evidence` endpoint; it has no independent UI surface of its own.

---

## Summary

- **Frontend surfaces changed:** 5 (two on `/evidence`, three on `/research/factor-lab`)
- **New pages/routes:** 0
- **Modified components:** 0 (no source code edited; behavior changed via new data in the ledger)
- **Navigation changes:** no
- **Backend-only changes:** 4 (three test files, one ledger data append)
