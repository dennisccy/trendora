# Phase goal-mcp-loop-iter-32 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-32 (goal mode, journey J-17 / backlog B-903, + J-19 close-out)
**Date:** 2026-07-14
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see how much of the platform's statistical-credibility budget has already been spent, before any new scan is proposed, by navigating to `/research` and clicking the new "Certification-budget accounting" card, or by going directly to `/research/budget`.
- Users can now see the total number of canonical trials run to date (currently 7) and what trial number the next one will be (currently #8).
- Users can now see the exact significance bar the next canonical trial must clear — `required_p` — shown both as a number (currently 0.00625) and as its formula (`= 0.05 ÷ 8 (Bonferroni)`), so the growth of the multiple-testing divisor is visible, not just its end result.
- Users can now see how much of the Thresholdout alpha budget remains (currently 0.9 of 1 total, with 0.1 already spent) before proposing a new scan.
- Users can now see the internal staging (LORD++) exploration economy's next-trial significance level (currently ≈0.0003926) and which trial number it applies to (#8) — an economy that was never surfaced anywhere in the product before this iteration.
- Users can now see a compact trend line (a small sparkline) on each of the four figures above, showing how that number has moved trial by trial — re-read verbatim from the recorded ledger history, not a fresh computation.

---

## What Changed in the Visible UI

- A new page, `/research/budget`, was added: a page heading ("Certification-budget accounting" + a one-line description), and a four-card grid (Total trials to date / Current canonical required p / Thresholdout budget remaining / Staging LORD++ next-trial level), each card showing a headline number, an explanatory subtext line, and a small inline-SVG trend sparkline. A "Back to Research" link sits at the top, matching the Graveyard and Registry pages' pattern.
- The `/research` hub's existing "Governance & process" grid now shows a third card, "Certification-budget accounting" (Wallet icon), beside the existing "Pre-registration registry" and "Negative-results graveyard" cards — the grid (already sized for three) is now full.
- On `/research/budget`, a loading state shows four pulsing placeholder cards before the real numbers arrive; if the backend is unreachable, a single red-bordered "Backend unavailable" card appears in place of the grid, with the "Back to Research" link still usable — never a blank or crashed page.
- If the underlying ledgers were ever empty (not the case today — both currently hold 7 trials), the same four cards would still render with honest zero/starting values (0 trials, `required_p = 0.05`, full budget, initial staging wealth) rather than an error or blank state.

---

## What Old Behavior Changed

- None. This is a purely additive read-only page — no existing page's data, layout, or behavior changed. The dev and frontend handoffs both confirm `/research/graveyard`, `/research/registry`, `/evidence`, and `/stocks` return the same HTTP 200 / same data as before, and neither handoff touched any of those files.

**Note on J-19 (registry lineage-scroll) — not a change this iteration.** The phase's Definition of Done also calls for flipping journey J-19 (clicking a graveyard row's "Lineage" link scrolls the matching registry row into view) from `partial` to `passing`. No code changed to accomplish this: the fix (`apps/frontend/app/research/registry/page.tsx:50-59`, added in iter-31) is confirmed present and untouched — `git log` shows no commit against `registry/page.tsx` or `graveyard/page.tsx` since iter-30/31, and neither file appears in this iteration's changed-file list. The user-visible behavior itself is identical to what iter-31 already shipped; what's outstanding is only a fresh canonical browser-qa verification pass against the current build, not a UI change.

---

## Not Visible Yet

- None. This iteration's one new backend capability — `GET /api/research/budget`, backed by the new `app.engine.budget_accounting` module — has a complete, matching UI consumer: `/research/budget` is confirmed to be its only consumer (grepped across the frontend) and renders all four figures plus their spend-over-time series. Nothing computed by the new backend module is left unexposed.
