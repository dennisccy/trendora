# Iteration State — ops-hardening

**After iteration:** 51 · **Date:** 2026-08-07 · **Verdict:** ESCALATE

## Journeys

4 passing (J-01 J-03 J-08 J-09) · 4 partial (J-04 J-05 J-06 J-07) · 0 failing — 8 total. J-07 moved failing→partial; J-04 NOT tested (DEFERRED-BUDGET, 2nd round; last verified iter-49).

## Active blockers

- **Verification debt (dev, lane-only)** — zero executed rows for ALL THREE targets J-05/J-06/J-07,
  2nd round running; J-04 deferred twice. Lane = BLOCKED. Run the 8-journey lane, NO code change.
- **`/api/health` stalls during long ingest phases (dev)** — 9/653 solo + 19/892 concurrent
  connection-level non-answers; attaches to whichever finalize-tail sub-phase is LONGEST, not to
  `factor_lab_all_warm`. Fix = scheduling (chunk CPU-bound loops with yield points), `data_manager.py`
  finalize tail + `research.py`.
- **OWNER** — may iter-52 move `compute_factor_lab_all` off-process? Only other known fix shape;
  iter-51's spec excluded it. Plus the unanswered `iter-50/cc` interlock contradiction.
- **HARNESS** — permission system denied both backend-restart routes UT-05 needed
  (`TRENDORA_FAULT_INJECT_MEMORY_ERROR`), so J-07 step 4 has no evidence.

## Last 2 verdicts

- iter 51: ESCALATE — fix landed, proven live (Factor Lab 780-875s → 0.0078s; no crash/wedge/restart;
  0 new MemoryErrors), but no target journey checked and the DoD was recorded met with TC-3/5/6 unmet.
- iter 50: ESCALATE — memory bounded (7.8GB→3.1GB) but the service wedged 17m30s, no target row.

## Do not redo

- **`factor_lab_all_warm` finalize-tail phase — BUILT, live-proven** (`data_manager.py:4261-4310`); one
  `__all_factors__` `event_study_cache` row at the current stamp; in `aggregates_refreshed` of runs 320-325.
- **`_combination_cohort_members` `set(range(pool_n))` bound — DONE** (`research.py:1557-1573`),
  byte-identical vs a pinned oracle.
- **`perf-budgets.md` Item T / Addendum 11 — WRITTEN** (583.76s phase; 1,048.17s tail vs 1,200s budget;
  VmPeak 3,652.4 MB vs 8,192 MB). Append only.
- **AG-10 surfaces frozen, verified empty** — `config.yaml`, `host-guard.env`, `start-backend.sh`,
  `dev.sh`, `start-frontend.sh`. Never edit.
- **Still DONE from iter-50:** columnar `_FactorCoreRecords`/`_FactorObsPool` bound; single-flight
  waiter cooldown; `phase_context_by_date` conditional skip.
- **Evidence capture is never an iteration goal** — leaderboard shot, 2 blank frames, J-07 walkthrough.
