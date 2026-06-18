# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32
**Date:** 2026-06-18
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|-------------|--------------|
| `/research` | `DowntrendOpportunityLab` (entire section) | New component | J-91 adds a downtrend-conditioned opportunity study over stored evidence | Scroll below the Recovery-Turn Edge lab and confirm the "Downtrend Opportunity" section heading is visible with three table panels rendered |
| `/research` | `DowntrendDimensionSelector` (Condition on dropdown) | New component | J-91 conditioning controls — lets user pick Phase, Severity band, or P(bear) band | Select "Severity band" from the "Condition on" dropdown and verify the three tables update their row cohort labels to severity-band names |
| `/research` | `DowntrendAngleTable` — "Held up best" | New component | J-91 shows best forward-return cohorts under downtrend conditions | Confirm the "Held up best" table has column headers (Cohort, n, Mean, Hit-rate, Ret/DD, Mean MDD) and that clicking the "Mean" header re-sorts rows without a page reload |
| `/research` | `DowntrendAngleTable` — "Fell hardest" | New component | J-91 shows worst forward-return cohorts — evidence only, no execution | Confirm the "Fell hardest" table carries the "Research evidence only" label and has no Buy/Sell/Trade button or link anywhere in or adjacent to the table |
| `/research` | `DowntrendRecoveryAngle` — "Recovery-turn edge by phase" | New component | J-91 reuses the Recovery-Turn Edge study in the same panel | Confirm the third panel header reads "Recovery-turn edge by phase" and its row counts match the standalone Recovery-Turn Edge lab above it for the same horizon |
| `/research` | `N=` chip (SampleLink) on each downtrend table row | New component | J-91 count-coherent drill-down — opens samples in a new tab | Click the `N=` chip on any row in the "Held up best" table; confirm a new tab opens at `/research/samples` and the count shown on that page matches the `n` value in the chip label |
| `/research` | Episodes / Pooled toggle (shared, reused in downtrend lab) | Changed behavior | J-91 downtrend lab reads the shared Episodes/Pooled toggle | While viewing the Downtrend Opportunity section, switch from Episodes to Pooled; confirm table row counts change without affecting the existing labs above |
| `/research` | `MacroPublicationLagLabel` | New component | J-92 discloses the publication-lag contract and default-off macro state | Confirm a label is visible in the Downtrend Opportunity lab stating that macro inputs are optional, off by default, and that macro values are only used once published on or before the data date |
| `/research/samples` | Drill-down cohort header for `downtrend-opportunity` kind | Changed behavior | J-91 adds a new cohort kind — the drill-down page must describe it | Navigate to `/research/samples` via a downtrend-opportunity `N=` chip and confirm the cohort header identifies the conditioning dimension (e.g., "Downtrend opportunity — Phase: Bear") rather than showing a blank or generic header |
| `/data` | `MacroFeedPanel` | New component | J-92 surfaces the FRED macro provider catalog | On the Data Manager page, scroll past the missing-data diagnostic and confirm a "Macro feed" panel appears listing at least four series rows in a table with columns for FRED id, publication lag, proxy, and status |
| `/data` | `MacroFeedPanel` — live-key status indicator | New component | J-92 shows env-var detection status (name only, never value) | Confirm the macro panel shows the env-var NAME (e.g., `FRED_API_KEY`) next to a "not set (NA)" or "detected" status, with no actual key value displayed anywhere on the page |
| `/data` | `MacroFeedPanel` — per-leg enable flags | New component | J-92 shows which wiring legs (severity/regime/study) are on or off | Confirm the three enable flags (severity, regime switching, study) all show "off" in the default configuration |
| `/data` | `MacroFeedPanel` — default-off note | New component | J-92 makes the default-unchanged state explicit | Confirm a note is visible in the macro panel stating that default figures are unchanged while all legs are off |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` — `compute_downtrend_opportunity_study` logic (observation tagging, three-angle ranking) — the computed data is surfaced via the frontend, not backend-only; listed here to note the computation itself is not user-visible, only its output via the API and UI.
- `apps/backend/app/engine/samples.py` — `KIND_DOWNTREND_OPPORTUNITY` dispatch and `_downtrend_opportunity_samples` builder — consumed by `GET /api/research/samples` which is already wired to the frontend drill-down; no standalone UI impact.
- `apps/backend/app/engine/market_phase.py` — `phase_context_by_date` / `_causal_timeline` accessor and J-92 optional macro legs in `_severity_reading` and `_regime_switching_observation` — the macro legs are off by default; no served figure changes.
- `apps/backend/app/data_providers/fred_provider.py` (new) — FRED macro provider implementation — no UI affordance to trigger a live fetch this iteration; the `/data` panel is read-only catalog.
- `apps/backend/app/models.py` — new `MacroSeries` standalone table — database schema addition with no direct UI rendering.
- `apps/backend/app/config.py` — `ConditioningBand`, `DowntrendOpportunityCfg`, `MacroSeriesCfg`, `MacroEnableCfg`, `MacroCfg` typed config classes — config-layer; no user-visible change until legs are enabled.
- `apps/backend/app/seed_loader.py` — `load_macro_seed` + macro proxies added to `all_seed_symbols` — data loading; no UI impact.
- `apps/backend/data/seed/macro/*.csv`, `data/seed/prices/_TNX.csv/_DXY.csv/_VXN.csv` (new seed files) — committed offline seed data; no UI impact.
- `apps/backend/tests/test_research.py`, `test_market_phase.py`, `test_db.py`, `test_config.py` — test additions — no UI impact.
- `apps/frontend/lib/api.ts` — `DowntrendOpportunityRow`/`DowntrendOpportunityResponse` types and `fetchDowntrendOpportunity` — API client layer consumed by the frontend; the change is only observable via rendered UI components listed above.
- `apps/frontend/lib/samples-link.ts` — `DowntrentOpportunityCohortParams` and `buildSamplesHref` branch — serialization helper consumed by the `N=` chip components listed above; not independently visible.
- `config.yaml` — `research.downtrend_opportunity` band catalog and `macro` block — config file; user-visible only via the Data Manager's macro panel and the conditioning controls (both listed above).

---

## Summary

- **Frontend surfaces changed:** 13
- **New pages/routes:** 0 (existing `/research`, `/research/samples`, and `/data` pages modified)
- **Modified components:** 13 (5 new lab components on `/research`, 1 cohort-header addition on `/research/samples`, 4 new macro panel components on `/data`, plus 1 shared toggle behavioral extension)
- **Navigation changes:** no (no new top-level nav links; the Downtrend Opportunity lab and macro panel are scroll-reachable within existing pages)
- **Backend-only changes:** 12 (engine logic, data models, providers, seed data, tests, config, and API client types that are not independently visible to users)
