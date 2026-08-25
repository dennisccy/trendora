# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the daily briefing, locked each evening into a tamper-evident record, and trimmed backend memory (short of target, still open). A data-recovery drill then deleted two trading days; a repair tool restored 585 of 587 affected stocks, later formally closed.

Since then, the team closed a database safety gap before it caused harm, carried out a narrow owner-approved repair (accepted with a small overshoot rather than redone), hardened the tool, and — with every safety check passing — cleared the stale calculation records for the 11 damaged trading dates, pausing again for the owner's go-ahead on the rebuild itself.

The next round built the safety checks the rebuild will need and investigated AVB, a stock whose recovered prices sit on a different number scale than every other stock. Its first check called AVB's numbers safe, but an independent look found that check had only ever looked at price, never volume — the honest answer was "not enough evidence." A test that round also briefly overwrote three saved record-keeping files from before; caught, restored, and fixed.

This round, the owner granted a one-time permission to check AVB's real trading volume against an outside source, and the answer is now a measured fact: on every other day Trendora's own numbers keep AVB's true trading value steady, but its two recovered days kept the adjusted price while leaving volume untouched, so their reported trading value reads about 2.8 times too high. The tool that missed this before is now genuinely fixed. The round also caught something more urgent: simply starting the app would silently write bad data into the real database, since the newest stored trading day is one of the 11 still waiting to be rebuilt. The rebuild stays paused, now waiting on the owner to approve a start-up safety guard and decide how to handle AVB's mismatched volume.

## What it can do today

The product shows every stock's real sector label, explains why each next-session candidate was picked and why others weren't, and keeps the two trading days lost in the August incident restored in the price history — though AVB's trading-volume figures on those two days are now known to read about 2.8 times too high, pending an owner decision. Backtesting, sector/theme views, and the methodology reference all work as before. The daily-summary and "what changed" pages stay unreliable until the cleared records rebuild, two pages (the Today page's quick read and the Market page's carry-over view) still don't work, and the app's "Latest" date reads about three weeks earlier than usual until the rebuild finishes.

_Last updated: 2026-08-25 after iteration 15._
