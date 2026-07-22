# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy to operate day to day: fast to start, honest about its own state, unrestricted in the historical data it can pull in, and quick to load every page.

## How it has grown

Trendora's core analytics were already built and proven earlier. This chapter turned to running the app day to day: early rounds removed a hidden backfill cap so any date range can be pulled in with an honest zero-work explanation, moved slow calculations to happen once as new data arrives instead of on every visit, made restarts near-instant, and added a real, enforced memory limit with a permanent crash log. A closer look at real usage then found two rough edges — an ordinary data update could briefly make the whole app look crashed, and a long job's progress bar could freeze and falsely claim to be stuck. Both were fixed.

Attention then turned to page speed everywhere: one round fixed a slow Backtest scorecard (35 seconds down to under one second), the next fixed two more slow spots (the home page's trend chart and the data page's coverage calendar, both to about a second), and a later round closed the last known slow spot — the Evidence page's first view after a data update, previously over a minute, now a fraction of a second. That same round's testing caught something more serious, though: during a second big data update run back-to-back, the app could briefly freeze for several minutes and need a manual restart. That round was held back rather than marked finished.

The next round tracked that freeze to how the app handled running low on memory mid-calculation, and fixed it — but shipped without the hands-on proof that the fix held in a real run, so the team paused rather than declare victory, with one more click-through check and a safety-limits consistency check left on the list.

This latest round finally delivered that proof, and closed the safety-limits gap too. The team ran the actual worst-case scenario on the real machine — a full data rebuild immediately followed by another big update, back-to-back in one process — under a cooled, carefully-monitored host, and it ran clean for 18 minutes: no freeze, no slowdown, and comfortable memory to spare. The app's startup scripts now also automatically apply the machine's safety limits every time, whether started the "developer" way or the "production" way, closing a gap where one of the two ways used to skip them entirely. Along the way, testing caught and fixed a genuine bug: a data job interrupted by a crash used to forget all its progress and show "nothing happened" even after processing hundreds of days — it now remembers correctly, though one more click-through check is still needed to fully confirm that in the browser.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any date range with no size cap and an honest explanation when nothing was new to add, trust that even the heaviest back-to-back data updates won't slow down or crash the running app, and rely on the status badge to tell the truth during startup, a data update, or a crash. One remaining click-through check — confirming an interrupted job now shows its true progress — plus a refreshed test report are what's left before this operations-hardening chapter is complete.

_Last updated: 2026-07-22 after iteration 9._
