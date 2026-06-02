**Verdict:** PASS

# QA Validation Report — goal-i_can_see_the_wealthy_future_forever-iter-9

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-9
**Date:** 2026-06-02
**Agent:** qa (MODE 2 — validation)
**Frontend Present:** yes
**Target journey:** J-28 — ≥2 new config-driven detected price patterns beyond VCP (`pullback_to_rising_dma`, `flat_base_breakout`), forward-tested.

---

## Summary

J-28 is fully delivered. Two new config-driven detected patterns (`pullback_to_rising_dma`, `flat_base_breakout`) ride alongside the setup status exactly like VCP — independently filterable on `/stocks`, auto-documented on `/methodology` from the config-backed catalog, and surfaced as pattern-vs-non-pattern forward-return breakdowns (with `n` + honest NA) on `/system-health`. The full backend suite passes (**351 passed, 4 skipped, 0 failed**), the frontend typechecks clean, all 20 functional test cases pass, and all five critical anti-goal seams were verified directly in source. No regression in VCP, sector/setup filters, or the Risk-Off→Actionable=0 gate.

---

## Step 1 — Required artifacts

| Artifact | Status |
|----------|--------|
| `docs/handoffs/goal-…-iter-9-dev.md` | ✅ present |
| `reports/reviews/goal-…-iter-9-review.md` (PASS_WITH_NOTES) | ✅ present, verdict PASS_WITH_NOTES |
| `runs/goal-…-iter-9/status.json` | ✅ present |
| `reports/qa/goal-…-iter-9-test-plan.md` | ✅ present (20 cases, executed below) |

Review verdict is PASS_WITH_NOTES with a single non-blocking NOTE (leaderboard badge/filter registry hardcodes the badge label in the frontend; glossary + tooltips DO auto-render from the catalog). This is an enhancement, not a defect — the spec explicitly contemplated a frontend pattern list for the filter. Not a blocker.

---

## Step 2 — Backend tests (exact output)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Log: `reports/qa/goal-…-iter-9-test.log`

```
================= 351 passed, 4 skipped in 1086.52s (0:18:06) ==================
EXIT:0
```

Run ONCE after DB regeneration (~18 min, per project-memory caveat). **0 failures, 0 errors.** This matches the dev handoff's net result. No failure digest needed (exit 0).

Key seam tests (all PASSED):
- `test_patterns.py::test_constructed_pullback_series_flags_with_pivot_and_invalidation`, `…flat_base…` — positive series flag with concrete pivot+invalidation.
- `test_patterns.py::test_extended_uptrend_does_not_flag_pullback`, `test_downtrend_does_not_flag_pullback`, `test_deep_base_does_not_flag_flat_base`, `test_base_below_prior_high_does_not_flag_flat_base` — wrong-shape does not flag.
- `test_patterns.py::test_short_history_pullback_is_na_never_fabricated`, `…flat_base…` — insufficient history → NA, no fabricated level.
- `test_patterns.py::test_pullback_detection_is_config_driven_not_hard_coded`, `test_flat_base_detection_is_config_driven_not_hard_coded`, `test_flat_base_volume_floor_is_config_driven`, `…is_deterministic` (×2) — config-driven + deterministic.
- `test_scoring.py::test_new_patterns_are_patterns_not_statuses` — force-flagging a new pattern changes NO setup status.
- `test_scanner.py::test_new_pattern_mirrors_match_record_json` — `is_<name>` == `record_json["<name>"]["flagged"]` for every result.
- `test_forward_testing.py::test_aggregates_by_new_patterns_exact`, `…_empty_cohort_is_na_padded` — `by_<name>` groups by stored mirror; empty cohort NA-padded (both True/False rows).
- `test_api_system_health.py::test_system_health_by_new_pattern_breakdowns_present` — both breakdowns in payload.
- `test_api_engine.py::test_new_patterns_served_from_storage_not_recomputed_keystone` — read path serves stored values when detectors patched to raise.
- `test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` — no new-pattern detector literal outside config.
- `test_methodology.py::test_catalog_documents_every_status_and_pattern`, `test_new_pattern_thresholds_match_patterns_config`, `test_incomplete_pattern_catalog_raises` — catalog completeness + boot guard fires.
- `test_config.py::test_pullback_ma_period_not_an_indicator_raises`, `…insufficient_history…`, `…nonpositive_percent…`, `…undercut_may_be_zero`, `test_flat_base_base_window_exceeds_lookback_raises`, `…nonpositive_ratio…` — config validators raise on invalid values, no silent default.

---

## Step 3 — Frontend tests

TC-12 independently re-verified via `cd apps/frontend && npx tsc --noEmit` → **exit 0** (no type errors). Chosen over `npm run build` to avoid clobbering the running dev server's `.next`. Dev handoff reports `npm run build` PASS (compiled + typechecked all 13 routes); reviewer confirmed typecheck pass.

---

## Step 3.5 — Functional test plan results

Live API base: `http://localhost:8835`. Frontend: `http://localhost:3835`. DB regenerated offline from the committed seed (latest snapshot 2026-05-28, Risk-on, 122 names).

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | Detectors flag positive series w/ pivot+invalidation | api/unit | Flag+pivot+invalidation; no-flag wrong shape | `test_patterns` positive/negative cases PASSED | PASS | Same contract dict as `detect_vcp` |
| TC-02 | Insufficient history → honest NA | api/unit | flagged=False, no fabricated level | `…is_na_never_fabricated` (×2) PASSED | PASS | |
| TC-03 | Config-driven (flips flag) + deterministic | api/unit | Threshold change flips; identical input identical out | `…config_driven…` + `…deterministic` PASSED | PASS | |
| TC-04 | Pattern-not-status | api/unit | setup unchanged; vcp unchanged | `test_new_patterns_are_patterns_not_statuses` PASSED + source seam verified | PASS | scoring.py:353 sets `setup` independently; patterns attached as separate keys 356–358 |
| TC-05 | Immutable mirror == record_json flag | api/unit | Equality for all rows | `test_new_pattern_mirrors_match_record_json` PASSED; live: 122/122 latest match | PASS | scanner.py:110–111 writes mirror once from `row["<name>"]["flagged"]` |
| TC-06 | `by_<name>` groups by mirror; empty NA-padded | api/unit | Both rows; n=0/mean=None empty | `…by_new_patterns_exact` + `…empty_cohort_is_na_padded` PASSED | PASS | forward_testing.py:602–625 via generic `_group_means`, no re-detect |
| TC-07 | System Health exposes both `by_<name>` | api/curl | Both keys + n per cohort | Live: `by_pullback_to_rising_dma` (n=163/1055), `by_flat_base_breakout` (n=48/1170) present beside `by_vcp` | PASS | HTTP 200 |
| TC-08 | Read path never re-detects (keystone) | api/integration | 200, served from snapshot when detector raises | `…served_from_storage_not_recomputed_keystone` PASSED | PASS | detectors referenced only in patterns.py + scoring.py (scan path) |
| TC-09 | No magic numbers | api/unit | No detector literal outside config | `test_engine_calc_code_has_no_magic_numbers` PASSED | PASS | sentinels 40/18/25/15 enforced |
| TC-10 | Catalog completeness + invalid-config boot fail | api/unit | Guard fires; validators raise | `test_incomplete_pattern_catalog_raises` + 6 config-validation tests PASSED | PASS | live `/api/methodology` shows 3 pattern + 6 setup entries |
| TC-11 | Full suite after DB regen | api/full | Exit 0; Risk-Off intact | 351 passed/4 skipped/0 failed; both bootstrap Risk-Off dates label "Risk-off" | PASS | DB regenerated offline, no live fetch |
| TC-12 | Frontend typechecks/builds | artifact | Build exit 0 | `tsc --noEmit` exit 0; handoff build PASS | PASS | |
| TC-13 | Filter by `pullback_to_rising_dma` | browser | Only flagged rows + badge/reason/invalidation | Unfiltered 122 → filtered **9** rows; all 9 carry the pullback badge w/ verbatim reason + concrete invalidation ($46.71 etc.) | PASS | DOM-asserted row count = API flagged count (9); distinct before/after shots |
| TC-14 | Filter by `flat_base_breakout` | browser | Same | Filtered **3** rows (TPH/GS/ADI); all carry flat-base badge + invalidation ($46.74 etc.) | PASS | DOM-asserted = API count (3) |
| TC-15 | Detail shows same pattern badge/invalidation | browser | Same as leaderboard | `/stocks/TPH`: both badges present, invalidation $46.71 (pullback) / $46.74 (flat-base) — identical to leaderboard | PASS | single source of truth |
| TC-16 | Methodology cards auto-render | browser | Meaning + thresholds + example | Both cards render ("Pullback to a rising DMA", "Flat-base breakout") w/ config thresholds + worked example | PASS | thresholds match `config.patterns.*` via `ref:` |
| TC-17 | System Health `by_<name>` panels + n + NA | browser | Numbers + n; NA below min-sample | Pullback-to-DMA −0.27% n=163 / non +2.39% n=1055; Flat-base +0.91% n=48 / non +2.08% n=1170; VCP +3.18% **n=27 ⚠** (honest low-sample marker) | PASS | values match API exactly |
| TC-18 | Regression J-16: VCP intact | browser | VCP filter/badge/glossary/by_vcp unchanged | VCP filter → 4 rows all w/ VCP badge; VCP card on methodology; `by_vcp` panel intact | PASS | |
| TC-19 | Regression J-12: 6 setups + 3 patterns | browser | All present from catalog | 10 cards: 6 setups + 3 patterns (VCP + 2 new) | PASS | |
| TC-20 | Regression J-02 + J-07 | browser | Sector/Actionable filters work; Risk-Off Actionable=0 | Sector=Technology → 58 Tech rows; Actionable filter functional; date 2025-04-04 → regime "Risk-off", Actionable count **0** | PASS | new patterns never promote to Actionable |

**20/20 test cases passed.**

---

## Step 4 — Chrome MCP browser checks

Frontend reachable at `http://localhost:3835` (HTTP 200). All flows driven via Chrome MCP; the pattern filter is a React-controlled native `<select>`, so changes were dispatched with the native value setter + a bubbling `change` event, and live DOM was asserted immediately before each capture (per the iter-6 browser-concurrency guardrail). Browser was the sole Chrome consumer during capture.

Evidence (under `reports/qa/goal-…-iter-9-evidence/`, all 7 sha256-distinct):
- `TC-13-stocks-unfiltered.png` (122 rows) vs `TC-13-stocks-pullback-filtered.png` (9 rows) — distinct hashes, DOM row-count asserted.
- `TC-14-stocks-flatbase-filtered.png` (3 rows).
- `TC-15-detail-TPH.png` (both pattern badges on detail).
- `TC-16-methodology-patterns.png` (both new cards).
- `TC-17-system-health-breakdowns.png` (all three breakdown panels).
- `TC-20-riskoff-actionable-zero.png` (Risk-off, Actionable=0).

```
sha256 (16-char prefix):
  ce0d75254c525b09  TC-13-stocks-unfiltered.png
  41da3e2a5819f075  TC-13-stocks-pullback-filtered.png
  405f99438c175d00  TC-14-stocks-flatbase-filtered.png
  675bcb171c5e8edd  TC-15-detail-TPH.png
  8f3fc359c12157f2  TC-16-methodology-patterns.png
  a89d47b49de0f207  TC-17-system-health-breakdowns.png
  d61c4cf51e733920  TC-20-riskoff-actionable-zero.png
7 files / 7 unique hashes — no duplicate before/after shots.
```

---

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the new capability?** Yes — `/stocks` gained a Pattern filter listing all 3 patterns + per-pattern badges; `/methodology` auto-renders 2 new pattern cards; `/system-health` gained 2 new breakdown panels.
2. **Can the user see, understand, and control the new capability?** Yes — filter (control), badge tooltip + glossary card (understand), forward-return breakdown with n (judge value).
3. **Relying on old generic pages for new functionality?** No — patterns ride the existing canonical homes exactly as the spec intends; no new generic surfaces.
4. **Technically complete but product-wise underexposed?** No — every new value is filterable, explained, and forward-tested in the UI.

**Verdict:** UI-PASS

---

## Anti-goal seam verification (direct source check, not status.json)

| Seam | Evidence |
|------|----------|
| Pattern-not-status | `scoring.py:353` sets `setup` independently; pattern results attached as separate row keys (356–358); `test_new_patterns_are_patterns_not_statuses` PASSED |
| No-lookahead | Detectors called on `inv_closes` (the same ≤D as-of bars VCP uses) at `scoring.py:338,341`; referenced only on the scan path |
| No magic numbers | `patterns.py` thresholds read from `cfg.patterns.<name>.*`; `test_no_magic_numbers` PASSED |
| Immutable mirror written once | `scanner.py:110–111` writes both mirrors from `row["<name>"]["flagged"]` in the single `ScannerResult(...)` |
| No recompute in read path | `forward_testing.py:602–625` `by_<name>` reads `is_<name>` mirror via `_group_means`; keystone read-path test PASSED |
| Config-driven UI vocabulary | `/methodology` cards + badge tooltips auto-render from the config-backed catalog (3 patterns, 6 setups) |
| Honest NA/n | System Health VCP cohort n=27<30 shows ⚠ marker; cohorts NA-padded; no fabricated numbers |
| Risk-Off gates Actionable | 2025-04-04 Risk-off run → Actionable=0 (browser-verified) |
| Scope | No `/research` route/page/endpoint in the diff (out of scope); canonical scores/buckets/setup-enum/regime untouched |

---

## Blockers

None.

---

## Status

All gates green: backend suite 351 passed / 0 failed, frontend typecheck clean, 20/20 functional cases pass, UI-PASS, all anti-goal seams intact, no regression. Recommend marking the iteration complete.

**Verdict:** PASS
