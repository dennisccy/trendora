# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35
**Date:** 2026-06-19
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|---|---|---|---|---|
| `/stocks` | Stocks leaderboard table (row count) | Changed behavior | J-85 rebuild repopulated stored snapshots with per-date dynamic universe; rows now vary by date instead of always returning 122 | Set the global as-of date to 2021-01-04 and confirm the table shows 0 rows; then set it to 2022-02-01 and confirm approximately 495–504 rows appear |
| `/stocks` | Stocks leaderboard table (early date empty state) | Changed behavior | Pre-warm-up dates now return 0 rows honestly (no fabricated membership before ~2021-10-18) | Set the global as-of date to any date before 2021-10-15 and confirm the table is empty with an appropriate empty-state message rather than showing any stock rows |
| `/stocks` | Stocks leaderboard table (latest date count) | Changed behavior | Rebuilt snapshots now admit approximately 544 members at the latest date, up from 122 | Set the global as-of date to the latest date (2026-06-16 or current) and confirm approximately 544 rows are present |
| `/stocks/NVDA` | NVDA detail scores (Leadership / Entry / Risk) | Changed behavior | Scores are now read from the rebuilt snapshot; must match the `/stocks` list row for the same date | Load `/stocks` at 2026-06-16, note NVDA's Leadership / Entry / Risk values, then navigate to `/stocks/NVDA` at the same date and confirm the three values are identical |
| `/data` | Membership timeline panel — SIZE column | Changed behavior | Rebuilt snapshots carry per-date member counts; SIZE now varies across rows | Navigate to `/data`, scroll the membership timeline below the fold into view, and confirm the SIZE column shows different values across multiple date rows (not a uniform 122 on every row) |
| `/data` | Membership timeline panel — Entries / Exits columns | Changed behavior | Dynamic per-date membership transitions now exist in the rebuilt data; previously all dashes | Navigate to `/data`, scroll the membership timeline into view, and confirm at least several date rows show non-dash values in both the Entries and Exits columns |
| `/data` | Membership timeline panel — step-function shape | Changed behavior | Universe grows from 0 at the warm-up boundary to ~544 over time; the curve must rise, not be flat | Scroll the membership timeline into view and confirm the SIZE values are near 0 for early dates (around Oct 2021) and rise to approximately 544 for recent dates, forming a visible step function |
| `/data` | Membership timeline panel — honesty labels | Must remain unchanged | Three survivorship / warm-up / universe-relative labels were present before the rebuild and must not have been lost | Scroll the membership timeline into view and confirm all three honesty label strings are still visible verbatim in the panel |
| `/data` | J-94 per-date coverage diagnostic | Changed behavior | Diagnostic now agrees with snapshot-served `/stocks` count (both 544 at latest); iter-34 inconsistency resolved | Open the `/data` coverage diagnostic for 2026-06-16 and confirm the admitted-member count shown equals the row count returned by `/stocks` at the same date (approximately 544) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/data/trendora.db` (database state only, not source code) — J-85 rebuild rewrote all stored `ScannerResult` snapshot rows and their associated `forward_returns` rows using the per-date resolver membership; `daily_prices` price seed was not modified (793,218 bars before and after). This is a data-layer change with no source-code diff; the UI impact flows entirely through the existing read endpoints that already serve these rows.
- `apps/backend/data/trendora.db.pre-iter35-rebuild.bak` — safety backup of the pre-rebuild database state; not served to any frontend, not visible to users.

---

## Summary

- **Frontend surfaces changed:** 0 (no frontend source-code diff)
- **New pages/routes:** 0
- **Modified components:** 0 (no component code changed)
- **Navigation changes:** no
- **Data-driven surfaces with changed behavior:** 9 (all existing surfaces; change is in served data, not code)
- **Backend-only changes:** 0 (the database repopulation is the source of all user-visible change; every affected value is already surfaced via existing pages)
