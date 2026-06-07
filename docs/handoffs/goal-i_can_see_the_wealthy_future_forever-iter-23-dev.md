# goal-i_can_see_the_wealthy_future_forever-iter-23 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-23
**Date:** 2026-06-07
**Agent:** developer
**Status:** complete

## What Was Built

J-35 — the **Expand-universe** job kind, end-to-end (backend + frontend), additive on the existing `/data` Data Manager. The operator can grow the scored universe from the committed ~548-name candidate pool by running an expand job over a market-cap-capable source; the screen runs as a chunked/resumable import (reusing the J-34 engine), and the job card shows passers + every omitted candidate with its reason. Ineligible (`supports_market_cap: false`) sources are rejected at the UI and the backend.

- **New `expand` job kind** (`JOB_KINDS` + `JobCreate.kind` Literal). Unknown kind still → 422.
- **Expand orchestration** in `app/engine/data_manager.py` (one branch in the existing `_run_job`, no parallel module): reads the committed pool `data/seed/universe_pool.csv`; runs the **reused J-34 chunked/resumable OHLCV fetch** over the **pool symbols** (the one substitution); then a screen step reads the stored bars, fetches a **real market-cap reference** per candidate, applies the **single** `screen_reasons` predicate, and writes only passers to `universe.json` + per-symbol CSVs + `meta.json`, recording every omission with its reason.
- **Market-cap-reference capability** added to the `PriceProvider` abstraction (`get_market_cap(symbol) -> float | None`); base raises (gates expand out of non-capable providers), implemented for real on yahoo (quote endpoint), tiingo (fundamentals), finnhub (basic-financials, $M→USD). `get_daily` is unchanged for every other journey.
- **Expand-eligibility gate** (backend) in `validate_job_request`: an expand whose `source` has `supports_market_cap: false` → explicit `ValueError` → 400; a needs-key expand source with no env/pasted key → the existing J-33 key rejection.
- **`screen_reasons` re-homed** into `app/engine/universe_screen.py` as the **single** definition; `scripts/screen_universe.py` re-exports it (the long-standing `from scripts.screen_universe import screen_reasons` and `tests/test_universe_screen.py` keep working — one definition, two importers).
- **Grown-universe single-source resolution** (the load-bearing decision — see below): `load_config()` (default config only) merges committed `universe.json` members into `universe.symbols` + `stock_sectors`, so `/api/data universe_count == /methodology resolved_size == len(config.universe.symbols)` holds by construction and an expand write flows into the Coverage `universe-count`.
- **Progress + summary**: `passers`, `omitted_total`, and a bounded `omitted` `[{symbol, reason}]` on `JobProgress.to_dict()` (served by `GET /api/data/jobs/{id}`); the expand screen outcome on the append-only `DataProviderRun` audit row + the run-history reader.
- **Frontend** (`/data` only, additive): Expand option in the job-kind selector; ineligible sources disabled with a plain-language reason; the passers + omitted-with-reason block on the existing job card; the Coverage `universe-count` reflects the grown universe.
- **Carry-over RED fix**: `tests/test_db.py::test_create_all_produces_expected_tables` now includes `import_checkpoints`.

## Key design decision — grown-universe single source (recorded per the plan)

`config.universe.symbols` is loaded from `config.yaml`; both `/data universe_count` and `/methodology` size read `len(cfg.universe.symbols)`, so they are already single-source — but the source was the YAML list, which `universe.json` did not feed. **Resolution:** `load_config()` (DEFAULT config only — alternate/inline test configs untouched) merges the committed `universe.json` members into `universe.symbols` as a **UNION** with the YAML base (`base ∪ screened passers`), and merges each new member's `sector` into `stock_sectors`. The union (not a replace) is deliberate: the config `themes` / `stock_sectors` reference existing universe names, and a pure replace would drop a committed themed name out from under its theme and break boot validation — the union grows the universe from the screen while keeping the config self-consistent for **any** artifact content. `universe.json` thus becomes the one canonical membership artifact both surfaces already read, satisfying the J-22 invariant by construction (proved by value in `test_merge_committed_universe_makes_universe_json_the_single_source`). Today `universe.json` does not exist on this host (live screen egress is walled), so the merge is a no-op and `universe_count` is the YAML 122 — an expand that passes members would grow it.

## Files Changed

- `apps/backend/app/engine/data_manager.py` — `expand` in `JOB_KINDS` + `_EXPAND_KINDS`; expand branch in `_run_job` (pool → reused chunked fetch → market-cap fetch → `screen_reasons` → write `universe.json`/CSVs/`meta.json`); `_run_expand_screen` / `_screen_one_candidate` / `_write_expand_artifacts` / `_write_universe_csv`; eligibility gate in `validate_job_request`; `passers`/`omitted_total`/`omitted` on `JobProgress`+`to_dict()`; expand in `_final_status`/`_final_summary`/`_provider_label`/`_persist_run`/`summarize_provider_run`; `seed_dir` threaded through `_run_job`/`run_data_job`/`resume_data_job` (injectable for tests); deferred checkpoint-finalize for expand (a cap-feed pause leaves the durable checkpoint `resumable`).
- `apps/backend/app/api/data.py` — `JobCreate.kind` gains `"expand"` (the existing `ValueError`→400 mapping surfaces the eligibility/key rejections; unknown kind still 422 via the typed model).
- `apps/backend/app/engine/universe_screen.py` — **new**: the single `screen_reasons` definition + `read_pool`.
- `apps/backend/scripts/screen_universe.py` — imports + re-exports `screen_reasons` from the new module (duplicate definition removed).
- `apps/backend/app/data_providers/base.py` — `PriceProvider.get_market_cap` capability hook (base raises).
- `apps/backend/app/data_providers/yahoo_provider.py` / `tiingo_provider.py` / `finnhub_provider.py` — real `get_market_cap` implementations (real data or raise; never fabricate).
- `apps/backend/app/config.py` — `_merge_committed_universe` (default-config-only `universe.json` → `universe.symbols`/`stock_sectors` union); optional `UniverseFilters.adv_window_days` (default 63, validated positive) so the ADV window is config-driven without a new required key.
- `apps/frontend/lib/api.ts` — `DataJobKind` += `"expand"`; `ExpandOmission` type; `DataJob` gains `passers`/`omitted_total`/`omitted`; `DataRun` gains `passers`/`omitted_total`.
- `apps/frontend/app/data/page.tsx` — Expand option in the job-kind `<select>`; ineligible-source disabling + inline reason; Start guarded for an ineligible expand; the `ExpandScreenResult` block (passers + omitted-with-reason) on the job card.
- `apps/backend/tests/test_db.py` — `import_checkpoints` added to the expected-tables set.
- `apps/backend/tests/test_data_manager.py` — expand happy/omit/no-fabrication/single-screen-source/idempotency-immutability/eligibility/needs-key/resumable/key-safety tests + the merge single-source + no-op tests.
- `apps/backend/tests/test_api_data.py` — expand kind accepted; expand-over-ineligible 400; needs-key expand 400; `supports_market_cap` exposed; expand job-status shape (passers + omitted).
- `apps/backend/tests/test_provider_clients.py` — `get_market_cap` tests (base raises; yahoo/tiingo/finnhub real value, absent→None, no-key raises, $M→USD scaling).

## Tests Run

Command (targeted selections — the full ~20-min suite is deferred to the QA regression gate per the interactive-dispatch operational constraint):

`cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py tests/test_api_data.py tests/test_db.py tests/test_universe_screen.py tests/test_provider_clients.py tests/test_config.py tests/test_config_engine.py -q`

Result: **168 passed, 3 skipped** (the 3 skips are `test_universe_screen.py`'s `universe.json`-absent skips — expected; that artifact is produced by a live screen, which is walled here).

Also ran `tests/test_sectors.py tests/test_themes.py` (86 passed) to confirm the config changes don't break the theme/sector engines.

Frontend: `npx tsc --noEmit` → clean (exit 0).

The FULL backend `pytest tests/` regression gate is **deferred to the QA stage** (per the dispatch operational constraint — a single foreground command is capped at ~10 min and the full suite is ~20 min; I ran targeted selections that finish well within the cap and cover every file I touched plus the directly-related engines).

## Pre-handoff verification

- **Service startup**: backend booted live on :8835 (full seed loaded) — `/api/health` 200, `/api/data` serves `universe_count: 122` + the `supports_market_cap` flags `{yahoo:T, tiingo:T, finnhub:T, alpha_vantage:F, stooq:F}`; `POST /api/data/jobs` expand-over-stooq → 400 (clear reason), unknown kind → 422, expand-over-yahoo → started. Frontend dev server started clean on :3835 — `/data` HTTP 200 and `/_next/static/chunks/main-app.js` 200 (a healthy hydrated shell, not the dead-shell failure mode). Both servers stopped and ports freed afterward (killed by port, never a broad pkill — multi-project machine).
- **External integration (live market-cap fetch)**: NOT exercised live — Yahoo/Stooq/Tiingo market-cap egress is externally walled for this host (MEMORY: data-provider-access-constraints; the iter-22 handoff). Per the goal's non-halting contract the expand **machinery is offline-provable with an injected provider** (the unit/integration tests do exactly this), and the **live** market-cap-expansion outcome is recorded honestly (a walled feed → every candidate omitted / a `resumable` pause, no fabricated member) — it does NOT halt the loop. See Known Issues.
- **Native deps**: none added (no `playwright install`/native compile step).

## Known Issues

- **Live market-cap expansion is data-gated (non-halting).** A real expand over yahoo/tiingo/finnhub on this host hits the walled market-cap egress, so the live outcome is NA / rate-limited (every candidate omitted with a `market_cap_fetch_failed`/`no_market_cap` reason, or a graceful `resumable` pause). This is recorded honestly and MUST NOT be treated as a code FAIL — the offline-provable injected-provider steps are the acceptance (per the spec's iter-7/8 lesson). Because the feed is walled, **no `universe.json` is produced on this host**, so `universe_count` stays at the YAML 122; an expand that passes members (e.g. via an injected provider in test, or a reachable feed) grows it through the documented single-source merge.
- **`universe.json` member shape**: the expand writer matches the offline `screen_universe.screen()` member/omitted record shape (symbol/sector/source/market_cap/reference_close/adv_dollar/bars/first/last; omitted: symbol/reason) so the two writers are interchangeable. The expand writer's `window` records `{asof}` (the resolved as-of) rather than the offline writer's `{start, end}` — both are descriptive metadata, not consumed by the read path.
- **ADV window** is now config-driven via the OPTIONAL `universe.filters.adv_window_days` (default 63 = the offline screen's documented `ADV_WINDOW`); optional so the 4 inline config fixtures need no new required key (MEMORY: config-fixtures-need-new-required-keys).
