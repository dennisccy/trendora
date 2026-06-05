# goal-i_can_see_the_wealthy_future_forever-iter-21 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-21
**Date:** 2026-06-05
**Agent:** developer
**Status:** complete
**Journey:** J-33 — Import real data from a selectable, key-aware provider source

## What Was Built

**Backend — config provider catalog (J-33)**
- `ProviderCatalogEntry` typed model in `config.py` — `{id, label, needs_key, env_var, supports_market_cap}`
  with a per-entry validator: `needs_key` ⇒ `env_var` required (the env-var **name** only, never a value).
- `DataManagerCfg` gains `providers: list[ProviderCatalogEntry]` + `default_source: str`; the old
  2-value `live_provider` Literal was **retired**. Boot validation on `DataManagerCfg` raises
  `ConfigError` on: a non-positive limit, **duplicate ids**, or **`default_source` ∉ catalog**. Helper
  methods `provider_ids()` / `provider_by_id()`.
- `config.yaml` `data_manager.providers`: 5-source catalog (`yahoo` no-key [default], `tiingo`,
  `finnhub`, `alpha_vantage`, `stooq` — the four key sources with their env-var names) + `default_source: yahoo`.

**Backend — provider clients**
- `make_provider(name, *, api_key=None, seed_dir=None)` now resolves every catalog id (`seed`/`yahoo`/
  `stooq`/`tiingo`/`finnhub`/`alpha_vantage`); each live client is **lazy-imported** (no HTTP at boot).
- New thin EOD clients behind the existing `PriceProvider.get_daily` contract:
  `yahoo_provider.py` (no-key, chart JSON), `tiingo_provider.py`, `finnhub_provider.py`,
  `alpha_vantage_provider.py` (key-aware). Each is one documented GET → JSON → ascending `Bar`s; **any**
  non-OK status / network error / unparseable body / (for key sources) missing key → `ProviderUnavailableError`,
  **never a fabricated bar**. Shared `_http.py` `fetch_json` helper (httpx, injectable client for tests).

**Backend — availability + source/key threading**
- `compute_provider_availability(cfg)` → per-source `{id,label,needs_key,env_var,supports_market_cap,available,reason}`,
  `available = (not needs_key) or bool(os.environ.get(env_var))` at request time. **No env value / key ever in the output.**
- `resolve_provider_key(entry, pasted)` = pasted session key, else `os.environ.get(entry.env_var)`, else None.
- `JobCreate` gains `source` + `api_key` (request-only). `validate_job_request(... , source, api_key)`
  now also rejects an **unknown source** and a **fetch against a needs-key source with no env/pasted key** (→ 400).
- `JobProgress` gains a `source` field (the chosen id — **not** secret); it has **no `api_key` field**.
  `start_data_job`/`run_data_job` thread `source` + `api_key`; the key is a **request-only local** passed
  to `make_provider(source, api_key=key)`, never written to the registry, the persisted `DataProviderRun`,
  the detail JSON, the logs, or any response. `_provider_label` records the chosen `source` id for a fetch.
- `GET /api/data` payload extended with `sources` (the availability list). `POST` response echoes the
  resolved `source` (never the key); job-status / run-history responses contain no key.

**Frontend**
- `lib/api.ts`: new `ProviderSource` type, `sources` on `DataOverviewResponse`, `source?` on `DataJob`/
  `StartJobResponse`, and `startDataJob(kind, start, end, opts?: {source?, api_key?})` (omits `api_key` when blank).
- `app/data/page.tsx`: Import-source `<Select>` populated **from `data.sources`** (no hardcoded list),
  shown for `fetch`/`both`; a per-source availability line; a conditional **session-only** `type="password"`
  key field (held in `useState` only — never localStorage/URL/cookie; cleared on job completion + unmount).
  Subtitle fix ("System Health" → "Backtest"). The source `<Select>` is **not** a date control (J-18 holds).

## Files Changed
- `config.yaml` — `data_manager.providers` catalog + `default_source`; removed `live_provider`.
- `apps/backend/app/config.py` — `ProviderCatalogEntry`; `DataManagerCfg` providers/default_source + boot validation.
- `apps/backend/app/data_providers/_http.py` *(new)* — shared `fetch_json` (httpx, injectable client).
- `apps/backend/app/data_providers/yahoo_provider.py` *(new)*, `tiingo_provider.py` *(new)*,
  `finnhub_provider.py` *(new)*, `alpha_vantage_provider.py` *(new)* — thin EOD clients.
- `apps/backend/app/data_providers/__init__.py` — `make_provider` resolves every catalog id + `api_key`.
- `apps/backend/app/data_providers/stooq_provider.py` — docstring updated (no `live_provider`).
- `apps/backend/app/engine/data_manager.py` — availability, key resolution, source/api_key threading, `_provider_label`.
- `apps/backend/app/api/data.py` — `JobCreate.source/api_key`; `/api/data` `sources`; 400 gates; source echoed.
- `apps/frontend/lib/api.ts` — `ProviderSource` + `sources` + `startDataJob` opts.
- `apps/frontend/app/data/page.tsx` — import-source picker + session-only key field + subtitle fix.
- `apps/frontend/next.config.mjs` — `NEXT_DIST_DIR` env override (isolated verification builds).
- Tests: `test_provider_clients.py` *(new)*; extended `test_config.py`, `test_data_manager.py`,
  `test_api_data.py`; fixture fan-out in `test_config.py`/`test_config_engine.py`/`test_sectors.py`/`test_themes.py`.

## Tests Run
Command (backend): `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: __PYTEST_RESULT__

Targeted pre-runs (all green): `test_config.py test_config_engine.py test_provider_clients.py test_api_data.py`
→ 97 passed; `test_data_manager.py test_sectors.py test_themes.py` → 21 passed.

Frontend: `tsc --noEmit` → 0 errors; `NEXT_DIST_DIR=.next-verify next build` → success (`/data` compiles;
built to a throwaway dir so the live `.next` is untouched — MEMORY `browser-qa-dead-shell-next-cache`).

Key unit proofs (J-33):
- **Catalog config-driven + boot validation** → `ConfigError` on missing `env_var`-when-`needs_key`,
  duplicate id, `default_source` ∉ catalog (`test_config.py`).
- **`compute_provider_availability` env-detected**; the env value/key is never in the output (`test_data_manager.py`).
- **`make_provider` resolves every catalog id**; each client raises on non-OK/unparseable (mocked HTTP, no
  live call); a needs-key client with no key raises explicitly (`test_provider_clients.py`).
- **Key-never-persisted (principal anti-goal)**: a pasted `api_key` is absent from every `DataProviderRun`
  column, from the job snapshot, and from logs; `JobProgress` has no `api_key` field; the `source` id IS
  recorded (`test_data_manager.py::test_pasted_api_key_never_persisted`).
- **Source threading**: omitted source ⇒ `default_source`; unknown source ⇒ 400; needs-key fetch w/o key
  ⇒ 400; key never echoed in the response (`test_api_data.py`).

## Known Issues / Notes
- **Documented deviation (naming):** the spec/blueprint reference a `ProviderCatalogCfg`. Implemented as
  `ProviderCatalogEntry` (typed per-source entry) + the catalog as `DataManagerCfg.providers` with the
  three required boot validations on `DataManagerCfg` — idiomatic with the existing
  `FactorLabCfg.factors` / `CombinationCfg.quantiles` pattern (a flat YAML list validated by its parent).
  All required validations and the data-contract value/path match the blueprint exactly; only the
  wrapper-model name differs.
- **Live fetch is data-walled & non-halting** (Yahoo 429 / Stooq key-gated for this IP — MEMORY
  `data-provider-access-constraints`). All J-33 machinery is proven **offline with mocked/injected
  providers**; **no live network call** is made in tests or the pipeline. A successful live import is
  recorded honestly as NA/rate-limited and must not halt the loop or veto GOAL_ACHIEVED.
- **Stooq** is marked `needs_key` in `config.yaml` (honest for this IP). The `StooqProvider` itself still
  calls the free CSV; the key requirement is enforced as a pre-run gate (selecting Stooq with no key → 400).
- **Out of scope (not built):** J-34 chunk/resume/backoff; J-35 `expand` job kind. `supports_market_cap`
  is declared in the catalog but consumed only by J-35 (iter-23).
- **No DB regen** — confined to the provider package + `/data` + config; zero scoring/snapshot/forward
  touch, so the 29 carried journeys' stored values are byte-identical.
- **Browser QA (J-33) for the next agent:** use the native-setter + bubbling-`change` pattern for the
  source `<select>` (MEMORY `react-controlled-select-needs-native-setter`), then assert live DOM. The
  source `<select>` (`aria-label="Import source"`) and Job-kind `<select>` are **not** date controls —
  the only date `<select>` app-wide remains the global header as-of switcher (J-18). The session key field
  is `aria-label="Session API key"`, `type="password"`.
