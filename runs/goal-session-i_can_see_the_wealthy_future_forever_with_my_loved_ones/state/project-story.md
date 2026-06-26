# Project story so far

Trendora is a local-first, research-only US equity leadership scanner — a decision-support and evidence-tracking platform that ranks stocks, explains every score, and proves its own usefulness through walk-forward historical evidence, without placing orders or touching real money.

## How it has grown

The product arrived at this session already carrying a full, verified set of capabilities: a live dashboard with a market-regime score, a ranked stock leaderboard filterable by sector or pattern, individual stock pages with a price breakdown of every score component, walk-forward backtest evidence with control groups, a Factor Research Lab, a persistent watchlist, and a Data Manager that handles imports, coverage gaps, and interrupted jobs.

Iterations 1 through 28 built out the platform in waves: a major-indexes chart, a regime label with a ranked top-themes strip, a global as-of URL with stepping buttons and year/month jump dropdowns, five forward-return columns and colour-graded max-drawdown columns on every leaderboard surface, Yahoo authentication for the expand-universe job, and a confirm-gated snapshot rebuild that makes newly added members appear across all historical dates.

Iterations 29 through 43 opened the market-intelligence chapter, completed the dynamic universe, and hardened the backend. The dashboard gained a Market Phase & Severity panel, a phase history timeline with causal downtrend episodes and a fenced retrospective sub-view, a recovery-turn signal and study, a Downtrend Opportunity study, and a macro-series feed. The stocks leaderboard now shows only stocks that were actually tradable on each past date. The Data Manager gained a rising membership-growth timeline with Year/Month filters and a per-date coverage diagnostic. A schema-versioning fix ensured stale cache rows are always recomputed; a single-flight computation guard stopped the server freezing under concurrent load.

Iterations 44 and 45 sharpened the dashboard and transformed the Research section. The old duplicate indexes card was removed; the phase pane now spans full stored history at any past date; the P(bear) line was replaced by a severity-velocity line; the Research section became a hub of seven individually-loaded labs, including a Severity-velocity × Regime study that honestly reports its own honest finding.

Iterations 46 through 48 resolved a serious memory problem that surfaced when the database reached three million rows. Two research labs were running out of memory on every request. Iteration 48 completed the fix — all reads are now processed in efficient batches, the Factor Lab serves a full decile table on the live database, and the full test suite flushed 1,060 tests passed, zero failed.

Iteration 49 added two clean, independent improvements: the stocks leaderboard gained a "Proximity to 52w high" column placed right after Risk, sortable and with a glossary tooltip, showing each stock's distance below its one-year high as a plain percentage. The detail page's Leadership breakdown now shows that same percentage instead of an opaque internal rank, keeping the two views in agreement. The readiness badge in the top bar was also fixed — it now correctly reaches Ready even when the app is opened at the machine's local network address, which previously showed a permanent "Backend unavailable" error.

## What it can do today

The product lets users see a live market dashboard with a single chart, severity-velocity line, and regime-aware tooltip; step to any past snapshot date and have every surface update; browse stocks that were actually tradable on each historical date via a leaderboard that now includes a sortable proximity-to-52-week-high column; open any stock for a score breakdown with forward-return and drawdown columns and a matching proximity percentage; save stocks to a watchlist; check the Data Manager for a membership-growth timeline with month/year filters, pagination, and a coverage diagnostic; and explore all seven Research labs — fully restored Factor Lab, multi-factor combination, Setup and Pattern event study, Severity-velocity × Regime study, Downtrend Opportunity, Recovery-Turn Edge, and Regime × Setup × Pattern study. The readiness badge works correctly on both localhost and a local network address.

_Last updated: 2026-06-26 after iteration 49._
