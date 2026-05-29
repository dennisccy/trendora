# Trendora — Project Planning & Design Document

> Status: **Draft for approval** · Date: 2026-05-29 · Owner: Dennis Chan
> Operative goal-mode file: [`docs/goal.md`](goal.md) · Framework: embedded `incredible_auto_dev` dev-chain (goal mode)
>
> This document is the human-facing architecture/decision record. `docs/goal.md` is what the
> dev-chain reads and verifies. Where they overlap, `goal.md` is authoritative for *what "done" means*;
> this document is authoritative for *how it is built and why*.

## 0. Decisions locked in this planning session

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | MVP scope | **Research MVP in one goal-mode session** (regime + sectors + themes + 3 stock scores + setups + 8 pages + immutable snapshots + walk-forward forward-testing). Paper-portfolio and news/LLM **deferred**. | Forward-testing is the whole point, so it earns its place; paper-portfolio/news add scope without proving the core. |
| 2 | Market data | **Provider abstraction + committed seed fixture.** Default `SeedProvider` (deterministic, offline). Optional live provider (Stooq first). | Goal mode browser-verifies journeys every iteration; a live network dependency would flake and stall the loop. |
| 3 | Forward-test evidence | **Historical walk-forward bootstrap** (strict no-lookahead) + keep accumulating live snapshots. | Live-only evidence needs calendar months; the engine and its evidence must exist at delivery. |
| 4 | Datastore | **SQLite via SQLModel, Postgres-ready** (engine URL is config). | Zero-infra local dev + frictionless goal-mode verification; volumes are tiny; switch to PG is config-only. |
| 5 | Journey scope | **All 11 journeys** (J-01…J-11). | User chose the ambitious, complete MVP. |
| 6 | Scoring philosophy | **"Try the current setup, leave room for change."** All weights/thresholds in `config.yaml`; tune without code changes. | The model is a hypothesis to be validated and improved, not a fixed truth. |

---

## 1. Product definition

Trendora is a **local-first, research-only US-equity leadership scanner** — decision support, not an
auto-trader. After the close it ranks the market top-down (regime → sectors → industries → themes →
stocks) and, per stock, reports three **independent** scores so leadership is never confused with
buyability:

- **Leadership** — how strong the stock is (RS, trend, proximity to highs).
- **Entry Quality** — is *now* a good price location, or is it too extended?
- **Risk** — danger factors (extension, volatility, weak regime/sector, climax, illiquidity).

It answers seven questions: current regime? leading sectors? leading themes? strongest stocks within
them? actionable now or extended? what would invalidate the idea? **and did past scanner output
actually beat SPY/QQQ/sector/random peers?** The last question is the product's reason to exist, and
it is answered by an immutable-snapshot + walk-forward forward-testing engine rather than by naive
backtesting.

**What it is not (this session):** no order execution, no auto-trading, no options/intraday/ML, no
news/sentiment, no paper-portfolio, no full-market universe.

---

## 2. Architecture

### 2.1 Repository layout (under `apps/`, to protect the dev-chain symlinks)

```
trendora/
├─ docs/
│  ├─ goal.md                              # goal-mode operative file
│  └─ superpowers/specs/2026-05-29-trendora-design.md   # this document
├─ config.yaml                             # ALL tunables (weights, thresholds, universe, themes, provider)
├─ apps/
│  ├─ backend/                             # Python 3.12 · FastAPI · SQLModel/SQLite · Pandas · APScheduler
│  │  ├─ main.py                           # THE FastAPI app — uvicorn entry `main:app` (scripts/start-backend.sh): builds app, CORS, includes app/api routers, startup (load config, create tables)
│  │  ├─ app/                              # package (imported as `app.*`; apps/backend is on sys.path via --app-dir) — no main.py here
│  │  │  ├─ config.py                      # load_config() → typed settings (pydantic)
│  │  │  ├─ db.py                          # engine (URL from config), session, create_all
│  │  │  ├─ models/                        # SQLModel tables (see §5)
│  │  │  ├─ data_providers/                # PriceProvider ABC, SeedProvider, StooqProvider
│  │  │  ├─ universe/                      # build/filter the universe + ETFs from config
│  │  │  ├─ prices/                        # load/store daily OHLCV; as-of windows
│  │  │  ├─ indicators/                    # MAs, RS, ATR%, volume, distance-from-high, contraction…
│  │  │  ├─ regime/                        # MarketRegime score + label
│  │  │  ├─ sectors/                       # sector/industry ETF scoring
│  │  │  ├─ themes/                        # theme membership + Theme Score
│  │  │  ├─ scoring/                        # Leadership/Entry/Risk + bucket() (single source of truth)
│  │  │  ├─ setups/                        # setup classification + reason + invalidation
│  │  │  ├─ scanner/                       # run_scan(as_of) → immutable snapshot
│  │  │  ├─ forward_testing/               # walk-forward backfill + forward-returns + aggregates
│  │  │  ├─ api/                           # routers (dashboard, stocks, themes, sectors, runs, health, watchlist)
│  │  │  └─ jobs/                          # APScheduler wiring (daily scan, forward-return update)
│  │  ├─ data/seed/                        # committed fixtures (see §2.3) + scenarios (risk-on / risk-off)
│  │  ├─ data/trendora.db                  # gitignored, created at runtime
│  │  ├─ tests/                            # pytest
│  │  └─ requirements.txt
│  └─ frontend/                            # Next.js 15 (App Router) · TS · Tailwind · shadcn/ui
│     ├─ app/                              # routes (see §4)
│     ├─ components/                       # tables, score cells, charts, filters
│     └─ lib/                              # api client, formatters (NO business computation)
└─ scripts/  (symlink → dev-chain)         # start-backend.sh / start-frontend.sh honor CHAIN_*_PORT
```

### 2.2 Runtime shape

```
Seed fixtures ─┐
               ▼
        data_providers ──► prices ──► indicators ──► regime ─┐
                                              │              ├─► scoring ──► setups ──► scanner.run_scan(as_of)
                                              │  sectors ◄────┤                              │
                                              │  themes  ◄────┘                              ▼
                                              └──────────────────────────────────►  immutable snapshot (DB)
                                                                                            │
 forward_testing.walk_forward(dates) ──► snapshots(as-of, no-lookahead) ──► forward_returns ─┴─► aggregates
                                                                                            │
                                              FastAPI (read-only over stored rows) ◄─────────┘
                                                            │
                                              Next.js dashboard (re-formats only)
```

- **Backend = single source of truth.** API endpoints read the latest stored rows; no endpoint
  recomputes a score or queries a provider directly during a request.
- **Determinism.** `SeedProvider` is the default; the entire app + all journeys run offline. Live
  refresh is an explicit, config-selected action.
- **Postgres-ready.** SQLModel + an engine URL from config; no SQLite-only SQL.

### 2.3 Seed dataset (committed, deterministic)

- ~120–150 liquid US common stocks spanning the example themes (NVDA, AMD, AVGO, MRVL, ANET, DELL,
  SMCI, VST, CEG, ETN, PWR, GEV, VRT, TT, CARR, MU, WDC, STX, MSFT, AMZN, GOOGL, ORCL, plus members for
  semis, cybersecurity, nuclear, defence, homebuilders, crypto-equities, power-grid, GLP-1, etc.).
- ETFs: index (SPY, QQQ, IWM, RSP), 11 sector ETFs (XLK…XLP), industry ETFs (SMH, SOXX, IGV, CIBR,
  HACK, SKYY, BOTZ, ROBO, URA, URNM, ITA, XAR, XHB, ITB, KRE, KBE, XBI, IBB, BKCH, WGMI), and ^VIX.
- ~2–3 years of daily OHLCV per symbol (split/adjusted in the fixture; no corporate-action logic needed
  at runtime for the MVP — documented as a limitation).
- The fixture is **built once in iteration 1** by a one-shot ingest script that fetches real EOD history
  from the live source (Stooq — free, no key), then **committed and frozen**. The build loop only reads
  the committed files and MUST NOT re-fetch live data mid-loop — re-fetching would make the walk-forward
  evidence irreproducible. Real history naturally supplies **both a risk-on stretch and a risk-off
  stretch**, so J-07 has a real Risk-Off run and J-02 has real Actionable candidates.
- Fixtures are plain files (CSV/Parquet) under `apps/backend/data/seed/`, loaded on first boot.

---

## 3. Backend design

| Module | Responsibility | Key functions | Notes |
|--------|----------------|---------------|-------|
| `config` | Load `config.yaml` → typed settings | `load_config()` | Single source of every tunable. |
| `data_providers` | Abstract OHLCV access | `PriceProvider.get_daily(symbol, start, end)`; `SeedProvider`, `StooqProvider` | Failure → explicit `unavailable`, never fabricate. |
| `universe` | Build the symbol set from config + filters | `build_universe()` | Filters (mcap>2B, $vol>50M, price>10) recorded; applied where data allows. |
| `prices` | Persist/query daily bars; as-of windows | `bars_asof(symbol, d)` | **as-of = bars with date ≤ d** (no-lookahead boundary). |
| `indicators` | Pure functions on a price series | `sma`, `ema`, `rs_vs(bench)`, `atr_pct`, `vol_ratio`, `dist_from_high`, `contraction`, `extension` | Pure, unit-tested, no DB. |
| `regime` | Market Regime score + label | `score_regime(asof)` | Inputs in §7.4. Universe-relative breadth labelled. |
| `sectors` | Sector/industry ETF scores | `score_sectors(asof)` | RS vs SPY 1/3/6m, MA stack, dist-from-high, vol trend, breadth. |
| `themes` | Theme membership + Theme Score | `score_themes(asof)` | Price-confirmed (not news). Many-to-many membership. |
| `scoring` | **Leadership / Entry / Risk + bucket** | `score_stock(...) → {value, components[]}`; `bucket(score)` | The single source of truth for the six canonical values. |
| `setups` | Setup status + reason + invalidation | `classify(stock_scores, regime, patterns)` | Regime-gated; thresholds from config. |
| `scanner` | Full run → immutable snapshot | `run_scan(asof) → run_id` | Writes run + all result rows in one transaction; never mutates. |
| `forward_testing` | Walk-forward + forward returns + aggregates | `walk_forward(dates)`, `update_forward_returns()`, `aggregate()` | Strict no-lookahead; control groups. |
| `api` | REST routers | see §6 | Read-only over stored rows. |
| `jobs` | Scheduler | `schedule_daily_scan()`, `schedule_forward_update()` | APScheduler; also exposed as endpoints. |

Scoring returns **both** the value and its component breakdown (`[{name, raw, normalized, weight,
contribution}]`) so the reason summary and the detail-page breakdown are generated from the same object
— guaranteeing explainability.

---

## 4. Frontend design

Next.js 15 App Router · TypeScript · Tailwind · shadcn/ui · Lightweight-Charts. The `lib/api` client
fetches typed responses; `lib/format` only re-formats (numbers tabular/monospace, bucket → colour).
**No business computation client-side.**

| Route | Page | Core components |
|-------|------|-----------------|
| `/` | Dashboard | RegimeCard, CandidateCounts, TopSectors, TopThemes, BreadthCard, LastRunBadge, EvidenceSummary |
| `/stocks` | Stock Leaderboard | FilterBar (theme/sector/setup/score/risk), ScoreTable (3 bucketed scores + setup + reason) |
| `/stocks/[ticker]` | Stock Detail | PriceChart (MAs+volume), ScoreBreakdown ×3, ThemeChips, SectorRS, SetupCard, ReasonList, InvalidationNote, ScoreHistory |
| `/themes` | Theme Leaderboard | ThemeTable (score, members, 1m/3m, breadth, trend) |
| `/sectors` | Sector Leaderboard | SectorTable (score, RS, dist-from-high, breadth, trend) |
| `/scanner-runs` | Runs history | RunList (date, regime, counts) |
| `/scanner-runs/[runId]` | Run detail | As-of snapshot view (read-only, immutable) |
| `/system-health` | Evidence | BucketReturnTable, ExcessVsBench, BySetup, ByRegime, ControlGroupPanel, SampleSizeBadges |
| `/watchlist` | Watchlist | AddForm, WatchTable (date, reason, current score/setup, price-since-added, invalidation) |

Design tokens follow the dense-dark analytical aesthetic (see `goal.md` → Design Direction). Scores
render as **bucket chip first, number second**; every score is expandable to its components.

---

## 5. Database schema

SQLModel tables (SQLite now, Postgres-ready). Types shown logically. `*_id` are integer PKs unless
noted. Snapshot tables are **append-only**.

**Reference / universe**
- `stocks` — `id, ticker (unique), name, sector_id, industry_id, market_cap, is_common, active`
- `etfs` — `id, ticker (unique), name, kind (index|sector|industry), tracks_sector_id?, tracks_industry_id?`
- `sectors` — `id, name, etf_ticker`
- `industries` — `id, name, sector_id, etf_ticker`
- `themes` — `id, slug (unique), name, description`
- `theme_members` — `id, theme_id, stock_id, category_tag?` (many-to-many; a stock may be in many themes)
- `stock_universe_memberships` — `id, stock_id, source (sp500|ndx|custom), added_on, removed_on?`

**Prices**
- `daily_prices` — `id, symbol, date, open, high, low, close, volume` · unique(`symbol`,`date`) · indexed(`symbol`,`date`)

**Immutable snapshots (one set per scanner run)**
- `scanner_runs` — `id, run_date, as_of_date, created_at, provider, regime_label, regime_score, is_walk_forward (bool), notes`
- `market_regime_results` — `id, run_id, score, label, components_json`
- `sector_scores` — `id, run_id, etf_ticker, score, rank, rs_1m, rs_3m, rs_6m, dist_from_high, trend_label, breadth, components_json`
- `theme_scores` — `id, run_id, theme_id, score, rank, ret_1m, ret_3m, breadth, trend_label, components_json`
- `stock_scores` — `id, run_id, stock_id, leadership, leadership_bucket, entry_quality, entry_bucket, risk, risk_bucket, components_json`
- `setup_classifications` — `id, run_id, stock_id, status, reason_summary, invalidation_note`
- `scanner_results` — `id, run_id, stock_id, rank, close, theme_ids_json, sector_id` (the joined per-stock row the leaderboard reads; denormalized for fast read & true as-of immutability)

**Validation (separate, append-only, keyed to snapshot)**
- `forward_returns` — `id, run_id, stock_id, horizon (1|5|10|20|60), fwd_return, excess_vs_spy, excess_vs_qqq, excess_vs_sector, max_drawdown, max_favorable_excursion, hit_invalidation (bool), computed_at` · unique(`run_id`,`stock_id`,`horizon`)

**User**
- `watchlist` — `id, ticker, reason, added_on, price_at_add, invalidation_level, notes`

**Ops**
- `data_provider_runs` — `id, provider, started_at, finished_at, symbols_ok, symbols_failed, status, message` (data-quality log)
- `system_settings` — `id, key (unique), value_json` (runtime-tweakable settings; config.yaml remains the source for scoring)

**Deferred (designed, NOT built this session)**
- `paper_portfolios` — `id, name, created_at, rules_json`
- `paper_portfolio_positions` — `id, portfolio_id, stock_id, weight, opened_on, closed_on?, open_price, close_price?`

> Why a denormalized `scanner_results` *and* per-aspect score tables: the score tables keep each
> canonical value computed once with its component JSON (explainability + coherence); `scanner_results`
> is the immutable joined row each list reads, so the as-of view is a stored fact, never a recomputation.

---

## 6. API design

All read endpoints serve stored rows (no recomputation). JSON; errors as `{detail}`.

| Method | Path | Returns |
|--------|------|---------|
| GET | `/api/health` | `{status:"ok", last_run_date, db_ok, provider}` |
| GET | `/api/dashboard` | regime, counts{actionable,breakout,pullback}, top_sectors[], top_themes[], breadth, last_run, evidence_summary |
| GET | `/api/market-regime/latest` | `{score, label, components[]}` |
| GET | `/api/sectors?run_id=` | ranked sector/industry scores (defaults to latest run) |
| GET | `/api/themes?run_id=` | ranked theme scores + members |
| GET | `/api/themes/{theme_id}?run_id=` | one theme: members with their stock scores |
| GET | `/api/stocks?run_id=&theme=&sector=&setup=&min_score=&max_risk=&sort=` | filtered, ranked leaderboard rows |
| GET | `/api/stocks/{ticker}?run_id=` | detail: scores+components, setup, reason, invalidation, theme membership, sector RS, price series, score history |
| GET | `/api/scanner-runs` | list of runs (date, regime, counts, is_walk_forward) |
| GET | `/api/scanner-runs/{run_id}` | full as-of snapshot for that run |
| POST | `/api/scanner-runs/run` | trigger a scan for an as-of date (default latest seed date) → `{run_id}` |
| GET | `/api/system-health?horizon=` | forward returns by bucket/setup/regime, excess vs benches, control groups, sample sizes |
| GET | `/api/paper-portfolio` | *(deferred — 501 Not Implemented placeholder)* |
| GET | `/api/watchlist` | watchlist entries with current state |
| POST | `/api/watchlist` | add `{ticker, reason, notes?}` → entry |
| DELETE | `/api/watchlist/{id}` | remove |

`run_id` defaults to the latest non-walk-forward run; passing a historical `run_id` yields the
immutable as-of view (powers J-07/J-08).

---

## 7. Scoring framework

### 7.1 Shape (applies to all six scores)

```
score = clamp( Σ_i  weight_i × normalize_i(component_i) , 0, 100 )
```

- **Components** are explicit, named, and individually meaningful (e.g., `rs_vs_spy_3m`,
  `above_50dma`, `dist_from_52w_high`).
- **normalize** maps a raw component to 0–100: continuous components by **percentile rank within the
  day's universe** (regime/sector/theme-relative where appropriate); boolean components to 0/100.
- **weights** come from `config.yaml` and sum to 1 within each score (validated at load).
- Each score function returns `{value, bucket, components:[{name, raw, normalized, weight, contribution}]}`.
  This object *is* the explainability and the reason summary source.

### 7.2 Buckets (config edges; default)

`A: 90–100 · B: 80–89 · C: 70–79 · D: 60–69 · E: <60` — one `bucket()` function, used everywhere.

### 7.3 The three stock scores (default components — all tunable in config)

- **Leadership** ↑ with: RS vs SPY 1m & 3m, RS vs sector, RS vs theme basket, above 20/50/150/200-DMA,
  50>200-DMA, proximity to 52w high, up/down-volume.
- **Entry Quality** ↑ with: proximity to a *rising* 20/50-DMA, volatility contraction, nearby support,
  base/pullback structure, healthy reward:risk; ↓ with extension, vertical/climax moves, large gaps
  without consolidation. (A strong leader far above its 20-DMA scores high Leadership, low Entry.)
- **Risk** ↑ with: extension from 20/50-DMA, high ATR%, low liquidity, Risk-Off regime, weak sector,
  gap/climax behaviour, price below key MAs, deteriorating RS. (RSI may be a minor component; it must
  not dominate.)

### 7.4 Regime / Sector / Theme scores

- **Regime** (0–100 + label): SPY/QQQ/RSP/IWM vs 50/200-DMA; VIX level & trend (if available); % of
  universe above 50-DMA and 200-DMA; new-high vs new-low (**universe-relative, labelled**). Labels:
  Strong risk-on / Risk-on / Narrow leadership / Choppy / Defensive / Risk-off.
- **Sector** (per ETF): RS vs SPY 1/3/6m; vs 20/50/150/200-DMA; distance from 52w high; volume trend;
  internal breadth (where member data exists).
- **Theme**: average member Leadership; % members >50/200-DMA; % within 10% of 52w high; equal-weight
  basket return vs SPY (1m/3m); # members at new 20-day/52-week highs; breadth expansion. **Price-
  confirmed, not news-driven.**

### 7.5 Decision rules (setup classification, config thresholds, regime-gated)

```
if regime == Risk-Off:            → no Actionable; produce watchlist-only labels
elif theme_score < theme_floor:   → Avoid (even if the chart looks good)        [theme_floor default 70]
elif leadership ≥ 80 and entry ≥ 70 and risk < 60:   → Actionable
elif leadership ≥ 85 and entry < 50:                 → Extended (watch for pullback)
elif leadership ≥ 75 and breakout_pattern:           → Breakout-watch
elif leadership ≥ 75 and pullback_pattern:           → Pullback-watch
elif risk > 80:                                      → Avoid
else:                                                → Risk-off-watchlist / none
```

All cutoffs (80/70/60/85/50/75/70/80) live in `config.yaml`.

### 7.6 `config.yaml` shape (illustrative)

```yaml
provider: seed            # seed | stooq
universe: { source: [sp500_seed, ndx_seed, custom], filters: { min_market_cap: 2_000_000_000, min_dollar_vol: 50_000_000, min_price: 10 } }
buckets: { A: 90, B: 80, C: 70, D: 60 }
scores:
  leadership: { weights: { rs_spy_1m: 0.15, rs_spy_3m: 0.20, rs_sector: 0.15, rs_theme: 0.10, ma_stack: 0.20, high_proximity: 0.10, up_down_vol: 0.10 } }
  entry_quality: { weights: { dist_rising_20: 0.25, contraction: 0.20, support_nearby: 0.15, structure: 0.20, reward_risk: 0.20 }, extension_penalty: { ... } }
  risk:         { weights: { extension: 0.20, atr_pct: 0.15, liquidity: 0.10, regime: 0.15, sector_strength: 0.10, gap_climax: 0.15, below_ma: 0.10, rs_deterioration: 0.05 } }
regime:  { weights: { ... }, vix_threshold: 20 }
themes:  { ai_data_centre: [NVDA, AMD, AVGO, MRVL, ANET, DELL, SMCI, VST, CEG, ETN, PWR, GEV, VRT, TT, CARR, MU, WDC, STX, MSFT, AMZN, GOOGL, ORCL], ... }
decision_rules: { theme_floor: 70, actionable: { leadership: 80, entry: 70, risk: 60 }, extended: { leadership: 85, entry: 50 }, watch: { leadership: 75 }, avoid_risk: 80 }
walk_forward:  { history_years: 2, asof_cadence: weekly, horizons: [1, 5, 10, 20, 60] }
```

---

## 8. Validation methodology

The core claim — *"higher-ranked stocks/themes/setups outperform benchmarks"* — is tested, never
assumed.

1. **Immutable snapshots.** Each scan persists run + score rows + the joined `scanner_results`. Never
   mutated. Forward returns are a separate append-only table keyed to `(run_id, stock_id, horizon)`.
2. **Walk-forward (no-lookahead).** `walk_forward(dates)` calls `run_scan(as_of=D)` for many past D
   using only `daily_prices.date ≤ D`. Then `update_forward_returns()` computes, for each
   `(run, stock, horizon h)`, the realized return from `D` to `D+h` and excess vs SPY/QQQ/sector using
   only `date > D`. A dedicated unit test asserts that altering any bar with `date > D` changes forward
   returns but **never** changes the as-of score.
3. **Buckets.** Forward returns aggregated by A–E bucket; the system is useful only if higher buckets
   show better forward returns than lower buckets **over a meaningful n** (sample size always shown).
4. **By setup & by regime.** Returns split by setup status and by regime label — "do Actionable beat
   Extended?", "do breakouts work only in risk-on?".
5. **Control groups (separating selection from sector beta).** For the top-ranked cohort, compare
   forward returns to: random same-sector stocks, random similar-market-cap, SPY, QQQ, sector ETF.
   This is the honesty check (J-10).
6. **Stated limitations (surfaced in UI, per anti-goals).** Survivorship bias (current-membership
   universe), universe-relative breadth, no corporate-action engine at runtime, small-n caution. The
   gold standard remains **live forward** snapshots accumulating over time; the walk-forward is the
   bootstrap.

**Evidence verdict (shown on System Health):** "positive evidence" only when bucket monotonicity holds
roughly (A≳B≳…≳E), top cohort beats SPY/QQQ *and* its random same-sector control, at an n above a
configured floor — otherwise "insufficient / mixed evidence", stated plainly.

---

## 9. Risks and mitigations

| # | Risk | Mitigation |
|---|------|-----------|
| 1 | **Survivorship bias** (current index members) | Accept for MVP; label it; treat live-forward as the gold standard; walk-forward is a bootstrap, not proof. |
| 2 | **Lookahead bias** | As-of windows (`date ≤ D` for scoring, `date > D` for returns) + a dedicated no-lookahead unit test; immutable snapshots. |
| 3 | **Theme hindsight bias** | Themes are explicit config; Theme Score is price-confirmed; forward-test themes from their definition date. |
| 4 | **Overfitting** | Few components, all weights in config, no per-name tuning; validate on buckets/control groups, not anecdotes. |
| 5 | **News hype** | No news in MVP; price/volume confirmation only. |
| 6 | **Late-signal / extension** | Entry Quality + Risk explicitly separate "great stock" from "buyable now". |
| 7 | **Regime dependency** | Regime-gated decision rules; forward returns split by regime. |
| 8 | **Sector-beta confusion** | Control groups vs random same-sector + sector ETF (J-10). |
| 9 | **Data quality** (gaps, splits, ticker changes) | Provider abstraction + `data_provider_runs` log; seed is pre-adjusted; failures surface as stale, never fabricated. |
| 10 | **False precision** | Buckets foregrounded; sample sizes shown; "insufficient evidence" is a first-class verdict. |
| 11 | **Trading psychology** | UI shows invalidation + evidence, never a bare "buy"; discourages impulsive action. |
| 12 | **Execution risk** | Explicitly out of scope; no order path exists. |
| 13 | **Goal-mode flakiness** (new) | Deterministic seed + relational/structural acceptance (no magic-number assertions) so journeys don't break when weights are tuned. |
| 14 | **Walk-forward small-n** (new) | Configurable cadence/horizons; always display n; verdict gated on a sample floor. |
| 15 | **Seed realism** (new) | Seed engineered to contain real risk-on and risk-off stretches and genuine leaders/laggards so journeys are meaningful. |

---

## 10. Implementation phases (as goal-mode iterations)

Goal mode decomposes adaptively from failing journeys; this is the expected order, not a hard script.

| Iter | Focus | Journeys lit | 
|------|-------|--------------|
| 0 | Baseline verify (greenfield) | — (everything fails; baseline maps the gap) |
| 1 | Foundation: FastAPI health + config + DB models + provider abstraction + SeedProvider + **one-shot ingest → build & commit the frozen seed (real Stooq EOD; risk-on + risk-off stretches)** + seed load + Next.js shell | (infra) |
| 2 | Indicators + Regime + Sectors → Dashboard regime/sector parts + Sector Leaderboard | J-04, part of J-01 |
| 3 | Themes + 3 stock scores + bucketing (canonical values) + Stock Leaderboard + Theme Leaderboard | J-02, J-03, J-06, rest of J-01 |
| 4 | Setups + reasons + invalidation + Stock Detail (chart + breakdowns) + regime-gating *logic* | J-05 |
| 5 | Scanner snapshots + Scanner Runs pages (immutability); seed a Risk-Off historical run + ≥1 earlier run so both journeys have stored runs to open | J-07, J-08 |
| 6 | Walk-forward + forward returns + aggregates + control groups + System Health | J-09, J-10 |
| 7 | Watchlist (persistence) + polish | J-11 |

(Order may merge/split; the decomposer chooses. Paper-portfolio and news are **later sessions**.)

---

## 11. To-do list (pre-implementation, human)

- [ ] Approve `docs/goal.md` and this design doc.
- [ ] Configure `.claude/project-template.md` for Trendora (stack, test/start commands, ports, never-commit).
- [ ] Add `apps/backend/data/*.db`, `node_modules/`, `.next/`, `.venv/`, `.env*` to gitignore (root .gitignore already covers most).
- [ ] Ports auto-offset per project path (default backend 8835 / frontend 3835; override via `CHAIN_BACKEND_PORT` / `CHAIN_FRONTEND_PORT`) — confirm no collision with other local projects.
- [ ] Decide the live refresh provider to wire after MVP (Stooq vs Tiingo) — not needed for the seed-only MVP.
- [ ] `./scripts/automation/run-goal.sh --session-id trendora` (review the drafted blueprint at the baseline pause).

---

## 12. Open questions

1. **Seed sourcing.** ✅ Resolved — a one-shot ingest script fetches real EOD history from Stooq (free,
   no key) **in iteration 1**, then commits and freezes it; the build loop never re-fetches. (Still
   open: any preferred symbols beyond the example-theme members + ETFs?)
2. **Walk-forward window.** Default `history_years: 2`, weekly as-of cadence — enough n for the evidence
   verdict, or go daily / 3 years (bigger fixture, slower scans)?
3. **Theme-detail page.** MVP shows members inline on the Theme Leaderboard; do you want a dedicated
   `/themes/[id]` page now or later? (API endpoint exists regardless.)
4. **Corporate actions.** MVP uses pre-adjusted seed prices with no runtime split/dividend engine — OK
   as a documented limitation for now?
5. **Bucket edges & decision cutoffs.** Defaults proposed in §7; tune now or after first walk-forward?
6. **Charts library.** Lightweight-Charts (finance-native, candles) vs Recharts (simpler) — preference?

(None of these block starting; I've chosen sensible defaults that goal mode can run with.)

---

## 13. Recommended first build task

**Iteration 1 — Foundation & deterministic spine.** Stand up `apps/backend` (FastAPI `/health`, config
loader, SQLModel models + `create_all`, the `PriceProvider` ABC + `SeedProvider`) and `apps/frontend`
(Next.js shell + nav + API client), wired by the dev-chain start scripts on the offset ports. **Build
the seed once:** a one-shot ingest script fetches real EOD history from Stooq for the universe + ETFs,
writes the frozen fixture under `apps/backend/data/seed/`, and commits it — after which the loop only
reads it (never re-fetches). Acceptance: backend `/health` returns ok with the committed seed loaded;
the frontend renders the nav shell and reads `/api/health`. This gives goal mode a green, deterministic
baseline to build every journey on — and proves the offline seed spine before any scoring exists.

> After approval, the next concrete step is **not** for me to write code — it's to configure
> `.claude/project-template.md` and hand off to `run-goal.sh`, which decomposes and builds against these
> journeys. I will not implement directly.
