# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and recovered 585 of 587 stocks lost in a recovery drill — until a deeper data problem forced a full shutdown, repair, and live re-verification; a testing-tool bug that briefly touched real data was found and fixed, and the app's memory use was checked and partly trimmed.

Iteration 28 rebuilt the home page into a "Today" page reading top-to-bottom as a real ten-second briefing, moving the old dashboard intact to a new "Market" page — though the three words meant to say whether the market is improving or worsening showed "NA" everywhere at first.

Iteration 29 proved those words work on one carefully chosen date; iteration 30 made them work on the actual page people land on, with two honest side notes flagged for the owner. Iteration 31 closed the session's two oldest open pieces — a "what changed since your last visit" list and a plain-English daily summary — both stuck half-finished for 25 rounds, now working and checked directly against the saved numbers. Ten of the project's eleven planned capabilities were then working, leaving only the check that the program doesn't use too much of the computer's memory.

Iteration 32 measured that memory use again, this time properly: a clean start, every reading saved to a file that survives, and an honest result — still about 2.97 GB against a 2.5 GB goal. But looking closer at the saved numbers turned up something useful: almost all of that is a five-second spike while the program is still starting up, not what it holds once it's actually running and answering requests, which is a much smaller ~710 MB. Fixing that spike is squarely on a to-do item the owner already wrote down, so the team plans to trim it next rather than waiting on a decision — though the owner could also simply accept the current number and call the memory goal met. All ten other capabilities were re-checked and still work exactly as before.

## What it can do today

The product lets users see each stock's honest sector label; see why each next-session candidate was picked or skipped; trust that each evening's saved briefing matches the screen exactly and never changes once saved, and openly says when an old day's data was lost and rebuilt; browse the two trading days recovered from an earlier data problem; read a reordered "Today" page with a ten-second briefing, including three plain words for whether the market is improving or worsening, a "what changed since last time" list that quietly holds back unimportant tiny moves, and a plain-English daily summary with its numbers available on request; and reach the full original dashboard on a separate "Market" page.

_Last updated: 2026-09-01 after iteration 32._
