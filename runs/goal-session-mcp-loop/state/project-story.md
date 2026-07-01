# Project story so far

Trendora is a market-leadership ranking tool that shows traders which of their scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample statistical testing, not in-sample curve-fitting.

## How it has grown

Trendora began this session with its analytical machinery already in place — Leadership, Entry Quality, and Risk scores; a market-regime tracker; sector leaderboards; a research lab; a watchlist — but with no user-facing evidence surface. Iterations 1 and 2 built that surface from scratch: "Proven" / "Not yet proven" chips appeared on every score across the leaderboard and stock detail pages, a dedicated Evidence ledger page went live, and Leadership became the first signal to earn a certified label after a sealed out-of-sample test (holdout edge +6.36% vs SPY, p ≈ 0.0005).

Iterations 3 through 6 closed the remaining gaps and repaired four pipeline defects, so all five original journeys ran through the canonical automated walkthrough end-to-end for the first time. A second edge was certified in the Breakout-watch setup's Risk-on regime (+6.12%). Iteration 7 was a pure re-verification pass. Iteration 8 delivered a sixth journey: the Research factor lab's vcp_contraction pattern earned a "Proven" badge (holdout +3.33%, p = 0.01149), adding a dedicated Evidence ledger row linking back to its full audit trail.

With four certified claims in the ledger, every future trial permanently tightens the Bonferroni multiple-testing bar — so a wide multi-horizon search could eventually fail to certify anything. Iteration 9 solved that problem before opening the wider search by introducing an internal "practice ledger" running a LORD++ online-FDR economy: it earns back testing capacity whenever it finds a real edge, so exploration stays feasible without touching the canonical bar at all. Nothing visible to users changed.

Iteration 10 put that practice ledger to work. A fixed, pre-approved list of four factor/horizon ideas was tested through the full referee — a narrow, reasoned set rather than a full cross-product, to prevent data-mining. Three of the four passed the strict out-of-sample bar (p < 0.010): volatility-contraction at 60 days, relative strength vs SPY at 60 days, and the already-proven Leadership score at 60 days. One honestly failed (volatility-contraction at 10 days). The testing budget visibly loosened as discoveries landed, exactly as the LORD++ economy was designed to do. Again, nothing on any user-facing screen changed — the four candidate verdicts sit in an internal staging file ready for the next iteration to act on.

## What it can do today

The product lets users browse 120 ranked stocks each showing a "Proven" or "Not yet proven" badge on every score; expand a "Why proven?" panel on any Leadership card to read the sealed out-of-sample proof (holdout edge, benchmark comparison, certification date); confirm that Entry Quality and Risk are honestly labeled "Not yet proven"; follow the Market Regime card to see the Breakout-watch setup's certified edge in Risk-on conditions; browse the Evidence page with all four certified claims and round-trip links to the leaderboard, research lab, and event-study lab; and see vcp_contraction labeled "Proven" in the Research factor lab with a link to its full auditable record.

_Last updated: 2026-07-01 after iteration 10._
