**Verdict:** COHERENCE-PASS

# Coherence Audit — Iteration 47

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration index:** 47
**Iter name:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47
**Snapshot SHA:** c6931917fe451c08a75a9a7d89a828a5eac253b2
**Audited:** 2026-06-22

---

## Scope

This iteration is a pure backend read-path memory-safety refactor (J-105). The diff touches:

- `apps/backend/app/engine/research.py` — 7 unbounded `select(ForwardReturn)…all()` ORM materializations replaced with column-projected, `yield_per`-streamed, cohort-bounded reads.
- `apps/backend/app/engine/forward_testing.py` — the warm-up idempotency-set full-table scan replaced with a streamed key-projected scan (`_streamed_existing_keys`).
- `apps/backend/app/config.py` + `config.yaml` — new required `research.read_batch_size` field (memory-safety knob; boot-validated >= 1).
- Five test fixture files (additive `read_batch_size` key to inline `ResearchCfg` dicts).
- Two new test files (`test_research_streaming.py`, `test_forward_testing_streaming.py`).
- `runs/…/state/blueprint.md` — one additive IA-line annotation for J-105 (same route, same endpoints, no nav-skeleton change).

UI surface map confirms: 0 frontend source files modified, 0 new pages/routes, 0 navigation changes.

---

## Step 1 — Data Contract Check

### Registered values checked

All research aggregate values registered in the blueprint Data Contract (event-study matrix cells, factor-lab decile/rank-IC, factor-combination composite, regime×setup×pattern cells, downtrend-opportunity figures, and all `N=` cohort counts) are served via their unchanged canonical endpoints:

- `GET /api/research/event-study`
- `GET /api/research/factor-lab`
- `GET /api/research/factor-combination`
- `GET /api/research/regime-setup-pattern`
- `GET /api/research/downtrend-opportunity`
- `GET /api/research/samples`

**No new endpoint introduced.** The diff adds no `@router.get`/`@router.post` decorator and no new API route file.

**No duplicate computation.** The refactored builders (`_factor_observations`, `_combination_observations`, `_event_study_members`, `_event_study_members_by_horizon`, `_rsp_member`, `_recovery_turn_observation_set`, `_severity_velocity_observation_set`, plus the warm-up `_streamed_existing_keys`) continue to read `forward_returns` verbatim from the database. The column projection (`ForwardReturn.run_id`, `ForwardReturn.symbol`, `ForwardReturn.realized_return`, etc.) fetches a strict subset of the stored fields — it does not recompute any canonical value. The helper classes `_SubjectResultRow` and `_regime_by_run_projected` are read-path utilities that consolidate existing ORM attribute accesses; they introduce no new formula or derivation.

**No non-canonical source.** No new UI surface fetches any value from an endpoint other than the registered canonical one. No client-side recomputation is introduced.

**New config key `research.read_batch_size`** is a streaming batch size (a memory-safety tuning parameter), not a displayed value. It is not a Data Contract value and requires no registration.

**Result: no Part A violation.**

---

## Step 2 — Information Architecture Check

### New pages / routes

None. The UI surface map records 0 new pages/routes and 0 navigation changes. The blueprint blueprint annotation is a single additive sentence on the existing `/research/event-study` IA line — the nav skeleton is unchanged, no `blueprint.reapproval-requested` was filed.

### Existing research surfaces

All seven restored surfaces (`/research/event-study`, `/research` Factor Lab, `/research` Factor-combination, `/research/regime-setup-pattern`, `/research/downtrend-opportunity`, `/research/samples`, and their `N=` drill-downs) were registered in the blueprint IA at iter-45 and remain reachable from the Research nav hub in ≤2 clicks.

**Result: no Part B violation.**

---

## Step 3 — Subjective Observations (advisory only)

None. The iteration is a backend read-path refactor with no frontend surface change, no label change, no value formatting change, and no layout drift.

---

## Summary

| Check | Result | Notes |
|-------|--------|-------|
| Duplicate computation of registered value | PASS | All builders read `forward_returns` verbatim; column projection is not a recompute |
| Non-canonical source for registered value | PASS | No new endpoint; all research surfaces unchanged |
| New unregistered displayed value | PASS | No new displayed value; `read_batch_size` is a memory-safety knob, not a value |
| Navigation path for new feature | PASS | No new route introduced |
| Duplicate home for existing entity | PASS | No new page |
| Parallel shell | PASS | No new layout/nav shell |

**No objective violation from Part A or Part B. COHERENCE-PASS.**
