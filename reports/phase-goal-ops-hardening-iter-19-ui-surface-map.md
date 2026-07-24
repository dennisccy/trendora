# Phase goal-ops-hardening-iter-19 — UI Surface Map

**Phase:** goal-ops-hardening-iter-19
**Date:** 2026-07-24
**Written by:** ui-impact-analyst

---

## Context: no frontend files changed, but one existing page is behaviorally affected

Zero files under `apps/frontend/` appear in this iteration's diff (confirmed via `git status --short`
and `git diff --stat -- apps/frontend/`, both empty for that directory). The only product/test files
touched are `apps/backend/app/engine/forward_testing.py` (modified — the un-elapsed-horizon
short-circuit, plus a retained column-projected existence read and skip-commit guard from two earlier
attempts this same iteration), `apps/backend/app/api/backtest.py` and `apps/backend/app/mcp/tools.py`
(both modified, but ONLY to capture a return value already computed and add one field to an internal log
line — confirmed by direct diff read: the actual returned response dict, `**card`, is untouched in both
files), two backend test files (new tests only), and `reports/perf-budgets.md` (a non-UI reporting
artifact). `backfill_run_forward_returns` is the sole function behind both `GET /api/backtest` (already
consumed by `apps/frontend/app/backtest/page.tsx` via `apps/frontend/lib/api.ts`'s `fetchBacktest`) and
the MCP `query_backtest` tool. Because this iteration's entire purpose is eliminating a real,
concurrency-triggered multi-second latency problem on that existing page, the row below captures the
resulting behavior change, per this dispatch's PUMP NOTE not to suppress this report on account of
`Frontend Present: no`.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/backtest` | Page load / data-fetch timing (`BacktestPage` in `apps/frontend/app/backtest/page.tsx`, whose `fetchBacktest` call hits `GET /api/backtest`) | Changed behavior (performance/latency only — no visual, label, or data change) | `backfill_run_forward_returns` (`apps/backend/app/engine/forward_testing.py`), called unconditionally on every request by this page's own API route, was re-attempting ~550 wasted price-history lookups per request for forward-return time windows that have not elapsed yet (the default "latest" view has ZERO elapsed windows, so it paid the full waste on every single load). The fix short-circuits those un-elapsed lookups before they start. | From a terminal (not requiring a browser), run 6 concurrent requests against the running backend and time each: `for i in 1 2 3 4 5 6; do curl -s -o /dev/null -w '%{time_total}s\n' http://localhost:8255/api/backtest & done; wait`. Confirm all 6 complete in well under 1 second each (the operator's post-fix measurement recorded a 112 ms mean / 302 ms max across 4,793 such requests, versus a 1083 ms mean / ~1.3 s max before this iteration on the identical protocol). Then tail the newest 6 `backtest_timing` lines in `logs/backend.log` and confirm `backfill_forward_returns_ms` reads as a small number (roughly 1-15 ms) rather than several hundred, with `write_taken=False` on each (all 6 hit the already-backfilled latest run, so no write is taken). |
| `/backtest` | Evidence section content (`ScorecardSection`, the by-horizon table, `RefreshingEvidenceBanner`/`EmptyState` routing in `BacktestResults`) | Regression guard — confirm NO change (byte-identity, AG-3) | The same function's control flow changed internally; this row exists to verify the fix did not alter what is actually displayed, since the whole point of the fix is that it must not. | Capture `curl -s http://localhost:8255/api/backtest \| python3 -m json.tool` once, then reload `/backtest` in a browser at its default (latest) as-of and visually compare against a capture taken before this iteration's backend restart (or against the developer's own before/after fixture values in `docs/handoffs/goal-ops-hardening-iter-19-dev.md`, TC-5). Confirm every field is identical: the scorecard numbers, `evidence_status`, `evidence_generated_at`, `evidence_asof`, `evidence_by_horizon` entries, and the return-attribution leadership lists — zero differences, not even in horizons that were skipped by the new short-circuit (those horizons legitimately had no stored value before this fix either, so their display is unchanged: still "not yet available"). |

<!-- Change Type key used above: Changed behavior -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/mcp/tools.py` — `query_backtest` (the MCP tool a connected AI assistant would call,
  not a page in this Next.js frontend) received the identical fix and the identical `write_taken` log
  field, and benefits from the exact same latency improvement as `/backtest` above — but it renders on no
  page in this project's browser UI, so no browser UI surface is affected by this file (see "Not Visible
  Yet" in the companion user-visible-changes report for this distinction).
- `apps/backend/app/api/backtest.py` / `apps/backend/app/mcp/tools.py` — the new `write_taken` field
  appended to the existing `backtest_timing`/`query_backtest_timing` log lines (`logs/backend.log`) — an
  operator-facing diagnostic detail only, confirmed (by direct diff read) never part of either file's
  returned response dict. No UI surface.
- `apps/backend/app/engine/forward_testing.py` — the actual fix (the `observable_days`/
  `observable_horizons` short-circuit, plus the retained column-projected existence read and
  skip-commit guard from this same iteration's two earlier, superseded attempts). No UI surface of its
  own — its only user-visible trace is the `/backtest` row above, which flows through the one unchanged
  call site (`GET /api/backtest`).
- `apps/backend/tests/test_forward_testing_serving_split.py`,
  `apps/backend/tests/test_forward_testing_concurrency.py` — new/extended unit and concurrency tests
  (TC-1 through TC-5 plus the horizon-short-circuit and partial-backfill tests). Test coverage only, no
  UI surface.
- `reports/perf-budgets.md` — gained the iter-19 dated sections recording all three attempts' live
  re-measurements, including the decisive post-fix TC-6 result. The project's performance-budget ledger,
  documented elsewhere (`blueprint.md`) as "not a UI page" — no in-product surface renders this file. No
  UI impact.
- `apps/backend/app/engine/data_manager.py` — confirmed byte-unchanged (absent from `git status`); its
  ingest-finalize call site (`_persist`, line ~2918) calls the same `backfill_run_forward_returns`
  function and is exercised by the same guard automatically, but has zero diff of its own this iteration.
  Listed for completeness since it is the other call site the fix's safety depends on.
- `docs/handoffs/goal-ops-hardening-iter-19-dev.md`,
  `reports/phase-goal-ops-hardening-iter-19-implementation-summary.md` — pipeline process documents. No
  UI impact.
- `runs/goal-ops-hardening-iter-19/` (plan.md, tc6-backtest-poll.csv, tc6-final-poll.csv, tc6-probe.csv,
  review-packet.md, status.json) — pipeline run-state and raw measurement artifacts. No UI impact.

---

## Summary

- **Frontend surfaces changed:** 0 (no `apps/frontend/` file appears in the diff)
- **UI surfaces with behavior impact via backend change:** 1 page (`/backtest`), 2 surface-map rows
  (load-time improvement + byte-identity regression guard)
- **New pages/routes:** 0
- **Modified components:** 0 (no component source edited — the effect above is a runtime/timing
  consequence of already-existing rendering code calling an already-existing, now-faster endpoint)
- **Navigation changes:** no
- **Backend-only changes:** 8 (`mcp/tools.py`'s MCP-tool-specific angle, the `write_taken` log field
  across both API/MCP files, `forward_testing.py` itself, 2 test files, `perf-budgets.md`,
  `data_manager.py` [confirmed unchanged], plus the dev-handoff/implementation-summary docs and the
  `runs/` run-state directory)
