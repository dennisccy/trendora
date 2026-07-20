# Project story so far

Trendora ranks stocks with explainable, evidence-checked signals — this chapter of its story is about making the running app itself trustworthy to operate day to day: fast to start, honest about its own state, unrestricted in the historical data it can pull in, and quick to load every page.

## How it has grown

Trendora's core analytics — the rankings, evidence-backed scoring, and every existing page — were already built and proven earlier. This chapter turned to running the app itself, starting from a stock-take that found backfills which silently did nothing, capped date ranges, calculations computed live on every visit, and no permanent crash log. Two early rounds closed the biggest of those gaps: backfills now pull in every requested day with no size cap, saying plainly when there's nothing new to do; heavy calculations now happen once, as new data arrives, restarts became near-instant, and the app genuinely enforces its memory limit with a permanent crash log.

A close look at real usage then surfaced two rough edges hiding in plain sight — an ordinary data update could briefly make the whole app look crashed, and a long job's on-screen progress could freeze and falsely claim to be stuck. A dedicated round fixed both: the status badge now tells the truth every time, showing a calm "Snapshot pending" message instead of a false crash alarm when new benchmark data is still processing, and the stuck-progress bug is fully gone.

With those fixed, the team turned to the last piece of this chapter: making sure every page loads quickly using only the data it actually needs. This latest round measured every page in the app for the first time and found one real slowdown — the Backtest page's main table was recalculating a large statistic from scratch on every visit, taking about 35 seconds. That's now fixed: the page loads in well under a second, with the exact same numbers as before, by saving the calculation the moment new data arrives instead of redoing it on every visit. Checking all the pages also turned up one that's still a bit too slow under everyday conditions — the home page's small trend-history chart, which can take a couple of seconds to appear because of how many things it loads at once in a real browser. That one isn't fixed yet, and while confirming everything else still worked, one of the automated safety checks came back stale and needs a second look before the team calls this chapter complete.

## What it can do today

The product lets users browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any date range with no size cap, get an honest explanation when there's nothing new to add, and get a near-instant Data page after a restart, backed by clear startup/crash messaging and a genuinely enforced memory limit. The status badge can be trusted to describe what's really happening, and the Backtest page's scorecard — once a 35-second wait — now appears in under a second.

_Last updated: 2026-07-20 after iteration 5._
