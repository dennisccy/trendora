# goal-i_can_see_the_wealthy_future-iter-5 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-5
**Date:** 2026-05-30
**Agent:** developer
**Status:** complete

## What Was Built

**Backend — the immutable snapshot persistence spine (recomputes nothing):**
- **4 append-only snapshot tables** in `app/models.py`: `ScannerRun` (one row per as-of date,
  `asof_date` unique), `ScannerResult` (one row per run×stock; typed score/bucket/setup columns +
  `record_json` holding the complete canonical `score_stocks` row), `SectorScoreRow`, `ThemeScoreRow`
  (stored copies of the `SectorRow` / `ThemeRow` shapes). Integer PKs, FKs, JSON text columns,
  Postgres-ready. Created by `create_all()` on startup. `forward_returns` / `paper_portfolio*` remain
  DESIGNED-but-not-created (noted in the model docstring).
- **`app/engine/scanner.py`** — `run_scan(session, asof, cfg)` calls the canonical engines ONCE for
  the date (`score_regime`, `score_sectors`, `score_themes`, `score_stocks`,
  `setups.summarize_candidates`) and persists ONE complete snapshot in a single transaction. It
  reimplements no scoring math; the run summary (regime/breadth/new-high-low/candidate counts) is
  READ from the canonical outputs, never recomputed from a second formula. **Idempotent + immutable:**
  a second scan for the same `asof_date` returns the existing run unchanged (no duplicate, no UPDATE).
  `bootstrap_runs(session_or_engine, cfg)` ensures a run for every `cfg.scanner.bootstrap_dates` date
  PLUS the latest data date; idempotent; reads ONLY the frozen seed (never live).
- **`app/api/runs.py`** — `GET /api/runs` (persisted runs, descending by `asof_date`, each with
  regime label+score, candidate counts, n_stocks) and `GET /api/runs/{run_id}` (one run's full STORED
  snapshot: regime panel + components, universe-relative breadth, candidate counts, and the ranked
  stored stock rows rehydrated from `record_json` into the canonical `StockRow` shape). Serves STORED
  rows only — never calls the live `score_*` engines for a historical date. `404` unknown run, `503`
  no price data.
- **`main.py`** — registers `runs.router`; calls `bootstrap_runs(engine, config)` in the lifespan
  after `load_seed`.
- **`config.py` + `config.yaml`** — new required `ScannerCfg { bootstrap_dates }`; ISO strings parsed
  to `datetime.date` (no date literal in calc code). `scanner.bootstrap_dates: ["2022-10-07",
  "2025-04-04"]` (both verified `"Risk-off"`).

**Frontend — two real pages (re-format only, never recompute):**
- `app/scanner-runs/page.tsx` — replaces the EmptyState stub with a dense dark run-list table
  (as-of date → link, colour-graded regime badge, candidate counts, stock count). Honest
  "Backend unavailable" / empty states.
- `app/scanner-runs/[runId]/page.tsx` — replaces the EmptyState stub with the immutable as-of view:
  an "Immutable snapshot — as of YYYY-MM-DD" header strip, the regime panel (label + 0–100 +
  `ComponentBreakdown`), universe-relative breadth, candidate counts, and a ranked stored stock table
  reusing `ScoreBadge` + the setup-status `Badge`. Honest unavailable / 404 states.
- `lib/api.ts` — `RunSummary` / `RunDetail` types + `fetchRuns()` / `fetchRun(runId)`; run-detail rows
  reuse the existing `StockRow` type.

## Files Changed

- `apps/backend/app/models.py` — add `ScannerRun`, `ScannerResult`, `SectorScoreRow`, `ThemeScoreRow` (append-only); update module docstring
- `apps/backend/app/config.py` — add required `ScannerCfg { bootstrap_dates: list[date] }`; import `date`
- `apps/backend/app/engine/scanner.py` *(new)* — `run_scan` (idempotent/immutable) + `bootstrap_runs` (frozen-seed only)
- `apps/backend/app/api/runs.py` *(new)* — `GET /api/runs`, `GET /api/runs/{run_id}` (serve STORED rows)
- `apps/backend/main.py` — register `runs.router`; call `bootstrap_runs` in lifespan
- `config.yaml` — add `scanner.bootstrap_dates`
- `apps/backend/tests/test_scanner.py` *(new)* — 7 tests (persists-complete / idempotent-immutable / no-lookahead / faithful-copy / risk-off-zero-actionable / distinct-as-of / bootstrap-idempotent)
- `apps/backend/tests/test_api_runs.py` *(new)* — 6 tests (list desc / detail stored / J-08 differs / J-07 zero-actionable / 404 / 503)
- `apps/backend/tests/test_no_magic_numbers.py` — add `test_scanner_has_no_scoring_or_date_literals`
- `apps/backend/tests/test_config_engine.py` — add 3 `ScannerCfg` validation tests + `scanner` in `VALID`
- `apps/backend/tests/test_config.py` — add `scanner` to `MINIMAL_VALID`
- `apps/backend/tests/test_db.py` — expected-table set now includes the 4 iter-5 snapshot tables (test renamed `…_produces_expected_tables`)
- `apps/backend/tests/test_sectors.py`, `tests/test_themes.py` — add `scanner` to their synthetic `_SYNTH_CFG` (now a required section)
- `apps/frontend/lib/api.ts` — `RunSummary` / `RunDetail` types + `fetchRuns()` / `fetchRun()`
- `apps/frontend/app/scanner-runs/page.tsx` — real run-list table (replaces stub)
- `apps/frontend/app/scanner-runs/[runId]/page.tsx` — real immutable as-of detail (replaces stub)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **143 passed, 0 failed** (full suite, 9m33s — the runtime is seed-loading fixtures, not a
regression). New this iter: 7 `test_scanner.py` + 6 `test_api_runs.py` + 1 `test_no_magic_numbers`
extension + 3 `ScannerCfg` validation tests. Updated for the new tables/required-config: `test_db.py`
(expected-table set), `test_sectors.py` / `test_themes.py` / `test_config.py` (synthetic `scanner`
section). No regressions — the 6 green journeys' endpoint tests (`test_api_engine.py` J-06 coherence
etc.) still pass.

Command: `cd apps/frontend && npm run build`
Result: PASS — compiled + typechecked all 10 routes, including `/scanner-runs` (2.76 kB) and
`/scanner-runs/[runId]` (4.83 kB).

Live boot (real `uvicorn main:app`, throwaway DB + port): cold boot ready in ~55s; `GET /api/runs`
served 3 runs DESC (2026-05-28 Risk-on / 2025-04-04 Risk-off 0-Actionable / 2022-10-07 Risk-off
0-Actionable); `GET /api/runs/1` (2022-10-07) = 122 rows, 0 Actionable, top3 HUBB/REGN/AXON; unknown
run → 404; restart → no port conflict (process cleanup verified). The pre-existing stale `:8835`
backend (old code, no `/api/runs`) was killed so downstream review/QA/browser-QA boot a fresh backend.

Keystone probe (real EOD seed, no fabrication): latest seed date **2026-05-28**; **2022-10-07** →
regime `Risk-off` (8.34), **0 Actionable**; **2025-04-04** → `Risk-off` (6.30), **0 Actionable**;
rankings differ by date (HUBB/REGN/AXON… vs KTOS/NOC/PLTR… vs MU/ARM/MRVL…); NVDA Leadership 22.13
vs 43.39 vs 47.48 — J-07 and J-08 both real end-to-end.

## Critical anti-goals — unit-proven

- **Snapshots immutable** — `test_run_scan_idempotent_and_immutable`: a second scan yields exactly one
  run, same id/created_at, byte-identical children. `test_bootstrap_runs_idempotent_persists_all_dates`:
  re-bootstrap creates nothing new, mutates nothing.
- **No lookahead** — `test_run_scan_no_lookahead`: a run dated D against the full seed is byte-identical
  to the run against a DB truncated to bars ≤ D.
- **Single source of truth** — `test_latest_run_faithful_to_live_computation`: the stored snapshot's
  per-stock `record_json` == `score_stocks(latest)["rows"]` and `regime_*` == `score_regime(latest)`,
  field-by-field. `/api/runs/{id}` serves the stored copy; live endpoints unchanged.
- **Risk-Off gates Actionable** — `test_risk_off_run_has_zero_actionable` (+ API `…_j07`): a configured
  "Risk-off" date stores `regime_label == "Risk-off"` and 0 Actionable results.
- **No magic numbers** — `test_scanner_has_no_scoring_or_date_literals`: scanner.py has no float /
  config-tunable-int / ISO-date literal; bootstrap dates come from `config.scanner.bootstrap_dates`.
- **No fabricated data** — unknown run → 404, no price data → 503 (both tested).

## Known Issues

- **First-boot cost (measured)**: a clean cold boot on a fresh temp DB became ready in **~55 s** end to
  end (verified live via `uvicorn main:app` on a throwaway port). The dominant cost is the
  **pre-existing** seed load (~205k price rows for ~158 symbols — unchanged by this iteration); the NEW
  cost this iteration adds is `bootstrap_runs` = 3 full-pipeline scans (regime+sectors+themes+stocks),
  run ONCE before serving and idempotently skipped on every later boot. On an already-seeded DB the
  net new first-boot cost is just those 3 scans. Flagged for backend-readiness probing so a slow first
  boot is not misread as "backend down". Restart (warm boot) was verified to have no port conflict.
- **`/api/health` still returns `last_run_date: null`** — wiring it to the newest persisted run is a
  small cosmetic follow-up, intentionally left out of scope (touching health.py was not in this spec).
- **Run-detail tickers are not links** to `/stocks/[ticker]` — the stored row is an as-of historical
  snapshot, so it deliberately does not deep-link to the live (latest) stock-detail page (that would
  mix a frozen date with today's numbers). Can be revisited if a per-snapshot stock view is added.
- **Process/harness gap (not product code) — recurring, please action this iteration:**
  1. **The audit step must actually run** and write `reports/audits/goal-i_can_see_the_wealthy_future-iter-5-audit.md`
     — that directory is still empty (audit handoff missing 4 full-depth iters running). This is the
     auditor agent's deliverable, flagged here per the spec's Definition of Done.
  2. **Browser-QA should own/self-heal its frontend** (start `next dev` if down, like QA mode-2) — the
     SKIP-on-HTTP-000 flap has recurred 4 iterations. Until fixed, reconcile journeys from the on-disk
     evidence PNGs, not a lone SKIP verdict.

## Suggested Next Phase

iter-6 (J-09, J-10): the walk-forward forward-testing engine + System Health. It reads these immutable
snapshots and writes realized 1/5/10/20/60-day forward returns into a **separate** append-only
`forward_returns` table keyed to `(run_id, stock, horizon)` — never mutating the snapshot — then
aggregates returns by bucket / setup / regime with excess-vs-SPY/QQQ/sector and random-same-sector
control groups. The no-lookahead boundary (`bars_asof`) and the append-only snapshot store built this
iteration are the groundwork it depends on.
