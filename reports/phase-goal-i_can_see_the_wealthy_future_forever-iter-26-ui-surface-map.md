# Phase goal-i_can_see_the_wealthy_future_forever-iter-26 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-26
**Date:** 2026-06-09
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `ResumeControl` — inline error `<span role="alert" data-testid="resume-error">` | Changed behavior | J-38 UT-11 fix: failed resume now shows a visible inline error instead of silently dropping the row | On a needs-key paused import, click Resume without entering a key; confirm a red inline message ("Enter the session key for … to resume.") appears next to the Resume button and the import row remains in the Unfinished Imports panel |
| `/data` | `ResumeControl` — row persistence after failed resume | Changed behavior | `onResumed` / overview reload now runs on SUCCESS only; a failed resume no longer triggers a list reload that could drop the row | On a needs-key paused import, click Resume without entering a key; confirm the row is still present in the Unfinished Imports panel after the error message appears (row does NOT disappear) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/data_manager.py` (`compute_provider_availability`, `_provider_entry_with_seed`, `seed_import_source_enabled`, `seed_import_overlay_dir`) — adds the env-gated `seed` entry to the API source catalog and the source-validator gate; OFF by default and absent from the committed `config.yaml`; the production UI source picker is unchanged when the env flag is unset.
- `apps/backend/app/data_providers/seed_provider.py` (`get_market_cap`) — adds optional `market_caps.csv` reading to `SeedProvider`; only consumed by the QA harness when the seed source is enabled; no production UI impact.
- `apps/backend/app/data_providers/__init__.py` (`make_provider`) — `seed` factory now honours `TRENDORA_SEED_IMPORT_DIR` overlay env dir; test/dev only; no production UI impact.
- `apps/backend/scripts/build_qa_fixture_db.py` (new) — throwaway QA fixture-DB + overlay builder; never run in production; no UI surface.
- `apps/backend/tests/test_data_manager.py` — test coverage only; no UI surface.
- `apps/backend/tests/test_api_data.py` — test coverage only; no UI surface.
- `apps/backend/tests/test_seed_provider.py` — test coverage only; no UI surface.
- `apps/backend/tests/test_provider_clients.py` — test coverage only; no UI surface.

---

## Summary

- **Frontend surfaces changed:** 1 (`/data` — `ResumeControl`)
- **New pages/routes:** 0
- **Modified components:** 1 (`ResumeControl` in `apps/frontend/app/data/page.tsx`)
- **Navigation changes:** no
- **Backend-only changes:** 8 files (all test/QA harness enablers or test files; zero production UI impact)
