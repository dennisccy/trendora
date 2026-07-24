# Iteration 19 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-19
**Date:** 2026-07-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Method note

No bounded `iter-diff.md` existed for this iteration, so the full noise-excluded
`git diff 13459fa5f4ef7598783e1cf7a0d252b5930cac6d` was read directly (5 files, 786
insertions / 15 deletions: `apps/backend/app/api/backtest.py`,
`apps/backend/app/engine/forward_testing.py`, `apps/backend/app/mcp/tools.py`, and two test
files). The excluded-paths `--stat` showed only harness bookkeeping (`runs/*`, `reports/*`,
iter-18 demo PNGs, `reports/perf-budgets.md`) — no lockfile changes. All three pump-note claims
were independently re-verified against the diff and current file contents, not taken on trust.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Regime score, market phase, realized forward-returns — `backfill_run_forward_returns` (realized-forward-returns sub-mechanism) | OK | `apps/backend/app/engine/forward_testing.py:1372` (same function, same signature); internal-only control-flow change (`observable_days`/`observable_horizons` short-circuit at :1436-1467, `if inserted:` commit guard at :1502). Both request-path callers unchanged in call shape: `apps/backend/app/api/backtest.py:151`, `apps/backend/app/mcp/tools.py:271` — same function, same args, unconditional; only the pre-existing `rows_inserted` return field (already part of the function's return dict before this iteration) is now captured to derive a log-only `write_taken` boolean. Confirmed by reading both full return statements: `backtest.py:198-205` and `mcp/tools.py:300-307` both still return exactly `{**card, is_latest, evidence_by_horizon, evidence_status, evidence_generated_at, evidence_asof}` — byte-identical response shape, `write_taken`/`backfill_result` never included. |
| Regime score, market phase, realized forward-returns — `compute_forward_aggregates`/`ForwardAggregateCache` sub-mechanism | OK (untouched) | `grep -n "compute_forward_aggregates" ` on the `forward_testing.py` diff returns zero hits — the iter-14/16/17 compute-vs-serve split is not touched by this diff, confirming the spec's own "do not conflate" claim. |
| Page performance budgets | OK | `reports/perf-budgets.md` diff is pure append (111 insertions, 0 deletions, `git diff --stat` confirmed) — same single canonical artifact, no second budgets file created. |
| `write_taken` (new log field) | Not a Data Contract value — no WARN needed | Purely an operational `logger.info` field on `backtest_timing`/`query_backtest_timing` (`backtest.py:33`, `mcp/tools.py:86`), never merged into either endpoint's response dict (verified above). The skill's Data Contract concerns displayed/served values; a log line is explicitly out of that scope, consistent with the same carve-out already applied to `ensure_loop_ms` et al. in iter-18. |

No new function, class, or route was added anywhere in the diff (`grep -nE '^\+.*def |^\+.*class |^\+.*@router\.'` over the three production files returns zero matches) — the fix is a control-flow change inside the one existing, already-canonical function. `backfill_run_forward_returns` still has exactly three call sites in production code (`api/backtest.py`, `mcp/tools.py`, `data_manager.py:2918`), and `data_manager.py` itself has zero diff this iteration (confirmed absent from `git status`/`git diff --stat`) — its ingest-time call site is unedited and automatically inherits the guard, exactly as the spec claims.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/backtest` (existing route, unchanged) | OK | Zero files under `apps/frontend/` appear anywhere in the diff (`git status --short` and `git diff --stat` both empty for that directory) — independently confirmed by the ui-impact-analyst's surface map (`reports/phase-goal-ops-hardening-iter-19-ui-surface-map.md`: "Frontend surfaces changed: 0 ... New pages/routes: 0 ... Navigation changes: no"). No nav/sidebar edit to inspect because no new route was introduced; `/backtest` keeps its pre-existing canonical home already registered in `blueprint.md`'s IA table for J-06/J-07/J-08. |

No new page, route, feature, or nav entry exists in this iteration — Part B's checks (no-nav-path, reachability, duplicate-home, parallel-shell) have nothing new to evaluate against.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. `blueprint.md`'s own iter-19 comment-block paragraph and the Notes-cell append to the
"Regime score, market phase, realized forward-returns" row accurately describe what the diff
actually does — no correction needed to the blueprint itself.
