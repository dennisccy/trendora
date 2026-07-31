# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, added a live status badge, fixed a cluster of low-memory crashes, rewrote the Backtest page into small running totals with identical output, fixed the production start script, and gave every research page an honest "still computing" message with a Retry button instead of a blank spinner.

A later round proved the app survives a genuine low-memory emergency, timed the health check under load for the first time, and rewrote the Data page's background refresh to work through the stock list in small batches, cutting peak memory 71% with identical numbers.

One round closed the last known code gap behind the "heavy work never takes the service down" promise, and the round after that finally proved the memory-sharing trick was genuinely used, catching and correcting a backwards headline number before it could mislead anyone. The round after that deliberately pushed a background calculation until it ran out of memory and watched the app catch that failure cleanly while still answering every request — but it also found the app could still freeze for several minutes afterward at a very tight memory limit, traced to a piece of code loading millions of price rows into memory all at once.

This latest round fixed exactly that spot — the Data page's supporting calculations now read price history in small batches instead of all at once — and re-ran the freeze test: it did not recur. The team also made the crash-recovery progress count on the Data page far more accurate after a hard restart (off by one day now, instead of off by a factor of ten). But the round's honest headline is a different problem: the automatic re-check of seven already-working features didn't actually run this time — it looked at the wrong web address and wrongly reported "the app is down" even though it was answering normally — so several previously-confirmed features (backfill, the status badge, precomputed calculations, and fast page loads) now need a fresh check before they can be promised again. Nothing is known to be broken; they simply weren't tested this round. The next round's first job is to fix that testing check and re-verify everything, then track down what still froze the server during the toughest version of the memory test.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools (Regime Lab, Factor Lab, Market Phase & Severity Lab, Regime x Phase x Factor, Severity-velocity). Backtest evidence always comes from stored results, never a live recompute, a live indicator shows when background work is running, and there is no artificial limit on how large a historical backfill request can be. Several other features — the honest startup/crash status badge, ahead-of-time calculations, and "still working" messages on research pages — are believed to still work but are due for a fresh check after this round's testing gap. The last piece being proven, that heavy background work can never crash or freeze the service, just had its main suspected cause fixed and is being re-tested.

_Last updated: 2026-07-31 after iteration 40._
