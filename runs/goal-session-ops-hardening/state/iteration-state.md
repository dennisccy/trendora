# Iteration State — ops-hardening

**After iteration:** 40 · **Date:** 2026-07-31 · **Verdict:** ESCALATE

## Journeys

3 passing (J-03 J-08 J-09 — carried on durability, NOT re-verified) · 1 partial (J-07, 6th straight) · 4 unknown (J-01 J-04 J-05 J-06 — **never tested this run**; nothing found broken, but their data path changed) · 0 failing — 8 total. Ledger: 37 findings, **13 unresolved, 0 critical** (iter-39/v /w /x RESOLVED; new iter-40/y).

## Active blockers

- **dev, TOP PRIORITY (iter-40/y) — the verification lane is OFF.** Zero screenshots, zero replay artifact, zero demo steps; DoD item 8 / TC-9 never executed; review, QA and closure all reported clean anyway. TWO causes, both one-line fixes: (1) the browser-QA precondition probes `http://localhost:8255/health`, but `apps/backend/main.py:127` mounts the health router under prefix `/api` — a **404 from a LIVE server** was read as "backend down" (`logs/backend.log` shows that 404 interleaved with `GET /api/health 200 OK`); (2) `reports/phase-*-iter-40-ui-test-plan.md` turned the spec's `Frontend Present: no` into "N/A — no UI tests required", waiving the required-still-passing replay the same spec demanded. `Frontend Present: no` must suppress NEW-surface tests only; an all-`SKIP` regression run must read as an unmet DoD item. **All 7 need a fresh screenshot before any achievement attempt.**
- **dev, iter-39/u — the J-07 blocker: a frozen process, thread still unidentified.** Wedge-drill run 1 froze at 2650 MB (14 threads in `futex_do_wait`, uncaught `MemoryError`, no traceback) — `runs/goal-ops-hardening-iter-40/wedge-drill/run1-notes.md`. `gdb` refused by `kernel.yama.ptrace_scope`, `py-spy` not installed. **Agent path that needs neither:** `faulthandler.register(signal.SIGUSR1, all_threads=True)` in the drill launch — in-process stack dump, no new dependency. Do NOT tune the cap again.
- **dev, iter-29/d — the LAST unbounded whole-table load.** `apps/backend/app/engine/prices.py:132-142` (`_BarCache.prefill`): `.yield_per(batch)` bounds the CURSOR, but every row still lands in one `by_symbol` dict (~1.1 GB). docs/goal.md Success Criteria forbid it verbatim; it is one of the two consumers in the run that froze.
- **dev, audit B2:** `wedge-drill/monitor.py:96-99` stops polling the instant `job_status` is terminal — but iter-39's wedge appeared AFTER the row read `ok`, so all 28 clean polls land before the window that previously failed. Poll a fixed interval PAST terminal status.
- **dev, small + written down:** count-based floor for the checkpoint density (still time-based only); add `BLOCKED` to `verdicts.py::BrowserQAVerdict` + the four `grep -oE 'PASS|FAIL|SKIPPED'` sites in `goal-iter-lean.sh` (audit T3 — traced fail-safe, hygiene only).
- **dev, deferred a 5th time (iter-33/g):** Regime Lab cold `view=pooled` background dispatch. **Carried, untouched:** iter-29/b + `warmup.py:194` (10 iterations unmade); iter-31/e; iter-32/f (WATCH); iter-35/k; iter-36/n; iter-37/o /q.
- **OWNER, settle BEFORE any achievement run:** iter-34/j — `/api/health` ≤0.1 s budget missed a **7th** time, **0 of 28** polls in budget (min/mean/max 0.1234/0.3266/0.8083 s) in J-07 step 2's own scenario; 5 evaluators have called it his. Ratify honest-WARN · rescope for the bounded compute window · commission the cached-snapshot fix. Also iter-33/i (`start-frontend.sh` → `HOST_GUARD_MARKER_FILES`).

## Last 2 verdicts

- iter 40: ESCALATE — J-07 `partial` a 6th time (the frozen thread is still unidentified), AND 7 required journeys shipped completely unverified while review, QA and the closure gate all reported clean. Only the auditor caught it — 4th consecutive iteration. Keep the auditor.
- iter 39: ESCALATE — J-07 step 4 finally proven live at the named handler, but two acceptance clauses were falsified by the iteration's own honest drill; audit #1 returned FAIL on defects review AND QA both passed.

## Do not redo

- **`_missing_data_diagnostic` streaming fix is DONE** (`data_manager.py:271`, `.yield_per(cfg.research.read_batch_size)`): byte-identity proven by a test that replays the OLD `.all()` path as its reference, structurally traced by the auditor, and memory effect MEASURED (+4.6 MB vs +349 MB on 1M rows). Do not re-open the fetch strategy or re-argue the comment.
- **Checkpoint cadence is DONE** (`_RUN_RECORD_CHECKPOINT_INTERVAL_S` 10.0 → 1.0): live `kill -9` drill = 12 done in memory vs 11 persisted, counts internally consistent. Only the count-based floor remains. The "last saved checkpoint" relabel is NOT needed.
- **`merge_ui_test_results.py` BLOCKED class (TC-6/TC-7) and `perf-budgets.md:4996`'s in-place retraction (TC-5) are DONE.**
- **J-07 steps 1, 2 (HTTP-200 half), 3, and the step-4 per-horizon isolation proof are CLOSED at iter-39** (`runs/goal-ops-hardening-iter-39/fault-drill/`). Do NOT re-run to re-prove. **Do NOT resume cap-tuning.**
- **Byte-frozen:** `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched`. **AG-10 launch scripts: zero diff, never weaken.** Settled at iter-39 and not re-openable: env-toggle guard, root-logger config, `read_pool()` in-situ measurement, `_compute_one_isolated` worker `MemoryError` isolation.
- **Never make evidence capture an iteration's goal.** Ride-along only: J-07's `[NEW]` walkthrough (10 iterations unrecorded).
