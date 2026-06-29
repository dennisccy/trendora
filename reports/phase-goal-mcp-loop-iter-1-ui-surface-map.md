# Phase goal-mcp-loop-iter-1 — UI Surface Map

**Phase:** goal-mcp-loop-iter-1
**Date:** 2026-06-29
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|-------------|-------------|
| All pages (persistent sidebar) | `sidebar.tsx` — "Evidence" nav link with ShieldCheck icon | Added navigation | New Evidence ledger page added to approved Information Architecture | Click "Evidence" in the left sidebar; verify it navigates to `/evidence` and the link highlights as active; verify "Evidence" appears after "Research" in the nav order |
| `/stocks` | `stocks/page.tsx` — `EvidenceStatusBadge` below Leadership ScoreBadge on each row | New component | Evidence status must appear beside every score (J-01) | Load `/stocks`; confirm every leaderboard row shows a small chip labeled "Not yet proven" with a Shield icon positioned below the Leadership score badge; confirm no row is missing the chip |
| `/stocks` | `stocks/page.tsx` — `EvidenceStatusBadge` below Entry Quality ScoreBadge on each row | New component | Evidence status must appear beside every score (J-01) | Load `/stocks`; confirm every leaderboard row shows a "Not yet proven" chip below the Entry Quality score badge; confirm no row is missing the chip |
| `/stocks` | `stocks/page.tsx` — `EvidenceStatusBadge` below Risk ScoreBadge on each row | New component | Evidence status must appear beside every score (J-01) | Load `/stocks`; confirm every leaderboard row shows a "Not yet proven" chip below the Risk score badge; confirm no row is missing the chip |
| `/stocks` | `stocks/page.tsx` — evidence-fetch failure degradation | Changed behavior | Fetch failure must never break the leaderboard | Simulate evidence fetch failure (block `/api/evidence`); confirm all leaderboard score badges, values, and row data remain visible; confirm all evidence chips fall back to "Not yet proven" rather than erroring |
| `/stocks/[ticker]` | `[ticker]/page.tsx` — `EvidenceStatusBadge` in Leadership `ScoreCard` | New component | Evidence status on stock detail scores (J-03) | Navigate to any stock detail page; confirm the Leadership ScoreCard shows a "Not yet proven" chip directly below the numeric score; confirm the existing score value and label are unchanged |
| `/stocks/[ticker]` | `[ticker]/page.tsx` — `EvidenceStatusBadge` in Entry Quality `ScoreCard` | New component | Evidence status on stock detail scores (J-03) | Navigate to any stock detail page; confirm the Entry Quality ScoreCard shows a "Not yet proven" chip directly below the numeric score |
| `/stocks/[ticker]` | `[ticker]/page.tsx` — `EvidenceStatusBadge` in Risk `ScoreCard` | New component | Evidence status on stock detail scores (J-03) | Navigate to any stock detail page; confirm the Risk ScoreCard shows a "Not yet proven" chip directly below the numeric score |
| `/evidence` | `evidence/page.tsx` — page heading | New page | The certified-claims ledger is a new top-level surface (J-05) | Navigate to `/evidence`; confirm the page heading displays "Evidence" as the title and the subtitle mentions "the certified-claims ledger" |
| `/evidence` | `evidence/page.tsx` — loading skeleton | New component | Non-blocking load while `/api/evidence` is in flight | Throttle `/api/evidence` response; confirm an animated skeleton card appears while loading and disappears when data arrives |
| `/evidence` | `evidence/page.tsx` — honest empty state card (`data-testid="evidence-empty"`) | New component | Current ledger is empty; page must show an honest no-claims message (J-05) | Navigate to `/evidence` with an empty ledger; confirm the card reads "No certified claims yet" and contains the sentence "every signal currently reads Not yet proven" |
| `/evidence` | `evidence/page.tsx` — claim-row field list inside empty state (`data-testid="evidence-claim-fields"`) | New component | Empty state must enumerate claim-row layout for verifiability (J-05) | On the `/evidence` empty state, confirm the bullet list contains exactly these five entries: "Hypothesis", "Out-of-sample verdict", "Control comparison (vs SPY)", "Registration date", "Forward-walk score-to-date" |
| `/evidence` | `evidence/page.tsx` — "Backend unavailable" error card | New component | Graceful degradation when backend is unreachable | Block `/api/evidence` entirely; navigate to `/evidence`; confirm a styled error card appears with "Backend unavailable" heading and a message indicating nothing is fabricated and every signal remains "Not yet proven" |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/evidence.py` — read-side resolver (`resolve_ledger_path`, `build_evidence_payload`); consumed exclusively through `GET /api/evidence`, which the frontend already calls — no standalone UI surface
- `apps/backend/app/config.py` — adds `EvidenceCfg(ledger_path)` typed config; operator-invisible default wired automatically; no UI surface affected
- `config.yaml` — adds `evidence.ledger_path` setting; runtime configuration only; no UI surface affected
- `apps/backend/tests/test_evidence.py` — unit tests for the resolver; no UI surface
- `apps/backend/tests/test_api_evidence.py` — API tests for `GET /api/evidence` including `/api/stocks` regression; no UI surface
- `apps/frontend/lib/evidence.ts` — pure helper logic (`resolveEvidenceStatus`, `evidenceAnchor`); no independently rendered UI; consumed internally by `EvidenceStatusBadge`
- `apps/frontend/lib/evidence.test.ts` — frontend unit tests; no UI surface
- `apps/frontend/lib/api.ts` — adds `fetchEvidence()` + new types; a data-layer addition; UI impact flows through the consuming pages already listed above

---

## Summary

- **Frontend surfaces changed:** 5 (sidebar, `/stocks` leaderboard, `/stocks/[ticker]` detail, `/evidence` page, evidence API client)
- **New pages/routes:** 1 (`/evidence`)
- **New components:** 2 (`EvidenceStatusBadge`, `EvidencePage` with `EvidenceEmptyState` / `ClaimRow` sub-components)
- **Navigation changes:** yes — "Evidence" entry added to persistent sidebar after "Research"
- **Backend-only changes:** 7 files (resolver, config, config yaml, 2 test files, pure frontend logic module, frontend test)
