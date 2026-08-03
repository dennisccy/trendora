# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, added a live status badge, fixed a cluster of low-memory crashes, and proved the app survives a real memory emergency while cutting background-refresh memory 71% with identical numbers.

Later rounds deliberately pushed a calculation until it ran out of memory (confirming a clean catch, but a freeze afterward), fixed the underlying price-loading slowness, and repaired a broken automatic recheck that had let some features go unverified — re-confirming the working set each time.

One round then put that repaired check to real use and found genuine trouble: a single-day price request could hang forever, and a heavy calculation ran the app out of memory for several minutes. The team traced the shortage back through ten days of history, admitted its own memory-saving attempt had made things slightly worse, and paused for the owner to decide how to fit thirty years of price history inside the app's protective memory limit.

Once the owner raised that limit, the fix proved out — the heavy calculation now runs well within the new limit — and the stuck single-day request was fixed too. But a new kind of trouble appeared: even with plenty of memory free, a heavy calculation could still get stuck and the whole app would stop answering for several minutes, a different and still-unresolved problem.

This latest round finally caught that freeze red-handed, capturing a live snapshot of exactly what the app was stuck on: a slow bookkeeping step that recalculates 26 years of stock-eligibility history from scratch every time even one new day of data is added. Two smaller honesty fixes landed too — failed jobs now explain what really went wrong, and the "Retry" button fails cleanly instead of with a blank error. But the freeze itself got worse, not better: the app stopped answering everything for over 20 minutes and had to be force-restarted, and the round's first attempt to bring in a genuinely new day of data ran straight into that freeze. Six of the app's eight core capabilities remain proven working; fixing the freeze and finishing the new-data case are the team's current focus.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools. It accepts a backfill request of any size and explains honestly when nothing new needed fetching, shows a clear boot/crash status badge, keeps pages loading only what they need, always serves backtest evidence from storage rather than a live recompute, and discloses live background-compute activity whenever it is running. Bringing in a genuinely new day of price data and staying responsive during a heavy background calculation are both still unreliable — the team now knows exactly why the calculation gets stuck and is working on a fix.

_Last updated: 2026-08-03 after iteration 44._
