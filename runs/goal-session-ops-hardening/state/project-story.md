# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early hardening removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, added a live status badge, fixed a cluster of low-memory crashes, and gave research pages an honest "still computing" message instead of a blank spinner. A later round proved the app survives a genuine low-memory emergency and cut the Data page's background-refresh memory 71% with identical numbers.

One round closed the last known gap behind the "heavy work never takes the service down" promise and caught a backwards headline number before it could mislead anyone. The next round deliberately pushed a background calculation until it ran out of memory, watched the app catch that failure cleanly while still answering every request, but found it could still freeze for several minutes afterward at a very tight memory limit — traced to a piece of code loading millions of price rows into memory all at once.

The round after that fixed exactly that spot so price-history loading happens in smaller pieces, re-ran the freeze test with it not recurring, and made crash-recovery progress tracking far more accurate. But its own automatic feature-recheck looked at the wrong web address, wrongly reported the app as down, and left several already-working features — the backfill, the status badge, precomputed calculations, and fast page loads — needing a fresh check before they could be promised again. Nothing was known to be broken; they simply weren't tested that round.

This latest round fixed that testing gap and put it to work: the backfill feature, the honest startup status badge, and the "only load what's needed" page behavior were all freshly re-checked in a live browser and confirmed working again, alongside the backtest-evidence and background-activity-indicator features. The team also shrank the memory used by the price-history loading behind the Data page by about half, with the exact same numbers coming out the other end, and made a killed backfill's saved progress far more accurate. The honest catch this round: the two features actually being worked on — the ingest-time precomputation guarantee and the heavy-load resilience guarantee — slipped through completely unchecked even though the freshly-repaired testing check reported a clean "all passed." Nothing is known to be broken; they simply weren't part of this round's testing sweep, a gap the team caught before it could mislead anyone. The same memory-freeze test was re-run and did not recur, though its root cause still isn't proven closed.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools. It accepts a backfill request of any size and explains honestly when nothing new needed fetching, shows a clear boot/crash status badge, keeps pages loading only what they need, always serves backtest evidence from storage rather than a live recompute, and discloses live background-compute activity whenever it is running. Two pieces are still being finished: the ingest-time precomputation guarantee and the heavy-load resilience guarantee are both being actively re-verified after this round's memory-bound fix, with the earlier freeze not recurring but not yet fully proven closed.

_Last updated: 2026-07-31 after iteration 41._
