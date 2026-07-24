# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy day to day: fast to start, honest about its own state, and resilient enough that heavy background work never takes it down.

## How it has grown

Early hardening removed a hidden backfill cap, moved slow calculations to run once at ingest instead of on every visit, made restarts near-instant, and enforced a real memory limit — until a heavier calculation once froze the whole app for about ten minutes under real load. The owner authorized a direct fix, and simultaneous visitors then began sharing one answer instead of duplicating work.

A brand-new calculation could still take up to three minutes on its own, so the owner picked the boldest of three options: redesign the Backtest page to never calculate anything live, always serving numbers prepared in advance, with three honest states (current, a labeled "still good" version, or "not yet calculated"). The following rounds closed most of the gap — daily updates now show yesterday's real numbers with a named "Refreshing" notice, a mislabeled date window was caught and fixed, and detailed timing measurement pinned down the one remaining rough edge: about 1 in 6 page loads during an active update ran a few seconds slower than they should, traced to a background database write getting stuck behind other work.

This latest round fixed that exact problem — after two attempts that turned out not to be the real cause (honestly reported as negative results, not hidden), the third stopped the page from redoing about 1,100 pointless database lookups on every visit. Under a live heavy-traffic test the page's slow step dropped from nearly a second to about fourteen-thousandths of a second (roughly 63× faster), every displayed number unchanged. Testing also found a second, separate slow spot: the very first view of an older, never-shown date can still take up to about a minute — now clearly understood and next up to fix, alongside confirming the speed fix also holds during a live data update and a still-owed check that a hard restart mid-job behaves safely.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and an honest zero-work explanation; the status badge stays truthful through startup, an update, or a crash; heavy calculations are prepared in advance rather than computed while someone waits. The Backtest page discloses whether its numbers are fresh, a labeled still-good version, or not yet ready, and now loads about ten times faster under heavy traffic — with one known rough edge: the very first view of an older, not-yet-seen date can still take up to about a minute.

_Last updated: 2026-07-24 after iteration 19._
