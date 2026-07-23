# Iteration Summary — goal-ops-hardening-iter-16
**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-23
**Iteration:** 16

## In plain words

**What you can do now:** Back-fill any historical date range with no size limit, and get a clear explanation whenever there's nothing new to fetch. See truthful status messages while the app starts up or if it crashes, instead of a blank or frozen screen. Get instant, accurate numbers on stock scans, sectors, and rankings, because the heavy calculations happen in the background as data comes in rather than while you wait on a page.

**What changed this time:** On the Backtest page, you can now tell at a glance whether the evidence you're looking at is fully current, a still-good previous version being shown while new data finishes processing in the background (with a timestamp so you know how fresh it is), or not yet calculated at all — instead of the page silently sitting there or showing nothing. Opening the page also no longer risks triggering a slow live recalculation just from viewing it.

**What's next:** Next, the team will close a gap where a routine daily update can briefly show an empty message instead of the last good numbers, and look into why a few page loads are still a bit slow while new data is being processed.

## Headline

Backtest evidence never makes you wait for a live recalculation anymore

## Direction

**Signal:** holding
**Why:** J-08 (Backtest evidence serves from storage only) landed this iteration and structurally closed the 178.74s cold-recompute blocker that stalled iter-15, with an in-audit fix for a false-claims banner bug — but no journey flipped to `passing`: J-01/J-03/J-04/J-05 held their prior status and J-06/J-07/J-08 all remain `partial`, pending a fallback-boundary fix, two missing screenshots, and an 11/68 latency-budget breach. Every remaining item is agent-owned rather than owner-blocked (unlike iter-15's STALLED), so direction holds steady into the next iteration rather than stalling or regressing.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: none (iters 12-16 all re-verified existing passing journeys or added new `partial` journeys — none flipped to `passing`)
- Regressions in last 5 iters: none by journey status (no passing→failing flips); iter-13 fired an overall REGRESSION verdict on the anti-goal axis (AG-8 escalated to a ~12-minute availability outage), not a journey flip
- Anti-goal violations in last 5 iters: 1 critical (AG-8) — carried/unresolved at iter-12, escalated to a full outage at iter-13 (drove that iteration's REGRESSION), resolved at iter-14; clean since (iter-15, iter-16)
- Iters with no journey state change: 2 of last 5 (iter-12, iter-15)

**Latest evaluator reasoning:** "The precompute-before-serve redesign (J-08) is real and structurally sound: `GET /api/backtest` and the MCP `query_backtest` tool are now pure readers that *cannot* reach `compute_forward_aggregates`, and the 178.74s blocking cold recompute that STALLED iter-15 is gone (worst read this iteration: 12.655s, a stored-row read under contention). I recomputed the operator's 68-row live poll CSV myself and it confirms the state machine end-to-end. No journey regressed, no anti-goal was violated, coherence is PASS — and the remaining work is concrete and agent-owned, so this continues rather than halts."

## What was done

- Split the Backtest evidence path into an ingest-only compute-and-persist function and a new read-only serving function that structurally cannot trigger a live recalculation — closing the 178.74s cold-recompute blocker that stalled iter-15.
- Added a three-state (ready / refreshing / not-yet-computed) disclosure to the `/backtest` evidence panel, with a generation timestamp and an explicit empty-state message where the page previously rendered silence.
- Redesigned the forward-aggregate cache's pruning from per-horizon deletion to a completeness-gated cutover, closing a confirmed live bug where two dataset versions could mix in one response.
- Landed 24/24 new/updated targeted backend tests and 0 TypeScript errors; ran the one authorized operator-supervised live pass (68-row poll) confirming the serving state machine holds end-to-end.
- Audit found and fixed an IMPORTANT defect mid-pipeline: the refreshing banner asserted two false claims ("still being warmed," "updates automatically") — corrected before this iteration closed.
- Re-verified J-01/J-03/J-05 passing via deterministic golden replay; carried J-04 passing without fresh evidence (kill/restart blocked this session).
- Verified 11/14 browser-QA test rows pass live (3 justified skips: the never-warmed empty state, the backend-down error card, and J-04's kill/restart).

## What's left

- Journey J-06 ("Pages load only what they need") stays partial — `/backtest` still breaches its committed ≤1.5s budget on 11/68 live polls while an ingest is actively running (max 12.655s).
- Journey J-07 ("Heavy aggregates never take the service down") stays partial — same latency residual, and step 1's "served from storage" claim is confirmed only for the gap-backfill shape, not yet for an as-of-advancing ingest.
- Journey J-08 ("Backtest evidence serves from storage only") stays partial — three open items: the common "ingest advances the latest date" case still serves an empty "not yet computed" message instead of the last-good evidence (ruled a required fix, not a design choice); the `not_yet_computed` state has zero live-browser evidence; and the one existing screenshot of the refreshing banner shows the pre-fix false copy, never re-rendered.
- J-04 ("Non-blocking boot with visible status") is carried as passing but was not freshly re-verified this iteration — a live kill/restart replay is required before any future GOAL_ACHIEVED call.
- The `conftest.py` `loaded_engine` test-fixture change (affecting 2 test files) remains unverified by an actual live test run.
- A fresh `demo.sh ops-hardening --session-live` walkthrough covering J-08's new steps has not been produced.
- Carried, unrelated: the pre-existing `test_db.py::test_create_all_produces_expected_tables` failure.

## Next step

FULL depth — the fix changes the same serving contract and adds a user-visible as-of label. No new features: close J-08, the sole item still holding J-06/J-07 back from `passing`. Agent-owned: (1) fix audit finding B1 so the fallback serves the last-good version labeled with its own as-of instead of falling to an empty state whenever the requested as-of has no complete version but an earlier one does; (2) capture live-browser evidence for the two still-unseen states — the corrected refreshing banner and `not_yet_computed` (on a disposable DB copy, never the working one); (3) root-cause the 11/68 latency breaches, which look like writer/reader contention on a stored-row read rather than compute cost, and record the result in `reports/perf-budgets.md`; (4) non-blocking: add a timezone designator to `evidence_generated_at`, decide on a self-heal for the sticky `refreshing` state, and de-duplicate the empty-state text. Operator (not agent-tractable this session): a live J-04 kill/restart replay — required before any GOAL_ACHIEVED — one `loaded_engine`-dependent test to close the fixture gap, and a fresh `demo.sh ops-hardening --session-live` run covering J-08's new steps. Owner, optional: if the ≤1.5s budget is not meant to govern reads taken during an active ingest, that needs a conscious, logged amendment in `reports/perf-budgets.md` — otherwise it binds as written and J-06 stays `partial`.

## Assumptions made

- iter-16 · goal-decomposer — Ambiguity: J-08 step 4 reads literally as "zero aggregate computation on ANY request," unqualified by is_latest/historical, but every sibling ingest-time cache carves out non-default/historical parameterization, and a fully literal reading would regress the pre-existing historical time-machine view. We chose: scoped the "never compute on request" guarantee to `is_latest == true` requests only, matching the ingest warm's own target and every one of J-08's 5 steps; historical `?as_of=` requests keep their existing lazy create-once-and-cache behavior, unchanged. Reversible: yes
- iter-16 · goal-evaluator — Ambiguity: goal.md J-08 step 2 promises the refresh window serves the last complete version "labeled with that version's served as-of," but the implementation resolves all three states strictly within one `asof_key`, so an ingest that advances the latest date yields `not_yet_computed` on a store full of complete versions — goal.md never states whether the fallback must cross as-of boundaries, and the auditor routed this call to the evaluator. We chose: ruled the fallback MUST cross as-of boundaries, keeping J-08 (and J-06/J-07) `partial` rather than accepting the iteration's own per-`asof_key` scoping as sufficient. Reversible: yes
- iter-16 · goal-evaluator — Ambiguity: J-04 is required-still-passing this iteration but has no golden replay script and rode the LLM browser-qa lane, which SKIPPED it because its steps need a backend kill/restart blocked this session — unclear whether it should carry over as `passing` or drop to `unknown`. We chose: carried J-04 as `passing` (basis: iter-13 precedent, iter-14's live pass, and confirmation its code surface is untouched) but deliberately did NOT advance `last_verified_iter` past iter-15, making a live J-04 replay a hard precondition for any future GOAL_ACHIEVED. Reversible: yes
- iter-15 · goal-decomposer — Ambiguity: whether UT-04's 211.8s concurrent-cache-miss finding is a J-06 budget violation, a J-07 responsiveness violation, both, or neither is not settled by goal.md's literal text. We chose: followed iter-14's evaluator, who already read UT-04 as blocking both J-06 and J-07, and built this iteration's entire scope on that same reading rather than re-litigating it. Reversible: yes
- iter-15 · goal-evaluator — Ambiguity: with the stacking pathology fixed, the residual `/backtest` cold-MISS is 178.74s over budget but the page renders honestly and the warm path is fast — whether that satisfies J-06/J-07's responsiveness clause (flipping both to passing → GOAL_ACHIEVED) or should stay `partial` pending an owner decision is pulled two ways by the goal text. We chose: did NOT flip J-06/J-07 to passing on the evaluator's own authority; kept both `partial` and returned STALLED to route the acceptance decision to the owner. Reversible: yes
- iter-14 · goal-decomposer — Ambiguity: J-07 step 4 permits either a test hook or a tightened cap in a throwaway process, but iter-13's actual REGRESSION trigger was concurrent load and the repo's existing "no leaked lock" tests are all monkeypatch-injected — unclear whether goal.md requires proof under a real induction plus concurrent callers, or whether the permissive reading suffices. We chose: required BOTH a real (non-monkeypatched) tightened-`ulimit -v` subprocess test AND a concurrent-caller test mirroring iter-13's trigger shape — a stricter reading, because the cheaper reading already missed this defect twice. Reversible: yes
- iter-14 · goal-decomposer — Ambiguity: the pump note authorized J-07's full-basis warm + VmPeak measurement as "operator-supervised" but didn't specify whether that means the agent runs the confined measurement itself or the human must literally type the launch command. We chose: wrote the standard path as the developer/reviewer running the confined pass directly under the declared host-guard caps, with an explicit operator-fallback if the environment blocks the process start. Reversible: yes
- iter-14 · goal-evaluator — Ambiguity: TC-6's literal test (induce memory pressure on the LIVE full-deep-basis process) was not executed — the operator judged it an unjustified hardware hazard — leaving open whether the two-leg evidence gathered instead is sufficient for J-07 step 4. We chose: ruled the two-leg evidence REASONABLE and did not treat it as a hard blocker requiring a halt, but also did not upgrade it to a literal PASS — a live-process induction remains a candidate owner-authorized follow-up. Reversible: yes
- iter-14 · goal-evaluator — Ambiguity: AG-8 drove iter-13's REGRESSION, and UT-04 shows the same concurrent-load trigger still produces a 211.8s `/backtest` anomaly this iteration — is AG-8 resolved, or still open because the fix doesn't fully hold under the reproduced trigger? We chose: marked AG-8 RESOLVED, because its text forbids a crash/memory-exhaustion/unbounded-load and UT-04 is none of these — it is a distinct, non-critical latency regression that keeps J-06/J-07 partial instead. Reversible: yes
- iter-13 · goal-evaluator — Ambiguity: whether escalating AG-8's observed severity from "silent internal abort" (iter-12) to "a full ~12-minute availability outage requiring an operator hard-restart" (iter-13), on byte-unchanged code triggered by concurrent test load rather than this iteration's own product diff, counts as newly-discovered damage (firing REGRESSION) or the same carried bug merely re-observed (continuing as iter-12 did). We chose: fired REGRESSION, since the specific justification iters 11/12 used to withhold the halt (smaller blast radius, self-recovers) is directly falsified this iteration and the affected property (availability) is exactly what this ops-hardening goal exists to guarantee. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-16-what-to-click.md`:

1. Open http://localhost:3255/backtest in your browser
2. Look at the small status pill near the top of the page (backend readiness indicator)
3. Scroll all the way to the bottom of the page, past the "Leadership cohorts" section
4. Navigate to http://localhost:3255/data. In the "Start a fetch / backfill job" card, type your chosen not-yet-snapshotted date into BOTH the "Start date" field and the "End date" field (making it a single-day job), leave "Job kind" set to "Backfill snapshots", then click "Start"
5. Every ~30 seconds, reload http://localhost:3255/backtest and check the bottom of the page again

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-16.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-16-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-16-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-16-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-16-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-16-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-16-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-16-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-16-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-ops-hardening-iter-16-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-16-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-16-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-16-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-16/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
