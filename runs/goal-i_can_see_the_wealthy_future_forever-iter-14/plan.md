# goal-i_can_see_the_wealthy_future_forever-iter-14 Execution Plan

**Target journey:** J-29 — Setup & Pattern Lab (event study) on `/research`.
**Goal alignment:** J-29 is goal capability #29; `/research` is its approved IA home (since iter-10). No drift, no scope creep. The blueprint is ALREADY updated for iter-14 (nav note + `/research` skeleton annotation + J-29 home row + the two Data-Contract rows are present) — the dev does NOT re-author it; the coherence-auditor verifies the diff against it.

## What to Build

Three backend pieces + one frontend section + a DB regen, all additive and forward-side only.

- **A. Store the MAE/MFE excursion path (NEW immutable, lookahead-free value).**
  - Add two `Optional[float]` append-only columns `mae` / `mfe` to `ForwardReturn` (default `None`; backward-compatible), documented in the docstring exactly like the existing audit columns.
  - Add a pure helper `forward_excursions(bars_after_list, entry_close, horizon) -> Optional[dict]` in `forward_testing.py`: `mae = min(low_i)/entry_close − 1`, `mfe = max(high_i)/entry_close − 1` over the FIRST `horizon` post-bars (date > D), reading each bar's `.low`/`.high`. It MUST share the EXACT NA gate as `forward_return()` (None when `entry_close` missing/zero OR `< horizon` post-bars) and be unchanged when bars after the h-th are removed (no-lookahead).
  - Extend the SINGLE INSERT path `_insert_run_forward_returns` to populate `mae`/`mfe` on the `ForwardReturn` it INSERTs, reusing the `post_bars`/`entry_close`/`horizon` already in hand (no extra query). INSERT-only + idempotent (existing skip-set unchanged; warm re-run inserts 0 rows, UPDATEs nothing). This is the ONE place excursions are computed, shared by the boot backfill AND `backfill_run_forward_returns`.
  - **DB regen** (delete `apps/backend/data/trendora.db`, reboot to regenerate from the committed seed) so existing rows carry `mae`/`mfe`. No UPDATE/backfill-in-place path.
- **B. The read-only event-study analytic `compute_event_study(session, subject_key, horizon, config=None)`** in `research.py` — SELECT-only over `ForwardReturn` (`realized_return`+`mae`+`mfe`) ⋈ `ScannerResult` (`setup_status` + stored mirror flags `is_vcp`/`is_pullback_to_rising_dma`/`is_flat_base_breakout`, verbatim) ⋈ `ScannerRun.regime_label` (verbatim). Calls NO scoring/regime/return/excursion/pattern math. Per subject × horizon: distribution (mean/median/%positive/dispersion/n/low_sample — reuse `_distribution` shape), expectancy (win_rate/avg_win/avg_loss/expectancy = mean), mean MAE/MFE, downside risk-adjusted (`return_per_downside_dev` reuse `_risk_adjusted`; `return_per_mae` = mean/mean(|mae|), None when mean|mae|==0 or n<2). Plus best-exit-horizon curve (argmax of `return_per_downside_dev`, fallback `mean_return`, over non-low-sample horizons), by-regime slice (every `config.regime.labels` label emitted; Σ per-regime n == selected-horizon pooled n), by-sector slice (config sector-name order, non-padded). Payload carries `subject{key,label,kind}`, `horizon`, `subjects` catalog, `horizons`, `default_horizon`, `min_sample`, `survivorship_bias` (reuse `SURVIVORSHIP_BIAS_LABEL`), `descriptive_caveat` (reuse `RESEARCH_CAVEAT`). Unknown subject → `ValueError`.
- **C. The serving endpoint `GET /api/research/event-study`** in `api/research.py` — params `subject` (default = first catalog subject) + `horizon` (default = `walk_forward.default_horizon`); returns `compute_event_study(...)` verbatim. 422 on unknown subject / unknown horizon, 503 when `latest_data_date is None` — mirror the existing `factor-lab`/`factor-combination` handlers exactly. **NO `as_of`/date param (J-18).**
- **Frontend.** Add an `EventStudyLab` section to `apps/frontend/app/research/page.tsx` BELOW `<CombinationLab>` (sibling component modeled on `CombinationLab`, taking the shared `horizon` prop), fed by a new `fetchEventStudy(subject, horizon, signal)` + `EventStudyResponse` in `apps/frontend/lib/api.ts`, with its own loading/empty/error states.

### Config decision (document, don't ask)
**PREFER NO new required config key.** Derive the subject catalog from the existing config-backed vocabulary: setups from `setups.ALL_STATUSES` + their `methodology:build_catalog(config)` labels; patterns from `config.patterns` keys (`vcp`, `pullback_to_rising_dma`, `flat_base_breakout`) + their catalog labels. Reuse `walk_forward.min_sample`/`horizons`/`default_horizon`. Only if an OPTIONAL allowlist/primary-metric is genuinely needed, add a typed `EventStudyCfg` on the existing `ResearchCfg` — and **if any field is required, add it to ALL FOUR inline test config dicts** (`MINIMAL_VALID`, `VALID`, `test_sectors`, `test_themes`) per MEMORY `config-fixtures-need-new-required-keys`.

## Agents Required
- developer: yes — backend (model column + excursion helper + INSERT extension + read-only analytic + endpoint + DB regen) and frontend (EventStudyLab section + api helper/type). Single full-pipeline pass.

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/models.py` — add `mae` / `mfe` `Optional[float]` columns to `ForwardReturn` (+ append-only docstring note).
- `apps/backend/app/engine/forward_testing.py` — add pure `forward_excursions(...)` helper; populate `mae`/`mfe` in `_insert_run_forward_returns` (shared by both backfill paths).
- `apps/backend/app/engine/research.py` — add `compute_event_study(...)` + a config-driven subject-catalog helper; reuse `_risk_adjusted`/`_downside_deviation`/`_distribution`/labels (no new risk formula).
- `apps/backend/app/api/research.py` — add `GET /research/event-study` (mirror factor-lab/factor-combination validation: 422/503).
- `config.yaml` / `apps/backend/app/config.py` — only if an OPTIONAL `EventStudyCfg` is added (prefer none; if required-field, update all four fixtures).
- `apps/frontend/lib/api.ts` — `fetchEventStudy(...)` + `EventStudyResponse` (+ supporting row types).
- `apps/frontend/app/research/page.tsx` — `EventStudyLab` component rendered below `CombinationLab`.
- `apps/backend/tests/test_forward_testing.py`, `test_research.py`, `test_api_research.py`, `test_no_magic_numbers.py` — see Key Test Scenarios.
- **DB regen:** delete `apps/backend/data/trendora.db`, reboot to regenerate from the committed seed; run the FULL backend suite ONCE after any fixture updates land.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-14-dev.md` — dev handoff.
- (Out of scope to author: `blueprint.md` — already updated by the decomposer.)

## UI Evolution
- **New user-facing capability:** on `/research`, pick any setup (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist) or pattern (VCP, Pullback-to-DMA, Flat-base) and read its pooled cross-snapshot event study — distribution + expectancy + MAE/MFE + downside-risk-adjusted ratios per horizon, best exit-horizon, and by-regime/by-sector behavior, all from stored lookahead-free survivorship-labelled evidence.
- **New information displayed:** per-(run,symbol,horizon) MAE/MFE excursions (newly stored, surfaced only through the event study); the per-subject distribution / expectancy / MAE-MFE / risk-adjusted ratios / best-exit-horizon / by-regime / by-sector analytics.
- **New user actions:** a subject selector (Setups vs Patterns, grouped by `kind`) on the new section; reuses the existing shared horizon selector. **No new date control.**
- **UI surface changes:** `/research` gains a third lab section (Setup & Pattern Lab) below Factor Lab + Combination Lab. No new page, route, or nav entry.
- **Navigation changes:** none.

## Visual Requirements
- **Component patterns:** mirror `CombinationLab` — panel `PanelTitle` + tabular tables; subject `<select>` grouped by `kind` via `<optgroup>` (the same config-driven, payload-derived pattern as the factor `<optgroup>`); reuse the shared `HorizonSelector` and `CaveatBanner`. No hard-coded subject list in the component.
- **Layout:** additive vertical section under the existing labs on the single `/research` page (dense dark workstation); a per-horizon distribution/exit-horizon table (one row per horizon: mean / median / %positive / dispersion / expectancy / mean-MAE / mean-MFE / return-per-downside-dev / return-per-MAE / n) with the best-exit-horizon row highlighted; a by-regime panel and a by-sector panel for the selected horizon.
- **Key visual effects:** palette tokens only (`--pos`/`--neg`/`--warn`); `tabular-nums` monospace for all numbers; raw shown beside risk-adjusted; low-sample cells muted as NA + n chips (like the Factor Lab regime table).
- **States to handle:** loading skeleton (reuse the existing `LabSkeleton` pattern), empty/low-sample (NA + n, never a fabricated 0), and an explicit "Backend unavailable" error on non-200 (503/422) — never fabricated evidence.

## Key Test Scenarios
- **Browser (J-29):** on `/research`, a SETUP subject renders per-horizon distribution + expectancy + MAE/MFE + both downside-risk-adjusted columns + n; a PATTERN subject (VCP) renders the same AND the by-regime + by-sector panels with ≥1 honest NA + n cell; best-exit-horizon/per-horizon curve renders; survivorship caveat visible; changing subject re-points (distinct values, distinct sha256).
- **Browser J-18 re-verify:** toggle the global as-of latest→historical and assert the event-study tables are byte-identical with **zero `as_of`-param requests** — ground on DISTINCT shots + a DOM/network assertion (iter-6 lesson; serialize Chrome access between `qa` and `browser-qa-agent`, de-dup evidence by sha256).
- **Browser J-07 / J-06 re-verify after regen:** both seeded Risk-Off runs Actionable=0; NVDA list↔detail byte-identical.
- **Unit — `test_forward_testing.py`:** MAE/MFE no-lookahead (computed from only `post_bars[:horizon]`, unchanged when later bars removed); NA gate (`< horizon` post-bars → None → no row, like `realized_return`); immutability/idempotency (2nd backfill inserts 0 rows, UPDATEs no snapshot row; `mae`/`mfe` populated on fresh INSERT); MFE ≥ realized-at-h ≥ MAE band relationship where assertable.
- **Unit — `test_research.py`:** extend the patch-to-raise keystone (add `forward_excursions` to the raise set alongside `run_scan`/`score_stocks`/`forward_return`/`detect_*`/`score_regime`) → `compute_event_study` still returns; **consistency invariant** — event-study pooled `mean_return` for a setup == `compute_forward_aggregates(h).by_setup[setup].mean_return`, and for VCP == the `by_vcp` flagged-cohort mean (SAME observations — iter-2 lesson: bind to `compute_forward_aggregates`, NOT the per-date scorecard's top cohort); downside-only risk-adjusted (return/downside-dev AND return/MAE both NA when no downside / mean|MAE|==0 / n<2 — never total vol); honest NA (empty regime/sector → NA + n=0; low-count subject → low_sample); unknown subject → ValueError; Σ per-regime n == selected-horizon pooled n.
- **Unit — `test_api_research.py`:** `GET /api/research/event-study` default subject/horizon; 422 unknown subject; 422 unknown horizon; 503 no data; payload shape (subjects catalog, per-horizon rows, by-regime/by-sector, caveats).
- **Unit — `test_no_magic_numbers.py`:** extend the `research.py`/`forward_testing.py` scan so the additions introduce no literal threshold (subjects/min_sample/horizons from config or the fixed `ALL_STATUSES`/`config.patterns` vocabulary; the `> 0` win/loss boundary and rank/index 1's are structural).
- **Suite gates:** full backend pytest green AFTER the DB regen + fixture updates (run ONCE, ~14–20 min — do not run two pytest invocations concurrently); frontend `npm run build` typechecks.

## Notes / Guardrails (for dev + reviewer)
- **Read-only is the keystone:** MAE/MFE are computed on the forward-side INSERT and STORED; the lab reads them verbatim and queries NO price bars and recomputes NO excursion/return. The patch-to-raise test is the proof — the reviewer must NOT "fix" the read-only seam.
- **Consistency-invariant scope (iter-2):** the same-observation equality is to `compute_forward_aggregates` (`by_setup`/`by_vcp`/`by_pattern`), NOT the per-date scorecard's top-ranked cohort — do not flag it as a mismatch.
- **NA fixtures (iter-11):** n is ~horizon-independent in this seed (≈1217–1218) — design honest-NA evidence around genuinely empty regimes/sectors or a low-count pattern subject, and risk-adjusted-NA around an all-non-negative (downside-undefined) cohort; never rely on horizon-driven shrinkage.
- **Lower regen risk than iter-13:** `score_stocks`/`scoring.py`/`scanner.py`/`patterns.py`/`regime.py`/`buckets.py` are UNTOUCHED (forward-side only) → snapshots regenerate byte-identical, so J-06/J-07 are expected trivially green; re-verify live anyway (critical + regen).
- **Out of scope (exclude):** J-31 synthesis; J-22/J-23/J-24 (Yahoo-429 data-walled — do NOT autonomously retry); any change to the six scores/buckets/setup vocab/Risk-Off gate/nav/date control; any UPDATE/backfill-in-place of existing `forward_returns` rows; options/intraday/ML/news.
