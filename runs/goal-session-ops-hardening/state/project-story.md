# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals. This chapter tracks making the running app itself trustworthy day to day — fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest, added a live status badge, and fixed a cluster of low-memory crashes. Later rounds (51-58) fixed a sometimes-silent status light, sped up two slow pages, stopped a busy data-fetch job from wrongly claiming there was no data, and returned to a fuller review process. Iteration 59 proved the Regime Lab page can no longer crash under memory pressure. Iteration 60 had the app's best day yet, and iteration 61 fixed a timezone mix-up that had wrongly flagged fresh data as stale — bringing seven of the product's eight promises to fully passing, with the Data Manager page refreshing its own numbers automatically.

Iteration 62 fixed the health report's latest-scan-date and stopped the Data Manager page erasing numbers on a single failed background refresh, then ran the project's first real end-to-end rehearsal of its trickiest promises — including a genuine 15-minute background job. That rehearsal exposed cracks in the checking tools themselves: one that could falsely report a broken feature right after a restart, and a rehearsal test that used up its own practice date. Iteration 63 fixed the restart-timing crack and made real, measured progress on the app's last open promise — staying fast to respond during a very long background job — though the count of slow replies rose for a reason nobody could yet explain, and the practice-date problem resurfaced a fourth time.

Iteration 64 fixed that practice-date problem for good: the check now picks its own fresh, unused day automatically every time, instead of a person hand-picking one that the app's own check then uses up. The long-postponed heavy-memory test finally ran and passed. And the open question from last round is now answered — the slow health-check replies during the biggest background job are real and repeat, not a busy computer: 59 of 930 checks were slower than the target, and for the first time one check got no answer at all within five seconds. Seven of the product's eight promises pass fully; the eighth — staying fast to respond during a long background job — stays partly done, with the team now pointed at the one specific slow step that causes it.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools with an honest "starting up"/"backend unavailable" status. It accepts a backfill over any date range with no hidden cap, explains clearly when there's nothing new to fetch, serves backtest results instantly from storage, and discloses when it's crunching numbers in the background. Pages load quickly because they only fetch what they need. The Data Manager page keeps its snapshot and gap counts current on its own. The Regime Lab page keeps working under heavy load. The app almost always answers its own health check quickly even during a heavy background job, though on the busiest moments a handful of replies can still lag or, rarely, not arrive within five seconds.

_Last updated: 2026-08-11 after iteration 64._
