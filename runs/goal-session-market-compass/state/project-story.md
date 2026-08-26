# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and — after a data-recovery drill deleted two trading days — restored 585 of 587 affected stocks while closing a database safety gap along the way.

Later rounds discovered that one stock, AVB, had two recovered trading days sitting on the wrong number scale, cleared safe by a first check that had compared price only and never volume; a deeper check confirmed the problem, and a following round fixed AVB's volume numbers for good, proving nothing else among 3.3 million stored prices had moved. The bigger discovery underneath it was that simply starting the app could silently overwrite results on the newest of eleven trading days still waiting to be properly rebuilt after an earlier incident. A safety guard against that was built and tightened over two more rounds, tested with dozens of passing checks — but only ever against a practice copy of the database, never switched on for the real one.

This round finally switched that guard on for the real database. It now carries a genuine "do not overwrite" record for all eleven damaged days, and the team proved it directly: every one of the eleven is refused, ordinary days are still allowed, and nothing else in the database moved. Along the way, the team also found and closed a second, previously-hidden way the app could have written over the same data. But the same check surfaced a new, narrower danger: someone can still force the app to overwrite one of the eleven days simply by asking for it by a particular web address, and nothing stops that yet. So the app stays switched off while the owner decides whether to close that narrower gap first, and separately whether to authorize the actual rebuild of the eleven damaged days, which still has not begun.

## What it can do today

The product lets users see each stock's honest, filled-in sector label, see why each next-session candidate was picked and why others weren't, and browse the two trading days lost in the August data incident — restored, with their trading-volume numbers corrected — in the price history.

_Last updated: 2026-08-26 after iteration 18._
