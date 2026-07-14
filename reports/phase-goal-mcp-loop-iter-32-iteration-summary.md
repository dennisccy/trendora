# Iteration Summary — goal-mcp-loop-iter-32

**Verdict:** PASS
**Iteration type:** goal-full
**Date:** 2026-07-14
**Iteration:** 32

## In plain words

**What you can do now:** You can browse a leaderboard of hundreds of stocks where every score is honestly labeled as either backed by tested evidence or "not yet proven," open the full evidence behind any score, and look through a complete, auditable record of every trading idea the system has tested — a moving-average pattern, several regime- and breakout-based setups, multi-factor combinations, and relative-strength signals, all still honestly unproven. You can view up to thirty years of price history and market-index context for any stock, and the page that manages your data connections runs quickly and reliably even on its heaviest job. The system refuses to test any brand-new idea unless it was written down and registered first, and you can browse a graveyard of every idea it has ever rejected — including internal early-research ideas — each with the exact reason it failed and a working link from a rejected idea straight to its original registration record. You can now also see, at a glance, how much of the platform's "testing budget" has already been used up.

**What changed this time:** New this round: a "certification-budget" page shows how many ideas have been tested so far, how strict the bar for the next test will be, how much testing budget remains, and how much room is left in an internal exploration pool — each with a small trend line — so nothing can quietly spend a year's worth of testing rigor without anyone noticing. Also, clicking a rejected idea's "lineage" link on the graveyard page now correctly jumps you straight down to its matching registration record, instead of leaving you to scroll and hunt for it — closing out the rough edge flagged last round.

**What's next:** Next, the team will likely add either a single daily health check for the whole platform or a check that audits the testing process itself for bias.

## Headline

Certification-budget accounting panel (/research/budget) ships; J-19 flips to passing

## Direction

**Signal:** improving
**Why:** This iteration shipped the new certification-budget accounting panel (J-17) as a purely additive, single-sourced surface (24 new backend tests, zero UI-recompute), and the canonical browser-qa lane recorded a clean passing frame for J-19's graveyard→registry lineage-scroll fix (UT-11: scrollY=154), closing the verification gap iter-31 left open. All seven required-still-passing journeys (J-18, J-05, J-11, J-01, J-06, J-08, J-09) re-verified clean, and every pipeline gate (review, QA, browser QA, audit, closure, ux-regression) passed with zero regressions and zero anti-goal violations. The goal-evaluator has not yet regenerated `eval.md` / `journey-history.json` for this iteration, so this read reflects the pipeline gates' own stated conclusions (audit + closure), not yet a canonical evaluator verdict.

**Trend (last 5 iters):**
- Newly passing this iter: J-17, J-19
- Newly passing in last 5 iters total: J-02, J-06, J-07, J-08, J-09, J-18, J-17, J-19
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 1 of last 5

**Latest evaluator reasoning:** [From iter-31, the most recent evaluator-log entry — iter-32 has not yet been evaluated] "iter-31 shipped J-19 as a textbook additive read-only surface, and I verified every load-bearing claim against artifacts I personally opened, not the handoffs. THE REGRESSION PROOF (iter-9 lesson, spec NOTES): all three ledger/registry state files (certified-claims.jsonl, staging-ledger.jsonl, pre-registrations.jsonl) + evidence.py/referee.py/ledger.py/scoring.py/tools.py/config.yaml/verify_claim.py are git-diff EMPTY vs HEAD (7 canonical / 7 staging rows, 0 PASS each, 11 pre-registrations; canonical Bonferroni divisor stays 8); the graveyard code is 6 new untracked files + 6 additive tracked edits. scan-report CLEAN, coherence COHERENCE-PASS."

## What was done

- Shipped `/research/budget`: a new read-only panel showing total canonical trials to date, the current required-p bar, Thresholdout budget remaining, and staging LORD++ wealth, each with a spend-over-time sparkline.
- Added a third "Certification-budget accounting" card to the `/research` hub's governance grid, reachable in ≤2 clicks.
- Built `app.engine.budget_accounting.build_budget_payload()` as a pure read-compose module that re-reads the exact `ledger`/`online_fdr`/`referee` seams `verify_edge` already uses — no parallel bookkeeping (single-source test-verified).
- Wired `GET /api/research/budget` (mirrors the existing graveyard endpoint), 200-on-missing-ledger, no DB/session.
- Re-verified (no code change) the J-19 graveyard→registry lineage-scroll fix via the canonical browser-qa lane, closing the iter-31 verification gap.
- Added 24 new backend tests (single-source equality, fixture-spend correctness on a throwaway ledger, resilience to missing/empty ledgers) — all pass; real ledgers confirmed byte-identical.
- Verified 14/14 target and regression journeys pass browser QA (J-17's four figures/sparklines/discoverability/resilience; J-19's lineage-scroll; required-still-passing J-18/J-05/J-01/J-06/J-08/J-09).

## What's left

- Six Must-have journeys remain unbuilt: J-20 (daily preflight verdict), J-21 (live-data drift guard), J-22 (certifier self-audit), J-23 (watchlist concentration view), J-24 (per-stock risk-budget card), J-25 (drawdown-expectations panel) — GOAL_ACHIEVED stays out of reach until each ships.
- Audit gap (non-blocking): required-still-passing journey J-11 had no independent re-verification this iteration (judged nil risk — no diff touches its surface and the ledger is 0-PASS); a cheap golden-replay follow-up is recommended.
- The budget panel is descriptive-only by design — no alerts or per-category spend breakdown yet (separate future backlog cards, not this iteration's scope).
- The goal-evaluator has not yet regenerated `eval.md` / `journey-history.json` for this iteration — J-17/J-19's status flips are confirmed by the audit, closure, and browser-QA gates but await the canonical evaluator pass.

## Next step

No `eval.md` exists yet for this iteration (the goal-evaluator has not run), so this is carried from the audit's own recommendation: proceed — J-17 lands passing and J-19 flips partial→passing on genuine canonical browser-qa evidence, the single-source acceptance is verified at the code level, and the real ledgers, divisor, and proven-badge surface are all untouched. The best next risky target is J-20 (daily preflight verdict, B-301) or J-22 (certifier-audit, B-102, the fourth governance surface); a cheap non-blocking follow-up is re-verifying J-11 via golden replay against the current ledger.

## Assumptions made

none recorded

## Quick verify

From `reports/phase-goal-mcp-loop-iter-32-what-to-click.md`:

1. Open `http://localhost:3255/research` in your browser
2. Click the "Certification-budget accounting" card
3. Wait a couple of seconds, then read all four cards on the page
4. Navigate to `http://localhost:3255/research/graveyard`
5. Click any row's Lineage link (an id followed by "→", in the rightmost "Lineage" column — skip any row that instead says "No registration lineage")

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-32.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-32-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-32-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-32-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-32-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-32-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-32-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-32-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-32-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-32-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-32-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-32-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-32-closure-verdict.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
