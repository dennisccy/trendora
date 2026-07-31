# Iteration 40 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The one code change this iteration promised was delivered well. The `/data` coverage screen used to
load every price row for every stock into memory at once before it started working; it now reads them
in small batches, and I checked myself that the answer it produces is exactly the same as before. The
crash-honesty fix also worked: after a hard kill, the job history now shows 11 of 25 days done when 12
were really done, instead of being off by a factor of ten. But this iteration also shipped with a hole
that no one but the auditor noticed: **seven journeys that the plan required to be re-checked were not
checked at all.** No browser test ran, no replay ran, and not a single screenshot was saved. The
review, the QA and the closure gate all reported "pass" anyway. J-07 "Heavy aggregates never take the
service down" still does not fully pass, for a sixth time — one of this iteration's own two test runs
still froze the server and nobody could find out which part froze.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | **unknown** (not tested; its data path changed) | none this iter — `reports/phase-goal-ops-hardening-iter-40-ui-test-results.md` row `UT-J-01` = SKIP; no replay artifact; last real proof `reports/qa/goal-ops-hardening-iter-39-evidence/J-01-verify.png` |
| J-03 No per-run range cap | passing | passing (carried, A.6 durability) | `reports/qa/goal-ops-hardening-iter-39-evidence/J-03-verify.png`; neither diff hunk touches range validation |
| J-04 Non-blocking boot with visible status | passing | **unknown** (not tested; its data path changed) | none this iter — `UT-J-04` = SKIP. Partial live corroboration only: `runs/goal-ops-hardening-iter-40/checkpoint-drill/post-restart-persisted-row.txt` (row flipped to `interrupted` after restart) |
| J-05 Aggregates are precomputed at ingest, never on the fly | passing | **unknown** (not tested; its data path changed) | none this iter — `UT-J-05` = SKIP; the changed function is inside the coverage payload producer |
| J-06 Pages load only what they need | passing | **unknown** (not tested; its data path changed) | none this iter — `UT-J-06` = SKIP; no page-load budget measured |
| J-07 Heavy aggregates never take the service down | partial | **partial** (6th consecutive) | `runs/goal-ops-hardening-iter-40/wedge-drill/run2-monitor.csv` (28/28 HTTP 200, VmPeak 2,713,600 kB); `logs/backend.log:149620-149729` (verified identical to the saved excerpt); `runs/goal-ops-hardening-iter-40/wedge-drill/run1-notes.md` (the process freeze that keeps it open) |
| J-08 Backtest evidence serves from storage only | passing | passing (carried, A.6 durability) | `reports/qa/goal-ops-hardening-iter-39-evidence/J-08-verify.png` — I opened it (spot-check 1): `/backtest` shows "Viewing as-of 2026-07-22 (latest)" served from storage |
| J-09 The backend discloses its own background-compute activity | passing | passing (carried, A.6 durability) | `reports/qa/goal-ops-hardening-iter-39-evidence/J-09-verify.png` — I opened it (spot-check 2): top bar shows "background compute running (1)" |

**Why four journeys became `unknown` rather than staying `passing`.** Nothing was found broken. They
were simply never tested this run, and the code that feeds each of them changed, so the older proof no
longer covers the build that exists now. Hunk 1 (`_missing_data_diagnostic` streaming) sits inside the
producer of the `/data` coverage figures (J-05, J-06); hunk 2 (`_RUN_RECORD_CHECKPOINT_INTERVAL_S`
10.0 -> 1.0) writes the very job-history row J-01 and J-04 read. J-03, J-08 and J-09 keep `passing`
because neither hunk lies on their path, which is exactly what the evidence-durability rule allows.
The auditor's own instruction agrees: "Do not treat J-01, J-03, J-04, J-05, J-06, J-08, J-09 as
re-verified this iteration" (`docs/handoffs/goal-ops-hardening-iter-40-audit.md`, section 5).

### J-07 against its four acceptance clauses (this iteration's evidence)

| Clause | State | What I verified myself |
|---|---|---|
| Single canonical producer | holds | `compute_forward_aggregates` is byte-frozen by the spec and absent from the diff |
| Byte-identical correctness | holds | The new equality test replays the OLD `.all()` path as a reference and compares default vs batch-size-3 output; the auditor independently traced identity structurally (sorted-universe iteration + set membership) |
| No unbounded whole-table materialization; never wedged; honest health | **not closed** | The named site IS fixed (`data_manager.py:271` now `.yield_per`). But run 1 froze the process at the same 2650 MB cap with an uncaught background-thread `MemoryError` and no traceback, and the frozen thread was never identified. Separately, `prices.py:132-142` still builds every `daily_prices` row into one dict — `yield_per` bounds its cursor, not its accumulator |
| `[NEW]` walkthrough recorded | not recorded (10th iteration) | `reports/demo/goal-ops-hardening-iter-40/` is empty; demo verdict `NOT_YET`, zero steps. Capture-only — carried as `evidence_makeup`, never a blocker |

Also on the record: I recomputed the health latencies from the raw capture — **0 of 28 polls met the
committed 0.1 s budget** (min 0.1234 s, mean 0.3266 s, max 0.8083 s). Seventh consecutive miss; owner
decision (iter-34/j).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language | OK | No score/ranking/evidence surface touched; diff is a fetch strategy, a throttle constant and QA tooling |
| AG-2 decision-quality only | OK | No returns, targets, signals or order simulation anywhere in the diff |
| AG-3 displayed numbers correct | OK, improved | The checkpoint fix closes iter-39/w: kill at 12 of 25 dates, persisted 11, and `10 + 1 + 0 = 11` is internally consistent (`post-restart-persisted-row.txt`, read by me). iter-36/n stays open, untouched |
| AG-4 no overfit edges | OK | No claim, referee or ledger path touched |
| AG-5 determinism / no-lookahead | OK | Fetch strategy only; the query, its `WHERE` clause and every consumer are unchanged |
| AG-6 referee gate | OK | No evidence-derived claims this iteration (ops/correctness work) |
| AG-7 no hard-coded credentials | OK | `scan-report.md` = CLEAN. I also grepped both drill `config.scratch.yaml` files: env-var **names** only (`TIINGO_API_KEY`, `FRED_API_KEY`, …), never values. `git check-ignore` confirms both 545-625 MB `drill.db` files are ignored |
| AG-8 resilience to data scale | **minor, open** | Improved at the named site and independently measured by the auditor (+4.6 MB vs +349 MB on a 1M-row table). Still open: iter-39/u (the run-1 freeze, undiagnosed) and iter-29/d (`prices.py:132-142` still materializes the whole `daily_prices` table into RAM, which docs/goal.md's Success Criteria forbid verbatim) |
| AG-9 offline-deterministic ingest | OK | No manifest in the diff; no new dependency (`py-spy` deliberately NOT added). Both drills ran on throwaway sqlite DBs under `runs/`; `_BACKFILL_KINDS = ("backfill","both")` vs `_FETCH_KINDS = ("fetch","both")` (`data_manager.py:105-106`) confirms the request's `source: "yahoo"` field never resolves a live provider for a backfill |
| AG-10 host resource ceiling | OK | `git diff ca42137f..HEAD --stat -- scripts/dev.sh scripts/start-backend.sh scripts/start-frontend.sh project-extensions/host-guard/` returns ZERO lines — all byte-identical, so AG-10's own REGRESSION trigger did not fire. Both drills launched via `scripts/start-backend.sh` with the host-guard banner present in the live log |
| **New this iteration** | **iter-40/y (minor, open)** | Seven required-still-passing journeys were never verified; browser QA headlined `SKIPPED` with 8/8 SKIP rows, the evidence directory was never created, no replay artifact exists, and review + QA + closure all reported clean |

Ledger after this iteration: **37 total, 13 unresolved, 0 critical.** Resolved this iteration:
iter-39/v, iter-39/w, iter-39/x. Every carried open item received an ITER-40 note recording what I
verified rather than inherited.

## Next-Step Recommendation

Run the next iteration at full depth. Do these, in order.

1. **Make the seven journey checks actually run — this is now the top item, ahead of J-07.** Two small
   fixes cause it. First, the health check that decides whether the app is up asks for
   `http://localhost:8255/health`, but the real address is `http://localhost:8255/api/health`; the
   wrong address returns "404 not found", which the checker read as "the app is down" even though the
   app was answering. Second, "this iteration has no new screens" must stop switching off the re-check
   of screens that already exist. After the fix, all seven journeys must produce a fresh screenshot.
2. **Find out what froze the server in the first test run.** Do not tune the memory limit again. Turn
   on Python's built-in thread-stack dump (`faulthandler`, triggered by a signal) before starting the
   drill; it works from inside the program and needs no special permission and no new package, so the
   two blocked routes (a machine-policy change for `gdb`, or installing `py-spy`) are not needed.
3. **Fix the last place that loads the whole price table into memory** (`prices.py:132-142`): the read
   is streamed but every row is still collected into one dictionary. The project's own success
   criteria forbid this in plain words, and it is the largest memory user during the test that froze.
4. **Keep watching after the job finishes, not just during it.** The monitor stops the moment the job
   reports "done", but the earlier freeze appeared just after that point.
5. Small and already written down: give the checkpoint timing a count-based floor as well as a
   time-based one; align the framework's list of allowed verdict words so `BLOCKED` is recognized
   everywhere.
6. Capture only, never an iteration's goal: J-07's `[NEW]` walkthrough recording (tenth iteration
   missing).
7. **Owner decisions, unchanged, and both should be settled before any success attempt.** (a) The
   `/api/health` response-time target of 0.1 s was missed for the seventh time — 0 of 28 checks met it
   this run. Three choices, all yours: accept the current honest-warning behaviour, relax the target
   for the short period while background work is running, or ask for the fix that serves readiness
   from a saved snapshot. (b) Whether `start-frontend.sh` should also be covered by the host-protection
   file list.

In one sentence: approve one more full-depth iteration whose first job is to make the seven journey
checks run again, and whose second job is to identify the thread that froze the server.

## Halt Justification (if halting)

Not halting. ESCALATE continues the loop and only forces the next iteration to run the full pipeline.
