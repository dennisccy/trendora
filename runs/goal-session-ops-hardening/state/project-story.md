# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy to operate day to day: fast to start, honest about its own state, unrestricted in the historical data it can pull in, and quick to load every page.

## How it has grown

Trendora's core analytics were already built and proven earlier. This chapter turned to running the app day to day: early rounds removed a hidden backfill cap so any date range can be pulled in with an honest zero-work explanation, moved slow calculations to happen once as new data arrives instead of on every visit, made restarts near-instant, and added a real, enforced memory limit with a permanent crash log.

A closer look at real usage then found two rough edges — an ordinary data update could briefly make the whole app look crashed, and a long job's progress bar could freeze and falsely claim to be stuck. Both were fixed: the status badge now tells the truth every time, and the progress-freeze bug is gone.

Attention then turned to page speed everywhere. One round fixed a slow Backtest scorecard (35 seconds down to under one) by saving its calculation the moment new data lands. The next round fixed two more slow spots — the home page's trend chart and the data page's coverage calendar — both now loading in about a second, and cleared up a scary-looking "minutes to load" report that turned out to be a false alarm from an overloaded test machine.

A later round closed the last known slow spot: the Evidence page's first view right after a data update, previously a wait of over a minute, now loads in a fraction of a second because its figures are calculated the moment the update finishes. That fix worked correctly — but testing the same round caught something more serious: during a second big data update run back-to-back, the app could briefly freeze and stop responding for several minutes, needing a manual restart to recover. That round was held back rather than marked finished, and the team paused to investigate.

The next round went after that freeze directly. The root cause turned out to be how the app handled running low on memory while catching up on background calculations after an update: one low-memory hiccup used to make it immediately try the next calculation anyway, piling pressure on top of pressure. The fix makes it stop that one step, clean up, and move on instead. A careful second pass over the work also caught and fixed a broken safety test that had been silently reporting "all good" while its real checks were missing. A live rehearsal of the exact freeze scenario — a big data reload immediately followed by another — ran clean with a comfortable memory cushion. What's still missing is the usual hands-on run-through of the app itself to confirm the fix holds in practice, and a re-check that nothing else quietly broke along the way — both are the very next items on the list, alongside making sure the app's safety limits are consistently switched on every time it starts.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any date range with no size cap and get an honest explanation when there's nothing new to add, and the status badge can be trusted to describe what's really happening during startup or a crash. The Backtest page's scorecard loads in under a second, most other pages load quickly too, and the Evidence page's figures are ready the instant a data update finishes. The fix for the back-to-back-update freeze has been built and passed its written checks and a live rehearsal, but the team hasn't yet re-confirmed it by clicking through the app itself — that confirmation, plus a final safety-limits check, is what's left before this chapter can close.

_Last updated: 2026-07-22 after iteration 8._
