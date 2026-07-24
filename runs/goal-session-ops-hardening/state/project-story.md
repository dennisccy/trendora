# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy to operate day to day: fast to start, honest about its own state, and resilient enough that heavy background work never takes it down.

## How it has grown

Trendora's core analytics were already built; this chapter has hardened how the app runs day to day — removing a hidden backfill cap, precomputing slow calculations at ingest instead of on every visit, making restarts near-instant, enforcing a real memory limit, and speeding up two of the slowest pages roughly tenfold, before testing uncovered a worse background memory problem that could freeze the whole app for about ten minutes and paused the project for an owner decision.

The owner authorized a direct fix that rewrote the freeze-causing calculation to use far less memory, proven under real stress tests; a following round let simultaneous requests share one answer instead of duplicating work, but a brand-new calculation could still take about three minutes on its own — a choice only the owner could resolve.

The owner chose the boldest of three options: redesign the Backtest page to never calculate anything live, always serving numbers prepared in advance. That shipped next, giving the page three honest states — current, a labeled "still good" earlier version, or "not yet calculated" — instead of a silent wait, though one everyday update still showed the empty message instead of the still-good version, and pages could run a little slow (never frozen) during an update.

This latest round closed that everyday gap: the Backtest page now keeps showing yesterday's real numbers with a small "Refreshing" notice during the most common kind of daily update, instead of briefly going blank, and that notice now names exactly which date's numbers are on screen. The team's own review caught and fixed a second honesty bug nearby — a window-size label had been quietly describing the wrong date. What's left is a genuine unsolved puzzle: roughly 1 in 6 page loads during an active update still run a few seconds slower than they should (never wrong, never frozen), and the next step is adding better internal measurement to finally pin down why.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and an honest zero-work explanation; the status badge stays truthful through startup, an update, or a crash; and heavy calculations are prepared in advance rather than computed while someone waits. The Backtest page discloses whether its numbers are fresh, a labeled still-good version, or not yet ready — now covering the most common daily update scenario without ever going blank — with occasional slower (never wrong or frozen) loading during an update as the one known rough edge.

_Last updated: 2026-07-24 after iteration 17._
