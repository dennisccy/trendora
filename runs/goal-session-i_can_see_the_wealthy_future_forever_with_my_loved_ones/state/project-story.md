# Project story so far

Trendora is a local-first, research-only US equity leadership scanner — a decision-support and evidence-tracking platform that ranks stocks, explains every score, and proves its own usefulness through walk-forward historical evidence, without placing orders or touching real money.

## How it has grown

The product arrived at this session already carrying a full, verified set of capabilities: a live dashboard with a market-regime score, a ranked stock leaderboard filterable by sector or pattern, individual stock pages with a price chart and a plain-language breakdown of every score component, walk-forward backtest evidence with control groups, a Factor Research Lab, a persistent watchlist, and a Data Manager that handles imports, coverage gaps, and interrupted jobs.

Iterations 1 through 28 built out the platform in waves: a major-indexes chart, a regime label with a ranked top-themes strip, a global as-of URL with stepping buttons and year/month jump dropdowns, five forward-return columns and five colour-graded max-drawdown columns on every leaderboard surface, Yahoo authentication for the expand-universe job, and a confirm-gated snapshot rebuild that makes newly added members appear across all historical dates.

Iterations 29 through 37 opened the market-intelligence chapter and completed the dynamic universe. The dashboard gained a Market Phase & Severity panel, a phase history timeline with dated causal downtrend episodes and a fenced retrospective sub-view, a recovery-turn signal, a Recovery-Turn Edge study, a Downtrend Opportunity study, and a macro-series feed. The stocks leaderboard now shows only the stocks that were actually tradable on each past date, and the Data Manager shows a rising membership-growth timeline alongside a per-date coverage diagnostic.

Iterations 38 through 40 reorganised the dashboard home and fixed a caching defect. The dashboard now leads with a compact at-a-glance row showing regime score and market-phase severity side by side, followed by a two-pane cross-view chart with regime bands on top and phase colour bands, a 0–100 severity line, and a bear-probability line on the bottom. A schema-versioning fix ensured stale cache rows are recomputed with the full payload; live screenshots in iteration 40 confirmed the bottom pane populates correctly and early dates show an honest empty state.

Iteration 41 made the Data Manager's membership history list navigable. The panel previously showed every snapshot date in one long scroll; it now has Year and Month dropdown filters and a 10-dates-per-page pager with an honest count readout. The underlying data is unchanged — this is a pure view transform — and 16 live browser checks confirmed all existing surfaces (coverage diagnostic, stock leaderboard, risk-off gate, score consistency) remain intact. One buildable feature remains before the current goal extension is fully complete.

## What it can do today

The product lets users see a live dashboard with a compact regime-and-phase summary on first paint, a two-pane cross-view chart showing regime bands and phase-severity bands on a shared timeline, a phase history timeline with retrospective sub-view, a Recovery-Turn Edge study and a Downtrend Opportunity study, step to any past snapshot date and have every surface update instantly, view a stock leaderboard showing only the stocks tradable on that past date, open any stock for a score breakdown with colour-graded forward-return and drawdown columns, sort and filter every leaderboard, click any sample count to see the exact stored observations, save stocks to a watchlist, and check the Data Manager for a membership-growth timeline with Year/Month filters and pagination, a coverage diagnostic, import progress tracking, and a macro-series feed.

_Last updated: 2026-06-20 after iteration 41._
