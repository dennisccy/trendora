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
bucket-by-bucket, benchmark-relative evidence from day one. Beyond that aggregate view, the user can
**interactively pick any past date** to replay that day's full scan and read its realized
forward-test scorecard, and **detected price patterns (starting with VCP — the Volatility
Contraction Pattern)** are tracked and forward-tested alongside the rankings — so the user can judge
for themselves whether each idea actually works.

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
- Every setup status and detected pattern is **explained in the UI** from a single config-backed
  catalog: a Methodology/Glossary page lists each with its plain-language meaning, the exact
  thresholds from config, and a worked example, and every setup/pattern badge carries an inline
  explanation; an entry added to config appears in both places with no code change.
- A user can **browse the whole dashboard as of any past trading day** via a global as-of date
  switcher (default: latest), with a clear "viewing as-of D (historical)" indicator, and can open a
  **Backtest workspace** to see that date's full scan plus a **forward-test scorecard** of how that
  date's cohort performed — realized 1/5/10/20/60-day and excess returns vs SPY/QQQ/sector and a
  random same-sector control — computed only from seed bars after D, with sample size and
  partial-horizon (NA) cases shown honestly.
- **Pages are served from persisted snapshots, not per-request recomputation**: each read endpoint
  returns canonical values stored for the resolved as-of date (computed once per date, then read
  from storage), a warm page reaches interactive in **under ~1.5 s**, and the same value still reads
  identically across pages.
- **VCP is detected as a config-driven pattern flag**: flagged stocks show a VCP badge with a
  plain-language reason and a concrete invalidation level (pivot / last-contraction low), are
  filterable on the leaderboard, are documented in the glossary, and appear as a **VCP-vs-non-VCP
  forward-return breakdown** (with sample size; NA below the min-sample threshold) so the evidence
  shows whether VCP-flagged names actually outperform.

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
16. **Setup & pattern glossary + inline explanations**: a single config-backed catalog of every
    setup status AND every detected pattern (plain-language meaning, the thresholds that define it,
    and a worked example), surfaced as a dedicated Methodology/Glossary page and as inline info
    tooltips on every setup/pattern badge; adding a new status or pattern to config makes it appear
    everywhere with no code change.
17. **Interactive as-of date selection** (historical replay + per-date forward test): a global
    as-of date switcher re-points the whole dashboard to any past trading day's immutable snapshot
    (strict no-lookahead), plus a dedicated **Backtest / Time-Machine** workspace to pick a date,
    view its full as-of scan, and read a per-date **forward-test scorecard** — how that date's
    ranked cohort / setups actually performed vs SPY/QQQ/sector and a random same-sector control at
    1/5/10/20/60 days — measured only from post-snapshot seed bars.
18. **Snapshot-served reads** (performance): every read endpoint serves canonical values from the
    persisted immutable snapshot for the resolved as-of date instead of recomputing the scan per
    request; a date viewed for the first time is computed once, persisted, and served from storage
    thereafter.
19. **VCP detection (Volatility Contraction Pattern)** — the first **detected pattern**: a
    rule-based, price+volume detector (progressively shallower pullbacks + volume dry-up into a
    pivot near the highs) whose thresholds live in config. It rides each stock row as a separate
    flag (with pivot + invalidation level) ALONGSIDE the setup status — it does not replace it — is
    filterable on the leaderboard, documented in the glossary, and tracked as a forward-test
    dimension (VCP vs non-VCP) so the evidence shows whether it adds value.

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
- **Methodology / Glossary** (`/methodology`) — explains the three scores, A–E buckets, the six
  regime labels, every setup status, AND every detected pattern (incl. VCP) — generated from the
  config-backed catalog.
- **Backtest / Time-Machine** (`/backtest`) — pick any historical as-of date; see its full as-of
  scan (read from the canonical snapshot) and a **per-date forward-test scorecard**. This is the
  single-date drill-down; System Health remains the cross-date aggregate, and Scanner Runs remains
  the immutable run list.

A global **as-of date switcher** in the top bar re-points Dashboard, Stocks, Themes, Sectors, and
Stock Detail to a chosen past snapshot (default: latest). The as-of date resolves to a stored
immutable snapshot — created once on first view, then never mutated. The **Stock Leaderboard**
(`/stocks`) gains a **VCP filter**, and **System Health** gains a **VCP-vs-non-VCP** forward-return
breakdown alongside its by-setup breakdown.

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
- **Setup & pattern catalog** (definition + thresholds + example) — one config-backed source; the
  glossary page and every inline tooltip read it, never re-describing an entry independently.
- **Detected patterns** (incl. VCP) — computed once per run by the pattern detector from config
  thresholds; the flag plus its pivot/invalidation level ride the stock row, and every view reads
  the same stored value.

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

- **J-12: Understand what each setup/pattern means (glossary + inline)**
  - Steps:
    1. Visit `/methodology`
    2. Read the entries for the six setups (Actionable, Breakout-watch, Pullback-watch, Extended,
       Avoid, Risk-off-watchlist) and for the VCP pattern
    3. Confirm each shows a plain-language meaning, the threshold rule that defines it, and an example
    4. On `/stocks`, hover/tap a setup badge and read its inline explanation
  - Acceptance: all six setup statuses and the VCP pattern are listed, each with (a) a plain-language
    description, (b) the thresholds that produce it (matching config), and (c) a worked example; the
    inline tooltip on a leaderboard badge shows the same definition; the list is generated from the
    config-backed catalog, so an entry added in config renders with no code change.

- **J-13: Browse the dashboard as of a past date (global as-of switcher)**
  - Steps:
    1. On `/`, open the as-of date switcher
    2. Select a past trading day
    3. Observe that `/`, then `/stocks`, `/themes`, and `/sectors` reflect that date
    4. Confirm a "viewing as-of D (historical)" indicator is shown
    5. Switch back to the latest date
  - Acceptance: selecting a past date re-points every page to that date's stored snapshot; the values
    match that date's Scanner Run (not the latest); a clear historical indicator is visible; no
    future-dated bar influences the as-of values; returning to latest restores the current view.

- **J-14: Backtest a past date and read its forward-test scorecard**
  - Steps:
    1. Visit `/backtest`
    2. Pick a historical as-of date with at least 60 post-snapshot bars
    3. Read the as-of scan summary (regime, top sectors/themes, the ranked Actionable/watch cohort)
    4. Read the forward-test scorecard — realized 1/5/10/20/60-day returns, excess vs SPY/QQQ/sector,
       and vs a random same-sector control
    5. Pick a recent date and confirm the longer horizons show NA rather than a fabricated number
  - Acceptance: for the chosen date the page shows the as-of cohort AND numeric forward returns by
    horizon with excess-vs-benchmark and control-group columns and sample size (n); returns are
    computed only from seed bars after D (no-lookahead); a date without enough post-snapshot bars
    shows partial/NA horizons rather than fabricated numbers.

- **J-15: Fast page loads from persisted snapshots**
  - Steps:
    1. Load `/stocks` for the latest date
    2. Reload the page
    3. Load `/`, `/themes`, and `/sectors`
  - Acceptance: the leaderboard renders its rows from the stored snapshot for the as-of date (not
    recomputed per request) and reaches interactive within the load budget (warm load < ~1.5 s); the
    values remain identical to the Stock Detail page (coherence preserved).

- **J-16: VCP — detected, explained, filterable, forward-tested**
  - Steps:
    1. On `/stocks`, apply the **VCP** filter
    2. Confirm flagged rows show a VCP badge plus a reason and an invalidation level
    3. Open one flagged stock; confirm the detail page shows the VCP badge with its pivot/invalidation
    4. On `/methodology`, read the VCP glossary entry
    5. On `/system-health`, read the VCP-vs-non-VCP forward-return breakdown
  - Acceptance: the VCP filter shows only flagged names (or an explicit empty-state if none in the
    current snapshot); each flagged row shows the badge + reason + a concrete invalidation level
    (pivot / last-contraction low); the glossary lists VCP with its meaning, the config thresholds
    that define it, and an example; System Health shows mean forward returns for VCP vs non-VCP with
    sample size n (NA below the min-sample threshold) derived from the walk-forward snapshots; the VCP
    flag is computed once on the backend and reads identically on leaderboard and detail. The VCP flag
    is SEPARATE from the setup status (a name can be both, e.g. "Breakout-watch" + VCP) and never makes
    a name Actionable on its own.

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
- **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted
  immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per
  request. The scan is computed once per date (bootstrap, scheduled, or first view) and then read
  from storage. *(extends Single source of truth)*
- **On-demand snapshots stay immutable & lookahead-free.** Creating a snapshot for a newly selected
  date is create-once: an existing snapshot MUST be read, never overwritten; an as-of-D snapshot MUST
  use only bars with date ≤ D. *(critical)*
- **Setup & pattern vocabulary is config-driven in the UI too.** The glossary and tooltips MUST be
  generated from the single config-backed catalog — no hard-coded per-entry copy or status/pattern
  list in the frontend — so a new status or pattern is explained automatically. *(extends No magic
  numbers)*
- **Honest forward-test for partial windows.** The per-date forward-test scorecard and the
  VCP-vs-non-VCP breakdown MUST show NA/partial for horizons or cohorts lacking enough samples and
  MUST show sample size — never fabricate or extrapolate a return to fill a gap. *(extends No
  fabricated data)*
- **VCP is a pattern, not a status.** VCP MUST NOT enter the mutually-exclusive setup-status enum and
  MUST NOT by itself promote a name to "Actionable"; it rides as a separate flag computed once per run,
  price+volume only, with date ≤ D (no-lookahead), and is part of the immutable snapshot. Its
  detection thresholds MUST come from config (no magic numbers). *(critical — protects Single source
  of truth + Risk-Off gating)*
