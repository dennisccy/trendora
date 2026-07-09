# Phase goal-mcp-loop-iter-24 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-24
**Date:** 2026-07-09
**Written by:** ui-impact-analyst

---

## Summary

This iteration is goal.md's fast-platform **mechanical backend pass** (items B/C/D/G/H), a new measurement
harness (item K), and **one** small new UI surface: a read-only storage-footprint card on the Data
Manager (`/data`). Every optimized backend path is byte-identity-gated — no displayed number anywhere in
the product changed. The overwhelming majority of this iteration's work is invisible by design: it makes
existing pages and API responses faster on the platform's 30-year/590-symbol dataset, not different.

---

## What Users Can Now Do

- Users can now see the platform's current data-storage footprint — the database's on-disk file size, plus
  how many price bars, scored results, and forward-return records it holds — in a new **"Storage
  footprint"** card on the `/data` (Data Manager) page, directly below the existing "Dataset coverage"
  card. The four values shown are: **Database file** (a human-readable size, e.g. "1.22 GB"), **Price
  bars** (e.g. "3,293,160"), **Scanner rows** (e.g. "165,755"), and **Forward returns** (e.g. "821,054").
  This is the iteration's only net-new capability; everything else below is an existing feature working
  the same way, just faster.

---

## What Changed in the Visible UI

- The `/data` page has one new card, "Storage footprint," placed directly after "Dataset coverage" in the
  page's existing panel stack (same column as the membership-timeline and survivorship panels below it).
  It uses the same card/metric styling as the rest of the page — no new visual style was introduced.
- On a brand-new or empty database, the same card is designed to show "0 B" and "0" for every count rather
  than an error or a blank space (the backend's `compute_capacity` always returns zeroes, never fails, on
  a cold DB) — this analysis did not independently browser-verify the empty-DB rendering; that check
  belongs to browser QA.
- Nothing else changed visually anywhere else in the product this iteration — no other page, label,
  button, or layout was touched.

---

## What Old Behavior Changed

*(Every item below is a "same output, faster" change — testers should re-verify that the numbers are
unchanged, not that they look different.)*

- **Opening a stock's detail page (e.g. `/stocks/AAPL`) or the `/watchlist` page:** previously the server
  had to load and JSON-parse every scored stock in the run (400+ records) just to answer for one or a
  few tickers. It now reads only the requested ticker(s) directly. The displayed values (score badges,
  setup label, price, evidence badges) are byte-identical to before — this is a response-time change only,
  proven by the existing byte-identity tests passing unedited.
- **The small "Ready / Initializing… / Backend unavailable" readiness badge shown in the top bar on every
  page:** previously its background check re-derived the warm-up calendar and looped through every cadence
  date on each ~2-second poll. It now reuses that derivation and issues one grouped query instead. The
  badge's three possible states and its "history n/m" progress figure are unchanged — only the cost of
  computing them changed. The same underlying value also drives the "Warming up — historical evidence
  still loading (n/m)" card shown on `/backtest` and the research pages while the backend is still warming
  up.
- **The `/data` page's "Missing-data diagnostic" card** (the no-history / thin / intra-series-gap rows, or
  the "No missing data" empty state): previously computing this on a cold backend issued one query per
  universe member (up to ~590 queries). It now issues one bulk query. The rows and empty-state shown are
  byte-identical — only how quickly the page's diagnostic section populates changed, most noticeably right
  after a server restart.
- **Database write behavior (not visible in any UI, flagged for completeness):** the database now writes
  in "WAL" mode, letting reads keep flowing while background jobs write, and two duplicate internal lookup
  structures were replaced with one new one tuned for date-range lookups. No page, count, or label changes
  as a result — this is the mechanism behind the speedups above, not a user-facing change itself. One
  physical side effect: the database's folder now contains two small companion files (`-shm`, `-wal`)
  alongside the main database file while the app is running — invisible to anyone using the web product,
  relevant only to someone inspecting the server's filesystem directly.

---

## Not Visible Yet

- The new `scripts/measure-perf.sh` measurement script and its output (the before/after latency tables and
  the DB capacity numbers appended to `reports/perf-budgets.md`) are operator/engineering tooling — there
  is no page or button in the product itself that runs this script or displays its report. It is read
  directly from the repository, not from the running application, by design (not a deferred UI gap).
- Three related fast-platform items from the same goal.md initiative were **deliberately not built** this
  iteration and have no UI or backend presence yet: a leaner `/api/stocks` leaderboard payload (item E),
  frontend-side interaction speedups like heatmap memoization and leaderboard search debounce (item I),
  and a ≥30%-faster background data-import job time (item F, tracked as journey J-16). These are scheduled
  for later iterations per goal.md — not gaps in this iteration's own scope.
