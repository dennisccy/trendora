# Phase goal-mcp-loop-iter-8 — UI Surface Map

**Phase:** goal-mcp-loop-iter-8
**Date:** 2026-06-30
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research/factor-lab` | `FactorsTable` — "Evidence (D10 · 20d)" column header | Updated layout | J-06: every factor's top-decile cohort now carries an evidence status chip; new column added to the all-factors table | Navigate to `/research/factor-lab`, scroll the factors table — confirm the column header "Evidence (D10 · 20d)" is present and the column appears to the right of the existing statistics |
| `/research/factor-lab` | `FactorEvidenceBadge` on vcp_contraction row | New component | vcp_contraction top-decile edge is certified PASS — the badge must read "Proven" | Scroll to the vcp_contraction factor row — confirm the chip text is exactly "Proven", the chip uses accent color with a ShieldCheck icon, and it is a clickable link |
| `/research/factor-lab` | `FactorEvidenceBadge` "Proven" link on vcp_contraction row — click behavior | New navigation | Deep-link from factor lab badge to the backing evidence ledger row | Click the "Proven" chip on the vcp_contraction row — confirm the browser navigates to `/evidence#factor-vcp_contraction-d10-h20` and the page scrolls the vcp_contraction claim row into view, without first expanding/collapsing the factor-lab row |
| `/research/factor-lab` | `FactorEvidenceBadge` on Leadership score row | New component | Leadership is a certified score-column factor; honest "Proven" is required here too | Scroll to the Leadership score factor row — confirm the chip text is "Proven" and clicking it navigates to `/evidence#signal-leadership_score` (the existing leadership ledger row, not a cohort anchor) |
| `/research/factor-lab` | `FactorEvidenceBadge` on ma_stack row | New component | ma_stack top-decile edge failed the statistical referee — the badge must not claim "Proven" | Scroll to the ma_stack factor row — confirm the chip text is "Not yet proven", the chip uses a muted/default color with an outline Shield icon, and no link or href is present |
| `/research/factor-lab` | `FactorEvidenceBadge` on all remaining factor rows (not vcp_contraction, not Leadership) | New component | No other top-decile cohort has a certified PASS — all must read "Not yet proven" | Scan every factor row that is neither vcp_contraction nor Leadership score — confirm each chip reads "Not yet proven" with no underline, no link, and no ShieldCheck icon |
| `/research/factor-lab` | `FactorLabPage` evidence fetch — fail-safe empty state | Changed behavior | Factor lab now fetches `GET /api/evidence`; if the fetch fails, every badge must fall back to "Not yet proven" with no link | Simulate or observe a failed evidence fetch (e.g. backend down); confirm no factor row shows "Proven", no JavaScript error appears, and the rest of the factor table still loads |
| `/evidence` | `ClaimRow` for vcp_contraction — new 4th row | New content | vcp_contraction top-decile cohort is the 4th certified entry in the ledger | Scroll to the bottom of the `/evidence` claim list — confirm a row exists with title "vcp_contraction — top decile (D10)", subtitle "Out-of-sample edge — factor top decile", holdout edge "+3.33%", p-value "0.01149", control label "vs SPY", registration date "2026-06-30", and the text "Backs: Research factor lab →" |
| `/evidence` | `ClaimRow` vcp_contraction row — "Backs: Research factor lab →" link | New navigation | Round-trip: evidence row → factor lab | Click "Backs: Research factor lab →" on the vcp_contraction row — confirm the browser navigates to `/research/factor-lab` |
| `/evidence` | `ClaimRow` vcp_contraction row — cohort anchor id | Changed behavior | `#factor-vcp_contraction-d10-h20` anchor enables the "Proven" badge deep-link to land correctly | Navigate directly to `/evidence#factor-vcp_contraction-d10-h20` in the browser address bar — confirm the vcp_contraction row scrolls into view without landing on a different or absent row |
| `/evidence` | `ClaimRow` for ma_stack — updated factor framing and linkback | Changed behavior | ma_stack previously lacked a factor title and linkback; now carries the same honest factor framing as vcp_contraction | Scroll to the ma_stack row on `/evidence` — confirm it now shows title "ma_stack — top decile (D10)", subtitle "Out-of-sample edge — factor top decile", a "Backs: Research factor lab →" link, and that the verdict chip still reads "Not yet proven" (FAIL — not "Proven") |
| `/evidence` | `ClaimRow` leadership_score row — score anchor preserved | Unchanged (regression check) | Score-row anchor `signal-leadership_score` must not be replaced by a cohort anchor | Navigate to `/evidence#signal-leadership_score` — confirm the leadership claim row scrolls into view and still displays "Backs: Stocks leaderboard →" |
| `/evidence` | `ClaimRow` Breakout-watch regime row | Unchanged (regression check) | J-04: event-study row must not be altered by this iteration | Scroll to the Breakout-watch row on `/evidence` — confirm it is still labeled "Regime: Risk-on" with its event-study linkback and no cohort anchor |
| `/stocks` | Score status badges — Leadership / Entry Quality / Risk | Unchanged (regression check) | vcp_contraction is a factor-only edge with no score signal; no per-stock badge must appear | Navigate to `/stocks` — confirm Leadership shows "Proven", Entry Quality and Risk show "Not yet proven", and no "vcp_contraction" label or badge appears anywhere on the page |
| `/stocks/{ticker}` | Leadership proof drill-down panel | Unchanged (regression check) | J-02: score-based evidence display must survive the new factor-cohort logic in `lib/evidence.ts` | Navigate to any stock detail page and open the Leadership score proof panel — confirm the OOS test result, SPY control line, and claim id/date still render as before |

---

## Backend-Only Changes (No UI Impact)

- `apps/frontend/lib/evidence.test.ts` — unit test file for the new pure helpers (`resolveCohortEvidence`, `cohortClaimId`, `cohortEvidenceAnchor`, `claimAnchorId`, `claimSurface` factor branch); no rendered output, no UI surface affected
- `apps/backend/tests/test_evidence.py` — confirming backend test over the 4-entry certified-claims ledger; TEST-ONLY with zero `apps/backend/app/**` change; no endpoint shape changed, no UI surface affected

---

## Summary

- **Frontend surfaces changed:** 3 routes/pages (`/research/factor-lab`, `/evidence`, `/stocks` regression-checked)
- **New pages/routes:** 0
- **Modified components:** 3 — `FactorsTable` (new Evidence column + colSpan), `ClaimRow` (new anchor id logic + 4th row + ma_stack framing), new `FactorEvidenceBadge` (local component in `_labs.tsx`)
- **Navigation changes:** no sidebar or nav-skeleton changes; two new cross-page deep-links added (factor lab → evidence row, evidence row → factor lab)
- **Backend-only changes:** 2 (frontend unit test file, backend unit test file)
