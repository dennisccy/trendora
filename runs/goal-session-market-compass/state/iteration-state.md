# Iteration State — market-compass

**After iteration:** 17 · **Date:** 2026-08-25 · **Verdict:** STALLED

## Journeys

3 passing (J-01 J-04 J-10) · 6 partial (J-02 J-03 J-05 J-06 J-09 J-11) · 2 failing (J-07 J-08) — 11 total.
Iters 13-17 under MAINTENANCE ISOLATION (browser QA + replay forbidden): only J-11 verified, all others carry prior status. Ledger: 7 total, **0 unresolved** (iter-16's AG-8 CLOSED by iter-17).

## Active blockers

- **HUMAN — the live boot-path hole is fully open and no non-owner action closes it. Nobody may start the
  backend.** Booting would (1) mint `maintenance_boundaries`, which `docs/goal.md`'s BLOCKER ON RECORD
  forbids creating, and (2) write a `ScannerRun` onto 2026-08-12 — the newest stored price day IS an
  incident date holding 0 runs. `main.py`'s `create_db_and_tables()` runs BEFORE `ensure_latest_snapshot()`,
  so `j11_preboot_guard.py` is inert. Owner picks: (a) authorize creating that one empty table → the
  built+tested arm script arms the guard; (b) order the Stage D rebuild of the 11 dates (safe: controlled
  script, not a booted app), needing a fresh written instruction; or (c) amend `docs/goal.md`.
- **HUMAN — Stage D remains NOT AUTHORIZED** (`J-11 STAGE D READY: YES` · `AUTHORIZED: NO`, unconditional).
- Riders (non-blocking): refusal tests for the 2 new evidence scripts (`run_j11_iter17_stage_d_readiness.py`
  can overwrite 3 committed iter-16 files if `--evidence-dir` is mistyped); fix the AVB note calling A/B
  "genuinely independent" (ratio ≈1.0 by algebra); fix QA's incident-date list; drop the `git diff`-only proof.

## Last 2 verdicts

- iter 17: STALLED — authorized slice delivered in full and correctly, AG-8 closed, zero live writes; but
  the guard is still inert on the live DB and every route to arming it is owner-owned.
- iter 16: STALLED — owner's 4-step sequence stopped where told; first `READY: YES`; guard built but inert.

## Do not redo

- **AG-8 bounded-query fix** — DONE, verified (`j11_preboot_guard.py:173-182`, `:218-228`: `active IS NOT
  FALSE`, 4-col projection, `LIMIT 101` + fail-closed `len(rows) > 100`). 39 tests pass.
- **Arm/disarm entrypoints** — DONE (`run_j11_maintenance_boundary_{arm,disarm}.py`): no default
  `--database-url`, `--confirm` required, dates from `INCIDENT_DATES`, refuses when the table is absent,
  never calls `create_all`. Do not rebuild; only INVOKING arm is blocked.
- **AVB label correction** — DONE (honest `AVB-A`); cannot move `READY: YES`. Do not re-run
  `run_j11_avb_correction.py` (spent); iter-16's two-cell correction is verified.
- **J-10 CLOSED by owner ruling (2026-08-24)** — 585 restored, EA/EQR unrestorable. Never reopen. Iter-16's
  artifacts are immutable (sha256 `e794dbf2…`, `1e35942c…`).
