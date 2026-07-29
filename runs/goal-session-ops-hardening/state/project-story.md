# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, and added a live status badge and a Data Manager panel so background work shows itself instead of staying invisible. A later re-check fixed a double-click race on the Backtest page and a Data Manager page that could briefly look empty, bringing all eight tracked capabilities to a confirmed-working state.

A mandatory double-check then turned up a cluster of low-memory problems: a fix on the Evidence page uncovered a related research tool, Factor Lab, that crashed on every visit, plus three more spots where the app could quietly run low on memory during heavy background work. One of those spots — the calculation behind the Backtest page's numbers — was tightened first, cutting its peak memory use by roughly a fifth, though an independent check found part of that same calculation still unbounded.

Factor Lab was fixed next: it used to fail with an out-of-memory error every time it opened, and now it loads and shows real numbers for every scoring factor and time horizon, with two people opening it at once no longer wasting a duplicate calculation. An independent check found that fix was real headroom rather than a permanent guarantee — a bit under a third of the old memory need, not a hard limit — so it was written down honestly rather than called finished.

This round finished the job the Backtest calculation started two rounds earlier: the one piece left unbounded — a full copy of nearly every scored stock-and-date pair, held in memory at once — is now gone, replaced by small running totals that produce the exact same numbers. A live test against the full real history ran the calculation twice with zero memory errors and well over half the memory ceiling still free, and the app's memory-safety record was written down for the first time in 32 rounds of this work. Two small checks remain on that same promise — timing the health check against its speed limit, and a deliberate low-memory drill — plus a still-unsettled question about whether the site's "production" launch script actually builds a production version, which is now blocking an honest page-speed measurement.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools including Factor Lab, and evidence-backed scores. An operator can back-fill any historical date range with an honest zero-work explanation and no size limit, and the status badge stays truthful through startup, updates, or a crash. Heavy calculations are prepared in advance rather than computed while someone waits, restarts serve stored numbers immediately, and the Backtest page always serves saved results instead of recalculating live — now backed by a calculation that can no longer run the server out of memory. The Evidence page discloses, claim by claim, when a figure couldn't be computed instead of leaving it silently blank. The Factor Lab research tool, which used to crash every time it was opened, now loads reliably.

_Last updated: 2026-07-29 after iteration 32._
