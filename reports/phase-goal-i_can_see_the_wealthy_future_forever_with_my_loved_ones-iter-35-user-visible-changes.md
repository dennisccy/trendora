# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35
**Date:** 2026-06-19
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now step the single global as-of date back to early 2021 on `/stocks` and see an honestly empty stock list (0 rows before approximately 18 Oct 2021), confirming the product shows a real point-in-time universe rather than a fabricated fixed list.
- Users can now step the as-of date forward through the history and watch the stock count rise naturally — roughly 495 stocks by January 2022, approximately 544 at the latest date — rather than a constant 122 at every date.
- Users can now read the Data Manager membership timeline on `/data` and see a genuine step-function curve: the SIZE column varies by date, the Entries and Exits columns show real membership changes (previously all dashes), and the curve rises from the warm-up boundary instead of sitting flat at 122.
- Users can now trust that every downstream surface that reads from stored snapshots — Themes, Sectors, Scanner-Runs, Backtest evidence, and Research — also reflects the per-date dynamic universe rather than the stale static 122-member list.

---

## What Changed in the Visible UI

- The `/stocks` leaderboard table now shows a date-dependent row count. At an early pre-warm-up date such as 2021-01-04 the table is honestly empty (n = 0). At 2021-10-25 it shows approximately 495 rows. At the latest date it shows approximately 544 rows. Previously every date returned exactly 122 rows regardless of when the date selector was set.
- The Data Manager page (`/data`) membership timeline panel now displays a rising step function instead of a flat line at 122. The SIZE column varies across rows. The Entries and Exits columns are populated with real values. The three honesty labels — survivorship bias, warm-up period, and universe-relative — remain exactly as before.
- The per-date coverage diagnostic on `/data` (J-94) now agrees with the snapshot-served `/stocks` row count at the same date (both 544 at 2026-06-16), resolving the iter-34 internal inconsistency where the diagnostic showed 544 but the served store showed 122.
- The NVDA detail page (`/stocks/NVDA`) and the NVDA row on the `/stocks` list now serve identical canonical scores (Leadership 40.37 / Entry 52.85 / Risk 39.17 at 2026-06-16) read from the single rebuilt snapshot — the two views agree, as required by the single-source contract.

---

## What Old Behavior Changed

- Stock universe count on `/stocks`: previously returned 122 rows at every as-of date (the stale static 122-member universe persisted by the iter-27 rebuild). Now returns 0 rows before the warm-up boundary (~2021-10-15), a rising count from ~495 in late 2021, and approximately 544 at the latest date.
- Data Manager membership timeline on `/data`: previously rendered a flat horizontal line at 122 for every date row, with Entries and Exits columns showing dashes. Now renders a step function with varying SIZE values and populated Entries/Exits columns.
- J-94 coverage diagnostic vs `/stocks` agreement: previously the diagnostic (reading the live resolver) reported 544 admitted members while the served `/stocks` page returned 122 — an internal inconsistency. Now both agree at 544 at the latest date.

---

## Not Visible Yet

- None. All affected capabilities were already exposed on existing screens. This iteration repopulated the stored snapshot data those screens read — it introduced no new backend endpoint, no new config key, and no new stored column. Every changed user-facing value is immediately visible on the existing `/stocks`, `/data`, Themes, Sectors, Scanner-Runs, Backtest, and Research pages.
