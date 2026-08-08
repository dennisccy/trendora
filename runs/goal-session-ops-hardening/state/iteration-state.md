# Iteration State — ops-hardening

**After iteration:** 52 · **Date:** 2026-08-08 · **Verdict:** ESCALATE

## Journeys

4 passing (J-01 J-03 J-08 J-09) · 4 partial (J-04 J-05 J-06 J-07) · 0 failing — 8 total.
All 4 target journeys got REAL executed rows (first time in 3 rounds). No status moved.

## Active blockers

- **TC-9 hard gate (dev-owned, no human needed):** the lane closed 01:41:48 but `research.py` — this round's whole
  fix — landed 02:39:48, so the only independent evidence measured a superseded tree and FAILed J-05/J-07.
  `runs/goal-ops-hardening-iter-52/status.json` = `blocked` / `audit_qa_failed` / `browser_checks_run: false`.
  Code is frozen; **re-run the lane before any new code.** Root cause is pipeline ORDERING (lane dispatched
  before audit + audit-fix), broken 6 of 7 rounds — not agent discipline.
- **Health non-answers remain (dev):** 2/1,285 concurrent, 34/1,283 polls >2.0s (worst 4.901s), both residuals in
  `coverage_membership_timeline_refresh` + `market_phase_warm` — the two finalize-tail phases that never got the
  chunked-sort / bounded-GC treatment.
- **Regime Lab 500s (dev):** `/research/regime-lab`'s data call MemoryErrors on the live request path
  (`compute_regime_lab` → `_regime_lab_members_by_horizon`); no access-log line is written, and `J-06.json` step 11
  passes anyway because it asserts only the page heading.
- **Owner, unanswered:** (a) may heavy compute move off-process? (asked iters 50, 51) (b) is the 1,200s
  finalize-tail budget solo-only? (met solo 955.75s, missed busy 1,261.42s) (c) iter-50/cc.

## Last 2 verdicts

- iter 52: ESCALATE — real fix (GIL-stall diagnosis → chunked sort + bounded GC) landed after the lane;
  J-05/J-07 still below `passing` since iters 39/34.
- iter 51: ESCALATE — `factor_lab_all` ingest-warm landed (12 min → 8 ms), no target journey checked.

## Do not redo

- **`factor_lab_all_warm` + `_cooperative_sorted` + `_cyclic_gc_paused`** — shipped, byte-identity proven
  (object-identity tests; auditor re-derived at 260K rows). Do NOT re-diagnose; only EXTEND to the two phases above.
- **`perf-budgets.md` Items U/V/W + Addenda 12/13/14** — append-only; TC-2/3/5/6/7 all measured and disclosed
  there. **AG-10 frozen surfaces** verified EMPTY — never edit.
- **J-04's boot + interrupted-job half** — proven (1.73s first 200; interrupted row keeps 2/5). Only its
  badge/banner and logfile halves remain unobserved.
- **iter-50 columnar bound, single-flight waiter cooldown, `phase_context_by_date` skip, `_combination_cohort_members` bound** — landed; do not re-open.
