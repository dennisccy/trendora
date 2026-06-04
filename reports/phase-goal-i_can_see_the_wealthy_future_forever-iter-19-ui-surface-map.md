# Phase goal-i_can_see_the_wealthy_future_forever-iter-19 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-19
**Date:** 2026-06-04
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research` | `AnalysisModeToggle` (`data-testid="analysis-mode-toggle"`, buttons `analysis-mode-all` / `analysis-mode-asof`) | New component | J-32 adds an All-history ⟷ As-of-date analysis mode | Load `/research`; confirm the toggle shows **All history** active by default; click **As of date** and confirm `aria-pressed` moves to the As-of segment |
| `/research` | `ModeContext` (`data-testid="analysis-mode-context"`) | New component | Explains the active mode and shows the resolved as-of cutoff | In All-history mode confirm the label reads "Pooling every snapshot — all history"; switch to As-of mode and confirm it names the resolved cutoff date (or states As-of equals all history at the latest date) |
| `/research` | Factor Lab (page-level decile / rank-IC figures) | Changed behavior | Factor-Lab fetch effect now keys on the resolved `asofCutoff` | In As-of mode, set the global top-bar `<select>` to an early date; confirm the decile/rank-IC figures change and `n` drops; confirm low-sample cells show **NA + n**, not a fabricated number |
| `/research` | `CombinationLab` (multi-factor combination cohort) | Changed behavior | Gains `asofCutoff` prop; refetches on cutoff change | In As-of mode at an early date, confirm the combination-cohort figures re-point and `n` decreases; click back to **All history** and confirm full-sample figures (larger `n`) return |
| `/research` | `EventStudyLab` (Setup & Pattern event study) | Changed behavior | Gains `asofCutoff` prop; per-horizon + by-regime/by-sector slices re-scope | In As-of mode at an early date, confirm the event-study horizon rows and regime/sector slices reflect the smaller point-in-time window; toggle back to All history and confirm full sample returns |
| `/research` | Global top-bar as-of `<select>` (existing, in `<header>`) | Changed behavior (consumer) | Research now consumes the single global as-of value in As-of mode only | **J-18 check:** confirm there is exactly one date `<select>` on the page and it is a descendant of `<header>`, not `<main>`; in **All-history mode**, move the global date and confirm Research figures are unchanged with **no** research network refetch; in **As-of mode** confirm the research fetch carries `?as_of=` |

> Note: the global as-of `<select>` is a React-controlled select — per MEMORY `react-controlled-select-needs-native-setter`, drive it with the native-setter + bubbling change event. The new mode toggle is a plain button group — click it directly.

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` — keyword-only `as_of` threaded into `compute_factor_lab` / `compute_factor_combination` / `compute_event_study` and their three observation builders; single `ScannerRun.asof_date <= as_of` membership filter; `asof_date` echo. Surfaced indirectly via the toggle — no standalone UI surface beyond what the labs already render.
- `apps/backend/app/api/research.py` — optional `as_of` query param on the three routes, validated via the shared `resolved_date` resolver (422 unparseable / 400 future-or-before-history); docstrings updated. Consumed by the frontend fetchers; no separate UI surface.
- `apps/backend/tests/test_research.py`, `apps/backend/tests/test_api_research.py` — test-only changes (new as-of engine/endpoint tests; the three `*_no_date_control_present` contract tests intentionally updated). No UI impact.

---

## Summary

- **Frontend surfaces changed:** 1 route (`/research`) with 2 new components + 3 re-pointing labs + 1 existing-consumer behavior change
- **New pages/routes:** 0
- **Modified components:** 5 (`AnalysisModeToggle` new, `ModeContext` new, Factor Lab effect, `CombinationLab`, `EventStudyLab`)
- **Navigation changes:** no
- **Backend-only changes:** 4 files (2 source: `engine/research.py`, `api/research.py`; 2 test)
