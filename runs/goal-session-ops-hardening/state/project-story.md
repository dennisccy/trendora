# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, added a live status badge, fixed a cluster of low-memory crashes, and gave research pages an honest "still computing" message instead of a blank spinner. A later round proved the app survives a genuine low-memory emergency and cut background-refresh memory 71% with identical numbers, then closed the last known gap behind the "heavy work never takes the service down" promise.

A subsequent round deliberately pushed a background calculation until it ran out of memory, watched the app catch that failure cleanly, but found it could still freeze for minutes afterward — traced to a piece of code loading millions of price rows into memory all at once. The next round fixed that spot to load history in smaller pieces, but its own automatic feature-recheck looked at the wrong web address and left several working features unverified rather than confirmed.

Last round fixed that testing gap and freshly re-checked five features as working again — but the two features that round was actually working on slipped through completely unchecked, a gap the team flagged rather than hide.

This latest round put the repaired testing check to its first real use, and it immediately found trouble: requesting a single day of price history can now get stuck forever on the Data page showing nothing, and a heavy background calculation ran the app out of memory, taking the status badge, the Backtest page, and the Data page offline for several minutes. The team traced the memory problem back through ten days of history — it was already there before this round began — and found its own attempt to trim memory in the price-loading code actually made things very slightly worse, not better, and reported that honestly rather than claiming a fix. The six other features re-checked this round all still work. Work is paused while the product owner decides how to fit thirty years of price history inside the app's protective memory limit.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools. It accepts a backfill request of any size and explains honestly when nothing new needed fetching, shows a clear boot/crash status badge, keeps pages loading only what they need, always serves backtest evidence from storage rather than a live recompute, and discloses live background-compute activity whenever it is running. Two features are currently broken and being fixed: starting a single-day price backfill can hang forever with no error, and a heavy background calculation can exhaust the app's memory and take pages offline for several minutes.

_Last updated: 2026-07-31 after iteration 42._
