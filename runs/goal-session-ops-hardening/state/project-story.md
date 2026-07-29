# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, and added a live status badge and a Data Manager panel so background work shows itself instead of staying invisible. A later re-check fixed a double-click race on the Backtest page and a Data Manager page that could briefly look empty, bringing all eight tracked capabilities to a confirmed-working state.

The next round fixed a low-memory problem on the Evidence page and added an honest note for the rare figure that can't be computed — but its mandatory double-check turned up the same kind of problem on a related research tool, Factor Lab, which crashed on every visit, plus three more spots where the app could quietly run low on memory during heavy background work.

One of those spots — the calculation behind the Backtest page's numbers — was tightened next, cutting its peak memory use by roughly a fifth, though an independent check found one piece of that same calculation still unbounded, and Factor Lab was still crashing.

This round finally fixed Factor Lab: it used to fail with an out-of-memory error every single time it was opened, and now it loads successfully and shows the same real numbers it was always meant to, for every scoring factor and every time horizon. Two people opening it at the same moment no longer trigger a wasted duplicate calculation either. An independent check found the fix is real headroom — a bit under a third of the old memory need — rather than a permanent guarantee, so the same kind of crash could return if the data grows large enough; that's now written down honestly rather than called finished. Nothing that used to work broke. The one piece of the Backtest calculation left unbounded two rounds ago is still unbounded and is now the team's top priority, alongside deciding how to fairly measure page-loading speed.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools including Factor Lab, and evidence-backed scores. An operator can back-fill any historical date range with an honest zero-work explanation and no size limit, and the status badge stays truthful through startup, updates, or a crash. Heavy calculations are prepared in advance rather than computed while someone waits, restarts serve stored numbers immediately, and the Backtest page always serves saved results instead of recalculating live. The Evidence page discloses, claim by claim, when a figure couldn't be computed instead of leaving it silently blank. The Factor Lab research tool, which used to crash every time it was opened, now loads reliably.

_Last updated: 2026-07-29 after iteration 31._
