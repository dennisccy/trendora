# Project story so far

Trendora is a market-leadership ranking tool that shows traders which scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample testing, not in-sample curve-fitting.

## How it has grown

The first eighteen iterations built Trendora's trust layer — honest "Proven"/"Not yet proven" badges, an auditable evidence ledger, and six certified trading edges — then, when the team deepened the price history to thirty years across several hundred companies, every old certified edge honestly recomputed to failing (the system working as designed), and an early crash from that change was fixed the next round. Iterations 20-21 widened price-refresh to the whole company list and confirmed the Data Manager's coverage calendar live.

Iteration 22 added three decades of index history, a volatility gauge, and a rate indicator to the dashboard chart, each labeled by source, though a display bug hid the deep history until iteration 23 signed it off with a clean, live-verified fix.

Iteration 24 sped up the app behind the scenes but a new memory setting collided with the connection pool, so opening the Data Manager page right after a restart could crash the whole backend; the team fixed it the same day but paused for a live re-check rather than ship unproven.

Iteration 25 closed that gap: two independent cold restarts confirmed the Data Manager page now loads safely and quickly, and every other page that needed re-checking came back clean, so the app's speed checks held with the crash risk gone.

Iteration 26 set out to make the background data-refresh jobs themselves faster, and the speed-up genuinely worked, cutting job time by roughly 80% with no change to any number shown on screen. But testing the full company-wide refresh reproduced a serious memory crash that took the whole backend down and did not recover on its own — a pre-existing weak spot the speed-up could not be shown to have avoided making worse. Because this is exactly the kind of failure Trendora is built never to allow, the team treated it as a step backward rather than progress: this round is rolled back for human review, the one piece of the problem this round's own changes had added was removed, and a dedicated round to harden the backend's memory handling is next in line before the faster data jobs can be signed off.

## What it can do today

The product lets users browse a leaderboard of hundreds of companies with an honest "proven" or "not yet proven" status on every score, open a fully auditable evidence ledger for every trading idea tested (currently all honestly "FAIL" while the deeper history is re-examined), and view up to thirty years of price history for any stock in a recent or full view. It shows a dashboard chart spanning three decades of major-index history plus a volatility gauge and a rate-spread indicator, each labeled by source, and a Data Manager page with a color-coded availability calendar across the whole company list — reliable in day-to-day use, though a full company-wide data refresh can still crash the backend, a risk the team is now working to close before calling the speed-up finished.

_Last updated: 2026-07-10 after iteration 26._
