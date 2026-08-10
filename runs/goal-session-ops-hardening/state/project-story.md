# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals. This chapter is about making the running app itself trustworthy day to day — fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest, added a live status badge, fixed a cluster of low-memory crashes, cut background-refresh memory 71%, and fixed a stuck history-loading step that once crashed the Factor Lab research page for nearly 13 minutes. Iteration 50 cut that page's peak memory from 7.8 GB to 3.1 GB and taught it to fail one number at a time instead of crashing outright. Iterations 51-53 chased a sometimes-silent status light and eventually fixed two slow spots inside the heaviest calculation — the first journey to move fully forward since iteration 45: the app's honest "starting up" and "backend unavailable" messages got their first real proof.

Iteration 54 fixed a subtle gap in the market-risk calculation, but a heavy background step turned out to have quietly run out of memory mid-job and skipped part of its work while marking itself "done" — caught only afterward. Iteration 55 fixed that record-keeping bug for good, though the status light still went briefly quiet during heavy jobs, slightly more than before.

Iteration 56 made two slow screens — the run-history list and the data-availability chart — genuinely fast, but introduced a new problem: while a data-fetch job ran, the availability chart wrongly claimed there was no data at all, for the whole length of the job, even with millions of prices already stored.

Iteration 57 fixed exactly that: the Data page's availability chart now shows the real, previous calendar with a calm "Data as of `<version>` — updating" note during a job, instead of the false "no data" message, and closed the two remaining slow spots on that same page — the app's status check and a stock's price chart both now answer in a fraction of a second, down from as much as several seconds. That was enough to finally move a journey forward again: "pages load only what they need" now works. Two things still don't fully work — precomputed aggregates staying reliable during a heavy job, and the app staying usable when it runs low on memory (it once kept saying "Ready" while several pages failed) — and both are the project's current focus.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools. It accepts a backfill over any date range with no hidden size cap and explains honestly when nothing new needed fetching. It serves backtest results instantly from storage and discloses honestly when it is crunching numbers in the background. It shows an honest "starting up" message while booting and a "backend unavailable" message if it goes down. The Data page, individual stock pages, and the run-history list all now load in well under a second, and the availability chart shows an honest "updating" note instead of a false "no data" message during an active data job.

_Last updated: 2026-08-10 after iteration 57._
