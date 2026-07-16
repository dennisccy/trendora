# Iteration Summary — goal-mcp-loop-iter-41

**Verdict:** PASS
**Iteration type:** goal-full
**Date:** 2026-07-16
**Iteration:** 41

## In plain words

**What you can do now:** You can browse a leaderboard of hundreds of stocks where every score is honestly marked "proven" or "not yet proven," open a full audit trail behind any tested idea, and view up to thirty years of price history with sourced index and macro context. You can browse every trading idea the system has tried — including the rejected ones — check how much statistical testing budget remains, and read a shared daily trust banner that also watches for live-data drift. On the Watchlist page you can see how concentrated your saved list is, and on any stock's page you can see a "how much can this hurt" risk breakdown ranked against the whole market. And now, opening any tested idea's own record, you can read what following it has historically felt like to hold — typical and worst-case losing depth, how many days it usually spent underwater, how long recovery usually took, and the longest losing streak on record — broken down by the market mood at the time, each with an honest sample size.

**What changed this time:** Every certified idea's page now shows a new panel: what following that idea has historically felt like to hold, split by the market conditions in place when you'd have started (calm uptrend, pullback, correction, bear market, or recovery) — typical and worst-case drawdown depth, days spent underwater, time to recover, and the longest losing streak, each backed by an honest sample count and a plain "not enough history yet" label wherever the sample is too thin to trust. This shows up on all seven tested ideas today, including the ones that failed their own test — it's a history lesson, never a forecast. A one-time ~9-second slowdown on first load after a data refresh was caught and fixed with caching before anyone but the testers saw it; every visit after that stays fast.

**What's next:** Next is a housekeeping round that re-confirms everything built so far still works correctly together — after that, every feature currently on the roadmap will be complete.

## Headline

Drawdown & dry-spell expectations panel ships on /evidence claim cards (J-25 — last Must-have)

## Direction

**Signal:** improving
**Why:** J-25 — the last unbuilt Must-have journey — was built and verified this iteration: browser QA passed 14/14 with zero skips, and the audit independently re-derived every served phase cell for all 7 ledger claims with zero mismatches, while closure, review, QA, and UX regression all cleared with no blocking issues. The formal goal-evaluator pass that would flip J-25 to "passing" in `journey-history.json` had not run as of this summary, and no regressions or new anti-goal violations were found anywhere in the pipeline. Only the iter-42 lean closeout (a deterministic replay of the full required-still-passing set) stands between here and GOAL_ACHIEVED.

**Trend (last 5 iters):**
- Newly passing this iter: none recorded yet — the goal-evaluator has not yet run for iter-41; J-25 is built and gate-verified (browser QA 14/14, audit zero mismatches, CLOSURE-PASS) pending that formal confirmation
- Newly passing in last 5 iters total: J-22 (iter-36), J-23 (iter-38), J-24 (iter-40)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 2 of last 5 (iter-37, iter-39 — lean verify-only closeouts)

**Latest evaluator reasoning:** (most recent available — from iter-40; no `eval.md` exists yet for iter-41) iter-40 delivered J-24 as a textbook strictly-additive, single-source, read-only surface, and I verified every status change against artifacts I personally opened, not the handoffs. NOT GOAL_ACHIEVED (J-25 unknown/unbuilt — no Must-have may be unknown at achievement). NOT ESCALATE (already full; review PASS_WITH_NOTES not fail-open; J-24 passed first build, not a 2-consecutive same-journey failure; the Chrome-MCP outage is an infra condition, not cross-cutting product ambiguity). CONTINUE.

## What was done

- Added two new append-only columns (`underwater_days`, `time_to_recover_days`) on `ForwardReturn`, computed in the same insert pass as the existing `max_drawdown` — zero extra bar reads.
- Built a new pure aggregation (`compute_drawdown_expectations`, plus a cached variant) joining stored forward-return stats to the causal market phase at entry, emitting per-phase median/p90/n distributions and a walk-forward-cadence longest-losing-streak figure.
- Wired an additive `expectations` field onto the existing `GET /api/evidence` endpoint and a new "Historical drawdown & dry-spell expectations" panel inside every `/evidence` claim card.
- Ran a full-universe (30-year, 590-symbol) database rebuild twice to populate the new columns; measured peak memory (~2.7GB VSZ / ~1.79GB RSS on both runs) safely under the 6144MB cap.
- Discovered and fixed a ~3x `/api/evidence` latency regression (9.3-9.6s uncached) by caching the new aggregation in the existing shared `EventStudyCache` table — warm reads now 6-17ms.
- Verified J-25 (the 1 target journey) passes browser QA — 14/14 UI tests PASS, 0 skipped — including live re-verification of all 10 required-still-passing journeys in the same pass.
- Added 29 new backend tests for the new helpers/aggregation plus 4 new evidence-endpoint tests and 1 new DB-migration test; QA independently confirmed 189 backend + 42 frontend tests pass with zero regressions, all pre-existing tests unedited.

## What's left

- Formal goal-evaluator confirmation and `journey-history.json` update for J-25 is still pending — this iteration's own dev/review/QA/browser-QA/audit/ux-regression/closure gates are all clean, but no `eval.md` had been written for iter-41 as of this summary.
- iter-42 lean closeout: deterministic golden-replay of the full required-still-passing set, folding in the never-replayed `J-23.json`, `J-24.json`, and the new `J-25.json` goldens (a systemic FULL-iteration replay gap recurring since iter-33).
- Minor: the new phase badges in the expectations table render flat gray instead of the app's single-source phase-color mapping (MINOR, tracked by reviewer/audit/QA/ux-regression, non-blocking).
- Minor: the visible method note doesn't yet disclose that "time-to-recover" excludes observations that never recovered within the horizon from its median/p90 (GAP, deferred, non-blocking).
- Minor: an `evidence.py` docstring lists 4 test files that never actually call `build_evidence_payload` (documentation-only, non-blocking).
- J-15 and J-16 (performance / data-jobs journeys) had no dedicated browser-QA test case in this iteration's plan; both are otherwise evidenced (perf-budgets report, static code-touch analysis) but the next iteration's UI test plan should add dedicated cases.

## Next step

No goal-evaluator verdict exists yet for this iteration, so this is carried from the audit's own recommendation (`docs/handoffs/goal-mcp-loop-iter-41-audit.md`), consistent with the pattern the last several iterations' evaluators have already set: Proceed. J-25 — the last unbuilt Must-have — is delivered, correct, and independently verified; GOAL_ACHIEVED becomes reachable after the iter-42 lean closeout, whose job is the deterministic golden-replay of the full required-still-passing set, folding in the never-replayed `J-23.json`, `J-24.json`, and the new `J-25.json` goldens. Two small, non-blocking polish items are optional for a future `/evidence` touch: add a method-note sentence disclosing that time-to-recover excludes never-recovered observations, and align the new phase badge with the app's shared `phasePosture` color mapping.

## Assumptions made

- iter-41 · goal-decomposer — Ambiguity: B-205's "pure aggregation helpers" left open whether underwater-duration / time-to-recover are stored or computed on-read. We chose: per-observation path stats over the first-horizon post-snapshot bars, stored additively on ForwardReturn alongside max_drawdown (J-86 precedent) and backfilled over the deep window — because on-read per-observation bar reads on /api/evidence would regress the J-15 latency budget, and the deep historical phases need populated coverage to clear the floor. Reversible: yes (additive columns / additive field / additive panel)
- iter-40 · goal-decomposer — Ambiguity: B-201 doesn't define the risk-budget "worst-20d window" search span — a name's full as-of history vs. only the max_lookback-windowed recent span (materially different numbers). We chose: compute over the name's full available as-of history (bounded per-symbol, no whole-table load), matching the honest "how much can this hurt (ever)" framing. Reversible: yes
- iter-40 · goal-evaluator — Ambiguity: J-24's DoD requires passing via browser-qa-agent, but the canonical lane recorded all 16 UT-XX SKIPPED (a Chrome-MCP port-binding outage) — leaving open whether J-24 is passing or partial. We chose: passing — the SKIP is a documented infra outage (not a fail-open past a FAIL), closure found the guard inapplicable, and the target's acceptance is independently pixel-verified from other working lanes plus the auditor's full-float-precision byte-match; zero post-lane fixes means no partial-trap. Reversible: yes
- iter-39 · goal-evaluator — Ambiguity: the DoD literally required `demo_runner --mode verify` (deterministic replay) over all 21 goldens, but only the 13 Required-still-passing goldens ran that way — the 8 Target journeys (incl. J-23) were re-verified via the LLM browser-qa lane instead. We chose: accepted the fresh LLM browser-qa walk as sufficient re-verification and bumped last_verified_iter for those 8 journeys — matches the established lean-closeout split (iter-34/36/37 precedent) and zero product diff means no regression mechanism. Reversible: yes
- iter-38 · goal-evaluator — Ambiguity: the iteration ended CLOSURE-FAIL on a replay gap affecting OTHER journeys, not J-23's own evidence — open whether J-23 itself is passing or partial. We chose: passing — J-23's own canonical evidence is complete and clean on the final build (closure explicitly exempts it); marking partial would misattribute an other-journeys gap to J-23. Reversible: yes
- iter-38 · goal-evaluator — Ambiguity: J-23's DoD step 3 (short-history name renders NA) had no live-browser case because no short-history-eligible ticker exists in the addable universe — verified instead by a backend unit test. We chose: scored J-23 passing with step 3 satisfied by the unit test plus the honest-NA machinery and the fully-populated real matrix observed — the environmental constraint is genuine, mirroring the iter-35/36 fetch→artifact→UI two-halves pattern. Reversible: yes
- iter-38 · goal-decomposer — Ambiguity: J-23's acceptance implies a shared ENB/correlation helper already exists (from the unbuilt B-104 evidence-correlation audit) — open whether to defer J-23 or build the helper now. We chose: build the one canonical ENB/correlation helper in app.engine.concentration now, so the future B-104 work reuses it — single-source constraint honored even though B-204 lands first. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: the DoD required J-01/J-03/J-05/J-11/J-17/J-18/J-19/J-20 to be live-re-verified, but neither the browser-qa lane nor a golden replay covered the required set cleanly — closure named J-05/J-11 as unverified. We chose: marked J-05, J-11 (and J-01/J-03) re-verified passing at iter-36 on frames the evaluator personally opened, crediting that independent evidence walk over the QA report's unevidenced rows; the dedicated golden replay is still owed as the next lean-closeout step. Reversible: yes
- iter-36 · goal-evaluator — Ambiguity: the iteration ended CLOSURE-FAIL on a DIFFERENT DoD line (other journeys' replay), not J-22's own evidence — open whether J-22 is passing or partial. We chose: passing — J-22's canonical browser-qa evidence is complete and clean on the final build with zero post-lane fixes; closure itself exempts J-22 from the blocking finding. Reversible: yes
- iter-36 · goal-decomposer — Ambiguity: J-22's acceptance mixes a "live end-to-end run" reading against the Consistency clause's "re-reads the persisted artifact, nothing recomputed in the UI" — open whether QA/browser-qa needs a live 200-trial run or a bounded/offline seeded run whose artifact the panel reads. We chose: a two-halves decomposition (mirroring iter-35's J-21 pattern) — a fast seeded CI test proves job→artifact, and browser-qa reads the persisted artifact for artifact→UI; the 200-trial battery runs offline, never live in-browser (anti-goal #8 discipline). Reversible: yes
- iter-35 · goal-evaluator — Ambiguity: J-21/J-16's acceptance reads as one end-to-end "click Fetch → live re-adjusted bars → card updates" observation, but browser-qa induced UI states via direct artifact injection and J-16's fetch-path check was a pytest integration test — no single browser observation covered the full path. We chose: passing on a two-halves decomposition (fetch→artifact proven by a real-`_run_job` integration test; artifact→UI proven by browser-qa's direct-injection DOM assertions) — the artifact is the single-source seam both readers consume. Reversible: yes

## Quick verify

From `reports/phase-goal-mcp-loop-iter-41-what-to-click.md`:

1. Open `http://localhost:3255/evidence` in your browser
2. On the FIRST claim card (its "Hypothesis" row shows badges "factor=leadership_score", "decile=10", "horizon=20"), scroll down past the 5 existing fields (Hypothesis, Out-of-sample verdict, Control comparison, Registration date, Forward-walk score-to-date)
3. In that table, find the "Expansion" row (the first row) and read its "Max-DD depth" cell
4. Scroll down to the "Correction" row (third row) and read its "Longest losing streak" cell
5. Scroll to the very bottom of the panel and read the two sentences below the table

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-41.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-41-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-41-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-41-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-41-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-41-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-41-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-41-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-41-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-41-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-41-qa.md |
| Audit | PASS | docs/handoffs/goal-mcp-loop-iter-41-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-41-closure-verdict.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
