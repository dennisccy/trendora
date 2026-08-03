# goal-ops-hardening-iter-43 Audit Report

**Date:** 2026-07-31
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

All five code deliverables landed correctly and are honestly documented: the `_BarCache.prefill` filter
revert is byte-faithful to the pre-iter-42 shape (independently re-run: `test_bar_cache.py` **22/22**),
the job-launch honesty fix marks the job `failed` in both the live registry and the persisted
run-history row and returns 503 instead of a false `200 {"status": "running"}`, and
`start-frontend.sh` now carries a HOST-GUARD block that is a byte-for-byte structural mirror of
`start-backend.sh`'s, with `HOST_GUARD_MARKER_FILES` extended. **But the iteration's second target
journey, J-07, does not pass**, and the QA report says otherwise: `reports/qa/...-qa.md` records
`**Verdict:** PASS` with a "`✓ PASS on memory/availability`" row for TC-7/TC-8 written 32 minutes
before the browser-QA lane returned `Browser QA Verdict: FAIL` on UT-J-07 — a directly-observed
**multi-minute total connection-refused outage** under a stalled background compute. The dev's own
`reports/perf-budgets.md` §5 is the honest record and contradicts the QA report: 63.6% of 272 health
polls breached the rescoped ≤2s budget and TC-8 was "not attempted this session". The iteration
delivered what it promised — including an honest re-score — but the re-score for J-07 is a FAIL, and
the evaluator must read it that way.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap): J-07's spec'd ≤2s bounded-compute-window `/api/health` budget measurably
fails; TC-8 was never obtained.**
`reports/perf-budgets.md:5787-5800` (Iteration 43 §5, latency table). TC-7 requires *"every poll
returns HTTP 200 **within the rescoped ≤2s bounded-compute-window budget**"* (spec
`docs/phases/goal-ops-hardening-iter-43.md:296-299`). Measured: **173 of 272 polls (63.6%) exceeded
2 s**, max 6,599 ms, and the profile *worsened* across the window (1,725 ms → 2,838 ms → 3,162 ms
window means) rather than staying flat as every prior BCW measurement in this file did. TC-8 (a
concurrent cached `GET /api/backtest` staying 200 against the live deep-basis DB) is recorded in the
same section's per-TC table as *"not attempted this session … deferred"*. The DEFINITION OF DONE item
*"J-07 steps 1-4 are re-verified live … against `memory_cap_mb: 8192` and the rescoped ≤2s
bounded-compute-window `/api/health` budget"* (spec `:242-245`) is therefore **not met**.
**Not fixed — deliberately.** The named probable cause (T2, iter-41's `_SymbolColumns` per-call
slicing cost, whose exposure this iteration's mandated revert widens from 548 to 591 symbols) is on
the spec's own OUT OF SCOPE list (`:220`), and the conditional TC-10 warm-seam bound is gated on
*"over cap or wedging"* — neither of which the memory axis showed (VmPeak flat at 32.4% of cap for
1,001 s). Fixing this requires the owner/evaluator disposition the dev handoff and perf-budgets both
request. The developer's disclosure of this is exemplary and is the single best artifact of this
iteration.

**B2 — IMPORTANT (gap): a heavy background aggregate compute left the service fully unreachable for
several minutes — a strictly worse J-07 failure than B1's slow-but-200.**
`reports/phase-goal-ops-hardening-iter-43-ui-test-results.llm.md:22-57` and `:140-153`. Directly
observed by the browser-QA lane *before it executed a single test step*: `curl
http://localhost:8255/api/health` returned connection-refused (exit 7, HTTP `000`) on five consecutive
retries, `ss -ltn` confirmed nothing listening on 8255, while the uvicorn process (PID 3524903) was
alive at 82-98% CPU with `logs/backend.log` ending mid-shutdown at `INFO: Shutting down` / `INFO:
Waiting for background tasks to complete.` The blocking work was a `background_compute` window
(`asof_key=2026-07-21`, `dataset_version=r1920-f4019170`) observed at `horizons_done: 0/5` after 137 s
and never advancing; the process required `kill -9`. This is a direct contradiction of J-07's
acceptance ("heavy aggregates never take the service down").
**Concrete lead for the next iteration (not fixed here):**
`incredible_auto_dev/scripts/start-backend.sh:95` execs uvicorn with no `--timeout-graceful-shutdown`,
so `Server.shutdown()` waits unboundedly on outstanding server tasks. Note the historical dispatch
thread itself *is* `daemon=True` (`apps/backend/app/engine/forward_testing.py:1691-1697`), so it is not
what uvicorn is waiting on — the blocking task is an in-flight request handler, and the precise
mechanism was **not isolated by anyone this iteration**. I did not fix this: it is outside this
iteration's IN SCOPE list (which names `start-frontend.sh` only), the true mechanism is unproven, and a
shutdown-timeout/cancellability change to the warm seam is exactly the "materially larger, unevidenced
change" the spec's OUT OF SCOPE section reserves.

**B3 — IMPORTANT (fixed): the new thread-launch guard was keyed to `RuntimeError` alone, leaving the
identical silent-zero-work hole open on its nearest sibling exit.**
`apps/backend/app/engine/data_manager.py:4774` and `:4803` (pre-fix). The spec's own error case is *"a
`RuntimeError` **(or equivalent)** raised by `threading.Thread.start()` must never leave a job's
run-history row at `running` with no further update"* (spec `:266-268`). `Thread.start()` wraps
`_start_new_thread` in a bare `except Exception` (CPython `Lib/threading.py`, confirmed by
`inspect.getsource` on this venv's 3.12.13) precisely because the C-level `thread.start_new_thread` has
two failure exits under one memory ceiling: `RuntimeError("can't start new thread")` when the OS
refuses the thread, and `PyErr_NoMemory()` → **`MemoryError`** when its own bootstate allocation fails
first. iter-42's outage produced both side by side under the same `ulimit -v` wall. **Live-proved
before fixing:** a `MemoryError` parametrization left `start_data_job`'s job at its `create_job()`-time
`running` default with **no `DataProviderRun` row at all**, and `start_resume_job`'s at
`get_job(...) is None` — the exact J-05 regression this iteration exists to close.
**Fix applied** (see §4): both guards now catch `Exception` and **always re-raise** (the handler only
ever adds an honest record — it can never convert a launch failure into a success); the two
`api/data.py` mappings widened to `(RuntimeError, MemoryError)` so the honest 503 covers both exits.

**B4 — OBSERVATION: the J-38 Retry path records the failure honestly but returns 500, not 503.**
`apps/backend/app/engine/data_manager.py:5068` (`retry_run` → `start_data_job`) reaches
`_fail_unlaunched_job` and so gets the same honest `failed` row, but `apps/backend/app/api/data.py:306`
does not catch the re-raised launch failure, so the endpoint answers 500 rather than the 503 its two
siblings now return. Behaviour is unchanged from before this iteration and the DoD only names the two
job/resume endpoints; noted for consistency, not a defect.

**B5 — OBSERVATION (verified sound): the prior audit pass's B2 `_run_detail` change is provably a
no-op on every pre-existing path.**
`apps/backend/app/engine/data_manager.py:4037` now serves `prog.message` in place of
`_final_summary(prog)` when `status == "failed"`. I traced all three callers rather than accepting the
inline claim: `_run_job`'s `finally` assigns `prog.message = _final_summary(prog)` at `:4543` and calls
`_finalize_run_record` at `:4553`, mutating only `prog.finished_at` in between — a field
`_final_summary` (`:3933-3963`) never reads — so the two expressions are the same string there;
`_create_run_record` (`:4055`) and `_checkpoint_run_record` (`:4152`) both serialize a still-`running`
job (called from the backfill loop at `:3056`/`:3141`), which the guard never matches. Confirmed
empirically by 219 passing tests across the three suites that exercise this serializer.

### Frontend Findings

**F1 — OBSERVATION: `apps/frontend/tsconfig.json` carries an un-attributed working-tree diff.**
The `include` array is re-ordered (`.next-alt-qa/types/**/*.ts` moved up, `next-env.d.ts` moved down) —
five identical entries, semantically inert, written by the real `next build` the new host-guard test
runs. It is not in `runs/goal-ops-hardening-iter-43/status.json`'s `changed_files`. Harmless, but it
will land in this iteration's commit as an unexplained diff unless reverted.

### Test Findings

**T1 — IMPORTANT (gap): the QA report overstates its own evidence and predates the browser lane's
FAIL.** `reports/qa/goal-ops-hardening-iter-43-qa.md:3`, `:84`, `:122`, `:166`.
Three specific over-claims:
1. `:84` — *"**Availability (TC-8)** | PASS | All 272 recorded `GET /api/health` polls returned HTTP
   200"*. TC-8 is the **concurrent cached `GET /api/backtest` read** clause (spec `:300-302`); the 272
   health polls are TC-7's availability clause. `perf-budgets.md` §5's own per-TC table records TC-8 as
   *"not attempted this session against the live deep-basis DB … deferred"*. A deferred criterion is
   labelled PASS against another criterion's evidence.
2. `:122` — TC-7 is marked *"✓ PASS on memory/availability … Latency finding disclosed … but does not
   block"*, when the ≤2s latency ceiling is part of TC-7's literal wording, not an adjacent note.
3. `:166` — *"No blockers to shipping this iteration"* directly contradicts
   `runs/goal-ops-hardening-iter-43/status.json`'s own populated `blockers[]` array, and was written at
   13:50 — 32 minutes before `reports/phase-goal-ops-hardening-iter-43-ui-test-results.md` recorded
   `Browser QA Verdict: FAIL` on target journey UT-J-07 at 14:23.
**Not rewritten.** Correcting another lane's report is outside an auditor's remit and would erase the
timeline that makes the sequencing legible; this audit report is the corrective record. **The
evaluator must not read the QA PASS as a J-07 pass.**

**T2 — GAP: `status.json` is factually stale about the browser lane.**
`runs/goal-ops-hardening-iter-43/status.json:9,25` reads `"browser_checks_run": false` and
`"next_action": "review"` although both browser lanes ran (deterministic replay 13:53, LLM browser-QA
14:22) and one FAILED; its single `blockers[]` entry names only the dev's incomplete live measurement,
not UT-J-07's FAIL or the total-unavailability incident. I deliberately did **not** mutate it — it is
harness-owned pipeline state and an auditor rewriting it mid-run risks corrupting the state machine —
but the evaluator should treat `ui-test-results.md` as authoritative over this file.

**T3 — OBSERVATION: two evidence screenshots are byte-identical duplicates.**
`md5sum` over `reports/qa/goal-ops-hardening-iter-43-evidence/`: `J-03-verify.png` ==
`J-04-verify.png` (`d4d84c50…`), and — more notably — `UT-J-07-fail.png` == `UT-J-05-result.png`
(`243d1c62…`). The cited "evidence" image for UT-J-07's FAIL therefore does not depict the failure. The
failure's real evidence (curl exit 7, `ss -ltn`, the `logs/backend.log` shutdown lines, the PID/CPU
readings) is narrative and specific enough to stand on its own, so this weakens the artifact, not the
finding.

**T4 — OBSERVATION (positive): test quality is high, not shallow.**
`test_bar_cache.py`'s replacements are genuine byte-identity oracles that assert the *removed*
condition is truly gone (SPY present after `expected_symbols=["AAA"]`, **zero** follow-up queries — the
exact inverse of the assertion they replace), not merely that the code compiles.
`test_start_frontend_script.py:639-687` reads the launched `next start` worker's own
`/proc/<pid>/status` `Cpus_allowed_list` and compares it to `HOST_GUARD_CPU_LIST`, and covers the
file-absent and `HOST_GUARD_ENABLED=0` branches against ambient values. The prior audit pass's B1
regression test derives its `symbols_ok` oracle from `_chunk_plan` rather than hardcoding it. These are
tight assertions.

---

## 3. Domain Assessment

**The revert is faithful and the surrounding correctness fixes survived it.** `prices.py:260-311` is a
single-hunk change restoring the unconditional whole-table `yield_per` scan; iter-41's `_SymbolColumns`
columnar accumulator and iter-42's B6 NULL sentinel are untouched, the `expected_symbols` zero-bar
bookkeeping loop (`:303-311`) is preserved, and the B1 `KeyError` publish-race lock barrier at
`:364-377`/`:422-427` is not in the diff at all — TC-2's regression test
(`test_lazy_load_is_published_atomically_to_a_concurrent_reader`, both parametrizations) passes in my
own independent 22/22 run. The docstring keeps the superseded iter-42 paragraph as historical record
and states the carried AG-8 disposition honestly ("a COMPRESSION of the whole-table load … not a BOUND
on row count"), which is the accurate carried state the DoD demanded and which the QA report's AG-8 row
also states correctly.

**The job-launch honesty fix is well-shaped domain work.** It routes a launch failure through the
*same* `prog.status = "failed"` + `_record_error` + `_finalize_run_record` mechanism `_run_job`'s own
outer handler uses rather than inventing a parallel failure vocabulary; `_finalize_run_record`'s
no-open-row INSERT fallback is the correct shape for `start_data_job` (whose `_create_run_record` at
`:4281` only ever runs on the thread that never started), and the resume sibling correctly rebuilds the
progress via the *shared* `_progress_from_checkpoint` so closing the paused attempt's open row does not
erase the work it had recorded. Both call sites re-raise unconditionally, so there is no path where a
failed launch is reported as success. After my B3 widening, both exits `Thread.start()` can take under
memory pressure reach that mechanism.

**AG-10 is strengthened, not weakened.** `host-guard.env`'s only change is the marker-list addition;
`HOST_GUARD_ENABLED=1`, `HOST_GUARD_CPU_LIST="0-15"`, `HOST_GUARD_BLAS_THREADS=8`,
`HOST_GUARD_MEMORY_HIGH="12G"` are byte-unchanged, `config.yaml` (`memory_cap_mb: 8192`) is not in the
diff at all, and `start-backend.sh`'s block is untouched. The new `start-frontend.sh` block is a
structural mirror placed *before* the build-if-stale section, so it also wraps `next build` — a
defensible strengthening beyond the literal ask, and correctly justified in-file.

**Where the domain is genuinely not healthy: J-07.** The memory axis is now unambiguously fine (VmPeak
flat at 2,720,636 kB = 32.4% of the raised cap across 1,001 s of continuous GIL-bound compute — a
longer soak than any prior measurement in the file). What replaced the memory problem is a *latency and
liveness* problem: a full-basis forward-aggregate warm that does not terminate in 28 minutes, degrades
`/api/health` from ~1.7 s to ~3.2 s means over its life, and — per the browser lane — can leave the
process unreachable for minutes. Two candidate causes are on record and **neither is confirmed**: T2's
broadened `_SymbolColumns` slicing cost, and a self-inflicted second concurrent dispatch during the
dev's own measurement window. The next iteration's first job is to isolate them (one trigger, no manual
mid-run probing), not to guess.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/data_manager.py` | B3 — `start_data_job`'s `thread.start()` guard widened from `except RuntimeError` to `except Exception` (always re-raised), so a `MemoryError` launch exit also reaches `_fail_unlaunched_job` |
| 2 | Important | `apps/backend/app/engine/data_manager.py` | B3 — same widening for `start_resume_job` → `_fail_unlaunched_resume` |
| 3 | Important | `apps/backend/app/api/data.py` | B3 — `start_job`/`resume_job` 503 mappings widened to `(RuntimeError, MemoryError)` so both launch exits return the honest 503, never a 500-shaped surprise |
| 4 | Important | `apps/backend/tests/test_data_manager.py` | B3 regression tests: `test_start_data_job_non_runtimeerror_launch_failure_also_marks_job_failed` (parametrized `RuntimeError`/`MemoryError`) and `test_start_resume_job_non_runtimeerror_launch_failure_also_marks_job_failed` |
| 5 | — | `docs/handoffs/goal-ops-hardening-iter-43-dev.md` | Amended the now-inaccurate "`try/except RuntimeError`" claim in Files Changed to record the audit widening |

**Post-fix verification (evidence, not assertion):**

- **Failure proved first.** `.venv/bin/python -m pytest tests/test_data_manager.py -k
  "non_runtimeerror_launch_failure" -q` against the **unfixed** tree → `2 failed, 1 passed` (the
  `RuntimeError` parametrization passed; both `MemoryError` cases failed —
  `TypeError: 'NoneType' object is not subscriptable` on `get_job(...)`, i.e. the job was never
  recorded at all).
- **Fix verified.** Same command shape post-fix:
  `pytest tests/test_data_manager.py -k "launch_failure or launch_oom" -q` → **6 passed** in 0.88 s
  (TC-3, TC-4, the prior pass's B1 preservation test, and the 3 new B3 cases).
- **No regression introduced.**
  `pytest tests/test_data_manager.py tests/test_api_data.py tests/test_data_manager_jobs_pipeline.py -q`
  → **219 passed** in 1203.40 s (baseline before my change, same command: **216 passed** in 1211.60 s —
  the delta is exactly the 3 new tests).
- **Independent re-verification of the iteration's own claims** (not accepted from the handoff):
  `pytest tests/test_bar_cache.py -q` → **22 passed** in 101.76 s, covering TC-1's byte-identity oracles
  and TC-2's publish-race regression test.
- **Diff reviewed for scope creep.** `git diff` on the two source files shows only the four `except`
  clauses and their comments; nothing else was touched.

---

## 5. Recommended Next Step

**Do not treat this iteration as closing J-07.** The five code deliverables (TC-1 through TC-5), the
induced-pressure drill (TC-9, clean: 31/31 health polls 200, 5,386 concurrent cached reads 0 non-200,
PID unchanged through the abort), the correctly-skipped conditional (TC-10), the six-journey regression
replay (TC-11, 6/6 PASS with dated screenshots) and J-05 (TC-6 — browser-QA UT-J-05 PASS: job 258
terminal `ok` in 325.4 s, `/scanner-runs/1882` instant from storage, `"Refreshed: … forward aggregates
…"`, badge `ready` throughout) are all genuinely done. **TC-7 and TC-8 are not**, and J-07 is failing on
two independent measurements.

The next iteration should target J-07 alone and, in this order:

1. **Isolate the latency regression cleanly** — one single trigger against the deep basis, no manual
   mid-run `/api/backtest` probing (the dev's own disclosed confound), so T2's contribution is
   attributable rather than hypothesised. This is the prerequisite; do not fix what has not been
   measured.
2. **Then either bound T2 directly** (an `_SymbolColumns`-aware windowed accessor for `bars_asof` that
   avoids reconstructing a full `Bar` per element) **or take the now-unfrozen warm seam** — but only
   against a measurement, and per the binding iter-42 lesson, measure the *whole job*, never the
   narrowed function.
3. **Separately, treat B2 (the unreachable-under-shutdown incident) as its own evidenced item** — the
   missing `--timeout-graceful-shutdown` on `start-backend.sh:95` is a concrete starting point, but the
   blocking in-flight task must be identified first; the daemon dispatch thread at
   `forward_testing.py:1691` is *not* it.

J-05 also carries one honest caveat worth carrying forward rather than losing: UT-J-05's PASS was
obtained against an **already-snapshotted** date (`already_snapshotted: 1`, the fast zero-new-snapshot
finalize path). It is valid evidence for "never recompute on the fly" but it is *not* evidence that the
genuinely-new-data heavy case now completes — the dev's own from-scratch attempt on an unsnapshotted
date never terminated within its observation window.

Finally: `apps/frontend/tsconfig.json` (F1) should be reverted before commit unless someone intends it.
