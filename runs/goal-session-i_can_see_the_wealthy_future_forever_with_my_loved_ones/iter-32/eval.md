# Iteration 32 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-91 (downtrend-conditioned three-angle opportunity study on `/research`) and J-92 (optional, config-default-OFF FRED macro feed + `MacroSeries` standalone table + `^TNX`/`^DXY`/`^VXN` proxies) both land correct, additive, and coherent, with primary evaluator-viewed evidence and browser-QA 23/23 PASS. The standing GOAL_ACHIEVED gate (a GREEN full backend suite) is unmet by exactly ONE stale failure — `test_api_data.py::test_get_data_overview_shape`, an over-strict exact-set guard tripped by J-92's correct blueprint-registered additive `macro` key on `GET /api/data` (the verbatim iter-20/23 additive-trips-blanket-guard pattern, NOT a regression). NOT GOAL_ACHIEVED regardless: J-93/J-94/J-95/J-96 are unbuilt buildable Must-haves.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-91 | failing | passing | reports/qa/.../iter-32-evidence/UT-03-samples-downtrend.png, UT-07-sort-ascending-pass.png, UT-04-top-page.png |
| J-92 | failing | passing | reports/qa/.../iter-32-evidence/UT-12-macro-panel-full.png |
| J-87 | passing | passing (re-verified) | UT-18-dashboard.png |
| J-88 | passing | passing (re-verified) | UT-18-dashboard.png (Market Phase panel; UT-18 in results table) |
| J-89 | passing | passing (carried; iter-31 live) | reports/phase-...-iter-31-ui-test-results.md |
| J-90 | passing | passing (re-verified) | UT-17-recovery-turn-edge (results-table row; consumed by J-91 angle c) |
| J-06 | passing | passing (re-verified) | UT-18-dashboard.png |
| J-18 | passing | passing (CRITICAL, re-verified) | UT-19-date-controls.png (0 `<input type=date>` on /research) |
| J-07 | already_passing | already_passing (carried) | iter-31 evidence |
| J-29 | passing | passing (re-verified, byte-identical) | UT-16-event-study (results-table row) |
| J-32 | passing | passing (re-verified) | UT-06-asof-toggle (mode, not date) |
| J-63 | passing | passing (re-verified) | UT-05 Episodes/Pooled toggle |
| J-51 | passing | passing (re-verified) | UT-03-samples-downtrend.png (total==n) |
| J-65 | passing | passing (re-verified) | UT-03-samples-downtrend.png (N= chip new tab) |
| J-77 | passing | passing (byte-identical, asserted) | suite (test_research.py byte-identity) |
| J-82 | passing | passing (every displayable row 2xx) | suite + UT-03 |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead | OK | `_macro_value_asof` filters `MacroSeries.published_date <= d` by construction; J-91 conditioning tag reads causal phase/severity/filtered-P(bear) ≤ D (smoothed/true-bear stays fenced on J-89) |
| Single source of truth / No recompute in read path | OK | Coherence COHERENCE-PASS: single canonical `research:compute_downtrend_opportunity_study` + sole endpoint `GET /api/research/downtrend-opportunity`; angle (c) reuses `compute_recovery_turn_edge` verbatim; samples drill-down reads the same membership builder ("nothing is recomputed") |
| No magic numbers | OK | `test_no_magic_numbers` passed (in the 945); band catalog + every series id / publication-lag / enable flag live in config |
| No fabricated data | OK | Absent FRED key → `ProviderUnavailableError` (no silent fallback); missing observation excluded; walled series shown NA; low-sample cohorts NA + n |
| No order/execution path | OK | Fell-hardest angle labelled "RESEARCH EVIDENCE ONLY — Trendora places no orders and offers no short-deployment path"; grep found only sort/re-order + disclaimer matches |
| No secrets in source / keys env-only, never persisted | OK | FRED key read from env via `env_var` NAME only, held in memory for the request only, never persisted/logged/echoed; key travels in `params` not the URL (redacted-error path honors the httpx URL-leak lesson); no committed key literal |
| Risk-Off must gate Actionable | OK | Scanner/regime engine untouched (additive diff; no `score_regime`/scanner path modified) |
| Scores explainable | OK | Dashboard component breakdown intact (UT-18); J-91 columns carry the J-47 glossary |
| Honest limitations surfaced | OK | Survivorship-bias label + macro publication-lag limitation label both present (UT-03, UT-04, UT-11) |
| Exactly one date selector (CRITICAL) | OK | 0 `<input type=date>` on /research (UT-19); As-of/All-history + Episodes/Pooled + dimension are MODES; new panel holds no date `useState`, no window/document keydown listener (coherence + source) |

## Full Suite Status

`1 failed, 945 passed, 4 skipped in 5060.79s (EXIT=1)` (`/tmp/iter32-full-suite.log`).

The lone failure `tests/test_api_data.py::test_get_data_overview_shape` asserts `set(payload) == {coverage, runs, sources, resumable_imports, unfinished_imports, job_progress}` (strict exact-set). J-92 additively adds the blueprint-registered `"macro"` key to the `GET /api/data` overview (coherence Step 1 J-92 confirms it as an additive field on the existing endpoint). The over-strict guard was not updated for the additive key — the verbatim iter-20 → iter-21 / iter-23 → iter-24 pattern (a correct additive feature trips a pre-existing blanket guard; suite goes RED; held one consolidation iter). This is NOT a regression and NOT an anti-goal violation: COHERENCE-PASS, no prior-passing journey broke, the dev correctly added the separate `MACRO_TABLES` expected-tables guard, and the byte-identity-when-disabled tests pass.

## QA-vs-browser-QA reconciliation (timeout)

The QA stage recorded FAIL claiming `GET /api/research/downtrend-opportunity` "timed out (>30s)". The later, authoritative browser-QA stage recorded 23/23 PASS and reported the endpoint DID render — after ~5 min of COLD-CACHE compute on this 1369-run live host, then cached. The QA "timeout" was a too-tight 30s wait against a cold cache, not a hang (the endpoint is `downtrend_opportunity_cached`). Acceptable (cached) cost for this iteration; a perf/cache warm-up follow-up is advisable but non-blocking.

## Evidence-hygiene defect (recorded, non-verdict-changing)

The evidence dir again carries a large cluster of 2141-byte BLANK frames (md5 `030409108ded...`), and several are CITED as the primary frame for J-91/J-92 sub-legs (UT-01/08/09/10/11 → blank `UT-01-downtrend-loaded.png`; UT-12/13/14/22 → blank `UT-12-macro-feed-panel.png`; UT-16/17). The verdict does NOT rest on those blanks — every claim is grounded on the byte-distinct, large, evaluator-VIEWED frames: `UT-03-samples-downtrend.png` (count-coherence 3==N=3), `UT-07-sort-ascending-pass.png` (NA-last sort + downside risk-adjusted), `UT-04-top-page.png` (panel + single as-of), `UT-12-macro-panel-full.png` (1.2MB real /data macro panel), `UT-18-dashboard.png` (J-87/J-88/J-06 unchanged), `UT-19-date-controls.png` (J-18). Next QA must md5sum the dir FIRST and re-capture any blank cited frame full-viewport (recurring every iteration).

## Next-Step Recommendation

iter-33 begins with reconciling the single stale guard, then the J-93/J-94/J-96 dynamic point-in-time universe cluster + J-95's data-walled envelope (FULL depth — backend engine + endpoints + the full pytest gate):

1. **Consolidation (one-line):** update `apps/backend/tests/test_api_data.py::test_get_data_overview_shape` to accept the additive `macro` key — either compare as a superset (`{...} <= set(payload)`) or add `"macro"` to the expected set, mirroring the iter-21/iter-24 additive-key reconciliation. Re-run the FULL suite to EXIT=0 (pump nohup-async; gate on the FLUSHED `0 failed, EXIT 0` line — never block the evaluator on the in-flight suite, iter-11 lesson).
2. **J-93/J-94/J-96** (per-as-of-date resolver screening price+ADV+min-history; min-history sufficiency gate + honest warm-up; membership timeline + survivorship/coverage labels) + **J-95** (backward-history / point-in-time-membership data-dependent envelope, non-halting blocked-NA). Required-still-passing: J-87/J-88 (consumed layer byte-identity), J-89/J-90/J-91 (the layer this cluster reads), J-06/J-18 (CRITICAL), J-29/J-32/J-63/J-51/J-65/J-77/J-82 (research labs + samples count-coherence).
3. **Perf/cache (advisory, fold in if cheap):** warm `downtrend_opportunity_cached` during background warm-up so the first cold request on a many-run host does not take ~5 min.

After the cluster lands green with the full suite GREEN, zero regression, and COHERENCE-PASS, the next evaluation is a GOAL_ACHIEVED candidate. J-22/J-23/J-24 stay honestly blocked-NA (data-walled, non-vetoing per goal.md lines 105-108).
