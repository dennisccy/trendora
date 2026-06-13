**Verdict:** COHERENCE-PASS

## Iteration 14 — Coherence Audit

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration index:** 14
**Iter name:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14
**Snapshot SHA:** 376cb4ec8b39342174d2199f8c2369889a4558b5
**Target journeys:** J-63 (event-study first-trigger Episodes default + Episodes/Pooled toggle)

---

## Part A — Data Contract check

### Registered value: Setup & Pattern event study

Blueprint canonical source: `research:compute_event_study` / `_event_study_members`
Blueprint canonical endpoint: `GET /api/research/event-study` and `GET /api/research/samples`

**A1 — Duplicate computation check.**

The diff introduces three new functions in `apps/backend/app/engine/research.py`:

- `_run_position_index` — builds a `run_id → ordinal` map via a single SELECT over `scanner_runs`. It does NOT compute any event-study figure (no forward return, hit-rate, expectancy, MAE/MFE). It is a positional index helper used solely by the episode-collapse grouping.
- `_collapse_to_episodes` — a pure in-memory grouping of the `_event_study_members` rows. It reads stored `return`/`mae`/`mfe`/`regime`/`sector` VERBATIM from existing member dicts; recomputes none of them.
- `_event_study_observation_set` — the single canonical builder that feeds BOTH `compute_event_study` and `_event_study_samples`. It calls `_event_study_members` (the pre-J-63 canonical builder, unchanged) and conditionally applies `_collapse_to_episodes`. No new figure is computed; the pooled path is the unchanged `_event_study_members` list returned directly.

`_episode_count` is a disclosure-only derivation that calls `_collapse_to_episodes` over the same member set; it recomputes no canonical value.

No new function computes a forward return, excursion, hit-rate, mean, regime label, or any canonical event-study figure. No duplicate computation. No FAIL.

**A2 — Non-canonical source check.**

`_event_study_samples` in `apps/backend/app/engine/samples.py` previously called `_event_study_members` directly (non-canonical for J-63). This iteration replaces that call with `_event_study_observation_set` (the new shared builder), so BOTH `compute_event_study` and `_event_study_samples` read from one builder. No second fetch path exists. No FAIL.

The frontend (`apps/frontend/app/research/page.tsx`) reads all event-study figures from the `EventStudyResponse` payload returned by `fetchEventStudy` (`GET /api/research/event-study`). The disclosure values `n`, `unique_symbols`, `episode_count` are read verbatim from the payload fields — no client-side recomputation. The `view` field is read from the payload (the resolved value the backend echoes) to drive chip labels and cohort hrefs. No non-canonical source. No FAIL.

**A3 — New displayed values check.**

Three new payload fields appear: `n`, `unique_symbols`, `episode_count`. The blueprint's Data Contract explicitly registers these as "derivations of the SAME observation set, served on the same event-study + samples payloads" with no new endpoint. They are not synonyms of any existing registered value (they are disclosure metadata for the observation-set size, not scores, returns, or figures). The blueprint already registers them additively in the J-63 row. No duplicate-of-existing violation. No FAIL.

The `view` field on the payload is the backend's echo of the cohort parameter — not a displayed value requiring a separate canonical source. No FAIL.

**Glossary entries.** Two new glossary terms ("Episode", "Pooled (per-signal-day)") are added to `config.yaml` under the existing `config.methodology` catalog. They join the pre-J-63 "Setup & Pattern Event Study" entry in the `forward_evidence` category. The blueprint Data Contract row for the methodology catalog explicitly notes "J-63 Episode / Pooled definitions join this same catalog." They are not duplicates of any registered value — they are textual definitions, not computed values. No FAIL.

---

## Part B — Information Architecture check

**New pages/routes:** None. The diff touches only existing files under existing routes:
- `/research` — `apps/frontend/app/research/page.tsx` (no new route)
- `/research/samples` — `apps/frontend/app/research/samples/page.tsx` (no new route)
- `/methodology` — glossary entries added via `config.yaml` to the existing catalog (no route change)

**Navigation skeleton:** Unchanged. The diff contains no changes to any sidebar, nav, or router file. The UI surface map confirms "Navigation changes: no."

**Reachability:** The Episodes/Pooled toggle is a control WITHIN the existing `/research` page (the Setup & Pattern Lab card). The disclosure line and `N=` chips are elements of that same card. All are reachable in 1 click from the sidebar (Research). No new click depth added.

**Duplicate home:** No new home for any entity. The `/research/samples` drill-down link-reached under Research is unchanged in its navigational position.

**Parallel shell:** No new layout or nav shell introduced. The toggle and disclosure render inside the existing `EventStudyLab` card structure.

No Part B violations. No FAIL.

---

## Part C — Advisory observations

None. The iteration is tightly scoped: two new frontend components (`EventStudyViewToggle`, `EventStudyDisclosure`) slot into the existing card, all values read verbatim from the payload, and the samples drill-down correctly labels the view it reproduces. No formatting inconsistency or labeling drift is observed.

---

## Summary

- Data Contract violations (Part A): 0
- Information Architecture violations (Part B): 0
- Advisory notes (Part C): 0

The `view="pooled"` path routes through the UNCHANGED pre-J-63 `_event_study_members` list (byte-identical by construction). The episode path uses one shared `_event_study_observation_set` builder feeding both the aggregate endpoint and the samples drill-down, so count-coherence holds structurally. No new endpoint, no new stored column, no new nav section, no duplicate home. The two glossary entries join the registered config-backed catalog, consistent with invariant 10.
