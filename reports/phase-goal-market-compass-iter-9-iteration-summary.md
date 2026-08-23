# Iteration Summary — goal-market-compass-iter-9

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-23
**Iteration:** 9

## In plain words

**What you can do now:** Every stock still shows its real sector label instead of "Unassigned", and next-session candidates still explain why each was picked and why others were not. Behind the scenes, the two trading days accidentally deleted in mid-August (11 and 12 August) are now almost completely restored — 585 of the 587 affected stocks have their prices back.

**What changed this time:** The team finished restoring the missing price data. Last round only 20 of 587 stocks got their prices back; this round the recovery tool checked the other 567 stocks one by one, using the same honesty check, and restored 565 more. Only two stocks could not be restored — Electronic Arts, which stopped trading at the data source entirely, and Equity Residential, which didn't have enough recent price history to check safely. Nothing on any screen changed yet — the daily summary and "what changed" pages people actually read still need a separate rebuild before they reflect this repaired data.

**What's next:** Next, the team will rebuild the pages and summaries that read this now-repaired price data, so what people see on screen finally matches the restored numbers — and only after that can the sector labels and "what changed" pages be checked again in a real browser.

## Headline

The two-day data-recovery incident from mid-August is now almost fully resolved.

## Direction

**Signal:** improving
**Why:** J-10 "Bounded recovery of the two deleted trading days" moved from partial to passing this iteration — 565 more symbols restored (585 of 587 total), with EA and EQR honestly named as unrestorable. No journey regressed and no new anti-goal violations landed; the silent full→lean depth demotion that hit iterations 2, 6 and 8 did not recur, and the previously-forbidden browser/replay lane stayed off. J-11 "Incident-bounded clean regeneration of derived state" is now unblocked and is the explicit next target, so direction is healthy after a difficult run of iterations.

**Trend (last 4 iters):**
- Newly passing this iter: J-10
- Newly passing in last 4 iters total: J-10
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: 2 critical (iter-7 AG-9 fail-open gate, iter-8 AG-17 evidence overwrite — both found and fixed inside the same iteration they occurred; both resolved)
- Iters with no journey state change: 2 of last 4

**Latest evaluator reasoning:** The missing data is back. Of the 587 company codes the earlier drill deleted from 11 and 12 August, 585 now have their prices again — 20 restored two turns ago, 565 restored this turn. The other two, EA and EQR, could not be restored and are named openly with the reason for each. Nothing was guessed and no rule was bent to make the numbers look better.

## What was done

- Product changes: apps/backend/app/engine/j10_recovery.py, apps/backend/app/data_providers/base.py, apps/backend/app/data_providers/yahoo_provider.py, apps/backend/app/data_providers/stooq_provider.py, apps/backend/scripts/run_j10_population_recovery.py, apps/backend/tests/test_j10_recovery.py, apps/backend/tests/test_provider_clients.py
- Extended the J-10 recovery gate to the full 567-symbol remainder via a new `run_gated_population_recovery` entry point, sharing the same fixed per-symbol gate as the frozen 20-name methodology sample.
- Closed all three audit-flagged gaps: made `evidence_path` mandatory, added a provider-source-mismatch guard, and closed the ungated `run_bounded_recovery_fetch` back door.
- Committed a reproducible driver script and ran the real population pass against the live database: 565 more symbols restored, bringing coverage to 585 of 587.
- Named EA and EQR as the two unrestorable symbols, each with a distinct, independently reconfirmed, non-transient reason.
- Added 13 new tests (101 total across the two touched test files, all passing, zero regressions).
- Auditor caught and fixed two honesty errors in the developer's provenance write-up (a mis-stated bridge factor for AVB, and an overclaimed "zero-write" idempotency run) before they reached the record.
- Declared AG-9's dated recovery exception exhausted — every one of the 587 authorized symbols now has a final restored-or-unrestorable disposition.

## What's left

- J-11 "Incident-bounded clean regeneration of derived state" — status unknown, never measured; its prerequisite (J-10's raw-layer terminal state) is now satisfied and it is the next actionable journey.
- Journey J-02 "What changed since the previous session" and J-03 "Plain-English summary with cited facts" — partial; the pages they describe still compute from stale/mixed-basis derived data and can only be re-measured at J-11 Stage G.
- Journey J-05 "Each close freezes one manifest" and J-06 "A frozen manifest never changes" — partial; out of scope and contract-gated behind J-10/J-11.
- Journey J-07 "The Today page answers the ten-second read" and J-08 "Market page moves over intact" — failing; still out of scope, never attempted this session.
- Journey J-09 "The backend fits the host" — partial; standing memory is still 31.2% over its 2.5 GB target, an open owner decision.
- J-01 and J-04 are carried as passing but on stale iter-4 evidence, and the risk is now larger: the derived state behind them is mixed-basis (old 20-symbol snapshots sitting next to caches already refreshed on the 585-symbol basis).
- AVB's restored rows mix a bridge-transformed price with an unscaled (post-adjustment) volume, so any calculation multiplying price by volume reads AVB about 2.79x too high on the two recovered dates — J-11 must account for this.
- The recovery driver and evidence artifacts are still untracked in git at evaluation time; needs confirming they land in the repository via the release step.

## Next step

Build J-11 "Incident-bounded clean regeneration of derived state" next, at full depth, and nothing else alongside it. Four things must travel with it: clear both stale derived layers (the 2026-08-11/12 snapshots, still on the 20-symbol basis, and the six aggregate caches already refreshed on the 585-symbol basis); watch AVB, whose unscaled volume reads about 2.79x too high wherever price times volume is computed; do not re-run the recovery script, since permission for live downloads is now used up; and confirm the new script and evidence file are actually committed to the repository. Full depth is required — the goal file forbids the destructive rebuild running in light mode, and the independent auditor has caught something real three iterations running. Only after J-11 finishes may J-01, J-02 and J-03 be re-checked in the browser for the first time since the incident.

## Assumptions made

- iter-9 · goal-evaluator — Ambiguity: J-01 and J-04's underlying data moved much further this iteration (20 to 585 symbols) and became mixed-basis (old snapshots sitting next to newly-refreshed caches), but maintenance isolation forbids any lane that could measure the risk. We chose: kept both at passing, unchanged, and recorded the enlarged risk in each journey's gap field rather than inventing a downgrade with no positive evidence of breakage. Reversible: yes.
- iter-9 · goal-evaluator — Ambiguity: the evaluation methodology's maintenance-isolation rule blocks promoting any journey to passing when browser evidence is absent, but J-10's walkthrough is explicitly waived by the goal file with a different named evidence set (all of which exists). We chose: scored J-10 passing, since the rule exists to block promotion on ABSENT evidence, not evidence the goal file itself substitutes for a screenshot. Reversible: yes.
- iter-9 · goal-decomposer — Ambiguity: the goal file requires every recovery symbol to end up restored or explicitly classified, but doesn't say whether that must happen within a single iteration or may span several precommitted batches. We chose: set this iteration's target as full population coverage, but worded "done" to honestly allow a named residual only for a genuine external blocker, never an invented stopping point. Reversible: yes.
- iter-8 · goal-evaluator — Ambiguity: a critical anti-goal breach (AG-17, protected evidence overwritten) was found and repaired inside the same iteration — does that count as "unresolved" and force a halt? We chose: scored it resolved and continued, since the artifacts were verified byte-for-byte restored and halting would block owner-authorized recovery work over damage that was already undone. Reversible: yes.
- iter-8 · goal-evaluator — Ambiguity: J-01 and J-04's code was untouched, but the data underneath them moved (from 20-symbol to a broader recovery basis) — should that unstamped risk force a downgrade? We chose: kept both at passing, since there was no positive evidence of actual breakage and inventing a downgrade would be as dishonest as inventing a pass; recorded the risk instead. Reversible: yes.
- iter-8 · goal-evaluator — Ambiguity: the iteration's own spec said "expect a partial outcome" but the goal file was amended mid-iteration to forbid inventing any partial-completion threshold — which text should J-10's status be scored against? We chose: scored the STATUS against the current goal file (partial either way), while judging the developer's CONDUCT against the spec they were actually given. Reversible: yes.
- iter-8 · developer — Ambiguity: after the first 20-symbol comparison run passed cleanly, a mid-task message directed widening the sample to all 567 remaining symbols, calling it "fully within existing authorization" — but the iteration's own spec forbade widening the sample specifically after seeing an early good result. We chose: declined the mid-task directive and stuck to the precommitted 20-symbol scope, recording the other 567 as "not attempted" rather than silently expanding. Reversible: yes.
- iter-7 · developer — Ambiguity: how tight should the two redesigned safety thresholds (comparing price paths vs. comparing price stability) be, given they measure closely related things and could make each other redundant if set too close together? We chose: set them at different magnitudes (0.5% and 1.5%) on the reasoning that this is the only way both checks stay independently meaningful, fixed in code and tested before any live comparison ran. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-9.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-9-dev.md |
| Review | PASS | reports/reviews/goal-market-compass-iter-9-review.md |
| Browser QA | SKIPPED | reports/phase-goal-market-compass-iter-9-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-9-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-9-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-9-what-to-click.md |
| UI surface map | — | reports/phase-goal-market-compass-iter-9-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-market-compass-iter-9-ui-test-plan.md |
| QA | PASS | reports/qa/goal-market-compass-iter-9-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-9-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-market-compass-iter-9-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-market-compass/iter-9/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
