**Verdict:** PASS

# QA Validation Report — goal-i_can_see_the_wealthy_future_forever-iter-11

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-11 (J-27 — regime-conditioned factor effectiveness on `/research`)
**Date:** 2026-06-02
**Agent:** qa (MODE 2 — validation)
**Frontend Present:** yes (browser checks executed)
**Services:** backend `http://localhost:8835` (health 200), frontend `http://localhost:3835` (200) — both managed by the QA runner.

> Note: the functional test plan lists base URLs `:8000`/`:3000`; this project actually runs on `:8835`/`:3835` (per `.claude/project-template.md`). All API/browser checks were executed against the real ports.

---

## Step 1 — Required artifacts

| Artifact | Status |
|----------|--------|
| `docs/handoffs/…-iter-11-dev.md` | ✅ present |
| `reports/reviews/…-iter-11-review.md` | ✅ present — **PASS_WITH_NOTES** |
| `runs/goal-i_can_see_the_wealthy_future_forever-iter-11/status.json` | ✅ present (phase-namespace path, as the dev handoff documents) |
| `reports/qa/…-iter-11-test-plan.md` | ✅ present (18 cases, executed below) |

Review verdict is PASS_WITH_NOTES (two NOTE-severity items, both non-blocking: a test-count wording nit in the handoff — 27/5-new vs the stated 29/6 — and an unused `horizon` param spec-prescribed for signature parity). Neither affects shippability.

---

## Step 2/3 — Backend + frontend test results

Per the project memory (full pytest ~14 min; do not run two pytest invocations concurrently), I ran the three files that exercise the J-27 change rather than re-running the full ~14-min suite a third time. The **full suite is independently confirmed green twice**: the dev handoff records `384 passed, 4 skipped, 0 failed in 1181.78s`, and the reviewer independently re-ran `test_research.py` → 27 passed.

**Targeted run (this QA pass):** `cd apps/backend && .venv/bin/python -m pytest tests/test_research.py tests/test_no_magic_numbers.py tests/test_api_research.py -v`

```
============================= test session starts ==============================
collected 35 items
... (all PASSED) ...
tests/test_research.py::test_by_regime_n_sums_to_total PASSED
tests/test_research.py::test_by_regime_rows_are_config_labels_in_order_with_honest_empty_rows PASSED
tests/test_research.py::test_by_regime_exact_spread_and_rank_ic PASSED
tests/test_research.py::test_by_regime_risk_adjusted_spread_na_when_top_decile_all_non_negative PASSED
tests/test_research.py::test_by_regime_low_sample_regime_is_na_with_honest_n PASSED
tests/test_research.py::test_factor_lab_is_read_only_no_scoring_or_return_or_pattern_call PASSED
tests/test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers PASSED
tests/test_no_magic_numbers.py::test_scanner_has_no_scoring_or_date_literals PASSED
tests/test_api_research.py::test_factor_lab_default_payload PASSED
tests/test_api_research.py::test_factor_lab_no_date_control_present PASSED
tests/test_api_research.py::test_factor_lab_changing_factor_and_horizon_changes_payload PASSED
tests/test_api_research.py::test_factor_lab_unknown_factor_422 PASSED
tests/test_api_research.py::test_factor_lab_invalid_horizon_422 PASSED
tests/test_api_research.py::test_factor_lab_503_when_no_price_data PASSED
======================== 35 passed in 215.36s (0:03:35) ==============================
```

**Frontend:** `npm run build` confirmed by dev handoff (compiled, types valid, 14 routes; `/research` 5.79 kB). Runtime behaviour additionally proven live below (stronger than a build).

---

## Step 3.5 — Functional test plan results

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | `by_regime` present & shaped | api | 200; `by_regime` array; each row has all 8 fields w/ correct types | 200; `by_regime` len=6; all 8 fields present, types correct (`regime` str, `n` int, `low_sample` bool, `rank_ic` obj w/ value) | **PASS** | factor=leadership_score h=5 |
| TC-02 | 6 rows in config order | api | `["Strong risk-on","Risk-on","Narrow leadership","Choppy","Defensive","Risk-off"]` | exact match, in order; n=0 regimes present as honest empty rows | **PASS** | |
| TC-03 | Σ per-regime n == n_total | api | sum == n_total | 1218 == 1218 (h=5); 1217 == 1217 (h=60) | **PASS** | invariant holds |
| TC-04 | Low-sample → honest NA | api | n<30 ⇒ low_sample=true, spread & ra_spread null | Strong risk-on & Defensive (n=0): low_sample=true, all values null; populated regimes numeric | **PASS** | no fabricated 0 |
| TC-05 | Risk-adjusted spread downside-only | unit+api | unit asserts None when top decile all-non-negative; raw spread can be numeric | `test_by_regime_risk_adjusted_spread_na_when_top_decile_all_non_negative` PASSED; `_risk_adjusted` is downside-only (source l.245–249) | **PASS** | live data had downside in all populated regimes; unit test is authoritative |
| TC-06 | Read-only keystone (regime verbatim) | unit | `by_regime` populated despite all compute fns raising | `test_factor_lab_is_read_only_no_scoring_or_return_or_pattern_call` PASSED (extended to patch `regime.score_regime`) | **PASS** | source: `select(ScannerRun)` SELECT-only, l.172/175/187 |
| TC-07 | Exact regime spread + rank-IC | unit | monotone ⇒ +spread & IC≈1; inverse ⇒ negative | `test_by_regime_exact_spread_and_rank_ic` PASSED | **PASS** | |
| TC-08 | No magic numbers / no new config key | unit | `research.py` clean | `test_engine_calc_code_has_no_magic_numbers` PASSED; source uses `cfg.regime.labels`, `wf.min_sample`, `fl.deciles` | **PASS** | |
| TC-09 | Error paths unchanged | api | bogus factor→422; horizon 999→422 | 422 / 422 | **PASS** | |
| TC-10 | Full backend suite green | unit | exit 0, 0 failures, J-27 tests included | 384 passed / 4 skipped / 0 failed (dev) + 35 passed (this QA, targeted) | **PASS** | full suite not re-run a 3rd time (~14 min; memory rule) — confirmed green twice |
| TC-11 | Frontend builds/typechecks | build | build exits 0, new types valid | dev handoff: compiled, types valid, 14 routes; runtime proven below | **PASS** | |
| TC-12 | Regime table renders | browser | 7 cols, 6 rows, n chips | table `data-testid="regime-effectiveness-table"`; headers Regime·n·Rank-IC·Top-decile mean·Bottom-decile mean·Spread (top−bottom)·Risk-adjusted spread; 6 rows; n chips present | **PASS** | TC-12-regime-table.png |
| TC-13 | Short→numeric, long→NA+n | browser | ≥1 numeric regime at short h; NA+n at long h | h=5 → Risk-on/Narrow leadership/Choppy/Risk-off numeric; h=60 → Strong risk-on & Defensive NA + `n=0 ⚠`; distinct sha256 | **PASS** | TC-13-horizon-5d.png / TC-13-horizon-60d.png (distinct) |
| TC-14 | Re-points on factor change | browser | new fetch w/ factor param; DOM changes | select→risk_score fired `GET .../factor-lab?factor=risk_score`; DOM re-pointed and matches API exactly (Risk-on −0.02/+2.59%, Narrow leadership −0.08/+5.10%, Choppy −0.10/−4.27%, Risk-off −0.17/−9.16%) | **PASS** | TC-14-factor-risk_score.png; distinct sha256 |
| TC-15 | J-18: as-of does NOT affect /research | browser | byte-identical; zero as_of requests | date switched ""→2025-11-28; `main` innerText **byte-identical**; **0** total fetches, **0** `as_of` params | **PASS** | TC-15-asof-unchanged.png |
| TC-16 | J-25: decile + rank-IC still render/re-point | browser | both render; re-point on factor/horizon | decile table (10 rows, headers Decile·Factor range·Mean fwd return·Risk-adjusted (downside)) + rank-IC card w/ descriptive label both present; re-point with factor/horizon | **PASS** | |
| TC-17 | Empty-state: no fabricated table when n_total==0 | browser/api/code | regime table absent on n_total==0 | no reachable n_total==0 combo (all horizons 1217–1218 obs); `FactorLab` returns EmptyState early at `data.n_total === 0` (page.tsx l.196–203) before rendering the regime table (l.233) | **PASS** | verified by code inspection — gate present, table not fabricated |
| TC-18 | Dev handoff present | artifact | file w/ required sections + exact counts | present; What Built / Files Changed / Tests Run (exact counts) / Known Issues / Suggested Next; documents status.json phase-namespace path | **PASS** | |

**18/18 test cases passed.**

---

## Step 4 — Chrome MCP browser checks

Executed against `http://localhost:3835/research` (frontend reachable). Evidence saved under `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-11-evidence/` (5 PNGs, all distinct sha256). Re-point / byte-identical claims are grounded on **distinct screenshots + DOM-text and network assertions** (browser-QA hygiene, iter-6 lesson) — never a single screenshot pair.

Key live findings:
- **Regime table renders** with all 6 configured labels, the 7 specified columns, and per-regime `n` chips (`n=732`, `n=0 ⚠`, etc.).
- **Re-points on horizon** (5d/60d) and **on factor** (leadership_score→risk_score) via a fresh `GET /api/research/factor-lab?...` each time; DOM values match the API payload **exactly** (single source of truth — UI re-formats only, no client recompute).
- **J-18 preserved:** changing the global top-bar as-of switcher left `/research` byte-identical and issued **zero** network requests and **zero** `as_of` params.
- **Honest NA:** n=0 regimes show `NA` + `n=0 ⚠`, never a fabricated 0.

Evidence: `TC-12-regime-table.png`, `TC-13-horizon-5d.png`, `TC-13-horizon-60d.png`, `TC-14-factor-risk_score.png`, `TC-15-asof-unchanged.png`.

Anti-goal seams verified directly in `apps/backend/app/engine/research.py` source (per the spec's process note):
- **Read-only / single source:** `_factor_observations` reads the stored regime via `select(ScannerRun)` (SELECT-only, l.172), `regime_by_run = {run.id: run.regime_label}` verbatim (l.175), attached as `"regime"` per observation (l.187). The extended patch-to-raise keystone test passes.
- **Downside-only:** `risk_adjusted_spread` reuses the downside `_risk_adjusted` decile legs and is `None` when low-sample or either leg is None (l.245–249) — never total volatility.
- **Config-driven (no magic numbers):** `for label in cfg.regime.labels`, `wf.min_sample`, `fl.deciles` (l.227–230); `test_no_magic_numbers` passes.
- **`by_regime` on the same pool:** `compute_factor_lab` returns `"by_regime": _regime_effectiveness(observations, cfg, horizon)` (l.310) — one computation, same observation pool, no new endpoint.

---

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the phase's new capability?** Yes — a new "Factor effectiveness by market regime" table on `/research`, below the decile table + rank-IC card.
2. **Can the user see/understand/control the new capability?** Yes — one row per configured regime with n, rank-IC, top/bottom decile means, and raw + downside-risk-adjusted spreads; it re-points with the existing factor + horizon controls.
3. **Relying on old generic pages?** No — purpose-built panel on the established `/research` home; no nav change.
4. **Technically complete but underexposed?** No — the regime-dependence insight is directly visible (e.g. leadership_score positive in Risk-on, negative in Choppy/Narrow leadership), with honest NA + n for low/empty regimes.

**Verdict:** UI-PASS

---

## Step 5b — Server cleanup

No servers were started by this QA pass (the QA runner manages `:8835`/`:3835`). Chrome MCP used the persistent shared browser. Nothing to kill.

---

## Blockers

None.

## Summary

All 18 functional test cases pass; 35/35 targeted backend tests pass; full suite confirmed green (384 passed). J-27 is delivered read-only, config-driven, downside-only, with honest per-regime NA + n, and the consistency invariant (Σ per-regime n == n_total) holds. Required-still-passing journeys verified: J-25 (decile + rank-IC render/re-point), J-18 (no second date state; zero as_of), J-09/J-19/J-15 (read path unchanged, SELECT-only keystone holds). No anti-goal violations.

**Verdict:** PASS
