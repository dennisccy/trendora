# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20
**Date:** 2026-06-15
**Agent:** developer
**Status:** complete

## What Was Built

The remaining backend research cluster — J-72, J-75, J-77 — all buildable OFFLINE against the committed seed, with byte-identity + count-coherence property gates.

- **J-72 — event-study perf + cache (figures byte-identical):**
  - Replaced the per-horizon re-scan of `forward_returns` in `compute_event_study` with a SINGLE batched
    read (`research._event_study_members_by_horizon`): one `ForwardReturn` SELECT covering every configured
    horizon (`horizon IN (...)`) + one `ScannerResult` + one `ScannerRun` SELECT. Per-horizon member lists
    are byte-identical to the old per-horizon builder (both now `order_by(ScannerResult.id)` for a total
    deterministic order). The compute loop calls the batched builder exactly once.
  - Added a STANDALONE create_all-managed cache table `event_study_cache` (NO `_ADDITIVE_COLUMNS` entry
    needed — it is a new table). `research.event_study_cached` serves the serialized
    `compute_event_study(...)` payload from the cache, keyed by `(subject, view, asof_key, dataset_version,
    horizon)`. The dataset-version stamp (`_dataset_version` = `r<max scanner_run id>-f<forward_returns
    count>`) changes on any dataset change, so a stale row is never hit (and is pruned on write) — the cache
    refreshes automatically after a backfill add or a removal. `GET /api/research/event-study` now serves
    via the cache (payload shape + values unchanged).

- **J-75 — per-stock forward returns (1/5/10/20/60-day), served VERBATIM from stored data:**
  - `snapshot_serving.stored_stock_rows` now additively attaches a `forward_returns` list to every served
    stock row — one `{horizon, return}` per `config.walk_forward.horizons` entry (NO hardcoded
    `[1,5,10,20,60]` literal), read VERBATIM from the stored `forward_returns` table for the resolved as-of
    run (the SAME stored rows Backtest/J-21 reads). A horizon with no stored row renders `return: null`
    (NA — never fabricated). The leaderboard list row and the detail row carry IDENTICAL values (J-06).

- **J-77 — Regime × Setup × Pattern ranked combinations study:**
  - Additively enriched the event-study observation pool (`research._event_study_members`) with each
    observation's stored `setup_status` + `patterns` (a `{pattern_key: bool}` map from the `is_<key>`
    mirrors). Purely additive — existing J-29/J-63 figures + samples drill-downs stay byte-identical.
  - Added `research.compute_regime_setup_pattern_study(...)`: a cross-subject grouping of the SAME stored
    observation set (`_regime_setup_pattern_observations` — every (run, ticker) with a realized return at
    the horizon, carrying stored regime + setup + pattern flags) by the (regime, setup, pattern) key. Each
    row reports `n`, `mean`, `median`, `pct_positive` (hit-rate), `expectancy`, and BOTH downside-only
    risk-adjusted figures (return/downside-dev AND return/mean-|MAE| — never total volatility). Default
    ranked by the risk-adjusted figure. An observation matching two patterns counts under both; one
    matching none counts under the `none` sentinel. Honors `view` (Episodes default/Pooled, J-63) and
    `as_of` (J-32 filter). Low-sample combinations carry an honest `n` + `low_sample` flag.
  - New endpoint `GET /api/research/regime-setup-pattern` (mirrors the event-study param style: `horizon`,
    `view`, `as_of`; 422 on bad horizon/view, 503 on no data).
  - New samples cohort selector `kind=regime-setup-pattern` (`samples._regime_setup_pattern_samples` +
    `compute_samples`), reachable via `GET /api/research/samples?kind=regime-setup-pattern&regime=&setup=&
    pattern=&view=`. The drill-down total EQUALS the study row's published `n` in BOTH Episodes and Pooled
    modes (same observation builder + same `_rsp_combination_filter` predicate — count-coherence keystone).

  Vocabularies for J-77 (regime labels, setup statuses, pattern keys) come from the EXISTING config-backed
  catalogs (`cfg.regime.labels`, `setups.ALL_STATUSES`, `cfg.patterns` keys via the new `research.pattern_keys`
  helper) — **NO new validated config section** was introduced, so the config-narrowing-site trap does not
  apply.

- **Frontend:**
  - `/research`: a NEW **Regime × Setup × Pattern — ranked combinations** study section with its OWN
    independent fetch + loading/skeleton state (per-section loading; no single slow query blocks the page,
    J-15/J-72). Client-side sortable columns (J-48 view transform; NA-last; default = the served
    risk-adjusted rank), its own Episodes ⇄ Pooled toggle (J-63), reuses the page's shared horizon +
    analysis-mode (J-18/J-32). Each row's `N=` chip opens `/research/samples` for that exact combination in
    a NEW tab (J-65, `?asof` href-stamped via the shared `SampleLink`/`useAsOfHref`, J-50).
  - `/stocks`: five forward-return columns (1/5/10/20/60-day, config-driven from the served rows),
    colour-graded by sign, client-side sortable under the J-48 contract (NA-last; default order = stored
    rank), NA cells render honest "NA".
  - `/stocks/[ticker]`: a new **Realized forward returns** panel showing the SAME five values for the
    resolved as-of date.
  - `lib/api.ts` / `lib/samples-link.ts` / `app/research/samples/page.tsx`: new types + fetch
    (`fetchRegimeSetupPattern`), the `forward_returns` field on `StockRow`, the `regime-setup-pattern`
    cohort param + samples-page cohort heading.

## Files Changed

Backend:
- `apps/backend/app/engine/research.py` — J-72 batched read + `event_study_cached` + dataset-version + cache helpers; J-77 observation enrichment (`pattern_keys`, `_stored_pattern_flags`) + `compute_regime_setup_pattern_study` + its observation builder/filter helpers; explicit `order_by(ScannerResult.id)` on the members queries.
- `apps/backend/app/engine/snapshot_serving.py` — J-75: `_forward_returns_by_symbol` / `_forward_returns_for_row`; `stored_stock_rows`/`stocks_payload`/`stock_detail_payload` thread config + attach `forward_returns`.
- `apps/backend/app/engine/samples.py` — J-77: `KIND_REGIME_SETUP_PATTERN` + `_regime_setup_pattern_samples` + `compute_samples` wiring.
- `apps/backend/app/api/research.py` — J-72: `/research/event-study` serves via `event_study_cached`; J-77: new `/research/regime-setup-pattern` endpoint + `/research/samples` new `setup`/`pattern` params + view validation for the new kind.
- `apps/backend/app/models.py` — J-72: new standalone `EventStudyCache` table.
- `apps/backend/tests/test_iter20_research_cluster.py` — NEW: 15 hand-built tests (J-72 byte-identity/single-batched-read/cache-refresh, J-75 serving/NA/coherence, J-77 group-by/count-coherence/4xx).
- `apps/backend/tests/test_api_research.py` — appended 10 API-level tests (J-72 endpoint byte-identity, J-75 leaderboard==detail==stored==backtest, J-77 endpoint + count-coherence same-instant + 4xx).

Frontend:
- `apps/frontend/lib/api.ts` — `StockForwardReturn` + `StockRow.forward_returns`; `RegimeSetupPattern*` types + `fetchRegimeSetupPattern`; `SampleCohort` new kind + setup/pattern fields.
- `apps/frontend/lib/samples-link.ts` — `RegimeSetupPatternCohortParams` + its serialization.
- `apps/frontend/app/research/page.tsx` — the new study section (fetch + loading + sortable table + view toggle + N= chips).
- `apps/frontend/app/stocks/page.tsx` — five sortable forward-return columns + cells.
- `apps/frontend/app/stocks/[ticker]/page.tsx` — the forward-return panel.
- `apps/frontend/app/research/samples/page.tsx` — `describeCohort` branch for the new kind.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest <targeted modules> -q`
Results (targeted modules, run to completion this turn):
- `tests/test_iter20_research_cluster.py` — 15 passed.
- `tests/test_iter20_research_cluster.py tests/test_research.py tests/test_samples.py` — 107 passed (the existing research/samples suites confirm the J-72 batched-read refactor + the J-77 additive enrichment leave existing figures byte-identical).
- `tests/test_api_research.py -k "<iter20 + forward_returns + regime_setup_pattern + ...>"` — 10 passed (API-level: J-72 byte-identity, J-75 leaderboard==detail==stored==backtest, J-77 endpoint + count-coherence SAME-INSTANT in both views + 4xx).
- `tests/test_db.py tests/test_config.py -k "additive or column or registry or config"` — 57 passed (the `_ADDITIVE_COLUMNS` guard test is unaffected — the cache is a standalone table; no new config section).
- `tests/test_api_research.py tests/test_api_engine.py tests/test_api_backtest.py tests/test_api_watchlist.py` — 98 passed, 2 failed on the first run. The 2 failures were two EXISTING `test_api_engine.py` tests (`test_api_stocks_equals_engine_output`, `test_asof_serves_stored_snapshot_matching_run_detail`) that asserted `/api/stocks` rows byte-equal the live `score_stocks` output / the immutable `/api/runs/{id}` rows — now broken by the J-75 ADDITIVE `forward_returns` serving field (absent from `score_stocks` and from the immutable run-detail path, which correctly does NOT carry forward returns). Both assertions were updated to compare the canonical scored rows MODULO the additive `forward_returns` field (no-drift guarantee preserved) + assert the field is present and config-driven. Re-run: **4 passed** (the two fixed tests + the two J-06 detail tests).

Live smoke (backend :8835 warm, frontend :3835): J-72 cache HIT 0.024s vs first-compute ~28s (byte-identity asserted by tests); J-77 endpoint HTTP 200, live count-coherence study row n=116 == samples total=116 == len(rows)=116 SAME-INSTANT; J-75 at a historical date (2021-01-04) AAPL shows all five populated forward returns and detail==list.

Frontend gate: `cd apps/frontend && npx tsc --noEmit` — clean (exit 0). (ESLint not installed — per iter-1 lesson.)

**FULL backend suite (~790 tests) still needs a pump run** — per the operational note it is NOT run in this dev turn (a dev-turn background run does not survive the turn ending, and the suite is ~35-46 min). Hand it to the pump as a `nohup` background run; gate on the flushed terminal summary line.

## Service State

- Backend restarted on **:8835** (reflects these changes; warm-up completed, readiness `ready`).
- Frontend restarted on **:3835** (`next dev`, compiling cleanly — not a prod build, so no `.next` clobber).

## Known Issues / Notes

- **J-72 is a perf property, not a displayed number** (iter-8 lesson) — the binding gates are byte-identity
  of figures + the single-batched-read assertion (both committed), NOT a wall-clock ratio.
- **Count-coherence is same-instant** (iter-7 lesson) — the J-77 count-coherence API test asserts the
  study row `n` against the LIVE `/research/samples` total at the same instant (Ns drift between boots as
  warm-up matures). Never assert against a hardcoded N.
- **Live-smoke contention:** while the long `loaded_engine` pytest run is in flight, the single-worker
  uvicorn on :8835 competes for CPU and a first-compute J-77 request can time out (HTTP 000) — a resource
  artifact, not a bug (the same requests pass deterministically in-process under TestClient). Re-smoke the
  live endpoints once the background pytest run finishes.
- **Pattern dimension semantics (J-77):** an observation flagged for two patterns (e.g. vcp + flat_base)
  appears under BOTH (regime, setup, pattern) combinations, and one with no flagged pattern appears under
  the `none` sentinel. The samples drill-down reproduces this exact membership, so count-coherence holds.
- **Out of scope (unchanged):** canonical scores/buckets/setups/patterns/regime labels (read verbatim;
  J-72 byte-identical); any new forward-return computation; a new nav section / second samples page;
  J-22/J-23/J-24 (data-walled, no code change); J-44 toggle-off-persistence debt (carried).
