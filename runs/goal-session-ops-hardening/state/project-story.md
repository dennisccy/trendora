# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals. This chapter tracks making the running app itself trustworthy day to day — fast, honest about its own state, and resilient under heavy background work.

## How it has grown

Early rounds removed a hidden backfill limit, moved slow calculations to run once at ingest, added a live status badge, fixed a cluster of low-memory crashes, and brought seven of the product's eight core promises to passing after fixing a timezone mix-up. A multi-round hunt for slow health-check replies during heavy background jobs (iterations 62-71) ended with two root causes found and fixed: the app now pre-computes its status answer instead of recalculating it live, and a database connection-pool shortage that once caused a two-and-a-half-minute silent gap was closed. Iteration 72 resized that pool with a boot-time safety check and made the status check always answer instantly; iteration 74 confirmed the eighth and final core promise stayed safe under real heavy load, peaking at 4,724 MB of an 8,192 MB memory allowance.

Iterations 73-75 were dogged by a screenshot tool that kept serving broken, unstyled pages instead of real evidence, voiding proof for two of the eight promises across several rounds. Iteration 75 finally got clean screenshots again and re-verified the last two uncertain promises with fresh, first-party proof — but no developer worked that round, so the glitch behind the broken screenshots stayed undiagnosed, just quiet.

Iteration 76 explained why, and it turned out to be bigger than one glitch: the team discovered a safety rule built into the automation itself that skips programming work whenever every one of the eight promises is already confirmed working — which, since iteration 74, has always been true. That rule, not bad luck, is why two rounds running produced no code changes. The team used the loop's own escape hatch to force the next round to actually staff a developer again, while this round's screenshots stayed clean for a second time in a row and the two previously-uncertain promises (stored backtest results, and disclosing background activity) were re-confirmed with numbers checked directly against the database, down to the second. A few small rough edges surfaced too: a stray leftover file at the top of the project, a display glitch where the "Ready" label can get hidden behind another badge on narrow screens during background work, and a recording tool that keeps saving duplicate before/after pictures instead of two different ones.

All eight core promises are confirmed passing today, each re-checked with its own fresh proof this round. What remains is genuinely diagnosing and fixing the broken-screenshot glitch — not just waiting for it to stay quiet — a short list of small cleanup items, and a growing list of self-review housekeeping notes that the team has asked the project owner how strictly to treat before calling the project finished.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, and all five research tools, always with an honest status message while the backend starts up. Backfills accept any date range with no hidden cap and explain when there's nothing new to fetch. Freshly calculated aggregates are ready right after a data import rather than computed on the fly, backtest results load instantly from storage with a "refreshing" note while new numbers compute, pages fetch only what they need, and the app discloses when it's crunching numbers in the background and when it's done, including how long the job took. All eight core promises are confirmed working, each re-verified with fresh evidence this round.

_Last updated: 2026-08-13 after iteration 76._
