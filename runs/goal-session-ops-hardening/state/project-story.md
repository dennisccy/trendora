# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals. This chapter is about making the running app itself trustworthy day to day — fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest, added a live status badge, fixed a cluster of low-memory crashes, cut background-refresh memory 71%, and fixed a stuck history-loading step whose cleanup once crashed the Factor Lab research page for nearly 13 minutes.

Iteration 50 cut that page's peak memory from 7.8 GB to 3.1 GB and taught it to fail one number at a time instead of taking the app down. Iteration 51's fix for the sometimes-silent status light made the problem worse, though it proved the app survives a broken calculation without a restart. Iteration 52 found the real cause — two slow spots inside the heaviest calculation — and mostly fixed them. Iteration 53 supplied the missing proof and sped up two more background steps, and for the first time since iteration 45, a journey moved fully forward: the app's honest "starting up" and "backend unavailable" messages got their first real proof.

Iteration 54 fixed a subtle gap in the market-risk calculation and closed the last silent moment in the health signal during the one background step it targeted — but the round was checked less thoroughly than its own plan called for, and it turned out a heavy background step had quietly run out of memory mid-job and skipped part of its work while its saved record still marked the job "done."

Iteration 55 fixed exactly that record-keeping bug, proven by a dedicated test. Its other aim — stopping the status light from briefly going quiet during heavy jobs — did not succeed and got slightly worse (11 quiet spells instead of 6), traced to a second heavy calculation crowding the same process. Two automated checks ran for the first time this session and passed, though their saved results were later accidentally overwritten.

Iteration 56 tackled the two screens that had grown slow as the stored data grew about fifteen times larger: the run-history list and the data-availability chart. Both are now genuinely fast — the run list dropped from several seconds to about a quarter of a second, and the availability chart from up to 21 seconds to under a tenth of a second, both checked by hand in the code and the database. But the fix introduced a new problem of its own: while a data-fetch job is running, the availability chart now wrongly claims there is no data at all, for the whole length of the job, even though the database holds millions of stored prices. The round was also supposed to run at a deeper, more careful checking pace and instead ran the shallower one, so that new problem reached the project record only because the evaluator caught it by hand. Two other slow spots on the same page — a health check and a single stock's price lookup — are still not fixed. The three reliability journeys not yet fully proven — precomputed aggregates, page loading, and heavy-job resilience — stay exactly where they were for a third straight round, though page loading made real, if incomplete, progress this time.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools. It accepts a backfill over any date range with no hidden size cap and explains honestly when nothing new needed fetching. It serves backtest results instantly from storage and discloses honestly when it's crunching numbers in the background. It shows an honest "starting up" message while booting and a "backend unavailable" message if it goes down, marking any interrupted job clearly once it's back. Two of its screens — the run-history list and the data-availability chart — now load close to instantly instead of taking several seconds to over twenty, though the availability chart still misbehaves for the duration of any data-fetch job.

_Last updated: 2026-08-10 after iteration 56._
