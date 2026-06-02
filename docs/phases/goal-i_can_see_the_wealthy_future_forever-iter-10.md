# Goal Iteration 10 — Factor Lab on `/research`: decile sort + rank-IC per factor (J-25)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 10
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-25
- **Required-still-passing journeys:** J-01, J-09, J-12, J-15, J-18, J-19
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Research lab is read-only, honest & not predictive.** Every Factor-Lab and event-study figure (decile means, rank-IC, combination cohorts, regime slices, distribution, hit-rate, expectancy, MAE/MFE, exit-horizon, risk-adjusted ratios) MUST be derived once from the stored per-observation forward returns + stored factor values + post-snapshot price path; the API and frontend MUST NOT recompute returns or factors to build them; low-sample cells show NA + n; results carry the survivorship-bias label. The lab is **descriptive evidence, not a fitted/ML predictive model**. *(extends No recompute in the read path + No machine-learning price prediction)*
  - **Risk-adjusted reporting is honest & must not conflate up/down volatility.** Every risk-adjusted figure (return/vol, return/MAE, Sharpe-like, expectancy) MUST be derived once from the stored per-observation forward returns + post-snapshot price path; "risk" MUST use downside volatility / MAE / drawdown — never total volatility, which would penalise healthy upside moves; raw and risk-adjusted MUST be shown side by side; low-sample cells show NA + n. *(extends Research lab is read-only)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Honest limitations surfaced.** Breadth and new-high/new-low metrics computed from the seed universe MUST be labelled "universe-relative"; walk-forward evidence MUST be labelled as carrying survivorship bias (current-membership universe) so results are never overstated.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. *(extends Single source of truth)*
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. *(critical)*

## GOAL

Stand up the **Research** sidebar home (`/research`) with its **first lab — the Factor Lab** — so a user can pick a factor (RS 3m, MA-stack, distance-from-52w-high, ATR%/volatility, Entry Quality, volume trend, the three scores, …) and a horizon and read a **decile table (D1…D10)** of mean forward return **alongside a risk-adjusted (downside) column**, each with sample size `n`, plus the factor's **rank information coefficient (rank-IC)** — all derived once, read-only, from the already-stored per-observation forward returns + stored factor values, with honest NA on low samples and a survivorship-bias label.

## BACKGROUND

J-28 closed the last fully-autonomous compute-only journey on existing homes (iter-9, CONTINUE). The only remaining autonomous track is the **compute-only `/research` labs (J-25–J-31)** over the already-stored seed — **not** the externally Yahoo-429-walled wave (J-22/J-23/J-24), which must NOT be autonomously retried (journey-history; iter-7/8 lessons). The `/research` top-level nav entry was added to the blueprint skeleton in iter-9 and its re-approval was **front-loaded** (`state/blueprint.reapproval-requested` written iter-9); `run-goal.sh` paused at iter-10's pre_decomposer for human approval, and that pause has now cleared (the marker is consumed/removed) — so `/research` is an **approved** home and this iteration builds the first lab under it. No new nav re-approval marker is needed (the skeleton entry is already approved; adding the page content is an additive edit).

J-25 is the entry point that establishes the new page/route/nav home **and** the **read-only lab-analytics seam** every later lab (J-26/J-27/J-29/J-30/J-31) reuses. It is purely descriptive: the Factor Lab READS the stored factor values (the typed `leadership_score`/`entry_quality_score`/`risk_score` columns + the named component `raw` values inside `ScannerResult.record_json`, e.g. `rs_spy_3m`, `ma_stack`, `high_proximity`, `atr_pct`, `up_down_vol`) and joins them to the stored realized returns (`forward_returns`), exactly the `stock_obs` join `forward_testing.compute_forward_aggregates` already builds — then groups them into deciles and computes a Spearman rank-IC. It recomputes **no** factor and **no** return. The Factor Lab is a **cross-date aggregate** (like System Health, which is also not as-of-scoped) — it has **no date control**, so J-18 ("exactly one date selector") is preserved by construction.

Full depth is warranted: a NEW page/route/nav home crossing backend (new engine module + new endpoint + new typed config block) and frontend (new page + selectors), requiring the full pipeline (coherence + ux-regression + closure). The iter-9 evaluator explicitly recommended **full** for this.

This is a verify-by-source session: full-depth iters here have repeatedly finished without a `status.json` or `auditor` handoff (and QA has falsely reported `status.json` present and shipped byte-identical duplicate screenshots) — see NOTES; the evaluator must verify the read-only seam in source and de-dup evidence by sha256.

## IN SCOPE

### Backend

- [ ] **New engine module `apps/backend/app/engine/research.py`** — the read-only research-lab analytics engine (Data Contract: `app.engine.research`). It computes lab figures by READING stored values verbatim and recomputing nothing. This iteration adds the Factor Lab functions; the module is designed to grow additively (event study J-29, etc.) like `forward_testing.py`/`patterns.py` did.
  - [ ] `factor_catalog(cfg) -> list[dict]` — the ordered, config-driven factor catalog: one entry per `config.research.factor_lab.factors` row, each `{key, label, family, direction, source}` (the `source` is metadata describing where the value is read from; not re-typed numbers).
  - [ ] A read-only per-observation builder that, for the requested `horizon`, joins each stored `ForwardReturn.realized_return` to its stored `ScannerResult` and extracts the requested factor's stored value — a typed score column (`leadership_score`/`entry_quality_score`/`risk_score`) OR a named component `raw` parsed from `record_json` at the config-declared `source` path (e.g. `leadership.components.<name>.raw`). Observations whose factor value is NULL/NA are EXCLUDED (never bucketed); observations with no realized return at the horizon contribute nothing (n=0). This is the SAME observation set `compute_forward_aggregates(horizon)` pools.
  - [ ] `compute_factor_lab(session, factor_key, horizon, cfg) -> dict` — returns: the resolved `factor` + `horizon` + the full `factors` catalog + `horizons` + `default_horizon` + `min_sample` + `survivorship_bias` label + `n_total`, the **decile table** `deciles: [{decile: 1..N, factor_min, factor_max, mean_return, risk_adjusted, n}]`, and the **`rank_ic: {value, n}`**.
    - **Deciles:** rank observations by the stored factor value and split into `config.research.factor_lab.deciles` (=10) equal-count quantiles (deterministic tie-break by ticker+run); each decile reports `mean_return` (mean of its stored realized returns), `risk_adjusted`, and `n`. A decile with `n < walk_forward.min_sample` shows its `n` but its means are flagged low-sample (the UI renders NA/low-sample honestly — never hidden, never fabricated). When `n_total < deciles`, emit honest NA rows, not fabricated buckets.
    - **Risk-adjusted = downside, never total volatility:** `risk_adjusted = mean_return / downside_deviation`, where `downside_deviation = sqrt(mean(min(r, 0)**2))` over the decile's stored returns (MAR = 0 — penalises only downside dispersion). `None` (NA) when `downside_deviation == 0` or `n < 2`. Add a small pure helper `_downside_deviation(returns)`; do **NOT** reuse `forward_testing`'s total-`stdev` distribution helper for this column (anti-goal: risk must not conflate up/down volatility). Raw `mean_return` and `risk_adjusted` are returned side by side.
    - **Rank-IC:** Spearman rank correlation between the stored factor value and the stored realized return across all observations (= Pearson correlation of their ranks; average-rank tie handling). `{value, n}`; `value` None when `n < 2` or a side has zero rank variance (honest NA, never a fabricated 0).
  - [ ] **Read-only discipline:** `compute_factor_lab` and its helpers MUST issue only SELECTs against `ForwardReturn` + `ScannerResult` (read stored values) and MUST NOT call `run_scan`, `score_stocks`, `backfill*`, `forward_return`, `detect_*`, or any scoring/return/bucket math. No write. No second computation of any score, return, bucket, or factor.
- [ ] **New API router `apps/backend/app/api/research.py`** — `GET /api/research/factor-lab` (registered in `apps/backend/main.py` with `prefix="/api"`, mirroring `system_health.router`).
  - [ ] Query params `factor` (default = first catalog factor) and `horizon` (default = `config.walk_forward.default_horizon`). Unknown `factor` → 422; `horizon` not in `config.walk_forward.horizons` → 422 (no fabricated factor/horizon); `503` when no price data exists at all (mirror `system_health.py`). Returns `compute_factor_lab(...)` verbatim — the view recomputes nothing.
- [ ] **Config: new typed block `research.factor_lab`** in `config.yaml` + a typed `ResearchCfg`/`FactorLabCfg` in `apps/backend/app/config.py` (validated, `extra="allow"`, added as `Config.research`).
  - [ ] `deciles: 10` (validated > 1).
  - [ ] `factors:` an ordered list (≥5) of `{key, label, family, direction, source}` rows spanning the typed score columns AND named components, including at least one volatility-family factor (`atr_pct`) so J-30 can extend it. Suggested seed: `leadership_score`, `entry_quality_score`, `risk_score` (typed columns) + `rs_spy_3m`, `ma_stack`, `high_proximity`, `up_down_vol`, `atr_pct` (component `raw`s). `direction ∈ {higher_better, lower_better}` documents the expected sign; `family` (e.g. `momentum`/`trend`/`volatility`/`score`) tags the factor for later grouping (J-30). The decile count + factor catalog living in config (not code) is the **No-magic-numbers** keystone; `min_sample` is reused from `walk_forward.min_sample` (no new threshold).
  - [ ] Validate at load: `deciles > 1`; every factor `key` unique; every factor `source` resolvable to a stored value (a typed `ScannerResult` column name, or a `record_json` dotted path of the documented shape) — an unresolvable/duplicate factor fails the boot loudly (`ConfigError`), never a silent default.

### Frontend

- [ ] **New page `apps/frontend/app/research/page.tsx`** — the Research home; this iteration renders the **Factor Lab** (model the layout on `apps/frontend/app/system-health/page.tsx`; dark analytical workstation, tabular-nums numbers, A–E/return colour grading from palette tokens).
  - [ ] A **factor selector** and a **horizon selector**, BOTH built from the server payload's `factors` / `horizons` (config-driven — NOT a hardcoded frontend factor list; per the iter-9 lesson the dropdown options must come from the server catalog so a config-only factor needs no frontend edit).
  - [ ] A **decile table** D1…D10: columns mean forward return (raw), risk-adjusted (downside), and `n` per decile; monotonicity visible via colour grading. Low-sample / NA cells render an explicit "NA" + the `n` (never blank, never a fabricated number).
  - [ ] A **rank-IC** readout: numeric value with sign + `n`.
  - [ ] The **survivorship-bias** label (verbatim from the payload) + a "universe-relative" / "descriptive, not predictive" caveat.
  - [ ] **No date control** on this page — it is a cross-date aggregate (like System Health). It MUST NOT import/add `useAsOf` date state or any second date selector (J-18). Loading + empty/low-sample + error states styled consistently.
- [ ] **Sidebar:** add a `{ href: "/research", label: "Research", icon: <lucide icon> }` `NavItem` to `apps/frontend/components/sidebar.tsx` (suggest `Microscope` or `Beaker`; `FlaskConical` is already used by Backtest). Place it adjacent to System Health / Backtest per the approved skeleton.

### New user-facing capability

A user can open **Research → Factor Lab**, choose any catalogued factor and a forward horizon, and read hard, forward-tested evidence of whether that factor sorts future returns: a D1→D10 decile table (raw mean return + a downside-risk-adjusted column, each with `n`) and the factor's rank-IC — so "does this signal actually rank future returns, and is the top decile good on a risk-adjusted basis?" is answerable from stored evidence, with honest NA where samples are thin.

### New information displayed

- Per-factor, per-horizon **decile means** (D1…D10) of realized forward return.
- A **risk-adjusted (downside-deviation)** column beside each decile mean.
- The factor's **rank information coefficient** (value + sign + n).
- Sample size `n` on every decile and the IC; the survivorship-bias / universe-relative / descriptive-not-predictive labels.

### New user actions

- Select a factor (config-driven dropdown).
- Select a forward horizon (from `walk_forward.horizons`).

### UI surface changes

- New sidebar entry **Research** and new route `/research` (Factor Lab). No change to any existing page's contract; the only edit to an existing file is the additive `NavItem` in `sidebar.tsx`.

### Product surface delta

The product gains its first **analysis lab** — moving from "here is the ranking + its aggregate forward-test evidence" to "interrogate which underlying factor drives forward return, by decile and rank-IC, raw and risk-adjusted." It deepens the skeptical, evidence-first posture without touching any scoring, snapshot, or date-control path.

### Blueprint conformance

`/research` is the **approved** top-level nav home added to the skeleton in iter-9 (re-approval front-loaded iter-9, pause cleared at iter-10). The Factor Lab page lives under it — an additive page under an already-approved nav section (no new nav-skeleton change, no new `blueprint.reapproval-requested` marker). `blueprint.md` is updated this iteration: the `/research` skeleton line is marked building/approved, the **J-25** journey-home row is added, and the **Factor-Lab analytics** Data-Contract row is registered (below).

### Data-contract additions

- **Factor-Lab analytics (per factor × horizon: decile mean return + downside risk-adjusted + rank-IC, each with `n`)** — the "Lab analytics" canonical value named in the goal's Product Shape.
  - **Computed once by:** `app.engine.research:compute_factor_lab` — a READ-ONLY aggregation derived ENTIRELY from the stored per-observation `forward_returns.realized_return` joined to the stored `ScannerResult` factor value (a typed score column or a `record_json` component `raw`, read verbatim). Recomputes no return and no factor; takes the same observation pool as `compute_forward_aggregates`.
  - **Served by:** `GET /api/research/factor-lab` (the single canonical endpoint; no other path computes deciles/rank-IC).
  - **Not a duplicate:** the factor *values* keep their existing canonical home (`scoring:score_stocks` → stored on `scanner_results`/`record_json`) and the realized *returns* keep theirs (`forward_testing` → `forward_returns`); this row registers only the NEW descriptive decile/IC aggregation over them, exactly as the J-19 attribution row registers new read-only slices of the same stored returns.

## OUT OF SCOPE

- **J-26** (multi-factor combination cohorts), **J-27** (regime-conditioned factor effectiveness), **J-29** (Setup & Pattern event study: expectancy/MAE/MFE/exit-horizon), **J-30** (full volatility family incl. downside/semivol factors + regime split), **J-31** (end-to-end synthesis) — later `/research` iterations that build on this iteration's page + read-only seam. This iteration ships the Factor Lab decile/rank-IC entry point only.
- **MAE/MFE-based** risk-adjusted ratios (return/MAE) — they need the post-snapshot daily high/low excursion path, which is not yet extracted; J-25's risk-adjusted column uses downside-deviation of the stored returns. Defer return/MAE to J-29.
- **J-22/J-23/J-24** (universe expansion, intraday/multi-timeframe) — externally Yahoo-429 data-walled; do NOT autonomously fetch/retry. Not part of the `/research` approval.
- Any change to scoring, regime, setups, patterns, snapshots, the as-of date control, the watchlist, or any existing endpoint's payload contract. The factor *values* are read as-stored; this iteration adds no new stored column and mutates no snapshot.

## DEFINITION OF DONE

- [ ] **J-25 passes via browser-qa-agent:** on `/research` (reached from the sidebar), selecting a factor + horizon renders a D1…D10 decile table with mean forward return, a risk-adjusted column, and `n` per decile, plus a numeric rank-IC with sign + n; low-sample deciles show NA + n; the survivorship-bias / universe-relative / descriptive labels are visible; changing factor or horizon re-points the table and IC (server values, no client recompute).
- [ ] **Required-still-passing journeys remain green:** J-01 (dashboard + the new sidebar still render), J-09 (System Health unchanged — shares the stored forward-return data, read-only), J-12 (methodology config catalog unaffected), J-15 (no new per-request recompute introduced), J-18 (`/research` exposes NO date control — only factor + horizon selectors), J-19 (attribution slices unchanged).
- [ ] **No anti-goal violation introduced** — verified in source: the read path issues only SELECTs and calls no scoring/return/factor computation (a patch-to-raise keystone test); risk-adjusted uses downside-deviation, not total stdev; decile count + factor catalog come from config; NA + n shown on low samples; no date state added; no order/secret path.
- [ ] **Unit/integration tests pass; no regressions** (full backend suite green; frontend `npm run build` typechecks).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-10-dev.md` (What Was Built / Files Changed / Tests Run with exact counts / Known Issues / Suggested Next Phase). If, as in prior full-depth iters here, no `status.json`/auditor handoff is produced, say so explicitly.
- [ ] `blueprint.md` updated (J-25 home + Factor-Lab Data-Contract row); coherence-auditor returns COHERENCE-PASS.

## TESTING REQUIREMENTS

- **Browser (J-25 + regressions):**
  - Sidebar shows **Research**; clicking it loads `/research` (feature is discoverable, ≤2 clicks).
  - Factor Lab renders the decile table + rank-IC for the default factor/horizon; the **factor dropdown options are DOM-asserted to match the server `factors` catalog** (config-driven, not hardcoded).
  - Changing the factor and the horizon re-points the decile table and the rank-IC to the server values (assert at least one value/label changes; no client-side recompute).
  - A low-sample decile (e.g. at horizon 60) shows **NA + n**, not a fabricated number; the survivorship/universe-relative/descriptive labels are present.
  - **Regression:** J-09 `/system-health` still renders its by-bucket/excess/control-group evidence; J-18 — assert `/research` has **no** date selector (only factor + horizon); J-01 `/` + the full sidebar render with the new item.
  - Serialize browser access (qa vs browser-qa-agent) on the shared Chrome and de-dup evidence by sha256 (iter-6 lesson); assert live DOM/network state before each capture.
- **Unit/integration (backend):**
  - **Read-only keystone (patch-to-raise):** monkeypatch `run_scan` / `score_stocks` / `forward_return` / `detect_vcp` (and the new pattern detectors) to raise, then assert `compute_factor_lab` still returns a full payload — proving it reads stored values only (mirror the existing snapshot-serving keystone test).
  - **Decile math:** on a small synthetic stored dataset (known factor values + returns) assert exact decile membership, `mean_return`, and `n`; assert a monotone factor yields monotone decile means.
  - **Rank-IC:** assert exact Spearman on known pairs — perfectly monotone → `value == 1.0`; perfectly inverse → `-1.0`; a known mixed set → its known value; `n < 2` or zero rank-variance → `value is None`.
  - **Risk-adjusted is downside-only:** a cohort whose returns are symmetric up/down has `risk_adjusted` computed from the downside leg only; a cohort with **no** negative returns → `downside_deviation == 0` → `risk_adjusted is None` (NOT a huge/total-vol number).
  - **NA honesty:** factor-NULL observations are excluded; a decile with `n < min_sample` reports its `n` and low-sample flag; a horizon with too few post-bars yields honest NA rows; an all-NA factor yields an empty/NA table with `n=0` — never fabricated rows.
  - **Consistency invariant:** the pooled mean of all factor-lab observations at horizon `h` equals `compute_forward_aggregates(session, h).overall["mean_return"]` (same stored observation set; mirrors the iter-2 distribution-mean invariant) — proving the lab is a read-only slice, not a second computation.
  - **Config-driven / no magic numbers:** adding a factor row to `config.research.factor_lab.factors` makes it appear in the catalog + endpoint with no code change; `deciles` and the catalog are read from config; a bad config (`deciles <= 1`, duplicate factor key, or an unresolvable factor `source`) raises `ConfigError` at boot.
- **Error cases:** unknown `factor` → 422; `horizon` not in `walk_forward.horizons` → 422; no price data → 503; all-NA factor → honest empty/NA table (n=0), no fabricated decile.

## NOTES

- **Approval state:** the `/research` nav re-approval was front-loaded in iter-9 and the iter-10 pre_decomposer pause has cleared (the `state/blueprint.reapproval-requested` marker is consumed). This iteration therefore BUILDS under the approved `/research` home and writes **no** new re-approval marker (the page is an additive child of an approved nav section).
- **Verify-by-source (process lesson, iters 2/3/6/8/9):** full-depth iters in this session have repeatedly produced **no `status.json` and no `auditor` handoff** (only `coherence.md` + `snapshot-sha`), while QA reports have sometimes falsely listed `status.json` as present and shipped **byte-identical duplicate screenshots**. The evaluator must verify the read-only seam directly in `app/engine/research.py` source (only SELECTs; no scoring/return/factor call) and de-dup evidence by sha256 — do not block on or trust those artifacts.
- **Concurrent-browser corruption (iter-6 lesson):** if both the `qa` agent and the `browser-qa-agent` do Chrome-MCP checks, serialize access (one vacates before the other captures) and assert live state (testid/URL/values) immediately before each capture; ground any before/after factor-or-horizon-change claim on distinct shots + a DOM/network assertion, never one screenshot pair.
- **Config-driven UI vocabulary (iter-9 lesson):** build the factor dropdown from the server `factors` catalog so a config-only factor needs no frontend edit — do not repeat the iter-9 seam where the leaderboard pattern badge/filter list was hardcoded in the frontend.
- **Consistency seam (iter-2 lesson):** the Factor Lab's per-horizon observation pool is the SAME set `compute_forward_aggregates(h)` uses; the pooled-mean == `overall.mean_return` invariant is the read-only cross-check (assert it). Do NOT "fix" a per-decile mean to match the overall mean — deciles legitimately differ from the pooled mean.
- **J-18 safety:** the Factor Lab is a cross-date aggregate; it must add no as-of/date state. This is the principal anti-goal risk of introducing a new analytical page — keep selectors to factor + horizon only.
- Reference model for the new page: `apps/frontend/app/system-health/page.tsx`; reference for the read-only seam + per-observation join: `forward_testing.compute_forward_aggregates` / `_attribution_slices`; reference for the typed config block + validation: `WalkForwardCfg` / `AttributionCfg` / `PatternsCfg` in `app/config.py`.
