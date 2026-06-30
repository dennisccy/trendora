# Project story so far

Trendora is a market-leadership ranking tool that helps quant-minded traders see which of their scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample statistical testing, not in-sample curve-fitting.

## How it has grown

Trendora began this session with its analytical machinery already in place (Leadership, Entry Quality, and Risk scores; a market-regime tracker; sector and theme leaderboards; research labs; a watchlist) but without any user-facing evidence surface — no badges on scores, no Evidence page, and no links connecting them. The opening baseline run confirmed the machinery was intact but produced no browser evidence.

Iterations 1 through 3 built and verified the core evidence surface. "Proven" / "Not yet proven" chips appeared on every score across the leaderboard and stock detail pages, a dedicated Evidence ledger page went live, and Leadership became the first signal to earn a certified label after a sealed out-of-sample test (279 holdout dates, +6.36% edge vs SPY, p ≈ 0.0005) — with a "Why proven?" drill-down panel on each Leadership card. A browser connectivity issue in iteration 2 caused screenshots to skip; iteration 3 fixed it with the full 16-test browser suite passing for the first time, closing four of the five required journeys.

Iteration 4 delivered the fifth and final journey feature. The referee certified a second edge — the Breakout-watch setup holds +6.12% out-of-sample advantage over the S&P 500 specifically in the current Risk-on regime (107 sealed holdout dates, p ≈ 0.0005). The Evidence page gained a clearly labeled regime-conditioned row and the Dashboard gained a "See evidence proven in this regime →" link. A live QA session confirmed all five journeys working in a real browser, but the automated screenshot lane hit a port-conflict (a stale server held the frontend port), leaving the formal picture record incomplete.

Iteration 5 fixed that port-conflict by adding a port-clearing step to the startup script — the fix is correct and the error-case test confirmed it works. However, a different harness bug surfaced: an internal pipeline handoff between the UI-impact report writer and the UI-test designer has a path/timing mismatch that caused the screenshot stage to abort before the port fix could even be exercised. The sign-off audit was missed for the third consecutive time as a knock-on effect. The product itself is unchanged — all five features remain in place and correct.

## What it can do today

The product lets users browse ranked equities with an evidence status on every score; expand a "Why proven?" panel on any Leadership card to read the out-of-sample proof; confirm that Entry Quality and Risk are honestly labeled "Not yet proven" with no fabricated confidence numbers; audit all certified claims on the Evidence ledger page with round-trip links to stock rankings; and navigate from the Dashboard's Market Regime card to the Evidence page to see the Breakout-watch setup's certified regime-conditioned edge (+6.12% vs SPY in the Risk-on regime), clearly labeled with the regime it holds in.

_Last updated: 2026-06-30 after iteration 5._
