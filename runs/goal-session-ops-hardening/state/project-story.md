# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, added a live status badge, fixed a cluster of low-memory crashes, and cut background-refresh memory 71%. Later rounds fixed slow price-loading, repaired a broken automatic recheck, fixed a bookkeeping step that re-scanned 26 years of history on every new day of data, and cut the Evidence page's own multi-minute freeze down to about a hundredth of a second. Iteration 48 fixed a stuck step in loading old price history; iteration 49 fixed the cleanup behind it so a backfill finishes inside its 20-minute promise — but that same testing then found the Factor Lab research page crashing the whole app for nearly 13 minutes if opened while a backfill was finishing.

Iteration 50 went after that crash directly, cutting the Factor Lab page's peak memory from about 7.8 GB to about 3.1 GB and teaching it to fail one number at a time instead of taking down the whole app; a 25-minute real test with the page repeatedly loaded came back clean. But the status light still sometimes answered a few seconds late during heavy background work, and the app once went completely silent for 17 and a half minutes and needed a restart.

Iteration 51 tried the obvious fix for that late-answering problem — pausing the background work more often so other requests get a turn — and it made things worse, not better: the status light missed more checks than before. The team did prove, for the first time, that the app survives a deliberately-broken background calculation without needing a restart.

Iteration 52, this one, found out why the obvious fix failed: two specific spots inside the heaviest background calculation each blocked the whole app for a full second or more, too fast for a simple pause point to interrupt. The team fixed both — splitting a giant sort into smaller pieces, and briefly pausing the app's own automatic memory cleanup for the same short window — and proved it works: the status light now answers almost every check during a heavy data job (2 missed out of 1,285, versus 19 out of 892 before), and the same background calculation finished about a fifth faster. One catch: the round's own proof-checking ran just before this fix was written, so it doesn't yet reflect the win — the next round's first job is simply to check again, no new code required.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools. It accepts a backfill over any date range and honestly explains when nothing new needed fetching, with no hidden size cap. It serves backtest results instantly from storage, never making a user wait on a live recalculation. It discloses honestly when it is crunching numbers in the background instead of looking broken. The team is now working to make that honesty hold even during the heaviest background jobs, so the status light never goes quiet.

_Last updated: 2026-08-08 after iteration 52._
