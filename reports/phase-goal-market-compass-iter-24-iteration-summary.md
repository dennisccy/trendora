# Iteration Summary — goal-market-compass-iter-24

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-28
**Iteration:** 24

## In plain words

**What you can do now:** See each stock's honest, mostly filled-in sector label. See why each next-session candidate was picked, and why others weren't. Browse the two trading days recovered from August's data incident, with corrected volume numbers, in the price history. The whole data-repair effort behind those numbers has been proven, through a real supervised test, to serve correctly on screen — not just sit correctly in the database.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team fixed a bug in the automated tool that starts the app for testing: it now locks in, once at the very start of each test run, which copy of the data to use, and refuses to start anything later that drifts from that choice. This closes the hole that let last round's routine testing accidentally reach the real, protected database instead of a safe practice copy.

**What's next:** Next, the team plans to check whether the app's memory use now fits the machine it runs on, and to fix a separate bug that let this round's own safety re-check of the three working features silently skip itself without telling anyone.

## Headline

Fixed the goal-mode launcher bug that let replay re-tests silently boot the protected database

## Direction

**Signal:** holding
**Why:** No journey moved this iteration — J-11 "Incident-bounded clean regeneration of derived state" stayed passing on a documentary re-check of an owner ruling, not a fresh browser pass, and J-01/J-04/J-10 held on iter-23 evidence because their own regression re-test silently never ran (a separate plan-parsing bug the evaluator found on its own). Nothing regressed and no anti-goal was newly broken, but J-07 "The Today page answers the ten-second read" and J-08 "Market page moves over intact and history stays honest" remain failing, and no independent auditor ran — the spec asked for full depth and was demoted to lean for the fifth time this session, which is exactly why the evaluator escalated rather than continuing normally.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: J-11 "Incident-bounded clean regeneration of derived state" (iter-23)
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 1 critical (iter-23 owner-ruling breach — a routine regression re-test accidentally booted the protected canonical database; resolved in iter-24)
- Iters with no journey state change: 2 of last 3 (iter-22, iter-24)

**Latest evaluator reasoning:** "The one job the owner authorised was done, and it works. The engine can no longer quietly switch to a different database part-way through a run: it now decides once, at the start, which start-up command to use, and refuses any later start-up that does not match. I did not take this from anyone's write-up — I ran the new safety test myself (18 checks, all passed) and watched the refusal happen. I also proved the protected database was never opened: its three files have not changed at all since yesterday, while the throw-away copy was the one written to during this run."

## What was done

- No product change this iteration.
- Locked the backend/frontend launch command once per goal-mode run (`goal_iter_lock_backend_launch_context`) and added a fail-closed guard inside `ensure_services_running` that refuses to start a backend whose command drifts from what was locked — closing the exact gap that let iteration 23 silently boot the protected database.
- Added a new regression test (`test-backend-launch-context.sh`, 18 assertions) proving the guard fails against the old code and passes against the fixed code, and that the fix itself never touches the real canonical database.
- Confirmed the "two copies" of the launcher script (`goal-iter-lean.sh`, live and vendored) are actually one file via a tracked symlink, so the fix landed in the one place that matters.
- Re-ran the existing automation test suites; no new failures — 6 pre-existing, unrelated timing-flaky failures in `test-goal-parallel-bqa.sh` were independently confirmed to predate this fix.
- Review passed (PASS, 2 minor notes); the evaluator independently re-ran the new test and confirmed the canonical database was byte-unchanged before and after.
- Browser QA was skipped — 0 target journeys this iteration (harness-only fix, no journey-visible surface).
- The evaluator found, on its own, that this iteration's regression re-test of J-01/J-04/J-10 silently never ran, due to a separate plan-parsing bug — nothing broke, but the safety net was effectively missing this round.

## What's left

- Journey J-07 "The Today page answers the ten-second read" — failing, not touched this iteration.
- Journey J-08 "Market page moves over intact and history stays honest" — failing, not touched this iteration.
- Re-test J-01, J-04 and J-10 for real next round — their regression re-test silently didn't run this iteration.
- Fix the plan-reading bug itself (`scripts/automation/lib/replay-lane.sh:75-77` reads only the first matching line of "Required-still-passing," so an early cross-reference in the spec emptied the re-test list) and add reporting so a silently-empty re-test list is flagged instead of logged as "nothing to do."
- The same unguarded-launch-command pattern this fix closed still exists, latent and out of scope, in five sibling scripts (`browser-qa-phase.sh`, `qa-phase.sh`, `run-phase.sh`, `demo-phase.sh`, `run-benchmark.sh`).
- No independent auditor or QA lane ran this iteration — the spec asked for full depth and was silently demoted to lean, the fifth time this has happened this session.
- J-04's proof screenshot still needs re-capturing to include the candidate card — sixth iteration running with this gap.
- The 7.8 GB disposable practice-copy database at `runs/goal-market-compass-iter-23/verify-clone/` may now be deleted but hasn't been yet.
- Five older owner questions remain open and non-blocking: whether 3.44 GB is acceptable for J-09, J-06's wording, J-01's test-step wording, whether an empty "next-session focus" is acceptable, and whether MNST joins the recovery list.

## Next step

Resume normal product work with the deeper checks turned on. Build J-09 "The backend fits the host" first — the goal file's own next item, and the smallest one (a configuration value plus a measurement). In the same round, fix the plan-reading bug that silently emptied this iteration's regression re-test list, and add a check so an empty re-test result is reported rather than logged quietly. Re-test J-01, J-04 and J-10 for real, since they were skipped this round through no fault of their own. Ask the next iteration's plan to say "Depth enforcement: required" so the deeper review actually runs, since this iteration asked for full depth and was demoted anyway for the fifth time this session.

## Assumptions made

- iter-25 · goal-decomposer — Ambiguity: J-09's iter-4 measurement (3.44 GB, over target) already ran to completion and stopped for owner review; unclear whether that closes J-09's actionable work until the owner rules, or whether the now-stale pre-recovery measurement itself warrants a fresh re-measurement without waiting. We chose: treat this as fresh re-verification work — re-run the measurement steps against the current live database, no config edit, no new owner authorization needed — since the database materially changed since iter-4 and re-measuring is read-only. Reversible: yes.
- iter-24 · goal-evaluator — Ambiguity: J-11's goal text changed (spec hash drifted) while the standing rule says a drifted pass is void pending re-verification or drops to unknown — but the new text IS the owner's ruling declaring J-11 "PASSING — CLOSED" and forbidding re-verification. We chose: keep J-11 passing, record the new hash, and treat a documentary + state-integrity check (confirming the certified database bytes are unchanged) as satisfying the re-verification the current text admits of — not a fresh browser pass. Reversible: yes.
- iter-24 · goal-decomposer — Ambiguity: the usual targeting rules rank work by journey advancement, but this iteration's entire authorized scope is an owner-directed harness fix touching no journey acceptance criterion, so "Target journeys" has no natural non-empty value. We chose: leave Target journeys empty ("none — infrastructure fix"), treat the owner's ruling as superseding normal journey-based targeting for this one iteration, and substitute a Required-still-passing regression check plus the fix's own test as the pass bar. Reversible: yes.
- iter-24 · goal-decomposer — Ambiguity: the owner's ruling names the fix location only by its vendored-mirror path, not the live path the project actually executes, and doesn't say whether both copies need the patch. We chose: apply the identical patch to both, keeping them in the same lockstep the project already maintains (later confirmed to be a single file via a tracked symlink, so the point turned out moot). Reversible: yes.
- iter-23b · goal-evaluator — Ambiguity: one owner ruling item forbids the canonical database being mutated by verification, while another says J-11 may close once the disposable-copy verification passes with no further authorization required — this iteration satisfied the second on the practice copy AND breached the first on the real database via a separate regression re-test in the same window. We chose: close J-11 (passing) and halt the session on the breach, rather than withhold the journey status, since every J-11 artifact traced only to the guarded practice copy and the breach was recorded as an unresolved critical item for the owner to rule on explicitly. Reversible: yes.
- iter-23 · goal-evaluator — Ambiguity: an owner ruling requires establishing that the "Today / Market Compass serving path works," but the literal `/market` page doesn't exist yet and returns a not-found error — unclear whether "serving path" means that exact page or the Market Compass feature, which today lives on the home page. We chose: read it as the feature and treat the `/market`-page check as not applicable rather than failed, since the Compass content demonstrably renders on the home page and the alternative would block J-11's closure on an unrelated, already-deferred product gap. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-24.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-24-dev.md |
| Review | PASS | reports/reviews/goal-market-compass-iter-24-review.md |
| Browser QA | SKIPPED | reports/phase-goal-market-compass-iter-24-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-market-compass/iter-24/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
