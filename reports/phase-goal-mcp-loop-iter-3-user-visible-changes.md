# Phase goal-mcp-loop-iter-3 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-3
**Date:** 2026-06-30
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

No new user-facing capabilities were added this iteration. This was a **verification-only** iteration: the only code change was to the automated QA start script (`scripts/start-frontend.sh`), which is not part of the deployed product.

The evidence layer features below already existed in the product from earlier iterations. This iteration proved — with a real browser and real screenshots — that they render correctly with backend-matching numbers:

- Users can view a green **"Proven"** badge on the Leadership score column for every row on the Stocks leaderboard at `/stocks`.
- Users can view a muted **"Not yet proven"** badge on the Entry Quality and Risk score columns on `/stocks`.
- Users can open any stock detail page and click **"Why proven?"** on the Leadership card to read the out-of-sample PASS result, holdout edge (+6.36%), p-value (~0.0005), cohort size (n = 12,297), SPY benchmark control, certified claim id, and registration date.
- Users can navigate to `/evidence` to see the `leadership_score` certified claim row with hypothesis, OOS PASS verdict, SPY control, +6.36% edge, and registration date, and use the **"Backs: Stocks leaderboard →"** link to return to `/stocks`.

These capabilities were verified byte-identical to `GET /api/evidence` output.

---

## What Changed in the Visible UI

**Nothing changed in the visible UI.** No file under `apps/frontend/**` was modified. The pages, components, navigation, forms, and layouts are identical to the prior iteration.

---

## What Old Behavior Changed

None. No existing user-facing behavior changed.

The only behavioral change is operational: the automated QA test lane now starts the site from a pre-built production bundle (`next start`) instead of a development server (`next dev`). This change is invisible to end users — the developer hot-reload workflow (`scripts/dev.sh`) is unchanged, and no runtime UI behavior differs.

---

## Not Visible Yet

- **J-04 (regime-conditioned evidence):** No regime-scoped certified claim exists yet. The regime-conditioned "Proven" badge and its proof drill-down are not yet available on any stock detail page or evidence row. This is the remaining journey before the overall goal can be declared achieved.
