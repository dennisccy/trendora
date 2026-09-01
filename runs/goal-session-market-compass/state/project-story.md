# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and survived a recovery drill and a data-repair incident. Iteration 28 rebuilt the home page into a "Today" page that reads top-to-bottom as a real ten-second briefing, moving the old dashboard intact to a new "Market" page. Iterations 29-31 added the three improving/worsening words, a "what changed since last time" list, and a plain-English daily summary — closing ten of the project's eleven originally planned capabilities.

That left one open item: keeping the program's memory use under the computer's limit. Iteration 32 found it still too high at first glance, though most of that turned out to be a brief startup spike. Iteration 33 fixed how the backend loads price history, and the measurement finally fit comfortably under the limit. Iteration 34 settled the last open questions — a second, independent measurement agreed closely with the first, and the full team of checks genuinely ran end to end this time — and the project was declared finished, pending the owner's confirmation of the memory figure.

Then the goal grew. On 1 September, two new capabilities were added to the plan: making the "picked or skipped" labels on next-session candidates honest, and making the "leadership rotation" panel actually useful. Iteration 35 tackled the first, and uncovered a bug that had been hiding for over thirty rounds — 37 of 539 stocks were wrongly marked "below the selection floor" even though their scores actually cleared it (the worst case scored well above the bar). The fix makes the leadership score the sole gate for candidacy; other checks now add an honest caution note instead of silently disqualifying a stock. The old, wrong records were left untouched exactly as the project's rules require, with a corrected version published alongside them. The second new capability — showing which way sectors and themes are rotating without just repeating the "what changed" list — has not been built yet; testing showed it currently duplicates that list and drops a couple of sector groups without saying so. That is the next round's target.

## What it can do today

The product lets users see each stock's honest sector label; see why each next-session candidate was picked, skipped, or flagged with a caution — now fully and correctly labeled; trust that each evening's saved briefing never changes once saved, and see an honest note when old data was lost and rebuilt; browse the two trading days recovered from an earlier data problem; read a reordered "Today" page with a ten-second briefing, plain improving/worsening words, a "what changed" list, and a plain-English summary; and reach the full dashboard on a separate "Market" page. It runs reliably within the computer's memory limits.

_Last updated: 2026-09-01 after iteration 35._
