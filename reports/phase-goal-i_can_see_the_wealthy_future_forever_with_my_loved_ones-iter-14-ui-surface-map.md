# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14
**Date:** 2026-06-13
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|---------------------|------------|-------------|--------------|
| `/research` | `EventStudyViewToggle` (segmented button group) | New component | J-63: adds Episodes vs Pooled view selection to the event study | Click the "Pooled" button — confirm the active pill moves to Pooled and the n figure in the disclosure line rises to the signal-day count; click "Episodes" — confirm the pill returns and n drops back to the episode count |
| `/research` | `EventStudyDisclosure` line (`data-testid="event-study-disclosure"`) | New component | J-63: discloses n / unique symbols / episode count in both modes | With Episodes mode active, confirm all three values (n, Unique symbols, Episodes) appear in the disclosure line; confirm the Episode term in the label shows a TermInfo tooltip when clicked |
| `/research` | Per-horizon, by-regime, by-sector `N=` chip links | Changed behavior | J-63: chips now carry the active `view` in their samples href and label reads "episodes" or "occurrences" | With Episodes active, hover/right-click a horizon N= chip and verify the href contains `view=episodes`; switch to Pooled and verify the same chip href contains `view=pooled` and the label reads "occurrences" |
| `/research` | `EventStudyLab` card — event-study figures (hit-rate, expectancy, MAE/MFE, by-regime, by-sector) | Changed behavior | J-63: all figures now derive from the currently selected view's observation set | Switch toggle from Episodes to Pooled and confirm that numeric figures (e.g. n on the disclosure line) change to the higher signal-day count; switching back restores the lower episode count |
| `/research/samples` | Cohort detail header line | Changed behavior | J-63: the header now states the overlap view the drill-down reproduces | Open a samples drill-down from an Episodes N= chip (new tab) — confirm the cohort line reads "Episodes (first-trigger)"; open one from a Pooled N= chip — confirm the line reads "Pooled (per-signal-day)" |
| `/research/samples` | Drill-down row list | Changed behavior | J-63: the drill-down rows now reflect the selected view (one row per episode vs one per signal-day) | In Episodes mode, click an N= chip for a subject where the same stock appeared on consecutive scan dates — confirm the drill-down shows ONE row for that continuous run at its first-trigger date, and the row count equals the N= figure |
| `/methodology` | Glossary entry — "Episode" | New entry | J-63: defines the Episode term used in the toggle and disclosure | Navigate to `/methodology`, search or scroll to "Episode", confirm an authored definition is present and categorized under forward evidence |
| `/methodology` | Glossary entry — "Pooled (per-signal-day)" | New entry | J-63: defines the Pooled term used in the toggle and disclosure | Navigate to `/methodology`, scroll to "Pooled (per-signal-day)", confirm an authored definition is present alongside the Episode entry |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` — `_run_position_index`, `_collapse_to_episodes`, `_event_study_observation_set`, `VIEW_EPISODES`/`VIEW_POOLED` constants — pure in-memory episode-collapse helper; fully consumed via the `view` parameter exposed on the event-study API and forwarded to the frontend.
- `apps/backend/app/engine/samples.py` — `view` cohort param on `_event_study_samples`/`compute_samples` — consumed by the samples drill-down API; rendered in the frontend cohort detail line.
- `apps/backend/tests/test_research.py`, `apps/backend/tests/test_samples.py`, `apps/backend/tests/test_api_research.py` — test files; no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 4 (two on `/research`, two on `/research/samples`) + 2 new glossary entries on `/methodology`
- **New pages/routes:** 0 (no new routes added)
- **Modified components:** 4 (`EventStudyViewToggle` new, `EventStudyDisclosure` new, N= chips updated, samples cohort header updated)
- **Navigation changes:** no
- **Backend-only changes:** 3 (engine helpers, samples engine extension, test files)
