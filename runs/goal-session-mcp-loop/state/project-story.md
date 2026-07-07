# Project story so far

Trendora is a market-leadership ranking tool that shows traders which scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample testing, not in-sample curve-fitting.

## How it has grown

Trendora's first fifteen iterations built the trust layer itself: honest "Proven"/"Not yet proven" badges, an auditable Evidence page, a private testing ground for new ideas, and six certified trading edges.

Aiming bigger, the product then swapped its roughly 5-year price history for a full ~30-year history across many more companies: iteration 16 built the fetching machinery but paused for a human decision when the data provider refused the request rather than fake the gap, and iteration 17 pointed it at a local archive and added matching stock-index and volatility history, each honestly labeled by source.

Iteration 18 threw the switch — history now reaches back 30 years and the tracked universe grew from about 120 companies to several hundred. Every one of the seven trading edges the product had certified was honestly re-tested against the deeper history and none held up, so the evidence system now reads "not yet proven" everywhere instead of showing a stale number. A new chart control and a cleaner drop of stale stocks landed too — but the same change crashed the stock list whenever a user sorted by "Sector," caught immediately by testing.

Iteration 19 fixed that crash at its root: sorting and filtering by Sector now works for every company, including the roughly 4-in-5 with no sector on file, which read a plain "Unassigned" label instead of crashing. The same round fixed a Data-page memory problem that could freeze the app after a restart (now well under 20 seconds even under simultaneous load), confirmed the broader company-history timeline displays correctly end to end, and added a safety net so a future unexpected error shows a calm "try again" message instead of wiping out the app — all confirmed by watching a real browser, not just by reading code. With that setback closed, the product is stable again and ready to keep growing: still open are re-earning "Proven" status for any of the retired trading ideas on the deeper history, tidying the Data page to match the larger company list, and showing the newly-added decades of market-index history.

## What it can do today

The product lets users browse a leaderboard of several hundred companies with up to 30 years of price history each, sort and filter that list by sector (with an honest "Unassigned" label for unmapped companies), and switch a stock's chart between a recent view and its full history. It shows an honest evidence status — currently "not yet proven" pending re-certification — on every score and past trading idea, with full reasoning auditable on the Evidence page, plus evidence conditioned on the current market regime and a company list that can be browsed as it looked on any past date. Any unexpected error now shows a contained message instead of a blank screen.

_Last updated: 2026-07-07 after iteration 19._
