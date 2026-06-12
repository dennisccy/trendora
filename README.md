# trendora

<!-- AUTO:capabilities -->
## What it does

Trendora is a local-first, research-only US equity leadership scanner and decision-support platform. It produces a daily ranked view of the market — from market regime down through sectors, industry groups, themes, and individual stocks — and never places orders or holds broker keys.

Current capabilities:

- **Daily dashboard**: market regime label (one of six, with a 0–100 score), ranked top sectors and themes, candidate counts (Actionable / Breakout-watch / Pullback-watch), market-breadth figure, last-scan timestamp, and a **Major indexes & regime chart** showing how S&P 500, Nasdaq 100, Russell 2000, S&P 500 Equal-Weight, and the Dow 30 (DIA) have moved across the full stored price history with color-coded market-regime bands in the background; when browsing a past date a clearly-labelled dashed vertical line marks exactly where the selected date falls so you can see both historical context and subsequent data in one view — no marker appears at the latest date; the card can be hidden with a toggle that persists across reloads.
- **Stock leaderboard**: ranked table with three independent, explainable scores per stock — Leadership, Entry Quality, and Risk — each displayed as an A–E bucket plus a 0–100 value; filterable by sector, setup status, and detected chart patterns including VCP. Click any column header to sort by that column (click again to reverse); click the rank column to restore the scanner's original order; clicking the info icon next to a column header opens the definition tooltip without triggering a sort. Filters and sort compose: the view always shows filtered results in the chosen order. Clicking a ticker opens the stock detail in a new tab so the leaderboard — filters, sort, scroll position, and selected date — stays exactly as you left it.
- **Stock detail**: full price + moving-average + volume chart (extending through the latest seed date with an as-of marker for historical views) with **optional market-regime bands** in the background (toggle default-on, persists); per-score component breakdowns, theme membership, setup status, plain-language reason, and a concrete invalidation level.
- **Theme and sector leaderboards**: ranked by score; each theme shows member tickers, basket returns, breadth, and trend label; each sector shows RS-vs-SPY, distance from 52-week high, and trend label.
- **Immutable scanner-run history**: append-only snapshots; opening a past run shows exactly what the scanner said on that date.
- **Global as-of date switcher**: a single top-bar control repoints the whole app — Dashboard, Stocks, Themes, Sectors, Stock Detail, and Backtest — to any past trading day's stored snapshot with a clear "viewing as-of D (historical)" indicator. Selecting a historical date updates the page URL with `?asof=YYYY-MM-DD` so the link can be copied and shared; the date survives a page reload or opening the link in a new tab; invalid or missing date parameters degrade safely to the latest view. Every in-app link — sidebar navigation, leaderboard rows, back links, scanner-run links, research subject links, watchlist tickers — automatically carries the selected `?asof` parameter, so middle-clicking, ctrl-clicking, or copying any link while browsing a historical date takes anyone who opens it to that same dated snapshot.
- **Consistent ISO date display**: every date shown anywhere in the app — the date switcher, stock and sector pages, chart tooltips, scanner run lists, job cards, coverage summaries — always reads as YYYY-MM-DD regardless of browser locale or device region settings.
- **Backtest workspace**: forward-tested evidence scoped to all snapshots dated on or before the selected as-of date — forward returns by score bucket (A–E), by setup type, by market regime, and VCP-vs-non-VCP; excess returns vs SPY, QQQ, and sector ETFs; a random same-sector control group; horizon-linked realized returns on Top Sectors, Top Themes, and the Ranked Cohort; and a return attribution panel (per-stock contributors and detractors, by-sector slice, by-rank-band, distribution and hit-rate).
- **Research area**: Factor Lab with decile sort, rank information coefficient, multi-factor composite cohorts (percentile-rank blend across any number of factors), and regime-conditioned effectiveness; Setup & Pattern Lab with pooled event-study forward-return distributions, hit-rate, expectancy, MAE/MFE, and exit-horizon — all raw and risk-adjusted. Every "N=" sample count on all Research surfaces is a clickable link that opens a drill-down page showing the exact stored observations behind that number — each row displays the ticker, the snapshot date, the stored factor value or setup match, and the realized forward return; the total on the drill-down page is guaranteed to equal the number on the chip you clicked. From any observation row you can click the ticker to open that stock's detail page set to that snapshot's exact date in a new tab.
- **Watchlist**: persists across backend restarts; each entry records date added, reason, current scores and setup, price-since-added, and invalidation level.
- **Methodology / Glossary**: a searchable, categorized glossary of terms — Scores & Buckets, Setups & Patterns, Regime & Breadth, Universe & Data, Forward-testing & Evidence, and Factor Lab & Statistics — served from a single config-backed catalog on the Methodology page; type any word to filter instantly. Every column header and stat label on the five dense analysis surfaces (Research Lab, Backtest scorecard, Stock Leaderboard, Dashboard breadth/regime cards, and Data Manager coverage table) carries an inline info marker you can hover or tap to read the exact same definition in place; no definition is duplicated or hard-coded.
- **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage with plain-language definitions for every figure (price history, universe, symbols, trading days, snapshot dates, backfill gaps) and a clear "universe vs symbols" distinction; inspect a per-symbol / per-universe-member coverage table (filterable by symbol, sortable by symbol or bar count, toggleable to universe members only) showing each ticker's date range, bar count, and whether it is thin or missing; pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range using validated ISO text inputs (invalid formats show an inline error and block submission), and backfill scanner snapshots. Live imports run in visible chunks ("chunk X of N"), retry automatically on rate-limit responses with exponential backoff, save their progress durably to the database, and expose an amber "rate-limited — resumable" state (distinct from a red failure) with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. Backfill jobs run multi-date compute in parallel (default 4 worker threads), completing the work materially faster than sequential execution; every completed job card shows a **Stage timings** block with per-stage elapsed time, items processed (symbols for fetch, dates for backfill), and the number of parallel workers — the backfill sub-block also shows the "per-date sum" versus actual wall-clock time so you can see the speed-up directly. An **Expand universe** job kind screens the committed candidate pool against market-cap, price, and liquidity rules over a chosen data source (Yahoo, Tiingo, or Finnhub), grows the scored universe to the names that pass, and displays exactly how many candidates passed plus every omitted candidate with its plain-language reason; sources that cannot supply market cap (Alpha Vantage, Stooq) are shown as disabled in the picker and blocked at the backend. A **seed-safe Remove imported data** panel lets the operator preview exactly what would be deleted — user-added bar count and range, committed-seed bars that are protected and kept, and the cascade of dependent snapshots and forward returns — before confirming; the committed seed can never be deleted, and a scope covering only seed bars is refused with a clear reason shown in the preview. A **Missing-data diagnostic** panel names every scored universe member that is insufficient for analysis, split into three labeled categories — no history, thin history, and intra-series gaps — each showing the exact shortfall in plain language; fixable rows carry a one-click "Pull the missing data" button and a "Pull all missing" button. A **unified Unfinished-imports** panel consolidates every import that did not finish cleanly — paused (rate-limited), partial (some symbols failed), or fully failed — each with a plain-language state explanation, done/remaining/failed counts, and the right action: Resume continues a paused import from where it stopped, Retry re-fetches only outstanding work, and Remove/Dismiss drops the actionable record while leaving the audit entry intact; a needs-key Resume or Retry re-prompts for the session-only key before dispatching.
- **Fast-ready boot with honest readiness badge**: the backend becomes usable within about 30 seconds of a cold start — it serves the core pages (Dashboard, Stocks, Sectors, Themes, Stock Detail) for the latest date immediately and runs the full historical walk-forward backfill in the background. The top-bar badge reports three honest states: **Ready** (green), **Initializing… history n/m** (amber, with live progress), or **Backend unavailable** (red). While the background warm-up is still running, the Backtest and Research pages display a clear "Warming up (n/m)" notice that automatically fills in with real data when loading finishes — no page refresh needed.
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

### Start the backend

```bash
cd apps/backend
.venv/bin/python -m uvicorn app.main:app --reload --port 8835
```

The backend defaults to port **8835** (auto-offset per project). Set `CHAIN_BACKEND_PORT` to override.

### Start the frontend

```bash
cd apps/frontend
NEXT_PUBLIC_API_URL=http://localhost:8835 npx next dev -p 3835
```

The frontend defaults to port **3835**. Set `CHAIN_FRONTEND_PORT` to override.

### Run backend tests

```bash
cd apps/backend && .venv/bin/python -m pytest tests/ -v
```

### Local URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3835 |
| Backend API | http://localhost:8835 |
| Health check | http://localhost:8835/health |
<!-- /AUTO:how-to-run -->
