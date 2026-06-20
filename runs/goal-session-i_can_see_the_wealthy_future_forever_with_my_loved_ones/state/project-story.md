# Project story so far

Trendora is a local-first, research-only US equity leadership scanner — a decision-support and evidence-tracking platform that ranks stocks, explains every score, and proves its own usefulness through walk-forward historical evidence, without placing orders or touching real money.

## How it has grown

The product arrived at this session already carrying a full, verified set of capabilities: a live dashboard with a market-regime score, a ranked stock leaderboard filterable by sector or pattern, individual stock pages with a price chart and a plain-language breakdown of every score component, walk-forward backtest evidence with control groups, a Factor Research Lab, a persistent watchlist, and a Data Manager that handles imports, coverage gaps, and interrupted jobs.

Iterations 1 through 28 built out the platform in waves: a major-indexes chart, a regime label with a ranked top-themes strip, a global as-of URL with stepping buttons and year/month jump dropdowns, five forward-return columns and five colour-graded max-drawdown columns on every leaderboard surface, Yahoo authentication for the expand-universe job, and a confirm-gated snapshot rebuild that makes newly added members appear across all historical dates.

Iterations 29 through 32 opened the market-intelligence chapter. The dashboard gained a Market Phase & Severity panel, a phase history timeline with dated causal downtrend episodes, a fenced retrospective sub-view, a recovery-turn signal, a Recovery-Turn Edge study, a Downtrend Opportunity study, and a macro-series feed. Iterations 33 through 37 delivered the dynamic point-in-time universe: the stocks leaderboard now shows only the stocks that were actually tradable on each past date, the Data Manager shows a rising membership-growth timeline, and a per-date coverage diagnostic confirms how many stocks were admitted or excluded.

Iteration 38 turned attention to the dashboard experience, reorganising the home page so the most important numbers appear first and adding a new two-pane cross-view chart that shows regime bands and phase colour bands on the same shared timeline. The restructure shipped to the DOM, but a caching issue caused the phase bands in the bottom pane to appear empty — a stale cache row for the live current date was written before the new data field was added to the payload.

Iteration 39 fixed that caching defect at the backend layer. A payload-schema version token is now folded into the cache key, guaranteeing that any stale row missing the phase-bands data is recomputed once with the full payload. Sixteen unit tests — including a test that specifically probes an already-cached stale row, exactly reproducing the bug — are green. However, a Chrome browser connectivity problem blocked the screen-capture step for the second consecutive iteration, so the visual proof that the chart now renders correctly is still pending. The next step is a brief live check to confirm the fix works on screen, then build the two remaining features.

## What it can do today

The product lets users see a live dashboard with a regime score and market-phase severity panel, browse a phase history timeline with dated downtrend episodes and an optional retrospective view, check the Recovery-Turn Edge and Downtrend Opportunity studies on the Research page, step to any past snapshot date and have every surface update instantly, view a stock leaderboard showing only the stocks tradable on that past date (empty before late 2021, roughly 544 stocks today), open any stock for a score breakdown with colour-graded forward-return and drawdown columns, sort and filter every leaderboard, click any sample count to see the exact stored observations, save stocks to a watchlist, and check the Data Manager for membership growth, a coverage diagnostic, import progress tracking, and a macro-series feed. The dashboard home now shows a compact at-a-glance summary row and a two-pane regime-versus-phase cross-view chart (phase bands repaired at the data layer; visual confirmation pending one more screen check).

_Last updated: 2026-06-20 after iteration 39._
