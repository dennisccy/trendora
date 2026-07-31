# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, added a live status badge, fixed a cluster of low-memory crashes, rewrote the Backtest page into small running totals with identical output, fixed the production start script, and gave every research page an honest "still computing" message with a Retry button instead of a blank spinner.

A later round proved the app survives a genuine low-memory emergency, timed the health check under load for the first time, and rewrote the Data page's background refresh to work through the stock list in small batches, cutting peak memory 71% with identical numbers.

One round closed the last known code gap behind the "heavy work never takes the service down" promise — multi-day imports now read the price-history table from disk once instead of twice — and ran a real 70-second stress test of the heaviest background calculation live, confirming the health check answered every poll and writing down the app's exact memory headroom. The next round finally proved that memory-sharing trick is genuinely being used, re-ran the heaviest calculation through its real trigger path, and caught and corrected a backwards headline number in its own memory comparison before it could mislead anyone.

This latest round tackled the hardest part of the promise directly: it deliberately pushed a background calculation until it ran out of memory, and watched the app catch that failure cleanly, in exactly the right internal step, while the app kept answering every health check and every saved-result request without a hiccup. Along the way the team also fixed the automated test checker so it no longer wrongly reports "broken" when the backend is simply switched off, fixed a backend testing switch that had been working backwards, and proved for the first time — with a real hard restart — that the app's status screens tell the truth after a crash. But the round also found a new problem: at a very tight memory limit the app can still freeze for several minutes after a job finishes, traced to a piece of code that loads millions of price rows into memory all at once. Fixing that one spot is now the very next target — it is the last piece standing between "heavy work never takes the service down" and being fully proven.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools (Regime Lab, Factor Lab, Market Phase & Severity Lab, Regime x Phase x Factor, Severity-velocity). An operator can back-fill any historical range with an honest explanation when there's nothing new to add, and the status badge stays truthful through startup, updates, or a crash — now proven with a real hard restart. Heavy calculations are prepared in advance, restarts serve stored numbers immediately, the Backtest page always serves saved results, and every research page shows an honest "still working" message instead of a blank screen during a slow load. The last piece being proven is that heavy background work can never crash or freeze the service — this iteration got very close and pinpointed the exact remaining fix.

_Last updated: 2026-07-31 after iteration 39._
