# Iteration 54 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The four code repairs this round asked for were all made, and I checked each one in the source
myself. But no journey changed status. The two journeys that turn on "the app keeps answering
while a data job runs" still fail that step: the developer's own one-per-second test recorded 6
moments where the health check got **no answer at all** and 53 more that took over 2 seconds. And
I found something no report mentions — during the very job the checks used to mark three journeys
green, the heavy aggregate step **ran out of memory and stopped early** (one of the five time
horizons was never computed), yet the saved record still says that work finished and the job
reads "ok". This round was also run at the shallow setting even though its own plan says deep, so
neither the audit nor the quality stage ran.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range | passing | passing | reports/qa/goal-ops-hardening-iter-54-evidence/J-01-verify.png · sqlite `data_provider_runs` 348 (19 of 28) and 349 (0 of 2) |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-54-evidence/J-03-verify.png · sqlite run 350 (283 trading of 412 calendar days) |
| J-04 Non-blocking boot with visible status | passing | passing | reports/qa/goal-ops-hardening-iter-54-evidence/UT-J-04-result.png (replay FAIL overturned — J-04-verify.png shows "Initializing… history 89/89" at replay time) |
| J-05 Aggregates precomputed at ingest | partial | partial | reports/qa/goal-ops-hardening-iter-54-evidence/UT-J-05-result.png · tc4-drill-out/health-polls.csv (6 non-answers) · logs/backend.log:233042 |
| J-06 Pages load only what they need | partial | partial | reports/qa/goal-ops-hardening-iter-54-evidence/UT-J-06-result.png · reports/perf-budgets.md Addendum 18 (WARN, two endpoints over budget) |
| J-07 Heavy aggregates never take the service down | partial | partial | reports/qa/goal-ops-hardening-iter-54-evidence/UT-J-07-result.png · reports/perf-budgets.md Addendum 17 · tc4-drill-out/health-polls.csv |
| J-08 Backtest evidence serves from storage only | passing | passing | reports/qa/goal-ops-hardening-iter-54-evidence/J-08-verify.png |
| J-09 Backend discloses background compute | passing | passing | reports/qa/goal-ops-hardening-iter-54-evidence/J-09-verify.png ("background compute running (1)") |

Shape unchanged: **5 passing / 3 partial / 0 failing**. No journey newly passing, none newly
failing, none regressed. No `journeys-changed.md`, no `browser-infra.json`; all 8 `spec_hash`
values match `goal_gate hash-journeys`, run by me.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (nothing unproven shown as proven) | OK | Backend-only diff; no proven-language added. `J-08-verify.png` still shows the honest "No elapsed forward window for this date yet" state. |
| AG-2 (no signals / price targets / orders) | OK | Nothing added to any surface; `Frontend Present: no`, zero `apps/frontend/**` files in `iter-diff.md`. |
| AG-3 (displayed numbers correct) | **MINOR VIOLATION (new)** | Run 351 stores `status='ok'` and lists `forward_aggregates` as refreshed, but `logs/backend.log:233042` shows that warm aborted at horizon 20 and horizon 60 was never computed. I considered scoring this critical and chose minor: no market number is fabricated. |
| AG-4 (no overfit edges) | OK | No claim, referee, or ledger path touched. |
| AG-5 (determinism / no lookahead) | OK | B1 widens a trailing count window by one bar in the `≤ as-of` direction (`market_phase.py:230`, `:572`); the retrospective stays behind its existing fence. |
| AG-6 (referee gate) | OK | No evidence-derived claims this iteration. |
| AG-7 (no hard-coded credentials) | OK | `iter-54/scan-report.md` = **CLEAN**, no secret/dependency/license findings. |
| AG-8 (memory / data-scale resilience) | **MINOR (carried + new)** | B3 removed one unbounded full-history read (`market_phase.py:1197` now uses `close_on`). But real, unforced `MemoryError`s fired on the shipped tree (`logs/backend.log:233007`, `:233042`, `:233277`) — the process degraded honestly and never wedged, which is the good half; `factor_lab_all` silently dropped out of run 351's refreshed list, which is the bad half. |
| AG-9 (offline-deterministic ingest) | OK | Checked at row level by me: `select distinct provider from data_provider_runs where id>=346` returns exactly `[('seed',)]` (runs 346-351). |
| AG-10 (host resource ceiling) | OK | Checked at the source: `git status --porcelain` AND `git diff --stat` over all five frozen paths are BOTH empty; `config.yaml:1363-1364` still reads 8192 / 2. |
| Pipeline depth integrity | **MINOR VIOLATION (new)** | Spec says `Depth: full` / `Full trigger: 1`; `iter-54/depth-dispatched` reads `lean`. No audit handoff and no QA report exist for iter-54. |
| DoD TC-7 (J-05's golden must run) | **MINOR VIOLATION (new)** | `regression-replay-results.md` has 5 rows and no J-05 row — second round running. |
| DoD TC-6 (live fault-injection drill) | **MINOR VIOLATION (new)** | Honestly disclosed as not run in the dev handoff; the reviewer filed it as its single MINOR. |
| J-06 budget clause | **MINOR VIOLATION (new)** | Addendum 18 WARN: `/api/runs` 3.2-7.5s and `/api/data/availability` 15.1-21.2s against a ≤1.5s budget. |

Coherence: **COHERENCE-PASS** (zero blocking, 3 advisory notes) — no structural veto.
Ledger after this round: **115 total, 50 unresolved, 0 unresolved critical**; **5 closed**
(iter-53's `co`, `cr`, `cs`, `cu`, `cq`), 6 new opened.

## Next-Step Recommendation

Run the next round at **full depth** (this is now required, not a suggestion). Work in this order.

1. **Fix the heavy step that runs out of memory, and stop the record from claiming work it did
   not finish.** During a normal data job the app's heaviest calculation ran out of memory part
   way through and skipped the last of its five time settings — but the saved job record still
   says that work was done, and the job is marked "ok". First make the record honest (say
   "partial", and list only what really finished). Then apply to that step the same bounded,
   take-a-breath treatment that already worked twice on other steps.
2. **Close the last six moments where the app went silent.** All six fall inside that same heavy
   step, and none in the step this round fixed — so this is one job, not many.
3. **Find out why two screens' data calls now take 5 to 21 seconds.** The job-history list and the
   data-availability chart got very slow because the stored data has grown about fifteen times
   larger. Nothing about this round caused it, but it is what keeps J-06 "Pages load only what
   they need" from passing.
4. **Actually run the three saved check scripts that exist and were not run** — J-05's has now
   been skipped twice, and the two written this round (J-04, J-07) have never been replayed.
   Also make the J-04 script wait for the app to finish starting before it checks, so it stops
   failing for a reason that is really the app behaving correctly.
5. **Run the round at the depth its own plan asks for.** This round's plan said "deep" and the
   engine ran "shallow", so the audit stage never happened — and the audit is the stage that has
   caught the real story six rounds in a row. This round proves the point: nobody reported the
   memory failure above.
6. SMALL AND ALREADY WRITTEN DOWN: the ~20-minute limit on a job's finishing work is still missed
   (30 minutes measured); the health check still does real database work on every call; the live
   fault drill for the relocated test switch is still owed.
7. CARRIED, untouched: iter-29/b + the badge wording after a permanently failed warm-up (27th
   round unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u;
   iter-46/az; iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj. Deferred a TWENTIETH
   time: iter-33/g, the Regime Lab — whose data ran out of memory again this round
   (`logs/backend.log:233007`).
8. CAPTURE ONLY, never a round's goal: one screenshot came back completely blank
   (`J-05-job-running.png`, 2 KB of empty dark frame); no walkthrough recording was made at all
   this round because the shallow setting skips that stage; J-07's is 24 rounds unrecorded.
9. OWNER: two decisions, still unanswered since rounds 50 and 51 — (a) may a future round move the
   heavy calculation into a separate process? That is still the only way to guarantee the app
   never pauses. (b) Does the 20-minute limit on a job's finishing work apply while the app is
   also serving people, or only when it is idle? And three facts worth knowing: the market-phase
   window bug is fixed and now proven against the old slow version rather than against itself; the
   step this round targeted went from one silent moment to none; and the app survived running out
   of memory for real, mid-job, without needing a restart.

## Halt Justification (if halting)

Not halting. ESCALATE only forces the next round to run at full depth.
