# Project story so far

Trendora is a market-leadership ranking tool that shows traders which scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample testing, not in-sample curve-fitting.

## How it has grown

The first eighteen iterations built the trust layer — honest "Proven"/"Not yet proven" badges, an auditable evidence page, a private testing ground, and six certified trading edges — then deepened the underlying history to thirty years with matching stock-index and volatility data, honestly labeled by source, and widened the tracked company list to several hundred names. Every previously-certified trading edge honestly failed re-testing on that deeper data (the system working as intended, not a step backward), though the same change briefly crashed the stock list when sorting by sector. Iteration 19 fixed that crash and added a safety net against blank-screen errors. Iterations 20-21 widened the Data Manager's price-refresh to the whole company list, gave its coverage calendar two clearly separate colors, and confirmed on the live site that it truly works.

Iteration 22 added deep historical market context to the dashboard's main chart: the S&P 500, Nasdaq, and Dow now reach back to 1996 — three decades instead of one — alongside a volatility gauge and an economic-indicator line, and every line now honestly discloses which data provider supplied it, on the chart and in a new Data Manager section. Partway through, the team caught and fixed a bug where that deep history loaded correctly but stayed hidden off-screen unless someone scrolled far back manually — the fix now shows the full three decades the moment the page opens. Every independent check since the fix — a code review, an internal spot-check, and a thorough audit — agrees it genuinely works, but the team's own process calls for one more specific hands-on browser recheck before calling the feature finished, so iteration 22 ends just short of that line.

## What it can do today

The product lets users browse a leaderboard of hundreds of companies with up to thirty years of price history each, sort and filter by sector, and switch a stock's chart between a recent and full-history view. It shows an honest, auditable evidence status on every score and past trading idea, tied to the current market regime, and lets users browse the company list as it looked on any past date. The Data Manager page's price refresh covers the whole company list at once, with a coverage calendar separating price data from already-scored data. Unexpected errors show a contained retry message instead of a blank screen. The new deep-history dashboard chart and data-source labels are built and working in every check so far, pending one final confirmation.

_Last updated: 2026-07-08 after iteration 22._
