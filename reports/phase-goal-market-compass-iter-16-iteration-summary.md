# Iteration Summary — goal-market-compass-iter-16
**Verdict:** STALLED
**Iteration type:** goal-full
**Date:** 2026-08-25
**Iteration:** 16

## In plain words

**What you can do now:** See each stock's real, filled-in sector label; see why each next-session candidate was picked and why others weren't; browse the two trading days that were lost in the August data incident — now restored, and as of this round, with their trading-volume numbers corrected too — in the price history.

**What changed this time:** Behind the scenes, one stock's (AVB) recorded trading-volume numbers for two days in August were corrected — they had been reading about 2.8 times too high. The team also built a new safety check into the app's start-up code meant to stop it from quietly overwriting repair-in-progress data, though that check is not yet switched on for the real data.

**What's next:** Next, the owner needs to approve turning on the new safety check for the real database, and then decide whether to go ahead and rebuild the 11 days of history still missing from the August incident.

## Headline

AVB volume corrected; Stage D reads READY for first time, but pre-boot guard is inert on live DB — stays unauthorized

## Direction

**Signal:** stalling
**Why:** J-11's Stage D readiness gate returned `READY: YES` for the first time this session after the owner-authorized AVB volume correction (`j11_avb_correction.py`) landed and was independently re-verified byte-for-byte against the live 8.4GB database. But the new pre-boot guard (`j11_preboot_guard.py`, wired into `warmup.py`) is proven only on disposable fixtures and stays inert against the live database, so maintenance isolation remains active and no application/browser lane can resume. J-07 and J-08 stay failing, unchanged for the third STALLED iteration running, holding direction at stalling rather than improving.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: none
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 2 new — 1 critical (iter-14, AG-17/C5, resolved same iteration) + 1 minor (iter-16, AG-8, unresolved)
- Iters with no journey state change: 3 of last 3

**Latest evaluator reasoning:** But the most important thing this iteration produced is not the YES. It is a hole in the safety catch, and I confirmed it myself. The safety catch is built correctly and sits in the right place, but it is switched off against the real database: the list of days it is supposed to protect was never written there, and the catch lets everything through when that list is empty. So if anyone starts the app today, it would still write a new day's results onto 12 August — the exact accident the owner's rule was written to prevent.

## What was done

- Product changes: apps/backend/app/engine/j11_avb_correction.py, apps/backend/app/engine/j11_preboot_guard.py, apps/backend/app/engine/j11_stage_d.py, apps/backend/app/engine/warmup.py, apps/backend/app/models.py, apps/backend/scripts/run_j11_avb_correction.py, apps/backend/scripts/run_j11_iter16_stage_d_readiness.py
- Derived and applied the one owner-authorized AVB `daily_prices.volume` correction (2026-08-11: 1,549,436 → 554,757; 2026-08-12: 10,350,885 → 3,706,010), independently proven isolated via three byte-identical hashes and an exact predicted `ohlcv_sum` delta.
- Established the corrected state as J-11's new certified raw-input baseline — only the `daily_prices_fingerprint` field superseded; the preflight gate now genuinely fails against the old baseline and passes against the new one.
- Built and proved, on disposable fixtures only, a fail-closed pre-boot guard meant to stop the app writing derived data onto a quarantined incident date during startup.
- Re-ran Stage D readiness against the corrected baseline: `J-11 STAGE D READY: YES` for the first time this session, `J-11 STAGE D AUTHORIZED: NO` unconditionally — no Stage D work performed or planned.
- Added 101 new tests (209 total across 12 J-11-scoped test files); zero regressions.
- Browser QA lane was contractually SKIPPED under maintenance isolation — 0 journeys re-verified via browser this iteration.

## What's left

- Journey J-07 ("The Today page answers the ten-second read") still failing.
- Journey J-08 ("Market page moves over intact and history stays honest") still failing.
- The new pre-boot safety guard is proven only on disposable test data — it is not yet registered against the real database, so starting the app today would still silently write derived data onto the quarantined 12 August incident date.
- Stage D itself (rebuilding the 11 missing days of derived history) has not started; even with the readiness check now reading YES, it needs a separate, explicit owner instruction.
- The recorded AVB classification is AVB-B, but the honest label on a scale-consistent comparison is AVB-A — this doesn't change the YES answer, but the record should be corrected before being relied on further.
- One unresolved minor anti-goal item: an unbounded database read on the shared app start-up path (AG-8) — low risk today, one-line fix pending.
- Five older owner questions remain open and non-blocking (J-09's memory footprint, J-06's wording, J-01's test-step wording, whether an empty "next-session focus" is acceptable, and whether MNST joins the recovery list).

## Next step

One safety job, then one decision, per the evaluator's recommendation: first, register the eleven quarantined incident dates in the live database so the new pre-boot guard actually switches on — until then, starting the app would still write bad data onto 12 August. Then the owner picks one of: (a) instruct the engine to run Stage D and rebuild the eleven days; (b) order a small non-destructive tidy-up first (re-run readiness with the volume figure supplied so the honest AVB-A label replaces AVB-B, fix the one-line unbounded table read in `j11_preboot_guard.py`, add a test for the live-shaped "table empty, latest day is a damaged day" case); or (c) change the plan in `docs/goal.md`. Whichever is chosen, Stage D itself still needs a separate, fresh owner instruction — this iteration ends `J-11 STAGE D AUTHORIZED: NO`.

## Assumptions made

- iter-16 · goal-evaluator — Ambiguity: this is the fourth consecutive STALLED, and the first where the readiness gate answered YES; real non-owner-owned tractable work exists (re-run readiness with `volume_override`, bound the AG-8 select, add a missing guard test), which reads like CONTINUE. We chose: STALLED under C.2 (every unblock path for the current blocker is owner-owned) — the owner's own ruling ends this step even on YES ("STOP for owner review"), and arming the pre-boot guard needs a live write outside this iteration's authorization. Reversible: yes.
- iter-16 · goal-evaluator — Ambiguity: AG-8 forbids "unbounded whole-table ORM loads," and the new guard's boot-path query is literally that, but AG-8's stated subject is resilience to data-scale change, and the control table it reads never widens with the data basis. We chose: record it as severity minor, unresolved, with the "letter-but-not-subject" reasoning stated openly rather than silently excusing it. Reversible: yes.
- iter-16 · goal-evaluator — Ambiguity: the owner's ruling says the pre-boot guard must be "proven on disposable test state" before isolation lifts, but doesn't say whether meeting that literal clause alone is enough while the guard is still inert against the real database. We chose: treat the clause as necessary but not sufficient — maintenance isolation stays ACTIVE, since reading it as sufficient would let a guard that protects nothing in production unlock booting the live backend. Reversible: yes.
- iter-16 · goal-decomposer — Ambiguity: the owner ruling didn't specify which fields of the Stage D certified baseline should be superseded by the AVB correction — the whole artifact, or only the touched field. We chose: supersede only `daily_prices_fingerprint`; every other composed field keeps sourcing unchanged from the original iteration-13 artifacts. Reversible: yes.
- iter-16 · goal-decomposer — Ambiguity: the ruling required the guard's "cleared" state to be "state-driven, not hardcoded" without specifying how clearance is determined; a simpler design could infer it from whether scan results already exist per date. We chose: require an explicit, persisted boundary marker rather than inferring clearance from partial per-date progress, so a failed, partially-completed future rebuild attempt still reads as blocked. Reversible: yes.
- iter-16 · goal-decomposer — Ambiguity: the owner authorized a bounded AVB volume correction but didn't prescribe the exact formula; two evidence-grounded formulas were numerically identical today but conceptually different in provenance. We chose: derive the corrected volume from the independently-sourced provider figure (not Trendora's own currently-wrong stored value) divided by the bridge factor, reusing the already-proven diagnostic transform. Reversible: yes.
- iter-15 · goal-evaluator — Ambiguity: the tractable non-owner work this iteration included a safety item (a pre-boot guard against an irreversible unauthorized write, armed and reachable by an ordinary act) — a stronger pull toward CONTINUE than prior iterations faced. We chose: STALLED, but promoted the guard to the first item of the recommendation, ahead of the AVB decision — every route through the current blocker is still owner-owned, and a stopped engine is strictly safer here. Reversible: yes.
- iter-15 · goal-evaluator — Ambiguity: J-10 is recorded `passing` and explicitly closed by the owner, but this iteration's authorized fetch proved, for the first time by measurement, that J-10's own AVB output was defective (dollar volume 2.793x too high on its two recovered dates). We chose: keep J-10 `passing`, do not re-stamp it, and record the full measurement as a prominent caveat instead of reopening it. Reversible: yes.
- iter-15 · goal-decomposer — Ambiguity: whether re-deriving the engine identity again this iteration, for readiness-reporting purposes, would violate the binding "do not redo" protection on iteration 14's frozen Stage D attempt-identity artifact. We chose: re-deriving is not a violation, since the protected item is Stage D's own freeze-for-execution act, not the general capability of computing the identity read-only. Reversible: yes.
- iter-15 · goal-decomposer — Ambiguity: the coordinator's goal asked for "whatever bridge-adjusted comparison tests whether price and volume rebasing compensate" without stating the exact formula, and no precedent existed in the codebase for what "compensating" means numerically. We chose: model it as a reverse-split-like rebase where the expected inverse volume ratio is `1/bridge_factor`, reusing the same relative-tolerance idiom the existing calibration-window check already uses. Reversible: yes.
- iter-14 · goal-evaluator — Ambiguity: iteration 13 returned STALLED partly reserving an owner inspection point that the owner had since answered, and real non-owner-owned tractable work existed (closing a classifier gap, adding a producer, porting tests), which reads like CONTINUE. We chose: STALLED again, with the honesty fix offered as an explicit option rather than hidden — that work cannot change the answer, and every path that actually clears the gate is owner-owned. Reversible: yes.

## Quick verify

From `reports/phase-goal-market-compass-iter-16-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser (do not add any `?asof=` to the URL)
2. Look at the top market-state band's regime score and the phase tile's severity value
3. Read the plain-English summary card, then click `"Show cited facts"`
4. Read the "What changed" card's header
5. Click into one card under "Next-session focus"

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-market-compass-iter-16.md |
| Dev handoff | — | docs/handoffs/goal-market-compass-iter-16-dev.md |
| Review | PASS | reports/reviews/goal-market-compass-iter-16-review.md |
| Browser QA | SKIPPED | reports/phase-goal-market-compass-iter-16-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-market-compass-iter-16-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-market-compass-iter-16-user-visible-changes.md |
| What to click | — | reports/phase-goal-market-compass-iter-16-what-to-click.md |
| UI surface map | — | reports/phase-goal-market-compass-iter-16-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-market-compass-iter-16-ui-test-plan.md |
| QA | PASS | reports/qa/goal-market-compass-iter-16-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-market-compass-iter-16-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-market-compass-iter-16-closure-verdict.md |
| Goal evaluation | STALLED | runs/goal-session-market-compass/iter-16/eval.md |
| Journey history | — | runs/goal-session-market-compass/state/journey-history.json |
