# Project story so far

Trendora is a market-leadership ranking tool that shows traders which scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample testing, not in-sample curve-fitting.

## How it has grown

The first eighteen iterations built the trust layer — honest "Proven"/"Not yet proven" badges, an auditable evidence page, a private testing ground, and six certified trading edges — then deepened the underlying history to thirty years of stock-index and volatility data, honestly labeled by source, and widened the tracked company list to several hundred names. Every previously-certified trading edge then honestly failed re-testing on that deeper data (the system working as intended, not a step backward), and a brief sector-sort crash that surfaced along the way was fixed the following round, with a safety net added against blank-screen errors.

Iterations 20-21 widened the Data Manager's price-refresh to the whole company list, gave its coverage calendar two clearly separate colors, and confirmed on the live site that it truly works.

Iteration 22 added deep historical market context to the dashboard's main chart: the S&P 500, Nasdaq, and Dow now reach back to 1996 — three decades instead of one — alongside a volatility gauge and an economic-indicator line, each honestly disclosing its data provider, both on the chart and in a new Data Manager section. Partway through, the team caught and fixed a bug where that deep history loaded correctly but stayed hidden off-screen unless someone scrolled far back manually; the fix itself was good, but the project's own formal double-check hadn't been re-run against it yet, so the round ended one step short of calling the feature finished.

Iteration 23 closed that gap. A dedicated, hands-on recheck in a real browser confirmed the three decades of history now show automatically the instant the dashboard loads, every line's data source is disclosed correctly, and nothing else on the site broke in the process — including a fresh, dedicated recheck of the Data Manager's coverage calendar, last individually verified back in iteration 21. The feature added in iteration 22 is now fully signed off rather than provisionally working, and the team is deciding what to tackle next: proving a fresh trading signal on the newer, deeper data, or making the app faster.

## What it can do today

The product lets users browse a leaderboard of hundreds of companies with up to thirty years of price history each, sort and filter by sector, and switch any stock's chart between a recent and full-history view. It shows an honest, auditable evidence status on every score and past trading idea, tied to the current market regime, and lets users browse the company list as it looked on any past date — including a dashboard chart that reliably shows three decades of S&P 500, Nasdaq, and Dow history plus a volatility gauge and a rate-spread indicator, each honestly labeled with its source. The Data Manager page refreshes prices for the whole company list at once, shows a coverage calendar separating price data from already-scored data, and degrades honestly (a contained retry message, never a blank screen) if something goes wrong.

_Last updated: 2026-07-09 after iteration 23._
