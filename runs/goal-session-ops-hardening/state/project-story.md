# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill cap, moved slow calculations to run once at ingest instead of on every visit, and made restarts near-instant, then fixed a database write that used to freeze the app for minutes under load and moved a second slow spot into the background so it no longer blocks the page.

The owner then settled the one open question — how strict the speed target should be during the roughly half-minute a background calculation runs — with a more generous target, and an independent second look confirmed the project had genuinely reached its original goal after a short tidy-up round.

With that goal met, the improvement loop proposed making the background calculation visible instead of invisible. One round built a live badge and a Data Manager panel showing what's computing and what happened last time, checked accurate to the millisecond, but left two loose ends: an unfinished guided walkthrough for the new indicator, and a wording gap where the panel said "nothing running" instead of "we don't know" when it briefly lost touch with the backend.

This round closed both of those loose ends — the guided walkthrough now includes the new indicator, and the panel gives an honest "we don't know" message instead of a misleading "nothing running" one. A first automatic check said every requirement was now met. A second, independent check looked harder and found two remaining gaps: the speed measurement for the status check hasn't been cleanly re-recorded on a quiet computer (two different readings disagree about whether it's within target), and nobody has actually shown the new panel correctly displaying a genuine failure with its reason — every example captured so far shows a successful run. So the project is not quite finished; the next round is already planned to close exactly those two gaps with safe, targeted tests.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and get an honest zero-work explanation; the status badge stays truthful through startup, updates, or a crash. Heavy calculations are prepared in advance rather than computed while someone waits, and the Backtest page discloses whether its numbers are fresh, a labeled still-good version, or not yet ready. A live badge and a Data Manager panel show, in real time, whenever background computing is happening, what happened last time, and — for the rare moment the app briefly can't confirm — an honest "we don't know" message instead of a false "all clear."

_Last updated: 2026-07-26 after iteration 25._
