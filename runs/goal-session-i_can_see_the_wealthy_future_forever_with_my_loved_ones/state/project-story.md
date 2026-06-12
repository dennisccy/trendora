# Project story so far

Trendora is a private stock-research tool that helps you see today's market clearly, step back to any past date, understand why each stock ranks the way it does, and look up any term the app uses — all without placing orders or touching real money.

## How it has grown

The product arrived at this session already carrying a full set of verified capabilities from a prior build cycle: a live dashboard with a market-regime score, a ranked stock leaderboard filterable by sector or pattern, individual stock pages with a price chart and a plain-language breakdown of every score component, walk-forward backtest evidence with control groups, a Factor Research Lab, a persistent watchlist, and a Data Manager that handles imports, coverage gaps, and interrupted jobs.

Iteration 0 was a baseline check: 38 carried capabilities confirmed working, six new must-haves identified as not yet built. Iterations 1 and 2 closed the remaining surface gaps. Every date in the app now always displays as YYYY-MM-DD. Historical date links survive a reload or a fresh tab. A "Major indexes & regime" card on the dashboard shows the S&P 500, Nasdaq, Russell 2000, and Equal-Weight S&P 500 with color bands marking each period as risk-on, neutral, or risk-off. The same regime bands appear behind every stock's detail chart.

Iteration 3 stayed behind the scenes, rewiring the data import pipeline to fetch multiple stocks at once and write completed batches in a single transaction — observable as a faster import with the same honest amber "rate-limited — resumable" state and Resume-from-checkpoint behavior.

Iteration 4 finished the original goal. A searchable glossary of 118 plain-language definitions now lives on the Methodology page, and every dense analysis surface carries inline info-tooltips that show the same definition right there. All original buildable journeys passed, and the team approved a seven-journey extension batch (J-48..J-54).

Iteration 5 opened the extension batch with three front-end improvements. The stock leaderboard became sortable by any column — click a header to re-order rows, click again to reverse, click the rank column to restore the original scanner order. No scores ever change during a sort; it is purely a view re-arrangement. Every in-app link now carries the selected historical date in its address, so sharing or middle-clicking any link while browsing a past date will take anyone to that exact same snapshot. Leaderboard tickers now open the stock detail in a new tab, leaving the leaderboard undisturbed.

Iteration 6 upgraded the dashboard's major-indexes and market-regime chart. When browsing a past date the chart no longer hides data after your selected date — the full stored price history and regime bands stay visible, with a clearly labelled dashed vertical line marking exactly where your selected date falls. At the latest date the chart looks the same as before with no marker. Also bundled: clicking the small info icon next to a leaderboard column header now opens the term definition without accidentally triggering a sort, and a browser developer-overlay error badge that appeared on the stocks page since iter-5 is gone.

## What it can do today

The product lets users see the latest market regime and top-ranked stocks on a dashboard with a major-indexes chart showing the full stored market history and a visible as-of marker when browsing historically; open any stock for a full explainable score breakdown with a regime-banded price chart; step back to any past date with a single global switcher so every page reflects that snapshot; sort the leaderboard by any column and restore the original ranking with one click; copy or middle-click any in-app link while viewing a historical date and land on that same dated view; click a leaderboard ticker to open the stock detail in a new tab without losing the leaderboard state; run walk-forward backtest evidence with control groups and return attribution; explore factor effectiveness in the Research Lab; save stocks to a persistent watchlist; manage price-data imports including rate-limited jobs that pause gracefully and resume from a checkpoint; and look up any term via a 118-term searchable glossary or inline info-tooltips on every dense analysis surface. All dates everywhere display as YYYY-MM-DD.

_Last updated: 2026-06-12 after iteration 6._
