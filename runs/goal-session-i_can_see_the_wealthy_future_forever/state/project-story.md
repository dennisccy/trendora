# Project story so far

Trendora is a local-first, research-only US equity leadership scanner — a decision-support workstation that ranks the market after the close and works to earn the user's trust with forward-tested evidence rather than ever shouting "buy."

## How it has grown

Trendora arrived at this session already substantially built — a dense, dark analytical dashboard for ranking US stocks, sectors, and themes after the close, designed around skepticism: every score is explained, every idea shows what would prove it wrong, and the product tracks whether its own past picks actually worked. The first iteration was a deliberate stock-taking — rather than add anything, it ran every planned feature against the live product to record what already works and what is still missing.

The check-up found a strong foundation: the daily market overview, the ranked stock, theme, and sector leaderboards, the explainable per-stock scorecards, the never-rewritten history of past scans, the forward-tested evidence page (with a fair random same-sector comparison), and the plain-language glossary all worked. The product also refused to flag anything "actionable" on a defensive, risk-off day, and showed honest "not enough data yet" marks rather than inventing numbers. Three gaps stood out — no tool to grow the dataset with more history, a backtest screen that kept its own date picker instead of the shared date control, and no breakdown of which stocks and sectors actually drove the results.

The second iteration closed the first of those gaps. The backtest screen used to carry its own separate date menu; now it reads the single shared date control at the top of the app, like every other screen. Pick a date once and it stays the same as you move around, and changing it re-points the backtest scan and its forward-test results too — so browsing any past date now works consistently across the dashboard, stocks, themes, sectors, and backtest together, and the one rule the product had been quietly breaking (two competing date controls) is fixed. Next, the work turns to the results breakdown — which individual stocks and sectors drove the forward-tested returns — followed later by the dataset-growth tool.

## What it can do today

The product lets users see the day's market overview at a glance; browse ranked lists of stocks, themes, and sectors; open any stock for an explained scorecard and the price that would invalidate the idea; revisit past scan days exactly as recorded; open a past date and read the whole product — dashboard, leaderboards, and backtest — as it stood that day, all driven by one shared date control; read forward-tested evidence of how higher-ranked picks performed against the market and a fair random benchmark; and look up every label and pattern in a plain-language glossary — with honest "not enough data yet" marks instead of fabricated numbers.

_Last updated: 2026-06-01 after iteration 1._
