# Iteration State — ops-hardening

**After iteration:** 42 · **Date:** 2026-07-31 · **Verdict:** REGRESSION

## Journeys

6 passing (J-01 J-03 J-04 J-06 J-08 J-09) · 1 regressed (J-05) · 1 failing (J-07) — 8 total

## Active blockers

- **OWNER — halt reason.** The 30-year basis (~3.3M rows) no longer fits `memory_cap_mb: 6144`
  (`config.yaml:1363`): the heavy warm exhausts it — `/api/health` 500 ×4 then unresponsive
  (`logs/backend.log:153050-153075`), MemoryError (`:154035-154049`), "Backend unavailable" pages.
  Pre-existing; AG-10 bars any agent raising the cap. Owner: raise cap · shorten basis · relax goal.
- **dev, after that decision — J-05's failure.** An accepted job whose worker can't start reports
  `running`/0 forever, showing nothing (job `cbf08538…`, `logs/backend.log:152717`→`:154483`, 290
  polls, no worker line) — breaks "Zero silent zero-work jobs".
- **dev/owner — `_BarCache.prefill`'s symbol filter** (`apps/backend/app/engine/prices.py`) measured
  **+5.1% VmPeak REGRESSION**, not the recorded 2.5% win (audit B2). Keep / revert / finish.
- **dev — `bars_asof` 70-80× slower/call** since iter-41's `_SymbolColumns` (T2). Re-run all 8
  journey checks after the memory decision — the 6 passes predate the outage by minutes.
- **OWNER, carried:** iter-34/j `/api/health` ≤0.1s budget (now a hard 500); iter-33/i
  `start-frontend.sh` → `HOST_GUARD_MARKER_FILES`?

## Last 2 verdicts

- iter 42: REGRESSION — J-05 passing at iter-39, untested 40-41, now verified FAILING; J-07's first
  hard live FAIL (service outage). The new target-journey guard is what surfaced both.
- iter 41: ESCALATE — J-07 missed `passing` a 7th time; audit caught a CRITICAL review + QA passed.

## Do not redo

- **Target-journey verification lane DONE and PROVEN** (iter-41/z): `ui-test-designer` emits `UT-<id>`
  rows for targets; `merge_ui_test_results.py:201-232` forces BLOCKED on a missing/all-SKIP target
  (proof: this run's own `FAIL 6/8`). QA's AG-8 row corrected — iter-41/ab.
- **`KeyError` publish race FIXED in-audit** (`prices.py:364-377`/`:422-427`) + regression test;
  **B4 re-probe DONE** (`common.sh` `ensure_services_running`); **B6 NULL-tolerance DONE** (TC-8).
- **Never re-tune `server.memory_cap_mb`**; don't touch `compute_forward_aggregates` /
  `ensure_historical_forward_aggregates_dispatched` before the owner's envelope decision.
- **iter-33/g (Regime Lab cold `view=pooled`) deferred 7×; J-07's `[NEW]` walkthrough: capture-only.**
