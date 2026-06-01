# Project story so far

Trendora is a local-first, research-only US equity leadership scanner — a decision-support workstation that ranks the market after the close and works to earn the user's trust with forward-tested evidence, rather than ever shouting "buy."

## How it has grown

Trendora arrived at this session already substantially built by earlier work — a dense, dark analytical dashboard for ranking US stocks, sectors, and themes after the market close, designed around skepticism: every score is explained, every idea shows what would prove it wrong, and the product tracks whether its own past picks actually worked. This first iteration was a deliberate stock-taking. Rather than add anything, it ran every planned feature against the live product to record exactly what already works and what is still missing.

The check-up found a strong foundation. The daily market overview, the ranked stock, theme, and sector leaderboards, the explainable per-stock scorecards, the never-rewritten history of past scans, the forward-tested evidence page (with a fair random same-sector comparison), the plain-language glossary, and the past-date scorecard all work today. The product also correctly refuses to flag anything "actionable" on a defensive, risk-off day — a deliberate guardrail — and honestly shows "not enough data yet" instead of inventing numbers.

Three gaps remain. There is no dataset-growth tool yet for adding more days of history; the backtest screen still keeps its own date picker instead of using the single shared date control; and the deeper breakdown of which individual stocks and sectors actually drove the results is missing. A handful of other features look healthy but couldn't be fully click-tested this round and need a clean re-check.

Next, the work turns to closing those three gaps — starting with unifying the date control, then adding the results breakdown, then building the dataset-growth tool.

## What it can do today

The product lets users see the day's market overview at a glance, browse ranked lists of stocks, themes, and sectors, open any stock for an explained scorecard and the price level that would invalidate the idea, revisit past scan days exactly as they were recorded, read forward-tested evidence of how higher-ranked picks performed against the market and a fair random benchmark, look up every label and pattern in a plain-language glossary, and open a past date to read its forward-test scorecard with honest "not enough data yet" marks.

_Last updated: 2026-06-01 after iteration 0._
