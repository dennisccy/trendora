# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and survived a recovery drill and a data-repair incident. Iteration 28 rebuilt the home page into a "Today" page that reads like a real ten-second briefing, moving the old dashboard to a new "Market" page. Iterations 29-34 added trend words, a "what changed since last time" list, a plain-English daily summary, and cut the program's memory use well under the computer's limit — the project was declared finished once, pending owner confirmation.

The goal grew again on 1 September, adding honest "picked or skipped" reasons for each candidate and a leadership-rotation panel. Iteration 35 fixed a hidden bug wrongly failing 37 stocks that actually cleared the selection bar. Iteration 36 built the rotation panel but wasn't declared finished — its one proof picture came out blank and review ran lighter than planned. Iteration 37 fixed both problems and the project was declared finished a second time.

The goal grew once more the same day: tell each skipped candidate its true reason for missing out, and make sure the "what changed" list never silently drops a stock move it already checked. Iteration 38 built the first part correctly, but the same change broke the evening briefing for almost every older saved evening — 21 of 23 saved days started showing an error, breaking six things that used to work. Iteration 39 repaired it, double-checking every claim against the saved records itself; all six broken things came back, older evenings now say honestly when a count isn't recorded instead of crashing, and the team found and logged one small leftover honesty problem on its own.

Iteration 40 finished the last piece: the "what changed" list now accounts for every stock move it checks, not just the ten biggest shown on screen. It now says plainly "Showing the top 10 stock moves" and separately how many more moves cleared the bar but were held back (4, on the day checked) — the "Suppressed moves" count grew from 36 to 79 because it now honestly includes the small stock moves it used to skip. The team recounted every number itself from the saved market data before trusting the screen. All fifteen promised features now work, and the project is being called finished for a third time — with two small housekeeping items (an undeclared test-script edit, and a lighter-than-planned check this round) flagged for the owner, and a short follow-up session recommended to record a few more proof videos of features that already work.

## What it can do today

The product lets a user open the evening briefing for any date across 30 years without it crashing, see each stock's honest sector label, and see the true reason each candidate was picked or skipped. It shows a plain-English daily summary and a complete "what changed since yesterday" list — now covering every stock move, not just the biggest ones — a leadership-rotation panel of gaining and losing sectors and themes, the full history on the Market page, and the two trading days recovered from an earlier data problem. A saved evening's briefing never quietly changes.

_Last updated: 2026-09-02 after iteration 40._
