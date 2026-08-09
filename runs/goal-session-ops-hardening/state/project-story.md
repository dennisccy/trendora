# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals. This chapter is about making the running app itself trustworthy day to day — fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest, added a live status badge, fixed a cluster of low-memory crashes, cut background-refresh memory 71%, and fixed a stuck history-loading step whose cleanup once crashed the Factor Lab research page for nearly 13 minutes.

Iteration 50 cut that page's peak memory from 7.8 GB to 3.1 GB and taught it to fail one number at a time instead of taking the app down. Iteration 51's fix for the sometimes-silent status light made the problem worse, though it did prove the app survives a broken calculation without a restart. Iteration 52 found the real cause — two slow spots inside the heaviest calculation — and mostly fixed them.

Iteration 53 supplied the missing proof and sped up two more background steps (working out which stocks currently qualify, and reading the market's risk level) by reading only the needed window of price history instead of a stock's whole multi-decade history — one step got 36 times faster. For the first time since iteration 45, a journey moved fully forward: the app's honest "starting up" and "backend unavailable" messages got their first real proof, checked against the app's own logs and database.

Iteration 54 fixed a subtle one-day gap in the market-risk calculation that could occasionally show the wrong risk label, sped up the retrospective research page's slow read, and closed the very last moment where the health signal went silent during the specific background step this round targeted — that silent-moment count reached zero for the first time, across a bigger live test than before. But the round was run at a shallower checking depth than its own plan called for, so the deeper checks that usually catch problems didn't run this time — and it turned out one of the app's heaviest background steps quietly ran out of memory mid-job and skipped part of its work, while its saved record still marked the job "done." The three reliability journeys still not fully proven (precomputed aggregates, page loading, and heavy-job resilience) all stay exactly where they were: two screens are now unexpectedly slow because the stored data grew much larger, and the health signal still goes quiet or slow during the app's single heaviest background step. The next round returns to full-depth checking and aims to make that heaviest step honest about partial work and close its remaining silent moments.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools. It accepts a backfill over any date range with no hidden size cap and explains honestly when nothing new needed fetching. It serves backtest results instantly from storage and discloses honestly when it's crunching numbers in the background. It shows an honest "starting up" message while booting and a "backend unavailable" message if it goes down, marking any interrupted job clearly once it's back.

_Last updated: 2026-08-09 after iteration 54._
