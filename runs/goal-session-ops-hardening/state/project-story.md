# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy to operate day to day: fast to start, honest about its own state, and resilient enough that heavy background data work never takes it down.

## How it has grown

Trendora's core analytics were already built; this chapter turned to running the app day to day — removing a hidden backfill cap, precomputing slow calculations once as data arrives instead of on every visit, making restarts near-instant, enforcing a real memory limit, and fixing edges where an ordinary update could make the app look crashed.

A speed-tuning round made two slow pages load about ten times faster, but testing then uncovered something worse: the same rare background memory problem could freeze the ENTIRE app for about ten minutes — the team called that a step backward and paused for an owner decision on how to fix it.

The owner authorized a direct fix, delivered next: the background calculation behind those freezes was rewritten to use far less memory, proven under a real forced low-memory test and a real multi-request stress test — and, for the first time, the heaviest possible background calculation ran against the full-size dataset without freezing anything. A real scheduled crash-and-restart proved the status badge keeps telling the truth through a crash. One rough edge turned up: the Backtest page could still take a few minutes to respond during that same heavy work.

This latest round chased that edge down. The team found the exact cause — several requests asking for the same not-yet-calculated numbers at once were each redoing the same expensive work instead of sharing one answer — and fixed it, so only the first request works and everyone else shares the answer. A real test against the full-size data confirmed the pile-up is gone, but also showed a genuinely brand-new calculation (one nobody has started yet) still takes about three minutes on its own, a cost this fix can't remove. The page can still be slow in that one case, though it never errors or freezes. Closing this chapter now rests on one decision only the product owner can make: add a progress indicator, redesign so results are always ready in advance, or accept the wait as a known limit.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and an honest zero-work explanation; the status badge stays truthful through startup, an update, or a crash; and an interrupted update leaves an honest record of real progress. Two key pages load quickly, and the app resists the heavy background work that used to freeze it. The Backtest page now shares duplicate work instead of repeating it, though a genuinely new calculation there can still take a few minutes — a known limit awaiting an owner decision.

_Last updated: 2026-07-23 after iteration 15._
