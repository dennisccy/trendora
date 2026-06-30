# Delivered — Trendora Decision-Quality Evidence Layer

**Session:** mcp-loop
**Date:** 2026-06-30
**Final verdict:** GOAL_ACHIEVED
**Iterations:** 7 (iter-0 through iter-6)

## What you can do today

Browse 120 ranked stocks, each showing a clear "Proven" or "Not yet proven" badge on every score — Leadership, Entry Quality, and Risk. On any stock with a "Proven" Leadership badge, expand the "Why proven?" panel to read exactly why: the out-of-sample test result (+6.36% holdout edge), the control comparison against the S&P 500, the sealed holdout sample size (12,297 observations), and the date the claim was registered. Entry Quality and Risk scores are honestly marked "Not yet proven" on every stock, so you never see a confident-looking number without backing. Open the Evidence page from the top navigation to browse all certified claims — each one shows its hypothesis, out-of-sample verdict, control comparison, and a round-trip link back to the surface whose badge it backs. On the Dashboard, check the current Market Regime (Risk-on 76.05) and follow the "See evidence proven in this regime" link to find the Breakout-watch setup's certified +6.12% out-of-sample edge, clearly labeled as holding specifically in the Risk-on regime.

## How it came together

The session opened with Trendora's analytical engine already running — Leadership, Entry Quality, and Risk scores on 120 stocks, a market-regime tracker, and a research lab — but with no evidence surface at all. Every score looked equally confident even though none had been statistically tested.

The first two iterations built the evidence layer from scratch. "Proven" and "Not yet proven" badges appeared inline on every score across the leaderboard and stock detail pages. A dedicated Evidence page went live in the navigation. Leadership became the first score to earn a "Proven" label after passing a sealed out-of-sample referee test: +6.36% holdout edge versus the S&P 500, with a p-value of 0.0005 and Bonferroni multiple-testing correction.

Iteration 3 fixed a browser connectivity issue that had blocked automated verification, then ran the first full canonical browser suite — confirming that every score carried a status badge, the "Why proven?" drill-down panel showed the correct numbers, unvalidated scores were honestly marked, and the Evidence ledger was fully auditable with working round-trip links. Four of the five journeys passed.

Iteration 4 completed the feature set. A second edge — the Breakout-watch setup's +6.12% out-of-sample advantage over the S&P 500 specifically in the Risk-on market regime — survived the referee and was certified. The Evidence page gained a regime-labeled row and the Dashboard gained a "See evidence proven in this regime" link. All five journeys were shown working in a live test, but a server port conflict blocked the automated screenshot lane, leaving the fifth journey's formal verification incomplete.

Iterations 5 and 6 repaired the verification machinery. A startup-script fix cleared the port conflict, but deeper pipeline defects were then uncovered: the automated system was quietly announcing success without producing its output reports, an unrecognized progress bookmark was aborting the run before the browser walkthrough could execute, and checks were being marked done without any artifacts on disk. All four root-cause defects were fixed in iteration 6. The full automated walkthrough ran end-to-end, the independent audit signed off, and the fifth journey passed the session-standard canonical lane for the first time.

## Watch it work

A full narrated walkthrough is embedded on the page that holds this document. Open it in your browser to see the product in action.
