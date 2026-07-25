# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill cap, moved slow calculations to run once at ingest instead of on every visit, and made restarts near-instant with a real memory limit — until one heavy calculation still froze the app for about ten minutes under real load, prompting a redesign so the Backtest page would only ever serve numbers labeled current, a "still good" earlier version, or "not yet calculated."

A stuck database write behind that freeze was found and fixed, making the page about 63x faster with every number unchanged, and a second slow spot — an older date's first view hanging for up to a minute — moved into the background so it no longer blocks the page. What followed proved the fix held: the page stayed fast even while new data imported at the same time, and the app survived a real hard crash-and-restart without losing its place mid-job.

One open question remained — how strict the speed target should be during the roughly half-minute a background calculation runs — which the owner answered directly with a slightly more generous target. The next round proved pages stayed responsive during that window with real numbers to show it, and a memory-safety question passed its first real-world test when an accidental overload was absorbed cleanly with no crash. That looked like the finish line, but an independent second look before calling it done caught a few loose ends first: an unfinished demo walkthrough for the newest capabilities, a test setting quietly loosened without being flagged, and one inconsistent note in the measurement report.

The next round tidied up exactly those loose ends, with no changes to the app itself: it wrote the missing guided walkthrough for the newest capabilities, tracked down the quietly loosened test setting and reverted it after finding no legitimate reason for the change, and re-confirmed every one of the app's seven proven capabilities still works with fresh evidence. A second, independent reviewer then rechecked everything from scratch and agreed: the project has genuinely reached its goal.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and get an honest zero-work explanation; the status badge stays truthful through startup, updates, or a crash, and has been proven to survive a hard crash-and-restart without losing its place. Heavy calculations are prepared in advance rather than computed while someone waits, the Backtest page discloses whether its numbers are fresh, a labeled still-good version, or not yet ready, and pages stay responsive even while new numbers compute in the background.

_Last updated: 2026-07-25 after iteration 23._
