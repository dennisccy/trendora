# Project story so far

Trendora is a local-first, research-only US stock scanner that, after the market closes each day, ranks the market from overall mood down to individual stocks and explains every score it shows — it never just says "buy this."

## How it has grown

The project began with a deliberately empty starting line: the first step built nothing and instead confirmed the workspace was bare, then laid out the plan — how the product would be organized for the person using it, and the one rule that governs everything: every number is worked out once and shown the same way on every page, so a stock's score can never disagree with itself. That plan was reviewed and approved before any construction began.

The second step is where Trendora became a real, openable app for the first time. We built the workstation's frame — a permanent left-hand menu, the page layout, and the dark, data-focused look the whole product will wear. Across the top sits an honest status badge that tells you whether the data engine is connected; it shows the data source, the latest date it has, and how many symbols are loaded — and if the engine is down, it plainly says so rather than pretending all is well.

Underneath that frame we loaded the foundation everything else will stand on: about five and a half years of real daily price history for roughly 158 stocks and funds. It is stored once and frozen, so the app runs completely offline — no internet, no keys, no logins — and gives the same answers every single time it restarts. We even proved, with a real test on real history, that this data captures both a genuine market downturn and a genuine market rally, so future rankings can be tested fairly against both kinds of weather.

This step shows no rankings or scores yet — that is by design. Every section greets you with a clear "nothing here yet" placeholder, and the honest groundwork is the point. Next, that price history gets turned into the first real readouts: a sense of the overall market mood and a leaderboard of the strongest sectors and industries.

## What it can do today

The product lets users open the workstation and move between its seven sections — a daily dashboard, leaderboards for stocks, themes and sectors, a per-stock detail view, a history of past scans, an evidence page, and a personal watchlist — and see a live, honest badge for whether the data engine is connected. There are no rankings or scores yet; every page shows a clear "nothing here yet" placeholder while a frozen, fully offline 5.4-year price history sits ready underneath.

_Last updated: 2026-05-29 after iteration 1._
