# Iteration Summary — goal-mcp-loop-iter-32

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-14
**Iteration:** 32

## In plain words

**What you can do now:** You can browse a leaderboard of hundreds of stocks where every score is honestly labeled as either backed by tested evidence or "not yet proven," open the full evidence behind any score, and look through a complete, auditable record of every trading idea the system has tested — a moving-average pattern, several regime- and breakout-based setups, multi-factor combinations, and relative-strength signals, all still honestly unproven. You can view up to thirty years of price history and market-index context for any stock, and the page that manages your data connections runs quickly and reliably even on its heaviest job. The system refuses to test any brand-new idea unless it was written down and registered first, you can browse a graveyard of every idea it has ever rejected — including internal early-research ideas, each with the exact reason it failed and a working link back to its original registration — and you can see at a glance how much of the platform's testing budget has already been used up.

**What changed this time:** New this round: a certification-budget page shows how many ideas have been tested so far, how strict the bar for the next test will be, how much testing budget remains, and how much room is left in an internal exploration pool — each with a small trend line — so nothing can quietly spend a year's worth of testing rigor without anyone noticing. Also, clicking a rejected idea's "lineage" link on the graveyard page now reliably jumps you straight down to its matching registration record instead of leaving you to scroll and hunt for it — closing out the rough edge flagged last round.

**What's next:** Next, the team will most likely add either a single daily health check that every page relies on, or a self-check that audits the testing process itself for bias.

## Headline

Certification-budget accounting panel ships at /research/budget; J-19 flips to passing

## Direction

**Signal:** improving
**Why:** This iteration shipped J-17 (the certification-budget accounting panel) as a newly passing journey on a clean canonical browser-qa run against the final build, and closed out J-19 (the graveyard→registry lineage-scroll fix) from partial to passing with a fresh md5-distinct before/after pair (scrollY=154). No journey regressed and no anti-goal was violated; all required-still-passing journeys re-verified clean. Six Must-have journeys (J-20..J-25) remain unbuilt, but the evaluator calls this a tractable path, not a plateau.

**Trend (last 5 iters):**
- Newly passing this iter: J-17, J-19
- Newly passing in last 5 iters total: J-02, J-06, J-07, J-08, J-09, J-18, J-17, J-19
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 1 of last 5

**Latest evaluator reasoning:** iter-32 shipped J-17 (the certification-budget accounting panel, backlog B-903) as a textbook additive read-only surface and cleanly closed out J-19 in the same pass. J-17 lands `passing` on a clean canonical browser-qa lane against the final build (no post-lane fix → no partial-trap), and J-19 flips `partial → passing` on a fresh, md5-distinct UT-11 before/after pair proving the lineage deep-link scroll fix. No journey regressed, no anti-goal was violated, coherence is COHERENCE-PASS, and every real ledger is byte-identical (divisor stays 8). GOAL_ACHIEVED remains out of reach: six Must-have journeys (J-20..J-25) are still unbuilt.

## What was done

- Shipped `/research/budget`: a new read-only panel showing total canonical trials to date, the current required-p bar, Thresholdout budget remaining, and staging LORD++ wealth, each with a spend-over-time sparkline.
- Added a third "Certification-budget accounting" card to the `/research` hub's governance grid, reachable in ≤2 clicks.
- Built `budget_accounting.build_budget_payload()`, a pure read-compose module that re-reads the exact `ledger`/`online_fdr`/`referee` seams the certifier's own `verify_edge` uses — no parallel bookkeeping (single-source test-verified).
- Wired `GET /api/research/budget` (mirrors the existing graveyard endpoint), 200-on-missing-ledger, no DB/session.
- Re-verified (no code change) the J-19 graveyard→registry lineage-scroll fix via the canonical browser-qa lane, closing the iter-31 verification gap.
- Added 24 new backend tests (single-source equality, fixture-spend correctness on a throwaway ledger, resilience to missing/empty ledgers) — all pass; real ledgers confirmed byte-identical (divisor stays 8).
- Verified 2 target journeys (J-17, J-19) pass browser QA, plus fresh live re-verification of required-still-passing journeys J-18, J-05, J-01, J-06, J-08, J-09 — 14/14 UI test cases overall.

## What's left

- Six Must-have journeys remain unbuilt: J-20 (daily preflight verdict), J-21 (live-data drift guard), J-22 (certifier self-audit), J-23 (watchlist concentration view), J-24 (per-stock risk-budget card), J-25 (drawdown-expectations panel) — GOAL_ACHIEVED stays out of reach until each ships.
- Required-still-passing journey J-11 was carried on byte-identity + corroboration rather than a dedicated golden replay this iteration (audit and ux-regression both flagged the gap as nil-risk); add a dedicated J-11 replay next iteration to close the 6-of-7 gap.
- The budget panel is descriptive-only by design — no alerts or per-category spend breakdown yet (separate future backlog cards, not this iteration's scope).
- Today's "trials over time" trend line looks like a simple staircase (all 7 real trials happen to be registered on the same date) rather than a spread timeline — an honest reflection of the real data, not a display bug.
- `.claude/project-template.md` remains the unfilled generic template (pre-existing gap, unrelated to this iteration).

## Next step

iter-33 (FULL) — continue J-20..J-25, one risky surface per iteration. Best next targets: J-20 (single daily preflight verdict, B-301, the daily-ops keystone re-read verbatim by the dashboard, /stocks, stock detail, /watchlist, and /evidence) or J-22 (certifier-audit, B-102, the fourth and final governance surface, run only against a throwaway ledger, leaving the real ledgers byte-identical). Either ships a new served surface and endpoint, so needs the full audit/ux-regression/closure guards; read the binding backlog card before planning. Fold in a cheap, non-blocking rider: add a dedicated J-11 golden replay to close the 6-of-7 required-still-passing gap the audit flagged. Roughly six more one-surface iterations would close the goal — a tractable path, not a plateau.

## Assumptions made

- iter-32 · goal-evaluator — Ambiguity: J-11 is in the required-still-passing set but got no dedicated golden replay or browser case this iteration; whether it must be re-verified via its own dedicated case each iteration, or whether a 0-PASS ledger plus a byte-identical certification economy plus corroborating frames showing 0 "Proven" suffices, is left open. We chose: scored J-11 `passing` on byte-identity + corroboration rather than holding it `unknown`, since the invariant is trivially satisfied on a 0-PASS ledger and both dependent surfaces directly showed 0 "Proven"; recommended adding a dedicated J-11 replay to the next iteration. Reversible: yes
- iter-31 · goal-evaluator — Ambiguity: whether J-19 should score `passing` (its own goal.md acceptance is met; the lineage-scroll failure is an out-of-acceptance refinement, now fixed) or `partial` (a DoD-named P1 browser case read FAIL and the fix wasn't canonically re-verified). We chose: `partial`, applying the session's "correct-but-not-cleanly-canonical-verified = partial" discipline — a human could reasonably flip this to passing. Reversible: yes
- iter-31 · goal-decomposer — Ambiguity: whether the STAGING ledger's non-PASS verdicts are in scope for J-19's "every non-PASS verdict," and whether composition should be backend- or frontend-side. We chose: surface both ledgers' non-PASS verdicts via a new backend `GET /api/research/graveyard` composition endpoint — the graveyard's purpose includes staging explorations and the honesty fence is preserved (staging carries 0 PASS). Reversible: yes
- iter-30 · goal-evaluator — Ambiguity: the DoD literally read "≥14 ledger-derived rows" but the committed registry has 11. We chose: scored the backfill-completeness line as met by 11 rows, treating "≥14" as an uncomputed estimate and the substantive dedup clause (14 raw entries minus 3 cross-ledger duplicates = 11) as the real bar. Reversible: yes
- iter-30 · goal-decomposer — Ambiguity: whether "every registered hypothesis" for the registry backfill meant the canonical ledger only or the union of both ledgers' distinct claims. We chose: the union of the pre-registered candidate rows and every distinct claim across both ledgers, deduplicated by hypothesis, each labeled by source. Reversible: yes
- iter-29 · goal-evaluator — Ambiguity: J-02's DoD requires the three inline "Not yet proven" score badges visible on the stock detail page, but both captured frames show them below the fold — no single pixel directly shows them. We chose: scored J-02 `passing`, backed by DOM assertions, factor-lab corroboration, leaderboard-scale evidence, and zero code diff since the last live capture. Reversible: yes
- iter-28 · goal-evaluator — Ambiguity: whether an honest all-FAIL rendering on five evidence journeys (J-02/06/07/08/09) satisfies each journey's written acceptance, or only its anti-goal guardrail. We chose: held all five at `partial`, since the proven-edge half of each journey's acceptance is absent — no certified edge exists on the current basis; GOAL_ACHIEVED stayed gated on a human unblock (later resolved by the owner's iter-29 re-scope). Reversible: yes
- iter-28 · goal-decomposer — Ambiguity: how many iterations to keep re-attempting the five evidence journeys when a staging exploration surfaces no promotable edge — keep trying vs. acknowledge a plateau. We chose: a verify-only plateau-acknowledgement pass with no new evidence claim, since the complete pre-registered candidate set already tested all-FAIL and re-submitting would self-defeat by tightening the divisor. Reversible: yes
- iter-27 · goal-evaluator — Ambiguity: whether 12 flagged "secret" findings — all planted fake keys inside the vendored framework's own test fixtures — count as a real anti-goal-#7 credentials violation. We chose: scoped the check to Trendora's own product source, not the vendored framework's self-test tooling — not a violation. Reversible: yes
- iter-26b · goal-evaluator — Ambiguity: whether a journey (J-16) whose proof attempt crashed the backend should read `partial` (capability real, verification incomplete) or `failing` (a verified negative outcome). We chose: `failing`, because a reproduced backend-wide crash is a verified negative outcome, not merely an unfinished verification. Reversible: yes
- iter-26 · goal-evaluator — Ambiguity: decision-tree rule 1 requires an "unresolved critical anti-goal violation" for REGRESSION, but it was genuinely uncertain whether iter-26 caused the memory crash or merely surfaced a pre-existing latent issue. We chose: scored it a regression regardless of causation, since a critical anti-goal was demonstrably, reproducibly violated and left unresolved — the fail-closed rule halts for human review rather than auto-looping. Reversible: yes

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
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-32/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
