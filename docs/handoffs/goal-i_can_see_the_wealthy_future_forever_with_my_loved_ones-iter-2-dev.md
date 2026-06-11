# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-2
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

J-43 (finish deep-linkable `?asof`), J-44 (dashboard Major-indexes & regime card), J-45 (regime bands behind the stock-detail price chart). Lean iteration — only the IN-SCOPE items.

### Backend (two new read-only stored-data paths, no schema/scoring change)
- **`app/engine/regime_history.py` — `get_regime_history(session, as_of=None, config=None)`**: returns the per-date regime series `{asof_date, points:[{date,label,score}]}` read **verbatim** from the immutable `scanner_runs` rows, bounded to dates `<= the resolved as-of`. No regime is recomputed (it only READS `ScannerRun.regime_label`/`regime_score`); as-of resolution reuses `scanner.resolve_as_of_date` (identical `?as_of=` semantics). Rows dated after the as-of are never returned (no-lookahead). An as-of before any run yields an honest empty `points`.
- **`GET /api/regime-history`** (`app/api/regime_history.py`): serves that series; `?as_of=` honored; `AsOfError` mapped to the shared 4xx/503.
- **`app/engine/indexes.py` — `compute_index_series(session, as_of, range_key, config)`**: server-side normalized-% lines for the **config-listed** index ETFs, rebased to the selected range start (first point exactly `0.0%`; `pct = (close/base − 1)·100`), bounded to dates `<= as-of` (via `bars_asof`). A configured symbol with no stored bars (DIA) is **omitted** (series + legend) — never synthesized. Returns `{asof_date, range, ranges, series}`. Unknown range preset → `UnknownRangeError`.
- **`GET /api/indexes`** (`app/api/indexes.py`): `range` (preset key) + `as_of` params; unknown preset → **422**; `AsOfError` → shared 4xx/503.
- **`config.yaml` + `app/config.py`**: new typed required `index_chart` section — `symbols` (ticker + legend display name; SPY/QQQ/IWM/RSP + DIA listed-but-barless), `range_presets` (3M/6M/1Y/All with trailing-day windows), `default_range`. Validated (`IndexChartCfg`/`IndexChartSymbol`/`IndexRangePreset`): unique preset keys + symbols, `default_range` ∈ presets, `days >= 1`. **Deliberately independent of `etfs.index`/scoring inputs** so listing DIA never touches regime/scoring computation. Added to ALL FOUR inline test config dicts (MINIMAL_VALID, VALID, test_sectors `_SYNTH_CFG`, test_themes).
- Routers mounted in `apps/backend/main.py`.

### Frontend
- **J-43 fix** (`components/asof-provider.tsx`): added the live-URL key `searchKey = searchParams.toString()` to the `AsOfUrlSync` serialize effect's dependency set. Previously the effect read a STALE `searchParams` from its closure, so on a deep-link load the restored `asOf=D` saw `current===next` and early-returned → the date-free URL "won" permanently. Keying on the live URL lets the effect re-serialize `?asof=D` after the restore commits, so it survives reload / fresh tab / click-through. Provider stays the sole `?asof` owner.
- **`lib/regime.ts`** — the ONE shared label → risk-family → color mapping (risk-on→green `--pos`, neutral→amber `--warn`, risk-off→red `--neg`). Both chart surfaces import it, so the same stored date shows the same band color everywhere (coherence). Computes no regime.
- **`components/regime-band-primitive.ts`** — a Lightweight-Charts v5 `ISeriesPrimitive` that paints the soft regime bands on the background layer as an honest step function between snapshot dates, clipped at the as-of x-coordinate (no band past the as-of). Shared by both charts.
- **`components/index-regime-chart.tsx`** (J-44 body) — normalized-% index lines (server `series`, no client return math) over the regime bands, a hover tooltip (ISO date + each index % + the exact stored regime label/score via the shared mapping + `formatIsoDate`), and a legend.
- **`components/major-indexes-card.tsx`** (J-44 card) — mounts on `/` (default ON), config-driven range-preset `<Select>` (options from the API), enable toggle persisted client-side (fully hides the card when off, with a "show" affordance); fetches `/api/indexes` + `/api/regime-history` at the SAME as-of (historical as-of → no bar/band past D); loading/empty/error states.
- **`components/price-chart.tsx`** (J-45) — new optional `regimePoints` + `regimeEnabled` props attach the band primitive behind price; bands defensively re-clipped to `date <= asofDate` so the J-20 forward region stays band-free; legend gains the three regime swatches. All J-20 behavior (forward candles/volume, as-of marker, MA overlays) unchanged.
- **`app/stocks/[ticker]/page.tsx`** (J-45) — fetches regime history at the same as-of, adds a **Regime** toggle (default ON, persisted) in the chart header, passes points to `PriceChart`. Scores/setup/VCP/as-of marker untouched.
- **`lib/use-persisted-toggle.ts`** — SSR-safe `localStorage` boolean preference (default value on first render, hydrates in effect) used by both toggles.
- **`lib/api.ts`** — `fetchRegimeHistory` + `fetchIndexes` and their types (re-format only; an unknown range throws via the 422).

## Files Changed
- `config.yaml` -- new `index_chart` section (symbols/names + range presets; no magic numbers)
- `apps/backend/app/config.py` -- `IndexChartCfg`/`IndexChartSymbol`/`IndexRangePreset` + required `index_chart` field + validation
- `apps/backend/app/engine/regime_history.py` -- NEW: verbatim stored regime series, as-of bounded
- `apps/backend/app/engine/indexes.py` -- NEW: server-side normalized-% index series, rebase/omit/422
- `apps/backend/app/api/regime_history.py` -- NEW: `GET /api/regime-history`
- `apps/backend/app/api/indexes.py` -- NEW: `GET /api/indexes`
- `apps/backend/main.py` -- mount the two new routers
- `apps/backend/tests/test_regime_history.py` -- NEW: verbatim-read + as-of bounding + empty-before-history
- `apps/backend/tests/test_indexes.py` -- NEW: rebase/hand-computed/as-of-bound/omission/config/422
- `apps/backend/tests/test_api_indexes.py` -- NEW: both endpoints == engine, DIA omitted, 422, as-of bound
- `apps/backend/tests/test_config.py` / `test_config_engine.py` / `test_sectors.py` / `test_themes.py` -- `index_chart` added to all four inline config dicts
- `apps/frontend/components/asof-provider.tsx` -- J-43 serialize-effect dep fix (live `searchKey`)
- `apps/frontend/lib/regime.ts` -- NEW: shared label→family→color mapping
- `apps/frontend/lib/use-persisted-toggle.ts` -- NEW: SSR-safe persisted boolean
- `apps/frontend/components/regime-band-primitive.ts` -- NEW: Lightweight-Charts band primitive
- `apps/frontend/components/index-regime-chart.tsx` -- NEW: J-44 chart body + tooltip + legend
- `apps/frontend/components/major-indexes-card.tsx` -- NEW: J-44 dashboard card (toggle/range/states)
- `apps/frontend/components/price-chart.tsx` -- J-45 regime-band props + legend
- `apps/frontend/app/page.tsx` -- mount `MajorIndexesCard` on `/`
- `apps/frontend/app/stocks/[ticker]/page.tsx` -- J-45 regime fetch + Regime toggle
- `apps/frontend/lib/api.ts` -- `fetchRegimeHistory` / `fetchIndexes` + types

## Tests Run
Command (backend): `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **FULL SUITE GREEN — 639 passed, 4 skipped, 0 failed in 2044.50s (0:34:04).** (+17 vs iter-1's 622: the new `test_indexes`/`test_regime_history`/`test_api_indexes` + config-fixture additions; no regressions across sectors/themes/config or any other suite.) The dev's original background run was torn down when the dev turn ended; the pump re-ran the identical command to completion and recorded the real numbers here. New tests previously confirmed green in isolation too:
- `tests/test_indexes.py` + `tests/test_regime_history.py` → 11 passed (0.43s)
- `tests/test_api_indexes.py` → 6 passed (229s, full warm seed)
- `tests/test_config.py` + `tests/test_config_engine.py` → 78 passed (2.5s)

Command (frontend): `cd apps/frontend && npx tsc --noEmit`
Result: clean (0 errors). Per the iter spec, `tsc --noEmit` is the frontend gate (ESLint is not installed).

## Known Issues
- **DIA is honestly omitted** from the index chart legend/series (no seed bars — providers rate-limit this host per project memory). J-44 is explicitly NOT gated on DIA; the card renders fully from SPY/QQQ/IWM/RSP. All four have 1356 seed bars.
- **Regime band count**: the fully-warm seed has ~11 dated cadence runs (2022-10 … 2026-05), so the bands render as an 11-segment step function. A freshly-booted DB before background warm-up completes has fewer runs (bootstrap dates + latest); the bands fill in as warm-up proceeds — honest, never fabricated.
- **Canvas hover not automatable**: per the accepted J-42 precedent and project memory, the hover-tooltip leg may be accepted on code inspection of the single tooltip hook (it reads the served stored label/score + `formatIsoDate`); the bands themselves are visible in screenshots.
- No live external fetch was performed (offline seed path only; no adapters/scrapers added this iteration).
