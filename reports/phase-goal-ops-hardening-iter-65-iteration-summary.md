# Iteration Summary — goal-ops-hardening-iter-65

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-08-11
**Iteration:** 65

## In plain words

**What you can do now:** Browse stock rankings, sector/theme views, backtests, and all five research tools with an honest "starting up / backend unavailable" status. Request a backfill over any date range with no hidden cap, and get a clear explanation when there's nothing new to fetch. See backtest results served instantly from storage, and see when the app is crunching numbers in the background. Pages load quickly because they only fetch what they need. The Data Manager page keeps its snapshot and gap counts current on its own. The app almost always answers its own health check quickly even during its biggest background job — this round's own check found only one slow reply out of over a thousand — but the team isn't yet ready to call that promise fully done, because the same check has swung between clean and rough on unchanged code from round to round.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team spent the round hunting for a slow spot inside the app's biggest background job, checking it four different ways (including a full real data job), and found none, so no product code changed. They also confirmed an earlier startup-timing fix actually took effect, and re-checked last round's one-off error page on the Scanner Runs screen — it did not happen again.

**What's next:** Next the team will target the one remaining short step inside the background job that caused this round's only slow reply, and try to get a shared, consistent way of measuring it so the "stays responsive" promise can finally be settled. They're also still waiting on the owner to decide whether the 2-second response promise should apply to long jobs too, or only to short ones.

## Headline

This round looked for a slow spot in the heavy background job and did not find one.

## Direction

**Signal:** holding
**Why:** No journey changed status this round — 7 of 8 Must-have journeys remain `passing`, and J-07 ("Heavy aggregates never take the service down") stays `partial` for the fifth consecutive round. The developer's four-level profiling of `factor_lab_all_warm` found zero stalls and this round's own live health-poll drill came back clean (1 breach of 1,057, 0 unanswered), but the same measurement has alternated clean/elevated on byte-identical code across recent rounds, so the evaluator held J-07 rather than promote it off one good reading. No regressions and no critical anti-goal violations, so the loop holds rather than moves.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: none
- Regressions in last 2 iters: none (both iter-64 and iter-65 explicitly rejected REGRESSION)
- Anti-goal violations in last 2 iters: iter-64: 6 new (all minor); iter-65: 4 new (all minor) — 0 unresolved critical in either
- Iters with no journey state change: 2 of last 2

**Latest evaluator reasoning:** This round looked for a slow spot in the heavy background job and did not find one. The developer measured the same job four different ways, including one full real data job, and none of the four showed the app pausing. So no code was changed at all this round. The health check answered every single time: 1,057 checks, 1,057 answers, none missed, and only ONE answer took longer than 2 seconds (2.37 seconds).

## What was done

- Product changes: No product change this iteration.
- Ran iter-52's interrupt-driven stall-profiling method against `factor_lab_all_warm` at four escalating fidelity levels (solo in-process, concurrent with the real `/api/health` route, through the real HTTP/ASGI stack, and a full live ingest) — zero stalls >0.30s found at every level.
- Re-ran the live 1 Hz health-poll drill through a real backfill: 1,057 polls, 1,057 HTTP 200, 0 unanswered, exactly 1 breach (2.370s) and 0 breaches inside `factor_lab_all_warm`; published as a new dated addendum in `reports/perf-budgets.md`.
- Attributed the round's single latency breach to a different, short phase (`coverage_membership_timeline_refresh`, its own 6.81s window) via the backend log's own phase markers.
- Confirmed `CHAIN_BACKEND_READY_WAIT_S`'s 90-second window fired live in this round's own engine log — the first firing since iter-64's 60→90 edit.
- Investigated iter-64's one-off `/scanner-runs` render error: no backend traceback found in either window and it did not recur this round; closed as "investigated, not reproduced."
- Verified all 8 target/required journeys pass merged browser QA (PASS 8/8) and raw deterministic replay (PASS 8/8, zero overturned rows this round).

## What's left

- Journey J-07 (Heavy aggregates never take the service down) stays `partial` — this round's drill was clean (1 breach of 1,057, 0 unanswered), but the metric keeps swinging between clean and elevated on unchanged code across rounds, so it wasn't promoted off one good reading.
- Two different measurement tools disagree on the same night: the developer's single-process counter said 1 slow reply of 1,057; the browser-QA lane's own separate counter said 8 of 240 — no shared counter yet exists to settle which is right.
- No showcase/demo lane ran this round, so the J-05 walkthrough capture remains unrecorded for a 7th round; the `evidence_makeup` flag stays set on J-05.
- Owner decision still pending, asked a 17th round: keep the 2-second health-ceiling promise for long jobs, or relax it to short jobs only.
- Owner sign-off still pending on the `scripts/automation/browser-qa-phase.sh` ordering fix, and a cost decision on running real ~17-minute data jobs every round.
- This round ran well past its time budget (8,247s against 3,600s) — a fifth consecutive over-budget round.
- The Regime Lab (iter-33/g) deferred for a 31st consecutive round.

## Next step

Keep going at lean depth — nothing forces a full round (prior verdict CONTINUE, coherence PASS, only two lean rounds in a row against a cadence of six, no new screen or button lands). Order for the next round: (1) bound the short "coverage and membership refresh" step, the last named in-code target left for J-07, then re-run the same 1 Hz health-poll drill and publish the raw file; (2) use one shared counter everywhere so the developer's and browser-QA lane's disagreeing numbers stop being two different answers to one question; (3) record what else the machine was doing next to the health-poll drill so the clean/bad alternation can be explained instead of argued; (4) ride along: record the J-05 walkthrough (unrecorded for 7 rounds); (5) owner — decide, for the 17th time, whether the 2-second health-ceiling promise applies to long jobs or short jobs only, and give sign-off on the `browser-qa-phase.sh` ordering fix and the cost of the real ~17-minute data jobs each round runs.

## Assumptions made

- iter-65 · goal-evaluator (2 of 2) — Ambiguity: the ledger's `resolved` flag has no defined meaning for a finding that was investigated exactly as specified but whose cause could not be found (iter-64/a, the one-off `/scanner-runs` error boundary). We chose: mark it resolved, with the residual unknown and a named next step written into the evidence string, rather than leaving it open indefinitely. Reversible: yes — a later evaluator can reopen it if the boundary recurs.
- iter-65 · goal-evaluator (1 of 2) — Ambiguity: this round's health-poll drill met TC-1's literal "0 breaches attributable to `factor_lab_all_warm`" bar (1 breach outside the phase, 0 inside), but J-07's own step text asks that every poll answer within budget, and the metric alternates clean/elevated on byte-identical code across rounds. We chose: keep J-07 `partial` rather than promote it off one clean reading. Reversible: yes — one more drill, ideally with a unified counter, can decide it.
- iter-64 · goal-evaluator (2 of 2) — Ambiguity: J-07's "every poll answers HTTP 200" clause was breached for the first time (1 of 930 polls got no answer within the client's 5.0s ceiling), and the tree has no rule for scoring a first-time non-answer inside an already-`partial` journey. We chose: keep J-07 `partial`, log it as a minor entry, and surface the fact in the owner section rather than converting it into a halt. Reversible: yes — a second non-answer would make `failing` the honest status.
- iter-64 · goal-evaluator (1 of 2) — Ambiguity: AG-8 *(critical)* requires both "never crash an existing page" and the honest contained-error-boundary failure mode; the `/scanner-runs` render error did both at once. We chose: score it a minor ledger entry, keep J-05 `passing`, no critical call. Reversible: yes — a later evaluator can re-score it if it recurs.
- iter-64 · goal-decomposer — Ambiguity: iter-63's next-step recommendation literally implied two separate real ingest jobs this lean round, on top of the one a lean round already carries by default. We chose: piggyback the attribution drill on J-05's own mandatory backfill, and prove the sentinel resolver's self-renewal at the unit level instead of a second live 20-minute replay. Reversible: yes — a later iteration can add a genuinely separate drill or live replay if the evidence proves insufficient.
- iter-63 · goal-evaluator (2 of 2) — Ambiguity: the `evidence_makeup` clearing rule says a flag clears "the moment a fresh capture lands, whatever the outcome," but J-07's own capture was a thin single frame not showing the clause's actual content, while J-05 got no capture at all. We chose: clear the flag on J-07 and keep it on J-05. Reversible: yes — a later evaluator can restore the flag.
- iter-63 · goal-evaluator (1 of 2) — Ambiguity: J-07's own metric measured 53x worse this round, but the verdict tree's REGRESSION limb only fires on a passing-to-failing transition, and J-07 has been `partial` since iter-51 — no rule covers a deterioration inside an already-partial journey. We chose: keep J-07 `partial`, log the deterioration as a minor entry, and return CONTINUE, since the journey's actual promise (service never goes down) was met outright with zero errors. Reversible: yes — the owner or a later evaluator can re-score it and halt on the next drill.
- iter-63 · goal-decomposer — Ambiguity: two adjacent scripts/automation fixes were listed, one tagged "(dev)" and one "OWNER-gated," without stating whether "(dev)" meant no owner go-ahead was needed. We chose: treat the replay-lane restart-race fix as dev-actionable and in scope, and leave the `browser-qa-phase.sh` ordering fix untouched and still owner-gated. Reversible: yes — a later evaluator or the owner can flag it and revert or re-gate the change.
- iter-62 · goal-evaluator — Ambiguity: `/data` keeping stale numbers after a failed refresh is more honest in one direction (real data isn't wiped by a blip) and less honest in another (the page no longer says the backend stopped answering), and AG-8 doesn't specify which matters more. We chose: score it a minor observation, not a violation, since the numbers shown are always real and the readiness badge still discloses outages independently. Reversible: yes — a later evaluator or the owner can re-score it.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-65.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-65-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-65-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-65-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-65/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
