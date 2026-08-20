# Iteration Summary — goal-market-compass-iter-4

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-08-20
**Iteration:** 4

## In plain words

**What you can do now:** Read a plain-English summary of today's market on the home page — the same numbers shown elsewhere on the page, said in words. See what changed since the last check-in, with an honest "nothing to compare yet" message on the very first stored day. See a list of stocks worth a second look next time, each with plain reasons why it was picked and why the others were not — right now, honestly, none clear the bar. Look up any stock's industry, now filled in for all 539 stocks, with where that information comes from explained on the Methodology page.

**What changed this time:** Nothing changed on any screen — four key pages were checked byte-for-byte before and after to prove it. Behind the scenes, the team reduced how much memory each database connection keeps ready, cutting the backend's overall peak memory use by nearly 29%. It's still using more than the goal's target amount, so the owner needs to decide if that's good enough.

**What's next:** Next, the owner needs to decide if the new memory savings are good enough — after that, the team will get back to proving that each evening's market briefing gets permanently locked in and can never be silently changed.

## Headline

DB connection cache halved (256MB -> 64MB); backend peak memory cut 28.9% but still over the 2.5GB target

## Direction

**Signal:** holding
**Why:** No journey crossed into passing this iteration — J-09's own headline number (backend memory) missed its target and landed at partial — and nothing regressed, so this isn't improving or regressing by the strict rule. But real journey-state movement happened in each of the last three iterations (J-01/J-02/J-03/J-04 promoted in iter-2, J-05/J-06 advanced in iter-3, J-09 measured for the first time in iter-4), so it isn't stalling either. It nets out to holding: steady, honest progress on the memory question, with two owner rulings now pending before the next full-depth build.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-01, J-02, J-03, J-04 (all in iter-2; J-01 promoted from partial, the other three from failing)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 2 total — 1 critical (AG-12, iter-3, found and fixed within the same iteration) and 1 minor (AG-2, iter-2, resolved in iter-3); 0 unresolved today
- Iters with no journey state change: 1 of last 5 (iter-1)

**Latest evaluator reasoning:** This iteration made one change: each database connection now keeps 64 MB of pages in memory instead of 256 MB. The backend's peak memory really did drop — from 4,837,420 kB to 3,439,100 kB, a 28.9% cut — but the goal asked for 2.5 GB or less, and 3.44 GB is 31% above that. The team reported the miss honestly and did not touch any of the owner-only limits to make the number look better. Nothing the user sees changed: four important pages were checked before and after and returned exactly the same bytes.

## What was done

- Product changes: config.yaml (`database.pragmas.cache_size` -262144 -> -65536), apps/backend/tests/test_db.py (pragma assertion updated to match)
- Halved the SQLite page-cache pragma per pooled connection (256MB -> 64MB); `pool_size` (24), `max_overflow` (44), and every other `database:` key left byte-unchanged.
- Re-measured standing-warm backend VmPeak via a lighter concurrent-burst path (no heavy backfill drill): 3,439,100 kB primary figure (28.9% cut from the 4,837,420 kB baseline), 4,493,232 kB on a 24-worker stress variant — both still over the 2.5GB (2,621,440 kB) target.
- Appended a new dated measurement (Addendum 40) to `reports/perf-budgets.md`, purely additive — the existing baseline entry is untouched (123 insertions, 0 deletions).
- Re-ran the concurrent-load burst check (zero `QueuePool` timeouts) and a byte-identity spot check across 4 endpoints (`/api/dashboard`, `/api/stocks`, `/api/market-phase`, `/api/compass`) — all byte-identical before vs. after the config change.
- Re-verified J-01 through J-04 (Required-still-passing regression smoke) still pass after the change, via deterministic replay plus the merged QA lane.
- Left every AG-10 owner-only limit (`memory_cap_mb`, `malloc_arena_max`, `pool_size`, `max_overflow`) byte-unchanged; recorded the honest over-target miss instead of compensating.
- Verified 0 target journeys pass browser QA this iteration — J-09's walkthrough is explicitly waived by goal.md (backend-only, no UI surface); verified instead via documentary evidence, and the numeric target itself was honestly MISSED, disclosed rather than hidden.

## What's left

- Journey J-07 (The Today page answers the ten-second read) failing — not this iteration's target; carried unchanged since iter-0.
- Journey J-08 (Market page moves over intact and history stays honest) failing — `/market` still returns 404; carried unchanged since iter-1.
- Journey J-05 (Each close freezes one next-session manifest, exported byte-consistently) partial — no live overnight close has ever been observed sealing a record; the make-up run is next iteration's plan.
- Journey J-06 (A frozen manifest never changes) partial — the "underlying run is unavailable" message can never render as written; needs an owner decision on rewording it or on how dated pages resolve.
- Journey J-09 (The backend fits the host) partial — measured backend memory is 3.44GB, 31% over the 2.5GB target; owner must rule whether that's acceptable or authorize one more lever (re-bounding the cache warm-up).
- Known limitation: a comment in `config.yaml` near the changed value still references the old 256MB figure (cosmetic, not functional; left alone to avoid touching an unrelated key).
- Known limitation: one pre-existing, unrelated test failure (`test_db.py::test_create_all_produces_expected_tables`) found but not fixed — stale table-registry bookkeeping, unrelated to this iteration's change.
- Three owner decisions still open and not blocking: rewording J-01's first two test steps, whether an empty "next-session focus" on the newest date is an acceptable honest result, and J-06's "unavailable" wording.

## Next step

First, the owner needs to rule on the memory result: accept 3.44 GB and call J-09 "The backend fits the host" done, keep the 2.5 GB target and authorize re-bounding the backend's cache warm-up (the one lever left), or set a different measured target — the team will not pick for itself. Once that's settled, the next build should run the J-05/J-06 make-up at full depth: remove and re-add the last two trading days to watch a real close actually seal a record, then delete and restore a day to watch the disclosure change, alongside the now three-times-overdue J-01–J-04 walkthrough recordings. That run starts two backends at once, so it should also cap the frontend build at 4 workers and stop the memory-pressure tests from copying the full database, and fix the J-01 test script that has now falsely failed twice on wrapped text.

## Assumptions made

- iter-4 · goal-evaluator — Ambiguity: J-09 has four of five acceptance steps met with evidence but the headline VmPeak step is unmet, and the status vocabulary has no rule for a journey whose supporting steps all pass while its one defining number misses. We chose: Scored J-09 `partial` (not `failing`), the same precedent used for J-06 at iter-3 — it records the real shape and writes the unmet step out in full; neither label affects the GOAL_ACHIEVED gate. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: J-09's acceptance text says a missed target must "stop for owner review," but goal.md doesn't say whether that means halting the whole loop or just stopping the tuning and reporting up while other work continues. We chose: Read it as "stop tuning and report" — verdict CONTINUE, with the owner ruling flagged at the top of the recommendation rather than pausing the session, since J-05 through J-08 don't depend on this number and one dev-workable lever (the cache warm-up re-bound) remains sanctioned. Reversible: yes — a pause or a goal.md edit can still halt it with nothing lost.
- iter-4 · goal-decomposer — Ambiguity: J-09's spec says to "re-run the standing-warm measurement" but doesn't say whether that requires the full ~31-minute heavy backfill drill or just the lighter pool-connection warm-up the original finding itself pointed to as the real driver. We chose: Directed the developer to the lighter concurrent-burst path, reusing the existing pool-pressure harness, to avoid repeating a heavy job on a host that had already frozen once that day. Reversible: yes — the heavier drill stays available as a fallback if the lighter path under-measures.
- iter-3 · goal-evaluator — Ambiguity: J-06's "unavailable" disclosure step is provably unreachable while its other steps are met, and the status vocabulary has no rule for a journey with both a proven defect and proven working parts. We chose: Scored J-06 `partial` rather than `failing`, writing the unmet step out in full so nothing is hidden; neither label reaches GOAL_ACHIEVED, so the choice costs nothing at the gate. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: J-01 through J-04 are flagged with a missing-walkthrough gap; fresh screenshots did land this iteration, but not the specific walkthrough capture that was asked for. We chose: Kept the gap flagged on all four, reading it as tracking the outstanding capture KIND (a walkthrough), not just "any newer image" — clearing it would lose the only scheduling hook for a make-up that's now overdue. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: an anti-goal rule bars a "historical view" from substituting "a newer manifest," but it doesn't say whether "newer" means a newer date's manifest or a newer version of the same date's manifest. We chose: Read it as date-scoped — serving the newest version for the SAME date is in-spec, because a later journey's own rule explicitly requires exactly that behavior. Recorded as OK, not a violation. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: a priority rule forbids bundling two risky journeys in one iteration, but the prior evaluator explicitly recommended building the manifest-freeze pair (J-05+J-06) together, and no rule addresses two journeys where one's steps all depend on the other's schema already existing. We chose: Built them together at full depth, treating them as one feature examined from two angles rather than two independent bets, since splitting them couldn't have improved diagnosability. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: one journey's first test step calls for a destructive, unrecoverable data rebuild, and its second step asks to pick a filter option that no longer exists now that coverage is complete — goal.md doesn't say whether a journey can pass with a skipped precondition and an unexecutable assertion step. We chose: Scored the journey passing because every acceptance clause (not the literal steps) is met with evidence, and read the unexecutable step's intent as satisfied more strongly by direct proof the option is gone. The request to reword both steps stays open with the owner. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: a candidate-explanation journey's steps require opening a candidate card "on the latest date," but zero stocks currently clear the selection rule on that date. We chose: Verified the empty-state steps live on the latest date and the card-opening steps on a real historical date with a genuine stored candidate, reading the assertions as being about traceability to stored data, not a specific calendar date. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: four journeys each require a recorded walkthrough, but the pipeline ran at lean depth so no walkthrough-recording lane executed for any of them. We chose: Scored all four passing (each has its own cited screenshot proving the behavior) with the missing recording tracked as a capture gap, not a reason to downgrade status; the make-up recording rides forward as a follow-up task. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: the plan already names the home page as where three new cards belong, but the home page is still the old, unmodified Dashboard, and its full reorganization is scoped to later journeys. We chose: Added the three new cards above the existing dashboard body on the home page, leaving final page layout and the old dashboard's move to a separate page for those later journeys. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: the plan describes one document covering both this iteration's content (session changes, narrative, candidates) and a later iteration's freeze/integrity fields (versioning, hashes, tamper-proofing), without saying which fields this iteration must actually build versus leave for later. We chose: Built only the content-computation logic and its content fingerprint this iteration, storing it in a new minimal table that the freeze work can extend additively later. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-4.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-4-dev.md |
| Review | PASS | reports/reviews/goal-market-compass-iter-4-review.md |
| Browser QA | BLOCKED | reports/phase-goal-market-compass-iter-4-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-market-compass/iter-4/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
