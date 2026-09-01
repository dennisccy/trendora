# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, survived a recovery drill and a deeper data-repair incident, and got the app's memory use checked and partly trimmed.

Iteration 28 rebuilt the home page into a "Today" page reading top-to-bottom as a real ten-second briefing, moving the old dashboard intact to a new "Market" page. Iterations 29-31 finished the three improving/worsening words, the "what changed since last time" list, and the plain-English daily summary — closing ten of the project's eleven planned capabilities and leaving only the check that the program doesn't use too much of the computer's memory.

Iteration 32 measured that memory use again properly — a clean start, every reading saved to a file that survives — and it was still too high, about 2.97 GB against a 2.5 GB goal. But looking closer showed almost all of that was a five-second startup spike, not what the program holds once it's actually running (a much smaller ~710 MB). Fixing that spike was already on the owner's own written to-do list.

Iteration 33 did exactly that fix. The backend now loads price history differently when it starts up, and the new measurement fits: about 2.4 GB at peak, 18% lower than the round before and under the 2.5 GB line for the first time — the last of the eleven planned capabilities to close. Every other capability was re-checked and still works exactly as before, and careful cross-checks proved no number a user sees moved at all. The team is holding off on calling the whole project finished, though: this closing round was supposed to get a second, independent check and didn't, nobody said so out loud, and the project's own automatic safety check still refuses to certify the round until a bookkeeping mismatch is fixed. One more careful round — or one line from the owner accepting today's number — will settle it.

## What it can do today

The product lets users see each stock's honest sector label; see why each next-session candidate was picked or skipped; trust that each evening's saved briefing matches the screen exactly and never changes once saved, and openly says when an old day's data was lost and rebuilt; browse the two trading days recovered from an earlier data problem; read a reordered "Today" page with a ten-second briefing, including three plain words for whether the market is improving or worsening, a "what changed since last time" list, and a plain-English daily summary; and reach the full original dashboard on a separate "Market" page. Behind the scenes, it now also runs comfortably within the computer's memory limits for the first time this project.

_Last updated: 2026-09-01 after iteration 33._
