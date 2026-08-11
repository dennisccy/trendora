# Iteration Summary — goal-ops-hardening-iter-63

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-11
**Iteration:** 63

## In plain words

**What you can do now:** You can start a historical data update for any date range with no size limit, and the app clearly explains when there's nothing new to fetch. It starts up without freezing and shows its own status the whole time. Pages load only what they need, so browsing feels quick, and results like backtests come back instantly from storage instead of being recalculated live. The app also tells you when it's busy crunching numbers in the background — and while that's happening it almost always answers instantly, though this round showed it can occasionally take a few seconds longer than promised.

**What changed this time:** Nothing changed on any screen — this was an internal speed fix. The engine now answers its own health check faster while a background data update is finishing: one specific slow moment dropped from about 2.85 seconds to about 2.42 seconds. The target is under 2 seconds, so this is real progress but not a full fix. The team also repaired two problems in its own testing tools: the automated checker now waits for the app to genuinely finish restarting before testing it, and a rehearsal test date that kept getting reused by accident was fixed (twice over, after it got reused again on the very same day).

**What's next:** Before doing any more speed work, the team will re-run the same test unchanged to find out why the number of slow replies jumped from 1 to 53 this round.

## Headline

Health-check breach cut 2.85s→2.42s (not fully closed); J-05 golden & replay-lane restart-race fixed

## Direction

**Signal:** holding
**Why:** No journey changed status this iteration — 7 of 8 stayed `passing` and J-07 ("Heavy aggregates never take the service down") stayed `partial`, even though its own acceptance metric got measurably worse (53 health-check polls over the 2.0s ceiling this round, against 1 last round, cause unattributed). REGRESSION didn't fire because the tree's limb needs a passing→failing transition and availability itself is unbroken (983/983 HTTP 200, zero errors). With the sole remaining journey still not fully passing and no unblock landed this round, the project is holding rather than advancing.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: J-05 "Aggregates are precomputed at ingest, never on the fly" (promoted iter-61)
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 13 new, all minor (iter-62: 6, iter-63: 7); 0 unresolved critical
- Iters with no journey state change: 2 of last 3 (iter-62, iter-63)

**Latest evaluator reasoning:** Seven of the eight journeys were re-tested by machine this round and all seven passed, each with its own fresh picture. The eighth, J-07 "Heavy aggregates never take the service down", stays part-done — and this round its own measurement got worse, not better. The app answered every one of 983 health checks during an 18-minute background job (no errors at all, all day), but 53 of those answers took longer than the 2-second promise, against 1 slow answer in the same test last round. The team was honest about it: the developer, the reviewer and the auditor all wrote plainly that the round's main goal was not met.

## What was done

- Product changes: apps/backend/app/engine/data_manager.py
- Profiled `coverage_membership_timeline_refresh`'s live GIL-hold latency (never assumed) and applied a cooperative `time.sleep(0)` yield inside `_missing_data_diagnostic`'s chunked scan, cutting the sole measured `GET /api/health` breach from 2.849s to 2.420s (not fully eliminated)
- Added a byte-identity unit test proving the fix changes only scheduling, not output
- Rotated J-05's self-consuming golden test date off its already-consumed target — fixed twice this round, once by the developer and again by the audit after the round's own replay lane consumed the new date too
- Added a backend-readiness gate to the deterministic replay lane so it no longer starts testing while the app is still warming up after a restart
- Corrected a doc-comment in a non-shipping frontend test file
- Verified 8/8 journeys pass merged browser QA, with the raw deterministic replay lane going 7/7 with zero overturned rows for the first time this session

## What's left

- Journey J-07 ("Heavy aggregates never take the service down") stays `partial` — health-check latency breach count worsened to 53/983 polls over 2.0s (up from 1/1078 last round), and the cause is unattributed
- Owner's 15-times-asked policy question is still open: does the 2-second health-check ceiling apply to long (15-20 minute) background jobs, or only to short ones
- The `factor_lab_all_warm` phase's 52 breaching polls are unattributed, not confirmed pre-existing — needs a controlled re-run with no code change to compare against
- J-05's golden test date was consumed a fourth consecutive round by the same round that rotated it (re-rotated to 2010-11-22 by the audit); a self-rotating mechanism is still needed
- The showcase demo lane started a real, unrequested 5-date ingest job after its own setup steps failed, and narrated it as finished when it was still running 10+ minutes later
- The named memory-failure fault-injection test case has not been exercised for 4 consecutive rounds
- The replay-lane readiness gate's 60s default budget is shorter than the ~80s warm-up window it is meant to guard against
- Owner-gated and still untouched: `scripts/automation/browser-qa-phase.sh`'s TARGET_JOURNEYS line-ordering fix

## Next step

Run the next round at **lean** depth. Order: (1) Before any more speed work, re-run the same 18-minute health-check drill on unchanged code and compare — one control run tells whether the 1→53 slow-reply jump is a real slowdown or just a busier machine. (2) Make the J-05 check script pick its own fresh, unused date at run time — for the fourth round running, a hand-picked date was eaten by the same round that set it. (3) Stop the showcase recorder from pressing Start when its own setup steps failed — this round it began a real 5-day data job by accident and described it as finishing in seconds. (4) Small and written down: raise the readiness wait from 60s to 90s; run the named memory-failure test (4th round untouched); correct the new test's over-claiming docstring; record a J-05 walkthrough step (rides along, never the round's own goal). (5) Carried, untouched: iter-29/b + the badge wording after a failed warm-up (36th round unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az; iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj; iter-57/f; iter-57/l; iter-59/g; iter-59/h; iter-59/k; iter-62/e; iter-62/f. Deferred a 29th time: iter-33/g, the Regime Lab. Owner: the same one-sentence decision, now for the 15th round — keep the 2-second health-check promise for long background jobs (J-07 stays open) or apply it to short jobs only (J-07's last gap closes); still also waiting on permission to fix the one-line ordering bug in `scripts/automation/browser-qa-phase.sh`, and a cost decision on the automatic 15-18 minute data job that now runs every round.

## Assumptions made

- iter-63 · goal-evaluator — Ambiguity: methodology A.7 says the `evidence_makeup` flag clears "the moment a fresh capture lands — whatever the outcome," but J-07's fresh demo capture is one still frame that doesn't show the crash-free warm + healthy `/api/health` sequence its own Acceptance names. We chose: clear the flag on J-07 (a fresh capture did land — the rule is literal) and keep it on J-05 (nothing was captured for J-05 at all). Reversible: yes.
- iter-63 · goal-evaluator — Ambiguity: the verdict tree's REGRESSION limb only fires on a passing/already_passing→failing transition, but J-07 (already `partial` since iter-51) had its own acceptance metric measure 53x worse this round, with the cause unattributed. We chose: keep J-07 `partial`, log the deterioration as a minor ledger entry, and return CONTINUE — availability itself (983/983 HTTP 200, zero errors) was met outright and nothing displayed is wrong. Reversible: yes.
- iter-63 · goal-decomposer — Ambiguity: the iteration-state digest labels the replay-lane restart-race fix "(dev)" and the browser-qa-phase.sh TARGET_JOURNEYS ordering fix "OWNER-gated," but neither document states explicitly whether "(dev)" means no owner sign-off is needed. We chose: treat the restart-race fix as dev-actionable and in scope this iteration, leaving the OWNER-gated ordering fix untouched. Reversible: yes.
- iter-62 · goal-evaluator — Ambiguity: the `/data` page's fix keeps showing last-good numbers indefinitely through a permanent outage with no local "refresh failing" note — more honest in one direction (real data isn't wiped by one blip), less honest in another (the page doesn't say the backend stopped answering). We chose: score it a minor observation, not an AG-8 critical violation — the numbers shown are always real, and the global readiness badge is the canonical surface for backend-down state. Reversible: yes.
- iter-62 · goal-evaluator — Ambiguity: ESCALATE's "lean iteration surfaced cross-cutting complexity" clause was literally live, but everything found was in the verification/test machinery, not the product, and this session has twice refused to manufacture a clause match to buy a side effect. We chose: ESCALATE anyway — the findings (a false-FAIL restart race, a self-consuming golden) are load-bearing for the loop itself and no lane had reported them. Reversible: yes.
- iter-62 · goal-decomposer — Ambiguity: the dispatch prompt recommended full depth as "binding by default," but the self-check's own four literal triggers (prior ESCALATE/REGRESSION, prior coherence FAIL, hardening cadence due, new full-stack journey) did not literally hold this round. We chose: lean depth, not full — none of the four triggers was literally true, and the scope was two small, self-contained bug fixes. Reversible: yes.
- iter-61 · goal-evaluator — Ambiguity: promoting J-05 to `passing` needs a results row plus screenshot for the same iteration per methodology, but no lane produced a J-05 row this round (a lane failure, not a product failure), while durability rules say prior evidence stays valid when the product code is unchanged. We chose: promote J-05 `partial`→`passing` anyway, since the only concrete blocker on record was proven void and the product diff since the last passing evidence touched zero ingest/serving code. Reversible: yes.
- iter-61 · goal-evaluator — Ambiguity: full depth remained structurally justified (two journeys carry a `[NEW]` walkthrough clause that only runs at full depth), but none of ESCALATE's three literal clauses fired this round. We chose: CONTINUE with a full-depth recommendation rather than ESCALATE, following the methodology's tree over overall impression. Reversible: yes.

## Quick verify

From `reports/phase-goal-ops-hardening-iter-63-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser
2. Navigate to `http://localhost:3255/data`
3. In the job form, type "2026-05-02" into "Start date" and "2026-05-03" into "End date" (a fast weekend-only span), then click "Start"
4. Navigate to `http://localhost:3255/scanner-runs`
5. Click any row's date

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-63.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-63-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-63-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-63-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-63-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-63-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-63-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-63-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-63-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-ops-hardening-iter-63-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-63-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-63-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-63-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-63/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
