# Iteration 38 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration did the hard measurement work it was asked to do, and it did it honestly. The memory
test finally ran with the shared data cache genuinely switched on (I found the proof lines in the live
backend log myself), and the heavy warm-up was finally triggered the way the journey text says it
should be — by a real data backfill, not by a page request. Seven of the eight journeys are passing.
But one of the four checks in J-07 "Heavy aggregates never take the service down" was never actually
run: the pressure test was re-tuned so that nothing ran out of memory, so the part that proves the app
survives running out of memory was not exercised. J-07 stays partly done for the fourth time in a row,
which is why the verdict is ESCALATE — that is the only verdict that forces the next run to use the
full pipeline, including the deep audit step. Two other things need saying plainly: the headline number
this iteration first published was backwards, and the audit found and fixed it; and the automatic
replay checks all ran while the backend was switched off, so they proved nothing this time.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing (re-verified live) | `reports/qa/goal-ops-hardening-iter-38-evidence/UT-J-01-result.png` (opened — immutable 2026-05-29 leaderboard, "Stored exactly as scanned"); merged results row UT-J-01 |
| J-03 No per-run range cap | passing | passing (re-verified live) | merged results row UT-J-03 (412-day request accepted, 283 dates over 5 chunks); `reports/qa/goal-ops-hardening-iter-38-evidence/UT-J-03-result.png` |
| J-04 Non-blocking boot with visible status | passing | passing — **NOT re-verified this iteration** (carried on evidence durability, methodology A.6) | merged row UT-J-04 = **SKIPPED**; replay FAIL is an artifact of a DOWN backend (`.../J-04-verify.png`, opened — "Backend unavailable" page); partial corroboration `.../UT-J-04-result.png` (opened — "Ready / provider: seed / seed 2026-07-22") |
| J-05 Aggregates are precomputed at ingest, never on the fly | passing | passing (steps 1, 2, 4 live; step 3 not executed) | merged results row UT-J-05 (new gap date 2005-04-12 backfilled; `/api/dashboard` 2.4 ms; 7 aggregates refreshed); `.../UT-J-05-result.png` |
| J-06 Pages load only what they need | passing | passing (deterministic replay PASS) | `reports/qa/goal-ops-hardening-iter-38-evidence/J-06-verify.png`; replay row UT-J-06 (the only replay row that passed) |
| J-07 Heavy aggregates never take the service down | partial | **partial (4th consecutive)** — steps 1 and 3 met; step 2 met over ~88% of the warm; **step 4 has no this-iteration evidence** | `runs/goal-ops-hardening-iter-38/mem-drill/two-arm-summary.json`; `.../j07-warm/health-latency.csv` (recomputed by me: 233/233 HTTP 200, VmPeak 58.6% of cap); `logs/backend.log:142444 / :143130 / :143652` (liveness lines, read live); **no J-07 row exists in the merged browser results** |
| J-08 Backtest evidence serves from storage only | passing | passing (re-verified live) | merged results row UT-J-08 (mid-warm 124 ms "refreshing" banner → post-warm 19 ms "ready"); `.../UT-J-08-result.png` |
| J-09 The backend discloses its own background-compute activity | passing | passing (re-verified live) | `reports/qa/goal-ops-hardening-iter-38-evidence/UT-J-09-result.png` (opened — "Ready" and "background compute running (1)" in the same frame); merged results row UT-J-09 |

Deferred (`DEFERRED-BUDGET`): none. `journeys-changed.md`: absent — all 8 `spec_hash` values match
`goal_gate hash-journeys docs/goal.md` exactly. `browser-infra.json`: absent.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (no unproven "proven" claims) | OK | No evidence-claim or proven-language change. Diff is 2 backend files (`git diff 8b1092fb --stat -- apps scripts project-extensions config.yaml`); no referee/ledger path touched. |
| AG-2 (decision-quality only) | OK | No return promise, price target, or order path anywhere in the diff. |
| AG-3 (displayed numbers correct) | OK for displayed values; **1 new finding on a recorded measurement** | No served value's shape or computation changed (coherence.md Data Contract table, all four rows OK). But the iteration's headline *measurement* was published backwards — recorded as **iter-38/r (minor, RESOLVED in-iteration)**; I reproduced both anchors from the raw CSVs myself. |
| AG-4 (no overfit edges) | OK | No referee/holdout/scoring code in the diff. |
| AG-5 (determinism, no lookahead) | OK | `compute_forward_aggregates` / `resolved_forward_aggregate_evidence` / `ensure_historical_forward_aggregates_dispatched` are byte-frozen — confirmed absent from the diff. |
| AG-6 (referee gate) | OK | No evidence-derived claims this iteration. |
| AG-7 (no hard-coded credentials) | OK | `scan-report.md` = CLEAN. The new `TRENDORA_FORCE_LEGACY_BAR_CACHE` is an env-var *read*, not a secret; no config/env file added. |
| AG-8 (resilience / no unbounded whole-table loads) | **Carried open + 1 new finding**; not critical | `data_manager.py:3098` → `prices.py:131-152` still streams the whole `daily_prices` table once per job (carried, iter-37). Newly measured: holding the shared cache across the tail raises tail-stage VmPeak +229.0 MB vs +0.0 MB fallback, but overall peak only +1.1% and 58.6% of cap on the live basis — contained. **New: iter-38/s (minor, open)** — step 4's isolation path was never exercised. |
| AG-9 (offline-deterministic ingest) | OK | Both drills ran against the committed seed / a throwaway copy of it (`seed_throwaway_db.py` → `load_seed`, 590 symbols / 3.29 M rows). No manifest change, no network provider added. |
| AG-10 (host resource ceiling) | OK | `git status --porcelain -- scripts/start-backend.sh scripts/dev.sh scripts/start-frontend.sh project-extensions/host-guard/` returns **0 lines** — launch scripts and host-guard byte-identical. All heavy compute launched via `scripts/start-backend.sh` per the dev handoff and the audit's live-log check. The 3072 MB drill hit its own `ulimit -v` in a throwaway process — the cap did its job. |

Ledger after this iteration: **32 total, 13 unresolved, 0 critical.** Three new: iter-38/r (resolved),
iter-38/s (open), iter-38/t (open).

Pipeline health: review PASS_WITH_NOTES · QA PASS · audit PASS_WITH_GAPS · coherence **COHERENCE-PASS**
(one non-blocking advisory about the test-only env toggle) · closure CLOSURE-PASS · ux-regression
SKIPPED (budget-shed, credited nothing) · demo NOT_YET with zero steps.

## Next-Step Recommendation

Run the next iteration at **full depth** and give it **one** target: finish J-07 "Heavy aggregates
never take the service down". Only one of its four checks is missing.

1. **First, and it is the whole job: actually run out of memory.** Start one throwaway backend with
   `scripts/start-backend.sh` at a memory cap tight enough that the *aggregate warm-up* runs out of
   memory — not the earlier data-loading step, which is where the 3072 MB attempt broke. While that is
   happening, keep asking the health endpoint once a second, and also re-read one page the app had
   already cached. The journey asks for exactly two things: the warm-up gives up honestly, and the same
   process keeps answering. Neither was sampled this time.
2. **Second, keep the health check running until the job is really finished.** This run stopped polling
   at 299 seconds of a 338-second job, leaving a 39-second blind spot. Remove the fixed time limit in
   the polling script.
3. **Third, repair the automatic replay checks.** They ran against a switched-off backend and reported
   6 failures out of 7 that were not real. Make the replay refuse to report a failure when the backend
   is not answering, and refresh the stale page selectors.
4. **Fourth, give J-04 "Non-blocking boot with visible status" a real live test.** It was not verified
   at all this time, because the tester was told not to restart services and J-04 needs a restart.
   Decide up front who is allowed to restart the backend, and schedule that test last so nothing else
   depends on it. This must be done before anyone declares the goal achieved.
5. **Also worth doing, small:** run J-05's cold-restart check (step 3), which was skipped for the same
   reason; and re-measure the `read_pool()` timing properly during a real backfill instead of
   estimating it (audit B3).
6. **Capture only, never a goal of its own:** the J-07 walkthrough recording is now missing for the
   eighth iteration in a row.
7. **Still waiting on the owner, and both should be settled before any "goal achieved" run:** (a) the
   health-check speed budget of 0.1 seconds, missed for the fifth time — 0 of 233 checks met it during
   this warm-up, so please either accept slower answers during background work, change the budget, or
   ask for the caching fix; (b) whether the frontend start script should also be covered by the host
   protection rules.

## Halt Justification (if halting)

Not halting. ESCALATE continues the loop but makes the next iteration's depth mandatory rather than
advisory — this session lost iteration 35 entirely when an advisory full-depth recommendation was
dispatched at a lighter depth against a spec that required code.

Rejected **REGRESSION** (tree C.1): no journey moved `passing` → `failing`. The six replay FAIL rows are
an environment artifact — I opened `J-01-verify.png` and `J-04-verify.png` and both show a "Backend
unavailable" page, so the replay ran while the backend was down; the authoritative merged file records
five overturns and one SKIPPED, no FAIL. No critical anti-goal is unresolved: `scan-report.md` is CLEAN,
no manifest was touched, the launch scripts and host-guard are byte-identical, and all 13 open ledger
findings are `minor`.

Rejected **STALLED** (tree C.2): the remaining blocker is not human-owned. The auditor states the exact
recipe for closing J-07 step 4, and it is ordinary agent work — one bounded throwaway drill via
`scripts/start-backend.sh`. The two genuine owner items (the 0.1 s health budget, the frontend launch
script) are real but neither is the only path to finishing J-07.

Rejected **GOAL_ACHIEVED** (tree C.3): J-07 is `partial`, and 13 ledger findings are unresolved.

Chose **ESCALATE** (tree C.4, first clause) under this session's recorded reading that "failed" means
"did not reach `passing`" — J-07 has now missed for four consecutive iterations. There is also an
independent, iteration-specific reason this time, and it is the stronger one: the review lane and the QA
lane BOTH passed an iteration whose single headline conclusion was backwards, and the QA report
additionally claimed "No regressions (J-01 … J-09) PASS" while citing unit tests, at a moment when the
replay lane was 1/7 and QA had no journey evidence at all. Only the audit lane caught either problem —
for the second iteration running. A lean iteration has no auditor, and the next iteration deliberately
pushes a live process out of memory.

I state the cost plainly: this is the fourth ESCALATE in a row, which reads harsher than this
iteration's work deserves. The work here was good and largely self-correcting — the drill's cache was
genuinely live for the first time, the warm was finally triggered through the path the journey names,
and the wrong number was found and fixed inside the same iteration with a re-runnable script. The
verdict is about what the next iteration needs, not about the quality of this one.
