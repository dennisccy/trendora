# Project story so far

Trendora is a research tool for a stock-market investor, opening each evening with a short, honest briefing instead of a plain dashboard.

## How it has grown

Early rounds gave every stock a real sector label, built the evening briefing, locked each session into a tamper-evident record, and recovered 585 of 587 stocks lost in a recovery drill — until a deeper data problem forced the owner to switch the whole app off. A five-stage repair rebuilt the damaged data and re-verified it live; a testing-tool bug that had briefly touched the real protected data was found and fixed, and the app's memory footprint was checked and improved.

Iteration 26 proved the evening briefing's own promise: a saved briefing never changes, and its exported copy always matches what's on screen. Iteration 27 closed a related gap: if the data behind an old frozen briefing went missing, the page now says so honestly instead of quietly rebuilding it.

Iteration 28 rebuilt the home page. It is now called "Today" and reads top-to-bottom as a real ten-second briefing: market state, summary, what changed, leadership rotation, next-session focus, and the manifest strip. The whole old dashboard — every card it ever had, down to the remembered show/hide switches — moved intact to a new "Market" page, one click away from the sidebar. One new idea did not fully land yet: three small words meant to say whether the market is improving or getting worse showed "NA" everywhere, because they only get written into brand-new saved briefings and every saved briefing so far predated them.

Iteration 29 tested that idea for real. The team made one carefully chosen, permanently recorded request for a date the product had never looked at before — August 3rd, 2026 — and the three words appeared correctly: "improving", "improving", "little changed", agreeing with the plain-English sentence already on the page. Every one of the twenty-six older saved briefings was checked afterward and confirmed untouched. But the page most people actually land on — today's own latest briefing, from August 12th — still shows "NA" for those same three words, because nobody has told the product to add them to that specific saved briefing yet. So the idea works, proven on one date, and finishing it means doing the same kind of one-time update to today's own briefing next.

## What it can do today

The product lets users see each stock's honest, mostly-complete sector label; see why each next-session candidate was picked and why others weren't; trust that each evening's saved briefing exactly matches what's on screen and never changes once saved; see the app honestly report when an old briefing's underlying data has gone missing rather than quietly rebuilding it; browse the two recovered trading days with corrected numbers, backed by checked-live repair work; read a reordered "Today" page covering market state, summary, what changed, and next-session focus on one screen; reach the full former dashboard, unchanged, on a new "Market" page reached from the sidebar; and, on one specific date so far (August 3rd, 2026), read plain-English words describing whether the market was improving or getting worse that day. Those same words are not yet visible on today's own latest briefing.

_Last updated: 2026-09-01 after iteration 29._
