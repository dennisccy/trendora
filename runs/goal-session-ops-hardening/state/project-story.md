# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, and reached an independently-confirmed speed goal — after which a live status badge and a Data Manager panel were added so background work shows itself instead of staying invisible.

A later thorough re-check then found two rare glitches in older parts of the app: opening a very old Backtest date twice at once could trigger a server error, and right afterward the Data Manager page could briefly look empty even though thirty years of real data were safely stored.

The next round fixed both — the Backtest page can no longer show a server error when two requests for the same never-checked date collide, and the Data Manager page now says plainly when its numbers are a real, slightly older snapshot instead of looking blank — catching and fixing a subtler bug of its own along the way. But that round's own automatic browser double-check of the two fixes was cut short by an outside usage limit, leaving them unconfirmed alongside a separate page (Evidence) found to occasionally run low on memory under heavy testing.

This round finished that unfinished business: a completed re-run of the same browser checks confirmed both fixes work exactly as intended, and a leftover setting pointing at a different, already-finished project — which had been making one unrelated page falsely report a problem — was cleaned up for good. Every one of the product's eight tracked capabilities is now confirmed working. One thing is still open: the Evidence page's occasional low-memory problem under heavy use, which is planned for next.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with an honest zero-work explanation and no size limit, and the status badge stays truthful through startup, updates, or a crash. Heavy calculations are prepared in advance rather than computed while someone waits, restarts serve stored numbers immediately, and the Backtest page discloses whether its numbers are fresh, a labeled still-good version, or not yet ready, without erroring out under a two-request race. A live badge and a Data Manager panel show background computing as it happens, what happened last time, and when coverage numbers are a real but slightly older reading rather than looking empty.

_Last updated: 2026-07-27 after iteration 28._
