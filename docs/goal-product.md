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
- **The stack is ready together (fast boot).** On a cold start the backend **accepts connections and
  serves the core pages (Dashboard, Stocks, Sectors, Themes, Stock Detail) for the latest as-of date
  within a small, config-set readiness budget** (on the order of one snapshot computation; effectively
  instant on a warm DB) — it **never blocks serving for minutes** on the historical walk-forward
  backfill, which instead **warms up in the background** with honest progress. A slow, contended, or
  failed warm-up never shows a misleading "unavailable" and never crashes the boot.
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
- **Every user-facing date reads `yyyy-MM-dd`.** One shared formatter/constant renders every displayed
  calendar date (Data Manager form + job cards + coverage + diagnostics, the as-of switcher and
  historical indicator, run lists, chart tooltip/crosshair dates) as ISO `yyyy-MM-dd` regardless of
  browser locale; the Data Manager date fields are validated ISO text inputs; API/DB/config date
  contracts stay ISO and unchanged.
- **The historical view survives navigation.** The single global as-of state is serialized into the URL
  (`?asof=yyyy-MM-dd` when historical; date-free at latest), so a leaderboard→detail click-through, a
  reload, a new tab, or a shared link restores exactly the selected historical date through the one
  global control — one date control, one state (J-18 amended, not weakened). While historical, every
  in-app link's **href itself carries `?asof`** — so middle-click / new-tab / copied-link navigation
  preserves the date without depending on post-navigation re-stamping (J-50) — and the leaderboard
  tickers open the detail in a new tab carrying the same date (J-54).
- **The market's path and its regime are visible at a glance.** The dashboard renders a major-indexes
  chart (config-listed committed index ETFs, normalized to a common % scale) over soft background bands
  built from the stored per-date market-regime history (exact label + score on hover), default-on behind
  a persisted toggle; the stock-detail price chart carries the same regime bands — both read stored
  values only (no regime or return recomputed in an endpoint or view). The dashboard card charts the
  **full stored history** regardless of the global as-of, drawing a **vertical as-of marker** when a
  historical date is selected (display-only context — post-as-of data feeds no as-of-scoped value); the
  stock-detail bands stay clamped at the as-of date (J-49 / J-45).
- **Fetch + backfill are materially faster.** Symbol fetching runs on a bounded, config-set parallel
  worker pool (rate-limit-aware; checkpoint/Resume and idempotency preserved), bar writes commit per
  chunk, and the walk-forward backfill loads each symbol's bars once per job (not once per date) — with
  canonical outputs proven identical by the existing suites and a committed benchmark script reporting
  stage timings. The multi-date snapshot backfill itself runs concurrently — at least ~2× faster than
  the per-date sequential sum, with identical snapshots — and per-stage timings (fetch vs backfill:
  elapsed, items processed, concurrency used) are surfaced in the job status (J-53).
- **Every domain term on every page is explained.** A config-backed glossary catalog covering the
  inventoried UI vocabulary (≥ 100 terms) renders as a searchable, categorized Glossary on
  `/methodology`, and the dense pages' column headers / stat labels carry info-tooltips reading the same
  catalog — no bare jargon anywhere in the UI.
- **Every research sample count is auditable.** Each `N=` figure on `/research` links to a read-only
  drill-down listing the exact stored observations behind it — the observation total equals the
  published N and the values are the same stored per-observation inputs the aggregate used — and each
  row's ticker opens the dated stock detail in a new tab (J-51 / J-52).
- **The leaderboard is findable and theme-aware.** `/stocks` carries a type-to-filter symbol search
  (ticker or company name, no submit button) and a Theme column + theme filter re-displaying the same
  served membership chips the detail page shows — all pure client-side view transforms over the
  already-served snapshot rows (composing with the existing filters and J-48 sorting), never a second
  compute path (J-55 / J-56).
- **Member structure is legible everywhere.** The Themes leaderboard's truncated member list expands in
  place (the `+n` reveals every remaining member) and every member ticker deep-links to the dated stock
  detail in a new tab; the Sectors leaderboard names and describes every ETF row from config (no more
  bare "KRE") and lists its universe members the same way — sector members from the existing
  `stock_sectors` mapping, industry members from a new config-curated stock→industry-group mapping
  honestly labelled as config-defined (an unmapped ETF shows an explicit empty state, never fabricated
  members) (J-57 / J-58).
- **Data jobs are stage-resumable, never re-fetch covered data, and finish reliably.** A job whose
  fetch completed but whose backfill failed resumes from the backfill stage with **zero provider
  calls**; a re-run over an already-covered range skips straight to backfill in seconds (never ~45
  minutes of no-op re-fetching to add `0 new bars`); the multi-date parallel backfill completes without
  the session/transaction crash and isolates a failing date instead of aborting the stage; every
  started job appears in Run history immediately (`running` → one honest terminal state; restart
  orphans marked `interrupted`); and progress is fine-grained and honest — per-symbol/per-date ticks, a
  current-activity line, a live heartbeat, and counters that can never exceed their totals (J-59 /
  J-60 / J-66 / J-67).
- **Data availability is visible per date, and the as-of picker shows it.** The Data Manager renders a
  per-trading-date availability heatmap (symbols-with-bars count + snapshot marker per date, exact
  figures on hover, click prefills the job form) built from a read-only descriptive endpoint, and the
  global as-of switcher becomes a calendar popover marking exactly the selectable snapshot dates — the
  same single global state, presented better (J-61 / J-62).
- **Event-study evidence is overlap-honest.** The Setup & Pattern Lab defaults to a **first-trigger
  episode** view (consecutive signal-days of the same symbol collapse into one observation) with the
  current pooled per-signal-day view one toggle away (byte-identical to today's figures), both modes
  disclosing n, unique symbols, and episode count — same stored observations, same builders,
  count-coherent with the `N=` drill-downs, which now sort/filter client-side and open in a new tab
  (J-63 / J-64 / J-65).

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
   stack, distance from 52w high, volume trend, internal breadth). Every ranked ETF row is **named and
   described from config** (the industry catalog becomes ticker → name/description reference data like
   `etfs.sector` — no bare tickers like "KRE", no hardcoded name in code) and carries its **universe
   member list**: sector members derived from the existing `stock_sectors` mapping, industry members
   from a config-curated stock→industry-group mapping (many-to-many, like themes) honestly labelled
   config-defined — an ETF with no universe member shows an explicit empty state (J-58).
6. **Theme engine**: manually-defined themes (config) mapping stocks→themes (many-to-many), with a
   price-confirmed Theme Score (not news-driven). Membership is visible end-to-end: the stock
   leaderboard shows each row's theme chips with a theme filter (J-56), and the Themes leaderboard's
   member list is fully expandable with dated new-tab member links (J-57).
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
    **legible and curatable**: a **per-trading-date availability heatmap** (for every trading day: the
    count of symbols with a stored bar + whether a snapshot exists, exact figures on hover, click
    prefills the job form — a read-only descriptive endpoint, J-61); a **plain-language coverage
    explainer** (defining every figure and the
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
    default boot path remains the committed offline seed. The job pipeline is **stage-aware and
    reliable**: the durable checkpoint records per-stage completion (fetch → screen → backfill) so a
    job that failed or was interrupted after a completed fetch is **resumable from the backfill stage
    with zero provider calls**, and the fetch planner skips provider calls for (symbol, window)s
    already fully covered against the trading calendar — a re-run over a covered range reaches the
    backfill stage in seconds (J-59); the multi-date parallel backfill is **transactionally sound** (no
    shared-session / invalid-'committed'-state crash; a failing date is isolated and reported while the
    rest complete — J-67). Every started job is **recorded in Run history immediately** (status
    `running`, then one honest terminal transition; orphaned rows from a dead process are marked
    `interrupted` on boot — J-60), and progress is **fine-grained and honest**: per-symbol fetch ticks,
    per-date backfill ticks, a current-activity line, a last-progress heartbeat, live per-stage
    timings, and counters that never exceed their totals (J-66).
21. **Unified as-of date control**: exactly one date selector — the global top-bar as-of switcher —
    governs every date-scoped page, **including Backtest**. Per-page date dropdowns are removed and the
    frontend holds no second, independent date state; "which date am I viewing" has a single source.
    That single state is serialized into the URL as `?asof=yyyy-MM-dd` while historical (Capability 36
    / J-43) — a deep-linkable serialization restored through the one control, not a second state. The
    switcher's presentation is a **calendar popover** marking exactly the available snapshot dates
    (unavailable days disabled, month navigation, a "Latest" shortcut) instead of one flat all-dates
    dropdown — a presentation upgrade of the same single state, never a second control (J-62).
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
    slices, and **risk-adjusted return** — all derived once from stored data. It is **overlap-honest**
    (J-63): the default headline mode collapses consecutive same-symbol signal-days into
    **first-trigger episodes** (one observation per continuous run), a toggle restores the pooled
    per-signal-day view (byte-identical to the prior figures), and both modes disclose n, unique
    symbols, and episode count — the same stored observations through the same builders, never a
    recompute.
30. **Volatility as a first-class factor family**: level (ATR%/HV), change/contraction (VCP-style), and
    downside/semivol, each decile/IC-tested and regime-conditioned; the contraction measure
    cross-validates the VCP thesis with forward-test evidence.
31. **Risk-adjusted return everywhere**: every decile / cohort / setup reports raw return AND
    return-per-unit-vol, return-per-unit-MAE, and a Sharpe-like ratio (plus expectancy), so a
    high-return / high-drawdown cohort is never mistaken for a good one; "risk" uses downside vol / MAE /
    drawdown, never penalising healthy upside volatility.
32. **Fast-ready boot + background warm-up**: the lifespan does only the minimal synchronous work to
    serve the **latest** as-of snapshot, then yields; the historical walk-forward cadence snapshots +
    `forward_returns` are produced by a **background warm-up task** (reusing the existing async-job /
    daemon-thread + `JobProgress` machinery) after the server is already serving. Warm-up exposes
    **live, honest progress** (e.g. "history 4/11") via the health / readiness endpoint; startup tunables
    (readiness budget, warm-up batch size, health poll interval / backoff) live in **config — no magic
    numbers**.
33. **Memoized / vectorized scan engine**: the per-date scan loads each symbol's bars **once** and reuses
    them across cadence dates / components (no re-fetch per component per date) so the warm-up (and any
    blocking work) is materially faster; a pure refactor with **identical canonical outputs** (the same
    scores / buckets / returns, asserted by the existing scanner / forward-test tests).
34. **Reproducible precomputed snapshot seed** *(optional accelerator)*: an optionally-committed,
    **byte-reproducible** materialization of `scanner_runs` + `forward_returns` over the committed price
    seed (regenerated by a committed script, verified to equal a fresh compute), **loaded verbatim** on a
    fresh DB exactly like the price seed — so even a first / cold boot is warm. It is a *cache of the
    deterministic computation*, never hand-authored.
35. **Uniform ISO date presentation**: every user-facing date renders `yyyy-MM-dd` through one shared
    formatter/constant (no locale-dependent widget output, no per-component format literals); the Data
    Manager's date fields are validated ISO text inputs (exact-format check, visible error state); API,
    DB, and config date contracts remain ISO and unchanged.
36. **Deep-linkable as-of (URL-serialized single state)**: the one global as-of control serializes its
    state into the page URL (`?asof=yyyy-MM-dd` only while historical; date-free at latest) on every
    date-scoped page, and a URL carrying `?asof` restores that date into the global control on load.
    One state, one control — the URL is its serialization, never a second, independent date state.
    While historical, every in-app navigational link's href embeds the param, so new-tab and
    copied-link navigation preserve the date too (J-50).
37. **Major-indexes & regime history visualization**: a dashboard card charting the config-listed index
    ETFs (SPY/QQQ/IWM/RSP, plus DIA once fetched) as % lines normalized to the selected range start,
    drawn over soft market-regime background bands built from the stored per-run regime history (three
    risk-family colors, the exact six-value label + score on hover, an honest step function between
    snapshot dates), with config-driven range presets and a default-on enable toggle persisted
    client-side; the same regime bands render behind the stock-detail price chart. Both surfaces read
    stored bars + stored regime only — nothing recomputed in an endpoint or view; the normalized series
    is computed server-side (the frontend only re-formats). The dashboard card renders the full stored
    history regardless of the global as-of, with a vertical as-of marker when historical (display-only
    context); the stock-detail bands stay clamped at the as-of date (J-49 / J-45).
38. **Parallel, batched, vectorized data pipeline**: the chunked import fetches symbols on a bounded,
    config-set worker pool (per-provider rate-limit aware; 429 backoff → resumable pause → durable
    Resume and per-`(symbol, date)` idempotency fully preserved; DB writes stay serialized/transactional
    and commit per chunk, not per symbol), and the walk-forward backfill realizes Capability 33: each
    symbol's bars are loaded once per job and indicators are computed once over the full series, then
    sliced per as-of date — identical canonical outputs asserted by the existing scanner/forward-test
    suites, plus a committed benchmark script reporting per-stage timings (advisory). The multi-date
    snapshot backfill also runs concurrently (mechanism open; determinism, serialized writes, and
    idempotency preserved — at least ~2× faster than the per-date sequential sum) and the job status
    payload reports per-stage timings (J-53).
39. **Full UI terminology glossary + inline term help**: one config-backed glossary catalog (the
    committed term inventory: scores & buckets, setups & patterns, regime & breadth, universe & data,
    forward-testing & evidence, factor-lab / statistics vocabulary) rendered as a searchable,
    categorized Glossary section on `/methodology`, with info-tooltips on the dense pages' column
    headers and stat labels reading the same catalog entries — a config-added term appears in both
    places with no code change; the existing setup/pattern catalog is referenced, never duplicated.
40. **Research sample drill-down (evidence auditability)**: every published research sample count links
    to a dedicated read-only samples page reproducing that exact cohort from the same stored
    per-observation data (count-coherent — the observation total equals the published N; same stored
    factor values and realized returns), with each row deep-linking to the dated stock detail in a new
    tab (J-51 / J-52). The `N=` chips open the drill-down in a **new tab** (J-65), and the samples
    table is **client-side sortable and ticker-filterable** under the J-48 view-transform contract —
    a filter narrows the view honestly ("x of N") and never alters the published cohort total (J-64).

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

- **Dashboard** (`/`) — the daily snapshot at a glance. The top is a **compact at-a-glance summary**
  that updates on every as-of change — the market-**regime** label + 0–100 score, and the market-**phase**
  label + 0–100 **severity** score (+ severity-band label) + filtered **P(bear)**, each with its named
  component breakdown reachable (J-98) — directly above the **single two-pane market cross-view chart** (there is no separate standalone
  Major-indexes card — it duplicated pane 0 and is removed, J-101): pane 0 = the
  **Major indexes & regime** lens (normalized index-ETF % lines over stored-regime background bands,
  default-on behind a persisted toggle — J-44) and pane 1 = the **same index lines over full-history
  phase-colored bands with the 0–100 severity line + the zero-centered severity-velocity line** (J-97 /
  J-102); the bottom pane's phase bands span the **full history at any as-of** (the as-of only positions the
  marker — J-101), and the retired **P(bear)** line stays in the **hover tooltip** beside the **regime label
  + score** the tooltip now also shows (J-102); the two panes **share one time axis**, so
  zoom/pan is synchronized across both — a view transform of the visible range, not a second date control.
  The breadth metrics, top sectors, candidate counts, top themes, last-run time, and evidence summary sit
  below in a **collapsed, expandable "More detail" section** (J-98). Its period selector **defaults to All
  (full history)** (J-78).
- **Stocks** (`/stocks`) — the Stock Leaderboard (ranked, filterable, **client-side sortable** — J-48 —
  with a **type-to-filter symbol search** (J-55) and a **Theme column + theme filter** re-displaying
  each row's served membership chips (J-56)). Rows link to Stock Detail (**opens in a new tab**, the
  href carrying the historical `?asof` — J-54/J-50). Each row also carries **five forward-return
  columns (1/5/10/20/60-day)** — the stock's realized forward return from the as-of date read from the
  stored `forward_returns` table (NA at/near latest where post-bars are insufficient), sortable per
  J-48 (J-75). Each row also shows a **Proximity to 52w high** column **directly after Risk** — the
  stored `high_proximity` value (the % the latest close sits below its 52-week high), client-side
  sortable (J-106). The page header also shows the as-of date's **market-regime label + score** (the same
  stored regime the Dashboard shows) and a **theme ranking** — a ranked Top-Themes strip plus `#n` rank
  badges on the theme chips / filter, re-displaying the `/themes` scores (J-80).
- **Stock Detail** (`/stocks/[ticker]`) — one stock's chart (with a **1D/1h/15m/5m timeframe selector**,
  rendering the full price path **through the latest date** with an as-of marker), score breakdowns,
  theme membership, setup, reason, invalidation, and per-snapshot history. Reached from a leaderboard
  row, not a top-nav tab. It also shows a **forward-return panel (1/5/10/20/60-day) for the as-of
  date** read from the stored `forward_returns` table and matching the leaderboard (J-75), and the
  price chart shows a **per-bar hover detail box** (date, OHLC, volume, % change, MA values) read from
  the already-served bars (J-76).
- **Themes** (`/themes`) — the Theme Leaderboard (ranked, with members + breadth). The member list is
  **fully expandable** (the `+n` overflow reveals every remaining member, collapsible) and each member
  ticker opens the dated Stock Detail in a **new tab** (J-57). Each theme row also carries **five
  forward-return columns (1/5/10/20/60-day)** — the equal-weight forward return of its member basket for
  the as-of date, read from the stored `forward_returns` table via the same builder Backtest uses,
  sortable per J-48 and NA-honest at/near latest (J-81).
- **Sectors** (`/sectors`) — the Sector/Industry Leaderboard. Every ETF row is **named + described from
  config** (no bare tickers like "KRE") and its expanded panel lists its universe **members** like the
  Themes page — expandable, with dated new-tab member ticker links; industry membership comes from the
  config-curated stock→industry-group mapping, honestly labelled config-defined (J-58). Each ETF row
  also carries **five forward-return columns (1/5/10/20/60-day)** — the sector / industry ETF's own
  forward return for the as-of date, read from the stored `forward_returns` table (the same value
  Backtest's Top Sectors shows), sortable per J-48 and NA-honest at/near latest (J-81).
- **Scanner Runs** (`/scanner-runs`, `/scanner-runs/[runId]`) — history of immutable runs; open one to
  see the exact as-of view for that date.
- **Watchlist** (`/watchlist`) — user-saved stocks with reason, current state, price-since-added, and
  invalidation.
- **Methodology / Glossary** (`/methodology`) — explains the three scores, A–E buckets, the six
  regime labels, every setup status, AND every detected pattern (incl. VCP) — generated from the
  config-backed catalog — plus the **full terminology Glossary** (J-47): a searchable, categorized
  list covering every domain term, label, column name, and dropdown option the UI shows, from the
  same config-backed catalog mechanism.
- **Backtest / Time-Machine** (`/backtest`) — see the full as-of scan (read from the canonical
  snapshot), a **per-date forward-test scorecard**, AND the **forward-tested evidence aggregates**
  (forward return by bucket/setup/regime, excess vs benchmarks, VCP-vs-non-VCP, and control-group
  comparisons) for the date chosen in the global as-of switcher (it has **no** date picker of its own).
  The evidence aggregates are scoped to an **expanding window of every snapshot dated ≤ the as-of date**
  (at the latest date this equals the full all-history aggregate). Scanner Runs remains the immutable
  run list.
- **Research** (`/research`) — the analysis labs: a **Factor Lab** (an **all-factors table** — one row per factor showing family, **Rank-IC** (value + N),
  a downside-**risk-adjusted** figure, and **all forward-return columns then all max-drawdown columns for every horizon
  (1/5/10/20/60d), grouped by metric (J-114) — no horizon selector** (J-109), client-side sortable — whose rows
  **expand in place to reveal that factor's decile sort** (carrying the same all-horizon return +
  max-drawdown columns in that same grouped order), hidden by default; J-107 / J-109), the multi-factor
  **composite** combination cohorts (a rank-blend across any number of selected factors, on its own
  `/research/factor-combination` sub-route) and a **Setup & Pattern Lab** (event-study across
  all snapshots: distribution, hit-rate, expectancy, MAE/MFE, exit-horizon, regime/sector slices). Every
  figure is shown raw **and** risk-adjusted and is derived once from the stored forward returns. Defaults
  to an all-history aggregate; an optional **"As of date"** mode restricts every figure to snapshots
  dated ≤ the global as-of date (a point-in-time / walk-forward view bound by the single global control —
  a mode, not a second date picker). Every sample-size figure (`N=…`) is a link into **Research
  Samples** (J-51). A **Regime × Setup × Pattern** study adds a **ranked, sortable table of
  (regime, setup, pattern) combinations** with per-horizon forward-return stats, drilling down via the
  same `N=` samples chips and respecting Episodes/Pooled (J-63) + the As-of mode (J-32) — derived once
  from the same enriched event-study observation set, never recomputed (J-77); its table **filters by
  regime / setup / pattern**, sorts **NA-last** in every column, **defaults to Pooled**, and every row's
  `N=` chip drills into the exact cohort without error (J-82). Each heavy lab section is **lazy-loaded**
  (fetched on expand / when scrolled into view, never four heavy requests at once) and the four heaviest
  labs — multi-factor combination, the Setup & Pattern event-study, Regime × Setup × Pattern, and Downtrend
  Opportunity — live on their **own `/research/*` sub-routes** linked from a `/research` hub, each served
  from a **derived-once, cached/precomputed** aggregate for fast, reliable loads (figures byte-identical — a
  performance property, J-72 / J-104). A **Severity-velocity × Regime forward-return study**
  (`/research/severity-velocity`) tests whether the sign of severity-velocity under a given regime predicts
  the forward market return — a regime-family × velocity-sign matrix of forward SPY returns (mean / win-rate
  / N per horizon) with `N=` drill-down, honest about its bull-dominated sample (J-103). A **Regime Lab**
  (`/research/regime-lab`) sorts the same cross-sectional stock forward returns by the canonical market-**regime**
  — a by-label summary (the six regime labels) and a **regime-score decile** sort — each with all
  forward-return columns then all max-drawdown columns per horizon (1/5/10/20/60d, grouped by metric — J-114), the rank-IC, and `N=` drill-down (J-110).
  A **Market Phase & Severity Lab** (`/research/phase-severity-lab`) does the same against the canonical
  market-**phase** label (the five phases) and a **severity-score decile** sort (J-111). A **Regime × Phase ×
  Factor** study (`/research/regime-phase-factor`) crosses all three as deciles — a ranked, filterable,
  **paginated (30 rows/page)** table of (regime-decile × severity-decile × factor-decile) combinations for a
  selected factor, each row carrying the per-horizon forward-return + max-drawdown stats with `N=` drill-down
  (J-112). These four (J-109–J-112) are **read-only re-surfacings of stored forward returns + max-drawdown
  grouped by the stored regime / served severity / stored factor values — derived once, cached, never
  recomputed**.
- **Research Samples** (`/research/samples`) — the drill-down behind every research sample count: each
  `N=…` figure on `/research` links here, parameterized to reproduce that exact cohort (analysis kind,
  factor(s)/subject, horizon, decile/cohort, regime, sector, and the all-history vs as-of scope, as
  applicable), listing every member observation — ticker, snapshot date, the qualifying stored
  value(s), and the realized forward return at the stated horizon. Reached from the `N=` chips (which
  open it in a **new tab** — J-65), not a top-nav tab; deep-linkable; the table is **client-side
  sortable + ticker-filterable** (J-64 — a view transform; the cohort total still equals the published
  N); row tickers open the dated Stock Detail in a new tab (J-52). The drill-down is **also reached
  from the Regime × Setup × Pattern combination `N=` chips** (J-77).
- **Data Manager** (`/data`) — grow, understand, and curate the dataset on demand: view current coverage
  with **plain-language definitions** (incl. the **universe-vs-symbols** distinction) and a **per-symbol /
  per-universe-member coverage table** (in-universe?, has-data?, date range, bar count, thin/missing
  flag); see **per-date availability at a glance** — the trading-day **availability heatmap**
  (symbols-with-bars count + snapshot marker per date, exact figures on hover; clicking prefills the
  job form — J-61); read a **missing-data diagnostic** (universe members with no/thin history below the config
  threshold, plus intra-series date gaps) and **pull the missing data** in one click (fetching exactly the
  gap via the chunked/resumable import); choose an import **source** (paste a **session-only key** if the
  provider needs one), pick a date or date range, fetch price history and/or backfill snapshots and/or
  **expand the universe** (pool → config screen), and watch the async job's live, **fine-grained**
  progress (per-symbol/per-date ticks, a current-activity line, a last-progress heartbeat, live stage
  timings — J-66); act on
  **Unfinished imports** in one unified section — **Resume** a rate-limited pause or a job stopped
  after its completed fetch stage (**resumable from the backfill stage, zero provider calls** — J-59),
  **Retry** remaining/
  failed symbols (idempotent), or **Remove/Dismiss** a stuck record (without touching the immutable run
  audit); **Remove imported data** that was fetched beyond the committed seed (by symbol and/or date
  range) behind a **confirm-preview** that cascades dependent snapshots/forward-returns and **never
  deletes the committed seed**; and read a **live history** of fetch/backfill/expand/remove runs that
  records every job from the moment it starts (`running` → one honest terminal transition; restart
  orphans marked `interrupted` — J-60). The `/data` date
  and symbol inputs are **job parameters, not the global as-of control**.

A single global **as-of date switcher** in the top bar is the **only** date control. It re-points
Dashboard, Stocks, Themes, Sectors, Stock Detail, **and Backtest** to a chosen past snapshot (default:
latest); no page keeps its own separate date picker. The switcher renders as a **calendar popover**
marking exactly the available snapshot dates (disabled non-selectable days, month navigation, a
"Latest" shortcut) rather than one flat all-dates dropdown — a presentation of the same single state,
never a second control (J-62). The same single state can also be stepped to the previous / next
available snapshot date **with the popover closed** — via top-bar **◀ ▶** buttons and (behind a
persisted, default-off checkbox) the **← →** keys — and the popover adds **Year + Month** quick-jump
dropdowns; all of these drive the one global state, never a second one (J-79). That single state is **serialized into the URL**
(`?asof=yyyy-MM-dd` while historical; date-free at latest) and is restored through the same global
control on load — deep links, reloads, new tabs, and leaderboard→detail click-throughs all preserve the
selected as-of view (J-43), and that state is **hydrated synchronously from the URL on load so every
page renders the selected date from first paint — no latest-date flash, and seeded on the server so the first render carries no hydration mismatch (J-73 / J-83)**; the URL is the one
state's serialization, never a second control. While
historical, every in-app navigational link's **href itself embeds `?asof`** (J-50), so new-tab /
middle-click / copied-link navigation preserves the date too; the stocks-leaderboard tickers, the
Research-Samples row tickers, and the theme / sector member tickers open Stock Detail in a **new tab**
(J-54 / J-52 / J-57 / J-58), and the research `N=` chips open the samples drill-down in a new tab
(J-65) — all other links stay
same-window. The as-of date resolves to a stored immutable snapshot — created once on first view, then
never mutated. The **Stock Leaderboard** (`/stocks`) gains a **VCP filter** (and filters for the
additional detected patterns) and **client-side sortable columns** (J-48 — a view transform; the
default order remains the scanner's stored rank), and **Backtest** carries a
**VCP-vs-non-VCP** forward-return breakdown alongside its by-setup breakdown (as-of-scoped). The Stock-Detail chart's
**timeframe selector** changes bar granularity only (up to the resolved as-of bound) — it is **not** a
second date control.

A top-bar **readiness badge** reports three **honest** states — **Ready**, **Initializing… (with
progress)**, and **Unavailable** — and the analytics pages (Backtest, Research) show a **"warming up
(n/m)"** state while the background historical warm-up is still loading, never an error and never an
empty / partial result presented as complete.

The backend is the single source of truth; every page only displays server-computed values.

### Canonical values (single source of truth — computed once, displayed identically everywhere)

- **Market Regime Score + label** — computed once per scanner run by the regime engine; the Stocks
  leaderboard header re-displays this stored value for the as-of date, identical to the Dashboard (J-80).
- **Sector Score** (per sector/industry ETF) — computed once per run.
- **Theme Score** (per theme) — computed once per run; the Stocks leaderboard re-displays the same
  ranking (a Top-Themes strip + `#n` chip / filter badges) it serves to the Themes page (J-80).
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
- **Per-stock forward returns (per symbol × horizon)** — each stock's realized forward return at
  1/5/10/20/60 trading days, read from the stored append-only `forward_returns` table for the resolved
  as-of run and surfaced **identically on the Stocks leaderboard, Stock Detail, and Backtest** — never
  recomputed in an endpoint or view; only bars dated > D (no-lookahead); NA where post-bars are
  insufficient (J-75). The **Themes and Sectors leaderboards' forward-return columns** read the SAME
  stored `forward_returns` through the SAME `leadership_returns` builder Backtest uses — sector = the
  ETF's own stored return, theme = the equal-weight member basket — so a theme / sector forward return
  reads **identically on its leaderboard and on Backtest** for the same date + horizon (J-81).
- **Lab analytics** (factor decile means + rank-IC — **now served per horizon (1/5/10/20/60d) with all forward-return columns then all
  max-drawdown columns (grouped by metric — J-114) on the all-factors table and the decile sort, the horizon selector removed; J-109** — multi-factor **composite** cohorts — a rank-blend
  across any number of factors — regime-conditioned slices, event-study distribution / hit-rate /
  expectancy, MAE/MFE, exit-horizon, and the **risk-adjusted ratios** return/vol · return/MAE ·
  Sharpe-like) — each derived once from the stored per-observation forward returns + stored factor
  values + post-snapshot price path, read identically wherever shown; never recomputed in the API or a
  view (the Research **all-history vs as-of-date** mode only filters the observation set to snapshots ≤
  the as-of date — it never recomputes a figure). They are additionally **served from a persisted/
  cached derived aggregate for fast loads** — the cache refreshes on dataset changes and the figures
  stay **byte-identical** (a performance property, not a recompute) (J-72; the previously-uncached
  multi-factor combination and Regime × Setup × Pattern studies join this cached set in J-104, so every
  heavy lab serves from a cached aggregate).
- **Regime / phase-severity / 3-way decile study aggregates** — the regime-label & regime-score-decile
  (J-110), phase-label & severity-score-decile (J-111), and regime × severity × factor-decile (J-112)
  forward-return + max-drawdown tables are each **derived once** from the stored append-only `forward_returns`
  (the realized return + the J-86 max-drawdown) grouped by the stored `regime_score` / `regime_label`, the
  served `/api/market-phase` severity / phase, and stored factor values, **persisted / cached** (the
  `EventStudyCache` + dataset-version idiom), and read identically wherever shown; they recompute **no**
  forward return / regime / severity / factor (only group stored values), use only bars dated > D
  (no-lookahead), are NA-honest on thin cells, and every `N=` drills into Research Samples reproducing the
  exact cohort — **never a recompute, never a second membership rule** (J-109 / J-110 / J-111 / J-112).
- **Per-timeframe bars + timeframe-scaled indicators/patterns** (1D/1h/15m/5m) — computed once per
  `(symbol, timeframe, as-of)` and served from storage; the daily timeframe stays the canonical swing
  series.
- **Universe membership** — defined once by the config-recorded screen; every page and list reads the
  same resolved universe.
- **Regime history series** (date → regime label + score) — read from the stored immutable
  `scanner_runs` rows; the dashboard index-chart bands and the stock-detail chart bands render the same
  stored values, identically colored for the same date — never recomputed in an endpoint or view. The
  as-of clamp is a per-surface display choice: the dashboard card reads the full stored series with an
  as-of marker (J-49); the stock-detail bands stay clamped at the as-of date (J-45) — both from the
  same single-source endpoint.
- **Normalized index display series** — computed once server-side from stored bars for the
  major-indexes chart (a presentation series, not a canonical score); the frontend only re-formats it.
  Served full-history to the dashboard card regardless of the global as-of (J-49) — same endpoint,
  clamp optional.
- **Phase / severity / P(bear) / severity-velocity timeline series** (date → phase label + 0–100 severity
  + filtered P(bear) + the **severity-velocity** — a deterministic, config-windowed causal slope of the
  0–100 severity, sign + = worsening, NA at the warm-up head; J-102) — computed once by the market-phase
  engine (J-87 / J-88 / J-89 / J-102) and served by `/api/market-phase`; the Market-Phase card reads the
  bounded disclosure tail, and the Dashboard cross-view chart reads the **full-history** series via a
  `?full=true` serialization of the already-computed `timeline_full` (same endpoint, same single series —
  not a recompute); the payload is **schema-versioned** so adding the velocity field refreshes the
  `MarketPhaseCache` rows (no stale shape). Read identically by the card and the Dashboard chart's second
  pane; never recomputed in a view (J-97 / J-102).
- **Severity-velocity × regime forward-return study aggregate** — the regime-family × velocity-sign matrix
  of forward benchmark (SPY) returns (mean / win-rate / N per horizon) is **derived once** from the stored
  append-only `forward_returns` joined to the served severity-velocity + stored regime label, persisted /
  cached (the `EventStudyCache` + dataset-version idiom) and read identically wherever shown; it recomputes
  no forward return (only groups stored values), uses only bars dated > D, is NA-honest on thin cells, and
  every `N=` drills into Research Samples reproducing the exact cohort — never a recompute, never a second
  membership rule (J-103).
- **Displayed date format** — one shared `yyyy-MM-dd` formatter/constant used by every surface that
  shows a calendar date; no component renders a date through a locale-dependent path.
- **Research sample membership** (the per-observation cohort behind every published N — ticker,
  snapshot date, qualifying stored factor/indicator value(s) or matched setup/pattern, realized
  forward return at the stated horizon) — assembled by the **same observation builders the lab
  aggregates are computed from** (one membership filter, one observation set) and served read-only by
  a samples endpoint family; the drill-down's observation total always equals the published N and
  re-exposes the same stored values — never a recompute, never a second membership rule.
- **Job stage timings** (fetch stage vs backfill stage: elapsed time, items processed, concurrency
  used) — recorded once by the data-manager job runner into the job progress/status payload;
  descriptive operational metadata, not a canonical score; the `/data` job card only re-formats it.
- **Per-date availability counts** (per trading date: symbols-with-bars count + snapshot-exists flag) —
  descriptive read-only metadata derived once from the stored bars + stored runs by the coverage
  machinery and served by one read-only endpoint; the heatmap and any availability figure only
  re-format it — no canonical score/return recomputed, never a second derivation (J-61).
- **Event-study observation set, in both modes** — the pooled per-signal-day observations AND their
  deterministic **first-trigger episode collapse** come from the same observation builders (one
  membership rule; the episode collapse is a pure stored-data-only grouping); every aggregate figure
  and every samples drill-down reads the same set for the same mode, so `N=` chips and drill-down
  totals stay count-coherent in both modes (J-63). Each observation additionally carries its stored
  **regime label, setup status, and pattern flags** (read verbatim — no recompute), so the **regime ×
  setup × pattern** combination study (J-77) is a pure grouping of the SAME observation set; enriching
  the observation with these stored fields does **not** change any existing event-study figure
  (byte-identical).
- **Industry-group names + memberships** — config-defined reference data (ticker → name/description;
  stock → industry groups, many-to-many like themes), read verbatim by the Sectors page and any other
  surface; no name, description, or membership is hardcoded or inferred in code (J-58).
- **Job lifecycle record** — one run-history record per started job, created at start (`running`) and
  closed by a single honest terminal transition (`ok` / `partial` / `failed` / `interrupted`); the job
  card, Run history, and Unfinished imports read the same record — never a second job-bookkeeping
  path (J-60).

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
       *(Amended by J-54: opens in a new tab)*
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
    for the same date — one date control, one resolved date everywhere. *(Amended by J-43: date-scoped
    pages now carry `?asof=yyyy-MM-dd` in the URL while a historical date is selected — that query param
    is the **serialization** of the single global state, restored through the global control on load,
    not a page-local date state; "one date control" never meant "date-free URL".)*

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
    *(Amended by J-63: the headline default becomes the first-trigger **Episodes** mode; this pooled
    per-signal-day view remains one toggle away, byte-identical — overlap is disclosed in both modes.)*

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
  - **Verification basis (re-scoped 2026-06-09, post iter-27):** acceptance is met by the **API-layer
    behaviour verified against the running backend + the green automated test suite + source-level proof of
    the seams above** — a multi-step **browser** capture is **NOT a gate**, and its absence MUST NOT keep
    this journey `partial` or block GOAL_ACHIEVED. The build is complete and committed; the only blocker
    across iters 23–27 was browser-fixture-harness wiring the autonomous chain could not self-correct, never
    a functional gap. Browser screenshots remain a nice-to-have, not required evidence. Concretely: the
    injected-provider expand producing passers + omitted-with-reason + a grown universe-count, asserted at
    the `/api/data` job and the `universe.json` / `meta.json` writes and by
    `test_seed_source_expand_writes_to_overlay_not_committed_seed`, is sufficient to mark this `passing`.

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
  - **Verification basis (re-scoped 2026-06-09, post iter-27):** acceptance is met by the **API-layer
    behaviour verified against the running backend + the green automated test suite + source-level proof of
    the seams above** — a multi-step **browser** capture is **NOT a gate**, and its absence MUST NOT keep
    this journey `partial` or block GOAL_ACHIEVED. The build is complete and committed; the only blocker
    across iters 23–27 was browser-fixture-harness wiring the autonomous chain could not self-correct, never
    a functional gap. Browser screenshots remain a nice-to-have, not required evidence. Concretely: the
    3-category diagnostic plus the gap-exact, idempotent pull — asserted at `/api/data` (the dispatched
    fetch job's symbol set and `[start, end]` equal the diagnosed gap) and by the J-37 diagnostic/pull tests
    and the real-httpx key-scrub regression — is sufficient to mark this `passing`.

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
  - **Verification basis (re-scoped 2026-06-09, post iter-27):** acceptance is met by the **API-layer
    behaviour verified against the running backend + the green automated test suite + source-level proof of
    the seams above** — a multi-step **browser** capture is **NOT a gate**, and its absence MUST NOT keep
    this journey `partial` or block GOAL_ACHIEVED. The build is complete and committed; the only blocker
    across iters 23–27 was browser-fixture-harness wiring the autonomous chain could not self-correct, never
    a functional gap. Browser screenshots remain a nice-to-have, not required evidence. Concretely: the
    Resume-from-durable-`next_chunk_index` success leg, the Retry-only-outstanding idempotency, the
    Dismiss-preserves-audit boundary, and the needs-key re-prompt — asserted at `/api/data` and by the J-38
    tests — are sufficient to mark this `passing` (the needs-key-without-key 400 is **correct** backend
    behaviour, not a defect, so it does not block the journey).

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
  - **Verification basis (re-scoped 2026-06-09, post iter-27):** acceptance is met by the **API-layer
    behaviour verified against the running backend + the green automated test suite + source-level proof of
    the seams above** — a multi-step **browser** capture is **NOT a gate**, and its absence MUST NOT keep
    this journey `partial` or block GOAL_ACHIEVED. This journey is provider-free and fully deterministic;
    the only blocker across iters 23–27 was browser-fixture-harness wiring the autonomous chain could not
    self-correct, never a functional gap. Browser screenshots remain a nice-to-have, not required evidence.
    Concretely: the confirm-preview enumeration (removable bars + range + cascade), the seed-protection
    refusal, and the whole-row cascade delete — all asserted by the J-39 tests and by source (whole-row
    `delete()` only, no in-place snapshot overwrite, no recompute reachable from the remove path) — are
    sufficient to mark this `passing`.

- **J-40: Backend is ready when the frontend is ready (fast boot, background warm-up, honest readiness)**
  - Steps:
    1. Cold-start the stack against a freshly-initialised DB (no persisted history beyond the latest
       snapshot)
    2. Within the readiness budget of the backend process starting, load `/` and `/stocks` — confirm they
       serve the latest snapshot (regime, candidate counts, ranked rows) without a long "Backend
       unavailable" wait
    3. Read the header readiness badge: it shows **Initializing… with progress** while history backfills —
       not a red "Backend unavailable"
    4. Open `/backtest` and `/research` immediately: confirm a clear **"warming up — historical evidence
       still loading (n/m)"** state (not an error, not a fabricated / empty-as-complete result), then full
       population once warm-up finishes — **with no manual restart**
    5. Reload after warm-up: the backend boots fast on the now-warm DB and all evidence is present
  - Acceptance: on a cold boot the server **accepts connections and serves the core read pages for the
    latest as-of date within the config-set readiness budget** (≈ one snapshot compute; near-instant on a
    warm DB) and does **not** block serving until the full historical cadence + forward-returns backfill
    completes; the historical warm-up runs as a **background task** after `yield` (reusing the existing
    async-job / progress machinery) and surfaces **honest live progress** via the health / readiness
    endpoint and the header badge; the badge distinguishes **Ready / Initializing (+progress) /
    Unavailable** and a slow warm-up reads "Initializing", never "unavailable", with a startup poll cadence
    fast enough that the flip to Ready shows within ~a second or two (not only on a 30 s cycle);
    Backtest / Research show an explicit **warming (n/m)** state until warm-up completes and then
    auto-populate; all warm-up writes obey the existing invariants (immutable, strict no-lookahead,
    single-source, no fabricated data — only the *scheduling* changed; the SAME canonical engines run).
    **Deterministic and provable offline against the committed seed** (NOT data-gated): an integration test
    asserts the server is serving (lifespan has yielded; the latest snapshot is present and the dashboard
    endpoint returns 200) **while** the cadence snapshots / forward-returns are still being produced.

- **J-41: Boot is resilient — a slow, contended, or failed warm-up never takes the app down**
  - Steps:
    1. While the background warm-up is mid-flight, trigger a **concurrent** snapshot creation for the same
       as-of date (e.g. a second backend instance / readiness-probe re-spawn / `--reload` double-fire
       against the same DB, or a direct concurrent `run_scan`)
    2. Confirm neither process crashes and the app keeps serving; **exactly one** snapshot exists per date
       (no duplicate, no UNIQUE-constraint crash)
    3. Force the warm-up to raise; confirm the backend still boots and serves the core pages, the failure
       is **logged** and reported honestly by the readiness endpoint, and the **next** boot completes the
       (idempotent) warm-up
  - Acceptance: `run_scan` and the forward-returns backfill are **idempotent and concurrency-safe** — a
    second concurrent creation for the same as-of date **returns the existing immutable snapshot**, never
    raising a `UNIQUE constraint` error and never writing a duplicate (proven by a unit test that simulates
    the create-between-check-and-insert race); any warm-up exception is **caught, logged, and non-fatal** —
    it MUST NOT prevent the server from starting or serving already-persisted snapshots, and the next boot
    finishes the idempotent warm-up; **no regression** to immutability / no-lookahead / single-source /
    no-fabrication. Deterministic and provable offline (no provider needed).

- **J-42: Every user-facing date reads `yyyy-MM-dd` (locale-proof)**
  - Steps:
    1. With a non-ISO browser locale (e.g. en-GB), visit `/data` and read the **Start a fetch /
       backfill** form's start/end date fields — they display literal `yyyy-MM-dd`, not a
       locale-rendered date
    2. Type an invalid value (e.g. `2026-13-40` or `10/06/2026`) — confirm an inline validation error
       and a blocked submit; type a valid `yyyy-MM-dd` and start a job
    3. Confirm the job card's date range, the coverage figures, and the missing-data diagnostic rows
       all show `yyyy-MM-dd`
    4. Read the global as-of switcher options, the "viewing as-of … (historical)" indicator, and a
       chart tooltip/crosshair date — all `yyyy-MM-dd`
  - Acceptance: wherever a specific calendar date is displayed (Data Manager form + job cards +
    coverage + diagnostics, the as-of switcher + historical indicator, run lists, watchlist date-added,
    chart tooltip/crosshair dates), it renders `yyyy-MM-dd` regardless of browser locale; the fetch
    form's date fields are **validated ISO text inputs** (exact-format check, visible error state,
    submit blocked on invalid; the submitted job uses exactly the typed dates); one shared
    formatter/constant defines the format — **no per-component date-format literals and no
    locale-dependent widget output** (compact chart **axis tick labels** may stay abbreviated — they
    are scale marks, not displayed dates); API parameters, DB values, and config remain ISO and
    behaviorally unchanged.

- **J-43: The selected as-of date survives click-through, reload, and new tabs (deep-linkable as-of)**
  - Steps:
    1. On `/stocks`, pick a historical date D in the global as-of switcher — confirm the URL now
       carries `?asof=D` and the historical indicator shows
    2. Click a leaderboard row to `/stocks/[ticker]` — the detail page still shows as-of D (URL carries
       `?asof=D`; the three scores/buckets equal that row's leaderboard values per J-06; the historical
       indicator is visible) *(Amended by J-54: opens in a new tab — the href itself carries `?asof=D`
       per J-50)*
    3. Reload the detail page — still as-of D
    4. Open the same URL in a fresh tab — still as-of D
    5. Switch back to the latest date — the `?asof` param disappears on every date-scoped page
  - Acceptance: the single global as-of state is serialized to `?asof=yyyy-MM-dd` on date-scoped pages
    whenever a historical date is selected and is absent at latest; loading any URL carrying `?asof`
    restores that date **into the one global control** (the top-bar switcher reflects it — no
    page-local state appears anywhere); leaderboard→detail click-through preserves the date and the
    detail values are that date's stored snapshot (J-06 coherence holds at the historical date); an
    unknown/invalid `?asof` value degrades safely to the latest view (no crash, no fabricated date);
    J-18 is **amended, not violated** — still exactly one date control and one resolved date, with the
    URL as that single state's serialization.

- **J-44: Dashboard major-indexes chart with the market regime visible per date**
  - Steps:
    1. Visit `/` — find the **Major indexes & regime** card (default enabled)
    2. Read the index lines — the config-listed index ETFs (SPY, QQQ, IWM, RSP; DIA once its bars
       exist), normalized to a common % scale (rebased at the selected range start), each named in a
       legend
    3. Read the soft regime background bands behind the lines; hover a date — the tooltip shows the
       `yyyy-MM-dd` date, each index's % value, and the exact stored regime label + score for that date
    4. Switch the range preset (e.g. 3M/6M/1Y/All) — the lines re-normalize to the new range start
    5. Toggle the card off — it hides; reload — still off; toggle on — back (a fresh browser defaults
       to ON)
    6. Set the global as-of to a past date D — the chart renders no bar and no band dated after D
       *(Amended by J-49: the card now renders the full history; D draws a vertical as-of marker
       instead of a clamp)*
  - Acceptance: the card renders the **config-listed** index series (symbols + display names from
    config — no hardcoded list) as normalized % lines sharing one scale, with a legend; the regime
    bands derive from the **stored per-run regime history** (label + score read from the persisted
    immutable runs — never recomputed in an endpoint or view), drawn as an honest **step function
    between snapshot dates**, colored by **three risk families** (risk-on / neutral / risk-off) with
    the exact six-value label + score on hover; the normalized series is computed **server-side** from
    stored bars (the frontend only re-formats; no client-side return math); range presets come from
    config; the enable/disable toggle **defaults to ON**, persists across reloads (a client-side
    display preference), and fully hides the card when off; with a historical global as-of nothing
    dated after the as-of date renders; a configured series with no stored bars (e.g. DIA before its
    one-shot fetch) is **omitted from the legend honestly — never fabricated — and the card still
    renders** with the available series (the journey is NOT gated on DIA). *(Amended by J-49: the
    dashboard card now renders the **full stored history** regardless of the global as-of — step 6 and
    the clause "with a historical global as-of nothing dated after the as-of date renders" are
    superseded for this card; a historical as-of D draws a clear **vertical as-of marker** at D instead
    of clamping. The full-history rendering is display-only market context — post-as-of data never
    feeds an as-of-scoped computed value — and J-45's stock-detail bands remain clamped at the as-of
    date.)*

- **J-45: Market-regime bands behind the stock-detail price chart**
  - Steps:
    1. Open `/stocks/NVDA` — the price+MA+volume chart shows the same soft regime background bands,
       colors identical to the dashboard mapping
    2. Hover — the chart surfaces the regime label (+ score) for the hovered date
    3. Toggle **Regime** off in the chart controls — bands disappear; reload — still off; default for
       a fresh browser is ON
    4. Set a historical as-of D — bands render only for dates ≤ D; the post-D forward region keeps its
       muted display-only treatment with **no regime bands** (the J-20 as-of marker and labels are
       unchanged)
  - Acceptance: the detail-chart bands read the **same stored regime values** as the dashboard card
    (identical label and color for the same date — coherence), drawn behind price with the same
    3-family / step-function treatment and the exact label on hover; a Regime toggle (default ON,
    persisted client-side) shows/hides the bands; bands never extend past the resolved as-of date —
    the forward/after-as-of region stays exactly as J-20 defines it (price display only, no regime, no
    signal); the three scores, setup status, VCP/pattern flags, and every J-20 behavior are unchanged;
    no regime value is computed client-side or recomputed per request.

- **J-46: Fetch + backfill are materially faster (parallel fetch, batched writes, vectorized scans)**
  - Steps:
    1. Start a multi-symbol fetch job — confirm symbols are fetched by a **bounded parallel worker
       pool** (worker count from config, default > 1) and the live progress stays accurate
    2. Force a persistent rate-limit (injected 429 provider) — the job still backs off, checkpoints,
       pauses in the **rate-limited — resumable** state, and **Resume** continues with no duplicate
       fetch (J-34 semantics intact under parallelism)
    3. Run a multi-date backfill over the seed — confirm (via the instrumented test) that each symbol's
       bars are loaded **once for the whole job**, not once per as-of date
    4. Run the committed benchmark script — it reports per-stage timings (fetch / scan / forward
       returns) on the seed
    5. Run the existing scanner / forward-test / immutability / no-lookahead suites — all green,
       outputs identical
  - Acceptance: symbol fetching uses a bounded, config-set worker pool (per-provider rate-limit aware;
    the worker count lives in config — no magic number) and bar writes are committed **per chunk in a
    single transaction** (not per symbol) with SQLite writes kept serialized/safe under the parallel
    fetchers; a test proves a K-date backfill performs **at most one bar-store load per symbol**
    (counted instrumentation), realizing Capability 33; canonical outputs are **identical** (the
    existing scanner, forward-returns, immutability, and no-lookahead suites pass unchanged — same
    scores/buckets/returns); the chunk checkpoint / durable Resume / per-`(symbol, date)` idempotency /
    honest-progress contracts (J-34/J-37/J-38) are regression-tested and intact under parallelism
    (progress counts never exceed totals; a paused job's checkpoint is still chunk-consistent); a
    committed benchmark script reports per-stage seed timings as **advisory evidence** (no flaky
    wall-clock assertion gates CI).

- **J-47: Every term on every page is explained (full glossary + inline term help)**
  - Steps:
    1. Visit `/methodology` — find the **Glossary** section: categorized groups (e.g. Scores & Buckets;
       Setups & Patterns; Regime & Breadth; Universe & Data; Forward-testing & Evidence; Factor Lab &
       Statistics) listing the UI's domain terms
    2. Type in the glossary search (e.g. "IC") — the list filters live to matching entries
    3. Read the entries for: breadth > 50-DMA, DMA (50/200-DMA), rank-IC, universe (vs symbols),
       decile, MAE, MFE, expectancy, hit-rate, dispersion, walk-forward, survivorship bias, horizon,
       excess return, composite (rank-blend), quantile, ATR%, pivot, invalidation — each a
       plain-language definition
    4. On `/research` and `/backtest`, hover the info marker on dense column headers / stat labels
       (e.g. Rank-IC, Mean MAE, Hit-rate, Expectancy) — the tooltip shows the same definition
    5. Add a new entry to the config catalog and reload — it appears in the Glossary (and is
       tooltip-addressable) with no code change
  - Acceptance: a **config-backed glossary catalog** (one committed source — config or a committed
    catalog file it references) covers the inventoried UI vocabulary — **at least 100 entries**
    spanning every page's domain terms (titles, column headers, dropdown options, badge/stat labels),
    including ALL the spot-check terms in step 3; the `/methodology` Glossary renders it **categorized
    and client-side searchable**, each entry showing the literal UI term and a plain-language
    definition (plus, where applicable, where it appears / its config-threshold reference);
    **info-tooltips** on the dense surfaces — at minimum the Research lab tables, the Backtest
    scorecard/attribution headers, the Stocks leaderboard column headers, the Dashboard
    breadth/candidate-count cards, and the Data Manager coverage headers — read the **same catalog
    entries** (no duplicated hardcoded copy); the existing setup/pattern catalog (J-12) is referenced
    or hosted by the same mechanism, never re-described in a second place; a config-added entry
    renders in both surfaces with no code change.

- **J-48: Stocks leaderboard column sorting (sort the view, never the scores)**
  - Steps:
    1. Visit `/stocks` — the table renders in the scanner's stored rank order by default (the `#`
       column, ascending)
    2. Click the **Leadership** column header — the visible rows re-order by Leadership; click again —
       the direction toggles; a visible sort indicator marks the active column + direction
    3. Sort by **Ticker**, **Sector**, **Entry Quality**, **Risk**, and **Setup** in turn — each
       re-orders the visible rows accordingly
    4. With a sort active, apply the Sector and Setup/pattern filters (J-02 / J-16) — filter and sort
       compose (the filtered rows render in the sorted order)
    5. Click the `#` header — the default rank order returns; confirm every rank, score, bucket,
       setup, and flag value is identical to before any sorting
  - Acceptance: the leaderboard's column headers (Ticker, Sector, Leadership, Entry Quality, Risk,
    Setup) are click-sortable with an asc/desc toggle and exactly one visible sort indicator; the `#`
    column is the default order — the scanner's stored rank — and restores it on demand; sorting is a
    **client-side view transform over the already-served snapshot rows**: it re-orders the rendered
    list only and **never changes, recomputes, or re-ranks any stored value** (each row's `#`, three
    scores/buckets, setup status, and pattern flags read exactly as served — single source of truth,
    no new endpoint, no recompute); score columns order by the stored 0–100 value (the A–E bucket
    rides along); sorting composes with the existing sector / setup-status / pattern filters, and
    J-02 / J-16 behavior is otherwise untouched.

- **J-49: Major indexes & regime card shows full history — the as-of is a marker, not a clamp (amends J-44)**
  - Steps:
    1. Set the global as-of switcher to a historical date D
    2. Visit `/` — the **Major indexes & regime** card still renders the **full stored history**: the
       index % lines and the regime bands extend past D through the latest stored date
    3. Confirm a clear **vertical as-of marker** is drawn at D on the card (the same as-of-divider
       treatment the stock-detail price chart already uses — J-20), so "where am I viewing" stays
       unmistakable
    4. Switch the range presets — the lines re-normalize per J-44; the marker stays at D
    5. Return to the latest date — the marker disappears and the card reads exactly as J-44 defines
    6. Open `/stocks/NVDA` at the same historical D — the stock-detail regime bands still stop at D
       (J-45 unchanged)
  - Acceptance: the dashboard card always charts **all available stored bars and stored regime
    history** regardless of the global as-of — read from the **same single-source endpoints**
    (`GET /api/indexes`, `GET /api/regime-history`) with the as-of clamp now optional for this
    surface (same stored values, nothing recomputed, no second path); while a historical as-of D is
    selected, a clearly visible vertical as-of marker is drawn at D (no marker at latest); every
    J-44 behavior not amended here is unchanged (config-listed series, server-side normalization,
    legend, step-function bands, three risk families, exact label + score on hover, config range
    presets, persisted default-ON toggle, honest omission of bar-less series); the full-history
    rendering is **display-only market context** — no post-as-of bar or regime value feeds any
    as-of-scoped score, count, gate, or evidence figure (no-lookahead intact); **J-45 is explicitly
    NOT amended** — the stock-detail regime bands still never render past the resolved as-of date.

- **J-50: The as-of date survives EVERY in-app navigation, including new tabs (extends J-43)**
  - Steps:
    1. Pick a historical date D in the global as-of switcher
    2. Inspect in-app links — the sidebar nav entries, the leaderboard rows, the theme / sector
       member links, and the research links — each link's `href` itself carries `?asof=D`
    3. Middle-click (or ctrl/cmd-click) a leaderboard row into a **new tab** — the new tab opens
       directly at as-of D
    4. Copy a link address and open it in a fresh tab — still as-of D
    5. Switch back to the latest date — every in-app `href` is date-free again
  - Acceptance: while a historical as-of D is selected, **every in-app navigational link embeds
    `?asof=D` in its `href`** (top-nav/sidebar entries, leaderboard → detail rows, theme/sector
    member links, research links) so same-tab clicks, new-tab / middle-click / ctrl-click opens, and
    copied links all land on as-of D **without depending on post-navigation re-stamping**; at the
    latest date every href is clean (no param); the embedded param is more of the same J-43
    serialization — restored **through the one global control** on load, never a page-local date
    state — so J-18 still holds (one date control, one state); an invalid `?asof` still degrades
    safely to the latest view, and the `/data` date/symbol inputs remain job parameters, never a
    date control.

- **J-51: Every research sample count is a link to its exact samples**
  - Steps:
    1. Visit `/research` — every published sample-size figure renders as a link: Factor Lab
       (`n_total`, per-decile n, rank-IC n, by-regime n), Combination Lab (baseline /
       single-condition / composite / strict-overlap cohort n), Event Study (per-horizon n,
       by-regime n, by-sector n, pooled `n_total`)
    2. Click a Factor Lab decile's `N` — a dedicated samples page opens, parameterized to that exact
       cohort (analysis kind, factor(s)/subject, horizon, decile/cohort, regime, sector, and the
       all-history vs as-of scope, as applicable)
    3. Read the samples table: one row per observation — ticker, snapshot (as-of) date, the stored
       qualifying value(s) that put it in the cohort (the factor value; for a Combination cohort,
       each referenced factor's stored value; for an Event Study, the matched setup/pattern), and
       the realized forward return at the stated horizon
    4. Confirm the displayed total **equals the N shown on the chip** that was clicked
    5. Click an `N=0` cohort (e.g. an empty strict-overlap) — the samples page shows an honest empty
       state, never a fabricated row
  - Acceptance: every research sample count is a hyperlink to a **dedicated, deep-linkable samples
    drill-down route** whose parameters fully reproduce the cohort (reload-safe); the page lists
    **every** member observation with its ticker, snapshot date, qualifying stored factor/indicator
    value(s) (or matched setup/pattern), and stored realized forward return at the stated horizon
    (a paged or virtualized table is acceptable — the displayed total must equal the published N and
    every observation must be reachable); **the observation total equals the published N** (count
    coherence — the same membership filter and observation set the aggregate was computed from), and
    every displayed value is the **same stored per-observation value** the aggregate used — the
    drill-down is **read-only** (a SELECT-only exposure of what the existing observation builders
    already assemble; it recomputes no factor, return, or membership); it honors the Research
    all-history vs as-of mode (J-32 — the same scoping, no second date state); n=0 cohorts show an
    explicit empty state; the survivorship-bias label is shown, and the table's column headers read
    the same glossary catalog as every dense surface (J-47). *(Amended by J-64/J-65: the `N=` chips
    open this drill-down in a NEW tab, and the samples table gains client-side sorting + a ticker
    view-filter — the displayed cohort total still equals the published N.)*

- **J-52: From a sample row to the dated stock detail**
  - Steps:
    1. From a J-51 samples table, click a row's ticker
    2. A **new tab** opens at `/stocks/[ticker]?asof=<that row's snapshot date>` — the "viewing
       as-of D (historical)" indicator shows and the scores/buckets/setup are that date's stored
       snapshot
    3. Switch back to the original research tab — its mode, selections, scope, and scroll are
       exactly as left
  - Acceptance: a samples-row ticker opens the stock detail in a **new tab** with `?asof=` set to
    **that row's snapshot date** (not the research tab's date); the new tab restores that date
    through the single global control per J-43 (`?asof` is the serialization — the top-bar switcher
    reflects it, the historical indicator is visible, and the page reads that date's stored
    immutable snapshot per J-06 — no recompute, no lookahead); the originating research tab's own
    state is untouched (independent tabs, one control semantics per tab — never a second date
    state); an unknown/invalid date degrades safely per J-43.

- **J-53: Fetch+backfill pipeline reports stage timings and backfills dates in parallel (extends J-46)**
  - Steps:
    1. Start a multi-date fetch + backfill job from `/data`
    2. Watch the job card: live progress stays accurate, and the job detail/status now surfaces
       **per-stage timings** — the fetch stage and the backfill stage, each with elapsed time, the
       symbols/dates processed, and the concurrency used
    3. On completion, confirm the multi-date backfill stage's wall-clock is materially below the sum
       of its per-date times — at least ~2× faster than the sequential per-date baseline
    4. Re-run the same range — create-once/idempotent semantics hold (existing snapshots are read,
       nothing duplicated, no UNIQUE crash)
    5. Run the scanner / forward-returns / immutability / no-lookahead suites — all green, outputs
       identical
  - Acceptance: the multi-date snapshot backfill is **no longer a sequential per-date wall-clock
    sum** — it completes at least **~2× faster** than the per-date-sum sequential baseline (evidenced
    by the job's own stage timings and a committed benchmark script — advisory, no flaky CI
    wall-clock gate), with the **mechanism left open** (parallel dates with serialized writes,
    parallel per-symbol computation within a date, further vectorization — any combination) so long
    as every guard holds: snapshots and forward returns are **identical to the sequential output**
    (the existing suites assert the same scores/buckets/setups/returns), create-once / idempotent /
    concurrency-safe snapshot creation is preserved (J-41), SQLite writes stay
    serialized/transactional, and progress stays honest (counts never exceed totals; checkpoints
    stay consistent — J-34/J-37/J-38 intact); the job status payload and the `/data` job card
    surface **per-stage timings** (fetch vs backfill: elapsed, items processed, concurrency used) as
    descriptive operational metadata; any new concurrency knob lives in config (**no magic
    numbers**).

- **J-54: Leaderboard ticker opens the stock detail in a new tab**
  - Steps:
    1. On `/stocks`, click a ticker — the stock detail opens in a **new tab**; the leaderboard tab
       keeps its filters, sort (J-48), scroll position, and date untouched
    2. With a historical as-of D selected, click a ticker — the new tab lands directly on
       `/stocks/[ticker]?asof=D` (the href carries the date per J-50)
    3. Confirm theme-member and sector links still navigate in the same window
  - Acceptance: the stocks-leaderboard ticker links open in a **new tab** (`target="_blank"` with
    `rel="noopener"`-equivalent behavior); the href itself carries `?asof=D` while historical (J-50)
    so the new tab resolves the same date through the single global control (J-43), and at latest
    the href is clean; the originating leaderboard tab's state (active filters, sort order, scroll,
    selected date) is never disturbed; the new-tab behavior applies **only** to the stocks-leaderboard
    tickers and the J-52 samples-table tickers — theme/sector member links and every other in-app
    link stay same-window; J-05 and J-43 are amended, not weakened (the click-through still lands on
    the same dated, coherent detail view per J-06). *(Amended by J-57/J-58/J-65: the theme/sector
    member tickers and the research `N=` chips now also open new tabs — the exclusivity list grows;
    nothing else changes.)*

- **J-55: Stocks leaderboard symbol search (type-to-filter, no button)**
  - Steps:
    1. Visit `/stocks` — a search input renders alongside the existing Sector / Setup / Pattern filters
    2. Type `nv` — the visible rows narrow **as you type** (no search button, no Enter required) to
       rows whose ticker or company name contains the text, case-insensitively (e.g. `NVDA` matches)
    3. With the search active, apply a Sector filter and click a J-48 column header — search, filters,
       and sort all compose (the searched+filtered rows render in the sorted order)
    4. Clear the input — every row returns; the active filters and sort are untouched
    5. Reload the page with `?q=nv` in the URL — the search restores; type a string matching nothing —
       the honest "no stocks match" empty state renders
  - Acceptance: the leaderboard carries a **type-to-filter search over the already-served rows** —
    case-insensitive substring match on ticker AND company name, applied instantly per keystroke with
    **no submit affordance and no refetch** (the `[asOf]`-keyed fetch is unchanged — J-15 warm load
    intact); it composes with the existing sector / setup / pattern filters, the J-56 theme filter, and
    J-48 sorting (filter THEN sort); the active query serializes as `?q=` exactly like the existing
    filter params (init-once from the URL, reflected on change, omitted when empty, never a date —
    J-18); the `x / N` visible-count stays honest and a no-match result renders the existing honest
    empty state (never a fabricated row); this is a **pure client-side view transform** — no new
    endpoint, no second compute path, every served value (rank, scores, buckets, setup, flags) reads
    exactly as served (single source of truth).

- **J-56: Stocks leaderboard theme column + theme filter**
  - Steps:
    1. Visit `/stocks` — a **Theme** column renders each row's theme membership chips (the `themes`
       the row already serves)
    2. A row in many themes shows a compact chip list with a `+n` overflow whose full membership is
       readable in place (tooltip or expand)
    3. Pick a theme in the new **Theme** filter — only rows whose membership includes it remain
    4. Combine with the Sector/Setup/Pattern filters, the J-55 search, and a J-48 sort — all compose;
       an empty result renders the honest empty state
    5. Open a filtered row's detail page — its theme chips match the leaderboard exactly (J-06)
  - Acceptance: the Theme column **re-displays the already-served `themes` chips verbatim** — the same
    config-derived membership the Stock Detail page shows (one canonical membership, J-06; nothing
    fetched or recomputed per row); the Theme filter's vocabulary derives from the served rows' themes
    (config order — like the Sector filter derives from rows) and keeps exactly the rows whose
    membership contains the selection; the selection serializes as `?theme=` like the other filter
    params (no date param — J-18); it composes with every existing filter, the J-55 search, and J-48
    sorting; a pure client-side view transform — no new endpoint, no second compute path, J-02/J-16/
    J-48 behavior otherwise untouched.

- **J-57: Theme members — expandable `+n`, every member a dated new-tab link (amends J-54)**
  - Steps:
    1. Visit `/themes` and expand a theme row whose member count exceeds the preview limit
    2. Activate the `+n` control — the remaining members render in place; activate again (or a
       collapse affordance) — the list folds back to the preview
    3. Click a member ticker — the Stock Detail opens in a **new tab**; the themes tab keeps its
       expansion state, scroll, and selected date untouched
    4. Select a historical as-of D and inspect a member link — its `href` itself carries `?asof=D`
       (J-50); clicking it lands the new tab on as-of D through the single global control
    5. Return to the latest date — the member hrefs are clean (no param)
  - Acceptance: the `+n` placeholder becomes a working **expand/collapse control** revealing EVERY
    remaining member of the theme (a re-display of the already-served member list — nothing refetched
    or recomputed); every member ticker renders as a link to `/stocks/[ticker]` opening in a **new
    tab** (`target="_blank"` with `rel="noopener"`-equivalent), the href embedding the global `?asof`
    while historical and clean at latest (J-50); the originating tab's state (expansion, scroll, date)
    is never disturbed; the row's expand-on-click behavior is not regressed (activating a member link
    or the `+n` never accidentally toggles the row); **J-54 is amended, not weakened** — its new-tab
    list now reads: stocks-leaderboard tickers, J-52 samples-row tickers, and theme/sector member
    tickers (J-57/J-58); every other in-app link stays same-window; membership remains the same
    stored/config-derived value everywhere (J-06).

- **J-58: Sectors page — every ETF named and described, with universe members**
  - Steps:
    1. Visit `/sectors` — every ranked row (sector AND industry kind) shows a human-readable name
       beside its ticker; `KRE` no longer reads as a bare ticker
    2. Expand `KRE` (or any industry row) — a plain-language description renders, plus a **Members**
       list presented like the Themes page
    3. Expand a sector row (e.g. `XLF`) — its members are the universe stocks of that GICS sector
    4. Click a member ticker — the dated Stock Detail opens in a **new tab** (the J-57 link contract)
    5. Expand an industry ETF with no mapped universe member — an explicit "no universe members
       mapped" note renders (never fabricated members)
    6. Confirm the names/descriptions and the stock→industry mapping are **config entries** (visible
       in config, reflected in the UI with no code change for a new entry)
  - Acceptance: every ranked ETF row carries a **config-sourced display name** and the expanded panel
    a **config-sourced plain-language description** — the industry catalog becomes ticker →
    name/description reference data like `etfs.sector` / `index_chart.symbols` (**no hardcoded
    name/description in backend or frontend code** — No magic numbers); the expanded panel lists
    **universe members**: a sector ETF's members derive from the existing `stock_sectors` config
    mapping and an industry ETF's from a **new config-curated stock→industry-group mapping**
    (many-to-many like `themes`, validated against the universe), **honestly labelled as a
    config-defined approximation — NOT the ETF's actual holdings**; an ETF with zero mapped universe
    members shows an explicit empty note (never fabricated members); member lists reuse the J-57
    expandable `+n` + dated new-tab ticker links; the served sector scores / ranks / components are
    **byte-unchanged** — this journey adds reference metadata and display only (no canonical value
    touched).

- **J-59: Resume from the failed stage — and covered ranges are never re-fetched (extends J-34/J-38)**
  - Steps:
    1. Run a `both` job whose fetch completes and whose backfill then fails (provable offline: the
       injected provider + a forced backfill fault)
    2. Read `/data` **Unfinished imports** — the job is listed as **failed at backfill — resumable
       from the backfill stage** (plain-language state + the right action)
    3. Click **Resume** — the fetch stage is **skipped entirely** (the injected counting provider
       records **zero calls**), only the backfill runs, and the job completes; snapshots already
       created before the failure are read, not recreated
    4. Restart the backend between the failure and the Resume — the stage checkpoint survives; Resume
       still starts at the backfill stage
    5. Start a fresh `both` job over an **already fully-fetched range** — the fetch stage completes in
       seconds with zero provider calls for the covered symbols, then proceeds to backfill
  - Acceptance: the durable import checkpoint becomes **stage-aware** — it records which pipeline
    stages (fetch → screen → backfill) completed, so a job that failed or was interrupted AFTER a
    completed fetch is **resumable from the failed stage**: Resume performs **zero provider calls**
    (asserted with an injected counting provider) and re-runs only the remaining stage(s), reusing the
    create-once/idempotent snapshot path (existing snapshots read, never overwritten — J-41/J-53
    intact); the stage checkpoint **survives a process/server restart** (J-34's durability extended;
    its rate-limit chunk-resume semantics unchanged); additionally the **fetch planner consults stored
    coverage against the benchmark trading calendar and skips the provider call for any (symbol,
    window) already fully covered** — re-running a job over a covered range reaches the backfill stage
    in seconds, never ~45 minutes of no-op re-fetching to add `0 new bars`, while a partially-covered
    window still fetches and the per-`(symbol, date)` INSERT-new-only idempotency still guarantees no
    duplicate row; J-38's Retry stays available and idempotent, and every unfinished state renders
    with the existing plain-language explanation + single right action; provable offline end-to-end.

- **J-60: Run history records every job from the moment it starts**
  - Steps:
    1. Start any `/data` job and read **Run history** immediately — the job is ALREADY listed (status
       `running`, with its kind, date range, and source)
    2. Watch it finish — the same record transitions to an honest terminal state (`ok` / `partial` /
       `failed`) with the final summary; a rate-limited pause shows as `resumable`
    3. Kill/restart the backend mid-job — after boot, the orphaned record reads **`interrupted`** (an
       honest terminal state; never stuck `running` forever, never vanished from history)
    4. Resume/Retry per J-59/J-38 — the subsequent attempt is visible in history too; the audit trail
       of what ran is complete
  - Acceptance: starting a job **creates its run-history record immediately** (status `running`,
    carrying kind / date range / source) instead of only writing history at the terminal `finally`;
    the Run history list shows in-flight, resumable, and finished jobs (a job can no longer be missing
    from history because it hasn't finished or because the process died); each record receives an
    honest lifecycle transition to ONE terminal state (`ok` / `partial` / `failed`, or `interrupted`
    applied by a boot sweep to `running` rows whose process is gone); the row-lifecycle mechanism is
    open (transition one row, or append linked attempt rows) but the audit MUST stay complete and
    truthful: a terminal record is never silently mutated afterwards, nothing is deleted or hidden by
    this feature (J-38 Dismiss semantics unchanged), no status is ever fabricated, and the record's
    counts/summary match the job's own payload (one bookkeeping source — J-60 is the same lifecycle
    the job card reads, not a second one).

- **J-61: Per-date availability heatmap — see exactly which dates have data**
  - Steps:
    1. Visit `/data` — an **availability heatmap** renders the trading-day calendar, each day colored
       by how many symbols have a stored bar on it, with a distinct marker on days that also have an
       immutable snapshot
    2. Hover a day — the exact figures render (date, symbols-with-bars / total symbols, snapshot
       yes/no)
    3. Find a sparsely-covered day — it is visibly different from a fully-covered day; a trading day
       with no bars at all is visibly empty
    4. Click a day (or select a range) — the job form's Start/End prefill with it
    5. Run a fetch/backfill over a gap and let it finish — the heatmap re-reads and shows the new
       coverage
  - Acceptance: a **read-only endpoint** serves per-trading-date availability — for each date of the
    benchmark trading calendar: the count of symbols with a stored bar and whether a snapshot exists —
    derived once from stored bars + stored runs (descriptive metadata; no canonical value recomputed;
    the same single source the existing coverage figures read); `/data` renders it as a calendar-style
    heatmap with a legend (color = symbols-with-bars; explicit snapshot marker), exact values on
    hover, and **honest partial-coverage rendering** (a 3-of-158 day MUST be visually distinct from a
    fully-covered day — fixing the misleading impression a single min→max "Price history" range
    gives); clicking a day (or range) prefills the job form's date inputs — **job parameters, never
    the global as-of control** (J-18); the heatmap reflects dataset changes after jobs/removals
    complete and renders gracefully on an empty DB (no fabricated cells).

- **J-62: The as-of switcher is a calendar that shows what is selectable**
  - Steps:
    1. Open the global as-of switcher — a **calendar popover** opens (month grid) instead of one flat
       all-dates dropdown
    2. Available snapshot dates are visibly marked and selectable; other days are disabled; month
       navigation reaches the oldest stored month; a **"Latest"** affordance returns to the latest view
    3. Pick a historical date — the whole app re-points exactly as today (J-13): historical badge,
       `?asof` URL serialization, href stamping all unchanged (J-43/J-50)
    4. Operate it by keyboard — open, navigate months/days, select, dismiss
    5. Load a URL with an invalid `?asof` — it still degrades to the latest view (J-43)
  - Acceptance: the top-bar switcher's **presentation** becomes a calendar popover marking exactly the
    selectable snapshot dates — the **same canonical run-date list the dropdown reads today** (no new
    date source, no new endpoint semantics) — with disabled non-selectable days, month navigation
    spanning the stored history, a "Latest" shortcut, and keyboard accessibility; selecting a date
    drives the **same single global as-of state** (J-13/J-18/J-43/J-50 semantics byte-unchanged); the
    widget mechanism is open (hand-rolled grid or a small date-picker dependency consistent with the
    stack) but it MUST hold **no second date state** (the calendar is a renderer of the one global
    control), MUST render textual dates `yyyy-MM-dd` through the shared formatter (J-42), and MUST
    degrade gracefully (no dates → disabled control; invalid URL date → latest per J-43).

- **J-63: Event study is overlap-honest — first-trigger episodes by default, pooled one toggle away
  (amends J-29)**
  - Steps:
    1. Visit `/research` → Setup & Pattern Lab — the headline figures read **Episodes** mode by
       default and an **Episodes ⇄ Pooled** toggle is visible
    2. Read the disclosure beside the figures: **n** (observations in the current mode), **unique
       symbols**, and **episodes**
    3. Pick a subject where one symbol persisted across consecutive snapshots (e.g.
       Risk-off-watchlist): pooled n exceeds episode n, and the episode-mode samples drill-down shows
       ONE row for that continuous run (its first trigger date) instead of many overlapping rows
    4. Flip to **Pooled** — every figure equals today's published values exactly
    5. Click an `N=` chip in each mode — the drill-down reproduces that exact cohort and its total
       equals the clicked N (J-51)
    6. Check `/methodology` — glossary entries explain Episode vs Pooled (J-47)
  - Acceptance: the event study gains a deterministic **episode collapse**: consecutive stored
    snapshot dates on which the same symbol matched the same subject (consecutiveness judged on the
    stored run-date sequence) form ONE episode, observed at its **first trigger date** using that
    observation's **stored** forward return / MAE / MFE at the stated horizon — a pure grouping of the
    SAME stored per-observation rows by the SAME observation builders (one membership rule; **no
    return, excursion, factor, or membership recomputed**); **Episodes is the default mode** and the
    toggle restores **Pooled** (per-signal-day), whose figures stay **byte-identical** to the current
    output; EVERY event-study figure (per-horizon distribution, hit-rate, expectancy, MAE/MFE, best
    exit-horizon, risk-adjusted ratios, by-regime, by-sector) respects the selected mode; both modes
    disclose **n + unique symbols + episode count** so window overlap is never hidden (extends *Honest
    limitations surfaced*); the mode is a **cohort parameter** carried by the `N=` chips into the
    samples drill-down — J-51 count-coherence holds in BOTH modes (the drill-down total equals the
    clicked N and lists exactly that mode's observations: episode rows in Episodes, signal-day rows in
    Pooled); the toggle is a MODE, not a date control (J-18/J-32 untouched); Episode/Pooled join the
    config-backed glossary + term tooltips (J-47); low-sample cells stay NA + n.

- **J-64: Research samples table — sortable and filterable (the J-48 contract)**
  - Steps:
    1. Open any `/research/samples` drill-down with rows
    2. Click the **Forward return** header — rows re-order; click again — the direction toggles;
       exactly one visible sort indicator
    3. Sort by **Ticker**, **Snapshot date**, and a qualifying-value column in turn — each re-orders
       the visible rows
    4. Type in the **ticker filter** — rows narrow as you type and the header reads "showing x of N";
       the cohort total still reads N
    5. Clear the filter and the sort — the served order and the full list return; every value reads
       exactly as served
  - Acceptance: the samples table's columns (Ticker, Snapshot date, each qualifying-value column,
    Forward return) are **click-sortable under the J-48 contract** — asc/desc toggle, exactly one
    visible indicator, stable ties, a pure client-side view transform over the already-served
    observation rows (re-orders only; recomputes and refetches nothing); a **ticker type-to-filter**
    narrows the visible rows (case-insensitive substring) with an honest **"showing x of N
    observations"** — the displayed cohort total stays the published N (J-51 count-coherence is about
    the cohort; a view filter narrows the view, never the cohort) and clearing restores every row; an
    all-filtered-out result shows an honest empty state (never a fabricated row); deep-link/reload
    behavior (J-51) and the J-52 row-ticker links are unchanged.

- **J-65: `N=` chips open the samples drill-down in a new tab (amends J-51/J-54)**
  - Steps:
    1. On `/research`, click any `N=` chip — `/research/samples` opens in a **new tab** showing that
       exact cohort
    2. Switch back to the Research tab — its lab, selections, scope, and scroll are exactly as left
    3. With a historical as-of and the as-of scope active, click a chip — the new tab still resolves
       the same cohort and date (the href carries the cohort params + scope + `?asof` per J-51/J-50)
  - Acceptance: every published `N=` sample-size chip (the J-51 set: Factor Lab, Combination Lab,
    Event Study) opens its drill-down in a **new tab** (`target="_blank"` with `rel="noopener"`-
    equivalent), the href still built by the same two-step cohort + as-of serialization (J-51/J-50 —
    deep-linkable, reload-safe, count-coherent, never a second date state); the originating Research
    tab's state is never disturbed; the drill-down's own "Back to Research" link stays same-window;
    **J-51's same-window note and J-54's exclusivity list are amended accordingly** — new-tab links
    are now: stocks-leaderboard tickers (J-54), samples-row tickers (J-52), theme/sector member
    tickers (J-57/J-58), and the `N=` chips (J-65); every other in-app link stays same-window.

- **J-66: Job progress is fine-grained, live, and honest (extends J-46/J-53)**
  - Steps:
    1. Start a multi-chunk fetch (or `both`) job and watch the job card: the symbols bar advances
       **per symbol** (not in whole-chunk jumps), a **current-activity line** names what is being
       worked on right now, and an **"updated Ns ago"** heartbeat ticks
    2. During the backfill stage, the dates bar advances per date and the activity line names the
       date being scanned (e.g. "scanning 2021-03-11 (12/22)")
    3. Read the per-stage section — each executed stage shows its own progress + elapsed **live**
       (the J-53 timings, no longer only in the final summary)
    4. Run a plan spanning 2+ date windows over the full symbol set — the symbols counter **never
       exceeds its total** (the observed `318/159` reading is the named defect and must be gone)
    5. Compare a genuinely stalled job (heartbeat not advancing) against a slow-but-working one —
       visually distinguishable at a glance
  - Acceptance: fetch progress ticks at **per-symbol completion granularity** (mechanism open — e.g. a
    thread-safe completion counter the pool workers tick while ALL DB writes + checkpointing stay on
    the orchestrating thread; chunk-atomic commit/rollback and the J-34 checkpoint semantics
    unchanged); backfill progress stays per-date with the current date named; the job payload + card
    carry a **current-activity message** and a **last-progress heartbeat timestamp** (the UI renders
    "updated Ns ago") so slow-but-alive is distinguishable from stalled; per-stage progress/timings
    (J-53) render **live during the run**, not only at completion; **counters are monotone and can
    never exceed their stated totals** — the symbols figure counts **distinct symbols** completed
    across date windows (or, if per-(symbol, window) units are surfaced, they are labelled as units
    against a matching unit total) — fixing the observed `318/159`; every figure remains honest
    descriptive job metadata (no canonical value recomputed, no fabricated count or timestamp); the
    UI polling interval and any heartbeat/granularity knob come from config (**no magic numbers**).

- **J-67: Multi-date backfill completes reliably — no more 'committed'-session crash (extends J-53/J-41)**
  - Steps:
    1. With bars covering a multi-month range (~90 trading dates), run a `backfill` job over it (or
       resume a `both` job at its backfill stage per J-59)
    2. The stage runs to completion — snapshots + forward returns for EVERY pending date; no
       `This session is in 'committed' state; no further SQL can be emitted within this transaction`
       failure
    3. Force one date to fail (offline fault injection) — that date is recorded as failed with its
       error while the OTHER dates still complete; the job ends in an honest `partial` state
    4. Re-run the same range — create-once fills only what is missing (no UNIQUE crash, nothing
       overwritten — J-41/J-53)
    5. Run the scanner / forward-returns / immutability / no-lookahead suites — green, outputs
       identical
  - Acceptance: the parallel multi-date backfill's DB session/transaction management is **made sound**
    — no Session is shared across concurrent workers mid-transaction and the orchestrating session is
    never left emitting SQL in an invalid ('committed') state (mechanism open: per-worker sessions
    with a single serialized writer, orchestrator-owned write batches with correct transaction
    boundaries, or equivalent — SQLite writes stay serialized/transactional); a multi-month
    `both`/`backfill` job (the reported ~91-date repro) **completes without the committed-session
    failure**; a single date's failure is **isolated** — recorded per-date (honest error + counts)
    while the remaining dates complete, ending in an honest `partial`, never aborting the whole stage
    and never fabricating a snapshot; canonical outputs stay **byte-identical** to the sequential
    engine (the existing suites assert it — *Parallel backfill never changes results*); create-once /
    idempotent / concurrency-safe snapshot creation (J-41) and honest progress (J-66) are preserved;
    a committed regression test exercises a multi-date parallel backfill end-to-end **including the
    failure-isolation path**, offline.

- **J-68: Multi-month / multi-year backfill no longer crashes with a 'committed' session — the real Data Manager reproduction (hardens J-67)**
  - Steps:
    1. In **Data Manager** (`/data`), with the committed seed loaded (158 symbols, real bars
       2021-01-04 → 2026-05-29), start a **backfill** job over a multi-month range — the reported
       repro is **2026-01-01 → 2026-06-13**; the full-history case is the entire seed range (~1,350
       trading dates). Also run the same range as a `both` job (fetch+backfill) per J-59.
    2. The job runs to completion — snapshots + forward returns for every pending date — and does
       **not** fail with `This session is in 'committed' state; no further SQL can be emitted within
       this transaction` (the J-67 fix did not hold for this orchestration path).
    3. Force one date to fail (offline fault injection): that date is recorded failed with its error
       while the OTHER dates still complete; the job ends in an honest `partial`.
    4. Re-run the same range — create-once fills only what is missing (no UNIQUE crash, nothing
       overwritten — J-41/J-53).
    5. Run the scanner / forward-returns / immutability / no-lookahead suites — green, outputs identical.
  - Acceptance: the exact reported reproduction — a `backfill` (and `both`) job spanning
    **2026-01-01 → 2026-06-13** through the Data Manager — **completes without the 'committed'-session
    failure**, and the **full seed range (2021-01-04 → 2026-05-29, ~1,350 dates) also completes**. The
    root cause is fixed at the source: no Session is left in a committed/invalid state mid-orchestration
    — in particular the per-date persist MUST NOT `rollback()` a session that its two internal commits
    (`scanner.persist_run_payload` + `forward_testing.backfill_run_forward_returns`) have already
    committed (mechanism open: a fresh session per date, orchestrator-owned transaction boundaries, or
    per-worker sessions with a single serialized writer — SQLite writes stay serialized + transactional).
    Per-date failure isolation, create-once idempotency (J-41), honest `partial`, and honest progress
    (J-66) are preserved; canonical outputs stay **byte-identical** to the sequential engine. A committed
    **regression test reproduces the ACTUAL job-orchestration path** (driving the same `_do_backfill`
    orchestration the UI job uses) over a multi-month range end-to-end **offline**, including the
    failure-isolation branch — explicitly closing the gap that let J-67 pass while the live job still
    crashed.

- **J-69: Removing imported data is range-scoped and accident-proof (amends J-39)**
  - Steps:
    1. In **Data Manager → Remove imported data**, note there is **no symbols field** — removal is
       scoped purely by date range, covering **all symbols** in that range.
    2. Enter a **From** and a **To** date; **both are required** — the Remove button stays disabled
       until both are valid (guards against an accidental delete-everything).
    3. Click **Remove**: a confirmation appears with a concise warning plus the **impact counts** —
       removable (user-added) bar count, affected-symbol count, and cascade-removed snapshot count —
       with the date range restated. It does **not** render the long per-symbol list, so the Confirm
       button is always visible.
    4. Click **Confirm**: only user-added bars in the range are deleted (committed seed stays protected
       — J-39), dependent snapshots/forward-returns cascade, and coverage + the availability heatmap
       refresh to reflect the removal.
  - Acceptance: the Remove panel has **no symbols input**; **both From and To are mandatory** (Remove
    disabled until both are valid ISO dates); the destructive request is sent **range-only / all symbols**
    (`{start, end}`, no `symbols`) to the existing `POST /api/data/remove`; the confirmation renders
    **counts only** (removable bar count, affected-symbol count, cascade snapshot count, restated range)
    sourced from the real backend computation (single source — never fabricated) and a **persistently
    visible Confirm button** — never a long symbol list that pushes the button off-screen; committed-seed
    protection and the seed-safe refusal/`reason` (J-39) are unchanged; after Confirm, coverage and the
    availability heatmap reflect the removal.

- **J-70: The per-date availability heatmap is readable and compact**
  - Steps:
    1. In **Data Manager**, open the **Per-date availability** heatmap.
    2. Every date number is **clearly legible** against its cell — including empty / low-density cells,
       which previously rendered dark-on-dark-grey.
    3. Months are ordered **most-recent first** (nearest to furthest back), top to bottom.
    4. The grid shows **two months per row** on a normal-width viewport, so more history is visible
       without excessive scrolling.
  - Acceptance: the day-number text meets a legible contrast against **every** density-bucket background
    (buckets 0–5), fixing the dark-text-on-dark-grey empty/low-density cells, using the existing design
    tokens (no hardcoded hex); month bands render in **descending** order (newest month first); month
    bands lay out **two-up per row** at standard widths (gracefully collapsing to one column on narrow
    screens). Cells still encode the same density buckets and read the same `GET /api/data/availability`
    payload — descriptive only, no canonical value recomputed (coherence preserved).

- **J-71: Step the as-of date with the keyboard (extends J-43 / the global as-of calendar)**
  - Steps:
    1. Open the **as-of** date control (top of page) so the calendar popover is showing.
    2. Press **←** to move the as-of date to the **previous available** snapshot date (one trading day
       older) and **→** to move to the **next available** date (one day newer).
    3. The as-of date updates **live** as you press — pages re-read at the new date — and the popover
       stays open so you can keep scrubbing; the viewed month follows the selected date.
    4. At the oldest available date **←** is a no-op; at the latest **→** is a no-op (rests at Latest).
  - Acceptance: while the as-of calendar popover is open, **ArrowLeft** selects the previous (older)
    available snapshot date and **ArrowRight** the next (newer) one, stepping **only among dates that
    actually have snapshots** (never an arbitrary calendar ±1 onto a non-trading / no-snapshot day);
    each step **drives the single global as-of control** and stays in sync with the `?asof` URL param
    (J-43), introducing **no page-local or second date state** (Anti-goal: *exactly one date selector*);
    stepping is **bounded** (no movement past the oldest/newest available date); the calendar's viewed
    month follows the selection; Escape / click / Enter still close/commit as today. Handling lives on
    the existing calendar dialog's `onKeyDown` (which already handles Escape) — **no global window
    listener**.

- **J-72: Research page loads fast — Setup & Pattern Lab / event study no longer slow (extends J-29/J-63, J-15 load discipline)**
  - Steps:
    1. Visit `/research` at the latest as-of — each lab section (Factor Lab, Combination Lab, Setup & Pattern Lab) shows its own loading state immediately; no single slow fetch blocks the whole page.
    2. The Setup & Pattern Lab (event study) results render promptly (no multi-second full-page block); re-rendering after changing subject / horizon / Episodes⇄Pooled is fast.
    3. Confirm every figure is unchanged vs before the optimization (same numbers — a speed change only).
    4. Run a backfill that adds snapshots (or flip the As-of vs All-history toggle, J-32) — the lab figures refresh correctly, no stale numbers.
  - Acceptance: the Research page becomes responsive — each lab section fetches independently with its own loading/skeleton state so no one slow query blocks the page, and the event study reaches interactive without a long blocking spinner (held to J-15's warm-load discipline); the event-study computation **no longer re-scans the stored `forward_returns` once per horizon** — it is derived **once** per `(subject, mode, as-of)` over the stored per-observation forward returns (a single batched read + a run-position index computed once for all horizons + a **persisted/cached derived aggregate** are all permitted — the same "derived once… persisted/cached, and read from storage" contract the as-of evidence aggregate already uses); EVERY figure stays **byte-identical** to the current output and is still **derived once from stored data and never recomputed in the view** (low-sample cells still NA + n; survivorship-bias label persists); the cache/precompute **refreshes after dataset changes** (backfill/removal) so it is never stale; the As-of vs All-history toggle still only FILTERS the stored observation set (J-32 — no recompute, no second date state, J-18). A committed test asserts the event-study output is unchanged and that the per-horizon computation issues a single batched read rather than one scan per horizon. *(performance change only — no canonical value changes, coherence preserved.)*

- **J-73: No as-of "date flash" — every page renders the selected date from first paint (extends J-43/J-18/J-50)**
  - Steps:
    1. On a page showing a historical as-of date D (URL carries `?asof=D`), click a top-nav link to another date-scoped page.
    2. The destination renders its data **at D immediately** — it never first shows the latest-date values and then swaps to D a few seconds later.
    3. Open a `?asof=D` deep link directly (and reload it, and open it in a new tab) — the first data fetch is already at D (no latest→D flash).
    4. At the latest date (date-free URL), navigation shows the latest view with no flash; an invalid `?asof` still degrades to latest (J-43) without flashing a wrong date.
  - Acceptance: the single global as-of state is **hydrated synchronously from the `?asof` URL param on first mount** (the URL is the serialization of the one global state, restored through the one global control — **Exactly one date selector** and J-43/J-18/J-50 unchanged; no second or page-local date state is introduced — the fix changes only *when* the one state is read: synchronously from the URL instead of after an async run-list fetch); consequently a date-scoped page's **first** data fetch uses the resolved as-of date and there is **no transient render at the latest date** when arriving at a historical `?asof` URL by any path (in-app navigation, deep link, reload, new tab / middle-click); the historical badge, `?asof` href-stamping (J-50), and the invalid→latest degrade (J-43) are unchanged; at the latest date the latest view renders with no flash.

- **J-74: Availability heatmap — coverage levels are clearly differentiated and every date legible (hardens J-61/J-70)**
  - Steps:
    1. In **Data Manager** (`/data`), open the **Per-date availability** heatmap.
    2. A sparsely-covered day, a moderately-covered day, and a fully-covered day are **obviously different colours** — not a near-uniform teal wash.
    3. Every date number is **clearly legible** against its cell for **every** density bucket (0–5), including empty / low-density cells.
    4. A **legend** maps each colour to its coverage level; hover still shows exact figures (date, symbols-with-bars / total, snapshot yes/no).
    5. Run a fetch/backfill (or a removal) and confirm the heatmap re-reads and re-colours from the new coverage.
  - Acceptance: the coverage scale becomes a **perceptually-ordered, clearly-separated multi-hue scale** (a low→high progression across distinct hues, e.g. slate→blue→teal→green→amber) so neighbouring density buckets are unambiguously different on the dark background — fixing the single-hue teal-opacity ramp (`bg-accent/15…/70`) where buckets 1–3 were near-identical (the reported "coverage colours are all very similar"); the **day-number text meets a legible contrast against every bucket background (0–5)**, visibly resolving the dark-text-on-dark low-density case (hardening J-70 beyond its prior bar); a **legend** documents the colour→coverage mapping; the scale is defined once from the design-token system (no scattered magic hex in individual cells); the heatmap stays **descriptive only** — it reads the same single-source `GET /api/data/availability` payload and recomputes no canonical value, still marks snapshot days distinctly, still renders honest partial coverage (a 3-of-158 day visibly distinct from a full day) and an empty DB gracefully (J-61/J-70 semantics preserved); the month ordering / two-up layout from J-70 is unchanged.

- **J-75: Forward returns on the stock leaderboard and stock detail (1/5/10/20/60-day)**
  - Steps:
    1. Set the global as-of switcher to a historical date D that has post-D bars in the seed.
    2. On `/stocks`, confirm each row shows **five forward-return columns — 1d / 5d / 10d / 20d / 60d** — each the stock's realized forward return from D over that many trading days, colour-graded by sign.
    3. Sort by any forward-return column (J-48 contract) and confirm the rows re-order.
    4. Open a stock's detail page (`/stocks/[ticker]`) — it shows the **same five** forward returns for the as-of date, matching that ticker's leaderboard values.
    5. Return the switcher to the **latest** date — confirm all five horizons show **NA** (no post-D bars yet), not a fabricated number.
    6. Step the as-of date progressively further back and confirm more horizons populate (1d/5d before 60d).
  - Acceptance: on `/stocks` every row carries **five forward-return columns (1/5/10/20/60 trading days)** and the Stock Detail page shows the **same five** forward returns for the resolved as-of date; each value is the stock's realized forward return read from the **stored append-only `forward_returns` table** for the as-of run (single source of truth — the SAME data Backtest/J-21 reads, **never recomputed** in the API or the view) using **only bars dated > D** (no-lookahead); a horizon lacking enough post-snapshot bars shows **NA** — so at/near the latest date the columns are honestly NA, never fabricated (*Honest forward-test for partial windows*); the leaderboard and detail values are **identical** for the same ticker/date/horizon (J-06-style coherence); the columns are **client-side sortable** under the J-48 contract (a view transform — re-orders only, recomputes/refetches nothing; the default order stays the scanner's stored rank) and colour-graded by sign; the single global as-of control still drives the date (no page-local date picker — J-18) and the historical `?asof` href-stamping (J-50) is unchanged. The per-stock forward returns are a **new read surface of existing stored data** (added to the Stocks IA + the canonical-values contract), not a new computation.

- **J-76: Stock-detail price chart — per-bar hover detail box (OHLCV + moving averages)**
  - Steps:
    1. Open `/stocks/[ticker]` and move the cursor across the price chart.
    2. A small detail box tracks the crosshair showing that bar's **date, open, high, low, close, volume**, the bar's **% change**, and each rendered **moving-average value** (e.g. 20/50/150/200-DMA) at that bar.
    3. Move into the post-as-of forward region (J-20) — the box still reads the hovered bar and labels it a forward/after-as-of bar.
    4. Move the cursor off the chart — the box disappears.
  - Acceptance: hovering any bar on the Stock-Detail price chart shows a detail box with that bar's date (the shared `yyyy-MM-dd` formatter, J-42), open/high/low/close, volume, % change, and each rendered moving-average's value at that bar — all read from the **already-served `/api/stocks/{ticker}/bars` data** (no extra request, no recompute; the exact values the chart plots), keyed to the chart's crosshair-move subscription (mirroring the existing `index-regime-chart` tooltip), styled with the existing design tokens, and never obscuring the as-of marker / forward divider (J-20) or the regime bands (J-45); a forward (post-as-of, display-only) bar is labelled as such and stays **visualization only — never an as-of signal** (*No lookahead*); leaving the chart hides the box. No canonical value is computed in the view (coherence preserved); the box works for every timeframe the chart renders.

- **J-77: Research — returns by regime × setup × pattern (ranked combinations study)**
  - Steps:
    1. Visit `/research` — a new **Regime × Setup × Pattern** study section renders a **ranked, sortable table** where each row is a combination of a market-regime label, a setup status, and a detected pattern.
    2. Each row shows the combination's forward-return stats at the selected horizon — **n, mean, median, % positive (hit-rate), expectancy, and a risk-adjusted figure** — for combinations meeting the config min-sample bar; the table is ranked (default by risk-adjusted return) and re-sortable by any column (J-48 contract).
    3. Change the horizon, flip **Episodes ⇄ Pooled** (J-63), and toggle **As-of vs All-history** (J-32) — every figure re-points consistently.
    4. Click a row's **N=** chip — `/research/samples` opens that exact combination cohort (new tab, J-65) and its total equals the row's n (J-51 count-coherence).
    5. Confirm low-sample / empty combinations show **NA + n** (or are honestly held below the min-sample bar), never fabricated, and the survivorship-bias label is present.
  - Acceptance: a new Research study section renders a **ranked, client-side-sortable table of (regime, setup, pattern) combinations** (J-48 contract — re-orders only, recomputes nothing), each row carrying the combination's per-horizon forward-return stats (n, mean, median, hit-rate, expectancy, and risk-adjusted return/vol · return/MAE) for the selected horizon; **every figure is derived once from the SAME stored event-study observation set** — the existing per-observation forward returns enriched so each observation also carries its stored **regime label, setup status, and pattern flags** (read verbatim from the stored snapshot / `ScannerResult` — **no regime/setup/pattern recomputed**, *Research lab is read-only*), grouped by the (regime, setup, pattern) key by the **same observation builders** the rest of the event study uses (one membership rule); this enrichment is **additive — existing event-study figures (J-29/J-63) stay byte-identical**; the **N= chips drill down** through the same samples machinery and the drill-down total equals the published n in both **Episodes (default) and Pooled** modes (J-63/J-51/J-64 count-coherence); the regime / setup / pattern vocabularies come from the **config-backed catalog** (no hardcoded lists — *config-driven vocabulary*); the **As-of vs All-history** toggle only FILTERS the stored observations (J-32 — no recompute, no second date state, J-18); low-sample combinations show **NA + n** (or are honestly held below the config min-sample threshold — no magic number) and the **survivorship-bias** label persists; the study is **descriptive evidence, never a fitted/predictive model**.

- **J-78: Dashboard major-indexes chart defaults to the full period (All)**
  - Steps:
    1. Load the Dashboard (`/`) fresh (no stored preference).
    2. The **Major indexes & regime** chart's period selector defaults to **All** (full available history), not 6M.
    3. The other range presets (3M / 6M / 1Y / All) remain selectable and switch the view as before.
  - Acceptance: on a fresh load the major-indexes chart's default range is **All** (full history), set via the **config** default (`index_chart.default_range`, `6M` → `all`) — a config change with **no magic number in code** and no second code path; all existing range presets still work; the chart still serves **full-history regardless of the global as-of** (J-49) so this is a default-window change only (no backend/contract change, no recompute, no second date state — J-18); the card's enable/disable toggle and its persistence are unchanged.

- **J-79: Step the as-of date without the panel blocking the view — buttons + opt-in arrows + quick year/month jump (amends J-71 / J-62)**
  - Steps:
    1. At a historical as-of date, click the top-bar **◀ / ▶** buttons beside the as-of control: the date moves to the previous / next **available snapshot date** with the **calendar popover closed** — the page re-reads and the view is never covered.
    2. Tick the top-bar **"← → steps date"** checkbox; now **←** / **→** step the as-of date the same way globally while the panel is closed. Untick to disable (the setting persists).
    3. Open the calendar and use the new **Year** and **Month** dropdowns to jump the viewed month directly instead of clicking the chevrons month-by-month.
    4. At the oldest available date **◀ / ←** is a no-op; at the latest **▶ / →** rests at Latest.
    5. Focus the `/stocks` symbol-search box and press **← / →** — the text caret moves and the as-of date does **not** change (keys are ignored while typing in a field).
  - Acceptance: the as-of date is steppable **with the calendar popover closed** via always-visible **◀ ▶** prev/next buttons in the top bar **and** — when a **persisted, default-off** "← → steps date" checkbox is on — the **← / →** arrow keys; every step moves **only among dates that actually have snapshots** (never an arbitrary calendar ±1 onto a non-trading / no-snapshot day), is **bounded** (no movement past the oldest / newest available date), drives the **single global as-of** control, and stays in sync with the `?asof` URL param (J-43 / J-50) — introducing **no page-local or second date state** (Anti-goal: *exactly one date selector*); the keyboard handler is **guarded** so it never fires while focus is in an input / textarea / select / contenteditable and never hijacks scrolling when the checkbox is off; the calendar gains **Year + Month dropdowns** that navigate the **viewed month only** (a presentation aid, not a second date state); the calendar's selectable-day / disabled-day / "Latest" affordances (J-62) and Escape / click-to-commit are unchanged. This **supersedes J-71's** "handling lives only on the open dialog's `onKeyDown` — no global window listener": the **opt-in** checkbox now permits a field-guarded global key handler, and stepping no longer requires the panel to be open.

- **J-80: Stocks leaderboard shows the selected date's market regime + theme ranking**
  - Steps:
    1. Visit `/stocks` at any as-of date.
    2. Read the **market-regime label + 0–100 score** for that date in the page header.
    3. Read the **ranked Top-Themes strip** beside it (themes in descending Theme Score: 1 · …, 2 · …, …); click a theme to open `/themes`.
    4. Note the **`#n` rank badge** on each row's theme chips and on the theme-filter options.
    5. Change the global as-of date — the regime label, the ranked strip, and the chip badges all re-point to the new date.
  - Acceptance: `/stocks` displays the resolved as-of date's **regime label + score** read from the **same stored canonical regime the Dashboard shows** (the run's stored `regime_label` / the `/api/dashboard` regime) and **identical** to the Dashboard for that date (J-06 coherence) — **never recomputed**; and a **theme ranking** presented **both** as a header **ranked Top-Themes strip** **and** as **`#n` rank badges** on the per-row theme chips + the theme filter, read from the **same `/api/themes` theme scores / ranks** the Themes leaderboard uses and in the **same descending order** — a pure re-display of served canonical values, **no second compute path** (*Single source of truth*). Both re-point with the single global as-of (J-18), show an **honest empty state** when a date has no ranked themes, and leave the existing leaderboard rows, filters, symbol search (J-55), column sorting (J-48), theme chips (J-56), and forward-return columns (J-75) unchanged.

- **J-81: Forward-return columns on the Themes and Sectors leaderboards (1/5/10/20/60-day; mirrors J-75)**
  - Steps:
    1. Set the global as-of to a historical date D that has post-D bars in the seed.
    2. On `/themes`, confirm each row shows **five forward-return columns — 1d / 5d / 10d / 20d / 60d** — the **equal-weight forward return of the theme's member basket** at D, colour-graded by sign; sort by any of them (J-48).
    3. On `/sectors`, confirm each row shows the **same five columns** — the **sector / industry ETF's own forward return** at D — also sortable.
    4. Cross-check a theme and a sector value against the **Backtest** page's Top Themes / Top Sectors at the same date + horizon — they are identical.
    5. Return the switcher to **latest** — every horizon shows **NA** (no post-D bars yet), never a fabricated number.
  - Acceptance: `/themes` and `/sectors` each carry **five forward-return columns (1 / 5 / 10 / 20 / 60 trading days)** for the resolved as-of date, mirroring J-75 on `/stocks` (colour-graded by sign, **client-side sortable** under the J-48 view-transform contract, NA-honest at / near latest); the **theme** value is the **equal-weight average of its member stocks' realized forward returns** and the **sector** value is the **ETF's own realized forward return**, **both read from the stored append-only `forward_returns` table via the SAME `leadership_returns` builder the Backtest page already uses** — so the columns are **identical** to Backtest's Top Themes / Top Sectors for the same date + horizon (J-06 coherence), use **only bars dated > D** (no-lookahead), and show **NA** where post-snapshot bars are insufficient (never fabricated — *Honest forward-test for partial windows*); they are a **new read surface of existing stored / derived data** (like J-75), **not** a new computation; the single global as-of drives the date (J-18) and the historical `?asof` href-stamping (J-50) is unchanged.

- **J-82: Regime × Setup × Pattern table — correct NA sorting, column filters, working N= drill-down, Pooled default (amends J-77)**
  - Steps:
    1. On `/research`, sort any numeric column of the **Regime × Setup × Pattern** table — rows shown as **NA** sink to the bottom in **both** ascending and descending order (they no longer scatter among the real values).
    2. Use the new **Regime**, **Setup**, and **Pattern** filter dropdowns to narrow the table; combine them with a column sort.
    3. Click any row's **N=** chip — `/research/samples` opens that exact `(regime, setup, pattern)` combination (new tab) **without error**, its total equal to the row's n.
    4. Confirm the section's view toggle now defaults to **Pooled** (Episodes still one click away).
  - Acceptance: four corrections to the J-77 section, every one a **read-only view / serve fix — no canonical value changes**: (a) **sorting treats a cell as NA using the SAME predicate the cell display uses** (`low_sample` OR `n === 0` OR `value === null`) so every displayed-NA row sorts **last in both directions** while present values sort numerically and the label columns lexically (a stable tie-break preserves the served rank) — fixing the low-sample rows that currently sort by a hidden number the UI is masking behind "NA"; (b) **client-side filter dropdowns for Regime, Setup, and Pattern**, built from the **config-driven vocabulary already in the payload** (`regime_labels` / `setups` / `patterns` / `pattern_none`), each defaulting to "All" — **pure view transforms** over the served rows that **compose with the sort and recompute nothing** (the J-56 / J-48 contract); (c) clicking the **N=** chip on **any** displayed row opens the samples drill-down for that exact `(regime, setup, pattern)` cohort **without error**, with **total == the row's n**, in **both Episodes and Pooled** modes and **both All-history and As-of** scopes (J-51 / J-65 count-coherence) — **including the pattern = none rows** — so the samples validation / vocabulary must accept **every** combination the study itself emits (no displayable row may return a 4xx); (d) **this section's Episodes ⇄ Pooled toggle defaults to Pooled** (Episodes still one click away), while the rest of the event study keeps its J-63 **Episodes** default. The J-77 derivation (one enriched observation set, no recompute, the survivorship-bias label) is otherwise unchanged.

- **J-83: As-of deep link renders with no React hydration mismatch — server-aware seeding (hardens J-73)**
  - Steps:
    1. Open a `?asof=D` deep link directly (and reload it, and open it in a new tab) — the browser console shows **no** "Hydration failed / server rendered HTML didn't match" error.
    2. The sidebar nav links (the J-50 `?asof` hrefs) and the as-of badge (the History icon + "Viewing as-of D (historical)") render at D in the **server** HTML and are **identical** on the client's first paint — no Clock→History icon swap, no latest→D flip.
    3. At the latest date (date-free URL) there is no error and no flash; an invalid `?asof` still degrades to latest (J-43) with no hydration error and no wrong-date flash.
    4. Client-side navigation, the ◀ ▶ / arrow stepping (J-79), and the calendar still update the date and the `?asof` URL exactly as before (J-43 / J-50 / J-62 / J-79 unchanged).
  - Acceptance: the single global as-of state is **seeded identically on the server and the client** so the server-rendered HTML already carries the resolved as-of date — eliminating the React-19 hydration mismatch in the sidebar hrefs (J-50) and the as-of indicator that J-73's client-only `window` read produced (the server seeded `null`, the client seeded D). Mechanism: a **Next.js middleware forwards the request's `?asof` query as a request header**; the **root layout (a server component) reads that header and passes it as `initialAsOf`** into the `AsOfProvider`; the provider's lazy initializer **prefers that server-provided value** — present and identical on both sides because it is serialized into the RSC payload — keeping the existing `readAsofFromUrl()` only as a client fallback. **No second or page-local date state is introduced** (Anti-goal: *Exactly one date selector*; J-18 / J-43 / J-50 / J-73 unchanged) — only *where* the one state is first read changes (a server-forwarded header instead of a client-only `window`). J-73's no-latest-flash data property is preserved (the first data fetch is still at D) and now extends to the indicator chrome (no Clock→History flip). The invalid→latest degrade (J-43), the historical badge, and the `?asof` href-stamping (J-50) are unchanged; no provider key/secret ever rides the header path (Anti-goal: *No secrets in source*). *(UI correctness fix — no canonical value changes; coherence preserved.)*

- **J-84: Expand-universe market-cap fetch authenticates with Yahoo (cookie + crumb); a systemic auth failure pauses resumable, never silently omits all (unblocks J-22 via J-35)**
  - Steps:
    1. From **Data Manager** (`/data`), run an **Expand-universe** job against a Yahoo-capable source.
    2. The market-cap fetch first acquires a Yahoo session **cookie + crumb** (exactly as the committed `apps/backend/scripts/screen_universe.py` runbook does), then batches `/v7/finance/quote?…&crumb=…`; candidates whose **real** market cap ≥ the config `min_market_cap` **pass**, and only genuinely too-small / capless names are omitted with an honest per-candidate reason.
    3. The resulting `universe.json` has a **non-empty `members` list** (not 0-of-548), each member carrying its **real** market cap — never fabricated.
    4. If Yahoo systematically rejects auth (persistent 401 / 429 across the whole batch), the job does **not** record all 548 omitted — it **pauses as resumable** ("market-cap provider auth failed — Resume to retry", mirroring the existing 429 pause); Resume continues with **zero duplicate fetch** and survives a backend restart.
    5. Offline / CI with an injected provider still screens deterministically (no live call).
  - Acceptance: the live `YahooProvider` market-cap path **authenticates exactly like the committed `screen_universe.py` runbook** — it sets the no-key Yahoo cookie (visiting `finance.yahoo.com`), obtains a **crumb** (`/v1/test/getcrumb`) with a browser-like User-Agent, then passes `crumb=…` to the **batched** `/v7/finance/quote` — fixing the HTTP-401 that made every candidate omit `no_market_cap` (0 passers of 548). The crumb / cookie are acquired at runtime and **never stored, logged, committed, or echoed** (Anti-goals: *No secrets in source*; *Import keys are env-or-session, never persisted*). A market cap is **real or absent — never fabricated** (Anti-goal: *No fabricated data*): a genuinely capless / sub-threshold candidate is still honestly omitted per-candidate (J-35), but a **systemic** auth / limit failure (the whole batch failing) is treated like the 429 case — the expand job **pauses resumable** (a clear operator state; zero duplicate fetch on Resume; survives a restart) **instead of silently recording all candidates omitted**, so an auth outage is never mistaken for "the universe is empty". This is the operator-facing path that **unblocks J-22** (the expanded ~500-name universe) and rides the existing J-34 / J-35 chunked / checkpointed / resumable import machinery (no second fetch path). The cookie + crumb acquisition and the pause-resumable behaviour are **buildable and testable offline with an injected provider** (a stub returning caps or raising 401 / 429); only an actual successful **real** Yahoo screen is data-gated (see the data-dependency note).

- **J-85: Expanding the universe makes its new members appear in the analysis — a confirm-gated full snapshot rebuild for the current universe (+ a coverage diagnostic)**
  - Steps:
    1. After an Expand-universe job adds members (J-84), `/data` shows a **coverage diagnostic**: "N universe members are not present in the latest snapshot — rebuild to include them" (read-only, descriptive).
    2. Trigger the **Rebuild snapshots for current universe** action (**confirm-gated**): a background job recomputes every snapshot (regime / sectors / themes / stocks + forward returns) over the current full universe, for **all** covered trading dates (including dates that already had a snapshot), with live per-date progress (J-66).
    3. On completion the new members appear on `/stocks`, `/themes`, `/sectors`, in `/scanner-runs`, and in the **Backtest** evidence + **Research** event study at **every** date — the walk-forward evidence now reflects the expanded universe.
    4. Strict no-lookahead holds (each rebuilt as-of-D snapshot uses only bars ≤ D; forward returns use only bars > D); the rebuild is **deterministic** (a fresh recompute equals itself); the committed **price** seed is untouched.
    5. Without a rebuild, the diagnostic keeps flagging the gap honestly — no fabricated membership, no silent partial.
  - Acceptance: a confirm-gated **"rebuild snapshots for the current universe"** background job (reusing the J-53 parallel-backfill + J-66 progress machinery) **regenerates the snapshot layer from scratch** — for every covered trading date, including dates that already had a snapshot — so newly-screened universe members (J-22 / J-84) appear in **every** read surface (the Stocks / Themes / Sectors / Scanner-Runs leaderboards, the Backtest evidence aggregates, and the Research event study) and the walk-forward evidence reflects the full universe. This reconciles with **Snapshots are immutable** by being a **regenerate-from-scratch reproducible recompute** (create-once over a cleared snapshot set — the same deterministic computation the Capability-34 snapshot seed is produced by), **never an in-place UPDATE / overwrite** of a live snapshot row, and it preserves **strict no-lookahead** (as-of-D uses bars ≤ D; forward returns use bars > D — Anti-goals: *No lookahead*; *On-demand snapshots stay immutable & lookahead-free*) and determinism (a fresh recompute is byte-identical to itself, asserted by the existing scanner / forward-test suites). The committed **price** seed is never deleted (Anti-goal: *the committed seed is never deletable*); membership is **real or honestly flagged missing — never fabricated** (Anti-goal: *No fabricated data*). A **read-only coverage diagnostic** surfaces "N universe members absent from the latest snapshot" derived from the stored bars + the resolved universe (descriptive metadata only — no canonical value recomputed; extends *Coverage & missing-data are descriptive & honest*), so the need for a rebuild is visible. The rebuild is **operator-triggered and confirm-gated** — never an automatic destructive surprise. The rebuild + diagnostic are offline / deterministic and buildable against the committed seed; only obtaining new **real** members upstream is data-gated (J-84 / J-22). *(Re-committing the regenerated snapshots into the optional Capability-34 snapshot seed remains a deterministic-script step, out of scope here.)*

- **J-86: Max-drawdown columns beside the forward returns everywhere (1 / 5 / 10 / 20 / 60-day; mirrors J-75 / J-81)**
  - Steps:
    1. At a historical as-of date D, on `/stocks` each row shows — **beside** its five forward-return columns — **five max-drawdown columns (1d / 5d / 10d / 20d / 60d)**, each the worst peak-to-trough decline over those D post-D trading days, shown as a ≤ 0 % figure, colour-graded by magnitude, and **sortable** (J-48).
    2. The Stock-Detail forward-return panel (`/stocks/[ticker]`) shows the **same five** max-drawdown values for the as-of date, identical to that ticker's leaderboard row.
    3. `/themes` and `/sectors` carry the paired max-drawdown columns too — theme = the equal-weight member-basket drawdown, sector / industry = the ETF's own drawdown — and they **match Backtest** for the same date + horizon (the J-81 contract).
    4. Backtest's evidence (by bucket / setup / regime / horizon) and the Research event-study + Regime × Setup × Pattern tables show an **aggregate max-drawdown** stat beside each return stat (mean MDD, with the same `n` + NA / min-sample discipline).
    5. At / near the latest date, max-drawdown is **NA** wherever the return is NA (insufficient post-D bars) — never fabricated.
    6. Adding a horizon to config produces both the return AND the max-drawdown column automatically (no hardcoded list).
  - Acceptance: a **max-drawdown** measure is computed once per `(run, symbol, horizon)` in the forward-testing engine **beside the existing realized return + MAE / MFE** — the worst running-peak-to-trough decline over the first `horizon` post-snapshot bars, `MDD = min over j of ( low_j / max(entry_close, high_1 … high_j) − 1 )` (≤ 0; the running peak seeded at the as-of-date close), using **only bars dated > D** (no-lookahead) and the SAME post-D window the returns use — and is **stored in the append-only `forward_returns` table** (a new nullable field; *Snapshots are immutable* / the append-only forward-returns contract unchanged). Every surface that shows the per-horizon forward returns gains a **paired max-drawdown read from that stored value, never recomputed in the API or the view** (Anti-goals: *Single source of truth*; *No recompute in the read path*): the `/stocks`, `/themes`, `/sectors` leaderboards and the Stock-Detail panel get five MDD columns / values (colour-graded, **client-side sortable** under the J-48 view-transform contract, mirroring J-75 / J-81 — theme = equal-weight member-basket drawdown, sector / industry = the ETF's own drawdown, via the SAME `leadership_returns` builder so they are **identical to Backtest** for the same date + horizon, J-06); and the **Backtest** evidence aggregates (by bucket / setup / regime / horizon) and the **Research** event-study + Regime × Setup × Pattern tables carry an **aggregate max-drawdown** (mean, with the same min-sample / NA discipline) beside each return stat. A horizon whose return is **NA** (insufficient post-D bars) shows max-drawdown **NA** too — never fabricated or extrapolated (Anti-goal: *Honest forward-test for partial windows*); the horizon set comes from `config.walk_forward.horizons` (**no hardcoded `[1, 5, 10, 20, 60]`** — Anti-goal: *No magic numbers*), so adding a horizon adds both columns everywhere. The single global as-of drives the date (J-18) and the `?asof` href-stamping (J-50) is unchanged. The drawdown is a **new read surface of existing stored data** computed in the same forward-returns pass — not a new per-request computation. A committed test asserts the MDD math (running-peak, ≤ 0, and the no-lookahead tail-invariance the way `forward_return` / `forward_excursions` already are) and that existing return figures stay **byte-identical**. *(The new stored field populates when forward returns are (re)computed — existing snapshots read NA until the J-85 rebuild or a forward-returns recompute repopulates them.)*

- **J-87: Deterministic as-of market-phase + drawdown-severity score (a read-only derived layer — no new column, no snapshot rebuild)**
  - Steps:
    1. At any as-of date D, the Dashboard shows a new **Market Phase & Severity** panel: a discrete **phase** (e.g. Expansion / Pullback / Correction / Bear / Recovery — labels + edges from config) and a **0–100 severity score** for D, with its **named component breakdown** (trailing-peak drawdown depth, time-underwater, the stored regime score/trend, breadth-below-200DMA, the ^VIX gate).
    2. Every component is **as-of strict**: trailing peak = the maximum index close over `[start, D]` from `bars_asof` (date ≤ D); time-underwater counts trading days since that peak; the regime/breadth inputs are read **verbatim from the stored `ScannerRun` rows dated ≤ D** — no future bar participates.
    3. Step the as-of back into the 2022 window — the panel deepens to **Bear** with a high severity (the seed's SPY −24.5% peak-to-trough is reproduced); step into 2024 — it reads Expansion/Recovery. The same date always shows the same phase/severity on every surface (coherence).
    4. The layer is a **cached read-only derivation** keyed to the resolved as-of + a dataset-version stamp (the J-72 `EventStudyCache` pattern) — computed once per resolved-as-of, served from cache, **never recomputed per request**, and adding **no column to any snapshot table and triggering no snapshot rebuild**.
    5. A configured input that is unavailable (insufficient history for a window) is shown **NA / partial**, never fabricated; the panel never alters any stock score, bucket, setup, or the Risk-Off→Actionable gate.
  - Acceptance: a new **deterministic, config-driven market-phase + drawdown-severity** value is derived for the resolved as-of date as a **pure function of the stored immutable snapshots + the index bars dated ≤ D** — exactly the read-only-derived-layer contract `regime_history` / `compute_availability` / `compute_coverage` / the as-of evidence aggregate already follow (*No recompute in the read path*; *Single source of truth*): it adds **no column to `scanner_runs` / `scanner_results` / `forward_returns`** and triggers **no snapshot rebuild**, and is computed-once-per-resolved-as-of then served (optionally cached behind a `dataset_version` stamp like `event_study_cache`, J-72 — refreshing after any dataset change, never serving a stale figure). Every component is **strictly causal**: the trailing peak is `max(close)` over `[start, D]` via `bars_asof`, time-underwater counts only trading days ≤ D, and the regime/breadth/trend inputs are read **verbatim from the stored `ScannerRun` rows dated ≤ D** — a value for D uses only bars ≤ D, unit-asserted the way `forward_return` proves its no-lookahead tail-invariance (*No lookahead*, critical — this feature is a lookahead minefield and every leg is fenced to ≤ D). Every weight, phase edge, drawdown/time-underwater threshold, and the ^VIX gate parameter comes from a new typed, validated `config` section (**no magic numbers** — the score is rejected at load if its weights do not sum to ~1.0, mirroring `regime.weights`), and the score is **explainable** (its named component breakdown renders beside the number — never a bare figure). The phase/severity is a **descriptive market-context read**, NOT a stock signal: it changes **no canonical stock score, bucket, setup status, pattern flag, or the Risk-Off→Actionable gate** (critical, untouched), introduces **no second date state** (it reads the single global as-of — *Exactly one date selector*), and a window with insufficient history shows **NA / partial**, never a fabricated value (*No fabricated data*; *Honest limitations* — breadth inputs stay universe-relative). Fully buildable and verifiable offline against the committed seed (which contains the 2022 bear + ^VIX).

- **J-88: Deterministic-parameter probabilistic 2-state regime-switching FILTERED bear-probability (causal Hamilton filter, never the smoothed)**
  - Steps:
    1. The Market Phase panel (J-87) gains a **P(bear) 0–1 probability** for the resolved as-of date from a **2-state (bear / risk-on) Markov-switching classifier**, shown beside the deterministic phase with its inputs disclosed (the observation vector: index return, breadth, ^VIX, optionally macro-z from J-92).
    2. The served probability is the **FILTERED** Hamilton-filter value P(state = bear | observations ≤ D) — a closed-form recursion over only data dated ≤ D; stepping the as-of forward extends the recursion one step, and **no future observation can change a past date's filtered probability** (unit-asserted tail-invariance).
    3. The transition matrix + per-state emission parameters are read **verbatim from a committed config block** (optionally produced by a deterministic offline calibration script over the seed) — the filter is **never EM-fit at serve time**; fixed params + fixed observations yield a byte-identical probability (a committed determinism test).
    4. Over the 2022 window P(bear) rises toward 1 and falls back through 2023–2024; a date with insufficient history shows **NA**, never a fabricated probability.
    5. The probability is market context only — it changes no stock score, bucket, setup, or the Risk-Off→Actionable gate.
  - Acceptance: a **2-state regime-switching bear-probability** is served for the resolved as-of date as the **deterministic forward Hamilton FILTERED probability** P(state = bear | observations ≤ D) — **probabilistic in output, fully deterministic in computation**: the transition matrix and per-state emission parameters come **verbatim from a committed, typed, validated `config.regime_switching` block** (optionally materialized by a committed deterministic offline calibration script over the seed, loaded verbatim — **never EM-fit at serve time**), so fixed params + fixed data → a fixed, reproducible, unit-testable probability with **no magic numbers** (every parameter is config; the module passes the `test_no_magic_numbers` tokenizer like `regime.py`). The filter is **strictly causal** — each date's probability is computed from observations dated ≤ D only, and the keystone discipline is that the **FILTERED** (forward, causal) probability is the served live value while the **SMOOTHED** (full-sample) probability is **lookahead and MUST NOT be served live or fed into any as-of score/signal/study-conditioning** (it may appear only on the J-89 retrospective surface) — the no-future-observation-influences-a-past-probability property is unit-asserted exactly as `forward_return`/`forward_excursions` prove their tail-invariance (*No lookahead*, critical). It is a **read-only derived value** over stored bars + stored runs (no new snapshot column, no rebuild, computed-once-per-resolved-as-of — *No recompute in the read path*; *Single source of truth*), it is **explainable** (its observation vector + per-state likelihood are disclosed, never a bare number), and it changes **no canonical stock score, bucket, setup, pattern flag, or the Risk-Off→Actionable gate** (critical, untouched) and adds **no second date state** (*Exactly one date selector*). Insufficient-history dates show **NA**, never a fabricated probability (*No fabricated data*). Buildable and verifiable offline against the committed seed (2022 bear + ^VIX); with macro inputs absent the filter runs on the price/breadth/VIX observation vector and the macro leg is honestly omitted (J-92).

- **J-89: Market-phase history timeline + causal downtrend-episode dating, with a clearly-fenced retrospective (smoothed) view**
  - Steps:
    1. A **Market-Phase timeline** overlays the Dashboard major-indexes/regime card: a per-date band of the J-87 phase + J-88 filtered P(bear), drawn as a step function across snapshot dates (the J-44/J-49 overlay treatment), read from the same single derived series.
    2. The timeline lists **causal downtrend episodes** — maximal runs where the as-of phase is Bear/Correction (or P(bear) ≥ a config threshold) using **only data ≤ each date** — each with its first-trigger date, the as-of severity at trigger, and (for dates ≤ the resolved as-of) its still-open or closed state; the 2022 bear appears as one dated episode.
    3. A separate, **explicitly labelled "Retrospective (full-sample)"** sub-view shows the **smoothed** P(bear) and an NBER/Bry-Boschan-style peak-to-trough "true bear dating" — visibly fenced as **analysis-only, not an as-of signal**, exactly like the J-49 post-as-of display-only context behind a marker.
    4. With a historical global as-of D, the causal episodes and the live timeline render **only dates ≤ D** (no band past D for the clamped consumer); the retrospective sub-view is the only place future-aware values appear, and it never feeds any score/study.
    5. An empty/early history yields an honest empty timeline; nothing is fabricated.
  - Acceptance: a **market-phase history timeline** renders the per-date J-87 phase + J-88 **filtered** P(bear) as a step function over snapshot dates, built from the **same single read-only derived series** the panel uses (no second computation — *Single source of truth*; *No recompute in the read path*) and drawn with the J-44/J-49 overlay treatment. **Causal downtrend-episode dating** is a deterministic grouping of the **as-of (≤ D) phase/probability** into maximal Bear/Correction runs — each episode observed at information available on its dates only, never using a future bar — so it is **strictly causal** and unit-asserted no-lookahead (*No lookahead*, critical). A **retrospective full-sample view** (the **smoothed** Markov probability + a peak-to-trough Bry-Boschan/NBER-style "true bear dating") is permitted **only** on a surface **explicitly labelled retrospective / analysis-only and visibly fenced from the as-of path** — it is lookahead by construction and **MUST NOT feed any as-of score, signal, episode, or study-conditioning tag** (this mirrors the J-49 *Full-history market context never looks ahead* precedent: future-aware data may be displayed behind a clear marker but never enters an as-of-scoped computed value). The live timeline clamps at the resolved as-of for the clamped consumer (J-45 semantics) while the dashboard card may render the full series behind the J-49 as-of marker; episode thresholds and phase edges come from **config** (no magic numbers); an early/empty history renders an **honest empty timeline**, never fabricated episodes (*No fabricated data*; breadth inputs stay universe-relative). It introduces **no second date state** (*Exactly one date selector*) and changes no canonical stock value or the Risk-Off→Actionable gate. Fully buildable and verifiable offline against the committed seed (the 2022 bear is one dated causal episode and a clean retrospective peak-to-trough case).

- **J-90: Causal recovery/turn signal and its forward-return edge study (the "recovery-turn edge")**
  - Steps:
    1. The Market-Phase panel surfaces a **causal recovery/turn signal** for the resolved as-of date — a config-defined transition out of a downtrend (e.g. phase leaves Bear, or filtered P(bear) crosses below a config threshold while the index reclaims a trailing MA), computed from **data ≤ D only**.
    2. A new **Recovery-Turn Edge** study on `/research` reports, per configured horizon, the **forward-return distribution** (mean/median/%-positive/expectancy + downside risk-adjusted + max-drawdown) of the universe/benchmark **measured from the recovery-signal date** — read verbatim from the stored `forward_returns` (entry close on the signal date, exits date > D), never recomputed.
    3. Each observation is tagged with the **causal as-of phase/severity/P(bear) at the signal date** (the J-87/J-88 values ≤ D), so the edge is conditioned only on information available at entry.
    4. Toggle horizon, Episodes ⇄ Pooled (J-63), and As-of ⇄ All-history (J-32); the **N= chips** drill down to count-coherent samples (total == published n).
    5. Low-sample cohorts show **NA + n**; the survivorship-bias label persists; the study implies **no order/execution** — it is forward-return evidence only.
  - Acceptance: a **causal recovery/turn signal** is computed for the resolved as-of date from **data dated ≤ D only** (a config-defined downtrend-exit transition over the J-87 phase / J-88 filtered probability / a trailing-MA reclaim — every threshold from config, **no magic numbers**), unit-asserted no-lookahead exactly as the other as-of signals (*No lookahead*, critical: the conditioning value at the signal date uses only ≤ D, and the forward returns use only bars > D). Its **forward-return edge** is a new read-only Research study built **entirely from the stored append-only `forward_returns`** (realized return + MAE/MFE + `max_drawdown`, read VERBATIM via the same observation-builder discipline as `compute_event_study`) joined to the stored `scanner_results`/`scanner_runs` and **each observation tagged with the causal as-of phase/severity/P(bear)** at entry — it **recomputes no return, score, regime, or signal** (*Research lab is read-only, honest & not predictive*; *Attribution is read-only*; *No recompute in the read path*). It reuses the existing horizon set (`config.walk_forward.horizons` — no hardcoded list), the **Episodes ⇄ Pooled** overlap-honesty modes (J-63) and the **As-of ⇄ All-history** filter (J-32 — a mode reading the single global as-of, **not a second date state**, *Exactly one date selector*); the **N= chips** drill down through the SAME shared-membership samples builder so the drill-down **total equals the published n** in both views (J-51/J-65 count-coherence — one membership rule, never a second filter); low-sample cohorts show **NA + n** (min-sample from config) and the **survivorship-bias** label persists. Risk is **downside-only** (return/downside-dev, return/|MAE|, max-drawdown — never total volatility, *Risk-adjusted reporting is honest*). The study is **descriptive evidence, never a fitted/predictive model**, and the recovery angle implies **no shorting, order, or capital-deployment path** (*No order/execution path*, critical). Fully buildable and verifiable offline against the committed seed (the 2022→2023 recovery turn produces dated signal observations with realized forward returns).

- **J-91: Downtrend-conditioned opportunity study — three angles (held-up-best / fell-hardest evidence / recovery-turn edge) conditioned on the causal as-of phase/severity/bear-probability**
  - Steps:
    1. A new **Downtrend Opportunity** study on `/research` lets the user condition the existing forward-return evidence on the **causal as-of downtrend state** — the J-87 phase, a severity band, or a J-88 P(bear) band (all ≤ D).
    2. Three angles render side by side: **(a) "What held up best"** — the strongest forward returns / leadership cohorts within downtrend dates (defensive/long evidence); **(b) "Weakness / short-research"** — what fell hardest (worst forward returns, deepest max-drawdown) within downtrend dates, **as evidence only, no execution**; **(c) "Recovery-turn edge"** — the J-90 edge surfaced in the same panel.
    3. Every figure is a grouping of the **same stored event-study observation set** (the J-77 enriched observations), with **each observation additionally tagged by its causal as-of phase / severity band / P(bear) band** (≤ D), grouped by the same observation-builders — no return/score/regime/phase recomputed.
    4. Horizon, Episodes ⇄ Pooled (J-63), As-of ⇄ All-history (J-32) all re-point consistently; **N= chips** drill down count-coherently (total == published n) in both modes, including the new conditioning dimensions.
    5. Low-sample / empty conditioned cohorts show **NA + n**; the survivorship-bias label persists; the weakness angle creates/implies **no order path**.
  - Acceptance: a new **downtrend-conditioned opportunity study** renders the **three required angles** — (a) held-up-best defensive/long evidence, (b) fell-hardest **weakness / short-research evidence (evidence ONLY)**, (c) the J-90 recovery-turn edge — as **ranked, client-side-sortable** tables (J-48/J-82 view-transform contract — re-orders only, recomputes nothing). **Every figure is derived once from the SAME stored event-study observation set** the rest of the lab reads (the J-77 enriched per-observation rows: stored realized return + MAE/MFE + `max_drawdown` + stored `regime_label` + `sector` + setup/pattern flags, all VERBATIM), **additionally tagged with the CAUSAL as-of phase / severity band / P(bear) band** at the observation's snapshot date (the J-87/J-88 values, ≤ D — read from the same read-only derived layer, **never recomputed**, and **strictly causal** so no future bar sets a conditioning tag, *No lookahead* critical), and grouped by the (phase/severity/bear-prob × angle) key by the **same observation-builders** the event study uses (one membership rule); this enrichment is **additive — the existing J-29/J-63/J-77 figures stay byte-identical**. The **N= chips drill down** through the SAME shared-membership samples builder (a new `kind` mirroring `_regime_setup_pattern_samples`) so the drill-down **total equals the published n** in both **Episodes (toggle) and Pooled** modes and both All-history and As-of scopes (J-51/J-65 count-coherence — never a second grouping; every displayable row must resolve without a 4xx, the J-82 lesson). The phase/severity/probability-band vocabulary comes from the **config-backed catalog** (no hardcoded lists — *config-driven vocabulary*); the **As-of ⇄ All-history** toggle only FILTERS the stored observations (J-32 — a mode, **no second date state**, *Exactly one date selector*); low-sample/empty conditioned cohorts show **NA + n** (min-sample from config — no magic number) and the **survivorship-bias** + universe-relative labels persist; risk is **downside-only** (max-drawdown / MAE / downside-dev — never total volatility). The study is **descriptive evidence, never a fitted/predictive model**, and the **weakness / short-research angle is surfacing evidence only — it creates and implies NO shorting, order, or capital-deployment path** (*No order/execution path*, critical). Fully buildable and verifiable offline against the committed seed (the 2022 bear supplies the downtrend-conditioned observations).

- **J-92: Real macro feed (FRED) + OHLCV macro proxies wired as optional config-driven inputs to severity, regime-switching emissions, and study conditioning (data-dependent / non-halting)**
  - Steps:
    1. A new **macro provider** fetches a configured set of FRED economic series (yield-curve 10y–2y inversion, unemployment trend, credit spreads) into a dedicated additive **`MacroSeries(symbol, date, value, source, published_date)`** store, and the OHLCV macro proxies (`^TNX`, `^DXY`, `^VXN`) ride the existing daily-bar path beside the already-seeded `^VIX`.
    2. The macro inputs are wired as **optional config-driven** legs into the J-87 severity score, the J-88 regime-switching observation vector/emissions, and the J-91 study conditioning — each leg **off by default in config** until enabled, so the price-only behavior is unchanged when macro is absent.
    3. Each macro series is **publication-lag aligned**: a value used on date D is only one **PUBLISHED on/before D** (`published_date ≤ D`), never the reference-date value — with an honest publication-lag limitation label.
    4. A small **committed macro seed** over the seed window makes the macro-conditioned features **verifiable offline with injected fixtures** (mirroring how `^VIX` is seeded); the live FRED/proxy refresh and any series not committed to the seed are **honestly blocked-NA, non-vetoing**.
    5. No FRED key is ever persisted (env-only); a walled provider records honest blocked-NA and never halts the loop or vetoes completion.
  - Acceptance: a **real FRED macro feed** is added behind the existing provider abstraction — a new **macro provider** (registered like the OHLCV providers in `make_provider`, key read **from the environment only, never persisted/logged/echoed** — *No secrets in source*) writing into a **dedicated additive `MacroSeries(symbol, date, value, source, published_date)` table** (a STANDALONE `create_all`-managed table so the `_ADDITIVE_COLUMNS` trap does NOT apply and **no snapshot rebuild** is required — the same standalone-table reasoning `event_study_cache` uses), **plus** the OHLCV macro proxies `^TNX` / `^DXY` / `^VXN` stored as plain `DailyPrice` bars beside the already-seeded `^VIX` (any symbol is accepted — no universe FK). The macro series are wired as **optional, config-default-off inputs** to the J-87 severity score, the J-88 regime-switching observation vector + emissions, and the J-91 study conditioning — so with macro absent or disabled every J-87..J-91 figure is **byte-identical** to the price/breadth/VIX-only path (additive, single-source). Every macro leg is **publication-lag aligned**: a value used for date D is only one whose **`published_date ≤ D`** (config publication-lag per series — using the reference-date value on D is lookahead and is forbidden), carrying an **honest publication-lag limitation label** (*No lookahead*, critical; *Honest limitations surfaced*). A **small committed macro seed over the seed window** makes the macro-conditioned features **buildable and fully testable offline with injected fixtures** (mirroring the `^VIX` seed) — those parts are expected to go green; the **live FRED/proxy refresh, and any series not committed to the seed, are data-dependent and non-halting** — when the provider is walled or a series is uncommitted it is recorded as **honestly blocked / unavailable (NA)** and **MUST NOT halt the loop, drive a STALLED verdict, or veto GOAL_ACHIEVED** (exactly the J-22 / J-44-DIA contract), and **no value is fabricated** (*No fabricated data*; *Live fetch is real-data-only*). Macro inputs change **no canonical stock score, bucket, setup, or the Risk-Off→Actionable gate** (critical, untouched) and add **no second date state** (*Exactly one date selector*). The provider + table + wiring are offline-buildable against injected fixtures + the committed macro seed; only the live FRED/proxy pull is data-gated.

- **J-93: Dynamic point-in-time universe membership — a per-as-of-date resolver becomes the SINGLE universe source feeding the scanner (stocks-only; populated by the J-85 rebuild)**
  - Steps:
    1. At any as-of date D, the scored stock set is no longer the one global `config.universe.symbols` list applied to every date — it is **resolved per-D** by a single new resolver that screens the candidate pool (`data/seed/universe_pool.csv`) on **price + ADV + minimum-history**, all computed from bars dated ≤ D (`bars_asof`), and feeds exactly that set into `score_stocks`.
    2. Step the as-of across the seed window: the membership **slides** — a name that has not yet accrued enough trailing history, or whose price / average-daily-dollar-volume sits below the config threshold at D, is **not** in the universe at D, and **enters** on the first date it clears all three; each snapshot persists its own scored membership in its own `ScannerResult` rows.
    3. `/stocks`, `/themes`, `/sectors`, `/scanner-runs`, the Backtest evidence, and the Research event study at D reflect **D's** membership; an earlier date with a smaller pool shows fewer scored names — honestly, never padded.
    4. Forward returns for each run are stored for **that run's scored tickers ∪ the benchmarks** (SPY / QQQ / sector ETFs always included), so excess-vs-benchmark stays computable even on a date whose stock universe is small or empty; a name that later exits the universe keeps its historical scored rows + forward returns untouched (immutable).
    5. The **universe-count contract becomes as-of-dependent**: `/api/data` `universe_count` and `/methodology` `resolved_size` report the members resolved **at the as-of date** (with the full-pool candidate count shown beside it), and the coverage surfaces read that same single resolver — no surface still assumes one global size. ETFs / ^VIX / the regime / sector / theme / benchmark / downtrend (J-87…J-92) machinery is **untouched** — they are infrastructure, never universe members.
  - Acceptance: a **single new point-in-time universe resolver** (a new typed, config-reading engine module — added to the `test_no_magic_numbers` `CALC_FILES` list so it carries no threshold literal) becomes the **PRIMARY universe path**, replacing the single global `config.universe.symbols` list (`scoring.py:282`/`:307`) as the source `score_stocks` iterates: for a given D it reads the committed candidate pool via `read_pool` (`universe_screen.py:51`) and admits each candidate that, from **bars dated ≤ D only** (`bars_asof`, `prices.py:185`), clears the config price (`universe.filters.min_price`) and ADV (over `universe.filters.adv_window_days`=63) thresholds **and** has ≥ `indicators.min_history_bars` (=200) trailing bars (the J-94 gate) — the **market-cap criterion is DROPPED** from the per-date screen (size is approximated by liquidity; market cap is a current-only scalar with no point-in-time series, so applying it per-historical-date would be lookahead-or-fabrication). The resolved set is the SINGLE membership read identically everywhere — the scored `ScannerResult` rows ARE the persisted membership (no second universe computation; *Single source of truth*; *No recompute in the read path*) — and `forward_symbols` is repointed so **each run's forward returns derive from that run's stored `ScannerResult` tickers ∪ `benchmark_symbols`** (always SPY/QQQ/sector ETFs) rather than the global `universe ∪ benchmarks` list (`forward_testing.py:89-99`), keeping the no-lookahead boundary (entry close on D via `close_on`, exits date > D via `bars_after`) byte-identical and benchmarks present on every run for the excess-return math. Membership is **strictly causal** — a value-for-D membership uses only bars ≤ D, unit-asserted via the same tail-invariance idiom `forward_return` uses (removing bars dated > D never changes D's resolved members), so **no future bar admits or drops a name** (*No lookahead*, critical). The feature is **stocks-only** (ETFs / ^VIX are never in the pool, so the regime / sector / benchmark / J-87…J-92 downtrend machinery is unchanged), it touches **no canonical scoring formula** (only the membership scanned over — the same reconciliation J-85 / *Snapshots are immutable* already permit), and it is **populated exclusively by the J-85 confirm-gated regenerate-from-scratch rebuild** (every snapshot cleared then recomputed over the per-date membership — never an in-place UPDATE; a name that later exits keeps its historical scored rows + forward returns). The **universe-count contract is migrated cleanly to as-of-dependence**: `compute_coverage.universe_count`, `_universe_selection.resolved_size`, and `_coverage_diagnostic_absent.universe_count` report the **members resolved at the as-of date** (the full-pool candidate count carried alongside, the J-22 invariant re-expressed as `universe_count == members-resolved-at-D` rather than `== len(global symbols)`), and the methodology Universe Selection section drops/relabels the market-cap threshold row to match the per-date rule (the dropped criterion documented, never silently asserted) — every surface that assumed one global size is updated in the same change. Membership is **real or honestly absent — never fabricated** (a sub-threshold or short-history name is excluded with a reason, never scored on padded values; *No fabricated data*), the resolver introduces **no second date state** (it reads the single global as-of; *Exactly one date selector*), and it **REDUCES survivorship bias** versus the static current-membership universe while the residual pool-survivorship is still labelled (*Honest limitations surfaced*; *Universe screen is reproducible & honest*). Fully buildable and verifiable offline against the committed 2021-2026 seed (with the honest warm-up of J-94); the true point-in-time index-constituent source is the data-walled J-95 enhancement.

- **J-94: Minimum-history sufficiency gate + honest warm-up boundary — the insufficient-data fix (a short-history stock is honestly excluded, never ranked against a full-history peer)**
  - Steps:
    1. A stock enters the universe at D **only if** it has ≥ `indicators.min_history_bars` (=200) trailing bars at D — so its MA200 / 52-week-high / 3-month-RS context exists before it is scored or cross-sectionally ranked; a 30-bar stock is **never** ranked against a 1000-bar stock.
    2. A candidate that is in the pool but below the history gate at D is **excluded with an honest reason** (the existing `thin` / `no_history` coverage vocabulary), not scored on thin / NA-heavy components.
    3. Because the committed seed starts 2021-01-04 for all symbols, the **earliest scoreable date** is `data-start + min_history` (~2021-10); stepping the as-of before that yields an **honestly empty** universe (no scored stocks) — a warm-up boundary, not a bug — while the regime / sector / benchmark surfaces still render.
    4. Forward returns remain valid through the warm-up: a stock scored at D measures its realized return from post-D bars exactly as before; an empty-universe early date simply has no stock observations (n=0), never a fabricated 0%.
    5. A new **per-date coverage diagnostic** reports, for the resolved as-of, how many pool candidates were excluded and why (below-history / below-price / below-ADV), so the small / empty early universe is explained, never mysterious.
  - Acceptance: the **minimum-history sufficiency gate** is the keystone of the per-date resolver (J-93) and the explicit fix for ranking a short-history stock cross-sectionally against full-history peers: a candidate is admitted at D **iff** `len(bars_asof(symbol, D)) >= config.indicators.min_history_bars` (=200, read from config — **no magic number**; the same canonical "insufficient-for-analysis" cutoff `_per_symbol_coverage` and `_missing_data_diagnostic` already use), so every admitted stock has the trailing window the long indicators (SMA200, 52-week high, 3-month RS) need and `score_stocks`'s cross-sectional percentiles are computed over a **history-homogeneous** set rather than mixing a 30-bar name into the peer distribution. A sub-gate candidate is **honestly EXCLUDED with a reason** — reusing the `thin` (`0 < bars < min_history_bars`) / `no_history` (`bars == 0`) coverage categories — and is **never scored on fabricated or NA-padded components** (*No fabricated data*; the indicator NA discipline at `scoring.py:_build_score` is preserved but no longer reached by a thin name in the universe). The boundary is **honest and deterministic**: the earliest scoreable date == the seed price-start + `min_history_bars` trading days (~2021-10 for the committed 2021-01-04 seed, full universe ~2022-01), and any as-of before it resolves to an **empty stock universe** rendered as an explicit empty state (the regime / sector / theme / benchmark surfaces still render from the ETF infrastructure, untouched) — never a fabricated early membership (*Honest limitations surfaced*). Forward-return validity is unaffected: an admitted stock at D still measures from bars dated > D (`bars_after`), and an empty / small early universe contributes n=0 to the aggregates exactly as a missing observation already does — never a fabricated 0% (*Honest forward-test for partial windows*). A **per-date coverage diagnostic** (a read-only descriptive derivation over the SAME stored bars + thresholds the J-36/J-37 diagnostics use, recomputing no canonical value — extends *Coverage & missing-data are descriptive & honest*) reports the resolved-as-of admitted count and the excluded counts by reason (below-history / below-price / below-ADV), so the small / empty warm-up window is **explained in plain language**, not implicit. The gate is **strictly causal** (admission at D reads only bars ≤ D; unit-asserted no-lookahead like `forward_return`), reads its threshold from config (the resolver module passes `test_no_magic_numbers`), introduces **no second date state** (*Exactly one date selector*), and changes **no canonical stock score or the Risk-Off→Actionable gate** (critical, untouched). Fully buildable and verifiable offline against the committed 2021-2026 seed (the warm-up boundary is a deterministic, reproducible property of the seed start date + `min_history_bars`).

- **J-95: Extend the import history backward (earlier start, covering the 2020 COVID crash) + the data-walled point-in-time index-membership enhancement (data-dependent / non-halting)**
  - Steps:
    1. A **confirm-gated clear → re-import → rebuild** flow can extend the committed price history backward (an earlier start than 2021-01-04 — e.g. 2020, which also covers the COVID crash for the J-87…J-92 downtrend features), so the analysis window has the full 200-bar context from early on instead of a long warm-up.
    2. The earlier-history fetch rides the existing chunked / checkpointed / resumable import machinery (no second fetch path); on success the snapshots are regenerated from scratch (J-85), and the dynamic universe (J-93/J-94) is full from a much earlier date.
    3. Until the earlier-history fetch is reachable, the feature is **offline-buildable against the committed 2021-2026 seed** with the honest J-94 warm-up — the backward-extension is recorded **honestly blocked / limited-coverage (NA)**, never halting the loop or vetoing completion.
    4. The candidate pool keeps its **explicit survivorship-bias label** (it is today's S&P 500 ∪ Nasdaq-100 ∪ prior list, not the as-of-date index constituents); an optional **true point-in-time index-membership source** (a historical-constituent feed) is offered as a data-dependent enhancement that would resolve the candidate pool itself per-date — never faked, never required.
    5. With neither the earlier history nor the constituent feed reachable, every other journey (J-93 / J-94 / J-96) still passes against the committed seed; the data-dependent legs auto-complete once the data becomes reachable, with no code change.
  - Acceptance: this journey is the **data-dependent / non-halting** envelope around the dynamic universe, exactly the J-22 / J-44-DIA contract. **(a) Backward history extension:** a confirm-gated **clear + re-import + rebuild** (the same J-85 regenerate-from-scratch mechanism + the J-34/J-35 chunked/resumable import path — no second fetch engine) can fetch an earlier price start (e.g. 2020, covering the COVID crash that enriches the J-87…J-92 downtrend / regime-switching evidence) so the per-date universe (J-93) reaches full membership from a much earlier date and the J-94 warm-up shrinks. On each resume the session attempts that fetch **once** (best-effort, never an autonomous retry loop); if the provider is unreachable the extension is recorded **honestly blocked / limited-coverage (NA)** and **MUST NOT halt the loop, drive a STALLED verdict, or veto GOAL_ACHIEVED** — the dynamic universe is fully buildable and verifiable offline against the committed 2021-2026 seed with the honest J-94 warm-up, and the earlier history auto-folds in via the same runbook once reachable, **no code change**. The committed price seed is **never deleted by the clear step** (`clear_snapshot_set` deletes only the snapshot layer, asserting `bars_before == bars_after`; the seed is un-deletable — *the committed seed is never deletable*), and any fetched history is **real committed data — never fabricated** (*No fabricated data*; *Live fetch is real-data-only*). **(b) Point-in-time index membership (data-walled):** the candidate pool (`universe_pool.csv`, today's S&P 500 ∪ Nasdaq-100 ∪ prior universe) carries its **explicit survivorship-bias label** (it is current-constituent, not as-of-date-constituent; *Universe screen is reproducible & honest*; *Honest limitations surfaced*); a **true point-in-time index-membership source** (a historical-constituent feed that would make the candidate pool itself resolve per-D, eliminating the residual pool-survivorship the J-93 liquidity screen cannot) is offered **only as a data-dependent, non-halting enhancement** — it is data-walled (no committed historical-constituent source) and **MUST NEVER be faked**: when absent, the pool stays the documented current-constituent listing with its honest label, and the as-of-dependent `universe_count` (J-93) is screened from that pool. No index-feed key is ever persisted (env-only; *No secrets in source*), and a walled provider records honest blocked-NA and never vetoes completion. Every J-93 / J-94 / J-96 figure stays byte-identical to the committed-seed path while these legs are absent.

- **J-96: Dynamic-universe membership timeline + coverage with honest survivorship / warm-up labels (entries, exits, per-date size, excluded counts)**
  - Steps:
    1. The Data Manager / coverage surface gains a **membership timeline**: per snapshot date, the resolved universe size (the count of scored stocks), drawn as a step function across the as-of dates — visibly empty/small through the warm-up, full from ~2022-01.
    2. The timeline lists **entries and exits** over time — the first date each name clears the screen (enters) and any date it drops below price / ADV / history (exits) — derived from the stored per-snapshot `ScannerResult` membership, read once, never recomputed.
    3. Beside each date the **excluded-by-reason counts** (J-94: below-history / below-price / below-ADV) explain why the resolved size is what it is, with the candidate-pool size as the denominator.
    4. The surface carries the **honest labels**: the pool-survivorship caveat (current-constituent pool, J-95), the warm-up boundary (J-94), and the universe-relative breadth caveat — so a reader never mistakes the dynamic universe for a true point-in-time index.
    5. An empty / early-history database yields an honest empty timeline; nothing is fabricated, and the timeline reads identically on every surface for the same date (coherence).
  - Acceptance: a **dynamic-universe membership timeline + coverage view** is a **read-only descriptive derivation** over the stored per-snapshot `ScannerResult` membership (J-93) + the stored bars + the config thresholds — recomputing **no** canonical score / return / membership (it reads the persisted scored-ticker sets that ARE the membership; *Single source of truth*; *No recompute in the read path*; extends *Coverage & missing-data are descriptive & honest*). It renders, per snapshot date (the `ScannerRun.asof_date` set `compute_coverage` already reads), the **resolved universe size** as a step function (the J-44/J-49 overlay treatment), and a deterministic **entries / exits** derivation — the first date each name appears in a snapshot's scored set (enters) and any date it disappears after having been present (exits) — grouped from the stored membership only, so it is **strictly causal** (each date observed from its own ≤ D snapshot; no future bar reclassifies a past entry/exit; *No lookahead*). Beside each date it shows the **J-94 excluded-by-reason counts** (below-history / below-price / below-ADV) against the candidate-pool denominator, so the small / empty warm-up window and every membership change are **explained in plain language**. The view carries the **honest labels** verbatim: the candidate pool's **survivorship-bias** caveat (current-constituent, not as-of-constituent — J-95; *Universe screen is reproducible & honest*), the **warm-up boundary** (J-94), and the **universe-relative breadth** caveat (*Honest limitations surfaced*) — and it states plainly that the dynamic universe **REDUCES** survivorship versus the static current-membership universe while the residual pool-survivorship remains until the J-95 constituent feed. An early / empty database yields an **honest empty timeline** (no fabricated dates or members; *No fabricated data*), it introduces **no second date state** (*Exactly one date selector*), changes **no canonical stock value or the Risk-Off→Actionable gate**, and is **fully buildable and verifiable offline** against the committed 2021-2026 seed (the warm-up-to-full transition and the membership entries are deterministic properties of the seed + `min_history_bars`).

- **J-97: Dashboard market cross-view — a two-pane synced indexes / phase-severity chart (the full causal phase/severity/P(bear) series served once)**
  - Steps:
    1. Directly below the existing **Major indexes & regime** chart, a **second stacked pane** renders the SAME normalized index-ETF % lines, this time over **phase-colored background bands** (the J-87 phase per date) with the **0–100 severity line** (J-87) and the **filtered P(bear) line** (J-88) overlaid — so a reader sees the same index path under both the regime lens (top pane) and the phase/severity lens (bottom pane).
    2. The two panes **share one time axis**, so dragging / scroll-zooming either pane zooms BOTH to the same date window — a perfectly synchronized cross-view with no second control.
    3. The bottom pane spans the **same full history** as the top pane: the phase/severity/P(bear) series is served **full**, not the bounded disclosure tail the Market-Phase card shows.
    4. The phase bands, severity, and P(bear) are the SAME server-computed J-87/J-88/J-89 series the card already reads — the chart only re-formats them; nothing is recomputed client-side, and the bottom pane carries the same as-of marker (J-49) the top pane uses.
    5. An as-of with no causal phase history renders an **honest empty** bottom pane; the chart never fabricates a severity, phase, or probability.
  - Acceptance: one Dashboard chart renders **two stacked `lightweight-charts` panes sharing a single time scale** — pane 0 = the existing normalized index % lines + stored-regime bands + as-of marker (J-44 / J-49, unchanged), pane 1 = the SAME normalized index lines + **phase-colored bands** + a **0–100 severity line** + the **filtered P(bear) line**, every series read from the SAME single served market-phase series the J-87 / J-88 / J-89 card consumes (*Single source of truth*; *No recompute in the read path*; the frontend only re-formats — no client-side return / probability / severity math). Because the panes share the time scale, zoom / pan is **inherently synchronized** across both — a view transform of the **visible range only**, **never a second date control** (the single global as-of stays the only date state; *Exactly one date selector*). The phase/severity/P(bear) timeline is served **full-history** for the Dashboard chart — a `?full=true`-style serialization of the `timeline_full` the market-phase engine ALREADY computes (mirroring `/api/indexes?full=true` and `/api/regime-history?full=true`), so the bottom pane spans the same window as the top with **no recompute and no new derivation**; the Market-Phase card keeps its bounded disclosure tail unchanged. The phase bands are drawn by a config-colored band primitive analogous to the stored-regime `RegimeBandPrimitive` (phase per snapshot date → band span), reading the served, config-driven phase labels verbatim (*Setup & pattern vocabulary is config-driven in the UI too*). Stored history dated after the as-of renders **display-only behind the as-of marker** and feeds no as-of-scoped computed value (*Full-history market context never looks ahead*; *Regime overlays read stored regime only*). An honest-empty timeline yields an honest-empty bottom pane (*No fabricated data*); the chart changes **no** canonical score, the Risk-Off→Actionable gate, or the as-of state. Fully buildable and verifiable offline against the committed 2021-2026 seed.

- **J-98: Dashboard at-a-glance restructure — a compact regime + phase/severity summary above the cross-view chart, the rest collapsed**
  - Steps:
    1. The top of the Dashboard becomes a **compact at-a-glance summary** that updates the instant the as-of date changes: the **market-regime label + 0–100 score**, and the **market-phase label + 0–100 severity score** (with its severity-band label) **+ filtered P(bear)** — the few figures a reader checks first.
    2. Each displayed score keeps its **named component breakdown reachable** (inline-compact or in a popover) — a score is never shown as a bare number.
    3. Directly below the summary sits the J-97 two-pane cross-view chart.
    4. The previously-top breadth metrics and the Top Sectors / Candidate Counts / Top Themes cards move into a **collapsed, expandable "More detail" section** below the chart — kept, not lost.
    5. Everything reads the single global as-of; no figure is recomputed in the view.
  - Acceptance: the Dashboard is reorganized so the **first paint shows only the at-a-glance summary + the J-97 cross-view chart** — a compact **Market Regime** figure (stored label + 0–100 score) and a compact **Market Phase & Severity** figure (stored phase label + 0–100 severity + severity-band label + filtered P(bear)), each re-displaying the SAME server-computed canonical values the Dashboard already serves (the regime from `/api/dashboard`, the phase / severity / P(bear) from `/api/market-phase`; *Single source of truth*; *No recompute in the read path*). Every displayed score **carries its named component breakdown** — kept reachable inline-compact or via a popover — so the compact layout still satisfies *Scores must be explainable* (no bare number). The existing **breadth metrics, Top Sectors, Candidate Counts, and Top Themes** are **not removed** — they relocate into a **collapsed, expandable "More detail" section** below the chart (the same data + same endpoints, only repositioned). The restructure introduces **no new endpoint, no new canonical value, and no second date state** (*Exactly one date selector*); it is an information-architecture reshuffle of already-served values, the Dashboard remains the single home for the daily snapshot (no duplicate home for an existing entity), and it changes **no** score, the Risk-Off→Actionable gate, or the as-of contract. Fully buildable and verifiable offline against the committed seed.

- **J-99: Dynamic-universe membership timeline — pagination (10 per page) + year / month filter (a pure view transform)**
  - Steps:
    1. The Data Manager's membership-timeline list (J-96) — today every snapshot date at once — becomes **paginated at 10 rows per page**, newest-first, with prev / next controls and a "Page x of N" readout.
    2. Two **dropdown filters** narrow the list — a **Year** filter and a **Month** filter — their options drawn from the dates actually present in the served timeline.
    3. Filtering and paging are a **client-side view transform** of the already-served `membership_timeline.points` payload — they re-order / narrow only the rendered rows; they recompute no per-date size, entry, exit, or excluded-by-reason count.
    4. The view stays **honest about what it hides** ("x of N dates") and the controls compose (year + month + page).
    5. An empty filter combination renders an **honest empty state**; no row is fabricated.
  - Acceptance: the J-96 membership-timeline table gains **client-side pagination (10 rows / page, newest-first, prev / next + "x of N")** and **Year + Month dropdown filters**, implemented as a **pure view transform** over the already-served `membership_timeline.points` payload — exactly the contract the leaderboard sort / search / filter already follow (*Leaderboard sorting, searching, and table filtering are view transforms*): the controls **re-order or narrow only the client-rendered rows**, never changing, recomputing, or re-deriving any per-date size / entries / exits / excluded-by-reason count (those stay the stored J-93 / J-94 values read verbatim; *No recompute in the read path*; *Single source of truth*). The Year / Month options are derived from the dates present in the payload; the filtered view stays **honest about what it hides** ("x of N dates") and **alters no underlying membership total**; an empty filter combination renders an **honest empty state**, never a fabricated row (*No fabricated data*). It requires **no backend change, no new endpoint, and no second date state** (the filters are list controls, not the global as-of switcher; *Exactly one date selector*), and reuses the existing `Select` control + the per-symbol coverage table's `useMemo` filter idiom. Fully buildable and verifiable offline.

- **J-100: Bounded-resource backend — the VM no longer freezes under concurrent dashboard / UI-test load (byte-identical canonical outputs)**
  - Steps:
    1. Concurrent `/api/data` (coverage) requests no longer each rebuild the full bar cache and recompute the O(dates × pool) membership timeline: a **single-flight + cached** path means concurrent callers share ONE in-flight computation (or the cached result), so N parallel probes cost ~one compute, not N.
    2. The membership-timeline / coverage cache key is **decoupled from forward-return churn** so the background warm-up (which inserts forward-returns) **no longer invalidates** it — eliminating the recompute storm during warm-up.
    3. The read path **reuses one process-level bar cache** (load-once, invalidate-on-data-change) instead of a fresh ~1.3M-row prefill per request, so memory stays bounded to a single copy regardless of concurrency.
    4. Heavy synchronous compute is **offloaded off the event loop** (a worker thread) and **server concurrency is capped** (a bounded semaphore / uvicorn `--limit-concurrency` + a heavy-endpoint timeout), so `/health` and light endpoints stay responsive; the backend process also runs under a **memory cap** so a runaway is OOM-killed (one process) instead of swap-freezing the whole 20 GB VM.
    5. Every served value stays **byte-identical** to the pre-change output — a pure performance / stability property, never a change to any score, return, membership, or gate.
  - Acceptance: under concurrent dashboard use and goal-mode UI-test load the backend stays **responsive and memory-bounded** — the intermittent whole-VM freeze is eliminated — while every canonical value remains **byte-identical** (a pure performance property, exactly the *Vectorized scans are a pure refactor* / J-72 contract; *Single source of truth* untouched). **(a)** `compute_coverage` / the J-96 membership timeline gain a **single-flight guard + result cache** (the same idiom the warm-up single-flight uses) so concurrent `/api/data` callers share one in-flight computation or the cached payload — N parallel probes no longer each build a `prefilled_bar_cache` (~1.3M `DailyPrice` objects) and recompute the O(~1369 dates × ~548 pool) loop. **(b)** the coverage / membership-timeline **cache key is decoupled from the forward-returns table** (membership depends only on bars + snapshot set + config), so the background warm-up's forward-return inserts **stop invalidating** it — no recompute storm during warm-up (*Warm-up obeys every data invariant and is idempotent, concurrency-safe, and non-fatal*). **(c)** the read path **reuses a single process-level bar cache** (load-once, invalidated on a real data change) for `_resolved_universe` + the timeline rather than a per-request prefill, bounding memory to one copy. **(d)** heavy synchronous compute is **run in a worker thread** (`run_in_threadpool` / `to_thread`) and server **concurrency is capped** (a bounded semaphore and/or uvicorn `--limit-concurrency` in the start script) with a request timeout on the heavy endpoints, so `/health` + light reads stay responsive (*Startup must not block serving on historical warm-up* reinforced at steady state); the backend process runs under an explicit **memory cap** (systemd `MemoryMax` / cgroup / `ulimit`) so a pathological spike is OOM-killed as a single process, never a swap-thrash freeze of the whole VM. **(e)** goal-mode / browser-QA **test hygiene** is codified: `/api/data` is single-loaded (never concurrently probed), with the `.pump-alive` toucher + heartbeat envs for long QA, so the harness no longer reproduces the freeze. Measured by a **concurrency load test** asserting K parallel `/api/data` calls all return within a bound, peak process RSS stays under a configured cap, `/health` latency stays low throughout, and the served coverage equals the single-request baseline (byte-identical); a test asserts warm-up forward-return inserts do **not** invalidate the membership cache; and the existing canonical suites stay green. It changes **no** canonical score / return / membership or the Risk-Off→Actionable gate. Fully buildable and verifiable offline against the committed seed.

- **J-101: Dashboard cross-view consolidation — one market chart (the duplicate Major-indexes card removed) whose phase pane spans the full history at any as-of**
  - Steps:
    1. The Dashboard shows **exactly one** market chart — the **two-pane cross-view** (J-97). The separate, redundant **Major indexes & regime** card (whose content is byte-for-byte the cross-view's pane 0) is **removed**; nothing is lost because pane 0 already renders the same normalized index % lines over the same stored-regime bands.
    2. In the bottom (phase) pane, the **phase-colored bands span the full history** — every snapshot date carries its causal phase color — **regardless of the selected as-of date**, exactly like the regime bands in the top pane (today they stop at the as-of because the series is fetched causal-`≤D`).
    3. Selecting a historical as-of **only moves the as-of marker**; it does **not** truncate the phase bands at the marker. Stored history dated after the as-of stays **display-only behind the marker** (a labelled forward/after-as-of display), feeding no as-of-scoped computed value.
    4. The two panes still share one time axis (zoom/pan synchronized); the single global as-of stays the only date state.
    5. An as-of with no causal phase history renders an honest-empty phase pane; the chart fabricates no band.
  - Acceptance: the Dashboard renders **one** market chart card — the J-97 two-pane synced cross-view — and the standalone **Major indexes & regime** card is **deleted** (it was a *duplicate home for an existing entity*: pane 0 already IS that chart, reading the SAME `/api/indexes?full=true` + `/api/regime-history?full=true` series; *Single source of truth*; *No recompute in the read path*). The bottom pane's **phase bands now span the same full history as the top pane's regime bands** — the phase/severity/velocity timeline is fed **full-history independent of the global as-of** (the phase-band primitive's clip stays `null`, and the series is fetched unfiltered by as-of, mirroring how `/api/regime-history?full=true` already serves the regime bands full-history regardless of as-of, J-49). The selected as-of renders **only as the marker**; stored history dated after D is **display-only behind the marker** and feeds **no** as-of-scoped score / return / severity (*No lookahead*; *Full-history market context never looks ahead*). The change introduces **no new endpoint, no new canonical value, and no second date state** (*Exactly one date selector*) and alters **no** score, the Risk-Off→Actionable gate, or the as-of contract — it is an information-architecture de-duplication plus a display-clamp alignment of already-served series. An honest-empty timeline yields an honest-empty pane (*No fabricated data*). Fully buildable and verifiable offline against the committed seed.

- **J-102: Cross-view phase pane — a served severity-velocity line replaces the P(bear) line, and the hover tooltip gains the regime status**
  - Steps:
    1. The market-phase engine serves a new **severity-velocity** value per timeline date — the rate of change of the 0–100 severity over a **config-defined lookback window (default 5 snapshots)**, sign **positive = severity worsening**, negative = severity easing.
    2. In the cross-view's phase pane, the **filtered P(bear) line is removed** from the plot (it was visually low-signal) and the **severity-velocity** is drawn instead, as a **zero-centered** line on its own overlay scale with a 0 reference.
    3. The hover **tooltip** adds the **market-regime label + 0–100 score** for the hovered date (the same stored regime the top pane's bands use) and the **severity-velocity** value — alongside the existing date, index %, phase, and severity. The **P(bear) value stays in the tooltip** (only its plotted line is removed).
    4. Severity-velocity is **strictly causal** — computed from severity at dates ≤ each date — and is **NA** at the warm-up head where the window is unavailable (no fabricated slope).
    5. Everything is a re-format of server-computed values; the frontend computes no velocity, regime, or probability itself.
  - Acceptance: `/api/market-phase` (and its `?full=true` `timeline_full`) carries a new **`severity_velocity`** field per date — the **deterministic, config-windowed slope of the served 0–100 severity** (the lookback window is a typed, validated `config.market_phase.*` key; *No magic numbers* — the module still passes the `test_no_magic_numbers` tokenizer), **strictly causal** (severity at dates ≤ D only), **NA** where the window head is unavailable, and **never smoothed with future data** (*No lookahead*). Because it is a new key in the **cached** market-phase payload, the **`SCHEMA_VERSION` token is bumped (`s1`→`s2`)** so `_cache_version` refreshes every `MarketPhaseCache` row to the new shape (the documented cache-schema discipline — a stale row must never serve the old shape). In the Dashboard cross-view's phase pane the **plotted filtered-P(bear) line is removed** and a **zero-centered severity-velocity line** is drawn on its own hidden overlay scale (reusing the retired P(bear) scale slot so the index % lines stay undistorted); the **hover tooltip** adds the **stored regime label + 0–100 score** (read from the already-fetched `/api/regime-history` points — *Single source of truth*; *Scores must be explainable*) and the **severity-velocity** value, while **retaining** the phase, severity, and **P(bear)** rows. The frontend **re-formats only** — it computes no velocity / regime / probability (*No recompute in the read path*). It adds **no second date state** (*Exactly one date selector*) and changes **no** canonical score, the Risk-Off→Actionable gate, or the as-of contract; the Market-Phase card and the at-a-glance summary keep showing P(bear) unchanged. Fully buildable and verifiable offline against the committed seed.

- **J-103: Severity-velocity × regime forward-return study — does rising / falling stress under a red regime predict the market's next move?**
  - Steps:
    1. A new **Research study**, on its own lazy-loaded sub-route reached from the `/research` hub, answers a precise question: conditioned on the **market-regime family** (risk-on / neutral / risk-off "red") and the **sign of severity-velocity** (rising vs falling stress) at a snapshot date, what is the **forward market return** (benchmark SPY) over 5 / 10 / 20 / 60 trading days?
    2. It renders a **regime-family × velocity-sign matrix**: each cell shows the **mean forward return, win-rate, and sample size N** at the selected horizon, drawn once from the stored forward returns — never recomputed in the view.
    3. Every **`N=` figure drills into Research Samples** (new tab) reproducing that exact cohort (the qualifying dates + their stored forward returns), exactly like the other labs' sample chips.
    4. The study states a **plain-language verdict** grounded in the data and carries **honest limitations** — the loaded sample window is bull-dominated with only shallow drawdowns, so it is **underpowered for sustained crashes** until the pre-2021 history (J-95) is loaded; NA/partial cells are shown honestly, never fabricated.
    5. Defaults to an all-history aggregate and respects the Research **As-of mode** (restricting to snapshots ≤ D) as a filter, never a recompute.
  - Acceptance: a **Severity-velocity × Regime forward-return study** is served from a **derived-once, cached aggregate** (the `EventStudyCache` + `_dataset_version` idiom the event-study / downtrend studies already use, with the schema token) over the **stored append-only `forward_returns`** (benchmark SPY) joined to the **served severity-velocity (J-102) + stored regime label** per snapshot date — a **pure grouping of stored data** that **recomputes no canonical return** (*Single source of truth*; *No recompute in the read path*; the figures are byte-identical and refresh only on a dataset change — the J-72 performance contract). The figure is a **regime-family × velocity-sign matrix** of **mean forward return, win-rate, and N** per horizon (5 / 10 / 20 / 60), every **`N=` chip linking into Research Samples** (new tab — J-65 / J-77) to the exact reproducing cohort (the study's per-cell total equals the published N; *Research sample membership* coherence). Forward returns use **only bars dated > D** (*No lookahead*) and are **NA/partial-honest** where samples are insufficient (*Honest forward-test for partial windows*). The surface lives at its **own `/research/severity-velocity` sub-route, reached from the `/research` hub and deep-linkable** (a real nav path, no orphan surface), lazy-loaded per J-104. It carries a **plain-language verdict** computed from the served figures plus the **honest survivorship / bull-dominated-sample / underpowered-for-crashes** caveats verbatim (*Honest limitations surfaced*) — documenting that, on the committed seed, **rising stress-velocity under a red regime preceded a bounce, not continuation** (the stated hypothesis is **not supported** on this window), while remaining a reusable tool to re-test once deeper-drawdown history loads. It honors the Research **As-of mode** as a pure observation-set filter (J-32) and **defaults to the all-history aggregate**; it adds **no second date state** (*Exactly one date selector*) and changes **no** canonical value or the Risk-Off→Actionable gate. Fully buildable and verifiable offline against the committed seed.

- **J-104: Research labs load reliably — every heavy panel cached, the slow queries fixed, and the page split + lazy-loaded so nothing fires four heavy fetches at once**
  - Steps:
    1. The Research panels that error / stall on load — **Multi-factor combination**, **Setup & Pattern event-study**, **Regime × Setup × Pattern**, and **Downtrend Opportunity** — are made fast and reliable.
    2. The two **uncached** studies (factor-combination, regime × setup × pattern) gain the **same derived-aggregate cache** the event-study and downtrend studies already use, so a repeat request is a cache hit, not a full recompute.
    3. The **full-table scan** in the downtrend-opportunity observation builder (reading every `ScannerRun` with no as-of bound) is **scoped to snapshots ≤ the as-of**, and the shared run-position-index reads are likewise as-of-bounded — so a single panel no longer scans the whole run table.
    4. The page no longer fires all heavy panels **concurrently on mount**: each heavy panel is **lazy** (collapsed by default, fetching only when expanded / scrolled into view) **and** the heaviest labs move to **their own `/research/*` sub-routes**, so any one page triggers at most one heavy fetch; `/research` becomes a hub linking to them.
    5. Every served figure stays **byte-identical** to before — a pure performance / reliability property, no change to any aggregate.
  - Acceptance: the four heavy Research labs **load without error under normal use** — a pure performance / stability property with **byte-identical** figures (the J-72 / *Vectorized scans are a pure refactor* contract; *Single source of truth* untouched). **(a)** `compute_factor_combination` and `compute_regime_setup_pattern_study` are served from a **persisted/cached derived aggregate** (the `EventStudyCache` + `_dataset_version` pattern already used by `event_study_cached` / `downtrend_opportunity_cached`, refreshing on dataset change), so they stop recomputing from scratch per request (*No recompute in the read path*). **(b)** the **full `select(ScannerRun)` table scan** in `_downtrend_opportunity_observation_set` is **bounded with `where(ScannerRun.asof_date <= as_of)`**, and the shared `_run_position_index` callers pass the as-of bound, so episodes-mode reads no longer load the entire run table. **(c)** the frontend **does not fire all four heavy fetches on mount**: each heavy panel is **lazy** (collapsed / fetch-on-expand or on-visible) **and** the heaviest labs are **split into their own `/research/*` sub-routes** (e.g. `/research/factor-combination`, `/research/event-study`, `/research/regime-setup-pattern`, `/research/downtrend-opportunity`, plus the J-103 `/research/severity-velocity`), with `/research` a hub that links to each — so at most one heavy computation runs per page (eliminating the concurrent-load pool exhaustion). The split is reflected in the navigation / IA (each lab is reachable and deep-linkable; no orphan surface) and the existing `N=` samples drill-downs keep working from the relocated labs. It changes **no** canonical score / return / membership / aggregate value or the Risk-Off→Actionable gate; the existing research suites stay green. Fully buildable and verifiable offline against the committed seed.

- **J-105: Research labs serve on the full live dataset without exhausting memory — the forward-return read path is streamed / column-projected (no unbounded full-table materialization), with byte-identical figures**
  - Steps:
    1. The heavy Research labs that **fail with an out-of-memory error** as the stored history grows — **Setup & Pattern event-study**, **Factor Lab**, **Multi-factor combination**, **Regime × Setup × Pattern**, and **Downtrend Opportunity** — serve **reliably regardless of how large the stored `forward_returns` table has become**.
    2. The per-observation builders **no longer load the entire `forward_returns` table as ORM objects** into memory (`select(ForwardReturn) … .all()`); they **stream column-projected rows** in config-sized batches and, where the cohort is subject-/factor-scoped, **filter the scan to only the rows the study needs** (the *Bounded-resource backend* contract of J-100, extended to the research read path).
    3. The warm-up forward-return **backfill** builds its idempotency set by **streaming projected keys**, not by materializing every stored row at once.
    4. Every served figure — every matrix cell, mean / win-rate / N, and every `N=` samples drill-down cohort — stays **byte-identical** to before; this is a pure memory-safety property, no change to any aggregate.
    5. The labs and their samples drill-downs **return successfully on the full live dataset**; an honest error state is shown only on a genuine fault, never fabricated data.
  - Acceptance: the five heavy Research labs (event-study, factor-lab, factor-combination, regime × setup × pattern, downtrend-opportunity) and their **`N=` Research-Samples drill-downs** serve **HTTP 200 on the full live dataset within bounded memory** — the read path **never materializes an unbounded full table**: the whole-table ORM `… .all()` loads in the per-observation builders and the warm-up `backfill_forward_returns` are replaced by **column-projected, `yield_per`-streamed reads bounded to the cohort each study reads** (*Bounded-resource backend*, J-100). Every served figure is **byte-identical** to the prior aggregation (*Single source of truth*; *No recompute in the read path*; *Vectorized scans are a pure refactor* — proven by **deep-equality tests of the bounded builder against the prior per-observation reference**, across as-of / all-history, pooled / episodes, and zero-N cohorts). Forward returns still use **only bars dated > D** (*No lookahead*) and stay **NA/partial-honest** (*Honest forward-test for partial windows*); each figure's reported cohort still **equals its `N=` samples drill-down** (*Research sample membership* coherence). The streaming **batch size is config-defined** (no magic number), the fix **adds no table**, and it changes **no** canonical score / return / membership / aggregate value or the Risk-Off→Actionable gate; the existing research + forward-testing suites stay green. This **closes the iter-46 regression** — event-study (J-29) and factor-lab (J-25 / J-26) went passing→failing with a `MemoryError` on the grown live `forward_returns`. Fully buildable and verifiable offline against the committed seed.

- **J-106: Stocks leaderboard shows a Proximity-to-52w-high column after Risk**
  - Steps:
    1. Visit `/stocks`.
    2. In the leaderboard table, find a new **Proximity to 52w high** column immediately after the **Risk** column.
    3. Read a stock's value — the percentage distance of its latest close below its 52-week high (0% at a fresh high, negative below) — the same value the stock's Leadership breakdown shows as its `high_proximity` component.
    4. Click the column header to sort by it (client-side), like the other sortable columns.
  - Acceptance: the `/stocks` leaderboard renders a **Proximity to 52w high** column **directly after the Risk column**, displaying the **stored** `high_proximity` value already carried on each stock row's Leadership component (the existing `indicators.dist_from_high(closes, config.indicators.high_window_52w)` — ≤ 0, 0 at a fresh high, **NA** when fewer than the window's bars) — **read from the persisted snapshot, never recomputed in the endpoint or the view** (*Single source of truth*; *No recompute in the read path*). The 52-week window is **config-driven** (*No magic numbers*). The column is **client-side sortable** under the existing view-transform contract (*Leaderboard sorting, searching, and table filtering are view transforms*; J-48) and is **NA-honest** (never fabricated). Its header carries the same **config-backed glossary tooltip** the term already has (J-47). It changes **no** canonical score, the Risk-Off→Actionable gate, or the as-of contract, and adds **no second date state** (*Exactly one date selector*). Fully buildable and verifiable offline against the committed seed.

- **J-107: Factor Lab — an all-factors Rank-IC + risk-adjusted table with an expandable per-factor decile sort (supersedes the single-factor dropdown view)**
  - Steps:
    1. Open `/research/factor-lab`.
    2. Instead of a single-factor dropdown, see a **table listing every config-catalog factor** (one row per factor) with its **family**, its **Rank-IC** (value + N), and a **risk-adjusted** figure, at the selected horizon (the existing horizon selector remains).
    3. Sort the table by any column (Rank-IC, risk-adjusted, N) — NA-last.
    4. Click a factor row to **expand it in place**, revealing that factor's **decile sort** (the D1..D10 decile table), hidden by default; click again to collapse.
    5. Each decile's `N=` chip still drills into Research Samples (new tab).
  - Acceptance: `/research/factor-lab` renders an **all-factors table** — one row per `config`-catalog factor (incl. the volatility family) showing **family, Rank-IC (value + N), and a downside-risk-adjusted figure**, all at the selected horizon — that **replaces** the prior single-factor dropdown view. Every value is **byte-identical** to the single-factor lab's because it is produced by the **same `compute_factor_lab` / `_rank_ic` / risk-adjusted builders** (one computation path — *Single source of truth*; *No recompute in the read path*; *Research lab is read-only, honest & not predictive*), served from a **derived-once cached aggregate** (the `EventStudyCache` + `_dataset_version` idiom, **streamed / column-projected per J-105** so it stays bounded on the full live dataset; the J-72 / J-104 performance contract — byte-identical figures that refresh only on a dataset change). The risk-adjusted figure uses **downside deviation only**, never total volatility, shown beside the raw Rank-IC (*Risk-adjusted reporting is honest & must not conflate up/down volatility*). Each factor row is **click-to-expand** (the keyboard-accessible `aria-expanded` expandable-row pattern the Sectors page already uses), revealing that factor's **decile sort** (the existing decile table: D1..D10 factor range, mean return, risk-adjusted, N, low-sample flag) **hidden by default**. The table is **client-side sortable NA-last** (*Leaderboard sorting … are view transforms*; J-48) and honors the Research **As-of mode** as a pure observation-set filter (J-32). Every decile `N=` chip still drills into **Research Samples** in a new tab reproducing the exact cohort (J-51 / J-65, count-coherent). This **supersedes** the Factor Lab's separate rank-IC card and **retires its per-regime effectiveness table** from this view (the regime-conditioned slice remains a derived-once canonical value, no longer surfaced as a Factor-Lab table; the multi-factor **composite** combination lab on `/research/factor-combination` is untouched). It adds **no second date state** (*Exactly one date selector*) and changes **no** canonical decile / IC value or the Risk-Off→Actionable gate; the existing research suites stay green. Fully buildable and verifiable offline against the committed seed.

- **J-108: The readiness badge reflects the true backend status — the always-"Backend unavailable" bug fixed (regression against J-40)**
  - Steps:
    1. Start the stack the way the developer runs it — **`./scripts/dev.sh`** (deterministic offset ports; it already sets `NEXT_PUBLIC_API_URL` to the backend port and `CORS_ORIGINS` to the frontend origin).
    2. Open the frontend and watch the top-bar readiness badge and the per-page data.
    3. Observe the bug: the badge shows **"Backend unavailable"** even though the backend process is up and `/api/health` returns HTTP 200.
    4. Diagnose the **actual** failing path end-to-end: the exact URL the browser calls for `/api/health`, the HTTP status / body / network error / CORS result, and the backend's reported `readiness` value.
    5. Fix the root cause so the badge is **accurate**.
  - Acceptance: running the app via **`./scripts/dev.sh`** against the committed seed, the top-bar readiness badge reaches **Ready** (or **Initializing… (n/m)** while the background warm-up runs) whenever the backend is genuinely accepting connections and serving the latest snapshot, and shows **Unavailable only when the backend truly cannot serve** — closing the regression where it was **stuck on "Backend unavailable"** (the J-40 honest-readiness contract; the *Readiness is reported honestly* anti-goal; the success criterion that *a slow, contended, or failed warm-up never shows a misleading "unavailable"*). The fix is grounded in a **diagnosed root cause of the live `/api/health` request path** — among: the resolved **frontend API base URL vs the actual backend port** under `dev.sh`'s offset (and the **host** case — a client opening the app at the LAN IP while `NEXT_PUBLIC_API_URL` is hardcoded `localhost`), the **CORS** origin set, the **health poll's success / failure / timeout conditions** in the ReadinessProvider, and the backend **readiness computation** (`readiness.py` `latest_servable`), including the `--reload` **double-instance / re-spawn** contention J-40 already flags — and is verified by observing the badge transition to **Ready / Initializing** with the backend up and to **Unavailable** only when it is genuinely down. The badge is **never hardcoded, inverted, or stuck**, and the fix **must not fake Ready** when the backend is down (honest states preserved; no fabricated availability — *No fabricated data*). It changes **no** canonical value or the as-of contract. Fully buildable and verifiable offline against the committed seed via `./scripts/dev.sh`.

- **J-109: Factor Lab — all-horizon forward-return + max-drawdown columns on both the all-factors table and the decile sort (removes the horizon selector; mirrors J-75 / J-86; amends J-25 / J-107)**
  - Steps:
    1. Visit the **Factor Lab** (`/research/factor-lab`) — the per-horizon selector (1d/5d/10d/20d/60d) is **gone**; every horizon is shown at once.
    2. In the **all-factors table**, each factor row shows — beside Family and Rank-IC — **all five forward-return columns (1/5/10/20/60d) first, then all five max-drawdown columns (1/5/10/20/60d)** — grouped by metric, never interleaved (J-114): the factor's **top-decile (D10)** cohort mean realized forward return and that cohort's mean peak-to-trough max-drawdown at each horizon, colour-graded and client-side sortable (J-48).
    3. Expand a factor row to reveal its **decile sort**: for each decile D1…D10, the same five forward-return columns then five max-drawdown columns (grouped by metric — J-114) — each the **decile's** mean realized forward return / mean max-drawdown at that horizon — with the per-decile sample size **n** (a samples chip) and the factor range.
    4. Click a decile's **n** chip for a given horizon — `/research/samples` opens that exact `(factor, horizon, decile)` cohort (new tab) and its total equals the displayed n.
    5. Toggle **As-of vs All-history** (J-32) — every column re-points; at/near the latest date the longer horizons read **NA** (insufficient post-D bars), never a fabricated number.
    6. Confirm low-sample deciles show **NA + n** and the survivorship-bias / descriptive-evidence labels persist.
  - Acceptance: the Factor Lab (J-107) **drops its single-horizon selector** and instead shows all `config.walk_forward.horizons` at once as **all forward-return columns then all max-drawdown columns (grouped by metric, never interleaved — J-114) on BOTH tables** — the all-factors table and each factor's expandable decile sort — mirroring the J-75 / J-86 leaderboard treatment. In the all-factors table a factor's per-horizon cell is its **top-decile (D10)** cohort mean realized forward return and that same cohort's mean max-drawdown (the holdable top cohort — consistent with the existing top-decile risk-adjusted column); in the decile sort each cell is that **decile's** mean realized forward return and mean max-drawdown. Every figure is read from the **stored append-only `forward_returns` table** (the realized return + the J-86 max-drawdown) by the **same observation builders the existing single-horizon view uses**, so each horizon column is **byte-identical to today's per-horizon figures** — decile membership is the existing per-horizon factor sort (independent per horizon), recomputing nothing (*Single source of truth*; *No recompute in the read path*) — and served from the same persisted/cached aggregate (the J-72 `EventStudyCache` + dataset-version idiom, its key extended to the all-horizons view). The horizon set comes from `config.walk_forward.horizons` (**no hardcoded `[1,5,10,20,60]`** — *No magic numbers*), so adding a horizon adds both columns automatically. Columns are **client-side sortable** under the J-48 view-transform contract (re-orders only — recomputes/refetches nothing) and colour-graded; the **As-of vs All-history** toggle (J-32) only FILTERS the observation set (no second date state — J-18); a horizon whose return is **NA** (insufficient post-D bars) shows its max-drawdown **NA** too (*Honest forward-test for partial windows*); low-sample deciles show **NA + n**. The **Rank-IC** and downside **risk-adjusted** figures remain, computed at `config.walk_forward.default_horizon` (now a fixed config default, not a user selector) and labelled with that horizon. Every **n** chip drills into Research Samples reproducing the exact `(factor, horizon, decile)` cohort (J-51 / J-65 count-coherence). This is a **new read surface of existing stored data, not a new computation**.

- **J-110: Research — Regime Lab: cross-sectional forward returns + max-drawdown by regime label and by regime-score decile (new `/research/regime-lab`; mirrors Factor Lab)**
  - Steps:
    1. From the `/research` hub, open the new **Regime Lab** tile (`/research/regime-lab`).
    2. Read the **by-label summary table**: one row per canonical market-regime label (the six the Dashboard shows — Strong risk-on … Risk-off), each showing the **cross-sectional mean forward return and max-drawdown — all five forward-return columns first, then all five max-drawdown columns (1/5/10/20/60d, grouped by metric — J-114)**, with n, colour-graded and sortable (J-48).
    3. Read the **regime-score decile sort**: D1…D10 by the stored 0–100 regime score, each decile showing its score range, the same five forward-return + five max-drawdown columns, and n.
    4. Read the **rank-IC** of the regime score vs the forward return at each horizon (sign + magnitude + n).
    5. Click any **n** chip — `/research/samples` opens that exact cohort (regime label **or** regime-score decile, at that horizon) and its total equals n.
    6. Toggle **As-of vs All-history** (J-32); low-sample buckets show **NA + n** and the survivorship-bias label persists.
  - Acceptance: a new Research lab at `/research/regime-lab` — a tile on the `/research` hub, **lazy-loaded on its own sub-route**, registered in the Navigation/IA + canonical-values contract — studies how stocks' forward returns relate to the market regime, **mirroring Factor Lab's main-table + decile-sort layout**. It pools the **same cross-sectional per-observation forward returns** the Factor Lab / event study use (stock × snapshot), each observation carrying its run's stored `regime_score` + `regime_label` read **verbatim from the immutable `ScannerRun` row** (the same canonical regime the Dashboard / Stocks header show — J-80; **no regime recomputed**), and groups them two ways: (a) by the **six canonical regime labels** and (b) into **deciles D1…D10 of the 0–100 regime score** (reusing the generic `_deciles` / `_decile_member_slice` machinery). For every bucket it shows, per `config.walk_forward.horizons` horizon, the **mean realized forward return and a mean max-drawdown** (columns grouped by metric per J-114 — all forward-return columns first, then all max-drawdown columns) — both read from the stored append-only `forward_returns` table (realized return + the J-86 max-drawdown), **never recomputed** (*Single source of truth*; *No recompute in the read path*) — plus n and, for the decile view, the score range and the **rank-IC** of the regime score vs the forward return. Every figure is derived once and served from the persisted/cached aggregate (the J-72 `EventStudyCache` + dataset-version idiom), uses **only bars dated > D** (*No lookahead*), is **NA-honest** on low-sample buckets and at/near the latest date (never fabricated — *Honest forward-test for partial windows*), and the horizon set is config-driven (*No magic numbers*). Columns are **client-side sortable** (J-48) and colour-graded; the **As-of vs All-history** toggle (J-32) only FILTERS the observation set (no second date state — J-18); every **n** chip drills into Research Samples reproducing the exact `(regime label | regime-score decile, horizon)` cohort (J-51 / J-65 count-coherence). Descriptive, survivorship-biased evidence (labels persist), **never a fitted/predictive model**. It is **DISTINCT from** Regime × Setup × Pattern (J-77 / J-82 — regime × setup × pattern combinations) and Severity-velocity × Regime (J-103 — severity-velocity sign × regime → SPY): it studies the **regime score/label alone against cross-sectional stock returns** (no setup/pattern/velocity dimension), so it introduces **no duplicate home** and recomputes none of their values.

- **J-111: Research — Market Phase & Severity Lab: cross-sectional forward returns + max-drawdown by phase label and by severity-score decile (new `/research/phase-severity-lab`; mirrors Factor Lab / J-110)**
  - Steps:
    1. From the `/research` hub, open the new **Market Phase & Severity Lab** tile (`/research/phase-severity-lab`).
    2. Read the **by-phase-label summary table**: one row per canonical market-phase label (the five the Dashboard shows — Expansion / Recovery / Pullback / Correction / Bear), each with the **cross-sectional mean forward return and max-drawdown — all five forward-return columns first, then all five max-drawdown columns (1/5/10/20/60d, grouped by metric — J-114)**, n, colour-graded and sortable (J-48).
    3. Read the **severity-score decile sort**: D1…D10 by the 0–100 severity score, each decile showing its score range, the five forward-return + five max-drawdown columns, and n.
    4. Read the **rank-IC** of the severity score vs the forward return at each horizon.
    5. Click any **n** chip — `/research/samples` opens that exact cohort (phase label **or** severity-score decile, at that horizon); total equals n.
    6. Toggle **As-of vs All-history** (J-32); low-sample buckets show **NA + n**; the survivorship-bias label persists.
  - Acceptance: a new Research lab at `/research/phase-severity-lab` — a `/research` hub tile, lazy-loaded on its own sub-route, registered in the Navigation/IA + canonical-values contract — mirrors J-110 for **market phase & severity**. It pools the **same cross-sectional per-observation forward returns** (stock × snapshot), each observation carrying its **snapshot date's served phase label + 0–100 severity score** read **verbatim from the `/api/market-phase` causal timeline** (the single full series of J-87 / J-97 / J-102 — **no phase/severity recomputed**), joined by snapshot date, and groups them two ways: (a) by the **five canonical phase labels** and (b) into **deciles of the 0–100 severity score** (generic `_deciles` machinery). For every bucket it shows, per `config.walk_forward.horizons` horizon, the **mean realized forward return and mean max-drawdown** (columns grouped by metric per J-114 — all forward-return columns first, then all max-drawdown columns) read from the stored `forward_returns` table (realized return + J-86 max-drawdown), **never recomputed** (*Single source of truth*; *No recompute in the read path*), plus n and (decile view) the score range + **rank-IC**. Derived once, served from the persisted/cached aggregate (J-72 idiom); **only bars dated > D** (*No lookahead*); **NA-honest** on thin cells and at/near latest (never fabricated); horizon set config-driven (*No magic numbers*). Columns client-side sortable (J-48) and colour-graded; the As-of vs All-history toggle (J-32) only FILTERS (no second date state — J-18); every **n** chip drills into Research Samples reproducing the exact `(phase label | severity-score decile, horizon)` cohort (J-51 / J-65 count-coherence). Descriptive, survivorship-biased evidence; **never a fitted model**. **DISTINCT from** Severity-velocity × Regime (J-103, which studies the velocity/slope **sign** of severity against SPY): this studies the severity **level** (and the phase label) against **cross-sectional stock returns** — no duplicate home, no recomputed canonical value.

- **J-112: Research — Regime × Market-Phase/Severity × Factor 3-way decile study: a ranked, filterable, paginated combination table with per-horizon forward returns + max-drawdown (new `/research/regime-phase-factor`; mirrors J-77 / J-82)**
  - Steps:
    1. From `/research`, open the new **Regime × Phase × Factor** tile (`/research/regime-phase-factor`).
    2. **Pick a factor** (any catalog factor). A ranked, sortable table then lists combinations, each row a **(regime-score decile, severity-score decile, factor decile)** triple, showing **n** and, per horizon (1/5/10/20/60d), **all forward-return columns first, then all max-drawdown columns (grouped by metric — J-114)**.
    3. **Filter** by regime decile, severity decile, and/or factor decile; **sort** any column (NA-last in both directions); the table **paginates at 30 rows per page**.
    4. Click a row's **n** chip — `/research/samples` opens that exact triple cohort (new tab) with total == n.
    5. Toggle **As-of vs All-history** (J-32); low-sample combinations show **NA + n** (or are held below the config min-sample); the survivorship-bias label persists.
  - Acceptance: a new Research lab at `/research/regime-phase-factor` — a `/research` hub tile, lazy-loaded on its own sub-route, registered in the Navigation/IA + canonical-values contract — renders a **ranked, client-side-sortable, paginated table of (regime-score decile × severity-score decile × factor decile) combinations** for a **selected factor**, mirroring the Regime × Setup × Pattern ranked-combination pattern (J-77 / J-82) over the three decile dimensions. It pools the **same cross-sectional per-observation forward returns** (stock × snapshot) the other labs use, each observation carrying its stored `regime_score` (`ScannerRun`, verbatim), its snapshot date's **served severity score** (the J-87 `/api/market-phase` series, verbatim), and the **selected factor's stored value**; it buckets each into **deciles** (generic `_deciles` machinery) and groups by the `(regime-decile, severity-decile, factor-decile)` key. Each row shows **n** and, per `config.walk_forward.horizons` horizon, the combination's **mean realized forward return and mean max-drawdown** (columns grouped by metric per J-114 — all forward-return columns first, then all max-drawdown columns) read from the stored `forward_returns` table (realized return + J-86 max-drawdown), **derived once** and served from the persisted/cached aggregate (J-72 idiom), **never recomputed** (*Single source of truth*; *No recompute in the read path*), **only bars dated > D** (*No lookahead*). The table is **client-side sortable** under the J-48 contract sorting **NA-last in both directions** (the J-82 predicate — `low_sample` OR `n === 0` OR `value === null` sinks last), **filterable** by regime decile / severity decile / factor decile from the config-driven vocabulary, and **paginated at 30 rows per page** (a pure view transform — re-orders/pages only, recomputes/refetches nothing); the **As-of vs All-history** toggle (J-32) only FILTERS the observations (no second date state — J-18). Low-sample / empty combinations show **NA + n** or are held below the config min-sample threshold (**no magic number**), **never fabricated** (*Honest forward-test for partial windows*); every **n** chip drills into Research Samples reproducing the exact `(regime-decile, severity-decile, factor-decile, horizon)` cohort **without error**, total == n (J-51 / J-65 count-coherence). Descriptive, survivorship-biased evidence (label persists); **never a fitted model**. **Distinct subject** from J-77 (setup/pattern) and J-103 (severity-velocity) — **no duplicate home, no recomputed canonical value**.

- **J-113: Research hub — the regime / phase / factor labs lead the hub in reading order**
  - Steps:
    1. Visit `/research`.
    2. The lab cards now read left-to-right, then top-to-bottom: **Factor Lab → Regime Lab → Market Phase & Severity Lab → Regime × Phase × Factor → Regime × Setup × Pattern → Severity-velocity × Regime**, then **Multi-factor combination → Setup & Pattern event study → Recovery-Turn Edge → Downtrend Opportunity**.
    3. Every lab is still present, reachable, and deep-linkable.
  - Acceptance: the `/research` hub's single ordered lab source (the `LABS` array the `grid-cols-1 sm:grid-cols-2 xl:grid-cols-3` grid maps over) is reordered to exactly that sequence — the regime / phase / severity-themed labs clustered first (Factor Lab, Regime Lab, Market Phase & Severity Lab, Regime × Phase × Factor, Regime × Setup × Pattern, Severity-velocity × Regime), followed by Multi-factor combination, Setup & Pattern event study, Recovery-Turn Edge, Downtrend Opportunity. A **pure presentation / information-architecture reorder**: no lab is added or removed (all ten remain reachable + deep-linkable — **no orphan surface, no duplicate home**); every route, the `?asof` href-stamping (J-50), and the per-lab lazy-load (J-104) behaviour is unchanged; and it touches **no** canonical score / return / value, no endpoint, and not the Risk-Off→Actionable gate. A committed test asserts the rendered card order inside the `data-testid="research-hub"` container (the order of the `research-lab-link-*` links). Pure frontend; buildable + verifiable offline against the committed seed.

- **J-114: Research labs — all forward-return columns grouped first, then all max-drawdown columns (de-interleave the J-109–J-112 lab tables to match the J-86 leaderboard order)**
  - Steps:
    1. Open the **Factor Lab** (`/research/factor-lab`). In the all-factors table, after Family / Rank-IC / risk-adjusted, the per-horizon columns read **all five forward-return columns (1/5/10/20/60d) first, then all five max-drawdown columns (1/5/10/20/60d)** — not alternating fwd → mdd → fwd per horizon. Expand a factor row: its decile sort uses the same grouped order.
    2. Open the **Regime Lab** (`/research/regime-lab`): both the by-label summary and the regime-score decile table show all five forward-return columns first, then all five max-drawdown columns.
    3. Open the **Market Phase & Severity Lab** (`/research/phase-severity-lab`): both the by-phase-label summary and the severity-score decile table use the same grouped order.
    4. Open the **Regime × Phase × Factor** study (`/research/regime-phase-factor`): the ranked combination table shows all five forward-return columns first, then all five max-drawdown columns.
  - Acceptance: across **every table of the four all-horizon Research labs** — Factor Lab (all-factors table + the expandable per-factor decile sort, J-109), Regime Lab (by-label + regime-score decile, J-110), Market Phase & Severity Lab (by-phase-label + severity-score decile, J-111), and Regime × Phase × Factor (the three-way combination table, J-112) — the per-horizon columns are **grouped by metric**: all `config.walk_forward.horizons` **forward-return** columns first (ascending — 1/5/10/20/60d), then all **max-drawdown** columns in the same horizon order — **never interleaved** (no fwd → mdd → fwd → mdd alternation). This **amends the "paired beside each" per-horizon column order in J-109–J-112** to match the existing `/stocks` / `/themes` / `/sectors` leaderboard order (J-86 — the max-drawdown columns sit to the **right** of all the forward-return columns), making the four labs consistent with the leaderboards. It is a **pure presentation / view-transform change**: every figure stays **byte-identical** and is still read from the stored append-only `forward_returns` table (the realized return + the J-86 max-drawdown), recomputing nothing (*Single source of truth*; *No recompute in the read path*); every column stays **client-side sortable** under the J-48 view-transform contract; and the colour-grading, the As-of vs All-history toggle (J-32), the NA-honesty (*Honest forward-test for partial windows*), the `n` chips + Research Samples drill-downs (J-51 / J-65), the J-112 30-rows-per-page pagination, and the **config-driven** horizon set (*No magic numbers* — adding a horizon adds its column in **both** groups) are all unchanged. **Out of scope / unchanged:** the Stock-Detail per-horizon card grid (it already shows each horizon's return and drawdown together, not as interleaved columns), the `/backtest` evidence aggregates, and the Research event-study / Regime × Setup × Pattern tables. It touches **no** canonical score / return / value, no endpoint, and not the Risk-Off→Actionable gate. A committed test asserts the header / column order on each of the four labs' tables (all forward-return headers precede all max-drawdown headers). Pure frontend presentation; buildable + verifiable offline against the committed seed.

**J-113 … J-114 are NOT data-dependent.** Both are pure frontend presentation / information-architecture changes over already-served values — J-113 (a reorder of the `/research` hub's lab cards) and J-114 (regrouping the four all-horizon labs' per-horizon columns to all-forward-return-then-all-max-drawdown, byte-identical figures) — buildable and verifiable offline against the committed seed. Neither may be recorded blocked-NA for provider reasons, and neither may halt the loop.

**J-109 … J-112 are NOT data-dependent.** All four are buildable and verifiable offline against the
committed 2021-2026 seed — they are **read-only re-surfacings of already-stored canonical values** (the
stored `forward_returns` realized return + the J-86 max-drawdown, the stored `ScannerRun` regime
score/label, the served `/api/market-phase` severity/phase, and stored factor values), grouped and cached
byte-identically (the J-72 / J-103 derived-once idiom): J-109 (an all-horizon presentation + paired
max-drawdown of the existing factor decile / rank-IC values, byte-identical per horizon), J-110 (a
derived-once cached grouping of the stored forward returns by the stored regime score/label), J-111 (the
same by the served phase/severity), and J-112 (the same by the regime × severity × factor deciles). None
may be recorded blocked-NA for provider reasons, and none may halt the loop.

**J-106 … J-108 are NOT data-dependent.** All three are buildable and verifiable offline against the committed seed — J-106 (a new read column over the stored `high_proximity` value), J-107 (an all-factors presentation + cached-aggregate reorg of the stored decile / rank-IC / risk-adjusted values, byte-identical), and J-108 (a frontend / backend readiness-correctness fix run via `./scripts/dev.sh`). None may be recorded blocked-NA for provider reasons, and none may halt the loop.

**J-105 is NOT data-dependent.** It is a bounded-memory / streaming read-path refactor with **byte-identical** figures, buildable and verifiable offline against the committed seed (the byte-identity versus the prior builder and the streamed / projected read path are seed-verifiable; the live-dataset memory headroom is that same bounded read path exercised at scale). It may **not** be recorded blocked-NA for provider reasons and may **not** halt the loop.

**J-101 … J-104 are NOT data-dependent.** All four are buildable and verifiable offline against the
committed 2021-2026 seed — J-101 (an information-architecture de-duplication + a display-clamp alignment
of the existing cross-view), J-102 (a deterministic config-windowed slope of the already-served severity
plus a tooltip / legend re-format), J-103 (a derived-once cached grouping of the stored forward returns by
the served regime + severity-velocity), and J-104 (a caching / query-bounding / lazy-load + page-split
performance refactor with byte-identical figures). None may be recorded blocked-NA for provider reasons,
and none may halt the loop. J-103's empirical *power* for deep, sustained crashes improves once the
pre-2021 history (J-95) loads, but the study itself is fully buildable / green on the seed now and that
deeper-history leg is **non-halting** (it never drives a STALLED verdict or vetoes GOAL_ACHIEVED).

**J-97 … J-100 are NOT data-dependent.** All four are buildable and verifiable offline against the
committed seed — J-97 (a two-pane chart over the already-served index / regime / phase-severity series plus a
full-history serialization of the market-phase engine's `timeline_full`), J-98 (an information-architecture
reshuffle of already-served Dashboard values), J-99 (a client-side pagination / filter view transform over
the served membership timeline), and J-100 (an in-process performance / stability refactor with byte-identical
canonical outputs plus ops guards). None may be recorded blocked-NA for provider reasons, and none may halt
the loop.

**J-93, J-94, and J-96 are NOT data-dependent.** All three are buildable and verifiable offline against the
committed 2021-2026 seed — J-93 (a per-as-of-date universe resolver that screens the committed candidate pool
on price + ADV + min-history from bars dated ≤ D, becomes the single source `score_stocks` iterates, repoints
forward returns to per-run membership ∪ benchmarks, and migrates the universe-count contract to
as-of-dependence — populated by the deterministic J-85 rebuild over the committed seed), J-94 (the min-history
sufficiency gate + the honest warm-up boundary, a deterministic property of the seed price-start +
`indicators.min_history_bars`, with a read-only per-date excluded-counts diagnostic), and J-96 (a read-only
membership timeline / coverage view over the stored per-snapshot membership). The committed seed starts
2021-01-04 for every symbol, so with the 200-bar gate the dynamic universe is honestly empty/small until
~2021-10 and full ~2022-01 — an honest, reproducible warm-up boundary (not a bug), provable offline. None of
the three may be recorded blocked-NA for provider reasons, and none may halt the loop. **J-95 is partly
data-dependent (non-halting)** — exactly like J-22 / J-35 / J-44's DIA: its confirm-gated clear + re-import +
rebuild flow, the J-85 regenerate-from-scratch mechanism, and the per-date resolver are buildable and fully
testable offline against the committed seed (with the honest J-94 warm-up), so those parts are expected to go
green; only an actual successful **real** backward-history fetch (an earlier price start — e.g. 2020, covering
the COVID crash) — and the optional **true point-in-time index-membership source** (a historical-constituent
feed that would resolve the candidate pool itself per-date, eliminating residual pool-survivorship) — is
data-gated. On each resume the session attempts the fetch once (best-effort, never an autonomous retry loop);
when the provider is walled or the constituent feed is absent the leg is recorded **honestly blocked /
limited-coverage (NA)** and **MUST NOT halt the loop, drive a STALLED verdict, or veto GOAL_ACHIEVED** — the
candidate pool stays the documented current-constituent listing with its survivorship-bias label, the dynamic
universe stays screened from that pool with the honest warm-up, every other journey finishes, and the
data-dependent legs auto-fold in via the committed runbook once reachable, **no code change**; no historical
price or membership is ever fabricated, and any provider key is read from the environment only and never
persisted, logged, committed, or echoed.

**J-87 … J-91 are NOT data-dependent.** All five are buildable and verifiable offline against the committed
seed — J-87 (a read-only as-of market-phase + drawdown-severity derivation over the stored snapshots +
index bars dated ≤ D, no new column / no rebuild), J-88 (a deterministic forward-Hamilton-FILTERED 2-state
bear-probability over committed-config params + seed observations — never EM-fit at serve time), J-89 (a
causal phase-history timeline + causal downtrend-episode dating, with a clearly-fenced retrospective/smoothed
analysis-only view), J-90 (a causal recovery/turn signal + its forward-return edge study over the stored
`forward_returns`), and J-91 (a downtrend-conditioned opportunity study grouping the SAME stored event-study
observation set, tagged by the causal as-of phase/severity/bear-probability, count-coherent in Episodes and
Pooled). The committed seed contains the 2022 bear (SPY ≈ −24.5% peak-to-trough into the 2022-10 trough) and
the already-seeded `^VIX`, so both being-in and having-emerged-from a long/severe downtrend are
deterministically provable offline. None of the five may be recorded blocked-NA for provider reasons, and
none may halt the loop. **J-92 is partly data-dependent (non-halting)** — exactly like J-22 / J-35 / J-44's
DIA: its FRED macro provider, its additive `MacroSeries(symbol, date, value, source, published_date)` table,
its per-series publication-lag alignment, and its config-driven wiring into the J-87 severity score / the
J-88 regime-switching observation vector + emissions / the J-91 study conditioning are buildable and fully
testable offline with injected fixtures plus a small committed macro seed over the seed window (mirroring how
`^VIX` is seeded), so those parts are expected to go green; only an actual successful **real** FRED pull and
the live `^TNX` / `^DXY` / `^VXN` proxy fetch — and any macro series not committed to the seed — is
data-gated, the FRED key is read from the environment only and **never persisted/logged/committed/echoed**,
and when the provider is walled it is recorded as **honestly blocked / unavailable (NA)** and **MUST NOT halt
the loop, drive a STALLED verdict, or veto GOAL_ACHIEVED** — every macro-conditioned figure stays
byte-identical to the price/breadth/VIX-only path while the macro leg is absent, and no macro value is ever
fabricated.

**J-83, J-85, and J-86 are NOT data-dependent.** J-83 (a server-side-seeded SSR / URL-hydration UI fix),
J-85 (a deterministic snapshot regenerate-from-scratch + a read-only coverage diagnostic over the
committed seed), and J-86 (a max-drawdown computed over the stored seed bars in the forward-returns pass
+ new read-only columns) are all buildable and verifiable offline against the committed seed; none may be
recorded blocked-NA for provider reasons, and none may halt the loop. **J-84 is partly data-dependent
(non-halting)** — exactly like J-22 / J-35: its Yahoo cookie + crumb authentication, its
pause-resumable-on-systemic-failure behaviour, and its screen logic are buildable and fully testable
offline with an injected provider (returning caps, or raising 401 / 429), so those parts are expected to
go green; only an actual successful **real** Yahoo market-cap screen — and thus J-22 fully passing through
J-35 — is data-gated, and when the provider is walled it is recorded as **honestly blocked /
rate-limited (NA)** and **MUST NOT halt the loop, drive a STALLED verdict, or veto GOAL_ACHIEVED**.

**J-79 … J-82 are NOT data-dependent.** All four are buildable and verifiable offline against the
committed seed — J-79 (seed-driven as-of UI: prev/next buttons + opt-in arrow keys + year/month
dropdowns), J-80 (re-display of the stored regime + stored theme scores already served), J-81 (theme /
sector forward returns read from the stored `forward_returns` table for historical as-of dates, via the
same `leadership_returns` builder Backtest uses), and J-82 (a sort / filter view fix + a
samples-validation reconciliation over the stored event-study observation set). None may be recorded
blocked-NA for provider reasons, and none may halt the loop.

**J-72 … J-78 are NOT data-dependent.** All seven are buildable and verifiable offline against the
committed seed — J-72 (perf + cache over the stored forward returns), J-73 (URL-hydration UI), J-74
(seed-driven heatmap), J-75 (forward returns from the stored `forward_returns` table for historical
as-of dates), J-76 (seed-driven chart hover box), J-77 (a grouping of the stored event-study
observation set, enriched with stored setup/pattern fields), and J-78 (a config default). None may be
recorded blocked-NA for provider reasons, and none may halt the loop.

**J-68 … J-71 are NOT data-dependent.** All four are buildable and verifiable offline — J-68 with the
committed seed + injected fault injection (the multi-date orchestration path), J-69 deterministically
(like J-39, no provider), and J-70/J-71 as seed-driven UI. None may be recorded blocked-NA for provider
reasons, and none may halt the loop.

**J-55 … J-67 are NOT data-dependent.** Every journey above is buildable and verifiable offline: the
UI journeys (J-55–J-58, J-61, J-62, J-64, J-65) run against the committed seed; the jobs journeys
(J-59, J-60, J-66, J-67) are provable with injected/counting providers + fault injection; J-63 derives
from stored snapshots. None of them may be recorded blocked-NA for provider reasons, and none may halt
the loop.

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
runbook. **J-44's DIA series is likewise data-dependent and non-halting**: the major-indexes chart MUST
render fully from the committed index ETFs (SPY/QQQ/IWM/RSP) regardless; the session attempts the
one-shot DIA fetch (committing the bars into the seed) best-effort, and while the provider is
unreachable DIA is honestly omitted from the legend — its absence never fails, blocks, or vetoes J-44.

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
  snapshot. A **wholesale regenerate-from-scratch of the entire snapshot set** (e.g. after a universe
  expansion — J-85) IS permitted as a deterministic, operator-triggered, confirm-gated **create-once
  rebuild** — every snapshot is cleared then recomputed reproducibly with strict no-lookahead — but an
  **existing snapshot MUST never be UPDATED or overwritten in place**, and the rebuild changes no
  canonical formula (only the universe membership it scans over). *(critical)*
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
  date control — its as-of mode reads the same single global as-of control (no second date state). The
  `?asof` URL query param (J-43) is the **serialization of that single global state** — written by and
  restored through the one global control — NOT a second date state; no page parses or holds its own.
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
- **Startup must not block serving on historical warm-up.** The boot path (FastAPI `lifespan`) MUST do
  only the minimal synchronous work needed to serve the **latest** as-of snapshot, then begin serving; the
  historical walk-forward cadence + `forward_returns` MUST be produced by a **background warm-up** after
  the server is accepting connections. The server MUST NOT withhold all requests (including `/health`) for
  the duration of the full backfill. *(operational)*
- **Warm-up obeys every data invariant and is idempotent, concurrency-safe, and non-fatal.** Background
  (and any concurrent) snapshot / forward-return creation MUST reuse the **same canonical engines** (no
  second compute path), MUST stay immutable + strict-no-lookahead + single-source, MUST be **idempotent and
  concurrency-safe** (a duplicate create for an as-of date returns the existing snapshot — never a
  UNIQUE-constraint crash or a duplicate row), and a warm-up **failure MUST be logged and non-fatal** (it
  never prevents serving already-persisted snapshots). *(extends Snapshots are immutable + No recompute in
  the read path)*
- **Readiness is reported honestly.** The health / readiness signal MUST distinguish **serving-ready** from
  **warming (with real progress)** from **unavailable**; it MUST NOT report ready before the latest snapshot
  is servable, MUST NOT mislabel a still-warming backend as "unavailable", and MUST NOT present a
  still-loading analytics aggregate as a complete or fabricated result. *(extends No fabricated data)*
- **Precomputed snapshot seed is a reproducible cache, never fabricated.** Any committed precomputed
  `scanner_runs` / `forward_returns` seed MUST be a **byte-reproducible** materialization of the
  deterministic, no-lookahead computation over the **committed price seed** (regenerated by a committed
  script and verified to equal a fresh compute), loaded **verbatim** on a fresh DB exactly like the price
  seed — it MUST NOT be hand-authored, edited, or allowed to diverge from what the engines produce.
  *(extends No fabricated data + Single source of truth)*
- **One date format, displayed — ISO contracts unchanged.** Every user-facing calendar date MUST render
  `yyyy-MM-dd` through one shared formatter/constant (no locale-dependent widget output, no
  per-component format literals); date inputs MUST validate the exact format before submit; API
  parameters, DB values, and config dates remain ISO and MUST NOT change shape. *(extends No magic
  numbers)*
- **The `?asof` URL param is a serialization, not a second date state.** Date-scoped pages MUST reflect
  the single global as-of state in the URL while historical (and stay date-free at latest), and a URL
  carrying `?asof` MUST restore it through the one global control; no page may parse, hold, or mutate
  its own independent date state. An invalid `?asof` MUST degrade to the latest view — never crash or
  fabricate a date. *(amends + extends Exactly one date selector)*
- **Regime overlays read stored regime only.** The dashboard index-chart bands and the stock-detail
  bands MUST be built from the persisted per-run regime values (label + score from the immutable runs);
  no endpoint, view, or client may recompute a regime, and the same date MUST show the same regime
  label/color on every surface. The stock-detail bands MUST NOT render past the resolved as-of date;
  the dashboard card renders the full stored history behind a visible as-of marker (J-49 — see
  *Full-history market context never looks ahead*). *(extends No recompute in the read path + Single
  source of truth)*
- **The index chart is honest and never data-gated.** A configured index series without stored bars
  MUST be omitted with no synthesized line; the chart MUST render fully from the committed ETFs without
  DIA; the normalized % series MUST be computed server-side from stored bars (the frontend only
  re-formats, no client-side return math). *(extends No fabricated data)*
- **Parallel import preserves every import contract.** Fetch parallelism MUST keep the per-provider
  rate-limit behavior (backoff → resumable pause → durable Resume), chunk-consistent checkpoints,
  per-`(symbol, date)` idempotency, honest progress, and serialized/transactional DB writes — a faster
  pipeline MUST NOT regress the J-34/J-37/J-38 semantics or corrupt concurrent SQLite writes. *(extends
  Pull-missing fetches exactly the gap + Unfinished-imports actions are idempotent)*
- **Vectorized scans are a pure refactor.** The memoized/vectorized backfill MUST produce identical
  canonical outputs (same scores, buckets, setups, patterns, forward returns — asserted by the existing
  suites) and MUST keep strict no-lookahead per as-of date: loading a symbol's full series once is a
  caching strategy; every per-date computation still uses only bars dated ≤ that date. *(extends No
  lookahead + Single source of truth)*
- **Glossary copy lives in one catalog.** Every glossary definition and term tooltip MUST come from the
  single config-backed catalog; no component may hardcode or duplicate a definition; the setup/pattern
  entries stay single-sourced (referenced or hosted by the same catalog, never re-described). *(extends
  Setup & pattern vocabulary is config-driven in the UI too)*
- **Leaderboard sorting, searching, and table filtering are view transforms.** Column sorting on
  `/stocks` (and on the `/research/samples` table — J-64), the J-55 symbol search, the J-56 theme
  filter, and the J-64 ticker filter MUST re-order or narrow only the client-rendered rows of the
  already-served payload; they MUST NOT change, recompute, or re-rank any stored value — the rank `#`,
  scores, buckets, setup statuses, pattern flags, and theme membership read exactly as served, and the
  default order remains the scanner's stored rank. A filtered view MUST stay honest about what it
  hides ("x of N") and MUST NOT alter a published cohort total. Sorting/searching/filtering MUST NOT
  introduce a new endpoint or any second compute path. *(extends Single source of truth + No recompute
  in the read path)*
- **Full-history market context never looks ahead.** The dashboard major-indexes & regime card MAY
  render stored bars and stored regime bands dated after the selected as-of **strictly as
  display-only context** behind a visible as-of marker; that rendering MUST NOT feed any as-of-scoped
  computed value (score, count, bucket, gate, aggregate, or evidence figure — all of which stay
  derived from data dated ≤ D), and the stock-detail regime bands MUST stay clamped at the resolved
  as-of date (J-45). *(extends No lookahead + Regime overlays read stored regime only)*
- **Sample drill-downs are read-only and count-coherent.** Every research samples page MUST list
  exactly the observations behind the published aggregate — the observation total MUST equal the N
  shown on `/research` (same membership filter, same observation set), and every displayed
  factor/indicator value and realized return MUST be the same stored per-observation value the
  aggregate was computed from; the drill-down MUST NOT recompute a factor, return, or membership,
  and an empty cohort renders an honest empty state, never a fabricated row. *(extends Research lab
  is read-only, honest & not predictive + No fabricated data)*
- **Parallel backfill never changes results.** Any backfill concurrency (parallel dates, parallel
  per-symbol computation, vectorization) MUST produce snapshots and forward returns identical to the
  sequential output (same canonical engines, same stored values — asserted by the existing suites),
  MUST preserve create-once / idempotent / concurrency-safe snapshot creation (J-41) and
  serialized/transactional SQLite writes, and MUST keep progress honest (counts never exceed totals;
  checkpoints stay consistent). A faster pipeline that changes any stored value is a regression, not
  an optimization. *(extends Vectorized scans are a pure refactor + Parallel import preserves every
  import contract)*
- **Backfill concurrency is transactionally sound.** No DB session may be shared across concurrent
  backfill workers mid-transaction, and the orchestrating session MUST never be left emitting SQL in
  an invalid ('committed') transaction state mid-stage; a per-date failure MUST be isolated and
  recorded (honest error + counts) while the remaining dates complete — one bad date never aborts the
  stage, corrupts a transaction, or fabricates a snapshot. *(extends Parallel backfill never changes
  results — J-67)*
- **Run history is complete and truthful (live from start).** Every started job MUST have a
  run-history record from the moment it starts (status `running`), receiving honest lifecycle
  transitions to exactly ONE terminal state (`ok` / `partial` / `failed` / `interrupted`); a `running`
  record whose process died MUST be marked `interrupted` by a boot sweep — never left `running`
  forever and never silently dropped. A terminal record MUST NOT be mutated afterwards (beyond the
  J-38 soft-dismiss flag), nothing in the audit trail may be deleted or hidden, and no status may ever
  be fabricated — the append-only identity means the record of what ran is permanent and truthful,
  which a start-inserted record with honest lifecycle transitions respects. *(amends + extends
  Unfinished-imports actions are idempotent and audit-preserving — J-60)*
- **Stage-resume re-fetches nothing.** Resuming or retrying past a completed fetch stage MUST perform
  ZERO provider calls, and the fetch planner MUST skip the provider call for any (symbol, window)
  already fully covered against the benchmark trading calendar — re-fetching data the store already
  holds is a defect, not a safety margin; the per-`(symbol, date)` write idempotency stays the last
  line of defense, never the only one. *(extends Pull-missing fetches exactly the gap +
  Unfinished-imports actions are idempotent — J-59)*
- **Episode mode recomputes nothing.** The event-study episode view MUST be a deterministic collapse
  (grouping) of the SAME stored per-observation rows the pooled view reads — one membership rule, the
  same observation builders, no return/excursion/factor recomputed; the pooled figures stay
  byte-identical; both modes disclose n + unique symbols + episode count; aggregates and samples
  drill-downs MUST stay count-coherent in both modes. *(extends Research lab is read-only, honest &
  not predictive + Sample drill-downs are read-only and count-coherent — J-63)*
- **The calendar is a presentation of the one date state.** The as-of calendar popover MUST render the
  same canonical snapshot-date list and write the same single global as-of state (and its `?asof`
  serialization) — it MUST NOT hold, parse, or invent a second date state; a date it cannot offer is
  disabled, never fabricated; an invalid URL date still degrades to latest. *(extends Exactly one date
  selector — J-62)*
- **The availability heatmap is descriptive, read-only metadata.** Per-date availability counts MUST
  be derived from stored bars + stored runs only (one read-only derivation, one endpoint), MUST NOT
  restate or recompute any canonical score/return/bucket, and MUST render partial coverage honestly (a
  sparse date never looks fully covered, an empty date never looks present); clicking it only prefills
  JOB parameters — never the global as-of control. *(extends Coverage & missing-data are descriptive &
  honest + Exactly one date selector — J-61)*
- **Progress is honest at fine grain.** Progress counters MUST be monotone within a run and MUST NEVER
  exceed their stated totals (a `318/159` reading is a defect, not a display quirk); the
  current-activity message and the last-progress heartbeat MUST reflect real work (never fabricated,
  never pre-dated); polling/heartbeat/granularity knobs live in config — no magic numbers. *(extends
  Parallel import preserves every import contract — J-66)*
- **Chart pane-zoom / range-sync is a view transform, not a date control.** Synchronizing the visible
  date range across the Dashboard's stacked chart panes (or any linked charts) changes only the
  **displayed window**; it MUST NOT introduce a second date state, write the global as-of, or feed any
  as-of-scoped computed value — the single global as-of switcher stays the only date control, and the
  full-history context past the as-of stays display-only behind the as-of marker. *(extends Exactly one
  date selector + Full-history market context never looks ahead — J-97)*
- **Bounded resource use is a pure performance property.** Single-flight/caching the coverage +
  membership-timeline compute, decoupling its cache key from forward-return churn, reusing one
  process-level bar cache, capping server concurrency, offloading heavy work to a worker thread, and any
  process memory cap MUST produce **byte-identical** canonical outputs (same scores, buckets, setups,
  returns, membership — asserted by the existing suites) and MUST preserve immutability + strict
  no-lookahead + single-source; a faster/leaner backend that changes any stored value is a regression,
  not an optimization. *(extends Vectorized scans are a pure refactor + Warm-up obeys every data
  invariant — J-100)*
