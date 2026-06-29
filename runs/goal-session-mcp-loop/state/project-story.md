# Project story so far

Trendora is a market-leadership ranking tool that gives quant-minded traders explainable, regime-aware scores for equities — Leadership, Entry Quality, and Risk — plus realized forward-return evidence. The current goal session is adding an evidence layer: every score will carry a visible "Proven" or "Not yet proven" status sourced from a rigorous out-of-sample statistical review, so users always know whether a signal has earned its confidence label.

## How it has grown

Trendora already delivered a full product in a prior session — explainable scores, market regime tracking, sector and theme leaderboards, a research lab, backtesting, and a watchlist. The underlying evidence plumbing was already in place too: a statistical referee, an append-only certified-claims ledger, an MCP evidence window, and a post-decompose gate that blocks any unproven claim from shipping. What was missing was the user-facing surface — no badge on any score, no Evidence page, and no nav entry.

Iteration 0 was a baseline check that tried to confirm the existing state via browser testing, but the browser-testing lane did not run, leaving all five target journeys unverified.

Iteration 1 fixed that and delivered the complete read-side evidence surface in one shot. The browser testing lane ran successfully this time, capturing real screenshots across four distinct flows. Every stock score on the leaderboard and on individual stock pages now shows a small "Not yet proven" chip right beside it — three chips per row, one each for Leadership, Entry Quality, and Risk. A new Evidence page is live at `/evidence`, reachable in one click from the left sidebar. It honestly says "No certified claims yet" today, and clearly shows what each future certified claim will look like: its hypothesis, out-of-sample verdict, control comparison versus SPY, registration date, and forward-walk score to date. No score is dressed up as proven — everything reads "Not yet proven" because no claim has survived the statistical referee yet, and the system is wired to keep it that way by default.

Two of the five target journeys are now confirmed passing: every score showing a visible evidence status, and unproven signals being honestly marked. The Evidence page and its navigation entry are verified, counting as a partial pass for the ledger-audit journey. The remaining two journeys — drilling into the proof behind a score, and viewing regime-conditioned evidence — need the first referee-certified statistical claim before they can proceed.

## What it can do today

The product ranks equities with explainable Leadership, Entry Quality, and Risk scores; tracks the current market regime; provides sector and theme leaderboards; offers backtesting and research labs; maintains a watchlist; and now shows a "Not yet proven" evidence status chip beside every score on both the leaderboard and stock detail pages, with a dedicated Evidence ledger page reachable from the sidebar in one click.

_Last updated: 2026-06-29 after iteration 1._
