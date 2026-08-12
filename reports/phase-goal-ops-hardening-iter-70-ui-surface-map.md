# Phase goal-ops-hardening-iter-70 — UI Surface Map

**Status:** N/A — Backend-only phase (Frontend Present: no)

No UI surfaces affected.

## Basis for this classification

All files changed in this iteration are backend-only (see
`docs/handoffs/goal-ops-hardening-iter-70-dev.md` Files Changed):

| File | Classification |
|------|-----------------|
| `apps/backend/app/engine/readiness.py` | backend-internal — background-refresh cache producer, no HTTP-facing shape change |
| `apps/backend/app/api/health.py` | backend-api — existing `GET /api/health` endpoint; response shape byte-identical to before (same field names/types/values), only the compute source (cache vs. per-request compute) changed |
| `apps/backend/main.py` | backend-internal — starts/stops the new daemon thread in `lifespan` |
| `apps/backend/app/engine/data_manager.py` | backend-internal — immediate-refresh trigger call at end of `_refresh_ingest_aggregates` |
| `config.yaml` | config — new `readiness.refresh_interval_seconds` knob, internal tuning value, not surfaced in any UI |
| `apps/backend/app/config.py` | config — `ReadinessCfg` schema extension for the above knob |
| `apps/backend/tests/test_readiness.py`, `test_health.py`, `test_health_watchdog.py`, `test_data_manager.py` | backend-internal — test files, no UI coupling |
| `reports/perf-budgets.md` | config/reporting artifact — not a UI surface |

`GET /api/health` is classified backend-api-unchanged rather than a new UI-affecting
backend-api change: the frontend already consumes this endpoint (`HealthBadge`,
`PreflightBanner`, `/data`'s `BackgroundComputePanel`), and per both the plan's "UI Evolution"
section and the phase spec's "UI surface changes: None," the response body is byte-identical
in field names, types, and values — confirmed by the dev handoff's own fixture-backed
byte-identity test (`test_health.py`) and the TC-2/TC-7 test coverage. There is no behavior
for a UI-impact analysis to map: no new field, no removed field, no changed value, no changed
status code, no changed latency-visible-to-user threshold under normal conditions. The only
externally observable effect is that `GET /api/health` remains responsive (instead of
occasionally slow or non-answering) during a heavy background warm — an availability property,
not a new or changed UI surface.

No route, page, component, modal, form, chart, or table in `apps/frontend/*` was touched, and
none requires a code change as a consequence of this iteration.
