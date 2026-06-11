# Project story so far

Trendora is a private stock-research tool that helps you see today's market clearly, step back to any past date, and understand why each stock ranks the way it does — all without placing orders or touching real money.

## How it has grown

The product arrived at this session already carrying a full set of verified capabilities from a prior build cycle. It can show a live dashboard with a market-regime score, rank stocks by setup quality, filter by sector or pattern, and display a price chart with a plain-language breakdown of every score component. A global date switcher lets you jump to any past date and see exactly how the market looked on that day — the same score, the same regime label, the same ranked list, all read from an immutable stored snapshot.

The walk-forward backtest page shows how the scoring system has performed over time, with honest NA values where the data window is too short, control-group comparisons against random same-sector picks and broad benchmarks, and full return attribution broken down by sector, rank band, and cohort. The Research Factor Lab lets you explore which individual factors (like relative strength or volatility) predicted returns best, broken down by decile and market regime. A watchlist persists your tracked names across sessions. The Data Manager lets you import price history from multiple providers, inspect coverage gaps, and manage interrupted imports cleanly.

This session opened with a baseline verification pass (iteration 0): every one of the 38 carried capabilities was confirmed still working on the unchanged codebase, and six new must-haves were confirmed as not yet built. Those six — consistent ISO date formatting, shareable historical date links, a major-indexes chart with regime overlays on the dashboard, regime color bands on stock charts, a faster parallel data pipeline, and a full ≥100-term glossary — are the gap this session now targets.

## What it can do today

The product lets users see the latest market-regime score and top-ranked stocks on a dashboard, browse and filter 122 ranked stocks by setup, sector, or pattern, explore theme and sector leaderboards, open any stock for a full explainable score breakdown with price chart, step back to any past date with a single date switcher, review walk-forward backtest evidence with honest NA values and control groups, save stocks to a persistent watchlist, manage price-data imports from multiple providers, and explore factor-effectiveness research in the Factor Lab.

_Last updated: 2026-06-11 after iteration 0._
