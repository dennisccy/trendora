# Project story so far

Trendora is a private stock-research tool that helps you see today's market clearly, step back to any past date, and understand why each stock ranks the way it does — all without placing orders or touching real money.

## How it has grown

The product arrived at this session already carrying a full set of verified capabilities from a prior build cycle: a live dashboard with a market-regime score, a ranked stock leaderboard filterable by sector or pattern, individual stock pages with a price chart and a plain-language breakdown of every score component, walk-forward backtest evidence with control groups, a Factor Research Lab, a persistent watchlist, and a Data Manager that handles imports, coverage gaps, and interrupted jobs.

Iteration 0 was a baseline check: 38 carried capabilities confirmed working, six new must-haves identified as not yet built — consistent date formatting, shareable date links, a market-index chart with regime overlays, regime bands on stock charts, a faster data pipeline, and a full glossary.

Iteration 1 delivered the date-formatting work. Every date shown anywhere in the app now always displays as YYYY-MM-DD regardless of the user's browser locale. The date entry fields on the Data Manager were replaced with validated text boxes that block submission on a badly formatted date.

Iteration 2 closed the URL-sharing gap and added two major chart surfaces. A historical date link now fully survives a reload or a fresh browser tab — you can copy the URL and share it, and the recipient lands on exactly the same snapshot you were viewing. A new "Major indexes & regime" card on the dashboard shows how the S&P 500, Nasdaq 100, Russell 2000, and S&P 500 Equal-Weight have moved over a selectable range, with color bands painted behind the lines that mark each period as risk-on, neutral, or risk-off. On every stock's detail page the same regime bands appear behind the price chart, driven by the identical color mapping so the same date always shows the same color on both surfaces. Toggles let you hide either chart surface, and those preferences persist across reloads.

Iteration 3 stayed entirely behind the scenes. The data import pipeline now fetches multiple stocks at once (up to four in parallel) instead of one at a time, and writes each completed batch as a single database transaction. A backfill job that spans many dates now loads each stock's price history only once for the whole job, instead of re-reading it for every date. The observable result is a faster import and backfill experience with the same honest amber "rate-limited — resumable" state and Resume-from-checkpoint behavior. All 659 backend tests stayed green, and the existing resumable-import flow was directly verified in the browser for the first time this session.

## What it can do today

The product lets users see the latest market regime and top-ranked stocks on a dashboard with a major-indexes chart showing regime history; open any stock for a full explainable score breakdown with a price chart that includes regime color bands; copy and share historical date links that survive new tabs and reloads; step back to any past date with a single global switcher so every page reflects that exact snapshot; review walk-forward backtest evidence with control groups and return attribution; explore factor effectiveness in the Research Lab; save stocks to a persistent watchlist; and manage price-data imports — including jobs that pause gracefully when rate-limited and resume from exactly where they left off without re-fetching already-saved data. All dates everywhere display as YYYY-MM-DD.

_Last updated: 2026-06-11 after iteration 3._
