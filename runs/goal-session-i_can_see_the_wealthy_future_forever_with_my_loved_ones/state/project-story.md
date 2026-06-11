# Project story so far

Trendora is a private stock-research tool that helps you see today's market clearly, step back to any past date, understand why each stock ranks the way it does, and look up any term the app uses — all without placing orders or touching real money.

## How it has grown

The product arrived at this session already carrying a full set of verified capabilities from a prior build cycle: a live dashboard with a market-regime score, a ranked stock leaderboard filterable by sector or pattern, individual stock pages with a price chart and a plain-language breakdown of every score component, walk-forward backtest evidence with control groups, a Factor Research Lab, a persistent watchlist, and a Data Manager that handles imports, coverage gaps, and interrupted jobs.

Iteration 0 was a baseline check: 38 carried capabilities confirmed working, six new must-haves identified as not yet built — consistent date formatting, shareable date links, a market-index chart with regime overlays, regime bands on stock charts, a faster data pipeline, and a full glossary.

Iterations 1 and 2 closed those surface gaps in quick succession. Every date in the app now always displays as YYYY-MM-DD regardless of browser locale. Historical date links survive a reload or a fresh tab — copy the URL and send it, and the recipient lands on exactly the same snapshot. A new "Major indexes & regime" card on the dashboard shows the S&P 500, Nasdaq, Russell 2000, and Equal-Weight over a selectable range, with color bands that mark each period as risk-on, neutral, or risk-off. The same regime bands appear behind every stock's detail chart, driven by the same color mapping, with a toggle that persists across reloads.

Iteration 3 stayed behind the scenes. The data import pipeline now fetches multiple stocks at once instead of one at a time, and writes each completed batch in a single database transaction. The observable result is a faster import experience with the same honest amber "rate-limited — resumable" state and Resume-from-checkpoint behavior — verified live in the browser for the first time.

Iteration 4 finished the product. A searchable Glossary of 118 plain-language definitions now lives on the Methodology page — browse it by category (scores, setups, breadth, data, forward-testing, factor-lab statistics) or type any word to filter the list instantly. On every dense analysis surface — the Research Lab, Backtest scorecard, Stock Leaderboard, Dashboard breadth cards, and Data Manager coverage table — column headers and stat labels carry a small info marker you can hover or tap to read the exact same definition right there. Every definition comes from one shared, config-backed catalog; nothing is duplicated or hard-coded anywhere in the codebase. This was the final buildable Must-have feature, and it landed with all 44 buildable journeys passing.

## What it can do today

The product lets users see the latest market regime and top-ranked stocks on a dashboard with a major-indexes chart showing regime history; open any stock for a full explainable score breakdown with a price chart that includes regime color bands; copy and share historical date links that survive new tabs and reloads; step back to any past date with a single global switcher so every page reflects that exact snapshot; run walk-forward backtest evidence with control groups and return attribution; explore factor effectiveness in the Research Lab; save stocks to a persistent watchlist; manage price-data imports including jobs that pause gracefully when rate-limited and resume from exactly where they left off; and look up any term shown in the app via a 118-term searchable glossary on the Methodology page or inline info-tooltips on every dense analysis surface. All dates everywhere display as YYYY-MM-DD.

_Last updated: 2026-06-11 after iteration 4._
