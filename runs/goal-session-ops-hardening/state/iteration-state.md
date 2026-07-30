# Iteration State — ops-hardening

**After iteration:** 38 · **Date:** 2026-07-30 · **Verdict:** ESCALATE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-08 J-09) · 1 partial (J-07, 4th straight) · 0 failing · 0 unknown — 8 total. Ledger: **13 unresolved, 0 critical** (new: iter-38/r RESOLVED, iter-38/s, iter-38/t). **J-04 was NOT re-verified this iteration** — carried on durability, `last_verified_iter`=iter-37.

## Active blockers

- **dev, iter-38/s — THE J-07 BLOCKER, and it is one drill.** Step 4 never ran: `mem-drill/config.scratch.yaml:1363` raised the cap 3072→4608 MB "so BOTH arms complete gracefully", so both arms finished `ok`, no `MemoryError`, and the per-item isolation handler (`data_manager.py:3401-3407` / `:3435-3440`) was never exercised. The one 3072 MB trial died with `RuntimeError: can't start new thread` inside `_do_backfill`'s prefill (`dates_done: 0`) — wrong stage, and with no health poll or cached read alongside. FIX: ONE throwaway drill via `scripts/start-backend.sh` at a cap tight enough to raise `MemoryError` **inside the aggregate warm**, with a 1 Hz `/api/health` poll AND one previously-cached read (`GET /api/backtest?as_of=<warm date>`) asserted 200 during and after the abort. That is all step 4 asks.
- **dev, audit B2 — same drill, free:** delete `j07-warm/monitor.py`'s `MAX_SECONDS` bound; it expired at 299 s of a 338 s job, leaving a ~39 s blind spot (~31 s mid-tail).
- **dev, iter-38/t — the deterministic replay lane is OFF:** 1/7 PASS, six FAILs captured against a DOWN backend (`J-01-verify.png`, `J-04-verify.png` both show "Backend unavailable"). Refresh stale selectors; make the lane probe `/api/health` and report BLOCKED, never FAIL, when the service is down. Its reconciliation footer also under-reports its own overturns (omits J-05, J-04).
- **dev + coordinator — J-04 needs a live restart test before any achievement run.** Browser-QA was instructed not to restart services; J-04 requires it. Settle who may restart, schedule that test LAST (binding iter-36 lesson). Same block hit J-05 step 3 (cold-boot coverage-from-storage) — fold it in.
- **dev, next code item (iter-33/g), deferred three times:** Regime Lab cold `view=pooled` needs the background dispatch `/api/backtest` got at iter-32; diagnose the bare "Internal Server Error" body.
- **dev, iter-29/d — the LAST unbounded whole-table load:** `data_manager.py:3098` → `prices.py:131-152` still selects `daily_prices` with NO WHERE clause, once per job. Largest open gap to GOAL_ACHIEVED.
- **dev, small + written down:** re-measure `read_pool()` in situ during a real multi-date backfill (audit B3 — current figure is a micro-benchmark × a derived call count); guard or delete `TRENDORA_FORCE_LEGACY_BAR_CACHE` (audit B5 — `=0` currently ENABLES legacy mode) + a 2-line test (T3); fix the root-logger gap so liveness logging need not use `.warning` (reviewer NOTE).
- **dev, carried minor, untouched:** iter-29/b + `warmup.py:194` badge wording (9 iterations unmade); iter-31/e; iter-32/f (WATCH only); iter-35/k; iter-36/n; iter-37/q.
- **OWNER, settle BEFORE any achievement run:** iter-34/j — the `/api/health` ≤0.1 s budget missed a **5th** time, **0 of 233** polls in budget (min/mean/max 0.1087/0.2829/1.3172 s) during step 2's own scenario. Three dispositions, all his: ratify honest-WARN · rescope for the bounded compute window · commission the cached-snapshot fix. Also iter-33/i (`start-frontend.sh` → `HOST_GUARD_MARKER_FILES`).

## Last 2 verdicts

- iter 38: ESCALATE — J-07 `partial` a 4th time because step 4 was never run (C.4 clause 1 → full depth MANDATORY). Steps 1 and 3 are genuinely DONE. Review AND QA both passed a headline number that was backwards; only the audit caught it — keep the auditor.
- iter 37: ESCALATE — J-07 `partial` a 3rd time; both live drills ran paths where the new code was inert.

## Do not redo

- **iter-38's measurement work is verified sound — do NOT re-plan it.** Cache liveness proven in the LIVE `logs/backend.log` (`:142444` live, `:143130` nullcontext, `:143652` live) with `dates_total: 3` — iter-37/o's gap is CLOSED. Do not re-run the two-arm comparison.
- **The two-arm answer is known and corrected:** tail-only **+229.0 MB live vs +0.0 MB fallback**, overall peak +1.1%, fallback 2.61× slower (`perf-budgets.md:4831-4849`, `mem-drill/audit-recompute-tail-deltas.py`). Do not re-derive.
- **J-07 steps 1 and 3 are DONE:** the warm ran through a real backfill's ingest-finalize hook (2025-05-23; all 5 horizons `ready`; `evidence_generated_at` 03:04:33Z→12:22:41Z), VmPeak 58.6% of the 6144 MB cap, recorded in `perf-budgets.md` "Iteration 38". Only step 4 is missing.
- **Fixed, do not re-open:** TC-6 + TC-7 tests (both mutation-checked load-bearing), the `membership_timeline_cached` docstring, "591"→"548" at `perf-budgets.md:4466`.
- **Byte-frozen:** `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched`. **AG-10 marker files + host-guard: zero diff, never weaken.** iter-37's shared-cache release at `data_manager.py:4327-4341` is mutation-proved — do not remove.
- **Never make evidence capture an iteration's goal.** Ride-alongs only: J-07's `[NEW]` walkthrough (8 iterations unrecorded, demo lane `not_yet` again) and the now three-way J-01/J-03/J-05 identical-md5 screenshots.
