# Iteration 37 — Coherence Audit

**Iteration:** goal-market-compass-iter-37
**Date:** 2026-09-01
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope of this iteration

Diff against snapshot `589b5b7781e9b15557cdca195e477de7348847e2` confirmed exactly two source files
touched (verified via `git diff <snapshot-sha> --stat` excluding lockfiles/binaries/`runs/*`/`reports/*`/
`docs/handoffs/*` and, separately, `apps/frontend/.next-verify/*` build-cache noise, which accounts for
all 55 other paths in the raw `git status`):

- `apps/backend/app/engine/compass.py` (`_assert_disposition_predicate` only, lines 593-609)
- `apps/backend/tests/test_manifest_invariants.py` (TC-24 fixture correction + one new unit test)

No `.tsx`, route, component, or `apps/frontend/lib/api.ts` file changed. This matches the iteration
spec's IN SCOPE / "UI surface changes: None" / "Blueprint conformance: No new surfaces" declarations
and the ui-surface-map's classification of both files as `backend-internal`.

## Data Contract check

The only production-code edit is inside `_assert_disposition_predicate`, an internal invariant guard
called by `evaluate_selection` (part of the already-registered "Next-session manifest — FREEZE/INTEGRITY
block" producer, `app.engine.compass.build_manifest_payload`). The diff converts two bare
`assert cond, msg` statements to `if not cond: raise AssertionError(msg)` with the identical condition,
identical message, and identical exception type (`AssertionError`) — confirmed by direct diff read
(`apps/backend/app/engine/compass.py:593-609`). This changes nothing about what is computed, only how the
guard fails under `python -O`. No new function, no new served field, no new computation path, no new
endpoint.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Next-session manifest — FREEZE/INTEGRITY block (`selection_disposition` truthfulness guard) | OK | `apps/backend/app/engine/compass.py:593-609` — same predicate, same producer (`build_manifest_payload`/`evaluate_selection`), same endpoint (`GET /api/compass`); guard-statement form only, not a computation change |
| TC-24 fixture (`test_manifest_invariants.py:935`) | OK (test-only) | HPE risk score raised `58.9`→`65.0` so the fixture genuinely exercises both qualifier-fail branches; no production code affected |

No new UI surface fetches this or any other registered value from a non-canonical source (no frontend
files changed at all this iteration). No new displayed value is introduced.

## Information Architecture check

No new page, route, or feature this iteration — nothing to check against the nav skeleton.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new surface this iteration) | OK | `apps/frontend/components/sidebar.tsx` unchanged (absent from diff); J-13's "Leadership rotation" section stays at its existing canonical home `/` per blueprint, not touched this round |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. This was a pure closing/hardening round (guard-statement robustness + a test-fixture fix) with
  zero product-surface delta, consistent with the blueprint's iter-37 note ("informational, no IA
  change, no Data Contract row change") and confirmed directly against the diff rather than taken on
  the note's word alone.
