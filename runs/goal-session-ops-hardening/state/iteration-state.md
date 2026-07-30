# Iteration State — ops-hardening

**After iteration:** 37 · **Date:** 2026-07-30 · **Verdict:** ESCALATE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-08 J-09) · 1 partial (J-07, 3rd straight) · 0 failing · 0 unknown — 8 total. Ledger: **11 unresolved, 0 critical**; iter-36/l + iter-36/m RESOLVED.

## Active blockers

- **dev, iter-37/o — THE J-07 BLOCKER, and it is a measurement, not a feature.** This iteration's ONE behavioural change (the ~1.13 GB `_BarCache` now held resident across the WHOLE finalize tail, `data_manager.py:3338`) was never measured: step 1/3's warm came from `GET /api/backtest` (no `JobProgress`, so `prog._shared_bar_cache` unset) and step 4's drill job had `dates_total: 0` (so `cache_ctx` = `nullcontext()`). FIX: re-run the SAME throwaway-DB drill with a real **K≥3-date** backfill so the shared cache is live, sample VmPeak across the whole tail, compare vs a forced-fallback run. Cheap and safe — do NOT inherit the audit's "hours on the 4.97 GB live basis" framing. Launch only via `scripts/start-backend.sh`.
- **dev — run J-07 step 1 through the path its own text names:** trigger the warm from a real backfill's ingest-finalize hook, not from `/api/backtest`, with the 1 Hz health poll during it.
- **dev, next code item (iter-33/g), queued twice and still unrun:** Regime Lab cold `view=pooled` needs the background dispatch `/api/backtest` got at iter-32; diagnose the bare "Internal Server Error" body. iter-37/q adds two fresh instances of that shape (uncaught `MemoryError` → HTTP 500 on `/api/backtest?as_of=` and `/api/data` at the 970 MB drill cap; the FIRST one precedes any abort, so the handoff's "already at the cap" story is wrong).
- **dev, iter-29/d — the LAST unbounded whole-table load** (I read the code): `data_manager.py:3098` still prefills and `prices.py:131-152` still selects `daily_prices` with NO WHERE clause. Once per job now, not twice. This is the largest open gap to GOAL_ACHIEVED.
- **dev, small + written down:** test `_do_backfill`'s new `except Exception` branch (reviewer MINOR); strengthen `test_run_data_job_backfill_wires_finalize_hook_end_to_end` to compare `aggregates_refreshed` vs a forced-fallback run (audit T2 — those warms swallow non-MemoryError exceptions, so a break is silent); stale docstring `data_manager.py:650-654`; "591 symbols" → 548 at `perf-budgets.md:4466`; audit B6's unmeasured `read_pool()` cost.
- **dev, carried minor, untouched:** iter-29/b + `warmup.py:194` badge wording after a permanently failed warm-up (8 iterations unmade); iter-31/e; iter-32/f (WATCH only); iter-35/k residual; iter-36/n.
- **OWNER, settle BEFORE any achievement run:** iter-34/j — the `/api/health` ≤0.1 s budget missed a 4th time and now in step 2's OWN scenario (**0 of 130** polls in budget, max 0.980 s, during a live 5-horizon warm). Three dispositions, all his: ratify honest-WARN as satisfying step 2 · rescope the budget for the bounded compute window · commission the agent fix (readiness from a cached snapshot). This is the only J-07 item no agent can settle. Also iter-33/i (`start-frontend.sh` → `HOST_GUARD_MARKER_FILES`), with new input: `scripts/dev.sh`'s SIGTERM trap orphaned the grandchild `next-server` and held port 3255 until kill -9.

## Last 2 verdicts

- iter 37: ESCALATE — J-07 steps 1-4 finally RAN and step 3's VmPeak margin is in `perf-budgets.md` at last, but two drills avoided the changed path, so J-07 stays `partial` (C.4 clause 1 → full depth MANDATORY). **The shipped code is sound; the gap is verification.** Review + QA both missed a real AG-8 regression that only the audit caught and fixed.
- iter 36: ESCALATE — J-06 restored to `passing`; J-07 `partial` because its browser lane never ran.

## Do not redo

- **iter-37's shipped work is verified sound — do NOT re-plan it.** Shared `_BarCache` across `_do_backfill` + the whole finalize tail; `test_kdate_backfill_loads_each_symbol_at_most_once` GREEN at max 1 load/symbol (was 10); `git show HEAD`-pinned byte-identity oracle + its mutation test (auditor re-verified the pinned body and re-ran both); audit B1's last-resort release at `data_manager.py:4327-4341` + `test_shared_cache_released_even_when_finalize_hook_never_runs` — mutation-proved, do not remove.
- **J-07 step 3 is DONE** — VmPeak 2,693,672 / 6,291,456 kB = 57.19% margin, recorded in `perf-budgets.md` "Iteration 37". Do not re-open; re-measure only for the finalize-tail question above.
- **iter-36/m is closed** — no leftover process, no listener on 8255/8256/3255 (checked live). Keep reaping; don't re-diagnose.
- **Byte-frozen:** `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched`. **AG-10 marker files + host-guard: zero diff, never weaken.**
- **Settled:** iter-33/h (all 5 Research labs share the honest-wait/Retry states) — extend, never rewrite; J-06's 11-page budget sweep (`perf-budgets.md:4099-4270`) still governs.
- **Never make evidence capture an iteration's goal.** Ride-alongs only: J-07's `[NEW]` walkthrough (7 iterations unrecorded, demo lane `not_yet` again); the J-01/J-03 identical-md5 screenshots; the rewritten `J-07.json` golden's DB-dependent literals (`n=8878`, `3508`) will need maintenance as the dev DB grows.
