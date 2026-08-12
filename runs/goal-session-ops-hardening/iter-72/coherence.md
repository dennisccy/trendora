# Iteration 72 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-72
**Date:** 2026-08-13
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

This iteration is backend-only (`Frontend Present: no`) and touches exactly one registered Data
Contract row — "Backend readiness / boot phase + preflight verdict"
(`app.engine.readiness.compute_readiness`/`compute_preflight`, `GET /api/health`) — plus one
infrastructure change (DB connection-pool sizing) and one test-only fault-injection hook reuse. No
new page, endpoint, or UI surface is introduced.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Backend readiness / preflight verdict (`readiness`, `preflight`, `stale_for_s`, `background_compute`) | OK | `apps/backend/app/engine/readiness.py:558-666` (removed the iter-71 synchronous-fallback branch in `get_readiness_and_preflight`; added a post-lock recheck in `_tick_and_cache`); `apps/backend/app/api/health.py:60-76` (docstring updated, no new field, no second endpoint) — same two producers, same one endpoint as the registered row |
| `readiness.max_stale_intervals` config knob | OK (now unconsumed, not deleted) | `apps/backend/app/config.py:589-601`, `config.yaml:1353` — the field stays typed/validated for a possible future consumer; its old comment claiming a live synchronous fallback was corrected in the SAME diff, matching the blueprint's iter-72 update paragraph |
| DB connection pool sizing (`database.pool_size`/`max_overflow`) | OK — infra config, not a displayed value | `config.yaml:118-125` (10+20→24+44), `apps/backend/app/config.py:1993-2011` (`DatabaseCfg` defaults raised to match), `apps/backend/app/config.py:2777-2794` (new `Config._db_pool_covers_server_concurrency` boot validator) — no UI-facing value computed or served here |
| `scripts/dev.sh` backend-subshell uvicorn flags + persistent logfile | OK — launcher/operational scaffolding, not a Data Contract row (mirrors the iter-9 precedent named in the blueprint) | `incredible_auto_dev/scripts/dev.sh` (== `scripts/dev.sh`, a symlink to the same file) lines ~49-79; frontend subshell byte-unchanged |
| `TRENDORA_FAULT_INJECT_MEMORY_ERROR=data_overview_endpoint` test hook | OK — reuses the existing registered fault-injection mechanism, new site name only, no new computing module | `apps/backend/app/engine/data_manager.py:3468-3480` (`_FAULT_INJECT_SITES` frozenset gains one member); `apps/backend/app/api/data.py:109-119` (single call to the existing `data_manager._fault_inject_memory_error`); precedent named in the blueprint's Membership-timeline row (iter-52's `spawned_backend_fault_injected` pattern) |

No new function reimplements `compute_readiness`/`compute_preflight`, no new UI surface fetches
readiness/preflight from a second endpoint, and no genuinely new displayed value appears
unregistered. `stale_for_s` stays un-rendered in the UI this iteration, consistent with the
blueprint's carried note.

## Information Architecture check

No new page, route, nav entry, or frontend file is touched (`git diff --stat` against the iter-72
diff shows zero files under `apps/frontend/`). The iteration spec's own "UI surface changes: None"
and "Blueprint conformance: No new pages or nav entries" match the diff.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new UI surface this iteration) | OK | `apps/frontend/components/sidebar.tsx` unchanged (not in diff); confirmed via `reports/phase-goal-ops-hardening-iter-72-ui-surface-map.md` ("Status: N/A — Backend-only phase") |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The audit report (`docs/handoffs/goal-ops-hardening-iter-72-audit.md`) already flags functional/
  evidence-completeness gaps for this iteration (missing TC-10 screenshot, an omitted `/api/backtest`
  failure count in the perf addendum, and the removal of iter-71's never-serve-arbitrarily-stale
  bound with no UI disclosure/watchdog). These are QA/audit-class findings, not coherence violations
  — no duplicate computation, no non-canonical source, and no navigation/IA defect is implicated by
  any of them — so they are noted here for completeness but do not affect this verdict.
- `readiness.max_stale_intervals` is now an unconsumed config knob (kept typed/validated per the
  developer's own note in `apps/backend/app/config.py:592-597` and `config.yaml:1353` for a possible
  future consumer). Not a coherence defect today, but worth flagging for a future iteration to either
  reintroduce a consumer or formally retire the field if it stays permanently dead.
