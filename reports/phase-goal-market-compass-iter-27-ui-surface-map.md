# Phase goal-market-compass-iter-27 — UI Surface Map

**Phase:** goal-market-compass-iter-27
**Date:** 2026-08-28
**Written by:** ui-impact-analyst

---

## File Classification

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/api/compass.py` | backend-api | indirect — confirmed consumed | `compass()` (`GET /api/compass`) reordered: checks for an existing manifest via `latest_manifest_for_date` BEFORE calling `resolved_run`/`run_scan`. The frontend already consumes this exact endpoint (`apps/frontend/lib/api.ts::fetchCompass`, called from `apps/frontend/app/page.tsx`), and its `basis` field is already rendered verbatim by `CompassManifestStrip`/`BasisLine`. No response schema change — only which `basis.status` values are reachable for a given input. |
| `apps/backend/app/engine/compass.py` | backend-internal | none | New pure-read helper `latest_manifest_for_date(session, as_of)` and a refactor of `get_or_create_manifest`'s existing inline query to call it. Same query shape, same return values, called from the same already-covered route. No independent UI surface — its only external effect is via the `compass.py` API route already listed above. |
| `apps/backend/tests/test_api_compass.py` | backend-internal (tests) | none | Test-only file. Flips one test's assertions to the fixed behavior and adds two new tests. No production code, no UI surface. |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/?asof=2025-04-15` | `CompassManifestStrip` → `BasisLine` badge (`compass-manifest-strip.tsx`, `data-testid="compass-manifest-basis"`) | Changed behavior (regression check — the common, already-working path) | The route reorder adds a new fast path ahead of the pre-existing slow path; this row proves the fast path is inert on the common case and the "available" state still renders correctly for an intact manifest+run pair | Navigate to `http://localhost:3255/?asof=2025-04-15`; wait for the Manifest card to populate; confirm the badge reads exactly "Basis: available" in the green/positive badge style, with no gray detail text beside it, and the nearby badges read "version 2" and "retrospective" |
| `/?asof=2026-08-12` | `CompassManifestStrip` → `BasisLine` badge | Changed behavior (regression check — an existing, unrelated "rebuilt" state) | Confirms the frontier manifest's `mode`/`version`/`manifest_hash` and its already-existing "rebuilt" basis state are unaffected by the reorder | Navigate to `http://localhost:3255/?asof=2026-08-12`; wait for the Manifest card to populate; confirm the badge reads exactly "Basis: rebuilt" in the amber/warn badge style, with the gray detail text "the source scanner run was recreated after this manifest was frozen" beside it, and nearby badges read "version 6" and "at ingest" |
| `/` (any historical `?asof=`) | `CompassManifestStrip` → "Regenerate manifest" button + `RegenerateConfirmModal` | Unaffected (regression check) | `POST /api/compass/regenerate` and its route handler are explicitly untouched this iteration; confirms the reorder in `GET /api/compass` did not disturb the sibling control | Navigate to `http://localhost:3255/?asof=2025-04-15`; click the outlined amber "Regenerate manifest" button (`data-testid="compass-manifest-regenerate-button"`); confirm a modal titled "Confirm manifest regenerate" opens (`data-testid="compass-manifest-regenerate-confirm-modal"`); click "Cancel" in the modal footer and confirm the modal closes with the badges unchanged |
| Not reachable via any live URL this iteration | `CompassManifestStrip` → `BasisLine` badge, `"unavailable"` variant (red/danger, label "Basis: unavailable") | New reachability (the actual fix; not a new component) | This is the core change — the badge state itself already existed (iter-11) but was structurally unreachable through the live route until this reorder. No as-of date in the current live database currently meets its trigger condition (frozen manifest + since-deleted backing run), and creating one is out of scope/forbidden this iteration | Not testable via the browser this iteration. Run `cd apps/backend && .venv/bin/python -m pytest tests/test_api_compass.py -v -k unavailable`; confirm `test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run` PASSES and its assertions include `basis["status"] == "unavailable"` and `healed is None` |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/compass.py::latest_manifest_for_date` — new pure-read helper consolidating an
  existing inline query; feeds only the already-listed `GET /api/compass` route — no independent UI
  surface.
- `apps/backend/app/engine/compass.py::get_or_create_manifest` — its existing-row check now calls the
  helper above instead of a duplicate inline query; same behavior, same callers, no UI surface of its own.
- `apps/backend/tests/test_api_compass.py` — test file only; no UI surface.

---

## Summary

- **Frontend surfaces changed:** 0 files touched; 1 surface (`CompassManifestStrip`'s Basis badge) gained
  a newly reachable display state with zero frontend code changes
- **New pages/routes:** 0
- **Modified components:** 0 (no `.tsx`/`.css` files changed — the badge's existing code path is simply
  reachable under new conditions)
- **Navigation changes:** no
- **Backend-only changes:** 2 (`compass.py` engine helper/refactor, `test_api_compass.py`)
