# Phase goal-mcp-loop-iter-23 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-23
**Date:** 2026-07-08
**Written by:** ui-impact-analyst

---

## Summary

This is a **zero-application-diff, verification-only iteration.** `git diff HEAD` touches exactly one file in the entire repository — a QA replay-script fixture (`runs/goal-session-mcp-loop/journey-scripts/J-13.json`), not application source. This is confirmed independently three times: by the developer's handoff, by the reviewer's report (`reports/reviews/goal-mcp-loop-iter-23-review.md`, verdict `PASS_WITH_NOTES`), and by this analysis's own `git status` / `git diff HEAD` check against the working tree. Nothing changed for a user of the product in this iteration.

The iteration's entire purpose was to re-run the canonical `browser-qa-agent` / `ux-regression-reviewer` / `phase-closure` gates against the build that already contains iter-22's shipped feature (deep, vendor-labeled index/macro overlays on the Dashboard chart, plus the `/data` vendor-disclosure panel), because those formal reports-of-record had gone stale after a last-minute chart fix (`minBarSpacing: 0.02`) and were blocking phase closure (iter-22 ended in `CLOSURE-FAIL`).

---

## What Users Can Now Do

**None. No new user-facing capability shipped in this iteration.**

For reference — this is prior capability being re-verified, not something new as of iter-23 — the following was already live as of iter-22 and remains unchanged:
- On the Dashboard (`/`), in the "Regime × phase cross-view" chart card, users can already see deep 1996-onward `^SPX`/`^NDX`/`^DJI` equity-index lines plus `^VIX`/`^TNX` overlays, each labeled with its data vendor ("Stooq", "Yahoo", or "FRED-macro proxy") in the legend and hover tooltip.
- On `/data`, users can already see the "Index & benchmark data provenance" panel (`IndexVendorPanel`), a table listing every one of those series' vendor and true first-recorded date.

See `reports/phase-goal-mcp-loop-iter-22-user-visible-changes.md` for the original full write-up of these capabilities.

---

## What Changed in the Visible UI

**None.** `git diff HEAD` shows zero changes anywhere under `apps/frontend/` — the Dashboard chart and the `/data` page render identically to how they did at the end of iter-22 (same components, same CSS, same data-fetch logic). The only file this iteration touched is an internal test-automation fixture — `journey-scripts/J-13.json`'s expected-text assertion changed from `"587 symbols"` to `"590 symbols"` — which is read only by the project's own automated browser-replay tooling, not by anything a product user sees or interacts with.

---

## What Old Behavior Changed

**None.** No application behavior changed anywhere. This was a verification-only pass with zero backend or frontend source diffs — confirmed by the developer, independently re-confirmed by the reviewer, and independently re-confirmed a third time here via direct inspection of `git diff HEAD` / `git status`.

---

## Not Visible Yet

- **A pre-existing test gap was newly surfaced (not a shipped defect a user can encounter).** This iteration's re-run of `test_api_indexes.py` is the first time this expensive test fixture has ever run to completion in this repo's history (iter-22's audit flagged it as "expensive/deferred"). It surfaced a genuine, previously-unobserved failure: `test_api_indexes_full_param_serves_through_latest_and_echoes_asof` fails (`KeyError: '^TNX'`) when the `full=true` query parameter is combined with a historical `as_of` date older than `^TNX`'s first bar (2021-01-04). No page in the current UI issues that specific combination — the `/stocks/{ticker}` Full ↔ Recent toggle does not also pass a historical `as_of` — so this gap is not reachable through any user action today. It does not affect the Dashboard's default (no `as_of`, `full=false`) view: the two tests that directly cover that view, `test_api_indexes_includes_vendor_and_first_for_deep_series` and `test_api_indexes_equals_engine_and_includes_committed_dia`, both pass. The dev handoff recommends a narrowly-scoped follow-up fix in a future iteration, since correcting it touches `apps/backend/` (either the test's assertion or `app/engine/indexes.py`'s full-mode logic), which is out of scope for this verification-only pass.
