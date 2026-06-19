# Project story so far

Trendora is a local-first, research-only US equity leadership scanner — a decision-support and evidence-tracking platform that ranks stocks, explains every score, and proves its own usefulness through walk-forward historical evidence, without placing orders or touching real money.

## How it has grown

The product arrived at this session already carrying a full, verified set of capabilities: a live dashboard with a market-regime score, a ranked stock leaderboard filterable by sector or pattern, individual stock pages with a price chart and a plain-language breakdown of every score component, walk-forward backtest evidence with control groups, a Factor Research Lab, a persistent watchlist, and a Data Manager that handles imports, coverage gaps, and interrupted jobs.

Iterations 1 through 24 built out the full surface in waves. The dashboard gained a major-indexes chart, a regime label with a ranked top-themes strip, and a global as-of URL that deep-links to any snapshot date with stepping buttons and year/month jump dropdowns. The Research Lab connects every sample-count chip to the exact stored observations. Themes and Sectors leaderboards gained five forward-return columns; the Expand-universe job gained Yahoo authentication; and five colour-graded max-drawdown columns appeared on every forward-return surface. As-of deep links render correctly from the first paint with no hydration mismatch.

Iterations 29 through 32 opened the market-intelligence chapter. The dashboard gained a Market Phase & Severity panel, a phase history timeline with dated causal downtrend episodes, a structurally fenced retrospective sub-view, a recovery-turn signal, and a Recovery-Turn Edge study. The Research page gained a Downtrend Opportunity study. The Data Manager gained a macro feed panel listing FRED economic series.

Iterations 33 and 34 tackled the dynamic point-in-time universe, building per-date coverage panels and a membership timeline. Iteration 35 ran an operator-confirmed overnight rebuild that fixed the stocks leaderboard — it now shows the honest point-in-time universe for every past date, empty before October 2021 and growing naturally to roughly 544 stocks by today. That same data growth exposed a performance gap: the Data Manager page began hanging because its coverage calculation looped through all 1,369 dates without a cache.

Iteration 36 fixed the hang by caching the membership timeline keyed to the dataset version, dropping response time from a five-minute hang to about fifteen seconds. But it inadvertently introduced a new bug: stocks with zero price history in the candidate pool were being re-read from the database once per date and per parallel worker instead of just once per job. The coverage diagnostic also could not get live browser confirmation that iteration.

Iteration 37 is the close-out. It fixed the load-once bug by recording an empty price series for every zero-bar candidate so the prefilled cache covers them — no per-date re-read, same numbers served. The full backend test suite flushed 977 passed, zero failed. A live browser pass (using Playwright since Chrome MCP was unavailable) confirmed the Data Manager page hydrates in about twenty-one seconds, the membership timeline step-function chart renders with its three honesty labels, and the coverage diagnostic shows the correct 544 admitted stocks with exclusion counts — the same values as before, now delivered reliably.

## What it can do today

The product lets users see a live dashboard with a regime score, Market Phase & Severity panel, phase history timeline with dated downtrend episodes, and a fenced retrospective sub-view. They can explore a Recovery-Turn Edge study and a Downtrend Opportunity study on the Research page. They can step to any past snapshot date and have every surface re-point instantly. The stocks leaderboard shows the honest point-in-time universe — empty before October 2021, rising to roughly 544 stocks by today. Users can open any stock for an explainable score breakdown with a regime-banded chart and five forward-return columns each paired with a colour-graded drawdown figure, sort and filter every leaderboard, click any sample count to see the exact stored observations, and save stocks to a watchlist. The Data Manager shows the membership growth timeline, a per-date coverage diagnostic, import progress tracking, and a macro feed panel.

_Last updated: 2026-06-19 after iteration 37._
