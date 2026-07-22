# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy to operate day to day: fast to start, honest about its own state, unrestricted in the historical data it can pull in, and quick to load every page.

## How it has grown

Trendora's core analytics were already built and proven earlier. This chapter turned to running the app day to day: early rounds removed a hidden backfill cap so any date range can be pulled in with an honest zero-work explanation, moved slow calculations to happen once as new data arrives instead of on every visit, made restarts near-instant, and added a real, enforced memory limit with a permanent crash log. A closer look at real usage then found two rough edges — an ordinary data update could briefly make the whole app look crashed, and a long job's progress bar could freeze and falsely claim to be stuck. Both were fixed.

Attention then turned to page speed everywhere: one round fixed a slow Backtest scorecard (35 seconds down to under one second), the next fixed two more slow spots (the home page's trend chart and the data page's coverage calendar), and a later round closed the Evidence page's slow first view after a data update. That same round's testing caught something more serious: during a second big data update run back-to-back, the app could briefly freeze for several minutes and need a manual restart. The team held that round back rather than call it finished.

The next round tracked the freeze to how the app handled running low on memory mid-calculation and fixed it, then proved the fix under the real worst case — a full data rebuild immediately followed by another big update, back-to-back in one process — running clean for 18 minutes with room to spare, and closed a gap where one of the app's two startup methods used to skip the machine's safety limits entirely. That round also caught and fixed a genuine bug along the way: a data job interrupted by a crash used to forget its progress and claim "nothing happened" even after processing hundreds of days.

This latest round finally proved that fix works. The team deliberately crashed the running app mid-update a third time and read the app's own history page afterward — it correctly showed the real progress the interrupted job had made, not a false "nothing happened." Every other previously-working capability was re-checked and still holds. That closes every checkbox in this operations-hardening effort except one: a known, rare slow-and-crash risk on one advanced page, which is waiting on a deliberate decision about how much to invest in fixing versus deferring, plus a couple of recorded walkthrough videos still to make.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any date range with no size cap and an honest explanation when nothing was new to add, trust that even the heaviest back-to-back data updates won't slow down or crash the running app, see the status badge tell the truth during startup, a data update, or a crash, and now also trust that if the app does crash mid-update, the interrupted job honestly shows the real progress it made rather than pretending nothing happened.

_Last updated: 2026-07-22 after iteration 10._
