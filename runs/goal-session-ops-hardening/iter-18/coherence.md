# Iteration 18 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-18
**Date:** 2026-07-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Regime score, market phase, realized forward-returns — `evidence_status`/`evidence_generated_at`/`evidence_asof`/`evidence_by_horizon` sub-values (blueprint row, `app.engine.forward_testing` → `GET /api/backtest` + MCP `query_backtest`) | OK | `apps/backend/app/engine/forward_testing.py:1174` (`resolved_forward_aggregate_evidence` — signature and role unchanged, still the ONLY resolver either endpoint calls for `is_latest=true`); `:1257` (`_serve` — the single formatter, unchanged, still the only function that turns a `horizon_map` into the served dict); `:1304-1354` (the widened-fallback candidate scan now runs in two queries — an identifying-columns-only scan at `:1304` that picks the winning `(asof_key, dataset_version)` via the new `_complete_version_identities` helper at `:1315`, then exactly one winner-only follow-up query at `:1341` that loads `payload_json` filtered to that one pair — the result is fed into the SAME `_serve()` at `:1354`, not a second formatter); `apps/backend/app/api/backtest.py:186-192` and `apps/backend/app/mcp/tools.py:291-297` (both return dicts are unchanged in shape — `**card` + `is_latest` + the four `evidence_*` fields — no new field leaked from the timing instrumentation). This is a query-shape refactor (fewer bytes read for discarded older candidates), not a new producer: only one code path computes/serves this value, exactly as before. `compute_forward_aggregates` itself is untouched (no hunk touches it) and remains the sole aggregation source, called only from `forward_aggregates_ingest_cached` (unchanged). |
| Per-request timing data (`total_ms`, `resolved_run_ms`, `backfill_forward_returns_ms`, `scorecard_ms`, `evidence_ms`, `ensure_loop_ms`) | N/A — not a Data Contract value | `apps/backend/app/api/backtest.py:86-113` (`_log_backtest_timing`) and `:182-185` (call site); `apps/backend/app/mcp/tools.py:207-232` (`_log_query_backtest_timing`) and `:287-290` (call site). These values are written ONLY to a `logging.getLogger("trendora.*").info(...)` call (destination: `logs/backend.log`) and are never included in either function's returned dict (confirmed by reading both full return statements, cited above) and never fetched, displayed, or recomputed by any UI surface (no frontend file changed this iteration — see IA check below). A log line is not a displayed/served value under this blueprint's Data Contract definition, so it needs no row — the same treatment the blueprint already gives `reports/perf-budgets.md` ("a measurement artifact, not a served runtime value"). Not even an "unregistered value" WARN applies. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK | `git diff --stat 87cfa36b694c3d32dcbb18a4c3c3363ba6534451 -- .` (noise-excluded) shows exactly 4 tracked files changed, all under `apps/backend/`: `app/api/backtest.py`, `app/engine/forward_testing.py`, `app/mcp/tools.py`, `tests/test_forward_testing_serving_split.py`; the bounded diff (`iter-diff.md`, 5 files shown in full, 0 truncated) additionally shows one new file, `apps/backend/tests/test_backtest_timing.py` — also backend-only. `git status --porcelain \| grep apps/frontend` returns zero matches. No sidebar/nav/router file (`apps/frontend/components/sidebar.tsx` or any `apps/frontend/*`) is touched, so there is nothing to check against `sidebar.tsx` — the existing `/backtest` nav entry and MCP `query_backtest` tool (both already registered in the blueprint's IA table for J-06/J-07/J-08) are the unchanged, sole homes for this row's value. The iter spec's own "Frontend Present: no" / "UI surface changes: None" fields (`docs/phases/goal-ops-hardening-iter-18.md`) match what the diff shows. The merged UI-test-results (`reports/phase-goal-ops-hardening-iter-18-ui-test-results.md`) SKIPPED its browser lanes (Chrome MCP infra outage, not a product defect per the dispatch note) but its non-browser signal — a raw `GET /backtest` returning HTTP 200 at the same byte count class as before, and `GET /api/backtest` still keyed under the same fields — is consistent with "no new/changed UI surface," and per the coherence-audit skill a live browser check is only an optional confirmation, never a dependency; static analysis (the diff/git-status check above) is authoritative and sufficient here. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. The two timing loggers intentionally use different names/message prefixes (`trendora.backtest`/`"backtest_timing"` vs. `trendora.mcp_backtest`/`"query_backtest_timing"`), matching the project's existing per-component `logging.getLogger("trendora.<component>")` convention (`main.py:45`, `data_manager.py:89`) and the iter spec's own TC-3 requirement (identical *field names*, not identical logger/prefix) — this is deliberate operational-log naming, not a displayed-label inconsistency, so it does not rise to a coherence advisory.
