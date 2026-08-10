# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals. This chapter is about making the running app itself trustworthy day to day — fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest, added a live status badge, fixed a cluster of low-memory crashes, cut background-refresh memory 71%, and fixed a stuck history-loading step whose cleanup once crashed the Factor Lab research page for nearly 13 minutes.

Iteration 50 cut that page's peak memory from 7.8 GB to 3.1 GB and taught it to fail one number at a time instead of taking the app down. Iteration 51's fix for the sometimes-silent status light made the problem worse, though it proved the app survives a broken calculation without a restart. Iteration 52 found the real cause — two slow spots inside the heaviest calculation — and mostly fixed them. Iteration 53 supplied the missing proof and sped up two more background steps by reading only the needed window of price history instead of a stock's whole multi-decade history — one step got 36 times faster — and for the first time since iteration 45, a journey moved fully forward: the app's honest "starting up" and "backend unavailable" messages got their first real proof.

Iteration 54 fixed a subtle one-day gap in the market-risk calculation, sped up a slow research-page read, and closed the very last silent moment in the health signal during the one background step it targeted. But the round was checked less thoroughly than its own plan called for, and it turned out one of the app's heaviest background steps had quietly run out of memory mid-job and skipped part of its work while its saved record still marked the job "done."

Iteration 55 went back to full-depth checking and fixed exactly that: the job-history record no longer claims a memory-starved background step finished when it didn't — proven by a dedicated test and independently re-checked in the source. The other half of the round's aim — stopping the app's status light from briefly going quiet during that same heavy step — did not succeed: a live test found it happening slightly more often than before (11 times instead of 6, out of about 1,839 checks over roughly half an hour), traced to a second, unrelated heavy calculation running at the same time and briefly crowding out the health check regardless of how often either one pauses to yield. Two automated checks (for precomputed aggregates and for surviving heavy jobs) ran for the first time this session and passed, though their saved results were later accidentally overwritten and need to be re-run and stored properly next round. The three reliability journeys not yet fully proven — precomputed aggregates, page loading, and heavy-job resilience — stay exactly where they were: two screens are still slow because the stored data grew much larger, and the health signal still goes quiet or slow during the app's single heaviest background step.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools. It accepts a backfill over any date range with no hidden size cap and explains honestly when nothing new needed fetching. It serves backtest results instantly from storage and discloses honestly when it's crunching numbers in the background. It shows an honest "starting up" message while booting and a "backend unavailable" message if it goes down, marking any interrupted job clearly once it's back.

_Last updated: 2026-08-10 after iteration 55._
