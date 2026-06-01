# goal-i_can_see_the_wealthy_future_forever-iter-0 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-0
**Date:** 2026-05-31
**Agent:** developer
**Mode:** baseline (verify-only) — INITIAL BUILD
**Status:** complete (intentional no-op + foundation verification)

## Summary

This is the iteration-0 **baseline assessment**, not a feature delivery. Per the iter spec's
IN SCOPE section, the baseline writes **no backend code, no frontend code, no config, no seed
data, and no tests** — the developer code step is an **intentional no-op**. Unlike a greenfield
baseline, the Trendora product **already exists** in this tree (built to GOAL_ACHIEVED by the
prior session `i_can_see_the_wealthy_future` at iter 12), so the value of this step is to
**verify the foundation** the downstream browser-QA depends on: the backend boots offline on the
committed seed, the frontend builds + typechecks, and the backend unit suite passes — and to
record an evidence-based per-journey expectation (file-scan + unit signals) for the
browser-qa-agent and goal-evaluator.

I read the iter spec, `docs/goal.md` (Must-have journeys + Anti-goals), and
`.claude/project-template.md`, then ran the verify-only activities below. **No source, config,
seed, or test file was created or modified.**

## What Was Built
- Nothing. This iteration is a measurement-only baseline; the product does not change.

## Files Changed
- None. No source, config, seed, or test files were created or modified by the developer step.
- (The coherence blueprint `runs/goal-session-i_can_see_the_wealthy_future_forever/state/blueprint.md`
  already exists — drafted by the goal-decomposer at baseline. It is **not** a developer artifact
  and is left untouched, awaiting human review/approval before iter-1.)
- Only this dev handoff and `runs/goal-i_can_see_the_wealthy_future_forever-iter-0/status.json`
  (pipeline artifacts) were written — neither is product code.

## Verification activities (no code changes)

### 1. Backend boots offline on the committed seed — PASS
- `CHAIN_BACKEND_PORT=8835 bash scripts/start-backend.sh` — started cleanly, no errors in the
  boot log, **no network calls and no API keys** (default `seed` provider).
- `GET /api/health` →
  `{"status":"ok","db_ok":true,"provider":"seed","last_run_date":null,"seed_latest_date":"2026-05-28","symbol_count":158}`
  — status ok, DB ok, provider = `seed` (offline), 158 symbols, latest seed bar 2026-05-28.
- Sanity-checked one canonical read endpoint: `GET /api/dashboard` returned a regime
  (`Risk-on`, score 74.32) with its named component breakdown — the snapshot-served read path
  works end to end.
- Backend was stopped **by port 8835** afterward (machine rule: never broad-`pkill` on this
  shared host); port confirmed free.

### 2. Frontend builds (compile + typecheck) — PASS
- `cd apps/frontend && npm run build` → **✓ Compiled successfully**, "Checking validity of
  types" passed, exit code 0.
- 12 routes generated: `/`, `/backtest`, `/methodology`, `/scanner-runs`,
  `/scanner-runs/[runId]`, `/sectors`, `/stocks`, `/stocks/[ticker]`, `/system-health`,
  `/themes`, `/watchlist`, `/_not-found`.
- **No `/data` route was generated** — corroborating that J-17 (Data Manager) is not implemented.

### 3. Backend unit suite — PASS (248 passed / 0 failed)
- Command (from project-template.md): `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
- **Result: `248 passed in 878.24s (0:14:38)` — 0 failed, 0 errors, 0 skipped.**
- Baseline-critical guarantees explicitly verified green:
  - **No-lookahead:** `test_scanner.py::test_run_scan_no_lookahead`,
    `test_scoring.py::test_asof_bounds_the_computation_no_lookahead`,
    `test_scoring.py::test_invalidation_na_on_short_history_is_honest_never_fabricated`.
  - **Snapshot immutability:** `test_scanner.py::test_run_scan_idempotent_and_immutable`,
    `test_scanner.py::test_runs_are_distinct_as_of_snapshots`,
    `test_watchlist_persistence.py::test_persisted_watchlist_does_not_create_snapshot_rows`.
  - **Risk-Off gates Actionable:** `test_setups.py::test_risk_off_regime_gates_actionable_to_zero`,
    `test_setups.py::test_risk_off_gate_holds_across_all_score_combinations`,
    `test_scanner.py::test_risk_off_run_vcp_flagged_rows_stay_watchlist_not_actionable`.
  - **VCP is a pattern, not a status:** `test_scoring.py::test_vcp_is_a_pattern_not_a_status`,
    `test_scoring.py::test_vcp_block_rides_each_row`.
  - **Single source of truth / no recompute:**
    `test_scoring.py::test_invalidation_and_themes_ride_on_the_shared_row_for_list_and_detail`,
    `test_scanner.py::test_latest_run_faithful_to_live_computation`.
  - **No magic numbers / honest NA:** `test_no_magic_numbers.py` (full file),
    `test_scoring.py::test_gap_climax_is_na_and_excluded_never_fabricated`,
    seed risk-on **and** risk-off stretch integrity (`test_seed_integrity.py`).
- I did **not** modify any test to make it pass (none failed).

## Structural file-scan signal for the three expected gaps (J-17 / J-18 / J-19)
The spec NOTES flag these explicitly; confirmed by read-only inspection (recorded, **not** fixed):

- **J-17 (Data Manager) — NOT IMPLEMENTED.** No `apps/frontend/app/data` page; no
  `apps/backend/app/api/data.py` router (routers present: backtest, dashboard, health,
  methodology, runs, sectors, stocks, system_health, themes, watchlist); no `data_manager`
  engine module; no `data`/`data_manager` section in `config.yaml`.
- **J-18 (one date control / no duplicate) — EXPECTED FAIL.** `apps/frontend/app/backtest/page.tsx`
  carries **its own** date picker independent of the global switcher — line 53 comment:
  *"The page's OWN date picker (independent of the global top-bar switcher)"*; a second
  `useState<string[]>` date state (line 55) and a local `BacktestDatePicker` component
  (lines 112, 175–193). The anti-goal **"Exactly one date selector"** requires Backtest to read
  the single global as-of control and expose **no** picker of its own. (A global
  `components/asof-switcher.tsx` + `components/asof-provider.tsx` do exist — good for J-13 — but
  Backtest does not consume them.)
- **J-19 (return attribution) — NOT IMPLEMENTED.** No attribution / contributor / detractor /
  rank-band / hit-rate code in `apps/backend/app` or the frontend `app/` pages.

## Per-journey expectation (developer signal — NOT the authoritative verdict)
The browser-qa-agent records the authoritative pass / partial / fail with evidence; the
goal-evaluator alone marks journey status. Journeys assert **relational/structural** properties
(same value in two places, buckets ordered, zero Actionable in Risk-Off, a number renders,
filters change rows) — not exact score numbers — so this expectation is grounded in surface
presence + unit-suite evidence, not score values.

| Journey | Route(s) | Supporting evidence | Dev expectation |
|---|---|---|---|
| J-01 Daily dashboard | `/` | `/api/dashboard` served regime+components live; `test_regime`, `test_api_engine` green | likely PASS — **verify** the last-scan timestamp renders (`/api/health` showed `last_run_date: null` on a fresh DB; the dashboard still served data, so bootstrap is lazy) |
| J-02 Stock Leaderboard + filters | `/stocks` | `test_scoring` (3 bucketed explainable scores), `test_setups` | likely PASS |
| J-03 Theme Leaderboard | `/themes` | `test_themes` (ranked desc, basket return, breadth) | likely PASS |
| J-04 Sector/industry Leaderboard | `/sectors` | `test_sectors` (ranked, SPY excluded, RS-vs-SPY) | likely PASS |
| J-05 Stock Detail (explainable) | `/stocks/[ticker]` | `test_scoring` (components, canonical invalidation), price chart present | likely PASS |
| J-06 Score consistency | `/stocks` ↔ `/stocks/[ticker]` | `test_scoring::..._shared_row_for_list_and_detail` | likely PASS |
| J-07 Risk-Off suppresses Actionable | `/scanner-runs/[runId]` | `test_setups` risk-off gate (all combos), `test_scanner` risk-off zero-Actionable | likely PASS |
| J-08 Immutable run history | `/scanner-runs` | `test_scanner` idempotent_and_immutable, distinct_as_of_snapshots | likely PASS |
| J-09 System Health evidence | `/system-health` | `test_forward_testing`, `test_api_system_health` | likely PASS |
| J-10 Control-group honesty | `/system-health` | `test_forward_testing` (control groups) | likely PASS |
| J-11 Watchlist persistence | `/watchlist` | `test_watchlist_persistence::..._survives_engine_restart` | likely PASS (browser must re-test after a real backend restart) |
| J-12 Glossary + inline | `/methodology` + `/stocks` badges | `test_methodology`, `test_api_methodology` | likely PASS |
| J-13 Global as-of switcher | `/` + `/stocks`/`/themes`/`/sectors` | `test_asof_resolver`; `asof-switcher.tsx` + `asof-provider.tsx` present | likely PASS |
| J-14 Backtest scorecard (NA short) | `/backtest` | `test_backtest_scorecard`, `test_api_backtest`; page shows honest NA empty-state | likely PASS |
| J-15 Fast loads from snapshots | `/stocks` + reload | `test_prices_asof`, snapshot-served reads | likely PASS — browser confirms warm load < ~1.5 s |
| J-16 VCP detected/explained/filterable/forward-tested | `/stocks`, `/methodology`, `/system-health` | `test_patterns`, `test_scoring` vcp_block / vcp_is_a_pattern_not_a_status | likely PASS |
| **J-17 Grow dataset (Data Manager)** | `/data` | **no surfaces exist** (page/router/engine/config all absent) | **FAIL — not implemented** |
| **J-18 One date control (no duplicate)** | `/backtest` | backtest page keeps its **own** `BacktestDatePicker` + date state | **FAIL — page-local date picker violates "exactly one date selector"** |
| **J-19 Return attribution** | `/system-health` + `/backtest` | **no attribution code** (per-stock contributors / by-sector / by-rank-band / hit-rate all absent) | **FAIL — not implemented** |

Net expectation: **J-01 … J-16 likely PASS, J-17 / J-18 / J-19 the real gaps** for later
iterations — consistent with the spec's baseline file-scan note and commit `043a456`'s claim
("Data Manager, unified as-of date control, and return attribution") whose Data Manager / date
unification / attribution surfaces are **absent** from the current tree.

## Anti-goal check
No anti-goal violation could be introduced — **no code changed**. The pre-existing tree's
critical anti-goals (no-lookahead, snapshot immutability, Risk-Off gating, VCP-as-flag, no-magic-
numbers, single-source-of-truth, honest-NA) are all backed by **green** unit tests this run
(see §3). The J-18 page-local date picker is a pre-existing **gap to fix in a later iteration**,
not a regression introduced here.

## Known Issues / observations for downstream steps
1. **`last_run_date: null` on a fresh DB at `/api/health`** while `/api/dashboard` still serves a
   regime — bootstrap of persisted runs appears lazy/first-view. Browser-QA should confirm
   J-01's "last-scan timestamp" and J-08's "≥2 dated runs" actually render in the UI (they may
   require the bootstrap to have run). Not a code change for this step.
2. **J-17 / J-18 / J-19 are confirmed gaps** (above) — record as fail; do not attempt to fix in
   the baseline.
3. The backend unit suite is slow (~14.6 min) due to real walk-forward/scanner computation over
   the seed — expected, not a defect; relevant for CI time budgeting in later iterations.
4. Browser-QA must run the **19** journeys against a freshly started backend+frontend (ports
   8835 / 3835) and is the authoritative source for pass/partial/fail with evidence.

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **248 passed, 0 failed (878.24s)**. Frontend: `cd apps/frontend && npm run build` — **green** (compiled + typechecked, exit 0).
