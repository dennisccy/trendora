# trendora

<!-- AUTO:capabilities -->
## What it does

Trendora is a local-first, research-only US equity leadership scanner and decision-support platform. It produces a daily ranked view of the market — from market regime down through sectors, industry groups, themes, and individual stocks — and never places orders or holds broker keys.

Current capabilities:

- **Today page**: an evening briefing view that shows at a glance the current market state, a summary of the day's moves, what changed since the previous session, which stocks led the market, and a set of next-session focus stocks with reasons for each selection. Market condition badges display regime, stress level, and market direction (though direction shows "NA" on historical dates until a new briefing is created with that data).
- **Market page**: the full interactive dashboard showing the market path under two lenses (regime and phase/severity) across the platform's entire multi-decade history, with ten major index and macro lines colour-coded and loadable from a pre-computed cache. Supporting cards show breadth metrics, candidate counts, top sectors, top themes, and detailed market phase breakdowns.
- **Stock leaderboard**: a ranked table with three independent explainable scores per stock (Leadership, Entry Quality, Risk), all displayed as letter buckets plus 0–100 values. Sortable and filterable by sector, setup status, and chart patterns; includes forward returns and max-drawdown columns at five horizons (1d, 5d, 10d, 20d, 60d), each colour-graded and honest about data gaps. A Proximity to 52-week high column shows the percentage distance below each stock's highest recent price.
- **Stock detail pages**: full price charts with optional market-regime bands, a chart-range toggle (recent ~5-year window or full history back to first trading day), and a hover detail box showing exact OHLCV and moving averages for each bar. Realized forward returns and max-drawdown figures for each horizon, per-score component breakdowns, theme membership, setup status, and plain-language invalidation levels.
- **Risk budget cards**: on every stock detail page and as sortable leaderboard columns, showing ATR%, downside-only volatility, overnight-gap profile (p95, median, worst), the single worst 20-trading-day window in the stock's price history, and distance to invalidation level — every number percentile-ranked against the current universe.
- **Sector and theme leaderboards**: ranked by score, showing member counts, realized forward returns at five horizons, max-drawdown, and trend labels. Theme rows expand to reveal all member tickers as clickable links. Sector rows expand to show plain-language descriptions and a dated ticker-chip list of mapped members.
- **Evidence tracking**: every score shows a status chip ("Not yet proven" or "Proven" linked to evidence). An Evidence page lists every tested hypothesis with its verdict, control comparison vs. SPY, registration date, and forward-walk score. Pre-certified claims show Historical drawdown & dry-spell expectations broken out by market phase (typical, worst-case, sample size, survivorship caveat).
- **Global as-of date switcher**: a single top-bar calendar control that repoints the entire app (Today, Market, Stocks, Themes, Sectors, Stock Detail, Backtest, Research) to any past trading day. Year/month dropdowns, arrow-key stepping through dates, and URLs carry the `?asof=YYYY-MM-DD` parameter so links are shareable and work on page load without flashing today's data first.
- **Point-in-time stock universe**: the set of stocks scored is recomputed for each date you view — roughly 548 names that meet history, price, liquidity, and data-freshness thresholds. The universe grows as older history accumulates; early dates honestly show an empty leaderboard before enough names qualify.
- **Immutable scanner-run history**: append-only snapshots; opening any past run shows exactly what the scanner said on that date. Saved evening briefings are immutable — once frozen, the data shown never changes; the app reports honestly if old briefing data has gone missing.
- **Research hub**: ten individually-loaded labs at `/research`, each with its own page so opening one never triggers the others — Factor Lab, Regime Lab, Market Phase & Severity Lab, Regime × Phase × Factor Lab, Regime × Setup × Pattern, Severity-velocity × Regime, Multi-factor Combination, Setup & Pattern Lab, Recovery-Turn Edge, and Downtrend Opportunity. Every lab shows return and drawdown statistics with sample counts; clicking any `N=` chip opens exact underlying observations in a new tab.
- **Pre-registration registry and negative-results graveyard**: two governance pages in the Research hub showing every hypothesis the platform has registered or tested, with selectors, rationale, registration date, and pass/fail status. Rejected hypotheses are listed separately with their test date, multiple-testing correction, and lineage to their original registration.
- **Certification-budget accounting**: a Research governance page showing how much of the platform's statistical credibility budget has been spent — total canonical trials run, next trial's significance bar (Bonferroni formula shown), Thresholdout alpha budget remaining, and internal staging budget.
- **Referee audit**: a Research governance page testing whether the platform's own statistical certifier can be trusted, showing its empirical false-pass rate (with 95% CI), configured significance threshold, and whether it caught a deliberately-cheating factor.
- **Watchlist**: persists across backend restarts; accepts any ticker in the ~548-name universe. Each entry shows date added, reason, current scores and setup, price-since-added, and invalidation level. A Concentration X-ray section shows a correlation heatmap of all saved stocks (over a 126-day trailing window by default), correlation-threshold clusters, and an "effective independent bets" figure to reveal hidden overlap.
- **Methodology and Glossary**: a searchable, categorized glossary of over 120 terms (Scores & Buckets, Setups & Patterns, Regime & Breadth, Universe & Data, Forward-testing & Evidence, Factor Lab & Statistics) served from config. Every column header and stat label on dense analysis surfaces carries an inline info marker with the exact same definition in place — no duplication, no hard-coding.
- **Data Manager**: view current dataset coverage (price history, universe size, trading days, snapshot dates) with plain-language definitions; inspect per-symbol coverage (date range, bar count, thin/missing status); fetch EOD price history by date range; backfill scanner snapshots across the full ~548-name committed pool in one action. A Storage footprint card shows on-disk size and live counts. A Live-vs-seed drift card reports whether freshly-pulled prices matched trusted reference data (showing any "adjustment seams" caused by dividends or splits). A Universe Diagnostic explains why the universe is its current size. A Membership Timeline charts universe growth as an SVG step-function, lists entries/exits by date, and shows survivorship/warm-up caveats. Import jobs appear in Run History the instant they start and update in place to final states (ok, partial, failed, resumable, interrupted). Stage-aware resume skips already-downloaded data. Backfill honors exact date ranges with no length limit, splitting large ranges into chunks. A seed-safe Remove data panel prevents accidental deletion of committed seed. A Rebuild snapshots panel clears existing snapshots and recomputes every date from scratch. An Unfinished-imports panel consolidates paused, partial, failed, or interrupted jobs with the right action (Resume, Retry, Dismiss). A Macro feed panel lists configured FRED series with publication lags and enabled wiring legs. An Index & benchmark data provenance panel lists every Dashboard chart line with its vendor and first-recorded date.
- **Availability heatmap**: on Data Manager, a month-by-month calendar grid where each day is colour-coded by price-data density (blue scale, dark to bright) and ringed in violet when a scored snapshot exists. Hovering shows exact figures; clicking prefills the job form's date inputs; shift-clicking sets a range. The heatmap refreshes automatically after data jobs or removals.
- **Fast-ready boot**: the backend becomes usable within ~30 seconds — it serves core pages (Today, Market, Stocks, Sectors, Themes, Stock Detail) immediately and runs full historical backfill in the background. A top-bar badge reports honest states: Ready (green), Initializing with live progress (amber), Snapshot pending (named date, steady accent color), or Backend unavailable (red). The health check responds in ~10-15ms at rest. During warm-up, Backtest and Research pages show "Warming up (n/m)" that auto-fills when ready.
- **Background compute visibility**: a small "background compute running (N)" badge on every page shows when the backend is computing evidence for a historical date. The Data Manager page lists each running window's as-of date, elapsed time, and step count, plus the most-recent outcome (succeeded/failed with reason).
- **Daily preflight verdict banner**: every page shows a shared status strip with a single verdict — GO (quiet green, "today's board is current"), DEGRADED (loud amber with specific reasons, e.g., stale data or live-vs-seed drift), or NO-GO (loud red, "do not rely on today's board"). The verdict is computed once and shown identically everywhere.
- **Backtest workspace**: forward-tested evidence scoped to snapshots on or before the selected as-of date, showing forward returns and max-drawdown by score bucket, setup type, market regime, and chart pattern (VCP vs. non-VCP); excess returns vs. SPY, QQQ, and sector ETFs; and attribution by stock, sector, and rank band. Every breakdown table includes a Mean MDD column. The main evidence table loads in under a second for the most recent date because statistics are pre-computed at ingest time; views now name which state they show (current, refreshing with prior version, or not-yet-computed). Historical (as-of) date views use far less memory, reading source data in small bounded chunks. Concurrent requests for the same not-yet-cached window share a single calculation instead of duplicating expensive work.
- **Honest sector labels**: stocks with mapped sectors show the sector name (or "Unassigned" if no mapping exists); the Sector column sorts correctly in both directions even for stocks with no on-file sector; the Sector filter dropdown offers "Unassigned" to isolate that group.
- **Contained error recovery**: if an unexpected error occurs on any page, the app shows a calm "Something went wrong" message with a "Try again" button instead of going blank — sidebar and header stay visible and usable; if the outer application shell fails, a fallback page appears instead of a blank tab.
<!-- /AUTO:capabilities -->

This project embeds the [`incredible_auto_dev`](https://github.com/dennisccy/incredible_auto_dev)
AI multi-agent dev-chain as a **git subtree** at `incredible_auto_dev/`, following the same
monorepo wiring as `gap_gap_filler`.

## Project layout

```
incredible_auto_dev/                                  AI multi-agent dev-chain (git subtree; remote auto_dev, --squash)
.claude CLAUDE.md config scripts templates tests      symlinks → incredible_auto_dev/
```

The root-level `.claude`, `CLAUDE.md`, `config`, `scripts`, `templates`, and `tests` are
symlinks into `incredible_auto_dev/`, so the dev-chain configuration is active from the repo
root (single source of truth, no duplication).

## Syncing the dev-chain

The subtree tracks `auto_dev/main` (`git@github.com:dennisccy/incredible_auto_dev.git`).

```bash
# one-time, after a fresh clone (the remote is not stored in the repo)
git remote add auto_dev git@github.com:dennisccy/incredible_auto_dev.git

# pull the latest dev-chain from upstream
git subtree pull --prefix incredible_auto_dev auto_dev main --squash

# push local incredible_auto_dev/ changes back upstream
git subtree push --prefix incredible_auto_dev auto_dev main
```

<!-- AUTO:how-to-run -->
## How to run

### Prerequisites

- Python 3.12
- Node.js (for the Next.js frontend)
- The repo cloned locally

### Install

```bash
# Backend — create a virtualenv and install dependencies
cd apps/backend
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

```bash
# Frontend — install Node dependencies
cd apps/frontend
npm install
```

### Quick start — both services at once

```bash
./scripts/dev.sh
```

Starts the backend and frontend on deterministic per-project ports (printed to the terminal) and watches for file changes. Ports default to **8000** (backend) and **3000** (frontend); set `CHAIN_BACKEND_PORT` / `CHAIN_FRONTEND_PORT` to override. This script's backend subshell applies the same machine safety limits as `start-backend.sh` below (memory ceiling, `MALLOC_ARENA_MAX`, and — when `project-extensions/host-guard/host-guard.env` exists and `HOST_GUARD_ENABLED=1` — CPU-core pinning and BLAS/OMP/numexpr thread caps); if that file is absent or disabled, behavior is unchanged. The frontend subshell is never restricted.

### Start the backend (manually)

```bash
cd apps/backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start the frontend (manually)

```bash
cd apps/frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 npx next dev -p 3000
```

### Start backend + frontend (hardened, no auto-reload)

```bash
bash scripts/start-backend.sh
bash scripts/start-frontend.sh
```

Same ports as `./scripts/dev.sh` (deterministic per-project offset; override with
`CHAIN_BACKEND_PORT` / `CHAIN_FRONTEND_PORT`). Differences from the quick-start/manual
commands above: `start-backend.sh` runs pending Alembic migrations first, does not
auto-reload on file changes, and appends every boot's output to a permanent, git-ignored
log file at `logs/backend.log` — so a crash always leaves a readable trace (boot lines with
no matching clean-shutdown line) even with no terminal left open to read it from. Both
`start-backend.sh` and `./scripts/dev.sh`'s backend subshell apply the same memory ceiling,
`MALLOC_ARENA_MAX`, and (when configured via `project-extensions/host-guard/host-guard.env`)
CPU-core pinning and math-library thread caps to the backend process.

### Run backend tests

**Targeted tests only** (the resource contract forbids running the full suite):

```bash
cd apps/backend && .venv/bin/python -m pytest tests/test_<module>.py -v
```

Run only the test files for modules you modified. The full seed data spans ~30 years of daily prices,
so the complete suite builds a multi-GB `loaded_engine` fixture and takes several hours — that is
run by the owner only. The product itself boots in well under a minute.

### Local URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Health check | http://localhost:8000/api/health |
<!-- /AUTO:how-to-run -->
