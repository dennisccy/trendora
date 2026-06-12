# Project story so far

Trendora is a private stock-research tool that helps you see today's market clearly, step back to any past date, understand why each stock ranks the way it does, and look up any term the app uses — all without placing orders or touching real money.

## How it has grown

The product arrived at this session already carrying a full set of verified capabilities from a prior build cycle: a live dashboard with a market-regime score, a ranked stock leaderboard filterable by sector or pattern, individual stock pages with a price chart and a plain-language breakdown of every score component, walk-forward backtest evidence with control groups, a Factor Research Lab, a persistent watchlist, and a Data Manager that handles imports, coverage gaps, and interrupted jobs.

Iterations 1 through 4 closed the remaining surface gaps and then achieved the original goal. Every date in the app displays as YYYY-MM-DD. Historical date links survive a reload or a fresh tab. A major-indexes and regime card on the dashboard shows the S&P 500, Nasdaq, Russell 2000, and Equal-Weight S&P 500 with color bands marking each market period. A searchable glossary of 118 plain-language definitions now lives on the Methodology page, and every dense analysis surface carries inline info-tooltips from the same catalog.

With the original goal met, the team approved a seven-journey extension batch. Iteration 5 made the stock leaderboard sortable by any column, ensured every in-app link carries the selected historical date so sharing or middle-clicking any link takes you to that same snapshot, and made leaderboard tickers open the stock detail in a new tab.

Iteration 6 upgraded the dashboard's major-indexes chart so browsing a past date no longer hides data after your selected date — the full stored price history stays visible with a clearly labelled vertical line marking where your chosen date falls. It also fixed a browser developer-overlay error badge that had appeared since iter-5 by moving the column-header info icon outside the sort button.

Iteration 7 closed the evidence chain on the Research Lab. Every "N=" sample count across all three research labs — Factor Lab, Combination Lab, and Event Study — is now a clickable link. Clicking it opens a new drill-down page showing the exact stored observations behind that number: the ticker, the snapshot date, the stored factor value or matched pattern, and the realized forward return. The page total is guaranteed to equal the chip you clicked, enforced by sharing the identical membership logic the research aggregates already use. From any row, clicking the ticker opens that stock's dated detail page in a new tab, restoring that observation's exact snapshot date through the single global date control. Browser QA confirmed 9 out of 9 tests passing, and the evaluator independently re-proved count-equality live against every chip kind.

## What it can do today

The product lets users see the latest market regime and top-ranked stocks on a dashboard with a full-history indexes chart and a visible as-of marker when browsing historically; open any stock for a full explainable score breakdown with a regime-banded price chart; step back to any past date with a single global switcher so every page reflects that snapshot; share or middle-click any in-app link to land on that exact dated view; sort the leaderboard by any column and restore the original ranking with one click; click a leaderboard ticker to open the stock detail in a new tab; run walk-forward backtest evidence with control groups and return attribution; explore factor effectiveness, multi-factor combinations, and setup/pattern event studies in the Research Lab; click any "N=" sample count to see the exact stored observations behind it and jump from any observation row to that date's full stock snapshot in a new tab; save stocks to a persistent watchlist; manage price-data imports including rate-limited jobs that pause gracefully and resume from a checkpoint; and look up any term via a 118-term searchable glossary or inline info-tooltips on every dense analysis surface.

_Last updated: 2026-06-12 after iteration 7._
