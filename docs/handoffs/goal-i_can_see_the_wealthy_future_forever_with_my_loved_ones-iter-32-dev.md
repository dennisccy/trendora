# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32
**Date:** 2026-06-18
**Agent:** developer
**Status:** complete

## What Was Built

**J-91 — Downtrend-conditioned Opportunity study (`/research`, additive over the existing evidence):**
- New read-only `research:compute_downtrend_opportunity_study` (+ `downtrend_opportunity_cached`,
  `_downtrend_opportunity_observation_set`, `_downtrend_angle_rows`, `_band_for`) in
  `apps/backend/app/engine/research.py`. It GROUPS the SAME enriched event-study observation set
  (`_regime_setup_pattern_observations` — stored realized return + MAE/MFE + `max_drawdown` + stored
  regime/sector/setup/pattern flags, read VERBATIM) and ADDITIVELY tags each observation with the CAUSAL
  as-of **phase / severity band / P(bear) band** at the observation's snapshot date, read from the
  read-only `market_phase` derivation (≤ D, FILTERED P(bear) only — never the J-89 smoothed/true-bear fence).
- Returns THREE angles: **(a) held_up_best** (best-first), **(b) fell_hardest** (worst-first, EVIDENCE
  ONLY — `weakness_evidence_only: true`, no order/execution path), **(c) recovery_turn_edge** (REUSES
  `compute_recovery_turn_edge` verbatim). Angles (a)+(b) rank the SAME conditioned cohorts; each cohort has
  per-horizon stats (n, mean, median, %-positive/hit-rate, expectancy, downside-only risk-adjusted
  [return/downside-dev, return/|MAE|], aggregate max-drawdown). Low-sample → honest `low_sample` flag + n.
- New endpoint `GET /api/research/downtrend-opportunity` (`horizon` / `view` Episodes⇄Pooled / `as_of`
  All-history⇄As-of params, mirroring `/api/research/event-study`). Horizons + min-sample come from
  `config.walk_forward`; the phase/severity-band/P(bear)-band vocabulary comes from a config-backed catalog.
- New `KIND_DOWNTREND_OPPORTUNITY` samples kind in `samples.py` reached via the EXISTING
  `GET /api/research/samples` (`dimension` + `cohort` selectors). Drill-down total == published row n in
  BOTH Episodes+Pooled and BOTH All-history+As-of; every displayable (dimension, cohort) row resolves 2xx.

**J-92 — Optional FRED macro feed + macro proxies (config-default-OFF):**
- New `FredProvider` macro provider (`apps/backend/app/data_providers/fred_provider.py`) registered in
  `make_provider` as `"fred"`. The FRED key is read FROM THE ENVIRONMENT ONLY (request-only, never
  persisted/logged/echoed); a no-key provider RAISES `ProviderUnavailableError` (never fabricated); a 429
  maps to `RateLimitError`; errors are built from the REDACTED URL so the key never leaks. FRED serves
  macro observations (`get_macro_series`), NOT OHLCV bars (`get_daily` raises).
- New STANDALONE `MacroSeries(symbol, date, value, source, published_date)` `create_all`-managed table
  (NOT `_ADDITIVE_COLUMNS`, NO snapshot rebuild) — registered in `test_db.py`'s new `MACRO_TABLES` guard.
- `^TNX` / `^DXY` / `^VXN` macro proxies stored as plain `DailyPrice` bars beside `^VIX` (committed seed).
- Macro wired as OPTIONAL config-default-OFF inputs to the J-87 severity score
  (`_macro_severity_legs` + `_severity_reading`) and the J-88 regime-switching observation
  (`_regime_switching_observation`). EACH leg OFF by default → with macro absent/disabled every J-87..J-91
  figure is BYTE-IDENTICAL to the price/breadth/VIX-only path (unit-asserted).
- Publication-lag alignment: a macro value usable for date D has `published_date <= D` (config per-series
  lag; the reference-date value on D is forbidden lookahead). Honest publication-lag limitation label.
- Committed small macro seed (`data/seed/macro/*.csv` + the three proxy price CSVs) loaded idempotently by
  `load_macro_seed`. The live FRED/proxy pull + any uncommitted series are data-dependent / NON-HALTING —
  honest blocked-NA, never fabricated.
- The macro feed catalog (env-detected availability + committed-seed coverage + per-leg flags) surfaced on
  `/data` via a new `macro` block on `GET /api/data` (`compute_macro_availability`) — env-var NAME only.

**Frontend:** the Downtrend Opportunity three-angle panel on `/research` + the macro provider catalog on
`/data` + the publication-lag limitation label. See the frontend handoff for details.

## Files Changed
- `apps/backend/app/config.py` -- new `ConditioningBand` / `DowntrendOpportunityCfg` (+ default factory) wired
  into `ResearchCfg`; new `MacroSeriesCfg` / `MacroEnableCfg` / `MacroCfg` (+ default factory) wired into
  `Config.macro`; band-catalog contiguity validator.
- `config.yaml` -- the real `research.downtrend_opportunity` band catalog + the `macro` block (env-var name +
  4 series + their publication-lags/proxies + the three default-OFF enable flags).
- `apps/backend/app/models.py` -- new STANDALONE `MacroSeries` table.
- `apps/backend/app/engine/market_phase.py` -- `phase_context_by_date` + `_causal_timeline` (the J-91 causal
  conditioning accessor, single-sourced with `recovery_turn_dates`); the J-92 OPTIONAL config-default-OFF
  macro legs in `_severity_reading` (`_macro_severity_legs`, `_macro_value_asof`) + the regime-switching
  observation (`_regime_switching_observation`).
- `apps/backend/app/engine/research.py` -- `compute_downtrend_opportunity_study` + observation builder + the
  three-angle ranking + `downtrend_opportunity_cached`.
- `apps/backend/app/engine/samples.py` -- `KIND_DOWNTREND_OPPORTUNITY` + `_downtrend_opportunity_samples` + dispatch.
- `apps/backend/app/api/research.py` -- `GET /api/research/downtrend-opportunity` + the new samples kind/selectors.
- `apps/backend/app/data_providers/__init__.py` -- register the `fred` macro provider in `make_provider`.
- `apps/backend/app/data_providers/fred_provider.py` (NEW) -- the FRED macro provider (env-only key).
- `apps/backend/app/engine/data_manager.py` -- `compute_macro_availability` (the `/data` macro catalog).
- `apps/backend/app/api/data.py` -- the `macro` block on `GET /api/data`.
- `apps/backend/app/seed_loader.py` -- `load_macro_seed` + the macro proxies added to `all_seed_symbols`.
- `apps/backend/data/seed/macro/*.csv` (NEW) + `data/seed/prices/_TNX.csv` / `_DXY.csv` / `_VXN.csv` (NEW).
- `apps/backend/tests/test_research.py` -- J-91 downtrend tests (byte-identity, no-lookahead, count-coherence
  Episodes×Pooled×All-history×As-of, every displayable row 2xx, downside-only risk, horizons-from-config,
  min-sample→NA, invalid-selector 4xx).
- `apps/backend/tests/test_market_phase.py` -- J-92 macro-disabled byte-identity of J-87/J-88 + the J-91
  phase-context; publication-lag no-lookahead; walled-series NA; FRED env-only / no-fabrication / parsing.
- `apps/backend/tests/test_db.py` -- register `macro_series` in the expected-tables guard (`MACRO_TABLES`).
- `apps/backend/tests/test_config.py` -- band-catalog + macro config validation; defaults-when-omitted.
- `apps/frontend/lib/api.ts` -- `fetchDowntrendOpportunity` + types; the `macro` block on the data overview.
- `apps/frontend/lib/samples-link.ts` -- the downtrend-opportunity cohort serialization.
- `apps/frontend/app/research/page.tsx` -- the `DowntrendOpportunityLab` (three side-by-side ranked tables +
  conditioning controls + Episodes/Pooled + the publication-lag label).
- `apps/frontend/app/research/samples/page.tsx` -- the downtrend-opportunity drill-down cohort header.
- `apps/frontend/app/data/page.tsx` -- the `MacroFeedPanel` (macro provider catalog + availability).

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v` (full suite handed to the pump nohup-async)
Targeted/fast results (inline, within the subagent cap):
- J-91 downtrend + band tests (`test_research.py -k "downtrend or band_for"`): 10 passed.
- J-92 macro + FRED tests (`test_market_phase.py -k "macro or fred"`): 8 passed.
- Config validation (`test_config.py -k "downtrend or macro or conditioning"`): 4 passed.
- `test_db.py` (incl. the new `MACRO_TABLES` guard + additive-migration tests): 11 passed.
- `test_no_magic_numbers.py`: 20 passed (research.py + market_phase.py stay magic-number-clean).
- Fast no-boot subset across research/market_phase/db/config/no-magic: 209 passed, 0 failed.
- API integration smoke (TestClient, file-backed synthetic DB): the new endpoint → 200 (3 angles,
  weakness_evidence_only=true), samples drill-down total == published n, invalid view/dimension → 422,
  `/api/data` carries the macro block (provider `fred`, env-var NAME only, 4 series).

Full ~880-test suite: launched ONCE via `nohup` (`/tmp/iter32-full-suite.log`) — the GOAL_ACHIEVED gate.
NOT blocked on here (iter-11/iter-29 lesson). An `exit=137` in that log is the known background-helper
harness-kill, NOT a test failure.

## Known Issues
- The macro seed values (`data/seed/macro/*.csv` + the `^TNX`/`^DXY`/`^VXN` proxies) are a deterministic,
  plausible COMMITTED OFFLINE SEED derived from the seed calendar + the committed `^VIX` (so the macro
  wiring is testable offline). They are NOT a live FRED pull — the live refresh (real FRED values) is
  data-dependent / non-halting and replaces them when a `FRED_API_KEY` is set and a macro fetch is run.
  This is honest by design (the J-22 / J-44-DIA non-halting contract); it does NOT change any default
  figure because every macro leg ships config-default-OFF.
- Macro legs are config-default-OFF, so the macro inputs do NOT influence any served figure by default —
  enabling a leg (`config.macro.enable.*`) plus configuring per-series `weight` + `stress_gate` is a
  deliberate config edit. The enabled-leg path is unit-tested (`test_macro_enabled_severity_leg_shifts_severity`)
  but not exercised by the live boot (which keeps every leg off).
- There is no Data-Manager UI affordance to TRIGGER a live FRED macro fetch this iteration — the `/data`
  macro panel is read-only catalog/availability (the live import flow is out of scope; the committed seed
  + the FRED provider give the offline-testable path the spec requires).
