# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and recovered 585 of 587 stocks lost in a recovery drill — until a deeper data problem forced a full shutdown, repair, and live re-verification; a testing-tool bug that briefly touched real data was found and fixed, and the app's memory use was checked and partly trimmed.

Iteration 28 rebuilt the home page into a "Today" page reading top-to-bottom as a real ten-second briefing, while the old dashboard moved intact to a new "Market" page. One idea didn't fully land: three words meant to say whether the market is improving or worsening showed "NA" everywhere, since only brand-new briefings carried them.

Iteration 29 proved the idea works, on one carefully chosen date, but today's own front page still showed "NA". Iteration 30 finished the job: an authorized update to today's own briefing made the three words read correctly on the page people actually land on. Two honest side notes came with it — the update quietly removed an old warning about lost-and-rebuilt data for that day, and a safety check for a related feature had been rewritten but never re-run — both flagged for the owner to weigh in on.

Iteration 31 closed the session's two oldest open pieces: a "what changed since your last visit" list and a plain-English daily summary, both stuck half-finished for 25 rounds since an earlier data problem. Both now work, checked directly against the saved numbers, and nothing else on the site changed. Ten of the project's eleven planned capabilities now work. The one still open checks that the program doesn't use too much of the computer's memory — the earlier measurement turned out to have no real proof behind it, so the team will measure it again properly, on a quiet computer, before anything else is added.

## What it can do today

The product lets users see each stock's honest sector label; see why each next-session candidate was picked or skipped; trust that each evening's saved briefing matches the screen exactly and never changes once saved, and openly says when an old day's data was lost and rebuilt; browse the two trading days recovered from an earlier data problem; read a reordered "Today" page with a ten-second briefing, including three plain words for whether the market is improving or worsening, a "what changed since last time" list that quietly holds back unimportant tiny moves, and a plain-English daily summary with its numbers available on request; and reach the full original dashboard on a separate "Market" page.

_Last updated: 2026-09-01 after iteration 31._
