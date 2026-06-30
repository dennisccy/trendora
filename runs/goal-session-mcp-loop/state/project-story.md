# Project story so far

Trendora is a market-leadership ranking tool that gives quant-minded traders explainable, regime-aware scores for equities — Leadership, Entry Quality, and Risk — plus realized forward-return evidence. The current goal session is adding an evidence layer: every score will carry a visible "Proven" or "Not yet proven" status sourced from a rigorous out-of-sample statistical review, so users always know whether a signal has earned its confidence label.

## How it has grown

Trendora already delivered a full product in a prior session — explainable scores, market regime tracking, sector and theme leaderboards, a research lab, backtesting, and a watchlist. The underlying evidence plumbing was already in place: a statistical referee, an append-only certified-claims ledger, an MCP evidence window, and a post-decompose gate that blocks any unproven claim from shipping. What was missing was the user-facing surface — no badge on any score, no Evidence page, and no nav entry.

Iteration 1 fixed that and delivered the complete read-side evidence surface in one shot. Every stock score on the leaderboard and on individual stock pages now shows a small evidence-status chip right beside it — three chips per row, one each for Leadership, Entry Quality, and Risk. A new Evidence page went live at `/evidence`, reachable in one click from the sidebar. It honestly showed "No certified claims yet" at the time, because no claim had yet survived the referee.

Iteration 2 crossed the platform's first significant milestone: the Leadership score became the very first signal to earn a certified "Proven" label. The statistical referee ran a sealed out-of-sample test — 279 holdout dates never used in building the score, compared against the SPY benchmark with a multiple-testing correction — and issued a PASS (significance p ≈ 0.0005, edge +6.36%). That ruling is now written permanently to the ledger. The proof-panel feature was also built: on any stock's detail page, a "Why proven?" button below the Leadership score expands to show those exact numbers in plain, auditable terms, with a direct link to the Evidence ledger row and a link back to the rankings.

One hurdle remains from iteration 2: the automated browser-testing lane encountered a connectivity issue (the test browser could not reach the backend), so the "Proven" badge and proof panel were not photographed working end-to-end. The code is clean, the ledger entry is real, and the API serves the right data — but the visual confirmation is still outstanding and is the focus of the next iteration.

## What it can do today

The product ranks equities with explainable Leadership, Entry Quality, and Risk scores; tracks the current market regime; provides sector and theme leaderboards; offers backtesting and research labs; maintains a watchlist; shows a "Proven" or "Not yet proven" evidence status chip beside every score on the leaderboard and stock detail pages; hosts a dedicated Evidence ledger page reachable from the sidebar; and delivers a "Why proven?" expandable proof panel on the Leadership score card showing the out-of-sample test result, SPY control comparison, and certification date (code-complete and unit-tested; browser confirmation pending).

_Last updated: 2026-06-30 after iteration 2._
