# Iteration 44 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The app still goes offline when a heavy background calculation gets stuck, and this time it was
offline for 20 minutes and 51 seconds and had to be killed by force. Six of the eight journeys were
re-checked and passed. The two journeys this round aimed at both failed: J-05 "Aggregates are
precomputed at ingest" was tested for the first time on a day that had never been saved before, and
the job ran for ten minutes without saving anything and then failed; J-07 "Heavy aggregates never
take the service down" failed for the third round in a row. The good news is real and I put it
first: after seven rounds of guessing, this round finally caught the app in the act and printed out
what it was stuck on. The stuck step is now named — the app recalculates roughly 2,860 days times
591 companies of membership history every single time you ingest one day.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | reports/qa/goal-ops-hardening-iter-44-evidence/J-01-verify.png (row UT-J-01, ui-test-results.md:18) |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-44-evidence/J-03-verify.png (row UT-J-03, :19) |
| J-04 Non-blocking boot with visible status | passing | passing | reports/qa/goal-ops-hardening-iter-44-evidence/J-04-verify.png (row UT-J-04, :20) |
| J-05 Aggregates are precomputed at ingest, never on the fly | partial | **failing** | reports/qa/goal-ops-hardening-iter-44-evidence/UT-J-05-job-failed.png + UT-J-05-J-07-job-and-outage-timeline.csv (row UT-J-05 = FAIL, :24) |
| J-06 Pages load only what they need | passing | passing | reports/qa/goal-ops-hardening-iter-44-evidence/J-06-verify.png (row UT-J-06, :21) |
| J-07 Heavy aggregates never take the service down | failing | failing | reports/qa/goal-ops-hardening-iter-44-evidence/UT-J-07-outage-checking-backend.png + UT-J-07-health-poll-baseline.csv (row UT-J-07 = FAIL, :25) |
| J-08 Backtest evidence serves from storage only | passing | passing | reports/qa/goal-ops-hardening-iter-44-evidence/J-08-verify.png (row UT-J-08, :22) — spot-checked by me |
| J-09 The backend discloses its own background-compute activity | passing | passing | reports/qa/goal-ops-hardening-iter-44-evidence/J-09-verify.png (row UT-J-09, :23) — spot-checked by me |

Deferred (`DEFERRED-BUDGET`): none. No `browser-infra.json`; no `journeys-changed.md`. All eight
`spec_hash` values match `goal_gate.py hash-journeys docs/goal.md`, which I ran myself — the goal
text is unchanged since each journey was last verified.

**Timing caveat I state rather than bury.** The six passing frames were captured 19:48-19:49Z on the
backend launched 19:42:01Z. A different process instance of the *same build* (launched 19:51:08Z)
went fully unreachable 20:10:33Z-20:31:24Z. The six passes attest this build's code on a healthy
process, not the instance's stability under a heavy warm. Same caveat as iters 42 and 43; any
achievement run must re-verify all six after the availability defect is closed.

**TC-13 closed and verified by me.** `md5sum` over the evidence directory returns eight distinct
checksums — iter-43/ai (two journeys sharing one screenshot) is fixed, not merely claimed.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven/confident without a ledger entry | OK | No evidence-ledger or badge surface in the diff. Diff is 5 product files (`api/data.py`, `engine/data_manager.py`, `start-backend.sh`, 3 test files) per `iter-44/iter-diff.md`; no proven-language added. |
| AG-2 decision-quality only | OK | No return promise, price target, signal, or order path added; nothing in the diff touches a recommendation surface. |
| AG-3 displayed numbers correct | OK, with one note | Six replay rows held all expects. Note, not a violation: J-07's golden anchors `n=8878`/`3508` no longer appear because the dataset grew across 44 iterations (llm results :201-210). That is stale test text, not a wrong displayed number — `Backfill gaps` reads 2533 today, consistent with the drift. Golden refresh owed. |
| AG-4 no overfit edges | OK | No referee/claim/holdout code touched. |
| AG-5 determinism + no lookahead | OK | No scoring or forward-return computation in the diff; the audit's three fixes are exception handling and a message string. |
| AG-6 evidence claims need a referee verdict | OK | No evidence-derived claim shipped; post-decompose gate is automatic for this journey set per goal.md Loop mechanics. |
| AG-7 no hard-coded credentials | OK | `iter-44/scan-report.md`: "CLEAN — no secret, dependency, or license findings on added lines"; 0 untracked files. No manifest changed; no new dependency. |
| AG-8 resilience to data scale | **VIOLATED (minor) — new: iter-44/ak, iter-44/al** | The service went fully unreachable for 20m51s under a heavy warm (51 timed-out health polls, which I counted in the timeline CSV). Its graceful-degradation half HOLDS — the UI showed an honest "Checking backend…" loading state, never a blank application-error page (I opened the frame). Also newly named by me from `logs/backend.log`: two unbounded per-row dict accumulators still raising `MemoryError` at the raised 8192 MB cap (`research.py:777`, `forward_testing.py:2343`), both caught by their isolation handlers. Scored minor — see below. |
| AG-9 offline-deterministic ingest | OK | No network call added; every changed backend line is exception handling or a message. Ingest ran against the committed seed. |
| AG-10 host resource ceiling | OK | I read the launch-script diff myself: the three uvicorn flags are ADDITIVE to the existing enforcement. `ulimit -v $((MEMORY_CAP_MB * 1024))` still at `start-backend.sh:56`, `MALLOC_ARENA_MAX` at `:60`, and the `==== HOST-GUARD (goal.md AG-10) — DO NOT REMOVE OR WEAKEN ====` block intact at `:76-101`. No cap value changed; no `config.yaml` or `host-guard.env` edit. |

**Severity call, stated rather than assumed.** I scored the outage MINOR, not critical, and I record
that I weighed critical. Grounds: this iteration did not introduce or widen the defect (its whole
product diff is a 503 mapping, a job-message fix, two exception guards, and additive launcher
flags); the scan report is CLEAN; the trigger was a background compute already stalled at
`horizons_done: 0/5` before the tester acted (llm results :32-38) plus one mandated backfill; the UI
degraded honestly rather than showing a broken page; and this session has carried the same
availability family as minor since iter-35/k. A reader who treats a 21-minute outage of the core
operation as a critical AG-8 breach regardless of who authored it would score this critical and halt.

Ledger after this iteration: **52 total, 17 unresolved, 0 critical.** Resolved this iteration:
iter-43/ai (duplicate screenshots) and iter-44/an (the failed-job message no-op, fixed in-audit with
a regression test). New and open: iter-44/ak, iter-44/al, iter-44/am.

## Pipeline Health

`coherence.md` = **COHERENCE-PASS** (no blocking violations; one advisory that says explicitly the
coherence pass must not be read as the iteration's goal being met). Review = **FAIL** with one
CRITICAL finding. QA = **FAIL** (revalidated; its earlier 20:52 PASS with "Browser QA SKIPPED" was
caught by the auditor as T3 and corrected). Audit = **FAIL** with one CRITICAL (B3). Browser QA =
**FAIL**, 6/8. ux-regression = SKIPPED. `status.json` = `blocked` / `audit_qa_failed`, three
blockers listed. Note `browser_checks_run: false` in `status.json` is stale — both browser lanes
demonstrably ran (replay 19:48-19:49Z with six dated PNGs; LLM lane 20:02-20:35Z).

## Next-Step Recommendation

Full depth (required, because this verdict is ESCALATE). In order:

1. **Make the app unable to stay offline, even when it is stuck inside itself.** This round proved
   that the shutdown deadline it added can never fire in the situation that matters: the deadline is
   enforced by the very machinery that freezes. The fix is a watchdog OUTSIDE the app — the launch
   script starts the web server in the background, waits its own deadline, and kills it if it will
   not stop. This is small, mechanical, and it turns a 21-minute silence into a short one. Give it
   its own round and its own name; do not fold it into other work.
2. **Fix the real cause of the freeze, now that we finally know it.** Ingesting ONE day currently
   makes the app recalculate its whole membership history — about 2,860 days across 591 companies —
   because the saved copy is thrown away wholesale whenever the data changes. Make that saved copy
   update for the new day instead of being rebuilt from scratch, and prove the result is identical
   to today's output. This is the single highest-value piece of work on the board and it deserves a
   round of its own.
3. **Re-run the two failing checks afterwards** — J-05 "Aggregates are precomputed at ingest" on a
   day that has never been saved, and J-07 "Heavy aggregates never take the service down" — and
   re-run the other six too, because their pictures were taken 21 minutes before the app went silent.
4. **Small and already written down:** the reviewer found that the memory-pressure safety test still
   fails about half the time, with a third escape route the audit did not close (something inside the
   error-logging itself runs out of memory); run that test three to five times in a row before anyone
   calls it fixed. Refresh J-07's stale test text (`n=8878`, `3508`) so it matches today's data.
   Update the stale comment at `data_manager.py:4730`.
5. **Carried, untouched:** iter-29/b and the badge wording after a permanently failed warm-up
   (SIXTEEN rounds unmade); iter-31/e; iter-32/f (now partly answered — the cost is inside the
   membership recompute, not the forward-aggregate loop); iter-35/k; iter-36/n; iter-37/o; iter-37/q.
   New this round: two unbounded memory accumulators on the evidence path
   (`research.py:777`, `forward_testing.py:2343`) — the right place to look next for the long-standing
   "no unbounded loads" promise, instead of a sixth attempt at the price cache.
6. **Deferred a TENTH time:** iter-33/g, Regime Lab's cold pooled view.
7. **Capture only, never a round's goal:** J-07's `[NEW]` walkthrough (fourteenth round unrecorded)
   and J-05's acceptance frames.
8. **Owner:** nothing outstanding. Both standing owner items closed at iter-43, and nothing this
   round needs a decision only the owner can make.

In one sentence for approval: the next round should build a watchdog outside the app that force-stops
a frozen backend, and the round after that should stop the app rebuilding its entire membership
history every time one day of data is added.
