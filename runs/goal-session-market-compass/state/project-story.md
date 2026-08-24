# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the daily briefing's core, locked each evening's briefing into a tamper-evident record, and cut backend memory use by 29% — short of target, still an open owner decision.

Then a data-recovery drill accidentally deleted two trading days of prices (11–12 August). A repair tool that finds exactly what's missing and touches nothing else restored 585 of the 587 affected stocks, leaving two names unrestorable for checked reasons; the owner has since formally closed that repair.

Turning to the daily-summary pages, which still compute from the old data, the team built safety checks first — and one caught a real problem: the database still carried an old, switched-off promise about how records link together, so cleaning it up wasn't yet safe. The owner authorized a narrow repair of that one table. The team removed the outdated link, proved all 24 saved briefings survived byte-for-byte, and fixed a bug where an old briefing wrongly claimed "everything checks out" with no proof (it now says "can't verify"). The repair went slightly further than approved, resetting a few unused technical defaults, so the team paused for sign-off; the owner reviewed it, accepted the small extra change rather than risk a second rewrite, and the team hardened the repair tool so it can't repeat the mistake.

With every safety check now passing against the real database, the owner authorized the next, riskier step: clearing out the stale calculation records for the 11 trading dates the original incident damaged, to make room for them to be rebuilt cleanly. This round, the team carried that out exactly as approved — the leftover records for those 11 dates are gone, nothing else in the database moved (checked row by row against a saved before-picture), and the recovered trading days, the saved briefings, and the watchlist all came through untouched. A careful double-check afterward found two small paperwork slips — an internal tracking number had quietly drifted since an earlier round, and a note claiming a group of records was "already cleared" turned out to be wrong — neither changed what was actually deleted, and both are now recorded as things to settle before the rebuild. The team has paused again, deliberately: rebuilding those 11 dates is the next big step, and just like this one, it needs its own fresh go-ahead from the owner.

## What it can do today

The product shows every stock's real sector label instead of "Unassigned," explains why each next-session candidate was picked and why others were not, and keeps the two trading days lost in the August incident permanently restored in the price history. Backtesting, sector and theme views, and the methodology reference all work as before. The daily summary and "what changed" pages remain unreliable for a stretch of dates until the cleared records are rebuilt — that rebuild is the very next step, pending the owner's go-ahead. Because the cleanup removed the newest few days' records as intended, the app's "Latest" date currently reads about three weeks earlier than before, until the rebuild restores it.

_Last updated: 2026-08-24 after iteration 13._
