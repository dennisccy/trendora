# Iteration 9 — Coherence Audit

**Iteration:** goal-market-compass-iter-9
**Date:** 2026-08-23
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Iteration 9 is a raw-layer maintenance iteration (J-10 population-scale recovery, maintenance
isolation required — no application services started, no browser/replay lane, no frontend work).
Confirmed by diff inspection: the only product files touched are
`apps/backend/app/data_providers/{base,stooq_provider,yahoo_provider}.py`,
`apps/backend/app/engine/j10_recovery.py`, `apps/backend/tests/{test_j10_recovery,test_provider_clients}.py`,
and the new committed driver `apps/backend/scripts/run_j10_population_recovery.py`. None of these
modules appear anywhere in the blueprint's Data Contract table. Zero hunks touch
`apps/backend/app/engine/compass.py`, `dashboard`, `stocks`, `sectors`, `themes`, `evidence`,
`data_manager.py`, `runs.py`, the readiness module, or any file under `apps/backend/app/api/` —
i.e. every canonical computing module and every canonical endpoint listed in the blueprint is
byte-unchanged this iteration. `git diff <snapshot> --stat -- apps/backend/app/api/ apps/backend/app/models.py apps/backend/app/db.py` returned empty.

The new functions added (`_check_fetch_provider_source_matches`, `_run_gated_recovery_core`,
`run_gated_recovery` (refactored), `run_gated_population_recovery`) all live inside
`app.engine.j10_recovery`, operate only on raw `daily_prices` rows via the pre-existing
`run_bounded_recovery_fetch` -> `data_manager.run_data_job` write path (no second insert path —
confirmed in the diff's own docstrings and by grep: no new `def` outside `j10_recovery.py` and the
driver script), and touch no value the blueprint registers as a displayed/served concept. This
matches the blueprint's own framing: "`daily_prices` raw rows are upstream data, not a blueprint
Data-Contract (served-value) entry."

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Next-session manifest (CONTENT + FREEZE/INTEGRITY) | OK — untouched | `app/engine/compass.py` not in diff |
| Engine identity | OK — untouched | `app/engine/engine_identity.py` not in diff |
| Stock sector label | OK — untouched | `app/engine/scoring.py` not in diff |
| Regime label + score / Breadth | OK — untouched | `app/api/dashboard*` not in diff |
| Market phase / severity / P(bear) | OK — untouched | `app/api/market_phase*` not in diff |
| Sector / theme scores + ranks | OK — untouched | `app/engine/sectors.py`, `themes.py` not in diff |
| Stock leadership/entry/risk scores | OK — untouched | `app/engine/scoring.py`/`setups*` not in diff |
| Evidence / certified-claim ledger | OK — untouched | `app/engine/evidence*` not in diff |
| Coverage payload | OK — untouched | `app/engine/data_manager.py` not in diff |
| Run summary / scanner runs list | OK — untouched | `app/api/runs.py` not in diff |
| Readiness / preflight state | OK — untouched | not in diff |
| Raw `daily_prices` bars (upstream, unregistered by design) | OK — read/write path unchanged | `apps/backend/app/engine/j10_recovery.py:735-806` (still uses the sole existing `run_bounded_recovery_fetch` -> `data_manager.run_data_job` insert path; no new insert path added) |

## Information Architecture check

No new page/route/feature. `Frontend Present: no` in the iteration spec is corroborated by the
diff: `git diff <snapshot> --stat -- apps/frontend/` returned empty, and the ui-surface-map
(`reports/phase-goal-market-compass-iter-9-ui-surface-map.md`) records "Not mapped this iteration —
maintenance isolation," consistent with the contract (application services, browser QA, and the
deterministic replay lane are forbidden this iteration by the same `Maintenance isolation:
required` marker the coherence-auditor is instructed to honor). Nothing to check against the nav
skeleton.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no frontend change) | OK | n/a — `apps/frontend/` diff empty against snapshot `65caacf0e44fc56e7a9d8165c6190c0c730a41f8` |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The iteration spec's own "Blueprint conformance" and "Data-contract additions: None" fields are
  corroborated by the diff, not merely asserted — confirmed directly rather than taken on faith.
- The new `PriceProvider.source` `ClassVar` (`apps/backend/app/data_providers/base.py`) is a
  provider-identity label consumed only by the new J-10 mismatch guard
  (`_check_fetch_provider_source_matches`, `apps/backend/app/engine/j10_recovery.py`) — it is not a
  displayed value and does not overlap any Data Contract row; no action needed.
- This is a pure raw-layer/infra iteration with no frontend and no registered-value change, matching
  the skill's documented no-op case ("iteration changed no frontend and registered no values").
