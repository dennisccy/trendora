# Project story so far

Trendora is a local-first, research-only US equity leadership scanner — a decision-support workstation that ranks the market after the close and earns the user's trust with forward-tested evidence rather than ever shouting "buy."

## How it has grown

Trendora arrived at this session already substantially built — a dense, dark analytical dashboard that ranks US stocks, sectors, and themes after the close, designed around skepticism: every score is explained, every idea shows what would prove it wrong, and the product tracks whether its own past picks actually worked. Its first iteration added nothing on purpose — it was a deliberate stock-taking that ran every planned feature against the live product and flagged three gaps: no tool to grow the dataset with more history, a backtest screen that kept its own date picker instead of the shared date control, and no breakdown of which stocks and sectors actually drove the results.

The second iteration closed the first gap. The backtest screen used to carry its own separate date menu; now it reads the single shared date control at the top of the app, like every other screen — pick a date once and it stays put as you move around, so browsing any past day works consistently across the whole product.

The third iteration delivered the results breakdown. Trendora could already tell you how its higher-ranked picks performed on average, but not *why* — which names carried the result and which dragged it. Now, on both the evidence page and the backtest screen, any forward-tested return opens into a plain breakdown: the individual stocks that drove it up or pulled it down (each with its sector), how the return splits across sectors and across ranking bands, and the overall spread and hit-rate. On the backtest screen you can switch which time window you're looking at — a day, a week, or longer — and the breakdown updates instantly, without reloading or changing the date. As everywhere else, when a date is too recent for results to have played out, the panels honestly show "not enough data yet" instead of inventing zeros. With the date control unified and the results now explainable, the last gap left is the tool to grow the dataset with more history — the next target.

## What it can do today

The product lets users see the day's market overview at a glance; browse ranked lists of stocks, themes, and sectors; open any stock for an explained scorecard and the price that would invalidate the idea; revisit past scan days exactly as recorded; open a past date and read the whole product — dashboard, leaderboards, and backtest — as it stood that day, all driven by one shared date control; read forward-tested evidence of how higher-ranked picks performed against the market and a fair random benchmark; break any forward-tested return down into the stocks, sectors, and ranking bands that drove it, with its spread and hit-rate; and look up every label and pattern in a plain-language glossary — always with honest "not enough data yet" marks instead of fabricated numbers.

_Last updated: 2026-06-01 after iteration 2._
