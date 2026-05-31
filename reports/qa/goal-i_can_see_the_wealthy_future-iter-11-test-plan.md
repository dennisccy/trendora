# goal-i_can_see_the_wealthy_future-iter-11 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future-iter-11
**Date:** 2026-05-31
**Frontend Present:** yes

## Phase Goal

Ship Trendora's first **detected price pattern** — a config-driven **VCP (Volatility Contraction Pattern)** flag that rides each stock's immutable snapshot row alongside (never replacing) its setup status: filterable + badged + explained (reason + pivot/invalidation) on `/stocks` and `/stocks/[ticker]`, and forward-tested (VCP-vs-non-VCP mean return + sample size `n`) on `/system-health`.

## Test Cases

### TC-01 — Implementation actually present (anti-no-op guard)

**Type:** artifact
**Preconditions:** Repo at iter-11 branch; dev step run.

**Steps:**
1. Confirm `apps/backend/app/engine/patterns.py` exists and defines `detect_vcp`.
2. `git diff --name-only` shows edits to `config.yaml`, `apps/backend/app/config.py`, `scoring.py`, `models.py`, `scanner.py`, `forward_testing.py`, `apps/frontend/lib/api.ts`, `app/stocks/page.tsx`, `app/stocks/[ticker]/page.tsx`, `app/system-health/page.tsx`.
3. `grep -rln "vcp" apps/` returns non-empty.
4. Confirm `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-11-dev.md` exists.
5. Confirm `runs/goal-i_can_see_the_wealthy_future-iter-11/status.json` shows `tests_run=true` / `qa_complete`.

**Expected outcome:** All files present, handoff written, status reached.
**Pass criteria:** Every file/edit above exists; grep non-empty; handoff + status.json present. Any missing item ⇒ FAIL.

---

### TC-02 — Config `patterns.vcp` block holds every threshold (no magic numbers in config source)

**Type:** artifact
**Preconditions:** `config.yaml` edited.

**Steps:**
1. Open `config.yaml`; locate `patterns: → vcp:`.
2. Confirm presence of all keys: `lookback_bars`, `min_contractions`, `max_contractions`, `max_base_depth_pct`, `contraction_shrink_ratio`, `max_last_contraction_pct`, `pivot_proximity_pct`, `volume_dryup_ratio`, `volume_window`, `min_history_bars`.

**Expected outcome:** A typed VCP threshold block exists with no thresholds missing.
**Pass criteria:** All 10 keys present with sane values (`0 < contraction_shrink_ratio <= 1`, all `*_pct > 0`, all windows/counts positive).

---

### TC-03 — Config typed validation (`test_config*.py`)

**Type:** api (unit)
**Preconditions:** `config.py` gains `VcpCfg` + `PatternsCfg`; targeted test files runnable.

**Steps:**
1. Run `cd apps/backend && python -m pytest tests/test_config*.py -q`.
2. Confirm a valid `patterns.vcp` block loads.
3. Confirm a non-positive window, `contraction_shrink_ratio` outside `(0,1]`, or non-positive `*_pct` raises `ConfigError` (not a silent default).

**Expected outcome:** Valid block loads; invalid blocks raise `ConfigError`.
**Pass criteria:** `test_config*.py` passes; both valid-load and invalid-raise assertions green.

---

### TC-04 — `detect_vcp` detector behavior (`test_patterns.py`)

**Type:** api (unit)
**Preconditions:** NEW `tests/test_patterns.py`.

**Steps:**
1. Run `cd apps/backend && python -m pytest tests/test_patterns.py -q`.
2. Verify: a constructed VCP series → `flagged=true`, `pivot ≈ base high`, `invalidation.level ≈ last-contraction low`.
3. Verify: a non-VCP series (steady uptrend / expanding volatility) → `flagged=false`.
4. Verify: short history (`< min_history_bars`) → `flagged=false`, no fabricated pivot, honest reason.
5. Confirm thresholds are read from a test config (no literal in the detector).

**Expected outcome:** Positive, negative, and NA paths all behave as asserted.
**Pass criteria:** `test_patterns.py` passes including pivot/invalidation approximate-equality and the NA-no-fabrication assertion.

---

### TC-05 — No magic numbers includes `patterns.py` (`test_no_magic_numbers.py`)

**Type:** api (unit)
**Preconditions:** `patterns.py` added to `CALC_FILES`; forbidden-int set extended for new tunables.

**Steps:**
1. Run `cd apps/backend && python -m pytest tests/test_no_magic_numbers.py -q`.

**Expected outcome:** `patterns.py` is held to the no-magic-numbers contract; every VCP threshold reads from `config.patterns.vcp`; only structural `0/1/2/100` literals permitted.
**Pass criteria:** Test passes with `patterns.py` in `CALC_FILES` and `scoring.py`/`forward_testing.py` membership unchanged.

---

### TC-06 — VCP is a pattern, NOT a status (critical anti-goal)

**Type:** api (unit)
**Preconditions:** `setups.py` UNCHANGED; VCP composed additively in `scoring.py`.

**Steps:**
1. Assert `"VCP" not in ALL_STATUSES`.
2. Assert `score_stocks` setup statuses are byte-identical with vs without the VCP block (flag alters no status).
3. Assert a Risk-off run's VCP-flagged rows are all `Risk-off-watchlist` (never Actionable).
4. Assert a VCP-flagged row never becomes Actionable solely from the flag.

**Expected outcome:** VCP never enters the setup enum and never promotes Actionable.
**Pass criteria:** All four assertions green via `test_scoring.py` / `test_setups.py` (relevant targeted files).

---

### TC-07 — Single-source / no-recompute-in-read-path KEYSTONE (patch-to-raise)

**Type:** api (unit)
**Preconditions:** Snapshot DB built; `detect_vcp` and `score_*` engines monkeypatchable.

**Steps:**
1. Monkeypatch `app.engine.patterns.detect_vcp` (and the `score_*` engines) to raise.
2. Assert `stocks_payload` / `/api/stocks` still serves the stored VCP flag.
3. Assert `stock_detail_payload` / `/api/stocks/{ticker}` still serves the stored VCP flag.
4. Assert `compute_forward_aggregates(...)["by_vcp"]` still returns the stored breakdown.

**Expected outcome:** Read path serves stored values from `scanner_results`; no re-detection occurs.
**Pass criteria:** All three read surfaces return stored VCP data WITHOUT raising — proving zero recompute in read path.

---

### TC-08 — Faithful mirror + immutability + no-lookahead stay green

**Type:** api (unit)
**Preconditions:** `models.py` adds only `is_vcp` (append-only); DB rebuilt from frozen seed.

**Steps:**
1. Assert `ScannerResult.is_vcp == json.loads(record_json)["vcp"]["flagged"]` for persisted rows.
2. Run and confirm green: `test_latest_run_faithful_to_live_computation`, `test_run_scan_no_lookahead`, `test_run_scan_idempotent_and_immutable`, `test_risk_off_run_has_zero_actionable`.
3. Confirm `run_scan` UPDATEs no existing row; `forward_returns` stays separate/INSERT-only.

**Expected outcome:** Mirror equals record; snapshot invariants intact with the new column.
**Pass criteria:** Mirror-equality assertion passes AND all four named invariant tests stay green.

---

### TC-09 — `by_vcp` forward-return dimension (`test_forward_testing.py`)

**Type:** api (unit)
**Preconditions:** `compute_forward_aggregates` gains `by_vcp`; `stock_obs` reads `res.is_vcp` verbatim.

**Steps:**
1. Run `cd apps/backend && python -m pytest tests/test_forward_testing.py -q`.
2. Confirm `by_vcp` returns two cohorts (`vcp: "VCP"` and `"non-VCP"`), each `{vcp, mean_return, n}`.
3. Confirm an empty cohort → `mean_return: null`, `n: 0` (NA, never fabricated).
4. Confirm `is_vcp` is grouped verbatim from the stored column (not re-detected).
5. Confirm pre-existing iter-6/iter-10 forward-testing assertions stay byte-green (additive only).

**Expected outcome:** `by_vcp` present, padded, honest NA, `n` carried; existing tests unchanged.
**Pass criteria:** `test_forward_testing.py` passes including the two-cohort + empty-cohort + verbatim-grouping assertions.

---

### TC-10 — Targeted backend suite green (regression)

**Type:** api (unit)
**Preconditions:** All backend edits complete; DB rebuilt.

**Steps:**
1. Run targeted files (background task, budget minutes): `python -m pytest tests/test_patterns.py tests/test_scoring.py tests/test_scanner.py tests/test_forward_testing.py tests/test_api_engine.py tests/test_api_system_health.py tests/test_no_magic_numbers.py tests/test_config*.py -q`.

**Expected outcome:** All targeted files pass; `score_stocks`-shape assertions extended (not broken) to include `vcp`.
**Pass criteria:** Zero failures across the targeted set; record exact pass/fail counts.

---

### TC-11 — Frontend build / typecheck clean

**Type:** artifact (build)
**Preconditions:** `lib/api.ts` gains `Vcp`/`vcp` on `StockRow` + `ForwardVcpRow`/`by_vcp`.

**Steps:**
1. Run `cd apps/frontend && npm run build`.

**Expected outcome:** Build + typecheck succeed with the new `vcp` field on `StockRow` and `by_vcp` on `SystemHealthResponse`.
**Pass criteria:** `npm run build` exits 0, no type errors.

---

### TC-12 — DB rebuild reproduces snapshots with VCP populated

**Type:** artifact
**Preconditions:** gitignored `apps/backend/data/trendora.db` deleted before bootstrap.

**Steps:**
1. Delete `apps/backend/data/trendora.db`.
2. Boot backend; allow walk-forward backfill (minutes).
3. Query `scanner_results`; confirm `is_vcp` column exists and is populated (mix of true/false per the seed).

**Expected outcome:** Fresh DB has the `is_vcp` column populated from the frozen seed; no manual ALTER.
**Pass criteria:** Column present; at least the latest snapshot flags a non-trivial set OR honestly flags none (empty-state path acceptable).

---

### TC-13 — `/stocks` VCP filter narrows rows (J-16)

**Type:** browser
**Preconditions:** Backend up (`CORS_ORIGINS=http://localhost:3835`); frontend up (`NEXT_PUBLIC_API_URL=http://localhost:8835`, `PORT=3835`).

**Steps:**
1. Navigate to `http://localhost:3835/stocks`.
2. Set the VCP `Select` to "VCP only"; `await_text` on a row-only VCP badge reason/pivot value (never a filter placeholder).
3. Confirm only flagged rows remain; set to "Non-VCP" and confirm flagged rows disappear; set to "All" and confirm full list returns.
4. If zero match for "VCP only", confirm the explicit styled empty-state renders (no fabricated rows).
5. Capture distinct PNG `TC-13-leaderboard-filtered.png` under `reports/qa/<phase>-evidence/`.

**Expected outcome:** Filter is pure client-side re-display on `row.vcp.flagged`; ranking unchanged; empty-state honest.
**Pass criteria:** "VCP only" shows only flagged rows (or empty-state); "All" restores; distinct PNG captured.

---

### TC-14 — `/stocks` VCP badge shows reason + pivot + invalidation (J-16)

**Type:** browser
**Preconditions:** As TC-13; ≥1 flagged row in latest snapshot.

**Steps:**
1. On `/stocks`, locate a VCP-flagged row's teal "VCP" `Badge`.
2. Confirm its `title`/tooltip carries `row.vcp.reason` + pivot + `row.vcp.invalidation.note`.
3. Capture distinct PNG `TC-14-leaderboard-badge.png`.

**Expected outcome:** Flagged rows show a compact accent VCP badge with explanatory tooltip (not a bare flag).
**Pass criteria:** Badge present with reason + pivot + invalidation note in tooltip; distinct PNG (md5 differs from TC-13).

---

### TC-15 — Stock Detail VCP badge identical to leaderboard (J-05/J-06)

**Type:** browser
**Preconditions:** A known VCP-flagged ticker from TC-14.

**Steps:**
1. Open `/stocks/{ticker}` for that flagged name.
2. Confirm the VCP badge renders with pivot + invalidation level matching the leaderboard's stored row byte-for-byte.
3. Open a NON-flagged ticker; confirm "No VCP pattern detected" (or nothing) — no fabricated pivot.
4. Capture distinct PNG `TC-15-detail-badge.png`.

**Expected outcome:** Detail VCP flag/pivot/invalidation is identical to the leaderboard row (J-06); unflagged shows honest empty.
**Pass criteria:** Flagged-detail values == leaderboard values; unflagged shows no fabricated pivot; distinct PNG.

---

### TC-16 — System Health VCP-vs-non-VCP forward-return breakdown (J-16)

**Type:** browser
**Preconditions:** As TC-13; `by_vcp` populated.

**Steps:**
1. Navigate to `/system-health`.
2. Locate the "Forward return: VCP vs non-VCP" `BreakdownPanel`.
3. Confirm two rows (VCP / non-VCP) each showing mean return + sample size `n`; `n < min_sample` flagged ⚠; `mean_return == null` shown NA/em-dash.
4. Confirm survivorship-bias label present.
5. Capture distinct PNG `TC-16-system-health-by-vcp.png`.

**Expected outcome:** Honest VCP-vs-non-VCP mean-return breakdown with `n`, ⚠ low-sample, NA when empty.
**Pass criteria:** Both cohorts render with `n`; low-sample/NA honestly labelled; distinct PNG (4 distinct surface md5s total).

---

### TC-17 — Regression: existing `/stocks` and System Health surfaces intact (J-02/J-09/J-10/J-13)

**Type:** browser
**Preconditions:** Services up.

**Steps:**
1. On `/stocks`, confirm sector + setup filters still narrow rows and ranking is unchanged.
2. On `/system-health`, confirm existing by-bucket / by-setup / by-regime / control-group panels are unchanged.
3. Use the as-of date switcher (J-13); confirm the leaderboard re-points to the selected snapshot.

**Expected outcome:** Pre-existing journeys behave as before; VCP additions are non-disruptive.
**Pass criteria:** Sector/setup filters + ranking unchanged; existing panels unchanged; as-of switcher re-points.

---

## Summary

Total test cases: 17
API/unit tests: 8 (TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10)
Browser tests: 5 (TC-13, TC-14, TC-15, TC-16, TC-17)
Artifact checks: 4 (TC-01, TC-02, TC-11, TC-12)

**Critical anti-goals covered:** VCP-is-a-pattern-not-a-status (TC-06), no-recompute/single-source keystone (TC-07), snapshots-immutable + no-lookahead + faithful mirror (TC-08, TC-12), no magic numbers (TC-02, TC-05), honest NA/no-fabrication (TC-04, TC-09, TC-13, TC-15, TC-16).

**Out of scope (do NOT test as failures):** `/methodology` VCP glossary entry (J-12 / next iteration); `classify_setup`/setup-enum change; `compute_run_scorecard`/`/api/backtest` (J-14); watchlist VCP UI.
