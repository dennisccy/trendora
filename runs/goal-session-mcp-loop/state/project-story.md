# Project story so far

Trendora is a market-leadership ranking tool that shows traders which scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample testing, not in-sample curve-fitting.

## How it has grown

The first eighteen iterations built the trust layer — honest "Proven"/"Not yet proven" badges, an auditable evidence ledger, and six certified trading edges — then deepened the price history to thirty years across several hundred companies; every previously-certified edge honestly failed re-testing on that deeper data (the system working as intended), and an early crash was fixed the next round.

Iterations 20-21 widened price-refresh to the whole company list and confirmed the Data Manager's coverage calendar live. Iteration 22 added three decades of S&P 500/Nasdaq/Dow history plus a volatility gauge and an economic-indicator line to the dashboard chart, each honestly labeled by data source — a display bug hid that history until iteration 23's recheck signed the feature off for good.

Iteration 24 focused on making the app itself faster — tuning the database, removing duplicate internal lookups, speeding up the stock-detail page and the readiness indicator, and adding a panel on the Data Manager page showing how much storage the database uses, all meant to change nothing but speed. Testing then found a serious problem: right after a server restart, opening the Data Manager page could crash the whole backend before it finished loading. The team found and fixed the likely cause the same day (a memory setting colliding with the new database connections), but hadn't yet re-confirmed the fix with a live restart-and-reload check by round's end — so this round is paused one verification step short of sign-off, not a step backward, since the fix itself is believed correct.

## What it can do today

The product lets users browse a leaderboard of hundreds of companies with an honest "proven" or "not yet proven" status on every score, drill into a fully auditable ledger of every trading idea tested, and view up to thirty years of price history for any stock in a recent or full view. It shows a dashboard chart spanning three decades of major-index history plus a volatility gauge and a rate-spread indicator, each labeled by source, and a Data Manager page with a color-coded calendar of data availability across the whole company list — normally degrading honestly rather than crashing, though a newly-found cold-restart crash there has been fixed but is still awaiting a final live check.

_Last updated: 2026-07-09 after iteration 24._
