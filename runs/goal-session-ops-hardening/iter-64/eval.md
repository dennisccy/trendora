# Iteration 64 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

This round fixed the test robot, not the app. The check script for J-05 "Aggregates are precomputed at
ingest" now picks its own fresh, unused day at run time, so it can no longer break itself; I proved this
by running the picker myself after the round finished — it returned a new day (2005-06-28) with 2,193
spare days left. The long-postponed memory-failure test finally ran and passed. The question the last
round left open is answered: the slow health checks are real and repeat, not a busy machine — 59 of 930
checks took longer than the owner's 2-second limit, and for the first time in this project one check got
no answer at all. Seven of eight journeys pass; J-07 "Heavy aggregates never take the service down" stays
partly done, as planned.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | reports/qa/goal-ops-hardening-iter-64-evidence/J-01-verify.png (replay PASS; live rows `data_provider_runs` id=422/423 checked against sqlite) |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-64-evidence/J-03-verify.png (replay PASS; 412-calendar-day span ran, id=424) |
| J-04 Non-blocking boot with visible status | passing | passing | reports/qa/goal-ops-hardening-iter-64-evidence/J-04-verify.png (replay PASS) |
| J-05 Aggregates are precomputed at ingest, never on the fly | passing | passing | reports/qa/goal-ops-hardening-iter-64-evidence/J-05-result.png ("Immutable snapshot — as of 2005-06-27", regime 58.71 = sqlite `scanner_runs` id=2962); replay steps 1-12 PASS, step 13 FAIL overturned — see Anti-goal check iter-64/a |
| J-06 Pages load only what they need | passing | passing | reports/qa/goal-ops-hardening-iter-64-evidence/J-06-verify.png (replay PASS) |
| J-07 Heavy aggregates never take the service down | partial | partial | reports/qa/goal-ops-hardening-iter-64-evidence/J-07-result.png + reports/perf-budgets.md Addendum 30 + runs/goal-ops-hardening-iter-64/evidence-drill/reconciliation.md (929/930 HTTP 200; 59 breaches of the ≤2.0 s ceiling; 1 unanswered poll) |
| J-08 Backtest evidence serves from storage only | passing | passing | reports/qa/goal-ops-hardening-iter-64-evidence/J-08-verify.png (spot-check: rendered 66.07 "Risk-on" = sqlite `scanner_runs` id=2870) |
| J-09 The backend discloses its own background-compute activity | passing | passing | reports/qa/goal-ops-hardening-iter-64-evidence/J-09-verify.png (spot-check: SNAPSHOT DATES 2961 matches the DB at capture time) |

No journey changed status. All 10 evidence frames are byte-distinct (md5 run by the evaluator). All eight
`spec_hash` values match `goal_gate.py hash-journeys` run this round; no `journeys-changed.md`, no
`browser-infra.json`, no `DEFERRED-BUDGET` row. `evidence_makeup` stays set on J-05 (no showcase lane ran
this round — `reports/demo/goal-ops-hardening-iter-64/` does not exist), cleared elsewhere.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven claims presented as proven | OK | No product code changed. `git diff 91daea98 --stat -- apps/` is one file: `apps/backend/tests/test_data_manager.py`, a docstring-only edit I read in full. No proven-language anywhere in the diff. |
| AG-2 return promises / orders | OK | Same one-file product diff; no such surface touched. |
| AG-3 displayed numbers correct | OK (with one minor open item) | Verified on three frames against sqlite: 58.71 "Narrow leadership" for 2005-06-27 = `scanner_runs` id=2962; 66.07 "Risk-on" for 2026-08-03 = id=2870; SNAPSHOT DATES 2961 matches the table at capture time. Minor: one job wrote two persisted run rows (iter-64/d). |
| AG-4 overfit edges | OK | No engine, referee, or ledger code in the diff. |
| AG-5 determinism / no-lookahead | OK | No scoring or forward-return code in the diff. |
| AG-6 evidence claims without referee | OK | This iteration makes no evidence-derived claim; the goal's Loop Mechanics exempt J-01…J-06. |
| AG-7 hard-coded credentials | OK | `iter-64/scan-report.md`: CLEAN — no secret, dependency, or license findings on added lines. |
| AG-8 resilience / honest degrade | MINOR — open (iter-64/a) | `/scanner-runs` rendered its contained error boundary during J-05's step 13 (`J-05-verify.png`). The boundary is what AG-8 prescribes (nav intact, honest wording, retry button), so this is not a critical breach — but the cause is unknown, and the two lane write-ups describe the frame wrongly. |
| AG-9 offline-deterministic ingest | OK | Every `data_provider_runs` row created this round (id=421 … 426) is `provider='seed'`; the only non-seed rows since 2026-08-01 remain id=297 and id=369, both pre-existing. |
| AG-10 host resource ceiling | OK | `git status --porcelain -- config.yaml project-extensions/` is EMPTY. `config.yaml:1363-1364` still reads `memory_cap_mb: 8192` / `malloc_arena_max: 2`; `host-guard.env` still reads `HOST_GUARD_MEMORY_HIGH="12G"` / `HOST_GUARD_BLAS_THREADS=8`. The spawned backend's own boot banner in `logs/backend.log` reads `memory_cap_mb=8192 malloc_arena_max=2` / `host-guard: cpu_list=0-15 blas_threads=8`. |

New minor entries this round: iter-64/a (unexplained `/scanner-runs` render error, mis-described by two
lanes), iter-64/b (health-latency breach reproduces; first unanswered poll), iter-64/c (the new note in
`J-05.json` documents the wrong date window), iter-64/d (one job, two persisted run rows), iter-64/e (the
review says "definition_of_done: complete" while TC-5/TC-9 had no lane and TC-2's replay failed),
iter-64/f (over budget again: 5,950 s against 3,600 s, first time at lean depth).
Closed this round: iter-63/c (self-consuming golden date — mechanism fixed and re-proven live by me),
iter-63/e (test docstring corrected), iter-63/g (named memory-failure test finally executed, 1 passed in
764 s). Ledger: **195 total, 100 unresolved, 0 unresolved critical.**
Coherence: **COHERENCE-PASS** (0 blocking, 2 advisory). Review: **PASS_WITH_NOTES**. Merged browser QA:
**PASS 8/8**. Raw replay: **FAIL 6/8**, both rows reconciled with a dated per-journey footer.

## Next-Step Recommendation

Run the next round at lean depth and give it this order.

1. **Make the slow step stop blocking the health check.** The measurement is now settled twice over: the
   waiting happens inside one job phase called `factor_lab_all_warm`, which ran for 568 seconds. Change
   that phase so it lets the health check answer, then re-run the same 1-per-second drill and publish the
   raw numbers. This is the only way to close J-07 "Heavy aggregates never take the service down" without
   the owner, and it must keep its results identical, proven by the equality test the journey already asks
   for.
2. **Find out why the Scanner Runs page failed to draw once.** A picture of it exists
   (`reports/qa/goal-ops-hardening-iter-64-evidence/J-05-verify.png`). It recovered by itself, so treat it
   as an investigation with a written answer, not a guess. If it happens again it stops being minor.
3. **Confirm the 90-second start-up wait actually took effect**, from the next round's own engine log —
   this round could only write the new value, not use it.
4. Small and written down: correct the wrong date window in the new note inside `J-05.json` (iter-64/c);
   check whether one job can stop writing two history rows (iter-64/d).
5. Riding along, never the round's own goal: record the J-05 walkthrough (unrecorded for six rounds).
6. Carried, untouched: iter-29/b and the badge wording after a permanently failed warm-up (37th round
   unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az;
   iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj; iter-57/f; iter-57/l; iter-59/g; iter-59/h;
   iter-59/k; iter-62/e; iter-62/f; iter-63/a; iter-63/b; iter-63/d; iter-63/f. Deferred a thirtieth time:
   iter-33/g, the Regime Lab.
7. **Owner — the same one sentence, asked a 16th time, but the facts behind it have changed.** The app
   must answer its health check within 2 seconds while a background job runs. That promise was written for
   a job of about 30 seconds; ours last 17 to 20 minutes. This round 929 of 930 checks were answered and
   the app served no errors, but 59 answers were slower than 2 seconds and one check got no answer at all
   within 5 seconds — the first time that has happened. Please say which you want: keep the 2-second
   promise for long jobs (J-07 stays open until the app is faster), or apply it to short jobs only (J-07's
   last gap closes). Also still waiting on you: permission to fix the ordering bug in
   `scripts/automation/browser-qa-phase.sh`, and a cost decision — the automatic check now runs a real
   17-minute data job every round, and that job is the main reason the round again ran past its time
   budget.

One sentence for you to act on: let the developers spend the next round making that one slow job phase
answer the health check on time, and tell us which version of the 2-second promise you want to keep.
