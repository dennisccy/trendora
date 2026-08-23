# Iteration 11 — Coherence Audit

**Iteration:** goal-market-compass-iter-11
**Date:** 2026-08-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

This iteration touches exactly one registered Data Contract row: the Next-session manifest
FREEZE/INTEGRITY block's `basis` sub-field (`basis.status`), which the blueprint documents (iter-11
update, `state/blueprint.md` lines 129-135) as gaining a fourth enum literal, additively, on the SAME
computing module and SAME endpoint — no new row, no new producer.

Traced end-to-end:

- **Producer:** `app.engine.compass.basis_disclosure` (`apps/backend/app/engine/compass.py:1100-1146`)
  remains the single implementation. The fail-closed fix (ruling A4) only adds branches inside this
  same function — a NULL/empty check, a `try/except` around `json.loads`, and an
  `isinstance(generation, dict)` guard — all returning the new `"unverifiable"` literal. No second
  `basis_disclosure`-shaped function exists anywhere in the diff or the repo (`grep -rn
  "basis_disclosure\|def basis"` across `apps/backend/app` returns exactly one `def` and one call
  site).
- **Call site:** `apps/backend/app/api/compass.py:43` — `"basis": basis_disclosure(session, row)` —
  unchanged, still the only caller, still served only by `GET /api/compass`. No new route or router
  was added anywhere in the diff (confirmed via `git diff --stat` against the noise-excluded snapshot:
  only `compass.py`, `j11_maintenance.py`, `models.py`, `test_manifest_invariants.py`,
  `compass-manifest-strip.tsx`, `api.ts`, `docs/goal.md`, plus the new migration engine
  module/script/tests and the new frontend label module/test — no `apps/backend/app/api/*` file other
  than the untouched existing `compass.py` route, no new FastAPI router/decorator in either new
  backend file).
- **Consumer:** `apps/frontend/lib/api.ts:1063-1069` extends `CompassBasisDisclosure.status`'s type
  union to the matching 4-literal set. `apps/frontend/components/compass-manifest-strip.tsx`'s
  `BasisLine` (the only renderer of `basis.status` in the frontend — confirmed by grep, one call site)
  now calls the newly extracted `basisDisclosureLabel` (`apps/frontend/lib/basis-disclosure-label.ts`)
  instead of its former inline ternary. This is a pure re-format/label mapping of a value still read
  from the same `view.basis` prop sourced from the canonical `GET /api/compass` response — not a
  recomputation and not a fetch from a second endpoint.
- The migration script (`apps/backend/app/engine/j11_schema_migration.py`,
  `apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py`) is a one-shot DDL/data-copy
  tool with no route, no server import, and no relationship to `basis_disclosure`'s computation — it
  changes `next_session_manifests`' constraint shape only, not any displayed value's producer/path.

No duplicate computation, no non-canonical source, no unregistered new value (the one new literal is
already registered in the blueprint's iter-11 update note).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `basis.status` (Next-session manifest FREEZE/INTEGRITY block) | OK | `apps/backend/app/engine/compass.py:1100-1146` (single producer, extended in place); `apps/backend/app/api/compass.py:43` (single serving call site, `GET /api/compass`); `apps/frontend/components/compass-manifest-strip.tsx:9,36` (single renderer, reads `view.basis` from the canonical response, formats via the extracted `apps/frontend/lib/basis-disclosure-label.ts`) |

## Information Architecture check

No new page, route, or nav entry was introduced. The diff's file set (7 tracked files + 5 new
untracked files: a backend engine module, a backend script, two backend test files, and a frontend
lib module + its test) contains no router, sidebar, or `app/` page file. The blueprint's own
"Blueprint conformance" field in the iteration spec (`docs/phases/goal-market-compass-iter-11.md`
lines 76-78) claims "No new page or nav entry; this work lives entirely under the existing 'J-05 /
J-06 manifest freeze + immutability' row's home (`/` — manifest strip)" — verified true: the only
UI-visible change is a label/variant addition inside the existing `compass-manifest-strip.tsx`
component that already lives at `/`, the registered home for J-05/J-06 in
`runs/goal-session-market-compass/state/blueprint.md` (IA table, "J-05 / J-06 manifest freeze +
immutability" row → `/` — Today).

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Manifest strip `basis` badge (existing surface, `/`) | OK | No nav file changed — confirmed no `sidebar.tsx`/router/`app/` file appears in the diff; feature stays inside its already-registered home, no parallel shell introduced |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The independent auditor pass (`docs/handoffs/goal-market-compass-iter-11-audit.md`, finding B1)
  found the live-schema migration also dropped three column `DEFAULT` clauses and reordered one
  column beyond the FK removal the owner authorized — a real deviation from ruling A1/AG-18's "nothing
  else" bound, already fixed forward (docstrings corrected, a pinning regression test added) and
  explicitly escalated to the owner for accept/reject. This is a schema-fidelity/authorization
  question, not a coherence violation: no displayed value's producer or serving endpoint moved, and no
  stored row value changed. Out of this gate's scope, noted for completeness only.
- The auditor's F1 finding notes the new `unverifiable` badge is currently unreachable in the live UI
  (all 8 no-recorded-basis rows fall into an earlier `preFreezeEra` branch that renders a different,
  also-honest message instead of reaching `BasisLine`). This does not create a second rendering path
  for the same value — it is the pre-existing `preFreezeEra` branch, unchanged by this iteration —
  and is a QA/audit observation about end-to-end visibility, not a coherence duplicate-source issue.
