# Project story so far

Trendora is a private stock-research tool that helps you see today's market clearly, step back to any past date, understand why each stock ranks the way it does, and look up any term the app uses — all without placing orders or touching real money.

## How it has grown

The product arrived at this session already carrying a full set of verified capabilities from a prior build cycle: a live dashboard with a market-regime score, a ranked stock leaderboard filterable by sector or pattern, individual stock pages with a price chart and a plain-language breakdown of every score component, walk-forward backtest evidence with control groups, a Factor Research Lab, a persistent watchlist, and a Data Manager that handles imports, coverage gaps, and interrupted jobs.

Iteration 0 was a baseline check: 38 carried capabilities confirmed working, six new must-haves identified as not yet built. Iterations 1 and 2 closed those surface gaps quickly. Every date in the app now always displays as YYYY-MM-DD. Historical date links survive a reload or a fresh tab. A "Major indexes & regime" card on the dashboard shows the S&P 500, Nasdaq, Russell 2000, and Equal-Weight with color bands marking each period as risk-on, neutral, or risk-off. The same regime bands appear behind every stock's detail chart, driven by the same color mapping.

Iteration 3 stayed behind the scenes, rewiring the data import pipeline to fetch multiple stocks at once and write completed batches in a single transaction — observable as a faster import with the same honest amber "rate-limited — resumable" state and Resume-from-checkpoint behavior.

Iteration 4 finished the original goal. A searchable Glossary of 118 plain-language definitions now lives on the Methodology page, browsable by category or searchable by word. Every dense analysis surface carries inline info-tooltips that show the same definition right there. All 44 original buildable journeys passed, and the human approved a seven-journey extension batch (J-48..J-54).

Iteration 5 opened the extension batch by tackling the three pure front-end improvements that share the same surfaces. The stock leaderboard is now sortable by any column — click a header to re-order rows by ticker, sector, leadership, entry quality, risk, or setup; click it again to reverse; click the rank column to restore the scanner's original stored order. No scores, buckets, or flags ever change during a sort — it is purely a view re-arrangement. Every in-app link now carries the selected historical date in its href, so middle-clicking, ctrl-clicking, or copying and pasting any link while browsing a past date will take anyone who opens it to that exact same snapshot. Leaderboard tickers now open the stock detail in a new tab, leaving the leaderboard's filters, sort order, scroll position, and date untouched on the original tab. Three of the seven extension journeys are now passing; four remain as planned targets for the next iterations.

## What it can do today

The product lets users see the latest market regime and top-ranked stocks on a dashboard with a major-indexes chart showing regime history; open any stock for a full explainable score breakdown with a regime-banded price chart; step back to any past date with a single global switcher so every page reflects that snapshot; sort the leaderboard by any column and restore the original ranking with one click; copy or middle-click any in-app link while viewing a historical date and land on that same dated view; click a leaderboard ticker to open the stock detail in a new tab without losing the leaderboard state; run walk-forward backtest evidence with control groups and return attribution; explore factor effectiveness in the Research Lab; save stocks to a persistent watchlist; manage price-data imports including rate-limited jobs that pause gracefully and resume from a checkpoint; and look up any term via a 118-term searchable glossary or inline info-tooltips on every dense analysis surface. All dates everywhere display as YYYY-MM-DD.

_Last updated: 2026-06-12 after iteration 5._
