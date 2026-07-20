# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy to operate day to day: fast to start, honest about its own state, and unrestricted in the historical data it can pull in.

## How it has grown

Trendora's core analytics — the rankings, the evidence-backed scoring, and every existing page — were already built and proven earlier. This chapter turns to running the app itself; a first stock-take found startup/crash messages and interrupted-job recovery already solid, but backfills that silently did nothing, capped date ranges, live-computed heavy calculations, and no permanent crash log.

The next round fixed the biggest of those gaps: a requested backfill now actually pulls in every trading day asked for, the old one-year size cap is gone, large requests run safely in visible chunks, and a zero-work backfill now says so plainly and survives a reload — after catching and fixing a bug where an interrupted job could show made-up "zero days" results.

This round made the app itself faster and more trustworthy to run. Heavy calculations — dataset coverage, the market-condition reading, and a commonly used research chart — are now done once as soon as new data arrives instead of being recalculated on every page view, and the Data page now names, in plain English, exactly which of these a finished backfill kept fresh. Reopening the app after a restart is now near-instant instead of taking several seconds. Starting the app for real now genuinely enforces its memory limit and keeps a permanent log, so a crash leaves evidence behind. A bug that could have briefly shown wrong numbers for older dates was caught and fixed the same day it appeared, before it reached anyone outside the team. Still open: a rare case where a routine, everyday data refresh can briefly blank the coverage numbers until the next restart, confirming the app holds up during a genuinely heavy job, and making every page load only what it needs — the next targets.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores exactly as before. An operator can also backfill any date range in full, submit backfills of any length without a size cap, get an honest, reload-proof explanation whenever a backfill has nothing new to do, see which background calculations a finished job kept fresh, and get a near-instant Data page after a restart — all backed by clear startup/crash messaging, a permanent crash log, and a memory limit that is now genuinely enforced.

_Last updated: 2026-07-20 after iteration 2._
