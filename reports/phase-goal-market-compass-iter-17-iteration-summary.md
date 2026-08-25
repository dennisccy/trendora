# Iteration Summary — goal-market-compass-iter-17

**Verdict:** STALLED
**Iteration type:** goal-full
**Date:** 2026-08-25
**Iteration:** 17

## In plain words

**What you can do now:** See each stock's sector label filled in honestly, with no guessing. See why each candidate for the next trading session was picked, and why others were passed over. Look up the two trading days recovered from August's data problem — including their now-corrected trading-volume numbers — in a stock's price history.

**What changed this time:** Behind the scenes, the safety check that is supposed to stop the app from writing new results on top of the 11 still-broken trading days was rewritten to be safer, and a way to switch that check on or off was built. Nobody has switched it on for the real app yet, so starting the real app today would still quietly write bad results onto one of those broken days (12 August). Nothing changed that a user can see.

**What's next:** Next, the owner needs to decide whether to switch that safety check on for the real app or start rebuilding the 11 broken trading days first — and until that decision is made, nobody should start the app.

## Headline

Boot-guard code shipped & tested; still unarmed live — booting today would still write to a damaged day

## Direction

**Signal:** stalling
**Why:** J-11 (the incident-bounded clean-regeneration repair) advanced within `partial` — the AG-8 bounded-query fix, new arm/disarm CLI entrypoints, and 39 new/extended tests all landed and were independently re-verified by review, QA and the evaluator, closing iteration 16's one open anti-goal entry. But no journey's status actually changed, J-07 and J-08 remain `failing`, and this is the fifth straight `STALLED` verdict (iters 13-17): the live pre-boot guard still cannot be armed on the production database because arming needs a table the owner has explicitly forbidden creating, so the exact boot-path exposure the guard exists to close is still fully open.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: none
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 1 (minor — AG-8, opened iter-16, closed iter-17)
- Iters with no journey state change: 3 of last 3

**Latest evaluator reasoning:** The team built exactly what the owner allowed and stopped exactly where the owner said to stop. The safety catch that is meant to stop the app from writing to the eleven damaged days is now well built, properly bounded, and covered by 39 passing tests, which I ran myself. Nothing was written to the real database — I checked the file myself and it has the same timestamp, the same size and an empty write log as before. But the catch is still switched off on the real database, and switching it on needs a table that does not exist there.

## What was done

- Product changes: apps/backend/app/engine/j11_preboot_guard.py, apps/backend/tests/test_j11_preboot_guard.py, apps/backend/tests/test_j11_preboot_guard_cli_scripts.py, apps/backend/scripts/run_j11_maintenance_boundary_arm.py, apps/backend/scripts/run_j11_maintenance_boundary_disarm.py, apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py, apps/backend/scripts/run_j11_iter17_stage_d_readiness.py
- Bounded the previously-unbounded `MaintenanceBoundary` boot-path query (AG-8 fix): filtered to `active IS NOT FALSE` (keeps NULL rows), column-projected, capped at `LIMIT 101` with a fail-closed overflow branch — closes iteration 16's minor AG-8 ledger entry.
- Added committed, production-capable arm and disarm CLI entrypoints for the J-11 maintenance-boundary lifecycle — proven only against disposable fixture databases, never invoked against the live one.
- Extended the guard's test suite 19→26 tests and added a new 13-test CLI-script suite (39/39 passing) — independently re-run by the reviewer, QA and the evaluator, not just taken from the dev handoff.
- Ran a strictly read-only live-database check (TC-11) confirming the exposure is unchanged: the safety table still doesn't exist and the guard still returns "not blocked" for 12 August.
- Proved zero live writes via byte-identical database file fingerprints (mtime/size/write-log size) at true start and true end of the iteration (TC-12).
- Re-derived the AVB readiness classification with the correct volume basis, replacing last iteration's understated `AVB-B` label with the honest `AVB-A` (the readiness answer itself, `YES`, is unchanged; iteration 16's own evidence files were left byte-unedited).
- Independent audit and evaluator re-derivation confirm the delivered code is correct, but surfaced two evidence-quality problems: QA's "11 incident dates confirmed" table actually lists 9 dates that are not incident dates (7 with no data at all), and the new AVB ratio (TC-13) is an algebraic identity of last iteration's own correction formula, not new independent evidence — though the `AVB-A` label itself holds up under attack.

## What's left

- Journey J-07 "The Today page answers the ten-second read" — still `failing`.
- Journey J-08 "Market page moves over intact and history stays honest" — still `failing`.
- **The live safety catch is not armed and the maintenance boundary is not active on the production database.** Starting Trendora today would both create the table the owner explicitly forbade creating and permanently write a new day's scan results onto 12 August, a quarantined incident date — this is an open hazard, not a completed check, and nobody should start the app until the owner decides how to close it.
- J-11's Stage D (rebuilding the 11 damaged trading days) and every later stage remain not started and not authorized — needs a fresh, explicit owner decision.
- The two new evidence-generating scripts have zero test coverage, including their own destination-folder refusal checks — one could overwrite three of last iteration's saved evidence files if the folder name is mistyped.
- Evidence-record cleanup owed: correct the wording that calls the AVB comparison "genuinely independent" (it isn't — the price term cancels algebraically), correct QA's incident-date list, and stop proving "other journeys' code is untouched" with a check that is blind to newly-added, not-yet-committed files.
- This iteration's five new code files and its whole evidence folder are still not committed to git — needs confirming.
- Five older owner questions remain open and non-blocking (the J-09 memory-size figure, J-06's wording, J-01's test-step rewording, an empty "next-session focus" panel, and whether MNST joins the recovery list), plus two standing framework defects (a forbidden-test-lane defect and a duplicate-journey-heading defect) that must be fixed before any goal-achieved certification.

## Next step

One safety decision is needed from the owner, and nobody should start the Trendora app until it is made: starting it today would both create the forbidden `maintenance_boundaries` table and permanently write a new day's results onto 12 August, one of the eleven still-damaged days. Pick one: (a) allow that one small, empty table to be created, after which the already-built, already-tested arming tool switches the safety catch on; (b) order the rebuild of the eleven damaged days (a separate, fresh written instruction is still required for this), after which the start-up path becomes safe on its own; or (c) change the plan in `docs/goal.md`. This iteration's green `STAGE D READY: YES` reading is a measurement of readiness, not an authorization — `J-11 STAGE D AUTHORIZED` stays `NO` regardless of which option is chosen, and four small non-blocking jobs (evidence-script test coverage, wording corrections, and confirming this iteration's new files reach git) ride along whenever the next iteration runs.

## Assumptions made

- iter-17 · goal-evaluator — Ambiguity: this is the fifth consecutive STALLED verdict (iters 13-17) and carries the strongest pull yet toward CONTINUE — the safety exposure is live right now, fires from an ordinary act with no decision needed, and iteration 15 faced the same shape and resolved it by building something (the guard). We chose: STALLED again, but only after directly checking whether any non-owner engineering could close the hole — it cannot: failing closed on a missing table has zero effect (the app creates the table before the guard ever runs), and failing closed on an empty table would block every normal start-up forever, an owner-level design decision. Reversible: yes.
- iter-17 · goal-evaluator — Ambiguity: how to score reports in which every individual claim is true and the four owner-facing status lines are exactly right, but the developer/reviewer/QA writeups never state what the green live-database check result means for the live system. We chose: score it as understated, not dishonest — no anti-goal ledger entry, no verdict penalty — while making the live exposure the headline of the evaluation everywhere it appears, ahead of the delivered work. Reversible: yes.
- iter-17 · goal-decomposer — Ambiguity: the owner's ruling scoped this iteration strictly to the maintenance-boundary guard/lifecycle work and said nothing about iteration 16's flagged AVB label-correction rider. We chose: fold the read-only volume-corrected re-run in anyway, since it writes nothing, cannot change the readiness answer, and leaving the known-understated `AVB-B` label uncorrected for another iteration would compound the exact honesty risk the goal file's honesty posture exists to prevent. Reversible: yes.
- iter-16 · goal-evaluator — Ambiguity: real, tractable non-owner work existed this iteration (re-running readiness with the volume figure, bounding the AG-8 query, adding a missing test), which reads like grounds to CONTINUE, and this was already the fourth consecutive STALLED verdict. We chose: STALLED again — every route past the switched-off safety catch is owner-owned, and none of the tractable items could change the readiness answer — naming the tractable work as explicit riders rather than hiding it. Reversible: yes.
- iter-16 · goal-evaluator — Ambiguity: an unbounded whole-table query sat on the shared boot path, literally matching the anti-goal's banned pattern, but that anti-goal's stated subject is resilience to data-scale growth and the table in question is a one-row control table read once per boot that never widens with the data basis. We chose: record it as a minor, unresolved anti-goal entry with the "letter-but-not-subject" reasoning stated openly, rather than silently waving it through. Reversible: yes.
- iter-16 · goal-evaluator — Ambiguity: the owner's ruling said maintenance isolation lifts once the pre-boot guard is "proven on disposable test state," without saying whether passing fixture tests alone is enough, or whether the guard must also actually function against the live database. We chose: treat the clause as necessary but not sufficient — isolation stays active — because reading it as sufficient would let a guard that is inert in production unlock booting the live backend and immediately cause the exact write the rule exists to prevent. Reversible: yes.
- iter-16 · goal-decomposer — Ambiguity: after the AVB volume correction, whether the whole certified J-11 baseline artifact needed a fresh rebuild, or only the one field the correction actually touches. We chose: supersede only the `daily_prices_fingerprint` field, keeping every other field sourced from the original iteration-13 capture, since the correction touches only `daily_prices` and nothing else changed. Reversible: yes.
- iter-16 · goal-decomposer — Ambiguity: the owner required the pre-boot guard's "cleared" state to be state-driven but did not specify how "cleared" is determined; a simpler design could infer it from whether a scan already exists for a given date. We chose: require an explicit, persisted boundary marker instead of inference, because inferring clearance from partial per-date progress would silently violate the goal file's existing rule that a partially-completed regeneration attempt must not count as accepted progress. Reversible: yes.
- iter-16 · goal-decomposer — Ambiguity: two numerically-identical formulas were available for the AVB volume correction — one grounded in Trendora's own (currently wrong) stored value, one grounded in the independently-sourced provider figure. We chose: ground the formula in the independently-sourced provider figure, reusing an already-tested transform, to keep the correction's provenance honest even though both paths produce the same number today. Reversible: yes.
- iter-15 · goal-evaluator — Ambiguity: an auditor finding about a guard against an irreversible unauthorized write — one that could fire from an ordinary act with no decision required — pulled harder toward CONTINUE with a safety target than iterations 13 or 14 had faced. We chose: STALLED, but promoted the guard to the first item of the recommendation, ahead of the AVB decision, because every route past the then-current blocker was still owner-owned and halting is asymmetrically safer (a stopped engine starts no backend). Reversible: yes.

## Quick verify

From `reports/phase-goal-market-compass-iter-17-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser (do not add any `?asof=` to the URL)
2. Click into one card under "Next-session focus"
3. Navigate to `http://localhost:3255/stocks` and select the Sector filter's `"Unassigned"` option
4. Clear the filter, search for symbol `AVB`, and open its stock detail page
5. Navigate to `http://localhost:3255/data` and look at the manifest count

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-17.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-17-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-market-compass-iter-17-review.md |
| Browser QA | SKIPPED | reports/phase-goal-market-compass-iter-17-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-17-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-17-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-17-what-to-click.md |
| UI surface map | — | reports/phase-goal-market-compass-iter-17-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-market-compass-iter-17-ui-test-plan.md |
| QA | PASS | reports/qa/goal-market-compass-iter-17-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-17-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-market-compass-iter-17-closure-verdict.md |
| Goal evaluation | STALLED | runs/goal-session-market-compass/iter-17/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
