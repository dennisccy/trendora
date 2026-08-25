# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, and locked each session into a tamper-evident record. A data-recovery drill then deleted two trading days; a repair tool restored 585 of 587 affected stocks. The team closed a database safety gap, carried out a narrow owner-approved repair, hardened the tool, and cleared the stale calculation records for 11 damaged trading dates — pausing for the owner's go-ahead on the rebuild itself.

The next rounds investigated AVB, a stock whose recovered prices sit on a different number scale than every other stock. An early check wrongly called AVB's numbers safe, since it had only ever checked price, never volume. With the owner's one-time permission to check AVB's real trading volume against an outside source, the team confirmed the suspicion: AVB's two recovered days kept the adjusted price but left volume untouched, reading about 2.8 times too high. That round also caught something more urgent — simply starting the app would silently write bad data into the database, since the newest stored trading day is one of the 11 still waiting to be rebuilt.

This round, the owner authorized the actual fix: AVB's two volume numbers were corrected for real, proven byte-for-byte to have touched nothing else in the 3.3-million-row price table. With the data corrected, the rebuild's readiness check answered YES for the first time all session. But the round's biggest discovery is a gap, not a green light: the new start-up safety guard was built and thoroughly tested, but is not switched on for the real database yet, so starting the app today would still silently damage a repair-in-progress day. The rebuild stays paused, waiting on the owner to switch the guard on for real and then decide whether to rebuild the 11 missing days.

## What it can do today

The product lets users see each stock's honest, filled-in sector label, see why each next-session candidate was picked and why others weren't, and browse the two trading days lost in the August data incident — now restored, and with their trading-volume numbers corrected too — in the price history.

_Last updated: 2026-08-25 after iteration 16._
