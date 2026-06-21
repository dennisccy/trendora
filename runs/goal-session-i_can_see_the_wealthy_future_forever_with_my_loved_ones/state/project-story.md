# Project story so far

Trendora is a local-first, research-only US equity leadership scanner — a decision-support and evidence-tracking platform that ranks stocks, explains every score, and proves its own usefulness through walk-forward historical evidence, without placing orders or touching real money.

## How it has grown

The product arrived at this session already carrying a full, verified set of capabilities: a live dashboard with a market-regime score, a ranked stock leaderboard filterable by sector or pattern, individual stock pages with a price chart and a plain-language breakdown of every score component, walk-forward backtest evidence with control groups, a Factor Research Lab, a persistent watchlist, and a Data Manager that handles imports, coverage gaps, and interrupted jobs.

Iterations 1 through 28 built out the platform in waves: a major-indexes chart, a regime label with a ranked top-themes strip, a global as-of URL with stepping buttons and year/month jump dropdowns, five forward-return columns and five colour-graded max-drawdown columns on every leaderboard surface, Yahoo authentication for the expand-universe job, and a confirm-gated snapshot rebuild that makes newly added members appear across all historical dates.

Iterations 29 through 37 opened the market-intelligence chapter and completed the dynamic universe. The dashboard gained a Market Phase & Severity panel, a phase history timeline with dated causal downtrend episodes and a fenced retrospective sub-view, a recovery-turn signal, a Recovery-Turn Edge study, a Downtrend Opportunity study, and a macro-series feed. The stocks leaderboard now shows only the stocks that were actually tradable on each past date, and the Data Manager shows a rising membership-growth timeline alongside a per-date coverage diagnostic.

Iterations 38 through 41 reorganised the dashboard home, fixed a caching defect, and made the Data Manager's membership history navigable. The dashboard now leads with a compact at-a-glance row and a two-pane cross-view chart; a schema-versioning fix ensured stale cache rows are recomputed with the full chart payload; and the previously unwieldy snapshot-date list gained Year/Month dropdown filters and a 10-dates-per-page pager.

Iteration 42 focused entirely on stability under load. When several browser tabs open the Data page simultaneously, the server previously ran a separate expensive calculation for each one, which could exhaust the connection pool and intermittently freeze the machine. Now all simultaneous visitors share a single computation — proven with 12 parallel requests triggering exactly one heavy compute — and the backend start script received hard limits on connections, timeouts, and process memory. No number on any page changed.

Iteration 43 was the final confirmation pass: zero code changes, 18 live browser checks via Playwright, and a confirmed full-suite result of 991 passing tests and 0 failures. Every value on the Data Manager page, the Stocks leaderboard, and the Dashboard matched the known-good baseline exactly. J-100 — the last unbuilt buildable journey — was formally declared passing, and the goal was achieved.

## What it can do today

The product lets users see a live dashboard with a compact regime-and-phase summary on first paint, a two-pane cross-view chart showing regime bands and phase-severity bands on a shared timeline, a phase history timeline with retrospective sub-view, a Recovery-Turn Edge study, and a Downtrend Opportunity study. Users can step to any past snapshot date and have every surface update instantly, view a stock leaderboard showing only the stocks tradable on that past date, open any stock for a score breakdown with colour-graded forward-return and max-drawdown columns, sort and filter every leaderboard, click any sample count to see the exact stored observations, save stocks to a watchlist, and check the Data Manager for a membership-growth timeline with Year/Month filters and pagination, a coverage diagnostic, import progress tracking, a macro-series feed, and a confirm-gated snapshot rebuild. The server handles simultaneous use without freezing.

_Last updated: 2026-06-21 after iteration 43._
