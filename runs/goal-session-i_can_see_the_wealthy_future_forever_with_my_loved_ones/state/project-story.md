# Project story so far

Trendora is a private stock-research tool that helps you see today's market clearly, step back to any past date, and understand why each stock ranks the way it does — all without placing orders or touching real money.

## How it has grown

The product arrived at this session already carrying a full set of verified capabilities from a prior build cycle. It can show a live dashboard with a market-regime score, rank stocks by setup quality, filter by sector or pattern, and display a price chart with a plain-language breakdown of every score component. A global date switcher lets you jump to any past date and see exactly how the market looked on that day — the same score, the same regime label, the same ranked list, all read from an immutable stored snapshot.

The walk-forward backtest page shows how the scoring system has performed over time, with honest NA values where the data window is too short, control-group comparisons against random same-sector picks and broad benchmarks, and full return attribution broken down by sector, rank band, and cohort. The Research Factor Lab lets you explore which individual factors (like relative strength or volatility) predicted returns best, broken down by decile and market regime. A watchlist persists your tracked names across sessions. The Data Manager lets you import price history from multiple providers, inspect coverage gaps, and manage interrupted imports cleanly.

Session iteration 0 was a baseline verification pass: every one of the 38 carried capabilities was confirmed still working on the unchanged codebase, and six new must-haves were identified as not yet built — consistent ISO date formatting, shareable historical date links, a major-indexes chart with regime overlays on the dashboard, regime color bands on stock charts, a faster parallel data pipeline, and a full ≥100-term glossary.

Iteration 1 tackled the first two of those gaps. Every date shown across the entire app — in the date switcher, on stock pages, in scanner run lists, in chart tooltips, in job cards, in coverage summaries — now always reads in YYYY-MM-DD format regardless of your browser's locale. The date entry fields on the Data Manager page were replaced with text boxes that validate your input immediately, showing a clear error and blocking submission if the date is not in the correct format. Work also advanced on shareable historical date links: when you select a past date, the URL already updates to carry that date, and pasting an invalid link degrades safely to the latest view — but the reload and new-tab preservation step still needs a small targeted fix, planned as the first task next iteration.

## What it can do today

The product lets users see the latest market-regime score and top-ranked stocks on a dashboard, browse and filter 122 ranked stocks by setup, sector, or pattern, explore theme and sector leaderboards, open any stock for a full explainable score breakdown with price chart, step back to any past date with a single date switcher, review walk-forward backtest evidence with honest NA values and control groups, save stocks to a persistent watchlist, manage price-data imports from multiple providers with validated date inputs, and explore factor-effectiveness research in the Factor Lab. All dates throughout the app display consistently in YYYY-MM-DD format.

_Last updated: 2026-06-11 after iteration 1._
