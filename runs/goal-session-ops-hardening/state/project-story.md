# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, added a live status badge, fixed a cluster of low-memory crashes, and cut background-refresh memory 71% with identical numbers. Later rounds proved a deliberately-induced memory failure degrades cleanly, fixed slow price-loading, repaired a broken automatic recheck, and — after the owner raised the app's protective memory limit — found and fixed a slow bookkeeping step that re-scanned 26 years of stock-eligibility history on every new day of data, though the app went dark for about 42 minutes while proving it. The round after that bounded two more memory-hungry spots and went a full round without running out of memory even under heavy load.

Iteration 47 fixed the Evidence page's own freeze — over two and a half minutes down to about a hundredth of a second, with the underlying numbers proven unchanged — but its own habit of re-checking all eight core capabilities slipped, running too early and never repeating after later code changes landed, for a second round running.

Iteration 48 picked up the one remaining broken piece: bringing in a single old day of missing price history used to get stuck showing "still working" forever. It fixed the exact stuck step — proven fast, under 25 seconds on three real runs — but uncovered two other old, slow cleanup steps sitting right behind it, one of them alone taking 22 minutes, so the whole job still didn't reliably finish end to end. For the first time this session, though, the automatic re-check confirmed two capabilities — accepting a backfill request over any date range, and honestly explaining when nothing new needed fetching — against real, checkable job records rather than page text alone.

This latest round, iteration 49, bounded those two remaining slow cleanup steps: a historical backfill now genuinely finishes inside its 20-minute promise, proven on three separate real runs. But finishing that check surfaced a serious new problem: opening the Factor Lab research page while that same backfill is finishing can crash the whole app — and it did, for nearly 13 minutes, during this round's own testing. That crash traces to a different, older research page nobody has fixed yet, not to this round's own work. Next: stop that page from crashing the app, then re-run the check on all eight core capabilities against a healthy app.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools. It accepts a backfill request over any date range and honestly explains when nothing new needed fetching, with no hidden cap on how large a range can be requested. It serves backtest results instantly from stored data, never making a user wait on a live recalculation. And it discloses honestly when it is crunching numbers in the background, instead of leaving a page looking broken. Bringing in a genuinely new, older day of price data now finishes fast enough on its own, but is not yet proven safe when someone browses other research pages at the same time — that is the team's next target.

_Last updated: 2026-08-05 after iteration 49._
