# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals. This chapter tracks making the running app itself trustworthy day to day — fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest, added a live status badge, and fixed a cluster of low-memory crashes — including cutting one calculation's peak memory from 7.8 GB to 3.1 GB (iteration 50). Iterations 51-57 chased a sometimes-silent status light, sped up the run-history list and the availability chart, and fixed a bug where a busy data-fetch job wrongly told users there was no data at all.

Iteration 58 finished that honesty fix and corrected a wrong health-check record from the round before, but two journeys stayed unfinished: making sure heavy number-crunching always happens ahead of time rather than on the fly, and making sure a very heavy calculation never takes the whole service down. Because some of iteration 58's own test write-ups didn't match their raw measurements, the team switched the next round back to the full, careful review process.

Iteration 59 delivered the project's best engineering yet on exactly those two problems. The Regime Lab research page can no longer crash under memory pressure — if the server is genuinely too busy, only the specific part that couldn't finish shows an honest "temporarily unavailable" note, while everything else keeps showing real numbers. The team also proved, by actually killing and restarting the server, that the Data page still shows correct saved numbers in well under a second afterward. Both checks ran live for the first time this project, and both passed — the server handled over seven hours of heavy load, including a 23-minute background job, with zero errors served.

Even so, neither journey is marked finished yet. The gap is paperwork, not the product: the official checklist has a hole where these two journeys fell through, so nothing formally logged the passing result, and a promised recorded video walkthrough of the fixes still hasn't been made. The team is closing that gap and plans to record the walkthrough next round. Today, six of the eight things the product promises work fully; the last two work in practice but aren't yet officially checked off.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools with an honest "starting up"/"backend unavailable" status. It accepts a backfill over any date range with no hidden cap, serves backtest results instantly from storage, and discloses when it's crunching numbers in the background. The Data page, stock pages, and run-history list all load in well under a second, and the Regime Lab page now keeps working even when the server is very busy, showing an honest "temporarily unavailable" note only for the specific part that couldn't be calculated in that moment.

_Last updated: 2026-08-11 after iteration 59._
