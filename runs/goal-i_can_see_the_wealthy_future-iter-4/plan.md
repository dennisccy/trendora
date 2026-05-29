# goal-i_can_see_the_wealthy_future-iter-4 Execution Plan

**Goal:** Complete the Stock Detail page (`/stocks/[ticker]`) so opening a leader (e.g. NVDA) shows a
price + moving-average candle chart with a volume series, theme-membership chips, and a concrete
server-computed invalidation level — alongside the three explainable scores already rendered. Turns
**J-05** green without regressing J-01–J-04 / J-06.

Aligns with `docs/goal.md` (J-05 acceptance), the roadmap (iter-4 = Stock Detail chart + invalidation),
and the blueprint Data Contract rows already registered this iteration (price/MA/volume series;
invalidation; theme membership). **No nav-skeleton change → no blueprint re-approval.** Note: setups,
reasons, and the Risk-Off gate already landed in iter-3, so iter-4 is precisely the *remaining* J-05
pieces (chart + volume + theme chips + invalidation) — consistent with the roadmap, not drift.

## What to Build

- **`sma_series(values, period)`** in `indicators.py` — rolling MA aligned 1:1 with input (`None` for the
  warm-up prefix, then the SMA). MUST reuse the existing `sma` windowing so the invariant
  `sma_series(values, p)[-1] == sma(values, p)` holds (one MA definition; period stays an argument).
- **`GET /api/stocks/{ticker}/bars`** (new route in the existing `app/api/stocks.py`) returning, for the
  as-of date (`latest_data_date`): `asof_date`, `ticker`, `bars` (ascending OHLCV read **only** via
  `bars_asof`, date ≤ as-of), and `ma` keyed by every period in `config.indicators.ma_periods`
  (`"20"`,`"50"`,`"150"`,`"200"`) → the `sma_series` aligned 1:1 with `bars` (number or `null`). `404`
  unknown ticker, `503` no price data — never a fabricated row.
- **`config.decision_rules.invalidation: { ma_period: 50 }`** + typed validation (`ma_period` must be one
  of `indicators.ma_periods`). No invalidation literal in calc code.
- **Invalidation level** computed once in `scoring.py:score_stocks` → `row["invalidation"]` =
  `{ basis, ma_period, level, price, note }`. `level` = canonical `sma(closes_asof, config invalidation
  ma_period)` — the SAME 50-DMA value that ends the `/bars` MA series and feeds the scoring
  `extension`/`support_nearby` components. **Note string built server-side** (verbatim to the UI); when the
  MA is NA → `level: null` + honest note ("Invalidation level NA — insufficient history"), never fabricated.
- **Theme membership** computed once in `score_stocks` → `row["themes"] = [{slug, name}, …]` (every theme in
  `config.themes` whose members contain the ticker; `[]` if none). Reuses the SAME `config.themes` map
  `score_themes` ranks and the SAME slug→name derivation (no second mapping).
- Invalidation + themes ride on the shared `score_stocks` row, so **both** `/api/stocks` (list) and
  `/api/stocks/{ticker}` (detail) carry them identically (J-06 preserved — no second shape).
- **Frontend:** install Lightweight-Charts (MIT, client-side, no key); render a candle chart with
  server-`ma` overlays + a volume series, theme chips, and the invalidation note verbatim on
  `/stocks/[ticker]`, replacing the placeholder paragraph (`page.tsx:139-143`). Add `fetchStockBars` +
  types to `lib/api.ts`; extend `StockRow` with `themes` + `invalidation`.

## Agents Required

- **developer: yes** — implements backend (indicators series helper, `/bars` endpoint, invalidation +
  themes on the scoring row, config block + validation) and frontend (charting lib, chart/volume/chips/
  invalidation UI, fetcher + types). TDD: backend unit/integration tests before/with the implementation.
  - backend-data: **yes**
  - frontend-ux: **yes**

## Frontend Present

Frontend Present: yes

## Files to Create/Modify

**Backend — modify:**
- `apps/backend/app/engine/indicators.py` — add `sma_series(values, period)` (NA-prefix aligned; reuses
  `sma` windowing). Stays literal-free (a `CALC_FILES` member of the no-magic-numbers test).
- `apps/backend/app/api/stocks.py` — add `GET /api/stocks/{ticker}/bars` (OHLCV via `bars_asof`; `ma` per
  `config.indicators.ma_periods` via `sma_series`; 404 unknown / 503 no-data). MA periods read from config —
  no literal.
- `apps/backend/app/engine/scoring.py` — attach `row["invalidation"]` (canonical `sma` over config
  invalidation `ma_period`; backend-built note; NA-honest) and `row["themes"]` (reverse of `config.themes`).
  Build the basis label from the config period (e.g. `f"{p}-DMA"`) — no `50` literal.
- `apps/backend/app/engine/themes.py` — extract a shared `theme_name(slug)` (= `slug.replace("_"," ").title()`,
  the current iter-3 derivation) reused by `score_themes` AND `score_stocks` (single naming source).
- `apps/backend/app/config.py` — add `InvalidationCfg { ma_period: int }` on `DecisionRulesCfg`; add a
  `Config`-level model_validator asserting `decision_rules.invalidation.ma_period ∈ indicators.ma_periods`.
- `config.yaml` — add `decision_rules.invalidation: { ma_period: 50 }`.
- *(optional)* `apps/backend/app/engine/prices.py` — add `opens(bars)` extractor, OR build OHLCV rows
  directly from `DailyPrice` in the endpoint (model already has open/high/low/close/volume). Reuse
  `closes(bars)` for the MA series either way.

**Backend — tests:**
- `tests/test_indicators.py` — `sma_series` warm-up NA, correct rolling values, `[-1] == sma` invariant.
- `tests/test_api_engine.py` (or new `tests/test_bars.py`) — `/bars` ascending, all dates ≤ asof
  (no-lookahead), `ma` keyed by every `ma_period` and length-aligned to `bars`; 404 unknown; 503 no-data.
- `tests/test_scoring.py` — row carries `invalidation` + `themes`; `invalidation.level ==
  sma(closes_asof(ticker), config invalidation ma_period)`; short-history ticker → `level is None` + honest
  note (no fabrication); `themes` matches the reverse of `config.themes`.
- `tests/test_api_engine.py` (J-06 guard) — `/api/stocks/{ticker}` row (incl. new `invalidation`+`themes`)
  equals the matching `/api/stocks` row (extend the existing list==detail assertion).
- `tests/test_config.py` — `invalidation` block validated; `ma_period` outside `ma_periods` rejected.
- `tests/test_no_magic_numbers.py` — confirm clean (50 already in `FORBIDDEN_INT_LITERALS`); extend
  `CALC_FILES` only if a new calc module appears.

**Frontend — modify/create:**
- `apps/frontend/package.json` — add `lightweight-charts` (confirm MIT, no key/credential, no runtime
  network callout → must clear the supply-chain gate; Recharts is the documented fallback — record any pivot
  in the handoff).
- `apps/frontend/lib/api.ts` — add `BarsResponse` (`asof_date`, `ticker`, `bars[]`, `ma: Record<string,(number|null)[]>`)
  + `fetchStockBars(ticker, signal)`; extend `StockRow` with `themes: {slug,name}[]` and
  `invalidation: {basis, ma_period, level: number|null, price: number|null, note: string}`. Keep the
  "RE-FORMATS server values only" discipline.
- `apps/frontend/app/stocks/[ticker]/page.tsx` — replace the placeholder paragraph with the chart panel +
  volume sub-pane, theme chips (link to `/themes`), and the invalidation note rendered **verbatim** from
  `row.invalidation.note`.
- `apps/frontend/components/price-chart.tsx` *(new)* — a **client-only** Lightweight-Charts wrapper
  (`"use client"`, mount in `useEffect`/`useRef`, dispose on unmount; dynamic import / SSR-guard since the
  lib touches `document`). Plots candles from `bars`, one line series per `ma[period]` (skip `null` →
  gaps; **never** compute a MA from closes), and a histogram volume series on a separate scale.

## UI Evolution

- **New user-facing capability:** open any leaderboard row's Stock Detail and study a price candle chart
  (with 20/50/150/200-DMA overlays + volume), see which themes the stock belongs to, and read a concrete,
  explainable invalidation level — all without the page ever recomputing a value.
- **New information displayed:** price candle chart + server MA overlays; volume series; theme-membership
  chips; a concrete invalidation level/note (e.g. "Invalid below the 50-DMA at $X").
- **New user actions:** click a theme chip to reach the existing `/themes` (optional link). No new mutating
  actions, no new route.
- **UI surface changes:** `/stocks/[ticker]` only — chart panel, volume sub-pane, theme chips, and the
  invalidation note added below/alongside the existing setup+reason header and three score cards.
- **Navigation changes:** none (Stock Detail stays row-reached under Stocks; chips link to existing Themes).

## Visual Requirements

- **Component patterns:** existing shadcn `Card` for the chart panel, the invalidation card, and the theme
  chips row; reuse `Badge`/chip styling for theme chips; keep the existing `ScoreCard`/`ComponentBreakdown`
  for the three scores (must not regress).
- **Layout:** chart as a full-width Card above the existing 3-score grid; theme chips + invalidation note in
  a compact Card near the setup/reason header. Dense, dark analytical workstation styling.
- **Key visual effects:** chart drawn on the dark surface with palette tokens only (candles green/red =
  `--pos`/`--neg`; MA overlay lines from accent/border-strong tones; volume histogram muted). Numbers stay
  monospace/tabular. No arbitrary hex/px.
- **States to handle:** chart skeleton while `/bars` loads; the existing "Backend unavailable" and "Unknown
  ticker" states must still work; honest NA treatment when `invalidation.level` is null (render the honest
  note, no fabricated number); empty/short-history → MA gaps drawn as gaps, never interpolated.

## Single-source & anti-goal guardrails (must hold)

- **One MA definition** feeds chart overlays + invalidation + scoring `extension`/`support_nearby` — all via
  `indicators:sma`/`sma_series` over the config period. Frontend plots the server `ma` series and computes
  no MA client-side.
- **No lookahead (critical):** `/bars` reads only `bars_asof` (date ≤ as-of); no charted bar after as-of.
- **Single source (critical):** invalidation note built server-side; `/api/stocks` == `/api/stocks/{ticker}`
  stays byte-identical after the new fields (J-06). FE re-formats only.
- **No magic numbers:** invalidation MA basis from `config.decision_rules.invalidation`; chart MA periods
  from `config.indicators.ma_periods`.
- **No fabricated data:** short-history MA = NA (chart gap + invalidation `null` + honest note); 404/503
  preserved.
- **Snapshots immutable (critical):** `models.py` UNCHANGED (no persistence this iter — snapshots arrive
  iter-5).
- **No order/execution path & No secrets:** no broker/order path; re-grep new/changed source; confirm the
  charting lib adds no credential and no runtime network callout.

## Key Test Scenarios

- Backend `pytest tests/ -v` passes (≥109 prior + new); frontend `npm run build` compiles + typechecks.
- `sma_series` warm-up NA + rolling values + `[-1] == sma` invariant.
- `/api/stocks/{ticker}/bars`: ascending, all dates ≤ asof; `ma` keyed by every config MA period and aligned
  to `bars` length; 404 unknown ticker; 503 no data.
- Scoring row carries `invalidation` (level == canonical sma over config period; short-history → null +
  honest note) and `themes` (== reverse of `config.themes`); J-06 list==detail byte-identical incl. new fields.
- **Browser (J-05):** `/stocks` → click a leader (e.g. NVDA) → `/stocks/NVDA`; **the chart canvas actually
  renders** (candles + MA overlay lines + volume visible — not just "page loaded"), theme chips render, the
  invalidation note renders with a concrete level, and the three score cards still show bucket+number+≥3
  components. Capture unknown-ticker (404) and backend-down states behaving honestly. Save screenshots to the
  iteration evidence dir.

## Process notes (carry forward — non-gating but required)

- **Emit the audit handoff** at this full-depth iteration — it was missing in iter-2 and iter-3.
- **Browser-qa server supervision:** J-05 is **canvas-rendered** (Lightweight-Charts draws to `<canvas>`), so
  a "page loaded" check is insufficient and the SKIP-vs-PASS flap (recurred iters 1–3, dead `next dev` on
  :3835) would hide a blank chart. The dedicated browser-qa MUST own/self-heal its frontend (start it if
  down, as QA mode-2 does) or share one managed server; the evaluator MUST reconcile J-05 from the on-disk
  evidence PNGs (confirming the chart canvas is populated), not a lone SKIP/PASS verdict.

## Assumptions (documented, not asked)

- **Charting lib = Lightweight-Charts** per the stack doc (Recharts is the fallback only if the supply-chain
  gate or SSR integration blocks it — document any pivot in the handoff). Pin a known version and follow its
  series-creation API (v5 renamed `addCandlestickSeries`→`addSeries(CandlestickSeries,…)`).
- **`/bars` 404/503 semantics:** 404 when the ticker is not in `config.universe.symbols`; 503 when
  `latest_data_date` is None (or no bars exist for a known symbol) — mirroring `/api/stocks/{ticker}`.
- **Invalidation MA period = 50** (default; must be one of `indicators.ma_periods`).
- **Theme `name`** = the existing iter-3 `slug.replace("_"," ").title()` derivation, shared (not duplicated)
  between `score_themes` and `score_stocks`.
