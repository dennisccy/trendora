# Iteration 36 — Coherence Audit

**Iteration:** goal-market-compass-iter-36
**Date:** 2026-09-01
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `session_delta.rotation.{sector,theme}.{gaining,losing}` (new field on the ALREADY-registered "Next-session manifest — CONTENT block" row) | OK | Built inside `build_manifest_payload` (`apps/backend/app/engine/compass.py:919-234` region, `delta["rotation"] = build_rotation(...)`), served by the existing `GET /api/compass` (no new route). Matches blueprint's iter-36 note (`runs/goal-session-market-compass/state/blueprint.md:322-356`) exactly: same producer, same endpoint. |
| `session_delta.rotation.*` rank-pair source | OK — no duplicate computation | `apps/backend/app/engine/session_delta.py`: `sector_rank_pairs`/`theme_rank_pairs` are the ONE pair-building computation; `_sector_changes`/`_theme_changes` (feeding `session_delta.changes`) and `compass.build_rotation` (feeding `session_delta.rotation`) both consume the SAME precomputed pairs passed once from `build_manifest_payload` (`compass.py:920-923`: `sector_pairs = sector_rank_pairs(...)`; `delta = compute_delta(..., sector_pairs=sector_pairs, theme_pairs=theme_pairs)`). Proven by `test_compute_delta_reuses_precomputed_pairs_no_second_query` (identity check) in `apps/backend/tests/test_session_delta.py:940-958`. |
| `direction_word` (rotation rows + `session_delta.changes[].direction_word`) | OK — no second word map | `_rank_direction_word` (`compass.py:102-112`) reuses the EXISTING `_flat_band_word` classifier and `compass.vocabulary.direction_words` map — the same one `state_band` already uses. Single computation applied in two placements (`_rotation_row` and `_attach_rank_direction_words`, `compass.py:115-127, 196-203`). |
| `session_delta.changes[]` (What-changed card, J-02) | OK — unchanged | `compass-whatchanged-card.tsx` is not touched by this diff; `_entry()`'s new `delta` param is additive/optional (`session_delta.py:254-270`) and does not alter the existing rendered fields. TC-10 in the spec targets exactly this invariant. |
| Frontend rendering source | OK — canonical only | `compass-leadership-rotation-section.tsx` reads only the `compass` prop (sourced from the page's single `GET /api/compass` call via `state.compass`, wiring unchanged — `apps/frontend/app/page.tsx:107`, not touched this iteration). The rewritten component computes no sign, selects no word, applies no threshold — it renders `row.delta`/`row.direction_word`/counts verbatim (`compass-leadership-rotation-section.tsx:1021-1067`). |
| AG-11 (no new composite score) | OK | Rotation row shape is asserted closed to `{label, from, to, delta, direction_word, drill_href}` — `test_rotation_no_composite_score_field_anywhere`, `apps/backend/tests/test_compass.py:752-763`. |

No new value is introduced that lacks blueprint registration — the decomposer pre-registered `session_delta.rotation` and the `changes[].delta`/`.direction_word` additions in the blueprint's iter-36 note (`state/blueprint.md:322-356`) before this iteration ran, matching what actually shipped.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Leadership rotation section rewrite (`/`, Today) | OK | No new page/route; `apps/frontend/components/sidebar.tsx` has zero diff against the iter-36 snapshot (confirmed via `git diff <snapshot-sha> -- apps/frontend/components/sidebar.tsx`, empty output). The section occupies the SAME existing slot on `/` already registered in the blueprint's Feature/journey homes table for J-13 (`state/blueprint.md:58`: "`/` — Leadership rotation section (existing `compass-leadership-rotation-section.tsx` slot; no new route)"). `apps/frontend/app/page.tsx`'s import/usage of `CompassLeadershipRotationSection` is unchanged this iteration. |

No new pages, routes, or nav entries were introduced; none were expected (iter spec's "Blueprint conformance" and "OUT OF SCOPE" both state no nav/IA change).

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The Leadership rotation section's new `rotation_top_k` (5 per side, so up to 10 rows per kind) is an independent display cap from the What-changed card's `top_k` (5 total per kind, magnitude-ranked). This means a sector/theme mover ranked 6th–10th by magnitude can appear in the rotation section but not in the What-changed list above it — a real, user-visible difference in *which rows are shown*, though the underlying `delta`/`direction_word` values for any row appearing in both places are identical (single computation, verified by `test_rotation_changes_entries_carry_same_delta_and_direction_word_as_rotation_rows`). This is a deliberate, blueprint-registered design decision (iter-36 note explicitly calls out `rotation_top_k` as "independent of `top_k` above"), not drift — flagging only so a future reader doesn't mistake differing row *counts* between the two sections for a "numbers don't match" defect.
- The legacy-row handling (a manifest minted before iter-36 has no `rotation` key at all) is a genuine third UI state and is handled honestly (no fabrication, no crash) both server-side (`manifest_row_payload` serves the stored bytes verbatim) and client-side (`compass-leadership-rotation-section.tsx`'s `rotation === null` branch, with an explicit "not recorded" message). Good AG-8/AG-12 hygiene, noted for completeness only — not a violation.
