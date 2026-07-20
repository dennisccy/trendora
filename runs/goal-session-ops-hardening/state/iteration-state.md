# Iteration State — ops-hardening

**After iteration:** 5 · **Date:** 2026-07-20 · **Verdict:** CONTINUE

## Journeys

2 passing (J-01 J-03) · 2 unknown (J-04 J-05 — not replayed this cycle) · 1 failing (J-06) — 5 total

## Active blockers

- **J-06 (dev-owned):** Dashboard `/api/indexes?full=true` = 1.68–2.19s in a real browser (3/3) vs ≤1.5s
  budget — browser HTTP/1.1 6-conn/origin queuing (curl 0.79–0.95s in-budget). Fix via HTTP/2 on the
  uvicorn launcher, coalesce the Dashboard's 10-13 on-load calls, OR re-commit a browser-realistic budget
  in `reports/perf-budgets.md` (fold in `/api/data/availability`, same class ~2.9–3.0s).
- **Regression evidence (dev-owned):** J-01 golden-script step-6 proxy ("2026-05-15" on `/scanner-runs`)
  is stale vs the now-750-row unpaginated run list — fix `runs/goal-session-ops-hardening/journey-scripts/J-01.json`;
  J-04/J-05 golden scripts were skipped this cycle — run them to move J-04/J-05 out of `unknown`.

## Last 2 verdicts

- iter 5: CONTINUE — J-06 backend fix correct but still fails TC-02 (Dashboard browser-budget); J-01 replay
  miss is a proven-stale proxy, not a regression; J-04/J-05 unreplayed.
- iter 4: CONTINUE — J-05 partial→passing (B3+F1 fixed & live-verified); J-06 deferred.

## Do not redo

- `ForwardAggregateCache` fix for `GET /api/backtest` (34.77s→0.138s, ~252×, byte-identical, honest
  cold-miss, correct dataset_version invalidation) — verified by review/QA/audit. Lives in
  `forward_testing.py forward_aggregates_cached` + `models.py ForwardAggregateCache` + `_refresh_ingest_aggregates` warm block. Shippable as-is.
- J-06 backend audit (TC-13): all 11 endpoints traced; `/api/runs` N+1 measured in-budget, left unfixed by design.
- B3/F1 readiness + heartbeat fixes (iter-4) — settled; `readiness.py`/`health-badge.tsx` out of scope.
- Before merge run `pytest tests/test_api_backtest.py tests/test_mcp_window.py -v` (loaded_engine suite unrun this cycle).
- Closure-gate: J-05 + J-06 `demo.sh --session-live` walkthroughs still owed before GOAL_ACHIEVED.
