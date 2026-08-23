# Project story so far

Trendora is a research tool for a stock-market investor, learning to open each evening with a short, honest "Today" briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the daily briefing's core, locked each evening's briefing into a tamper-evident record, and shrank backend memory use by 29% (short of target — still an open owner decision).

Then a data-recovery drill accidentally deleted two days of stock prices (11 and 12 August). The team built a repair tool that works out exactly what's missing and refuses to touch anything else; after a failed first supplier and a near-miss safety check that was caught and fixed, the redesigned check restored prices in two rounds — 20 companies, then the remaining 567 — leaving only two names unrestorable for clear, checked reasons. 585 of the original 587 affected stocks now have their prices back.

This round the team turned to the next problem: the daily summary and "what changed" pages people read still compute from the old, incomplete data, even though the prices themselves are fixed. Before touching that shared data, the team built and proved a set of safety checks — a full "before" snapshot of everything the cleanup would touch, and one frozen fingerprint of today's calculation rules so the eventual rebuild can prove it used a single consistent recipe throughout. Those checks caught something important: the database still carries an old, switched-off promise about how its records link together, and twelve existing records already break that promise — so the big cleanup is not yet safe to start. The team has paused and is asking the product owner to choose how to resolve it: accept the current state in writing, authorise a small guarded database fix, or loosen the rule's wording. Nothing was broken or lost this round, and the tool that had previously switched itself on by mistake and briefly overwritten evidence stayed off for the second round running.

## What it can do today

The product still shows every stock's real sector label instead of "Unassigned", explains why each next-session candidate was picked and why others were not, and the two trading days lost in the August data incident are back in the price history. Backtesting, sector and theme views, and the methodology reference all work as before. The plain-English daily summary and "what changed" list remain unreliable for the two recovered dates until the pages are rebuilt from the now-restored price history — that rebuild is paused pending one decision from the product owner.

_Last updated: 2026-08-23 after iteration 10._
