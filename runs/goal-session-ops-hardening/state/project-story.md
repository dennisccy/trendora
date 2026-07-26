# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill cap, moved slow calculations to run once at ingest instead of on every visit, made restarts near-instant, and fixed slow spots that used to freeze or block the app — the owner then settled the speed target for background work, and an independent check confirmed the project had reached its original goal.

The improvement loop then proposed making that background work visible instead of invisible. One round built a live badge and a Data Manager panel showing what's computing and what happened last time; a follow-up round finished the guided walkthrough for it and gave it an honest "we don't know" message for the rare moments it loses touch with the backend. An independent second check still found two loose ends before it would call the goal met: a speed measurement that hadn't been cleanly re-recorded on a quiet computer, and no proof the panel could correctly show a genuinely failed background job.

This round closed both of those loose ends for good: a clean speed measurement was taken on a quiet computer and came in comfortably within target, and a new safety-net test now proves the panel would correctly show a failed background job with its reason — without ever having to trigger a risky real failure to prove it. But while re-checking everything this thoroughly, the team also turned up two real, if rare, glitches in older, untouched parts of the app: opening an old historical date twice in quick succession can trigger a server error, and right afterward the Data Manager page can briefly show an empty-looking dataset even though thirty years of data are safely stored. Neither breaks the running app, but both need a closer look, so the project isn't quite finished — the next round is already planned to find out exactly what a person sees when that error happens, fix it so it can't happen, and make the Data Manager page tell the truth instead of showing zeros.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and get an honest zero-work explanation; the status badge stays truthful through startup, updates, or a crash. Heavy calculations are prepared in advance rather than computed while someone waits, and the Backtest page discloses whether its numbers are fresh, a labeled still-good version, or not yet ready. A live badge and a Data Manager panel show, in real time, whenever background computing is happening, what happened last time, and — for the rare moment the app briefly can't confirm — an honest "we don't know" message instead of a false "all clear."

_Last updated: 2026-07-26 after iteration 26._
