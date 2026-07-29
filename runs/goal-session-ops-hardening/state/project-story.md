# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, and added a live status badge and a Data Manager panel so background work shows itself instead of staying invisible. A later thorough re-check found and fixed a double-click race on the Backtest page plus a Data Manager page that could briefly look empty, bringing all eight tracked capabilities to a confirmed-working state — with one thing still open: the Evidence page's occasional low-memory problem under heavy use.

The next round fixed that Evidence page problem — proven by opening the page and combing the background log across a full test window — and added a calm, honest note for the rare case a single figure can't be computed. But that round's mandatory double-check of a related research tool, Factor Lab, turned up the SAME kind of problem there: the page crashed on every visit from a memory error, plus three more spots where the app could quietly run low on memory in the background during heavy work.

This round went after the most acute of those three spots: the calculation behind the Backtest page's numbers. It now processes years of history in smaller batches instead of loading it all into memory at once, and an independent double-check measured a real one-fifth cut in peak memory use, with a full-scale trial finishing cleanly for the first time. But that same check found the fix incomplete — one of the three memory-hungry pieces of the calculation is still unbounded, so what shipped is real breathing room, not a complete fix — and the Factor Lab page still crashes when opened, unresolved for a second round running. A careful review this round also caught the testing pipeline briefly mislabeling a failed check as a pass, a paperwork bug that has now been flagged for a fix. Nothing that used to work broke. The team's next job is to stop Factor Lab from crashing and finish tightening the one remaining bottleneck in the Backtest calculation.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with an honest zero-work explanation and no size limit, and the status badge stays truthful through startup, updates, or a crash. Heavy calculations are prepared in advance rather than computed while someone waits, restarts serve stored numbers immediately, and the Backtest page always serves saved results instead of recalculating live. The Evidence page discloses, claim by claim, when one figure couldn't be computed instead of leaving it silently blank. One research tool, Factor Lab, still occasionally fails to load because of an unresolved memory problem the team is working on next.

_Last updated: 2026-07-29 after iteration 30._
