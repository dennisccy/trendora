# goal-i_can_see_the_wealthy_future_forever-iter-13 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-13
**Date:** 2026-06-02
**Frontend Present:** yes

## Phase Goal

Make volatility a first-class **family of four** factors on the `/research` Factor Lab — ATR% (level), HV (level), VCP-style contraction (change), downside/semivol — each computed once in the scoring/snapshot path (bars ≤ D, no lookahead), stored on the immutable snapshot, and read verbatim by `compute_factor_lab` to render a decile table (raw + downside-risk-adjusted + `n`), Spearman rank-IC, and by-regime split — **without** any volatility value entering a weighted score (J-06/J-07 must stay byte-identical after the DB regen).

## Test Cases

### TC-01 — New indicator math: exact values + NA on short history
**Type:** api (unit — `apps/backend/tests/test_indicators.py`)
**Preconditions:** Backend repo; pytest available.
**Steps:**
1. Run `hist_volatility(closes, window)`, `vol_contraction(closes, recent, prior)`, `downside_vol(closes, window)` on a known fixed series with hand-computed expected values.
2. Run each with fewer than the required bars; run `vol_contraction` with a zero prior; run `downside_vol` on an all-up (non-negative-return) series.
**Expected outcome:** Exact numeric matches on the fixed series; NA on insufficient history; `vol_contraction` NA on zero prior; `downside_vol` returns 0/NA (never penalises upside) on all-up series; HV expressed as a percent comparable to ATR%.
**Pass criteria:** All three function tests pass; periods are read as arguments (no literals); negative-leg-only semantics confirmed for `downside_vol`.

### TC-02 — Score-invariance regression (CRITICAL keystone — protects J-06/J-07)
**Type:** api (unit — `apps/backend/tests/test_scoring.py`)
**Preconditions:** Volatility additions present in `scoring.py`/`models.py`/`config.yaml`.
**Steps:**
1. Score a representative stock set with the volatility additions present.
2. Compare Leadership / Entry Quality / Risk scores, A–E buckets, setup status, candidate counts, and regime label against the pre-change baseline.
**Expected outcome:** Every score, bucket, setup status, candidate count, and regime label is **byte-identical** to baseline; the three new values never pass through `_build_score`.
**Pass criteria:** Test asserts byte-identical results; source inspection confirms none of `hv`/`vcp_contraction`/`downside_vol` appears in any `config.scores.*.weights` and `_build_score` is unchanged.

### TC-03 — Config boot resolves new sources; typo fails loudly; no magic numbers
**Type:** api (unit — `apps/backend/tests/test_config.py`)
**Preconditions:** Three new `research.factor_lab.factors` entries + `FACTOR_TYPED_COLUMNS` extension + new `indicators` windows.
**Steps:**
1. Boot config; assert the three new factor sources (`hv`, `vcp_contraction`, `downside_vol`) resolve.
2. Inject a typo/unresolvable factor source and boot.
3. Run `test_no_magic_numbers`.
**Expected outcome:** Valid sources resolve at boot; the typo raises `ConfigError` loudly (never a silent default); `test_no_magic_numbers` stays green (only structural literals `0/1/2/100` added to math).
**Pass criteria:** Resolve test passes, `ConfigError` raised on typo, `test_no_magic_numbers` green; new windows/labels live in config.

### TC-04 — `compute_factor_lab` over the three new factors (decile + rank-IC + by-regime + honest NA)
**Type:** api (integration — `apps/backend/tests/test_research.py`)
**Preconditions:** DB regenerated with the new stored values.
**Steps:**
1. Call `compute_factor_lab` for each of `hv`, `vcp_contraction`, `downside_vol` on the seed.
2. Inspect deciles, rank-IC `{value, n}`, and `by_regime` split; inspect a low-sample regime/decile and a downside-undefined decile.
**Expected outcome:** Populated deciles, numeric rank-IC, and by-regime split for each factor; low-sample decile/regime → NA + `n` (never fabricated 0); risk-adjusted column is **downside-only** (None when a decile has no downside / n<2).
**Pass criteria:** All assertions pass; NA cells carry `n`; risk-adjusted is downside-only.

### TC-05 — Read-only keystone: lab recomputes nothing
**Type:** api (regression — `apps/backend/tests/test_research.py`)
**Preconditions:** Patch-to-raise harness on `run_scan`/`score_stocks`/`detect_*`/`score_regime`.
**Steps:**
1. Run `compute_factor_lab` / `GET /api/research/factor-lab` for the new factors with those functions patched to raise.
**Expected outcome:** No exception raised — the lab reads stored values only and recomputes nothing.
**Pass criteria:** Existing read-only patch-to-raise test still passes for the new factors.

### TC-06 — Error & edge cases (unknown key 422, NULL excluded, short-history NA)
**Type:** api
**Preconditions:** Backend running on port 8835.
**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8835/api/research/factor-lab?factor=not_a_factor"`
2. Verify a factor-NULL observation is excluded from bucketing; verify a short-history stock yields NA volatility values that propagate to honest NA.
**Expected outcome:** Unknown factor key → **422**; NULL observations excluded (never bucketed/fabricated); short-history → NA, never a fabricated 0.
**Pass criteria:** HTTP 422 on unknown key; no fabricated values appear in any decile.

### TC-07 — Full backend suite green after DB regen
**Type:** api (suite)
**Preconditions:** DB regenerated (delete `apps/backend/data/trendora.db`, reboot so `create_all` + `bootstrap_runs` + `backfill_run_forward_returns` rebuild).
**Steps:**
1. Run the **full** backend pytest **once** (~14 min; do NOT run two pytest invocations concurrently).
**Expected outcome:** All backend tests pass on the regenerated DB.
**Pass criteria:** Exit code 0; pass/fail counts recorded verbatim.

### TC-08 — Frontend typecheck/build
**Type:** artifact
**Preconditions:** Frontend deps installed.
**Steps:**
1. Run `npm run build` in `apps/frontend`.
**Expected outcome:** Build succeeds with no type errors (including the optional `<optgroup>` grouping change).
**Pass criteria:** Build exits 0.

### TC-09 — J-30 browser: each of the four volatility measures renders fully
**Type:** browser
**Preconditions:** Backend (8835) + frontend (3000) running; DB regenerated.
**Steps:**
1. Navigate to `/research`; open the factor dropdown.
2. Select each of `atr_pct`, `hv`, `vcp_contraction`, `downside_vol` in turn.
3. For each, capture the decile table (raw mean + downside-risk-adjusted + `n`), the numeric rank-IC with `n`, and the by-regime split. De-dup screenshots by sha256.
**Expected outcome:** Each measure renders a populated decile table (both raw and downside-risk-adjusted, each with `n`), a numeric rank-IC with `n`, and the by-regime split; survivorship-bias + descriptive-not-predictive labels visible; "risk" is downside-only.
**Pass criteria:** All four measures render the full set of evidence; labels present; distinct (sha256-deduped) screenshots per claim.

### TC-10 — J-30 honest-NA cell captured (regime/decile, not horizon shrinkage)
**Type:** browser
**Preconditions:** As TC-09.
**Steps:**
1. With a new volatility factor selected, locate a low-sample/empty **regime** (e.g. Strong risk-on / Defensive at n=0) or a downside-undefined decile (all-non-negative → `risk_adjusted` NA).
2. Capture it.
**Expected outcome:** The cell shows **NA + n**, never a fabricated 0.
**Pass criteria:** At least one genuine NA cell captured via a low-sample regime or downside-undefined decile (NOT via horizon shrinkage — `n` is ~horizon-independent in this seed).

### TC-11 — Contraction cross-check vs existing VCP forward-test evidence
**Type:** browser / api
**Preconditions:** As TC-09; System Health VCP-vs-non-VCP breakdown available.
**Steps:**
1. Read `vcp_contraction`'s decile/IC and confirm it derives from the SAME stored `forward_returns` observations the System Health VCP-vs-non-VCP breakdown uses (no recomputation).
2. State the reported direction honestly.
**Expected outcome:** `vcp_contraction` is consistent with the existing VCP evidence (same stored pool, no recompute); the reported direction is stated honestly — if contraction does NOT predict, that is a valid descriptive finding.
**Pass criteria:** Same-pool consistency confirmed; direction reported honestly (descriptive acceptance).

### TC-12 — J-18 regression: as-of toggle does not re-point the Factor Lab
**Type:** browser
**Preconditions:** As TC-09.
**Steps:**
1. With a new volatility factor selected, toggle the global as-of date.
2. Observe network requests and table values.
**Expected outcome:** Factor-Lab tables stay **byte-identical** across the toggle; **zero** `as_of`-param requests fire.
**Pass criteria:** Tables unchanged; no `as_of` request observed for the new factors.

### TC-13 — J-25 / J-27 regression: re-point on factor change
**Type:** browser
**Preconditions:** As TC-09.
**Steps:**
1. Switch among factors and confirm the decile table, rank-IC, and regime split re-render and re-point each time.
**Expected outcome:** J-25 (decile/IC) and J-27 (regime split) still render and re-point correctly on factor change.
**Pass criteria:** Tables update on every factor change; no stale data.

### TC-14 — CRITICAL post-regen: J-07 Risk-Off gate (Actionable = 0)
**Type:** browser
**Preconditions:** DB regenerated; seeded Risk-Off run available.
**Steps:**
1. Open the seeded Risk-Off run on `/stocks` (or the scanner view).
2. Count stocks marked "Actionable".
**Expected outcome:** **Zero** stocks are "Actionable" (watchlist-only) under Risk-Off.
**Pass criteria:** Actionable count == 0 (unchanged after regen).

### TC-15 — CRITICAL post-regen: J-06 NVDA score consistency across views
**Type:** browser
**Preconditions:** DB regenerated.
**Steps:**
1. Read NVDA's Leadership / Entry Quality / Risk scores (number + A–E bucket) on the `/stocks` leaderboard.
2. Read the same on `/stocks/NVDA`.
**Expected outcome:** NVDA's three scores (number + bucket) are **byte-identical** across the two views.
**Pass criteria:** Leaderboard values == detail values for all three scores and buckets.

### TC-16 — Anti-goal source seam: read-only lab + no weight leak
**Type:** artifact (source inspection)
**Preconditions:** Diff available.
**Steps:**
1. Confirm `research.py` calls no `run_scan`/`score_stocks`/`forward_return`/`detect_*`/`score_regime`.
2. Confirm `hv`/`vcp_contraction`/`downside_vol` appear in no `config.scores.*.weights` and `_build_score` is unchanged.
3. Confirm the new values are computed in `scoring.py` from bars ≤ D (no lookahead) and read-only in the lab.
**Expected outcome:** Read-only seam intact; no weight leak; no lookahead.
**Pass criteria:** All three source conditions hold.

### TC-17 — Dev handoff artifact present
**Type:** artifact
**Preconditions:** Dev complete.
**Steps:**
1. Verify `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-13-dev.md` exists and documents the changes.
**Expected outcome:** Handoff present and substantive.
**Pass criteria:** File exists, describes indicator math, storage, config, regen, and tests.

## Summary

Total test cases: 17
- API tests (unit/integration/suite): 7 — TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07
- Browser tests: 7 — TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15
- Artifact checks: 3 — TC-08, TC-16, TC-17

**Critical gates:** TC-02 (score-invariance keystone), TC-14 (J-07 Risk-Off=0), TC-15 (J-06 NVDA consistency) — any failure here is a hard blocker. TC-11 acceptance is **descriptive** (an honest "contraction does not predict" finding still passes).
