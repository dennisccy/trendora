# Delivered — Decision-Quality Improvement Loop

**Session:** mcp-loop
**Date:** 2026-06-30
**Final verdict:** GOAL_ACHIEVED
**Iterations:** 7

## What you can do today

Browse a ranked list of 120 stocks and see a "Proven" or "Not yet proven" badge beside every Leadership, Entry Quality, and Risk score on every row — no score is ever shown without a clear evidence status.

Tap "Why proven?" on any stock's Leadership card to read the full out-of-sample proof that earned that label: the statistical test result, a +6.36% edge measured across 12,297 real observations, a comparison against the S&P 500 as a control, and the date the claim was certified and sealed.

Confirm for yourself that Entry Quality and Risk are honestly marked "Not yet proven" on every stock with no drill-down panel and no fabricated confidence numbers — the product only claims certainty where it has earned it.

Open the Evidence page from the sidebar to audit every certified claim in one place. Each entry shows the hypothesis, the out-of-sample verdict, the benchmark comparison, and the registration date, with round-trip links back to the surfaces they power and forward to the research lab.

On the Dashboard, follow the Market Regime card's "See evidence proven in this regime" link to the Evidence page. There you can read the Breakout-watch setup's certified +6.12% out-of-sample edge over the S&P 500, clearly labeled as applying specifically in the current Risk-on market environment.

## How it came together

The project opened with Trendora already ranking 120 stocks with three independent scores and a real-time market-regime tracker, but with no evidence surface — no badges, no Evidence page, no links, and no proof behind any displayed number. Every score looked equally confident even though none had been through a rigorous test.

The first wave of work built the read-side evidence layer from the ground up. "Not yet proven" chips appeared inline on every score across the leaderboard and every stock detail page, giving traders an honest picture against an empty ledger. A dedicated Evidence page went live in the sidebar. Then the Leadership score was put through a sealed out-of-sample referee test — 12,297 observations, +6.36% edge over the S&P 500, p-value 0.0005, Bonferroni-corrected — and passed. The ledger was stamped, Leadership's badge flipped to "Proven," and a "Why proven?" drill-down panel was wired up to show the exact numbers behind that label.

A browser connectivity issue in the test harness briefly delayed visual confirmation. Once fixed, the automated browser suite ran cleanly and verified four of the five journeys: every score had a status badge, the proof panel showed correct numbers matching the ledger, Entry Quality and Risk were honestly labeled, and the Evidence page was fully auditable with working round-trip links.

The fourth milestone brought the second certified edge. The Breakout-watch event-study pattern was found to hold a +6.12% advantage over the S&P 500 specifically in the Risk-on market regime — surviving a sealed holdout of 107 independent dates with p ≈ 0.0005. The Evidence page gained a clearly labeled "Regime: Risk-on" row and the Dashboard gained a direct link to it. A leftover server process blocked the automated screenshot lane, leaving the final journey's formal verification pending.

The last two iterations were a disciplined harness repair. A startup-script port-conflict fix was shipped first. Then four deeper pipeline defects were uncovered and corrected: one step was announcing success without producing its output report, an unrecognized progress bookmark was aborting the entire run before the browser walkthrough could execute, and checks were being marked complete without any artifacts on disk. With all four root causes fixed, the full automated walkthrough ran end-to-end for the first time in three rounds, the independent audit signed off, and the final journey passed the session-standard canonical lane. Every success criterion was met.

## Watch it work

A full narrated walkthrough is embedded on the page that holds this document.
Open it in your browser to see the product in action.
