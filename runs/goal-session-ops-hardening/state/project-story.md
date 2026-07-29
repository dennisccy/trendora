# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, and added a live status badge and a Data Manager panel so background work shows itself instead of staying invisible. A later re-check fixed a double-click race on the Backtest page and a Data Manager page that could briefly look empty.

A mandatory double-check then turned up a cluster of low-memory problems, including a research tool — Factor Lab — that crashed on every visit, and three more spots where the app could quietly run low on memory during heavy background work. Factor Lab was fixed so it now loads real numbers for every scoring factor and time horizon; an independent check found that fix was real headroom rather than a permanent guarantee, so it was written down honestly rather than called finished. The Backtest page's own underlying calculation was tightened piece by piece across several rounds, and two rounds ago the last unbounded piece — a full copy of nearly every scored stock-and-date pair, held in memory all at once — was finally replaced with small running totals that produce the exact same numbers, proven against the full real history with zero memory errors and well over half the memory ceiling still free.

This round fixed a different, quieter problem: the script that is supposed to "start the site in production mode" for measurement and testing had actually been starting it in slower developer mode for the entire project, so every page-speed number recorded so far had never reflected true production behavior. That's now genuinely fixed, and for the first time the team measured how fast all eleven main pages actually load — every one loads in well under a tenth of a second. That measurement also caught a real user-facing problem along the way: the Research → Regime Lab page could sit on a blank, unlabelled loading spinner for up to a minute and a half the first time it's opened after new data arrives, occasionally with a raw error. The team fixed the display side in the same round — the page now says plainly "Still computing — Ns elapsed" with an explanation of what's happening, and offers a Retry button if the load fails.

What's left is narrow and specific: proving the site never goes down under heavy background calculation work, which needs two more checks — timing how fast the health check responds while the app is busy, and a deliberate test of what happens if the app runs low on memory mid-calculation.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools including Factor Lab and Regime Lab, and evidence-backed scores. An operator can back-fill any historical date range with an honest zero-work explanation and no size limit, and the status badge stays truthful through startup, updates, or a crash. Heavy calculations are prepared in advance rather than computed while someone waits, restarts serve stored numbers immediately, and the Backtest page always serves saved results instead of recalculating live — now backed by a calculation that can no longer run the server out of memory. Every main page now loads quickly under genuine production conditions, and the Regime Lab page gives an honest "still working" message with a Retry option instead of freezing during its rare slow first load.

_Last updated: 2026-07-29 after iteration 33._
