# Iteration 48 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-48
**Date:** 2026-08-05
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

Registered row touched this iteration: **"Membership timeline / research hot-key caches"**
(`membership_timeline_cache`, `event_study_cache`; served by `/data`, `/sectors`, `/themes`,
`/research/*`, `/evidence`). No other registered row is touched — zero routes/`api.py` files changed
(diff stat confirms only `data_manager.py`, `research.py`, `samples.py` + 4 test files).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Membership timeline (`entries`/`exits`/`excluded`, per date) | OK | `apps/backend/app/engine/data_manager.py:523-524` adds an optional `reuse_excluded_by_date` param to the SAME canonical `_membership_timeline`; `:891-917` (`membership_timeline_cached`) is a new branch that still calls the SAME function — no new computing module, no new table, no new endpoint. `entries`/`exits` are still recomputed fresh in full date order every call (unchanged); only the per-date `excluded` tally, proven order-independent by the docstring's purity argument, is conditionally reused from the SAME cache row's previous generation. |
| Factor-sample cohort, `total` slice | OK | `apps/backend/app/engine/samples.py:174` now passes `cfg=cfg` explicitly to the SAME `_factor_observations` (previously relied on its internal `get_config()` default) — a config-resolution consistency fix, not a new computation; row-building loop below it (`:203-216`) reuses the SAME `members` list in place (memory optimization), same values. |
| Factor-sample cohort, `regime` slice | OK | `apps/backend/app/engine/research.py:329-388` adds `_factor_regime_observations` — a NEW function, but it lives inside `app.engine.research`, the row's own registered canonical module, and is called only from `samples.py:187` (`_factor_samples`'s `regime` branch), the row's own registered call path, still served by the SAME `GET /api/evidence` / `/research/factor-lab`. It replaces the previous `[o for o in _factor_observations(...) if o["regime"] == regime]` post-filter with an inline bounded filter inside the SAME chunked join loop — the iteration spec requires (TC-5) and the test diff adds a pinned-reference byte-identity proof against the pre-fix population, mirroring the identical pattern the iter-47 decile-branch fix (`_factor_decile_observations`) already established as coherent for this exact row. Not a second producer: it is an implementation refactor of the row's own registered computation, not an independent re-derivation. |
| New displayed value/field | N/A — none added | UI surface map confirms 0 frontend files changed, 0 new response fields; existing `status`/`aggregates_refreshed`/`message`/drawdown-expectations fields are unchanged in shape, only faster/safer to resolve. |

No duplicate computation, no non-canonical source. The blueprint's own iter-48 changelog paragraph
(`runs/goal-session-ops-hardening/state/blueprint.md:352`) and the row's iter-48 note
(`:410`) were appended THIS iteration and describe exactly this diff — "SAME computing modules
... SAME table ... SAME endpoint ... no second producer, no schema change" — which the diff matches.

## Information Architecture check

Zero frontend files changed (confirmed by diff stat and `reports/phase-goal-ops-hardening-iter-48-ui-surface-map.md`'s
own summary: "Frontend surfaces changed: 0 ... New pages/routes: 0 ... Navigation changes: no").
The spec's own "Blueprint conformance" field and "UI surface changes: None" declaration match the diff.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` (Data Manager) | OK — pre-existing home, no new route | `runs/goal-session-ops-hardening/state/blueprint.md:384` (Navigation skeleton); no `sidebar.tsx`/router changes in diff (0 frontend files touched) |
| `/evidence`, `/research/factor-lab` | OK — pre-existing homes, no new route | `runs/goal-session-ops-hardening/state/blueprint.md:384`; same — no frontend diff |
| `/scanner-runs` | OK — pre-existing home, no new route | `runs/goal-session-ops-hardening/state/blueprint.md:384`; same — no frontend diff |

No new page, no new nav entry, no parallel shell, no duplicate home — nothing to check beyond
confirming the diff truly touches no frontend/nav files, which it does not.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. This iteration's product diff is backend-only, targets exactly the one already-registered
  Data Contract row named in its own spec, reuses the SAME canonical modules/table/endpoints
  end-to-end, and the blueprint's Data Contract + IA sections were updated in the same commit-set to
  document it — model behavior for a decomposer to repeat.
