# goal-market-compass-iter-38 Dev Handoff

**Phase:** goal-market-compass-iter-38
**Date:** 2026-09-01
**Agent:** developer
**Status:** complete

## What Was Built

J-14: the Next-session focus section's "Not priority" ("why-not") list now states each
non-candidate's true reason for exclusion, and the actually-near-miss (below-floor) names can
now appear in the display — both defects named in the iteration spec.

### Backend (`apps/backend/app/engine/compass.py`, `evaluate_selection`)

- **True reason + advisory misses carried through.** Added `_failed_condition_entries(checks)`
  (reused by both `non_qualifying` rows and, new, `excluded_by_cap_pairs` rows) — every failed
  check now carries the SAME `gating` tag `_qualifier_checks` already produces. Previously,
  cap-excluded rows were extended with an unconditional `[]` (`why_not_pool.extend((row, [])
  for row, _checks in excluded_by_cap_pairs)  # passed everything, cut by cap`) — a comment that
  was true under `rule_version` v1 but became false the moment iter-35 (J-12) made
  `entry_min_score`/`risk_max_score` advisory-only, because a row can now clear the leadership
  gate, still fail an advisory qualifier, AND be cap-excluded.
- **`reason` field.** Every `why_not` entry now carries `reason:
  "excluded_by_cap" | "below_selection_floor"`, reusing the EXISTING closed
  `_DISPOSITION_EXCLUDED_BY_CAP` / `_DISPOSITION_BELOW_FLOOR` vocabulary
  (`comparison_cohort[].selection_disposition`'s own vocabulary) — no new label set.
- **`cap_rank` / `cap`.** A cap-excluded entry's 1-based leadership rank among all above-floor
  qualifying rows (reusing the SAME sort `qualifying` was already sorted by — no new ordering
  computed) and the configured `max_candidates` value; both `null` for `below_selection_floor`
  entries.
- **`why_not_totals`.** `{excluded_by_cap_uncapped, below_floor_in_band_uncapped}` — the two full
  pool counts, computed from the SAME `non_qualifying`/`excluded_by_cap_pairs` partitions the
  disposition tally already computes, BEFORE the display truncation (no new query).
- **The actual display fix — `_select_why_not_display` + new config key
  `compass.selection.why_not_cap_per_reason` (default `10`).** This is the part of the fix that
  is NOT obvious from the spec's literal wording alone, and is the one that makes "near-miss
  names come back" actually true on real data, not just in a fixture:

  `excluded_by_cap` rows are, by construction, always at/above `leadership_min_score`, so a
  single leadership-desc sort over the combined why-not pool ALWAYS ranks every cap-excluded row
  above every `below_selection_floor` row. On the committed 2026-08-12 frontier there are 27
  cap-excluded rows and only 20 `why_not_cap` display slots — so a naive "just add the reason
  field" fix would still show 20/20 cap-excluded and ZERO near-miss names; the reasons would be
  honest, but the near-miss restoration promised by the iteration title would not actually
  happen. `why_not_cap_per_reason` reserves up to N display slots for EACH reason class (10/10
  today, summing to the existing `why_not_cap` of 20); a scarce class's unused slots backfill
  from the other class's remaining pool. Config-only (`compass.selection`, validated
  `2 * why_not_cap_per_reason <= why_not_cap`), never a candidacy rule (AG-15), part of
  `manifest_config_hash`'s broad scope only (never `candidate_rule_hash`/`cohort_rule_hash` —
  unchanged).
- No new magic-number literal in `compass.py` — `why_not_cap_per_reason` is config-driven
  (`config.yaml` `compass.selection.why_not_cap_per_reason: 10`); `compass.py` remains a
  `test_no_magic_numbers.CALC_FILES` entry.

### Frontend

- `apps/frontend/lib/api.ts`: `WhyNotFailedCondition` gained `gating: boolean`; `WhyNotEntry`
  gained `reason: WhyNotReason`, `cap_rank: number | null`, `cap: number | null`; new
  `WhyNotTotals` interface; `CompassSelection` gained `why_not_totals`. The doc comment at the
  old `~1048-1050` no longer states the false universal "an EMPTY failed_conditions means the
  member passed every qualifier" claim — it now documents `reason`/`gating`/`cap_rank`/`cap` and
  states the TRUE (narrower) invariant.
- `apps/frontend/components/compass-focus-section.tsx`, `WhyNotList` / new `WhyNotLeadIn`: the
  false "— passed every qualifier, cut only by the focus-list cap." sentence now renders ONLY
  for entries with a truly empty `failed_conditions`. A cap-excluded entry names its rank and the
  cap ("— ranked #N of the above-floor names, cap C") plus any advisory misses; a below-floor
  entry keeps its existing failed-conditions list (already led by the `leadership_min_score`
  miss) plus any additional advisory misses, each now labeled "— advisory" when `gating: false`.
  The "Not priority" `Disclosure` summary now discloses both uncapped totals alongside the
  existing shown-count. No client-side threshold, rule, or derivation — every word rendered is a
  served field (component's own "re-renders served structures, implements no rule" comment
  still holds; verified by re-reading the diff).

## Files Changed

- `apps/backend/app/engine/compass.py` — `evaluate_selection`'s why-not construction; new
  `_failed_condition_entries` and `_select_why_not_display` helpers; module docstring updated.
- `apps/backend/app/config.py` — `CompassSelectionCfg` gained `why_not_cap_per_reason: int` +
  validator (`> 0`, `2 * why_not_cap_per_reason <= why_not_cap`); default factory updated.
- `config.yaml` — `compass.selection.why_not_cap_per_reason: 10`, commented.
- `apps/backend/tests/test_compass.py` — extended `test_excluded_by_cap_get_empty_failed_conditions`
  and `test_why_not_near_miss_has_failed_conditions_with_distance` with the new fields; added
  fixture `why_not_reasons_run` (isolating DXCM-shaped + below-floor rows, J-14 step 7) and three
  new tests: `test_why_not_reasons_and_cap_rank_isolate_each_condition` (TC-1/TC-2/TC-3),
  `test_why_not_totals_uncapped_before_display_truncation` (TC-4/TC-11), and
  `test_why_not_display_reserves_slots_for_the_scarcer_reason` (proves the display fix actually
  surfaces near-miss names when cap-excluded rows dominate).
- `apps/backend/tests/test_manifest_invariants.py` — added
  `test_tc23_why_not_cap_change_moves_only_display_length_not_totals_or_served_reasons` (TC-23
  extension: a `why_not_cap`-only config change moves only display length, never the uncapped
  totals nor an already-shown entry's served fields).
- `apps/frontend/lib/api.ts` — `WhyNotFailedCondition`, `WhyNotEntry`, new `WhyNotReason` /
  `WhyNotTotals`, `CompassSelection.why_not_totals`.
- `apps/frontend/components/compass-focus-section.tsx` — `WhyNotList` rewritten, new
  `WhyNotLeadIn`; "Not priority" `Disclosure` summary discloses both totals.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_compass.py
tests/test_manifest_invariants.py tests/test_api_compass.py tests/test_engine_identity.py -q`
Result: **136 passed, 0 failed.**

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_no_magic_numbers.py -v`
Result: `test_scanner_has_no_scoring_or_date_literals` passes;
`test_engine_calc_code_has_no_magic_numbers` FAILS — but on `indicators.py`, `forward_testing.py`,
`research.py` only (never `compass.py`). Confirmed **pre-existing**: reproduced the identical
failure via `git stash` against the pre-iteration tree. This is the "pre-existing failing test on
untouched files" item explicitly carried forward as OUT OF SCOPE by this iteration's own spec —
not introduced or touched by this change.

Command: `cd apps/frontend && NEXT_DIST_DIR=.next-verify npx next build`
Result: **compiles and type-checks successfully**, all 30 routes generated. (`npm run build`
bare refuses to target the live `.next` dir per this repo's build guard — the sanctioned
verification path is `NEXT_DIST_DIR=.next-verify npx next build`, matching the guard's own
printed instructions.) `npm run lint` prompts interactively for first-time ESLint setup — no
`.eslintrc*` is committed in this repo; this is a pre-existing condition (not introduced by this
iteration) and out of scope to fix here.

## Pre-fix baseline / post-fix measured counts (DEFINITION OF DONE)

Measured directly against the committed 2026-08-12 frontier data (`ScannerRun` id 3158, the
CURRENT `seed_latest_date`/default `/` view) by calling `compass.evaluate_selection` — read-only,
no manifest row touched.

**Pre-fix baseline** (matches the iteration spec's own cited measurement exactly):
- 20 of 20 served `why_not` entries had an empty `failed_conditions` (falsely rendered as
  "passed every qualifier, cut only by the focus-list cap.").
- 27 non-candidates clear the 80.0 leadership floor (`excluded_by_cap` pool).
- 25 non-candidates sit in the `[75.0, 80.0)` why-not band (`below_selection_floor` pool,
  individually why-not-eligible).
- All 20 shown entries were `excluded_by_cap` (leadership-desc sort always outranks the
  below-floor band) — 0 near-miss names ever listable.

**Post-fix measured** (same run, new code, via direct function call — read-only):
- `why_not_totals: {"excluded_by_cap_uncapped": 27, "below_floor_in_band_uncapped": 25}` —
  matches the pre-fix baseline exactly (unchanged pools, now honestly disclosed).
- `disposition_tally: {"below_selection_floor": 502, "excluded_by_cap": 27}` — unchanged from
  before this change (verified structurally: no line touching `disposition_tally`,
  `candidates`, `comparison_cohort`, `near_threshold_shadow`, `_candidate_rule_subset`, or
  `_cohort_rule_subset` was modified — the diff is confined to the why-not construction block
  and two new helper functions; see the diff hunk list below).
- 20 entries shown: **10 `excluded_by_cap` + 10 `below_selection_floor`** (was 20/0). Ten real
  near-miss tickers are now visible: `EXPE, INCY, MTB, PH, MMM, TRV, MET, EXPD, HSIC, BKNG`.
- **0 of 20** shown entries have an empty `failed_conditions` on this specific date's top-10
  cap-excluded set (all ten happen to carry an advisory miss today) — unit tests
  (`test_why_not_reasons_and_cap_rank_isolate_each_condition`, TC-2) prove the empty-list path
  still serves correctly when a row genuinely clears everything.
- Named advisory misses on cap-excluded rows now correctly surfaced, matching the iteration
  spec's own cited examples exactly: `DXCM` → `entry_min_score`; `QLYS` → `entry_min_score` +
  `risk_max_score`; `SWK` → `entry_min_score` + `risk_max_score` (the spec's cited QLYS/SWK
  actual scores — 70.85/60.18 vs the 60.0 risk ceiling — match).

Live end-to-end confirmation: started the backend + frontend via `scripts/dev.sh` (canonical
ports were free; used the offset ports it derived, 8255/3255), confirmed `GET /api/health`
readiness, then called `POST /api/compass/regenerate?as_of=2026-08-12&confirm=true` (the
system's existing, sanctioned "explicit confirm-gated regenerate" action — the SAME mechanism
prior iterations 30–37 used to mint each successive `2026-08-12_v{N}.json` after an
`evaluate_selection` change) to mint **version 10**, which the default `GET /api/compass` (no
`as_of`) now serves. This was necessary because the pre-existing frozen version 9 is immutable
(AG-12) and a plain `GET` on an already-frozen as-of never recomputes — QA/browser verification
of the Today page needs a manifest actually minted under the new code to see the corrected
"Not priority" list. Confirmed `2026-08-12_v9.json`'s sha256 is byte-identical before and after
(`870cb600...`); `git status`/`git diff` show zero changes under
`apps/backend/data/exports/`; only a new `2026-08-12_v10.json` file was added. Fetched `/` via
curl (200 OK, normal Next.js RSC payload) — full interactive/screenshot verification is
browser-qa-agent's job (Chrome MCP). Both dev servers were stopped afterward (verified via `ss`
and `ps` that ports 8255/3255 and all `next dev`/`next-server`/`uvicorn` child processes are
gone).

## Anti-goal re-check

- **AG-11 (no new composite number):** no new blended/composite score introduced. `reason` is a
  label from an EXISTING closed vocabulary; `cap_rank`/`cap` are structural (a rank and a
  configured integer, never a score); `gating` is a boolean already computed by
  `_qualifier_checks`; `why_not_totals` are plain counts. Verified: `test_no_composite_score_field_anywhere`
  passes unchanged.
- **AG-12 (manifest immutability):** `2026-08-12_v9.json` (and every other pre-existing
  manifest row/file) is byte-identical before/after — confirmed by sha256 and `git status`.
  Only a NEW version (10) was minted via the existing, sanctioned regenerate action; no row was
  mutated or deleted.
- **AG-15 (no outcome-tuned selection):** `leadership_min_score`/`entry_min_score`/
  `risk_max_score` values are untouched. The new `why_not_cap_per_reason` is a DISPLAY
  allocation for an already-non-selecting list (why-not entries are, by definition, not
  candidates) — it changes nothing about candidacy, and its value (10, half of the existing
  `why_not_cap` of 20) was chosen for even display balance, not from any realized-return
  analysis.
- **AG-16 (cohorts are not controls):** `near_threshold_shadow` is untouched by this change
  (structurally verified — no line touching it was modified) and still has no field in the
  why-not payload; a restored near-miss why-not entry is a selection-trace row (ticker +
  condition evaluation) only, never a shadow-cohort row.
- **AG-17 (repair never rewrites provenance):** not implicated — this change touches no
  provenance/eligibility field and mints no manifest for an as-of predating J-11 Stage G.

## Known Issues

- `why_not_cap_per_reason`'s default value (10) was chosen as an even split of the existing
  `why_not_cap` (20) rather than being specified by name anywhere in the iteration spec — the
  spec says only "the split governed by config-only keys" without naming a value. Flagging this
  as an implementation judgment call for the reviewer to confirm, not a spec ambiguity I could
  resolve by re-reading further.
- `npm run lint` cannot run non-interactively in this repo (no committed ESLint config; it
  prompts for first-time setup) — pre-existing, not touched by this iteration. The production
  `next build` typecheck (the other half of the project's "frontend tests" per
  `project-template.md`) passes cleanly.
- `test_engine_calc_code_has_no_magic_numbers` fails on `indicators.py`/`forward_testing.py`/
  `research.py` — confirmed pre-existing (reproduces identically via `git stash`), explicitly
  carried forward as OUT OF SCOPE by this iteration's own spec.
- The regenerated `2026-08-12_v10.json` is a new, larger export than v9 — this is expected and
  disclosed (new `why_not` keys added; `manifest_config_hash` and `content_hash` legitimately
  move on this newly minted manifest per the spec's own scope rule); no schema_version bump was
  needed (`selection.why_not` is an unconstrained array in
  `docs/handoffs/trendora-next-session-manifest-v1.schema.json`; TC-25 schema-validation tests
  pass unchanged).
