# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and recovered 585 of 587 stocks lost in a recovery drill — until a deeper data problem forced the owner to switch the whole app off. A five-stage repair rebuilt the damaged data and re-verified it live; a testing-tool bug that had briefly touched the real protected data was found and fixed, and the app's memory footprint was checked and improved.

Iteration 26 proved the evening briefing's own promise: a saved briefing never changes, and its exported copy always matches what's on screen. One gap remained — if the data behind an old frozen briefing went missing, the app quietly rebuilt it instead of saying so. Iteration 27 closed that gap: the evening page now checks whether a saved briefing already exists before rebuilding anything, so a genuinely missing record is now reported honestly, proven by comparing the old buggy check against the fixed one on the same scenario. A separate independent check also caught and corrected a browser test that had, on its own, added one harmless extra entry to the protected data.

Iteration 28 rebuilt the home page itself. It is now called "Today" and reads top-to-bottom as a real ten-second briefing: market-state band, summary, what-changed, leadership rotation, next-session focus, and the manifest strip. The whole old dashboard — every card it ever had, down to the remembered show/hide switches — moved intact to a new "Market" page, one click away from the sidebar, and stepping back to an old date there still shows that date's own honest numbers. One new idea did not fully land yet: three small words meant to say whether the market is improving or getting worse show "NA" on every date the product can currently show, because they only get written into brand-new saved briefings and every saved briefing so far predates them. The team confirmed this live against the real data rather than guessing, and the next step is one new saved briefing that will make the real words appear on screen.

## What it can do today

The product lets users see each stock's honest, mostly-complete sector label; see why each next-session candidate was picked and why others weren't; browse the two recovered trading days with corrected numbers; trust that the incident-repair work behind those numbers has been checked live; trust that each evening's saved briefing exactly matches what's on screen and never changes once saved; see the app honestly report when an old briefing's underlying data has gone missing rather than quietly rebuilding it; read a reordered "Today" page covering market state, summary, what changed, and next-session focus on one screen; and reach the full former dashboard, unchanged, on a new "Market" page reached from the sidebar. The three new market-direction words on the Today page are not yet visible on any date the product can currently show.

_Last updated: 2026-08-31 after iteration 28._
