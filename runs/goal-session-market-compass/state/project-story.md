# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and recovered 585 of 587 stocks lost in an early recovery drill. Later rounds fixed a hidden volume bug, then found a way the app itself could quietly overwrite still-broken days left over from that same incident — serious enough that the owner switched the whole app off pending a full repair.

The owner then approved a five-stage repair in writing, and the team worked through it one fully-checked stage at a time. Iteration 19 rebuilt all eleven damaged days through the ordinary scanning engine and proved the rebuild faithful three separate ways. Iteration 20 filled in the missing forward-looking figures for those same eleven days. Iteration 21 cleared out outdated "cached answers" from five internal stores and caught a new risk: one ordinary page visit after restart could quietly undo the cleanup. Iteration 22 ran the fifth and final stage — a full, twelve-part database check — live against the real database, and every check passed; the safety lock covering the eleven damaged days was switched off, since the database-level repair was now certified complete. What still hadn't happened was watching the repaired data actually appear correctly on screen, the one thing the plan called this stage's real job — and that needed the app running again, a decision only the owner could make.

The owner gave that permission in writing. Iteration 23 built a safe, disposable practice copy of the whole database, switched the real app on against that copy for the first time in many weeks, and confirmed the repaired data — including the two recovered trading days and today's own numbers — genuinely displays correctly on screen. That finishes the long data-repair project. But while a routine re-check of two older, already-working features ran in the same round, a mistake in the automated test tooling briefly started a second, unauthorized copy of the app pointed at the real, protected data instead of the safe copy, and it quietly added ten small, harmless recalculated entries there. Nothing important was lost or changed — every entry is correct and easily recomputable — but the team caught the mix-up itself, on its own initiative, recorded it honestly, and stopped all further work to let the owner decide how to clean it up and how to stop it from happening again.

## What it can do today

The product lets users see each stock's honest, mostly filled-in sector label; see why each next-session candidate was picked and why others weren't; and browse the two trading days recovered from August's data incident, with corrected volume numbers, in the price history. As of this round, the whole data-repair effort behind those numbers has been proven — through a real, supervised test — to serve correctly on screen, not just sit correctly in the database. The Today page's full day-to-day view, the manifest-freezing pieces, and the Market page are still being built; work on them resumes once the owner has weighed in on this round's data-protection mix-up.

_Last updated: 2026-08-27 after iteration 23._
