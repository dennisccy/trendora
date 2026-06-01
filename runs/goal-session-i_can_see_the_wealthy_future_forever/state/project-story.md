# Project story so far

Trendora is a local-first, research-only US equity leadership scanner — a decision-support workstation that ranks the market after the close and earns the user's trust with forward-tested evidence rather than ever shouting "buy."

## How it has grown

Trendora arrived at this session already substantially built — a dense, dark analytical dashboard that ranks US stocks, sectors, and themes after the close, designed around skepticism: every score is explained, every idea shows what would prove it wrong, and the product tracks whether its own past picks actually worked. Its first pass added nothing on purpose — a deliberate stock-taking that flagged three gaps: no tool to grow the dataset with more history, a backtest screen that kept its own stray date picker instead of the shared control, and no breakdown of what actually drove the results.

The passes that followed closed those gaps one by one. The backtest screen moved onto the single shared date control at the top of the app, so picking a date once holds everywhere you go. Then any forward-tested return became something you can open up — into the individual stocks that drove it up or down, how it splits across sectors and ranking tiers, and its overall spread and hit-rate. Next came the "Data Manager": a screen that shows how much history the product holds, lets the user backfill a single date or a whole range and fetch fresh prices, and watch a live progress bar before a clear final summary — new days immediately appear in the shared date control and the track record grows to cover them, while failed price fetches say so plainly and never invent numbers.

With every major capability built, the latest pass was a careful re-check of the screens that had never been driven all the way through. It confirmed two work end-to-end: filtering the stock leaderboard down to one sector or setup (with an honest "nothing matches here" message instead of fabricated rows), and the VCP chart-pattern tools that flag, explain, and forward-test that setup. Three screens still need their final check — that a saved watchlist survives a restart, that pages load fast from saved snapshots, and that a stock's scores read identically on the list and its detail page — because the automated checker ran out of time partway through. Those three are all that stand between today and calling the goal done.

## What it can do today

The product lets users see the day's market overview at a glance; browse ranked lists of stocks, themes, and sectors and filter the stock list by sector, setup, or the VCP chart pattern; open any stock for an explained scorecard and the price that would invalidate the idea; revisit past scan days exactly as recorded; move the whole product to any past day with one shared date control; read forward-tested evidence of how higher-ranked picks performed against the market and a fair random benchmark; break those returns down into the stocks, sectors, and ranking tiers that drove them; grow the dataset on demand by date or range and watch it backfill live; and look up every label and pattern in a plain-language glossary — always with honest "not enough data yet" marks instead of fabricated numbers.

_Last updated: 2026-06-01 after iteration 4._
