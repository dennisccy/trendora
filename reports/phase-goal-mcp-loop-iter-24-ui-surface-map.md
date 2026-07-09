# Phase goal-mcp-loop-iter-24 — UI Surface Map

**Phase:** goal-mcp-loop-iter-24
**Date:** 2026-07-09
**Written by:** ui-impact-analyst

---

## File Classification

Per `.claude/skills/diff-to-ui-impact.md`, against the dev handoff's "Files Changed" list, independently
cross-checked against `git status`/`git diff` (both agree on the same file set).

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/db.py` | backend-internal | none (direct) | SQLite pragma tuning (`journal_mode=WAL`, `synchronous`, `busy_timeout`, `cache_size`, `mmap_size`, `temp_store`), connection-pool sizing, and a guarded startup index-hygiene migration. No API response shape changes; makes every DB-backed request cheaper but isn't attributable to one visible element (see Row 7 below for its indirect effect). |
| `apps/backend/app/config.py` | config | none | New `DatabasePragmasCfg` + `DatabaseCfg.pragmas`/`pool_size`/`max_overflow` fields (all default-populated). No env var or setting exposed anywhere in the UI. |
| `config.yaml` | config | none | New `database.pragmas` block + `pool_size`/`max_overflow` keys backing the above; deploy-time config, not user-facing. |
| `apps/backend/app/models.py` | backend-internal | none | Dropped 2 redundant indexes (`ix_daily_prices_symbol_date`, `ix_forward_returns_run_symbol`) and the guarded migration adds `ix_daily_prices_date`. Schema-level only — the classic "migration ≠ UI change" case; no served value is affected. |
| `apps/backend/app/engine/snapshot_serving.py` | backend-api | indirect | New `filtered_stock_rows()`; `stock_detail_payload` (serves `GET /api/stocks/{ticker}`) now uses it instead of deserializing the whole leaderboard. The frontend already consumes this endpoint on `/stocks/{ticker}` — same byte-identical payload, cheaper to build. |
| `apps/backend/app/api/watchlist.py` | backend-api | indirect | `_canonical_rows` now calls `filtered_stock_rows` for its ticker set instead of the whole-leaderboard path. Consumed by the existing `/watchlist` page — same payload, cheaper. |
| `apps/backend/app/engine/readiness.py` | backend-api | indirect | Memoizes the SPY warm-up calendar + replaces a per-date existence loop with one grouped query, feeding `GET /api/health`. Consumed globally by `HealthBadge` (every page, root layout) and `WarmingState` (`/backtest`, `/research/*`) — same reported `state`/`warmup` values, cheaper on each ~2s poll. |
| `apps/backend/app/engine/data_manager.py` | full-stack | direct (partial) | Two distinct changes in one file: (1) `_missing_data_diagnostic`'s N+1 fix — backend-api/indirect, feeds the EXISTING `/data` "Missing-data diagnostic" card, byte-identical, cheaper; (2) new `compute_capacity()` — full-stack/direct, the sole data source for the BRAND-NEW `/data` storage card. |
| `apps/backend/app/api/data.py` | full-stack | direct | Adds the additive `"capacity"` key to the `GET /api/data` payload — directly and only consumed by the new `StorageCapacityPanel`. |
| `incredible_auto_dev/scripts/measure-perf.sh` (repo-root symlink `scripts/measure-perf.sh`) | backend-internal (ops tooling) | none | New curl-timed benchmarking script for operators; not reachable from any page or button in the product. |
| `.gitignore` | config | none | Added `*.db-shm`/`*.db-wal` patterns — a direct consequence of item B's WAL mode; pure repo hygiene. |
| `apps/frontend/lib/api.ts` | frontend-direct | direct | New `DataCapacity` type + `DataOverviewResponse.capacity` field — the typed contract the new card reads. |
| `apps/frontend/app/data/page.tsx` | frontend-direct | direct | New `StorageCapacityPanel` component + `fmtBytes()` formatter, rendered on `/data` directly after `CoveragePanel`. This is the iteration's one genuinely new UI surface. |
| `reports/perf-budgets.md` | docs/reporting | none | Appended measured latency tables + the capacity snapshot; an engineering report read from the repo, not served through the product. |
| `apps/backend/tests/test_db.py`, `test_data_manager.py`, `test_health.py`, `test_api_engine.py`, `test_api_data.py` | tests | none | Targeted unit/integration coverage for items B/C/D/G/H/K; not shipped to any user-facing surface. |

---

## Affected UI Surfaces

| Route/Page | Component/Element | Change Type | Why Changed | What to Test |
|-----------|------------------|------------|-------------|--------------|
| `/data` | `StorageCapacityPanel` (new; `data-testid="storage-capacity-panel"`) | New component | Item K — additive `capacity` field on `GET /api/data`; the iteration's one new user-facing capability | Load `/data`, scroll to directly below the "Dataset coverage" card, and confirm a "Storage footprint" card renders with four values: a human-readable file size (e.g. "1.22 GB", never a raw byte count) labeled "Database file", and three comma-formatted integers labeled "Price bars", "Scanner rows", and "Forward returns". Cross-check those four numbers against the `capacity` object in the `GET /api/data` response in the browser's Network tab. |
| `/data` | `MissingDataDiagnosticPanel` ("Missing-data diagnostic" card, `data-testid="missing-data-diagnostic"`) | Changed behavior (perf only, byte-identical) | Item H — `_missing_data_diagnostic`'s per-universe-member N+1 query replaced with one bulk query | Restart the backend (cold DB cache), then load `/data` as the very first request and observe how long the "Missing-data diagnostic" card takes to populate its rows (or show "No missing data"). Confirm the exact same rows/empty-state that appeared before this iteration still appear (no row added, removed, or re-labeled), and that the overall `/data` page load stays within the budget recorded in `reports/perf-budgets.md`. |
| `/stocks/{ticker}` (e.g. `/stocks/AAPL`) | Stock detail page's data fetch (backed by `stock_detail_payload` / `GET /api/stocks/{ticker}`) | Changed behavior (perf only, byte-identical) | Item D — ticker-filtered fetch (`filtered_stock_rows`) replaces deserializing the whole leaderboard to find one row | Open `/stocks/AAPL` and record every displayed field (score badges, setup label, price, evidence badges). Open `/stocks` and locate the AAPL row. Confirm every field matches exactly between the two pages, and that `/stocks/AAPL` finishes loading well under its 0.3s API / 3s page warm budgets. |
| `/watchlist` | Watchlist table (backed by `_canonical_rows` / `GET /api/watchlist`) | Changed behavior (perf only, byte-identical) | Item D — same ticker-filtered fetch, wired into the watchlist's canonical-rows path | Add 2-3 tickers (e.g. AAPL, MSFT, NVDA) to the watchlist via its "Add" control, reload `/watchlist`, and confirm each row's score/setup/price fields exactly match that same ticker's row on `/stocks` — no value drift introduced by the filtered fetch. |
| Global (every page; rendered from the root layout) | `HealthBadge` top-bar readiness pill (`data-testid="readiness-badge"`) | Changed behavior (perf only, values unchanged) | Item G — memoized warm-up calendar + one grouped run-existence query replaces a per-date loop, on every `/api/health` poll (~every 2s) | Load any page (e.g. `/`) while the backend is still warming up and confirm the badge shows "Initializing… history n/m" with the state progressing normally (no missing/garbled value), then confirm it flips to "Ready" once warm-up completes. Watch the Network tab and confirm each `/api/health` call returns in ≤0.1s. |
| `/backtest`, `/research/*` (e.g. `/research/severity-velocity`) | `WarmingState` card ("Warming up — historical evidence still loading (n/m)", `data-testid="warming-state"`) | Changed behavior (perf only, indirect) | Item G — same underlying readiness value the top-bar badge reads | While the backend is still warming up, load `/backtest` and confirm the "Warming up…" card's "(n/m)" progress figure matches the top-bar badge's "history n/m" figure at the same moment, and that the page auto-populates its real content once warm-up finishes (no manual refresh needed). |
| `/data` (whole-page cold load) | Page-level initial load (`GET /api/data` overall response) | Changed behavior (perf only) | Items B + C + H together — WAL/pragma tuning, dropped redundant indexes + new `ix_daily_prices_date`, and the N+1 fix all reduce the cost of the same cold-path query plan | Stop and restart the backend, then load `/data` as the very first request after boot. Confirm the page fully renders (coverage panel, new storage card, diagnostic panel) without a blank/frozen frame, and completes within the ≤60s cold-path / ≤1.5s warm `/api/data` budgets recorded in `reports/perf-budgets.md`. |

**Note on pages measured but not listed above:** `/stocks` (the leaderboard's own `GET /api/stocks` path)
and `/evidence` were re-measured this iteration (see `reports/perf-budgets.md`) to confirm they still meet
their committed budgets, but neither has any code change in this iteration's diff — item E (a leaner
`/api/stocks` payload) is explicitly out of scope this iteration. They are omitted from the table above
because nothing in their serving path actually changed.

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/db.py` — SQLite pragma tuning + connection-pool sizing + the guarded index-hygiene
  migration runner — internal engine tuning with no surface of its own (see the last row above for its
  indirect speed contribution to `/data`'s cold load).
- `apps/backend/app/config.py` + `config.yaml` — new `database.pragmas`/`pool_size`/`max_overflow` config
  keys, all default-populated — no UI-exposed setting or env var.
- `apps/backend/app/models.py` — index drop (`ix_daily_prices_symbol_date`, `ix_forward_returns_run_symbol`)
  / add (`ix_daily_prices_date`) — schema-level only, no served value affected.
- `incredible_auto_dev/scripts/measure-perf.sh` (repo-root symlink `scripts/measure-perf.sh`) — new
  operator CLI benchmarking tool — not reachable from any page or button in the product.
- `reports/perf-budgets.md` — engineering report (latency tables + capacity snapshot) — read from the
  repository, not served through the running app.
- `.gitignore` — added WAL sidecar-file patterns (`*.db-shm`, `*.db-wal`) — repo hygiene only.
- `apps/backend/tests/test_db.py`, `test_data_manager.py`, `test_health.py`, `test_api_engine.py`,
  `test_api_data.py` — automated test coverage for items B/C/D/G/H/K — no user-facing surface.

---

## Summary

- **Frontend surfaces changed:** 1 route (`/data`) gains new content; 4 existing surfaces
  (`/stocks/{ticker}`, `/watchlist`, the global readiness badge, `/backtest`+`/research/*`'s warming card)
  get an indirect, byte-identical speed improvement with no visual change.
- **New pages/routes:** 0
- **Modified components:** 1 new component added (`StorageCapacityPanel`, plus its `fmtBytes()` helper) to
  the existing `/data` page; 0 existing frontend components were edited (`CoveragePanel` itself is
  untouched — the page composition just renders one more panel after it).
- **Navigation changes:** no
- **Backend-only changes:** 7 non-test files/areas (`db.py`, `config.py`, `config.yaml`, `models.py`,
  `measure-perf.sh`, `perf-budgets.md`, `.gitignore`) + 5 test files, all with no direct UI surface.
