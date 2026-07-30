# Iteration State — ops-hardening

**After iteration:** 36 · **Date:** 2026-07-30 · **Verdict:** ESCALATE

## Journeys

7 passing (J-01 J-03 J-04 J-05 **J-06 restored** J-08 J-09) · 1 partial (J-07) · 0 failing · 0 unknown — 8 total. Ledger: **11 unresolved, 0 critical**; iter-33/h RESOLVED.

## Active blockers

- **J-07 WAS NEVER RUN (dev) — the one journey left.** No J-07 row in the merged results; UT-13/UT-14 SKIPPED because the browser lane took the backend down mid-plan and was then denied a restart 3×; `status.json: browser_checks_run=false`. Two agent unblocks: grant the restart, and **order backend-down tests LAST**. The auditor booted it himself via `scripts/start-backend.sh`, so this is NOT environmental. Still owed: step 1's full-horizon warm, step 2's 1 Hz poll DURING it, step 4's drill re-verified against the bounded paths, and step 3's VmPeak margin written into `reports/perf-budgets.md` (it exists only in the audit handoff: 2,691,796 / 6,291,456 KB = 42.8%).
- **REAP PID 2944679 BEFORE ANY MEMORY MEASUREMENT (dev, iter-36/m):** still alive, 4.1 GB RSS, VmPeak ~100 KB under the 6,291,456 KB cap, no listener on 8255, `/api/health` silent — the lane's `kill -TERM` never reaped it.
- **CLOSURE-FAIL is a FALSE ALARM (framework):** `closure_gate.py:71-74` greps the phrase `backend-only`; the only match is a correct scoping label at `…-user-visible-changes.md:35`, in a file that documents 4 changed pages. Fix the guard to test the CLAIM, not the phrase. 2nd time in 4 iterations UI bookkeeping cost a clean finish.
- **dev, iter-36/l — the LAST unbounded whole-table prefill:** `data_manager.py:3183` (`_persist_per_date_coverage_snapshots`) + `:3085` (`_do_backfill`), multi-date backfill only. It is what stands between today and J-07's Acceptance clause being literally true, and what keeps `test_kdate_backfill_loads_each_symbol_at_most_once` red (10, was 11 pre-fix).
- **dev, next in queue after the above (iter-33/g):** Regime Lab cold `view=pooled` needs the same background dispatch `/api/backtest` got; diagnose the HTTP 200 carrying "Internal Server Error". iter-36's UT-12 saw VmPeak ~100 KB under cap + a `MemoryError` at `research.py:3339`.
- **dev, small + written down:** stale docstring `data_manager.py:650-654` (describes deleted code); "591 symbols" → 548 at `perf-budgets.md:4466`; `read_pool()` now re-read once per (batch × date) ≈ 20,680 calls (audit B6) — unmeasured in wall-clock.
- **dev, carried minor:** iter-35/k residual (~4% not a bound); `warmup.py:194` + badge wording after a permanently failed warm-up (7 iterations unmade); iter-31/e; iter-32/f (WATCH only); iter-36/n (duplicate-date double-count, unreachable in prod).
- **OWNER, both still waiting, settle BEFORE any achievement run:** iter-34/j — `/api/health` ≤ 0.1 s budget, missed AGAIN (30/30 HTTP 200 but max 132 ms on a quiet backend); iter-33/i — should `start-frontend.sh` join `HOST_GUARD_MARKER_FILES`?

## Last 2 verdicts

- iter 36: ESCALATE — J-06 restored to `passing` on 4 screenshots I opened; J-07 `partial` a 2nd straight iteration purely because its browser lane never ran (tree C.4 clause 1). ESCALATE makes full depth MANDATORY, not advisory. **The shipped code is sound — the verdict is about missing verification, not defects.**
- iter 35: ESCALATE — a `full` spec dispatched at `evidence` depth built nothing; the live run proved two carried findings real, dropping J-06 and J-07 to `partial`.

## Do not redo

- **iter-36's shipped work is verified sound — do NOT re-plan or re-open it.** `_membership_timeline` batching (peak 1.13 GB → 330 MB, 70.7%), byte-identity proven on BOTH payload halves (TC-2 + the auditor's negative-controlled B1 test), `stored_by_key` chunking, 4 sibling labs wired. Only the blockers above remain.
- **iter-33/h is RESOLVED** — all 5 Research labs share the honest-wait/Retry states (`UT-05-computing.png`, `UT-03/08/11-error.png` all opened). Do not re-wire; extend, never rewrite.
- **Do NOT re-run J-07's iter-34 drill from scratch** — only re-verify against the new bounded paths. J-07 step 2's iter-34 latency work is done (`perf-budgets.md:4271-4329`).
- **Byte-frozen:** `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched`. **AG-10 marker files + host-guard: zero diff this iteration, never weaken.**
- **Settled, do not re-open:** J-06's 11-page sweep (`perf-budgets.md:4099-4270`) — on-load paths unchanged, so it still governs; `start-frontend.sh` prod mode; the `/api/health` budget as agent work (owner call).
- **Never make evidence capture an iteration's goal.** Ride-alongs only: J-07's `[NEW]` walkthrough (6 iterations unrecorded) and a J-06 budgets-table walkthrough — a `[NEW]` J-06 demo now EXISTS (steps 01-04), so that one is a subject gap, not an absence.
