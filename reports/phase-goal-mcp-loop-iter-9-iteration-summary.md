# Iteration Summary — goal-mcp-loop-iter-9

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-01
**Iteration:** 9

## In plain words

**What you can do now:** Browse 120 ranked stocks each showing a "Proven" or "Not yet proven" badge on every score; expand a "Why proven?" panel on any Leadership card to read the sealed out-of-sample proof (holdout edge, benchmark comparison, certification date); confirm that Entry Quality and Risk are honestly labeled "Not yet proven"; view all four certified claims on the Evidence page with round-trip links to the leaderboard, research lab, and event-study lab; follow the Market Regime card to see the Breakout-watch setup's certified edge in Risk-on conditions; and on the Research factor lab see vcp_contraction labeled "Proven" with a link to its full auditable record, while all others (including the tested-and-rejected ma_stack) honestly show "Not yet proven."

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The engineering team built an internal "practice ledger" system that lets the platform explore new potential edge discoveries without permanently tightening the bar that future "Proven" labels must clear. Every score, badge, and displayed number on screen is byte-for-byte identical to before.

**What's next:** Next we'll surface a certified edge at a new forward-looking time horizon on the Research factor lab — the first of two new journeys the product needs to complete.

## Headline

Sustainable trial economy (LORD++ staging ledger) built; canonical evidence byte-identical, J-07/J-08 enabled

## Direction

**Signal:** holding
**Why:** No journey changed state this iteration — J-01 through J-06 held at passing, confirmed via canonical byte-identity path (backend-only refactor; browser QA skipped by spec design). J-07 and J-08 entered journey-history as unknown (unbuilt by design), which is not a regression. No currently-failing journeys exist (J-07/J-08 are unknown, not failing), so stalling does not apply. Iter-8 was the last productive flip (J-06 to passing); the metric is stable at six passing with two unbuilt Must-have journeys remaining.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-04 (iter-6), J-06 (iter-8)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 2 of last 5 (iters 5 and 7)

**Latest evaluator reasoning:** iter-9 cleanly delivered its sole deliverable — Part A of goal.md's engineering direction, the sustainable trial economy (an injectable, default-off online-FDR / LORD++ deflation policy in a separate internal staging ledger). This is a backend infrastructure milestone (like the iter-2 "backend milestone — not a journey-state change"): by explicit spec design it flips NO journey to passing. The two new human-authored Must-have journeys J-07 (multi-horizon) and J-08 (multi-factor combination) remain unbuilt/unknown, so the goal is not yet achieved — but real, load-bearing progress landed and the next step is crisp, so this is CONTINUE.

## What was done

- NEW `online_fdr.py` — pure LORD++ module (no RNG, no I/O); deterministic per-trial significance allocation from rejection-offset sequence; ζ(1.6) normalizer accurate to ~1e-12; 7 frozen-value unit tests pass
- Made deflation policy injectable on `RefereeState` (default = Bonferroni); `certify_edge` reproduces today's `required_p = alpha_per_test / divisor` byte-identically; `test_referee.py` and `test_forward_walk.py` left unedited and stay green — strongest possible proof defaults are unchanged
- Added `rejection_offsets(path)` derived accessor to `ledger.py`; returns `[1, 2, 4]` from the live canonical file with no entries rewritten
- `verify_edge` in `tools.py` threads the economy: canonical → always Bonferroni (honesty fence); staging → online-FDR when `fdr.enabled`, else Bonferroni; still the sole ledger writer; honesty fence verified by a DB integration test
- `forward_walk.py` reproduce-contract: re-derives `test_level` from each entry's recorded `required_p` so a re-score reproduces the original verdict byte-for-byte for both Bonferroni and LORD++ entries
- Extended `config.py` with typed `FdrCfg` (default-off, backward-compatible) + `staging_ledger_path`; malformed `fdr` block raises `ConfigError` — never silently weakens the bar; `config.yaml` updated with documented `evidence.staging_ledger_path` + `fdr` sub-block
- `verify_claim.py` gate routes per-claim `"ledger"` key (default `staging`, explicit `canonical`); fail-closed on unrecognized values and unset paths; `STAGING_LEDGER_PATH` exported alongside `LEDGER_PATH` in `run-goal.sh` at both dispatch sites
- Full backend suite: 1285 passed, 1 pre-existing unrelated timing flake (data_manager, untouched by iter-9); 14/14 QA functional tests PASS; Review PASS, Audit PASS, Closure CLOSURE-PASS; canonical 4-entry golden and `proven_signals == {leadership_score}` confirmed

## What's left

- Journey J-07 (Multi-horizon certified edge surfaced — the loop sees beyond the 20-day horizon) — unknown/unbuilt; targeted iter-10
- Journey J-08 (Multi-factor combination certified edge surfaced on Combination lab + Evidence) — unknown/unbuilt; targeted iter-11
- Evidence Claim blocks for iter-10/iter-11 MUST carry explicit `"ledger":"canonical"` or they route to staging and silently never surface (gate default is now staging — critical footgun)
- Pre-existing `test_data_manager_jobs_pipeline.py` wall-clock timing flake (non-blocking; data_manager untouched by iter-9; passes in isolation)

## Next step

iter-10 (FULL): open the scan aperture — Part B Phase 1 — and surface J-07. Use the new staging ledger to explore a NON-20 forward horizon (1/5/10/60) for a factor-decile cohort cheaply under the online-FDR economy, then promote exactly one out-of-sample winner to canonical by carrying an `## Evidence Claim` with an explicit `"ledger":"canonical"` key so the post-decompose gate certifies it under strict Bonferroni (divisor 5, `required_p=0.010`). On PASS, surface the row on `/evidence` + the factor-lab "Proven" badge at that horizon (uncertified horizons read "Not yet proven"), and browser-verify J-07. FULL depth because iter-10 ships a new referee-gated "Proven" claim and a new public-surface badge (the iter-8 escalation rule). Then iter-11 does the same for a PRE-REGISTERED 2-factor combination to surface J-08. GOAL_ACHIEVED becomes reachable once both land verified.

Load-bearing reminder for the iter-10 author (audit §5): the gate default is now `"ledger":"staging"` — a claim intended for the user-facing badge MUST set `"ledger":"canonical"` EXPLICITLY, or the winner is certified into staging and silently never surfaces (conservative fail direction, but a real footgun for J-07/J-08 surfacing).

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-9.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-9-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-9-review.md |
| Browser QA | SKIPPED | reports/phase-goal-mcp-loop-iter-9-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-9-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-9-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-9-what-to-click.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-9-qa.md |
| Audit | PASS | docs/handoffs/goal-mcp-loop-iter-9-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-9-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-9/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
