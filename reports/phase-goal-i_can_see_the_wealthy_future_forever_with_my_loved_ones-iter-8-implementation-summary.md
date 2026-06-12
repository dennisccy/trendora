# Iteration 8 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8
**Date:** 2026-06-12
**Written by:** developer

---

## Features Implemented

- **Faster multi-date backfills (J-53)**: When you grow the dataset over a date range on the Data
  Manager (`/data`), the work of building the per-date snapshots now runs on several worker threads at
  once instead of one date after another. The result is the same data as before (proven identical), but
  the backfill finishes materially faster — roughly 2× or more on a multi-date range.
- **Per-stage job timings (J-53)**: Each fetch+backfill job now reports, on its `/data` job card, exactly
  where it spent its time — a Fetch section and a Backfill section, each with elapsed time, how many
  items it processed (symbols for fetch, dates for backfill), and how many workers ran in parallel. The
  backfill section also shows the "per-date sum" (how long the dates would have taken one at a time) next
  to the actual elapsed time, so the speed-up is visible right on the card.
- **New "Stage timings" and "Concurrency" help tooltips**: The two new labels carry info-tooltips that
  read plain-language definitions from the shared glossary (the same source the Methodology page uses).
- **Dow 30 (DIA) now on the dashboard index chart (J-44)**: A one-time real-data fetch pulled the full
  history of the DIA index ETF and committed it into the dataset, so the dashboard's "Major indexes &
  regime" chart now shows five lines including "Dow 30 (DIA)" instead of four.

---

## Changed Behavior

- **Data Manager job card**: Previously showed live progress + a final summary. Now also shows a
  per-stage timings block (fetch vs backfill: elapsed, items, concurrency, and the backfill speed-up).
- **Multi-date backfill**: Previously processed each date sequentially. Now computes the dates
  concurrently while still writing to the database one date at a time, in order — same stored
  snapshots/forward-returns, faster.
- **Dashboard major-indexes chart**: Previously 4 index lines (SPY/QQQ/IWM/RSP). Now 5, with DIA added.
- **Fresh-database seed load**: Now loads 159 symbols (was 158) because DIA's committed bars are
  included.

---

## Backend-Only Items

- None. Every backend change is surfaced in the UI (the stage timings on the `/data` job card; DIA on
  the dashboard chart).

---

## Incomplete Items

- **J-22 (expanded ~500-name universe)**: The one-shot best-effort fetch was attempted once. The daily
  price feed is reachable, but the provider's **market-cap** reference (required by the universe screen)
  returned HTTP 401 (walled). With no real market cap available, the screen cannot add members without
  fabricating, so this journey is recorded as **honestly blocked (NA)** — non-vetoing per the goal. It
  auto-unblocks with no code change once a market-cap-capable provider is reachable (or via the
  Data Manager's Expand-universe job).
- **J-23 / J-24 (intraday multi-timeframe seed + chart selector)**: Recorded as **honestly blocked
  (NA)** — non-vetoing. There is no buildable fetch path yet (the data provider has no intraday
  interval support and the timeframe-aware store is not built; building it was out of scope this
  iteration), so no intraday bars were fetched or fabricated.

---

## Config and Environment Changes

- `config.yaml` → `data_manager.import_chunking.backfill_workers` — NEW. Controls how many worker
  threads the multi-date backfill uses (default: `4`; must be `>= 1`, where `1` means sequential). It is
  boot-validated like the other import tunables (an invalid value fails startup loudly — no silent
  default).
- `config.yaml` → `methodology.terms` — two NEW glossary entries (`stage timings`, `concurrency`) that
  back the new info-tooltips and appear on the Methodology glossary page.
- `apps/backend/data/seed/prices/DIA.csv` — NEW committed real-data file (1356 daily bars for DIA,
  2021-01-04 → 2026-05-28). This is the only data file added; no secrets, no `.env`, no database file.

---

## Known Limitations

- **The ≥~2× speed-up is advisory evidence, not a hard test gate.** It is shown on the job card (elapsed
  vs per-date sum) and in the committed benchmark script, but the automated test suite does NOT assert a
  wall-clock ratio (that would be flaky on a shared machine). The hard guarantee that IS tested is that
  the parallel output is byte-for-byte identical to the sequential output.
- **The backend must be restarted** for the new stage-timings field to appear in job payloads (the
  field was added to the in-memory job record this iteration).
- **Provider reality for the one-shot fetch**: Only DIA's daily history was reachable this run; the
  market-cap feed (J-22) and any intraday feed (J-23/J-24) were not. Those journeys stay honestly NA and
  do not block completion.
