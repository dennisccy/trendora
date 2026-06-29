# Project story so far

Trendora is a market-leadership ranking tool that gives quant-minded traders explainable, regime-aware scores for equities — Leadership, Entry Quality, and Risk — plus realized forward-return evidence. The current goal session is adding an **evidence layer**: every score and ranking will carry a visible "Proven" or "Not yet proven" status sourced from a rigorous out-of-sample statistical review, so users always know whether a signal has earned its confidence label.

## How it has grown

Trendora already delivered a complete product — explainable scores, market regime tracking, sector and theme leaderboards, a research lab, backtesting, and a watchlist. That prior session brought all of it to production quality and was declared complete.

This new goal session opened with a baseline check. Before building anything, the team mapped exactly what the evidence layer needs versus what already exists. The underlying plumbing — a statistical referee, an append-only certified-claims ledger, an MCP evidence window, and a post-decompose gate that blocks any unproven claim from shipping — is already in the codebase and ready to use. What is missing is the user-facing surface: no badge on any score, no Evidence page, no nav entry, and no API endpoint to deliver evidence status to the browser.

The browser check that was meant to confirm the baseline empirically did not run in this first iteration, so all five target journeys are recorded as "not yet verified." The next iteration steps up to a full build: it will wire an evidence API to the ledger, add "Not yet proven" badges to every stock score, and create the Evidence page and nav entry — so users begin seeing honest status labels instead of naked numbers.

## What it can do today

The product ranks equities with explainable Leadership, Entry Quality, and Risk scores; tracks the current market regime and phase; provides sector and theme leaderboards; offers backtesting and research labs; and maintains a watchlist. The evidence layer is not yet live — scores do not yet show "Proven / Not yet proven" status.

_Last updated: 2026-06-29 after iteration 0._
