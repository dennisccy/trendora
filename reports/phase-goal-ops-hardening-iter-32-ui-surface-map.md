# Phase goal-ops-hardening-iter-32 — UI Surface Map

**Status:** N/A — Backend-only phase (Frontend Present: no)

No UI surfaces affected.

## Basis for this classification

All five files changed this iteration are backend-only (per `docs/handoffs/goal-ops-hardening-iter-32-dev.md`):

| File | Classification (diff-to-ui-impact) | Why |
|------|-------------------------------------|-----|
| `apps/backend/app/engine/forward_testing.py` | backend-internal | Restructures `compute_forward_aggregates`'s in-memory accumulation (new `_ExactMeanAcc`, `_GroupAcc`, `_ControlGroupBuilder`, `_AttributionAccumulator` classes) so the unbounded `stock_obs` list is replaced by bounded per-chunk accumulators. The three existing call sites (`GET /api/backtest`, MCP `query_backtest`, ingest finalize warm) are byte-unchanged and the response payload is confirmed byte-identical by a 46-test oracle. No route, request/response schema, or status-code change. |
| `apps/backend/tests/test_forward_testing.py` | backend-internal | Test-only; updates three direct-call unit tests to the new `_attribution_slices(acc, cfg)` signature. |
| `apps/backend/tests/test_forward_testing_aggregates_streaming.py` | backend-internal | Test-only; extends the byte-identity oracle and adds a new accumulator-scaling test (TC-1). |
| `reports/perf-budgets.md` | config/engineering-artifact | New dated measurement section (VmPeak + margin); an internal ops-engineering record, not a rendered UI surface. |
| `docs/handoffs/goal-ops-hardening-iter-32-dev.md` | non-code | Documentation artifact. |

No `apps/frontend/` files were touched. `GET /api/backtest`'s served payload is confirmed byte-identical
before and after (byte-identity oracle + live warm re-read), so even the backend-api pathway that the
`/backtest` frontend page consumes carries zero observable change — same fields, same values, same shape.

There is therefore no route/page/component/table/chart/form to enumerate in a surface-map table, and no
"What to Test" UI action exists for this iteration.
