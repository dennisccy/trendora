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
forward returns from the data that came after. So the **Backtest workspace** shows real,
bucket-by-bucket, benchmark-relative evidence as of any chosen date — an expanding walk-forward window
of every snapshot dated ≤ that date. The user can **interactively pick any past date** to replay that
day's full scan, read its realized forward-test scorecard, and see that same as-of-scoped evidence, and
**detected price patterns (starting with VCP — the Volatility
Contraction Pattern)** are tracked and forward-tested alongside the rankings — so the user can judge
for themselves whether each idea actually works.

The MVP is **offline-first**: it boots and runs deterministically on a **committed seed dataset** (so
every result is reproducible), behind a **provider abstraction** that lets a live end-of-day data
source refresh the data later. A **Data Manager** lets the user extend the dataset on demand — fetching
more real EOD history via the config-selected live provider (real data only) and backfilling additional
immutable snapshots by date or date range — but the default boot path stays offline and deterministic.
It places **no orders** and holds **no broker keys**.

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
  **Backtest workspace** renders forward return **by score bucket (A–E)**, **by setup type**, and **by
  regime**, plus a **control-group comparison** (top-ranked cohort vs random same-sector cohort vs
  SPY/QQQ/sector ETF) — all scoped to the snapshots dated ≤ the selected as-of date — so sector beta is
  visibly separated from stock selection.
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
- **Data-dependent journeys never block the rest.** The expanded ~500-name universe (J-22) and the
  intraday multi-timeframe work (J-23/J-24) depend on a real data fetch the committed seed does not yet
  contain; the session retries that fetch best-effort on resume, and when the provider is unreachable it
  records those journeys as honestly blocked (NA) and **continues** — they never halt the loop or veto
  completion of the buildable journeys.

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
11. **Forward-tested evidence analytics (on Backtest)**: forward returns by bucket, by setup, by regime,
    excess vs SPY/QQQ/sector, and random-same-sector control groups — scoped to an expanding window of
    snapshots dated ≤ the selected as-of date.
12. **Watchlist** with persistence, reason, current state, price-since-added, and invalidation.
13. A **dense, dark analytical web dashboard**: Dashboard, Stock Leaderboard, Theme Leaderboard, Sector
    Leaderboard, Stock Detail, Scanner Runs, Watchlist.
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
20. **Data Manager (on-demand dataset growth + coverage clarity + seed-safe curation)**: a UI + API to
    grow, understand, and curate the dataset manually by date or date range. It can (a) **fetch** real
    EOD OHLCV via the config-selected live provider for a chosen date/range — extending beyond the
    committed seed, real data only (on provider failure it surfaces an explicit error and never
    fabricates prices) — and (b) **backfill** immutable scanner snapshots for a date/range from available
    bars (offline/deterministic). Fetching or backfilling a range **auto-generates** the scanner
    snapshots and forward returns for the new trading days, so the forward-test sample actually grows. It
    runs as an **async background job with live progress** (e.g. "fetched 80/158 symbols", "snapshots
    23/120 dates") and a final success/failure summary, and the run is recorded (extends the existing
    data-provider run log). The Data Manager also offers a **config-catalog source picker** (env-detected
    availability + an optional session-only key paste, never persisted/committed), a **chunked,
    rate-limit-aware import** that **checkpoints durably** and, on a persistent 429, **backs off → stops →
    exposes Resume** (continuing from the last completed chunk, no duplicate fetch, surviving a restart),
    and an **Expand-universe** job kind that screens the committed candidate pool from the UI (the
    operator-facing path that unblocks the expanded universe). Beyond growing data it makes the dataset
    **legible and curatable**: a **plain-language coverage explainer** (defining every figure and the
    **universe-vs-symbols** distinction — universe = the config-screened scored names; symbols = every
    ticker with bars, incl. index/sector/industry ETFs + `^VIX`) plus a **per-symbol / per-universe-member
    coverage table** (in-universe?, has-data?, date range, bar count, thin/missing flag); a **missing-data
    diagnostic** that flags what is **insufficient for analysis** — universe members with no or thin
    history (below the config history threshold) and intra-series date gaps — each with a **one-click
    "pull the missing data"** that fetches exactly the gap through the same chunked/resumable machinery; a
    **unified Unfinished-imports** section listing every non-completed import (paused, partial, failed)
    with a plain-language state explanation and the right action — **Resume** (rate-limited pause),
    **Retry remaining/failed** (idempotent — re-fetches only what is missing), or **Remove/Dismiss**
    (drops only the actionable job-control record, never the immutable run audit); and a **seed-safe
    Remove-data** control that deletes **only user-added bars** (beyond the committed seed, by symbol
    and/or date range) behind a **confirm-preview**, **cascade-removing the snapshots/forward-returns
    derived solely from them** so nothing is left inconsistent, while the **committed seed is never
    deletable**. Every coverage/diagnostic figure is **read-only descriptive metadata** (no canonical
    score/return/bucket recomputed), every threshold comes from config (**no magic numbers**), and the
    default boot path remains the committed offline seed.
21. **Unified as-of date control**: exactly one date selector — the global top-bar as-of switcher —
    governs every date-scoped page, **including Backtest**. Per-page date dropdowns are removed and the
    frontend holds no second, independent date state; "which date am I viewing" has a single source.
22. **Return attribution / contribution analysis**: beyond aggregate mean returns, the forward-test
    surfaces (a) **per-stock top contributors & detractors** (which individual tickers drove or dragged
    the cohort), (b) a **by-sector** breakdown (separating sector beta from stock selection), (c) a
    **by-rank-band** breakdown (e.g. 1–10 / 11–50 / 51+, testing whether the ranking itself adds value),
    and (d) **distribution & hit-rate** (median, % positive, dispersion) alongside the mean with sample
    size n — so a weak number is diagnosable (concentration, outliers, ranking efficacy) rather than
    taken at face value. Every slice is derived once from the stored per-observation forward-return data
    (never recomputed in the API or a view) and is surfaced on Backtest — both the per-date scorecard and
    the as-of-scoped aggregate (an expanding window of snapshots dated ≤ the as-of date).
23. **Full chart history through latest**: the Stock Detail price+MA+volume chart renders the complete
    path to the latest seed date with a clear **as-of marker**; the post-as-of region is labelled
    forward/after-as-of and is **display-only** — it never feeds a score, bucket, setup, pattern, or
    factor (those stay date ≤ D).
24. **Horizon-linked realized-return columns on Backtest**: Top Sectors / Top Themes / Ranked Cohort sit
    below Return Attribution and each carries a realized forward-return at the selected horizon (sector =
    sector-ETF return; theme = equal-weight member basket; cohort = the stock's own return), read from
    the stored forward returns and re-pointed by the horizon selector.
25. **Rule-based, reproducible ~500-name universe**: membership is defined by the config-recorded screen
    (min market cap / dollar-volume / price + any membership rule), transparent in the UI, and expandable
    via config + real committed seed — no hand-picked code list.
26. **Multi-timeframe bars (1D / 1h / 15m / 5m)**: a timeframe-aware store + provider + committed intraday
    seed with documented per-timeframe coverage windows; timeframe-scaled indicator/pattern periods from
    config; a chart timeframe selector; strict per-timeframe no-lookahead; daily remains the canonical
    swing timeframe.
27. **Factor Lab**: decile sort + **rank information coefficient (IC)** per factor, **multi-factor
    composite combination cohorts** (a config-weighted percentile rank-blend across any number of
    selected factors, oriented by side), and **regime-conditioned** factor effectiveness; the factor set
    includes an explicit **volatility family** (level / contraction / downside) and intraday-derived
    factors where coverage allows. Descriptive evidence only — not a fitted predictive model.
28. **Additional detected patterns beyond VCP**: ≥2 config-driven price/volume detectors (e.g.
    pullback-to-rising-DMA, flat-base breakout, RS-line new high, inside-day/tight-area), each
    forward-tested and following the VCP "pattern-not-status" contract.
29. **Setup & Pattern research lab (event study)**: pools every historical occurrence of a setup/pattern
    and reports the forward-return distribution, hit-rate, **expectancy**, **MAE/MFE** (max
    adverse/favorable excursion from post-snapshot daily highs/lows), best exit-horizon, regime/sector
    slices, and **risk-adjusted return** — all derived once from stored data.
30. **Volatility as a first-class factor family**: level (ATR%/HV), change/contraction (VCP-style), and
    downside/semivol, each decile/IC-tested and regime-conditioned; the contraction measure
    cross-validates the VCP thesis with forward-test evidence.
31. **Risk-adjusted return everywhere**: every decile / cohort / setup reports raw return AND
    return-per-unit-vol, return-per-unit-MAE, and a Sharpe-like ratio (plus expectancy), so a
    high-return / high-drawdown cohort is never mistaken for a good one; "risk" uses downside vol / MAE /
    drawdown, never penalising healthy upside volatility.

## Non-Goals

- **No order execution, no auto-trading, no brokerage integration, no capital deployment** — Trendora
  is decision-support and research only.
- No options/options-flow. Intraday timeframes (1h / 15m / 5m) **are now in scope** — for finer
  entry/setup detection and additional factors — but only as committed, coverage-honest seed data behind
  the same provider abstraction; the canonical swing/return horizon stays **multi-day end-of-day**. No
  real-time streaming/tick data and no sub-minute scalping.
- No machine-learning price prediction.
- No social-media sentiment, and **no news/LLM catalyst enrichment in this session** (deferred to a
  later session; the technical core must work first).
- **No paper-portfolio module in this session** (the data model leaves room for it; deferred to a
  later session).
- Not the full US market, and **not a hand-picked list**: the universe is a reproducible, **rule-based
  liquidity / market-cap / price screen** (~400–500 liquid US names) recorded in config,
  expandable/refreshable via config + committed seed.
- Not 100 indicators — a small, testable, explainable set; RSI may exist as a minor component but must
  not dominate scoring.
- Not financial advice; not a real-time signal/alert service.

## Constraints

- **Runs locally and offline by default.** The committed seed dataset makes every scan deterministic
  and reproducible with no network and no API keys. A live EOD provider is optional, config-selected,
  and its key (if any) comes only from the environment — never committed. The live provider may be
  invoked **on demand from the Data Manager** as a going-forward refresh *outside* the build loop;
  fetched bars are persisted (and may be committed back into the seed for reproducibility), and any
  walk-forward evidence computed over user-fetched data is labelled honestly. The default boot path
  remains the committed offline seed.
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
- **Stock Detail** (`/stocks/[ticker]`) — one stock's chart (with a **1D/1h/15m/5m timeframe selector**,
  rendering the full price path **through the latest date** with an as-of marker), score breakdowns,
  theme membership, setup, reason, invalidation, and per-snapshot history. Reached from a leaderboard
  row, not a top-nav tab.
- **Themes** (`/themes`) — the Theme Leaderboard (ranked, with members + breadth).
- **Sectors** (`/sectors`) — the Sector/Industry Leaderboard.
- **Scanner Runs** (`/scanner-runs`, `/scanner-runs/[runId]`) — history of immutable runs; open one to
  see the exact as-of view for that date.
- **Watchlist** (`/watchlist`) — user-saved stocks with reason, current state, price-since-added, and
  invalidation.
- **Methodology / Glossary** (`/methodology`) — explains the three scores, A–E buckets, the six
  regime labels, every setup status, AND every detected pattern (incl. VCP) — generated from the
  config-backed catalog.
- **Backtest / Time-Machine** (`/backtest`) — see the full as-of scan (read from the canonical
  snapshot), a **per-date forward-test scorecard**, AND the **forward-tested evidence aggregates**
  (forward return by bucket/setup/regime, excess vs benchmarks, VCP-vs-non-VCP, and control-group
  comparisons) for the date chosen in the global as-of switcher (it has **no** date picker of its own).
  The evidence aggregates are scoped to an **expanding window of every snapshot dated ≤ the as-of date**
  (at the latest date this equals the full all-history aggregate). Scanner Runs remains the immutable
  run list.
- **Research** (`/research`) — the analysis labs: a **Factor Lab** (decile / rank-IC per factor incl. the
  volatility family, multi-factor **composite** combination cohorts — a rank-blend across any number of
  selected factors — regime-conditioned effectiveness) and a **Setup & Pattern Lab** (event-study across
  all snapshots: distribution, hit-rate, expectancy, MAE/MFE, exit-horizon, regime/sector slices). Every
  figure is shown raw **and** risk-adjusted and is derived once from the stored forward returns. Defaults
  to an all-history aggregate; an optional **"As of date"** mode restricts every figure to snapshots
  dated ≤ the global as-of date (a point-in-time / walk-forward view bound by the single global control —
  a mode, not a second date picker).
- **Data Manager** (`/data`) — grow, understand, and curate the dataset on demand: view current coverage
  with **plain-language definitions** (incl. the **universe-vs-symbols** distinction) and a **per-symbol /
  per-universe-member coverage table** (in-universe?, has-data?, date range, bar count, thin/missing
  flag); read a **missing-data diagnostic** (universe members with no/thin history below the config
  threshold, plus intra-series date gaps) and **pull the missing data** in one click (fetching exactly the
  gap via the chunked/resumable import); choose an import **source** (paste a **session-only key** if the
  provider needs one), pick a date or date range, fetch price history and/or backfill snapshots and/or
  **expand the universe** (pool → config screen), and watch the async job's live progress; act on
  **Unfinished imports** in one unified section — **Resume** a rate-limited pause, **Retry** remaining/
  failed symbols (idempotent), or **Remove/Dismiss** a stuck record (without touching the immutable run
  audit); **Remove imported data** that was fetched beyond the committed seed (by symbol and/or date
  range) behind a **confirm-preview** that cascades dependent snapshots/forward-returns and **never
  deletes the committed seed**; and read a history of fetch/backfill/expand/remove runs. The `/data` date
  and symbol inputs are **job parameters, not the global as-of control**.

A single global **as-of date switcher** in the top bar is the **only** date control. It re-points
Dashboard, Stocks, Themes, Sectors, Stock Detail, **and Backtest** to a chosen past snapshot (default:
latest); no page keeps its own separate date picker. The as-of date resolves to a stored immutable
snapshot — created once on first view, then never mutated. The **Stock Leaderboard** (`/stocks`) gains a
**VCP filter** (and filters for the additional detected patterns), and **Backtest** carries a
**VCP-vs-non-VCP** forward-return breakdown alongside its by-setup breakdown (as-of-scoped). The Stock-Detail chart's
**timeframe selector** changes bar granularity only (up to the resolved as-of bound) — it is **not** a
second date control.

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
  per resolved as-of date by the forward-testing engine over the snapshots dated ≤ that date (+ their
  post-snapshot prices), persisted and read from storage; never recomputed in a view.
- **Setup & pattern catalog** (definition + thresholds + example) — one config-backed source; the
  glossary page and every inline tooltip read it, never re-describing an entry independently.
- **Detected patterns** (incl. VCP) — computed once per run by the pattern detector from config
  thresholds; the flag plus its pivot/invalidation level ride the stock row, and every view reads
  the same stored value.
- **Resolved as-of date** — single-source: one global control resolves the viewing date; no page holds
  a second, independent date state.
- **Forward-return attribution slices** (per-stock contribution, by-sector, by-rank-band, and
  distribution/hit-rate) — derived once from the stored per-observation forward returns and read
  identically wherever shown; never recomputed per request or per view.
- **Lab analytics** (factor decile means + rank-IC, multi-factor **composite** cohorts — a rank-blend
  across any number of factors — regime-conditioned slices, event-study distribution / hit-rate /
  expectancy, MAE/MFE, exit-horizon, and the **risk-adjusted ratios** return/vol · return/MAE ·
  Sharpe-like) — each derived once from the stored per-observation forward returns + stored factor
  values + post-snapshot price path, read identically wherever shown; never recomputed in the API or a
  view (the Research **all-history vs as-of-date** mode only filters the observation set to snapshots ≤
  the as-of date — it never recomputes a figure).
- **Per-timeframe bars + timeframe-scaled indicators/patterns** (1D/1h/15m/5m) — computed once per
  `(symbol, timeframe, as-of)` and served from storage; the daily timeframe stays the canonical swing
  series.
- **Universe membership** — defined once by the config-recorded screen; every page and list reads the
  same resolved universe.

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

- **J-09: Backtest forward-tested evidence (as-of-scoped, expanding window)**
  - Steps:
    1. Visit `/backtest`
    2. Read the "forward return by score bucket" table/chart (buckets A–E) for a horizon (e.g., 20-day)
    3. Read the excess return vs SPY and vs QQQ
    4. Read the breakdown of forward return by setup type and by market regime
    5. Move the global as-of switcher to an earlier date and confirm the evidence re-points (fewer
       snapshots contribute, the sample size n drops); return to latest and confirm it matches the full
       aggregate
  - Acceptance: a by-bucket forward-return table renders numeric mean returns for buckets A–E at a stated
    horizon; numeric excess-vs-SPY and excess-vs-QQQ values render; a by-setup-type and a by-regime
    breakdown each render numbers — all on `/backtest`, each with the sample size (n) shown so the
    evidence is not presented as more certain than it is; the aggregate reflects **only snapshots dated ≤
    the selected as-of date** (no future snapshot leaks into the as-of-D evidence), so n is non-decreasing
    toward the latest date and equals the all-history aggregate at latest; every figure is derived once
    per as-of date from stored snapshots + stored forward returns (never recomputed in the view) and
    low-sample cells show NA honestly.

- **J-10: Control-group honesty (selection vs sector beta)**
  - Steps:
    1. On `/backtest`, locate the control-group comparison
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
    5. On `/backtest`, read the VCP-vs-non-VCP forward-return breakdown
  - Acceptance: the VCP filter shows only flagged names (or an explicit empty-state if none in the
    current snapshot); each flagged row shows the badge + reason + a concrete invalidation level
    (pivot / last-contraction low); the glossary lists VCP with its meaning, the config thresholds
    that define it, and an example; Backtest shows mean forward returns for VCP vs non-VCP with
    sample size n (NA below the min-sample threshold) derived from the walk-forward snapshots; the VCP
    flag is computed once on the backend and reads identically on leaderboard and detail. The VCP flag
    is SEPARATE from the setup status (a name can be both, e.g. "Breakout-watch" + VCP) and never makes
    a name Actionable on its own.

- **J-17: Grow the dataset by date / date range**
  - Steps:
    1. Visit `/data` and read the current coverage (price-history date range, symbol count, the set of
       snapshot/as-of dates, and any gaps)
    2. Pick a date range (or a single date) and start a fetch + backfill job
    3. Watch the async job's live progress and read its final summary
    4. Open the global as-of switcher and confirm new as-of dates are now selectable; open
       `/backtest` and confirm the forward-test sample size (n) has grown
  - Acceptance: the job runs asynchronously with a visible progress indicator and a final summary that
    lists how many symbols/dates succeeded vs failed; newly created snapshot dates appear in the global
    as-of switcher; the Backtest evidence sample size (n) increases relative to before the run; a forced
    provider failure surfaces an explicit error state and fabricates no prices or scores.

- **J-18: One date control (no duplicate)**
  - Steps:
    1. Visit `/backtest` and confirm there is **no** page-local date dropdown
    2. Change the date in the global top-bar as-of switcher
    3. Observe the Backtest as-of scan and forward-test scorecard re-point to that date
    4. Open another date-scoped page (e.g. `/stocks`) for the same date and compare
  - Acceptance: the Backtest page exposes no date selector of its own; the single global switcher drives
    it; the as-of date shown on Backtest matches the switcher and matches the value other pages resolve
    for the same date — one date control, one resolved date everywhere.

- **J-19: Diagnose weak forward-test returns via attribution**
  - Steps:
    1. Visit `/backtest` (the as-of-scoped aggregate and the single-date scorecard both live here)
    2. Read the **per-stock top contributors & detractors** (named tickers with realized returns)
    3. Read the **by-sector** and **by-rank-band** (e.g. 1–10 / 11–50 / 51+) return breakdowns
    4. Read the **distribution & hit-rate** panel — median, % positive, and dispersion alongside the mean
  - Acceptance: all four attribution layers render numbers with their sample size (n); the per-stock list
    names individual tickers with their realized return; the slices are consistent with the existing
    aggregate mean (same underlying observations, not a re-computation); low-sample slices show n and NA
    honestly rather than a fabricated number.

- **J-20: Price & MA chart shows the full path through the latest date (with as-of marker)**
  - Steps:
    1. Set the global as-of switcher to a historical date D that has bars after D in the seed
    2. Open `/stocks/NVDA` (or any listed name) and view the price + moving-average chart
    3. Observe the chart renders through the **latest** available seed date, not truncated at D
    4. Confirm a visible divider / shaded region marks D and the post-D region is labelled forward/
       after-as-of; the three scores, setup status, and VCP flag are unchanged
  - Acceptance: when viewing a historical as-of D, the price+MA+volume chart extends to the latest seed
    date; D is marked with a visible divider and the post-D region is labelled; the three scores, setup
    status, VCP flag, and every ranking signal remain computed strictly from bars with date ≤ D (the
    extension is display-only); at the latest as-of the chart is unchanged; moving-average lines drawn
    past D are visualization, never as-of signals.

- **J-21: Backtest — leadership cohorts below attribution, with horizon-linked realized returns**
  - Steps:
    1. Visit `/backtest` for a historical as-of date D with at least one forward horizon of post-bars
    2. Confirm the section order is: as-of scan summary → forward-test scorecard → **Return Attribution**
       → **Top Sectors**, **Top Themes**, **Ranked Cohort** (the three leadership lists now sit BELOW
       Return Attribution)
    3. Confirm each of Top Sectors, Top Themes, and Ranked Cohort shows a **realized forward-return** column
    4. Change the horizon selector and confirm the return column on all three updates to that horizon
    5. Pick a recent date and confirm horizons lacking post-bars show NA, not a fabricated number
  - Acceptance: on `/backtest`, Top Sectors / Top Themes / Ranked Cohort render below the Return
    Attribution section; each row carries a realized forward-return at the selected horizon (sector =
    sector-ETF return; theme = equal-weight member-basket return; cohort = the stock's own return) read
    from the stored forward-return data (never recomputed in the view); changing the horizon re-points
    every return column; horizons without enough post-snapshot bars show NA honestly; the single global
    as-of control still drives the date (no page-local date picker — J-18 preserved).

- **J-22: Transparent, rule-based, expanded universe (~500 names)**
  - Steps:
    1. Visit `/methodology` (or `/data`) and read the **universe selection rule** — the exact liquidity,
       price, and market-cap screen from config that defines membership
    2. Confirm the universe now spans ~400–500 names (not 158), each with committed daily history
    3. Confirm the screen and the sector/theme assignments are config-driven (no hand-curated code list)
  - Acceptance: the universe is defined by a documented, reproducible screen whose thresholds live in
    config (min market cap, min dollar volume, min price, plus any membership rule); the seeded universe
    contains ~400–500 symbols each with committed daily OHLCV; every member passes the recorded screen;
    the selection methodology is surfaced in the UI and matches config; expanding/refreshing the universe
    is a config + seed operation, not a code change; breadth and forward-test labels remain honest
    ("universe-relative", survivorship-biased to current membership).

- **J-23: Multi-timeframe bars — intraday seed + timeframe-aware pipeline**
  - Steps:
    1. Confirm the bar store is timeframe-aware (1D / 1h / 15m / 5m) behind the provider abstraction
    2. Confirm a committed intraday seed exists with **documented coverage windows** (e.g. 5m/15m ≈ recent
       ~60 days, 1h ≈ ~1–2 years, 1D = full history)
    3. Confirm indicators and patterns read timeframe-scaled periods from config (no daily-only literals)
  - Acceptance: bars are stored and queried per timeframe with strict per-timeframe no-lookahead; the
    committed intraday seed boots offline-deterministically; per-timeframe coverage windows are recorded
    and surfaced honestly (a timeframe with insufficient history shows NA, never fabricated bars);
    indicator/pattern periods for each timeframe come from config; the daily pipeline and all of
    J-01…J-19 are unchanged (daily remains the canonical swing timeframe).

- **J-24: Timeframe selector on the stock chart (1D/1h/15m/5m)**
  - Steps:
    1. Open `/stocks/NVDA`
    2. Use the chart **timeframe selector** to switch between 1D, 1h, 15m, and 5m
    3. Confirm price, moving averages, and any pattern overlay recompute for the selected timeframe (from
       config-scaled periods)
    4. Confirm a timeframe with insufficient committed history shows an explicit limited-coverage / NA
       state, not fabricated bars
  - Acceptance: the stock chart offers 1D/1h/15m/5m; switching timeframe re-renders price+MA+volume and
    any pattern overlay computed for that timeframe from server values (single source of truth, no client
    recompute); coverage limits are shown honestly; the as-of date control still bounds the upper edge of
    every timeframe (no second date state — "exactly one date selector" preserved).

- **J-25: Factor Lab — decile sort and rank-IC per factor (raw and risk-adjusted)**
  - Steps:
    1. Visit the **Factor Lab** (`/research`)
    2. Pick a factor (RS 3m, MA-stack, distance-from-52w-high, the volatility family, Entry Quality,
       volume trend, …) and a horizon
    3. Read the **decile table**: for each decile D1…D10, the mean forward return AND a risk-adjusted
       column (return/vol or return/MAE), each with sample size n
    4. Read the **rank information coefficient (IC)** — the rank correlation between the factor and the
       forward return — with its sign and magnitude
  - Acceptance: for a chosen factor + horizon the lab shows mean forward return by decile (monotonicity
    visible), a risk-adjusted column alongside it, and a numeric rank-IC, each with n; all values are
    derived once from the stored per-observation forward returns + stored factor values (never recomputed
    in the view); low-sample deciles show NA; the analysis is labelled survivorship-biased /
    universe-relative.

- **J-26: Factor Lab — multi-factor composite cohort (any number of factors)**
  - Steps:
    1. In the Factor Lab, add factor conditions (each a catalog factor at a top/bottom side) and keep
       adding **up to all catalog factors** (e.g. RS 3m top + ATR% bottom + VCP-contraction bottom + …)
    2. Read the **Combined** cohort's forward return (raw and risk-adjusted: return/vol, return/MAE),
       hit-rate, and n against an all-names baseline and against each single condition
  - Acceptance: the user can select from 2 up to **all** catalog factors (the cap lives in config, not in
    code); the **Combined** cohort is a **composite percentile-rank blend** of the selected factors (each
    oriented by its top/bottom side), taking the top config-quantile of that composite — so it is
    **non-empty and clears the min-sample threshold** for a sensible selection (no longer perpetually
    0/NA) and **scales to all factors**; it is shown beside the unconditional baseline and each
    single-factor cohort so interaction is visible; every figure is derived **once from stored factor
    values + stored returns** (recomputes no factor and no return — read-only, descriptive, never a
    fitted/ML model); the blend weights and quantile come from config (default equal-weight — no magic
    numbers); low-sample cells show NA + n and the survivorship-bias label is shown. *(The strict
    AND-intersection MAY remain as an optional secondary "strict overlap" column for small selections,
    clearly labelled and NA when empty.)*

- **J-27: Factor Lab — regime-conditioned factor effectiveness**
  - Steps:
    1. In the Factor Lab, view a factor's decile/IC **split by market regime** (e.g. Risk-on vs Defensive
       vs Risk-off)
    2. Confirm the factor's effectiveness (IC, the top-minus-bottom-decile spread, and the risk-adjusted
       spread) is shown per regime
  - Acceptance: a factor's forward-return relationship (raw and risk-adjusted) is shown conditioned on the
    snapshot's regime label, with per-regime n; regimes with insufficient samples show NA; all values
    derive from the stored snapshots + forward returns (no recompute).

- **J-28: More detected patterns beyond VCP (forward-tested)**
  - Steps:
    1. On `/stocks`, filter by a new pattern (e.g. pullback-to-rising-DMA, flat-base breakout, RS-line new
       high, inside-day / tight-area)
    2. Confirm flagged rows show the pattern badge + reason + invalidation, documented on `/methodology`
    3. On the Setup & Pattern Lab (or Backtest), read the pattern-vs-non-pattern forward-return
       breakdown with sample size
  - Acceptance: at least two new price/volume patterns are detected by config-driven rules (thresholds in
    config, no magic numbers), ride alongside the setup status exactly like VCP (a pattern, never a status,
    never auto-Actionable, computed once with date ≤ D), are filterable on the leaderboard, documented in
    the glossary from the config catalog, and appear as a pattern-vs-non-pattern forward-return breakdown
    with sample size; NA below the min-sample threshold.

- **J-29: Setup & Pattern research lab — event study across all snapshots**
  - Steps:
    1. Visit the **Setup & Pattern Lab** (`/research`)
    2. Pick a setup (e.g. Actionable, Breakout-watch) or a pattern (VCP, …)
    3. Read its **pooled forward-return distribution** across all historical snapshots — mean, median,
       % positive (hit-rate), dispersion, **expectancy**, and **risk-adjusted return** (return/vol,
       return/MAE, Sharpe-like) — by horizon
    4. Read its **MAE / MFE** (max adverse / favorable excursion from post-snapshot daily highs/lows)
    5. Read the **best exit-horizon** curve and the **by-regime** and **by-sector** slices
  - Acceptance: for a chosen setup/pattern the lab pools every historical occurrence and shows, per
    horizon, mean / median / % positive / dispersion / expectancy AND the risk-adjusted ratios with sample
    size n; MAE and MFE are computed from the stored post-snapshot daily highs/lows (no-lookahead, never
    fabricated); a per-horizon return curve and the regime/sector slices render; every figure is derived
    once from the stored per-observation forward returns + price path (read-only — the API/view never
    recomputes returns); low-sample cells show NA honestly and the survivorship-bias label is shown.

- **J-30: Volatility as a return driver — the factor family, risk-adjusted and regime-conditioned**
  - Steps:
    1. In the Factor Lab, select the **volatility family** and view each measure: **level** (ATR% / 20-day
       historical volatility), **change / contraction** (the VCP-style contraction metric), and **downside
       / semivol**
    2. For each measure, read the decile table (raw return AND risk-adjusted) and the rank-IC, by horizon
    3. Split by regime (per J-27) and confirm the sign and strength of each measure per regime
    4. Cross-check the **contraction** measure against the VCP pattern's event-study (J-29) and confirm the
       evidence agrees (contraction → better risk-adjusted forward return)
  - Acceptance: each of the three volatility measures renders a decile table (raw + risk-adjusted) and a
    numeric rank-IC with n, regime-conditioned; "risk" uses downside volatility / MAE (not total
    volatility); the contraction measure's evidence is consistent with the VCP event-study (the same
    underlying observations, not a recomputation); the analysis carries the survivorship-bias /
    universe-relative label and low-sample cells show NA — making explicit *which* volatility measure and
    *which direction* predicts forward return in this universe, rather than assuming the textbook
    relationship.

- **J-31: Find a high-return driver end-to-end (synthesis)**
  - Steps:
    1. In the Factor Lab, identify a factor (or combination) whose top decile/cohort has the strongest,
       monotone, positive **risk-adjusted** forward return with adequate n
    2. Cross-check it is robust in the current market regime (per J-27)
    3. In the Setup & Pattern Lab, confirm a setup/pattern aligned with that factor has positive expectancy
       and tolerable MAE at a sensible exit-horizon
    4. On `/stocks`, filter to the names expressing that factor/pattern today and open one on Stock Detail
       across timeframes
  - Acceptance: a user can travel from "which factor / setup / pattern drives positive risk-adjusted
    return" (lab evidence, with n and regime context) to "which names express it now" (leaderboard filter
    → detail) without any recomputed or fabricated number; every step reads canonical stored values; weak
    or low-sample evidence is shown as NA, not hidden.

- **J-32: Research point-in-time toggle (as-of vs all-history)**
  - Steps:
    1. Visit `/research` and toggle the analysis mode to **As of date**
    2. Set the global as-of switcher to an earlier trading day
    3. Confirm the decile / rank-IC / cohort figures recompute from **only** snapshots dated ≤ that date
       (smaller n, more NA at early dates)
    4. Toggle back to **All history** and confirm the full-sample figures return
  - Acceptance: the Research labs offer an **All history ⟷ As of date** toggle; in **As of date** mode
    every figure pools **only** observations whose snapshot date ≤ the global as-of date (a point-in-time
    / walk-forward view); in **All history** mode it pools every snapshot (the default); the toggle reuses
    the **single global as-of control** and introduces **no second date state** (J-18 preserved — the
    toggle is a mode, not a date picker); both modes are read-only over stored values (no recompute);
    low-sample cells show NA + n and the survivorship-bias label persists.

- **J-33: Import real data from a selectable, key-aware provider source**
  - Steps:
    1. Visit `/data` and open the **Import source** control in the Data Manager
    2. Read the provider catalog — each source (Yahoo no-key, Tiingo, Finnhub, Alpha Vantage, Stooq)
       shown with availability: **available** when a key is present in the environment, or **needs key**
       with a **session-only paste field**
    3. Pick a source; for a key-required source with no env key, paste a key (held in memory for this
       run only)
    4. Start an import; on a provider failure read an **explicit error / unavailable** state (never a
       fabricated bar)
  - Acceptance: the import section offers a **config catalog** of providers (the list, and each
    provider's key requirement + env-var name, live in config — no hardcoded provider list in the
    component); availability is **env-detected** at request time; a key typed into the UI is
    **session-only** — held in memory for the run, **never written to disk, the run log, or the DB, and
    never echoed back** (verifiable: absent from `/api/data`, the run history, and the database); on any
    provider failure the job surfaces an explicit error and **fabricates no prices** (Live fetch is
    real-data-only); the import date inputs remain **job parameters**, not the global as-of control (one
    date selector preserved). *Data-dependent / non-halting:* the section, catalog, key-detection and
    error states are provable offline with an **injected provider** (a stub returning bars / raising); a
    *successful live fetch* additionally needs a reachable provider and is recorded honestly as NA /
    rate-limited when walled — it MUST NOT halt the loop or veto GOAL_ACHIEVED.

- **J-34: Chunked, rate-limit-resilient import that resumes from the last completed chunk**
  - Steps:
    1. Start an import that spans more symbols / dates than one request window
    2. Watch it run in **batches** (chunk x/N) with live per-chunk progress (symbols ok/failed, bars
       added)
    3. Hit a provider rate-limit (429): observe the job retry with **backoff**, then — if the limit
       persists — **stop gracefully** in a **"rate-limited — resumable"** state with progress saved
    4. Click **Resume**: confirm it continues from the **next un-fetched chunk**, re-fetches nothing
       already stored, and that the checkpoint **survived a server restart** in between
  - Acceptance: the import is split into batches whose **symbol-batch size, date-window size,
    max-retries, backoff base/cap, and inter-request sleep all come from config** (no magic numbers in
    the engine); after each completed chunk progress is **checkpointed durably** (persisted, not
    in-memory-only) so it survives a process / server restart; on a persistent rate-limit the job ends in
    an explicit **resumable / paused** status (distinct from `failed`) recording symbols done vs
    remaining — it **fabricates nothing** and does **not** halt the goal loop; **Resume** continues from
    the last completed chunk and the per-`(symbol, date)` idempotency guarantees **no duplicate fetch or
    row**; symbols that never succeeded are shown honestly as failed / NA. Provable offline with an
    injected provider scripted to raise 429 after K symbols.

- **J-35: Expand the universe from the Data Manager (pool → config screen → members)**
  - Steps:
    1. On `/data`, pick the **Expand universe** job kind
    2. Confirm it reads the committed **~548-name candidate pool** (`universe_pool.csv`) and the
       **config screen** (`universe.filters`: min price / min dollar-vol / min market-cap)
    3. Start the expansion as a **chunked, resumable** import (per J-34) over the selected source
    4. On completion, confirm the universe grows toward **~400–500 members**, the **selection
       methodology** + per-member screen-pass + **omitted-with-reason** record are surfaced, and
       `/methodology` matches config
  - Acceptance: the expand job is a **config + data operation, not a code change** — it reads the
    committed pool + the config screen (no hand-curated list), fetches **real OHLCV + a real market-cap
    reference** for each candidate via the selected provider (a provider that cannot supply market cap is
    **not selectable** for expansion, shown disabled with a reason), applies the screen, and writes only
    passers to the universe (`universe.json` + per-symbol CSVs + refreshed `meta.json`); a candidate that
    fails to fetch / lacks data / fails a threshold is **logged and omitted, never fabricated**; breadth
    and forward-test labels stay **universe-relative / survivorship-biased**; this is the
    **operator-facing path that auto-unblocks J-22** — once the data is reachable J-22's acceptance is
    met with **no code change**. *Data-dependent / non-halting* exactly like J-22: the job UI + screen
    logic are provable offline (injected provider), but the live expansion needs a reachable provider and
    is recorded as NA / rate-limited when walled — never halting or vetoing.

- **J-36: Understand coverage — per-symbol table + universe-vs-symbols clarity**
  - Steps:
    1. Visit `/data` and read the **Coverage** panel's plain-language **definitions** block — what each
       figure means, including the explicit distinction between the **universe** (the stocks that pass the
       config screen — `universe.filters`: min market cap, min dollar-volume, min price — and are the
       names scored/ranked) and **symbols** (every ticker with stored bars, which additionally includes
       the index/sector/industry ETFs and `^VIX` that are data-only references, never scored as leaders),
       and what a **backfill gap** is (a trading day with bars but no scanner snapshot)
    2. Read the aggregate coverage figures (price-history date range, universe size, symbol count, trading
       days, snapshot dates, backfill gaps) each shown next to its one-line definition rather than as a
       bare number
    3. Open the **per-symbol coverage table** and read, for each priced symbol and each universe member:
       whether it is **in-universe**, whether it **has data**, its bar **date range** (first → last), its
       **bar count**, and a **thin / missing flag** when its history is below the config history threshold
       or absent
    4. Filter the table to **universe members only** and confirm every member either has data or is
       explicitly flagged missing — no member is silently absent
  - Acceptance: the Coverage panel renders a definitions block that names, in plain language, the
    **universe-vs-symbols** distinction and every coverage figure, so no number is shown unlabelled; the
    per-symbol table renders one row per stored symbol AND one row per universe member with the columns
    in-universe / has-data / date-range / bar-count / thin-or-missing flag, each value read directly from
    stored `daily_prices` (range, count) and `config.universe.symbols` (membership) — it is **descriptive
    metadata derived once from stored bars + config, recomputing no canonical score, return, bucket, or
    setup**; a universe member with no bars shows **has-data = no + missing** (NA, never a fabricated range
    or zero-bar row faked as present), and a member whose bar count is below the config history threshold
    (`indicators.min_history_bars`) shows the **thin** flag; the "thin" / history threshold is read from
    config — **no magic number in the coverage code**; the table is sortable/filterable in the UI only
    (the backend returns the canonical rows once) and reads identically to the aggregate figures (the
    symbol count equals the table's distinct-symbol rows, the universe size equals the in-universe rows)
    so the panel can never present two drifting truths; the panel serves gracefully on an empty dataset
    (null range, zero counts, empty table) rather than erroring.

- **J-37: Diagnose insufficient-for-analysis data and pull exactly the missing history (one-click)**
  - Steps:
    1. On `/data`, read the **Missing-data diagnostic** — a list of what is currently **insufficient for
       analysis**, in three honest categories: (a) **universe members with no history at all**, (b)
       **universe members with thin history** below the config minimum (`indicators.min_history_bars`),
       and (c) **intra-series date gaps** (a member missing trading days inside its own first→last range,
       measured against the benchmark trading calendar)
    2. Confirm each diagnostic row states the symbol, the category, and the concrete shortfall (e.g.
       "BRKB: 40 bars, needs ≥ 200" or "ANET: 12 missing trading days between 2024-03-04 and 2024-05-01")
    3. Click **Pull the missing data** on a row (or **Pull all missing**) — confirm it pre-fills a fetch
       job whose **symbols and date span are exactly the diagnosed gap** (not the whole universe, not the
       whole window) and starts it via the existing chunked, rate-limit-resilient import (J-34) over the
       config-selected source
    4. Watch the job's live progress and final summary; on completion confirm the diagnostic row clears
       (or shrinks) because the gap is now filled, and the per-symbol coverage table (J-36) reflects the
       new bars
    5. Force the provider unreachable and confirm the diagnostic still renders honestly (the shortfall is
       real, read from stored data) and the pull surfaces an explicit error / rate-limited state,
       fabricating no bars
  - Acceptance: the diagnostic is **read-only metadata derived once from the stored bars + the config
    thresholds** — it recomputes no score/return/bucket and invents no data; "insufficient" is defined by
    config (`indicators.min_history_bars` for thin/absent history; the benchmark trading calendar — the
    same SPY-bar calendar the walk-forward and coverage use — for intra-series gaps) with **no magic
    number** in the diagnostic code; each category (no-history / thin / intra-series gap) is reported
    separately with the exact shortfall and the symbol, and a universe member that is fine appears in none
    of them; **Pull the missing data** constructs a fetch job whose symbol set and `[start, end]` are
    precisely the diagnosed gap and dispatches it through the **existing J-34 chunked/checkpointed/
    resumable machinery** (no second fetch path) so the pull is chunked, rate-limit-resilient, resumable,
    and **per-`(symbol, date)` idempotent — it fetches only the missing bars and INSERTs new-only, never
    overwriting a committed bar or re-fetching one already stored**; the live fetch is **real-data-only** —
    on provider failure the pull surfaces an explicit error / rate-limited state and **fabricates no
    price** to clear a diagnostic row; the diagnostic is **fully provable offline with an injected
    provider** (a stub returning the gap bars) for the UI + diagnosis + job-construction logic, while a
    *successful live pull* additionally needs a reachable provider and is recorded honestly as NA /
    rate-limited when walled — it **MUST NOT halt the loop, drive STALLED, or veto GOAL_ACHIEVED** (the
    same non-halting contract as J-33/J-34/J-35); the import's date/symbol inputs remain **job parameters,
    never the global as-of control** (one date selector preserved).

- **J-38: Unified Unfinished-imports — Resume / Retry / Remove with state explanation**
  - Steps:
    1. On `/data`, read the **Unfinished imports** section — a single list of every import that did
       **not** finish cleanly: rate-limited **paused** imports (resumable), **partial** runs (some symbols
       failed), and **failed** runs (all symbols failed)
    2. Confirm each row **explains its state** in plain language (e.g. "Paused — hit a provider rate-limit
       (429); progress saved", "Partial — 142/158 symbols ok, 16 failed", "Failed — every symbol failed;
       provider unreachable") and shows symbols done / remaining / failed and chunk progress where
       applicable
    3. On a **paused** row, click **Resume** — confirm it continues from the next un-fetched chunk (J-34),
       re-fetching nothing already stored, surviving a backend restart
    4. On a **partial** or **failed** row, click **Retry remaining/failed** — confirm it re-runs only the
       un-fetched/failed `(symbol, date)` work and, because of per-`(symbol, date)` idempotency, fetches
       only what is still missing (already-stored bars are skipped)
    5. On any row, click **Remove / Dismiss** — confirm the row leaves the Unfinished-imports list and
       will not be re-offered, while the **Run history** audit log below is unchanged (the run still
       appears there as the immutable record of what happened)
  - Acceptance: the Unfinished-imports section lists **all** non-completed imports in one place —
    paused/resumable, partial, and failed — each with a plain-language state explanation and its
    done/remaining/failed counts, read from durable job-control state (the resumable checkpoint and the
    recorded run summary), **never recomputing a canonical value**; **Resume** is offered only for a
    genuinely paused (rate-limited) checkpoint and continues from the durable `next_chunk_index` (survives
    a restart); **Retry remaining/failed** re-dispatches only the outstanding work and, via
    **per-`(symbol, date)` idempotency (INSERT-new-only)**, **re-fetches and re-inserts nothing already
    stored** — a retry that fully succeeds leaves no duplicate bar and the same dataset it would have
    reached without the failure; **Remove / Dismiss** removes only the **actionable job-control record**
    (the resumable checkpoint, or a soft-dismiss flag on the operational run) so the item stops being
    offered for action — it **MUST NOT delete, hide, or mutate any immutable scanner snapshot,
    forward-return row, or the append-only Run-history audit entry**, which remain the permanent record;
    every action is dispatched through the existing import engine (no parallel path), and Retry/Resume
    against a needs-key source re-prompt for the **session-only key** (request-only, never persisted); the
    section is **provable offline with an injected provider** (stubs scripted to pause/partially-fail/
    fully-fail), and any *live* retry outcome is recorded honestly as NA / rate-limited when the provider
    is walled — **non-halting**, never vetoing completion.

- **J-39: Remove imported data — user-added-only, seed-safe, cascade-consistent, confirm-preview**
  - Steps:
    1. On `/data`, open the **Remove data** control and choose a scope — by **symbol**, by **date range**,
       or both (e.g. "remove TSLA bars after 2026-05-29", "remove everything fetched for BRKB")
    2. Read the **confirm-preview**: exactly which `(symbol, date)` bars would be removed (count + range),
       and exactly which **derived dependents** would cascade — the scanner snapshots and forward-return
       rows whose inputs come **solely** from those user-added bars
    3. Confirm the preview shows that **committed-seed bars are excluded and protected** — any seed-covered
       `(symbol, date)` in the chosen scope is listed as **not removable** with the reason "committed
       seed", and the removable count covers only data fetched **beyond** the seed
    4. Confirm the removal, then re-read the per-symbol coverage table (J-36) and the as-of switcher —
       confirm the removed bars and any snapshot dates that existed **only** because of them are gone, and
       that nothing inconsistent remains (no snapshot or forward return references a now-absent bar)
    5. Attempt to remove a seed-only symbol or a seed-covered date range and confirm the action is
       **refused** (the seed is never deletable from the UI), fabricating nothing
  - Acceptance: removal targets **only user-added data — bars fetched beyond the committed seed** — and the
    **committed seed is never deletable from the UI**; seed vs user-added is determined from the
    **committed seed coverage manifest** (the per-symbol `first`/`last`/`bars` windows recorded in
    `apps/backend/data/seed/meta.json`), so a `(symbol, date)` inside a seed window is protected and
    excluded from every removal and a removal of a wholly-seed scope is **refused with an explicit
    reason**, never a silent partial; the **confirm-preview** enumerates exactly what will be removed — the
    removable bar count + range AND the cascade of dependent rows — **before** any deletion, so nothing is
    removed without an explicit, accurate preview; deleting bars **cascade-removes the scanner snapshots
    and forward-return rows derived solely from them** so the dataset is left **consistent** — no snapshot,
    result, or forward return is left referencing an absent bar — and this cascade is a **whole-row removal
    of the derived snapshot/forward-return together with its provenance, NOT an in-place mutation or
    overwrite of any retained snapshot** (a snapshot that still has all its underlying bars is untouched;
    immutability means *never overwritten in place*, which a consistency-preserving whole-row delete does
    not violate); the operation **fabricates nothing** (it only deletes; it never recomputes or invents a
    replacement value) and, after it runs, the global as-of switcher, the per-symbol coverage, and the
    Backtest sample size all reflect the smaller dataset honestly; the Run-history audit log records the
    removal as its own operational entry; the entire control is **deterministic and provable offline** (it
    needs no provider — it only reads the seed manifest and deletes user-added rows) and touches no
    key/secret.

**Data-dependent journeys (non-halting).** **J-22**, **J-23**, and **J-24** require a one-shot offline
fetch of real data the committed seed does not yet contain — expanded-universe daily OHLCV + market-cap
(J-22) and an intraday bar seed (J-23/J-24) — pulled via the config-selected live provider / the committed
universe runbook. On each resume the session SHOULD **attempt that fetch once** (a single best-effort
attempt, never an autonomous retry loop). If the provider is unreachable, J-22/J-23/J-24 are recorded as
**honestly blocked / limited-coverage (NA)** and **MUST NOT halt the loop, drive a STALLED verdict, or
veto GOAL_ACHIEVED** — the session continues and finishes every other journey (including the Backtest
evidence move, the composite combination cohort, and the Research as-of toggle). They auto-complete via
the committed runbook — **no code change** — once the data becomes reachable; until then every breadth /
forward-test / coverage label stays honest (universe-relative, survivorship-biased, NA where data is
missing — never fabricated). **J-22 also auto-unblocks via the J-35 UI import path** (an operator points
the Data Manager at a reachable provider and runs the Expand-universe job), in addition to the dev
runbook.

The import journeys **J-33**, **J-34**, **J-35**, **J-37**, and **J-38** are **only partly
data-dependent**: their UI + provider catalog + key-detection + chunk/resume/checkpoint + stop-on-limit +
missing-data-diagnostic / pull-missing / retry machinery is **buildable and fully testable offline** with
an **injected provider** (a stub that returns bars or raises 429), so those parts are expected to go green
like any other journey — they are **not** blanket-blocked. Only the **live-fetch outcome** (an actual
successful real import — thus J-22 fully passing through J-35, and a successful pull/retry in J-37/J-38) is
data-gated: when every provider is walled it is recorded as **honestly blocked / rate-limited (NA)** and
**MUST NOT halt the loop, drive STALLED, or veto GOAL_ACHIEVED**. **J-36** (coverage description) and
**J-39** (seed-safe removal) are **fully deterministic — they need no provider** and are expected to go
green unconditionally, like backfill.

## Anti-goals

- **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward
  returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar
  influences an as-of score. Chart **visualization** MAY render bars dated > D strictly as a labelled
  forward/after-as-of display; this display path MUST NOT feed any score, bucket, setup status, pattern
  flag, factor value, or ranking — all of which remain computed from bars with date ≤ D — and the
  moving-average lines drawn past D are visualization only, never as-of signals. *(critical)*
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
  from storage. The relocated **as-of-scoped evidence aggregate** (forward returns by bucket / setup /
  regime, excess vs benchmarks, control-group, and VCP-vs-non-VCP) is likewise derived once per resolved
  as-of date over the snapshots dated ≤ D, persisted/cached, and read from storage — never recomputed per
  request and never including a snapshot dated > D. *(extends Single source of truth)*
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
- **Live fetch is real-data-only.** The Data Manager MUST use the config-selected live provider to
  fetch real EOD bars; on a provider failure it MUST surface an explicit error and MUST NOT synthesize
  prices to fill a gap or force a successful run. *(extends No fabricated data)*
- **Import keys are env-or-session, never persisted.** The import provider catalog and each provider's
  key-requirement + env-var name MUST come from config (no hardcoded provider list in code); a provider
  key MUST be read from the environment, or — if the user pastes one into the import UI — held **in
  memory for that run only**, **never written to disk, the run log, the DB, or any committed file, and
  never echoed back** in any response. The import's date inputs are **job parameters, not a second date
  control** (the single global as-of switcher stays the only date selector). *(extends Live fetch is
  real-data-only + Exactly one date selector)*
- **Range backfill stays immutable & lookahead-free.** Snapshots created for a fetched or backfilled
  date range are create-once: an existing snapshot MUST be read, never overwritten, and an as-of-D
  snapshot MUST use only bars with date ≤ D. *(reaffirms On-demand snapshots stay immutable, for
  ranges)*
- **Coverage & missing-data are descriptive & honest.** The coverage figures, the per-symbol/per-
  universe-member table, and the insufficient-for-analysis diagnostic MUST be **read-only metadata derived
  from the stored bars + config** — they MUST NOT recompute or restate any canonical score, return,
  bucket, or setup. A universe member with no or thin history MUST be shown as **missing / thin (NA)**,
  never as a fabricated range, zero-bar-faked-as-present, or filled value; the **history threshold
  defining "thin/insufficient"** and the trading calendar defining an intra-series gap MUST come from
  config (`indicators.min_history_bars` and the benchmark-bar calendar) — **no magic number** in
  coverage/diagnostic code. The **universe-vs-symbols** distinction (config-screened scored names vs every
  ticker with bars) MUST be surfaced in plain language, not left implicit. *(extends No fabricated data +
  No recompute in the read path)*
- **Pull-missing fetches exactly the gap, real-data-only, idempotently.** The one-click "pull the missing
  data" MUST construct a fetch covering **only** the diagnosed `(symbol, date)` shortfall and MUST run it
  through the existing chunked/checkpointed/resumable import path (no second fetch path); it MUST be
  **per-`(symbol, date)` idempotent (INSERT-new-only)** — re-fetching/duplicating nothing already stored,
  never overwriting a committed seed bar — and on provider failure it MUST surface an explicit error /
  rate-limited state and **fabricate no price** to clear a diagnostic row. *(extends Live fetch is
  real-data-only)*
- **Unfinished-imports actions are idempotent and audit-preserving.** Resume and Retry MUST re-fetch only
  outstanding work and, via per-`(symbol, date)` idempotency, produce **no duplicate fetch or row**;
  **Remove/Dismiss MUST drop only the actionable job-control record** (a resumable checkpoint, or a
  soft-dismiss of the operational run summary) — it MUST NOT delete, hide, mutate, or fabricate any
  **immutable scanner snapshot or forward-return row**, and the append-only `data_provider_runs` audit
  trail MUST remain the permanent record of what ran. *(extends Run log is append-only + Snapshots are
  immutable)*
- **Data removal is seed-safe & consistency-preserving.** Removal MUST target **only user-added bars**
  (data fetched beyond the committed seed, identified from the committed seed coverage manifest) — the
  **committed seed MUST NEVER be deletable from the UI**, and a wholly-seed removal MUST be refused with an
  explicit reason, never a silent partial. A **confirm-preview** MUST enumerate exactly what will be
  removed (bars + cascaded dependents) before anything is deleted. Deleting bars MUST **cascade-remove the
  snapshots and forward-returns derived solely from them** so nothing is left referencing an absent bar;
  this is a **whole-row deletion of a derived row together with its provenance — NOT an in-place
  mutation/overwrite of a retained snapshot** (the *Snapshots are immutable* identity means "never
  overwritten in place," which a consistency-preserving whole-row removal respects). Removal MUST
  **fabricate nothing** — it only deletes; it never recomputes or invents a replacement value. *(extends
  Snapshots are immutable + No fabricated data)*
- **Attribution is read-only.** The forward-return attribution slices (per-stock contribution,
  by-sector, by-rank-band, distribution/hit-rate) MUST be derived from the stored per-observation
  forward returns; the API and frontend MUST NOT recompute returns to build them. *(extends No recompute
  in the read path)*
- **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every
  date-scoped page (including Backtest) reads the single global as-of control. The Stock-Detail chart
  **timeframe selector** (1D/1h/15m/5m) is NOT a date control — it changes bar granularity only, bounded
  by the resolved as-of date. The Research **all-history / as-of-date** toggle is likewise a MODE, NOT a
  date control — its as-of mode reads the same single global as-of control (no second date state).
  *(extends Single source of truth)*
- **Intraday stays deterministic & coverage-honest.** Intraday timeframes MUST boot from the committed
  seed (no live/streaming dependency in the boot path), MUST record per-timeframe coverage windows, MUST
  enforce per-timeframe no-lookahead, and MUST show NA where history is insufficient — never fabricating
  intraday bars or extrapolating across gaps. *(extends No fabricated data + No lookahead)*
- **Universe screen is reproducible & honest.** Universe membership MUST come from the config-recorded
  screen (no hand-curated list masquerading as a screen); expansion MUST use real committed data only (no
  fabricated history); breadth and walk-forward labels stay "universe-relative" / survivorship-biased to
  current membership. *(extends No magic numbers + No fabricated data)*
- **Research lab is read-only, honest & not predictive.** Every Factor-Lab and event-study figure (decile
  means, rank-IC, combination cohorts, regime slices, distribution, hit-rate, expectancy, MAE/MFE,
  exit-horizon, risk-adjusted ratios) MUST be derived once from the stored per-observation forward returns
  + stored factor values + post-snapshot price path; the API and frontend MUST NOT recompute returns or
  factors to build them; low-sample cells show NA + n; results carry the survivorship-bias label. The lab
  is **descriptive evidence, not a fitted/ML predictive model** — the **composite combination cohort** is
  a transparent, config-weighted percentile rank-blend of the **stored** factor values (a deterministic
  ranking/grouping, never a fitted/learned model), and the **as-of-date** mode merely FILTERS the stored
  observation set to snapshots dated ≤ the as-of date (it recomputes nothing). *(extends No recompute in
  the read path + No machine-learning price prediction)*
- **New patterns are patterns, not statuses.** Every new detected pattern MUST follow the VCP contract:
  config-driven thresholds, computed once with date ≤ D, price+volume only, riding alongside the setup
  status, never entering the setup-status enum, and never alone promoting a name to "Actionable".
  *(reaffirms VCP is a pattern, not a status)*
- **Risk-adjusted reporting is honest & must not conflate up/down volatility.** Every risk-adjusted figure
  (return/vol, return/MAE, Sharpe-like, expectancy) MUST be derived once from the stored per-observation
  forward returns + post-snapshot price path; "risk" MUST use downside volatility / MAE / drawdown — never
  total volatility, which would penalise healthy upside moves; raw and risk-adjusted MUST be shown side by
  side; low-sample cells show NA + n. *(extends Research lab is read-only)*
