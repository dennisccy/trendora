# goal-mcp-loop-iter-4 — Implementation Summary

**Phase:** goal-mcp-loop-iter-4
**Date:** 2026-06-30
**Written by:** developer

---

## Features Implemented

- **Regime-labeled evidence on the Evidence page**: The certified "Breakout-watch setup" claim now
  appears on the Evidence ledger with a clear **"Regime: Risk-on"** tag, so the reader can see this edge
  was proven specifically in the current market regime — not in general.
- **An honest title for the setup claim**: That same row used to read a confusing **"Unmapped signal"**
  and falsely point at the Stocks leaderboard. It now reads **"Breakout-watch setup"** with the plain-
  language note **"Out-of-sample edge in the Risk-on regime"**, and its "Backs:" link points to the
  **Research event-study lab** where this kind of evidence comes from.
- **A shortcut from the Dashboard to the evidence**: The Dashboard's Market Regime panel gains a
  **"See evidence proven in this regime →"** link that jumps straight to the Evidence page, so a reader
  who notices today's regime can immediately see what has been proven to work in it.

---

## Changed Behavior

- **Evidence page — the setup (non-score) claim row**: Previously showed "Unmapped signal" and a
  misleading "Backs: Stocks leaderboard →" link. Now shows a meaningful title ("Breakout-watch setup"),
  an honest one-line framing, a "Regime: Risk-on" tag, and a correct "Backs: Research event-study lab →"
  link.
- **Evidence page — the Leadership (score) claim row**: **Unchanged.** It still reads "leadership_score",
  "PASS", "+6.36%", and "Backs: Stocks leaderboard →", with no regime tag. This was verified in a real
  browser so the existing journeys do not regress.
- **Dashboard — Market Regime panel**: The regime number and label (Risk-on, 76.05) are unchanged; only
  the new "See evidence proven in this regime →" link was added.

---

## Backend-Only Items

- None. There is **no backend code change** this iteration. The certified evidence (including its regime
  tag) was already produced by the referee/gate and is already served by the existing evidence API; this
  iteration only displays it. A new backend **test** was added to lock in that the regime claim does not
  accidentally change which signals count as "Proven".

---

## Incomplete Items

- None. Every item in the iteration spec is implemented:
  - the Evidence Claim was certified by the gate (the regime edge is "PASS" in the ledger);
  - the regime label, the honest title/link, and the Dashboard shortcut are all built and browser-verified;
  - the required-still-passing journeys (Leadership still "Proven"; Entry Quality + Risk still "Not yet
    proven"; the Leadership proof drill-down and ledger linkback) were confirmed unchanged.

---

## Config and Environment Changes

- None. No new environment variables, no config files, no database migrations. The work is display-only
  and reads the same evidence the platform already computes.

---

## Known Limitations

- **Evidence is regime-conditioned, by design.** The "Breakout-watch setup" edge is labeled as proven
  **in the Risk-on regime** specifically — it is not a claim that it works in every regime, and it is
  framed as historical out-of-sample evidence, never as a "buy now" signal.
- **Only one regime edge is proven so far.** This iteration certifies and shows a single regime-scoped
  edge (Breakout-watch in Risk-on). The other scores (Entry Quality, Risk) honestly remain "Not yet
  proven"; broader or additional regime claims are future work.
- **The regime claim row sits below the Leadership row** on the Evidence page (below the fold on a short
  window) — a reader (or an automated screenshot) must scroll down to see it.
- **Frontend unit tests need a TypeScript-aware runner.** In this environment the bundled Node cannot run
  the `.ts` test files directly; they were run by compiling them first (all pass). This is a tooling note
  only and does not affect the running app.
