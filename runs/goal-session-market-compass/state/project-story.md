# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and recovered 585 of 587 stocks lost in an early data-recovery drill.

Later rounds found and fixed a hidden volume-data bug in one stock (AVB), proving no other stored price had moved, then discovered that simply starting the app could overwrite results on days still waiting to be rebuilt after an earlier incident. A safety guard against that was built and tested over several rounds, but only ever against a practice copy of the database.

Iteration 18 switched that guard on for the real database, proving every one of the eleven damaged days was refused while ordinary days stayed allowed, and closed a second hidden overwrite path — but found a narrower one still open, so the app stayed switched off pending an owner decision.

The owner approved the full four-step rebuild in writing, and iteration 19 carried out the first and biggest step: rebuilding all eleven damaged days' worth of market analysis — scores, sector and theme rankings, and individual stock results — through the ordinary, unmodified scanning engine, in one careful, fully-checked run. The team verified the result three separate ways rather than trusting its own report: reading the live database directly, comparing it against the state recorded at the end of the previous round, and comparing the rebuilt numbers against a screenshot taken before the original incident happened. All eleven days now hold real numbers again and nothing else in the database moved. The rebuild is real, but it is only step one of four — the eleven days still have no forward-looking research figures and their saved snapshots haven't been refreshed, so the app stays switched off and the incident is still officially "not yet repaired." The next step, already approved, is filling in those missing figures.

## What it can do today

The product lets users see each stock's honest, filled-in sector label, see why each next-session candidate was picked and why others weren't, and browse the two trading days lost in the August data incident — restored, with their trading-volume numbers corrected — in the price history.

_Last updated: 2026-08-26 after iteration 19._
