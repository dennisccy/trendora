# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, added a live status badge, fixed a cluster of low-memory crashes, and cut background-refresh memory 71% with identical numbers. Later rounds proved a deliberately-induced memory failure degrades cleanly, fixed slow price-loading, repaired a broken automatic recheck, and — after the owner raised the app's protective memory limit — found and fixed a slow bookkeeping step that re-scanned 26 years of stock-eligibility history on every new day of data, though the app went dark for about 42 minutes while proving it. The round after that bounded two more memory-hungry spots and went a full round without running out of memory even under the heaviest load anyone had thrown at it.

A more recent round fixed the Evidence page's own freeze — over two and a half minutes down to about a hundredth of a second, with the underlying numbers proven unchanged — but its own re-check habit slipped: the automatic check that confirms all eight core capabilities ran too early and was never repeated after later code changes landed, for a second round running.

This latest round picked up the one remaining broken piece: bringing in a single old day of missing price history used to get stuck showing "still working" forever. The exact stuck step is now fixed and proven fast — under 25 seconds, on three separate real runs — but finishing it uncovered two other old, slow cleanup steps sitting right behind it, one of them alone taking 22 minutes, so the whole job still does not reliably finish end to end, for a fifth round running. Two research pages, Factor Lab and Evidence, now use noticeably less computer memory for certain views, with identical numbers shown as before. And for the first time this session, the automatic re-check confirmed two capabilities — accepting a backfill request over any date range, and honestly explaining when nothing new needed fetching — against real, checkable job records rather than page text alone. The app stayed healthy throughout, answering every one of 454 health checks. Next: bound the two remaining slow cleanup steps, then re-run the check on all eight core capabilities.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools. Confirmed working today: requesting a backfill over any date range with an honest explanation when nothing new needed fetching, viewing backtest results without ever waiting for a live recalculation, and seeing an honest notice while the app is crunching numbers in the background. Still needing a fresh check: the boot/crash status badge, pages loading only what they need, and staying responsive during heavy background work. Bringing in a genuinely new, older day of price data remains unreliable, now for a fifth round running, though the team has narrowed the cause down to two specific, named slow cleanup steps.

_Last updated: 2026-08-05 after iteration 48._
