# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the daily briefing's core, locked each evening's briefing into a tamper-evident record, and cut backend memory use by 29% — short of target, still an open owner decision.

Then a data-recovery drill accidentally deleted two trading days of prices (11-12 August). A repair tool that finds exactly what's missing and touches nothing else restored 585 of the 587 affected stocks in two rounds, leaving two names unrestorable for checked reasons; the owner has since formally closed that repair.

Turning to the daily-summary pages, which still compute from the old data, the team built safety checks before touching it — and one caught a real problem: the database still carried an old, switched-off promise about how records link together, so the cleanup wasn't yet safe. The team paused for an owner decision.

The owner authorized a narrow repair of that one table. The team removed the outdated link, proved all 24 saved briefings survived byte-for-byte, and fixed a bug where an old briefing wrongly claimed "everything checks out" with no proof (it now says "can't verify"). But the repair went slightly further than approved, resetting a few unused technical defaults, so the team paused again for sign-off.

This round the owner gave that sign-off, accepting the small extra change rather than risking a second rewrite. The team then finished the cleanup: fixed the repair tool itself so it can't make that mistake again, made the "can't verify" honesty check airtight against a wider range of bad records, and corrected an inaccurate internal note. Every safety condition for the big rebuild now checks out against the real database, for the fourth review running. The team has paused once more — not because anything is wrong, but because the next step, rebuilding the daily-summary pages, is deliberately an owner "go" decision, the same category of step that caused the original data loss.

## What it can do today

The product shows every stock's real sector label instead of "Unassigned," explains why each next-session candidate was picked and why others were not, and the two trading days lost in the August incident are back in the price history for good. Backtesting, sector and theme views, and the methodology reference all work as before. The daily summary and "what changed" pages remain unreliable for the two recovered dates until they are rebuilt — every safety check for that rebuild now passes, awaiting the owner's go-ahead.

_Last updated: 2026-08-24 after iteration 12._
