# Project story so far

Trendora is a local-first, research-only US equity leadership scanner — a decision-support workstation that ranks the market after the close and earns the user's trust with forward-tested evidence rather than ever shouting "buy."

## How it has grown

Trendora arrived already substantially built — a dark dashboard ranking US stocks, sectors, and themes after the close, every score explained and every idea showing what would prove it wrong. Early passes closed the last gaps — one shared date control, click-through from any forward-tested return to the names behind it, a Data Manager that backfills without inventing numbers, identical scores across pages, a watchlist that survives a restart, and fast loads from saved snapshots — completing all nineteen original must-have journeys.

The owner then set a larger target: a bigger universe, more chart timeframes, and research labs. Charts learned to keep drawing past a chosen past date all the way to today while scores still reflect only what was known then, and a backtest view showed the real return each top sector, theme, and ranked stock delivered. Widening the universe toward roughly 500 names stalled across several passes — the machinery is built and tested, but the one-time download of real price history it needs kept hitting a temporary outage of the free data source, and the team refused to fake it. So work turned to data already in hand: the scanner learned three chart patterns, and a Research area opened with a Factor Lab testing whether a signal actually sorted future returns — later passes split that evidence by market mood, combined signals, gathered a family of volatility measures, and added a Setup & Pattern Lab studying every past occurrence of a setup or pattern (typical gain, hit-rate, worst dip and best rise, best holding length), always with honest "not enough history" marks.

This latest pass built the capstone that ties it all together: from any lab finding you can now click "View the names expressing this on the leaderboard" and land on the stock list already filtered to those names, then open one for its full scorecard — and filtered views now live in the web address, so any can be bookmarked or shared. The feature is built and the code checks out; a final end-to-end walkthrough was held over to a short next pass after a local build glitch blocked the test browser. No stock's score changed.

## What it can do today

The product lets users see the day's market at a glance; browse ranked stocks, sectors, and themes and filter the list by sector, setup, or any of three chart patterns — now also via shareable, bookmarkable links; open any stock for a plain-English scorecard, identical on list and detail, plus the price that would prove the idea wrong; rewind the whole app to any past day with one shared date control and watch a chart continue past it; read forward-tested evidence by stock, sector, and ranking tier; explore the Research area to test whether a signal sorts future returns — by group, market mood, combinations, and a volatility family — and study any setup or pattern's full pooled track record; save a watchlist that survives a restart; grow the dataset by date; and look up every label in a plain-language glossary — always with honest "not enough data yet" marks instead of fabricated numbers.

_Last updated: 2026-06-03 after iteration 15._
