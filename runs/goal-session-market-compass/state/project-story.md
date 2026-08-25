# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the daily briefing's core, locked each evening's briefing into a tamper-evident record, and cut backend memory use by 29% — short of target, still an open owner decision. A later data-recovery drill accidentally deleted two trading days of prices; a careful repair tool restored 585 of 587 affected stocks, and the owner has since formally closed that repair.

Turning to the daily-summary pages, the team found and fixed a database safety problem before it could cause harm, then carried out a narrow, owner-approved database repair; it went slightly further than approved, the owner accepted the small extra change rather than risk redoing it, and the repair tool was hardened against repeating the mistake. With every safety check passing, the owner then authorized clearing out the stale calculation records for the 11 trading dates the original incident damaged, to make room for a clean rebuild — the team carried that out exactly as approved, verified row-by-row against a saved before-picture, and paused again to wait for the owner's go-ahead on the rebuild itself.

This round, the team built the safety checks the rebuild will need: a fresh readiness fingerprint, automatic tripwires that would stop the rebuild if anything drifted mid-way, and an investigation into one stock (AVB) whose stored prices sit on a different number scale than every other stock. The team's own check called AVB's numbers safe, but a closer, independent look found the check never actually looked at trading volume — only price — so the honest answer is "not enough evidence yet," not "safe." Separately, one of this round's own new tests accidentally overwrote three saved record-keeping files from the previous round; it was caught during review, the files were restored exactly, and the tool responsible was fixed so it can't do that again. The rebuild remains paused, waiting for the owner to decide how to settle the one open volume question.

## What it can do today

The product shows every stock's real sector label instead of "Unassigned," explains why each next-session candidate was picked and why others were not, and keeps the two trading days lost in the August incident permanently restored in the price history. Backtesting, sector and theme views, and the methodology reference all work as before. The daily summary and "what changed" pages stay unreliable for a stretch of dates until the cleared records are rebuilt — paused on one open question about a single stock's trading-volume data, which only the owner can resolve. Because the cleanup removed the newest few days' records as intended, the app's "Latest" date currently reads about three weeks earlier than before, until the rebuild restores it.

_Last updated: 2026-08-25 after iteration 14._
