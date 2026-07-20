# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy to operate day to day: fast to start, honest about its own state, and unrestricted in the historical data it can pull in.

## How it has grown

Trendora's core analytics — the rankings, evidence-backed scoring, and every existing page — were already built and proven earlier; this chapter turned to running the app itself, starting from a stock-take that found backfills which silently did nothing, capped date ranges, calculations computed live on every visit, and no permanent crash log.

Two rounds then closed the biggest of those gaps: backfills now pull in every requested day with no size cap, running safely in visible chunks and saying plainly when there's nothing new to do; heavy calculations now happen once, as new data arrives, restarts became near-instant, and the app genuinely enforces its memory limit with a permanent crash log. A bug that could leave the Data page's numbers looking stale after a routine update was also caught and fixed, at no added cost when there's nothing new to add.

That same close look then surfaced two rough edges hiding in plain sight: an ordinary data update could briefly make the whole app look crashed even though it hadn't, and a long job's on-screen progress could freeze partway through and falsely claim to be stuck. This latest round fixed both. The status badge now tells the truth every time — an everyday update never falsely flips it to "Backend unavailable," and when new data lands for the benchmark stock ahead of processing, the badge instead shows a calm "Snapshot pending" message naming what's pending and what to do about it, while real crashes and a never-set-up database still show the true warning, unchanged. The stuck-progress bug is fully fixed too, after a same-round follow-up closed a gap the first pass missed.

With those fixed, everything built so far holds up cleanly under real use. The one piece of this chapter still to come is making sure every page loads quickly using only the data it actually needs — the team's next target.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores exactly as before. An operator can also back-fill any date range with no size cap, get an honest, reload-proof explanation when there's nothing new to add, and get a near-instant Data page after a restart — backed by clear startup/crash messaging, a permanent crash log, and a genuinely enforced memory limit. The Data page's coverage figures stay accurate after any update, and the top-bar status badge can now be fully trusted: it never falsely claims the backend is down, and a big job's live progress never freezes or falsely appears stuck.

_Last updated: 2026-07-20 after iteration 4._
