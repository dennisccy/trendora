# Iteration Summary — goal-mcp-loop-iter-28

**Verdict:** STALLED
**Iteration type:** goal-lean
**Date:** 2026-07-12
**Iteration:** 28

## In plain words

**What you can do now:** Browse a leaderboard of hundreds of companies with an honest "proven" or "not yet proven" status on every score, open the full evidence ledger to see every trading idea tested so far (all currently read "FAIL" while the deeper thirty-year history is re-proven), and follow the market-regime panel through to the evidence backing it. View up to thirty years of price history for any stock in a recent or full view, browse the company list as it looked on any past date, see three decades of major-index history plus a volatility gauge and a rate indicator on the dashboard chart (each labeled by its source), and check the Data Manager page's color-coded calendar of data availability across the whole company list — with the heaviest data-refresh job now running reliably without crashing.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team went back and re-tested every trading idea that had been pre-approved for testing against the deeper thirty-year history, and confirmed all of them still honestly come up short — none earned a "proven" badge. Nothing broke, nothing new shipped; this was a check, not a build.

**What's next:** A person now needs to decide what happens with the five ideas that keep failing their tests: either approve a fresh batch of ideas to try, or accept that these particular five may not have a provable edge on the newer data. The automatic loop can't make that call on its own.

## Headline

Zero-code plateau check confirms the pre-registered evidence candidate set is exhausted (all FAIL)

## Direction

**Signal:** holding
**Why:** iter-28 shipped no code and produced no journey state changes — J-01/J-03/J-04/J-05/J-10/J-11/J-13 re-verified passing, J-02/J-06/J-07/J-08/J-09 stayed sanctioned-partial, and no journey is in a `failing` state. This isn't the "improving" trajectory of iter-25/27 (no newly-passing journey) nor a regression (no critical anti-goal violation, no passing journey broke) — it's a steady state pending a human decision on the five stalled evidence journeys.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-13 (iter-25, recovered from regression), J-15 (iter-25), J-16 (iter-27, recovered from regression)
- Regressions in last 5 iters: J-13 (iter-24, recovered iter-25)
- Anti-goal violations in last 5 iters: 2 critical — anti-goal #8 (iter-24, resolved iter-25) and anti-goal #8 again (iter-26, resolved iter-27)
- Iters with no journey state change: 1 of last 5 (iter-28 only)

**Latest evaluator reasoning:** iter-28 was a deliberate zero-code plateau-assessment pass. It shipped no product source, no data-model change, and — load-bearingly — no `## Evidence Claim`, establishing with recorded referee evidence that the five sanctioned-partial evidence journeys (J-02/J-06/J-07/J-08/J-09) have no promotable edge on the 30-year basis: the complete pre-registered candidate set (`proposer-guidance.md` §4.1 four singles + §4.2 three combinations) is empirically exhausted — all 7 canonical + 7 staging entries FAIL, six of seven staging members wrong-direction, the best right-direction candidate far from any bar. The only remaining unblock for these journeys is a human revision of the pre-registered candidate registry or a goal.md re-scope.

## What was done

- Ran a deliberate zero-code plateau-assessment pass — confirmed via `git diff` that `apps/backend/app`, `apps/frontend`, `config.yaml`, `data/seed`, and both evidence ledgers are byte-identical to HEAD.
- Read both evidence ledgers directly: canonical `certified-claims.jsonl` (7 entries) and `staging-ledger.jsonl` (7 entries) are all-FAIL — the complete pre-registered candidate set (proposer-guidance.md §4.1 + §4.2) is empirically exhausted.
- Ran the two targeted frozen-golden ledger tests (`test_canonical_ledger_frozen_golden`, `test_committed_staging_ledger_is_the_regenerated_30y_discovery`) — 2/2 passed, confirming no drift.
- Documented the plateau finding with the full referee evidence tables (holdout edge, p-value, required-p per candidate) in the dev handoff for the evaluator.
- Verified 7 required-still-passing journeys (J-01, J-03, J-04, J-05, J-10, J-11, J-13) pass browser QA via deterministic golden-script replay + live evaluator spot-checks.
- Held J-02/J-06/J-07/J-08/J-09 at partial, overriding the browser-qa lane's over-claimed "PASS (see note)" which only verified the honest-status half, not a Proven edge to drill.

## What's left

- Journey J-02 (Drill into the proof behind a score) — partial; no "Proven" badge exists anywhere to drill into.
- Journey J-06 (vcp_contraction top-decile edge) — partial; the retired edge honestly recomputes to FAIL on the 30-year basis.
- Journey J-07 (Multi-horizon certified edge, 60-day) — partial; same closed-FAIL status.
- Journey J-08 (Multi-factor combination edge) — partial; the composite candidate's holdout edge is essentially zero.
- Journey J-09 (rs_spy_3m 60-day edge) — partial; the retired +21.34% edge now honestly reads FAIL.
- The entire pre-registered evidence candidate set (4 singles + 3 combinations) is empirically exhausted — no autonomous next candidate exists; unblocking needs a human to widen the candidate registry or amend goal.md.
- Non-blocking carry-forwards: `IndicatorsCfg._validate`'s guard gap for `breadth_short_ma`/`breadth_long_ma`; grant the browser-qa lane backend-lifecycle permission so cold-start/backend-down repros can run live; remove the stray `.pytest-tmp-iter27/` scratch directory (~2.9 GB, untracked).

## Next step

Halt for a human decision. Menu: (1) widen or revise the pre-registered candidate registry (`docs/goal.md` §4.1/§4.2 / `proposer-guidance.md`) — e.g. open the goal.md-deferred families (quantile spreads D10−D1, regime-conditioning, sector cohorts); or (2) amend `docs/goal.md` to re-scope J-02/J-06/J-07/J-08/J-09 to accept the honest all-FAIL ledger as their terminal contract. On `--resume` after option 1, the next iteration runs FULL, promoting only a genuine winner that clears the canonical Bonferroni divisor-8 bar with margin, honoring the honest-stop guard (report, don't force, if none clears).

## Assumptions made

- iter-28 · goal-evaluator — Ambiguity: The browser-qa lane marked J-02/J-06/J-07/J-08/J-09 "PASS (see note)", scoring only the honest-status half of each journey (badges correctly read "Not yet proven"); each journey's written acceptance requires a Proven certified edge to surface or drill, leaving open whether an honest all-FAIL rendering satisfies the journey or only its anti-goal-#1 guardrail. We chose: Held all five at partial, not passing, per the strict journey acceptance and the 10-iteration session precedent — the honest-status half is satisfied but the proven-edge half is absent; GOAL_ACHIEVED stays gated on a real PASS certified-claim, which is human-unblock-gated. Reversible: yes
- iter-28 · goal-decomposer — Ambiguity: goal.md's loop mechanics leave open how many iterations to keep re-attempting the five evidence journeys when a staging exploration surfaces no promotable edge — keep trying vs. acknowledge a plateau. We chose: A verify-only / plateau-acknowledgement pass with no Evidence Claim, after verifying on disk that the complete pre-registered candidate set is already exhausted (all FAIL); the remaining unblock is a human revision of the registry, surfaced to the evaluator rather than manufacturing a claim. Reversible: yes
- iter-27 · goal-evaluator — Ambiguity: Anti-goal #7 vs the deterministic scan-report flagging 12 CRITICAL secrets, all planted fake keys inside a vendored framework subtree entered via a squash-merge rather than the iteration's product dev work — leaving open whether "source files" covers vendored framework test tooling. We chose: Read anti-goal #7 as scoped to the Trendora product source; the iter-27 product diff carries zero real credentials, so scored upheld / not a violation. Reversible: yes
- iter-26b · goal-evaluator — Ambiguity: J-16's target proof crashed the backend but its perf/byte-identity half was real and one honest-progress sub-criterion was positive, so J-16 could be read as partial rather than failing. We chose: failing, because there was a verified negative outcome (a reproduced backend-wide crash) and J-16's own DoD explicitly requires no-OOM/no-crash — partial is reserved for correct-but-not-cleanly-verified work, not a verified failure. Reversible: yes
- iter-26 · goal-evaluator — Ambiguity: it was genuinely uncertain whether iter-26 caused the anti-goal #8 violation or merely surfaced a pre-existing latent VSZ bomb while probing a heavier fallback job path. We chose: Scored REGRESSION because a critical anti-goal is demonstrably, reproducibly violated and unresolved — the verdict does not depend on this-iteration causation, matching the fail-closed rule for critical anti-goal violations. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-28.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-28-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-28-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-28-ui-test-results.md |
| Goal evaluation | STALLED | runs/goal-session-mcp-loop/iter-28/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
