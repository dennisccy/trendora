# Project story so far

Trendora is a market-leadership ranking tool that shows traders which of their scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample statistical testing, not in-sample curve-fitting.

## How it has grown

Trendora began this session with its analytical machinery already in place — Leadership, Entry Quality, and Risk scores; a market-regime tracker; sector leaderboards; a research lab; a watchlist — but with no user-facing evidence surface. Iterations 1 and 2 built that surface from scratch: "Proven" and "Not yet proven" chips appeared on every score across the leaderboard and stock detail pages, a dedicated Evidence ledger page went live, and Leadership became the first signal to earn a certified label after a sealed out-of-sample test (holdout edge +6.36% vs SPY, p ≈ 0.0005).

Iterations 3 through 8 steadily closed the remaining gaps. By iteration 6, all five original journeys ran through the canonical automated walkthrough end-to-end. A second certified edge arrived with the Breakout-watch setup's Risk-on regime (+6.12%). Iteration 8 added a sixth journey: the volatility-contraction pattern earned a "Proven" badge on the Research Factor Lab at the 20-day horizon (+3.33%), with a dedicated Evidence ledger row linking back to its full audit trail.

Iterations 9 and 10 were a two-part setup for a wider search. Iteration 9 introduced an internal practice ledger running a LORD++ economy that earns back testing capacity whenever it finds a real edge — keeping the canonical multiple-testing bar strict while making exploration feasible. Iteration 10 put that practice ledger to work: a small pre-approved list of factor/horizon ideas was tested through the full referee. Three of four passed the strict out-of-sample bar, with the volatility-contraction pattern at the 60-day horizon standing out as the most credible result (+8.91% holdout edge). These verdicts stayed internal — nothing on any user-facing screen changed — ready for promotion in iteration 11.

Iteration 11 promoted that winner. The vcp_contraction 60-day edge was certified into the canonical ledger as the fifth entry, and the Research Factor Lab evolved from a single evidence chip per factor into an honest per-horizon strip: five pills showing each factor's proven/unproven status at 1, 5, 10, 20, and 60 trading days. The 60-day "Proven" chip deep-links directly to its auditable evidence entry. Every uncertified horizon reads "Not yet proven." Browser QA confirmed all 15 test cases passing with DOM-level assertions against a live stack.

## What it can do today

The product lets users browse the stock leaderboard and see "Proven" or "Not yet proven" on every score; expand the proof panel on any Leadership card to read the sealed out-of-sample evidence (+6.36% vs SPY); confirm Entry Quality and Risk are honestly labeled "Not yet proven"; follow the Breakout-watch setup's certified edge in strong-market conditions; browse the Evidence page with all five certified claims and round-trip links to each research surface; and see the volatility-contraction pattern marked "Proven" in the Research Factor Lab at both the 20-day and 60-day horizons, while all shorter horizons and most other factors honestly read "Not yet proven."

_Last updated: 2026-07-01 after iteration 11._
