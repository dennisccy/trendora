# Iteration 31 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-31
**Date:** 2026-07-29
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Scope confirmed from the diff (`git diff 16da31344c...`, plus the iter-31 spec's "Data-contract
additions: None" and the ui-surface-map's "Status: N/A — Backend-only phase"): only
`apps/backend/app/engine/research.py`, `apps/backend/app/config.py`, `config.yaml`, and two test files
changed. No frontend file changed at all.

The touched value is the Factor-Lab-all `factors_table` (decile table + rank-IC), served by
`GET /research/factor-lab?all=true` and the MCP tool in `app.mcp.tools`. Per the blueprint's iter-29
paragraph (`state/blueprint.md:280`) this view is explicitly "a legacy consumer with no Data Contract
row of its own since its OWN displayed values are unchanged by this fix" — a precedent this iteration's
own Blueprint-conformance section (`docs/phases/goal-ops-hardening-iter-31.md:150-156`) invokes again,
and the blueprint's iter-31 paragraph (`state/blueprint.md:284`) restates it. This is consistent —
Factor-Lab-all is a real, previously-established exception, not a new unregistered value invented this
iteration to dodge registration.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Factor-Lab-all `factors_table` (decile/rank-IC) | OK | `apps/backend/app/engine/research.py:677-717` (`compute_factor_lab_all`) — same sole producer, same two callers (`GET /research/factor-lab?all=true`, MCP tool), unchanged; iter-31 only restructures the internal `_all_factor_observations_by_horizon` return shape (`research.py:510-641`, dict-per-horizon → `(core_records, pools)` tuple/index encoding) and adds a single-flight guard to `factor_lab_all_cached` (`research.py:3057-3163`) — no new endpoint, no second computing module, no client-side recomputation. Byte-identity is enforced by new/updated tests (`test_factor_lab_all.py::test_shared_pools_chunked_equal_the_pinned_unchunked_reference`, `::test_returned_pool_structure_projected_to_the_live_basis_stays_under_the_memory_cap`). |
| `research.factor_pool_max_observations` (new config knob) | OK | `apps/backend/app/config.py:1354-1391`, `config.yaml:900-1029` — an internal AG-8 disclosure ceiling (logs a WARNING, never displayed to a user, never a served value); not a Data Contract candidate. |

No new UI surface fetches this value from a different endpoint (no frontend file changed at all — see
`reports/phase-goal-ops-hardening-iter-31-ui-surface-map.md`). No new function independently recomputes
`factors_table`, `pools`, or any decile/rank-IC figure outside `app.engine.research`. `_factor_observations`
/ `_runs_with_fr` / `_fr_slice_map` (the sibling single-factor path serving `/evidence`) and
`compute_forward_aggregates` / `resolved_forward_aggregate_evidence` (a different module) show zero diff in
`git diff` — confirmed byte-frozen as the spec required, not silently touched.

## Information Architecture check

No new page, route, or nav entry. `git diff --stat` and the diff itself touch zero files under
`apps/frontend/`. `/research/factor-lab` keeps its existing home under the Research nav section
(`state/blueprint.md` IA table, line ~311: `Research /research — index of 15 labs (event-study,
factor-lab, regime-lab, …)`). The ui-surface-map (`reports/phase-goal-ops-hardening-iter-31-ui-surface-map.md`)
independently confirms: "No UI surfaces affected."

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/research/factor-lab` (existing) | OK | No nav file change to inspect — `apps/frontend/components/sidebar.tsx` (or equivalent) has zero diff this iteration; the route's response shape is unchanged (DoD requires byte-identical output), so its existing nav entry and reachability are untouched. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None of substance. This is a clean, narrowly-scoped, backend-only availability/concurrency fix that
  matches its own stated Blueprint-conformance section exactly: no new Data Contract row, no
  Information Architecture change, one additive documentation paragraph in `state/blueprint.md`
  (iter-31, line 284) recording the change — consistent with the diff's `+2` line count against
  `blueprint.md` (`git diff --stat`: `runs/goal-session-ops-hardening/state/blueprint.md | 2 +`).
- Carried framework nit (not this iteration's scope, not a coherence issue): `merge_ui_test_results.py`'s
  `_ROW_RE` drops `TC-`-prefixed rows — already flagged in the iteration spec's NOTES for owner/framework
  action.
