# Iteration 8 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** lean

## Summary

J-06 is genuinely delivered: the vcp_contraction top-decile (D10 @ h20) edge was referee-certified PASS by the post-decompose gate (ledger line 4 — holdout +3.33%, p=0.01149 < required_p 0.0125, Bonferroni divisor 4) and is now surfaced honestly as a "Proven" evidence badge on the Research factor lab and as a 4th claim row on `/evidence`, both reading the canonical `GET /api/evidence` verbatim with zero recomputation and zero `apps/backend/app/**` diff. All six Must-have journeys (J-01…J-06) pass on the canonical browser-qa lane (17/18; the lone P2 fail is a benign click-bubble UX nuance), coherence is COHERENCE-PASS, and every anti-goal is upheld — the rejected ma_stack cohort is audit-listed FAIL and reads "Not yet proven" on both surfaces.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | reports/qa/goal-mcp-loop-iter-8-evidence/UT-15-result.png (120/120 rows; Leadership "Proven", Entry Quality + Risk "Not yet proven"; no vcp inline badge) |
| J-02 | passing | passing | reports/qa/goal-mcp-loop-iter-8-evidence/UT-16-result.png (MU detail: Leadership "Proven"; drill-down DOM-asserted: PASS +6.36% / p=0.0004998 / +6.36% vs SPY / leadership_score registered 2026-06-30) |
| J-03 | passing | passing | reports/qa/goal-mcp-loop-iter-8-evidence/UT-15-result.png (Entry Quality + Risk "Not yet proven", never a confident number); ma_stack FAIL reads "Not yet proven" on factor lab (UT-03/UT-09) |
| J-04 | passing | passing | reports/qa/goal-mcp-loop-iter-8-evidence/UT-05-result.png (Breakout-watch "Regime: Risk-on", "Out-of-sample edge in the Risk-on regime", +6.12% vs SPY, "Backs: Research event-study lab →"); UT-14 |
| J-05 | passing | passing | reports/qa/goal-mcp-loop-iter-8-evidence/UT-05-result.png (leadership row 5 fields + "Backs: Stocks leaderboard →"); UT-13 round-trip anchor |
| J-06 | (new) | passing | reports/qa/goal-mcp-loop-iter-8-evidence/UT-05-result.png (vcp_contraction row PASS +3.33% / p=0.01149 < alpha/4=0.0125 / vs SPY / 2026-06-30 / "Backs: Research factor lab →"); UT-03/UT-04 (factor-lab "Proven" badge DOM + deep-link to #factor-vcp_contraction-d10-h20) |

All displayed numbers byte-match `certified-claims.jsonl`: vcp +0.0333/p=0.011494 (line 4), leadership +0.06359 (line 1), Breakout +0.06125 (line 2), ma_stack +0.02619 FAIL (line 3).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No unbacked "Proven" (critical) | OK | Only certified cohorts read "Proven" (leadership_score, vcp_contraction). ma_stack FAIL → "Not yet proven" on both surfaces; Entry Quality + Risk → "Not yet proven". leadership_score reading "Proven" on the factor lab is genuinely certified (line 1 PASS) — not a violation. |
| Decision-quality only (critical) | OK | Subtitle "Out-of-sample edge — factor top decile"; page banner "Research-only · decision support · no orders". No buy/sell/return promise. |
| Displayed numbers correct (critical) | OK | vcp +3.33%/p=0.01149 byte-match ledger line 4; all four rows verified against the engine output. |
| No overfit edges (critical) | OK | vcp certified via sealed holdout + SPY control + Bonferroni divisor 4 (p < α/4); ma_stack honestly FAILED the same bar and is shown FAIL. |
| Determinism / no-lookahead (critical) | OK | Zero engine/referee/`api/evidence`-shape diff — only `apps/frontend/*` + tests changed (confirmed via git diff). |
| No ship without passing referee verdict (critical) | OK | Post-decompose gate appended vcp_contraction PASS as ledger line 4. |
| No hardcoded credentials (critical) | OK | Secret-scan of the iter-8 diff returned clean. |

## Coherence

COHERENCE-PASS (runs/goal-session-mcp-loop/iter-8/coherence.md) — no Data Contract or Information Architecture drift. No new endpoint, no new page, no nav change; the factor-lab badge and `/evidence` factor row are additional readers of the already-registered `GET /api/evidence`. No structural veto.

## Next-Step Recommendation

Halt — goal achieved. All six Must-have journeys (J-01…J-06) are passing and the `<!-- AUTO:journeys -->` block carries no further unbuilt scope. If the continuous-improvement proposer extends `docs/goal.md` with a new journey, dispatch it **lean** for a verify-only re-confirmation, escalating to **full** only if it ships a new referee-gated "proven" claim or touches the shared evidence resolver / a new public-surface badge (the iter-8 footprint that warranted full).

## Halt Justification

GOAL_ACHIEVED: every Must-have journey (J-01…J-06) has status `passing` with positive pixel/DOM evidence on the canonical browser-qa lane; no critical (or minor) anti-goal violation exists — all seven are upheld and the only FAIL ledger entry (ma_stack) is correctly surfaced as "Not yet proven"; and coherence is COHERENCE-PASS (no structural veto). J-06 — the sole outstanding journey — flips from new to passing this iteration. Non-blocking carry-forwards (do not gate): the factor-lab vcp "Proven" badge pixel and the J-02 drill-down panel both render below the fold and were DOM-asserted rather than scrolled into frame; the passive "Not yet proven" chip bubbles a click to the row-expand handle (UT-09 P2); the demo-narrator gallery render was SKIPPED (Playwright not installed); and a dead `cohortEvidenceAnchor` import remains in `_labs.tsx` (reviewer NOTE).
