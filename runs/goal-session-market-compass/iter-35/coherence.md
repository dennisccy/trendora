# Iteration 35 — Coherence Audit

**Iteration:** goal-market-compass-iter-35
**Date:** 2026-09-01
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Diff scope (confirmed via `git diff 24f1765c...` and `git status`): 5 files, all backend —
`apps/backend/app/engine/compass.py`, `apps/backend/tests/test_api_compass.py`,
`apps/backend/tests/test_compass.py`, `apps/backend/tests/test_manifest_invariants.py`,
`config.yaml`. Zero frontend files touched, matching the iter-35 spec's own "UI surface changes:
None" / "No new page or nav entry" declaration and the blueprint's iter-35 note.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Next-session manifest — CONTENT block: `selection.candidates` / `selection.disposition_tally` / `selection.why_not` (the row J-12 targets) | OK | Fix lives entirely inside the already-registered canonical producer `app.engine.compass.evaluate_selection` (`apps/backend/app/engine/compass.py:642` — confirmed sole definition via `grep -rn "def evaluate_selection"`) and the already-registered checklist builder `_candidate_payload` (`compass.py:568-618`). No new function computes candidacy/disposition independently. |
| Serving endpoint for the above (`GET /api/compass`) | OK | Confirmed via `apps/backend/app/api/compass.py:58` (`@router.get("/compass")`) — unchanged this iteration, not touched by the diff. `POST /api/compass/regenerate` (`compass.py:90`) is likewise pre-existing and untouched — no new route added. |
| New field `checklist[].gating` (boolean tag distinguishing the leadership gate from advisory qualifiers) | OK (additive, within already-registered row) | `compass.py:509-535` (`_qualifier_checks`) is the SINGLE source of the tag; `_candidate_payload` (`compass.py:552-559`) reads it rather than re-deriving it. This is a sub-field enrichment of the already-registered `selection.candidates`/`selection.why_not` checklist structure, not an independent new value — same additive pattern as iter-11/12's `basis.status` extension and iter-28's `state_band`. The blueprint's iter-35 note (`state/blueprint.md:300-319`) already records this plan against the existing CONTENT-block row, so it is registered, not merely unregistered-and-new. |
| `config.yaml` `compass.selection.rule_version` bump (`"v1"` → `"v2"`) | OK | Threshold VALUES (`leadership_min_score`, `entry_min_score`, `risk_max_score`) unchanged (verified in the diff — only the `gating`/advisory classification and the version string changed); no schema-file (`trendora-next-session-manifest-v1.schema.json`) version bump, matching the spec's OUT-OF-SCOPE declaration. |
| Pre-existing stored `next_session_manifests` rows / export files (AG-12/AG-17) | OK | Diff contains no writer/migration code touching stored rows; test suite additions (`test_perturbing_advisory_qualifiers_leaves_hashes_membership_and_dispositions_unchanged`, `test_disposition_predicate_holds_for_every_comparison_cohort_row`) exercise the invariant in-process against fixture DBs only, not the canonical database. |

## Information Architecture check

No new page, route, or nav-reachable feature this iteration (confirmed: zero frontend files in
the diff; `reports/phase-goal-market-compass-iter-35-ui-surface-map.md` is absent, consistent with
`Frontend Present: no` in the iteration spec's metadata). The corrected disposition labels surface
through the SAME already-registered home (`/` — Next-session focus section / manifest strip,
per `state/blueprint.md`'s Information Architecture table) via the SAME endpoint. Nothing to audit
under Part B.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route this iteration) | N/A | apps/frontend/components/sidebar.tsx not touched (confirmed via `git status`/diff scope) |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The new runtime invariant checks (`_assert_disposition_predicate` in `compass.py:462-480`, and the
  `assert len(gating_checks) == 1` in `evaluate_selection` at `compass.py:687`) are plain Python
  `assert` statements, which no-op under `python -O`. This is a code-robustness observation, not a
  coherence violation (no duplicate computation, no non-canonical source) — outside this gate's
  scope; flagging only for the reviewer/auditor's awareness if not already covered.
- None of the Data Contract or IA rows required correction; this iteration is a clean example of a
  single-producer, single-endpoint bugfix with no drift.
