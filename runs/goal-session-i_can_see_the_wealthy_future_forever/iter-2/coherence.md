**Verdict:** COHERENCE-PASS

# Coherence Audit — goal-i_can_see_the_wealthy_future_forever-iter-2 (J-19 Return attribution)

- **Session:** i_can_see_the_wealthy_future_forever
- **Iteration:** 2
- **Audited against:** `runs/goal-session-i_can_see_the_wealthy_future_forever/state/blueprint.md`
- **Diff base:** `git diff 3b5340d7e629cc1ea656bb96876636b7e17d51cd` (+ uncommitted working tree)
- **UI surface map:** present and consistent with the diff

No objective Data-Contract or Information-Architecture violation. The iteration adds the J-19 return-attribution slices exactly as the blueprint's J-19 row and critical anti-goal *"Attribution is read-only"* require: a read-only derivation of the already-built per-observation `stock_obs`, attached to the two existing canonical payloads, surfaced through one shared component rendered inside two pages that already have a nav home.

---

## Step 1 — Data Contract check (the "numbers don't match" gate) → PASS

**No duplicate computation of any registered value.** The new `_attribution_slices(stock_obs, cfg)` (`apps/backend/app/engine/forward_testing.py:436`) takes the **already-built** per-observation list and `cfg` and **takes no `Session`** — so it structurally cannot issue a second `forward_returns` / price-bar query. Its three sub-helpers group existing stored returns rather than recomputing any:
- `_per_stock_attribution` (line 401) aggregates `obs["return"]` per ticker with `mean(rets)` — grouping, not recomputation.
- `_distribution` (line 421) takes statistics over `[obs["return"] for obs in stock_obs]`.
- `by_sector` / `by_rank_band` reuse the existing `_group_means` helper (lines 458–459).

**`distribution.mean_return` is the SAME value as the registered `overall.mean_return`, not a divergent copy.** `overall.mean_return = _mean_or_none([o["return"] for o in stock_obs])` (`forward_testing.py:508–509,553`); `distribution.mean_return = mean([obs["return"] for obs in stock_obs])` (line 460 → 428) — the same `mean()` over the same observation list, served from the same payload by the same canonical module. This is a deliberately convergent value (the blueprint registers it as a consistency invariant), and `test_attribution_consistency_with_aggregate` (`test_forward_testing.py`) asserts `distribution.mean_return == overall.mean_return`, `distribution.n == overall.n`, and that the by-sector / by-rank-band `n`s sum to `overall.n`. The read-only seam is further locked by `test_attribution_is_pure_over_passed_observations_no_new_query`, which asserts the signature is exactly `{stock_obs, cfg}` (no DB access).

**No non-canonical source / no new endpoint.** `attribution` rides the existing payloads: `compute_forward_aggregates` → `GET /api/system-health` (`forward_testing.py:560`) and each `by_horizon` entry of `compute_run_scorecard` → `GET /api/backtest` (line 663). `apps/frontend/lib/api.ts` adds the `attribution` field type-only to `SystemHealthResponse` and `BacktestScorecardHorizonRow` — no fetcher signature change, no new fetch path.

**Frontend re-formats only.** `components/return-attribution.tsx` renders server-derived values via the existing `Return` / `fmtPct` / `returnClass` / `SampleSize` primitives; the only client math is `fmtUnsignedPct` (×100 + `%` for display) — formatting, not return recomputation.

**No unregistered value.** The J-19 row already existed in the Data Contract (status `⛔ NOT BUILT — target`) and was **refined in place, additively** — naming the shared helper, the consistency invariants, and the new `walk_forward.attribution` config keys (blueprint.md lines 92, 124). New config keys are registered and config-driven (`config.py:AttributionCfg`/`RankBand`; `config.yaml:497`) — no magic numbers in calc code.

## Step 2 — Information Architecture check → PASS

**No new page/route, no nav change.** The only new frontend file is the shared `apps/frontend/components/return-attribution.tsx` component (no new `app/**/page.tsx`). It is rendered inside two routes already in the blueprint's nav skeleton — `/system-health` (`page.tsx:207`) and `/backtest` (`page.tsx:141`) — both top-level persistent-sidebar entries (1 click). No `Sidebar`/router edit was needed or made.

**No duplicate home / no parallel shell.** The attribution panels are a `<section>` appended within each page's existing layout, under the canonical homes the blueprint assigns to J-19 (System Health aggregate + Backtest per-date). It is not a second results page for an existing entity, and it introduces no parallel nav/shell.

**Critical invariant #5 (exactly one date selector) preserved.** The new `HorizonViewSelector` on `/backtest` (`page.tsx:411`) is a **view preference over data already in the payload** — `onChange={setViewHorizon}` only picks which `by_horizon[*].attribution` to display; there is no `useEffect` keyed on it, no refetch, no fetch param. The page still reads the date solely from the global `useAsOf()` switcher (no second date state). A horizon (forward-window length) is not a date control — System Health already has the legitimate equivalent. J-18 consolidation intact.

## Step 3 — Subjective observations (advisory) → none blocking

- `fmtUnsignedPct` is a new local formatter for the non-directional hit-rate / dispersion figures. It matches `fmtPct`'s 2-decimal precision, and the neutral (no green/red, no sign) treatment for non-directional stats is a deliberate, defensible choice. No formatting drift worth a WARN.
- Test-fixture touches in `test_config.py`, `test_sectors.py`, `test_themes.py` (8–9 lines each) only add the now-required `walk_forward.attribution` block to synthetic config dicts — benign fixture maintenance, no value-serving code.

---

## Summary

| Gate | Result | Evidence |
|---|---|---|
| Data Contract — duplicate computation | PASS | `_attribution_slices(stock_obs, cfg)` takes no Session; groups stored `obs["return"]`; consistency unit-asserted |
| Data Contract — non-canonical source | PASS | rides existing `GET /api/system-health` + `GET /api/backtest`; api.ts type-only; FE re-formats |
| Data Contract — unregistered value | PASS | J-19 row refined in place additively; config keys registered |
| IA — navigation path / reachability | PASS | no new route; renders in `/system-health` + `/backtest` (1-click sidebar homes) |
| IA — duplicate home / parallel shell | PASS | section appended within existing canonical homes/layout |
| IA — one date selector (inv. #5) | PASS | horizon-view selector is a no-refetch view preference; date still from `useAsOf()` only |

**No FAIL. No advisory issue requiring next-iteration consolidation.**
