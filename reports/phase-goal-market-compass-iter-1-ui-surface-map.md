# Phase goal-market-compass-iter-1 — UI Surface Map

**Phase:** goal-market-compass-iter-1
**Date:** 2026-08-20
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/stocks` | Leaderboard **Sector** column cell (`sectorLabel(row.sector)`, `apps/frontend/app/stocks/page.tsx`) | Changed behavior (data completeness) | Backend fallback (curated `config.stock_sectors` map, then `universe_pool.csv`) now resolves sectors for names the curated map never covered | After running a fresh backfill covering the two most recent trading days (see the `/data` precondition test), navigate to `http://localhost:3255/stocks`, type `GRMN` into the "Search ticker or name…" box (`data-testid="stocks-search"`), and confirm the Sector cell in the GRMN row reads `Consumer Discretionary` instead of `Unassigned`. Then search `DELL` and confirm its Sector cell still reads `Technology` (curated map unchanged). |
| `/stocks` | **Sector** filter dropdown (`aria-label="Filter by sector"`, same file) | Changed behavior (data completeness) | Same underlying fix shrinks the "Unassigned" bucket and broadens the real-sector options in the dropdown | Open the "Sector" dropdown, select `Unassigned`, and read the `data-testid="visible-count"` badge. Live baseline measured while writing this report (pre-fallback, 2026-08-14 run): `424 / 541`. After a fresh backfill, confirm the first number is **at most 5%** of the total (per TC-1) — a material drop from today's 78.4%. |
| `/stocks/{ticker}` | Stock detail header sector text (plain span next to the setup-status badge, `apps/frontend/app/stocks/[ticker]/page.tsx`) | Changed behavior (data completeness) | Same stored field, same `sectorLabel()` rendering helper, simply populated more often | Navigate to `http://localhost:3255/stocks/GRMN` after the backfill and confirm the small text next to the setup-status badge reads `Consumer Discretionary` (was `Unassigned`). Navigate to `http://localhost:3255/stocks/DELL` and confirm it still reads `Technology`. Cross-check both against `GET http://localhost:8255/api/stocks/{ticker}`'s `"sector"` field — all three surfaces (leaderboard cell, detail header, API) must agree (TC-2). |
| `/methodology` | `UniverseSelectionCard` → new "Stock sector labels" subsection (`data-testid="universe-sector-basis"`, "Data basis" badge, `apps/frontend/app/methodology/page.tsx`) | New content (existing card, new subsection) | Discloses the two-source sector basis (curated first, pool-CSV fallback second) and the current-only limitation (B-114 referenced as open), served from `config.yaml`'s `methodology.universe_selection.sector_basis` via `GET /api/methodology` | Navigate to `http://localhost:3255/methodology`. **Environment caveat, confirmed live**: the whole parent "Universe Selection" card (`data-testid="universe-selection"`) is absent today — `GET http://localhost:8255/api/methodology` currently omits the `universe_selection` key entirely because the pre-existing, unrelated gate `apps/backend/data/seed/universe.json` does not exist in this repo. What IS testable today: confirm the rest of the page still renders cleanly (heading "Methodology", entries list, glossary) with no console error and no broken layout gap where the card would sit. If/when `universe.json` is later built (a separate, manual, out-of-scope job — no UI button triggers it), re-check that the subsection shows this exact text verbatim: "Each stock's sector label is resolved from two sources, in order: the curated `config.stock_sectors` mapping (Trendora's original universe) first, then — for any name the curated map does not cover — a fallback to the sector recorded in the committed candidate pool (universe_pool.csv). A name present in neither source serves no sector ('Unassigned') — never a fabricated value. Both sources describe the CURRENT sector only: there is no point-in-time sector history, so a stock's sector label at a historical as-of date reflects today's mapping, not necessarily what its sector was on that date (tracked open as backlog item B-114)." |

<!-- Change Type key used above: "Changed behavior" = same control/element, materially different data; "New content" = new subsection inside an existing, unchanged card. No new page, route, form, modal, or nav entry was added by this iteration. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/universe_screen.py` — new `resolve_pool_sector()` and `pool_sector_map()`
  functions beside the existing `read_pool()` reader — pure lookup/normalization helpers. They have no
  route or API of their own; their only externally observable effect is through the `/stocks` and
  `/stocks/{ticker}` rows above, via `scoring.score_stocks`.
- `apps/backend/app/engine/scoring.py` — the one-line `"sector"` field wiring
  (`cfg.stock_sectors.get(ticker) or pool_sectors.get(ticker)`) is itself backend-internal row-assembly
  logic; it is not a UI surface, only the data it produces is (covered by the `/stocks` rows above). No
  other field in this module's output changed — `Stock.sector_id`, `stock_sector_etf`, and every
  score/bucket/setup_status input remain byte-identical (TC-4).
- `apps/backend/app/config.py` → `UniverseCfg.pool_sector_aliases`, and `config.yaml` →
  `universe.pool_sector_aliases` — new config knob, defaults to `{}` (verified no-op today against the
  real committed pool — TC-6). No UI control reads or edits this value; it exists purely as a future
  normalization seam for a pool-CSV refresh with mismatched sector spelling.
- `apps/backend/app/engine/methodology.py::_universe_selection` — now includes `sector_basis` in its
  returned dict. This is the data-producing half of the `/methodology` row above; the function itself has
  no UI surface (it is consumed only through `GET /api/methodology`, which the `/methodology` row already
  covers).
- Test files (`apps/backend/tests/test_scoring.py`, `test_universe_screen.py`, `test_methodology.py`,
  `test_api_methodology.py`) — new/updated automated test coverage (`test_pool_sector_fallback_*`,
  `test_resolve_pool_sector_*`, `test_pool_sector_map_*`, `test_historical_row_sector_not_rewritten_by_pool_fallback`,
  `test_universe_selection_sector_basis_*`). Test infrastructure, not a UI surface.

---

## Summary

- **Frontend surfaces changed:** 2 (`/stocks` + `/stocks/{ticker}` — data-only, zero code diff;
  `/methodology` — code + new content, currently gated off in this environment)
- **New pages/routes:** 0
- **Modified components:** 1 (`UniverseSelectionCard` in `apps/frontend/app/methodology/page.tsx`), plus 1
  TypeScript interface extended (`UniverseSelection` in `apps/frontend/lib/api.ts` — a type definition, not
  a rendered component)
- **Navigation changes:** no
- **Backend-only changes:** 5 (listed above)
