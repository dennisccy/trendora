# Phase goal-i_can_see_the_wealthy_future_forever-iter-27 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-27
**Date:** 2026-06-09
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

No new user-facing capabilities were introduced in this iteration.

This iteration is explicitly **capture-only**: all four Data-Manager capabilities being targeted (J-37 missing-data diagnostic + gap-exact pull, J-38 Resume-an-unfinished-import, J-39 Remove-data confirm-preview, J-35 Expand-universe) were already built and committed in earlier iterations. The deliverable here is a verified test-harness wiring recipe documented in the dev handoff — not new product code.

---

## What Changed in the Visible UI

Nothing changed in the visible UI. `git diff --stat HEAD -- apps/ config.yaml` is empty — no frontend source (`apps/frontend/`) and no backend source (`apps/backend/`) was modified in this iteration.

The four capabilities exercised by this iteration are accessible on the existing `/data` (Data Manager) page as they were before this iteration:
- The Coverage panel and Missing-data diagnostic (J-37 surfaces)
- The Unfinished-imports panel with Resume / Retry / Remove-Dismiss actions (J-38 surfaces)
- The Remove-data form with confirm-preview (J-39 surface)
- The Import source picker and Expand-universe controls (J-35 surface)

---

## What Old Behavior Changed

None. No behavior change was introduced. The offline `seed` import source remains OFF by default (env-gated, not listed in the committed `config.yaml`). End users on the live production instance see no difference before and after this iteration.

---

## Not Visible Yet

The four Data-Manager capabilities listed below exist in the product code at HEAD (`77d0816`) and are accessible on the `/data` page under the right conditions, but their end-to-end browser flows have not yet been captured as "passing" journeys (the capture step is owned by the downstream browser-QA agent, not this iteration's developer step):

- **J-37:** Missing-data diagnostic showing no-history / thin / intra-series-gap categories with exact shortfalls, and the one-click gap-exact pull that clears the row.
- **J-38:** Resume-an-unfinished-import continuing from `next_chunk_index`, and the visible inline `resume-error` alert (row retained) when a needs-key Resume has no key provided.
- **J-39:** Remove-data confirm-preview enumerating removable user-added bars + protected committed-seed breakdown + dependent cascade; wholly-seed scope refusal with explicit reason.
- **J-35:** Expand-universe job using the `seed` source running to completion with passers + omitted-with-reason list + grown universe count.

These are not "not built" — the code exists at HEAD. They are "not yet captured end-to-end in the browser" because the test harness was previously wired to the live host where the fixture conditions (insufficient-member, resumable checkpoint, `seed` source) did not exist. The harness wiring recipe delivered in this iteration enables the browser-QA step to capture them.
