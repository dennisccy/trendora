# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and recovered 585 of 587 stocks lost in an early recovery drill. Later rounds fixed a hidden volume bug, then found a way the app itself could quietly overwrite still-broken days left over from that same incident — serious enough that the owner switched the whole app off pending a full repair.

The owner then approved a five-stage repair in writing. The team rebuilt the eleven damaged days, filled in their missing forward-looking figures, cleared out stale cached answers, and finally ran a full, twelve-part database check live against the real database — every check passed, and the safety lock covering the damaged days was switched off.

The owner then gave permission to switch the app back on. Iteration 23 built a safe, disposable practice copy of the database, turned the real app on against that copy for the first time in many weeks, and confirmed the repaired data — including the two recovered trading days and today's own numbers — genuinely displays correctly on screen. That finished the long data-repair project. But in the same round, a mistake in the automated testing tool briefly started a second, unauthorized copy of the app pointed at the real, protected data instead of the safe copy, and it quietly added ten small, harmless recalculated entries there. Nothing important was lost, but the team caught it, recorded it honestly, and paused for the owner to decide how to clean it up and prevent it happening again.

The owner ruled: keep the ten harmless entries as-is, and authorized exactly one fix — close the hole in the testing tool so it can never again start the app against the wrong copy of the data by mistake. Iteration 24 built that fix: the tool now decides, once, at the very start of each test run, which copy of the data to use, and refuses to start anything later that doesn't match, proven with a new safety test that fails on the old tool and passes on the fixed one. While checking this, the team also caught, on its own, that this round's routine safety re-check of the three already-working features had silently not run at all, due to a separate bug in how the tool reads its own instructions. Nothing broke as a result, but the safety net was missing, so the next round will run with more careful review switched on.

## What it can do today

The product lets users see each stock's honest, mostly filled-in sector label; see why each next-session candidate was picked and why others weren't; and browse the two trading days recovered from August's data incident, with corrected volume numbers, in the price history. The whole data-repair effort behind those numbers has now been proven, through a real supervised test, to serve correctly on screen. The Today page's full day-to-day view, the manifest-freezing pieces, and the Market page are still being built.

_Last updated: 2026-08-28 after iteration 24._
