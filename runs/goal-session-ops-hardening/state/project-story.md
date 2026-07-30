# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, and added a live status badge. A later round fixed a cluster of low-memory crashes — including a research tool that crashed on every visit — and rewrote the Backtest page's calculation into small running totals with identical output. A further round fixed the site's production start script (it had quietly run slower developer mode), measured every main page loading in well under a tenth of a second, and replaced Regime Lab's blank 90-second spinner with an honest "Still computing" message and Retry button.

The next round proved the app survives a genuine low-memory emergency — a throwaway test starved the backend during its heaviest calculation and it recovered cleanly, no restart needed — and timed the health check under load for the first time. All eight core promises worked at once, though the app still loaded its entire price history into memory during startup housekeeping.

The round meant to fix that shipped no code — a setup mix-up meant only inspection happened. It wasn't wasted: it caught, live, that four research pages really do show a blank screen during a slow load, and that a heavy background job pushes memory to its safety limit, never crashing but with no room to spare. Two of the eight core promises slipped from fully to partly proven, though nothing broke for an ordinary user.

This latest round built the fix. The Data page's background refresh — which used to load every stock's entire 30-year price history at once — now works through the stock list in small batches, cutting peak memory 71% with identical numbers, proven byte-for-byte. All four remaining research pages now show the same honest "Still computing" message and Retry button Regime Lab already had, so no research page leaves users staring at a blank screen. The promise that heavy background work never takes the service down is still only partly proven — the automated check meant to confirm it couldn't run this round (it was blocked from restarting the test backend), so a person checked by hand and found it healthy; the full check needs to run properly next round.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools (Regime Lab, Factor Lab, Market Phase & Severity Lab, Regime × Phase × Factor, Severity-velocity). An operator can back-fill any historical range with an honest zero-work explanation, and the status badge stays truthful through startup, updates, or a crash. Heavy calculations are prepared in advance, restarts serve stored numbers immediately, the Backtest page always serves saved results, and every research page now shows an honest "still working" message instead of a blank screen during a slow load. Confirming that heavy background work never takes the service down under the app's single heaviest scenario is the top priority next.

_Last updated: 2026-07-30 after iteration 36._
