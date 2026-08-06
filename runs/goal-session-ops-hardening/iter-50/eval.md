# Iteration 50 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This round made the app use much less memory and did not fix the thing it was built to fix. The
heaviest research page now needs about 3.1 GB instead of 7.8 GB, and a 25-minute test run with a
data job and that page running together produced no memory failures at all. But during this round's
own testing the app stopped answering anything at all for 17 minutes and 30 seconds, and only a
restart brought it back. So J-07 "Heavy aggregates never take the service down" stays failing. Four
journeys still pass on fresh, real pictures. Three are still part-done. One was not checked at all
because the round ran out of time.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `reports/qa/goal-ops-hardening-iter-50-evidence/J-01-verify.png` + UT-J-01 PASS; `data_provider_runs` ids 313/314 created by the replay itself at 21:10:24/21:10:41Z with the asserted counts (19 of 19 dates; 0 of 0 on the weekend span), read in sqlite by me |
| J-03 No per-run range cap | passing | passing | `reports/qa/goal-ops-hardening-iter-50-evidence/J-03-verify.png` + UT-J-03 PASS; `data_provider_runs` id 315 (2025-06-01→2026-07-17, 283/283 dates, `ok`), created 21:10:46Z by the replay, read by me |
| J-04 Non-blocking boot with visible status | partial | partial (NOT tested — `DEFERRED-BUDGET`) | `ui-test-results.md` "Deferred (iteration budget)" row UT-J-04 + "Missing Required Journeys"; prior status and prior stamp (iter-49) carried per SPEED-15 |
| J-05 Aggregates are precomputed at ingest, never on the fly | partial | partial | UT-02 PASS-with-note; `reports/qa/goal-ops-hardening-iter-50-evidence/iter50-auditfix2-tc1-live-drill.json` (run 318 terminal `ok`, 7 aggregates refreshed); I read `data_provider_runs` 316/317/318 and `scanner_runs` 2908/2909/2910 with 275/291/263 stored `scanner_results` rows. No UT-J-05 row; no leaderboard screenshot; UT-09 SKIPPED |
| J-06 Pages load only what they need | partial | partial | UT-01 PASS + `reports/qa/goal-ops-hardening-iter-50-evidence/UT-01-result.png` (warm load, 11 real rows); UT-10 PASS-with-finding (warm 52 ms nav / 163 ms API in budget; cold misses 780.2 s and 874.7 s). No UT-J-06 row |
| J-07 Heavy aggregates never take the service down | failing | failing | UT-03 **FAIL** + `reports/qa/goal-ops-hardening-iter-50-evidence/UT-03-fail.png` (opened by me: badge stuck on "Checking backend…"); `logs/backend.log` silence 22:57:06Z→23:14:36Z; drill JSON `health.polls_over_2s = 96` of 1179, `latency_max_s = 10.0633`. No UT-J-07 row |
| J-08 Backtest evidence serves from storage only | passing | passing | `reports/qa/goal-ops-hardening-iter-50-evidence/J-08-verify.png` (opened by me: badge "Ready", provider seed, 591 symbols, regime 66.07, honest-NA scorecard) + UT-J-08 PASS. `evidence_makeup` cleared |
| J-09 The backend discloses its own background-compute activity | passing | passing | `reports/qa/goal-ops-hardening-iter-50-evidence/J-09-verify.png` (opened by me: badge "background compute running (1)", coverage panel populated, 2,907 snapshot dates) + UT-J-09 PASS. `evidence_makeup` cleared |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language without a certified claim | OK | none observed — backend-only 7-file diff adds no proven/confident wording; the new `status`/`factors_status` fields are degrade signals (`research.py:1324`, `:1339`, `:3910`) |
| AG-2 decision-quality only | OK | none observed — no new displayed value, no order/target surface; `apps/frontend/` untouched (0 hits in `git diff`) |
| AG-3 displayed numbers correct | OK | byte-identity for the columnar rewrite proven by data comparison against an independently written pre-columnar oracle (`tests/test_factor_lab_all.py:480` vs `_all_pools_reference_unchunked:391`), read by the auditor. Recorded caveat: the TC-3 oracle (`test_research_streaming.py:623`) calls the current builder, so it pins only the per-(factor,horizon) transient |
| AG-4 no overfit edges | OK (n/a) | none observed — no new claim or edge surfaced this iteration |
| AG-5 determinism / no lookahead | OK | none observed — the diff is data representation + concurrency control; no scoring or forward-return window touched |
| AG-6 referee gate on evidence claims | OK (n/a) | J-05/J-06/J-07 are ops journeys carrying no Evidence Claims (goal.md "Loop mechanics") |
| AG-7 no hard-coded credentials | OK | `iter-50/scan-report.md` CLEAN — no secret, dependency or license findings on added lines |
| AG-8 resilience / never exhaust a service's memory | **VIOLATED** | 17 m 30 s total service wedge requiring a restart; `logs/backend.log` last line 2026-08-05 23:57:06,885 local → restart banner 23:14:36Z, verified by me. Ledger `iter-50/bx`, severity `minor` in the machine field with grounds stated; the weight is carried on J-07 = failing |
| AG-9 offline-deterministic ingest | OK | every run created this iteration (313–318) is `provider='seed'` — I queried `data_provider_runs` myself; no network or paid provider introduced |
| AG-10 host resource ceiling | OK | `git diff` AND `git status` over `config.yaml`, `project-extensions/host-guard/host-guard.env`, `scripts/start-backend.sh`, `scripts/dev.sh`, `scripts/start-frontend.sh` are EMPTY (run by me); `config.yaml:1363-1364` still reads `memory_cap_mb: 8192` / `malloc_arena_max: 2`; every launch banner reads `memory_cap_mb=8192 malloc_arena_max=2`, `host-guard: cpu_list=0-15 blas_threads=8` |
| Secrets / paid SaaS / license (scan categories) | OK | `scan-report.md` CLEAN; the 7 changed files are all under `apps/backend/app/engine/` and `apps/backend/tests/` — no manifest, no config, no LICENSE touched |
| Coherence | COHERENCE-WARN | advisory only, does not veto. Two tidy-ups named: register `by_horizon[].status` / `factors_status` in the Data Contract, and correct the blueprint's own "no new field" claim |

## Next-Step Recommendation

Full depth (required, because the verdict is ESCALATE). Give the next round this order.

1. **Take the heavy research calculation off the request path.** This is the one change that matters.
   Opening the Factor Lab page still makes the app compute for 12 to 15 minutes the first time after
   any data job, and while it computes, the health check that tells the app "I am alive" answers
   slowly — 96 of 1,179 checks were slower than the 2-second promise, the worst at 10 seconds. Using
   less memory did not fix this and cannot: the page and the data job are fighting for the same
   processor. Either compute this page's numbers during the data job and store them, the way the goal
   already says everything heavy should work, or move the calculation off the thread that answers
   requests.
2. **Then run the eight journey checks last, and change no code afterwards.** This rule has now been
   broken five rounds in a row, and this time the code changed three separate times after the checks
   ran — including a full rewrite of the very code the checks were meant to prove. Three journeys had
   no check at all this round: "Aggregates are precomputed at ingest" (J-05), "Pages load only what
   they need" (J-06) and "Heavy aggregates never take the service down" (J-07). "Non-blocking boot
   with visible status" (J-04) was dropped for lack of time. The J-05 check now points at 2010-11-08,
   which I confirmed still has no stored snapshot.
3. **Rebuild the quality report from that run.** The current one says "pass" while the round's own
   browser check says "fail" and the machine record says the check never ran. It must be regenerated,
   never hand-edited. This is the second round running with this contradiction.
4. **Find out why the app went completely silent for 17 minutes.** It was not a crash — the process
   stayed alive and busy but answered nothing, and the data job had already finished successfully. The
   teardown step is now timed, so a repeat will say where it went. Do not claim this is fixed: it did
   not happen again in a 25-minute test, but that test never reached the same memory level either.
5. SMALL AND ALREADY WRITTEN DOWN: `research.py:1334` builds a set over the whole pool in one go and
   was the last thing logged before the silence; the waiting-caller hold can now last 43 minutes and
   has never been measured with more than one caller; the two other slow spots in the data job's
   clean-up tail.
6. CARRIED, untouched: iter-29/b and the badge wording after a permanently failed warm-up (23rd round
   unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az;
   iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj. Deferred a SIXTEENTH time: iter-33/g,
   the Regime Lab.
7. CAPTURE ONLY, never a round's goal: the walkthrough recorded zero steps for the third round
   running, and no picture was taken of the stored leaderboard for a freshly backfilled day.
8. OWNER: one thing needs your decision, and three facts belong in front of you. The decision: the
   spec asks for two things that cannot both be true — a deferred warm-up must "never silently drop
   the work", but it must also "defer" when the other one is running. Today both sides can step aside
   at once and the work is dropped for that data version. Please say which one wins. The facts: the
   heaviest page now uses about 3.1 GB instead of 7.8 GB, well inside your 8 GB ceiling; adding one
   old day of history finished successfully three times out of three, in 11, 18 and 24 minutes; and
   the app nevertheless went completely silent for 17 and a half minutes during this round's own
   testing and needed a restart.

## Halt Justification (if halting)

Not halting. ESCALATE continues the loop at full depth.
