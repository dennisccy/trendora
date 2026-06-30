# Phase goal-mcp-loop-iter-3 — UI Surface Map

**Phase:** goal-mcp-loop-iter-3
**Date:** 2026-06-30
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

No UI surfaces were modified this iteration. No file under `apps/frontend/**` was changed. The table below is intentionally empty.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| — | — | — | No frontend source files were changed | — |

---

## Backend-Only Changes (No UI Impact)

- `scripts/start-frontend.sh` — QA bring-up script switched from `next dev` to `next start` (pre-built production bundle). Fixes the automated browser-test lane start-up flakiness that caused all 18 UI tests to be skipped in iter-2. This is an operational/config change: it only affects how the site is launched for automated QA; it does not change any page, component, route, navigation, or runtime behavior visible to users. No UI surface affected.

---

## Surfaces Verified This Iteration (unchanged, browser-proven)

These surfaces were not modified but were browser-tested with fresh screenshots to confirm correct rendering. Included here as a reference for QA operators who need to re-verify.

| Route / Page | Component / Element | Verification Status | What Was Confirmed | Specific Test Action |
|-------------|--------------------|--------------------|-------------------|---------------------|
| `/stocks` | Leaderboard row — Leadership column | Verified | "Proven" chip (green) present on all ~120 rows | Navigate to `/stocks` with no `?as_of=` parameter; wait for rows to populate; confirm the Leadership column shows a green "Proven" chip on at least the first 5 visible rows |
| `/stocks` | Leaderboard row — Entry Quality column | Verified | "Not yet proven" chip (muted) present on all ~120 rows | On the `/stocks` leaderboard, confirm the Entry Quality column shows a muted grey "Not yet proven" chip; confirm no "Why proven?" toggle appears when that chip is clicked |
| `/stocks` | Leaderboard row — Risk column | Verified | "Not yet proven" chip (muted) present on all ~120 rows | On the `/stocks` leaderboard, confirm the Risk column shows a muted grey "Not yet proven" chip; confirm no "Why proven?" toggle appears when that chip is clicked |
| `/stocks` | Health badge | Verified | Reads "Ready" when backend is healthy | On the `/stocks` page with both services running, confirm the health badge reads "Ready" and does not show "Checking backend…" or "Backend unavailable" |
| `/stocks/{ticker}` | Leadership score card — "Why proven?" toggle | Verified | Expands proof panel with OOS result byte-identical to `/api/evidence` | Navigate to `/stocks/MU`; click the "Why proven?" toggle on the Leadership card; confirm the panel shows: PASS, +6.36%, p ≈ 0.0005, n = 12,297, vs SPY, claim id `leadership_score`, registered 2026-06-30 |
| `/stocks/{ticker}` | Leadership score card — "View backing evidence row →" link | Verified | Link navigates to `/evidence#signal-leadership_score` | On `/stocks/MU` with the "Why proven?" panel expanded, click "View backing evidence row →"; confirm the browser navigates to `/evidence` and scrolls to the `leadership_score` row |
| `/stocks/{ticker}` | Entry Quality score card | Verified | No "Why proven?" toggle present | Navigate to `/stocks/MU`; confirm the Entry Quality card has no "Why proven?" toggle or drill-down |
| `/stocks/{ticker}` | Risk score card | Verified | No "Why proven?" toggle present | Navigate to `/stocks/MU`; confirm the Risk card has no "Why proven?" toggle or drill-down |
| `/evidence` | leadership_score claim row | Verified | Row rendered with all five fields byte-identical to `/api/evidence` | Navigate to `/evidence`; confirm the `leadership_score` row is present and displays: hypothesis text, PASS OOS verdict, +6.36% edge, SPY benchmark control, and registration date 2026-06-30 |
| `/evidence` | "Backs: Stocks leaderboard →" linkback | Verified | Link navigates back to `/stocks` | On `/evidence`, click the "Backs: Stocks leaderboard →" link on the `leadership_score` row; confirm the browser navigates to `/stocks` |

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only / operational changes:** 1 (`scripts/start-frontend.sh` — QA bring-up script only)
