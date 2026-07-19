# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — and this chapter of its story is about making the running app itself trustworthy to operate day to day: fast to start, honest about what it is doing, and unrestricted in the historical data it can pull in.

## How it has grown

Trendora's core analytics — the rankings, the evidence-backed scoring, and every existing page — were already built and proven in an earlier chapter of this project. This new chapter turns attention to running the app itself: starting in seconds, being honest about its own state, doing the heavy number-crunching in advance instead of on the spot, and letting the owner pull in any stretch of historical data without hitting an arbitrary limit.

The first checkpoint was a plain stock-take with no changes made: startup and crash messages already worked well and an interrupted data job already recovered correctly, but backfilling a month of history quietly created nothing, long date ranges were still capped, heavy calculations still ran live instead of being stored in advance, and there was no permanent crash log.

The next round of work closed the biggest of those gaps. Requesting a backfill for a specific stretch of history — like all of May 2026 — now actually pulls in every trading day asked for, instead of silently doing nothing. The old one-year size limit on backfill requests is gone, and a very large request now runs safely in visible chunks instead of being rejected outright. A zero-work backfill now says so plainly instead of looking like an unexplained success, and every outcome — requested days, trading days, skipped days and why — is shown in plain language and survives a page reload. Along the way, the team caught and fixed a bug where an interrupted job could show made-up "zero days" information instead of admitting it never finished.

The starting-up and crash messages, and the interrupted-job recovery, were re-checked this round and still work correctly. Still missing: a permanent crash log, a firm startup memory limit, storing heavy calculations in advance, and making sure every page loads only what it needs — that's the next target.

## What it can do today

The product still lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores exactly as before. An operator can now also backfill any date range and see every requested trading day pulled in, submit backfills of any length without hitting a size limit, and get an honest, reload-proof explanation whenever a backfill has nothing new to do — on top of the startup/crash messages and interrupted-job recovery already in place.

_Last updated: 2026-07-19 after iteration 1._
