# Iteration Summary — goal-mcp-loop-iter-31

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-13
**Iteration:** 31

## In plain words

**What you can do now:** You can browse a leaderboard of hundreds of stocks where every score is honestly labeled as either backed by tested evidence or "not yet proven." You can open the full evidence behind any score, look through a complete, auditable record of every trading idea the system has tested so far — including a moving-average pattern, several regime- and breakout-based setups, multi-factor combinations, and relative-strength signals, all still honestly unproven — and view up to thirty years of price history and market-index context for any stock. The page that manages your data connections runs quickly and reliably even on its heaviest job, and the system now refuses to test any brand-new trading idea unless it was written down and registered first.

**What changed this time:** You can now open a new page that shows every idea the system has ever rejected — including, for the first time, ideas from its internal early-stage research that were never shown before — each with the exact reason it was turned down, a clear flag on the one idea that can never be tried again, and a plain-English rule explaining when (if ever) a rejected idea could be reconsidered. A small link on this new page — meant to jump straight to a related record — didn't quite work on the first pass; a fix is already in place but hasn't been double-checked yet, so this feature counts as nearly, but not quite, finished.

**What's next:** Next, we'll add a page showing how much statistical testing room is left before results become unreliable, and quickly confirm that the link-jumping fix on the new rejected-ideas page works as intended.

## Headline

Negative-results graveyard (J-19) ships read-only; held partial pending a canonical lineage-scroll re-verify

## Direction

**Signal:** holding
**Why:** iter-31 shipped J-19 (the negative-results graveyard) as byte-identity-clean additive work with an airtight regression proof across all three ledger files and the shared evidence/registry engine, but held it at partial because the canonical browser-qa lane recorded a P1 failure (the lineage-link auto-scroll, UT-07) that was fixed and live-verified only at the audit stage, not re-confirmed by that same canonical lane. No journey regressed and no anti-goal was newly violated, so momentum holds rather than advances this round; iter-32 folds in one more browser-qa pass on J-19 alongside starting J-17.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-02, J-06, J-07, J-08, J-09, J-16, J-18
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 1 of last 5

**Latest evaluator reasoning:** Iter-31 delivered J-19 (the negative-results graveyard, B-902) as a clean, purely additive read-only surface: a new pure `app.engine.graveyard` compose module + `GET /api/research/graveyard` + `/research/graveyard` page, reusing `registry.match_registration` (no second matcher) and recomputing no verdict. The core is browser-verified and the regression proof is airtight (all three ledger/registry state files + `evidence.py`/`referee.py`/`ledger.py`/`tools.py`/`config.yaml`/`verify_claim.py` byte-identical; divisor stays 8; 0 PASS). J-19 is scored partial, not passing, on one verification-integrity gap: the canonical browser-qa lane recorded UT-07 (P1) FAIL (the lineage link doesn't auto-scroll on SPA navigation); the auditor fixed it and browser-verified the fix, but the DoD-named canonical lane was never re-run against the fix. GOAL_ACHIEVED is unreachable regardless — J-17 and J-20..J-25 remain unbuilt.

## What was done

- Shipped `/research/graveyard`, a new read-only page listing all 14 non-passing hypotheses (7 canonical + 7 staging) with selectors, verdict, date, deflation, ledger origin, and registration lineage.
- Added a new pure backend module (`app.engine.graveyard`) and `GET /api/research/graveyard` endpoint that reuses the existing registry lineage matcher instead of reimplementing it.
- Flagged the one permanently-retired hypothesis (`ma_stack`) with a "permanent" marker and added a Revisit-protocol panel explaining the re-test rule, linked from every row.
- Surfaced the internal staging-ledger's rejected ideas for the first time; the honesty fence held (0 "Proven" anywhere, evidence endpoint and all ledger files byte-identical).
- Added a row anchor to `/research/registry` plus an in-audit scroll-into-view fix so a graveyard lineage link lands on its exact target row.
- Ran the canonical browser-qa lane against the iteration's one target journey (J-19): 11 of 14 checks passed, 1 P1 failure (lineage-link auto-scroll) was fixed and live-verified during audit but not yet re-confirmed by that same canonical lane — so 0 of 1 target journeys are counted as fully passing this iteration.

## What's left

- Journey J-19 ("Dead hypotheses are browsable so nobody retries them blindly") is holding at partial, not passing — needs one clean canonical browser-qa re-run confirming the lineage-link auto-scroll fix (already applied and live-verified during audit).
- Seven Must-have journeys remain unbuilt: J-17 (statistical-budget panel), J-20 (daily preflight verdict), J-21 (live-data drift guard), J-22 (referee self-audit), J-23 (watchlist concentration view), J-24 (per-stock risk-budget card), J-25 (drawdown-expectations panel).
- Two browser checks were skipped this iteration (empty-ledger state, loading skeleton) — both are covered by passing backend tests but not yet exercised live in a browser.
- `.claude/project-template.md` is still the unfilled generic template (pre-existing gap, unrelated to this iteration).
- The frontend's pure-logic test harness (`node lib/*.test.ts`) still cannot run in this environment (pre-existing sandbox limitation, unchanged from the prior iteration).

## Next step

iter-32 (FULL): build J-17, the statistical-budget panel (backlog B-903) — the next ready governance/ops surface now that J-18 and J-19 are delivered; read the B-903 backlog card first, ship no new Evidence Claim, and never re-submit a closed FAIL. Fold in the J-19 close-out without reopening its implementation: iter-32's browser-qa lane should record one clean, passing frame for the graveyard-to-registry lineage scroll (the fix is already in the tree and verified, just not yet canonically re-confirmed) — that alone flips J-19 from partial to passing. Non-blocking carry-forwards: live-execute the two skipped graveyard checks (empty-ledger state, loading skeleton), address the recurring pattern of the QA stage grading PASS from the unit suite while the canonical browser-qa artifact reads FAIL, and consider a shared hash-scroll hook if a third deep-linked table appears.

## Assumptions made

- iter-31 · goal-decomposer — Ambiguity: whether the STAGING ledger's non-PASS verdicts are in scope for J-19's "every non-PASS verdict," and whether composition should be backend- or frontend-side. We chose: surface both ledgers' non-PASS verdicts via a new backend `GET /api/research/graveyard` composition endpoint — the graveyard's purpose includes staging explorations and the honesty fence is preserved (staging carries 0 PASS). Reversible: yes
- iter-31 · goal-evaluator — Ambiguity: whether J-19 should score `passing` (its own goal.md acceptance is met; the lineage-scroll failure is an out-of-acceptance refinement now fixed) or `partial` (a DoD-named P1 browser case read FAIL and the fix isn't canonically re-verified). We chose: `partial`, applying the session's "correct-but-not-cleanly-canonical-verified = partial" discipline. Reversible: yes
- iter-30 · goal-evaluator — Ambiguity: the DoD literally read "≥14 ledger-derived rows" but the committed registry has 11. We chose: scored the backfill-completeness line as met by 11 rows, treating "≥14" as an uncomputed estimate and the substantive dedup clause as the real bar (14 raw entries minus 3 cross-ledger duplicates = 11 forced-correct). Reversible: yes
- iter-30 · goal-decomposer — Ambiguity: whether "every registered hypothesis" for the registry backfill meant the canonical ledger only or the union of both ledgers' distinct claims. We chose: the union of the pre-registered candidate rows and every distinct claim across both ledgers, deduplicated by hypothesis, each labeled by source. Reversible: yes
- iter-29 · goal-evaluator — Ambiguity: J-02's three inline "Not yet proven" score badges sit below the captured screenshot's fold, so no single pixel directly shows them. We chose: scored `passing`, backed by DOM assertions, factor-lab corroboration, leaderboard-scale evidence, and zero code diff since the last live capture. Reversible: yes
- iter-28 · goal-evaluator — Ambiguity: whether an honest all-FAIL rendering on five evidence journeys satisfies each journey's acceptance, or only its anti-goal guardrail. We chose: held all five at `partial`, since the proven-edge half of each journey's acceptance is absent — no certified edge exists on the current basis. Reversible: yes
- iter-28 · goal-decomposer — Ambiguity: how many iterations to keep re-attempting five evidence journeys when a staging exploration surfaces no promotable edge. We chose: a verify-only plateau-acknowledgement pass with no new evidence claim, since the full pre-registered candidate set already tested all-FAIL and re-submitting would self-defeat. Reversible: yes
- iter-27 · goal-evaluator — Ambiguity: whether 12 flagged "secret" findings — all planted fake keys inside the vendored framework's own test fixtures — count as a real credentials violation. We chose: scoped the check to Trendora's own product source, not the vendored framework's self-test tooling — not a violation. Reversible: yes
- iter-26b · goal-evaluator — Ambiguity: whether a journey whose proof attempt crashed the backend should read `partial` (capability real, verification incomplete) or `failing` (a verified negative outcome). We chose: `failing`, because a reproduced crash is a verified negative outcome, not just an unfinished verification. Reversible: yes
- iter-26 · goal-evaluator — Ambiguity: whether this iteration actually caused a memory crash or merely surfaced a pre-existing latent issue. We chose: scored it a regression regardless of causation, since a critical anti-goal was demonstrably, reproducibly violated and left unresolved. Reversible: yes

## Quick verify

From `reports/phase-goal-mcp-loop-iter-31-what-to-click.md`:

1. Open `http://localhost:3255/research` in your browser
2. Click the "Negative-results graveyard" card
3. Wait for the table to finish loading
4. Find the row whose Selectors chips include `factor=ma_stack`
5. Click that row's Lineage link (reads `factor-ma_stack-d10-h20 →`)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-31.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-31-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-31-review.md |
| Browser QA | FAIL | reports/phase-goal-mcp-loop-iter-31-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-31-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-31-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-31-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-31-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-31-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-mcp-loop-iter-31-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-31-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-31-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-31-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-31/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
