**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-11 (J-27: Factor Lab regime-conditioned effectiveness)

- **Session:** i_can_see_the_wealthy_future_forever
- **Iteration:** 11
- **Snapshot SHA audited:** `5871e997f9df827bb1b729cedf490eff61fa43ad` (+ uncommitted working tree)
- **Auditor:** coherence-auditor
- **Result:** no objective Data-Contract or Information-Architecture violations. One non-blocking, non-coherence code nit noted for the reviewer.

## Scope of changes audited

`git diff` against the snapshot touched only the files the spec promised:

| File | Nature |
|---|---|
| `apps/backend/app/engine/research.py` (+72) | `_factor_observations` attaches stored regime; new `_regime_effectiveness` helper; `by_regime` added to `compute_factor_lab` return |
| `apps/backend/tests/test_research.py` (+150) | extended read-only keystone + J-27 scenarios (tests, no surface) |
| `apps/frontend/app/research/page.tsx` (+103) | additive `RegimeEffectivenessTable` + `RegimeCell` on the existing Factor Lab page |
| `apps/frontend/lib/api.ts` (+17) | `RegimeEffectivenessRow` type + `by_regime` field on `FactorLabResponse` |
| `runs/goal-session-.../state/blueprint.md` (+7) | additive registration of the `by_regime` slice + iter-11 nav note |
| telemetry/trace | automation artifacts (non-source) |

No change to `forward_testing.py`, `scoring.py`, `scanner.py`, `patterns.py`, `regime.py`, `config.yaml`, the snapshot/as-of read path, the watchlist, or any API view — matching the spec's OUT OF SCOPE list and confirming this is a pure additive slice.

## Part A — Data Contract check (the "numbers don't match" gate) → PASS

The blueprint's **Factor-Lab analytics** row (canonical module `app.engine.research:compute_factor_lab`, canonical endpoint `GET /api/research/factor-lab`) was extended this iteration to register the new `by_regime` slice as part of the **same value** (read-only extension, analogous to the J-19 attribution slices). Checked against the objective FAIL rules:

1. **No duplicate computation.** `_regime_effectiveness` (`research.py:216`) reuses the existing `_deciles` and `_rank_ic` helpers over the **same `observations` pool** `compute_factor_lab` already built. It computes no factor, no return, no regime. The decile count comes from `config.research.factor_lab.deciles`, the low-sample threshold from `config.walk_forward.min_sample`, and the regime list from `config.regime.labels` — all config refs, **no new numeric literal**.
   - The only other `by_regime` in the tree is `forward_testing.py:622` (mean forward return by regime, for System Health). That is a **distinct registered value** (mean return), not the same as the research lab's factor-effectiveness rank-IC/spread by regime — different question, different population semantics. Not a duplicate. (Verified via `grep -rn "by_regime"`.)

2. **Regime read VERBATIM (single source of truth — the keystone for this iteration).** `regime_by_run = {run.id: run.regime_label for run in run_rows}` (`research.py:175`) reads the stored `scanner_runs.regime_label` with a SELECT-only query, mirroring `forward_testing.py:538`. `research.py` **does not import the regime engine** and never calls `score_regime` (verified: `grep "score_regime|from app.engine.regime"` → none). The regime is the canonical value computed once by `regime:score_regime`; the lab consumes it, never recomputes it. Satisfies invariants #1, #2, #9.

3. **No non-canonical source.** The frontend reads `data.by_regime` from the **same** `FactorLabResponse` returned by the single `fetchFactorLab` → `GET /api/research/factor-lab` call (`page.tsx:41`). No new endpoint, no new query param, no client-side recomputation — the table re-formats payload values via the existing `fmtPct`/`fmtRatio`/`returnClass`/`SampleSize` helpers (allowed re-format).

4. **No unregistered value.** The `by_regime` slice is registered in the blueprint Data Contract this iteration (additive edit to the Factor-Lab row) — so no A5 "unregistered value" WARN applies.

5. **Read-only / downside-only honesty preserved (invariant #9).** Spreads are simple subtractions of already-computed decile fields (`top_mean - bottom_mean`; `top_ra - bottom_ra`); `risk_adjusted_spread` reuses the iter-10 downside-only `risk_adjusted` field (`_deciles`/`_risk_adjusted` unchanged in this diff) and returns `None` (NA) when low-sample or either leg is None — never a total-volatility fallback. Frontend `RegimeCell` renders muted "NA" on `low_sample || value === null`, never a fabricated number.

## Part B — Information Architecture check → PASS

1. **No new route / page / nav entry.** The change is a single additive panel rendered inside the existing `FactorLab` component on the already-approved `/research` page (`page.tsx:232`). The blueprint nav skeleton notes "**NO skeleton change**" for iter-11 and writes no `blueprint.reapproval-requested` marker — consistent with the diff.
2. **Reachability.** `/research` is an existing top-level sidebar entry (≤2 clicks, approved iter-10); the panel is reached by scrolling that page. No discoverability regression.
3. **No duplicate home.** No second page for any entity — the panel extends the canonical Factor Lab home.
4. **No parallel shell.** Uses the established page shell (`Card`, `PanelTitle`, existing table/cell styling). No new layout/nav.

## Part C — Advisory (non-blocking)

- **Label & format consistency: good.** Regime rows are server-driven from `config.regime.labels` (no hard-coded frontend regime array — the iter-9 config-driven-vocabulary lesson is honored), so the regime vocabulary stays identical to System Health's by-regime breakdown. Raw means/spread use `fmtPct`, rank-IC and risk-adjusted spread use `fmtRatio`, matching the existing decile table and rank-IC card.
- **Minor code nit (NOT a coherence issue, for the reviewer):** `_regime_effectiveness(observations, cfg, horizon)` accepts a `horizon` parameter that is unused in the body (the `observations` are already horizon-scoped upstream). Harmless dead parameter — no effect on coherence, single-source, navigation, or data flow. Flagging only so the reviewer can drop it if desired.

## Conclusion

This is a textbook-clean additive iteration: the new `by_regime` slice is derived once by the canonical `compute_factor_lab` over the same observation pool, the regime is read verbatim from its single source, no endpoint/route/nav/date-state is introduced (J-18 holds — `/research` has no date control), and the blueprint Data Contract was proactively extended to register the slice. No objective violation under Step 1 or Step 2.

**Verdict: COHERENCE-PASS**
