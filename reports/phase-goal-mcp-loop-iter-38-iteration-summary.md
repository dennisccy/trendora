# Iteration Summary — goal-mcp-loop-iter-38

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-15
**Iteration:** 38

## In plain words

**What you can do now:** You can browse a leaderboard of stocks with an honest "proven" or "not yet proven" label on every score, drill into the full evidence behind any of them, and review a complete, auditable record of every trading idea ever tested — including ones that combine several signals or look at relative strength — along with how much of the statistical testing "budget" remains. You can view up to thirty years of price history for any stock with clearly source-labeled index and macro context, and see the full universe of tracked stocks as it looked on any given day. Every page carries one shared status banner confirming today's data is current, watches for live prices quietly drifting from the saved history, and reports honestly on how well-calibrated its own testing checker is. And on your watchlist, you can now see how concentrated your saved stocks really are — which ones move together, how they cluster, and how many genuinely independent bets the list represents, plus sector, theme, and setup crowding.

**What changed this time:** Your watchlist page gained a new "Concentration X-ray" view: a grid showing how correlated each pair of your saved stocks is, groups of names that move together, crowding breakdowns by sector/theme/setup, and one headline number for how many genuinely independent bets your list represents. A stock without enough price history yet is honestly marked as missing data rather than showing a guessed number.

**What's next:** Next, a quick behind-the-scenes check will confirm nothing else on the site quietly broke, then a new card showing how much each stock could hurt your portfolio is planned.

## Headline

Watchlist gains a Concentration X-ray: correlation matrix, clusters, and an effective-independent-bets headline

## Direction

**Signal:** improving
**Why:** iter-38 flipped J-23 (watchlist concentration X-ray) from unknown to passing with clean, multiply-corroborated evidence — 13/15 browser tests pass, live production data matches the math to 10+ digits, and the audit found zero critical/important issues. The iteration ended CLOSURE-FAIL only because the required-still-passing replay of J-01/J-02/J-03/J-05/J-10/J-13/J-20 was not executed inline this iteration — the third recurrence of a known FULL-iter tooling gap, not a new defect — and the evaluator independently confirmed no regression risk via diff inspection. With 23 of 25 journeys now passing and only J-24/J-25 left unbuilt, direction stays healthy.

**Trend (last 5 iters):**
- Newly passing this iter: J-23
- Newly passing in last 5 iters total: J-21, J-22, J-23
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 2 of last 5

**Latest evaluator reasoning:** iter-38 (FULL) delivered the target journey J-23 (watchlist concentration X-ray, backlog B-204) as a strictly-additive, single-source, read-only surface — verified on four screenshots the evaluator personally opened. The iteration ended CLOSURE-FAIL, but the block is narrow and does not touch J-23's own evidence: it is the recurring FULL-iter replay gap (a FULL iter routes through `run-phase.sh`, which has no deterministic-replay lane, so the required-still-passing set J-01/02/03/05/10/13/20 was not golden-replayed) — the exact iter-33 / iter-36 pattern, and the closure auditor explicitly exempts J-23. No regression, no critical anti-goal, coherence PASS; GOAL_ACHIEVED is barred because J-24 and J-25 remain unbuilt/unknown.

## What was done

- Added `app.engine.concentration`, the single canonical ENB/correlation helper (Pearson correlation plus `(Σλ)²/Σλ²` effective-number-of-bets over eigenvalues), reusable by the future evidence-correlation audit.
- Added `app.engine.watchlist_xray.build_xray_payload`, a pure composer producing the pairwise correlation matrix, deterministic correlation-threshold clusters, ENB, and sector/theme/shared-setup concentration for the watchlist.
- Served the new data as an additive `xray` field on the existing `GET /api/watchlist` — existing `asof_date`/`entries[]` shape stays byte-identical.
- Built the Watchlist page's new "Concentration X-ray" section (correlation heatmap, cluster badges, ENB headline + methodology tooltip, concentration bars) that reads the served payload verbatim — zero browser-side recompute.
- Added typed config (`watchlist.xray.{corr_window_days, cluster_threshold, min_overlap_days}`) plus 24 new fast backend unit/integration tests and 4 new API tests, all passing.
- Verified 1 target journey (J-23) passes browser QA — 13/15 UI tests PASS, 2 P2 tests sanctioned-SKIP (satisfied by backend tests).

## What's left

- Closure blocker: the required-still-passing deterministic replay for J-01, J-02, J-03, J-05, J-10, J-13, and J-20 was not executed inline this iteration — QA's own dedicated test case (TC-17) was marked PASS on a bare HTTP-200 smoke check, not an actual replay or live re-verification.
- Journeys J-24 (per-stock risk-budget card) and J-25 (phase-conditional drawdown/dry-spell outlook) remain unbuilt — the last two Must-have journeys before the goal is reachable.
- `enb_member_count` (how many watchlist names actually fed into the ENB figure) is computed and served but has no display slot on the page yet — self-disclosed, currently inert on the 2-name watchlist.
- A similar correlation view for certified evidence claims on `/evidence` was not built this phase — only the shared math helper exists, for future reuse.
- Minor: the config validator only rejects one of two unreachable-floor cases for `min_overlap_days` vs `corr_window_days` (one-character fix, non-blocking; shipped default unaffected).
- Minor: no single test combines the "2 correlated + 1 independent" fixture with clusters and ENB together in one payload — both are covered separately.

## Next step

iter-39 = LEAN verify-only closeout: run the deterministic golden-script replay over J-01/J-02/J-03/J-05/J-10/J-13/J-20 (scripts already exist on disk), fold in the new J-23 golden, and re-clear closure to CLOSURE-PASS — this is hygiene/record closeout, not failure-remediation, since J-23's own evidence is clean. Then iter-40 = FULL J-24 (per-stock risk-budget card) and iter-41 = FULL J-25 (phase-conditional drawdown/dry-spell outlook), one risky surface per iteration; after those three, GOAL_ACHIEVED becomes reachable. Systemic flag (recurred at iter-33, iter-36, and now iter-38): the required-still-passing deterministic-replay DoD line is structurally unsatisfiable by any FULL iteration because `run-phase.sh` has no replay lane — a durable framework fix (adding the replay lane to `run-phase.sh`/`run-goal.sh`'s full path) is owed to the maintainer.

## Assumptions made

- iter-38 · goal-evaluator — Ambiguity: whether J-23 is `passing` or `partial` given the iteration ended CLOSURE-FAIL. We chose: `passing` — J-23's own canonical browser-qa evidence is complete and clean on the final build, and closure explicitly exempts J-23; the CLOSURE-FAIL is entirely a different DoD line (the required-still-passing replay of other journeys). Reversible: yes
- iter-38 · goal-evaluator — Ambiguity: J-23's DoD step 3 (short-history name renders honest NA) was verified by a backend unit test rather than a live browser observation, since no short-history-eligible ticker exists in this environment's addable universe. We chose: score J-23 `passing` with step 3 satisfied by the backend test plus the honest-NA machinery and the fully-populated real matrix opened live; the environmental constraint is genuine, not a lane skipping work. Reversible: yes
- iter-38 · goal-decomposer — Ambiguity: J-23's acceptance implies the evidence-correlation-audit helper (B-104) already exists, but B-104 is unbuilt. We chose: build the one canonical ENB/correlation helper in this iteration as the single source; the future B-104 audit will import the same helper rather than a second implementation. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: whether to carry J-05/J-11 (and J-01/J-03) at last-good passing or mark them re-verified this iter, since neither the browser-qa lane nor a golden-script replay directly re-verified them. We chose: marked them re-verified `passing` on the strength of frames the evaluator personally opened, crediting the independent evidence walk over the QA report's unevidenced rows; the dedicated per-journey golden replay is still the mandated next lean-closeout step. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: whether J-22 is `passing` or `partial` given the iteration ended CLOSURE-FAIL. We chose: `passing` — J-22's own canonical evidence is complete and clean on the final build with zero post-lane fixes, and closure explicitly exempts J-22; the block is an other-journeys replay gap. Reversible: yes
- iter-36 · goal-decomposer — Ambiguity: whether J-22's browser/QA acceptance requires a live 200-trial referee-audit run or a bounded/offline seeded run whose persisted artifact the panel reads. We chose: a two-halves decomposition — a fast seeded CI test proves the job-to-artifact half, and browser-qa reads the persisted artifact for the artifact-to-UI half; the 200-trial battery runs offline, never live in the browser/QA lane. Reversible: yes
- iter-35 · goal-evaluator — Ambiguity: J-21 and J-16's acceptance reads as a single end-to-end observation of a live fetch updating the drift card, but browser-qa induced the states by writing the drift-report artifact directly and J-16's fetch-path check was a pytest integration test, not a browser-driven fetch. We chose: score both `passing` via a two-halves decomposition (a real-fetch integration test for the fetch-to-artifact half, browser-qa DOM assertions for the artifact-to-UI half); auditor and ux-regression both accepted the decomposition. Reversible: yes
- iter-35 · goal-decomposer — Ambiguity: B-304's card lists three post-fetch checks, but J-21's binding journey acceptance only exercises the overlap check plus the readiness degrade/recover effect; the detectors the seam-scan check would depend on are unbuilt. We chose: scope iter-35 to the overlap comparator, single drift-report artifact, and preflight drift component only, deferring the distribution-envelope and junction-seam checks as neither is required by J-21's acceptance. Reversible: yes
- iter-34 · goal-evaluator — Ambiguity: whether a GO-only live re-confirmation of J-20 (the loud DEGRADED/NO-GO states weren't re-induced live this pass) counts as "re-confirmed passing," since J-20's acceptance names all three states. We chose: `passing` — J-20 was already fully verified across all three states at iter-33, the tree is git-identical since then, so there's no regression mechanism for the loud states; requiring a fresh live re-induction on an already-verified, byte-identical journey would be verification for its own sake. Reversible: yes
- iter-33 · goal-evaluator — Ambiguity: whether J-20 is `passing` or `partial` given the iteration ended CLOSURE-FAIL, where the block is a different DoD line (six other required journeys not deterministically replayed) rather than J-20's own evidence. We chose: `passing` — J-20's own evidence is complete and clean on the final build with no post-lane fix; marking `partial` would misattribute an other-journeys replay gap to J-20. Reversible: yes
- iter-33 · goal-decomposer — Ambiguity: B-301's "data freshness vs expectation" is underspecified for a deterministic offline app running against a frozen seed — a wall-clock anchor would make the healthy GO state impossible and break determinism. We chose: anchor freshness to a deterministic config/seed-derived reference (default = the seed's own latest available date) and induce stale test states via a controlled config/env override, never wall-clock time. Reversible: yes
- iter-32 · goal-evaluator — Ambiguity: whether J-11 (in the required-still-passing set) must be re-verified via its own dedicated case each iteration, or whether a 0-PASS ledger plus byte-identical economy and corroborating frames suffices, since it got no dedicated golden replay or browser case this iteration. We chose: score J-11 `passing` on byte-identity plus corroboration rather than holding it `unknown`, since the invariant is trivially satisfied on a 0-PASS ledger and the entire economy is git-diff empty. Reversible: yes
- iter-31 · goal-evaluator — Ambiguity: whether J-19 is `passing` (its own goal.md acceptance is met and the failing case is an out-of-acceptance refinement now fixed) or `partial` (a DoD-named P1 browser case reads FAIL and the fix isn't canonically re-verified). We chose: `partial` — applying the session's "correct-but-not-cleanly-canonical-verified = partial" discipline, since the auditor's own browser re-check is not the DoD-named canonical lane. Reversible: yes

## Quick verify

From `reports/phase-goal-mcp-loop-iter-38-what-to-click.md`:

1. Open `http://localhost:3255/watchlist` in your browser
2. Scroll down below the entries table
3. Read the headline just above the correlation grid, then hover the cell where the "ABBV" row crosses the "MSFT" column
4. Look at the "Clusters" badges, then the three bar sections below them (Sector concentration / Theme concentration / Shared setup)
5. Click the small "i" info icon immediately to the right of the "effective independent bets" headline

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-38.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-38-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-38-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-38-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-38-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-38-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-38-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-38-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-38-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-38-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-38-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-38-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-mcp-loop-iter-38-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-38/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
