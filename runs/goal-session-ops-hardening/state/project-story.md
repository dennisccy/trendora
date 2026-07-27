# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill cap, moved slow calculations to run once at ingest instead of on every visit, made restarts near-instant, and fixed slow spots that used to freeze or block the app; the owner then settled a speed target for background work, and an independent check confirmed the project had reached its original goal.

The improvement loop then proposed making that background work visible instead of invisible: one round built a live status badge and a Data Manager panel showing what's computing and what happened last time, and the next round finished its guided walkthrough, took a clean speed measurement on a quiet computer, and proved with a safety-net test that the panel would correctly show a failed job — closing two loose ends an earlier independent check had found.

That same thorough re-checking then turned up two new, rare glitches in older parts of the app: opening a very old Backtest date twice in quick succession could trigger a server error, and right afterward the Data Manager page could briefly look empty even though thirty years of real data were safely stored.

This round fixed both glitches: the Backtest page can no longer show a server error when two requests for the same never-checked date collide, and the Data Manager page now says plainly when its numbers are a real, slightly older snapshot instead of looking blank. While reviewing the fix, the team also caught and corrected a subtler bug of its own — an early version could have shown the wrong count of newly-added records — before it ever reached anyone. One thread is still open: the automatic browser check meant to independently confirm both fixes was cut off partway by an outside usage limit, so that confirmation, plus a fix for a separate page (Evidence) found to occasionally run out of memory under heavy testing, are next.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with an honest zero-work explanation, and the status badge stays truthful through startup, updates, or a crash. Heavy calculations are prepared in advance rather than computed while someone waits, and the Backtest page discloses whether its numbers are fresh, a labeled still-good version, or not yet ready — and no longer crashes under a two-request race. A live badge and a Data Manager panel show whenever background computing is happening, what happened last time, and now also when coverage numbers are a real but slightly older reading rather than looking empty.

_Last updated: 2026-07-27 after iteration 27._
