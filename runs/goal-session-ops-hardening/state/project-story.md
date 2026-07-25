# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy day to day: fast to start, honest about its own state, and resilient enough that heavy background work never takes it down.

## How it has grown

Early hardening removed a hidden backfill cap, moved slow calculations to run once at ingest instead of on every visit, made restarts near-instant, and enforced a real memory limit — until one heavier calculation still froze the app for about ten minutes under real load. The owner authorized a fix so simultaneous visitors share one answer instead of duplicating work, then backed a bigger redesign: the Backtest page would never calculate anything live, always serving numbers labeled as current, a "still good" earlier version, or "not yet calculated." Later rounds closed most of the gap — daily updates began showing yesterday's real numbers under a named "Refreshing" notice, a mislabeled date window was caught and fixed, and careful measurement traced the one remaining rough edge to a background database write getting stuck behind other work.

Three rounds ago that exact problem was fixed: after two honestly-reported false starts, the real fix stopped the page from redoing over a thousand pointless database lookups on every visit, making its slow step roughly 63× faster with every number unchanged. The next round found and fixed a second, separate slow spot — the very first view of an older, never-shown date could hang for up to a minute — by moving that calculation into the background instead of letting it block the page.

With both slow spots fixed, this latest round was a pure "prove it holds up" check, not a build round. The team confirmed two things under real conditions at the owner's request: the Backtest page stayed fast with zero slowdowns even while genuinely new data was being imported at the same time, and the app survived a real hard crash-and-restart, recovering cleanly without losing its place in an in-progress job. Both checks came back clean, closing out the Backtest speed-and-honesty promise. One rough edge remains — for about half a minute during certain background calculations, some page loads run a little slower than the target, never broken, just briefly slower — and resolving it needs the project owner to decide how strict that target should be during that window. Five of the seven things being tracked now work as intended; only that one decision stands between here and done.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and get an honest zero-work explanation; the status badge stays truthful through startup, an update, or a crash, and has now been proven to survive a real hard crash-and-restart without losing its place. Heavy calculations are prepared in advance rather than computed while someone waits, and the Backtest page discloses whether its numbers are fresh, a labeled still-good version, or not yet ready — confirmed to stay fast even while new data is being imported in the background.

_Last updated: 2026-07-25 after iteration 21._
