# Iteration Summary — goal-mcp-loop-iter-11

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-01
**Iteration:** 11

## In plain words

**What you can do now:** Browse the stock leaderboard and see which scores are "Proven" or "Not yet proven"; click any proven score to read its full out-of-sample evidence (holdout edge, benchmark comparison, registration date); check the Research Factor Lab and see each factor's evidence status separately for every tested holding period (1, 5, 10, 20, and 60 trading days); click a "Proven" chip to jump straight to its certified evidence entry; browse the Evidence ledger listing all five certified results with round-trip links to the leaderboard, event-study lab, and factor lab; confirm that uncertified factors, uncertified horizons, and failed tests are all honestly labeled "Not yet proven."

**What changed this time:** The Research Factor Lab now shows a separate label for each tested holding period — five answers per factor row instead of one. The volatility-contraction pattern earned its first "Proven" label at the 60-day horizon (+8.91% out-of-sample, +8.91% vs the SPY benchmark), the platform's first certified edge beyond the 20-day window. Clicking that chip takes you to a new entry on the Evidence page with the full audit trail. Its shorter horizons (1-day, 5-day, 10-day) remain honestly labeled "Not yet proven."

**What's next:** Next we will certify a two-factor combination edge and show it on the Combination Lab, which would complete all planned user-facing journeys and open the door to declaring the goal fully achieved.

## Headline

vcp_contraction D10 @ h60 promoted to canonical; factor lab gains per-horizon chip strip; J-07 passes (unknown → passing)

## Direction

**Signal:** improving
**Why:** J-07 flipped from unknown to passing this iteration — the vcp_contraction h60 edge was certified into the canonical ledger (5th entry), rendered as a per-horizon badge on the factor lab, and confirmed by 15/15 browser QA tests with DOM-level assertions against a live stack. No prior-passing journey regressed, and all seven anti-goals are upheld. J-08 is the sole remaining unbuilt journey, with a concrete scoped next step.

**Trend (last 5 iters):**
- Newly passing this iter: J-07
- Newly passing in last 5 iters total: J-06 (iter-8), J-07 (iter-11)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 3 of last 5 (iter-7 re-verification only, iter-9 enablement-only, iter-10 discovery-only)

**Latest evaluator reasoning:** iter-11 surfaced J-07 end-to-end: the referee-certified vcp_contraction D10 @ h60 signal-less edge was promoted to the canonical ledger (5th entry, PASS, +8.91% holdout, p=0.0004998, Bonferroni divisor 5) and rendered as a per-horizon "Proven" badge on /research/factor-lab deep-linking to a new /evidence row, with h1/h5/h10 honestly reading "Not yet proven". J-07 flips unknown -> passing (progress), but J-08 (multi-factor combination) remains unknown/unbuilt — explicitly out of scope this iteration — so the goal is not yet achieved. No regression, no anti-goal violation, coherence COHERENCE-PASS. Skeptical finding (non-blocking): the 11 evidence PNGs collapse to 3 distinct images by md5; none shows the vcp_contraction row or h60 chip scrolled into the viewport — the iter-3 lesson recurred despite being specced verbatim. J-07 still passes on the DOM+ledger+unit-test channels; the pixel artifact is a documentation gap, not a functional failure.

## What was done

- Promoted vcp_contraction D10 @ h60 to canonical ledger via the post-decompose gate: 5th entry, PASS, +8.91% holdout, +8.91% vs SPY, p=0.0004998 < required_p=0.010, Bonferroni divisor 5, signal-less (no `signal` key)
- Evolved `/research/factor-lab` Evidence column from a single h20 chip to a per-horizon strip of five chips (1d/5d/10d/20d/60d) per factor row, each resolved via the existing `resolveCohortEvidence` matcher with no new data path
- Added `data-horizon={h}` attribute to every chip enabling per-horizon DOM selection; h60 chip is a `<Link>` with stopPropagation deep-link guard; h1/h5/h10 chips are non-interactive divs
- New `/evidence` claim row for vcp_contraction D10 h60 auto-rendered by the existing `ClaimRow` component; subtitle reads "Out-of-sample edge — factor top decile · 60-day hold" (h20 subtitle byte-identical)
- Extracted pure `factorHorizonBadges` module (`lib/factor-lab-evidence.ts`) enabling unit-testable per-horizon logic without a React renderer
- Zero backend engine/router/referee/ledger/evidence.py changes; all backend changes are test-only golden updates to reflect the 5-entry ledger reality
- 45 unit tests green (27 frontend evidence + 5 factor-lab-evidence + 13 backend); `tsc --noEmit` clean; `proven_signals` pinned byte-identical to `{leadership_score}` by the frozen-golden test on the real on-disk ledger
- Verified 15/15 browser QA tests on the canonical lane (DOM attributes, href values, live click navigation, error-state rendering, 0 skipped)

## What's left

- Journey J-08 (Multi-factor combination certified edge surfaced on the Combination lab + Evidence) — status `unknown`, unbuilt by design; the sole remaining Must-have journey blocking GOAL_ACHIEVED; will face Bonferroni divisor 6 (required_p ≈ 0.00833) after this iteration's canonical write tightened the bar from 5 to 6
- Non-blocking documentation gap: iter-12 browser QA should capture one explicit `/stocks` screenshot and scroll all asserted badges into the viewport before capture (iter-3 lesson recurred; also noted by auditor and ux-regression reviewer)

## Next step

iter-12 (FULL) — surface J-08 (the sole remaining Must-have journey). Promote ONE PRE-REGISTERED 2-factor combination from the config-backed candidate set (never an ad-hoc data-mined cohort) via an explicit `"ledger":"canonical"` `## Evidence Claim`. It now faces **Bonferroni divisor 6 (required_p ~= 0.00833)** after iter-11's canonical write tightened the bar 5->6 — promote only a candidate whose recorded raw p clears 0.00833 with margin. Surface the new combination row on `/evidence` + a "Proven" badge on `/research/factor-combination` (uncertified combinations read "Not yet proven"); keep it signal-less so J-01/J-02/J-03 stay unaffected. FULL depth because it ships a new referee-gated canonical claim + a new public-surface badge (the auditor-grade high-stakes write, mirroring iter-8/iter-11). BROWSER-QA HARD REQUIREMENT: actually scroll each asserted badge/row into the viewport and capture DISTINCT screenshots (do not relabel one full-page capture across many UT ids). GOAL_ACHIEVED becomes reachable the moment J-08 lands browser-verified with J-01..J-07 non-regressed.

## Quick verify

From `reports/phase-goal-mcp-loop-iter-11-what-to-click.md`:

1. Navigate to `http://localhost:3255/research/factor-lab` — expect the Evidence column header reads "Evidence (D10 · per horizon)"
2. Find the `vcp_contraction` row and look at the Evidence column — expect 5 chips labeled 1d/5d/10d/20d/60d
3. Check the 60d chip on the `vcp_contraction` row — expect it reads "Proven" and is a clickable link
4. Click the 60d "Proven" chip — expect browser navigates to `http://localhost:3255/evidence#factor-vcp_contraction-d10-h60`
5. On the Evidence page, locate the fifth claim row (subtitle contains "60-day hold") — expect status "PASS", holdout "+8.91%", SPY comparison "+8.91%", forward-walk "Pending"

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-11.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-11-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-11-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-11-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-11-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-11-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-11-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-11-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-11-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-11-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-11-qa.md |
| Audit | PASS | docs/handoffs/goal-mcp-loop-iter-11-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-11-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-11/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
