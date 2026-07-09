# Project story so far

Trendora is a market-leadership ranking tool that shows traders which scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample testing, not in-sample curve-fitting.

## How it has grown

The first eighteen iterations built the trust layer — honest "Proven"/"Not yet proven" badges, an auditable evidence ledger, and six certified trading edges — then deepened the price history to thirty years across several hundred companies, honestly failing every old certified edge on the new data (the system working as intended) and fixing an early crash the next round.

Iterations 20-21 widened price-refresh to the whole company list and confirmed the Data Manager's coverage calendar live; iteration 22 added three decades of index history plus a volatility gauge and a rate indicator to the dashboard chart, each labeled by source, though a display bug hid that history until iteration 23 signed it off.

Iteration 24 sped up the app behind the scenes — tuning the database, trimming duplicate lookups, and quickening the stock-detail page — but a new memory setting collided with the connection pool: right after a restart, opening the Data Manager page could crash the whole backend before it finished loading. The team fixed it the same day but the round ended one live check short of confirming it held.

Iteration 25 closed that gap with no new code. The team restarted the real backend from scratch twice and watched the Data Manager page load cleanly both times, in about ten seconds each and well under the safe memory limit; an independent live browser check confirmed the same result, so the crash risk is now confirmed gone and the app's speed checks still hold.

## What it can do today

The product lets users browse a leaderboard of hundreds of companies with an honest "proven" or "not yet proven" status on every score, drill into a fully auditable ledger of every trading idea tested, and view up to thirty years of price history for any stock in a recent or full view. It shows a dashboard chart spanning three decades of major-index history plus a volatility gauge and a rate-spread indicator, each labeled by source, and a Data Manager page with a color-coded calendar of data availability across the whole company list — now confirmed reliable even in the moment right after the app restarts, not just once it has been running a while.

_Last updated: 2026-07-09 after iteration 25._
