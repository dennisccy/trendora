# Project story so far

Trendora is a market-leadership ranking tool that shows traders which scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample testing, not in-sample curve-fitting.

## How it has grown

The first eighteen iterations built Trendora's trust layer — honest "Proven"/"Not yet proven" badges, an auditable evidence ledger, and six certified trading edges — then, when the team deepened the price history to thirty years across several hundred companies, every old certified edge honestly recomputed to failing (the system working as designed), and an early crash from that change was fixed the next round. Iterations 20-21 widened price-refresh to the whole company list and confirmed the Data Manager's coverage calendar live.

Iteration 22 added three decades of index history, a volatility gauge, and a rate indicator to the dashboard chart, each labeled by source, though a display bug hid the deep history until iteration 23 signed it off with a clean, live-verified fix.

Iteration 24 sped up the app behind the scenes — tuning the database, trimming duplicate lookups, and quickening the stock-detail page — but a new memory setting collided with the connection pool: right after a restart, opening the Data Manager page could crash the whole backend before it finished loading. The team fixed the cause the same day, but the round ended one live check short of confirming it held, so it paused for human review rather than ship unproven.

Iteration 25 closed that gap with no new code: the team restarted the real backend from a cold stop twice and watched the Data Manager page load cleanly both times, in about ten seconds each and well under the safe memory limit, confirmed by an independent live browser check. Every other page that needed re-checking after the scare — the leaderboard, the evidence ledger, the dashboard, and the deep index history — was also freshly re-confirmed working, so the crash risk is now gone and the app's speed checks still hold. Next, the team turns to speeding up the background data-refresh jobs or proving a new trading edge on the updated thirty-year data.

## What it can do today

The product lets users browse a leaderboard of hundreds of companies with an honest "proven" or "not yet proven" status on every score, open a fully auditable evidence ledger for every trading idea tested (currently all honestly "FAIL" while the deeper history is re-examined), and view up to thirty years of price history for any stock in a recent or full view. It shows a dashboard chart spanning three decades of major-index history plus a volatility gauge and a rate-spread indicator, each labeled by source, and a Data Manager page with a color-coded availability calendar across the whole company list — now confirmed reliable right after the app restarts.

_Last updated: 2026-07-09 after iteration 25._
