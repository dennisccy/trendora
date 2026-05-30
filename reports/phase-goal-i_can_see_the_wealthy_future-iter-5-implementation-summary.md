# Goal iter-5 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future-iter-5
**Date:** 2026-05-30
**Written by:** developer

---

## Features Implemented

- **Scanner Runs history page (`/scanner-runs`)**: A dated, dark table listing every saved scan
  snapshot, newest first. Each row shows the as-of date, a colour-graded market-regime badge
  (label + score), the candidate counts (Actionable / Breakout-watch / Pullback-watch), and how many
  stocks were scanned. Clicking a date opens that run's frozen view.
- **Immutable run-detail page (`/scanner-runs/[runId]`)**: Opens one past scan exactly as it was
  recorded on its date. A "Immutable snapshot — as of YYYY-MM-DD" header makes clear this is a frozen
  historical view, never recomputed for today. It shows that date's regime panel (label + 0–100 score
  + component breakdown), universe-relative breadth, candidate counts, and a ranked table of the
  stored stocks (Leadership / Entry Quality / Risk as A–E bucket + number, setup status, reason).
- **Saved scan snapshots (backend)**: The scanner now permanently records each scan as an immutable,
  append-only snapshot. On startup it saves a snapshot for two real historical Risk-Off dates
  (2022-10-07 and 2025-04-04) plus the latest data date — so the history has multiple dated runs to
  browse out of the box.
- **History API (`GET /api/runs`, `GET /api/runs/{run_id}`)**: New read-only endpoints that serve the
  saved snapshots — the list (newest first) and one run's full stored detail.

---

## Changed Behavior

- **Scanner Runs pages**: Previously both `/scanner-runs` and `/scanner-runs/[runId]` were
  "coming soon" placeholders. They are now real, data-driven pages.
- **Backend startup**: The backend now does a little extra work on the *first* boot of a fresh
  database — it scans and saves ~3 historical snapshots before it starts serving (about 1–2 seconds
  per date). On every later boot this is skipped because the snapshots already exist.
- The six existing pages (Dashboard, Stocks, Themes, Sectors, Stock Detail) are **unchanged** — their
  data still comes from the live on-request endpoints, so nothing about them regressed.

---

## Backend-Only Items

- None. Every new capability is reachable from the UI: the run list and the run-detail page are both
  wired to the new endpoints, and Scanner Runs is already in the left sidebar.

---

## Incomplete Items

- None deferred from this phase's spec. Forward-return testing, the System Health page, and the
  Watchlist remain in later iterations by design (out of scope here). The `forward_returns` table is
  intentionally *designed but not created* this iteration — it lands in iter-6 as a separate
  append-only table keyed to these snapshots, so the snapshots themselves are never modified.

---

## Config and Environment Changes

- `config.yaml` — new `scanner.bootstrap_dates` list (`["2022-10-07", "2025-04-04"]`). These are the
  historical dates the scanner saves a snapshot for on first boot; both are real seed dates the engine
  labels "Risk-off". The latest data date is added automatically in code (not listed). No new
  environment variables. No secrets. No database migration (tables are created automatically on
  startup).

---

## Known Limitations

- **Breadth and new-high/low figures are universe-relative** (computed from the ~122-stock seed
  universe, not the whole market) and are labelled as such on every run — this is by design, not a bug.
- **The history is reproducible, not mutable.** The database file is ephemeral/gitignored; on a fresh
  database the scanner deterministically re-creates identical snapshots from the committed seed. Once a
  snapshot row exists, no code path ever updates it.
- **`/api/health` still reports `last_run_date: null`.** Wiring it to the newest saved run is a small
  cosmetic follow-up, intentionally left out of scope to avoid touching the health endpoint this
  iteration.
- **First-boot cost**: on a brand-new database the backend saves the historical snapshots before it
  starts serving. A measured clean cold boot reached "ready" in ~55 seconds — most of that is the
  pre-existing one-time data-seed load (unchanged by this iteration); saving the 3 snapshots adds a few
  seconds on top. Every later boot skips this (the snapshots already exist), so it is a one-time cost.
  This is flagged so a slow first boot is not mistaken for the backend being down.
