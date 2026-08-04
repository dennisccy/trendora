# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, added a live status badge, fixed a cluster of low-memory crashes, and proved the app survives a real memory emergency while cutting background-refresh memory 71% with identical numbers.

Later rounds deliberately pushed a calculation past its memory limit to prove the catch was clean, fixed the underlying price-loading slowness, and repaired a broken automatic recheck that had let some features go unverified.

One round then found a single-day price request could hang forever and a heavy calculation could exhaust memory for several minutes, prompting the owner to raise the app's protective memory limit. Once raised, that heavy calculation ran well within it and the stuck request was fixed — but a new kind of freeze appeared, where the whole app could stop answering for several minutes even with memory to spare.

The next round finally caught that freeze red-handed: a slow bookkeeping step was recalculating 26 years of stock-eligibility history from scratch every time even one new day of data was added. The freeze itself got worse in that round, not better — the app went silent for over 20 minutes.

This latest round built the fix for that exact bookkeeping step — a correct, thoroughly tested change that makes adding a new, recent day of data fast instead of re-checking 26 years of history. But when tried live, it never actually got exercised, because every day left to backfill in this database turns out to be an old gap rather than a new one — and the app went dark again anyway, this time for about 42 minutes, worse than before. The cause is now traced to two other spots that quietly use unlimited memory while someone is simply browsing the Evidence page. Two smaller honesty fixes also landed: a failed data job now always leaves a trace explaining what went wrong, and automated test screenshots now identify themselves so honest look-alikes aren't mistaken for mistakes. Six of the app's eight core capabilities remain proven working; taming those two memory spots is the team's next, most focused target.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools. It accepts a backfill request of any size and explains honestly when nothing new needed fetching, shows a clear boot/crash status badge, keeps pages loading only what they need, serves backtest evidence from storage rather than a live recompute, and discloses live background-compute activity whenever it is running. Bringing in a genuinely new day of price data and staying responsive during heavy background work are both still unreliable — the team now knows exactly which two code spots are responsible and is working to fix them next.

_Last updated: 2026-08-04 after iteration 45._
