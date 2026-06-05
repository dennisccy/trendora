# Phase goal-i_can_see_the_wealthy_future_forever-iter-21 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-21 (J-33 — Import source picker)
**Date:** 2026-06-05
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `JobForm` — **Import source** `<select>` (`aria-label="Import source"`) | New form field | J-33 makes the import provider user-selectable, config-driven | Set Job kind to "Fetch EOD prices"; confirm the Import source dropdown appears and lists Yahoo, Tiingo, Finnhub, Alpha Vantage, Stooq, each suffixed with "· available" or "· needs key". (Use native-setter + bubbling `change` per MEMORY `react-controlled-select-needs-native-setter`, then assert live DOM.) |
| `/data` | `JobForm` — Import source visibility toggle | Changed behavior | Picker shows only for fetch-type jobs | Set Job kind to "Backfill snapshots" and confirm the Import source dropdown and key field are absent; switch to "Fetch EOD prices" or "Fetch + backfill" and confirm the dropdown appears. |
| `/data` | `JobForm` — availability line (`data-testid="source-availability"`) | New component | J-33 surfaces per-source availability + reason from `GET /api/data` | Select Yahoo and confirm the line reads label + "available" + reason; select Tiingo (no env key) and confirm it reads "needs key" + a reason like "set $TIINGO_API_KEY or paste a session key". |
| `/data` | `JobForm` — **Session API key** field (`type="password"`, `aria-label="Session API key"`) | New form field | J-33 lets users paste a session-only key for a key-required source | Select a needs-key source with no env key (e.g. Tiingo); confirm a masked password field appears with the "held in memory for this run only…" caption. Select an available source and confirm the field disappears. |
| `/data` | `JobForm` — start a fetch against an unavailable provider | Changed behavior | J-33 must surface explicit error, never fabricate | Select a source and start a fetch while the provider is walled; confirm the Job progress card shows a failed/partial status with an error list and "(no data fabricated)", and the run history records the run without any key value. |
| `/data` | `JobProgressPanel` — header hint | Updated layout | Header now echoes the chosen source id | Start a fetch with Yahoo selected; confirm the Job progress card header shows the source id (e.g. `fetch job · yahoo · <start> → <end>`) and never shows any pasted key. |
| `/data` | `JobForm` — needs-key fetch with no key | Changed behavior | Up-front rejection instead of silent no-op | Select a needs-key source, leave the key blank, and start a fetch; confirm an inline error (`role="alert"`) appears explaining a key is required, and no job starts. |
| `/data` | `JobForm` — default source | Changed behavior | J-17 fetch preserved when no source picked | Start a fetch without changing the pre-selected source; confirm it runs against the default (Yahoo) and behaves like the prior fetch. |
| `/data` | `DataManagerPage` — page subtitle | Changed text | Opportunistic fix of stale iter-17 wording | Confirm the subtitle reads "…grow the Backtest evidence" and no longer says "System Health evidence". |
| `/data` (app-wide) | Date controls — **J-18 regression check** | No change (must verify) | New source/key controls must add NO date state | Confirm exactly one date `<select>` exists app-wide (the global header as-of switcher); the `/data` Start/End inputs remain `type="date"` job parameters and the Import source / Job kind selects are not date controls. |

---

## Backend-Only Changes (No UI Impact)

- `config.yaml` + `apps/backend/app/config.py` (`ProviderCatalogEntry`, `DataManagerCfg.providers`/`default_source`, boot validation) — defines the config-driven catalog and validates it at boot; surfaced to the UI only via the `sources` field, not directly.
- `apps/backend/app/data_providers/_http.py`, `yahoo_provider.py`, `tiingo_provider.py`, `finnhub_provider.py`, `alpha_vantage_provider.py`, `__init__.py` (`make_provider` resolving every catalog id + `api_key`) — new/extended provider clients; exercised only when a live fetch runs, no direct UI surface.
- `apps/backend/app/engine/data_manager.py` (`compute_provider_availability`, `resolve_provider_key`, source/api_key threading, `_provider_label`) — computes the availability metadata the UI renders and threads the session-only key; the key itself is never returned to the UI.
- `apps/backend/app/api/data.py` (`JobCreate.source/api_key`, `sources` in `GET /api/data`, 400 gates, source echoed) — the API contract the picker consumes; the new `sources` array is the only user-visible product, and the key is never echoed.
- `apps/frontend/lib/api.ts` (`ProviderSource` type, `sources` on `DataOverviewResponse`, `startDataJob` opts) — typed client wiring with no standalone surface.
- `apps/frontend/next.config.mjs` (`NEXT_DIST_DIR` override) — build tooling only; no runtime UI impact.
- Test files (`test_provider_clients.py` and extended config/data-manager/api/sectors/themes tests) — no UI impact.

---

## Summary

- **Frontend surfaces changed:** 1 page (`/data`), with 5+ distinct element changes in `JobForm` / `JobProgressPanel`
- **New pages/routes:** 0 (additive to the existing Data Manager home; no nav change)
- **Modified components:** `JobForm` (Import source select, availability line, session key field), `JobProgressPanel` (source in header), `DataManagerPage` (subtitle)
- **Navigation changes:** no
- **Backend-only changes:** 7 backend file groups + client typing + config/build + tests
