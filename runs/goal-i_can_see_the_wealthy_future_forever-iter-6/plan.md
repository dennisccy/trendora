# goal-i_can_see_the_wealthy_future_forever-iter-6 Execution Plan

**Target journeys:** **J-20** — full chart path through latest seed date, display-only (Stock Detail);
**J-21** — Backtest leadership cohorts below Return Attribution with horizon-linked realized returns.
**Depth:** full (crosses backend + frontend; two **critical** anti-goal seams).
**Critical anti-goals in play:** *No lookahead* (chart display carve-out), *Attribution is read-only* /
*No recompute in the read path*, *Exactly one date selector* (J-18), *No fabricated data* (honest NA).

**Verified against source before planning (real names this plan builds to):**
- `app/engine/prices.py` has `bars_asof` (≤ D) / `bars_after` (> D) / `close_on` / `latest_data_date`;
  **no** full-path helper exists yet → add `bars_through_latest`.
- `app/api/stocks.py::stock_bars` serves `{asof_date, ticker, bars[], ma{}}` from `bars_asof` only; the
  score/VCP path is a **separate** endpoint (`stock_detail_payload`, snapshot row) — the chart endpoint
  never touches scoring. Default contract stays ≤ D.
- `app/engine/forward_testing.py::compute_run_scorecard` already builds, **per horizon**, `ret_by_symbol
  = {fr.symbol: fr.realized_return}` over the stored `forward_returns` for the run — this dict ALREADY
  contains the universe stocks **and** the sector ETFs (`forward_symbols` includes them). `_sector_etf_by_name(cfg)`
  (name→ETF ticker) exists. `config.themes` is `slug → [member tickers]`; `etfs.sector` is `ETF → name`.
  So J-21's three returns are a pure read of `ret_by_symbol` — no new query, no recomputed return.
- `app/api/backtest.py` rides each `scorecard.by_horizon[*]` entry verbatim — `leadership_returns` adds
  to that entry exactly like `attribution` did in iter-2. **No new endpoint, no new canonical value.**
- Frontend: `app/stocks/[ticker]/page.tsx::StockChartPanel` calls `fetchStockBars` → `PriceChart`
  (`components/price-chart.tsx`, Lightweight-Charts, server-MA-only). Scores read `fetchStock`
  (unchanged). `app/backtest/page.tsx` renders `ScanSummarySection` (regime + counts + Top Sectors/Themes/
  Ranked Cohort) → `ScorecardSection` → `BacktestAttributionSection`; the horizon **view** selector +
  `viewHorizon` state live INSIDE `BacktestAttributionSection` and hold no date state (J-18 intact).

**This iteration is additive: no existing value is recomputed, no new endpoint, no nav/sidebar change.**

## What to Build

### Backend (J-20 — display-only chart extension)
- **`app/engine/prices.py`** — add `bars_through_latest(session, symbol)`: the symbol's full ascending
  bar list **not** bounded by D (`select(DailyPrice).where(symbol==symbol).order_by(date)`). Distinct
  from `bars_asof`. **Do NOT** import/route it into `scanner.run_scan` / `scoring.score_stocks` /
  `patterns.detect_vcp` — it is a display accessor only.
- **`app/api/stocks.py::stock_bars`** — add an opt-in `through: Optional[str] = None`. When
  `through == "latest"`: source bars from `bars_through_latest` (full series), compute the `ma` map over
  the **full** close series (display-only), and expose the as-of boundary so the frontend can split/label
  the forward region — add `latest_date` to the payload AND a per-bar `is_forward` (`bar.date > asof`).
  When `through` is omitted/anything else: behaviour is **byte-identical to today** (bars ≤ D, `is_forward`
  all false / absent) so the default contract stays ≤ D. Keep the same validation: 404 unknown ticker,
  503 no data, 4xx invalid `as_of` — never a fabricated row. `asof_date` still echoes the resolved D.

### Backend (J-21 — read-only leadership-return projection)
- **`app/engine/forward_testing.py`** — add ONE shared helper `_leadership_returns(ret_by_symbol, cfg)`
  (takes **no Session**, issues no query, recomputes no return — this is how *Attribution is read-only*
  is satisfied structurally, mirroring `_attribution_slices`). It returns three keyed lists from the
  already-built `ret_by_symbol`:
  - `sectors`: for each `etfs.sector` entry → `{sector_etf, sector, mean_return: ret_by_symbol.get(etf), n}`
    (the **ETF's own** stored return; `n` 0/1; `null` when absent).
  - `themes`: for each `config.themes` slug → `{slug, mean_return, n}` where `mean_return` = **equal-weight
    mean** over `ret_by_symbol.get(member)` for members that have a stored return, `n` = that member count,
    `null` when n=0 (honest NA — never fabricate a missing member's return).
  - `cohort`: for each stored `ScannerResult` ticker → `{ticker, mean_return: ret_by_symbol.get(ticker), n}`.
  Wire into `compute_run_scorecard`'s per-horizon loop: add `"leadership_returns": _leadership_returns(
  ret_by_symbol, cfg)` to each `by_horizon` entry (alongside `cohort`/`excess`/`control_group`/`attribution`).
- **No-magic-numbers note:** the projection is **complete** (every sector ETF / theme / cohort ticker),
  so the backend needs **no** row-count literal; the frontend's existing display slices govern how many
  rows show. If the developer instead bounds the annotated set, that bound MUST come from config (e.g. a
  new `walk_forward.leadership.*` key) — no integer literal in `forward_testing.py` (`test_no_magic_numbers`).

### Frontend (J-20)
- **`lib/api.ts`** — `BarsResponse`: add `latest_date?: string`; `PriceBar`: add `is_forward?: boolean`.
  `fetchStockBars(ticker, asof?, signal?, through?)` — add the optional `through` param (appends
  `&through=latest`).
- **`app/stocks/[ticker]/page.tsx::StockChartPanel`** — call `fetchStockBars(ticker, asOf, signal, "latest")`;
  pass the as-of boundary (`asof_date` / `latest_date` / per-bar `is_forward`) into `PriceChart`. The three
  score cards, setup, VCP badge, and invalidation note still read `fetchStock` — **unchanged**.
- **`components/price-chart.tsx`** — accept the boundary props; draw a visible **as-of divider/shaded
  region at D** and label the post-D region "forward / after-as-of (display only)". Recommended mechanism
  (developer may substitute an equally-visible, token-based one): tint the `is_forward` candles via
  per-point `color`/`wickColor` (Lightweight-Charts supports per-bar colour) using a muted palette token,
  add a series marker at the as-of bar, and add a legend item for the forward region. **Palette tokens
  only** (read CSS vars as the component already does — no ad-hoc hex). At the latest as-of there are no
  `is_forward` bars → chart is visually unchanged.

### Frontend (J-21 — Backtest reorg + return columns + one lifted selector)
- **`lib/api.ts`** — add `LeadershipReturns` types (`sectors`/`themes`/`cohort` rows) and
  `leadership_returns` on `BacktestScorecardHorizonRow`.
- **`app/backtest/page.tsx`** — **split** `ScanSummarySection`: keep regime + candidate counts as the
  top "as-of scan summary"; **move** Top Sectors / Top Themes / Ranked Cohort to a new section rendered
  **BELOW** `BacktestAttributionSection`. New section order: as-of scan summary → forward-test scorecard
  → **Return Attribution → Top Sectors, Top Themes, Ranked Cohort**.
  - **Lift `viewHorizon`** out of `BacktestAttributionSection` to a shared parent (page level) so ONE
    selector drives BOTH the attribution panels AND the three leadership return columns. Keep the existing
    `HorizonViewSelector` UI; it stays a **VIEW** selector — no refetch, no fetch param, no date state
    (J-18 preserved; the global as-of switcher still owns the date).
  - Add a realized-return column to each of the three lists: join `by_horizon[viewHorizon].leadership_returns`
    onto the rows already fetched from `/api/sectors` (by `row.ticker` = sector ETF), `/api/themes`
    (by `row.slug`), `/api/stocks` (by `row.ticker`). Render with the existing `<Return value n min>`
    component → honest "—" (NA) when a horizon lacks post-bars. Keep the existing `TOP_N_PANEL`/`COHORT_ROWS`
    display constants (display-only; unchanged).

## Agents Required
- developer: yes — one developer covers both tracks (backend + frontend).
  - backend-data: yes — `bars_through_latest`; the `?through=latest` bars-endpoint extension + boundary
    fields; `_leadership_returns` wired into `compute_run_scorecard`; new unit/consistency tests.
  - frontend-ux: yes — `api.ts` types/fetcher param; `PriceChart` as-of divider + forward-region label;
    Backtest section reorg + lifted horizon selector + the three return columns.

Frontend Present: yes

## Files to Create/Modify
- `apps/backend/app/engine/prices.py` — add `bars_through_latest` (display-only; not in the score path).
- `apps/backend/app/api/stocks.py` — `?through=latest` opt-in on `stock_bars` + `latest_date`/`is_forward`.
- `apps/backend/app/engine/forward_testing.py` — `_leadership_returns` helper + per-horizon wiring.
- `apps/backend/tests/test_prices.py` (or `test_api_stocks*`) — J-20 no-lookahead + boundary + edge tests.
- `apps/backend/tests/test_backtest_scorecard.py` (+ `test_api_backtest.py`) — J-21 read-only equality/NA tests.
- `apps/frontend/lib/api.ts` — `BarsResponse`/`PriceBar` boundary fields, `fetchStockBars` `through` param,
  `LeadershipReturns` types + `leadership_returns` on the scorecard horizon row.
- `apps/frontend/components/price-chart.tsx` — as-of divider/shaded forward region + label (palette tokens).
- `apps/frontend/app/stocks/[ticker]/page.tsx` — opt into `through=latest`; thread the boundary to the chart.
- `apps/frontend/app/backtest/page.tsx` — reorg (lists below attribution), lift `viewHorizon`, return columns.
- `runs/.../state/blueprint.md` — flip the J-20 (bars row) and J-21 (leadership-returns row) notes from
  "target iter-6" to built; **no nav-skeleton change, no `blueprint.reapproval-requested`** this iter.

## UI Evolution
- **New user-facing capability:** at a historical as-of D, the Stock-Detail chart shows the price/MA/volume
  path **through the latest seed date** with D marked and the post-D region labelled forward/display-only;
  on Backtest, each Top Sector / Top Theme / Ranked-Cohort name shows a **realized forward-return** at the
  selected horizon, and one selector re-points every return column (and the attribution) at once.
- **New information displayed:** J-20 post-as-of price/MA/volume bars (labelled) + an as-of boundary marker;
  J-21 a realized-return column on Top Sectors / Top Themes / Ranked Cohort (per horizon, honest NA).
- **New user actions:** J-20 none (the global as-of switcher drives it); J-21 the existing horizon selector
  now also re-points the three leadership lists' return columns.
- **UI surface changes:** `/stocks/[ticker]` chart extends through latest + as-of divider/label;
  `/backtest` lists relocate **below** Return Attribution and each gains a horizon-linked return column.
- **Navigation changes:** none (both live on existing homes; no sidebar/nav-skeleton change).

## Visual Requirements
- **Component patterns:** reuse existing — `PriceChart` (Lightweight-Charts) for J-20; `Card`/`<Return>`/
  `ScoreBadge`/the existing `HorizonViewSelector` for J-21. No new component library pieces.
- **Layout:** Stock Detail unchanged except the chart panel; Backtest keeps the dense dark grid, with the
  three leadership lists relocated to a section below Return Attribution.
- **Key visual effects:** as-of **divider/shaded region** on the chart + a labelled forward region, using
  CSS palette tokens (`--border-strong`/`--text-faint`/`--warn` family) — **no ad-hoc hex**; numbers stay
  monospace/tabular; return colour-grading via the existing `<Return>` palette tokens.
- **States to handle:** chart loading/empty/error already exist (keep); latest as-of → no forward region;
  return column NA ("—") when a horizon lacks post-bars; `n < min_sample` keeps the existing low-sample ⚠.

## Key Test Scenarios
- **(J-20 unit)** For a historical D: `bars_through_latest` returns bars with date > D AND the payload
  marks D (`latest_date` + per-bar `is_forward`); the as-of-D **scores/VCP are byte-identical** whether or
  not post-D bars exist (snapshot row + `score_stocks`/`detect_vcp` unchanged — the extension never feeds
  scoring). Latest as-of → no forward region. Unknown ticker → 404; invalid `as_of` → 4xx (never fabricated).
- **(J-21 unit)** Derived sector / theme / cohort realized returns **equal a direct read** of stored
  `forward_returns` at the horizon (sector = the ETF's row; theme = mean of member rows; cohort = the
  symbol's own row), recomputing no return; a (row, horizon) with insufficient post-bars → `null`/NA;
  consistent with the existing scorecard (same stored observations).
- **(J-20 browser)** Set a historical D via the **global switcher** + in-app nav; open `/stocks/NVDA`;
  capture the chart with the **as-of divider** and the **labelled post-D forward region**; confirm the
  three score cards + setup + VCP badge match the ≤ D values; switch to latest → no forward region.
- **(J-21 browser)** On `/backtest` at a historical D with post-bars: confirm section order (scorecard →
  Return Attribution → the three lists) and a return column on each; capture a **before/after** of a return
  column when the **horizon** is switched (one selector re-points all three + attribution); a recent date
  shows **NA**; confirm **no page-local date dropdown** (J-18). Drive all date changes via the global
  switcher + in-app nav (in-memory as-of provider resets to Latest on hard reload); flush evidence
  incrementally and reconcile the evidence dir with the results file (iter-4 lesson).

## Coherence guardrails / documented assumptions
- **No-lookahead (critical):** the full-path helper is display-only and is **never** routed into
  `score_stocks`/`detect_vcp`/`run_scan`; scores/VCP/invalidation keep reading the snapshot row (bars ≤ D).
  The `?through=latest` opt-in keeps the endpoint's default contract ≤ D so the boundary is obvious.
- **Attribution-read-only / single-source (critical):** `_leadership_returns` reads the SAME stored
  `forward_returns` rows the scorecard/attribution already read — no second query, no recomputed return,
  no new endpoint, no new canonical value.
- **Exactly-one-date-selector (J-18, critical):** the lifted horizon control stays a **VIEW** selector
  (no refetch / no date param / no date state); the global as-of switcher remains the only date control.
- **No fabricated data:** missing (row, horizon) returns → `null`/NA with honest `n`; never a fabricated 0%.
- **Assumptions (documented, not blocking):** J-20 uses the spec's recommended `?through=latest` opt-in and
  exposes the boundary via `latest_date` + per-bar `is_forward`; the divider is rendered by tinting forward
  candles + a marker at D + a legend label (developer may substitute an equally-visible token-based effect);
  J-21's `leadership_returns` is a complete keyed projection (sectors by ETF ticker, themes by slug, cohort
  by ticker) joined onto rows the frontend already fetches, so no backend row-count literal is introduced.
- **Out of scope (excluded):** J-22…J-31 (≈500-name universe, multi-timeframe bars + chart timeframe
  selector, the `/research` labs, more patterns, volatility family, synthesis); any new endpoint / nav home /
  `/research` surface; any change to how scores/buckets/setups/VCP/regime/forward-aggregates are **computed**;
  any live-fetch / Data Manager / re-seed change. Not GOAL_ACHIEVED after this iter (J-22…J-31 remain unbuilt).
```

