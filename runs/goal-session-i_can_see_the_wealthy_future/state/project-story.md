# Project story so far

Trendora is a local-first, research-only US stock scanner that, after the market closes, ranks the market from overall mood down to individual stocks and explains every score it shows — it never just says "buy this."

## How it has grown

Trendora began from a deliberately empty starting line with one rule that governs everything: every number is worked out once and shown the same way on every page, so a score can never disagree with itself. It became a real, openable app — a permanent left-hand menu, a dark data-focused layout, and an honest "is-the-data-fresh" badge — running entirely offline on about five and a half years of frozen daily price history for roughly 158 stocks and funds.

Then the numbers reached the screen: a Dashboard and a Sectors page reading the day's market mood, a filterable list of stocks each with three plain grades (strength, buy-point quality, risk) and a one-line reason, a Themes page, and each stock's own page with a candle-and-trend chart, its themes, and the price where the idea would be wrong. Trendora then gained a memory — a permanent, unchangeable record of every past daily scan, including real downturns where it correctly flagged zero stocks worth acting on. It learned to grade its own track record on a System Health page that replays past scans and measures how its highly graded stocks actually performed afterward, against the S&P 500, the Nasdaq-100, and a fair group of randomly chosen same-sector stocks, with honest sample sizes and a survivorship caveat. It then added a personal watchlist that remembers your own note about each stock and survives a restart — completing the original must-have list.

The vision was then widened with five new must-have goals. Trendora learned to time-travel: a top-bar switcher lets you pick any past trading day and see the entire dashboard — mood, stocks, themes, sectors, and any stock's page — exactly as it stood then, clearly badged as a historical view, and every page now loads its numbers from the saved daily snapshot rather than recomputing them on each visit, so views stay fast and perfectly consistent.

The most recent round set out to add a Backtest page — pick a past day and see how that day's top-graded picks actually performed afterward. This time the page was fully designed and approved, but the build step never ran, so nothing changed for users yet. Thirteen of the sixteen must-haves still pass; the very next step is to actually build that Backtest page.

## What it can do today

The product lets users open a daily dashboard (market mood, breadth, top sectors and themes, how many stocks are actionable, the data date); browse and filter a ranked list of stocks, each with three explainable grades and a reason; open any stock's own page for its chart, themes, and invalidation level; rank investing themes and every sector and industry; rely on every score reading the same everywhere; reopen any earlier day from a permanent scan history; pick any past trading day from a top-bar switcher to see the whole dashboard as it stood then, served fast from saved snapshots; check a System Health page that grades — with honest sample sizes and a fair control group — whether its high grades predicted better returns; and keep a personal watchlist that survives a restart.

_Last updated: 2026-05-31 after iteration 9._
