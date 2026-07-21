# Iteration State — ops-hardening

**After iteration:** 6 · **Date:** 2026-07-21 · **Verdict:** CONTINUE

## Journeys

4 passing (J-01 J-03 J-04 J-05) · 1 partial (J-06) — 5 total. All product acceptance verified;
GOAL_ACHIEVED is blocked only by the closeout items below, not by any failing journey.

## Active blockers

- **Closure gate FAILED** (docs): `user-visible-changes.md` + `ui-surface-map.md` still assert a RETRACTED
  "/evidence 555.97s severe regression" — re-issue via ui-impact-analyst, then re-run phase-closure-auditor.
- **J-06 residual** (dev): `/evidence` first-view ~73s cold-miss on the live dev DB (audit B1) — warm the 7
  evidence `drawdown_expectations` keys at ingest finalize (`data_manager.py:3138` idiom); ~9.5s on seed.
- **Session gate** (dev | human): J-05 + J-06 `demo.sh ops-hardening --session-live` walkthroughs unproduced
  — produce them, or the human explicitly accepts the deferral.
- **Confirm** (dev): `pytest tests/test_api_backtest.py tests/test_mcp_window.py -v` to completion (25/0 on
  the initial build; QA's re-run was still in-progress on file).

## Last 2 verdicts

- iter 6: CONTINUE — J-06 latency genuinely fixed (both endpoints in budget 3/3 real-browser) + J-04/J-05 out
  of unknown, but closure FAILED and named GOAL_ACHIEVED-gate prerequisites remain.
- iter 5: CONTINUE — ForwardAggregateCache fixed /api/backtest, but J-06 Dashboard still >1.5s real-browser.

## Do not redo

- Dashboard/Data-Manager fetch-stagger fix (phase-cross-view-card.tsx 250ms; data/page.tsx 2500ms) — DONE,
  verified 3/3 real-browser, frontend-only, byte-identical payloads. Do NOT add a combined/second endpoint.
- J-01 golden-script step-6 rewrite ("no new snapshots" on /data) — DONE, deterministic replay PASS.
- J-04/J-05 freshly verified passing this iter — do not re-litigate their product acceptance.
- ForwardAggregateCache (/api/backtest ~252×), readiness.py B3/F1, max_range_days/snapshot_cadence — settled prior iters.
