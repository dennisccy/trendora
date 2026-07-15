# goal-mcp-loop-iter-38 — UI Surface Map

**Phase:** goal-mcp-loop-iter-38
**Date:** 2026-07-15
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/watchlist` | "Concentration X-ray" section container (`WatchlistXraySection`, `data-testid="watchlist-xray"`) | New component | J-23/B-204: new descriptive section disclosing watchlist concentration risk | With the real persistent watchlist (ABBV, MSFT — 2 entries), navigate to `/watchlist`, scroll below the existing entries table, and confirm a "Concentration X-ray" `Card` renders with the subtitle "Descriptive only — how correlated, clustered, and concentrated your watchlist really is. No recommendations." |
| `/watchlist` | Correlation matrix heatmap (`CorrelationHeatmap`, `data-testid="watchlist-xray-matrix"`) | New component | Pairwise return-correlation matrix, honest NA cells, zero browser-side recompute | On `/watchlist` with ABBV+MSFT, confirm a 2×2 grid renders with ABBV and MSFT as both row and column headers; hover the off-diagonal ABBV/MSFT cell (`data-testid="watchlist-xray-cell"`, `data-row="ABBV"` `data-col="MSFT"`) and confirm the cell text reads **"-0.11"** in red/negative (`text-neg`) styling, and its `title` tooltip reads "ABBV vs MSFT: -0.114 correlation over the trailing 126 trading days". |
| `/watchlist` | Correlation cell NA state (`data-testid="watchlist-xray-cell"` with `data-na="yes"`) | New component (state) | Undefined/insufficient-history pair must render honest NA, never a fabricated number | Add a ticker with under 60 trading days of price history to the watchlist alongside ABBV/MSFT, reload `/watchlist`, and confirm that new ticker's row/column cells render a muted "—" with a dashed border (`data-na="yes"`) rather than a numeric value; hover the cell and confirm the title states the exact day counts on each side versus the 60-day requirement. |
| `/watchlist` | Effective-independent-bets headline (`data-testid="watchlist-xray-enb"`) | New component | Headline "effective independent bets" figure + explicit trailing window | On `/watchlist` with ABBV+MSFT, confirm the text **"≈ 2.0"** appears immediately followed by "effective independent bets (over the last 126 trading days)". |
| `/watchlist` | ENB methodology info icon (`InfoTooltip`, accessible name "What is effective independent bets?") | New component | Explains the eigenvalue methodology and the honesty floor inline, next to the headline | Click the info icon next to the ENB headline on `/watchlist` and confirm a text panel opens explaining the figure is derived from eigenvalues of the correlation matrix over "the trailing 126 trading days" and that a name with under 60 days of overlapping history is excluded and shown as NA; click outside the panel and confirm it closes. |
| `/watchlist` | Cluster badges (`data-testid="watchlist-xray-clusters"`) | New component | Deterministic correlation-threshold grouping (connected components, no ML) | On `/watchlist` with ABBV+MSFT (correlation −0.114, below the 0.70 cluster threshold), confirm two separate single-ticker badges render ("ABBV" and "MSFT" each alone, `default` gray variant) rather than one joined "ABBV · MSFT" badge — the caption above reads "Names grouped when their correlation is at or above 0.70." |
| `/watchlist` | Sector concentration bars (`data-testid="watchlist-xray-sector"`) | New component | Sector-crowding disclosure with null-sector bucketing (iter-18/19 nullable-field lesson) | On `/watchlist` with ABBV+MSFT, confirm two bars render: "Technology" reading "1 · 50%" (MSFT) and "Unassigned" reading "1 · 50%" (ABBV, which has no `stock_sectors` mapping) — confirms the new consumer buckets the null sector rather than crashing or omitting it. |
| `/watchlist` | Theme concentration bars (`data-testid="watchlist-xray-theme"`) | New component | Multi-membership theme-crowding disclosure | On `/watchlist` with ABBV+MSFT, confirm three theme bars render, each reading "1 · 50%": the three themes MSFT belongs to in `config.yaml`'s `themes:` catalog (AI/data-centre, software/cloud, megacap leaders). Confirm ABBV — a member of none of those theme lists — contributes no bar of its own. |
| `/watchlist` | Shared-setup concentration bar (`data-testid="watchlist-xray-setup"`) | New component | Reuses the existing `setupVariant()` Badge coloring rather than a new color scale | On `/watchlist` with ABBV+MSFT (both currently classify "Avoid"), confirm a single bar renders reading "2 · 100%" with an "Avoid" badge colored in the same red/danger variant the entries table's own Setup column already uses for "Avoid" rows. |
| `/watchlist` | Insufficient-watchlist empty state (`EmptyState`, title "Not enough names yet for an X-ray") | New component (state) | Honest empty/insufficient state for a watchlist with fewer than 2 names | Remove entries (or use a fresh account) until the watchlist has 0 or 1 saved name, reload `/watchlist`, and confirm the X-ray section is replaced by an `EmptyState` titled "Not enough names yet for an X-ray" with body text starting "Add at least one more stock..." — confirm this wording is distinct from the zero-entries `EmptyState` ("Your watchlist is empty") shown when there are 0 saved names at all. |
| `/watchlist` (API contract) | `GET /api/watchlist` response shape | Changed behavior (additive) | New `xray` field computed once alongside the existing response; existing fields byte-identical | Call `GET /api/watchlist` directly (e.g. `curl http://localhost:<backend-port>/api/watchlist`) and confirm the JSON still has top-level `asof_date` (string) and `entries` (array) exactly as before, plus a new top-level `xray` object carrying `status`, `window_days`, `min_overlap_days`, `cluster_threshold`, `tickers`, `history_days`, `correlation_matrix`, `clusters`, `effective_number_of_bets`, `enb_member_count`, `sector_concentration`, `theme_concentration`, and `setup_concentration`. |

<!-- Change Type key used above: New component | New component (state) | Changed behavior -->

---

## Backend-Only Changes (No UI Impact)

Not itself a UI file, but directly in the serving chain for the `/watchlist` X-ray section above — listed here with the feed-through made explicit rather than claimed as isolated:

- `apps/backend/app/engine/concentration.py` (NEW) — the one canonical ENB/correlation math module: `correlation_matrix()` (Pearson, honest `None` on an undefined/zero-variance pair) and `effective_number_of_bets()` (`(Σλ)²/Σλ²` over `numpy.linalg.eigvalsh`). No UI file itself, but every correlation-matrix cell and the ENB headline on `/watchlist` trace to these two functions verbatim.
- `apps/backend/app/engine/watchlist_xray.py` (NEW) — `build_xray_payload()`, the pure composer that builds the exact `xray` object the page renders. Directly feeds all ten rows above; the sector/theme/setup helpers inside this file are the single source for the three concentration-bar rows.
- `apps/backend/app/config.py` (MODIFIED) — new `WatchlistXrayCfg`/`WatchlistCfg`. Confirmed feed-through: `corr_window_days` (126) is the literal number in "over the last 126 trading days" and the InfoTooltip text; `cluster_threshold` (0.7) is the literal "0.70" in the clusters caption; `min_overlap_days` (60) is the literal "60" in the InfoTooltip text and NA-cell hover titles.
- `config.yaml` (MODIFIED) — the committed `watchlist.xray:` block restating the same three values (`corr_window_days: 126`, `cluster_threshold: 0.7`, `min_overlap_days: 60`) — the exact numbers a user reads on the page today.

Genuinely backend-only, zero UI surface affected (test files only):
- `apps/backend/tests/test_concentration.py` (NEW) — 14 unit tests for the pure ENB/correlation math (B-204 fixture, hand-derived exact values).
- `apps/backend/tests/test_watchlist_xray.py` (NEW) — 10 tests for the composer (NA handling, null-sector bucketing, determinism, missing bars).
- `apps/backend/tests/test_api_watchlist.py` (MODIFIED, +4 tests) — additive-shape, byte-identity, no-proven/advice-language, and determinism tests for the endpoint's new `xray` field, alongside the ~9 pre-existing tests for the unchanged parts of the endpoint.

Frontend support file with no independent rendered surface of its own (already covered by the rows above):
- `apps/frontend/lib/api.ts` (MODIFIED) — `WatchlistXray` type family (+ 3 concentration sub-types) and the extended `WatchlistResponse.xray` field. Pure typing — every field it declares is exercised by one of the rendered rows above; there is no UI surface to test in this file directly (verified via `npx tsc --noEmit`, not a UI check).

---

## Summary

- **Frontend surfaces changed:** 1 (`/watchlist` — gains one new "Concentration X-ray" section with 9 distinct visual states/components: container, matrix, matrix NA-cell state, ENB headline, info tooltip, cluster badges, sector bars, theme bars, setup bar, plus the insufficient-watchlist empty state)
- **New pages/routes:** 0
- **Modified components:** 1 existing page file modified (`apps/frontend/app/watchlist/page.tsx`), 1 new component file (`apps/frontend/components/correlation-heatmap.tsx`), 1 typed API-client file extended (`apps/frontend/lib/api.ts`)
- **Navigation changes:** no — `/watchlist` is the same pre-existing top-level nav item; no new route, no nav-skeleton change
- **Backend-only changes:** 3 test files (zero UI impact); 4 other backend/config files feed the one affected surface described above (see feed-through notes)
