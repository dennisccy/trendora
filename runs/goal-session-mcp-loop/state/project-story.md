# Project story so far

Trendora is a market-leadership ranking tool that helps quant-minded traders see which of their scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample statistical testing, not in-sample curve-fitting.

## How it has grown

Trendora began this session with all its analytical machinery intact from a prior build (Leadership, Entry Quality, and Risk scores; a market-regime tracker; sector and theme leaderboards; research labs; a watchlist) but without any user-facing evidence surface: no badges on scores, no Evidence page, and no links connecting them.

Iteration 1 built the entire evidence read-side in one shot: "Proven" / "Not yet proven" chips appeared on every score across the leaderboard and stock detail pages, a dedicated `/evidence` ledger page went live, and the sidebar gained an Evidence entry — though the ledger showed nothing yet because no claims had cleared the referee.

Iteration 2 crossed the platform's first milestone: Leadership became the first signal to earn a certified "Proven" label after a sealed out-of-sample test (279 holdout dates, +6.36% edge vs SPY, p ≈ 0.0005, with multiple-testing correction). A "Why proven?" drill-down panel opened on every stock's Leadership card. A browser-lane connectivity issue caused all screenshots to skip that round, leaving the visual record incomplete.

Iteration 3 fixed that gap by switching the front-end start script from an on-demand compiler to a pre-built bundle, eliminating the race condition. The full browser suite ran cleanly for the first time: 16 tests, 16 passes. Four of the five required user journeys were formally photographed and closed.

Iteration 4 delivered the fifth and final journey. The platform's referee certified a second edge — the Breakout-watch setup holds an out-of-sample +6.12% advantage over the S&P 500 specifically in the current Risk-on market regime (107 sealed holdout dates, p ≈ 0.0005). The Evidence page now shows this claim with a clear "Regime: Risk-on" label, an honest subtitle ("Out-of-sample edge in the Risk-on regime"), and the exact statistical proof verbatim from the ledger. The Dashboard's Market Regime card gained a "See evidence proven in this regime →" link that navigates there in one click. A live QA session confirmed all five journeys working in a real browser; however the canonical automated-screenshot lane hit the same port-conflict pattern as iteration 2 (a stale server process held the frontend port), so the formal screenshot record is pending one more clean run.

## What it can do today

The product lets users browse ranked equities with an evidence status on every score; tap "Why proven?" on any Leadership card to read the out-of-sample proof (+6.36% edge, p ≈ 0.0005, vs SPY); confirm that Entry Quality and Risk are honestly labeled "Not yet proven" with no fabricated drill-down; audit all certified claims on the Evidence ledger page with round-trip links to stock rankings; and navigate from the Dashboard's Market Regime card directly to the Evidence page to see the Breakout-watch setup's certified regime-conditioned edge (+6.12% vs SPY in the Risk-on regime), clearly labeled with the regime it holds in.

_Last updated: 2026-06-30 after iteration 4._
