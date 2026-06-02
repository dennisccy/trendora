# Phase goal-i_can_see_the_wealthy_future_forever-iter-13 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-13
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

<!-- New capabilities the user gains on the existing /research Factor Lab page. -->

- Users can now open the **Factor Lab** (`/research`), open the **Factor** dropdown, and pick any of **four** volatility measures — **ATR % (volatility level)**, **Historical volatility (HV)**, **Volatility contraction (VCP-style)**, and **Downside volatility (semivol)** — where previously only ATR % was available.
- Users can now read, for each of the three new volatility measures, its full evidence panel: the **decile table** (raw mean forward return **and** the downside-risk-adjusted column, each with sample size `n`), the **Spearman rank-IC** (with `n`), and the **by-regime effectiveness split** — so they can see *which* volatility measure and *which direction* actually sorted forward returns in this universe, rather than assuming the textbook relationship.
- Users can now see the volatility measures **grouped together under a "Volatility" heading** in the Factor dropdown (the dropdown is now organized into family sub-headings — Score, Momentum, Trend, Volatility, etc.), making the volatility family obvious at a glance.
- Users can still combine each new volatility factor with the existing **horizon** selector (e.g. 5d / 60d) and the existing **combination-cohort** and **by-regime** views — the new factors flow through every existing Factor-Lab control.

---

## What Changed in the Visible UI

<!-- Specific UI elements that changed. -->

- The **Factor** dropdown on `/research` now renders its options inside native `<optgroup>` sub-headings keyed off each factor's family (capitalised: "Score", "Momentum", "Trend", "Volatility", …). Previously the dropdown was a flat list of options.
- The **Volatility** group in that dropdown now lists **four** entries (ATR %, Historical volatility (HV), Volatility contraction (VCP-style), Downside volatility (semivol)); previously only ATR % was present.
- Selecting **Historical volatility (HV)**, **Volatility contraction (VCP-style)**, or **Downside volatility (semivol)** populates the existing decile table, rank-IC card, and regime-effectiveness table with that factor's data — these surfaces were already present but had no way to display these three measures before.
- The factor header line (factor label · family · direction) now correctly reports `volatility · lower better` for the three new measures.
- Low-sample deciles/regimes and the downside-undefined case continue to display honest **NA + `n`** (no fabricated 0) for the new factors — consistent with existing factors.

---

## What Old Behavior Changed

<!-- Existing features that work differently — regression-sensitive. -->

- **Factor dropdown layout:** the dropdown previously presented a flat option list; it now presents the same options grouped under family sub-headings. Option **values are unchanged**, so any existing selection/deep-link behavior is preserved — only the visual grouping is new.
- **Database was regenerated** this iteration so every immutable snapshot carries the three new stored volatility values. As a regression-sensitive consequence, every existing score-driven surface must be re-verified to be byte-identical: the `/stocks` leaderboard scores/buckets, the `/stocks/[ticker]` detail score breakdowns, the Risk-Off → Actionable=0 gate, regime labels, and candidate counts. The dev handoff reports these are unchanged (NVDA Leadership 47.48/E, Entry 66.24/D, Risk 33.79/E; both seeded Risk-Off runs show Actionable=0) — but this is the highest-priority re-verification for QA.

---

## Not Visible Yet

<!-- Backend capabilities deliberately not surfaced in the leaderboard/detail UI. -->

- The three new per-stock volatility values (`hv`, `vcp_contraction`, `downside_vol`) are stored on every snapshot row and ride the canonical `/api/stocks` and `/api/stocks/{ticker}` responses, but they are **intentionally NOT displayed** on the `/stocks` leaderboard or the `/stocks/[ticker]` score breakdowns. By design they are stored for read-only Factor-Lab consumption only (they enter no weighted score). The only place a user sees them is the `/research` Factor Lab decile/IC evidence.
