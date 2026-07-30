# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, added a live status badge, fixed a cluster of low-memory crashes, rewrote the Backtest page into small running totals with identical output, fixed the production start script, and gave Regime Lab an honest "Still computing" message with a Retry button instead of a blank spinner.

A later round proved the app survives a genuine low-memory emergency — a throwaway test starved the backend during its heaviest calculation and it recovered cleanly — and timed the health check under load for the first time, though the app still loaded its entire price history into memory during startup housekeeping. The Data page's background refresh was then rewritten to work through the stock list in small batches instead of all at once, cutting peak memory 71% with identical numbers, and the last four research pages gained the same honest loading message Regime Lab already had.

One more round closed the last code gap behind the "heavy work never takes the service down" promise — multi-day imports now read the price-history table from disk once instead of twice — and ran a real 70-second stress test of the heaviest background calculation live for the first time, confirming the health check answered every single poll and writing down the app's exact memory headroom (57% to spare). A double-check that same round caught and fixed a subtle way the new memory-sharing trick could have quietly held onto over a gigabyte of memory forever after a rare failure.

This latest round finally proved that memory-sharing trick is genuinely being used, not just sitting unused in the code, and re-ran the heaviest calculation through its real trigger path — a genuine data import, not a shortcut — while keeping the health check answering correctly for the whole several-minute run. A careful double-check also caught and corrected a backwards headline number before it could mislead anyone: the round's own memory comparison had reported the wrong conclusion, now fixed. The one thing still missing is the hardest part of the promise: deliberately pushing that background work until it truly runs out of memory, to prove the app survives that gracefully. That is the very next target.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools (Regime Lab, Factor Lab, Market Phase & Severity Lab, Regime x Phase x Factor, Severity-velocity). An operator can back-fill any historical range with an honest explanation when there's nothing new to add, and the status badge stays truthful through startup, updates, or a crash. Heavy calculations are prepared in advance, restarts serve stored numbers immediately, the Backtest page always serves saved results, every research page shows an honest "still working" message instead of a blank screen during a slow load, and multi-day data imports now read the price history from disk only once instead of twice. Proving the app survives truly running out of memory during heavy background work is the last item before this chapter's promises are all fully proven.

_Last updated: 2026-07-30 after iteration 38._
