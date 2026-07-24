# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy day to day: fast to start, honest about its own state, and resilient enough that heavy background work never takes it down.

## How it has grown

Trendora's core analytics were already built; early hardening removed a hidden backfill cap, moved slow calculations to run once at ingest instead of on every visit, made restarts near-instant, enforced a real memory limit, and sped up two of the slowest pages roughly tenfold — until a heavier calculation, under real load, could freeze the whole app for about ten minutes. The owner authorized a direct fix, and a further round let simultaneous visitors share one answer instead of duplicating work.

Even so, a brand-new calculation could still take up to three minutes on its own — a choice only the owner could resolve. The owner picked the boldest of three options: redesign the Backtest page to never calculate anything live, always serving numbers prepared in advance. That gave the page three honest states (current, a labeled "still good" version, or "not yet calculated"), though one everyday update still showed the empty message, and pages could run a little slow during updates.

The next round closed that gap: the Backtest page now shows yesterday's real numbers with a "Refreshing" notice naming the exact date on screen during the most common daily update, and the team's own review caught and fixed a second honesty bug — a mislabeled date window.

This latest round tackled the one remaining rough edge: about 1 in 6 page loads during an active update still ran a few seconds slower than they should. The team added detailed internal timing measurement and, for the first time, pinned the cause down — a background database write on every request was getting stuck behind other work under load, not a scheduling issue as previously suspected. The fix itself hasn't shipped yet; this measurement, plus two small housekeeping improvements, is what landed this round. Everything else works exactly as before.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and an honest zero-work explanation; the status badge stays truthful through startup, an update, or a crash; and heavy calculations are prepared in advance rather than computed while someone waits. The Backtest page discloses whether its numbers are fresh, a labeled still-good version, or not yet ready, covering the most common daily update without going blank — with occasional slower (never wrong or frozen) loading during an update as the one known rough edge, its cause now pinned down.

_Last updated: 2026-07-24 after iteration 18._
