# goal-i_can_see_the_wealthy_future-iter-6 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-6
**Date:** 2026-05-30
**Agent:** developer
**Status:** complete

## What Was Built

The walk-forward forward-testing engine + a populated **System Health** evidence dashboard (J-09, J-10).

- **`bars_after(session, symbol, d, limit=None)`** — the strict inverse of `bars_asof`: bars with **date > D**, ascending. The forward no-lookahead boundary. Optional `limit` caps the leading post-snapshot bars fetched (the backfill passes `limit=max(horizons)`).
- **`close_on(session, symbol, d)`** — the close of the latest bar with **date ≤ D** (the as-of entry close), single-bar form of `bars_asof(...)[-1].close` (cheap entry lookup; same backward boundary).
- **`ForwardReturn` model (`forward_returns` table)** — append-only, unique `(run_id, symbol, horizon)`. Stores `realized_return` (= h-th post-bar close / entry close − 1), plus `entry_close`, `asof_date`, `measured_date` for audit. `symbol` covers universe stocks AND benchmark ETFs (SPY, QQQ, the 11 sector ETFs). INSERT-only — keyed to the snapshot, never mutating it.
- **`app/engine/forward_testing.py`** (the Data-Contract module name):
  - `forward_return(bars_after_list, entry_close, horizon)` — pure; NA (None) when < horizon post-bars or entry missing/zero (never fabricated).
  - `walk_forward_asof_dates(session, cfg)` — the cadence as-of set: from `latest − history_years`, stepping at `asof_cadence`, snapped to real seed trading days, capped at the cutoff that still leaves ≥ max(horizons) post-bars.
  - `backfill_forward_returns(session_or_engine, cfg)` — idempotent, frozen-seed-only: persists a `run_scan` snapshot per cadence date, then INSERTs realized forward returns for **every** persisted run with ≥1 post-snapshot bar (incl. the Risk-off bootstrap runs, so by-regime carries both regimes). A second call inserts 0 rows.
  - `compute_forward_aggregates(session, horizon, cfg)` — the SINGLE canonical aggregation. READS the stored `leadership_bucket` / `setup_status` / `sector` / `rank` (`scanner_results`) and `regime_label` (`scanner_runs`) **verbatim** and groups the stored realized returns by them. Returns by-bucket (A–E) / by-setup / by-regime means + n, excess vs SPY & QQQ, and the control-group cohorts (top-ranked, random same-sector, SPY, QQQ, sector-ETF). Carries `min_sample` + a `survivorship_bias` label. Never recomputes a score/bucket/setup.
- **`GET /api/system-health?horizon=`** (`app/api/system_health.py`, registered under `/api`) — returns `compute_forward_aggregates(...)` verbatim. `horizon` defaults to `config.walk_forward.default_horizon` (20) and must be one of `config.walk_forward.horizons` else **422**; **503** when no price data.
- **Lifespan wiring** — `backfill_forward_returns(engine, config)` runs after `bootstrap_runs` (idempotent; coexists).
- **Typed config** — `WalkForwardCfg` + `ControlGroupCfg` (promoted from the scaffolded passthrough); `config.yaml` adds `walk_forward.{default_horizon, control_group:{seed, top_n, peers_per_sector}}` and sets `asof_cadence: quarterly` (see below).
- **Frontend** — `/system-health` graduates from the EmptyState stub to the dense-dark evidence dashboard: horizon selector (1/5/10/20/60), by-bucket A–E table, excess vs SPY/QQQ, by-setup + by-regime breakdowns, the control-group comparison panel, a prominent survivorship-bias banner, per-figure `n` with low-sample (`n < min_sample`) warn flagging, and pos/neg return colouring. `lib/api.ts` gains `SystemHealthResponse` types + `fetchSystemHealth(horizon)`.

## Chosen walk-forward cadence, as-of count, and first-boot time (spec-required documentation)

- **Cadence = `quarterly` over `history_years: 2`** (config, not code). The original scaffold value `weekly` would generate ~101 as-of dates; at the measured **~14 s per `run_scan`** (1.4 M `DailyPrice` ORM rows materialized per scan via `bars_asof`, which the plan requires be kept byte-identical) that is a ~23-minute first boot — intractable. `quarterly` yields a **bounded 8-date** set spanning two years, each still leaving ≥ 60 post-snapshot bars. Widen to monthly/weekly in `config.yaml` (no code change) for denser evidence at a slower first boot.
- **As-of dates (8 cadence):** 2024-05-28, 2024-08-28, 2024-11-27, 2025-02-28, 2025-05-28, 2025-08-28, 2025-11-28, 2026-02-27. Plus the 3 existing bootstrap runs (2022-10-07 Risk-off, 2025-04-04 Risk-off, 2026-05-28 latest) ⇒ **11 runs total; 10 contribute forward returns** (the latest seed-date run has 0 post-bars = the natural **n=0** demonstration). 6,739 `forward_returns` rows.
- **Both regimes confirmed in the by-regime sample:** Risk-on, Narrow leadership, Choppy, **and Risk-off** all appear (the Risk-off bootstrap dates 2022-10-07 / 2025-04-04 sit near market bottoms, so they honestly show strongly positive forward returns — exactly the kind of evidence the page surfaces, under the survivorship caveat).
- **First-boot backfill time (fresh DB):** ~**223 s** (bootstrap ~54 s + walk-forward backfill ~169 s), dominated by the 11 `run_scan` calls. **Subsequent boots are idempotent and fast** (already-persisted runs/returns are skipped). I warmed the committed runtime DB during verification so the QA/browser-QA boot reuses it.

## Files Changed

- `apps/backend/app/engine/prices.py` — add `bars_after` (date > D, optional limit) + `close_on`; docstring now describes both boundaries.
- `apps/backend/app/models.py` — add append-only `ForwardReturn` (`forward_returns`); docstring update.
- `apps/backend/app/config.py` — add `WalkForwardCfg` + `ControlGroupCfg`, wire `walk_forward` into `Config`.
- `apps/backend/app/engine/forward_testing.py` *(new)* — the forward-testing engine (pure return + backfill + aggregates).
- `apps/backend/app/api/system_health.py` *(new)* — `GET /api/system-health`.
- `apps/backend/main.py` — register `system_health.router`; call `backfill_forward_returns` in the lifespan.
- `config.yaml` — typed `walk_forward` (`asof_cadence: quarterly`, `default_horizon: 20`, `control_group:{seed:20240601, top_n:20, peers_per_sector:5}`).
- `apps/backend/tests/test_forward_testing.py` *(new)* — boundary, purity, aggregates-verbatim, determinism, no-fabrication, INSERT-only/idempotent/no-feedback proofs.
- `apps/backend/tests/test_api_system_health.py` *(new)* — API by-bucket/setup/regime+excess+control with n, default+non-default horizon, 422, 503, J-01..J-08 regression guard.
- `apps/backend/tests/test_no_magic_numbers.py` — guard extended to `forward_testing.py` + `prices.py`.
- `apps/frontend/app/system-health/page.tsx` — real evidence dashboard (replaces stub).
- `apps/frontend/lib/api.ts` — `SystemHealthResponse` types + `fetchSystemHealth`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v` and `cd apps/frontend && npm run build`
Result: backend — see the implementation summary / QA (fast forward-testing + no-magic suite: 17 passed; backfill immutability/idempotency integration: 4 passed; full suite run for regression). Frontend `npm run build` — green (all 10 routes typecheck; `/system-health` now 4.44 kB).

## Single-source / no-lookahead / immutability guarantees (how each is proved)

- **No lookahead (forward):** `bars_after` returns only date > D (boundary test + disjoint-partition assertion with `bars_asof`); `forward_return` uses the h-th post-bar, is NA when short, and is unchanged when later bars are removed; a run's stored scores are byte-identical with vs without forward returns (forward never feeds back).
- **Immutable snapshots:** backfill performs only INSERTs — a pre-existing run's child fingerprint is identical before/after, and a second backfill inserts 0 rows.
- **Single source:** aggregates group by the STORED `leadership_bucket` verbatim (a deliberately inverted stored-bucket fixture proves no re-bucketing); the frontend re-formats the one payload (no recomputed return/excess/bucket). Exact registered names used: module `app.engine.forward_testing:compute_forward_aggregates`, table `forward_returns`, endpoint `GET /api/system-health`.
- **No magic numbers:** horizons, min_sample, history_years, asof_cadence, default_horizon, and control-group `{seed, top_n, peers_per_sector}` all from config; benchmark tickers from `config.etfs`; guard test extended to the new calc files.
- **No fabricated data / honest limits:** zero-post-bar run = n=0 (no row); low-sample cells flagged (`n < min_sample`); 503 no data; 422 invalid horizon; survivorship-bias label on every payload + in the UI.

## Known Issues / Limitations

- **First-boot cost (~223 s on a fresh DB).** Inherent to replaying 11 full scans at ~14 s each (the `bars_asof` ORM-materialization cost, which the plan requires be left byte-identical). I warmed the runtime DB during verification so QA reuses it; the full pytest suite likewise pays one ~223 s lifespan backfill on its first `TestClient` (no readiness timeout applies to pytest). This is the spec's anticipated "longer first boot"; per the spec the durable runner-side fix (own/await the frontend + extended readiness timeout in `scripts/automation/browser-qa-phase.sh`) and the missing `reports/audits/` handoff are **runner-script gaps, not product scope** — flagged here for whoever drives the runner.
- **Bucket A is low-sample at short horizons** (e.g. n≈24 at 20-day < min_sample 30) — this is the honest outcome (few A-grade leaders per scan) and is visibly flagged, not hidden. Widening the cadence (config) raises n.
- **Survivorship bias is real and labelled:** evidence uses the current-membership universe; the Risk-off-bottom positive returns especially should be read as an upper bound.
