# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and recovered 585 of 587 stocks lost in a recovery drill — until a deeper data problem forced the owner to switch the whole app off. The owner approved a five-stage repair: the team rebuilt the damaged trading days, filled in missing figures, cleared stale cached answers, and ran a full database check live — every check passed, and the safety lock came off.

Iteration 23 confirmed the repaired data displays correctly on screen, finishing the repair project — but an automated-testing mistake briefly pointed a second, unauthorized copy of the app at the real protected data, adding ten small harmless entries. The owner ruled to keep those entries and close the testing-tool hole; iteration 24 built that fix, and in the process caught that the round's own safety re-check of the three working features had silently not run at all.

Iteration 25 closed both loose ends: it re-checked the app's memory use (an honest miss, but noticeably improved), fixed the testing-tool bug for real, and the safety re-check genuinely ran and passed. A closer second check then caught two more subtle mistakes in that same round's own work before either could mislead anyone, and confirmed the real database, switched back on for ordinary use for the first time since the incident, behaved safely under thousands of requests.

Iteration 26 tackled the evening briefing's own promise: that a saved briefing never changes and its exported copy always matches what's shown. The team proved, checking it themselves rather than trusting the write-up, that a saved briefing file is an exact byte-for-byte copy of what the page displays, and that creating a corrected version of an old briefing leaves the original completely untouched. One real gap remains: if the data behind an old frozen briefing goes missing, the app quietly rebuilds it instead of telling the user honestly — flagged for careful, closely-reviewed work next round.

## What it can do today

The product lets users see each stock's honest, mostly filled-in sector label; see why each next-session candidate was picked and why the others weren't; browse the two recovered trading days, with corrected volume numbers, in the price history; trust that the data-repair work behind those numbers has been checked twice, live; and trust that each evening's saved briefing file exactly matches what's shown on screen and stays unchanged once frozen. The Today page's full day-to-day view and the Market page are still being built, and one honest gap remains in how the app reports a missing data run behind an old briefing.

_Last updated: 2026-08-28 after iteration 26._
