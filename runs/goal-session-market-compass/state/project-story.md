# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and survived a recovery drill and a data-repair incident. Iteration 28 rebuilt the home page into a "Today" page that reads top-to-bottom as a real ten-second briefing, moving the old dashboard intact to a new "Market" page. Iterations 29-34 added the three improving/worsening words, a "what changed since last time" list, a plain-English daily summary, and finally brought the program's memory use comfortably under the computer's limit — the project was declared finished once, pending the owner's confirmation.

Then the goal grew again on 1 September, with two new capabilities added to the plan: making the "picked or skipped" labels on next-session candidates honest, and making the "Leadership rotation" panel genuinely useful. Iteration 35 tackled the first and uncovered a bug that had been hiding for over thirty rounds — 37 of 539 stocks were wrongly marked "below the selection floor" even though their scores actually cleared it. The fix makes the leadership score the sole gate for candidacy; other checks now add an honest caution note instead of silently disqualifying a stock.

Iteration 36 tackled the second capability, building the "Leadership rotation" panel: sectors and themes gaining ground on one side, losing ground on the other, each move marked with a plus or minus number and a plain word, with every count adding up correctly for the first time. But that round was not declared finished, for two reasons unrelated to whether the feature worked: it was supposed to use the full review team and quietly used a lighter one instead without anyone flagging it, and the one picture meant to show the new panel came out completely blank.

Iteration 37 closed both of those gaps and did nothing else. The full review team genuinely ran this time, proven in the system's own logs rather than taken on trust. The picture of the Leadership rotation panel was retaken and checked by hand — it is no longer blank, and it shows exactly the two-sided, both-directions view the panel was built to show, with the counts still adding up for every sector and theme. An internal safety check inside the candidate-picking code was also hardened so it can never be silently switched off, and a test that looked like it was checking something but wasn't now genuinely does. With every one of the thirteen planned capabilities re-checked and passing, and both outstanding process gaps closed, the project has now been declared finished a second time — this time with nothing left to build.

## What it can do today

The product lets users see each stock's honest sector label; see why each next-session candidate was picked, skipped, or flagged with a caution — fully and correctly labeled; trust that each evening's saved briefing never changes once saved, and see an honest note when old data was lost and rebuilt; browse the two trading days recovered from an earlier data problem; read a reordered "Today" page with a ten-second briefing, plain improving/worsening words, a "what changed" list, and a plain-English summary; see which sectors and themes are gaining or losing leadership this session, in both directions, with a plain word for each move; and reach the full dashboard on a separate "Market" page. It runs reliably within the computer's memory limits.

_Last updated: 2026-09-01 after iteration 37._
