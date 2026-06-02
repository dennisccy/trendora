# Goal Iteration 13 — Volatility as a first-class factor family (Factor Lab), risk-adjusted & regime-conditioned

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 13
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-30
- **Required-still-passing journeys:** J-07 (CRITICAL — re-verify after DB regen), J-06 (CRITICAL — re-verify after DB regen), J-02, J-05, J-08, J-09, J-12, J-16, J-18, J-19, J-25, J-27
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **Research lab is read-only, honest & not predictive.** Every Factor-Lab figure (decile means, rank-IC, regime slices, risk-adjusted ratios) MUST be derived once from the stored per-observation forward returns + stored factor values + post-snapshot price path; the API and frontend MUST NOT recompute returns or factors to build them; low-sample cells show NA + n; results carry the survivorship-bias label. The lab is **descriptive evidence, not a fitted/ML predictive model.**
  - **Risk-adjusted reporting is honest & must not conflate up/down volatility.** Every risk-adjusted figure (return/vol, return/MAE, Sharpe-like, expectancy) MUST be derived once from the stored per-observation forward returns + post-snapshot price path; "risk" MUST use downside volatility / MAE / drawdown — never total volatility, which would penalise healthy upside moves; raw and risk-adjusted MUST be shown side by side; low-sample cells show NA + n.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **Honest limitations surfaced.** Walk-forward evidence MUST be labelled as carrying survivorship bias (current-membership universe) so results are never overstated.
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page reads the single global as-of control. *(extends Single source of truth)*
  - **VCP is a pattern, not a status.** VCP rides as a separate flag computed once per run, price+volume only, with date ≤ D. *(critical)* — *(the new `vcp_contraction` FACTOR is a continuous volatility measure, NOT the VCP pattern flag; it MUST NOT touch `detect_vcp`, the setup status, or any score.)*

## GOAL

On the Factor Lab (`/research`), make **volatility a first-class factor family** — the user can select each of three volatility measures (**level**: ATR% + historical volatility; **change/contraction**: a VCP-style volatility-compression measure; **downside/semivol**) and read its decile table (raw mean forward return **and** the downside-risk-adjusted column) + Spearman rank-IC + the by-regime effectiveness split, each with sample size `n` and honest NA — so the evidence makes explicit *which* volatility measure and *which direction* actually predicts forward return in this universe (not the assumed textbook relationship), with the contraction measure cross-checked for consistency against the existing VCP forward-test evidence.

## BACKGROUND

This is the next compute-only `/research` lab member after J-25 (decile/IC, iter-10) → J-27 (regime split, iter-11) → J-26 (combination cohorts, iter-12). The iter-12 evaluator recommended **full depth, target J-30**, and explicitly required the decomposer to determine up front whether the volatility factor values already exist or must be added.

**Decisive codebase finding (verified in source this planning pass):** the Factor-Lab catalog (`config.research.factor_lab.factors`) currently carries **exactly one** volatility-family factor — `atr_pct` (level, `source: risk.components.atr_pct.raw`). The indicator engine (`apps/backend/app/engine/indicators.py`) computes ATR%, SMA, RS, MA-stack, dist-from-high, vol-trend — but **no historical-volatility (stdev-of-returns), no independent contraction value, and no downside/semivol**. The `entry_quality.contraction` component (`scoring.py:146`) is just `_neg(atr)` = −ATR% (perfectly anti-correlated with `atr_pct`), **not** an independent contraction measure. Therefore J-30's full family **requires three NEW stored factor values** (HV, VCP-style contraction, downside/semivol). Per the *Research lab is read-only* anti-goal, the lab MUST NOT recompute factors — so the new values must be **computed once in the scoring/snapshot path (bars ≤ D, no lookahead) and stored on the immutable snapshot**, then read verbatim by the existing `compute_factor_lab`. This means a **DB regeneration** (existing snapshots predate the new values) and a **mandatory re-verify of the critical J-07 Risk-Off gate + J-06 score consistency** after regen — hence **full depth on the critical path** (exactly the fork the iter-12 recommendation flagged).

Good news that bounds the risk: the read-only analysis machinery already exists. `compute_factor_lab` (`research.py:266`) already produces the decile table + downside-risk-adjusted column + Spearman rank-IC + the **`by_regime`** split (J-27) for *any* catalog factor, and the frontend factor dropdown is **fully config-driven** (`research/page.tsx:134` maps `data.factors`; line 219 already renders `factor.family`). So once the new values are stored and the catalog entries added, all three measures render automatically with no new research-engine function and no required frontend registry edit.

**Lessons applied (from `lessons.md`):**
- **iter-11:** in this seed, per-regime/per-cohort `n` is nearly horizon-independent (1218@5d vs 1217@60d) — you CANNOT thin samples by lengthening the horizon to exercise an NA path. Design the honest-NA evidence around **genuinely empty/low-sample regimes** (e.g. Strong risk-on, Defensive at n=0) and the **downside-undefined** case (an all-non-negative decile → `risk_adjusted` NA), not horizon shrinkage.
- **iter-9:** the `/research` factor dropdown is config-driven (so config-only factors auto-appear) — UNLIKE the `/stocks` leaderboard pattern badges, whose registry is hardcoded. No leaderboard/badge edit is in scope here.
- **iter-3 / iter-10 (process):** full-depth iters in this session frequently finish with **no `-audit.md`** and a `status.json` written to the **phase-namespace** path `runs/goal-i_can_see_the_wealthy_future_forever-iter-13/status.json` (NOT under `runs/goal-session-.../iter-13/`). Don't block on those; verify the critical anti-goal seams in source. De-dup browser evidence by sha256 (distinct screenshots per claim).
- **iter-7/8:** J-30 is **compute-only over the existing committed seed — NO external fetch — so it is NOT data-walled** (unlike J-22/J-23/J-24, Yahoo-429). Do NOT autonomously retry J-22/J-23/J-24.

## IN SCOPE

### Backend

- [ ] **Indicator math (`app/engine/indicators.py`)** — add pure, DB-free, NA-graceful functions for the new volatility measures, each taking its window(s) as an argument (no literals — periods come from config):
  - [ ] **Historical volatility (level)** — standard deviation of daily simple returns over an `hv_window` (NA if fewer than `hv_window + 1` bars). Expressed as a percent so it is comparable to ATR%.
  - [ ] **Volatility contraction (change/contraction — the VCP-style measure)** — a continuous volatility-compression ratio = recent realized volatility / prior realized volatility over config windows (e.g. `vol_contraction_recent` vs `vol_contraction_prior` bars). A value **< 1 = volatility drying up = contracting** (the VCP thesis, expressed continuously). NA on insufficient history or a zero prior. *(The dev MAY instead derive a continuous contraction value from `patterns.detect_vcp`'s existing contraction internals if that ties more tightly to the VCP definition — either way it MUST be a continuous value, price/volume only, computed ≤ D, config-windowed.)*
  - [ ] **Downside / semi-volatility (downside/semivol)** — downside semideviation of trailing daily returns over a `semivol_window` about MAR=0 (`sqrt(mean(min(r,0)**2))`), negative-leg only (NEVER total volatility). NA on insufficient history. **Distinct from** `research.py:_downside_deviation`, which is the downside deviation of FORWARD returns used for the risk-adjusted column — this new factor is a *pre-snapshot stock characteristic* (bars ≤ D), not a forward-return statistic.
- [ ] **Scoring/snapshot path (`app/engine/scoring.py`)** — compute the three new volatility values per stock from the SAME as-of bars already read (`bars_asof(...) ≤ D` — no extra round-trip, no lookahead) and **store them on the immutable snapshot**. Choose ONE storage mechanism (both established in this codebase; both require the DB regen this iter already does):
  - **(Recommended) Typed columns on `ScannerResult`** — add `hv`, `vcp_contraction`, `downside_vol` as `Optional[float]` columns (the established append-only-column precedent — exactly how `is_vcp`/`is_pullback_to_rising_dma`/`is_flat_base_breakout` were added; a fresh DB from `create_all` carries them from the start, no Alembic). Extend `FACTOR_TYPED_COLUMNS` (config.py:97) so the catalog sources are bare column names. This bypasses the weighted-component cross-check cleanly and makes the family literally "first-class".
  - **(Alternative) A new non-scored block in `record_json`** — write `row["volatility"] = {"components": [{"name": "hv", "raw": …, "available": bool}, …]}` (rides losslessly into `record_json` via `scanner.py:105` — no schema change). Then extend `FACTOR_SOURCE_BLOCKS` (config.py:98) with `"volatility"` AND extend the boot validator `_factor_lab_sources_resolve` (config.py:947) with a parallel path that resolves a `volatility.components.<name>.raw` source against a config-declared allowlist of research-only volatility component names (so the boot stays loud on a typo — never a silent default), since these names are deliberately NOT in any `scores.<block>.weights`.
  - [ ] **HARD CONSTRAINT — the three new values MUST NOT enter any of the three weighted scores.** They are not added to `config.scores.{leadership,entry_quality,risk}.weights` and never participate in `_build_score`. Consequence (must hold and be tested): every stock's Leadership / Entry Quality / Risk score, A–E bucket, setup status, candidate counts, regime label, and the Risk-Off→Actionable gate are **byte-identical** before and after this change. *(Single source of truth + Risk-Off gating — critical.)*
- [ ] **Config (`config.yaml` + `app/config.py`)** — add, all read as arguments (No magic numbers):
  - [ ] the new windows under `indicators` (`IndicatorsCfg` already allows extra keys): e.g. `hv_window`, `semivol_window`, `vol_contraction_recent`, `vol_contraction_prior` (positive ints).
  - [ ] three new entries in `research.factor_lab.factors` with `family: volatility` and the appropriate `direction` and `source`:
    - `hv` — label "Historical volatility (HV)" — `direction: lower_better`
    - `vcp_contraction` — label "Volatility contraction (VCP-style)" — `direction: lower_better` (lower ratio = more contraction)
    - `downside_vol` — label "Downside volatility (semivol)" — `direction: lower_better`
  - [ ] keep `test_no_magic_numbers` green (it scans `indicators.py`, `scoring.py`, `research.py` per `tests/test_no_magic_numbers.py:19-36`): the new windows/labels live in config; the only literals in the new math are structural (indexing/`2`/`100`).
- [ ] **DB regeneration** — after the scoring change, regenerate the database so every immutable snapshot carries the new volatility values and the forward-return pool is intact: stop the backend (by port 8835 — see memory `dev-server-cleanup-by-port`), delete `apps/backend/data/trendora.db`, reboot so `db.create_all` + `scanner.bootstrap_runs` rebuild all snapshots + `forward_testing.backfill_run_forward_returns` repopulates returns. Run the **full** backend pytest ONCE after regen (memory `backend-test-suite-runtime`: ~14 min; do NOT run two pytest invocations concurrently).

### Frontend (Next.js `apps/frontend/app/research/page.tsx`)

- [ ] **No required change for core acceptance** — the new volatility factors appear in the existing config-driven factor dropdown automatically; selecting each renders its decile table (raw + downside-risk-adjusted) + rank-IC + by-regime split via the existing `FactorLab` component.
- [ ] **(Recommended, low-risk)** make the **volatility family explicit** so J-30 step 1 ("select the volatility family and view each measure") is obvious: group the factor dropdown `<option>`s by `family` (e.g. native `<optgroup>` keyed off the config-driven `factor.family`) — purely presentational, config-driven, no recompute, no new value. Do NOT hard-code a volatility factor list in the frontend (derive groups from `data.factors`).

### New user-facing capability

The user can open `/research`, pick each of the four volatility measures (ATR%, HV, VCP-style contraction, downside/semivol) at any horizon, and read whether — and in which direction — that volatility measure sorted realized forward returns in this universe, on a downside-risk-adjusted basis, both overall and split by market regime, with honest `n`/NA.

### New information displayed

The decile table + rank-IC + by-regime effectiveness for three NEW factors (HV, VCP-style contraction, downside/semivol), rendered by the existing Factor-Lab surface. (Raw mean + downside-risk-adjusted + `n` per decile; rank-IC `{value, n}`; per-regime rank-IC / top-bottom decile spread raw + risk-adjusted / `n`.)

### New user actions

Select the new volatility measures from the factor dropdown (and, if the optional grouping ships, see them grouped under a "Volatility" family heading). No new date control, no new mutation.

### UI surface changes

`/research` Factor Lab only (additive catalog members on the existing page; optional dropdown grouping). No new page, route, endpoint, or nav entry.

### Product surface delta

Volatility graduates from a single ATR% factor to a labelled family of four measures spanning level / contraction / downside — the analytical heart of J-30 (and the groundwork the J-31 synthesis will travel through).

### Blueprint conformance

No nav-skeleton change. The volatility family lives on the **existing, approved `/research` Factor Lab home** as additive catalog members. **No `blueprint.reapproval-requested` marker is written.** (`blueprint.md` updated this iteration: an additive Data-Contract row for the new stored volatility factor values + an iter-13 nav note.)

### Data-contract additions

- **NEW canonical value — per-stock volatility factor values (`hv`, `vcp_contraction`, `downside_vol`).** Computed **once** by the scoring engine (`app.engine.scoring:score_stocks`, from bars ≤ D — no lookahead), stored on the immutable snapshot (typed `ScannerResult` columns OR a non-scored `record_json["volatility"]` block), served on the canonical `GET /api/stocks` + `GET /api/stocks/{ticker}` rows like any other stored component, and **READ verbatim** (never recomputed) by `app.engine.research:compute_factor_lab` via the existing `_extract_factor_value`. This is the SAME computed-once-stored-then-read pattern `atr_pct`/`rs_spy_3m` already follow — **not** a second computation path and **not** a new endpoint for an existing value (it is a brand-new value with one computing module and one storage). Registered in `blueprint.md` this iteration.
- **NOT a new value:** the decile/rank-IC/by-regime analysis over these factors is the EXISTING J-25/J-27 Factor-Lab value (`compute_factor_lab` / `GET /api/research/factor-lab`) — the new factors are catalog members, not a new computation. Do NOT add a second endpoint or a second decile/IC computation.

## OUT OF SCOPE

- **J-29 (Setup & Pattern event study — MAE/MFE, expectancy, exit-horizon).** Deferred — it needs the post-snapshot daily high/low excursion path extracted first (the larger lift). J-30's contraction cross-check this iter is against the **existing** VCP-vs-non-VCP System Health breakdown (same stored `forward_returns` pool), NOT a new event study. The deeper MAE/MFE event-study cross-check lands with J-29.
- **J-31 (synthesis), J-22/J-23/J-24 (externally Yahoo-429 data-walled — do NOT autonomously retry).**
- Adding any volatility value to a weighted score, the stock-detail score breakdowns, or the leaderboard (no `/stocks` or `/stocks/[ticker]` UI change; the values are stored for lab consumption only).
- Any new date control or as-of state on `/research` (J-18 must stay resolved).
- `return/MAE` risk-adjustment (needs J-29's excursion path) — this iter's risk-adjusted column stays the existing downside-return-deviation ratio.

## DEFINITION OF DONE

- [ ] **J-30 passes via browser-qa-agent:** on `/research`, each of the four volatility measures (atr_pct, hv, vcp_contraction, downside_vol) renders a populated decile table (raw mean **and** downside-risk-adjusted column, each with `n`), a numeric rank-IC with `n`, and the by-regime split; low-sample deciles/regimes show NA + `n` (not a fabricated 0); the survivorship-bias + descriptive-not-predictive labels are visible; "risk" is downside-only.
- [ ] The contraction measure (`vcp_contraction`) is verified **consistent with the existing VCP forward-test evidence** — its decile/IC is read from the SAME stored `forward_returns` observations the System Health VCP-vs-non-VCP breakdown uses (no recomputation); the *direction* it reports is stated honestly (if contraction does NOT predict, that is a valid honest finding — the acceptance is descriptive, per J-30's "rather than assuming the textbook relationship").
- [ ] **CRITICAL re-verify after DB regen:** J-07 — open the seeded Risk-Off run and confirm **zero** stocks are "Actionable"; J-06 — NVDA's Leadership/Entry/Risk (number + bucket) are byte-identical on `/stocks` and `/stocks/NVDA`.
- [ ] Required-still-passing journeys remain green (J-02, J-05, J-08, J-09, J-12, J-16, J-18, J-19, J-25, J-27).
- [ ] No anti-goal violation introduced (verify the read-only seam in source: `research.py` still calls no `run_scan`/`score_stocks`/`forward_return`/`detect_*`/`score_regime`; the new values are computed in `scoring.py` ≤ D and read-only in the lab).
- [ ] Unit tests pass; full backend suite green after regen; frontend `npm run build` typechecks.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-13-dev.md`.

## TESTING REQUIREMENTS

- **Browser (browser-qa-agent):** J-30 on `/research` — select each volatility measure and capture its decile table (raw + downside-risk-adjusted + n), rank-IC, and by-regime split; capture at least one honest-NA cell (target an empty/low-sample **regime** or a downside-undefined decile — NOT horizon shrinkage, per the iter-11 lesson). Re-verify J-25/J-27 still render and re-point on factor change, and J-18 (toggle the global as-of → the Factor-Lab tables stay byte-identical with zero `as_of` requests). De-dup all screenshots by sha256 (one distinct shot per claim).
- **Critical post-regen browser/integration:** J-07 (Risk-Off run → Actionable=0) and J-06 (NVDA scores byte-identical across leaderboard↔detail) AFTER the DB regen.
- **Unit/integration (backend):**
  - the three new indicator functions — exact values on a known fixed series + NA on short history (HV/semivol/contraction periods come from config).
  - **score-invariance regression** — assert the three scores + buckets + setup status + candidate counts for a representative scored set are byte-identical with the volatility additions present (the new values never enter `_build_score` / any weight sum). This is the keystone protecting J-06/J-07.
  - config boot — the three new factor sources RESOLVE at boot (typed columns or the extended `volatility` block path) and an unresolvable/typo source raises `ConfigError` loudly; `test_no_magic_numbers` stays green.
  - `compute_factor_lab` returns populated deciles + rank-IC + `by_regime` for each new volatility factor on the seed; low-sample → NA + `n`; the risk-adjusted column is downside-only (None when the decile has no downside / n<2).
  - the read-only keystone (`test_research.py` patch-to-raise on `run_scan`/`score_stocks`/`detect_*`/`score_regime`) still passes — the lab recomputes nothing.
- **Error cases:** unknown factor key → endpoint 422 (existing behaviour, extended catalog); a factor-NULL observation is EXCLUDED (never bucketed/fabricated); short-history stock → NA volatility values that propagate to honest NA, never a fabricated 0.

## NOTES

- **Why full depth:** crosses backend (indicator math + scoring/snapshot + config + possible model column) and the read-only lab, touches the **critical scoring/snapshot path**, requires a **DB regen**, and requires re-verifying the **critical J-07 Risk-Off gate + J-06 score consistency** after regen — well beyond a lean browser-smoke change. Same justification J-25/J-26/J-27 carried, plus the regen risk.
- **The single biggest risk** is a volatility value leaking into a weighted score (which would shift every score and could break J-07/J-06). The HARD CONSTRAINT above + the score-invariance regression test are the guard. The reviewer/auditor should confirm in source that none of `hv`/`vcp_contraction`/`downside_vol` appears in any `config.scores.*.weights` and that `_build_score` is unchanged.
- **Process expectations (this session):** a full-depth iter here typically produces no `-audit.md`; `status.json` lands at `runs/goal-i_can_see_the_wealthy_future_forever-iter-13/status.json` (phase-namespace), not under `runs/goal-session-.../iter-13/`. Verify the critical seams in source; do not block on absent audit artifacts.
- **Strategic:** GOAL_ACHIEVED is NOT autonomously reachable while J-22/J-23/J-24 stay externally Yahoo-429 data-walled. After J-30, the remaining autonomous runway is **J-29 (event study; needs the post-snapshot MAE/MFE excursion path)** → **J-31 (synthesis; needs J-29 + J-27)**. Expect, once the labs are done, either operator confirmation of a reachable no-key egress (J-22 auto-heals via its committed runbook) or a correct STALLED on the data-walled remainder. **Do NOT autonomously retry J-22/J-23/J-24.**
