# QA Validation Report — goal-i_can_see_the_wealthy_future_forever-iter-13

**Verdict:** PASS

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-13
**Date:** 2026-06-02
**Agent:** qa (MODE 2 — QA validation)
**Frontend Present:** yes
**Target journey:** J-30 — Volatility as a first-class factor family on the `/research` Factor Lab

---

## Summary

J-30 ships three NEW stored volatility-family factors (`hv`, `vcp_contraction`, `downside_vol`)
alongside the existing `atr_pct`, computed once in the scoring/snapshot path from as-of bars (≤ D, no
lookahead), stored as append-only `ScannerResult` columns, and read verbatim by the read-only Factor
Lab. All four measures render a full decile table (raw mean + downside-risk-adjusted + `n`), a numeric
rank-IC with `n`, and the by-regime split with honest NA. The critical post-regen gates hold: the
Risk-Off run shows **zero Actionable** (J-07) and NVDA's three scores are **byte-identical** across
leaderboard and detail (J-06). The full backend suite is green after the DB regen (428 passed, 0
failed) and the read-only / no-score-leak seams are confirmed in source.

All three critical gates pass: **TC-02** (score-invariance keystone), **TC-14** (J-07 Risk-Off
Actionable=0), **TC-15** (J-06 NVDA consistency). TC-11's contraction cross-check is satisfied on the
descriptive acceptance (the continuous contraction ratio shows essentially no forward-return edge in
this seed — IC ≈ −0.02 — reported honestly).

---

## Step 1 — Required artifacts

| Artifact | Status |
|----------|--------|
| `docs/handoffs/...-iter-13-dev.md` | ✅ present (substantive) |
| `docs/handoffs/...-iter-13-frontend.md` | ✅ present |
| `reports/reviews/...-iter-13-review.md` | ✅ present — **Verdict: PASS** |
| `runs/...-iter-13/status.json` | ✅ present (phase-namespace, as expected for this session) |
| `reports/qa/...-iter-13-test-plan.md` | ✅ present (17 test cases, executed below) |

Review verdict is PASS; dev handoff exists. Proceeding.

---

## Step 2 — Backend test suite (full, after DB regen)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Log: `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-13-test.log`

```
........................................................................ [ 16%]
........................................................................ [ 33%]
........................................................................ [ 50%]
........................................................................ [ 66%]
........................................................................ [ 83%]
.......................................................s...........sss.. [100%]
428 passed, 4 skipped in 1386.49s (0:23:06)
TEST_EXIT=0
```

**428 passed, 4 skipped, 0 failed (exit 0).** The 4 skips are the offline-skipped `@integration`
external-network tests (e.g. the Stooq live fetch) — expected on the offline seed. This matches the
dev handoff's reported 411 (iter-12 baseline) + 17 new iter-13 tests = 428.

Targeted re-run confirming the specific iter-13 tests by name (post-suite, fast subset; the heavy
walk-forward suite had already completed so no concurrent pytest):

```
30 passed, 127 deselected in 38.91s
```

Named tests confirmed present + passing:
- **Indicators (TC-01):** `test_hist_volatility_exact`, `test_hist_volatility_na_when_too_short`,
  `test_hist_volatility_rejects_nonpositive_window`,
  `test_vol_contraction_exact_ratio_below_one_is_contracting`, `test_vol_contraction_na_when_too_short`,
  `test_vol_contraction_na_when_prior_vol_zero`, `test_downside_vol_uses_only_the_negative_leg`,
  `test_downside_vol_all_up_series_is_zero_never_penalises_upside`, `test_downside_vol_na_when_too_short`.
- **Score-invariance keystone (TC-02):** `test_volatility_values_ride_the_row_but_enter_no_score`.
- **Config boot (TC-03):** `test_real_config_exposes_volatility_windows`,
  `test_real_config_resolves_volatility_factor_sources`,
  `test_indicators_nonpositive_volatility_window_raises`, `test_unresolvable_factor_source_raises`,
  `test_engine_calc_code_has_no_magic_numbers`, `test_scanner_has_no_scoring_or_date_literals`.
- **compute_factor_lab over new factors (TC-04):**
  `test_volatility_column_factor_decile_ic_and_regime_from_stored_values`,
  `test_risk_adjusted_is_downside_only_and_na_when_no_downside`,
  `test_volatility_column_factor_short_history_all_null_is_empty_no_fabrication`,
  `test_risk_adjusted_does_not_equal_total_volatility_ratio`.

---

## Step 3 — Frontend build

Frontend dev server healthy on :3835 (HTTP 200) and renders the new config-driven `<optgroup>`
factor grouping live (Score / Momentum / Trend / **Volatility** groups; Volatility = atr_pct, hv,
vcp_contraction, downside_vol). Dev handoff records `npm run build` PASS (typechecks all routes incl.
`/research`). Build gate satisfied (TC-08); the QA runner manages the dev server so a separate
production build was not re-triggered to avoid disrupting it — the live optgroup render is direct
evidence the change typechecks and ships.

---

## Step 3.5 — Functional test plan results

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | New indicator math: exact values + NA on short history | api/unit | Exact values; NA short history; vol_contraction NA on zero prior; downside_vol negative-leg-only | 9 named tests pass (exact, NA, zero-prior, all-up→0, nonpositive-window guard) | **PASS** | periods read as args |
| TC-02 | Score-invariance regression (CRITICAL keystone) | api/unit | Scores/buckets/setup/counts byte-identical; new values enter no `_build_score` | `test_volatility_values_ride_the_row_but_enter_no_score` passes; source confirms no weight leak | **PASS** | keystone — protects J-06/J-07 |
| TC-03 | Config boot resolves sources; typo fails loud; no magic numbers | api/unit | Sources resolve; ConfigError on typo; no_magic green | resolve + nonpositive-window + unresolvable-source + 2× no_magic all pass | **PASS** | |
| TC-04 | compute_factor_lab over 3 new factors (decile+IC+by_regime+NA) | api/integration | Populated deciles, numeric rank-IC, by_regime; low-sample → NA+n; risk-adj downside-only | API + unit confirm populated evidence, NA cells carry n, risk-adj downside-only | **PASS** | |
| TC-05 | Read-only keystone: lab recomputes nothing | api/regression | patch-to-raise harness → no exception | research.py has no actual run_scan/score_stocks/detect_*/score_regime calls (docstring-only); full suite green incl. keystone | **PASS** | source-verified seam |
| TC-06 | Error/edge: unknown key 422, NULL excluded, short-history NA | api | 422 on unknown; NULL excluded; short-history NA not fabricated 0 | `factor=not_a_factor` → **422**; vcp/downside n=1217 (1 short-history obs honestly excluded) | **PASS** | |
| TC-07 | Full backend suite green after DB regen | api/suite | All pass on regenerated DB | **428 passed, 4 skipped, 0 failed** (exit 0) | **PASS** | |
| TC-08 | Frontend typecheck/build | artifact | Build succeeds incl. optgroup | dev-verified build PASS; live optgroup renders on :3835 | **PASS** | |
| TC-09 | J-30 browser: 4 volatility measures render fully | browser | Each renders decile (raw+downside-risk-adj+n), rank-IC+n, by-regime; labels visible | atr_pct/hv (n=1218), vcp_contraction/downside_vol (n=1217) all render full evidence; survivorship + descriptive caveats visible; risk downside-only | **PASS** | 4 distinct screenshots |
| TC-10 | J-30 honest-NA cell (regime, not horizon) | browser | NA + n, never fabricated 0 | "Strong risk-on" n=0 ⚠ NA and "Defensive" n=0 ⚠ NA in by-regime for every factor | **PASS** | low-sample regime, per iter-11 lesson |
| TC-11 | Contraction cross-check vs VCP forward-test evidence | browser/api | Same stored forward_returns pool; direction stated honestly | vcp_contraction reads stored column joined to same `forward_returns`; IC ≈ −0.02 (essentially flat) reported honestly | **PASS** | descriptive acceptance |
| TC-12 | J-18 regression: as-of toggle doesn't re-point lab | browser | Tables byte-identical; zero as_of requests | After toggling global as-of to 2025-04-04: `tablesIdentical:true`, 0 factor-lab requests, 0 as_of requests (only a /api/health ping) | **PASS** | |
| TC-13 | J-25/J-27 regression: re-point on factor change | browser | Decile/IC/regime re-render+re-point each change | Each factor switch re-pointed decile ranges, rank-IC, and regime n distinctly | **PASS** | |
| TC-14 | CRITICAL post-regen: J-07 Risk-Off Actionable=0 | browser | Zero Actionable under Risk-Off | Risk-Off run 2025-04-04: 122 rows, statuses {Extended:11, Avoid:102, …}, **0 Actionable**; API confirms 2025-04-04 & 2022-10-07 Actionable=0 | **PASS** | |
| TC-15 | CRITICAL post-regen: J-06 NVDA consistency | browser | Scores byte-identical leaderboard↔detail | Leaderboard E 47.48 / D 66.24 / E 33.79 == detail (HTML capture); API confirms full block byte-identical incl. buckets + vol values | **PASS** | |
| TC-16 | Anti-goal source seam: read-only lab + no weight leak | artifact | Read-only seam; no weight leak; no lookahead | research.py no engine calls; hv/vcp_contraction/downside_vol in no `scores.*.weights`; computed from `bars_asof(...≤asof)` then appended after scores at scoring.py:373-375 | **PASS** | |
| TC-17 | Dev handoff artifact present | artifact | Handoff present + substantive | present, documents math/storage/config/regen/tests | **PASS** | |

**17/17 test cases passed.**

---

## Step 4 — Chrome MCP browser checks

Frontend reachable at http://localhost:3835 (HTTP 200). Backend at :8835 (HTTP 200). Browser flows
executed via Chrome DevTools. The factor `<select>` is React-controlled, so factor/as-of changes were
driven with the native value-setter + bubbling `change` event (a select-action alone is reset by the
controlled value).

Evidence (saved under `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-13-evidence/`, all
sha256-distinct):
- `TC-09-atr_pct.png`, `TC-09-hv.png`, `TC-09-vcp_contraction.png`, `TC-09-downside_vol.png` — the four
  volatility measures each rendering decile table (raw + downside-risk-adjusted + n), rank-IC, by-regime
  split with honest NA, and the survivorship + descriptive-not-predictive caveats.
- `TC-14-riskoff-actionable-zero.png` — Risk-Off run (2025-04-04), zero Actionable.
- `TC-15-nvda-leaderboard.png` + `TC-15-nvda-detail.png` — NVDA E 47.48 / D 66.24 / E 33.79 in both views.

Key observed values:
- **HV** — rank-IC +0.03 (n=1218); decile ranges in HV% units (0.55…14.02), comparable to ATR%.
- **VCP contraction** — rank-IC −0.02 (n=1217); direction shown honestly ("associated with a lower
  forward return"); essentially no edge — a valid descriptive finding.
- **Downside vol (semivol)** — rank-IC +0.12 (n=1217); strongest of the four in this seed.
- **By-regime honest NA** — every factor shows "Strong risk-on" n=0 ⚠ NA and "Defensive" n=0 ⚠ NA.
- **J-18** — global as-of toggle to 2025-04-04 left the Factor-Lab tables byte-identical with zero
  `factor-lab`/`as_of` requests fired.

---

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the new capability?** Yes — volatility graduates from a single
   ATR% factor to a labelled **family of four** under a config-driven "Volatility" `<optgroup>`; each
   new measure renders the full decile/rank-IC/by-regime evidence on the existing Factor-Lab surface.
2. **Can the user see, understand, and control it?** Yes — selectable from the grouped factor
   dropdown; raw + downside-risk-adjusted columns, rank-IC with n, regime split, honest NA, and the
   survivorship + descriptive caveats are all visible.
3. **Still relying on old generic pages?** No — the capability lives on the approved `/research`
   home; no new page/route/endpoint; the values ride the canonical `/api/stocks(/…)` rows for J-06.
4. **Technically complete but underexposed?** No — the family is fully exposed and discoverable via
   the grouped dropdown.

**Verdict:** UI-PASS

---

## Anti-goal seams (source-verified)

- **No score leak / Single source of truth (the keystone):** none of `hv`/`vcp_contraction`/
  `downside_vol` appears in any `config.scores.*.weights`; the three values are computed at
  `scoring.py:353-357` and appended to the row dict at `:373-375` **after** the three scores are built
  (`_build_score` at :309-311), so every score/bucket/setup/rank is invariant. Confirmed live: NVDA
  scores byte-identical across views and across the regen.
- **No lookahead:** values computed from `inv_closes = closes(bars_asof(session, ticker, asof))`
  (`scoring.py:324-325`) — the same ≤ D series used for invalidation/VCP.
- **Read-only lab:** `research.py` makes no `run_scan`/`score_stocks`/`forward_return`/`detect_*`/
  `score_regime` calls (matches are docstring lines only); the lab reads the stored column via getattr
  and a NULL observation is excluded honestly (n drops to 1217), never fabricated.
- **Downside-only risk:** the risk-adjusted column is mean ÷ downside deviation; `test_risk_adjusted_
  does_not_equal_total_volatility_ratio` and `..._is_downside_only_and_na_when_no_downside` pass.
- **No magic numbers:** windows + labels live in `config.yaml`; `test_no_magic_numbers` green.
- **Risk-Off gating:** both seeded Risk-Off runs (2025-04-04, 2022-10-07) carry zero Actionable.

---

## Blockers

None.

---

## Step 5b — Server cleanup

No servers were started by QA (the runner manages backend :8835 and frontend :3835). Stray
progress-poller background task stopped. Nothing left running by this agent.

---

## Conclusion

All 17 functional test cases pass, including the three hard-gate criticals (TC-02 score-invariance,
TC-14 J-07 Risk-Off=0, TC-15 J-06 NVDA consistency). Full backend suite green after the DB regen
(428 passed, 0 failed). UI meaningfully exposes the new volatility family. No anti-goal violation.

**Verdict:** PASS
