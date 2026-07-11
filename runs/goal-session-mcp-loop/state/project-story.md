# Project story so far

Trendora is a market-leadership ranking tool that shows traders which scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample testing, not in-sample curve-fitting.

## How it has grown

The first eighteen iterations built Trendora's trust layer — honest "Proven"/"Not yet proven" badges, an auditable evidence ledger, and six certified trading edges — then, when the team deepened the price history to thirty years across several hundred companies, every old certified edge honestly recomputed to failing (the system working as designed). Iterations 20-23 widened price-refresh to the whole company list, confirmed the Data Manager's coverage calendar live, and added three decades of index history, a volatility gauge, and a rate indicator to the dashboard chart, each labeled by source.

Iteration 24 sped up the app behind the scenes, but a new memory setting collided with the connection pool, so opening the Data Manager page right after a restart could crash the whole backend; the team fixed it the same day but paused for a live re-check rather than ship unproven. Iteration 25 closed that gap: two independent cold restarts confirmed the page now loads safely and quickly, and every other page that needed re-checking came back clean.

Iteration 26 set out to make the background data-refresh jobs themselves faster, and the speed-up genuinely worked, cutting job time by roughly 80% with no change to any number shown on screen. But testing the full company-wide refresh reproduced a serious memory crash that took the whole backend down and did not recover on its own. Because this is exactly the kind of failure Trendora is built never to allow, the team treated it as a step backward: that round was rolled back for human review, and a dedicated round to harden the backend's memory handling was queued next.

Iteration 27 delivered that fix. A first attempt (reading smaller windows of price history instead of the whole history at once) helped but wasn't enough on its own — a second consecutive company-wide refresh still crashed the app in testing. A follow-up fix capped how much memory the app's internal machinery could fragment across jobs and added a cleanup step after every refresh job finishes. The team then watched the heaviest job in the app — refreshing every score for every company across three decades — complete successfully three times in a row, with no crash and comfortable memory headroom to spare. Every other page was re-checked live and came back clean.

## What it can do today

The product lets users browse a leaderboard of hundreds of companies with an honest "proven" or "not yet proven" status on every score, open a fully auditable evidence ledger for every trading idea tested (currently all honestly "FAIL" while the deeper history is re-examined), and view up to thirty years of price history for any stock in a recent or full view. It shows a dashboard chart spanning three decades of major-index history plus a volatility gauge and a rate-spread indicator, each labeled by source, and a Data Manager page with a color-coded availability calendar across the whole company list — and the full-universe data refresh, the heaviest job in the app, now completes reliably without crashing the backend.

_Last updated: 2026-07-12 after iteration 27._
