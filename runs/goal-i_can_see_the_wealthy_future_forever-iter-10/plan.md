# goal-i_can_see_the_wealthy_future_forever-iter-10 Execution Plan

**Goal (J-25):** Stand up the **Research** sidebar home (`/research`) with its first lab — the **Factor Lab** —
so a user picks a factor + a forward horizon and reads a **decile table (D1…D10)** of mean forward return
**plus a downside-risk-adjusted column** (each with `n`) and the factor's **rank-IC**, all derived **once,
read-only** from the already-stored per-observation forward returns ⋈ stored factor values. No factor and
no return is ever recomputed. Cross-date aggregate (like System Health) → **NO date control** (J-18 safe).

This is full depth (new page/route/nav home + new engine module + new endpoint + new typed config block).
Alignment with `docs/goal.md` is clean: capability #27 (Factor Lab), J-25, and anti-goals "Research lab is
read-only/not predictive", "Risk-adjusted must not conflate up/down vol", "No recompute in read path",
"No magic numbers", "Exactly one date selector". The blueprint already carries the J-25 nav + Data-Contract
rows (decomposer pre-populated them). **No scope drift.**

## What to Build

**Backend**
- New engine module `app/engine/research.py` — the read-only research-lab analytics engine. This iteration:
  - `factor_catalog(cfg) -> list[dict]` — ordered, config-driven catalog: one `{key, label, family, direction, source}` per `config.research.factor_lab.factors` row.
  - A read-only per-observation builder that, for a `horizon`, joins each stored `ForwardReturn.realized_return` to its stored `ScannerResult` (by `run_id` + `ticker`) and extracts the factor's stored value — **the SAME observation pool `forward_testing.compute_forward_aggregates(horizon)` builds.** Factor-NULL observations are EXCLUDED (never bucketed).
  - `compute_factor_lab(session, factor_key, horizon, cfg) -> dict` returning: resolved `factor` + `horizon` + full `factors` catalog + `horizons` + `default_horizon` + `min_sample` + `survivorship_bias` label + `n_total`; the **decile table** `deciles: [{decile, factor_min, factor_max, mean_return, risk_adjusted, n}]`; and `rank_ic: {value, n}`.
  - Pure helper `_downside_deviation(returns)` = `sqrt(mean(min(r,0)**2))` (MAR=0). **Do NOT reuse `forward_testing`'s total-`stdev`.**
- New API router `app/api/research.py` — `GET /api/research/factor-lab?factor=&horizon=`, registered in `main.py` with `prefix="/api"` (mirror `system_health.router`). Returns `compute_factor_lab(...)` verbatim.
- Config: new typed `research.factor_lab` block in `config.yaml` + `ResearchCfg`/`FactorLabCfg` in `app/config.py`, added as required `Config.research`, validated at boot.

**Frontend**
- New page `app/research/page.tsx` (Research home → Factor Lab), modeled on `app/system-health/page.tsx`.
- Sidebar: additive `NavItem { href: "/research", label: "Research", icon: Microscope }` in `components/sidebar.tsx` (place adjacent to System Health / Backtest; `FlaskConical` is taken by Backtest — use `Microscope` or `Beaker`).
- `lib/api.ts`: new types + a `getFactorLab(factor?, horizon?)` fetch helper.

## Agents Required
- **developer: yes** — backend (engine + API + config) and frontend (page + sidebar + api client) in one pass, TDD.
- backend-data: **yes** (new engine module, endpoint, typed config block, read-only join over stored rows)
- frontend-ux: **yes** (new `/research` page, factor/horizon selectors, decile table, rank-IC readout, sidebar entry)
- reviewer / qa / browser-qa-agent / coherence-auditor / ux-regression-reviewer / closure: per the full-depth goal pipeline.

## Frontend Present

Frontend Present: yes

## Files to Create/Modify
- `app/engine/research.py` — **create.** Read-only factor-lab engine (catalog + per-obs builder + `compute_factor_lab` + `_downside_deviation` + Spearman rank-IC). SELECTs against `ForwardReturn` + `ScannerResult` only.
- `app/api/research.py` — **create.** `GET /api/research/factor-lab`; 422 unknown factor / bad horizon; 503 no price data (mirror `system_health.py`).
- `apps/backend/main.py` — **modify.** Import `research` in the `app.api` import block; `app.include_router(research.router, prefix="/api")`.
- `apps/backend/app/config.py` — **modify.** Add `FactorLabFactor`, `FactorLabCfg`, `ResearchCfg` models + `research: ResearchCfg` (required) on `Config`; boot validators (see Design Notes).
- `config.yaml` — **modify.** Add the `research:` block (near `walk_forward`/`patterns`) with `factor_lab: {deciles: 10, factors: [...]}`.
- `apps/frontend/app/research/page.tsx` — **create.** Factor Lab page (selectors + decile table + rank-IC + labels; no date control).
- `apps/frontend/components/sidebar.tsx` — **modify.** Add the `/research` NavItem (+ icon import).
- `apps/frontend/lib/api.ts` — **modify.** `FactorLabResponse`/decile/`rank_ic` types + `getFactorLab()` helper.
- **Tests (extend existing files; no parallel suites):** `tests/test_research.py` (**create**: read-only keystone, decile math, rank-IC, downside-only, NA honesty, consistency invariant, config-driven); `tests/test_api_research.py` (**create**: 422/503/default/payload); and **modify** every synthetic-Config fixture to add the now-required `research` block — `tests/test_config.py` (`MINIMAL_VALID` + validation-failure cases), `tests/test_config_engine.py`, `tests/test_sectors.py`, `tests/test_themes.py`, and any other test that constructs a full Config dict; add the `deciles: 10` integer sentinel to `tests/test_no_magic_numbers.py`.

## UI Evolution
- **New user-facing capability:** open **Research → Factor Lab**, choose a catalogued factor + a forward horizon, and read forward-tested evidence of whether that factor sorts future returns (decile table + rank-IC, raw and downside-risk-adjusted).
- **New information displayed:** per-factor/per-horizon decile means (D1…D10) of realized forward return; a downside-risk-adjusted column beside each; the factor's rank-IC (value + sign + n); sample size `n` everywhere; survivorship-bias / universe-relative / descriptive-not-predictive labels.
- **New user actions:** select a factor (config-driven dropdown built from server `factors`); select a horizon (from server `horizons`).
- **UI surface changes:** new route `/research` (Factor Lab). The only edit to an existing page is the additive sidebar `NavItem`; no existing page's contract changes.
- **Navigation changes:** new sidebar entry **Research** (≤2 clicks to the lab). No `blueprint.reapproval-requested` marker (the `/research` nav was approved at the iter-10 pre-decomposer pause; this is an additive child page).

## Visual Requirements
- **Component patterns:** reuse the System Health page idiom — metric/section Cards, a dense numeric table for the decile grid, shadcn `Select` for the factor + horizon dropdowns. Numbers monospace/`tabular-nums`.
- **Layout:** sidebar + main content; a header (title + factor/horizon selectors + caveat labels), then the decile table, then the rank-IC readout.
- **Key visual effects:** return/IC colour grading from palette tokens only (`--pos` green / `--neg` red), monotonicity visible across D1→D10. Dark analytical workstation; no arbitrary hex/spacing/font sizes.
- **States:** loading (skeleton), empty/low-sample (explicit **"NA" + `n`** per decile cell — never blank, never a fabricated number), error (styled message). Responsive: table scrolls horizontally < ~640px.

## Design Notes (critical — prevents the known failure modes)

1. **The `source` resolver (the central detail).** `record_json` score blocks store `components` as a **LIST** of `{name, raw, …}` dicts, NOT a name-keyed map. So a factor `source` is one of two shapes:
   - a **typed column**: `leadership_score` / `entry_quality_score` / `risk_score` → read the `ScannerResult` column directly (these are never NULL).
   - a **component raw**: documented dotted path `<block>.components.<name>.raw` where `block ∈ {leadership, entry_quality, risk}` → parse the path, load `record_json`, find the component dict in `record_json[block]["components"]` with `name == <name>`, return its `raw` (None/NA when missing or `available: false`).
   - **Boot validation** (no DB needed): each `source` must be a known typed column OR match the dotted pattern with a valid `block` and a `<name>` present in `config.scores.<block>.weights`. Unresolvable/duplicate `key`/`source` → raise `ConfigError`. This is the No-magic-numbers keystone.
   - Suggested ≥5 factors (must include a volatility-family one for J-30): `leadership_score`, `entry_quality_score`, `risk_score` (typed) + `rs_spy_3m`, `ma_stack`, `high_proximity`, `up_down_vol` (→ `leadership.components.<name>.raw`), `atr_pct` (→ `risk.components.atr_pct.raw`). `direction ∈ {higher_better, lower_better}` and `family` are **descriptive metadata only** — they do NOT flip the decile sort. Read the stored `raw` verbatim (raws are already oriented by scoring; do not re-orient).
2. **Read-only discipline.** `compute_factor_lab` + helpers issue ONLY SELECTs against `ForwardReturn` + `ScannerResult`; they MUST NOT call `run_scan`/`score_stocks`/`backfill*`/`forward_return`/`detect_*` or any scoring/return/bucket math. Mirror the join in `forward_testing.compute_forward_aggregates` (lines ~526–560). No write, no second computation.
3. **Risk-adjusted = downside only.** `risk_adjusted = mean_return / _downside_deviation(returns)`; `None` (NA) when `downside_deviation == 0` or `n < 2`. Never total stdev (anti-goal: must not penalise healthy upside). Raw `mean_return` and `risk_adjusted` shown side by side.
4. **Deciles.** Rank observations by stored factor value, split into `config.research.factor_lab.deciles` (=10) equal-count quantiles; deterministic tie-break by `(ticker, run_id)`. Per decile: `mean_return`, `risk_adjusted`, `n`; flag `n < walk_forward.min_sample` low-sample (UI renders NA honestly). When `n_total < deciles`, emit honest NA rows — never fabricated buckets.
5. **Rank-IC.** Spearman = Pearson of the average-rank-transformed factor and return across all observations; `{value, n}`; `value` None when `n < 2` or either side has zero rank variance.
6. **Consistency invariant** (read-only cross-check, mirrors iter-2): for a **never-NULL typed-column factor** (e.g. `leadership_score`), the pooled mean of all factor-lab observations at horizon `h` == `compute_forward_aggregates(session, h).overall["mean_return"]` (same observation set). Assert this — it proves the lab is a read-only slice, not a second computation. (For factors with NULLs the pools differ legitimately; do NOT "fix" decile means to the pooled mean.)
7. **J-18 safety (principal risk of a new analytical page):** `/research` must add **no** as-of/date state — selectors are factor + horizon ONLY. Do not import `useAsOf` or any date control.
8. **`research` becomes a required `Config` field (iter-9 lesson).** Adding it WILL break every synthetic-Config test fixture that omits it (iter-9 hit exactly this with the pattern blocks: `test_config_engine.py`, `test_sectors.py`, `test_themes.py`, plus `test_config.py::MINIMAL_VALID`). Grep for Config-dict-building fixtures and add the `research` block to each — budget for it.
9. **Config-driven UI vocabulary (iter-9 lesson):** the factor dropdown options MUST come from the server payload's `factors` catalog — NOT a hardcoded frontend list — so a config-only factor needs no frontend edit.
10. **DB regeneration:** the factor lab reads existing stored `scanner_results.record_json` + `forward_returns` — **no new column, no snapshot mutation.** No DB regeneration is required (unlike iter-9). Confirm against the existing DB.

## Key Test Scenarios

**Backend (pytest — must pass; assert exact values):**
- **Read-only keystone (patch-to-raise):** monkeypatch `run_scan`/`score_stocks`/`forward_return`/`detect_vcp` (+ new detectors) to raise → `compute_factor_lab` still returns a full payload (proves SELECT-only).
- **Decile math:** synthetic stored dataset (known factor values + returns) → exact decile membership, `mean_return`, `n`; a monotone factor yields monotone decile means.
- **Rank-IC:** perfectly monotone → `1.0`; perfectly inverse → `-1.0`; known mixed set → its known value; `n<2` or zero rank-variance → `None`.
- **Downside-only:** symmetric up/down cohort → `risk_adjusted` from the downside leg only; an all-non-negative cohort → `downside_deviation==0` → `risk_adjusted is None` (NOT a huge total-vol number).
- **NA honesty:** factor-NULL observations excluded; `n<min_sample` decile reports `n` + low-sample flag; too-few-post-bars horizon → honest NA rows; all-NA factor → empty/NA table `n=0` (no fabricated rows).
- **Consistency invariant:** pooled lab mean at `h` == `compute_forward_aggregates(h).overall.mean_return` (typed-column factor).
- **Config-driven / no magic numbers:** adding a `factors` row → it appears in catalog + endpoint with no code change; `deciles` + catalog read from config; bad config (`deciles<=1`, duplicate key, unresolvable `source`) → `ConfigError` at boot.
- **Errors:** unknown `factor` → 422; `horizon` ∉ `walk_forward.horizons` → 422; no price data → 503.
- Full backend suite green (note: ~14 min; do not run two pytest invocations concurrently).

**Frontend / Browser (J-25 via browser-qa-agent; serialize Chrome access with qa, de-dup evidence by sha256, assert live DOM/network before each capture):**
- `npm run build` typechecks all routes.
- Sidebar shows **Research**; clicking loads `/research` (≤2 clicks).
- Factor Lab renders the decile table + rank-IC for the default factor/horizon; **factor dropdown options DOM-asserted to match the server `factors` catalog** (config-driven, not hardcoded).
- Changing factor and horizon re-points the decile table + rank-IC to server values (assert ≥1 value/label changes; no client recompute).
- A low-sample decile (e.g. horizon 60) shows **NA + n**; survivorship / universe-relative / descriptive-not-predictive labels present.
- **Regressions:** J-09 `/system-health` still renders its evidence; **J-18 — `/research` has NO date selector** (only factor + horizon); J-01 `/` + the full sidebar render with the new item.

## Process / Evidence Notes (verify-by-source)
- Full-depth iters here have repeatedly finished with **no `status.json` and no `auditor` handoff** (only `coherence.md` + snapshot-sha), and QA has sometimes falsely listed `status.json` present and shipped byte-identical duplicate screenshots. The dev handoff must state explicitly if no `status.json`/auditor handoff is produced. The evaluator must verify the read-only seam **directly in `app/engine/research.py` source** (only SELECTs; no scoring/return/factor call) and de-dup evidence by sha256.
- Dev handoff → `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-10-dev.md` (What Was Built / Files Changed / Tests Run with exact counts / Known Issues / Suggested Next Phase).
- `blueprint.md` J-25 rows are already present (decomposer); coherence-auditor must return COHERENCE-PASS.

## Out of Scope (exclude)
- J-26/J-27/J-29/J-30/J-31 (later `/research` labs); MAE/MFE-based ratios (need the excursion path — J-29); J-22/J-23/J-24 (externally Yahoo-429 data-walled — do NOT autonomously fetch/retry).
- Any change to scoring, regime, setups, patterns, snapshots, the as-of date control, the watchlist, or any existing endpoint's payload contract. No new stored column; no snapshot mutation.
