# Iteration 29 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The main fix worked. The Evidence page now builds its drawdown figures in small bounded batches, and I saw
the proof myself: the full-page picture of `/evidence` shows all 7 claim cards with real numbers, and the
backend log has no memory failure from that page at all. The session's oldest open problem is closed. But
this same run turned up three NEW out-of-memory failures on three other paths, and the browser report said
there were none — that claim is wrong, and I checked the log line by line. Two journeys are marked
"partly done", not "done": J-06 "Pages load only what they need" never wrote its fresh timings into the
budgets file, and J-07 "Heavy aggregates never take the service down" had a memory failure inside the very
function it names. Nothing broke that used to work, so the loop keeps going.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | reports/qa/goal-ops-hardening-iter-29-evidence/J-01-verify.png (replay 6/6 PASS) |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-29-evidence/J-03-verify.png (byte-identical to J-04's — no independent image) |
| J-04 Non-blocking boot with visible status | passing | passing | reports/qa/goal-ops-hardening-iter-29-evidence/J-04-verify.png (opened; readiness pill reads "Initializing… history 89/89") |
| J-05 Aggregates are precomputed at ingest, never on the fly | passing | passing | reports/qa/goal-ops-hardening-iter-29-evidence/J-05-verify.png + DB run 201 `aggregates_refreshed` |
| J-06 Pages load only what they need | passing | **partial** | reports/qa/goal-ops-hardening-iter-29-evidence/J-06-evidence-page.png (opened) — step 2 unmet: `reports/perf-budgets.md` unmodified |
| J-07 Heavy aggregates never take the service down | passing | **partial** | reports/qa/goal-ops-hardening-iter-29-evidence/J-07-backfill-complete.png (opened) + logs/backend.log:130039-130048 |
| J-08 Backtest evidence serves from storage only | passing | passing | reports/qa/goal-ops-hardening-iter-29-evidence/J-08-verify.png (replay PASS) |
| J-09 The backend discloses its own background-compute activity | passing | passing | reports/qa/goal-ops-hardening-iter-29-evidence/J-09-verify.png (opened; "background compute running (1)" pill) |

Merged results file: `reports/phase-goal-ops-hardening-iter-29-ui-test-results.md` (8/8 PASS as written).
Replay lane: `reports/phase-goal-ops-hardening-iter-29-regression-replay-results.md` (6/6 PASS, zero FAIL,
zero reconciliation overturns). I did not accept the merged file's two smoke rows at face value — see the
Anti-goal check and the reasoning in the evaluator log.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (no unbacked "proven") | OK | No claim-status code in the diff; `/evidence` cards all render "FAIL — holdout edge …" plus "Not yet proven"-family copy in J-06-evidence-page.png. |
| AG-2 (decision-quality only) | OK | No returns promise, price target, signal or order path added; the new UI string is "Unavailable — monitored and refreshed as new data arrives." |
| AG-3 (displayed numbers correct) | OPEN QUESTION | `/evidence` figures are real and match the ledger's 7 claims. But data_provider_runs 201 lists `coverage` + `membership_timeline` as refreshed while logs/backend.log:130004 records that refresh failing with MemoryError in the same window; fresh `coverage_snapshot` rows for r1874 also exist (00:00:49 / 00:01:00). I could not settle which reading is right, so I recorded it as an unsettled question, not a scored violation. |
| AG-4 (no overfit edges) | OK | No referee/ledger code in the diff; claim verdicts unchanged. |
| AG-5 (determinism / no lookahead) | OK | The `as_of` cutoff moved UP into the new `_runs_with_fr()` discovery query, upstream of every derived structure; TC-3 asserts zero returned observations reference a run dated after D; the audit re-derived the same. |
| AG-6 (referee gate) | OK | No new evidence-derived claims this iteration. |
| AG-7 (no hard-coded credentials) | OK | `runs/.../iter-29/scan-report.md`: CLEAN — no secret findings on added lines. Config change is `research.factor_join_run_chunk: 100`. |
| AG-8 (data-scale resilience) | **4 findings, all minor, all unresolved** | (a) `/research/factor-lab` 500 on every visit from MemoryError (4/4 requests at logs/backend.log:83701, 86231, 127815, 129033; audit FAIL / ux-regression FAIL). A code fix landed AFTER the audit and one live request returned 200 (:129876), but nobody re-ran TC-9 in a browser. (b) Boot warm-up MemoryError (:130049-130094, `warmup.py:194` → `forward_symbols_for_run`) leaves readiness stuck "initializing" forever. (c) `compute_forward_aggregates` MemoryError (:130039-130048, `forward_testing.py:965`). (d) Ingest coverage refresh MemoryError inside the whole-table `daily_prices` prefill (:130004-130038, `prices.py:141`). Severity `minor` on stated grounds — see the assumption ledger. |
| AG-9 (offline-deterministic ingest) | OK | No manifest change; no network client added; the ingest ran against `provider: seed` (data_provider_runs 201). |
| AG-10 (host resource ceiling) | OK | logs/backend.log boot banner: "start-backend.sh: launching … memory_cap_mb=6144 malloc_arena_max=2 / host-guard: cpu_list=0-3,8-11 blas_threads=4". Dev and audit test runs used `taskset -c 0-3,8-11` with BLAS/OMP caps. No HOST-GUARD block removed. |
| Secrets / paid SaaS / license | OK | `scan-report.md` CLEAN on all three categories; no manifest or LICENSE file in the product diff. |
| Fabricated / substituted data | OK | Byte-identity oracles pin output equality (TC-2 and `_all_pools_reference_unchunked`); the Factor Lab error box explicitly says "No figures are shown rather than fabricated values". |

**Coherence:** `runs/goal-session-ops-hardening/iter-29/coherence.md` = COHERENCE-PASS. No structural veto.
**Goal-edit drift:** no `journeys-changed.md`; all 8 `spec_hash` values match `goal_gate hash-journeys`.

## Next-Step Recommendation

Run the next round at full depth. Do these five things, in this order.

1. Prove the Factor Lab page actually works now. Open `/research/factor-lab` in a real browser and take a
   picture that shows the decile table and the rank-IC numbers. Someone repaired the code after the audit
   was written, but no report describes that repair, no reviewer checked it, and no one has opened the page
   since. The audit predicted the crash would simply move to a different line in the same function, and that
   prediction has not been tested. If the page still fails, bound the returned pools too, not just the
   lookup map.
2. Stop the three new out-of-memory failures. They are on three separate paths: the start-up warm-up
   (`warmup.py:194`), the background forward-aggregate job (`forward_testing.py:965`), and the ingest
   coverage refresh, which still reads the whole price table into memory (`prices.py:141`). The second one
   is inside a function this iteration deliberately froze, so the planner must lift that freeze on purpose.
3. Decide what the top-bar badge should say when start-up warm-up fails for good. Right now it says
   "Initializing… history 89/89" forever while the app is fully usable. That is confusing. Either recover
   the warm-up or say plainly that it stopped.
4. Write this iteration's page-load timings into `reports/perf-budgets.md`. That single missing edit is the
   only reason J-06 "Pages load only what they need" is marked partly done. Also run the J-06 replay script
   through the deterministic lane so its row appears in the merged results file.
5. Tell the browser-testing step to stop claiming "zero memory errors" without showing the log lines it
   counted. This run claimed zero and there were three. Ask it to print the boot line number it counted
   from, so the number can be checked.

One more thing for the owner to decide, not urgent: the run record for the 2022-04-12 backfill says
"coverage refreshed" while the log says that refresh ran out of memory. Someone should confirm which is
true before the next release note repeats it.
