# Iteration 38 — Coherence Audit

**Iteration:** goal-market-compass-iter-38
**Date:** 2026-09-01
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

All changed values are additive fields on the ALREADY-REGISTERED "Next-session manifest — CONTENT
block" row (`selection.why_not[]`, `selection.why_not_totals`), whose blueprint contract is: computed
by `app.engine.compass.build_manifest_payload` (via `evaluate_selection`), served only by
`GET /api/compass`. Confirmed no second producer or second route was introduced.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `selection.why_not[].reason` (excluded_by_cap / below_selection_floor) | OK | `apps/backend/app/engine/compass.py:900,908` — reuses pre-existing `_DISPOSITION_BELOW_FLOOR`/`_DISPOSITION_EXCLUDED_BY_CAP` constants (defined `compass.py:496-497`, already used by `comparison_cohort[].selection_disposition`), assigned inside `evaluate_selection`, the same registered producer. |
| `selection.why_not[].failed_conditions[].gating` | OK | `apps/backend/app/engine/compass.py:672-109` (new `_failed_condition_entries` helper) — `gating` is read straight from `_qualifier_checks`' existing per-check `gating` tag, no new rule. Used for both non-qualifying rows and now also cap-excluded rows (`compass.py:930-936`, was previously discarded via an unconditional `[]`). |
| `selection.why_not[].cap_rank` / `.cap` | OK | `apps/backend/app/engine/compass.py:901` (`enumerate(excluded_by_cap_pairs, start=sel.max_candidates + 1)`) — reuses the SAME leadership-sorted `qualifying` ordering already computed for candidate selection; no new ranking pass. |
| `selection.why_not_totals.{excluded_by_cap_uncapped, below_floor_in_band_uncapped}` | OK | `apps/backend/app/engine/compass.py:913-918` — computed from the same `excluded_by_cap_pairs`/`non_qualifying` partitions the disposition tally already computes, before the `why_not_cap` display truncation (`_select_why_not_display`, `compass.py:806-823`). |
| `compass.selection.why_not_cap_per_reason` (new config key) | OK | `apps/backend/app/config.py:2653,2670-2676`; `config.yaml:1447` — display-allocation-only tunable under the existing `compass.selection` namespace, validated (`2 * cap_per_reason <= why_not_cap`), no literal in code (`compass.py` remains a `test_no_magic_numbers.CALC_FILES` entry, confirmed at `test_no_magic_numbers.py:57`). Not part of `candidate_rule_hash`/`cohort_rule_hash` per the config comment and IN SCOPE item — matches AG-15 (display allocation, not a candidacy rule). |
| Frontend rendering (`compass-focus-section.tsx`) | OK — re-format, not recomputation | `apps/frontend/components/compass-focus-section.tsx` `WhyNotLeadIn`/`WhyNotList` render `reason`/`cap_rank`/`cap`/`gating` fields verbatim from the served `WhyNotEntry`; no client-side threshold, distance, or reason derivation (confirmed: no new arithmetic on qualifier values, only served-field branching). Fetched via the single existing `fetchCompass()` → `GET /api/compass` (`apps/frontend/lib/api.ts:1231-1232`) — no new fetch call added. |

No new producer, no new endpoint, no duplicate/competing computation of any registered value found.
No new displayed value/entity outside the Data Contract was introduced (all additions are documented
sub-fields of the already-registered `selection.*` object, matching the iter-38 blueprint note and the
spec's "Data-contract additions" section verbatim).

## Information Architecture check

No new page, route, or nav entry in this iteration — only an existing component
(`apps/frontend/components/compass-focus-section.tsx`) on the existing Today (`/`) page was modified.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| "Not priority" disclosure, Today (`/`) | OK — pre-existing home, unchanged | `apps/frontend/components/sidebar.tsx` (unmodified this iteration, confirmed via `git status`/diff file list — not among the changed files); feature stays inside the already-registered `compass-focus-section.tsx` slot under the Today IA row. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. The change is a clean, narrowly-scoped additive extension entirely within the already-registered
  producer/endpoint pair, with vocabulary and ordering fully reused rather than re-derived — the pattern
  this session's blueprint update notes (iter-28 through iter-37) have consistently followed.
