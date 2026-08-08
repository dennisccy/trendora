# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals. This chapter is about making the running app itself trustworthy day to day — fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest, added a live status badge, fixed a cluster of low-memory crashes, and cut background-refresh memory 71%. Iterations 48-49 fixed a stuck history-loading step and its cleanup — then testing found the Factor Lab research page crashing the whole app for nearly 13 minutes when opened during a backfill.

Iteration 50 cut that page's peak memory from 7.8 GB to 3.1 GB and taught it to fail one number at a time instead of taking the app down — but the status light still sometimes answered late during heavy jobs, once going silent for 17.5 minutes.

Iteration 51's fix — pausing the background work more often — made the late-answering problem worse, though it did prove the app survives a deliberately-broken calculation without needing a restart.

Iteration 52 found the real cause: two spots inside the heaviest calculation each blocked the app for a full second or more. Splitting a giant sort into pieces and briefly pausing the app's own memory cleanup fixed both, and the status light nearly stopped missing checks during a heavy data job — but the round's own proof-checking ran just before the fix was written, so the scoreboard couldn't move yet.

Iteration 53 finished that job and supplied the missing proof. Two more background steps — working out which stocks currently qualify, and reading the market's risk level shown on the Dashboard — were loading a stock's entire multi-decade price history just to read its last few months; reading only the needed window instead made the risk-level step 36 times faster and closed both steps' contribution to the status light going quiet. For the first time since iteration 45, a journey moved fully forward: the app's honest "starting up" and "backend unavailable" messages finally got their first real proof, checked against the app's own logs and database rather than taken on faith. A small one-day gap the same check found in the new math is harmless today but not yet proven safe in general, and two other reliability journeys are still not fully proven — both carried into the next round, alongside making two disagreeing internal reports agree with each other.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools. It accepts a backfill over any date range with no hidden size cap and explains honestly when nothing new needed fetching. It serves backtest results instantly from storage and discloses honestly when it's crunching numbers in the background. It also shows an honest "starting up" message while booting and a "backend unavailable" message if it goes down, marking any interrupted job clearly once it's back — proven for the first time this round.

_Last updated: 2026-08-08 after iteration 53._
