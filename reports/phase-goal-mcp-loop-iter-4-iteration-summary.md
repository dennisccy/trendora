# Iteration Summary — goal-mcp-loop-iter-4

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-06-30
**Iteration:** 4

## In plain words

**What you can do now:** Browse ranked stocks with an evidence status on every score — Leadership shows "Proven", Entry Quality and Risk show "Not yet proven". Tap "Why proven?" on any stock's Leadership card to read the rigorous out-of-sample test that backs that label (holdout edge, benchmark comparison, significance figure). Visit the Evidence ledger from the sidebar to audit every certified claim and follow links back to the stock rankings. Now you can also click "See evidence proven in this regime →" on the Dashboard's Market Regime card to jump directly to the Evidence page, where the Breakout-watch setup row is labeled "Regime: Risk-on" and shows its certified out-of-sample edge (+6.12% vs the S&P 500) with the exact statistical proof.

**What changed this time:** The Dashboard's Market Regime card now includes a "See evidence proven in this regime →" link that takes you straight to the Evidence page. On that page, the Breakout-watch row now shows a "Regime: Risk-on" badge, an honest title ("Breakout-watch setup"), and the out-of-sample proof (+6.12% vs S&P 500, statistically significant, certified by the platform's referee). That row previously displayed a confusing placeholder and linked incorrectly to the Stocks page; it now links to the Research event-study lab. Everything else — the Leadership "Proven" badge, the proof drill-down panel, the other score chips — is byte-identical to before.

**What's next:** Next the automated browser-check lane will run cleanly against the live app (a leftover server process blocked the port this round), capturing fresh screenshots for all five journeys and completing the verification record needed to formally declare the goal achieved.

## Headline

Regime-conditioned evidence (J-04): Breakout-watch x Risk-on certified and labeled; canonical browser lane skipped

## Direction

**Signal:** improving
**Why:** J-04 advanced from unknown to partial — the feature was built (regime label, honest title, Dashboard affordance), gate-certified (Breakout-watch×Risk-on PASS, holdout +6.12% vs SPY, p=0.0004998 < alpha/2=0.025), and visually confirmed in the QA lane (TC-01 Dashboard affordance, TC-03 Evidence page byte-correct values). J-05 received fresh pixel evidence this iteration confirming the leadership row is byte-unchanged. The sole gap blocking GOAL_ACHIEVED is a stale next-server process that occupied :3255 and caused the canonical browser-qa-agent lane to skip all 11 tests; iter-5 targets only that harness fix plus fresh canonical screenshots for all five journeys.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-01, J-02, J-03, J-05
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 1 of last 5 (iter-0, initialization seed)

**Latest evaluator reasoning:** The feature half genuinely succeeded — TC-01 shows Dashboard Risk-on 76.05 and the "See evidence proven in this regime →" affordance; TC-03 shows the /evidence "Regime: Risk-on" Breakout-watch row with values byte-identical to the certified ledger (holdout_edge 0.06124…, control_excess same, p_value 0.0004997…, register_date 2026-06-30). However GOAL_ACHIEVED is withheld: the canonical browser-qa-agent lane reported all 11 SKIP ("frontend not running" — stale next-server held :3255), which is the exact iter-0/iter-2 pattern the spec designates a HARD verification gap. J-01/J-02/J-03 have no fresh iter-4 pixels, and the spec-required post-QA audit handoff is absent (current_step=qa_complete).

## What was done

- Certified the Breakout-watch × Risk-on event-study edge at the post-decompose gate (holdout +6.12% vs SPY, p=0.0004998 < alpha/2=0.025, 107 sealed holdout dates / 277 in-sample; second `certified-claims.jsonl` entry; gate blocked=false)
- Added "Regime: Risk-on" badge to regime-conditioned claim rows in `ClaimRow` on the Evidence page; badge hidden when `claim.regime` is absent so the leadership (score) row is visually unchanged
- Replaced misleading "Unmapped signal" title and Stocks leaderboard linkback on the setup claim with "Breakout-watch setup" title, "Out-of-sample edge in the Risk-on regime" subtitle, and "Backs: Research event-study lab →" linkback
- Added "See evidence proven in this regime →" affordance to the Dashboard Market Regime card, linking to `/evidence` (additive; regime number/label unchanged)
- Introduced two pure testable helpers — `regimeLabel()` and `claimSurface()` — in `apps/frontend/lib/evidence.ts`; 15 frontend unit tests and 10 backend tests pass
- Added backend confirming unit test asserting `proven_signals` stays keyed only on `leadership_score` over the 2-entry ledger (`_resolve_signal` → None for the event-study regime claim; regime claim adds no signal)
- Verified J-05 fresh via QA-lane TC-03: leadership row byte-identical after adding the regime row; zero `apps/backend/app/**` diff; coherence audit PASS (no Data Contract duplication, no IA drift)
- Canonical browser-qa-agent lane SKIPPED all 11 tests ("frontend not running") — stale next-server held :3255; QA visual confirmation came from the QA agent's parallel TC-* lane only

## What's left

- Journey J-04 (Regime-conditioned evidence) — partial; feature delivered and gate-certified but canonical browser-qa-agent lane SKIPPED (11/11); needs fresh canonical UT-* screenshots with the regime row scrolled into frame before capture
- Journey J-01 (Every score shows an evidence status) — carried passing; last pixel evidence from iter-3 (UT-02); needs fresh canonical screenshot in iter-5
- Journey J-02 (Drill into the proof behind a score) — carried passing; last pixel evidence from iter-3 (UT-08); needs fresh canonical screenshot in iter-5
- Journey J-03 (Unproven / noise signals are honestly marked) — carried passing; last pixel evidence from iter-3 (UT-06); needs fresh canonical screenshot in iter-5
- Post-QA audit handoff absent (`docs/handoffs/goal-mcp-loop-iter-4-audit.md`); pipeline stopped at `qa_complete` for the second consecutive iteration — terminal run must produce the audit handoff
- Port conflict: `start-frontend.sh` does not free :3255 before binding (no `fuser -k`); a stale next-server blocked the canonical lane and must be killed before the iter-5 browser-qa lane runs

## Next step

iter-5 (full) = the final, decisive verification pass — no new feature code beyond a harness fix. (1) Free :3255 before the browser-qa lane binds (kill any orphan next-server; `start-frontend.sh` lacks the `fuser -k` that `dev.sh` uses). (2) Capture fresh canonical (UT-*) screenshots for all five journeys through the browser-qa-agent: J-04 (Dashboard Risk-on + affordance → /evidence "Regime: Risk-on" row scrolled into frame, values matching GET /api/evidence), J-05 (leadership row + "Backs: Stocks leaderboard →" linkback round-trip), J-01/J-03 (/stocks every score status), J-02 (/stocks/{ticker} Leadership proof drill-down). (3) Produce the post-QA audit handoff at `docs/handoffs/goal-mcp-loop-iter-5-audit.md` (the audit stage has stopped at qa_complete twice; the terminal run must complete it). On a clean full run with five fresh canonical screenshots and an audit handoff, all five Must-have journeys go green through the session-standard lane and GOAL_ACHIEVED is reachable.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-4.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-4-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-4-review.md |
| Browser QA | SKIPPED | reports/phase-goal-mcp-loop-iter-4-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-4-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-4-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-4-what-to-click.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-4-qa.md |
| Coherence audit | COHERENCE-PASS | runs/goal-session-mcp-loop/iter-4/coherence.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-4/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
