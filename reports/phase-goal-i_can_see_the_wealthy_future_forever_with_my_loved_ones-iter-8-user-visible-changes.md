# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8
**Date:** 2026-06-12
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- After a fetch+backfill job completes (or while it is still running), users can read exactly where the job spent its time by looking at the job card on `/data` — a new "Stage timings" block shows elapsed time, number of items processed (symbols for fetch, dates for backfill), and how many worker threads ran in parallel for each stage.
- Users can see the concrete speed-up achieved by parallel backfill on the job card itself: the Backfill sub-block shows the "per-date sum" (how long the dates would have taken in series) next to the actual wall-clock elapsed time, plus a labeled "X.X× faster than the per-date sum" line.
- Users can hover the info icon next to "Stage timings" and "Concurrency" on the job card to read plain-language glossary definitions without leaving the `/data` page (same copy as the Methodology page).
- On the dashboard (`/`), users can now see the Dow 30 (DIA) index as a fifth line in the "Major indexes & regime" chart alongside SPY, QQQ, IWM, and RSP.

---

## What Changed in the Visible UI

- **`/data` job card — Stage timings block (new)**: After a job's fetch and/or backfill stage completes, a new "Stage timings" section appears on the job card. It contains one sub-block per executed stage (Fetch and/or Backfill). Each sub-block shows: Elapsed (human-readable duration), Symbols or Dates (items processed), and Concurrency (number of parallel workers as "N×"). The Backfill sub-block additionally shows "Per-date sum" and the speed-up ratio. A stage that never ran is fully absent (not shown as zero).
- **`/data` job card — TermInfo tooltips on new labels**: The "Stage timings" section header and the "Concurrency" stat label each carry a new info icon (TermInfo tooltip trigger, placed as a sibling of the label text). Hovering reveals a glossary definition.
- **`/` dashboard — Major-indexes chart**: The chart now renders five lines instead of four, with "Dow 30 (DIA)" added to the legend (1356 bars from 2021-01-04 onward).
- **`/methodology` glossary page**: Two new entries — "stage timings" and "concurrency" — appear in the glossary (served from the config-backed term catalog).

---

## What Old Behavior Changed

- **`/data` job card progress panel**: Previously showed live progress bars + a final summary after completion. Now also includes a per-stage timings block (rendered during and after the job runs). For in-flight jobs, timings for already-completed stages are shown; for stages not yet started, no block appears. The previous behavior (progress bars + summary) is unchanged; the timings block is additive.
- **`/` dashboard Major-indexes chart**: Previously showed 4 index lines (SPY, QQQ, IWM, RSP). Now shows 5 lines with DIA added. The legend is longer by one entry.
- **Multi-date backfill job duration**: Backfill jobs over a multi-date range now complete materially faster (roughly 2× or more) because dates are computed in parallel. The stored output — snapshots, forward returns — is identical to the sequential result; only the wall-clock time changes.
- **Fresh-database seed symbol count**: A fresh installation now loads 159 symbols (previously 158) because the committed DIA bars are included in the seed load.

---

## Not Visible Yet

- **`backfill_workers` config knob**: The new `data_manager.import_chunking.backfill_workers` setting in `config.yaml` controls the number of parallel backfill threads (default: 4). It is boot-validated and takes effect on restart, but there is no UI in the product to read or change this setting — it requires editing `config.yaml` directly.
- **J-22 (expanded ~500-name universe)**: The backend and UI for adding a larger stock universe exist, but the provider's market-cap reference endpoint returns HTTP 401 (walled). No real market-cap data was fetched; no UI change. This journey is honestly blocked until a market-cap-capable provider is reachable.
- **J-23 / J-24 (intraday multi-timeframe charts)**: No intraday data path exists in the provider abstraction or the pipeline. No bars were fetched or displayed; no UI surface was changed.
