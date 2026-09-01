# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and survived a recovery drill and a deeper data-repair incident. Iteration 28 rebuilt the home page into a "Today" page that reads top-to-bottom as a real ten-second briefing, moving the old dashboard intact to a new "Market" page. Iterations 29-31 added the three improving/worsening words, a "what changed since last time" list, and a plain-English daily summary, closing ten of the project's eleven planned capabilities.

That left one open item: making sure the program doesn't use too much of the computer's memory. Iteration 32 measured it properly and found it still too high at first glance, but a closer look showed almost all of that was a brief startup spike rather than what the program actually holds once running. Iteration 33 fixed how the backend loads price history at startup, and the new measurement fit comfortably under the limit for the first time — the last of the eleven planned capabilities to close. But the team held off calling the whole project finished: that closing round was supposed to get a second, independent check and didn't say so, and the project's own automatic safety check still refused to certify the round over a bookkeeping mismatch.

Iteration 34 settled both of those open points. A second, completely independent measurement — a fresh restart of the program, checked by a different reviewer — landed close enough to the first (within a fraction of a percent) to put the memory question to rest for good, at roughly 12% under the limit either way. The internal bookkeeping tool that had been wrongly marking the whole project "blocked" was fixed, and this time the full team of checks — reviewer, independent auditor, quality check, and closing gate — genuinely ran end to end, unlike the shortcut that slipped through the round before. Every other capability was re-checked once more and still works exactly as before, with careful cross-checks proving no number a user sees moved at all. The project is now considered finished, pending one confirmation from the owner accepting the final memory figure.

## What it can do today

The product lets users see each stock's honest sector label; see why each next-session candidate was picked or skipped; trust that each evening's saved briefing matches the screen exactly and never changes once saved, and openly says when an old day's data was lost and rebuilt; browse the two trading days recovered from an earlier data problem; read a reordered "Today" page with a ten-second briefing, including three plain words for whether the market is improving or worsening, a "what changed since last time" list, and a plain-English daily summary; and reach the full original dashboard on a separate "Market" page. It also now runs comfortably and reliably within the computer's memory limits, confirmed by two independent checks that agree with each other closely.

_Last updated: 2026-09-01 after iteration 34._
