# Project story so far

Trendora is a market-leadership ranking tool that helps quant-minded traders see which of their scoring signals have genuinely earned their confidence labels — through rigorous out-of-sample statistical testing, not in-sample curve-fitting.

## How it has grown

Trendora already delivered a full product in a prior session: explainable Leadership, Entry Quality, and Risk scores for equities, a market-regime tracker, sector and theme leaderboards, backtesting tools, research labs, and a watchlist. Under the hood it also had a statistical referee engine, an append-only ledger for certified claims, and a post-decompose gate that blocks any unproven signal from being labeled as confident. What was missing was the user-facing surface — no badge on any score, no Evidence page, and no nav entry.

Iteration 1 built the entire evidence read-side in one shot. Every score on the leaderboard and stock detail pages gained a small "Proven" or "Not yet proven" chip right beside it. A dedicated Evidence page went live at `/evidence`, reachable from the sidebar in one click. It honestly showed no certified claims yet, because none had passed the referee.

Iteration 2 crossed the platform's first significant milestone: Leadership became the very first signal to earn a certified "Proven" label. The statistical referee ran a sealed out-of-sample test — 279 holdout dates never used in building the score, compared against the SPY benchmark with a multiple-testing correction — and issued a PASS (significance p ≈ 0.0005, edge +6.36%). That ruling was written permanently to the ledger. A "Why proven?" button also went live on every stock's Leadership card, expanding to show those exact numbers with a direct link to the Evidence ledger row. The code was complete and unit-tested, but the automated browser-test lane hit a connectivity issue and skipped every visual check.

Iteration 3 closed that gap. The start-up script for the browser tests was tightened to serve a pre-built site bundle instead of compiling pages on demand, eliminating the race condition that caused the previous skips. With both services running reliably, the full browser suite ran for the first time: 16 tests, 16 passes, zero skipped. The "Proven" badge, the proof panel with its PASS verdict and exact statistical figures, the Evidence ledger row, and all round-trip links were photographed in a real browser. Every number displayed in the UI matches the backend byte-for-byte. Four of the five required user journeys are now fully verified. The fifth — surfacing evidence tied to the current market regime — is next.

## What it can do today

The product lets users browse ranked equities with an evidence status on every score; tap "Why proven?" on any Leadership card to read the out-of-sample statistical proof (PASS, +6.36% edge, p ≈ 0.0005, 12,297 observations, vs SPY); confirm that Entry Quality and Risk are honestly labeled "Not yet proven" with no fabricated drill-down; and audit the full certified claim on the Evidence ledger page, following links back and forth to the stock rankings.

_Last updated: 2026-06-30 after iteration 3._
