# Project story so far

Trendora is a research tool for a stock-market investor, learning to open each evening with a short, honest "Today" briefing instead of a plain dashboard.

## How it has grown

Before this chapter began, Trendora was already a solid research platform. Early rounds gave every stock a real sector label, built the daily briefing's core, locked each evening's briefing into a tamper-evident record, and shrank backend memory use by 29% — short of target, still an open owner decision.

Then an accident happened: a data-recovery drill rehearsal accidentally deleted two days of stock prices (11 and 12 August). The team built a fenced-off repair tool that works out exactly which prices are missing and refuses, in code, to touch anything else. The first live attempt failed cleanly when the original supplier started blocking automated requests. A second attempt, switching supplier and adding a safety check that compares prices before trusting them, found one stock just outside tolerance and correctly refused to write anything — the days stayed missing, but the team caught and fixed a flaw in that safety check first.

This round, the owner redesigned the safety check to compare how prices move over time rather than their raw level, and the team ran it for real for the first time. It worked as designed: a first careful batch of 20 (of the 587 still missing) companies passed and got their 11-12 August prices back. Worth knowing: this batch compared Yahoo's prices against Yahoo's own older prices, not the original supplier, so it proves the check works correctly — not yet that two suppliers agree. The other 567 companies are still missing on purpose, to be restored in small checked batches. One thing to watch: a safety-check tool meant to stay off until the repair is complete switched itself on anyway this round, and briefly overwrote two of the team's own incident-proof pictures before they were restored. Fixing that comes first next round, before the team resumes the remaining 567 companies and then cleanly rebuilds everything the incident touched — a new finishing requirement the owner added this round.

## What it can do today

The rest of Trendora — scanner, sector and theme views, backtesting, methodology reference — works as before. Every stock shows its real sector instead of "Unassigned," and next-session candidates explain why each was picked and why others were not. The plain-English summary and "what changed" list stay unreliable for the newest dates while the repair continues. Still missing: a live close sealing a fresh record, the page's final layout, and a dedicated Market page.

_Last updated: 2026-08-21 after iteration 8._
