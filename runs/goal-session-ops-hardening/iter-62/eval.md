# Iteration 62 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This round fixed two small things and both fixes are real: the health check now reports the true
latest scan date (I read `2026-08-03` out of the database myself, and that is exactly what the app
serves), and the Data Manager page no longer wipes good numbers off the screen when one background
refresh fails. Seven of eight journeys pass; J-07 "Heavy aggregates never take the service down"
stays part-done for the 13th round, waiting on one owner sentence. The round also did something no
round has done before: the automatic replay checked J-05 and J-07 as well, and J-05's check ran a
real 15-minute data job that created a genuinely new day of data — I confirmed the new row in the
database. But the checking machinery also tripped over itself: it started one minute after the app
was restarted and reported two false failures, and J-05's own check script has now used up the
spare date it needs, so it will fail next round unless someone changes the date first.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `reports/phase-goal-ops-hardening-iter-62-ui-test-results.md` UT-J-01 PASS; `reports/qa/goal-ops-hardening-iter-62-evidence/UT-J-01-result.png` (frame does not show the claim — corroborated by me from sqlite: `data_provider_runs` id=413 19/19 dates, id=414 0/0) |
| J-03 No per-run range cap | passing | passing | UT-J-03 replay PASS; `reports/qa/goal-ops-hardening-iter-62-evidence/J-03-verify.png`; `data_provider_runs` id=411 (283 dates over a 412-day span, 13:25:18→13:47:04Z) |
| J-04 Non-blocking boot with visible status | passing | passing | UT-J-04 PASS; `reports/qa/goal-ops-hardening-iter-62-evidence/UT-J-04-result.png` (Ready badge, "GO — today's board is current", 2958/2438 = database) |
| J-05 Aggregates are precomputed at ingest, never on the fly | passing | passing | UT-J-05 replay PASS; `reports/qa/goal-ops-hardening-iter-62-evidence/J-05-verify.png`; live job `data_provider_runs` id=412 (2010-11-17, 15m04s, snapshots_created=1) → `scanner_runs` id=2958 |
| J-06 Pages load only what they need | passing | passing | UT-J-06 replay PASS; `reports/qa/goal-ops-hardening-iter-62-evidence/J-06-verify.png` |
| J-07 Heavy aggregates never take the service down | partial | partial (unchanged) | UT-J-07 PASS rows (replay + live), `reports/qa/goal-ops-hardening-iter-62-evidence/J-07-verify.png`; but no health-latency drill this round — the ≤2s question is untouched, and the walkthrough recording still does not exist (`evidence_makeup`) |
| J-08 Backtest evidence serves from storage only | passing | passing (carried, not re-tested) | Outside this iteration's required set; no row this round; last verified `goal-ops-hardening-iter-61` |
| J-09 The backend discloses its own background-compute activity | passing | passing | UT-J-09 replay PASS; `reports/qa/goal-ops-hardening-iter-62-evidence/J-09-verify.png` |

Two replay rows FAILED and were overturned live by the browser lane (`reports/phase-goal-ops-hardening-iter-62-regression-replay-results.md`, reconciliation footer): J-01 (step 09) and J-04 (step 02). I checked the cause myself: the app was restarted at `2026-08-11T13:24:00Z` (boot banner in `logs/backend.log`) and both replay frames, taken one minute later, show the "initializing history 89/89" state. Those are false failures caused by the restart, not product faults. No `DEFERRED-BUDGET` rows; no `browser-infra.json`; no `journeys-changed.md`; all eight `spec_hash` values match `goal_gate.py hash-journeys`, run by me.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven presented as proven | OK | No evidence/claim surface touched; diff is 5 files (health endpoint, its test, two new frontend files, `/data`'s two catch handlers) |
| AG-2 decision-quality only | OK | No returns, targets, signals or orders anywhere in the diff |
| AG-3 displayed numbers correct | OK | Served `last_run_date` = `2026-08-03` = `max(scanner_runs.asof_date)` (I queried it); `/data` renders SNAPSHOT DATES **2958** / BACKFILL GAPS **2438** = `coverage_snapshot` payload = `count(distinct asof_date)` = 2958 / 2438. Four evidence-quality shortfalls logged minor: iter-62/a, /c, /f (see below) |
| AG-4 no overfit edges | OK | No referee, ledger or claim path touched |
| AG-5 determinism / no-lookahead | OK | No scoring or forward-return code touched; the only backend change is one `MAX()` read |
| AG-6 referee gate | OK | No evidence-derived claims this iteration |
| AG-7 no credentials in source | OK | `iter-62/scan-report.md` CLEAN; 5-file diff, no manifest, lockfile or LICENSE |
| AG-8 resilience / honest degrade | OK, one minor | The fix improves it (a transient blip no longer wipes real data). Minor iter-62/e: after any number of consecutive refresh failures `/data` keeps last-good numbers with no local "refresh failing" note; the global readiness badge still tells the truth about the backend |
| AG-9 offline-deterministic ingest | OK | All 30 ingest rows today are `provider='seed'`; the only non-seed rows since 2026-08-01 are id=297 and id=369, both pre-existing and previously ledgered |
| AG-10 host resource ceiling | OK | `git diff` AND `git status --porcelain` over `config.yaml`, `scripts/`, `project-extensions/` are BOTH empty; `config.yaml:1363-1364` still reads 8192 / 2; this round's boot banner reads `memory_cap_mb=8192 malloc_arena_max=2` and `host-guard: cpu_list=0-15 blas_threads=8` |

Six new minor entries (iter-62/a…f), none critical. Ledger: **182 total, 94 unresolved, 0 unresolved critical.** `coherence.md` is **COHERENCE-PASS** (0 blocking, 0 advisory). Review is **PASS**. Merged browser QA is **PASS 7/7**.

The app's own log for this round's process: **370** health answers, **zero** non-200 health answers, **zero** server errors of any kind, **zero** memory errors — while three data jobs ran at the same time in one process (heavy-warm windows opened 14:24:30, 14:25:18, 14:27:11 and all closed by 14:47:04 local). Whole-file totals are unchanged from last round (129 server errors, 8,211 memory errors), so this round added none.

## Next-Step Recommendation

Run the next round at full depth (this verdict makes that binding). In this order.

1. **Change the date J-05's check script uses, before anything else runs.** The script backfills
   2010-11-17 and demands "0 already snapshotted", but this round's own run created that day
   (`scanner_runs` id=2958). Next round it will report a failure that is not real. While editing it,
   also point its last three steps at the day it just created — they still look at 2010-11-16, a date
   from two rotations ago.
2. **Stop the checking robot from starting while the app is still waking up.** It began one minute
   after a restart and reported two false failures on journeys that are fine. A future round could
   read a false failure as a real break and stop the whole session.
3. **Make the slow part of the data job answer the health check faster.** This is the only path that
   closes J-07 "Heavy aggregates never take the service down" without the owner. From this round's own
   log, the first phase of the job's tail takes 55 seconds (`coverage_membership_timeline_refresh`) —
   that is exactly where last round's single slow answer (2.849 s) happened. Make that phase pause for
   other work, then re-run last round's measurement drill and publish the raw file.
4. **Record the walkthrough** for J-05 and J-07. Both ask for one in writing, it has never been made,
   and the recorder only runs at full depth. It rides along; it is never a round's own goal.
5. **Take one real picture per journey.** Two journeys were given the same image this round, and that
   image shows what neither of them claims.
6. Small and already written down: the new test file tells the reader to run it with `node`, which
   fails on this machine (`npx tsx` works); `/data` should say when its refresh is failing.
7. Carried, untouched: iter-29/b and the badge wording after a permanently failed warm-up (35th round
   unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az;
   iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj; iter-57/f; iter-57/l; iter-59/g;
   iter-59/h; iter-59/k. Deferred a twenty-eighth time: iter-33/g, the Regime Lab.
8. **OWNER — the same one-sentence decision, 14th round.** The app must answer its health check within
   2 seconds while a background job runs. That promise was written for a job of about 30 seconds; our
   jobs last 15 to 23 minutes. Please say which you want: keep the 2-second promise for long jobs
   (J-07 stays open until the app is faster), or apply it to short jobs only (J-07's last gap closes).
   Two facts worth knowing. First, the app served zero errors of any kind again this round, through
   three jobs running at once. Second, item 3 above is a real chance to close J-07 without you — so
   this is no longer the only way forward, just the fastest.
   Also still waiting on you: permission to fix the test-lane file (`scripts/automation/browser-qa-phase.sh`)
   and a cost decision — the automatic check now runs a real 15-minute data job every round.

The next round should fix the two checking-machinery problems (items 1 and 2), then try to make the
slow phase of the data job answer faster (item 3). A person can approve that in one sentence.
