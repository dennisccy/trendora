# Project story so far

Trendora is a market-leadership ranking tool that helps traders see which of their scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample statistical testing, not in-sample curve-fitting.

## How it has grown

Trendora began this session with its analytical machinery already in place (Leadership, Entry Quality, and Risk scores; a market-regime tracker; sector leaderboards; a research lab; a watchlist) but without any user-facing evidence surface. Iterations 1 and 2 built the read-side evidence path: "Proven" / "Not yet proven" chips appeared on every score across the leaderboard and stock detail pages, a dedicated Evidence ledger page went live, and Leadership became the first signal to earn a certified label after a sealed out-of-sample test (holdout edge +6.36% vs SPY, p ≈ 0.0005). Iteration 3 ran the first full canonical browser suite, closing most required journeys. Iteration 4 certified a second edge — the Breakout-watch setup's +6.12% out-of-sample advantage in the Risk-on regime — but a port conflict blocked the automated screenshot lane, leaving one journey unverified.

Iterations 5 and 6 resolved the pipeline issues. With four harness defects repaired, the automated walkthrough ran end-to-end for the first time, the independent audit signed off, and all five original journeys were confirmed green. Iteration 7 was a pure verification pass — confirming everything still worked unchanged — before the improvement loop proposed extending the goal with a sixth journey: certifying a plain research factor's top-decile edge on the factor lab.

Iteration 8 closed that extension. The vcp_contraction factor's top-decile cohort was put through the referee gate (the fourth trial under a tightened Bonferroni bar) and earned a PASS — holdout edge +3.33%, p = 0.01149. The Research factor lab gained a dedicated "Evidence" column: vcp_contraction reads "Proven" — the first plain research factor, not a score, to earn this label — and links straight to its auditable entry on the Evidence page. Every other factor, including ma_stack whose edge was tested and rejected, honestly reads "Not yet proven." The Evidence page now lists four certified claims. All six journeys are green and the goal is achieved.

## What it can do today

The product lets users browse 120 ranked stocks each showing a proven or not-yet-proven label on every score; expand a "Why proven?" panel on any Leadership card to read the sealed out-of-sample proof (holdout edge, benchmark comparison, certification date); confirm that Entry Quality and Risk are honestly labeled "Not yet proven"; view all four certified claims on the Evidence page with round-trip links to the stocks leaderboard, the research lab, or the event-study lab; follow the Market Regime card to the Evidence page to see the Breakout-watch setup's certified edge in the Risk-on regime; and on the Research factor lab, see which factors have a certified top-decile edge — vcp_contraction showing "Proven" and linking to its full auditable record, all others (including the rejected ma_stack) honestly labeled "Not yet proven."

_Last updated: 2026-06-30 after iteration 8 — GOAL_ACHIEVED._
