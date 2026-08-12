# Iteration 70 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

The fix worked. The app used to redo two slow checks every time something asked "are you healthy?".
Now it prepares those answers in the background and hands over a ready answer. During a real
17-minute data job, all 1,030 health checks were answered, none took longer than 2 seconds, and the
slowest was 1.23 seconds. Last round, 77 checks were too slow and 3 got no answer at all. I checked
these numbers myself from the raw files, not from any report.

But this round produced no picture evidence for any journey. The test backend shut itself down
between two test stages, so the browser check and the replay check never ran. Nothing failed —
they were never run. All eight journeys now wait for a re-check next round.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range | passing | partial (pending-infra) | not tested — `reports/phase-goal-ops-hardening-iter-70-regression-replay-results.md` row UT-J-01 = BLOCKED; `reports/qa/goal-ops-hardening-iter-70-evidence/INFRA-backend-down.png` |
| J-03 No per-run range cap | passing | partial (pending-infra) | not tested — same replay file, row UT-J-03 = BLOCKED |
| J-04 Non-blocking boot with visible status | passing | partial (pending-infra) | not tested — same replay file, row UT-J-04 = BLOCKED |
| J-05 Aggregates precomputed at ingest | passing | partial (pending-infra) | not tested — same replay file, row UT-J-05 = BLOCKED. Ingest path DID run for real: `runs/goal-ops-hardening-iter-70/evidence-drill/backend-log-phase-lines.txt` (job `22057414…`, 9 finalize phases, clean teardown) — code evidence, not a screenshot |
| J-06 Pages load only what they need | passing | partial (pending-infra) | not tested — same replay file, row UT-J-06 = BLOCKED |
| J-07 Heavy aggregates never take the service down | partial | partial (step 2 passed; browser half owed) | `runs/goal-ops-hardening-iter-70/evidence-drill/tc1-health-poll.csv` (1,030 polls, 0 over 2.0 s, 0 non-answers, max 1.226 s); `…/health-watchdog-slice.jsonl` (1,065 records, `readiness_s` p90 0.000003 s, `preflight_s` p90 0.000001 s); `reports/perf-budgets.md` Addendum 36 |
| J-08 Backtest evidence serves from storage only | passing | partial (pending-infra) | not tested — same replay file, row UT-J-08 = BLOCKED |
| J-09 Backend discloses background-compute activity | passing | partial (pending-infra) | not tested — same replay file, row UT-J-09 = BLOCKED |

Shape: **8 partial (0 failing, 0 regressed)**. No journey moved to `failing`. `BLOCKED` is not `FAIL` —
the replay file says so itself: "BLOCKED means they were never checked."

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language backing | OK | No evidence claim added; diff is 10 backend/config files, none touching the ledger or any proven badge (`git diff --numstat` vs `8567f700`, run by me) |
| AG-2 decision-quality only | OK | No price target, signal, or order path in the diff |
| AG-3 displayed numbers correct | OK, with a NEW named risk | Response shape byte-identical (`test_health.py:349-364`); I polled the live backend 3x: HTTP 200 in 6.5-6.7 ms, `readiness: "ready"`, preflight GO, all 13 fields present. NEW risk logged as iter-70/d: `readiness.py:567-575` returns the cache with no age check, so a dead tick thread would serve a frozen-but-plausible value forever |
| AG-4 no overfit edges | OK | No pattern surfaced; no referee-facing change |
| AG-5 determinism / no lookahead | OK | Cache wraps the same two producers; no scoring or forward-return code touched |
| AG-6 referee gate | OK | No evidence-derived claim this iteration |
| AG-7 no hard-coded credentials | OK | `iter-70/scan-report.md` = CLEAN; the only new identifier is one float config knob |
| AG-8 resilience / no unbounded loads | OK | No new query or whole-table read; the tick calls the same `compute_readiness`/`compute_preflight`. Round window (1,502 log lines) has zero 5xx / ERROR / Traceback / MemoryError / CRITICAL; whole-file totals unchanged (129 HTTP 500s, last at line 249,034, iteration 57). The one frame this round shows a contained, honest "Backend unavailable" degraded state — never a blank error page |
| AG-9 offline-deterministic ingest | OK | `data_provider_runs` id 452 (this round's drill) is `provider='seed'`, `status=ok`; the only non-seed rows since 2026-08-01 remain ids 297 and 369, both pre-existing (read from sqlite by me). `bars_fetched: 0` |
| AG-10 host resource ceiling | OK | `git status --porcelain -- config.yaml project-extensions/ scripts/` shows only `config.yaml`, and its whole diff is ONE added line (`refresh_interval_seconds: 0.5`). `memory_cap_mb: 8192`, `malloc_arena_max: 2`, host-guard ENABLED=1 / CPU 0-15 / BLAS 8 / 12G all intact; no launch script touched; the drill ran via `scripts/start-backend.sh` |

**Minor violations opened this round (all minor, no critical):** iter-70/a (the QA report claims a
replay that does not exist), iter-70/b (zero journey evidence this round), iter-70/c (32.1 s of the
job window never polled), iter-70/d (unbounded cache staleness), iter-70/e (walkthrough clause still
unmet), iter-70/f (tenth over-budget round).
**Closed this round:** iter-69/a, iter-69/b, iter-69/c, iter-69/d.
Ledger: **230 total, 115 unresolved, 0 unresolved critical.**
Coherence: **COHERENCE-PASS** (0 blocking, 2 advisory). Review: **PASS_WITH_NOTES**.
Audit: **PASS_WITH_GAPS**. Closure: **CLOSURE-PASS**.

## Next-Step Recommendation

Run a normal (lean) round with two jobs.

1. **Re-check all eight journeys with the backend actually running.** They were never tested this
   round. The engine will schedule this automatically because every journey is marked as owing
   browser evidence. Start the backend and confirm it answers before the checking stage begins.
2. **Stop the health answer from going stale silently.** The app now keeps a prepared health answer
   in memory. If the background job that refreshes it ever dies, the app will keep serving the old
   answer forever and no one would know. Add a "prepared at" time to the answer and recompute it on
   the spot if it is older than a few refresh cycles. This is small work and it protects the promise
   this whole project is built on: the app must tell the truth about its own state.
3. **Measure the whole job next time.** Start the health polling BEFORE the data job starts. This
   round the polling began 32 seconds late and missed four early stages, including
   `coverage_membership_timeline_refresh` — the stage that held the single slow answer in each of the
   two rounds before last. It is unmeasured, not proven clean.
4. Small and written down: fix the QA report habit of claiming a check that did not run (iter-70/a);
   make the fallback in `health.py` explicit instead of relying on an accidental error (reviewer
   MINOR, audit B5); add one test that proves a finished job's new state actually reaches the health
   answer within one refresh cycle (audit T1).
5. Rides along, never the goal: record the J-05 walkthrough (12 rounds unrecorded) and the J-07
   walkthrough steps that J-07's own acceptance text asks for.
6. Carried, untouched: iter-29/b and the badge wording after a permanently failed warm-up (43rd round
   unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az;
   iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj; iter-57/f; iter-57/l; iter-59/g;
   iter-59/h; iter-59/k; iter-62/e; iter-62/f; iter-63/a; iter-63/b; iter-63/d; iter-64/b; iter-64/e;
   iter-64/f; iter-65/b; iter-65/c; iter-65/d; iter-66/b; iter-66/e; iter-66/f; iter-66/g; iter-67/f;
   iter-67/g; iter-68/d; iter-68/e; iter-69/e. Deferred a thirty-sixth time: iter-33/g, the Regime Lab.

**Owner — good news for once, and one decision that may now be easy.** The app must answer its health
check within 2 seconds while a background job runs. Last round, 83 answers were too slow and 3 got no
answer at all. This round the app made the two slow checks ahead of time instead of on demand: all
1,030 checks were answered, none took longer than 2 seconds, and the slowest was 1.23 seconds — during
the same heavy stage that caused every problem before. Your long-standing question (keep the 2-second
promise for long jobs, or apply it only to short ones) may no longer cost you anything: the app now
meets it for long jobs. Please still say which you want, so the journey can be closed rather than left
open. Two things still wait on you: permission to fix the one-line ordering bug in
`scripts/automation/browser-qa-phase.sh`, and a cost decision — this round ran a real 17-minute data
job plus a 1-hour test run and took about 5 hours against a 1-hour budget. One thing needs no decision
from you: the test backend shut itself down mid-round, so nothing was checked in the browser this
round. The next round re-checks everything.

## Halt Justification (if halting)

Not halting.
