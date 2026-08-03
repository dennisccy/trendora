# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter is about making the running app itself trustworthy day to day: fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest instead of live, made restarts near-instant, added a live status badge, fixed a cluster of low-memory crashes, and proved the app survives a real low-memory emergency while cutting background-refresh memory 71% with identical numbers.

A later round deliberately pushed a calculation until it ran out of memory, confirmed the app catches that cleanly but can still freeze for minutes afterward, and the next round fixed the underlying price-loading spot — though its own automatic recheck looked at the wrong web address and left several features unverified. The following round fixed that testing gap and re-confirmed five features as working, but the two features it was actively improving slipped through completely unchecked.

The round after that put the repaired testing check to its first real use and found real trouble: a single-day price request could get stuck forever showing nothing, and a heavy background calculation ran the app out of memory, taking it offline for several minutes. The team traced the memory shortage back through ten days of history — it predated that round — and honestly reported that its own attempt to save memory in the price-loading code had actually made things very slightly worse. Work paused for the product owner to decide how to fit thirty years of price history inside the app's protective memory limit.

This latest round resumed once the owner raised that limit, and the fix worked: a heavy calculation now runs comfortably within a third of the new limit, with no runaway growth. The stuck single-day request is fixed too — it now runs and finishes honestly instead of hanging forever. But the full "bring in a brand-new day of data" case still hasn't been tested, so that feature is only part-proven. And a new kind of trouble showed up: even with plenty of memory free, a heavy calculation got stuck and the whole app stopped answering for several minutes — a different problem than last time, still unresolved. The six other features re-checked this round all still work.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools. It accepts a backfill request of any size and explains honestly when nothing new needed fetching, shows a clear boot/crash status badge, keeps pages loading only what they need, always serves backtest evidence from storage rather than a live recompute, and discloses live background-compute activity whenever it is running. Bringing in a brand-new day of price data is only partly proven — the stuck-job bug behind it is fixed, but the full ingest case hasn't been tried yet. A heavy background calculation can still, in rare cases, make the whole app stop responding for several minutes; that is the team's current focus.

_Last updated: 2026-08-03 after iteration 43._
