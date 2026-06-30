# Phase goal-mcp-loop-iter-2 — UI Surface Map

**Phase:** goal-mcp-loop-iter-2
**Date:** 2026-06-30
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/stocks/{ticker}` | `ScoreProofPanel` — "Why proven?" toggle button (`data-testid="score-proof-toggle"`) | New component | J-02: user must be able to expand/collapse proof for a Proven score | On the Leadership ScoreCard, click the "Why proven?" button — verify the proof body (`data-testid="score-proof-body"`) becomes visible and the chevron rotates |
| `/stocks/{ticker}` | `ScoreProofPanel` — out-of-sample test fields (`proof-holdout-edge`, `proof-p-value`) | New component | J-02: display the exact certified OOS result verbatim | Expand the proof panel on Leadership — verify holdout-edge reads "+6.36%" and p-value reads "0.0004998" (values sourced from `GET /api/evidence`, byte-identical) |
| `/stocks/{ticker}` | `ScoreProofPanel` — control comparison field (`proof-control-excess`) | New component | J-02: display the SPY benchmark excess, honestly labeled | Expand the proof panel on Leadership — verify the control-excess field reads "+6.36%" with label "vs SPY (benchmark control)" |
| `/stocks/{ticker}` | `ScoreProofPanel` — certified-claim link (`proof-evidence-link`) | New component | J-02: round-trip from score to evidence ledger | Expand the proof panel on Leadership — click "View backing evidence row →" — verify browser navigates to `/evidence` and the `signal-leadership_score` anchor is in view |
| `/stocks/{ticker}` | `ScoreProofPanel` — proof-claim-id field | New component | J-02: display claim id and registration date | Expand the proof panel — verify the claim-id field reads "leadership_score · registered 2026-06-30" |
| `/stocks/{ticker}` | `EvidenceStatusBadge` — Leadership score (`data-testid="evidence-badge"`, `data-proven="true"`) | Changed behavior | Leadership is now Proven; badge data changes state | Navigate to any stock detail — confirm the Leadership badge chip reads "Proven" (not "Not yet proven") and `data-proven="true"` is set |
| `/stocks/{ticker}` | `ScoreCard` — Entry Quality and Risk scores | No change (regression guard) | These scores must remain unproven; no panel may appear | On the Entry Quality and Risk ScoreCards, confirm no "Why proven?" toggle or `data-testid="score-proof"` element exists |
| `/stocks` | `EvidenceStatusBadge` — Leadership column | Changed behavior (state-only) | Leaderboard Leadership badge reflects certified status | On the Stocks leaderboard, verify the Leadership column badge reads "Proven" for every stock row and clicking it navigates to `/evidence#signal-leadership_score` |
| `/evidence` | `ClaimRow` — leadership_score row (`id="signal-leadership_score"`) | Changed behavior (data-populated) | Evidence page now has a real certified claim to display | Navigate to `/evidence` — verify one claim row appears with the Leadership hypothesis text, a "PASS" verdict chip, holdout edge ~+6.36%, control vs SPY ~+6.36%, and registration date 2026-06-30 |
| `/evidence` | `ClaimRow` — "Backs: Stocks leaderboard →" linkback | Changed behavior (data-populated) | Round-trip from evidence back to leaderboard | On the leadership_score claim row, click "Backs: Stocks leaderboard →" — verify navigation returns to `/stocks` |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/evidence.py` — added `_resolve_signal()` to derive the UI signal key for a certified score-column PASS entry that omits the explicit `signal` field. Display-routing only; no new value computed, no new endpoint, no change to `GET /api/evidence` response shape. Defense-in-depth for future claim registration.
- `apps/backend/tests/test_evidence.py` — test-only additions covering the new derivation logic and proven-field assertions; no UI surface affected.
- `apps/frontend/lib/evidence.test.ts` — frontend unit tests for `proofFieldsFor`, formatters, and `SCORE_SIGNALS`; no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 4 (stock-detail ScoreCard, stock-detail proof panel, stocks leaderboard badge, evidence claim row)
- **New pages/routes:** 0
- **New components:** 1 (`ScoreProofPanel`)
- **Navigation changes:** no (new links exist within existing pages but no top-level nav entry added)
- **Backend-only changes:** 3 (evidence engine hardening, backend tests, frontend unit tests)
