# Iteration 38 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-38
**Date:** 2026-07-30
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope of this iteration

Backend-only measurement/hardening iteration (spec: "Frontend Present: no", "New UI surface: None",
"Data-contract additions: None", "Blueprint conformance: No new page/nav"). Confirmed by:

- `git diff 8b1092fb...` (product code): only `apps/backend/app/engine/data_manager.py` and
  `apps/backend/tests/test_data_manager.py` changed (`--stat`: 39 / 90 lines respectively). No
  frontend file (`apps/frontend/**`) touched anywhere in the diff.
- `reports/phase-goal-ops-hardening-iter-38-ui-surface-map.md`: "Status: N/A — Backend-only phase,"
  every changed file classified backend-internal/config-docs, "No table rows are produced for this
  phase."
- `runs/goal-ops-hardening-iter-38/mem-drill/` and `.../j07-warm/` are throwaway-DB drill evidence
  (seed scripts, monitor CSVs, job-status JSON snapshots) — measurement scaffolding under `runs/`,
  not shipped product code; excluded from review scope per the harness convention and consistent
  with the ui-surface-map's own classification.
- `runs/goal-session-ops-hardening/journey-scripts/J-01.json` / `J-05.json` changes are golden
  regression-script fixture updates (added steps / retargeted dates), not product surfaces.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Backfill run-summary contract (`aggregates_refreshed`, etc.) | OK | `apps/backend/app/engine/data_manager.py:3111-3123` (`_do_backfill`, unchanged registered module) still the sole writer; new `TRENDORA_FORCE_LEGACY_BAR_CACHE` env-gate only toggles between the two pre-existing branches (stash shared cache vs. not) — no new computation, no new field |
| Job history / per-date exclusion reasons | OK | `data_manager.py:3350-3364` (`_refresh_ingest_aggregates`, unchanged registered module) gains only a `logger.warning(...)` liveness line; served via the SAME `GET /api/data` / `GET /api/data/jobs/{job_id}` / `_run_detail()` path — no second producer, no second endpoint |
| Membership timeline / research hot-key caches | OK | `data_manager.py:648-663` — `membership_timeline_cached`'s docstring corrected (audit B7) to describe the ALREADY-shipped `_excluded_counts_by_date` batching behavior; no code/logic change, no new derivation |
| Page performance budgets | OK | `reports/perf-budgets.md` — new dated sections (Iteration 38 two-arm VmPeak comparison, step-1 real-trigger warm, `read_pool()` re-read cost, "591"→"548" correction) all land in the ONE existing artifact; row is explicitly "N/A — a measurement artifact, not a served runtime value" in the blueprint, so no computing-module/endpoint constraint applies |

No new displayed value is introduced this iteration (spec confirms; diff confirms — no new API
field, no new frontend consumer).

## Information Architecture check

No new page/route/feature. `git diff --stat` shows zero files under `apps/frontend/`; the
ui-surface-map independently confirms "No UI surfaces affected." J-07's existing cross-cutting home
(global readiness badge + `/backtest`) and the Data Manager (`/data`) home are unchanged — nothing to
check against nav/sidebar files this iteration.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new route this iteration) | OK | n/a |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `_do_backfill` (`apps/backend/app/engine/data_manager.py:3121-3123`) now carries a
  `TRENDORA_FORCE_LEGACY_BAR_CACHE` environment-variable escape hatch whose only purpose, per its own
  comment, is to force the pre-iter-37 fallback path for this iteration's throwaway two-arm drill —
  "unset in every real deployment." This is not a Data Contract or IA violation (it toggles between
  two already-existing, already-registered branches, adds no second computation/endpoint, and is not
  exposed through any UI or public API), but a permanent test-only conditional living in a
  production hot path is worth a follow-up cleanup note for the decomposer/reviewer track rather than
  the coherence gate.
- The blueprint's iter-38 narrative paragraph (`runs/goal-session-ops-hardening/state/blueprint.md`,
  appended lines) accurately matches the diff's actual scope (drill-fixture fix, liveness log line,
  docstring/report corrections, two new tests) — no drift between what the blueprint claims and what
  shipped.
