# Iteration 7 — Coherence Audit

**Iteration:** goal-market-compass-iter-7
**Date:** 2026-08-21
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

Backend-only, no-UI iteration (J-10 retry: vendor swap `stooq`→`yahoo` + new fail-closed
adjustment-convention gate). Diff touches exactly three files —
`apps/backend/app/data_providers/yahoo_provider.py`, `apps/backend/app/engine/j10_recovery.py`,
`apps/backend/tests/test_j10_recovery.py` — plus the untracked post-dev audit fix inside the same two
non-test files (`docs/handoffs/goal-market-compass-iter-7-audit.md` documents a CRITICAL fail-open fix
in `check_adjustment_convention`). No route file, no frontend file, and `state/blueprint.md` itself
were touched. No objective Data Contract or Information Architecture violation found.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| All 11 blueprint-registered rows (manifest CONTENT/FREEZE blocks, engine identity, sector label, regime, market phase/severity/P(bear), breadth, sector/theme scores, stock scores, evidence status, coverage, run summary, readiness) | OK — untouched | Diff contains no edits to `app/engine/compass.py`, `app/engine/session_delta.py`, `app/api/*`, `scoring.py`, `sectors.py`, `themes.py`, `data_manager.coverage_from_storage`, or any route file this iteration |
| `run_data_job` write path (single-producer for `daily_prices`/`scanner_runs`/`data_provider_runs`) | OK — still exactly one definer | `grep -rn "def run_data_job\b" apps/backend/app` → only `apps/backend/app/engine/data_manager.py:6095`; `grep -rln "run_data_job\b" apps/backend/app` → only `data_manager.py` (definer) + `j10_recovery.py` (caller, unchanged call sites). Matches iter-6's confirmed finding; still holds after this iteration. |
| New: adjustment-convention check verdict (`check_adjustment_convention` → agree/mismatch/inconclusive) | OK — not a displayed value, no registration required | `apps/backend/app/engine/j10_recovery.py` (new function, ~line 470 region) — held in-memory only, never DB-written (asserted by 9 new tests, e.g. `test_convention_check_never_writes_regardless_of_verdict`), never served by any endpoint or route (`reports/phase-goal-market-compass-iter-7-ui-surface-map.md`: "No API route exposes this method"). Consumed only by the dev handoff (documentation) and internal orchestration — not a product-displayed entity, so Data Contract rule A4/A5 (duplicate-of / unregistered-value) does not apply. |
| New: `YahooProvider.get_adjusted_close` | OK — additive, no second write path | `apps/backend/app/data_providers/yahoo_provider.py:96-134` — a parallel read-only method alongside `get_daily`; `get_daily`'s contract, request shape, and callers are unchanged (confirmed by diff; the new `_FakeAdjustedCloseProvider` test fixture explicitly `pytest.fail`s if `get_daily` is ever called by the check). Used exclusively by `check_adjustment_convention`. |

No duplicate computation, no non-canonical source, no second producer introduced.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| *(none — no new page/route/feature this iteration)* | OK — vacuous | `git diff 6ebdeaa6...HEAD --stat -- apps/backend/app/api apps/frontend` returns empty; `reports/phase-goal-market-compass-iter-7-ui-surface-map.md` confirms zero UI surfaces changed, zero new routes, no navigation changes; `runs/goal-session-market-compass/state/blueprint.md` is byte-unchanged this iteration (`git diff 6ebdeaa6...HEAD --stat -- .../blueprint.md` empty, `git status` clean on it, last commit touching it is `1147912` — iter-4's showcase commit, not iter-7) |

Nothing to check against `Sidebar.tsx`/router config — no candidate route exists.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. This is a clean pure-backend/test iteration against the coherence rubric specifically (no
IA/Data-Contract drift). See "Observations for the evaluator" below for a substantive but
out-of-mandate note.

## Observations for the evaluator (informational — not a coherence verdict input, per dispatch instruction)

- **`docs/goal.md` has uncommitted owner amendments made after this iteration's spec was written.**
  The current working tree's J-10 step 2a text replaces the absolute-level adjustment-convention
  tolerance this iteration implemented with a precommitted path-agreement + stable
  multiplicative-bridge test, plus a one-series-end-to-end rule, a persisted per-pair evidence
  requirement, and an explicit zero-usable-pairs-can-never-agree rule. The iter-7 code (`git diff
  6ebdeaa6...`) predates all of this — it implements a single absolute relative-delta-on-close-price
  tolerance (`CONVENTION_CHECK_TOLERANCE = 0.0075`), not path-agreement/bridge. This is a real,
  material spec-vs-implementation gap, but it is a data-fidelity/AG-9-conformance question for the
  evaluator, not an IA or Data Contract structural issue — `daily_prices.close` ingestion mechanics
  are not a blueprint-registered displayed value, so no Data Contract rule is implicated. Consistent
  with last iteration's handling, flagged here as an observation only.
  - Directly relevant supporting context already on record: the post-dev auditor's
    `docs/handoffs/goal-market-compass-iter-7-audit.md` independently found and fixed the same
    zero-pairs-never-agrees gap this iteration (finding B1, CRITICAL, fixed in
    `j10_recovery.py`) and separately flagged an unresolved gap (B2, IMPORTANT, not fixed) that the
    gate validates Yahoo's `adjclose` while the unchanged restore path (`run_bounded_recovery_fetch`
    → `data_manager.run_data_job` → `provider.get_daily`) would write Yahoo's raw `quote.close` — the
    exact "one series, end to end" concern the owner's amendment now makes an explicit rule. Since the
    gate returned `mismatch` on the real run, this gap never reached a write this iteration (zero DB
    rows changed, independently confirmed by the auditor's read-only SQL: `daily_prices` MAX(date)
    2026-08-10, `data_provider_runs` MAX(id)/COUNT 541/541, `next_session_manifests` COUNT 24 /
    MAX(as_of) 2026-08-12 — AG-12 held). Both B2 and the goal.md redesign are already correctly
    scoped as next-iteration work, not this iteration's to close.
- `reports/qa/goal-market-compass-iter-6-evidence/` (quarantined under AG-17) was left untouched by
  this iteration, consistent with its quarantine status — confirmed via `git status`/diff showing no
  changes under that path, and the audit report's independent confirmation ("byte-unchanged... last
  touched by commit `e58b773b`"). Not treated as clean evidence; not recommended for deletion.
