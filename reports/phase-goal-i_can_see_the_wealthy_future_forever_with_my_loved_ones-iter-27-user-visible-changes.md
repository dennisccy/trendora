# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27
**Date:** 2026-06-17
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see the worst peak-to-trough drawdown (max drawdown) for every 1/5/10/20/60-day forward-return window on the `/stocks` leaderboard — five new "MDD" columns appear to the right of the existing forward-return columns, colour-graded and sortable.
- Users can now see a paired max-drawdown figure beneath each horizon return card on the `/stocks/[ticker]` Stock Detail page.
- Users can now see five paired max-drawdown columns to the right of the forward-return columns on the `/themes` leaderboard, sortable by any MDD horizon.
- Users can now see five paired max-drawdown columns to the right of the forward-return columns on the `/sectors` leaderboard, sortable by any MDD horizon.
- Users can now see an aggregate "Mean MDD" column beside the return statistics on every Backtest evidence panel (by-bucket, by-setup, and by-regime breakdowns).
- Users can now see an aggregate "Mean MDD" column beside the return statistics on the Research event-study per-horizon table and on the Regime × Setup × Pattern table.
- Users can now trigger a full snapshot rebuild on the `/data` page by clicking the "Rebuild snapshots for current universe" button, confirming via a modal dialog, and watching live progress in the existing job card.
- Users can now see on the `/data` page how many scanned-universe stocks are missing from the latest snapshot ("N members absent — rebuild to include them") and which tickers they are; when none are absent a calm "all members present" note is shown instead.

---

## What Changed in the Visible UI

- The `/stocks` leaderboard table now includes five additional columns labelled with the horizon (e.g. "1d MDD", "5d MDD", "10d MDD", "20d MDD", "60d MDD") to the right of the forward-return columns; cells show a negative percentage (colour-graded red by severity) or "NA" when the window is not yet complete.
- The `/stocks/[ticker]` Stock Detail page's forward-return horizon cards now each show a second line underneath the return value labelled "Max drawdown".
- The `/themes` leaderboard table now includes five additional MDD columns to the right of the forward-return columns; the expanded-member row colspan was widened to cover these new columns.
- The `/sectors` leaderboard table now includes five additional MDD columns to the right of the forward-return columns; the expanded-member row colspan was widened to cover these new columns.
- The Backtest evidence panels now contain a "Mean MDD" column beside the return statistics in the by-bucket, by-setup, and by-regime breakdown tables, and a "Mean max drawdown" figure in the evidence summary header.
- The Research page event-study and Regime × Setup × Pattern tables now each contain a "Mean MDD" column beside the return statistics, with the same NA and low-sample gating as the other cells.
- The `/data` page now contains a `RebuildPanel` section with: (a) a coverage diagnostic banner (amber, only when absent count > 0) listing absent universe members with the prompt to rebuild, or a calm "all members present" note when no members are absent; (b) a "Rebuild snapshots for current universe" button that is disabled while a job is running and opens a confirm dialog before any destructive action; (c) a confirm modal (Card + fixed overlay, Confirm button always visible outside the scroll region) that posts the rebuild job on confirmation.

---

## What Old Behavior Changed

- Forward-return tables on `/stocks`, `/themes`, and `/sectors`: previously showed five forward-return columns. Now each page also shows five paired max-drawdown columns to the right of them. The sort contract (NA-last, re-order only) is unchanged; no refetch occurs when sorting MDD columns.
- Stock Detail forward-return panel: previously showed only the realized return per horizon. Now each horizon card also shows its paired max drawdown underneath the return value.
- Backtest and Research aggregated tables: previously reported mean forward return (and MAE/MFE on Research) only. Now they also report aggregate "mean max drawdown" beside the return statistics.
- Existing forward-return rows in the database that predate this iteration show "NA" (not zero) for max drawdown until the operator triggers a confirm-gated rebuild. This is honest NA — the value was never computed for those rows.

---

## Not Visible Yet

- None. Every backend addition in this iteration (the rebuild job kind, the coverage diagnostic, and the max-drawdown stored values) is wired to a visible UI surface. The rebuild job reuses the existing J-66 progress card and run-history surface.
