# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy to operate day to day: fast to start, honest about its own state, unrestricted in the historical data it can pull in, and quick to load every page.

## How it has grown

Trendora's core analytics were already built and proven earlier. This chapter turned to running the app day to day: early rounds removed a hidden backfill cap so any date range can be pulled in with an honest zero-work explanation, moved slow calculations to happen once as new data arrives instead of on every visit, made restarts near-instant, and added a real, enforced memory limit with a permanent crash log.

A closer look at real usage then found two rough edges — an ordinary data update could briefly make the whole app look crashed, and a long job's progress bar could freeze and falsely claim to be stuck. Both were fixed: the status badge now tells the truth every time, and the progress-freeze bug is gone.

Attention then turned to page speed everywhere. One round fixed a slow Backtest scorecard (35 seconds down to under one) by saving its calculation the moment new data lands. The next round fixed two more slow spots — the home page's trend chart and the data page's coverage calendar — both now loading in about a second, and cleared up a scary-looking "minutes to load" report that turned out to be a false alarm from an overloaded test machine.

The most recent round closed the very last known slow spot: the Evidence page's first view right after a data update, previously a wait of over a minute, now loads in a fraction of a second because its figures are calculated the moment the update finishes rather than the moment someone opens the page. That fix works correctly and was confirmed live. But testing this round also caught something more serious: during a second big data update run back-to-back, the running app can briefly freeze and stop responding for several minutes, needing a manual restart to recover — the opposite of the "honest, always-responsive" promise this whole chapter of work is about. Because of that finding, this round is paused for a closer look rather than marked finished. Right now, backfilling any date range, the honest zero-work messaging, and truthful startup/crash status are all confirmed working; the team is investigating and fixing the heavy-update freeze before this chapter can close.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any date range with no size cap and get an honest explanation when there's nothing new to add, and the status badge can be trusted to describe what's really happening during startup or a crash. The Backtest page's scorecard loads in under a second, most other pages load quickly too, and the Evidence page's figures are now ready the instant a data update finishes. One reliability gap is currently being investigated: a rare freeze during back-to-back heavy data updates that needs to recover on its own instead of requiring a manual restart.

_Last updated: 2026-07-21 after iteration 7._
