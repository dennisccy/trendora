# Iteration 23 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-23
**Date:** 2026-06-07
**Written by:** developer

---

## Features Implemented

- **Expand-universe job (the operator path to grow the universe)**: On the Data Manager (`/data`) there is a new job kind, **Expand universe**. Running it screens the committed ~548-name candidate pool against the config rules (minimum market cap, minimum dollar-volume, minimum share price) over a chosen data source, and grows the scored universe to the names that pass. It runs as a chunked, resumable import — the same machinery the existing fetch uses — so it shows live "chunk X of N" progress and can be resumed if the data source rate-limits it.
- **See exactly who passed and who was dropped**: When the job finishes (or as it runs), the job card shows how many candidates **passed** and lists every **omitted** candidate with a plain-language reason — e.g. "market_cap … below the threshold", "price … below $10", "no_market_cap" (the source had no market cap for it), or "fetch_failed". Nothing is ever invented to force a pass.
- **Only market-cap-capable sources can run an expand**: The screen needs each candidate's market cap. Sources that cannot provide it (Alpha Vantage, Stooq) are shown **disabled with a reason** in the source picker, and the Start button is blocked — and the backend rejects such a request too. Yahoo, Tiingo, and Finnhub can supply market cap and are selectable.
- **The grown universe shows up in one place**: After a successful expand, the Coverage panel's **Universe** count reflects the new membership, and the Universe-Selection methodology page shows the same number — one source, no double-counting.

## Changed Behavior

- **Data Manager job kinds**: Previously the job picker offered Fetch / Backfill / Fetch + backfill. Now it also offers **Expand universe**. The import-source picker, which previously appeared only for fetch jobs, now also appears for an expand job (with the ineligible-source disabling described above).
- **Run history**: An expand run now appears in the Data Manager's run history with its kind, status, and a summary of how many candidates passed vs. were omitted.
- **Universe membership source**: The app now treats a committed universe screen-result file (`universe.json`) as the single source of universe membership when it is present — growing the universe from the recorded screen. When that file is absent (the current state on this machine), behavior is unchanged and the universe is the 122 names from the config file.

## Backend-Only Items

- None. Every backend capability added this iteration has corresponding UI on `/data` (the Expand option, the eligibility gating, the passers + omitted-with-reason block, and the grown Universe count).

## Incomplete Items

- None of the iteration's in-scope items are deferred. The one item that cannot be *demonstrated live on this machine* is the **live market-cap expansion outcome** — see Known Limitations. Per the iteration's non-halting contract, the expand machinery is fully proven offline with an injected (test) data source; the live outcome is recorded honestly when the real feed is unreachable and does not block anything.

## Config and Environment Changes

- **`universe.filters.adv_window_days`** — a new optional setting in `config.yaml` controlling how many trading days the average-daily-dollar-volume liquidity measure uses. Default: `63` (about three months — the value the offline screen already used). Optional, so existing configs need no change.
- No new environment variables, no database migration (the `import_checkpoints` table already existed from iteration 22; only a test's expected-table list was corrected).
- No secrets added. A pasted session API key (for a key-gated source) is still held in memory for the request only and is never written to disk, the database, the run log, or any response — the same guarantee as the existing fetch/resume, now also covering the expand job's error messages.

## Known Limitations

- **The live universe expansion cannot complete on this machine.** Growing the universe for real requires fetching each candidate's market cap from a live data provider, and those feeds (Yahoo, Stooq, Tiingo) are blocked / rate-limited from this host (a long-standing environment constraint). When that happens, the expand job records the outcome **honestly** — every candidate omitted with a "could not fetch market cap" reason, or a graceful "rate-limited — resumable" pause — and never invents a member, price, or market cap. This is by design and is **not** a failure of the feature: the expand logic, the screen, the eligibility gate, and the screen-result display are all proven with an injected test data source. Because the live feed is walled, the universe count stays at 122 on this machine until a reachable feed (or an injected source in testing) produces passing members.
- The expand job only adds committed price bars (insert-new-only, never overwriting an existing bar) and writes the universe membership file. It does **not** regenerate any existing scanner snapshot, score, or forward-return — the historical evidence is left untouched.
