# Iteration Summary — goal-mcp-loop-iter-40

**Verdict:** PASS
**Iteration type:** goal-full
**Date:** 2026-07-15
**Iteration:** 40

## In plain words

**What you can do now:** You can browse a leaderboard of stocks with an honest "proven" or "not yet proven" label on every score, drill into the full evidence behind any of them, and review a complete, auditable record of every trading idea ever tested — including ones that combine several signals or look at relative strength — along with how much of the statistical testing "budget" remains. You can view up to thirty years of price history for any stock with clearly source-labeled index and macro context and see the full universe of tracked stocks as it looked on any given day, while every page carries one shared status banner confirming today's data is current, watches for live prices quietly drifting from the saved history, and reports honestly on how well-calibrated its own testing checker is. On your watchlist, you can see how concentrated your saved stocks really are — which ones move together, how they cluster, and how many genuinely independent bets the list represents, plus sector, theme, and setup crowding. And now, opening any stock also shows a "how much can this hurt" risk card — how much it swings, how big its overnight price jumps tend to be, its worst losing stretch on record, and how much room is left before the case for holding it would be considered broken — with every number ranked against the rest of the market, and you can sort the whole stock list by any of these risk measures too.

**What changed this time:** Opening any stock's page now shows a new "Risk budget" card that answers "how much can this hurt" — its typical and downside price swings, its overnight price-jump risk, its worst twenty-day losing stretch on record, and how much room is left before the case for holding it would be considered broken — with each number ranked against the rest of the market, and honestly marked "not enough data" for stocks with too little history. The same five risk numbers are now sortable columns on the main stock list too, so you can rank every stock by risk without opening each one, and a short explanation of each new number was added to the site's glossary page. One thing to note: the automated tool that normally re-checks every page in a real browser hit a technical hiccup this round, though an earlier check in the same process did see the new card working correctly with real numbers, and every calculation behind it was independently double-checked by hand.

**What's next:** Next, we'll add a panel showing how deep and how long a stock's price slumps have historically gotten, broken out by market conditions — the last planned feature before everything on the roadmap is built.

## Headline

Risk-budget card and leaderboard columns ship for every stock (J-24)

## Direction

**Signal:** improving
**Why:** J-24 (the per-stock risk-budget card + matching leaderboard columns) was built this iteration and cleared every gate — review PASS_WITH_NOTES, QA PASS (182 fast-lane tests + 19/19 functional cases), audit PASS_WITH_GAPS with an independent byte-match re-derivation of every served value, and CLOSURE-PASS with zero blocking issues — leaving only J-25 before all 25 Must-haves are built. The canonical UT-XX browser-qa lane was SKIPPED, not failed, due to a Chrome MCP infrastructure outage (6 tool-level attempts across 2 profiles all failed to bind the DevTools port); a separate functional QA pass drove a real browser ~17 minutes earlier and captured the card rendering correctly with real values. A formal goal-evaluator verdict and journey-history update for iter-40 had not yet been produced at the time of this summary, so this direction call rests on the review/QA/audit/closure chain rather than a recorded "passing" journey-history entry.

**Trend (last 5 iters):**
- Newly passing this iter: none recorded yet in the evaluator-log (iter-40 has not been formally evaluated; per closure/audit, J-24 was delivered and closed clean this iteration — see Why above)
- Newly passing in last 5 iters total (iters 35-39): J-21, J-22, J-23
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 2 of last 5

**Latest evaluator reasoning:** iter-39 is the lean verify-only closeout the iter-38 CONTINUE mandated, and it closed the recurring iter-38 CLOSURE-FAIL "required-still-passing deterministic replay" gap with ZERO product change. I verified every load-bearing claim against artifacts I personally opened, not the handoffs. Depth lean was mandatory (the deterministic-replay lane lives only in goal-iter-lean.sh; a full iter routes through run-phase.sh which has 0 replay-lane refs and would re-skip it — the exact iter-33/36/38 structural gap). *(Most recent logged evaluator entry — iter-40 itself has not yet been evaluated.)*

## What was done

- Added a new "Risk budget" card to every stock's detail page — ATR%, downside volatility, overnight-gap profile (median/p95/worst), overnight variance share, worst 20-day window, and distance-to-invalidation, each with a universe-percentile label.
- Added 5 matching sortable risk-budget columns (ATR%, Downside vol, Gap p95, Worst 20d, Dist. to invalidation) to the `/stocks` leaderboard, reading the same server-computed values as the detail card — no client-side recompute.
- Documented all 3 new metrics on the `/methodology` glossary page.
- Proved the three main scores (Leadership, Entry Quality, Risk) stay byte-identical — an automated test forces the new numbers to an absurd value and confirms no score moves.
- Rebuilt the backend's snapshot database so the new fields carry real values on the running instance; the auditor independently byte-matched every served value against an offline recomputation to full float precision.
- Canonical browser-QA lane (16 UT-XX target/regression cases): 0 verified — all SKIPPED after Chrome MCP failed to bind its DevTools port across 6 attempts and 2 profiles; the separate functional QA pass (19/19 TC-XX cases) drove Chrome MCP successfully ~17 minutes earlier and captured the card rendering live with real values.

## What's left

- Journey J-25 ("Drawdown and dry-spell expectations are visible, phase-conditional, and honest") is unbuilt — the last remaining Must-have before all 25 are complete.
- The 6 new `test_scoring.py` risk-budget integration tests have never run through pytest (the 30-year-history test fixture takes 30+ minutes and was killed mid-setup this session); behavior is independently confirmed via a standalone script and the auditor's byte-match re-derivation, but formal pytest certification is still owed.
- The canonical browser-QA lane never rendered the 5 new leaderboard columns, the 3 new `/methodology` glossary entries, or the required-still-passing regression journeys (J-01/02/03/05/10/12/13/20) in a live browser this iteration (Chrome MCP outage) — a live pass is recommended once the tool is healthy.
- The "short-history stock shows NA" acceptance path is architecturally unreachable in the current universe (every admitted stock has ≥346 bars, far more than any risk-budget window needs) — unit-tested but can never be browser-demonstrated without changing the universe floor or the spec.
- The recurring systemic gap persists: a FULL iteration has no deterministic-replay lane, so the required-still-passing journey set still needs a formal replay/re-verification pass (as iter-34/37/39 provided after prior FULL iterations).
- J-23's golden script has still never run through the deterministic `demo_runner --mode verify` replay lane (LLM-walked twice instead) — a non-blocking carry-forward.
- A parked, pre-existing uncommitted diff (`warmup.py` and others, predating iter-40) remains in the working tree — needs isolating at the release/commit step, not a product regression.

## Next step

iter-41 (FULL) — J-25 (backlog B-205, the phase-conditional drawdown/dry-spell expectations panel), the last unbuilt Must-have; after it, all 25 Must-haves would be passing and GOAL_ACHIEVED becomes reachable. Two non-blocking items recommended to fold in first: formally certify the 6 new `test_scoring.py` risk-budget tests via `pytest tests/test_scoring.py -k risk_budget -v` (their behavior is already independently byte-verified, just not pytest-certified), and record that J-24's "short-history renders NA" sub-path is unit-verified only — architecturally unreachable in the current universe, not a defect — so it isn't mistaken for a browser-verified pass. Also carry the recurring systemic flag (a FULL iteration has no deterministic-replay lane in `run-phase.sh`, so iter-41 should either run the closure replay inline or be followed by a lean verify pass) and re-cover the leaderboard columns + methodology page with a live-browser pass once Chrome MCP is healthy again (this iteration's canonical lane was infrastructure-skipped, not failed).

## Assumptions made

- iter-40 · goal-decomposer — Ambiguity: What "worst-20d window in the name's history" means — the name's full available as-of history, or a max_lookback-windowed recent span. We chose: The name's FULL available as-of history (bars ≤ as-of, from the per-symbol series already resident in the scan's bar cache — bounded, no new DB load), not a windowed recent span. Reversible: yes
- iter-39 · goal-evaluator — Ambiguity: The iter-39 DoD required `demo_runner.py --mode verify` over all 21 goldens, but only the 13 Required-still-passing goldens actually ran through demo_runner; the 8 Target journeys (J-01/02/03/05/10/13/20 + J-23) were re-verified by the LLM browser-qa lane instead, leaving open whether that counts as closing the iter-38 replay gap. We chose: Accepted the fresh LLM browser-qa walk as sufficient and bumped the 8 Target journeys' last_verified_iter to iter-39, since the evaluator personally opened real, byte-correct frames, zero product diff means no regression mechanism, and this two-lane split is the established lean-closeout pattern; J-23.json's golden still has zero demo_runner coverage, recorded as a non-blocking carry-forward. Reversible: yes
- iter-38 · goal-evaluator — Ambiguity: The iteration ended CLOSURE-FAIL, and the session's `partial` discipline normally withholds `passing` from a target with incomplete canonical evidence, but J-23's own canonical browser-qa evidence was complete and clean — the CLOSURE-FAIL was entirely a different DoD line (the required-still-passing replay of other journeys). We chose: Scored J-23 `passing` — the `partial` guard was fully satisfied on J-23's own evidence, and closure itself explicitly exempted J-23; the guard is honored at the overall verdict level (CONTINUE, not GOAL_ACHIEVED) instead. Reversible: yes
- iter-38 · goal-evaluator — Ambiguity: J-23's DoD step 3 (a short-history name renders honest NA) had no live browser observation because no short-history-eligible ticker exists in the addable universe. We chose: Scored step 3 satisfied by a backend unit test asserting the exact NA property plus the honest-NA machinery and the fully-populated real matrix opened live; the environmental constraint is genuine, not a lane skipping work. Reversible: yes
- iter-38 · goal-decomposer — Ambiguity: J-23's acceptance implies the evidence-correlation-audit helper (backlog B-104) already exists, but B-104 is unbuilt, leaving open whether to defer J-23 or build the helper itself. We chose: Build the one canonical ENB/correlation helper this iteration as the single source; the future B-104 audit will import the same helper rather than a second implementation. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: Whether to carry J-05/J-11 (and J-01/J-03) at last-good passing or mark them re-verified, since neither the browser-qa lane nor a golden-script replay directly re-verified them that iteration. We chose: Marked them re-verified `passing` on the strength of frames the evaluator personally opened, crediting the independent evidence walk over the QA report's unevidenced rows; the dedicated per-journey golden replay remained the mandated next lean-closeout step. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: Whether J-22 is `passing` or `partial` given that iteration ended CLOSURE-FAIL. We chose: `passing` — J-22's own canonical evidence was complete and clean on the final build with zero post-lane fixes, and closure explicitly exempted J-22; the block was an other-journeys replay gap. Reversible: yes
- iter-36 · goal-decomposer — Ambiguity: Whether J-22's browser/QA acceptance requires a live 200-trial referee-audit run or a bounded/offline seeded run whose persisted artifact the panel reads. We chose: A two-halves decomposition — a fast seeded CI test proves the job-to-artifact half, and browser-qa reads the persisted artifact for the artifact-to-UI half; the 200-trial battery runs offline, never live in the browser/QA lane. Reversible: yes
- iter-35 · goal-evaluator — Ambiguity: J-21 and J-16's acceptance reads as a single end-to-end observation of a live fetch updating the drift card, but browser-qa induced the states by writing the drift-report artifact directly and J-16's fetch-path check was a pytest integration test, not a browser-driven fetch. We chose: Scored both `passing` via a two-halves decomposition (a real-fetch integration test for the fetch-to-artifact half, browser-qa DOM assertions for the artifact-to-UI half); auditor and ux-regression both accepted the decomposition. Reversible: yes
- iter-35 · goal-decomposer — Ambiguity: B-304's card lists three post-fetch checks, but J-21's binding journey acceptance only exercises the overlap check plus the readiness degrade/recover effect; the detectors the seam-scan check would depend on are unbuilt. We chose: Scoped iter-35 to the overlap comparator, single drift-report artifact, and preflight drift component only, deferring the distribution-envelope and junction-seam checks since neither is required by J-21's acceptance. Reversible: yes
- iter-34 · goal-evaluator — Ambiguity: Whether a GO-only live re-confirmation of J-20 counts as "re-confirmed passing," since the loud DEGRADED/NO-GO states weren't re-induced live that pass and J-20's acceptance names all three states. We chose: `passing` — J-20 was already fully verified across all three states at iter-33 and the tree was git-identical since then, so there was no regression mechanism for the loud states; requiring a fresh live re-induction on an already-verified, byte-identical journey would be verification for its own sake. Reversible: yes

## Quick verify

From `reports/phase-goal-mcp-loop-iter-40-what-to-click.md`:

1. Open `http://localhost:3255/stocks/AAPL` in your browser
2. Read the small paragraph of text at the top of the "Risk budget" card
3. Open `http://localhost:3255/stocks` in a new tab
4. Scroll the table horizontally to the right until you pass the "Proximity to 52w high" column
5. Type `AAPL` into the "Search ticker or name…" box, then compare the number in the "ATR%" column for the AAPL row to the "ATR %" tile you saw in step 1

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-40.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-40-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-40-review.md |
| Browser QA | SKIPPED | reports/phase-goal-mcp-loop-iter-40-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-40-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-40-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-40-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-40-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-40-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-40-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-40-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-40-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-40-closure-verdict.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
