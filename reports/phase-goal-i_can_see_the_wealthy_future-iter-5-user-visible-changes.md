# Phase goal-i_can_see_the_wealthy_future-iter-5 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future-iter-5
**Date:** 2026-05-30
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open **`/scanner-runs`** and see a **history of dated, immutable scan snapshots** in a table — each row showing the as-of date, the market regime that day (label + 0–100 score), and how many stocks were Actionable / Breakout-watch / Pullback-watch.
- Users can now click any run's **as-of date** to open **`/scanner-runs/[runId]`** and read **exactly what the scanner said on that date** — a frozen, historical view that is never recomputed for today.
- Users can now open the seeded **Risk-Off** run (2025-04-04 or 2022-10-07) and confirm it shows regime label **"Risk-off"** with **zero Actionable** stocks — every stock is watchlist-only (J-07).
- Users can now open an **older** run and a **newer** run and confirm their stored rankings and scores **differ** — proving each snapshot is a frozen as-of view, not a recomputation of the latest data (J-08).
- Users can now read, per historical run, the full regime panel (label, score, component breakdown), universe-relative breadth (above 50-DMA, above 200-DMA, net new highs), candidate counts, and a ranked stored stock table (Leadership / Entry Quality / Risk as A–E buckets, setup status, reason).
- Users can navigate back to the run list from a detail page via the **"All runs"** button.

---

## What Changed in the Visible UI

- **`/scanner-runs`** graduated from an iter-1 "empty/coming soon" stub to a **real dense dark table** of persisted runs (newest first), with a colour-graded regime badge (green risk-on → red risk-off), three candidate-count columns, and a stock-count column.
- **`/scanner-runs/[runId]`** graduated from an empty stub to a **full immutable as-of detail page** with a lock-icon header strip reading **"Immutable snapshot — as of YYYY-MM-DD"** plus the scanned-at timestamp, provider, and benchmark.
- The run-detail page reuses the **same `ScoreBadge` rendering** as the live `/stocks` leaderboard, so a stock's Leadership/Entry-Quality/Risk buckets read identically on a stored run and on the live page.
- Each run-list row's as-of date is a **clickable link** (accent colour, underline on hover/focus) to that run's detail page.
- A **"Risk-off-watchlist"** candidate count tile appears on run-detail pages alongside Actionable / Breakout-watch / Pullback-watch.

---

## What Old Behavior Changed

- No existing live page changed. The `/api/dashboard`, `/api/stocks`, `/api/sectors`, `/api/themes`, and `/api/stocks/{ticker}/bars` endpoints and their pages were **deliberately left byte-identical** to protect J-01–J-06. The only UI change is the two `/scanner-runs` pages going from stubs to real pages — there is no behavior regression to re-verify on the existing pages, only a no-regression confirmation.

---

## Not Visible Yet

- **`/api/health` still reports `last_run_date: null`** — the newest persisted run's date is not yet wired into the health endpoint (a cosmetic follow-up, intentionally deferred). Not surfaced anywhere users see.
- **Forward returns / walk-forward results** are designed for (the `forward_returns` table is described in code) but **not created and not displayed** — deferred to iter-6 (J-09/J-10).
- **Run-detail tickers are plain text, not links** to `/stocks/[ticker]` — by design, a frozen as-of row must not deep-link to the live latest-date stock detail. Users cannot click through from a stored run row to a stock page.
