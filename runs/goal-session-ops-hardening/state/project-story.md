# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy to operate day to day: fast to start, honest about its own state, unrestricted in the historical data it can pull in, and quick to load every page.

## How it has grown

Trendora's core analytics were already built and proven earlier; this chapter turned to running the app day to day. Early rounds removed a hidden backfill cap, moved slow calculations to happen once as new data arrives instead of on every visit, made restarts near-instant, added a real enforced memory limit with a permanent crash log, and fixed two rough edges where an ordinary data update could make the app look crashed or a job's progress bar could freeze and falsely claim to be stuck.

Attention then turned to page speed everywhere — fixing a slow Backtest scorecard, a slow trend chart, a slow coverage calendar, and the Evidence page's slow first view — until testing caught something bigger: two big data updates run back-to-back could briefly freeze the app for several minutes and force a manual restart. The team held that round back rather than call it finished. The next round tracked the freeze to how the app handled running low on memory mid-calculation, fixed it, and proved the fix under the real worst case — a full data rebuild immediately followed by another big update, back-to-back in one process, running clean with room to spare. A later round proved, by deliberately crashing the app mid-update a third time, that an interrupted job's history now honestly shows the real progress it made rather than pretending nothing happened.

This latest round went back to re-check page-loading speed now that startup itself has been hardened. The re-check itself came back clean — the app still starts in about a second and a half, and a code review found no slow shortcuts hiding on any of the pages it checked. But while that re-check was running, the app hit its own memory safety limit twice in the background, and two advanced pages briefly failed to load as a result — a real, live instance of the rare risk the team has been tracking and deliberately deferring, now caught happening for real instead of just in theory. Rather than call the chapter finished, the team paused to bring in extra scrutiny before deciding what to do about it.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and an honest explanation when nothing was new to add, trust that even the heaviest back-to-back data updates won't slow down or crash the running app, see the status badge tell the truth during startup, a data update, or a crash, and trust that if the app does crash mid-update, the interrupted job honestly shows the real progress it made. One rare risk remains open: occasionally, running low on background memory can briefly stop a couple of advanced pages from loading — the team is deciding how to fix or limit that before calling this chapter complete.

_Last updated: 2026-07-22 after iteration 11._
