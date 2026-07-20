# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy to operate day to day: fast to start, honest about its own state, and unrestricted in the historical data it can pull in.

## How it has grown

Trendora's core analytics — the rankings, evidence-backed scoring, and every existing page — were already built and proven earlier; this chapter turns to running the app itself. A first stock-take found startup and crash messaging already solid, but backfills that silently did nothing, capped date ranges, heavy calculations computed live on every visit, and no permanent crash log.

The next round fixed the biggest of those gaps: a requested backfill now pulls in every trading day asked for, the old size cap is gone, large requests run safely in visible chunks, and a zero-work backfill says so plainly and survives a reload — after catching and fixing a bug where an interrupted job could show made-up "zero days" results.

The following round made the app faster and more trustworthy to run day to day: heavy calculations are now done once, as new data arrives, instead of on every page view; restarting became near-instant; and starting the app for real now genuinely enforces its memory limit and keeps a permanent crash log. A bug that could have briefly shown wrong numbers for older dates was caught and fixed the same day it appeared.

Most recently, the team closed the one problem that round had left open: an ordinary, everyday data top-up used to leave the Data page's numbers looking stale until a bigger job or a restart happened to fix them — that is now fixed and verified, at no added cost when there's nothing new to add. The team also ran the app through a genuinely heavy, multi-minute data job for the first time and confirmed it stays fast and stays within its memory budget throughout. That same close look turned up two more rough edges that had been hiding in plain sight: an ordinary data update can briefly make the whole app look like it has crashed even though it hasn't, and the on-screen progress for a long job can freeze and falsely claim it's stuck. Both are queued to be fixed next, before the team turns to the last item on this chapter's list — making sure every page only loads what it actually needs.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores exactly as before. An operator can also back-fill any date range in full, submit backfills of any length without a size cap, get an honest, reload-proof explanation whenever a backfill has nothing new to do, see which background calculations a finished job kept fresh, and get a near-instant Data page after a restart. The Data page's coverage figures now also stay accurate after routine, everyday data updates, not only after bigger jobs — all backed by clear startup/crash messaging, a permanent crash log, and a genuinely enforced memory limit.

_Last updated: 2026-07-20 after iteration 3._
