# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and — after a data-recovery drill deleted two trading days — restored 585 of 587 affected stocks while closing a database safety gap along the way.

Later rounds turned to one stock, AVB, whose two recovered trading days sat on a different number scale than the rest. An early check wrongly called AVB safe, because it compared price only, never volume; with the owner's one-time permission to check AVB's real volume against an outside source, the team confirmed the suspicion — the recovered days kept the adjusted price but left volume untouched, about 2.8 times too high. That round also caught something more urgent: simply starting the app would silently write bad data in, because the newest stored trading day is one of 11 still waiting to be rebuilt.

The next round fixed AVB's volume numbers for real — proven to have touched nothing else among 3.3 million stored prices — and built a start-up safety guard to stop the app writing onto any of the 11 damaged days. But that guard was only tested on a practice copy of the database, never switched on for the real one.

This round tightened that guard's code to read only what it needs and fail safe rather than crash, added the on/off switches for it, and proved the fix with 39 passing tests; it also corrected last round's AVB reading to the fully honest version. But the real news is that the danger is not theoretical: today, simply starting the app would both create the missing safety record and quietly write results onto one of the damaged days, because that record has never been switched on for the real database. Nothing is fixed by that alone — it is now clear exactly what starting the app today would do, and the app stays paused until the owner decides how to close the gap.

## What it can do today

The product lets users see each stock's honest, filled-in sector label, see why each next-session candidate was picked and why others weren't, and browse the two trading days lost in the August data incident — restored, and with their trading-volume numbers now corrected — in the price history.

_Last updated: 2026-08-25 after iteration 17._
