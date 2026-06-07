# trendora

<!-- AUTO:capabilities -->
## What it does

Trendora is a local-first, research-only US equity leadership scanner and decision-support platform. It produces a daily ranked view of the market — from market regime down through sectors, industry groups, themes, and individual stocks — and never places orders or holds broker keys.

Current capabilities:

- **Daily dashboard**: market regime label (one of six, with a 0–100 score), ranked top sectors and themes, candidate counts (Actionable / Breakout-watch / Pullback-watch), market-breadth figure, and last-scan timestamp.
- **Stock leaderboard**: ranked table with three independent, explainable scores per stock — Leadership, Entry Quality, and Risk — each displayed as an A–E bucket plus a 0–100 value; filterable by sector, setup status, and detected chart patterns including VCP.
- **Stock detail**: full price + moving-average + volume chart (extending through the latest seed date with an as-of marker for historical views), per-score component breakdowns, theme membership, setup status, plain-language reason, and a concrete invalidation level.
- **Theme and sector leaderboards**: ranked by score; each theme shows member tickers, basket returns, breadth, and trend label; each sector shows RS-vs-SPY, distance from 52-week high, and trend label.
- **Immutable scanner-run history**: append-only snapshots; opening a past run shows exactly what the scanner said on that date.
- **Global as-of date switcher**: a single top-bar control repoints the whole app — Dashboard, Stocks, Themes, Sectors, Stock Detail, and Backtest — to any past trading day's stored snapshot with a clear "viewing as-of D (historical)" indicator.
- **Backtest workspace**: forward-tested evidence scoped to all snapshots dated on or before the selected as-of date — forward returns by score bucket (A–E), by setup type, by market regime, and VCP-vs-non-VCP; excess returns vs SPY, QQQ, and sector ETFs; a random same-sector control group; horizon-linked realized returns on Top Sectors, Top Themes, and the Ranked Cohort; and a return attribution panel (per-stock contributors and detractors, by-sector slice, by-rank-band, distribution and hit-rate).
- **Research area**: Factor Lab with decile sort, rank information coefficient, multi-factor composite cohorts (percentile-rank blend across any number of factors), and regime-conditioned effectiveness; Setup & Pattern Lab with pooled event-study forward-return distributions, hit-rate, expectancy, MAE/MFE, and exit-horizon — all raw and risk-adjusted.
- **Watchlist**: persists across backend restarts; each entry records date added, reason, current scores and setup, price-since-added, and invalidation level.
- **Methodology / Glossary**: config-backed catalog of every setup status and detected pattern with plain-language meaning, exact thresholds, and a worked example; inline tooltips on every badge link back to the same definition.
- **Data Manager**: grow, understand, and curate the dataset on demand — view current dataset coverage, pick an import source (with optional session-only API key, never persisted), fetch EOD price history by date range, and backfill scanner snapshots. Live imports run in visible chunks ("chunk X of N"), retry automatically on rate-limit responses with exponential backoff, save their progress durably to the database, and expose an amber "rate-limited — resumable" state (distinct from a red failure) with a Resume button that continues from the next un-fetched chunk without re-fetching saved data — surviving a full backend restart. A pasted API key is scrubbed from all error messages, job cards, and run history before it is ever stored or displayed. An **Expand universe** job kind screens the committed candidate pool against market-cap, price, and liquidity rules over a chosen data source (Yahoo, Tiingo, or Finnhub), grows the scored universe to the names that pass, and displays exactly how many candidates passed plus every omitted candidate with its plain-language reason; sources that cannot supply market cap (Alpha Vantage, Stooq) are shown as disabled in the picker and blocked at the backend.
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
