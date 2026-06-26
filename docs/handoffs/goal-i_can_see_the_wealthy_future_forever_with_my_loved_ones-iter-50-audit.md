# Goal Iteration 50 (J-107 — Factor Lab all-factors table) Audit Report

**Date:** 2026-06-26
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

J-107 is genuinely and correctly built. The Factor Lab `/research/factor-lab` is restructured from a single-factor dropdown into an all-factors sortable + expandable table served by an additive `all=true` flag on the existing endpoint (no new endpoint, no new table), every figure byte-identical to the canonical single-factor `compute_factor_lab` output, over a single bounded `yield_per`-streamed `(run_id, id)`-ordered observation pool served from a derived-once `EventStudyCache` sentinel namespace. I re-ran the load-bearing tests myself: 12/12 unit tests (byte-identity, cache HIT==MISS==fresh + stale-prune + refresh, bounded read, NA honesty) and 6/6 all-factors API tests (incl. API-level byte-identity vs the single-factor view, as-of scoping, 422) pass. No critical or important gaps remain; the only findings are documented OBSERVATIONs.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (verified): byte-identity holds by construction, not just by assertion.**
`_all_factor_observations` (`apps/backend/app/engine/research.py:400-456`) iterates the SAME `forward_returns`-joined-`scanner_results` pool in the SAME `(run_id, id)` ScannerResult order as the single-factor `_factor_observations` (lines 231-250), keeps NULL factor values rather than dropping the whole observation (the explicit contrast with `_combination_observations` at line 591), then `compute_factor_lab_all` (lines 459-528) filters each factor to its own non-null subset preserving that order and sorts with the identical `(factor, ticker, run_id)` key (line 503), feeding the SAME `_deciles` / `_rank_ic` builders. The `float()` coercion (line 497) and `realized` return value are applied identically on both paths, so per-factor deciles / rank-IC / n_total are byte-identical. Confirmed by `test_all_factors_per_factor_is_byte_identical_to_compute_factor_lab` (exact dict equality across all-history + as-of + populated/component/zero-N) and at the API level by `test_factor_lab_all_is_byte_identical_to_single_factor_view`. Both pass.

**B2 — OBSERVATION (verified): cache reuses `EventStudyCache`, no new table.**
`factor_lab_all_cached` (`research.py:2838-2887`) is a faithful clone of `event_study_cached` / `factor_combination_cached`, keyed on a fixed sentinel `subject="__all_factors__"` / `view="factors_table"` + `_dataset_version` + `asof_key` + `horizon`. `apps/backend/app/models.py:385` confirms `EventStudyCache` is the only cache table and no new `table=True` model was added. The stale-version row is pruned on write, and the dataset-version stamp folds in `max(scanner_runs.id)` + `count(forward_returns)` so the cache refreshes on any dataset change. Proven by `test_stale_dataset_version_row_is_a_miss_and_is_pruned` (seeds a real populated stale row with a sentinel payload and asserts it is never served and is pruned) and `test_cache_refreshes_after_dataset_change`.

**B3 — OBSERVATION (verified): bounded read, no unbounded `.all()` over the heavy tables.**
The FR scan is column-projected + `yield_per`-streamed (`research.py:427-438`); the ScannerResult side is `yield_per`-streamed in `(run_id, id)` order (lines 440-445), riding `ix_scanner_results_run_id` so no temp-B-tree sort spills on the ~93%-full host. There is exactly ONE heavy read for all N factors (the pool is built once at line 488). The only `.all()` in the builder neighbourhood is over `runs_with_fr` ids (a small set), not the row tables. Proven by the source-guard `test_shared_pool_read_is_bounded_and_run_id_id_ordered`, the runtime `test_all_factors_chunk_independent` (batch=1 vs 1,000,000 byte-identical), and `test_all_factors_fires_one_shared_pool_read_not_n`.

**B4 — OBSERVATION (verified): error handling is explicit and config-sourced.**
`apps/backend/app/api/research.py:97-117` returns 503 when no price data exists, 422 for an unknown horizon (verified by `test_factor_lab_all_invalid_horizon_422`), and routes `as_of` through the shared `resolved_date` resolver (422 unparseable / 400 future-or-before-history). All catalog / horizon / decile-count / min_sample / batch values are config-sourced (no inline literals in the all-factors builder), so `test_no_magic_numbers` stays green.

### Frontend Findings

**F1 — OBSERVATION: `fetchFactorLab` / `FactorLabResponse` remain as unused exports.**
`apps/frontend/lib/api.ts:1092-1126` still exports the single-factor `FactorLabResponse` interface and `fetchFactorLab` function, but a repo-wide grep confirms neither is imported anywhere outside `api.ts` (only `fetchFactorLabAll` is used, in `_labs.tsx:34,177`). The spec explicitly permitted "clean up OR annotate as intentionally retained," and the dev handoff documents the intentional retention. The handoff's stated rationale ("the single-factor endpoint is still the canonical source the Research Samples drill-downs read from") is slightly imprecise — drill-downs go through `/api/research/samples`, not `fetchFactorLab` — but the retention is harmless and the single-factor backend endpoint is still live and tested. Reviewer flagged the same as a NOTE. No action required.

**F2 — OBSERVATION (verified): the new table meets the spec UI contract.**
`FactorsTable` / `FactorRows` / `FactorSortHeader` (`_labs.tsx:462-657`) render one row per catalog factor with Factor / Family / Rank-IC / N / Risk-adjusted (downside) columns + an expand chevron. Sort is a pure view transform (`useMemo` over served rows, line 476-495) with correct NA-last behaviour in BOTH directions (`else if (ana) return 1; else if (bna) return -1;`, lines 488-489) and a stable catalog-order tie-break; default is rank-IC descending. Rows are the keyboard-accessible `role="button"` + `aria-expanded` expandable control with no nested interactive element in the summary row; the decile `N=` `SampleLink` drill-downs (`cohort={{kind:"factor", factor, horizon, slice:"decile", decile}}`, line 704-710) live in the separate expanded panel. `FactorSelector` and `RegimeEffectivenessTable` are removed from this view; `HorizonSelector` and the `AnalysisModeToggle` (single global as-of via `useResearchControls`, no second date state) remain. Honest WarmingState / ResearchError / LabSkeleton / EmptyState are preserved.

**F3 — OBSERVATION: the summary-row Risk-adjusted column is always the top (D10) decile.**
For a `lower_better` factor the strongest cohort is the bottom decile, but the column consistently shows the top (highest-factor-value) decile's downside risk-adjusted figure (re-presented from `deciles[-1]`, not recomputed). Direction is conveyed by the rank-IC sign and the per-row `(direction)` hint, and the full raw-vs-risk-adjusted comparison is available side-by-side in the expanded decile table (`mean_return` + `risk_adjusted`). Documented in both handoffs and in code; a presentation choice, not an anti-goal violation (the figure is downside-only via `_risk_adjusted`, never total volatility).

### Test Findings

**T1 — OBSERVATION (verified by re-run): the targeted suites are tight and green.**
`tests/test_factor_lab_all.py` → 12 passed (1.10s, re-run by auditor). `tests/test_api_research.py -k all` → 6 passed (re-run by auditor). Assertions are exact (deep dict equality via `json.dumps(sort_keys=True)`, exact `n_total`, exact `risk_adjusted == deciles[-1].risk_adjusted`), and cover all-history + as-of + zero-N/low-sample edge cases — not loose "something returned" checks.

**T2 — GAP: QA browser coverage was thin and the full-suite green-flush is unverified at audit time.**
The QA report records 6/20 functional cases explicitly PASS, 4 PARTIAL, 9 NOT_TESTED (host resource constraints), 0 FAILED. The architecturally load-bearing cases (byte-identity, cache, bounded read, NA honesty, one-row-per-factor, 422) are all unit/API-proven and I independently re-ran them green. The DoD "full pytest suite flushes `0 failed, EXIT 0`" is the GOAL_ACHIEVED-candidacy gate run nohup-async via the pump (the dev handoff is honest that the developer did not run it end-to-end); verifying that flushed line is the goal-evaluator's responsibility, not a phase-correctness defect. No regression evidence was found in any suite I ran.

---

## 3. Domain Assessment

The core domain logic is correct and faithful to the project's research-lab disciplines:

- **Single source of truth / no recompute in the read path.** The all-factors view re-presents existing `compute_factor_lab` outputs through one shared computation path; there is no second rank-IC / decile / risk-adjusted derivation and no new served value. Byte-identity is proven, not asserted, and the same symbol's figures cannot differ between the single-factor and all-factors views.
- **Risk is downside-only.** The `risk_adjusted` figure flows entirely through `_risk_adjusted` (mean / downside-deviation about MAR=0), never total volatility; NA when n<2 or no downside.
- **Honest, descriptive, non-predictive.** Survivorship + descriptive caveats are carried verbatim; zero-N / low-sample factors and deciles render NA + n, never a fabricated number; the empty observation set renders an honest empty state.
- **No lookahead / as-of is a pure filter.** `as_of` scopes the shared pool to `ScannerRun.asof_date <= D` and is folded into the cache key; it recomputes nothing.
- **Exactly one date selector.** The page reads the single global as-of through `useResearchControls`; the All-history/As-of control is a mode, not a second date state.
- **No magic numbers / no new table / bounded read.** All thresholds are config-sourced; `EventStudyCache` is reused under a sentinel namespace; the heavy read is streamed and `(run_id, id)`-ordered (the iter-47/48 OOM / disk-full lesson is respected on the cold-miss path).

The architecture remains local-first and minimal: an additive query flag, a reused cache table, and a re-presentation of already-stored evidence. No scope drift beyond the spec (the per-regime table is retired from this view only; the backend computation is untouched; the combination lab is untouched).

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issues were found. All findings are OBSERVATION-level (or a non-blocking GAP that is the goal-evaluator's gate, not a phase defect), so per the auditor rules nothing was changed.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

Proceed. J-107 — the last unbuilt buildable Must-have — is correctly implemented, byte-identity-proven, bounded, cached, and honestly NA-handling, with the UI evolved to a sortable/expandable all-factors table and no anti-goal violation. The remaining items are documented OBSERVATIONs. The one outstanding pre-condition for the GOAL_ACHIEVED candidacy is the async full-suite `0 failed, EXIT 0` flush via the pump (T2) — that is the goal-evaluator's gate to confirm; the load-bearing subset is independently re-verified green and no regression was observed. Optionally, a trivial future cleanup could remove or JSDoc-annotate the unused `fetchFactorLab` / `FactorLabResponse` exports (F1).
