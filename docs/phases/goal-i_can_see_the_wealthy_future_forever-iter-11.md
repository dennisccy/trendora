# Goal Iteration 11 — Factor Lab: regime-conditioned factor effectiveness (J-27)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 11
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-27
- **Required-still-passing journeys:** J-25, J-18, J-09, J-19, J-15 (all other journeys J-01–J-24, J-26, J-28–J-31 carry green via the additive `/research` diff — see NOTES)
- **Anti-goal reminders** (verbatim from `docs/goal.md`; this iteration must respect each):
  - **Research lab is read-only, honest & not predictive.** Every Factor-Lab and event-study figure (decile means, rank-IC, combination cohorts, regime slices, distribution, hit-rate, expectancy, MAE/MFE, exit-horizon, risk-adjusted ratios) MUST be derived once from the stored per-observation forward returns + stored factor values + post-snapshot price path; the API and frontend MUST NOT recompute returns or factors to build them; low-sample cells show NA + n; results carry the survivorship-bias label. The lab is **descriptive evidence, not a fitted/ML predictive model**. *(extends No recompute in the read path + No machine-learning price prediction)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **Risk-adjusted reporting is honest & must not conflate up/down volatility.** Every risk-adjusted figure (return/vol, return/MAE, Sharpe-like, expectancy) MUST be derived once from the stored per-observation forward returns + post-snapshot price path; "risk" MUST use downside volatility / MAE / drawdown — never total volatility, which would penalise healthy upside moves; raw and risk-adjusted MUST be shown side by side; low-sample cells show NA + n.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Single source of truth.** Each canonical value MUST be computed exactly once and read identically by every page; the API and frontend MUST NOT recompute them. *(critical)*
  - **Honest limitations surfaced.** Breadth/new-high-low metrics MUST be labelled "universe-relative"; walk-forward evidence MUST be labelled as carrying survivorship bias (current-membership universe).
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page reads the single global as-of control. *(extends Single source of truth)*

## GOAL

On the Factor Lab (`/research`), the user can see a chosen factor's effectiveness **split by market regime** — per regime, the rank-IC, the top-minus-bottom-decile raw spread, the downside-risk-adjusted spread, and the per-regime sample size `n` — so they can tell whether a factor that "works" overall actually works in Risk-on vs Choppy vs Risk-off, with honest NA for regimes that lack enough samples.

## BACKGROUND

J-25 (iter-10) established the `/research` Factor Lab and the read-only lab-analytics seam: `app.engine.research:compute_factor_lab` reads stored `forward_returns.realized_return` joined to the stored factor value on `scanner_results` (SELECT-only), groups them into a decile table (raw mean + downside risk-adjusted + `n`) and a Spearman rank-IC, all config-driven. The goal-evaluator's iter-10 recommendation names **J-27 as the primary next target — "the smallest direct extension of J-25: add a `regime` field to each observation from the stored `scanner_runs.regime_label`, then split the existing decile/IC + the top-minus-bottom-decile spread by regime, with honest per-regime n/NA."**

This is genuinely small and additive (one engine function extended, one read-only helper added, one UI panel, no new endpoint, no nav change), but it is dispatched at **full** depth per the evaluator's explicit recommendation and because it adds backend aggregation logic that needs real unit tests (regime grouping, spread math, the Σ-per-regime-n == n_total invariant, and the read-only keystone must continue to hold) plus a coherence + ux-regression + closure pass on a critical-anti-goal surface (the read-only research lab).

The regime-per-observation read is **already proven** in `forward_testing.compute_forward_aggregates` (line 538: `regime_by_run = {run.id: run.regime_label for run in run_rows}`; line 622: `by_regime` grouped against `cfg.regime.labels`). J-27 reuses the SAME stored regime label (single source of truth) — the lab reads it verbatim and recomputes no regime.

## IN SCOPE

### Backend

- [ ] **Extend `_factor_observations`** (`apps/backend/app/engine/research.py`) to attach the stored regime label to each observation: read the runs that have forward returns at the horizon (`select(ScannerRun)` for `run_id in runs_with_fr`), build `regime_by_run = {run.id: run.regime_label}` (mirroring `forward_testing.py:538`), and add `"regime": regime_by_run.get(res.run_id)` to each observation dict. Stay SELECT-only — read the stored regime label **verbatim**, recompute no regime/score/return.
- [ ] **Add a read-only `_regime_effectiveness(observations, cfg, horizon)` helper** in `research.py`: for each regime label `L` in `config.regime.labels` (in config order — no hard-coded regime list), filter observations to that regime and emit a row:
  - `regime`: the label
  - `n`: number of observations in that regime
  - `low_sample`: `n < config.walk_forward.min_sample`
  - `rank_ic`: `_rank_ic(...)` over the regime's `(factor, return)` pairs (reuse the existing helper; `value` is None on n<2 / zero variance)
  - `top_decile_mean`, `bottom_decile_mean`: the raw `mean_return` of the highest and lowest decile from a per-regime decile split (reuse `_deciles(...)` with `config.research.factor_lab.deciles` + `min_sample`); `deciles[-1].mean_return` and `deciles[0].mean_return`
  - `spread`: `top_decile_mean − bottom_decile_mean` (the long-short decile spread, raw); **None when `low_sample` or either leg is None**
  - `risk_adjusted_spread`: `deciles[-1].risk_adjusted − deciles[0].risk_adjusted` (downside-only, reusing the existing `_risk_adjusted`); **None when `low_sample` or either leg is None** (an all-non-negative decile has no downside risk → honest NA, never a total-vol number)
- [ ] **Add `"by_regime": _regime_effectiveness(observations, cfg, horizon)`** to the `compute_factor_lab(...)` return dict — same function, same observation pool, no second computation. (Existing keys unchanged.)
- [ ] **Config: read-only — NO new literal.** Regime labels come from `config.regime.labels`; the low-sample threshold is reused from `config.walk_forward.min_sample`; the decile count from `config.research.factor_lab.deciles`. Add no new config key and no numeric literal in `research.py`.
- [ ] **API: no change to `apps/backend/app/api/research.py`.** The new `by_regime` slice rides the SAME `GET /api/research/factor-lab` payload, served verbatim — no new endpoint, no new query param.

### Frontend

- [ ] **Types (`apps/frontend/lib/api.ts`):** add a `RegimeEffectivenessRow` interface (`regime: string; n: number; low_sample: boolean; rank_ic: RankIC; top_decile_mean: number | null; bottom_decile_mean: number | null; spread: number | null; risk_adjusted_spread: number | null`) and add `by_regime: RegimeEffectivenessRow[]` to `FactorLabResponse`.
- [ ] **Panel (`apps/frontend/app/research/page.tsx`):** add a `RegimeEffectivenessTable` panel below the existing decile table + rank-IC card. Columns: **Regime · n · Rank-IC · Top-decile mean · Bottom-decile mean · Spread (top−bottom) · Risk-adjusted spread**. Render one row per `data.by_regime` entry (server-driven — the regime list comes from the payload/`config.regime.labels`, **never a hard-coded frontend regime list**, per the iter-9 config-driven-vocabulary lesson). Use the existing NA treatment (`DecileValue`-style: low-sample or null → "NA" + the `SampleSize` chip), `fmtPct` for the raw mean/spread columns, `fmtRatio` for the risk-adjusted spread and rank-IC, `returnClass` for colour grading. The panel re-points on factor/horizon change (it reads the same `data` the `useEffect` already refetches — no new selector).
- [ ] **No date control added.** The page's only state stays `{factor, horizon, state}` — no `useAsOf`, no `asof`, no date picker (J-18). The new panel introduces no second date state.

### New user-facing capability

A user picks a factor + horizon on the Factor Lab and reads, per market regime, whether the factor's ranking actually sorts forward returns in that regime — the rank-IC and the long-short (top-minus-bottom-decile) spread both raw and downside-risk-adjusted — so a factor that looks good on the pooled table can be seen to be regime-dependent (e.g. strong in Risk-on, NA/weak in Risk-off).

### New information displayed

A "Factor effectiveness by market regime" table on `/research`: one row per configured regime label, each with per-regime `n`, rank-IC, top-decile mean, bottom-decile mean, raw top−bottom spread, and downside-risk-adjusted spread; low-sample / insufficient regimes render NA + n.

### New user actions

None beyond the existing factor + horizon selectors (the new panel re-points with them). No new control, no date control.

### UI surface changes

One additive panel on the existing `/research` page (below the decile table and rank-IC card). No new page, no new route, no nav change.

### Product surface delta

The Factor Lab graduates from "does this factor sort returns overall?" to "…and does it still sort returns *in this regime*?" — the central question of regime-conditioned factor research, answered read-only from already-stored evidence.

### Blueprint conformance

Lives under the existing **Research** (`/research`) home (blueprint IA, approved iter-10). No nav-skeleton change → **no `blueprint.reapproval-requested` marker written.** The blueprint Data-Contract row for **Factor-Lab analytics** is extended (additively) to register the `by_regime` slice as part of the SAME value (same module `app.engine.research:compute_factor_lab`, same endpoint `GET /api/research/factor-lab`).

### Data-contract additions

No NEW canonical value and no new endpoint. The `by_regime` slice is a **read-only extension of the already-registered Factor-Lab analytics value** (exactly as the J-19 attribution slices are read-only slices of the same stored returns): it is derived once by `compute_factor_lab` from the SAME observation pool, reading each observation's regime **verbatim from the canonical `scanner_runs.regime_label`** (computed once by `regime:score_regime`; never recomputed here). The blueprint's Factor-Lab row is updated to note this. **Do not** introduce a second endpoint, a second factor/return computation, or a second regime computation.

## OUT OF SCOPE

- A full per-regime 10-row decile **table** (six copies of the decile table). The acceptance is satisfied by the per-regime summary row (n + rank-IC + top/bottom decile means + raw spread + risk-adjusted spread); the spread IS the decile signal. Full per-regime decile tables are visual clutter and not required — exclude.
- J-26 (multi-factor combination cohorts), J-29 (event study / MAE-MFE), J-30 (full volatility family), J-31 (synthesis) — later `/research` iterations.
- J-22 / J-23 / J-24 — externally Yahoo-429 data-walled; **do NOT autonomously retry.**
- Any change to `forward_testing.py`, `scoring.py`, `scanner.py`, `patterns.py`, `regime.py`, the snapshot/as-of read path, the watchlist, or any existing endpoint.
- Adding/altering the global as-of switcher or introducing any date state on `/research`.
- New config keys or any numeric literal in `research.py`.

## DEFINITION OF DONE

- [ ] **J-27 passes via browser-qa-agent:** the "Factor effectiveness by market regime" table renders on `/research` with one row per configured regime label; each row shows per-regime `n`, rank-IC, and the raw + downside-risk-adjusted top-minus-bottom-decile spreads; low-sample/insufficient regimes show NA + n (no fabricated number); changing factor and horizon re-points the regime table.
- [ ] **Required-still-passing journeys remain green:** J-25 (existing decile table + rank-IC still render and re-point), J-18 (no second date state — `/research` still ignores the global as-of), J-09 (System Health by-regime + the shared forward-return pool unchanged), J-19 (attribution read-only seam unchanged), J-15 (no new per-request recompute — endpoint stays SELECT-only).
- [ ] **No anti-goal violation introduced:** read-only (the read path computes no return/factor/regime — keystone test holds with regime math also patched to raise); risk-adjusted spread is downside-only (NA when no downside, never total volatility); regime labels + thresholds from config (no magic numbers); low-sample → NA + n (no fabrication); single source of truth (regime read verbatim from `scanner_runs`); survivorship/descriptive labels still shown.
- [ ] **Consistency invariant holds:** Σ over regimes of per-regime `n` == `n_total` (every observation carries exactly one of the configured regime labels) — unit-asserted.
- [ ] **Unit tests pass; no regressions.** Backend suite green (extend `tests/test_research.py`); frontend typechecks/builds.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-11-dev.md`.

## TESTING REQUIREMENTS

### Browser (J-27 — verify on a healthy, serialized Chrome layer)

- Visit `/research`. Confirm the regime-effectiveness table renders with one row per configured regime label (the six: Strong risk-on, Risk-on, Narrow leadership, Choppy, Defensive, Risk-off), each with its `n` chip.
- Use a **short horizon (e.g. 5d or 1d)** to maximize per-regime sample so at least one regime clears `min_sample` and shows a numeric rank-IC + spread; capture that row. Then a **longer horizon (e.g. 60d)** and/or a sparse regime to capture an **NA + n** cell — proving honest low-sample treatment, not a fabricated 0.
- Change the **factor** and confirm the regime table values re-point (assert via DOM text + the observed `GET .../factor-lab?factor=…&horizon=…` network call; capture **distinct sha256** before/after screenshots — do not rely on a single pair).
- **J-18 regression:** change the global top-bar as-of switcher and confirm the Factor Lab (decile table, rank-IC, AND the new regime table) is byte-identical with **zero** `as_of`-param requests — `/research` is a cross-date aggregate with no date control.
- **J-25 regression:** confirm the existing decile table + rank-IC card still render and re-point on factor/horizon change.
- Capture an explicit backend-down / error state proof is NOT required (existing error card unchanged), but confirm the regime table is absent (not fabricated) when `n_total == 0` (empty-state path).

### Unit / integration (extend `apps/backend/tests/test_research.py`)

- `by_regime` splits observations by stored regime and **Σ per-regime n == n_total** (a ≥2-regime hand fixture; proves every observation carries one configured regime label, read verbatim).
- Exact regime spread + rank-IC on a hand fixture: a monotone factor within one regime → known `spread` (top-decile mean − bottom-decile mean) and `rank_ic.value ≈ 1.0`; an inverse regime → negative.
- **Read-only keystone extended:** in the existing patch-to-raise test, also `monkeypatch` `app.engine.regime.score_regime` (and keep `run_scan`/`score_stocks`/`forward_return`/`detect_*`) to raise, and assert `compute_factor_lab(...)["by_regime"]` is still fully populated — proving the regime is read from stored `scanner_runs`, never recomputed.
- **Downside-only spread:** a regime whose top decile is all-non-negative → `risk_adjusted_spread` is None (NA), while `spread` (raw) is numeric — downside-only honesty preserved.
- **Config-driven regimes:** the `by_regime` rows are exactly `config.regime.labels` in order (no hard-coded regime list); a regime with no observations is an honest `n=0` row, not omitted or fabricated.
- **Low-sample NA:** a regime with `n < walk_forward.min_sample` carries `low_sample=True` with its honest `n`, and `spread`/`risk_adjusted_spread` are None (UI renders NA).
- Existing tests stay green (decile math, rank-IC, the pooled-mean == `compute_forward_aggregates.overall.mean_return` consistency invariant, NA honesty, config/boot validation).

### Error cases

- Unknown `factor` → 422 (existing behavior, unchanged). Unknown `horizon` → 422 (unchanged). `n_total == 0` for a (factor, horizon) → empty-state, no regime table fabricated. A regime with n<2 / zero rank variance → `rank_ic.value` None (NA), never a fabricated 0.

## NOTES

- **Evaluator recommendation (iter-10):** "full depth; target J-27 — add a `regime` field per observation from the stored `scanner_runs.regime_label`, split the existing decile/IC + the top-minus-bottom-decile spread by regime, honest per-regime n/NA; reuses `compute_factor_lab`'s read-only observation builder + the `/research` page shell; no nav re-approval; not data-walled." This spec implements exactly that.
- **Reuse, do not re-derive (iter-2 lesson, applied to J-27):** the per-regime split must use the SAME `_factor_observations` pool. The J-27 consistency invariant is **Σ per-regime n == n_total** (analogous to J-19's "by-sector/by-rank-band n's sum to overall.n"). A reviewer must NOT "reconcile" a per-regime mean against the pooled mean — different populations, legitimately different numbers; only the n's sum.
- **Config-driven vocabulary (iter-9 lesson):** render the regime rows from the server payload (`data.by_regime`, itself derived from `config.regime.labels`), not a hard-coded frontend regime array — so a config regime-label change needs no frontend edit, matching how the factor dropdown is already config-driven.
- **Browser-QA hygiene (iter-6 lesson):** if both the `qa` agent and the `browser-qa-agent` run Chrome-MCP checks, serialize browser access (one vacates before the other captures); de-dup evidence by sha256; ground any "re-points on change" / "byte-identical on as-of change" claim on **distinct** shots + a DOM/network assertion, never a single screenshot pair.
- **Process note for the evaluator (iter-3/6/9/10 lessons):** full-depth iters in this session have repeatedly finished without an `-audit.md` handoff, and `status.json` is written to the **phase-namespace** path `runs/goal-i_can_see_the_wealthy_future_forever-iter-11/status.json` (NOT `runs/goal-session-.../iter-11/`, which holds only `coherence.md` + `snapshot-sha`). Check BOTH paths before concluding an artifact is absent; verify the critical read-only / downside-only / single-source seams directly in `research.py` source rather than trusting a QA artifact table.
- **Not GOAL_ACHIEVED after this iter:** J-26, J-29, J-30, J-31 remain unbuilt `/research` labs (compute-only, now-unblocked) and J-22/J-23/J-24 remain externally data-walled — so failing journeys remain; the evaluator records pass/fail.
