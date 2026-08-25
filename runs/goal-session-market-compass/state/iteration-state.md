# Iteration State — market-compass

**After iteration:** 15 · **Date:** 2026-08-25 · **Verdict:** STALLED

## Journeys

3 passing (J-01 J-04 J-10) · 6 partial (J-02 J-03 J-05 J-06 J-09 J-11) · 2 failing (J-07 J-08) — 11 total. Iter-15 ran under MAINTENANCE ISOLATION (browser QA + replay lane forbidden by contract), so NO journey was tested and every status is carried, not re-verified. Anti-goal ledger: 6 total, 0 unresolved.

## Active blockers

- **OWNER DECISION (human) — the AVB convention.** `J-11 STAGE D READY: NO` · `AUTHORIZED: NO`. Measured and re-derived read-only by the evaluator (`runs/goal-market-compass-iter-15/j11-avb-bridge-diagnostic.json`): Trendora's stored AVB convention is bridged price + COMPENSATING volume (dollar-volume ratio ~1.0000 on 08-05/06/07/10); J-10's two recovered bars are bridged price + RAW volume (ratio exactly 2.7930), so their dollar volume is 2.793x too high (08-12 stores $1,860,985,686 vs the provider's $666,303,475). Options: (a) accept in writing with a dated caveat; (b) order a correction — a `daily_prices` write the plan forbids outright, needing its own dated permission; (c) reword the gate; (d) change the plan. Stage D needs a separate fresh owner instruction regardless (C10/A12).
- **ARMED SAFETY HAZARD (owner decides shape, then dev) — auditor B1, confirmed independently.** `apps/backend/main.py:100` → `warmup.ensure_latest_snapshot` → `run_scan(latest_data_date(...))`; `MAX(date) FROM daily_prices` = 2026-08-12, an incident date with ZERO `ScannerRun`s — so ANY backend boot INSERTs a run there before any request, and `GET /api/compass` on an incident as-of then mints AG-12-immutable manifests for the 7 dates lacking one. Both IRREVERSIBLE. Needs a PRE-BOOT guard (request-level is too late), in place BEFORE Stage G reopens the browser/replay lanes. Only maintenance isolation prevents it today — an operator convention, not code.
- Non-blocking, ride along next run: readiness staleness check compares clocks not DB fingerprints (B2); AVB-D override prints the wrong underlying label (B3); dev-handoff per-file test counts wrong (aggregate 157 passing is right).

## Last 2 verdicts

- iter 15: STALLED — AVB convention settled on real fetched evidence as AVB-C (`READY: NO`); every route past it is owner-owned; zero live DB writes; no anti-goal violation; auditor B1 escalated above it.
- iter 14: STALLED — Stage D preflight built but its AVB check was a price-only tautology; evaluator overturned four lanes' AVB-B to AVB-D; every unblock path owner-owned.

## Do not redo

- **Stage C bounded clear** — executed and verified in iter-13; all 11 incident dates at zero `ScannerRun`s.
- **Stage B1** (manifest FK migration + `basis_disclosure` fail-closed fix) — complete and closed; owner-accepted 4-item DDL residual; no second live rewrite authorized. Iter-11's REGRESSION verdict stands (A14).
- **J-10** — CLOSED by owner ruling; never reopen, never retry EA/EQR; its AG-9 exception is exhausted. Its AVB dollar-volume defect is recorded as a caveat, not a reopening.
- **AG-9 dated exception #2** (AVB fetch) — CONSUMED and EXHAUSTED by iter-15; evidence at `runs/goal-market-compass-iter-15/j11-avb-provider-fetch-evidence.json`. Any further fetch needs a NEW dated amendment.
- **Iter-13/14 evidence dirs + iter-14's `j11-stage-d-readiness.json`** — byte-preserved historical evidence; iter-14's is superseded, never edited.
- **`avb_daily_prices_sha256` = `0257c56d…0b11cd`** — RESOLVED, never a data mismatch: sha256 over the concatenated `repr()` of `(symbol,date,open,high,low,close,volume)` across all 5,397 AVB rows ordered by date.
