**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-18 (J-26 composite combination-cohort re-scope)

- **Session:** i_can_see_the_wealthy_future_forever
- **Iteration:** 18 — *Factor Lab: composite percentile-rank combination cohort (replace strict-AND headline)*
- **Target journey:** J-26 (re-scope bar-raise, not a new value)
- **Snapshot audited:** `git diff e2da4d7c6755a00e610529465ff5fc7e56bd999c` + uncommitted working tree
- **Scope of diff:** `engine/research.py`, `api/research.py`, `config.py`, `config.yaml`, `frontend/app/research/page.tsx`, `frontend/lib/api.ts`, blueprint, tests. **No** `scoring.py`/`scanner.py`/`regime.py`/`patterns.py`/`buckets.py`/`forward_testing.py` change → scoring/snapshot path byte-identical (J-06/J-07 preserved, no DB regen).

## Result

No objective violations in Part A (Data Contract) or Part B (Information Architecture). No advisory notes worth carrying. This is a textbook **refinement of an existing Data-Contract value** — same module, same endpoint, same page, read-only.

---

## Part A — Data Contract (the "numbers don't match" gate) → PASS

Registered value under audit: **Factor-Lab multi-factor combination cohort (J-26)** — canonical module `app.engine.research:compute_factor_combination`, canonical endpoint `GET /api/research/factor-combination`.

1. **No duplicate computation.** The composite blend is computed *inside* the same `compute_factor_combination` (`engine/research.py`). The two new helpers `_percentile_rank_fractions` (`research.py:407`) and `_composite_scores` (`research.py:419`) are pure and called only from that function; they **reuse** the existing `_average_ranks` and `_quantile_cutoff` helpers rather than re-implementing ranking/cutoff. No second `compute_*`, service, or module computes this cohort. The API change (`api/research.py:7-8`) is **docstring-only** — signature unchanged.
2. **Canonical source preserved.** The frontend `CombinationTable` reads `data.composite` / `data.strict_overlap` from the same `combinationSource` (`GET /api/research/factor-combination`). No new fetch path; `lib/api.ts` comments assert "re-formats only and recomputes no return/factor/cohort." No client-side recomputation.
3. **Read-only confirmed.** `_composite_scores` blends `obs["values"][key]` (stored factor values, read verbatim) and returns are pulled from `pool[i]["return"]` (stored realized returns via the SELECT-only `_combination_observations`). No `run_scan`/`score_stocks`/`backfill*`/`forward_return`/`detect_*`/`score_regime` call is introduced. Percentile-ranking stored values is a deterministic grouping — the same read-only class as the J-25 decile sort (coherence invariant #9 upheld). Risk-adjusted stays the downside-only `_risk_adjusted` via the unchanged `_cohort_stats`.
4. **No new/duplicate value.** `composite` (headline) and `strict_overlap` (secondary) are two cohorts of the **same** registered combination value — `strict_overlap` is the demoted iter-12 AND-intersection; the old single `combined` key is cleanly removed across engine, `api.ts`, and `page.tsx` (no back-compat alias, no dead code). Neither duplicates the single-factor decile/IC value, which keeps its own home (`compute_factor_lab` / `GET /api/research/factor-lab`). The echoed `composite_quantile` / `weighting` are config metadata for honest labelling, not computed values.
5. **Registration consistent.** The blueprint Data-Contract J-26 row was edited additively to describe the composite blend + secondary strict-overlap, explicitly keeping "the SAME module + endpoint serve the refined value (no second computation, no second endpoint)." No unregistered value.
6. **No magic numbers / no parallel source.** Blend tunables are all config-sourced: `max_conditions: 11`, `composite.quantile: quintile`, `composite.weighting {scheme: equal, default_weight: 1.0}` (`config.yaml`), typed + boot-validated by `CompositeCfg`/`CompositeWeightingCfg`/`CombinationCfg` (`config.py` — `composite.quantile` must be a real quantiles key; `default_weight > 0`). Weights normalized in-engine from `default_weight` (no `1/k` literal). Only structural arithmetic (`1 − frac`, `rank / n`) appears in calc code.

## Part B — Information Architecture (the "where do I find it / why is it everywhere" gate) → PASS

1. **Navigation path exists.** The change edits the **existing** "Multi-factor combination cohort" section on the **existing** `/research` Factor Lab page (already a top-level sidebar entry). ui-surface-map confirms **0 new pages/routes, no nav changes**. Reachable in 1 click.
2. **Reachability ≤2 clicks.** `/research` is a top-level sidebar link; the Combination Lab is a section on that page. Within bounds.
3. **No duplicate home.** No second page/route for the combination cohort; the existing section is refined in place.
4. **No parallel shell.** Page stays in the established left-sidebar shell; no new layout/nav introduced.
5. **Re-approval correct.** No nav-skeleton change, so **no `blueprint.reapproval-requested` marker is written**. The iter-17 marker is consumed (file deleted in this diff) — operator approval of the System Health retirement, unrelated to this iter's surface. Blueprint "Nav-skeleton update (iter-18): NO skeleton change" matches the diff.
6. **J-18 (one date selector) upheld.** Endpoint signature unchanged — **no `as_of` param added**; frontend adds **no date/as-of state** (reuses the page's shared `horizon` selector only; `api.ts` comment: "there is NO as-of/date control (J-18)"). J-32 correctly deferred to iter-19.

## Part C — Advisory (WARN only) → none

- Labels are consistent backend↔frontend ("Combined (composite rank-blend)" / "Strict overlap (AND)", rendered verbatim; testids `combination-row-composite` / `combination-row-strict_overlap`). No label drift.
- All cohort rows share the same `_cohort_stats` → `CohortCell`/`SampleSize` rendering — formatting is uniform; low-sample/empty cells show NA + n (no fabricated 0). No formatting drift.
- Old `combined` key removed cleanly — no dead-code or stale-reference drift.

No advisory issues to record for next-iteration tidy-up.

---

**Bottom line:** iter-18 keeps the app coherent — one computing module and one serving endpoint for the (refined) combination-cohort value, no second home or parallel shell, no new date state, and the scoring/snapshot path untouched. **COHERENCE-PASS.**
