# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — and this chapter of its story is about making the running app itself trustworthy to operate day to day: fast to start, honest about what it is doing, and unrestricted in the historical data it can pull in.

## How it has grown

Trendora's core analytics — the rankings, the evidence-backed scoring, and all the existing pages — were already built and proven in an earlier chapter of this project. This new chapter turns attention to running the app itself: starting in seconds, being honest about its own state, doing the heavy number-crunching in advance instead of on the spot, and letting the owner pull in any stretch of historical data without hitting an arbitrary limit.

This iteration was the very first checkpoint for that new chapter — a careful "where do we stand today" check, with no changes made yet. The results were a mix. Good news: the app already shows a clear "starting up" message with progress, already shows a clear "crashed" message if the backend goes down, and already correctly marks an interrupted data job instead of leaving it stuck — all inherited from earlier work. Not yet working: pulling in a full month of historical data currently creates no new snapshots at all (a leftover monthly-only rule quietly blocks it), there is still a cap on how large a historical data request can be, the heavy calculations are still recomputed on the spot instead of stored in advance (making a few pages take ten seconds or more right after new data comes in), and the app does not yet keep a permanent written record of what happened when it crashes.

So today, none of the five planned improvements are fully finished, though the honest-startup-and-crash-messages one is nearly there, missing only a saved log file and a firm memory limit. The team's next move is to fix the historical-data-loading limit together with the long-range-request cap, since they share the same underlying cause, before turning to the storage and page-speed work.

## What it can do today

The product still lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores exactly as before. The new operational promises are not yet delivered, though the app already shows clear "starting up" and "crashed" messages and correctly recovers an interrupted data job after a restart.

_Last updated: 2026-07-19 after iteration 0._
