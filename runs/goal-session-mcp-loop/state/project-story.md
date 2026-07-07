# Project story so far

Trendora is a market-leadership ranking tool that shows traders which scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample statistical testing, not in-sample curve-fitting.

## How it has grown

Trendora spent its first fifteen iterations building the trust layer itself — honest "Proven" / "Not yet proven" badges, an auditable Evidence page, a safe private testing ground for new ideas, and six certified trading edges — reaching every original must-have capability by iteration 15.

With that foundation in place, the operator aimed bigger: swap the roughly 5-year price history for a full ~30-year history across many more companies. Iteration 16 built the fetching machinery, but the outside data provider refused the request from this location, so — rather than fake the gap — the team paused for a human decision. The operator pointed it at a local archive already on the machine, and iteration 17 added matching stock-index and volatility history alongside it, each honestly labeled by source, clearing the way for the one-time switch-over.

Iteration 18 threw that switch. Price history now reaches back up to 30 years, the tracked universe grew from about 120 companies to several hundred, and — because the underlying data changed — all seven trading edges the product had ever certified were honestly re-tested against the deeper history. None held up, so the evidence system now reads "not yet proven" everywhere instead of showing stale numbers, exactly as the honesty rules require when the ground shifts under a claim. A new control lets a stock's chart switch between a recent view and its full history, and stocks whose data has gone stale are now cleanly dropped from the rankings. But the same change also broke something real: sorting the stock list by "Sector" now crashes the page for the many newly-added companies with no sector on file. Testing caught it immediately, and fixing it is the top priority — this round isn't considered finished until it's resolved.

## What it can do today

The product lets users browse a leaderboard of several hundred companies with up to 30 years of price history per stock, switch a stock's chart between a recent view and its full history, add many more tickers to a personal watchlist, and see an honest evidence status on every score and past trading idea — all currently "not yet proven" after the re-test — with full reasoning and claim history auditable on the Evidence page. One action is temporarily broken: sorting the stock list by Sector crashes the page, and fixing that is the immediate next step.

_Last updated: 2026-07-07 after iteration 18._
