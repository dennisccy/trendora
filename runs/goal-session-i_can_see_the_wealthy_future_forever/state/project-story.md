# Project story so far

Trendora is a local-first, research-only US equity leadership scanner — a decision-support workstation that ranks the market after the close and earns the user's trust with forward-tested evidence rather than ever shouting "buy."

## How it has grown

Trendora arrived at this session already substantially built — a dense, dark analytical dashboard that ranks US stocks, sectors, and themes after the close, designed around skepticism: every score is explained, every idea shows what would prove it wrong, and the product tracks whether its own past picks actually worked. Its first pass added nothing on purpose — a deliberate stock-taking that ran every planned feature against the live product and flagged three gaps: no tool to grow the dataset with more history, a backtest screen that kept its own date picker instead of the shared date control, and no breakdown of which stocks and sectors actually drove the results.

The next pass closed the date-control gap: the backtest screen, which used to carry its own separate date menu, now reads the single shared control at the top of the app like every other screen — pick a date once and it stays put as you move around. The pass after that delivered the results breakdown — any forward-tested return now opens into a plain view of the individual stocks that drove it up or down, how it splits across sectors and ranking tiers, and the overall spread and hit-rate, on both the evidence page and the backtest screen.

This latest pass closed the final gap: a tool to grow the dataset on demand. A new "Data Manager" screen shows how much history the product holds and how many days still need filling in; the user picks a single date or a date range, chooses to backfill snapshots and/or fetch fresh prices, presses Start, and watches a live progress bar count through the work before a clear final summary. Newly added days immediately become selectable in the shared date control without reloading, and the evidence page's track record visibly grows to cover them. When a live price fetch can't reach its source it says so plainly and never invents prices, and dates too early for results still honestly show "not enough data yet." With that, every major capability Trendora set out to deliver is now built and working; the remaining work is a careful re-check of a few existing screens before calling the goal done.

## What it can do today

The product lets users see the day's market overview at a glance; browse ranked lists of stocks, themes, and sectors; open any stock for an explained scorecard and the price that would invalidate the idea; revisit past scan days exactly as recorded; move the whole product — dashboard, leaderboards, and backtest — to any past day with one shared date control; read forward-tested evidence of how higher-ranked picks performed against the market and a fair random benchmark; break any of those returns down into the stocks, sectors, and ranking tiers that drove it, with its spread and hit-rate; grow the dataset on demand by date or range and watch it backfill live; and look up every label and pattern in a plain-language glossary — always with honest "not enough data yet" marks instead of fabricated numbers.

_Last updated: 2026-06-01 after iteration 3._
