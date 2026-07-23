# goal-ops-hardening-iter-15 Dev Handoff

**Phase:** goal-ops-hardening-iter-15
**Date:** 2026-07-23
**Agent:** developer
**Status:** complete (backend fix + tests; ONE operator-supervised live pass still pending — see "Known Issues")

## What Was Built

- **Root-cause determination for UT-04's 211.8s finding — measured, not adopted as the first plausible
  story.** Three candidates were named for investigation (none prescribed): (a) no de-duplication in
  `forward_aggregates_cached`'s MISS path; (b) GIL/CPU contention between concurrent heavy Python
  aggregation loops (single-process `uvicorn`, no `--workers`); (c) WAL/session contention from the
  iter-14 streamed read holding its transaction open longer than the old `.all()` did.
  - Direct code read confirmed candidate (a): the pre-fix `forward_aggregates_cached` had NO lock,
    in-flight marker, or memoization on a cache MISS — it always called `compute_forward_aggregates`
    directly.
  - A throwaway, same-shape measurement (this host, host-guard-confined, 60,000-row `ScannerResult` +
    `ForwardReturn` fixture at one horizon) reproduced candidate (a)'s magnitude directly: **5 concurrent
    same-key MISSes invoked `compute_forward_aggregates` 5 times (not 1) and took 9.91x a single
    baseline call's wall-clock** (10.449s vs. 1.054s).
  - A SEPARATE, isolated measurement of candidate (c) alone (a single `compute_forward_aggregates` call,
    never routed through the wrapper — no redundant recomputation involved — timed with a background
    thread committing 3,220 writes to an unrelated symbol throughout) measured only **1.59x** (1.639s vs.
    1.031s) — well inside the 5.0x smoke-guard bound.
  - **Conclusion: candidate (a) is the confirmed dominant mechanism.** Candidate (b) GIL contention is
    real (the 5 concurrent copies above ran ~2x slower each, not just N-fold slower in aggregate) but is
    a SYMPTOM of (a)'s redundancy — removing the redundant copies removes the GIL contention between
    them. Candidate (c) is real but small in isolation and does not independently explain a 140x-scale
    overrun. Scaled to the real deep-basis tables (`forward_returns` 3,935,930+ rows, ~65x this
    fixture's size) and the "up to 10 redundant concurrent passes" shape the plan's call-site analysis
    names (the finalize warm's 5-horizon loop and `/api/backtest`'s own 5-horizon comprehension can both
    target the SAME keys at once), this fully accounts for a 211.8s finding. **[iter-15 audit
    reconciliation: the live TC-4 pass — see the "Operator-Supervised Live Reproduction — Results"
    section below — does NOT bear this out; post-fix cold MISS is 178.74s, only a 15.6% reduction, so
    candidate (a)'s stacking accounts for ~15.6% of the deep-basis finding, NOT its bulk. The dominant
    residual 178.74s is one cold full-basis compute the wrapper fix cannot reduce; whether a wrapper-only
    fix suffices for the ≤1.5s budget is the open evaluator/owner call (Known Issue #3). Same correction
    applied to reports/perf-budgets.md's root-cause conclusion.]**
  - **Decision: `app.db`'s session/WAL configuration is NOT touched this iteration** — the isolated
    measurement did not show an effect large enough to justify it.

- **The fix — an in-process single-flight de-dup in `forward_aggregates_cached`'s MISS path only**
  (`apps/backend/app/engine/forward_testing.py`), mirroring `data_manager.compute_coverage`'s established
  J-100 per-key-lock + in-flight-event idiom (no new concurrency abstraction invented):
  - The FIRST concurrent caller for a `(horizon, asof_key, dataset_version)` key becomes its owner and
    computes via `compute_forward_aggregates` (the SOLE producer, completely unchanged — same signature,
    same columns read, same streamed pattern from iter-14).
  - Every OTHER concurrent caller for that SAME key waits, bounded (45s, mirroring the existing test
    file's `BOUNDED_TIMEOUT_S`/the real `database.pragmas.busy_timeout_ms` reasoning), then re-reads the
    now-persisted `ForwardAggregateCache` row with its OWN session — never a second producer.
  - A failed or genuinely-wedged owner still releases its slot (`finally`, runs on success or exception)
    so a waiter falls through to an independent compute rather than blocking forever (TC-8).
  - Re-measured on the identical 60,000-row fixture, post-fix: **1 invocation (not 5), 1.098s (1.04x,
    not 9.91x)**.
  - All three existing call sites (`app/api/backtest.py:72`, `app/mcp/tools.py:205`,
    `data_manager.py:3230`) keep calling `forward_aggregates_cached` completely unchanged.

- **Test additions** in `apps/backend/tests/test_forward_testing_concurrency.py`, clearly banner-separated
  from iter-14's own `test_tc3_*`/`test_tc4_*` tests already in that file (named descriptively per the
  plan's naming-collision warning, never `test_tc1_`/`test_tc2_`):
  - `test_forward_aggregates_cached_dedups_concurrent_same_key_miss_to_one_compute` (TC-1): 5 concurrent
    callers for the SAME never-yet-cached key invoke `compute_forward_aggregates` exactly once
    (call-count instrumentation); all 5 payloads byte-identical.
  - `test_compute_forward_aggregates_concurrent_write_during_read_ratio_bounded` (TC-2): a dedicated,
    module-scoped 100,000-row fixture (sized for a comfortable ≥1.0s baseline margin — the existing
    60,000-row `memory_pressure_db` fixture clears the 1.0s bar but only by ~3-5%, a distinct empirical
    sizing task from that fixture's own memory-cap calibration) proves the ratio stays ≤5.0x (measured
    1.59x).
  - `test_forward_aggregates_cached_waiter_does_not_deadlock_when_owner_raises` (TC-8): a deterministic
    two-thread interleaving (owner claims the slot, waiter registers as non-owner, THEN the owner raises)
    proves the waiter never blocks past the bounded timeout — it falls through and independently
    recomputes a byte-identical payload. **Test validity independently verified:** the fix's own
    `event.set()` cleanup was temporarily disabled and this test re-run — it correctly FAILED (waiter
    thread did not finish), confirming the test is not vacuous; the fix was restored immediately after.

- **Re-confirmation of byte-identity (TC-3):** the existing 32-test suite in
  `test_forward_testing_aggregates_streaming.py` passes unmodified — no change was needed since
  `compute_forward_aggregates` itself is untouched.

- **`reports/perf-budgets.md` update:** transcribed the original 211.8s UT-04 finding (previously only
  documented in `reports/phase-goal-ops-hardening-iter-14-ux-regression.md:61,118-122`, never in this
  canonical artifact) into a new dated section, immediately followed by this iteration's root-cause
  measurements, the fix description, and a PENDING/operator-supervised placeholder for the live TC-4/5/6
  full-deep-basis reproduction with the exact 7-step protocol (mirrors the iter-14 PENDING→RESULTS
  pattern already used in this same file).

- **`runs/goal-session-ops-hardening/state/blueprint.md` update (light-touch, not a rewrite):** amended
  the pre-drafted iter-15 narrative paragraph and the `forward_aggregates` Data Contract row's iter-15
  sentence to reflect the actual (not merely planned) root cause, fix, and the still-open operator pass —
  explicitly marked "BUILT (developer pass), pending evaluator confirmation," never claiming
  evaluator-confirmed status that only a later evaluator pass can grant.

## Files Changed

- `apps/backend/app/engine/forward_testing.py` — added the single-flight de-dup (module-level
  `_FORWARD_AGG_LOCK` / `_FORWARD_AGG_INFLIGHT` / `_FORWARD_AGG_WAIT_TIMEOUT_S`) to
  `forward_aggregates_cached`'s MISS path only. `compute_forward_aggregates` is byte-identical/untouched.
- `apps/backend/tests/test_forward_testing_concurrency.py` — added TC-1/TC-2/TC-8 tests (a new dedicated
  `write_contention_engine` fixture for TC-2) plus a banner comment separating this iteration's tests from
  iter-14's own TC-3/TC-4 tests already in the file.
- `reports/perf-budgets.md` — transcribed the original 211.8s finding + this iteration's root-cause
  measurements/fix, plus a PENDING operator-supervised placeholder for the live TC-4/5/6 pass.
- `runs/goal-session-ops-hardening/state/blueprint.md` — updated the iter-15 narrative paragraph and the
  `forward_aggregates` Data Contract row's iter-15 sentence.

No file under `apps/frontend/` appears in this diff (Frontend Present: no, confirmed).

## Tests Run

Command: `cd apps/backend && taskset -c 0-3,8-11 env OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 .venv/bin/python -m pytest <file(s)> -v`
(host-guard-confined per this session's standing constraint; `TMPDIR`/`TMP`/`TEMP` exported per the
environment note)

| Suite | Result |
|---|---|
| `test_forward_testing_concurrency.py` (full file — 3 existing iter-14 + 3 new iter-15) | **6 passed**, 17.9s |
| `test_forward_testing_aggregates_streaming.py` (full file — TC-3, 32-test byte-identity suite) | **32 passed**, 4.9s |
| `test_forward_testing.py -k "forward_aggregates_cached"` (existing cache tests) | **3 passed**, 0.6s |
| `test_data_manager.py -k "test_finalize_hook"` (all 29 finalize-hook tests, the real ingest call site) | **29 passed**, 5.3s |
| **Total** | **70 passed, 0 failed, 0 skipped** |

**Not run — cited, not executed (`loaded_engine`-fixture files, per this session's standing constraint):**
`test_api_backtest.py`, `test_backtest_scorecard.py`, `test_mcp_window.py` all depend on the `loaded_engine`
fixture (full committed-seed load). These cover the `/api/backtest` endpoint and MCP `query_backtest` tool
end-to-end, but neither call site was touched by this change (both keep calling
`forward_aggregates_cached` exactly as before) — the function's own correctness (byte-identity + the new
concurrency behavior) is already comprehensively re-verified by the 70 tests above. An initial attempt to
run these three files together was killed after ~6 minutes on realizing mid-run that they carry the
`loaded_engine` fixture (confirmed via `grep` afterward) — this is exactly the class of file the plan
warned to "cite, don't run."

No full pytest suite was run. The pre-existing, unrelated `tests/test_db.py::test_create_all_produces_
expected_tables` failure is carried forward untouched (no schema change this iteration).

## Known Issues

1. **TC-4/TC-5/TC-6 (operator-supervised, full-deep-basis live reproduction) has NOT been performed this
   iteration.** ***RESOLVED 2026-07-23 — see the "Operator-Supervised Live Reproduction — Results
   (2026-07-23)" section appended at the end of this handoff, and
   `reports/perf-budgets.md`'s "TC-4 / TC-5 / TC-6 ... RESULTS" section, for the operator-supervised pass
   and this developer pass's independent verification of it. The paragraph below is left unedited as the
   historical record of what was pending and why.*** Services were down at dispatch time and this session's
   agents cannot start/stop them (subagent-resume broken). This is expected per the pump note ("I will boot
   them for the operator-supervised live reproduction later... Do NOT attempt it yourself") — not a gap in
   the developer pass. **Exact steps for the operator to run next** (also recorded in
   `reports/perf-budgets.md`'s new PENDING section):
   1. Confirm a cooled host (idle `Tctl`), the 1Hz host-guard hwmon sampler running, thermal watchdog
      armed.
   2. Start the backend via `scripts/start-backend.sh` ONLY — a FRESH restart is required (do not reuse
      the currently-running pre-fix process's numbers) — under host-guard confinement
      (`HOST_GUARD_CPU_LIST=0-3,8-11`, `HOST_GUARD_BLAS_THREADS=4`, `HOST_GUARD_REQUIRE_MARKERS=1`).
      Record the process-start timestamp and PID.
   3. Let the finalize warm trigger all 5 configured horizons; concurrently issue a live
      `GET /api/backtest` request for a not-yet-warmed horizon (the exact UT-04 trigger shape) — measure
      the resolving request's wall-clock via server-side timing. Record PASS if ≤1.5s, WARN with the
      measured number if not.
   4. Same pass: spot-check `/stocks`, `/sectors`, `/scanner-runs`, `/evidence` page loads (or their
      on-load endpoints) while the warm runs — record PASS/WARN per page; confirm none renders blank or
      frozen.
   5. Poll `GET /api/health` at 1Hz throughout; confirm every poll returns HTTP 200 within budget, no
      wedge.
   6. Cross-read `logs/backend.log` and `logs/hwmon/hwmon.csv` for the measurement window before
      attributing any remaining slowness to ambient load.
   7. Report console output, PIDs, and timestamps verbatim for attributed transcription into
      `reports/perf-budgets.md`'s PENDING section (which already has this same protocol written out).
2. **`loaded_engine`-fixture test files not re-run this pass** (see "Tests Run" above) — cited as
   unaffected, not executed, per this session's standing constraint on that fixture class.
3. **Escalation flag not triggered.** The spec asked me to name plainly if the investigation concluded the
   latency was "a hard architectural single-process/GIL limit that a targeted fix cannot meaningfully
   reduce." It is not: the measured evidence shows the redundant-recomputation defect (candidate a), not
   an inherent single-process ceiling, dominates — and a targeted, in-process fix (no process-model
   change) closes nearly all of the measured gap on the small fixture. Whether it closes the FULL 211.8s
   gap on the real deep basis is exactly what the pending operator-supervised TC-4 pass will confirm or
   refute.
4. Pre-existing, unrelated: `tests/test_db.py::test_create_all_produces_expected_tables` failure, carried
   forward untouched (no schema change this iteration).
5. **New observation, NOT fixed this iteration (out of scope — flagged for the reviewer/auditor to
   triage):** while confirming the root cause, I checked whether this same "no de-duplication on a
   concurrent same-key MISS" shape exists in `forward_aggregates_cached`'s sibling ingest-time caches —
   `research.event_study_cached`, `market_phase.market_phase_cached`,
   `forward_testing.compute_drawdown_expectations_cached`, and
   `indexes.index_series_cached_with_status`. None of these four have any lock/in-flight mechanism either
   (confirmed by `grep` — no `threading`/`_LOCK`/`INFLIGHT` reference in any of their modules), so the
   SAME theoretical redundant-recompute pattern could in principle affect them too, under a concurrent
   same-key MISS. This iteration's plan scoped the fix explicitly to `forward_aggregates_cached` only (the
   confirmed, measured UT-04 culprit) — I have NOT touched, tested, or measured any of the other four, and
   do not know whether any of them has ever produced a comparable live symptom. Recording this here per
   instruction, not fixing it — a decision on whether to investigate/fix the others is a scope call for a
   future iteration, not this one's to make.

## Operator-Supervised Live Reproduction — Results (2026-07-23)

**This section resolves Known Issue #1 above.** The operator ran the TC-4/TC-5/TC-6 protocol against a
fresh post-fix boot (`start-backend.sh`, pid 4166118, launched 15:41:03 BST) and reported the results for
attributed transcription. This developer-continuation turn did the following ONLY — no code was changed,
no service was started/stopped (pid 4166118 was already up and stays up for the browser lane), the repro
was NOT re-run, and no full pytest suite was run:

1. Read the operator's report and the three raw CSVs it cited
   (`runs/goal-ops-hardening-iter-15/tc4-backtest-timings.csv`, `tc456-health.csv`, `tc456-vm-samples.csv`).
2. Recomputed every derived statistic (counts, min/max/median, the `VmPeak` margin, the health non-200
   epochs) directly from those CSVs rather than accepting the operator's arithmetic on trust, and
   cross-read `logs/backend.log` and `logs/hwmon/hwmon.csv` for the same window, per the protocol's own
   step 6.
3. Transcribed the results into `reports/perf-budgets.md`'s new "TC-4 / TC-5 / TC-6 ... RESULTS" section
   (resolving that file's PENDING placeholder), with the operator's figures attributed and this pass's
   recomputation marked explicitly wherever it confirms or diverges from them.
4. Updated `runs/goal-ops-hardening-iter-15/status.json`.

**Headline results (full detail and tables in `reports/perf-budgets.md`):**

- The core fix claim holds on the deep basis: the single-flight dedup prevents the *stacking* pathology
  iter-14 measured — every one of the 64 polled `/api/backtest` calls resolved independently, none hung,
  and the fix's own targeted tests (70/70, prior developer turn) are unaffected by this pass.
- TC-4 (cache-miss latency, budget ≤1.5 s): **WARN**, confirmed exactly — one cold MISS on the new dataset
  version took 178.743092 s (~119x over budget), matching the operator's figure precisely. This is the
  expected cost of one genuinely cold full-basis compute; it is not the stacking defect the fix targets.
- TC-4, second finding (this pass's own recomputation, NOT in the operator's report): a **second** call,
  5.373490 s at epoch 1784818231, also breaches the same ≤1.5 s budget (~3.6x over) and was not mentioned
  in the operator's "0.24-0.67 s for everything else" summary. Cause undetermined (candidates: a later
  in-job dataset-version bump, or transient contention) — recorded as a second WARN point, not diagnosed
  here.
- TC-5 (page spot-checks): operator's figures transcribed with attribution (not independently recomputable
  — no raw CSV was captured for these ad hoc checks). The `/api/scanner-runs` 404 the operator flagged as a
  guessed path is confirmed genuinely a wrong path (no such backend route exists); the frontend's
  `/scanner-runs` page actually calls `GET /api/runs` / `GET /api/runs/{run_id}` (`apps/backend/app/api/
  runs.py`) — not a page defect.
- TC-6 (health-poll liveness): **materially PASS**, every figure recomputed exactly matches the operator's
  report (498/500 HTTP 200, median 0.168 s, max 3.573 s, both non-200 epochs identical).
- Memory: **PASS**, `VmPeak` peak and 36.3% margin recomputed exactly matching; live-re-confirmed against
  pid 4166118's current `/proc/.../status` at recomputation time (still 4,005,376 kB, i.e. unchanged since
  the CSV's own peak — the process has not restarted). The operator's cited backend-console-log path
  (`/tmp/trendora-be15-tc4.log`) is empty (0 bytes) and does not itself support the "zero MemoryError"
  claim, but the claim is independently confirmed true via `logs/backend.log`'s actual current-boot window.
- **Thermal discrepancy, flagged and NOT self-resolved:** the operator reported "Tctl 42 °C idle band...
  peaked 64 °C during the run." `logs/hwmon/hwmon.csv` for the exact matching window instead shows a
  **peak of 84 °C**, with 94.7% of samples (620/655) above 64 °C for most of the ~11-minute run, cooling
  toward the 48-54 °C range only in the final ~15-20 s. No abort threshold was breached (84 °C stays under
  the 95 °C trip; NVMe/DIMM both well under their own limits), so "no trip" is independently confirmed —
  but the reported peak itself does not match the sampler. Given this project's documented thermal/memory
  host-crash history, this is recorded as a priority open item for the evaluator/operator to reconcile,
  not smoothed over.

**Known Issues carried forward / newly added by this pass:**

- The two items above (the unflagged 5.37 s TC-4 spike, and the Tctl discrepancy) are new observations
  from this transcription pass, not fixed or explained here — they are handed to the evaluator per this
  agent's fix-mode discipline (report, don't silently resolve problems outside the current task's scope).
  Also recorded as their own line in `runs/goal-ops-hardening-iter-15/status.json`'s `notes`.
- The "2.00 s" boot-to-first-health-200 figure and the job's exact wall-clock launch/terminal timestamps
  are not independently reproducible from the raw evidence provided to this pass (see `reports/
  perf-budgets.md` for the specific gaps) — transcribed with attribution, not silently upgraded to
  "confirmed."
- All previously-listed Known Issues (2-5 above) are unchanged and still open.
