# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and recovered 585 of 587 stocks lost in an early recovery drill. Later rounds fixed a hidden volume bug, then found a way the app itself could quietly overwrite still-broken days left over from that same incident — serious enough that the owner switched the whole app off pending a full repair.

The owner then approved a five-stage repair in writing, and the team worked through it one fully-checked stage at a time. Iteration 19 rebuilt all eleven damaged days through the ordinary scanning engine and proved the rebuild faithful three separate ways. Iteration 20 filled in the missing forward-looking figures for those same eleven days, and disproved a claim in the original plan that some undamaged days also had gaps. Iteration 21 cleared out outdated "cached answers" from five internal stores, kept two other caches after proving them still safe, and caught a new risk: one ordinary page visit after restart could quietly undo the cleanup.

Iteration 22 ran the fifth and final stage — a full, twelve-part database check — live against the real database, and every check passed. The team closed the page-visit risk found the step before, and the check itself caught one more stale leftover: a cached "who's tracked today" record for one day held an outdated answer, so it was discarded to be recalculated correctly next time. A bug in the check itself — one of its twelve tests could never actually fail — was caught and fixed the same day, with the fix proven safe against the work already done. The safety lock covering the eleven damaged days was then switched off, since the database-level repair is now certified complete. What still hasn't happened is watching the repaired data actually appear correctly on screen, the one thing the plan calls this stage's real job — that needs the app running, which is now the owner's decision alone.

Nothing else in the database has moved, and every step has been independently double-checked against live data before being trusted. The Today page and the Market page are still known to be broken and are waiting for the app to come back online before anyone can work on them.

## What it can do today

The product lets users see each stock's honest, mostly filled-in sector label; see why each next-session candidate was picked and why others weren't; and browse the two trading days recovered from August's data incident, with corrected volume numbers, in the price history. The main decision screens — Today, Market and Compass — stay switched off until the final repair stage's on-screen check is done and the owner allows the app to run again.

_Last updated: 2026-08-27 after iteration 22._
