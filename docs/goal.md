# Project Goal

## Vision

Trendora is a **local-first, research-only US equity leadership scanner** — a decision-support and
evidence-tracking platform, **not** an auto-trading bot. After the close it produces a daily ranked
view of the market — **market regime → sectors → industry groups → themes → individual stocks** — and
for each stock it reports three deliberately *independent* measures:

- **Leadership Score** — how strong the stock is.
- **Entry Quality Score** — whether the current price location is buyable or already too extended.
- **Risk Score** — danger factors (extension, volatility, weak regime, weak sector, climax, poor liquidity).

These are never collapsed into one oversimplified "buy" number, so a great leader at a terrible entry
(high Leadership, low Entry Quality) is labelled exactly that. Every score is **explainable** — it
carries the named components that produced it and a plain-language reason + invalidation note.

Trendora's most important job is to **prove its own usefulness**. Every scan is saved as an
**immutable snapshot**, and a **forward-testing engine** measures whether higher-ranked stocks,
themes, and setups actually outperform SPY, QQQ, sector ETFs, and **random same-sector peers** over
1 / 5 / 10 / 20 / 60 trading days. Because live evidence takes calendar months to accumulate, the
system **bootstraps that evidence from history with a strict walk-forward**: it replays the scan
*as-of* many past dates using only data available on that date (no lookahead), then measures realized
forward returns from the data that came after. So the System Health page shows real,
bucket-by-bucket, benchmark-relative evidence from day one.

The MVP runs **fully offline on a committed seed dataset** (so every result is deterministic and
reproducible), behind a **provider abstraction** that lets a live end-of-day data source refresh the
data later. It places **no orders** and holds **no broker keys**.

## Target Users

- The repository owner — a self-directed swing/position trader who wants to fish only in strong areas
  (strong theme → strong sector → strong stock → acceptable entry) instead of trading weak single-name
  setups, and who wants hard evidence that the rankings work *before* trusting them with money.
- Any quant-minded retail trader who wants a skeptical, explainable, "cost-of-being-wrong"-aware
  leadership scanner that foregrounds invalidation levels and forward-tested evidence over news hype.

## Success Criteria

- A daily scan produces, from the seed dataset, a complete immutable snapshot: a **market regime**
  (score 0–100 + one of six labels), ranked **sector/industry** scores, ranked **theme** scores, and
  per-stock **Leadership / Entry Quality / Risk** scores, a **setup status**, a **reason summary**, and
  an **invalidation note** — all reproducible across restarts because the default data provider is the
  committed seed.
- The same canonical value (any of the six scores, the setup status, the regime label, the A–E bucket)
  reads **identically everywhere it appears** — leaderboard, detail page, dashboard — because it is
  computed once in the scoring engine and only re-formatted by the UI.
- Each stock's three scores are presented as **A–E buckets foregrounded with the raw 0–100 secondary**,
  and every displayed score exposes its **component breakdown** (component → contribution) — no
  black-box numbers.
- In a seeded **Risk-Off** regime, the scanner marks **zero stocks "Actionable"** and produces
  watchlist-only labels; in a risk-on regime it produces Actionable / Breakout-watch / Pullback-watch
  candidates per the config thresholds.
- The **walk-forward forward-testing engine** computes 1/5/10/20/60-day forward returns and excess
  returns vs SPY, QQQ, and sector ETF for past snapshots **using only post-snapshot data**, and the
  System Health page renders forward return **by score bucket (A–E)**, **by setup type**, and **by
  regime**, plus a **control-group comparison** (top-ranked cohort vs random same-sector cohort vs
  SPY/QQQ/sector ETF) so sector beta is visibly separated from stock selection.
- Scanner runs are **append-only and immutable**: opening a past run shows exactly what the scanner
  said on that date (different from the latest run), and forward returns are stored in a separate table
  keyed to the snapshot — the snapshot itself is never mutated.
- A user can build a **watchlist** that persists across a backend restart, each entry carrying the
  date added, the reason, the current score/setup, price-since-added, and an invalidation level.
- All scoring weights, thresholds, the stock universe, and the theme definitions live in **one config
  file** — no scoring literal is hard-coded — so the model can be tuned and improved without code
  changes.
- Unit tests cover indicator math, relative-strength and bucket logic, scoring consistency, **the
  no-lookahead guarantee** in walk-forward, and snapshot immutability; the app boots and serves all
  pages offline against the seed.

## Key Capabilities

1. **Provider abstraction** for daily OHLCV: a deterministic **SeedProvider** (reads the committed
   fixture; the default, requires no network or keys) and a swappable **live provider** (free EOD
   source) selected by config.
2. **Universe + ETF management**: a seed universe (~120–150 liquid US common stocks spanning the
   example themes) plus index ETFs (SPY, QQQ, IWM, RSP), the 11 sector ETFs, and the industry-group
   ETFs, with the liquidity/price/market-cap filter rules recorded in config.
3. **Indicator engine**: moving averages (20/50/150/200), relative strength vs SPY/sector/theme, ATR%,
   volume metrics, distance from 52-week high, volatility contraction, extension from 20/50-DMA,
   drawdown from recent high.
4. **Market Regime engine** → score 0–100 + label (Strong risk-on / Risk-on / Narrow leadership /
   Choppy / Defensive / Risk-off).
5. **Sector & industry leadership** scoring from sector/industry ETFs (RS vs SPY over 1/3/6m, MA
   stack, distance from 52w high, volume trend, internal breadth).
6. **Theme engine**: manually-defined themes (config) mapping stocks→themes (many-to-many), with a
   price-confirmed Theme Score (not news-driven).
7. **Three independent stock scores** — Leadership, Entry Quality, Risk — each a weighted sum of
   normalized, **named, explainable components** with weights from config; presented as A–E buckets.
8. **Setup classification**: Actionable, Pullback-watch, Breakout-watch, Extended, Avoid,
   Risk-off-watchlist (Post-earnings-gap-hold and RS-new-high-before-price defined but earnings-gap
   stubbed until earnings data exists).
9. **Daily scanner** that runs the full pipeline and writes an **immutable snapshot**; runnable on a
   schedule (APScheduler) or on demand via the API.
10. **Walk-forward backfill** that replays the scan as-of past dates with **strict no-lookahead**, plus
    a **forward-returns** job that measures realized 1/5/10/20/60-day and excess returns.
11. **System Health / evidence** analytics: forward returns by bucket, by setup, by regime, excess vs
    SPY/QQQ/sector, and random-same-sector control groups.
12. **Watchlist** with persistence, reason, current state, price-since-added, and invalidation.
13. A **dense, dark analytical web dashboard**: Dashboard, Stock Leaderboard, Theme Leaderboard, Sector
    Leaderboard, Stock Detail, Scanner Runs, System Health, Watchlist.
14. *(nice-to-have)* Edit scoring weights/thresholds from a config view.
15. *(nice-to-have)* Historical charts of a stock's scores across past snapshots.

## Non-Goals

- **No order execution, no auto-trading, no brokerage integration, no capital deployment** — Trendora
  is decision-support and research only.
- No options/options-flow, no intraday/scalping — **daily candles and end-of-day analysis only**.
- No machine-learning price prediction.
- No social-media sentiment, and **no news/LLM catalyst enrichment in this session** (deferred to a
  later session; the technical core must work first).
- **No paper-portfolio module in this session** (the data model leaves room for it; deferred to a
  later session).
- Not the full US market on day one — a curated seed universe of liquid names; expansion later.
- Not 100 indicators — a small, testable, explainable set; RSI may exist as a minor component but must
  not dominate scoring.
- Not financial advice; not a real-time signal/alert service.

## Constraints

- **Runs locally and offline by default.** The committed seed dataset makes every scan deterministic
  and reproducible with no network and no API keys. A live EOD provider is optional, config-selected,
  and its key (if any) comes only from the environment — never committed.
- Backend: **Python 3.12, FastAPI (uvicorn), SQLModel over SQLite** (Postgres-ready — engine URL is
  config, no raw SQLite-only SQL), Pandas, APScheduler, Pydantic, pytest.
- Frontend: **Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui**, Lightweight-Charts (or
  Recharts) for charts.
- **One config file** (`config.yaml`) holds every tunable: scoring weights, thresholds, decision-rule
  cutoffs, bucket edges, the universe list + filters, theme definitions, provider selection, and
  walk-forward parameters. No scoring/threshold literal is hard-coded in calculation code.
- The backend is the **single source of truth**; the frontend only re-formats values from the API and
  never recomputes a score, return, or bucket.
- The app lives entirely under **`apps/`** (`apps/backend`, `apps/frontend`) so it never clobbers the
  embedded dev-chain's root symlinks (`config`, `scripts`, `tests`, `templates`). Ports are
  **auto-offset per project** by the dev-chain start scripts (default backend 8835 / frontend 3835;
  honors `CHAIN_BACKEND_PORT` / `CHAIN_FRONTEND_PORT`) so it can run alongside other projects.
- Keep the design small, testable, and extensible: structure it so paper-portfolio and news enrichment
  *could* be added later, but they must not exist in this version.

## Design Direction

- Visual style: a **dense, dark, data-forward analytical workstation** — numeric tables, compact metric
  cards, colour-graded leaderboards and a heatmap-style score grid. Not a flashy consumer trading-app
  aesthetic. (Reference: the analytical dashboards of `gap_gap_filler` / `finovae_strategy_platform`.)
- Mood: **skeptical and evidence-driven**. The product exists to *earn* trust, so invalidation levels,
  reason components, honest limitations, and forward-tested evidence are always visible alongside any
  ranking. Numbers are monospace/tabular; scores show as A–E buckets first to resist false precision.
- The UI must **discourage impulsive buying**: it ranks, explains, shows what would invalidate an idea,
  and shows whether the scanner has positive evidence — it never says a bare "buy this".

## Product Shape

### Navigation / information architecture

- **Dashboard** (`/`) — the daily snapshot at a glance: regime, top sectors, top themes, candidate
  counts, breadth, last-run time, evidence summary.
- **Stocks** (`/stocks`) — the Stock Leaderboard (ranked, filterable). Rows link to Stock Detail.
- **Stock Detail** (`/stocks/[ticker]`) — one stock's chart, score breakdowns, theme membership, setup,
  reason, invalidation, and per-snapshot history. Reached from a leaderboard row, not a top-nav tab.
- **Themes** (`/themes`) — the Theme Leaderboard (ranked, with members + breadth).
- **Sectors** (`/sectors`) — the Sector/Industry Leaderboard.
- **Scanner Runs** (`/scanner-runs`, `/scanner-runs/[runId]`) — history of immutable runs; open one to
  see the exact as-of view for that date.
- **System Health** (`/system-health`) — the forward-tested evidence: returns by bucket/setup/regime,
  excess vs benchmarks, and control-group comparisons.
- **Watchlist** (`/watchlist`) — user-saved stocks with reason, current state, price-since-added, and
  invalidation.

The backend is the single source of truth; every page only displays server-computed values.

### Canonical values (single source of truth — computed once, displayed identically everywhere)

- **Market Regime Score + label** — computed once per scanner run by the regime engine.
- **Sector Score** (per sector/industry ETF) — computed once per run.
- **Theme Score** (per theme) — computed once per run.
- **Leadership Score, Entry Quality Score, Risk Score** (per stock) — each computed once per run by the
  scoring engine; the dashboard, leaderboard, and detail page all read the same stored value.
- **A–E bucket** — derived once from a score by the single bucketing function (config edges).
- **Setup status** (per stock) — computed once per run from scores + regime + detected pattern.
- **Forward-return aggregates** (by bucket / setup / regime, and excess vs benchmarks) — computed once
  by the forward-testing engine from stored snapshots + post-snapshot prices; never recomputed in a view.

## Must-have user journeys

- **J-01: Daily dashboard at a glance**
  - Steps:
    1. Visit `/`
    2. Read the Market Regime panel (label + 0–100 score)
    3. Read the candidate counts: # Actionable, # Breakout-watch, # Pullback-watch
    4. Read the Top Sectors and Top Themes lists, the market-breadth figure, and the last-scan timestamp
  - Acceptance: the regime label is one of the six defined labels with a numeric score; the three
    candidate counts each render a number; at least 3 top sectors and at least 3 top themes are listed
    (each with a score); a breadth percentage and a last-scan timestamp are shown.

- **J-02: Stock Leaderboard with working filters**
  - Steps:
    1. Visit `/stocks`
    2. Confirm the table is ranked and each row shows ticker, Leadership, Entry Quality, Risk (as A–E
       bucket + number), setup status, and a non-empty reason summary
    3. Apply the Sector filter to a single sector and observe the rows change
    4. Apply the Setup-status filter to "Actionable"
  - Acceptance: the leaderboard renders multiple ranked rows each with three bucketed scores, a setup
    status, and a reason; selecting a sector reduces the visible rows to that sector only; selecting
    "Actionable" shows only rows whose setup status is Actionable (or an explicit empty-state if none).

- **J-03: Theme Leaderboard**
  - Steps:
    1. Visit `/themes`
    2. Confirm themes are listed in descending Theme Score order
    3. For the top theme, read its top member stocks, its 1-month and 3-month basket return, its breadth
       figure, and its trend label
  - Acceptance: at least 3 themes render ranked by Theme Score (non-increasing); the top theme shows a
    list of member tickers, numeric 1m and 3m returns, a breadth percentage, and a trend label.

- **J-04: Sector / industry Leaderboard**
  - Steps:
    1. Visit `/sectors`
    2. Confirm sector/industry ETFs are ranked by Sector Score
    3. For the top row read RS-vs-SPY, distance-from-52-week-high, and the trend label
  - Acceptance: sector/industry ETFs render ranked by score; each row shows a numeric RS-vs-SPY value, a
    distance-from-52w-high percentage, and a trend label; SPY itself is shown as the 0% RS reference or
    excluded, not ranked as a leader against itself.

- **J-05: Stock Detail with explainable scores**
  - Steps:
    1. From the Stock Leaderboard, click `NVDA` (or any listed leader) to open `/stocks/NVDA`
    2. Confirm a price chart with moving averages and a volume series renders
    3. Expand each of the three scores (Leadership, Entry Quality, Risk) and read their component
       breakdowns
    4. Read the theme-membership chips, the setup status, the reason summary, and the invalidation note
  - Acceptance: the detail page shows a price+MA chart and volume; each of the three scores shows its
    A–E bucket, its 0–100 value, and at least 3 named contributing components; theme membership, setup
    status, a reason summary, and a concrete invalidation level (e.g., "below 50-DMA at $X") all render.

- **J-06: Score consistency across pages (coherence)**
  - Steps:
    1. On `/stocks`, note `NVDA`'s Leadership, Entry Quality, and Risk scores (number + bucket)
    2. Open `/stocks/NVDA`
    3. Compare the three scores on the detail page to the leaderboard
  - Acceptance: NVDA's Leadership, Entry Quality, and Risk scores (and their A–E buckets) are identical
    on the leaderboard and the detail page — one computed value per score, never recomputed per view.

- **J-07: Risk-Off regime suppresses Actionable**
  - Steps:
    1. Visit `/scanner-runs`
    2. Open the seeded run dated on a Risk-Off day (its row is labelled Risk-Off / Defensive)
    3. Read that run's regime panel and its stock results
  - Acceptance: the opened run's regime label is Risk-Off (or Defensive) and **no** stock in that run
    carries the setup status "Actionable" — the scanner produced watchlist-only labels for that regime,
    demonstrating regime gating.

- **J-08: Immutable scanner-run history**
  - Steps:
    1. Visit `/scanner-runs`
    2. Confirm at least two dated runs are listed
    3. Open an older run and read its top-ranked stocks and their scores
    4. Return and open the latest run
  - Acceptance: multiple dated runs are listed; the older run's rankings/scores are shown as stored for
    that date and differ from the latest run's — confirming each snapshot is an immutable as-of view, not
    a recomputation of today's numbers.

- **J-09: System Health forward-tested evidence**
  - Steps:
    1. Visit `/system-health`
    2. Read the "forward return by score bucket" table/chart (buckets A–E) for a horizon (e.g., 20-day)
    3. Read the excess return vs SPY and vs QQQ
    4. Read the breakdown of forward return by setup type and by market regime
  - Acceptance: a by-bucket forward-return table renders numeric mean returns for buckets A–E at a stated
    horizon; numeric excess-vs-SPY and excess-vs-QQQ values render; a by-setup-type and a by-regime
    breakdown each render numbers — all derived from the walk-forward snapshots, with the sample size (n)
    shown so the evidence is not presented as more certain than it is.

- **J-10: Control-group honesty (selection vs sector beta)**
  - Steps:
    1. On `/system-health`, locate the control-group comparison
    2. Read the forward return of the top-ranked cohort, the random-same-sector cohort, SPY, QQQ, and the
       relevant sector ETF for the same horizon
  - Acceptance: for a stated horizon the page shows the top-ranked cohort's forward return alongside a
    random-same-sector cohort and SPY/QQQ/sector-ETF returns, each numeric and labelled, so a reader can
    see whether the ranking adds value beyond simply being in a hot sector.

- **J-11: Watchlist with persistence**
  - Steps:
    1. Open `/watchlist`
    2. Add `ANET` with a free-text reason ("ANET — strong leader, watching pullback")
    3. Confirm it appears with date-added, the reason, its current score/setup, price-since-added, and an
       invalidation level
    4. Restart the backend (or reload after a restart) and revisit `/watchlist`
  - Acceptance: the added stock appears immediately with date-added, reason, current Leadership/Entry/Risk
    + setup, a price-since-added figure, and an invalidation level; after a backend restart the entry is
    still present (persisted in the database), proving the watchlist is not in-memory only.

## Anti-goals

- **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward
  returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar
  influences an as-of score. *(critical)*
- **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or
  overwritten after creation; forward returns live in a separate append-only table keyed to the
  snapshot. *(critical)*
- **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status)
  MUST be computed exactly once by the scoring/regime engine and read identically by every page; the
  API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views.
  *(critical)*
- **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe
  entry, and theme definition MUST come from the config file — no such literal in calculation code.
- **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/
  unavailable state and MUST NOT synthesize prices or scores to force a green journey.
- **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or
  be reachable; Trendora is research-only. *(critical)*
- **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere; the default seed
  path requires none, and any live-provider key is read only from the environment.
- **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks
  "Actionable" (watchlist-only). *(critical)*
- **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no
  score may be shown as a bare number with no reasons.
- **Honest limitations surfaced.** Breadth and new-high/new-low metrics computed from the seed universe
  MUST be labelled "universe-relative" (not full-market internals), and walk-forward evidence MUST be
  labelled as carrying survivorship bias (current-membership universe) so results are never overstated.
- The frontend MUST NOT store auth tokens in `localStorage` (applies only if auth is ever added; this
  version has no auth).
