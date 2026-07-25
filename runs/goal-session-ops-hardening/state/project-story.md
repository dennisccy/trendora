# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill cap, moved slow calculations to run once at ingest instead of on every visit, and made restarts near-instant with a real memory limit — until one heavy calculation still froze the app for about ten minutes under real load. The owner backed a redesign so the Backtest page would never calculate anything live, always serving numbers labeled current, a "still good" earlier version, or "not yet calculated."

A stuck database write behind that freeze was found and fixed, making the page about 63x faster with every number unchanged, and a second slow spot — the first view of an older date hanging for up to a minute — moved into the background so it no longer blocks the page.

With both slow spots fixed, one round confirmed the Backtest page stays fast even while new data imports at the same time, and that the app survives a real hard crash-and-restart without losing its place mid-job. That left one open question — how strict the speed target should be during the roughly half-minute a background calculation runs — which the owner then answered directly, writing a slightly more generous target for that window and, the same day, adjusting how long the window may run.

This latest round re-tested against that new target and it held up: pages stayed responsive during background work with real numbers to prove it, and a memory-safety question got its first real-world test when an accidental overload was absorbed cleanly with no crash. That looked like the finish line, but an independent second look before calling it done caught a few loose ends — an unfinished demo walkthrough for the newest capabilities, a test setting quietly loosened without being flagged, and one inconsistent note in the measurement report. Nothing is broken; the paperwork proving it's finished isn't quite there yet, so one more short round is tidying it up before the project can be called complete.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and get an honest zero-work explanation; the status badge stays truthful through startup, updates, or a crash, and has been proven to survive a hard crash-and-restart without losing its place. Heavy calculations are prepared in advance rather than computed while someone waits, the Backtest page discloses whether its numbers are fresh, a labeled still-good version, or not yet ready, and pages now stay responsive even while new numbers compute in the background.

_Last updated: 2026-07-25 after iteration 22._
