# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy to operate day to day: fast to start, honest about its own state, and resilient enough that heavy background work never takes it down.

## How it has grown

Trendora's core analytics were already built; this chapter has hardened how the app runs day to day — removing a hidden backfill cap, precomputing slow calculations as data arrives instead of on every visit, making restarts near-instant, enforcing a real memory limit, and speeding up two of the slowest pages roughly tenfold. Testing then uncovered something worse: the same rare background memory problem could freeze the entire app for about ten minutes — a step backward that paused the project for an owner decision.

The owner authorized a direct fix: the calculation behind those freezes was rewritten to use far less memory, proven under a real forced-low-memory test and a real multi-request stress test, with the heaviest possible background calculation completing against the full-size dataset without freezing anything for the first time. One rough edge remained — the Backtest page could still take minutes to respond during that same heavy work — and the next round's fix, which let simultaneous requests share one answer instead of duplicating work, still left a brand-new calculation taking about three minutes on its own, a decision only the owner could resolve.

The owner chose the boldest of three options: redesign the Backtest page to never calculate anything live, always serving numbers already prepared in the background. This iteration delivered that redesign — the page now always shows one of three honest states (fully current, a labeled "still good" earlier version while an update finishes, or an explicit "not yet calculated" message) instead of a silent wait or a blank spot, and the team's own review caught and fixed a banner that was telling a small fib about what was happening, before it shipped. Two rough edges remain: a common everyday update currently shows the empty message instead of the still-good version it should show, and pages can still be a little slow, though never frozen, while an update is actively running.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and an honest zero-work explanation; the status badge stays truthful through startup, an update, or a crash; and heavy calculations are prepared in advance rather than computed while someone waits. The Backtest page now discloses whether its numbers are fresh, a still-good earlier version, or not yet ready — closing most of the multi-minute wait that page used to risk, with two known rough edges still being smoothed out.

_Last updated: 2026-07-23 after iteration 16._
