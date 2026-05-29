# Phase goal-i_can_see_the_wealthy_future-iter-1 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future-iter-1
**Date:** 2026-05-29
**Written by:** developer

---

## Features Implemented

- **The Trendora workstation shell**: open the app and you get a dense, dark analytical layout with a
  permanent left menu listing all seven destinations — Dashboard, Stocks, Themes, Sectors, Scanner
  Runs, System Health, and Watchlist. You can click between all of them.
- **Live "is the engine running?" badge**: the top bar shows a status badge. Green ("Backend OK") with
  the data provider, the latest data date, and how many symbols are loaded when everything is healthy;
  red ("Backend unavailable") if the backend can't be reached. It never shows a fake "OK".
- **Offline, reproducible data foundation**: the app ships with a committed dataset of real daily
  price history (about 5.4 years, ~158 stocks and ETFs). It runs entirely offline — no internet, no
  API keys, no logins — and gives the same answers every time it restarts.
- **A single settings file** (`config.yaml`) that holds the stock list, the theme groupings, the ETF
  lists, and the score grade boundaries. Everything tunable lives here, not buried in code.
- **A health check page** (`/api/health`) the badge reads to confirm the backend is up.

This iteration is deliberately **data-empty**: there are no rankings, scores, or charts yet. Each page
shows a tidy "nothing here yet — this is what will appear" message. The goal of this step was to stand
up a trustworthy, reproducible foundation, not to show numbers.

---

## Changed Behavior

- None. This is the first build (the repository was empty of application code before this iteration).

---

## Backend-Only Items

- `GET /api/health` — the connectivity probe. It IS surfaced in the UI (the status badge reads it), so
  it is not hidden; listed here only because it is an API endpoint rather than a page.
- The committed price dataset and the reference tables (stocks, ETFs, sectors, themes) are loaded into
  the database on first start but are **not yet displayed** anywhere — they feed the scoring that
  arrives in later iterations.

---

## Incomplete Items

- **No scoring, rankings, charts, scanner runs, evidence, or watchlist actions** — these are out of
  scope for this iteration by design (they arrive in iterations 2–7). Every page is an empty state.
- **The `industries` reference list is not populated yet** (the table exists; industry ETFs are loaded
  separately). It will be filled in when sector/industry scoring lands.
- **No user journey (J-01…J-11) passes yet** — expected. This iteration is the planned infrastructure
  step; success is "the shell boots offline against a real committed dataset and connects", which is
  met.

---

## Config and Environment Changes

- **`config.yaml`** (new, repo root) — the single source of all tunables: data provider (`seed`),
  database location, the ~122-stock universe + filters, ETF lists, the 11 theme groupings, and the
  A–E grade boundaries. Scoring/regime/decision/walk-forward sections are present but not yet used.
- **`CORS_ORIGINS`** (backend env var) — which web origins may call the API; set automatically by
  `scripts/start-backend.sh`. Default: `http://localhost:3000`.
- **`NEXT_PUBLIC_API_URL`** (frontend env var) — where the frontend finds the backend; set
  automatically by `scripts/start-frontend.sh`. Example in `apps/frontend/.env.example`.
- **Database** — SQLite at `apps/backend/data/trendora.db`, created automatically on first start
  (not committed). Switching to Postgres later is a one-line change of the database URL in `config.yaml`.
- First-time setup (already done here): create the Python virtualenv + `pip install -r
  apps/backend/requirements.txt`; `npm install` in `apps/frontend`.

---

## Known Limitations

- **Data source note:** the plan named Stooq for the one-time data fetch, but Stooq now requires a
  captcha-obtained key (which we will not commit as a secret). The data was instead fetched from the
  free, no-key **Yahoo Finance** end-of-day feed. It is equally real and, once committed, frozen — so
  this choice has no effect at runtime. One stock (CyberArk / CYBR) was dropped because it is delisted
  (acquired) and has no data; we removed it rather than invent prices.
- **Prices are adjusted for splits/dividends; trading volume is raw**, so volume can jump at a stock
  split. This is a documented, accepted simplification for the research MVP.
- **The live status badge and cross-origin calls are best confirmed in a real browser** — the
  automated checks here confirm the pages render and the backend answers, and browser QA does the
  click-through.
- The committed dataset is a **curated ~158-symbol universe**, not the whole market (by design).
