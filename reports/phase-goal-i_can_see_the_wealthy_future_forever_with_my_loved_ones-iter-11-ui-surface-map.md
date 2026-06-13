# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-11
**Date:** 2026-06-13
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/sectors` | Expanded ETF row panel — header name | Changed behavior | Industry ETFs now display a config name instead of the bare ticker | Expand any industry ETF row (e.g. SMH); confirm the panel header reads a name like "Semiconductors (VanEck)" and NOT just "SMH" |
| `/sectors` | Expanded ETF row panel — description line | New component | Industry ETFs now have a one-line plain-language description from config | Expand SMH; confirm a description paragraph appears below the ticker/name header; expand XLK (sector ETF with null description); confirm no description line and no crash |
| `/sectors` | Expanded ETF row panel — member chip list (sector ETFs) | New component | Sector ETFs now list their universe members (stocks mapped via `stock_sectors`) | Expand XLK; confirm ticker chips appear for Technology-sector stocks; confirm each chip has `data-testid="sector-member-link"` and clicking one opens the stock's detail page in a new browser tab |
| `/sectors` | Expanded ETF row panel — member chip list (industry ETFs) | New component | Industry ETFs now list their universe members (stocks mapped via `stock_industries` config) | Expand SMH; confirm member chips include NVDA, AMD and others; confirm the section header reads "Members (config-defined)" |
| `/sectors` | Expanded ETF row panel — "+N" member expand/collapse toggle | New component | When more than 6 members exist, a "+N" button reveals all remaining members | Expand XLK (which has >6 sector members); confirm only 6 chips show initially; click the "+N" button (`data-testid="sector-members-toggle"`); confirm all members appear; click "Show fewer"; confirm list collapses back to 6 |
| `/sectors` | Expanded ETF row panel — zero-member empty state | New component | ETFs with no mapped universe stocks must show an explicit message, never fabricated names | Expand KRE ("Regional Banks (SPDR)"); confirm the panel shows "No universe members are mapped to this ETF (config-defined)." (`data-testid="sector-members-empty"`) and zero ticker chips |
| `/sectors` | Member chip href under historical as-of | Changed behavior | Member chip links must carry `?asof=<date>` when the user is viewing a historical snapshot | Set the global as-of control to a past date; expand any sector ETF row with members; click a member chip; confirm the new tab opens the stock detail URL containing `?asof=<date>` |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/config.py` — adds `IndustryETFEntry` Pydantic model and `_stock_industries_valid` validator; raises explicit `ConfigError` on malformed entries. Validation runs at startup; the error surfaces as a startup failure, not a UI element. No new UI surface.
- `apps/backend/app/engine/sectors.py` — reads name/description from catalog and resolves member lists. Drives data that surfaces on `/sectors` via the existing API — classified as indirect-API, not a new UI surface.
- `apps/backend/app/models.py` — adds `description` and `members_json` columns to `SectorScoreRow`. Database schema change; no direct UI surface.
- `apps/backend/app/engine/scanner.py` — persists `description` and `members_json` into the immutable snapshot row. No direct UI surface.
- `apps/backend/app/engine/snapshot_serving.py` — `_sector_row` echoes `description` + `members` from the stored row into the `GET /api/sectors` response. The frontend already consumes `GET /api/sectors`; the new fields are therefore rendered by `app/sectors/page.tsx`.
- `apps/backend/app/seed_loader.py` — `add_etf` gains an optional `name` parameter; industry ETFs are seeded with their config display name. Internal seeding; no direct UI surface.
- `config.yaml` — `etfs.industry` converted to a `ticker -> {name, description}` catalog; new `stock_industries` section added. Config-only; UI reads names/descriptions via the API response.

---

## Summary

- **Frontend surfaces changed:** 1 page (`/sectors`)
- **New pages/routes:** 0
- **Modified components:** 1 (`app/sectors/page.tsx` — expanded panel gains description + member list)
- **Navigation changes:** no
- **Backend-only changes:** 6 (config, validator, engine, model, scanner, snapshot_serving, seed_loader — all feed into the existing `/api/sectors` endpoint consumed by the single changed frontend page)
