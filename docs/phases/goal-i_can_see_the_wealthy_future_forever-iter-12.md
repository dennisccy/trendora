# Goal Iteration 12 — Factor Lab: multi-factor combination cohorts (J-26)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 12
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-26
- **Required-still-passing journeys:** J-25, J-27, J-18, J-09, J-19, J-15, J-16, J-28, J-01, J-12
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **Research lab is read-only, honest & not predictive.** Every Factor-Lab and event-study figure (decile means, rank-IC, combination cohorts, regime slices, distribution, hit-rate, expectancy, MAE/MFE, exit-horizon, risk-adjusted ratios) MUST be derived once from the stored per-observation forward returns + stored factor values + post-snapshot price path; the API and frontend MUST NOT recompute returns or factors to build them; low-sample cells show NA + n; results carry the survivorship-bias label. The lab is **descriptive evidence, not a fitted/ML predictive model**. *(extends No recompute in the read path + No machine-learning price prediction)*
  - **Risk-adjusted reporting is honest & must not conflate up/down volatility.** Every risk-adjusted figure (return/vol, return/MAE, Sharpe-like, expectancy) MUST be derived once from the stored per-observation forward returns + post-snapshot price path; "risk" MUST use downside volatility / MAE / drawdown — never total volatility, which would penalise healthy upside moves; raw and risk-adjusted MUST be shown side by side; low-sample cells show NA + n. *(extends Research lab is read-only)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey. *(here: low-sample cohorts show NA + n, never a fabricated return)*
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. *(the Factor Lab is a cross-date aggregate — it has NO date control at all; the new section adds none)*
  - **Single source of truth.** Each canonical value MUST be computed exactly once and read identically by every page; the API and frontend MUST NOT recompute it.

## GOAL

On the Factor Lab (`/research`), the user can combine **2–3 factor conditions** (each = a catalog factor at its **top** or **bottom** quantile, e.g. *RS-3m top-quintile AND ATR% bottom-tertile*) and read the **combined (AND) cohort's** forward return (raw mean, median, downside-risk-adjusted), **hit-rate (% positive)**, and **n** side-by-side against the **unconditional baseline** and each **single-factor cohort** — so factor *interaction* effects are visible — derived once, read-only, from the already-stored forward returns + stored factor values.

## BACKGROUND

24/31 must-have journeys pass (iter-11 ended CONTINUE; J-27 regime-split landed clean). The remaining failing journeys split into two groups: **externally data-walled** (J-22/J-23/J-24 — Yahoo HTTP 429 on the no-key feed; **do NOT autonomously retry** — they auto-heal only on operator confirmation of a reachable egress) and **unbuilt compute-only `/research` labs** (J-26, J-29, J-30, J-31). The iter-11 evaluator's explicit recommendation is **full depth, target J-26** — the smallest direct extension of the now-doubly-proven read-only Factor-Lab seam (J-25 decile/IC + J-27 by-regime). It is compute-only over the existing stored seed (**not data-walled**) and rides the **existing approved `/research` home** as an additive section (**no nav re-approval, no `blueprint.reapproval-requested`**).

The seam this iteration extends already exists and is verified read-only: `app.engine.research._factor_observations` builds the per-observation `{run_id, ticker, factor, return, regime}` pool by SELECT-only-joining stored `forward_returns.realized_return` to the stored factor value on `ScannerResult` (`_extract_factor_value` reads a typed column or a `record_json` component `raw` **verbatim**); `_risk_adjusted` is the downside-only `mean / downside_deviation`; `_deciles`/`_regime_effectiveness` are pure groupings. J-26 reuses these primitives over a **multi-factor** observation pool. This is full depth (a new read-only aggregation + a new serving endpoint + new frontend section + real unit tests + coherence/ux-regression/closure on the critical read-only research surface) — the same justification J-25/J-27 carried.

**Lessons applied (from this session's ledger):**
- *iter-2 (wrong-consistency-invariant lesson):* do **not** assert `baseline.mean == compute_forward_aggregates(h).overall.mean_return`. The combination pool requires **all referenced factors non-null**, so it is a (possibly strict) **subset** of any single factor's `_factor_observations` pool — a different population. The correct, asserted invariants are nesting/intersection (see DEFINITION OF DONE), not equality to the aggregate mean.
- *iter-11 (NA-fixture lesson):* you cannot thin samples by lengthening the horizon (n is ~horizon-independent in this seed). Design the low-sample/NA fixture around a **genuinely small combined cohort** — the AND of two *opposing* extremes (e.g. *top-quintile of A* AND *bottom-quintile of A*, or two near-orthogonal extremes) naturally yields `n < min_sample` → honest NA — or the downside-undefined (all-non-negative) risk-adjusted case.
- *iter-6 (browser-evidence-hygiene lesson):* serialize Chrome access between the `qa` and `browser-qa` agents, de-dup every screenshot by sha256, and ground any "before/after" / "re-points" claim on **distinct** shots + a DOM/network assertion — never a single pair.
- *iter-10/11 (full-depth artifact lesson):* a full-depth goal iter in this session typically produces **no `-audit.md`** handoff and writes `status.json` at the **phase-namespace** path `runs/goal-i_can_see_the_wealthy_future_forever-iter-12/status.json` (not under `runs/goal-session-.../iter-12/`). The evaluator should verify the critical read-only seams **in source**, not block on the missing audit/status artifacts.

## IN SCOPE

### Backend
- [ ] **`apps/backend/app/engine/research.py` — add `compute_factor_combination(session, conditions, horizon, config) -> dict`** (the SINGLE canonical multi-factor combination read; read-only):
  - [ ] Add a read-only **multi-factor observation builder** (e.g. `_combination_observations(session, factors, horizon)`) that mirrors `_factor_observations`: SELECT `ForwardReturn` (at `horizon`) + the `ScannerResult` rows for runs that have a return, read **each** referenced factor's stored value via the existing `_extract_factor_value` (+ `parse_factor_source`), and keep an observation **only when a realized return exists AND every referenced factor is non-null** (a NULL in any referenced factor **excludes** that observation — never fabricated). Each obs carries `{run_id, ticker, return, values: {factor_key: float}}`. Issue **only SELECTs**; call **no** `run_scan` / `score_stocks` / `backfill*` / `forward_return` / `detect_*` / `score_regime` — recompute **no** factor and **no** return.
  - [ ] **Quantile threshold** per condition, computed over the shared pool's values for that factor: a **deterministic, tie-tolerant** empirical cutoff (e.g. nearest-rank on the sorted pool values). `side: top` ⇒ membership = `value >= cutoff(1 − fraction)`; `side: bottom` ⇒ membership = `value <= cutoff(fraction)`. Ties at the boundary are **included** (a cohort may be marginally larger than `fraction · pool_n`) — honest, documented in the docstring; the method is a fixed statistical rule (NOT a tunable → no magic-number violation; only the `fraction` is config).
  - [ ] **Cohorts:** `baseline` = the whole pool; one `single` cohort per condition (its own membership); `combined` = the **exact set-intersection (AND)** of all single memberships.
  - [ ] **Per-cohort stats** (`CohortStats`): `mean_return` (`statistics.mean`), `median_return` (`statistics.median`), `hit_rate` (fraction of member returns `> 0`), `risk_adjusted` (REUSE the existing downside-only `_risk_adjusted` — `mean / downside_deviation`, MAR=0; **never total volatility**), `n`, `low_sample` (`n < walk_forward.min_sample`). Empty cohort ⇒ `mean_return`/`median_return`/`hit_rate`/`risk_adjusted` = `None` (NA), never a fabricated 0.
  - [ ] **Payload** returns: the resolved `conditions` (each `{factor:{key,label,family,direction,source}, side, quantile:{key,label,fraction}}`), `horizon`, `horizons`, `default_horizon`, `min_sample`, `min_conditions`, `max_conditions`, the config-driven `factors` catalog (reuse `factor_catalog`), the config-driven `quantiles` list, `survivorship_bias` (reuse `SURVIVORSHIP_BIAS_LABEL`), `descriptive_caveat` (reuse `RESEARCH_CAVEAT`), `pool_n`, `baseline {label, stats}`, `singles [{condition, stats}, …]`, `combined {label, stats}`. Raise `ValueError` for an unknown factor/side/quantile or an out-of-range condition count (the API pre-validates → 422).
- [ ] **`apps/backend/app/api/research.py` — add `GET /api/research/factor-combination`** (the single canonical serving endpoint for this NEW value; returns `compute_factor_combination(...)` verbatim, recomputing nothing):
  - [ ] Query params: `condition` (repeatable, each `"<factor_key>:<side>:<quantile_key>"`) and `horizon` (optional int). When `condition` is omitted/empty → use `config.research.factor_lab.combination.default_conditions`.
  - [ ] Validate: condition **count ∈ [min_conditions, max_conditions]**; each `factor_key ∈ factor_catalog`; `side ∈ {top, bottom}`; `quantile_key ∈ config quantiles`; `horizon ∈ walk_forward.horizons` → **422** on any violation (no fabricated factor/side/quantile/horizon). **503** when no price data exists at all (mirror the existing `factor_lab` route / `system_health.py`). NO as-of/date param (J-18).
- [ ] **`config.yaml` — extend `research.factor_lab` with a `combination` block** (every tunable in config — No magic numbers):
  - [ ] `min_conditions: 2`, `max_conditions: 3`.
  - [ ] `quantiles:` an ordered list of `{ key, label, fraction }` (e.g. `quintile 0.20`, `quartile 0.25`, `tertile 0.3333`, `half 0.50`) — the dropdown vocabulary, server-driven (a config-only quantile needs no frontend edit).
  - [ ] `default_conditions:` the canonical 2-condition default shown on first load (e.g. `{factor: rs_spy_3m, side: top, quantile: quintile}`, `{factor: atr_pct, side: bottom, quantile: tertile}`) — each referencing a real catalog factor + a real quantile key, count within `[min_conditions, max_conditions]`. The low-sample threshold is **REUSED** from `walk_forward.min_sample` (no new threshold).
- [ ] **`apps/backend/app/config.py` — type + validate the new block** (extend `FactorLabCfg`, which is `extra="allow"`, with a typed `combination: CombinationCfg`): validate `1 <= min_conditions <= max_conditions`; every `quantiles[*].fraction ∈ (0, 1)` and `key` unique; every `default_conditions[*].factor` ∈ the sibling `factors` keys and `.quantile` ∈ the `quantiles` keys and `.side ∈ {top, bottom}`; `min_conditions <= len(default_conditions) <= max_conditions`. An invalid block raises `ConfigError` at boot — **never a silent default** (match the existing `_validate` / `_factor_lab_sources_resolve` discipline).

### Frontend
- [ ] **`apps/frontend/lib/api.ts`** — add types `FactorCombinationCondition`, `QuantileOption`, `CohortStats`, `FactorCombinationResponse`, and `fetchFactorCombination(conditions, horizon, signal)` (throws on non-200 → explicit "Backend unavailable", never fabricated). Builds `condition=<factor>:<side>:<quantile>` repeated query params.
- [ ] **`apps/frontend/app/research/page.tsx`** — add a **"Multi-factor combination cohort"** section **below** the existing regime-effectiveness table:
  - [ ] **Controls (config-driven, server-data only):** 2–3 condition rows, each = a **Factor** `<Select>` (from `data.factors`), a **Side** toggle (**Top** / **Bottom**), and a **Quantile** `<Select>` (from `data.quantiles`). A **"+ Add condition"** control (disabled at `max_conditions`) and a per-row **remove** (disabled at `min_conditions`). The factor/quantile option lists come **from the payload** — **no hard-coded factor or quantile list in the frontend** (extends the config-driven-vocabulary anti-goal). Default conditions come from the first payload (server `default_conditions`).
  - [ ] **Reuse the existing page `horizon` state** for this section (one shared horizon selector for the whole page). Add **only** `conditions` state — **no as-of/date state** (J-18). A second `useEffect` keyed on `[conditions, horizon]` fetches `factor-combination`.
  - [ ] **Comparison table:** rows = **Baseline (all names)**, one row per single condition (labelled e.g. "RS vs SPY (3m) · top quintile"), and **Combined (AND)**; columns = **Cohort**, **n**, **Mean fwd return**, **Median**, **Hit-rate**, **Risk-adjusted (downside)**. Re-format the payload only; render **NA + the honest `n`** when a cohort is `low_sample` or a stat is `null` (reuse the existing `SampleSize` / `DecileValue`-style NA treatment — never a fabricated number). Show a short honest note that **return/MAE is not yet available** (arrives with the event-study lab, J-29) so the single risk-adjusted column (downside-deviation) is not silently passing as "all" risk measures.
  - [ ] Loading skeleton + the existing "Backend unavailable" error treatment for this section; an empty-pool state (`pool_n === 0`) renders an honest empty message (no fabricated cohort).

### New user-facing capability
The user can compose a 2–3 condition multi-factor cohort on the Factor Lab and immediately see whether **combining** factors adds value over the **baseline** and over **each single factor** — reading mean, median, hit-rate, downside-risk-adjusted return, and sample size, with honest NA on thin combined cohorts.

### New information displayed
A "Multi-factor combination cohort" comparison table: Baseline vs each single-condition cohort vs the Combined (AND) cohort, each with n / mean / median / hit-rate / downside-risk-adjusted forward return at the selected horizon.

### New user actions
Pick a factor + side (top/bottom) + quantile for each of 2–3 conditions; add/remove a condition; change the shared horizon — all re-point the combination table.

### UI surface changes
One additive section appended to the existing `/research` Factor Lab page. **No new page, no new route, no nav/sidebar change.**

### Product surface delta
The Factor Lab graduates from single-factor evidence (decile/IC, regime split) to **interaction** evidence — the user can test "do two signals together beat either alone?" — still purely descriptive, read-only, honest about small samples.

### Blueprint conformance
Lives under the **existing approved `/research`** Information-Architecture home (Factor Lab page). **No nav-skeleton change → no `blueprint.reapproval-requested` written.** Blueprint updated additively: a new Data-Contract row for the J-26 combination value, an IA-homes row for J-26, and an iter-12 nav-skeleton note ("NO skeleton change").

### Data-contract additions
ONE new displayed value — **Factor-Lab multi-factor combination cohorts** (baseline + per-single-condition + combined-AND cohort: mean / median forward return, hit-rate, downside-risk-adjusted, n) — computed once by `app.engine.research:compute_factor_combination` and served by `GET /api/research/factor-combination`. This is a **NEW** descriptive aggregation, **not a duplicate**: the single-factor decile/IC/regime value keeps its canonical home (`compute_factor_lab` / `GET /api/research/factor-lab`); the realized *returns* keep theirs (`forward_testing` → `forward_returns`); the factor *values* keep theirs (`scoring:score_stocks` → `scanner_results`/`record_json`). This row registers only the new read-only multi-factor cohort grouping over those same stored values — exactly as the J-19 attribution slices and the J-27 regime split are distinct read-only slices of the same stored returns. (Registered in `blueprint.md` by this spec's blueprint edit.)

## OUT OF SCOPE

- **Boolean pattern-flag conditions** (e.g. "VCP-flagged" as a condition). The goal's J-26 example cites "… AND VCP-flagged" illustratively, but the **acceptance** is quantile-cohort-based; conditions this iteration are catalog-factor top/bottom quantiles only. Leave the condition model extensible to boolean flags, but do not build pattern-flag conditions now (keeps the iteration tight; a later follow-on can add them).
- **return/MAE and MAE/MFE excursion** — these need the post-snapshot daily high/low excursion path, which is **J-29's** deliverable (sequenced after J-26/J-30). J-26's risk-adjusted column is the established **downside-deviation** measure (`_risk_adjusted`); the UI states return/MAE arrives with J-29 (honest, not hidden).
- **Any new decile/IC math** — the combination reuses the existing pure helpers; the single-factor decile table / rank-IC / regime split are unchanged.
- **J-22 / J-23 / J-24** — externally Yahoo-429 data-walled; do **not** fetch, probe, or retry.
- **J-29 / J-30 / J-31** — later `/research` labs; not this iteration.
- Any change to `scoring.py` / `forward_testing.py` / `scanner.py` / `patterns.py` / `regime.py` / `snapshot_serving.py` / the as-of provider / `backtest/page.tsx` / any existing endpoint. The diff must be additive (new engine function + new route + config block + new frontend section + tests).
- No new date/as-of control anywhere (J-18).

## DEFINITION OF DONE

- [ ] **Target J-26 passes via browser-qa-agent:** on `/research`, building a 2-condition combined cohort (and adding a 3rd) renders the comparison table with Baseline + each single + Combined, each showing n / mean / median / hit-rate / downside-risk-adjusted; at least one configuration shows the Combined cohort with `n` **smaller** than each single (interaction visible), and a deliberately thin combined cohort shows **NA + n** (not a fabricated number).
- [ ] **Required-still-passing journeys remain green:** J-25 (decile table + rank-IC still render and re-point on factor change), J-27 (regime table intact), **J-18** (changing the global as-of leaves the WHOLE `/research` page — decile table, rank-IC, regime table, AND the new combination table — byte-identical, with **zero** `as_of`-param requests), J-09 / J-19 / J-15 (forward-testing + attribution + snapshot-served read paths untouched), J-16 / J-28 / J-01 / J-12 (additive `/research` diff).
- [ ] **No anti-goal violation introduced** — verified in source: `compute_factor_combination` issues only SELECTs and calls no scoring/return/pattern/regime math; the risk-adjusted column is downside-only; quantiles/limits/defaults come from config; low-sample/empty cohorts show NA + n.
- [ ] **Unit tests pass; no regressions.** New tests in `apps/backend/tests/test_research.py` (see TESTING). The full backend suite passes (run **once** — project-memory: ~14 min, do not run two pytest invocations concurrently); frontend typechecks.
- [ ] **Coherence:** coherence-auditor returns COHERENCE-PASS (new value registered in the Data Contract; no existing contract value recomputed or served from a new path; no duplicate home).
- [ ] **Dev handoff** written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-12-dev.md`.

## TESTING REQUIREMENTS

- **Browser (browser-qa-agent), serialized with the qa agent on the shared Chrome; de-dup every shot by sha256:**
  - **J-26:** load `/research`; confirm the "Multi-factor combination cohort" section renders the default 2-condition cohort with a Baseline row, two single rows, and a Combined (AND) row, each with n / mean / median / hit-rate / risk-adjusted. Change a condition (factor/side/quantile) and confirm a fresh `GET /api/research/factor-combination?...` fires and the DOM matches the API (distinct before/after shots + observed network). Add a 3rd condition; confirm the table grows to 3 single rows + Combined and that Combined `n` ≤ each single `n` ≤ pool. Drive the **NA fixture** (opposing extremes → thin combined cohort) and capture the **NA + n** Combined cell.
  - **J-18 (regression, the principal risk):** with the combination section present, toggle the global as-of date (e.g. latest → a historical date) and assert the decile table, rank-IC, regime table **and the new combination table** are byte-identical with **zero** `as_of`-param requests (extend the existing iter-11 UT-08 check to cover the new table).
  - **J-25 / J-27 (regression):** decile table + rank-IC + regime table still render and re-point on factor/horizon change.
- **Unit/integration (`apps/backend/tests/test_research.py`):**
  - **Read-only keystone (critical):** extend the existing patch-to-raise keystone so monkeypatching `run_scan` / `score_stocks` / `forward_return` / `detect_*` / `score_regime` to raise does **not** break `compute_factor_combination` (it SELECTs + pure-groups only).
  - **Cohort algebra:** on a controlled fixture, assert `combined` membership == exact set-intersection of the single memberships; `baseline.n == pool_n`; each `single.n <= pool_n`; `combined.n <= min(single.n)`.
  - **Stats correctness:** mean / median / hit-rate computed exactly on a known fixture; `risk_adjusted` equals the downside-only `_risk_adjusted` of the membership (and is `None` for an all-non-negative or `n<2` cohort).
  - **No magic numbers:** `min_conditions`/`max_conditions`/`quantiles`/`default_conditions` are read from config; `test_no_magic_numbers` (scanning `research.py`) still passes (no new literal in calc code).
  - **Honest NA:** a deliberately thin combined cohort (`n < min_sample`) ⇒ `low_sample: true` and the UI renders NA; an empty cohort ⇒ stats `None`, never a fabricated 0.
  - **Pool honesty:** an observation NULL in any referenced factor is excluded from the pool (so `pool_n` ≤ each single factor's `_factor_observations` n — do **not** assert equality to `compute_forward_aggregates.overall.mean`).
- **Error / config cases:** unknown factor/side/quantile or out-of-range condition count → `ValueError` (engine) / **422** (API); `horizon ∉ walk_forward.horizons` → 422; no price data → 503; invalid `combination` config (min>max, fraction ∉ (0,1), duplicate quantile key, `default_conditions` referencing an unknown factor/quantile, or count outside [min,max]) → **ConfigError at boot**.

## NOTES

- **Why a new endpoint is coherent (not a duplicate):** J-26 needs inputs the single-factor endpoint cannot express (a *list* of factors + per-factor quantile conditions), and it produces a genuinely new value (combined-AND cohort vs baseline vs singles). The coherence-auditor hard-fails on recomputing an *existing* contract value, serving an *existing* value from a non-canonical path, or a duplicate home — none apply here. The single-factor decile/IC/regime value stays on `compute_factor_lab` / `/api/research/factor-lab`, untouched. Register the new value in the Data Contract (done in this spec's blueprint edit) so the auditor sees one canonical computing module + one serving endpoint for it.
- **Risk-adjusted = downside-only, reused.** Do not introduce a second risk measure or any total-volatility ratio. Reuse `_risk_adjusted` / `_downside_deviation` verbatim; show raw mean alongside it.
- **Process expectation (evaluator):** per the iter-10/11 pattern, this full-depth iter will likely produce no `-audit.md` and write `status.json` at the phase-namespace path `runs/goal-i_can_see_the_wealthy_future_forever-iter-12/status.json`. Verify the read-only / downside-only / no-magic-numbers seams **in source**; do not block on the missing audit handoff.
- **Autonomous runway after J-26:** J-30 (volatility family — extends the J-25 catalog + J-27 regime split) → J-29 (event study — larger lift; needs the post-snapshot daily high/low MAE/MFE excursion path extracted first; this is where return/MAE lands) → J-31 (synthesis; needs J-29 + J-27). **GOAL_ACHIEVED is not autonomously reachable** while J-22/J-23/J-24 stay externally data-walled — expect either operator confirmation of a reachable no-key egress or a (correct) STALLED on the data-walled remainder once the labs are done. Do **not** autonomously retry J-22/J-23/J-24.
