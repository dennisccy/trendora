# Iteration 29 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-29
**Date:** 2026-07-29
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope reviewed

Product-code diff (`git diff 0b36dba6...` / `iter-diff.md`) touches exactly 9 files, all previously
identified by the iter spec and the ui-surface-map:

- `apps/backend/app/config.py` (new `research.factor_join_run_chunk` config knob)
- `apps/backend/app/engine/evidence.py` (`build_evidence_payload` per-claim isolate-and-continue guard)
- `apps/backend/app/engine/research.py` (`_factor_observations` / `_all_factor_observations_by_horizon`
  join-accumulator chunking; new private helpers `_runs_with_fr`, `_fr_slice_map`, `_all_fr_slice_map`)
- `apps/backend/tests/test_evidence.py`, `test_factor_lab_all.py`, `test_research_streaming.py` (new tests)
- `apps/frontend/app/evidence/page.tsx` (`DrawdownExpectationsPanel` branches on the new resolver)
- `apps/frontend/lib/evidence.ts`, `evidence.test.ts` (`resolveDrawdownExpectationsPanelState`,
  `expectations_status` type)
- `config.yaml` (`factor_join_run_chunk: 100`)

`git status --porcelain` shows the identical file set uncommitted — nothing outside the reviewed diff.
The remaining ~90 changed files (`incredible_auto_dev/*`, `project-extensions/host-guard/*`, framework
docs) are the goal-mode meta-framework's own tooling, not part of the Trendora product surface the
blueprint governs — out of scope for this audit, confirmed by inspecting the diff headers directly.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `expectations_status: "unavailable"` (new, per-claim) | OK — registered | Blueprint "Membership timeline / research hot-key caches" row (blueprint.md:345) names `build_evidence_payload` as computing module, `GET /api/evidence` as serving endpoint. Diff extends the SAME function's SAME per-claim loop (`apps/backend/app/engine/evidence.py:118-140`, wrapping the pre-existing `compute_drawdown_expectations_cached` call in try/except) — no new function, no new endpoint. Frontend reads it verbatim off the existing `fetchEvidence()` → `GET /api/evidence` call (`apps/frontend/lib/api.ts:476-483`, unchanged) via a pure resolver (`apps/frontend/lib/evidence.ts:1214-1222`) — re-presentation only, not a recompute. |
| Regime score / market phase / realized forward-returns / factor-observation pool (`_factor_observations`, `_all_factor_observations_by_horizon`) | OK — same producer, refactored not duplicated | Blueprint row (blueprint.md:339, 345) names `app.engine.research`/`forward_testing` as the sole producer for both the Evidence drawdown-expectations path and the Factor Lab. The new helpers `_runs_with_fr` (`research.py:152-170`), `_fr_slice_map` (`research.py:173-190`), `_all_fr_slice_map` (`research.py:326-345`) are private, in-module decompositions called ONLY from the same two existing entry points (`_factor_observations`, `_all_factor_observations_by_horizon`) — no second computing module, no second endpoint. Byte-identity to the pre-chunk implementation is asserted by new unit tests (`test_research_streaming.py` TC-2, `test_factor_lab_all.py`'s `_all_pools_reference_unchunked` oracle). |
| `research.factor_join_run_chunk` config knob | OK — not a displayed value | Internal accumulator-chunk-width tuning parameter (`config.py`, `config.yaml`); never served to the UI, not a Data Contract entry. |

No new function computes an already-registered value independently of its canonical module; no new UI
surface fetches a registered value from a non-canonical endpoint; no new displayed value is an
unregistered synonym of an existing one.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/evidence` (`DrawdownExpectationsPanel` new "unavailable" state) | OK | No route/nav change — `apps/frontend/components/sidebar.tsx`'s Evidence entry (blueprint.md:308) is untouched by this diff; the new state lives inside the existing claim card, additive to the existing panel's branching logic. |
| `/research/factor-lab` (regression-only, backend function shared) | OK | Diff does not touch `apps/frontend/app/research/factor-lab/page.tsx` or any router/nav file; the row exists only because the ui-surface-map correctly flags it for regression verification, not because a new surface was added. |

No new page, route, or parallel shell was introduced this iteration, matching the spec's own
"Blueprint conformance" claim ("No new page/nav/route").

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The blueprint's "Membership timeline / research hot-key caches" row (blueprint.md:345) still reads
  "iter-29 (AG-8 closure) -- **TARGETED this iteration, not yet built**" — i.e., it has not yet been
  updated to reflect that the fix landed. This is expected process lag (the decomposer updates the
  `[TARGET]`/built status only after the evaluator confirms), not a coherence defect; flagging so the
  iter-30 decomposer remembers to flip it once the evaluator scores this iteration.
- The diff's own comments (`config.py`, `config.yaml`, and the new "iter-29 AUDIT" test block in
  `test_research_streaming.py`/`test_factor_lab_all.py`) document that an initial version of this fix
  reused `research.read_batch_size` (2000, a row-count knob) as the run-count chunk width, which produced
  exactly one chunk against the live basis (1,812-1,871 runs/horizon) and bound nothing — this was caught
  and corrected within the same iteration (separate `factor_join_run_chunk` knob, default 100, with a new
  regression test pinning the shipped config actually chunks). This is a within-iteration self-correction
  already reflected in the diff, not an open coherence issue — noted for context only.
