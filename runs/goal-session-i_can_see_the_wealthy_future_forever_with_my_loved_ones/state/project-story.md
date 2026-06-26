# Project story so far

Trendora is a local-first, research-only US equity leadership scanner — a decision-support and evidence-tracking platform that ranks stocks, explains every score, and proves its own usefulness through walk-forward historical evidence, without placing orders or touching real money.

## How it has grown

The product arrived at this session already carrying a full, verified set of capabilities: a live dashboard with a market-regime score, a ranked stock leaderboard filterable by sector or pattern, individual stock pages with a score breakdown, walk-forward backtest evidence with control groups, a Factor Research Lab, a persistent watchlist, and a Data Manager that handles imports, coverage gaps, and interrupted jobs.

Iterations 1 through 28 built out the platform in waves: a major-indexes chart, a regime label with a ranked top-themes strip, a global as-of URL with stepping buttons and year/month jump dropdowns, five forward-return columns and colour-graded max-drawdown columns on every leaderboard surface, Yahoo authentication for the expand-universe job, and a confirm-gated snapshot rebuild.

Iterations 29 through 43 opened the market-intelligence chapter and hardened the backend. The dashboard gained a Market Phase & Severity panel, a phase history timeline with causal downtrend episodes, a recovery-turn signal, a Downtrend Opportunity study, and a macro-series feed. The stocks leaderboard began showing only stocks that were actually tradable on each past date. The Data Manager gained a rising membership-growth timeline with pagination and a per-date coverage diagnostic. A schema-versioning fix ensured stale cache rows are always recomputed, and a single-flight computation guard stopped the server freezing under concurrent load.

Iterations 44 through 51 sharpened the dashboard with a severity-velocity line and a consolidated two-pane cross-view chart; transformed the Research section into a hub of seven individually-loaded labs; resolved a serious memory problem that had caused the Factor Lab to crash on the full live database; added a proximity-to-52-week-high column on the stocks leaderboard; and turned the Factor Lab into a full all-factors comparison table with each row expandable to a 10-bucket decile breakdown and drill-through evidence counts. Iteration 51 was the verify-only close-out: 1,079 tests passed, the goal was declared achieved.

Iteration 52 opens a new chapter. The goal was extended with four fresh Research labs to build. The first, delivered this iteration, transformed the Factor Lab: it now shows all five time horizons (1, 5, 10, 20, and 60 trading days) at once — no dropdown needed. Each factor row now pairs both its expected forward return and its worst-case max-drawdown for every horizon, giving a full edge-and-risk profile in a single glance. Three more cross-sectional labs — Regime Lab, Phase & Severity Lab, and a three-way Regime × Phase × Factor study — are queued for the next three iterations.

## What it can do today

The product lets users see a live market dashboard with a regime score, severity-velocity line, and phase timeline; step to any past snapshot date and have every surface update; browse stocks that were actually tradable on each historical date via a leaderboard with forward-return columns, colour-graded max-drawdown, and a sortable proximity-to-52-week-high column; open any stock for a named score breakdown; save stocks to a watchlist; check the Data Manager for a membership-growth timeline with filters and a per-date coverage diagnostic; and explore all seven Research labs — the Factor Lab (now showing all five configured horizons at once with paired forward-return and max-drawdown columns, each factor row expandable to its full 10-bucket decile breakdown with drill-into-evidence observation counts, no horizon-picking required), multi-factor Combination Lab, Setup and Pattern event study, Severity-velocity × Regime study, Downtrend Opportunity, Recovery-Turn Edge, and Regime × Setup × Pattern study.

_Last updated: 2026-06-27 after iteration 52._
