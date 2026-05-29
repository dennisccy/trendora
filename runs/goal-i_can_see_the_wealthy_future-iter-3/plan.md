# goal-i_can_see_the_wealthy_future-iter-3 Execution Plan

Per-entity canonical scores: three independent per-stock scores + theme scores + setup
classification, each computed **exactly once** in the engine and read identically everywhere.
Targets **J-02, J-03, J-06** and finishes **J-01**; **J-04 must stay green**. Depth: full
(backend + frontend + new unit tests). Mirrors the proven `sectors.py` template throughout.

## What to Build

**Backend engine (each value computed EXACTLY ONCE; all tunables from `config.yaml`):**
- `app/engine/labels.py` — promote the shared `label_for(score, edges)` out of `regime.py`; update
  `regime.py`, `sectors.py`, `themes.py` to import it. `sectors.py` MUST stop importing the private
  `regime._label_for`. **Refactor must not change `/api/sectors` output (J-04 regression risk).**
- `app/engine/scoring.py` — `score_stocks(session, asof, config) -> {asof_date, benchmark, rows[]}`,
  mirroring `sectors.py` (cross-sectional percentile → config-weighted blend → 0–100, NA-graceful,
  `to_bucket`, component shape `{name, raw, percentile, weight, contribution, available}`). Each row is
  the stock's **complete canonical record**: three independent scores (**Leadership / Entry Quality /
  Risk**, weights from `config.scores.*.weights`), each with **≥3 available named components keyed to
  config keys**, **plus** its setup status + reason (reads regime once via `regime.score_regime`, applies
  `setups.classify_setup`). Risk = *danger* (higher = more dangerous) — state in docstring, keep
  consistent. All bars via `bars_asof` (no lookahead).
- `app/engine/themes.py` — `score_themes(session, asof, config) -> {asof_date, rows[]}`: price-confirmed
  Theme Score (0–100 + bucket + named components) per `config.themes` theme, plus member tickers, 1m & 3m
  equal-weight basket return (windows from `config.indicators.rs_windows`), breadth % (members above
  50-DMA, **universe-relative**), trend label (from new `config.theme_scores.trend_edges`).
- `app/engine/setups.py` — `classify_setup(scores, regime, config) -> {status, reason}` mapping the three
  scores + regime to the six `config.decision_rules` statuses. **CRITICAL gate: regime label == Risk-off ⇒
  zero "Actionable"** (watchlist-only), regardless of scores. Plus `summarize_candidates(stock_rows)` —
  the single place candidate counts are derived (counts canonical setup statuses).

**Backend API (serve engine output verbatim; 503 on no data — never fabricate):**
- `GET /api/stocks` → `score_stocks(latest_data_date)`; 503 when no data.
- `GET /api/stocks/{ticker}` → the **same row** filtered from the *same* `score_stocks` result (do NOT
  recompute per-ticker) → byte-identical to the list row (**J-06**); 404 unknown ticker.
- `GET /api/themes` → `score_themes(latest_data_date)`; 503 when no data.
- Wire `/api/dashboard`: `candidate_counts` ← `setups.summarize_candidates(score_stocks.rows)`;
  `top_themes` ← top-N of `score_themes` (slice, like Top Sectors slices `/api/sectors`). **Leave
  breadth / new-high-low untouched** (already computed once in `regime.py` — do NOT recompute).
- Register `stocks`, `themes` routers in `main.py` under `/api`.

**Config + data linkage (reference data + validation — no scoring literals in code):**
- Add `theme_scores:` (`weights:` summing ~1.0 over every theme component + `trend_edges:` LabelEdge list).
- Add `stock_sectors:` (every `universe.symbols` ticker → a GICS sector name that is one of the 11
  `etfs.sector` values, e.g. `NVDA: Technology`). Reference data, not a magic number.
- `config.py`: add typed validation + consumption for `theme_scores`, the existing
  `scores.{leadership,entry_quality,risk}.weights` (complete component set, sum ~1.0), and
  `decision_rules` (required cutoff keys present) — mirroring iter-2's `SectorsCfg`/`RegimeCfg`.
- `seed_loader.py` (`load_reference_data`): set `Stock.sector_id` from `stock_sectors` on create **and
  backfill** existing rows lacking it (idempotent). **`models.py` MUST NOT change** (`Stock.sector_id`
  FK already exists; no persistence/snapshot work this iteration).

**Frontend (re-format only — never compute a score/bucket/return client-side):**
- `lib/api.ts`: add `fetchStocks`, `fetchStock(ticker)`, `fetchThemes` + `StockRow`/`ThemeRow` types;
  change `DashboardResponse.candidate_counts` / `top_themes` from placeholders to their real shapes.
- `/stocks`, `/stocks/[ticker]`, `/themes`, `/` — see UI Evolution.

## Agents Required
- backend-data: yes — engine modules, endpoints, config validation, seed linkage, pytest suites.
- frontend-ux: yes — four surfaces (leaderboard + filters, minimal detail, theme leaderboard, dashboard rollup).

Frontend Present: yes

## Files to Create/Modify

**Create (backend):** `app/engine/labels.py`, `app/engine/scoring.py`, `app/engine/themes.py`,
`app/engine/setups.py`, `app/api/stocks.py`, `app/api/themes.py`,
`tests/test_scoring.py`, `tests/test_themes.py`, `tests/test_setups.py`.
**Modify (backend):** `config.yaml` (add `theme_scores`, `stock_sectors`), `app/config.py` (typed
`ThemeScoresCfg` + `ScoresCfg` + `DecisionRulesCfg` validation), `app/engine/regime.py` &
`app/engine/sectors.py` (import `labels.label_for`; drop private `_label_for` usage),
`app/api/dashboard.py` (real `candidate_counts` + `top_themes`), `main.py` (register routers),
`tests/test_api_engine.py` (J-06 list==detail guard), `tests/test_no_magic_numbers.py`
(CALC_FILES += `scoring.py`,`themes.py`,`setups.py`,`labels.py`; FORBIDDEN_INT_LITERALS += `85` and any
new `theme_scores`/`decision_rules` integer cutoffs), `tests/test_config_engine.py` (or a new
`test_config_scores.py`) for the newly-validated blocks.
**Create (frontend):** `app/themes/page.tsx` content (replace stub). 
**Modify (frontend):** `app/stocks/page.tsx`, `app/stocks/[ticker]/page.tsx`, `app/page.tsx`,
`lib/api.ts`. Reuse existing `ScoreBadge` (`{bucket, score}`), `ComponentBreakdown`, `EmptyState`.

## UI Evolution
- **New user-facing capability:** rank/filter/explain every stock by three independent A–E scores; drill
  into a stock's score components; rank themes by a price-confirmed score; read a complete dashboard
  (regime + real candidate counts + Top Sectors + Top Themes + breadth + as-of date).
- **New information displayed:** per-stock Leadership/Entry Quality/Risk (bucket + raw + component
  breakdown), setup status, reason; per-theme score, members, 1m/3m basket return, breadth %, trend label;
  dashboard candidate counts (# Actionable / Breakout-watch / Pullback-watch) and Top Themes (≥3, scored).
- **New user actions:** filter `/stocks` by sector and by setup status (incl. "Actionable"); click a
  stock row → its detail page; expand a score's component breakdown; expand a theme row's breakdown.
- **UI surface changes:** `/stocks` (empty → leaderboard + 2 filters), `/stocks/[ticker]` (stub → minimal
  3-score detail), `/themes` (empty → ranked leaderboard), `/` (pending placeholders → real counts + Top Themes).
- **Navigation changes:** none — all four are existing IA homes in `blueprint.md`; rows link to
  `/stocks/[ticker]` exactly as the sector page pattern. **No `blueprint.reapproval-requested`.**

## Visual Requirements
- **Components:** dense dark tables matching `/sectors`; `ScoreBadge` for all four score types (A–E
  foregrounded, raw secondary); `ComponentBreakdown` for expandable rows; setup-status as a palette-token
  `Badge`; filters via shadcn select/dropdown primitives; `EmptyState` when a filter matches no rows.
- **Layout:** persistent sidebar + main content (existing shell); horizontally-scrollable tables at the
  ~640px breakpoint. Numbers use the monospace `.num` (tabular-nums) class.
- **Effects / palette:** colour-grade scores green→amber→red via the existing bucket→token mapping;
  Risk colour-graded by its *danger* direction. Tokens only — no arbitrary hex. Honesty labels
  ("universe-relative") in `--warn` amber.
- **States:** loading skeleton, empty (no rows / filter-empty), and explicit red "Backend unavailable"
  (no fabricated rows) on every new page — mirror iter-2.
- **Filtering is client-side re-display of server rows only** — no recompute or re-sort of scores.

## Key Test Scenarios
- **J-02 (browser):** `/stocks` renders multiple ranked rows, each with three bucketed scores
  (bucket + number), a setup status, and a non-empty reason; Sector filter reduces rows to one sector;
  Setup-status = Actionable shows only Actionable rows (or explicit empty-state if none).
- **J-03 (browser):** `/themes` lists ≥3 themes by non-increasing Theme Score; top theme shows member
  tickers, numeric 1m & 3m returns, a breadth %, and a trend label.
- **J-06 (browser + unit):** NVDA's three scores **and** A–E buckets are identical on `/stocks` and
  `/stocks/NVDA`; `test_api_engine.py` asserts the list row == detail row.
- **J-01 (browser):** regime label+score, three candidate counts (each a number), ≥3 Top Sectors and ≥3
  Top Themes (each scored), a breadth %, and an as-of timestamp all render.
- **J-04 regression (browser):** `/sectors` unchanged after the `labels.py` extraction.
- **Risk-off gate (unit, critical):** feed a Risk-off regime → `classify_setup` returns zero "Actionable".
- **Single source (unit):** changing a `config.scores.*` weight changes the score; ≥3 available
  components per score; NA components excluded + `available:false` (never fabricated); deterministic on
  the seed; all reads via `bars_asof`.
- **No-magic-numbers (unit):** extended `CALC_FILES`/`FORBIDDEN_INT_LITERALS` pass.
- **Config validation (unit):** bad `theme_scores`/`scores` weights or missing `decision_rules` cutoffs → `ConfigError`.
- **Error cases:** unknown ticker → 404; no price data → 503 on all three new endpoints; insufficient
  history → NA components, not a crash or fabricated 0.
- **Gates:** `cd apps/backend && .venv/bin/python -m pytest tests/ -v` green (no regressions);
  `cd apps/frontend && npm run build` green.

## Assumptions (documented per questioning policy — not blocking)
- **Component→indicator mapping** is at the developer's discretion within the spec's guidance, subject to
  the hard constraints: each score has **≥3 *available* components**, every component **named and keyed to
  its `config.scores.*` weight key**, Risk follows the *danger* direction. Components needing data absent
  from the seed (e.g. `gap_climax` → earnings; any earnings/fundamental-only key) report **NA
  (`None`)/`available:false`** and are excluded from the weighted sum — **never fabricated**. `rs_sector`
  uses the stock's sector ETF (via `Stock.sector_id`), `rs_theme` the theme basket; `regime` /
  `sector_strength` Risk components **read** the canonical regime/sector outputs, never recompute them.
- **`stock_sectors`** is factual GICS reference data the developer fills for every universe symbol (sector
  name ∈ the 11 `etfs.sector` values). Validated in `config.py` (every symbol covered; names valid).
- **`theme_scores` values** (weights + trend_edges) are illustrative defaults like `sectors:`; journeys
  assert structure/ordering, not exact numbers, so they may be tuned later. Any new integer cutoff added
  here MUST also be added to `FORBIDDEN_INT_LITERALS`.
- **`candidate_counts` shape:** `summarize_candidates` may count all six statuses (canonical); the
  dashboard displays the three required (# Actionable / Breakout-watch / Pullback-watch).
- **Blueprint already reconciled:** `runs/goal-session-.../state/blueprint.md` already carries the
  additive iter-3 Data-Contract attributions (breadth→regime, counts→`setups:summarize_candidates`) and
  serving notes. Dev confirms consistency; does **not** re-edit the nav skeleton and does **not** write a
  reapproval request.

## Coherence & Scope Flags
- **Single-source is the headline risk (J-06 + the iter-5 trap).** One `score_stocks` feeds both
  `/api/stocks` and `/api/stocks/{ticker}`; the dashboard derives counts/Top-Themes from the *same*
  `score_stocks`/`score_themes` outputs (count/slice = re-format, not recompute). Do NOT recompute
  breadth/new-high-low — read the regime engine's. New modules **read** existing canonical sources.
- **No scope drift:** spec aligns with `docs/goal.md` + roadmap (iter-3 = themes + 3 stock scores +
  leaderboards). Persistence/immutability, full Stock Detail (J-05), the J-07 browser journey,
  walk-forward, watchlist, and live data are explicitly **out of scope**; `models.py` stays untouched.

## Process Notes (from the iter-2 eval — non-blocking, for the pipeline)
- **Produce the audit handoff** this full-depth iteration (it was missing in iter-2).
- **Harden frontend supervision:** before any browser SKIP/PASS, confirm the managed `next dev` on **port
  3835** is up and stable, and **judge from the on-disk evidence directory / screenshots** — the
  SKIP-vs-PASS flap has recurred twice; reconcile by viewing the PNGs, not a lone verdict.
