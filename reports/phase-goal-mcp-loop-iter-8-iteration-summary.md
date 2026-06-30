# Iteration Summary — goal-mcp-loop-iter-8

**Verdict:** GOAL_ACHIEVED
**Iteration type:** goal-full
**Date:** 2026-06-30
**Iteration:** 8

## In plain words

**What you can do now:** Browse 120 ranked stocks each showing a "Proven" or "Not yet proven" label on every score; expand a "Why proven?" panel on any Leadership card to read the sealed out-of-sample proof (holdout edge, benchmark comparison, certification date); confirm that Entry Quality and Risk are honestly labeled "Not yet proven"; view all four certified claims on the Evidence page with round-trip links back to the stocks leaderboard, the research lab, or the event-study lab; follow the Market Regime card on the Dashboard to the Evidence page to read the Breakout-watch setup's certified edge in the Risk-on regime; and on the Research factor lab, see whether each factor's top performers have a certified statistical edge — the vcp_contraction factor reads "Proven" and links straight to its full auditable ledger entry, while every other factor (including ma_stack, which was tested and rejected) honestly reads "Not yet proven."

**What changed this time:** The Research factor lab gained a dedicated "Evidence" column showing whether each factor's top performers have been rigorously tested out-of-sample. The vcp_contraction factor is the first plain research factor — not a score — to earn a "Proven" label: its top-decile stocks beat the S&P 500 by +3.33% on a sealed holdout (p = 0.01149, certified). Clicking the badge takes you straight to its auditable entry on the Evidence page, which now lists four certified claims. Every untested or failed factor reads "Not yet proven" — including ma_stack, whose edge was tested this round and rejected.

**What's next:** All six required capabilities are now live and verified. If the improvement system proposes a new certified edge, the next step will be a quick re-check rather than a full build.

## Headline

vcp_contraction D10 certified edge surfaced as "Proven" on the Research factor lab and as a 4th /evidence row; all 6 Must-have journeys green

## Direction

**Signal:** improving
**Why:** J-06 is newly passing this iteration — the vcp_contraction top-decile cohort was certified through the referee gate (4th trial, Bonferroni divisor 4, holdout +3.33%, p=0.01149 < required 0.0125) and browser-verified on both the factor lab and the Evidence page. All five prior journeys (J-01 through J-05) were re-confirmed on the canonical browser-QA lane. All six Must-have journeys are now green with zero anti-goal violations.

**Trend (last 3 iters):**
- Newly passing this iter: J-06
- Newly passing in last 3 iters total: J-06 (iter-8); J-01..J-05 were already green entering this window
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: none
- Iters with no journey state change: 1 of last 3 (iter-7, verify-only pass)

**Latest evaluator reasoning:** J-06 is genuinely delivered: the vcp_contraction top-decile (D10 @ h20) edge was referee-certified PASS by the post-decompose gate (ledger line 4 — holdout +3.33%, p=0.01149 < required_p 0.0125, Bonferroni divisor 4) and is now surfaced honestly as a "Proven" evidence badge on the Research factor lab and as a 4th claim row on `/evidence`, both reading the canonical `GET /api/evidence` verbatim with zero recomputation and zero `apps/backend/app/**` diff. All six Must-have journeys (J-01…J-06) pass on the canonical browser-qa lane (17/18; the lone P2 fail is a benign click-bubble UX nuance), coherence is COHERENCE-PASS, and every anti-goal is upheld — the rejected ma_stack cohort is audit-listed FAIL and reads "Not yet proven" on both surfaces.

## What was done

- Certified vcp_contraction D10 h20 via the post-decompose referee gate: 4th ledger entry, holdout +3.33%, p=0.01149 < required α/4=0.0125 (Bonferroni divisor 4); no `signal` key on the claim — does not enter `proven_signals`, never lights an inline /stocks score badge
- Added `resolveCohortEvidence(cohort, claims)` read-side cohort-selector matcher in `apps/frontend/lib/evidence.ts` — scans served `claims[]` for a PASS entry matching all five selectors; fail-safe to "Not yet proven" on any mismatch, matched-but-non-PASS entry (ma_stack FAIL), empty list, or fetch failure
- Added `cohortClaimId` / `cohortEvidenceAnchor` / `claimAnchorId` anchor helpers — a single shared contract so every badge href and `/evidence` row id agree: score rows keep `signal-…`, signal-less factor cohort rows get `factor-<f>-d<d>-h<h>`, event-study rows stay `undefined`
- Extended `claimSurface` with a `kind === "factor"` branch — honest title derived from cohort selectors, "Out-of-sample edge — factor top decile" subtitle (no buy/sell language), and "Backs: Research factor lab →" linkback; score-signal and event-study branches are byte-identical (J-04/J-05 unchanged, unit-asserted)
- Added `FactorEvidenceBadge` "Evidence (D10 · 20d)" column to Research factor lab (`_labs.tsx`) — vcp_contraction "Proven" badge deep-links to `/evidence#factor-vcp_contraction-d10-h20`; all other factors (including ma_stack) read "Not yet proven" (no link); "Proven" link has `stopPropagation()` guard; fail-safe: all badges fall to "Not yet proven" on evidence fetch failure (UT-11 verified live)
- Updated `/evidence` `ClaimRow` to derive its row `id` from the shared `claimAnchorId`; 4th /evidence claim row for vcp_contraction renders all five required fields plus the "Backs: Research factor lab →" linkback
- Added confirming backend test (`test_build_payload_vcp_contraction_factor_cohort_post_certification`) asserting `proven_signals == {leadership_score}`, vcp_contraction `proven:true / signal:null`, and ma_stack `proven:false` with byte-exact ledger values over the 4-entry ledger; zero `apps/backend/app/**` change
- Verified 20/20 functional tests + 17/18 browser-qa tests PASS (1 P2 partial fail: "Not yet proven" chip click bubbles to row expand — non-blocking); 25/25 frontend unit tests + 11/11 backend unit tests green; TypeScript clean

## What's left

- All Must-have journeys passing, no closure blockers.

## Next step

Halt — goal achieved. All six Must-have journeys (J-01…J-06) are passing and the `<!-- AUTO:journeys -->` block carries no further unbuilt scope. If the continuous-improvement proposer extends `docs/goal.md` with a new journey, dispatch it lean for a verify-only re-confirmation, escalating to full only if it ships a new referee-gated "proven" claim or touches the shared evidence resolver / a new public-surface badge (the iter-8 footprint that warranted full).

## Quick verify

From `reports/phase-goal-mcp-loop-iter-8-what-to-click.md`:

1. Navigate to `http://localhost:3255/research/factor-lab` — confirm the factors table loads with a column header reading exactly "Evidence (D10 · 20d)"
2. Scroll to the vcp_contraction row and look at the Evidence cell — confirm a "Proven" chip in accent color with a ShieldCheck icon appears as a clickable link
3. Click the "Proven" chip — confirm navigation to `http://localhost:3255/evidence#factor-vcp_contraction-d10-h20` with the vcp_contraction row already scrolled into view; the factor row is NOT expanded
4. Read the vcp_contraction row on `/evidence` and verify all six items: title "vcp_contraction — top decile (D10)", holdout edge "+3.33%", p-value "0.01149", control label "vs SPY", date "2026-06-30", and linkback "Backs: Research factor lab →"
5. Click "Backs: Research factor lab →" — confirm navigation back to `/research/factor-lab` with the Evidence column and vcp_contraction "Proven" badge intact

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-8.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-8-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-8-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-8-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-8-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-8-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-8-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-8-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-8-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-8-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-8-qa.md |
| Audit | PASS | docs/handoffs/goal-mcp-loop-iter-8-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-8-closure-verdict.md |
| Goal evaluation | GOAL_ACHIEVED | runs/goal-session-mcp-loop/iter-8/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
