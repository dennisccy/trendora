# Project story so far

Trendora is a local-first, research-only US equity leadership scanner — a decision-support and evidence-tracking platform that ranks stocks, explains every score, and proves its own usefulness through walk-forward historical evidence, without placing orders or touching real money.

## How it has grown

The product arrived at this session already carrying a full verified set of capabilities: a live dashboard with a market-regime score, a ranked stock leaderboard, individual stock pages with a score breakdown, walk-forward backtest evidence, a Factor Research Lab, a persistent watchlist, and a Data Manager that handles imports and coverage gaps.

Iterations 1 through 28 built out the platform in waves: a major-indexes chart, a regime label with a ranked top-themes strip, a global as-of URL with stepping buttons and year/month jump dropdowns, five forward-return columns and colour-graded max-drawdown columns on every leaderboard surface, Yahoo authentication, and a confirm-gated snapshot rebuild.

Iterations 29 through 43 opened the market-intelligence chapter and hardened the backend. The dashboard gained a Market Phase & Severity panel, a phase history timeline, a recovery-turn signal, and a macro-series feed. The Data Manager gained a membership-growth timeline with pagination and a per-date coverage diagnostic. A schema-versioning fix and a single-flight computation guard stopped the server freezing under concurrent load.

Iterations 44 through 51 sharpened the dashboard with a severity-velocity line and a consolidated cross-view chart; resolved a serious memory problem that had caused the Factor Lab to crash on the full live database; added a proximity-to-52-week-high column on the leaderboard; and turned the Factor Lab into a full all-factors comparison table with each row expandable to a 10-bucket decile breakdown.

Iterations 52 through 55 added four new Research labs. Factor Lab now shows all five time horizons at once, pairing expected forward return and worst-case max-drawdown side by side. The Regime Lab cross-references returns and drawdown with the six canonical market regimes. The Market Phase & Severity Lab does the same by phase label and stress level. The Regime × Phase × Factor Lab provides a three-way interaction view for any chosen factor, with filters, sorting, pagination, and drill-through to exact observations. After iteration 55 all planned features were built and verified for the first time.

Iteration 56 put the finishing touches on the Research section. The ten lab cards are now in a logical reading order — the analysis labs (Factor Lab, Regime Lab, Market Phase & Severity, Regime × Phase × Factor) lead the hub — and every horizon-based table groups its expected-return columns before its drawdown columns, matching the stock leaderboard layout. All 111 planned features are built and verified.

## What it can do today

The product lets users see a live market dashboard with a regime score, severity-velocity line, and phase timeline; step to any past snapshot date and have every screen update; browse historically-accurate stock leaderboards with expected-return columns, colour-graded max-drawdown, and a sortable proximity-to-52-week-high column; open any stock for a named score breakdown; save stocks to a watchlist; check the Data Manager for a membership-growth timeline with filters and a per-date coverage diagnostic; and explore ten Research labs — now presented in a logical reading order, with every horizon-based table grouping expected-return columns before drawdown columns — including the Factor Lab (all horizons, expandable decile breakdowns), Regime Lab, Market Phase & Severity Lab, Regime × Phase × Factor Lab (three-way interaction for any factor at five time horizons with drill-through to exact observations), and six further studies.

_Last updated: 2026-06-28 after iteration 56._
