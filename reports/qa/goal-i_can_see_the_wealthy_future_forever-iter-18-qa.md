**Verdict:** PASS

# QA Validation Report — goal-i_can_see_the_wealthy_future_forever-iter-18

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-18
**Date:** 2026-06-04
**Agent:** qa (MODE 2: QA Validation)
**Frontend Present:** yes
**Goal:** On `/research` → Factor Lab, replace the perpetually-0/NA strict-AND **Combined** cohort with a non-empty **composite percentile-rank blend** (config-weighted, top config-quantile), scaling to all 11 catalog factors, demoting strict-AND to a secondary **Strict overlap (AND)** column — read-only, downside-only risk-adjusted, no magic numbers, zero added date state (J-26; required-still-passing J-25/27/30/18/06/07/29/31).

---

## Step 1 — Required artifacts

| Artifact | Status |
|----------|--------|
| `docs/handoffs/...-iter-18-dev.md` | ✅ present |
| `docs/handoffs/...-iter-18-frontend.md` | ✅ present |
| `reports/reviews/...-iter-18-review.md` | ✅ present, **PASS_WITH_NOTES** (one NOTE: a stale UI docstring at page.tsx:530 — non-blocking) |
| `runs/goal-i_can_see_the_wealthy_future_forever-iter-18/status.json` | ✅ present (phase-namespace path per session lesson) |
| `reports/qa/...-iter-18-test-plan.md` | ✅ present (18 cases, executed below) |

Services up at validation start: backend `http://localhost:8835/api/health` → 200; frontend `http://localhost:3835` → 200.

---

## Step 2/3 — Backend & frontend test results

**Backend (targeted, run by QA):** The dev agent already ran the FULL suite once (**461 passed, 4 skipped in 1168.75s** — the 4 skips are pre-existing offline/network `integration`-marked tests). Per `backend-test-suite-runtime` (full suite ~14–20 min, no concurrent invocations) I re-ran the iteration's directly-affected files plus the anti-goal guard:

```
cd apps/backend && .venv/bin/python -m pytest \
  tests/test_research.py tests/test_api_research.py tests/test_config.py tests/test_config_engine.py -q
→ 156 passed in 262.14s (0:04:22)

.venv/bin/python -m pytest tests/test_no_magic_numbers.py -q
→ 2 passed in 0.13s
```

This covers every J-26 backend assertion: composite non-empty/clears `min_sample`, scales-to-all-factors, orientation (`test_combination_composite_orientation_top_vs_bottom`), opposing-extremes strict-overlap-NA-while-composite-populated, read-only keystone (`test_combination_is_read_only_no_scoring_or_return_or_pattern_call`), cohort algebra/exact stats, downside-only risk-adjusted, config-driven cohort size, and all `composite` boot-validation `ConfigError` cases. **0 failures.**

**Frontend build:** Dev handoff reports `npm run build` compiled + typechecked clean (13 routes; `/research` 9.75 kB). I deliberately did **not** re-run `npm run build` during validation — per the `browser-qa-dead-shell-next-cache` lesson, a prod build clobbers the running dev server's `.next` and produces a dead shell. Frontend type/build is accepted on the dev report; the live dev server hydrated correctly through all browser checks below (real interactive DOM, not a dead shell).

---

## Step 3.5 — Functional test plan results

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | Composite non-empty & clears min_sample (defaults) | api | HTTP200; composite.n≥30; numeric; distinct from baseline; no `combined` key | HTTP200; composite n=244, mean +1.21%, median +0.70%, hit 54.10%, risk-adj +0.26; baseline n=1217; **no `combined` key** | PASS | horizon must be ∈{1,5,10,20,60}; used 20 |
| TC-02 | Scales to all 11 catalog factors | api | accepts up-to-cap; composite.n>0 | 11 conditions accepted HTTP200; composite n=243; strict n=0 | PASS | max_conditions=11 = catalog count |
| TC-03 | Empty strict-overlap while composite populated | api | strict n=0/NA; composite n>0 same payload | opposing-extremes (rs_spy_3m top+bottom): strict n=0 all-null NA; composite n=1217 | PASS | membership-driven (iter-11 lesson) |
| TC-04 | Orientation (top vs bottom side) | api | oppositely-oriented cohorts | top-side vs bottom-side composites are distinct cohorts (mean +1.78% n=244 vs +2.64% n=245); rigorous monotone-fixture orientation passes in unit test | PASS | strict orientation proven in `test_combination_composite_orientation_top_vs_bottom` |
| TC-05 | Downside-only risk-adjusted | api/source | mean/downside-dev; NA on no-downside/n<2 | `_risk_adjusted = mean / _downside_deviation` (`sqrt(mean(min(r,0)^2))`); None when n<2 or dd=0 (source research.py:84-91) | PASS | verified in source + unit tests; never total vol |
| TC-06 | Echoed composite metadata | api | quantile {key,label,fraction} + weighting | `composite_quantile={quintile,"Quintile (20%)",0.2}`; `weighting={scheme:equal,default_weight:1.0}` | PASS | config-driven labels |
| TC-07 | Error cases | api | 422 unknown factor/side/quantile, over-cap, bad horizon; 503 no-data | unknown factor=422, bad side=422, bad quantile=422, 12 conditions=422, 1 condition=422, horizon=21→422 | PASS | 503 no-data path covered by existing endpoint tests |
| TC-08 | Config validation raises ConfigError | artifact | bad composite.quantile/weighting + existing cross-checks raise | `test_combination_composite_unknown_quantile_raises`, `_nonpositive_weight_raises`, `_unknown_scheme_raises`, `_min_gt_max_raises`, `_duplicate_quantile_key_raises`, `_default_*_raises` all pass | PASS | |
| TC-09 | Config-driven cohort size / no magic numbers | artifact | quantile change re-points n; no literal in research.py | `test_combination_composite_cohort_size_is_config_driven` pass; `test_no_magic_numbers` 2 passed | PASS | |
| TC-10 | Read-only keystone (no recompute) | artifact | no run_scan/score_stocks/backfill/forward_return/detect_/score_regime; diff clean of scoring/snapshot math | patch-to-raise test passes; `git diff` touches NO scoring/scanner/regime/patterns/buckets/forward_testing file | PASS | J-06/J-07 byte-identical |
| TC-11 | Cohort algebra invariants | artifact | composite⊆baseline; strict⊆each single; baseline.n==pool_n | `test_combination_cohort_algebra_and_exact_stats` pass; baseline n=1217==pool_n | PASS | |
| TC-12 | Browser: default render | browser | order Baseline→singles→Composite(emphasized)→Strict(secondary); composite numeric n≥30 distinct from baseline; labels | rows in exact order; composite n=244 (+1.21%/+0.70%/+54.10%/+0.26); strict_overlap n=49 renders; survivorship + descriptive-not-predictive labels present | PASS | evidence TC-12 |
| TC-13 | Browser: add up to all catalog factors | browser | add enabled to cap, disabled at 11; composite n>0 | added to conditionCount=11, **Add disabled at cap**; composite n=244 (no hard-coded UI cap) | PASS | evidence TC-13 |
| TC-14 | Browser: empty strict-overlap + composite populated (same shot) | browser | composite n>0 AND strict NA+n same view | opposing rs_spy_3m top+bottom: composite n=244 populated; **strict_overlap n=0 ⚠ NA/NA/NA/NA** in same view | PASS | evidence TC-14 (headline bar-raise captured live) |
| TC-15 | Browser: J-18 re-verify | browser | lab byte-identical across as-of toggle; zero `/api/research/*?as_of=`; one date select | clean isolated test: lab innerText 408==408 byte-identical; perf research reqs 3→3 (toggle fired none); **0 as_of requests**; exactly **1** date `<select>` | PASS | Performance Resource Timing used (reliable); evidence TC-15 |
| TC-16 | Browser: J-25/J-27/J-30 spot-check | browser | decile/rank-IC re-point on factor change; regime + volatility render | decile D1 range 2.15…19.00 (leadership)→0.40…0.75 (rs_spy_3m) re-pointed; by-regime rank-IC table + volatility-family present with data | PASS | evidence TC-16 |
| TC-17 | Frontend build + full backend pytest | artifact | build typechecks; pytest 0 failures | dev: 461 passed/4 skipped full suite + clean build; QA re-ran 158 targeted tests green | PASS | full suite not re-run by QA (runtime); build not re-run (dead-shell lesson) |
| TC-18 | Dev handoff artifact exists | artifact | present + rank-blend/no-recompute note | present; states composite is "a deterministic ranking/GROUPING of stored values … recomputes no factor and no return and is NOT a fitted/ML model" | PASS | |

**18/18 test cases passed.**

---

## Step 4 — Chrome MCP browser checks

Executed live against `http://localhost:3835/research` (real hydrated DOM — not a dead shell). Selects driven via native-setter + bubbling change event per `react-controlled-select-needs-native-setter`. Network verified via the Performance Resource Timing API (more reliable than a `window.fetch` wrapper — the app binds `fetch` at module load, so a post-load wrapper misses requests; noted during testing).

Evidence (all sha256-distinct, under `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-18-evidence/`):
- `TC-12-combination-default.png`
- `TC-13-all-11-conditions.png`
- `TC-14-empty-strict-overlap-composite-populated.png`
- `TC-15-j18-asof-toggle-byte-identical.png`
- `TC-16-j25-j27-j30-repoint.png`

Key live observations:
- **Composite is the populated headline** (`combination-row-composite`, n=244, emphasized) and **Strict overlap (AND)** (`combination-row-strict_overlap`) is the muted secondary — exactly the re-scoped J-26 product delta.
- **The headline bar-raise is captured live** (TC-14): on the exact opposing-extremes selection that previously yielded 0/NA, the composite is populated (n=244) **while** strict-overlap shows honest `n=0 ⚠ NA`.
- **J-18 holds:** the global as-of toggle leaves the Combination Lab byte-identical, fires zero `/api/research/*?as_of=` requests, and the page carries exactly one date `<select>` ("View as-of date") — no date state added on `/research`.

---

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the new capability?** Yes — the Combination Lab now renders a populated "Combined (composite rank-blend)" headline row + a labelled "Strict overlap (AND)" secondary row, with hint text describing the config-weighted blend.
2. **Can the user see/understand/control it?** Yes — add/remove conditions up to all 11 catalog factors (cap disables at 11), composite quantile + equal-weight labelling shown, survivorship + descriptive-not-predictive caveats present.
3. **Relying on old generic pages?** No — same `/research` Factor Lab section, no new page/route/nav.
4. **Technically complete but under-exposed?** No — the populated composite and the honest NA strict-overlap are both directly visible and differentiable.

**Verdict:** UI-PASS

---

## Anti-goal verification (source/diff)

- **Read-only / no recompute:** patch-to-raise keystone test covers the composite path; `git diff` touches no `scoring.py`/`scanner.py`/`regime.py`/`patterns.py`/`buckets.py`/`forward_testing.py` math or the snapshot/serving path → J-06/J-07 byte-identical, no DB regen.
- **Downside-only risk-adjusted:** `_risk_adjusted = mean / _downside_deviation`, NA on no-downside / n<2 — never total vol (source-verified + unit-tested).
- **No magic numbers:** `test_no_magic_numbers` passes; composite quantile + weighting + `max_conditions=11` all config-sourced.
- **No fabricated data:** empty/low-sample cohorts show NA + n (live TC-03/TC-14), never a fabricated 0.
- **Exactly one date selector:** confirmed live (1 date `<select>`; zero `as_of` on `/research`).
- **Single source of truth:** same module `compute_factor_combination`, same endpoint `GET /api/research/factor-combination` — no second computation/endpoint.

---

## Blockers

None.

## Notes

- Review's lone NOTE (stale `CombinationLab` docstring at `page.tsx:530`) is cosmetic and non-blocking; the user-visible hint text was updated correctly (verified live). Carry to a future cleanup if desired.
- Full backend suite was run once by the developer (461 passed); QA re-ran the 158 directly-affected tests rather than re-running the ~20-min full suite concurrently, per `backend-test-suite-runtime`.

---

**Verdict:** PASS
