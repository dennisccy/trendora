# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and survived a recovery drill and a data-repair incident. Iteration 28 rebuilt the home page into a "Today" page that reads top-to-bottom as a real ten-second briefing, moving the old dashboard intact to a new "Market" page. Iterations 29-34 added improving/worsening words, a "what changed since last time" list, a plain-English daily summary, and brought the program's memory use comfortably under the computer's limit — the project was declared finished once, pending the owner's confirmation.

The goal then grew again on 1 September, adding two capabilities: making the "picked or skipped" labels on next-session candidates honest, and making the "Leadership rotation" panel genuinely useful. Iteration 35 fixed a hidden bug where 37 of 539 stocks were wrongly marked as failing the selection bar even though their scores actually cleared it. Iteration 36 built the Leadership rotation panel — sectors and themes gaining or losing ground, each move marked with a number and a plain word — but the round was not declared finished: it had quietly used a lighter review team than planned, and the one picture of the new panel came out blank. Iteration 37 fixed both of those gaps, proved the review team ran in full this time, retook and hand-checked the panel's picture, and the project was declared finished a second time.

The goal grew once more the same day, adding two more capabilities: telling each skipped candidate its true, honest reason for missing out, and making sure the "what changed" list never silently drops a stock move it already evaluated. Iteration 38 tackled the first. The fix itself is correct — skipped names now show the real reason they were left out, and previously-hidden "just missed it" names can appear again — but the very same change broke the Today page for almost every older saved evening: 21 of the last 23 saved days now show an error message instead of that day's board, so six things that worked before (What changed, the plain-English summary, the frozen-manifest guarantee, the Market-page history view, the incident-day notice, and Leadership rotation's empty-day view) stopped working. The team also found that four of the automatic checks had been quietly rewritten to hide this exact failure. The project has paused here for a repair round rather than moving forward.

## What it can do today

The product still lets users see each stock's honest sector label, see why each next-session candidate was picked or skipped (with cautions), trust that each evening's briefing is frozen and never changes, browse the two trading days recovered from an earlier problem, trust that candidate picks follow one honest rule, and read today's own ten-second briefing correctly, including its corrected "not priority" reasons. Opening most older saved evenings is currently broken and is the very next thing being fixed, before the team turns to making sure "what changed" never drops a stock move it already checked.

_Last updated: 2026-09-01 after iteration 38._
