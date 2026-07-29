# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, and added a live status badge and a Data Manager panel so background work shows itself instead of staying invisible.

A later thorough re-check found two rare glitches — a double-click race on the Backtest page, and a Data Manager page that could briefly look empty — and the next round fixed both, confirmed by a completed browser re-check after an earlier one had been cut short by an outside usage limit. That round also cleaned up a leftover setting that had been making one unrelated page falsely report a problem, bringing all eight tracked capabilities to a confirmed-working state, with one thing still open: the Evidence page's occasional low-memory problem under heavy use.

This round set out to close that last problem, and the core of it is fixed: the Evidence page's calculation now uses a small, fixed amount of memory instead of memory that grows with the site's price history, proven by opening the page and by checking the background log across the whole test window. A single claim whose figures fail to compute now shows a calm, honest note instead of risking the whole page. But the fix's first version didn't actually work at today's scale — a careful second look caught and corrected that before it shipped — and the same round's mandatory double-check of a related research page (Factor Lab) found it crashing on every visit from a similar, still-unfixed memory problem, plus three more spots where the app can quietly run low on memory in the background. None of this took the app down or broke anything that used to work, so the two capabilities most touched this round — "pages load only what they need" and "heavy calculations never take the service down" — are currently marked as partly, not fully, working. Fixing the Factor Lab crash and the three new memory spots is next.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with an honest zero-work explanation and no size limit, and the status badge stays truthful through startup, updates, or a crash. Heavy calculations are prepared in advance rather than computed while someone waits, restarts serve stored numbers immediately, and the Backtest page always serves saved results instead of recalculating live. The Evidence page now discloses, claim by claim, when one figure couldn't be computed instead of leaving it silently blank.

_Last updated: 2026-07-29 after iteration 29._
