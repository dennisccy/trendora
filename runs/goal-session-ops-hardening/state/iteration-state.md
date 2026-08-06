# Iteration State — ops-hardening

**After iteration:** 50 · **Date:** 2026-08-06 · **Verdict:** ESCALATE

## Journeys

4 passing (J-01 J-03 J-08 J-09) · 3 partial (J-04 J-05 J-06) · 1 failing (J-07) — 8 total. J-04 was NOT tested (DEFERRED-BUDGET); J-05/J-06/J-07 had zero lane rows of their own.

## Active blockers

- **J-07 health ceiling — dev.** `GET /api/health` breached ≤2 s on 96 of 1,179 polls (worst 10.06 s) during the live TC-1 drill. Cause is GIL contention between two CPU-bound computes, NOT memory — a memory bound cannot close it. Fix: take `compute_factor_lab_all` off the request path (ingest-time artifact) or off the event loop. `apps/backend/app/engine/research.py`.
- **17 m 30 s service wedge — dev, unproven-either-way.** `logs/backend.log` 22:57:06Z → restart 23:14:36Z; process alive, `futex_do_wait`, RSS 7.76 GB; only a restart cleared it. Did NOT reproduce in the 1,522 s post-fix drill (0 MemoryErrors, VmPeak 3,129 MB). Teardown is now instrumented. Do not claim fixed.
- **Lane never ran against current code — process.** `status.json`: `browser_checks_run: false`, `qa_verdict: INVALID_PENDING_REGENERATION`. TC-13 breached a 5th round: lane 00:13 → `warmup.py` 03:03, `data_manager.py` 05:41, `research.py` 07:28. Re-run the 8-journey lane LAST and REGENERATE `reports/qa/goal-ops-hardening-iter-50-qa.md` — never hand-edit.
- **Interlock spec contradiction — HUMAN/owner.** TESTING REQUIREMENTS "never silently drop the work" vs TC-5 "the finalize-tail warm defers analogously" cannot both hold; today both sides can defer and the drawdown warm is dropped for a whole dataset version (`data_manager.py:4290`, `warmup.py:202-232`). Audit B2 / ledger `iter-50/cc`.
- **`research.py:1334`** `set(range(pool_n))` in `_combination_cohort_members` — last MemoryError frame before the wedge, untouched by any diff since iter-31.

## Last 2 verdicts

- iter 50: ESCALATE — memory genuinely fixed (7.76 GB → 3.13 GB, 0 MemoryErrors in a 1,522 s drill) but J-07 failed a 2nd consecutive round on the ≤2 s health ceiling and a 17 m 30 s wedge; no journey changed status.
- iter 49: ESCALATE — the backend DIED for 12 m 45 s during its own lane; J-07 `partial` → `failing`, J-05 `failing` → `partial`.

## Do not redo

- **Evidence capture is never an iteration goal.** Demo (0 steps, 3rd round) and the missing `/scanner-runs` leaderboard screenshot ride the make-up lane as passenger tasks only.
- **Columnar `_FactorCoreRecords`/`_FactorObsPool` bound is DONE and byte-identity-proven** against an independently written pre-columnar oracle (`tests/test_factor_lab_all.py:480` vs `:391`). Do not re-open.
- **Single-flight waiter cooldown is DONE** (`research.py:3854-3871`, audit B1, failing-first test). Do not re-open.
- **`phase_context_by_date` conditional skip is DONE** (`data_manager.py:3889-3919`, TC-6).
- **AG-10 frozen files are correct and untouched** — `config.yaml` (8192 / 2), `host-guard.env`, `start-backend.sh`, `dev.sh`. Never edit; raising the cap is not the fix.
- **Carried, untouched (do not schedule as new diagnosis):** iter-29/b · iter-31/e · iter-32/f · iter-33/g (16th deferral) · iter-35/k · iter-36/n · iter-37/o · iter-37/q · iter-39/u · iter-46/az · iter-46/ba · iter-47/bd · iter-47/bf · iter-47/bi · iter-48/bj.
