# Iteration Summary — goal-ops-hardening-iter-64

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-08-11
**Iteration:** 64

## In plain words

**What you can do now:** Browse stock rankings, sector/theme views, backtests, and all five research tools with an honest "starting up / backend unavailable" status. Request a backfill over any date range with no hidden cap, and get a clear explanation when there's nothing new to fetch. See backtest results served instantly from storage, and see when the app is crunching numbers in the background. Pages load quickly because they only fetch what they need. The Data Manager page keeps its snapshot and gap counts current on its own. The app almost always answers its own health check quickly even during a heavy background job, though on the busiest moments a handful of replies can still lag.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team fixed the automatic testing robot so it stops picking a practice date it already used up (it now picks a fresh, unused day itself every time), added a safety check so the demo-recording tool never presses a "Start" button after an earlier setup step has already failed, ran a long-postponed heavy-memory test (it passed), and confirmed that the occasional slow reply during the app's biggest background job is a real, repeatable delay rather than a fluke.

**What's next:** Next the team will target the one specific slow step inside the app's biggest background job so it stops blocking the health check — the last piece needed to fully close the "stays responsive during heavy work" promise. The team is also still waiting on the owner to say whether the 2-second response promise should apply to long jobs too, or only to short ones.

## Headline

This round fixed the test robot, not the app.

## Direction

**Signal:** holding
**Why:** No journey changed status this round — 7 of 8 Must-have journeys stay `passing`, and J-07 ("Heavy aggregates never take the service down") stays `partial` for the fourth consecutive round. J-05's four-round-old hand-rotation defect was fixed at the mechanism level and self-verified live, and J-07's latency-breach jump was confirmed to reproduce (not host noise) — real progress on the verification substrate and on attribution — but no journey newly passed, nothing regressed, and no critical anti-goal violation fired, so the loop holds rather than moves this iteration.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: none
- Regressions in last 2 iters: none (both iter-63 and iter-64 explicitly rejected REGRESSION)
- Anti-goal violations in last 2 iters: iter-63: 7 new (all minor); iter-64: 6 new (all minor) — 0 unresolved critical in either
- Iters with no journey state change: 2 of last 2

**Latest evaluator reasoning:** This round fixed the test robot, not the app. The check script for J-05 "Aggregates are precomputed at ingest" now picks its own fresh, unused day at run time, so it can no longer break itself; the long-postponed memory-failure test finally ran and passed. The question the last round left open is answered: the slow health checks are real and repeat, not a busy machine — 59 of 930 checks took longer than the owner's 2-second limit, and for the first time one check got no answer at all. Seven of eight journeys pass; J-07 stays partly done, as planned.

## What was done

- Product changes: No product change this iteration. (One test-file docstring edit only; everything else is test-harness/tooling, journey-script data, docs, and reports.)
- Built a run-time sentinel-date resolver for J-05's golden so it self-selects an unused day at run time instead of being hand-rotated — closes a defect that recurred across 4 consecutive rounds; re-verified live against the DB after the round (returns a new, different day with 2,193 spare days left).
- Added a mutation guard to the demo/showcase recorder: no mutating click fires after a preceding step's precondition failed in the same script.
- Raised `CHAIN_BACKEND_READY_WAIT_S` from 60s to 90s at both call sites (`common.sh`, `replay-lane.sh`) — not yet self-verified; this run still sourced the old 60s value before the edit landed.
- Corrected a test docstring's inaccurate claim about a "pinned pre-fix oracle" — no assertion or logic changed.
- Ran the previously-unrun-for-4-rounds memory-pressure fault-injection test: 1 passed in 764.23s, with zero change to the shared log's MemoryError count.
- Attributed J-07's latency-breach jump: it reproduces (59 of 930 health polls breached the 2s ceiling, versus 1 of 1,078 two rounds ago) — a real, repeatable slowdown, not host noise.
- Verified 8 target/required journeys against merged browser QA (PASS 8/8); raw deterministic replay was 6/8, with two rows (J-05 step 13, J-07 step 2) overturned and reconciled after live re-checks against the frames and the database.

## What's left

- Journey J-07 (Heavy aggregates never take the service down) stays `partial` — the health-latency breach is now confirmed to reproduce (59/930 over the 2s ceiling), and this round produced the session's first-ever unanswered health poll; root cause of the slow phase (`factor_lab_all_warm`) is not yet fixed, only measured.
- `CHAIN_BACKEND_READY_WAIT_S`'s 90s bump is not yet self-verified — the next iteration must confirm it fired live from its own engine log before the item is closed.
- No showcase/demo lane ran this round, so the mutation guard and a fresh J-05 walkthrough capture were only proven at the unit level, not exercised live; the `evidence_makeup` flag stays set on J-05.
- `/scanner-runs` failed to render once during replay (a contained, honest error boundary was shown, not a blank crash) — cause unexplained; it did not reproduce on a live recheck minutes later.
- Owner decision still pending, asked a 16th round: keep the 2-second health-ceiling promise for long jobs (J-07 stays open until the app is faster), or relax it to short jobs only (closes J-07's last gap).
- Owner sign-off still pending on the `scripts/automation/browser-qa-phase.sh` line-ordering fix, and on the cost of running a real ~17-minute data ingest job every round.
- A newly-added note in `J-05.json` documents the wrong sentinel date window (should read 2005-03-01..2016-12-31) — small carried fix.
- The Regime Lab (iter-33/g) deferred for a 30th consecutive round; no capacity this round.

## Next step

Run the next round at lean depth. Order: (1) make the slow job phase `factor_lab_all_warm` (568s, 58 of 59 breaches) stop blocking the health check, then re-run the same 1 Hz drill and publish the raw numbers — the only agent-only path left to close J-07. (2) Find out why `/scanner-runs` failed to draw once and write down the answer even though it didn't reproduce. (3) Confirm from the next round's own engine log that the 90-second readiness wait actually took effect. (4) Small fixes: correct the wrong date window documented in `J-05.json`'s new note; check whether one job can stop writing two persisted run rows. (5) Record the J-05 walkthrough (unrecorded for six rounds). (6) Owner: the same 2-second health-ceiling question, asked a 16th time — decide whether the promise applies to long jobs or short jobs only; also pending: permission to fix the `browser-qa-phase.sh` ordering bug, and a cost decision on the ~17-minute ingest job that runs every round.

## Assumptions made

- iter-64 · goal-evaluator (2 of 2) — Ambiguity: J-07's "every poll answers HTTP 200" clause was breached for the first time (1 of 930 polls got no answer within the 5.0s client ceiling), while the tree gives no rule for scoring a first-time non-answer inside an already-`partial` journey. We chose: keep J-07 `partial`, log it as iter-64/b, and surface the fact in the owner section rather than converting it into a halt. Reversible: yes — one more drill decides it; a second non-answer would make `failing` the honest status.
- iter-64 · goal-evaluator (1 of 2) — Ambiguity: AG-8 (critical) requires both "never crash an existing page" and the honest contained-error-boundary failure mode; this round's `/scanner-runs` render error did both at once, and AG-8 doesn't say which half governs. We chose: score it a minor ledger entry (iter-64/a), keep J-05 `passing`, no critical call. Reversible: yes — a later evaluator can re-score it if it recurs.
- iter-64 · goal-decomposer — Ambiguity: iter-63's next-step recommendation literally implied two separate real ingest jobs this lean round (a control drill plus a second live J-05 replay) on top of the one a lean round already carries. We chose: piggyback the attribution drill on J-05's own mandatory backfill, and prove the sentinel resolver's self-renewal at the unit level instead of a second 20-minute live replay. Reversible: yes — a later iteration can add a genuinely separate drill or live replay if needed.
- iter-63 · goal-evaluator (2 of 2) — Ambiguity: the `evidence_makeup` clearing rule says "the moment a fresh capture lands, whatever the outcome," but J-07's own capture was a thin single frame not showing the clause's actual content, while J-05 got no capture at all. We chose: clear the flag on J-07 (a fresh capture literally landed) and keep it on J-05 (nothing was captured). Reversible: yes — a later evaluator can restore the flag.
- iter-63 · goal-evaluator (1 of 2) — Ambiguity: J-07's own metric measured 53x worse this round, but the verdict tree's REGRESSION limb only fires on a passing→failing transition, and J-07 has been `partial` since iter-51 — no rule exists for a deterioration inside an already-partial journey. We chose: keep J-07 `partial`, log the deterioration as a minor entry (iter-63/a), and return CONTINUE, since the journey's actual promise (service never goes down) was met outright with zero errors. Reversible: yes — the owner or a later evaluator can re-score it and halt on the next drill.
- iter-63 · goal-decomposer — Ambiguity: two adjacent scripts/automation fixes were listed, one tagged `(dev)` and one `OWNER-gated`, without stating whether `(dev)` meant no owner go-ahead was needed. We chose: treat the replay-lane restart-race fix as dev-actionable and in scope, and leave the `browser-qa-phase.sh` ordering fix untouched and still owner-gated. Reversible: yes — a later evaluator or the owner can flag it and revert or re-gate the change.
- iter-62 · goal-evaluator — Ambiguity: `/data` keeping stale numbers after a failed refresh is more honest in one direction (real data isn't wiped by a blip) and less honest in another (the page no longer says the backend stopped answering), and AG-8 doesn't specify which matters more. We chose: score it a minor observation (iter-62/e), not a violation, since the numbers shown are always real and the readiness badge still discloses outages independently. Reversible: yes — a later evaluator or the owner can re-score it.
- iter-62 · goal-evaluator — Ambiguity: this lean iteration's findings (a replay lane racing the pipeline's own restart, a golden consuming its own reserved date, a lane running a real 15-minute ingest every round) were all in the verification machinery, not the product, so it's unclear whether ESCALATE's "cross-cutting complexity" clause should fire. We chose: ESCALATE anyway, since the findings are load-bearing for the loop itself and no other lane had caught them. Reversible: yes — this only bound that round's default; the arbiter or owner could have run it differently.
- iter-62 · goal-decomposer — Ambiguity: whether depth-selection guidance should defer to a literal trigger test when the recommendation text and the trigger list read in tension. We chose: LEAN depth, since none of the four full triggers were literally true and the scope was two small, self-contained bug fixes with a nameable blast radius. Reversible: yes — the arbiter, a later evaluator, or the owner can force full for that iteration or the next.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-64.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-64-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-64-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-64-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-64/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
