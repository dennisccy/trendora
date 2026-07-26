# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill cap, moved slow calculations to run once at ingest instead of on every visit, and made restarts near-instant — until one heavy calculation still froze the app for about ten minutes under real load, prompting a redesign so the Backtest page always serves numbers labeled current, a "still good" earlier version, or "not yet calculated."

The stuck database write behind that freeze was fixed (63x faster, numbers unchanged), and a second slow spot — an older date's first view hanging for up to a minute — moved into the background so it no longer blocks the page. The fix held under real concurrent data imports and survived a hard crash-and-restart without losing its place.

The owner then settled the one open question — how strict the speed target should be during the roughly half-minute a background calculation runs — with a more generous target; pages stayed responsive during that window and a memory-safety scare (an accidental overload) was absorbed cleanly with no crash. An independent second look caught a few loose ends before calling it done: an unfinished guided walkthrough, a quietly loosened test setting, and one inconsistent report note. A follow-up round tidied up exactly those, with no changes to the app itself, and a second independent reviewer agreed the project had genuinely reached its goal.

With the original goal met, the improvement loop proposed one more capability: making that background calculation visible instead of invisible. This round built it — a live badge next to the "Ready" status, present on every page, that says when the backend is quietly computing something in the background, plus a new panel on the Data Manager page showing which date is being worked on, how far along it is, and the outcome of the last run, including an honest reason if it failed. The numbers were checked against the database and proven accurate to the millisecond. What's left is small: writing matching guided-tour steps for the new indicator, and making the panel say "we don't know" instead of "nothing running" on the rare occasion it briefly loses touch with the backend.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and get an honest zero-work explanation; the status badge stays truthful through startup, updates, or a crash, and has survived a hard crash-and-restart without losing its place. Heavy calculations are prepared in advance rather than computed while someone waits, the Backtest page discloses whether its numbers are fresh, a labeled still-good version, or not yet ready, and pages stay responsive while new numbers compute in the background. A live badge and a Data Manager panel now show, in real time, whenever that background computing is happening and what happened last time.

_Last updated: 2026-07-26 after iteration 24._
