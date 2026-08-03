# goal-ops-hardening-iter-44 Dev Handoff

**Phase:** goal-ops-hardening-iter-44
**Date:** 2026-08-03 (revised same day by the developer fix pass, after the audit's FAIL verdict)
**Agent:** developer
**Status:** complete — **but the phase GOAL was NOT achieved.** TC-2, TC-5 and TC-7 are not met and TC-4
was disclosed rather than fixed; see "Fix Notes" and "Known Issues". Several claims in the original
handoff were refuted by this pipeline's own browser lane and have been corrected in place rather than
left standing with an appended note.

## What Was Built

- **`ServerOpsCfg` launcher-flag wiring (TC-1)** — `incredible_auto_dev/scripts/start-backend.sh` (=
  `scripts/start-backend.sh`) now passes `--limit-concurrency` / `--timeout-keep-alive` /
  `--timeout-graceful-shutdown` to uvicorn, read from `get_config().server` via the same inline
  venv-python pattern the existing `memory_cap_mb`/`malloc_arena_max` block uses. No magic numbers.
  Verified live against the real launched process's `/proc/<pid>/cmdline`.
- **Live SIGUSR1 diagnosis of J-07's `horizons_done: 0/5` stall (TC-3)** — reproduced live twice (two
  corroborating all-thread dumps, ~888s apart) via `scripts/start-backend.sh` with
  `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1=1`. Named, with full stack traces, both blocking call chains:
  (a) the ingest job's own finalize-tail thread stuck in `_excluded_counts_by_date`'s documented
  **O(dates × pool)** `resolve_with_reasons` loop (`data_manager.py`), triggered by
  `membership_timeline_cache`'s all-or-nothing `dataset_version` invalidation forcing a full
  ~2,860-date recompute on every ingest; (b) the request-triggered historical forward-aggregate
  dispatch stuck in `compute_forward_aggregates`'s bounded-slice streaming read. The second dump also
  live-confirms, for the first time, that T2 (`_SymbolColumns.__getitem__`/`bars_asof`'s previously
  hypothesized 70-80× slicing cost) is a real contributor — inside `resolve_with_reasons`'s bar
  lookups, not directly in the forward-aggregate loop as earlier iterations guessed.
- **TC-4 disposition: honestly disclosed as unresolved, not fixed.** Both candidate fixes (an
  incremental membership-timeline cache redesign; a sixth `_SymbolColumns`/`bars_asof` bound attempt)
  are materially larger, unevidenced work — the latter has 5 prior attempts in this session, the most
  recent a measured +5.1% regression that was reverted. See `reports/perf-budgets.md` iteration-44 §2
  for the full named finding and next-iteration candidates.
- **TC-2 — NOT CLOSED (refuted on this same build; corrected 2026-08-03 after audit B3).** On both drill
  runs, with background threads still actively (non-deadlocked) blocked mid-computation, `kill -TERM`
  exited the live process cleanly in 6s (then 5s on a second instance), inside the 120s
  `graceful_timeout_seconds`, no `kill -9` needed — and a new opt-in subprocess test
  (`test_start_backend_self_terminates_on_sigterm_with_stuck_background_task`) reproduces that
  deterministically. **But that is only the schedulable-process case.** Later the same day, on this
  identical build, the browser lane sent `SIGTERM` at 20:26:13 UTC, the process was still alive at
  20:31:12 (4m59s, past the configured 120s), and `SIGKILL` was required at 20:31:37 UTC.
  `logs/backend.log` carries **no shutdown output at all** for that process — uvicorn's signal handling
  never ran. `--timeout-graceful-shutdown` is enforced by the asyncio event loop; when the loop itself is
  wedged (all 19 threads `S`, cumulative CPU not advancing), the flag can never fire. See "Known Issues".
- **TC-5 — NOT MET; TC-6 — PASS; TC-7 — NOT CLOSED (refuted on this same build).** A fresh backend, ONE
  backfill trigger, no manual mid-run probing:
  - **TC-5 (≤2s BCW health budget): NOT MET.** 224/240 polls (93.3%) were within budget;
    **16/240 (6.7%) exceeded 2 s**, `max_latency=2.354s`
    (`runs/goal-ops-hardening-iter-44/j07-warm/clean-remeasure-summary.json`, `over_2s_budget: 16`). This
    is a large improvement over the confounded diagnostic run's 70.9% and the best number this session has
    produced — but TC-5's criterion is *every* poll, so it is a miss. (Corrected after audit B4: the
    original handoff called this a "WARN" and the QA report rendered it as "constraints held" with a ✓.)
  - **TC-6 (concurrent cached `GET /api/backtest`): PASS** — 200 in 162 ms, served from storage.
  - **TC-7 (never fully unreachable): NOT CLOSED.** On this run `GET /api/health` never returned non-200
    across 240 polls. On the SAME build later the same day the browser lane recorded **51 consecutive
    timed-out `/api/health` polls over 20m51s** (20:10:33 → 20:31:24 UTC), two independent pollers plus
    `curl --max-time 4` returning `http_code=000` — the iter-43 total-outage failure mode recurred, and
    lasted longer than the incident it was written to close. See "Known Issues".
- **`POST /data/jobs/{run_id}/retry` 503 parity (TC-9)** — wraps `data_manager.retry_run(...)` in the
  same `(RuntimeError, MemoryError)` → `HTTPException(503, ...)` handling `start_job`/`resume_job`
  already carry, so all three job-launch endpoints share one honest-error contract.
- **`_run_job` failed-job message honesty (TC-10)** — the `finally` block no longer unconditionally
  overwrites `prog.message` with `_final_summary`'s generic "work done" text for a `failed` job; the
  outer exception handler now also sets `prog.message` to the real captured exception text, and the
  `finally` block only falls back to `_final_summary` when `prog.status != "failed"`. A normally
  completed job's `_final_summary` text is unchanged. This is also what makes the iter-43 audit's
  `_run_detail` B2 fix (previously a no-op per its own B5 finding) actually diverge now.
  **As first shipped this was still a no-op for `MemoryError`** — `str(MemoryError())` is the empty
  string, and an empty `prog.message` is falsy, so `_run_detail`'s truthiness guard fell straight back to
  `_final_summary`'s generic text (exactly what the live failed run 272 persisted). Closed during the
  audit (B1/T1) with a type-name fallback,
  `reason = scrub(str(exc)) or f"{type(exc).__name__} (no message)"`, plus a regression test that pins the
  textless case. Text-carrying exceptions are byte-identical to before.
- **`apps/frontend/tsconfig.json` (TC-11)** — confirmed clean against `git diff HEAD`; the iter-43 F1
  stray `include`-array reordering is not present. No frontend work was done this iteration (no
  product-facing frontend change; `Frontend Present: no` per the plan).

## Files Changed

- `incredible_auto_dev/scripts/start-backend.sh` (= `scripts/start-backend.sh`, symlinked) -- added
  `--limit-concurrency` / `--timeout-keep-alive` / `--timeout-graceful-shutdown` to the uvicorn `exec`
  line, sourced from `get_config().server`.
- `apps/backend/app/api/data.py` -- `retry_job`: wrapped `data_manager.retry_run(...)` in
  `try/except (RuntimeError, MemoryError)` → `HTTPException(503, ...)`.
- `apps/backend/app/engine/data_manager.py` -- `_run_job`: the outer `except Exception as exc:` block
  now also sets `prog.message = scrub(str(exc))`; the `finally` block's `prog.message =
  _final_summary(prog)` assignment is now conditional on `prog.status != "failed"`.
- `apps/backend/tests/test_start_backend_script.py` -- new
  `test_start_backend_wires_server_ops_cfg_flags_into_uvicorn_cmdline` (TC-1, fast, always-on); new
  `spawned_backend_fast_graceful_timeout` fixture + new
  `test_start_backend_self_terminates_on_sigterm_with_stuck_background_task` (TC-2, opt-in via
  `TRENDORA_RUN_HEAVY_INGEST_TEST=1`, mirrors the existing heavy-ingest fixture's gating).
- `apps/backend/tests/test_api_data.py` -- new `test_retry_thread_launch_failure_is_503` (TC-9,
  parametrized over `RuntimeError`/`MemoryError`).
- `apps/backend/tests/test_data_manager.py` -- new
  `test_run_job_outer_exception_preserves_real_message_not_final_summary` and
  `test_run_job_normal_completion_still_gets_final_summary` (TC-10).
- `reports/perf-budgets.md` -- new "Iteration 44" dated section: the launcher-flag confirmation, both
  verbatim SIGUSR1 dumps with the named blocking call chains, the TC-4 disposition rationale, the clean
  re-measurement's TC-5/TC-6/TC-7 table, the TC-8 regression confirmation (with the pre-existing-flake
  finding for `test_ingest_finalize_memory_pressure.py`), and next-iteration candidates for the
  evaluator.
- `apps/frontend/tsconfig.json` -- verified clean, no change made.

## Live Drill Artifacts (not committed test code — evidence only)

- `runs/goal-ops-hardening-iter-44/j07-warm/drill.py`, `drill-stdout.log`, `drill-samples.csv` (partial)
  -- the combined J-05/J-07 diagnostic drill (SIGUSR1 dumps, both signals polled).
- `runs/goal-ops-hardening-iter-44/j07-warm/clean-remeasure.py`,
  `clean-remeasure-stdout.log`, `clean-remeasure-summary.json`,
  `clean-concurrent-backtest-response.json` -- the clean, single-trigger TC-5/TC-6/TC-7 re-measurement.
- `runs/goal-ops-hardening-iter-44/j07-warm/monitor.py` -- the standalone `background_compute`-only
  monitor (superseded by `drill.py`'s combined version; kept for reference).
- `runs/goal-ops-hardening-iter-44/j07-warm/availability.json`,
  `scanner-runs-before.json`, `availability-clean.json` -- the unsnapshotted-date confirmations for
  both live triggers (`2019-02-28`, `2019-02-27`).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -q`
Result: 152 passed (369.8s)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_api_data.py -q`
Result: 50 passed (6.2s)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_start_backend_script.py -v`
Result: 9 passed, 2 skipped (heavy, opt-in) (58.0s)

Command: `cd apps/backend && TRENDORA_RUN_HEAVY_INGEST_TEST=1 .venv/bin/python -m pytest tests/test_start_backend_script.py -k test_start_backend_self_terminates_on_sigterm_with_stuck_background_task -v -s`
Result: 1 passed (22.0s) -- SIGTERM-to-exit measured at 0.40s against an 8s configured timeout

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_bar_cache.py -q`
Result: 22 passed (91.1s)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_ingest_finalize_fault_injection.py -v`
Result: 5 passed (0.65s) -- TC-8 regression, deterministic mechanism, PASS

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_ingest_finalize_memory_pressure.py -v`
Result at handoff: 1 passed, 1 FAILED -- originally (and wrongly) attributed to fixture calibration drift.

> **AUDIT CORRECTION (iter-44 auditor, 2026-08-03):** this failure was NOT fixture calibration drift.
> It was two real product defects in the memory-pressure isolation handlers (audit finding B2), both
> fixed during the audit with the captured escape tracebacks as evidence. The file now reports
> **2 passed in 170.76s**. See `docs/handoffs/goal-ops-hardening-iter-44-audit.md` §2/§4.

### Re-verification after the audit fixes (developer fix pass, 2026-08-03)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_api_data.py
tests/test_ingest_finalize_memory_pressure.py tests/test_ingest_finalize_fault_injection.py -q`
Result: **57 passed in 159.02s** -- the memory-pressure file is now **2/2** (was 1 failed, 1 passed at
handoff), confirming audit B2's two fixes hold; TC-9's Retry-503 parity and TC-8's 5 fault-injection
cases still pass.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -q -k "run_job or
final_summary"`
Result: **3 passed, 150 deselected in 0.67s** -- includes the audit's new
`test_run_job_textless_exception_still_names_a_real_reason` (B1/T1), which pins the textless-`MemoryError`
case the original TC-10 test could not reach.

Live drills (not pytest -- real launched processes, `runs/goal-ops-hardening-iter-44/j07-warm/`):
diagnostic drill (~1,058s, two SIGUSR1 dumps, one SIGTERM-to-clean-exit in 6s) and clean re-measurement
(~601s, one SIGTERM-to-clean-exit in 5s) -- see `reports/perf-budgets.md` iteration-44 for full results.

> **AUDIT CORRECTION (iter-44 auditor, 2026-08-03) — the TC-2 and TC-5/TC-6/TC-7 bullets above are
> refuted by this pipeline's own later browser lane.** Both claims are true of the runs they measured
> and false as general statements. During `reports/phase-goal-ops-hardening-iter-44-ui-test-results.llm.md`'s
> run the backend went fully unresponsive for **20m51s** (51 consecutive timed-out `/api/health` polls,
> two independent pollers, `curl` `http_code=000`) — TC-7 recurred, worse than iter-43 — and a `SIGTERM`
> at 20:26:13 UTC did NOT exit the process within its configured 120s window; `SIGKILL` was required at
> 20:31:37 UTC (TC-2 refuted). `logs/backend.log` carries **no shutdown output at all** for that process.
> See audit finding B3.

## Known Issues

- **J-07's `horizons_done: 0/5` stall is diagnosed but NOT fixed.** The root cause
  (`_excluded_counts_by_date`'s O(dates × pool) full-history recompute, forced by
  `membership_timeline_cache`'s coarse invalidation) is named with two live, corroborating stack dumps.
  A genuine fix needs either an incremental membership-timeline caching redesign or another
  `_SymbolColumns`/`bars_asof` bound attempt — both judged materially larger than this iteration's
  "smallest correct fix" scope, and the latter has a session history of 5 prior attempts (most recent a
  measured regression). Recorded as next-iteration candidates in `reports/perf-budgets.md`.
  ~~Availability (the actual J-07 promise) held throughout every live observation this iteration made.~~
  **That last sentence was wrong as a general claim and is withdrawn** — it generalized from the two drill
  runs. See the two entries immediately below.
- **CRITICAL, UNFIXED — the service DID go fully unreachable on this build (audit B3): a 20m51s total
  outage requiring `SIGKILL`.** This is the phase GOAL's first clause and it is not met. TC-2 and TC-7
  are both refuted by this pipeline's own browser lane
  (`reports/phase-goal-ops-hardening-iter-44-ui-test-results.llm.md`): 51 consecutive timed-out
  `/api/health` polls 20:10:33→20:31:24 UTC, `SIGTERM` at 20:26:13 not honored within the configured 120 s
  window, `SIGKILL` at 20:31:37. **Mechanism (verified independently, not taken from the tester's
  report):** `logs/backend.log` has no shutdown output whatsoever for that process — its last line is a
  caught `MemoryError` in `evidence.py` at 20:13:56 UTC and the next is the following launch banner.
  uvicorn's signal handling never ran, because `--timeout-graceful-shutdown` is enforced by the asyncio
  event loop and the loop itself was wedged (all 19 threads `S`, cumulative CPU not advancing, internal
  logging stopped). **Deliberately NOT fixed in this pass**, per the audit's own disposition: the two
  candidate root-cause fixes are the ones this iteration's spec defers (incremental membership-timeline
  redesign; a sixth `_SymbolColumns`/`bars_asof` bound attempt, whose fifth attempt measured a +5.1%
  regression), and no in-process watchdog can escape a wedge in which no Python thread advances. The
  evidenced next step is an **out-of-process** supervisor deadline (systemd-style `TimeoutStopSec`, or the
  launcher backgrounding uvicorn and owning its own SIGKILL escalation) — a NEW mechanism that must be
  specified as such rather than smuggled into this iteration as a "wiring" change.
- **TC-5's threshold was not met (audit B4), and was originally reported as if it were.** 16 of 240 polls
  (6.7%) exceeded the ≤2 s bounded-compute-window budget, `max_latency_s: 2.354`
  (`runs/goal-ops-hardening-iter-44/j07-warm/clean-remeasure-summary.json`). The measurement itself is a
  real improvement (70.9% → 6.7%) and is not in dispute; what was wrong was reporting a hard-threshold DoD
  checkbox as met when its own artifact says otherwise. Corrected in this handoff and in
  `reports/perf-budgets.md` §3.
- **`test_ingest_finalize_memory_pressure.py::test_tight_cap_aborts_forward_aggregates_with_caught_memory_error_and_recovers`**
  — RESOLVED during the audit; **the file now passes 2/2** (re-verified in this fix pass, 57 passed
  in 159.02s alongside `test_api_data.py` and `test_ingest_finalize_fault_injection.py`). The original
  handoff's diagnosis below was **wrong** and is retained only for the record.
  ~~A pre-existing test-fixture calibration drift (`TIGHT_CAP_KB=750,000`, set at iter-34) that this
  iteration's own live diagnostic explains: `_membership_timeline`'s unbounded `.all()` membership read
  now also competes for the same tight cap the test originally aimed only at the forward-aggregates loop.
  Not this iteration's evidenced scope to fix.~~ `TIGHT_CAP_KB` needs **no** recalibration; if this test
  becomes flaky again, treat it as a new escape to trace, not a number to tune.

  > **AUDIT CORRECTION (iter-44 auditor):** this diagnosis was wrong, and the DoD item it was filed
  > under (TC-8, "the existing induced-pressure abort still holds") was therefore NOT met at handoff.
  > The cap was not miscalibrated: `_refresh_ingest_aggregates` genuinely violated its documented
  > "log + continue, never raise" contract at two sites, each captured verbatim from the child probe's
  > stderr — (1) `_resolve_libc_malloc_trim`'s `except (OSError, AttributeError)` did not catch
  > `MemoryError`, so `_release_process_memory()` — called from INSIDE the per-horizon `except
  > MemoryError` abort handler — re-raised out of the handler (`ctypes/util.py:297 in
  > _findSoname_ldconfig`); and (2) the deferred `from app.engine import indexes` sat one line ABOVE
  > its `try`, so importing the not-yet-loaded module under an exhausted cap escaped the function
  > entirely (`<frozen importlib._bootstrap_external>:1191 in get_data`). Both fixed in the audit;
  > the file now passes 2/2. Note this is the SAME binding iter-43 lesson this iteration cites twice
  > ("key the guard to the whole exception set the incident produces") applied to the abort handlers
  > themselves.
- **The clean re-measurement's backfill job (`2019-02-27`) was left in an honest in-flight state**
  (status `running`, snapshot created, finalize tail still active) when its host process was
  deliberately SIGTERM'd at the end of the observation window — matching TC-12's option (b) ("if it does
  not terminate within a bounded observation window, the run's honest in-flight state is captured and
  reported"), not a fabricated success. The prior boot's orphan-sweep (`sweep_orphaned_runs`, unmodified
  this iteration) will mark this row `interrupted` on the next real restart, consistent with J-04's
  established restart-resilience contract (exercised and confirmed in iter-43).
- **No browser/QA regression replay was run by this developer pass** (J-01/J-03/J-04/J-06/J-08/J-09,
  TC-13) — that is the browser-qa lane's own step per this iteration's TESTING REQUIREMENTS. The
  backend-level evidence above (J-09's `background_compute.active` disclosure exercised live twice this
  iteration; J-08's storage-serving contract exercised live via the TC-6 concurrent cached read) is
  offered as supporting, not substituting, evidence.
- **Frontend:** no frontend work this iteration (`Frontend Present: no`); `apps/frontend/tsconfig.json`
  confirmed unchanged from `git diff HEAD` (TC-11; independently re-verified by the auditor — the diff is
  genuinely empty, not merely asserted).
- **Observation, not fixed (audit B5): `--limit-concurrency 64` adds a path where `/api/health` can return
  503 rather than a slow 200.** This is exactly what `ServerOpsCfg`'s docstring specifies, so it is by
  design, and there is no evidence of it firing this iteration (the incident produced timeouts, not 503s).
  Recorded only because J-07's acceptance is worded as "returns 200 throughout": a future connection
  pile-up above 64 would fail that clause by design rather than by starvation. Related and also
  pre-existing: `start-backend.sh`'s `read` gives no diagnostic if the venv-python config read fails — all
  five variables would be empty and `ulimit -v $((MEMORY_CAP_MB * 1024))` would evaluate to `ulimit -v 0`.
  This iteration extended that pattern rather than introducing it; left unchanged here as out of the
  audit's fix scope.
- **Observation, not fixed (audit T2): TC-2's automated test cannot fail the way production failed.**
  `test_start_backend_self_terminates_on_sigterm_with_stuck_background_task` triggers a backfill, sleeps
  2.0 s, asserts `status == "running"`, then SIGTERMs. A 2-second-old job on a throwaway DB has a live
  event loop, so the test measures uvicorn's normal graceful path (0.40 s against an 8 s budget) — not the
  wedged-loop condition that produced the incident. It is a valid TC-1-wiring regression test; it is not
  evidence for TC-2's DoD claim. A test that reproduces a genuine wedge is new, unevidenced work and was
  not attempted.
- **Observation (audit T3): the QA report's verdict is stale and will mislead a reader.**
  `reports/qa/goal-ops-hardening-iter-44-qa.md` (written 20:52, verdict PASS) states "Browser QA:
  **SKIPPED** — no UI changes shipped this iteration", while this iteration's TESTING REQUIREMENTS mandate
  browser tests for J-05, J-07 and six regression journeys. The browser lane then ran at 21:37 and returned
  **FAIL**. Anything keying off QA's PASS without reading
  `reports/phase-goal-ops-hardening-iter-44-ui-test-results.llm.md` will draw the wrong conclusion. The QA
  report is QA's own artifact and was not edited by this pass.

## Fix Notes (fix pass, 2026-08-03 — after audit FAIL)

**Inputs read:** `docs/handoffs/goal-ops-hardening-iter-44-audit.md` (FAIL), the phase spec, the execution
plan, `reports/qa/goal-ops-hardening-iter-44-qa.md`, and
`reports/phase-goal-ops-hardening-iter-44-ui-test-results.llm.md`.

**Product-code changes in this pass: none.** The audit's three code fixes (B1, B2 ×2) and its new
regression test (T1) were applied during the audit itself; I verified all four are present in the working
tree and re-ran their tests rather than re-implementing them. Every remaining audit finding was either
explicitly out of this iteration's evidenced reach (B3), an accuracy defect in the record rather than in
the code (B4), or an observation the audit marked not-to-fix here (B5, T2, T3). Per fix-mode discipline I
touched only what the audit listed, and did not attempt the out-of-process shutdown deadline the audit
names as the real TC-2 fix — it is a new mechanism and the audit explicitly says it must be specified as
such, not smuggled in here.

| Audit finding | Disposition in this pass |
|---|---|
| B1 — TC-10 message honesty was a no-op for `MemoryError` | Verified fixed in tree (`reason = scrub(str(exc)) or f"{type(exc).__name__} (no message)"`, used for both `_record_error` and `prog.message`); re-ran its tests. Recorded in the handoff body and `perf-budgets.md` §5 so the record no longer claims TC-10 worked from the start. |
| B2 — `_refresh_ingest_aggregates` broke its "never raise" contract at two sites | Verified both fixes in tree (`_resolve_libc_malloc_trim`'s uncached `except MemoryError: return None`; the deferred `indexes` import moved inside its `try`); re-ran the memory-pressure file, **2/2 passing**. Replaced the wrong "fixture calibration drift" diagnosis in the handoff and `perf-budgets.md` §4. |
| B3 — TC-2/TC-7 refuted; 20m51s outage, `SIGKILL` required | **Not fixed** (correct per the audit). Recorded as a CRITICAL unfixed Known Issue with the verified mechanism and the named next step (out-of-process supervisor deadline). Struck the refuted claims from the handoff body and `perf-budgets.md` §2/§3, including the wrong parenthetical that "the launcher flag alone — TC-1 — is sufficient to close the 'held hostage' failure mode". |
| B4 — TC-5 reported as met when its own artifact says otherwise | **Fixed in the record.** TC-5 now reads **NOT MET** (16/240 polls over budget, max 2.354 s) in both the handoff and `perf-budgets.md` §3, with the artifact cited inline. |
| B5, T2, T3 — observations | Recorded above verbatim in substance; no code changed, per the audit's own scoping. |
| Withdrawn recommendation | The "`TIGHT_CAP_KB=750,000` needs recalibration" item is struck from `perf-budgets.md`'s evaluator bullets — with B2's two real escapes fixed the fixture passes at the existing cap. |

**Re-verification run in this pass** (`TMPDIR` isolated per the dispatch; no full-suite run — ~10 h on
this basis):

```
pytest tests/test_api_data.py tests/test_ingest_finalize_memory_pressure.py \
       tests/test_ingest_finalize_fault_injection.py -q      → 57 passed in 159.02s
pytest tests/test_data_manager.py -q -k "run_job or final_summary" → 3 passed, 150 deselected in 0.67s
```

The memory-pressure file passing 2/2 is the load-bearing result: it was 1 failed / 1 passed at handoff.

**Honest status of the phase after this pass:** the mechanical half (TC-1, TC-3, TC-9, TC-10, TC-11,
TC-12, TC-13) is done and verified, and the audit's three defect fixes make the system materially stronger.
**TC-2, TC-5 and TC-7 are not met**, and TC-4 was disclosed (option b) rather than fixed. The phase GOAL's
first clause — "stop J-07's heavy warm from taking the whole service unreachable" — was **not achieved**,
and the record now says so everywhere instead of in appended corrections only.
