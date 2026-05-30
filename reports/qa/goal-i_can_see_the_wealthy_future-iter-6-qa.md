**Verdict:** PASS

# goal-i_can_see_the_wealthy_future-iter-6 — QA Validation Report

**Phase:** goal-i_can_see_the_wealthy_future-iter-6
**Date:** 2026-05-30
**Agent:** qa (MODE 2: QA Validation)
**Frontend Present:** yes
**Services:** backend http://localhost:8835 (200), frontend http://localhost:3836 (200)

## Summary

The walk-forward forward-testing engine (J-09, J-10) is functionally complete and ships clean.
Backend `pytest` is fully green (168 passed, 0 failed — including all 25 new iter-6 unit/integration
tests). The live `GET /api/system-health` endpoint returns the full evidence payload (by-bucket A–E,
by-setup, by-regime, excess vs SPY/QQQ, control-group cohorts — each with `n`, a `survivorship_bias`
label, and `min_sample`), rejects out-of-range horizons with 422, and the J-01–J-08 regression
endpoints are all 200 with Risk-Off runs showing zero Actionable. The populated `/system-health`
dashboard renders all J-09 panels and the J-10 control-group panel in browser, the horizon selector
re-fetches and changes figures (values match the API payload — no client recomputation), low-sample
cells carry `n` and a ⚠ warn flag, and the survivorship-bias disclaimer is prominent. Frontend
`npm run build` is green for all 10 routes.

All 19 functional test cases PASS.

---

## Step 1 — Artifact Verification

| Artifact | Status |
|----------|--------|
| `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-6-dev.md` | ✅ present, complete |
| `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-6-frontend.md` | ✅ present |
| `reports/reviews/goal-i_can_see_the_wealthy_future-iter-6-review.md` | ✅ PASS_WITH_NOTES |
| `runs/goal-i_can_see_the_wealthy_future-iter-6/status.json` | ✅ present (`review_passed`) |
| `reports/qa/goal-i_can_see_the_wealthy_future-iter-6-test-plan.md` | ✅ present, executed |

Review verdict is PASS_WITH_NOTES (one cosmetic NOTE: an unused `horizon` param in `_control_groups()`
— non-blocking, no functional impact).

---

## Step 2 — Backend Tests

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Log: `reports/qa/goal-i_can_see_the_wealthy_future-iter-6-test.log`

```
======================= 168 passed in 1311.33s (0:21:51) =======================
```

**Exit code: 0. 168 passed, 0 failed, 0 errors.** (The ~22-minute run time is the spec-anticipated
heavy lifespan backfill: `test_api_system_health.py`'s `TestClient` pays one ~223 s fresh-DB
walk-forward backfill, plus several heavy integration boots.)

25 new iter-6 tests, all PASSED — mapping directly to the keystone anti-goals:

- **No-lookahead (forward boundary):** `test_bars_after_returns_only_future_bars_ascending`,
  `test_bars_after_limit_is_the_unbounded_prefix`, `test_close_on_is_the_asof_close`,
  `test_forward_return_uses_the_hth_post_bar`, `test_forward_return_is_na_when_fewer_than_h_post_bars`,
  `test_forward_return_unchanged_when_later_bars_removed`, `test_forward_return_na_on_missing_or_zero_entry`,
  `test_stored_scores_identical_with_and_without_forward_returns`.
- **Immutability / idempotency:** `test_backfill_inserts_forward_returns_without_mutating_snapshot`,
  `test_backfill_is_idempotent`, `test_backfill_latest_run_has_zero_post_bars`.
- **Single source / aggregates correctness:** `test_aggregates_by_bucket_setup_regime_exact`,
  `test_aggregates_excess_vs_spy_and_qqq_exact`, `test_aggregates_control_groups`,
  `test_aggregates_group_by_stored_bucket_not_rescored` (proves no re-bucketing).
- **No fabrication / both regimes:** `test_aggregates_zero_post_bar_run_contributes_n0`,
  `test_system_health_both_regimes_present`.
- **Determinism / honesty labels:** `test_control_group_determinism_same_seed_same_cohort`,
  `test_aggregates_carry_survivorship_label_and_min_sample`.
- **API:** `test_system_health_default_horizon_full_payload`,
  `test_system_health_non_default_horizon_changes_payload`, `test_system_health_invalid_horizon_422`,
  `test_system_health_503_when_no_price_data`, `test_iter1_to_iter5_endpoints_unaffected_j01_to_j08`.
- **No magic numbers (extended to the new calc files):** `test_no_magic_numbers.py` both PASSED.

---

## Step 3 — Frontend Build (TC-19)

Command: `cd apps/frontend && npm run build` → **exit 0.** All 10 routes compiled/typechecked;
`/system-health` = 4.44 kB.

---

## Step 3.5 — Functional Test Plan Results

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | `bars_after` no-lookahead boundary | unit | only date>d, ascending | `test_bars_after_*` PASSED | PASS | Strict inverse of `bars_asof` |
| TC-02 | `forward_return` purity / NA / entry-close-on-D | unit | h-th post-bar; NA if short; unchanged when later bars removed | 4 forward_return tests PASSED | PASS | incl. NA on missing/zero entry |
| TC-03 | Forward returns never feed back into scores | unit | scores byte-identical w/ & w/o fwd returns | `test_stored_scores_identical_*` PASSED | PASS | No feedback |
| TC-04 | Immutability: backfill INSERT-only | integration | no UPDATE of snapshot rows | `test_backfill_inserts_*_without_mutating_snapshot` PASSED | PASS | |
| TC-05 | Backfill idempotency | integration | 2nd call inserts 0 rows | `test_backfill_is_idempotent` PASSED | PASS | |
| TC-06 | `compute_forward_aggregates` correctness | unit | exact by-bucket/setup/regime + excess + control means + n | `test_aggregates_*_exact`, `_group_by_stored_bucket_not_rescored` PASSED | PASS | Buckets read verbatim |
| TC-07 | Control-group determinism | unit | same seed → identical cohort | `test_control_group_determinism_*` PASSED | PASS | |
| TC-08 | No fabrication: n=0 run + both regimes | integration | empty run n=0; Risk-on & Risk-off present | `test_aggregates_zero_post_bar_run_contributes_n0`, `test_system_health_both_regimes_present` PASSED | PASS | |
| TC-09 | No magic numbers guard extended | unit | config-sourced literals only | `test_no_magic_numbers.py` (2) PASSED | PASS | |
| TC-10 | `/api/system-health` default + non-default horizon | api | 200 both; full payload; differ | default 200 (horizon=20); `?horizon=5` 200; payloads differ (A: +6.00% vs −1.09%) | PASS | by_bucket/setup/regime, excess, control_group, n, survivorship_bias, min_sample all present |
| TC-11 | `/api/system-health` invalid horizon → 422 | api | 422 | `?horizon=999` → **422** | PASS | |
| TC-12 | `/api/system-health` 503 when no price data | api | 503, no fabrication | Code path verified (`raise HTTPException(503)` when `latest_data_date is None`); `test_system_health_503_when_no_price_data` PASSED | PASS | Per plan precondition (code-path inference) + unit proof |
| TC-13 | J-01–J-08 regression guard | api | endpoints 200; Risk-Off=0 Actionable; ≥2 runs | `/api/{dashboard,stocks,sectors,themes,runs}` all 200; both Risk-off runs (2022-10-07, 2025-04-04) Actionable=0; 11 runs | PASS | Walk-forward cadence added runs — intended |
| TC-14 | J-09: by-bucket/setup/regime + excess render | browser | all panels numeric + n + survivorship | All render; 23 `n=` figures; A–E table; excess SPY/QQQ; by-setup; by-regime (Risk-on & Risk-off); survivorship banner | PASS | Screenshot `TC-14-system-health-j09.png` |
| TC-15 | J-09: horizon selector changes figures | browser | figures change; default 20; from payload | Bucket A +6.00% (20d) → −1.09% (5d), matches API `-0.01089`; active btn toggles | PASS | Screenshot `TC-15-horizon-change-5d.png`; no client recompute |
| TC-16 | J-10: control-group comparison panel | browser | 5 cohorts numeric+labelled+n | Top-ranked (n=200), Random same-sector (n=285), SPY (n=10), QQQ (n=10), Sector ETF (n=65) | PASS | Screenshot `TC-16-control-group-j10.png` |
| TC-17 | Low-sample / unavailable states explicit | browser | n<30 flagged with ⚠ | 6 ⚠ flags present; `n` shown beside every figure | PASS | e.g. A n=24 ⚠, Actionable n=2 ⚠ |
| TC-18 | Dev handoff present and complete | artifact | cadence + as-of count + first-boot time + both regimes | All four present (quarterly/2yr; 8 cadence + 3 bootstrap = 11 runs; ~223 s first boot; both regimes confirmed) | PASS | |
| TC-19 | Frontend build green | artifact | build exits 0 | `npm run build` exit 0; 10 routes | PASS | |

**19/19 test cases passed.**

---

## Step 4 — Chrome MCP Browser Checks

Executed against http://localhost:3836 with the live backend.

- **`/system-health` (J-09):** renders the dense-dark evidence dashboard fully styled (bg `#0a0e14`).
  Survivorship-bias banner prominent at top. **By score bucket** A–E table with colour-graded rows and
  mean returns (A +6.00% n=24 ⚠, B +3.74% n=87, C +1.11% n=162, D +1.40% n=173, E +2.05% n=772).
  **Excess vs SPY** (+2.03% vs +1.52%) and **vs QQQ** (+2.03% vs +1.99%). **By setup type** and
  **by market regime** (both Risk-on +2.63% n=732 and Risk-off +10.55% n=242 present) numeric + n.
- **Horizon selector (J-09):** buttons 1d/5d/10d/20d/60d, default 20d active. Clicking 5d re-fetched
  `/api/system-health?horizon=5` and the figures changed (bucket A +6.00% → −1.09%), matching the API
  payload exactly — confirming re-format-only (no client recomputation).
- **Control-group panel (J-10):** all five cohorts present, each numeric + labelled + n — Top-ranked
  cohort (rank ≤ 20) +3.02% n=200, Random same-sector peers +1.52% n=285, SPY +1.52% n=10, QQQ
  +1.99% n=10, Sector ETF +1.43% n=65.
- **Low-sample states:** 6 ⚠ warn flags on cells with n < min_sample (30); `n` shown beside every
  figure. No hidden or fabricated numbers.
- **Regression (J-08):** `/scanner-runs` renders all 11 immutable dated runs including both Risk-off
  dates (2022-10-07, 2025-04-04) and the new walk-forward cadence snapshots (2024-05-28 … 2026-02-27) —
  intended immutable as-of history, not a regression. `/` (Dashboard) renders.

Evidence PNGs (`reports/qa/goal-i_can_see_the_wealthy_future-iter-6-evidence/`):
`TC-14-system-health-j09.png`, `TC-15-horizon-change-5d.png`, `TC-16-control-group-j10.png`,
`REG-scanner-runs-j08.png`.

### Environment note (harness, not product)

The QA-runner-managed frontend (port 3836) had died on its own before validation began (returned
HTTP 000). Per the spec's QA-mode-2 "own/await your frontend" guidance, I restarted it via
`scripts/start-frontend.sh`. While running `npm run build` for TC-19 (a *production* build), that build
overwrote the live `next dev` server's `.next` directory, transiently corrupting the dev runtime
(MODULE_NOT_FOUND / CSS 404 / "Checking backend…" across routes). I recovered by killing the trendora
dev server **by port** (per the machine's multi-project cleanup rule — the gap_gap_filler dev server on
a different port was left untouched), clearing `.next`, and restarting clean. All browser evidence above
was captured on the clean rebuild and is reproducible. This is a self-inflicted dev-mode artifact of
build-over-running-dev-server, **not** a product regression — the production `npm run build` passed
cleanly for all 10 routes and the backend API was 200 throughout.

---

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the new capability?** Yes — `/system-health` graduated from an
   EmptyState stub to a full multi-panel forward-tested-evidence dashboard.
2. **Can the user see, understand, and control the capability?** Yes — by-bucket/setup/regime tables,
   excess vs benchmarks, control-group comparison, a horizon selector (1/5/10/20/60), per-figure `n`,
   low-sample ⚠ flags, and a prominent survivorship-bias caveat.
3. **Still relying on old generic pages?** No — dedicated, purpose-built panels.
4. **Technically complete but product-underexposed?** No — every backend aggregate is surfaced and
   interactively controllable.

**Verdict:** UI-PASS

---

## Blockers

None.

## Non-blocking notes

- Review NOTE: unused `horizon` param in `_control_groups()` (`forward_testing.py:301`) — cosmetic,
  no functional impact.
- First boot of a fresh DB is ~223 s (spec-anticipated heavy backfill); subsequent boots are idempotent
  and fast. Documented in the dev handoff.
- Bucket A is low-sample at short horizons (n≈24 < min_sample 30) — the honest outcome (few A-grade
  leaders per scan), visibly flagged with ⚠, not hidden.
