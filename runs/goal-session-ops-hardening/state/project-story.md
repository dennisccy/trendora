# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, and added a live status badge so background work shows itself instead of staying invisible.

A later round of double-checking found and fixed a cluster of low-memory problems — including a research tool, Factor Lab, that crashed on every visit — and tightened the Backtest page's own calculation piece by piece until its last unbounded memory use was replaced with small running totals that produce the exact same numbers.

A more recent round fixed a different, quieter problem: the script meant to start the site in production mode for measurement and testing had actually been running slower developer mode the whole project. That's now fixed, and the team measured for the first time how fast all eleven main pages load — every one in well under a tenth of a second. The same measurement caught a real problem: the Regime Lab research page could sit on a blank, unlabelled spinner for up to a minute and a half on its first load after new data arrives. The team fixed the display in the same round — it now says plainly "Still computing" with elapsed time, and offers a Retry button if loading fails.

This round closed the session's last open item: proving the site survives a genuine low-memory emergency without going down. The team deliberately starved a throwaway copy of the backend of memory during its heaviest background calculation and watched it recover cleanly — the risky calculation stopped, health checks kept answering, and previously saved results kept serving, all without a restart. They also timed, for the first time, how fast the health check responds while the app is busy; it answers reliably but a little slower than the strict speed target, now an open question for the owner to settle. With that, all eight things the app must be able to do now work — though the team has also flagged that the app still loads its entire price history into memory during startup housekeeping, which is now the biggest remaining item before the project can be called finished.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and research tools including Factor Lab and Regime Lab. An operator can back-fill any historical date range with an honest zero-work explanation, and the status badge stays truthful through startup, updates, or a crash. Heavy calculations are prepared in advance, restarts serve stored numbers immediately, and the Backtest page always serves saved results. Every main page now loads quickly under real production conditions, the Regime Lab page gives an honest "still working" message during its rare slow first load instead of freezing, and the whole service has now been proven to survive a real memory emergency without ever going down.

_Last updated: 2026-07-30 after iteration 34._
