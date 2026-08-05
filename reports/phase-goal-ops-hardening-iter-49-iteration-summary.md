# Iteration Summary — goal-ops-hardening-iter-49

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-05
**Iteration:** 49

## In plain words

**What you can do now:** Ask for a backfill over any date range and get an honest explanation when nothing new needed fetching — with no hidden cap on how large a range you can request. View backtest results instantly from stored data, without ever waiting on a live recalculation. See an honest notice while the app is crunching numbers in the background, instead of a page that just looks broken.

**What changed this time:** On the Data Manager page, backfilling an old missing day of price history now reaches a real "finished" status in about 17-18 minutes across three separate test runs, instead of spinning on "running" indefinitely (in the worst prior case, it never finished at all). But this round also uncovered a serious problem: opening the Factor Lab research page while that same backfill is still finishing can crash the whole app — and it did, for about 13 minutes, during this round's own testing. That crash is not caused by this round's fix; it is a real, unfixed bug in a different, older page.

**What's next:** Next, we'll stop the Factor Lab page from crashing the app while a backfill is running, then re-check all eight core capabilities against a healthy app.

## Headline

A historical-day backfill now finishes inside the advertised ~20-minute window on an idle machine.

## Direction

**Signal:** holding
**Why:** J-05 "Aggregates are precomputed at ingest, never on the fly" moved failing → partial: the fix genuinely meets its 20-minute bound on 3/3 idle-host runs, but the in-app job never reached a terminal status because a live backend crash (unrelated, out-of-scope code) interrupted it mid-run. That same crash dropped J-07 "Heavy aggregates never take the service down" from partial → failing (a 12m45s outage). No journey moved passing→failing under the evaluator's own regression test, and no journey newly reached full "passing" status this round, so the net journey table is a wash even though the round both fixed its own target and surfaced a serious new-old problem.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: J-01, J-03 (both promoted iter-48)
- Regressions in last 2 iters: none (J-07 dropped partial→failing in iter-49, but it was never `passing`, so it does not meet the evaluator's own regression definition)
- Anti-goal violations in last 2 iters: 13 new ledger entries (5 in iter-48, 8 in iter-49; one resolved in-audit in each round), 0 unresolved critical in either round; iter-49's outage (`iter-49/bp`) is explicitly scored `minor` in the machine severity field
- Iters with no journey state change: 0 of last 2

**Latest evaluator reasoning:** This round did the job it was given and then the app crashed for a different reason. The thing it set out to fix is fixed: adding one old day of history now finishes inside its twenty-minute promise on three separate live runs, and I checked those three runs myself from the raw measurement files rather than trusting the report. But while the checks were running, the whole backend died for twelve minutes and forty-five seconds.

## What was done

- Product changes: apps/backend/app/engine/data_manager.py, apps/backend/app/engine/forward_testing.py, apps/backend/app/engine/research.py
- Bounded `forward_aggregates_warm`: a ratio-based accumulator reuses one `as_integer_ratio()` conversion per observation across all 7 accumulator adds instead of recomputing it 7 times, proven byte-identical.
- Bounded `drawdown_expectations_warm`: column-projected `ScannerResult` reads (no full ORM row materialization) plus a once-per-invocation memoized phase-context timeline cut the slowest claim from 63.9s to 16.34s (3.9x) and made a previously-unfinishable claim complete in 50.94s.
- Added per-horizon and per-claim sub-phase timing logging so a slow run can be attributed to a specific horizon or claim, not just "the loop as a whole" (TC-2).
- Reassigned J-04's backend-restart/crash-recovery check to the automated test suite (which is allowed to kill/restart the service) after 3 rounds with zero real check from the browser-only lane; both new tests pass.
- Proved the full finalize tail reaches a terminal status within the 20-minute bound on 3/3 independent live runs (1,012.71s / 1,048.22s / 1,044.77s), with 45-49% memory margin under the cap.
- Audit found and fixed: a MemoryError handler that degraded to a MORE memory-hungry path instead of stopping (B3); a test that could pass without actually exercising the code it existed to test (T1); and a journey golden that targeted an already-consumed date, which would have produced a fabricated PASS (rotated, resolved).
- Browser QA: 0 of 2 target journeys (J-05, J-07) reached a PASS row this round — both blocked by a live 12m45s backend crash triggered by an unrelated, out-of-scope research page, not by this iteration's own fix (6/15 overall browser QA tests passed).

## What's left

- Journey J-07 (Heavy aggregates never take the service down) failing — a 12m45s backend crash during this round's own testing, triggered by opening the Factor Lab page while a backfill's finalize tail was running; the crashing code (`research.py`'s `compute_factor_lab_all`) is untouched by this iteration and is the next iteration's primary scope, bundled with the boot-path warm-up loop that has no interlock with it.
- Journey J-05 (Aggregates are precomputed at ingest, never on the fly) partial — the 20-minute bound is proven 3/3 on an idle host, but the in-app job never reached a terminal status through the product's own path because of the same crash; no lane has yet exercised the journey's own step 2 or 3.
- Journey J-06 (Pages load only what they need) partial — the Factor Lab page's own read is what triggered the crash; no fresh page-load budget numbers were recorded this round.
- Journey J-04 (Non-blocking boot with visible status) partial — backend restart/crash-recovery now has real, passing automated test coverage for the first time in three rounds, but the badge-in-the-same-window UI assertion is still unproven.
- The health check misses its own 2-second promise 6-9 times per run on all 3 runs, with two responses over 5 seconds each run — a pre-existing, disclosed, unfixed gap.
- J-08 and J-09 fell back to durability/live-spot-check evidence rather than a fresh lane row, because the backend was down when their checks were attempted.
- This round's QA report (verdict PASS) contradicts the same round's browser-QA report (FAIL) and audit (FAIL) — it must be regenerated next round, not read on its own.
- The demo walkthrough recorded zero steps for a second consecutive round, and several evidence screenshots are blank frames or duplicates copied forward from earlier rounds.

## Next step

Full depth (required by this ESCALATE verdict). First, stop the Factor Lab research page from taking down the whole app: put a limit on what that page loads into memory, and stop the start-up warm-up from running the same heavy calculation at the same time as a data job — landed together as one change, per five concurring reviews. Then run the eight journey checks last, with nothing touching the code afterward: J-04, J-08 and J-09 produced no real check this round because the app was down, and J-05's own check now points at 2012-01-04 (confirmed to have no snapshot yet). After that, finish proving J-05 through the app's own pages (not just an idle-host drill), and make the health check keep its two-second promise.

## Assumptions made

- iter-49 · goal-evaluator — Ambiguity: J-05 has a FAIL row from its own lane (the in-app job never reached a terminal status) but its 20-minute timing bound was proven 3/3 on live runs that used a fresh throwaway copy of the database on an idle host, not the journey's own in-app path — does that count toward moving the journey off `failing`? We chose: move it to `partial` (not `passing`) — the bound is proven, but no lane has ever executed the journey's own step 2 or 3, and the one executed row is a FAIL. Reversible: yes
- iter-49 · goal-evaluator — Ambiguity: the backend crashed for 12m45s during this round's own testing (AG-8, marked critical in goal.md), from a crash the iteration didn't introduce and was explicitly forbidden from fixing — neither goal.md nor the evaluator's own rubric says how to score a critical-class anti-goal breach an iteration didn't cause. We chose: log it as a `minor`-severity ledger entry and put the weight on the journey instead (J-07 moves partial → failing), verdict ESCALATE rather than REGRESSION, because the repair is fully specified and agent-owned and a halt would hand the owner a decision he doesn't have. Reversible: yes
- iter-48 · goal-evaluator — Ambiguity: J-06 had a PASS row from the deterministic replay and a screenshot showing an honest slow-loading state, but two new MemoryErrors landed inside the same replay window on a route the journey itself visits, and the timing of those errors relative to the replay is inferred from log position, not a stamped time. We chose: score J-06 `partial`, declining the lane's own PASS, because a page that exhausts the whole memory envelope isn't "loading only what it needs" under any reading — flagged the log-position inference as the weaker half of the reasoning. Reversible: yes
- iter-48 · goal-evaluator — Ambiguity: TC-7 says the full 8-journey lane must be the last product-code-adjacent event, and a post-lane change did touch product code (samples.py) — does that void the lane's rows even though no replayed journey exercises the changed code path? We chose: keep the lane's rows and promote J-01 and J-03 to `passing`, resting the promotion on database rows the replay itself created rather than the lane's verdict, while filing the TC-7 breach as its own ledger item rather than absorbing it silently. Reversible: yes
- iter-48 · developer — Ambiguity: the spec's Error Cases requirement reads literally as "a genuine non-memory exception during the finalize tail must flip the run row to `failed`," but that would mean unwinding a separate, deliberately hardened isolation boundary that exists so a derived-data fault never misreports a working ingest as failed. We chose: satisfy the "never silently running" half and not the literal "flips to failed" half, adding a test proving the new code path is caught by the existing isolation convention instead — flagged explicitly that a literal reading would see this as incomplete. Reversible: yes (no code change for this entry; a scope decision only)
- iter-48 · developer — Ambiguity: the spec forbids extending the existing incremental fast path to the historical-gap-insert case "unless the investigation itself proves a new, safe, tested alternative" — the spec doesn't prescribe what that alternative should look like, only that it must be proven and logged. We chose: a new code path that reuses previously-cached per-date tallies for already-cached dates and only resolves the genuinely new date, proven correct because the reused function is a pure function of a single date's own inputs and cannot be affected by inserting an unrelated date elsewhere — with a resolver-call-count test, a byte-identity oracle test, and a dedicated safety-regression test added. Reversible: yes — the new branch is additive; reverting restores the old always-recompute behavior.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-49.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-49-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-49-review.md |
| Browser QA | FAIL | reports/phase-goal-ops-hardening-iter-49-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-49-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-49-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-49-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-49-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-49-ui-test-plan.md |
| UX regression | UX-REGRESSION-FAIL | reports/phase-goal-ops-hardening-iter-49-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-49-qa.md |
| Audit | FAIL | docs/handoffs/goal-ops-hardening-iter-49-audit.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-49/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
