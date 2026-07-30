# Iteration State — ops-hardening

**After iteration:** 34 · **Date:** 2026-07-30 · **Verdict:** CONTINUE

## Journeys

**8 passing (J-01 J-03 J-04 J-05 J-06 **J-07** J-08 J-09) · 0 partial · 0 failing · 0 unknown — 8 total.** All Must-have journeys are green; only the ledger's 8 open findings block GOAL_ACHIEVED.

## Active blockers

- **dev, FIRST AND BIGGEST (iter-29/d):** `docs/goal.md` Success Criteria say verbatim "no code path streams the full `daily_prices` table into RAM" — `apps/backend/app/engine/prices.py:131-152` does exactly that (a 7-column `select` with NO WHERE, `.yield_per`, every row into `by_symbol`, ~1.5 GB per `data_manager.py:3025`'s own comment), reached on J-07's warm path via `_refresh_ingest_aggregates` (`data_manager.py:3164`) → `refresh_coverage_snapshot` → `_compute_coverage_uncached` (`:814`) → `prefilled_bar_cache`. Code re-read at iter-34.
- **dev (iter-33/g):** `/research/regime-lab` cold `view=pooled` blocks the request thread 60-90 s (`app/engine/research.py:3509-3559`, once per `dataset_version`); one call returned HTTP 200 carrying the body "Internal Server Error", undiagnosed. Needs `/api/backtest`'s iter-32 background dispatch.
- **dev, cheap + structural (iter-33/h):** `resolveLabLoadPanel` is wired into `RegimeLabPage` only; 4 sibling labs (`phase-severity-lab`, `regime-phase-factor`, `factor-lab`, `severity-velocity`) keep the bare unlabelled `LabSkeleton` + no Retry — the shape UT-11 proved is a P1. Resolver is generic + exported: wiring only.
- **dev, carried, all minor, none firing today:** `warmup.py:194` + what the badge says after a permanently failed warm-up (5 iterations unmade); iter-31/e; iter-32/f (WATCH only, never a goal).
- **capture ride-alongs, never an iteration's goal:** the `[NEW]` walkthrough steps J-06's and J-07's own Acceptance name (budgets table vs live page loads; crash-free warm + healthy health) — 4 consecutive iterations unrecorded, why both carry `evidence_makeup`. Also `J-07.json`'s literal `1873` needs a provenance line.
- **OWNER, settle BEFORE any achievement run (iter-34/j):** `GET /api/health` measured 0.105-1.132 s during its own warm — **0 of 185 polls** inside the written ≤0.1 s budget, so J-07 step 2's "within its existing budget" is not literally true. Not fixable by re-measuring on a quiet host. Pick one: ratify the honest-WARN convention as satisfying the clause; rescope the budget for the bounded background-compute window; or commission the agent fix (serve readiness from a cached snapshot).
- **OWNER, non-blocking (iter-33/i):** should `start-frontend.sh` join `HOST_GUARD_MARKER_FILES` now it runs a full `next build` inside automated lanes? Measured: the build inherits mask `0-3,8-11` today.

## Last 2 verdicts

- iter 34: CONTINUE — **J-07 crossed to passing**, closing the session's last non-green journey: the induced-memory-pressure drill (deferred 20 iterations) fired the exact iter-8 `MemoryError` branch in a throwaway `start-backend.sh` process that then served 14 more health 200s + 3 cached reads with no restart, and health latency was finally recorded (honest WARN).
- iter 33: CONTINUE — launcher genuinely serves `next start`; J-06's 11-page real-browser sweep + boot-to-health + code audit landed, so **J-06 crossed to passing**; the sweep's own P1 (Regime Lab cold stall) was fixed frontend-only inside the iteration.

## Do not redo

- **J-07 steps 2 and 4 are DONE** — latency recorded (`reports/perf-budgets.md:4271-4329`, raw CSVs under `runs/goal-ops-hardening-iter-34/`), drill recorded (`:4330-4438`, corroborated in `logs/backend.log:137264-137369`), plus the permanent regression test `apps/backend/tests/test_ingest_finalize_memory_pressure.py` (2 passed, real `ulimit -v` induction + control). Do not re-run the drill; extend it only if a NEW frame needs proving.
- **`compute_forward_aggregates` / `resolved_forward_aggregate_evidence` / `ensure_historical_forward_aggregates_dispatched` stay byte-frozen** — verified zero-diff again at iter-34.
- **J-06's sweep is DONE** (`reports/perf-budgets.md:4099-4270` + `...-iter-33-dev.md:151-186`); **`start-frontend.sh` is settled prod mode**; **`merge_ui_test_results.py` `_ROW_RE` → `(?:UT|TC)-` is FIXED** and held again this run.
- **The UT-11 honest-wait fix is DONE for Regime Lab** (`lib/lab-load-panel.ts` + `_labs.tsx`) — extend to the 4 siblings (iter-33/h), never rewrite it.
- **AG-10 marker files zero diff** — never weaken. The drill's `TRENDORA_CONFIG` cap override (970 MB, launched via `scripts/start-backend.sh`) is the sanctioned pattern: it TIGHTENS, never bypasses.
- **Do NOT re-open the `/api/health` ≤0.1 s budget as agent work without the owner's answer above** — it is now an explicit owner decision (iter-34/j), not a measurement gap.
