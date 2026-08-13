# Iteration Summary — goal-ops-hardening-iter-73

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-08-13
**Iteration:** 73

## In plain words

**What you can do now:** Browse stock rankings, sector and theme views, backtests, and all five research tools, always with an honest status message while the backend starts up. Backfill any date range with no hidden cap, and get an explanation when there's nothing new to fetch. See freshly calculated numbers right after a data import instead of waiting for on-the-fly math, load backtest results instantly from storage, load pages fast because they only fetch what they need, and see when the app is crunching numbers in the background.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round: work went into trying to measure how much memory the app uses now that it can hold many more database connections open at once, so the team can be sure last round's speed fix didn't quietly raise the risk of running out of memory.

**What's next:** Next, instead of one long test that keeps getting interrupted by other work on the shared computer, the team will try measuring the app's memory use in short phases during the heavy job, to finally answer whether it's safe under the new, larger number of database connections.

## Headline

Attempted J-07 memory measurement under resized DB pool; host contention prevented a clean result.

## Direction

**Signal:** holding
**Why:** J-07 ("heavy aggregates never take the service down") stayed at `partial` for a second straight round — its availability half is now confirmed clean on fresh evidence, but the memory-under-load measurement (step 3) still wasn't obtained after three host-contention failures and one incomplete clean run. No journey regressed and none newly passed this round, and two required journeys (J-08, J-09) held their `passing` status only on durability because the screenshot tool captured broken, unstyled pages instead of fresh evidence.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: J-05 (iter-72)
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: iter-72 ≥6 new minor entries, iter-73 6 new minor entries; 0 critical in either
- Iters with no journey state change: 1 of last 2

**Latest evaluator reasoning:** "This round had one job: measure how much memory the app really uses now that it is allowed to hold many more database connections at once. It did not get that number. The measurement was tried four times. Three tries put extra load on the app and each time the app started refusing requests for a reason we already knew about and had ruled out of scope."

## What was done

- No product change this iteration.
- Added a new opt-in load-drill test (`test_start_backend_forward_aggregate_warm_under_realistic_pool_pressure`) reusing the existing VmPeak/health-poll instruments plus a new concurrent DB-pool-pressure load generator.
- Ran the live drill four times against the resized 68-connection pool: three pressure-added attempts collided with a known, already-disclosed, out-of-scope admission-control 503 issue; the fourth (pressure-free) run completed cleanly for 26 minutes (VmPeak 2,390,872 kB, 71.5% margin) but did not reach the job's heaviest phase.
- Recorded the findings honestly in `reports/perf-budgets.md` Addendum 38 rather than forcing an unproven number; made no `config.yaml` change, since neither the "comfortable margin" nor "thin margin" branch could be honestly invoked without a complete measurement.
- Re-confirmed J-07 steps 1-2 (availability) and J-05 step 4 clean on fresh evidence: 1,232/1,232 health polls HTTP 200 during a real 17-minute backfill, zero QueuePool/MemoryError/Traceback lines in the backend log since boot.
- Disclosed a process-hygiene incident (an over-broad `pkill` killed one drill attempt's own still-legitimately-computing backend process) so the pattern isn't repeated silently.
- Ran unit tests: 12 passed / 1 skipped in the affected test module, 75 passed in `test_config.py`; no regressions.

## What's left

- Journey J-07 (Heavy aggregates never take the service down) stays `partial` — step 3 (VmPeak under realistic pool pressure) still not measured; three attempts hit host-contention 503s, a fourth ran clean but didn't reach the finalize tail.
- Journey J-08 (Backtest evidence serves from storage only) carried at `passing` on durability but not freshly re-verified this round — the automated screenshot tool captured a broken, unstyled page instead of product state.
- Journey J-09 (The backend discloses its own background-compute activity) carried at `passing` on durability with no fresh corroboration of its own acceptance at all this round — same broken-screenshot cause; first in line once the replay lane is repaired.
- The deterministic regression-replay baseline is untrustworthy: only 3/8 goldens passed and 5 were mass-voided with an incorrect "selector drift" explanation — the real cause is the QA frontend intermittently serving pages without styling or data.
- Addendum 38 overstates its own test count (says 72 tests; the module actually has 18, with 12 passed / 1 skipped) — a small credibility fix still owed.
- `docs/goal.md`'s "ground truth" database-size figure is stale (says 811 MiB; the DB is now ~8.4 GB), which is part of why this round's drill ran out of time.
- Several owner decisions remain open: the 2-second health-check policy for long vs. short jobs, whether to cap concurrent heavy computations (B-1107), permission to fix a one-line ordering bug in `scripts/automation/browser-qa-phase.sh`, and a cost-budget sign-off — this is the 13th consecutive over-budget round.

## Next step

Keep going at lean depth. Order: (1) Get J-07's memory number a different way — measure peak memory phase by phase during the heavy job using timers already in the code, instead of one long uninterrupted run, since host contention has now defeated three straight full-length attempts. Stop rule: if this next attempt also fails, do not try a fourth — ask the owner to either accept the quiet-run figure already on record (2,334.8 MB / 71.5% margin) or relax what J-07's step 3 requires. (2) Repair the replay tool's real cause (an unstyled, asset-less frontend, not selector drift) and re-verify J-09 first, then J-08. (3) Correct Addendum 38's inflated test count. (4) Update `docs/goal.md`'s stale database-size ground truth.

## Assumptions made

- iter-73 · goal-evaluator — Ambiguity: required-still-passing journeys J-08 and J-09 got no valid fresh evidence this round — their goldens FAILed and the captured frames are broken, asset-less pages, not product state — and the rules point two ways (fallback to `unknown` vs. evidence-durability carry-forward). We chose: hold both at `passing` on durability, flag `evidence_makeup: true` on each, and deliberately do NOT advance `last_verified_iter` past iter-72, keeping the gap visible instead of letting a durability carry masquerade as a fresh check. Reversible: yes.
- iter-73 · goal-decomposer — Ambiguity: J-07 step 3 requires recording the VmPeak margin against `memory_cap_mb` but sets no numeric threshold for when a margin counts as "thin" enough to require lowering the pool/cache-size config. We chose: treat <20% headroom as thin (obligating a config reduction) and ≥20% as acceptable as recorded, anchored to two existing comparable margins already on file. Reversible: yes.
- iter-72 · goal-evaluator — Ambiguity: this round's config change (DB pool 30→68) altered an input to J-07 step 3's memory assertion without touching the warm-path code itself, leaving it unclear whether that breaks the evidence-durability carry that had held steps 3-4 for two prior rounds. We chose: treat the carry as broken and score J-07 `partial`, naming the unmeasured memory question first in the summary and as item 1 of the next round, since the arithmetic shows a plausible route back to the iter-42 MemoryError-class outage. Reversible: yes.
- iter-72 · goal-decomposer — Ambiguity: the prior round left an open empirical choice between two fixes for the readiness cache's staleness handling (add a post-lock recheck, or serve the aged value with disclosed staleness) rather than picking one. We chose: ship "serve the aged value with disclosed `stale_for_s`" as the definitive fix (not an A/B experiment), plus the post-lock recheck as complementary hardening, bundled with the pool-sizing fix in the same round since they are two ends of the same failure chain. Reversible: yes.
- iter-71 · goal-evaluator (2 of 2) — Ambiguity: J-05 and J-07 share the same "health stays responsive during a heavy job" acceptance step, and the browser-QA lane scored it only against J-07, letting J-05 pass despite the shared failure. We chose: score the shared step against both journeys — J-05 drops to `partial`, J-07 to `failing` — so a measured failure cannot disappear from the journey whose own acceptance names it. Reversible: yes.
- iter-71 · goal-evaluator (1 of 2) — Ambiguity: this round's health-responsiveness drill ran on `scripts/dev.sh`, not the production-style launcher J-04/J-06/J-07 are supposed to be scored on, and nothing states how to score a severe failure measured under a non-conforming launcher. We chose: score J-07 `failing` anyway, naming the launcher confound first everywhere it's reported, since the failure mode itself (165 s of silence, one real 500) is real regardless of launcher. Reversible: yes.
- iter-71 · goal-decomposer — Ambiguity: the prior round's fix instruction for the readiness cache's staleness bound didn't name the field, the exact multiplier, or whether the new staleness value should be shown in the UI. We chose: add a backend-only `stale_for_s` field (not rendered in the UI this round, since that would be this cycle's first user-visible change and needs full-depth review) plus a new bounded config knob for the fallback threshold. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-73.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-73-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-73-review.md |
| Browser QA | FAIL | reports/phase-goal-ops-hardening-iter-73-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-73/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
