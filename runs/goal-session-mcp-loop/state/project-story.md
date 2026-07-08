# Project story so far

Trendora is a market-leadership ranking tool that shows traders which scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample testing, not in-sample curve-fitting.

## How it has grown

Trendora's first eighteen iterations built the trust layer — honest "Proven"/"Not yet proven" badges, an auditable evidence page, a private testing ground, and six certified trading edges — then deepened the underlying history to thirty years with matching stock-index and volatility data, each honestly labeled by source, and widened the tracked company list from about 120 to several hundred names. Every previously-certified trading edge honestly failed re-testing on that deeper data (the system working as intended, not a step backward), though the same change briefly crashed the stock list when sorting by "Sector."

Iteration 19 fixed that crash at its root, added an honest "Unassigned" sector label for companies with no sector on file, fixed a memory problem on the Data page, and added a safety net so an unexpected error shows a calm retry message instead of wiping out the whole app.

Iteration 20 turned to the Data Manager page: refreshing prices now covers the entire company list instead of a smaller reference set, the redundant "Expand universe" option was removed, and the daily coverage calendar switched to two clearly separate colors for "data exists" versus "already scored." A hands-on check confirmed it worked, but the team's automatic verification pass couldn't finish that round because the site was briefly unreachable at the exact moment it ran, leaving the update built but not officially signed off.

Iteration 21 closed that gap: with the site reachable this time, the automatic checker clicked all the way through the real running product and confirmed every part of the Data Manager update behaves exactly as intended, while also re-confirming four other previously-working areas — sorting the company list, the evidence page, a stock's price chart, and the honest "not yet proven" labels. One unrelated spot-check hit a page that intentionally hides a company count until a separate internal step is run — not a problem this iteration caused, and the same figure checked out fine on the pages that do show it. Next: close out the official sign-off, then turn to re-earning "Proven" status for the retired trading ideas on the deeper 30-year history.

## What it can do today

The product lets users browse a leaderboard of hundreds of companies with up to thirty years of price history each, sort and filter by sector (with an honest "Unassigned" label for unmapped companies), and switch a stock's chart between a recent and full-history view. It shows an honest, auditable evidence status — currently "not yet proven" pending re-certification — on every score and past trading idea, tied to the current market regime, and lets users browse the company list as it looked on any past date. Refreshing prices on the Data Manager page now covers the whole company list at once, with a coverage calendar that clearly separates price data from already-scored data. Unexpected errors show a contained retry message instead of a blank screen.

_Last updated: 2026-07-08 after iteration 21._
