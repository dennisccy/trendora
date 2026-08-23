# Project story so far

Trendora is a research tool for a stock-market investor, learning to open each evening with a short, honest "Today" briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the daily briefing's core, locked each evening's briefing into a tamper-evident record, and shrank backend memory use by 29% (short of target — still an open owner decision).

Then a data-recovery drill accidentally deleted two days of stock prices (11 and 12 August). The team built a repair tool that works out exactly what's missing and refuses to touch anything else; after a failed first supplier and a near-miss safety check that was caught and fixed, the redesigned check restored prices in two rounds — 20 companies, then the remaining 567 — leaving only two names unrestorable for clear, checked reasons. The owner has since formally closed that repair: 585 of the original 587 affected stocks have their prices back for good.

Attention then turned to the daily summary and "what changed" pages, which still compute from the old, incomplete data even though the prices themselves are fixed. Before touching that shared data, the team built and proved a set of safety checks, and those checks caught something important: the database still carried an old, switched-off promise about how its records link together, so the big cleanup was not yet safe to start. The team paused and asked the owner to choose how to resolve it.

This round the owner authorized a narrow, carefully-checked repair of that one database table, and the team carried it out: the outdated linking rule was removed, and all 24 saved evening briefings were checked byte-by-byte to prove nothing was lost. A separate honesty bug was fixed at the same time — the app used to wrongly claim "everything checks out" for older briefings missing some bookkeeping detail; it now says "can't verify this" instead. But the repair went slightly further than the owner had approved — it also reset a few unused technical defaults on that table — so the team has paused again, this time to get the owner's sign-off on that small extra change before the next, bigger step: rebuilding the daily summary pages themselves.

## What it can do today

The product shows every stock's real sector label instead of "Unassigned", explains why each next-session candidate was picked and why others were not, and the two trading days lost in the August data incident are back in the price history for good. Backtesting, sector and theme views, and the methodology reference all work as before. The plain-English daily summary and "what changed" list remain unreliable for the two recovered dates until the pages are rebuilt from the now-restored price history — that rebuild is paused pending the owner's sign-off on this round's database repair.

_Last updated: 2026-08-23 after iteration 11._
