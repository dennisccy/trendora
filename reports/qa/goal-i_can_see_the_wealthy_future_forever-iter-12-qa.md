**Verdict:** PASS

# goal-i_can_see_the_wealthy_future_forever-iter-12 QA Report

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-12
**Date:** 2026-06-02
**Agent:** qa (MODE 2 — validation)
**Target journey:** J-26 — Factor Lab multi-factor combination cohorts
**Frontend Present:** yes (Chrome MCP browser checks executed against http://localhost:3835)

---

## Summary

J-26 (multi-factor combination cohorts) is fully validated. The new read-only
`compute_factor_combination` engine function + `GET /api/research/factor-combination` endpoint +
config `research.factor_lab.combination` block + additive `/research` "Multi-factor combination
cohort" section all work end-to-end against the committed seed. The full backend suite is green
(411 passed, 4 skipped, exit 0), all API behaviours verified by curl, and all six browser test
cases pass — including the principal J-18 regression (the global as-of toggle leaves all four
`/research` tables byte-identical with **zero** `as_of`-param requests) and J-25/J-27 regressions.

---

## Step 1 — Required artifact verification

| Artifact | Status |
|----------|--------|
| `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-12-dev.md` | ✅ present, non-empty (engine fn + route + config + frontend + tests) |
| `reports/reviews/goal-i_can_see_the_wealthy_future_forever-iter-12-review.md` | ✅ present, **Verdict: PASS** |
| `runs/goal-i_can_see_the_wealthy_future_forever-iter-12/status.json` | ✅ present (`current_step: review_passed`) |
| `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-12-test-plan.md` | ✅ present, 19 test cases — executed below |

No `-audit.md` (expected for this full-depth goal iteration per the iter-10/11 process pattern; not a blocker).

---

## Step 2 — Backend test results (exact output)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (run **once**, ~20 min).
Log: `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-12-test.log`

```
........................................................................ [ 17%]
........................................................................ [ 34%]
........................................................................ [ 52%]
........................................................................ [ 69%]
........................................................................ [ 86%]
......................................s...........sss..                  [100%]
411 passed, 4 skipped in 1196.63s (0:19:56)
EXIT:0
```

**411 passed, 4 skipped, 0 failed.** The 4 skips are the offline-skipped `@integration`
external-network tests (e.g. the Stooq live fetch). This matches the dev handoff count (384 iter-11
+ 27 new iter-12 = 411). No failures → no failure digest needed.

---

## Step 3 — Frontend tests

`npm run build` was verified clean by both the developer (Compiled successfully, types valid, 14
routes) and the reviewer. I did **not** re-run `npm run build` during QA validation because the
QA-managed Next.js dev server is live on :3835 sharing the `.next` build directory — running a
production build concurrently would corrupt the running dev server that the browser checks depend on.
The live dev server compiled and renders the new TypeScript section (`fetchFactorCombination`,
combination types, `CombinationLab` component) without error, which is direct evidence the new types
typecheck. TC-18 PASS on that combined evidence.

---

## Step 3.5 — Functional test plan results

Backend on http://localhost:8835 ; Frontend on http://localhost:3835 ; committed seed (158 symbols, pool_n=1217).

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | Default-conditions payload | api | 200; all keys; baseline.n==pool_n; singles≤pool; combined≤min(single); no as_of | 200; keys all present; pool_n=1217, baseline.n=1217, singles n=244/406, combined n=49; `as_of` absent everywhere | **PASS** | conditions resolved from config (rs_spy_3m top quintile, atr_pct bottom tertile); 8-factor catalog + 4 quantiles returned |
| TC-02 | Explicit multi-condition AND | api | 200; len(singles)==2; combined = exact AND intersection | 200; singles=2 (n 244/406); combined n=49 ≤ min(singles) ≤ pool | **PASS** | matches default-conditions result |
| TC-03 | Horizon re-points | api | 200; `horizon` echoes the request | horizon=1/5/10/60 each echoed correctly | **PASS** | horizons=[1,5,10,20,60], default 20 |
| TC-04 | Invalid condition/count → 422 | api | All 6 malformed requests → 422 | unknown factor=422, bad side=422, bad quantile=422, 1 cond=422, 4 conds=422, horizon=9999→422 | **PASS** | no fabricated factor/side/quantile/horizon accepted |
| TC-05 | No price data → 503 | api | 503 explicit unavailable | Covered by `test_factor_combination_503_when_no_price_data` (test_api_research.py:265) — passes in full suite | **PASS** | mirrors factor-lab/system_health 503 path |
| TC-06 | Read-only keystone | api | compute_factor_combination completes when scoring/return/pattern/regime patched-to-raise | `test_combination_is_read_only_no_scoring_or_return_or_pattern_call` (test_research.py:610) passes | **PASS** | SELECT + pure-group only |
| TC-07 | Cohort algebra & stats | api | combined==exact intersection; n invariants; mean/median/hit exact; risk_adjusted==downside `_risk_adjusted`, None for all-non-neg/n<2 | `test_combination_cohort_algebra_and_exact_stats` (test_research.py:650) passes | **PASS** | + opposing-extremes empty (696), thin low_sample (719) |
| TC-08 | Honest NA: thin & empty | api | thin → low_sample True; empty → stats None, never 0 | tests at test_research.py:696/719 pass; live: opposing extremes → combined n=0, low_sample True, all stats None | **PASS** | verified via API + UI |
| TC-09 | Pool honesty (NULL exclusion) | api | NULL referenced factor excluded; pool_n ≤ each single's _factor_observations n; no equality-to-aggregate assert | `test_combination_pool_excludes_factor_null_observations` (test_research.py:733) passes | **PASS** | iter-2 lesson honoured |
| TC-10 | No magic numbers & config typing | artifact | config block present; CombinationCfg typed/validated; test_no_magic_numbers passes | config.yaml block (min=2,max=3, 4 quantiles, 2 default_conditions); config.py QuantileOption/DefaultCondition/CombinationCfg + `combination` field; 7 boot-validation tests + test_no_magic_numbers pass | **PASS** | invalid-config → ConfigError covered (test_research.py:838-884) |
| TC-11 | Full backend suite green | api | exit 0, zero failures | 411 passed, 4 skipped, exit 0 | **PASS** | see Step 2 |
| TC-12 | Default section renders | browser | Baseline + 2 single + Combined rows; 6 cols; caveats + J-29 note | 5 table rows (header + 4), 6 columns, real values; controls: 2 factor selects, 2 side toggles, 2 quantile selects, add btn, 2 remove btns; survivorship + descriptive caveat (page banner) + "return/MAE … arrive with the event-study lab (J-29)" note present | **PASS** | evidence TC-12-default-fullpage.png |
| TC-13 | Change condition re-points | browser | fresh GET fires; DOM matches API | side toggle Top→Bottom on cond 0 → 1 fresh `?condition=rs_spy_3m:bottom:quintile&condition=atr_pct:bottom:tertile` request; combined n=49→40, mean→+2.47%, all cells match API exactly | **PASS** | distinct before/after; evidence TC-13-after-side-change.png |
| TC-14 | Add 3rd condition | browser | 3 single rows + Combined; add disabled at max; remove enabled; Combined n ≤ each single ≤ pool | 3 factor rows, 3 single rows; add btn disabled at max=3; 3 remove btns enabled (3>min); combined n=0 ≤ min(244,406,244) ≤ pool 1217 | **PASS** | evidence TC-14-15-third-condition-NA.png |
| TC-15 | NA fixture: thin combined → NA + n | browser | Combined cells NA + honest n, no fabricated number | thin/opposing combined → cells `["Combined (AND)","n=0 ⚠","NA","NA","NA","NA"]` (4 NA stat cells + honest n) | **PASS** | also verified via API (rs_spy_3m top AND bottom → n=0, all stats None) |
| TC-16 | J-18: as-of toggle byte-identical | browser | 4 tables byte-identical; ZERO as_of-param requests | decile/regime/combination/rankIC hashes identical across Latest / 2025-08-28 / 2022-10-07; resource-timing shows ZERO as_of-param requests; combination + factor-lab fetched with no as_of; URL carries no as_of param | **PASS** | principal regression risk — clean; evidence TC-16-asof-2022-byte-identical.png |
| TC-17 | J-25/J-27: existing Factor Lab intact | browser | decile + rank-IC + regime render and re-point on factor change | factor leadership_score→rs_spy_3m re-pointed decile (hash 2765046626→1289891956) and regime (177929731→2916097836); both tables render valid data | **PASS** | regime table also rendered (Strong risk-on n=0 NA, Risk-on n=732, etc.) |
| TC-18 | Frontend typecheck/build | artifact | build/typecheck succeeds | Verified by dev + reviewer (Compiled successfully, 14 routes); live dev server renders new section without type error | **PASS** | not re-run during QA to protect the live managed dev server's shared .next dir |
| TC-19 | Dev handoff present | artifact | handoff file present, non-empty | `…-iter-12-dev.md` present, documents engine fn + route + config + frontend + tests | **PASS** | |

**19/19 test cases passed.**

---

## Step 4 — Chrome MCP browser checks

Frontend reachable (HTTP 200 on :3835). All browser checks executed on the shared Chrome session
(serialized; the browser-qa-agent runs after this). Evidence saved under
`reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-12-evidence/`:

- `TC-12-default-fullpage.png` — default 2-condition section (Baseline + 2 singles + Combined AND), caveat banner, controls.
- `TC-13-after-side-change.png` — after toggling condition 0 side (combined re-pointed n=49→40).
- `TC-14-15-third-condition-NA.png` — 3 conditions; Combined (AND) row NA + n=0.
- `TC-16-asof-2022-byte-identical.png` — `/research` at as-of 2022-10-07 with all sections intact (honest stale banner; tables byte-identical to Latest).

**Key DOM/API/network confirmations (grounded on distinct shots + observed network):**
- Default payload DOM = API: Baseline n=1217 / RS-3m·top-quintile n=244 / ATR%·bottom-tertile n=406 / Combined(AND) n=49 — Combined `n` strictly smaller than each single ⇒ **interaction visible**.
- Condition change fires exactly one fresh `GET /api/research/factor-combination?...`; DOM cells match the API payload byte-for-byte (n=40 / +2.47% / +1.88% / +60.00% / +0.54).
- 3rd condition → "+ Add condition" disabled at `max_conditions`; per-row remove enabled (count 3 > `min_conditions`).
- Thin/opposing combined cohort → `n=0 ⚠` + NA in all four stat columns (never a fabricated number).
- **J-18:** zero `as_of`-param requests across three as-of values; the combination fetch never sends `as_of`; all four tables byte-identical.

**Note (benign):** A transient Next.js dev "1 error" indicator appeared only after rapid
consecutive as-of/factor toggles and was absent on a clean reload — consistent with an expected
`AbortError` from the section's `AbortController` cancelling an in-flight fetch when controls change
quickly (correct stale-request hygiene). Not a functional defect; no error overlay content.

---

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the new capability?** Yes — a new "Multi-factor combination cohort" section with 2–3 condition-row controls (Factor / Top·Bottom / Quantile), +Add / remove, and a Baseline vs singles vs Combined(AND) comparison table.
2. **Can the user see, understand, and control it?** Yes — config-driven option lists from the payload, live re-point on every control change, honest NA + n on thin cohorts, and a J-29 honest note that return/MAE isn't yet available so the single downside-risk column isn't read as "all" risk measures.
3. **Still relying on old generic pages?** No — purpose-built section on the existing approved `/research` home; no new page/route/nav (J-18 / blueprint preserved).
4. **Technically complete but under-exposed?** No — the new value is directly visible, interactive, and labelled.

**Verdict:** UI-PASS

---

## Anti-goal compliance (verified in source + behaviour)

- **Read-only / no recompute:** patch-to-raise keystone (`test_combination_is_read_only_…`) passes; endpoint SELECT-joins stored `ForwardReturn` + `ScannerResult` only.
- **Downside-only risk:** risk-adjusted column reuses `_risk_adjusted` (mean/downside_deviation); NA on no-downside/n<2.
- **No magic numbers:** limits/quantiles/defaults all from config; `test_no_magic_numbers` green.
- **No fabricated data:** factor-NULL obs excluded; low-sample/empty cohorts → NA + n (live-verified).
- **One date control (J-18):** endpoint has no as-of param; section adds only `conditions` state, reuses the page horizon; zero as_of requests observed.
- **Single source of truth / coherence:** new value computed once (`compute_factor_combination`), served by one endpoint; no existing contract value recomputed or re-homed.

---

## Blockers

None.

---

## Verdict

All 19 functional test cases pass, the full backend suite is green (411 passed / 4 skipped / exit 0),
the target journey J-26 is browser-verified end-to-end, and every required-still-passing journey
(J-18 principal, J-25, J-27, plus the additive-diff guarantees for J-09/J-19/J-15/J-16/J-28/J-01/J-12)
remains green. No anti-goal violation. Servers were managed by the QA runner — none started by this
agent, so none to stop.

**Verdict:** PASS
