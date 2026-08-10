# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals. This chapter is about making the running app itself trustworthy day to day — fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest, added a live status badge, fixed a cluster of low-memory crashes, and cut background-refresh memory and a Factor Lab crash (iteration 50: 7.8 GB peak memory down to 3.1 GB, failing gracefully instead of crashing). Iterations 51-55 chased a sometimes-silent status light, fixed two slow spots in the heaviest calculation, and closed a bug where a background step silently skipped work while marking itself "done."

Iteration 56 made the run-history list and the availability chart genuinely fast, but introduced a bug: while a data-fetch job ran, the chart wrongly claimed there was no data at all. Iteration 57 fixed that with a calm "updating" note during a job and closed the page's remaining slow spots — enough to finally move a journey forward again: "pages load only what they need" now works.

Iteration 58 finished the honesty fix: the chart no longer says "updating" when no job is running, and can no longer wrongly claim "no data yet" over an already-saved reading. The team also corrected a mistaken health-check record from the previous round with a properly re-measured one. No journey newly passed or failed this round — six of eight still work fully; the same two don't: "aggregates are precomputed at ingest" (one restart-and-reload check still outstanding) and "heavy aggregates never take the service down" (a heavy calculation hit the app's memory limit exactly this round, though nothing broke). Because two of this round's own test write-ups didn't match their raw measurements, the next round will run with the full, more careful review process turned back on.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools with an honest "starting up"/"backend unavailable" status. It accepts a backfill over any date range with no hidden cap, serves backtest results instantly from storage, and discloses when it's crunching numbers in the background. The Data page, stock pages, and run-history list all load in well under a second, and the availability chart now only shows "updating" when a data job is genuinely in progress.

_Last updated: 2026-08-10 after iteration 58._
