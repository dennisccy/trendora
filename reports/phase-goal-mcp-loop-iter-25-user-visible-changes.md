# Phase goal-mcp-loop-iter-25 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-25
**Date:** 2026-07-09
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Nothing new. Verified directly against the repository (`git diff HEAD --stat -- apps/backend apps/frontend config.yaml` returns empty): this iteration added no page, button, field, panel, or endpoint. It is a fix-verification and artifact-reconciliation pass only, carrying forward the previous iteration's UI byte-for-byte.
- The only practical difference for anyone using the product: opening the Data Manager page (`/data`) as the very first action right after the backend service restarts no longer risks bringing down the entire application. This is a restored guarantee rather than a new feature — the page was always supposed to behave this way; the immediately preceding iteration had temporarily broken it.

---

## What Changed in the Visible UI

- None. Every page in the product — `/stocks`, `/stocks/{ticker}`, `/data`, `/evidence`, Dashboard, Sectors, Themes, Backtest, Research, Watchlist — renders exactly as it did going into this iteration: same layout, same components, same displayed numbers, same navigation. Confirmed directly: `apps/frontend/**` has zero diff against `HEAD`.
- The `/data` page's storage-footprint card (`StorageCapacityPanel`, showing DB file size plus row counts for `daily_prices` / `scanner_results` / `forward_returns`) and its missing-data coverage diagnostic (`CoveragePanel`) — both introduced in the prior iteration — are untouched: identical markup, identical formatting, identical values.

---

## What Old Behavior Changed

- **`/data`'s very first load immediately after a backend restart.** Previously: the backend's SQLite connection tuning reserved 1 GB of virtual memory per pooled database connection; with up to 30 connections available (10 base + 20 overflow), opening `/data` as the first request after any restart could exhaust the backend's 6 GB memory ceiling and crash the entire server process — not just show an error on that one page, but take every page in the product down with it. This was discovered and reproduced twice by the canonical browser test in the immediately preceding iteration.
  - The fix (disabling that per-connection memory reservation, a one-line configuration change) was already written and in place before this iteration began. This iteration's entire job was to prove the fix holds under real, live conditions rather than accept it on paper: the backend was fully stopped and cold-started twice, with the Data Manager's underlying data request fired as the very first heavy request each time.
  - Result, both times: the request completed successfully in roughly 9.4–9.5 seconds, peak memory use stayed under a third of the ceiling, and the backend kept running normally afterward to serve further pages.
  - Practically, this means restarting the service and immediately opening the Data Manager page will no longer bring the whole application down for every user.

---

## Not Visible Yet

- There is no on-screen indicator of this fix — nothing new appears anywhere. The only observable difference is the *absence* of a crash under the specific "restart, then immediately open Data Manager" sequence described above.
- This iteration's proof comes from direct, real backend restarts and real data requests with memory monitored throughout the process — not from a point-and-click browser session. This project's standard practice is to also confirm the identical restart-then-load sequence through an actual browser session before treating the issue as fully and formally closed; that browser-driven confirmation is the next step in this phase's pipeline and had not yet produced its result as of this report.
