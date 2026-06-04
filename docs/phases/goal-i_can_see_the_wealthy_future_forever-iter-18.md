# Goal Iteration 18 — Factor Lab: composite percentile-rank combination cohort (replace strict-AND headline)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 18
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-26
- **Required-still-passing journeys:** J-25, J-27, J-30 (same Factor Lab page), J-18 (principal anti-goal risk — exactly one date selector), J-15 (read-only / no recompute), J-06, J-07 (scoring/snapshot path must stay byte-identical — no DB regen), J-29, J-31 (other `/research` labs untouched)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Research lab is read-only, honest & not predictive.** Every Factor-Lab and event-study figure (decile means, rank-IC, combination cohorts, regime slices, distribution, hit-rate, expectancy, MAE/MFE, exit-horizon, risk-adjusted ratios) MUST be derived once from the stored per-observation forward returns + stored factor values + post-snapshot price path; the API and frontend MUST NOT recompute returns or factors to build them; low-sample cells show NA + n; results carry the survivorship-bias label. The lab is **descriptive evidence, not a fitted/ML predictive model** — the **composite combination cohort** is a transparent, config-weighted percentile rank-blend of the **stored** factor values (a deterministic ranking/grouping, never a fitted/learned model), and the **as-of-date** mode merely FILTERS the stored observation set to snapshots dated ≤ the as-of date (it recomputes nothing). *(extends No recompute in the read path + No machine-learning price prediction)*
  - **Risk-adjusted reporting is honest & must not conflate up/down volatility.** Every risk-adjusted figure (return/vol, return/MAE, Sharpe-like, expectancy) MUST be derived once from the stored per-observation forward returns + post-snapshot price path; "risk" MUST use downside volatility / MAE / drawdown — never total volatility, which would penalise healthy upside moves; raw and risk-adjusted MUST be shown side by side; low-sample cells show NA + n.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. … The Research **all-history / as-of-date** toggle is likewise a MODE, NOT a date control. *(extends Single source of truth)* — **NOTE: J-32 (the Research as-of toggle) is OUT OF SCOPE this iter (iter-19). This iter adds NO date state of any kind.**
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/ unavailable state and MUST NOT synthesize prices or scores to force a green journey. *(here: an empty/low-sample cohort shows NA + n, never a fabricated 0)*
  - **Single source of truth.** Each canonical value is computed exactly once and read identically by every page; the API and frontend MUST NOT recompute them.

## GOAL

On the **Factor Lab** (`/research`), make the multi-factor **Combined** cohort a **non-empty composite percentile-rank blend** of the selected factors (config-weighted, top config-quantile of the blend), so combining factors yields a real, sample-sufficient cohort instead of the perpetually-0/NA strict AND-intersection — and let the user combine **up to all catalog factors**. The strict-AND overlap stays as an optional, clearly-labelled secondary column.

## BACKGROUND

The operator re-scoped `docs/goal.md` (commit `d723133`) after the iter-16 STALLED, **raising J-26's acceptance bar**: the Combined cohort must now be a **composite percentile-rank blend** that is "**non-empty and clears the min-sample threshold (no longer perpetually 0/NA) and scales to all factors**", with the strict AND-intersection allowed only as an optional secondary "strict overlap" column. The iter-14 implementation (strict AND-intersection) is built and unchanged but no longer meets the headline acceptance — the goal-evaluator correctly re-classified J-26 `passing → partial` at iter-17 (a re-scope bar-raise, **not** a code regression). The iter-17 evaluator's next-step recommendation is explicit: **iter-18 → J-26 (full depth)** — "Replace the strict AND-intersection (`research.py:479 combined_members &= members`) with the re-scoped composite percentile-rank blend … keep the strict-AND as an optional secondary 'strict overlap' column."

Why **full** depth: this touches the **critical read-only research-lab path**, needs real unit tests (composite non-empty + clears `min_sample`; scales to all factors; blend weights/quantile from config — no magic numbers; recomputes no factor/return; downside-only risk-adjusted), and a coherence/closure pass. The nav-skeleton retirement from iter-17 (System Health → single Backtest evidence home) has already been **operator-approved** (`state/blueprint.reapproval-requested` is consumed/absent), so `run-goal.sh` does not pause again here.

**This is a refinement of an EXISTING Data-Contract value, not a new one.** The combination-cohort value keeps its single computing module (`app.engine.research:compute_factor_combination`) and single serving endpoint (`GET /api/research/factor-combination`). We change HOW the Combined cohort is grouped (composite blend instead of strict-AND headline) and add a secondary strict-overlap cohort to the same payload — no second module, no second endpoint, no new page/route/nav entry. The composite is a **ranking/grouping of stored factor values** (percentile ranks of values read verbatim), exactly the same class of read-only operation as the J-25 decile sort — it recomputes **no factor and no return**.

Lessons applied (from `lessons.md` / evaluator log):
- **iter-11:** in this seed you cannot thin a sample by lengthening the horizon (n is ~horizon-independent). Design any honest-NA / empty-cohort fixture around **membership** (opposing-extremes conditions, or a tiny all-factors-non-null pool), never horizon length.
- **iter-10/process:** `status.json` for this session lands at the **phase-namespace** path `runs/goal-i_can_see_the_wealthy_future_forever-iter-18/status.json`, NOT `runs/goal-session-.../iter-18/`. Do not block on an "absent" status.json; verify seams in source.
- **iter-17 watch-item (non-blocking, NOT this iter's path):** `/api/backtest` calls `compute_forward_aggregates` 5×/request — that is the Backtest path, unrelated to `/research`.

## IN SCOPE

### Backend

- [ ] **`app.engine.research:compute_factor_combination`** — replace the strict-AND headline cohort with a **composite percentile-rank blend** cohort, and demote strict-AND to a secondary cohort:
  - **Composite blend (the new headline `Combined`):** over the SAME read-only pool that `_combination_observations(session, distinct_factors, horizon)` already builds (each obs keeps every referenced factor's stored value, read verbatim — no recompute), for each **condition** (a catalog factor at a `top`/`bottom` side):
    1. Compute each observation's **percentile rank** of that condition's factor value within the pool (REUSE the existing pure `_average_ranks` helper → divide by n to get a fraction in (0, 1]).
    2. **Orient by side:** `top` → use the rank fraction as-is (high stored value ⇒ high score); `bottom` → use `1 − rank_fraction` (low stored value ⇒ high score). (The user's `side` orients the blend, consistent with how the single-condition cohorts are oriented; the catalog `direction`/`family` stay descriptive metadata and never flip the sort.)
    3. **Composite score** per observation = the **config-weighted mean** of the oriented percentile ranks across the conditions (default **equal-weight**, i.e. each condition `1/k`, weights normalized to sum to 1 — the equal-weight default and any weighting scheme come from config, never a literal in calc code).
    4. **Composite cohort** = the **top config-quantile** of the pool by composite score (REUSE `_quantile_cutoff` on the sorted composite scores: members = obs with composite ≥ `cutoff(1 − composite_fraction)`; boundary ties included). For a sensible selection this is **non-empty (≈ `composite_fraction · pool_n` names) and clears `walk_forward.min_sample` (30)**.
  - **Strict overlap (secondary):** KEEP the existing exact AND-intersection of the single-condition memberships (the current `combined_members &= members` logic) as a separate, clearly-labelled secondary cohort (e.g. `strict_overlap`, label "Strict overlap (AND)") — shown beside the composite; **NA + n when empty** (never a fabricated 0).
  - **Payload shape:** keep `baseline` + `singles[]` unchanged; the headline `combined` cohort becomes the **composite** cohort (rename to a clear key, e.g. `composite`, label "Combined (composite rank-blend)"), and add the secondary `strict_overlap` cohort. Both reuse `_cohort_stats` → the downside-only `_risk_adjusted` (mean / downside-deviation; NA when no downside / n<2 — never total vol). Echo the resolved composite quantile + weighting in the payload so the UI labels them honestly. Remove the old single `combined` key cleanly (update all references — no back-compat alias, no dead code).
  - **Scales to all factors:** the algorithm must accept up to all catalog factors with no code cap; the only cap is `comb.max_conditions` (config).
  - Keep it **read-only**: SELECT-only via `_combination_observations`; call no `run_scan` / `score_stocks` / `backfill*` / `forward_return` / `detect_*` / `score_regime`. Percentile-ranking stored values is a grouping, not a recomputation.

- [ ] **`config.yaml` → `research.factor_lab.combination`:**
  - Add a `composite` sub-block with the blend's tunables: the **`quantile`** (a real `quantiles` key — the top fraction of the composite taken as the cohort, e.g. `quintile`) and the **`weighting`** default (equal-weight; the config-declared scheme + default weight — no `1/k` literal invented in code beyond structural arithmetic). Keep `quantiles`, `default_conditions`, `min_conditions` as-is.
  - **Raise `max_conditions`** so a user can combine **up to all catalog factors** — set it to the number of catalog factors (currently **11**), config-driven (the cap lives in config, not code).

- [ ] **`apps/backend/app/config.py` → `CombinationCfg`** (+ a small typed `CompositeCfg`): type the new `composite` block and validate it at boot (loud `ConfigError`, never a silent default): `composite.quantile` MUST be a real `quantiles` key; the weighting scheme/default weight valid (> 0). Keep the existing `1 ≤ min_conditions ≤ max_conditions`, unique-quantile-key, and default-conditions cross-checks. (Remember `config-fixtures-need-new-required-keys`: if `composite` becomes a required field, add it to ALL inline test config dicts that build a `CombinationCfg`/`FactorLabCfg`, not just the obvious one.)

- [ ] **`apps/backend/app/api/research.py` → `factor_combination`** — endpoint signature is unchanged (`condition` repeatable + `horizon`); the composite + strict-overlap cohorts ride the same payload verbatim. The condition-count validation already reads `comb.min_conditions`/`comb.max_conditions`, so raising `max_conditions` automatically lets the endpoint accept up to all catalog factors. **Add NO `as_of` param** (J-32 is iter-19; J-18 — no date state).

### Frontend

- [ ] **`apps/frontend/app/research/page.tsx` → `CombinationTable` + `CombinationLab`:**
  - Render the **composite** cohort as the primary, emphasized "Combined" row (it is now non-empty), and the **strict overlap (AND)** cohort as a secondary, clearly-labelled row (NA + n when empty, via the existing `CohortCell`/`SampleSize`). Row order: Baseline → each single → **Combined (composite)** → Strict overlap (AND).
  - The condition editor already disables "Add condition" at `data.max_conditions` (payload-driven) — confirm raising the config cap lets the UI add up to all catalog factors; no hard-coded cap in the UI.
  - Update the section **hint text** (currently "Combine 2–3 factor conditions … combined-AND cohort") to describe the composite rank-blend (non-empty, top config-quantile, config-weighted default equal) and that strict-overlap is the optional secondary column.
  - **Add NO date/as-of state** (J-18). Reuse the page's shared `horizon` selector only.
- [ ] **`apps/frontend/lib/api.ts` → `FactorCombinationResponse`** — update the type to carry `composite` + `strict_overlap` (replacing the old single `combined`), plus the echoed composite-quantile/weighting metadata. Re-format only — never compute a cohort client-side.

### New user-facing capability

On `/research` → Factor Lab → "Multi-factor combination cohort", the user can add **2 up to all catalog factor** conditions and read a **Combined (composite rank-blend)** cohort that is actually populated (mean / median forward return, hit-rate, downside risk-adjusted, n) — beside the all-names baseline, each single-factor cohort, and a secondary **Strict overlap (AND)** column — so factor interaction is visible and "does combining beat either alone?" is answerable instead of perpetually NA.

### New information displayed

A populated **Combined (composite)** cohort row (non-empty for a sensible selection) and a secondary **Strict overlap (AND)** row (honest NA + n when empty). The composite quantile + equal-weight labelling is shown so the blend is transparent. Survivorship-bias + descriptive-not-predictive labels persist.

### New user actions

Add/remove combination conditions up to all catalog factors (the existing add/remove control, cap raised via config). No new control type; no date control.

### UI surface changes

The existing "Multi-factor combination cohort" section on `/research` (Factor Lab). No new page, route, or nav entry.

### Product surface delta

The combination section graduates from "strict AND-intersection that is usually 0/NA" to "a non-empty composite cohort + an honest strict-overlap secondary" — the section now delivers real, sample-sufficient combination evidence and scales to the whole factor catalog.

### Blueprint conformance

Lives under the **existing approved `/research`** Information-Architecture home (Factor Lab page) — **no nav-skeleton change, no `blueprint.reapproval-requested`**. The iter-17 System Health retirement is already operator-approved (marker consumed).

### Data-contract additions

**None — this refines an EXISTING value.** The combination-cohort value keeps its single computing module `app.engine.research:compute_factor_combination` and single serving endpoint `GET /api/research/factor-combination`. The blueprint's existing J-26 Data-Contract row is edited (additively) to describe the composite blend replacing the strict-AND headline + the secondary strict-overlap; no second computation, no second endpoint, no new value introduced. Read the registered canonical stored factor values + stored returns; introduce no parallel source.

## OUT OF SCOPE

- **J-32 (Research as-of toggle).** No `as_of` param on any `/research` endpoint, no date/mode state — that is iter-19. This iter adds **zero** date state.
- **J-22 / J-23 / J-24** (expanded universe, intraday, timeframe selector) — externally Yahoo-429 data-walled and **non-halting** per the re-scoped goal; do NOT autonomously re-probe or retry.
- Any change to `scoring.py` / `scanner.py` / `regime.py` / `patterns.py` / `buckets.py` / `forward_testing.py` math or the snapshot/serving path — **no DB regen** (this is a pure read-only `/research` change; J-06/J-07 must stay byte-identical).
- Per-condition custom user weights via the request (extensibility point) — the must is the **config-driven equal-weight default**; only add request-level weights if trivial and fully config-defaulted. Do not over-build.
- Boolean pattern-flag conditions in the combination (still out of scope, as in iter-12).
- return/MAE risk-adjustment in the combination cohort (lives in J-29's event study; the combination cohort uses the downside-deviation `_risk_adjusted` only).

## DEFINITION OF DONE

- [ ] **J-26 passes via browser-qa-agent** on `/research`: the Combination Lab shows a **non-empty Combined (composite)** cohort (n ≥ `min_sample`, populated mean/median/hit-rate/risk-adjusted) for the default conditions, beside Baseline + singles + a secondary **Strict overlap (AND)** row; adding conditions up to several/all catalog factors keeps the composite non-empty; an empty strict-overlap selection shows the **composite populated while strict-overlap shows NA + n** (the headline improvement, captured live).
- [ ] **Required-still-passing journeys remain green:** J-25 (decile/rank-IC re-point on factor change), J-27 (by-regime split), J-30 (volatility family) on the same page; J-18 (the global as-of toggle leaves the lab byte-identical with **zero `as_of` requests**; exactly one `<select>` for date, none added on `/research`); J-06/J-07 (scoring/snapshot path untouched — git-verify, no DB regen); J-29/J-31 unaffected.
- [ ] **No anti-goal violation introduced** — verified in source: read-only (patch-to-raise keystone covers the composite path), downside-only risk-adjusted, no magic numbers (composite quantile + weighting + raised `max_conditions` all from config), no fabricated data (empty/low-sample → NA + n), exactly one date selector (no date state added to `/research`), single source of truth (same module + endpoint).
- [ ] **Unit tests pass; no regressions.** Full backend pytest green (run ONCE per `backend-test-suite-runtime`); frontend `npm run build` typechecks.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-18-dev.md`.

## TESTING REQUIREMENTS

- **Browser (J-26 on `/research`, exclusive Chrome — serialize vs any other Chrome user, de-dup evidence by sha256):**
  - Default load → Combination Lab: assert the **Combined (composite)** row is populated (n ≥ 30, numeric mean/median/hit-rate/risk-adjusted via DOM), distinct from Baseline; the **Strict overlap (AND)** secondary row renders.
  - Add conditions up to (near) all catalog factors → composite stays non-empty (DOM-assert n > 0).
  - Drive an **empty-strict-overlap** selection (e.g. opposing-extremes or many-factor selection) → assert **composite populated AND strict-overlap = NA + n** in the same shot (membership-driven NA per the iter-11 lesson, not horizon-driven).
  - **J-18 re-verify:** toggle the global as-of (in-app, not hard reload — iter-1 lesson) → the lab is byte-identical (distinct sha256 before/after + network spy showing **zero `/api/research/*?as_of=` requests**); count exactly one date `<select>` (none added on `/research`).
  - Spot-check J-25/J-27/J-30 still render and re-point above the Combination Lab.
- **Unit/integration (backend `tests/test_research.py` + `tests/test_api_research.py`):**
  - **Composite non-empty + clears `min_sample`** for the default conditions: `composite.stats.n ≥ min_sample` and `> 0` (the headline fix).
  - **Scales to all factors:** a selection up to `max_conditions` (≈ all catalog factors) returns a non-empty composite cohort.
  - **Orientation correctness:** on a monotone fixture, a `top`-side composite selects the high-factor names and a `bottom`-side composite selects the low-factor names.
  - **Strict overlap retained + honest NA:** extend `test_combination_opposing_extremes_empty_cohort_is_na_not_zero` so the opposing-extremes fixture yields **`strict_overlap` n=0 / NA AND `composite` non-empty** (proves the bar-raise is met on the exact fixture that used to be 0/NA).
  - **Read-only keystone:** extend `test_combination_is_read_only_no_scoring_or_return_or_pattern_call` so the composite path also triggers no `run_scan`/`score_stocks`/`backfill*`/`forward_return`/`detect_*`/`score_regime` (patch-to-raise).
  - **Downside-only risk-adjusted:** composite/strict cohort `risk_adjusted` is `mean / downside_deviation` (NA when no downside / n<2) — never total vol.
  - **Cohort algebra:** `composite ⊆ baseline`; `strict_overlap ⊆ each single`; `baseline.n == pool_n`.
  - **No magic numbers:** `test_no_magic_numbers` still passes (no decile/quantile/weight/cap literal in `research.py`).
  - **Config validation (boot `ConfigError`):** `composite.quantile` not a real `quantiles` key → raises; invalid weighting → raises; existing `min/max`/quantile/default-condition cross-checks still raise.
  - **Config-driven cohort size:** changing `composite.quantile` re-points the composite cohort `n` (proves the cap/fraction is config-sourced, not hard-coded).
- **Error cases:** unknown factor/side/quantile and out-of-range condition count still → `422` (existing endpoint tests, now exercised up to the raised cap); invalid horizon → `422`; no-price-data → `503`.

## NOTES

- **The composite is NOT a fitted/ML model.** It is a deterministic, transparent percentile-rank blend of **stored** factor values (the goal's anti-goal explicitly blesses exactly this). Make that legible in source comments + the dev handoff so the reviewer/auditor/coherence-auditor do not mistake the rank-blend for a recomputation or a learned model. It ranks stored values (like the J-25 decile sort) — it recomputes no factor and no return.
- **No DB regen** this iter — `score_stocks`/snapshots are untouched, so J-06/J-07 stay byte-identical (git-verify the scoring path is absent from the diff; do not re-bootstrap the DB).
- **Verify seams in source, not the QA table.** Per the recurring full-depth process gap in this session, `status.json` lands at the phase-namespace path (`runs/goal-i_can_see_the_wealthy_future_forever-iter-18/status.json`) and an `-audit.md` handoff is often absent — substitute source-level verification of the read-only seam, the composite-non-empty invariant, and the J-18 no-date-state seam.
- **Evidence hygiene:** de-dup browser screenshots by sha256 (iter-3/6 duplicate-shot bug); ground every before/after claim on distinct shots + a DOM/network assertion.
- **Strategic (for the evaluator, not this iter's build):** after J-26 lands, **iter-19 → J-32** (Research All-history ⟷ As-of-date MODE, reusing iter-17's `asof_date ≤ D` seam — a mode, not a second date control). After J-26 + J-32 land and nothing regresses, **GOAL_ACHIEVED is reachable** on the buildable set — J-22/J-23/J-24 are honestly blocked (NA) and **non-halting per the re-scoped goal**; do NOT autonomously re-probe them.
