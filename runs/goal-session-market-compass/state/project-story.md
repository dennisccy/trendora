# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and recovered 585 of 587 stocks lost in a recovery drill — until a deeper data problem forced the owner to switch the whole app off. A five-stage repair rebuilt the damaged data and re-verified it live; every check passed and the safety lock came off.

Iteration 23 confirmed the repaired data displays correctly — but an automated-testing mistake briefly pointed an unauthorized copy of the app at the real protected data, adding ten harmless entries the owner ruled to keep. Iteration 24 closed that testing-tool hole and caught that the round's own safety re-check had silently not run. Iteration 25 closed both loose ends: it re-checked memory use (an honest miss, but improved), fixed the testing-tool bug for real, confirmed the safety re-check genuinely ran, and confirmed the real database — back on for the first time since the incident — behaved safely under real traffic.

Iteration 26 tackled the evening briefing's own promise: that a saved briefing never changes and its exported copy always matches what's shown. The team proved, checking it themselves, that a saved file is byte-for-byte identical to what the page displays, and that correcting an old briefing leaves the original untouched. One gap remained: if the data behind an old frozen briefing went missing, the app quietly rebuilt it instead of saying so.

Iteration 27 closed that gap. The evening page now checks whether a saved briefing already exists before doing any rebuilding, so if the data behind an old briefing has genuinely gone missing, the app now says so honestly instead of quietly patching over it — proven by comparing the old, buggy version of the check against the fixed one on the same scenario. A separate independent check also caught that a browser test had, on its own, permanently added one harmless extra entry to the protected data; it was recorded and corrected, with no real harm done. The next targets are the Today page's full day-to-day view and rebuilding the Market page.

## What it can do today

The product lets users see each stock's honest, mostly-complete sector label; see why each next-session candidate was picked and why others weren't; browse the two recovered trading days with corrected numbers; trust that the repair work behind those numbers has been checked live; trust that each evening's saved briefing exactly matches what's on screen and never changes once saved; and see the app honestly report when an old briefing's underlying data has gone missing, instead of quietly rebuilding it. The full Today page and the Market page are still being built.

_Last updated: 2026-08-28 after iteration 27._
