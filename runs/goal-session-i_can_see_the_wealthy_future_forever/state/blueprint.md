# App Blueprint — i_can_see_the_wealthy_future_forever (Trendora)

<!--
Coherence contract for the whole app. Drafted by the goal-decomposer at baseline; you approve it once
(edit anything, then `--resume`); the coherence-auditor enforces it every iteration.

WHAT THIS SESSION IS. It continues the same Trendora codebase the prior session
`i_can_see_the_wealthy_future` built to GOAL_ACHIEVED for J-01..J-16 (every one of those surfaces is
present in the tree — verified by file-scan). `docs/goal.md` now adds three more must-have journeys:
J-17 Data Manager (`/data`), J-18 unified as-of date control, J-19 return attribution.

BASELINE FILE-SCAN FINDING (the real remaining work). Despite commit 043a456's message ("add Data
Manager, unified as-of date control, and return attribution"), those changes are NOT in the working
tree:
  - J-17 Data Manager — ABSENT: no `apps/frontend/app/data/page.tsx`, no `apps/backend/app/api/data.py`,
    no data-manager engine module, no `data`/`data_manager` section in `config.yaml`.
  - J-18 unified as-of — NOT satisfied: `apps/frontend/app/backtest/page.tsx` still has its OWN
    `BacktestDatePicker`, explicitly "independent of the global top-bar switcher" (the duplicate date
    control J-18 forbids).
  - J-19 attribution — ABSENT: no per-stock contribution / by-sector / by-rank-band / distribution /
    hit-rate code in `forward_testing.py`, `/system-health`, or `/backtest` (the term "attribution"
    appears only as a charting-library credit in `price-chart.tsx`).
The iter-0 baseline will formally confirm this; the goal-evaluator (not the decomposer) records the
pass/fail. So J-01..J-16 below carry REAL, verified `app.engine.*` / `GET /api/*` names; J-17/18/19 are
the TARGET contract (convention-named) that iter-1+ must build/verify to.

REVIEW CHECKLIST (before you resume):
  1. Information Architecture — does every journey have a home reachable in <=2 clicks? Stock Detail and
     Run Detail are intentionally row-reached, not top-nav. `/data` is the new home for J-17.
  2. Data Contract — is every "same-number-everywhere" value listed with ONE computing module and ONE
     serving path? The six canonical scores + A-E bucket + setup status are the J-06 criticals. The
     J-17/18/19 rows are proposals — rename if you prefer a different layout, then iter-1+ builds to match.
  3. J-18 specifically requires DELETING the Backtest page's own date picker so the single global
     switcher drives it — confirm that direction.
-->

## Information Architecture

**Layout shell:** Left persistent sidebar (nav) + main content area — a dense, dark analytical
workstation. Numbers are monospace/tabular; every score shows its **A–E bucket first, raw 0–100
secondary**. Single mobile breakpoint ~640px (wide tables scroll horizontally). The backend is the
single source of truth; every page only re-formats server-computed values and never recomputes a
score, bucket, or return.

A single global **as-of date switcher** in the top bar must be the **only** date control (J-18). It
re-points Dashboard, Stocks, Themes, Sectors, Stock Detail, **and Backtest** to a chosen past snapshot
(default: latest); its options read the canonical `GET /api/runs`. **J-18 (resolved iter-1, re-confirmed
iter-3):** `/backtest` reads only the global switcher — its page-local `BacktestDatePicker` was removed;
the frontend holds no second, independent date state.

**Navigation skeleton** (the persistent sidebar — every feature lives under one of these):

```
Trendora
├── Dashboard        /                       (J-01)                          [built]
├── Stocks           /stocks                 (J-02, J-06, J-16 VCP filter, J-28 pattern filters)  [built; J-28 filters iter-9]
│   └── Stock Detail /stocks/[ticker]        (J-05, J-06, J-16, J-28 pattern badges)  [built; J-28 badges iter-9]  — row-reached, not top-nav
├── Themes           /themes                 (J-03)                           [built]
├── Sectors          /sectors                (J-04)                           [built]
├── Scanner Runs     /scanner-runs           (J-08)                           [built]
│   └── Run Detail   /scanner-runs/[runId]   (J-07, J-08)                     [built]  — row-reached
├── Backtest         /backtest               (J-14, J-18, J-19 per-date)      [built]
├── System Health    /system-health          (J-09, J-10, J-16 by-VCP, J-19 aggregate, J-28 by-pattern)  [built; J-28 by-pattern iter-9]
├── Watchlist        /watchlist              (J-11)                           [built]
├── Methodology      /methodology            (J-12, J-28 new-pattern glossary entries)  [built; J-28 entries iter-9]  — config-backed glossary; feeds inline tooltips
├── Data Manager     /data                   (J-17)                           [built iter-3]  — additive sidebar entry
└── Research         /research               (J-25 Factor Lab [iter-10]; J-26, J-27, J-29, J-30, J-31 planned)  [building iter-10 — Factor Lab; nav APPROVED, re-approval pause cleared iter-10]
```

Legend: [built] = present in the tree; ⚠ = present but violates the contract (fix needed); ⛔ = not built.

**Nav-skeleton change (iter-9):** the `/research` top-level entry is ADDED to the skeleton as the planned canonical home for the compute-only analysis labs (J-25–J-31). Its approval is **front-loaded** — `blueprint.reapproval-requested` is written this iteration so `run-goal.sh` pauses for human approval at the *start of iter-10*, before the first lab is built under it. **iter-9 itself builds no `/research` code** (its target J-28 rides existing homes). The labs are cross-date aggregate views (like System Health), not a per-date drill-down.

**Nav-skeleton update (iter-10):** the front-loaded `/research` approval pause has **CLEARED** (the `blueprint.reapproval-requested` marker is consumed/removed) — `/research` is an **APPROVED** home. iter-10 builds the FIRST lab under it: **J-25 Factor Lab** (decile sort + rank-IC per factor, raw + downside-risk-adjusted). This is an additive page under the approved section — **no new `blueprint.reapproval-requested` marker is written**. The Factor Lab is a cross-date aggregate (like System Health): it has **no date control** (J-18 preserved — only factor + horizon selectors). J-26/J-27/J-29/J-30/J-31 remain planned `/research` iterations that reuse this iteration's page + the read-only lab-analytics seam.

**Feature / journey homes** (each reachable in ≤2 clicks from the sidebar):

| Journey | Canonical home (route) | Status |
|---|---|---|
| J-01 Daily dashboard at a glance | `/` | built |
| J-02 Stock Leaderboard + working filters | `/stocks` | built |
| J-05 Stock Detail with explainable scores | `/stocks/[ticker]` (row → detail) | built |
| J-06 Score consistency across pages | `/stocks` ↔ `/stocks/[ticker]` | built |
| J-03 Theme Leaderboard | `/themes` | built |
| J-04 Sector / industry Leaderboard | `/sectors` | built |
| J-08 Immutable scanner-run history | `/scanner-runs` | built |
| J-07 Risk-Off regime suppresses Actionable | `/scanner-runs/[runId]` (row → detail) | built |
| J-13 Browse dashboard as of a past date | global as-of switcher (top bar) | built |
| J-14 Backtest a past date + per-date forward-test scorecard | `/backtest` | built |
| J-15 Fast page loads from persisted snapshots | cross-cutting (`snapshot_serving`) | built |
| J-09 System Health forward-tested evidence | `/system-health` | built |
| J-10 Control-group honesty (selection vs sector beta) | `/system-health` | built |
| J-11 Watchlist with persistence | `/watchlist` | built |
| J-12 Setup/pattern glossary + inline explanations | `/methodology` | built |
| J-16 VCP detected/explained/filterable/forward-tested | `/stocks`, `/stocks/[ticker]`, `/methodology`, `/system-health` | built |
| J-18 One date control (no duplicate) | `/backtest` driven by the global switcher | built (iter-1; re-confirmed iter-3) |
| J-19 Diagnose weak returns via attribution | `/system-health` (aggregate) + `/backtest` (per-date) | built iter-2 |
| **J-17 Grow the dataset by date / range** | `/data` | **built iter-3** (blueprint-approved home; additive sidebar entry) |
| **J-20 Full chart path through latest (display-only, as-of marker)** | `/stocks/[ticker]` (existing home; row-reached) | **built iter-6** — chart extension only (`?through=latest` opt-in + as-of divider/forward-region label); no new surface |
| **J-21 Backtest leadership cohorts below attribution + horizon-linked realized returns** | `/backtest` (existing home) | **built iter-6** — section reorg (lists below Return Attribution) + read-only return columns driven by the one lifted horizon view-selector; no new surface |
| **J-22 Transparent, rule-based, expanded universe (~500 names)** | `/methodology` (Universe Selection rule) + `/data` (grown coverage count) — existing homes | **GATED — runbook pending a reachable no-key feed (re-confirmed iter-8).** iter-7: code/UI/pool built + tested; expansion fetch GATED on Yahoo 429. iter-8: the mandated single polite re-probe at dispatch **re-walled** (Yahoo HTTP 429 on BOTH no-key halves — chart/OHLCV + cookie+crumb/market-cap) → per the probe-gate + *No fabricated data* anti-goal the screen+ingest did NOT run; nothing fabricated, no file changed; universe stays 122. The committed finish runbook (`screen_universe.py --screen` → `apply_universe_to_config.py` → re-verify Risk-Off bootstrap dates → regenerate db → full pytest once → commit seed) **auto-heals with zero code change** the moment the operator confirms a reachable no-key egress — do NOT autonomously retry. No new surface, no nav change. `/methodology` Universe-Selection section + `/data` `universe_count` serve the SAME resolved universe; the honest gate keeps the section suppressed until a real `data/seed/universe.json` exists. Expansion is real committed data only — never fabricated. |
| **J-28 More detected patterns beyond VCP (forward-tested)** | `/stocks` + `/stocks/[ticker]` (filter + badges) + `/methodology` (config-backed glossary) + `/system-health` (pattern-vs-non-pattern breakdown) — existing homes | **iter-9 target.** Compute-only over the stored seed (no fetch — NOT data-walled); rides existing homes; needs no `/research` home and no blueprint re-approval (the goal's J-28 acceptance allows the breakdown on "the Setup & Pattern Lab **or System Health**"). Adds ≥2 config-driven detectors (`pullback_to_rising_dma`, `flat_base_breakout`) following the VCP "pattern-not-status" contract. No new surface, no nav change. (Evaluator records pass/fail.) |
| **J-25 Factor Lab — decile sort + rank-IC per factor (raw + risk-adjusted)** | **`/research`** (the APPROVED new nav home — first lab) | **iter-10 target.** Compute-only over the stored seed (no fetch — NOT data-walled). NEW page/route/nav home under the approved `/research` section + NEW read-only lab-analytics seam (`app.engine.research:compute_factor_lab`, served by `GET /api/research/factor-lab`). Reads stored factor values (typed `leadership/entry_quality/risk_score` columns + named component `raw`s in `record_json`) joined to stored `forward_returns` — recomputes no factor/return (the SAME observation pool `compute_forward_aggregates` uses). Decile table (raw mean + downside-risk-adjusted + `n`) + Spearman rank-IC; honest NA below `walk_forward.min_sample`; survivorship-bias + descriptive-not-predictive labels. **Cross-date aggregate — NO date control (J-18 preserved).** Decile count + factor catalog from `config.research.factor_lab` (No magic numbers). (Evaluator records pass/fail.) |

<!-- NEW WAVE (J-20..J-31, added to docs/goal.md after the J-01..J-19 GOAL_ACHIEVED).
     iter-6: opened the two that refine EXISTING homes (J-20 `/stocks/[ticker]`, J-21 `/backtest`) — no nav change.
     iter-9: builds J-28 (more detected patterns) on EXISTING homes (`/stocks`, `/stocks/[ticker]`, `/methodology`,
             `/system-health`) — no nav change; AND front-loads the `/research` nav re-approval (skeleton entry + marker).
     iter-10: `/research` approval pause CLEARED (marker consumed) → builds the FIRST lab under the approved home —
             J-25 Factor Lab (`/research`: decile + rank-IC, raw + downside-risk-adjusted; new `app.engine.research`
             read-only seam + `GET /api/research/factor-lab` + `config.research.factor_lab`). Additive page under the
             approved section — NO new marker. Cross-date aggregate, NO date control (J-18). The seam J-26/J-27/J-29/J-30/J-31 reuse.
     Remaining wave members and their homes:
       - J-22 ~500-name universe → `/methodology` (+ `/data`) — existing homes. GATED on Yahoo 429 (external).
       - J-23/J-24 multi-timeframe bars + chart timeframe selector → `/stocks/[ticker]` — existing home. DATA-WALLED (external).
       - J-25/J-26/J-27 Factor Lab, J-29 Setup & Pattern Lab, J-30 volatility family → the NEW `/research` sidebar home.
       - J-31 synthesis → cross-page (labs → leaderboard filter → detail).
     The `/research` home is a NAV-SKELETON addition. Per agent rules it is added to the skeleton AND a
     blueprint.reapproval-requested marker is written when the labs are about to be built. iter-9 writes that
     marker NOW (front-loaded, NOT iter-10) so the human approves `/research` at iter-10's pre-decomposer pause —
     i.e. BEFORE the first lab is built under it (correct gate placement; the marker pauses the NEXT iteration's
     pre_decomposer, run-goal.sh:804). iter-9 itself builds NO `/research` code. -->


## Data Contract

Every value below is computed **once** by the scoring / regime / forward-testing engine during a scan
(or the forward-returns / data-manager job), **stored** on a snapshot table, and only re-formatted by
the API/UI. Read endpoints serve canonical values from the **persisted immutable snapshot for the
resolved as-of date** — they do NOT recompute per request; the frontend never recomputes a score,
bucket, or return. Engine modules live under `apps/backend/app/engine/` (confirmed present: `regime`,
`sectors`, `themes`, `scoring`, `buckets`, `setups`, `patterns`, `indicators`, `prices`, `scanner`,
`forward_testing`, `methodology`, `labels`, `normalize`, `snapshot_serving`).

| Canonical value | Computed once by (single module/function) | Served by (canonical endpoint) | Status / notes |
|---|---|---|---|
| Market Regime score (0–100) + label (6), breadth %, net new-high/low | `app.engine.regime:score_regime` | `GET /api/runs/{run_id}`, `GET /api/dashboard` | built. breadth + new-high/low are **universe-relative** (honest limitation). |
| Candidate counts (#Actionable / Breakout / Pullback) + last-scan ts | `app.engine.setups:summarize_candidates` | `GET /api/dashboard` | built. counts the canonical setup statuses; never recomputed. |
| Sector / industry score (+ RS-vs-SPY, dist-52w-high, trend) | `app.engine.sectors:score_sector` | `GET /api/sectors` | built. SPY = 0% RS reference, not ranked vs itself. Dashboard "Top Sectors" slices this. |
| Theme score (+ members, 1m/3m basket return, breadth, trend) | `app.engine.themes:score_themes` | `GET /api/themes` | built. price-confirmed. Dashboard "Top Themes" slices this. |
| Leadership / Entry Quality / Risk (per stock) | `app.engine.scoring:score_stocks` | `GET /api/stocks` (list) **and** `GET /api/stocks/{ticker}` (detail) | built. leaderboard & detail read the **same** stored row → J-06. Never collapsed into one "buy" number. |
| A–E bucket | `app.engine.buckets:to_bucket` (config edges) | rides on each score | built. derived once; never re-derived in API/UI. |
| Setup status (per stock) | `app.engine.setups:classify_setup` | rides on the stock rows | built. Actionable / Pullback-watch / Breakout-watch / Extended / Avoid / Risk-off-watchlist. **Risk-Off ⇒ zero Actionable** (J-07). |
| Score component breakdown + reason + invalidation | `app.engine.scoring:score_stocks` (invalidation MA from `decision_rules.invalidation`, via `indicators:sma`) | `/api/stocks` + `/api/stocks/{ticker}` | built. engine emits structured level + human note; frontend renders verbatim; NA when MA not computable. |
| Theme membership (per stock) | `app.engine.scoring:score_stocks` from the `config.themes` map | `/api/stocks` + `/api/stocks/{ticker}` | built. one source = config theme map; chips link to `/themes`. |
| Detected pattern — **VCP** flag (+ pivot/invalidation/reason) | `app.engine.patterns:detect_vcp`, composed on the row by `score_stocks` (price+volume, ≤ D) | `/api/stocks` + `/api/stocks/{ticker}`; mirror col `scanner_results.is_vcp` for `by_vcp` | built. **SEPARATE from setup status** — never promotes Actionable (*VCP-is-a-pattern-not-a-status* critical). `/stocks` filter is client-side re-display. |
| Detected pattern — **`pullback_to_rising_dma`** flag (+ pivot/invalidation/reason) — J-28 | `app.engine.patterns:detect_pullback_to_rising_dma`, composed on the row by `score_stocks` (price+volume, ≤ D); thresholds from `config.patterns.pullback_to_rising_dma` (incl. `ma_period` ∈ `indicators.ma_periods`) | `/api/stocks` + `/api/stocks/{ticker}`; mirror col `scanner_results.is_pullback_to_rising_dma`; `by_pullback_to_rising_dma` breakdown on `/api/system-health`; catalog entry via `methodology:build_catalog` | **iter-9 target.** **SEPARATE from setup status** — never promotes Actionable (*New-patterns-are-patterns-not-statuses* — reaffirms the VCP critical). Computed once per run, ≤ D (no-lookahead), stored on the immutable snapshot, read verbatim everywhere (single source / no recompute). `/stocks` filter is client-side re-display; forward breakdown reads the stored mirror, never re-detects; cohort < `walk_forward.min_sample` shows `n`+NA. NOT a second computation of any existing score/return/bucket. (Evaluator records pass/fail.) |
| Detected pattern — **`flat_base_breakout`** flag (+ pivot/invalidation/reason) — J-28 | `app.engine.patterns:detect_flat_base_breakout`, composed on the row by `score_stocks` (price+volume, ≤ D); thresholds from `config.patterns.flat_base_breakout` | `/api/stocks` + `/api/stocks/{ticker}`; mirror col `scanner_results.is_flat_base_breakout`; `by_flat_base_breakout` breakdown on `/api/system-health`; catalog entry via `methodology:build_catalog` | **iter-9 target.** **SEPARATE from setup status** — never promotes Actionable (*New-patterns-are-patterns-not-statuses*). Computed once per run, ≤ D (no-lookahead), stored on the immutable snapshot, read verbatim everywhere. `/stocks` filter is client-side re-display; forward breakdown reads the stored mirror, never re-detects; cohort < `walk_forward.min_sample` shows `n`+NA. NOT a second computation of any existing value. (Evaluator records pass/fail.) |
| Price / MA / volume series (per ticker, as-of) | bars `prices:bars_asof` (≤ as-of); MAs `indicators:sma`/`sma_series` over `config.indicators.ma_periods` | `GET /api/stocks/{ticker}/bars` | built. frontend plots the **server** MA series; latest 50-DMA == scoring 50-DMA == invalidation level. **iter-6 (J-20): built.** the chart renders the full path **through the latest seed date** via `prices:bars_through_latest` behind the opt-in `?through=latest` on the SAME endpoint (default contract stays ≤ D, byte-identical), exposing the as-of boundary (`latest_date` + per-bar `is_forward`) so the chart shades/labels the post-D region with an as-of divider marker. post-D bars + MA are **DISPLAY-ONLY** visualization — they do NOT feed any score/bucket/setup/VCP/factor/ranking (those stay on the snapshot row, bars ≤ D; the helper is referenced only by the chart endpoint, never the scoring path — source-asserted). NOT a new canonical value. *(No-lookahead chart carve-out, critical)* |
| Setup & pattern catalog (meaning + config thresholds + example) | `app.engine.methodology:build_catalog(config)` (live values resolved from canonical config) | `GET /api/methodology` | built. ONE source for `/methodology` + every inline `/stocks` tooltip + the setup-filter vocabulary; unresolvable ref → `ConfigError` at boot. |
| Scanner run snapshot (immutable as-of run: list + detail) | `app.engine.scanner:run_scan` (calls each engine once per date; recomputes nothing) | `GET /api/runs`, `GET /api/runs/{run_id}` | built. append-only `scanner_runs`/`scanner_results`(+`sector_scores`,`theme_scores`); bars ≤ D. *(Snapshots-immutable + No-lookahead critical)* |
| Snapshot-served reads + resolved as-of date / available dates | `app.engine.snapshot_serving` (+ as-of resolution in `scanner`, create-once) | available: `GET /api/runs`; resolved `asof_date` echoed by every re-pointed read endpoint | built. **one** date source (J-13/J-15). "viewing as-of D (historical)" = resolved ≠ latest. |
| Forward-return aggregates (by bucket / setup / regime / **VCP**; excess vs SPY/QQQ/sector; control groups) | `app.engine.forward_testing:compute_forward_aggregates` | `GET /api/system-health` | built. post-snapshot bars only; each cell carries `n`; labelled survivorship-biased. Stored in append-only `forward_returns`. |
| Per-date forward-test scorecard (per-horizon return, excess, control groups) | `app.engine.forward_testing:compute_run_scorecard` (READS stored `forward_returns` + `scanner_results` verbatim); create-once `backfill_run_forward_returns` (INSERT-only) | `GET /api/backtest` | built. same stored rows `/api/system-health` aggregates — one source, two read paths. As-of scan summary reuses `/api/dashboard|sectors|themes|stocks?as_of=`. NA per horizon when short. |
| Watchlist entry (date-added, reason, current score/setup/invalidation, price-since-added) | current scores READ live from `scoring:score_stocks` (latest); price-since via `prices:close_on` | `GET /api/watchlist` (`POST` add, `DELETE` remove) | built. user-mutable `watchlist` table (survives restart → J-11). Stores only `{ticker, reason, created_at, asof_date_added, entry_close}`; scores read at serve time (single source). Not a snapshot; not an order. |
| **Forward-return attribution slices** (per-stock contributors/detractors, by-sector, by-rank-band, distribution/hit-rate; with `n`) — J-19 | `app.engine.forward_testing` shared attribution helper — **derived once** from the SAME per-observation `stock_obs` list (`forward_returns` ⋈ `scanner_results` sector/rank/bucket, read verbatim) that `compute_forward_aggregates` / `compute_run_scorecard` already build; recomputes no return. Rank-band edges + list size from `config.walk_forward.attribution.{rank_bands, top_contributors_k}` | `GET /api/backtest` (per-date, inside each `by_horizon` entry) **and** `GET /api/system-health` (aggregate, keyed to the selected `horizon`) — existing endpoints, no new surface | **built iter-2.** *Attribution is read-only* — never recompute returns to build a slice; consistent with the existing aggregate mean (same observations: by-sector/by-rank-band `n`s sum to `overall.n`, distribution mean == `overall.mean_return`); low-sample/empty slices show `n`/NA. (Evaluator records pass/fail.) |
| **Backtest leadership realized returns** (per sector = sector-ETF return; per theme = equal-weight member-basket return; per cohort stock = its own return; per horizon) — J-21 | `app.engine.forward_testing:_leadership_returns` — a shared **read-only projection** (takes no Session, issues no query, recomputes no return) over the SAME `ret_by_symbol` dict the scorecard already built from the stored `forward_returns`: sector = the ETF's own stored return (`cfg.etfs.sector`); theme = equal-weight mean of member stocks' stored returns over members that HAVE a return (config theme map); cohort = the symbol's own stored return (keyed by `cfg.universe.symbols`). **Recomputes no return.** | `GET /api/backtest` (existing endpoint; rides each `scorecard.by_horizon[*]` entry as `leadership_returns`) | **built iter-6.** *Attribution is read-only* — a read-only slice of the existing forward-returns value, NOT a second computation and NOT a new endpoint. The three lists now render BELOW Return Attribution and the existing horizon **VIEW** selector (lifted to page level) re-points their return columns (no second date state → J-18 preserved). NA/null honestly when a (row, horizon) lacks post-bars; nothing fabricated. (Evaluator records pass/fail.) |
| **Dataset coverage + fetch/backfill job** (price range, symbol count, snapshot dates, gaps; async progress + run history) — J-17 | `app.engine.data_manager:compute_coverage` (read-only coverage/gaps over `DailyPrice`+`ScannerRun`) + `app.engine.data_manager:run_data_job` which ORCHESTRATES the existing canonical create-once paths `scanner.run_scan` + `forward_testing.backfill_run_forward_returns` (no second scan/return math) and the **config-selected live provider** `app.data_providers.stooq_provider.StooqProvider` (real EOD only) for new trading days | `GET /api/data` (coverage + run history), `POST /api/data/jobs` (start job → `{job_id}`), `GET /api/data/jobs/{job_id}` (live status) | **built iter-3.** async in-process job + live progress (in-memory registry) + final summary persisted to append-only `DataProviderRun`. Coverage/gaps/progress are NEW descriptive values (not duplicates of any canonical score/return); backfill reuses the registered `scanner.run_scan`/`forward_testing.backfill_run_forward_returns` (no second computation path). Provider failure → explicit error, **never fabricated prices** (*Live fetch is real-data-only* critical). Range backfill is create-once/immutable/lookahead-free. The `/data` date inputs are **job parameters, not a viewing as-of control** (J-18 preserved). Default boot stays the committed offline seed. `data_manager` config block holds any tunables (no magic numbers). |

| **Universe membership + selection screen** (resolved member set; the screen rule + `min_market_cap`/`min_dollar_vol`/`min_price` thresholds; resolved size; per-member screen-pass reference values: market cap, ADV, price, sector) — J-22 | Resolved **once, offline, at seed-build time** by the screen+ingest step (`ingest_seed.py`/sibling): a documented committed candidate pool (membership rule) screened by `config.universe.filters` against REAL fetched data (Yahoo, no-key). The result is the committed `config.universe.symbols` + `config.stock_sectors` + per-member `Stock.market_cap` (populated at `seed_loader`) + a committed screen record (`meta.json`/`universe.json`). The running app **reads** this; it never recomputes membership or market cap. | Screen **rule + thresholds + resolved size**: `GET /api/methodology` (thresholds resolved live from `universe.filters` via the `ref` mechanism). Member **count + coverage**: `GET /api/data`. Both read the **same** resolved universe. | **GATED — runbook pending a reachable no-key feed (re-confirmed iter-8). iter-7: serving code built + tested; fetch GATED on Yahoo 429. iter-8: the dispatch-time re-probe RE-WALLED (Yahoo 429 on both no-key halves) → the screen+ingest did NOT run, universe stays 122, nothing fabricated, no file changed. The committed finish runbook auto-heals with zero code change on operator confirmation of a reachable egress — do NOT autonomously retry.** `GET /api/methodology` serves the Universe-Selection section (thresholds live from `universe.filters` via `ref`; resolved size = `len(config.universe.symbols)`) and `GET /api/data` serves `universe_count` from the SAME one universe (single source, no recompute — tested). `Stock.market_cap` is populated read-only from the committed screen record. *Universe screen is reproducible & honest* — config-recorded screen, **no hand-curated list masquerading as a screen**; the committed candidate pool (S&P 500 ∪ Nasdaq-100 ∪ prior, real Wikipedia constituents) + the screen+ingest pipeline are built; expansion is real committed data only (**no fabricated history**; the offline OHLCV/market-cap fetch remains externally blocked — Yahoo 429 re-confirmed iter-8 — and runs via the committed runbook only when a reachable no-key feed is confirmed; never synthesized). Not a second computation of any existing score/return/bucket. Breadth + walk-forward labels stay **universe-relative / survivorship-biased**. Date grid unchanged (only universe width grows). *(Evaluator records pass/fail.)* |

| **Factor-Lab analytics** (per factor × horizon: decile mean forward return + downside-risk-adjusted column + Spearman rank-IC, each with `n`) — J-25 | `app.engine.research:compute_factor_lab` — a READ-ONLY aggregation derived ENTIRELY from the stored per-observation `forward_returns.realized_return` joined to the stored factor value on `ScannerResult` (a typed score column `leadership_score`/`entry_quality_score`/`risk_score`, OR a named component `raw` parsed from `record_json` at the config-declared `source` path, e.g. `leadership.components.rs_spy_3m.raw`) — read VERBATIM. Recomputes NO factor and NO return; takes the SAME observation pool as `forward_testing.compute_forward_aggregates`. Decile count + factor catalog + each factor's source/direction/family come from `config.research.factor_lab`; the low-sample honesty threshold is reused from `walk_forward.min_sample`. Risk-adjusted = `mean_return / downside_deviation` (downside semideviation about 0 — never total volatility). | `GET /api/research/factor-lab` (the SINGLE canonical lab endpoint; no other path computes deciles/rank-IC) | **iter-10 target.** *Research lab is read-only, honest & not predictive* — derived once from stored returns + stored factor values; the API/frontend recompute nothing; low-sample cells show NA + `n`; survivorship-bias + descriptive-not-predictive labels carried. **NOT a duplicate:** the factor *values* keep their canonical home (`scoring:score_stocks` → `scanner_results`/`record_json`) and the realized *returns* keep theirs (`forward_testing` → `forward_returns`); this row registers only the NEW descriptive decile/IC aggregation over them (exactly as the J-19 attribution row registers read-only slices of the same stored returns). Cross-date aggregate — **NO date control** (J-18). Consistency invariant: pooled mean of all observations at horizon h == `compute_forward_aggregates(h).overall.mean_return` (same observation set). (Evaluator records pass/fail.) |

Health probe: `GET /api/health` → `{"status":"ok", ...}` (no canonical value).

## Coherence invariants (the auditor hard-fails on these)

1. **Single source of truth** — the six scores + A–E bucket + setup computed once; API/frontend never recompute; same symbol reads identically across pages (J-06). *(critical)*
2. **No recompute in the read path** — read endpoints serve persisted-snapshot values for the resolved as-of date; create-once on first view is the only blessed compute. *(critical)*
3. **Snapshots immutable** — `scanner_run` + result rows never mutated; `forward_returns` is a separate append-only table. *(critical)*
4. **No lookahead** — as-of-D snapshot uses only bars ≤ D; forward returns only bars > D; unit-tested. *(critical)*
5. **Exactly one date selector** — a single global as-of control drives every date-scoped page incl. Backtest; no second date state. (J-18 resolved iter-1; re-confirmed holding iter-3.) *(critical)*
6. **Detected patterns are patterns, not statuses** — VCP and every new detected pattern (J-28: `pullback_to_rising_dma`, `flat_base_breakout`) ride as separate flags computed once per run (price+volume, ≤ D, config thresholds); none enters the setup-status enum or promotes Actionable alone. *(critical)*
7. **Risk-Off gates Actionable** — zero Actionable in a Risk-Off regime. *(critical)*
8. **No fabricated data** — provider failure (incl. Data Manager live fetch) surfaces an explicit error; never synthesize prices/scores; partial forward-test horizons show NA + `n`. *(critical)*
9. **Attribution & lab analytics are read-only** — attribution slices (J-19) AND Factor-Lab/research analytics (J-25+: decile means, rank-IC, risk-adjusted) are derived from stored per-observation forward returns + stored factor values; the API/frontend never recompute a return or factor to build them; risk-adjusted figures use downside volatility / MAE (never total volatility); low-sample cells show NA + `n`.
10. **No magic numbers** — weights/thresholds/edges/universe/themes/provider/walk-forward params from `config.yaml`.
11. **No order/execution path** — research-only; no brokerage/order/capital-deployment code reachable. *(critical)*
12. **Every feature navigable** from the sidebar; no second home for an existing entity.
