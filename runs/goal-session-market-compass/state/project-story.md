# Project story so far

Trendora is a research tool for a stock-market investor, learning to open each evening with a short, honest "Today" briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the daily briefing's core, locked each evening's briefing into a tamper-evident record, and shrank backend memory use by 29% — short of target, still an open owner decision.

Then an accident happened: a data-recovery drill accidentally deleted two days of stock prices (11 and 12 August). The team built a fenced-off repair tool that works out exactly which prices are missing and refuses, in code, to touch anything else. The first live attempt failed cleanly when the original supplier started blocking automated requests. A second attempt, switching supplier and adding a safety check that compares how prices move rather than their raw level, found one stock just outside tolerance and correctly refused to write anything — a flaw in that safety check was caught and fixed first. The redesigned check then ran for real: a first careful batch of 20 (of 587 missing) companies passed and got their prices back, though that batch only proved the check worked, not that two different suppliers agree with each other. Along the way, a safety-check tool meant to stay off during the repair switched itself on twice and briefly overwrote two of the team's own incident-proof pictures — repaired each time, though the underlying trigger stayed live.

This round, the team finished the job: it checked the remaining 567 companies one by one with the same honest rule and got 565 more of them back. Only two names could not be restored, and both have a clear, checked reason rather than a guess — one stock stopped trading at the data source entirely, and one didn't have enough recent price history to check safely. So 585 of the original 587 affected stocks now have their prices back, and the tool that kept switching itself on stayed off the whole round this time. What's not fixed yet: the daily summary and "what changed" pages people actually read still compute from the old, incomplete data — rebuilding those is the very next piece of work.

## What it can do today

The product still shows every stock's real sector label instead of "Unassigned", and explains why each next-session candidate was picked and why others were not. Backtesting, sector and theme views, and the methodology reference all work as before. The plain-English daily summary and "what changed" list remain unreliable for the two recovered dates until the pages are rebuilt from the now-restored price history — that rebuild is the very next piece of work.

_Last updated: 2026-08-23 after iteration 9._
