# goal-i_can_see_the_wealthy_future_forever-iter-11 Execution Plan

**Goal (J-27):** On the Factor Lab (`/research`), show a chosen factor's effectiveness **split by market
regime** — per configured regime label: `n`, rank-IC, top-decile mean, bottom-decile mean, the raw
top-minus-bottom-decile spread, and the **downside-risk-adjusted** spread — so a factor that "works"
pooled can be seen to be regime-dependent, with honest **NA + n** for regimes that lack samples.

This is the **smallest additive extension of J-25** (iter-10): one engine function extended, one read-only
helper added, one UI panel, one type, extended tests. **No new endpoint, no new query param, no nav change,
no new config key, no DB regeneration, no schema change, no snapshot mutation.** Dispatched at **full**
depth per the iter-10 evaluator recommendation (new backend aggregation needs real unit tests + a
coherence/ux/closure pass on a critical anti-goal surface — the read-only research lab).

**Goal alignment (verified — no drift):** `docs/goal.md` J-27 (line 641) defines exactly this; the
blueprint already pre-registers "J-27 regime split [iter-11]" under the approved `/research` home (line 67)
and the read-only lab-analytics contract (item #9, line 179). The `by_regime` slice is an additive
read-only extension of the already-registered Factor-Lab value — **same module `compute_factor_lab`, same
endpoint `GET /api/research/factor-lab`, same observation pool, same stored `scanner_runs.regime_label`
read verbatim.** No new canonical value. No `blueprint.reapproval-requested` marker.

## What to Build

**Backend (`apps/backend/app/engine/research.py` only — SELECT-only throughout)**
- **Extend `_factor_observations`** to attach the stored regime label per observation. Add `ScannerRun` to
  the `app.models` import; mirror `forward_testing.py:534-538`: read `run_rows = select(ScannerRun).where(
  ScannerRun.id.in_(runs_with_fr))`, build `regime_by_run = {run.id: run.regime_label for run in run_rows}`,
  and add `"regime": regime_by_run.get(res.run_id)` to each observation dict. **Read the stored label
  verbatim — recompute no regime/score/return.**
- **Add `_regime_effectiveness(observations, cfg, horizon)`** (new read-only helper). For each label `L` in
  `cfg.regime.labels` **in config order** (no hard-coded regime list), filter observations to that regime
  and emit one row: `regime`, `n`, `low_sample` (= `n < cfg.walk_forward.min_sample`),
  `rank_ic` (`_rank_ic` over the regime's `(factor, return)` pairs), `top_decile_mean`/`bottom_decile_mean`
  (`deciles[-1].mean_return` / `deciles[0].mean_return` from a **per-regime** `_deciles(...)` split),
  `spread` (= top − bottom), `risk_adjusted_spread` (= `deciles[-1].risk_adjusted − deciles[0].risk_adjusted`).
- **Add `"by_regime": _regime_effectiveness(observations, cfg, horizon)`** to the `compute_factor_lab`
  return dict — SAME observation pool, no second computation. Existing keys unchanged.
- **API unchanged:** `apps/backend/app/api/research.py` is **not** touched. `by_regime` rides the existing
  `GET /api/research/factor-lab` payload, served verbatim.

**Frontend**
- `apps/frontend/lib/api.ts`: add `RegimeEffectivenessRow` interface + `by_regime: RegimeEffectivenessRow[]`
  on `FactorLabResponse`.
- `apps/frontend/app/research/page.tsx`: add a `RegimeEffectivenessTable` panel **below** the existing
  decile-table + rank-IC grid (inside `FactorLab`, after the `lg:grid-cols-3` block). Server-driven rows
  from `data.by_regime` — **never a hard-coded frontend regime array.**

## Agents Required
- **developer: yes** — backend (engine extension + helper) and frontend (type + panel) in one pass, TDD.
- backend-data: **yes** (extend `_factor_observations`, add `_regime_effectiveness`, extend `test_research.py`)
- frontend-ux: **yes** (the `RegimeEffectivenessTable` panel + the `RegimeEffectivenessRow` type)
- reviewer / qa / browser-qa-agent / coherence-auditor / ux-regression-reviewer / closure: per the full-depth goal pipeline.

## Frontend Present

Frontend Present: yes

## Files to Create/Modify
- `apps/backend/app/engine/research.py` — **modify.** Import `ScannerRun`; attach `regime` per observation in `_factor_observations`; add `_regime_effectiveness(...)`; add the `by_regime` key to `compute_factor_lab`.
- `apps/backend/tests/test_research.py` — **modify.** Add the J-27 scenarios (see Key Test Scenarios); extend the existing patch-to-raise keystone to also patch `app.engine.regime.score_regime`.
- `apps/frontend/lib/api.ts` — **modify.** Add `RegimeEffectivenessRow` + `by_regime` on `FactorLabResponse`.
- `apps/frontend/app/research/page.tsx` — **modify.** Add the `RegimeEffectivenessTable` panel.
- **Do NOT touch:** `app/api/research.py`, `config.yaml`, `app/config.py`, `forward_testing.py`, `scoring.py`, `scanner.py`, `patterns.py`, `regime.py`, the sidebar, any other page, or any other test fixture (no new required Config field this iter — unlike iter-10).

## UI Evolution
- **New user-facing capability:** pick a factor + horizon on the Factor Lab and read, per market regime, whether the factor's ranking actually sorts forward returns in that regime (rank-IC + raw and downside-risk-adjusted long-short decile spread) — so a pooled "good" factor can be seen to be regime-dependent.
- **New information displayed:** a "Factor effectiveness by market regime" table — one row per configured regime label (the six: Strong risk-on, Risk-on, Narrow leadership, Choppy, Defensive, Risk-off), each with per-regime `n`, rank-IC, top-decile mean, bottom-decile mean, raw top−bottom spread, downside-risk-adjusted spread. Low-sample / insufficient regimes render **NA + n**.
- **New user actions:** none beyond the existing factor + horizon selectors (the new panel re-points with them). **No new control, no date control.**
- **UI surface changes:** one additive panel on the existing `/research` page. No new page, no new route.
- **Navigation changes:** **none.** Lives under the approved `/research` home. No `blueprint.reapproval-requested` marker.

## Visual Requirements
- **Component patterns:** reuse the existing page idiom — wrap the panel in `Card` + `PanelTitle`; a dense numeric `<table>` matching `DecileTable`. Numbers monospace (`num`/`tabular-nums`). Reuse the page's `SampleSize` chip and the `DecileValue`-style NA treatment.
- **Layout:** full-width panel stacked below the decile-table + rank-IC grid (`space-y-4` already wraps the page).
- **Key visual effects:** `returnClass` colour grading from palette tokens only (`--pos`/`--neg`) on the mean/spread/IC cells. No arbitrary hex/spacing/font sizes.
- **States:** the panel renders only when `data` is present (inside `FactorLab`, so the `n_total === 0` empty-state and the loading skeleton/error card already gate it). Per-cell NA: low-sample or null → **"NA" + the `SampleSize` chip**, never blank, never a fabricated number. Responsive: the table scrolls horizontally < ~640px (`overflow-x-auto`).

## Design Notes (critical — prevents the known failure modes)

1. **Sort each regime's observations ascending by factor before `_deciles` (THE likely correctness bug).**
   `_deciles` assumes the input is factor-ascending (`compute_factor_lab` pre-sorts the pooled pool into
   `ordered`). Inside `_regime_effectiveness`, after filtering to a regime you MUST
   `sorted(regime_obs, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))` (mirror the existing
   tie-break) before calling `_deciles(...)` — otherwise top/bottom deciles are scrambled and the spread is wrong.
2. **`spread` / `risk_adjusted_spread` are None (NA) when `low_sample` OR either leg is None.** Compute them
   only when `not low_sample and top is not None and bottom is not None`. The risk-adjusted legs come from
   `_deciles`' existing `risk_adjusted`, which is already None when a decile has **no downside**
   (`_downside_deviation == 0`) or `n < 2` — so an all-non-negative top decile naturally yields
   `risk_adjusted_spread = None` (honest NA), **never a total-volatility number.** Do not invent a fallback.
3. **Regime-row `low_sample` is on the regime's TOTAL `n`** (`n < walk_forward.min_sample`), distinct from
   the per-decile `low_sample` inside `_deciles`. The row's NA gate uses the regime-total flag.
4. **Config-driven, no magic numbers, no new config key.** Regime labels from `cfg.regime.labels`; threshold
   from `cfg.walk_forward.min_sample`; decile count from `cfg.research.factor_lab.deciles`. Add **no** new
   config key and **no** numeric literal in `research.py` (`test_no_magic_numbers.py` already scans this file).
5. **Every configured regime emits a row — even `n=0`** (honest empty row, not omitted, not fabricated).
   Iterate `cfg.regime.labels` in order; a regime with no observations → `n=0`, `rank_ic.value=None`,
   spreads `None`. (This differs from `forward_testing.by_regime`'s `pad=False`; J-27 wants all six rows so
   the browser sees one row per configured label.)
6. **Read-only discipline holds.** The only new DB read is `select(ScannerRun)` for the runs already in
   `runs_with_fr` — still SELECT-only. No `run_scan`/`score_stocks`/`forward_return`/`detect_*`/`score_regime`
   call. The regime is **read verbatim** from `scanner_runs.regime_label` (single source of truth).
7. **Frontend renders rows from the payload (iter-9 config-driven-vocabulary lesson).** Map over
   `data.by_regime` — never a hard-coded frontend regime list — so a config regime-label change needs no
   frontend edit. Use `fmtPct` for the raw mean/spread columns, `fmtRatio` for the rank-IC + risk-adjusted
   spread, `returnClass` for colour, and the existing NA-+-`SampleSize` treatment for null/low-sample cells.
8. **No second date state (J-18).** The page's only state stays `{factor, horizon, state}`. Do not add
   `useAsOf`, `asof`, or any date picker. The new panel reads the same `data` the existing `useEffect` refetches.
9. **No DB regeneration / no schema change.** `regime_label` is already stored on every `scanner_run`; the
   lab just reads it. Confirm against the existing DB — do not rebuild.

## Key Test Scenarios

**Backend (extend `apps/backend/tests/test_research.py`; assert exact values):**
- **Σ per-regime `n` == `n_total`** on a ≥2-regime hand fixture (proves every observation carries exactly one configured regime label, read verbatim).
- **Exact regime spread + rank-IC:** a monotone factor within one regime → known `spread` (top-decile mean − bottom-decile mean) and `rank_ic.value ≈ 1.0`; an inverse regime → negative.
- **Read-only keystone (extended):** in the existing patch-to-raise test, ALSO `monkeypatch` `app.engine.regime.score_regime` to raise (keep `run_scan`/`score_stocks`/`forward_return`/`detect_*` patched) → assert `compute_factor_lab(...)["by_regime"]` is still fully populated (proves the regime is read from stored `scanner_runs`, never recomputed).
- **Downside-only spread:** a regime whose top decile is all-non-negative → `risk_adjusted_spread is None` (NA) while raw `spread` is numeric (downside-only honesty preserved; never total vol).
- **Config-driven regimes:** `by_regime` rows are exactly `cfg.regime.labels` in order; a regime with no observations is an honest `n=0` row (not omitted, not fabricated).
- **Low-sample NA:** a regime with `n < walk_forward.min_sample` → `low_sample=True` with its honest `n`, and `spread`/`risk_adjusted_spread` are `None`.
- **No regression:** existing `test_research.py` (decile math, rank-IC, downside-only, NA honesty, the pooled-mean == `compute_forward_aggregates.overall.mean_return` consistency invariant, config/boot validation) stays green. Full backend suite green — **note ~14 min runtime; do NOT run two pytest invocations concurrently.** Errors unchanged: unknown `factor`/`horizon` → 422; `n_total == 0` → empty-state (no regime table fabricated).

**Frontend / Browser (J-27 via browser-qa-agent; serialize Chrome access with the `qa` agent, de-dup evidence by sha256, assert live DOM/network before EACH capture — iter-6 lesson):**
- `cd apps/frontend && npm run build` typechecks all routes incl. `/research`.
- `/research` renders the "Factor effectiveness by market regime" table with **one row per configured regime label** (the six), each with its `n` chip.
- **Short horizon (5d or 1d)** to maximize per-regime samples → capture at least one regime that clears `min_sample` with a numeric rank-IC + spread. Then a **longer horizon (60d) and/or a sparse regime** → capture an **NA + n** cell (proves honest low-sample treatment, not a fabricated 0). *(Per-regime n is the pooled ~1218 split across up to six regimes, so NA/low-sample/`n=0` rows are EXPECTED here and are correct, not a defect — unlike iter-10's pooled table which never hit NA.)*
- **Re-points on factor change:** change the factor → regime-table values change (assert via DOM text + the observed `GET .../factor-lab?factor=…&horizon=…` network call; capture **distinct** sha256 before/after shots — not a single pair).
- **J-18 regression:** toggle the global top-bar as-of switcher → the Factor Lab (decile table, rank-IC, AND the new regime table) is **byte-identical** with **zero** `as_of`-param requests.
- **J-25 regression:** the existing decile table + rank-IC card still render and re-point on factor/horizon change.

## Process / Evidence Notes (verify-by-source — iter-3/6/9/10 lessons)
- Full-depth iters here have repeatedly finished with **no `status.json` and no auditor handoff** (only `coherence.md` + snapshot-sha). `status.json` lands in the **phase-namespace** path `runs/goal-i_can_see_the_wealthy_future_forever-iter-11/status.json` — **NOT** `runs/goal-session-.../iter-11/` (which holds only `coherence.md` + snapshot-sha). Check BOTH before concluding an artifact is absent. The dev handoff must state explicitly if no `status.json`/auditor handoff is produced.
- Verify the read-only / downside-only / single-source seams **directly in `app/engine/research.py` source** (only SELECTs; no scoring/return/factor/regime call — see the extended patch-to-raise keystone), not by trusting a QA artifact table. De-dup any browser evidence by sha256; ground every "re-points"/"byte-identical" claim on distinct shots + a DOM/network assertion.
- Dev handoff → `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-11-dev.md` (What Was Built / Files Changed / Tests Run with exact counts / Known Issues / Suggested Next Phase).
- `blueprint.md` Factor-Lab Data-Contract row is extended additively to register the `by_regime` slice as part of the SAME value; coherence-auditor must return COHERENCE-PASS (no new canonical value, no new endpoint, no second computation).

## Out of Scope (exclude)
- A full per-regime 10-row decile **table** (six copies). The per-regime summary row (n + rank-IC + top/bottom decile means + raw spread + risk-adjusted spread) satisfies acceptance — the spread IS the decile signal.
- J-26 (multi-factor combination cohorts), J-29 (event study / MAE-MFE), J-30 (full volatility family), J-31 (synthesis) — later `/research` iterations.
- J-22 / J-23 / J-24 — externally Yahoo-429 data-walled; **do NOT autonomously retry.**
- Any change to `forward_testing.py`, `scoring.py`, `scanner.py`, `patterns.py`, `regime.py`, `app/api/research.py`, `config.yaml`, `app/config.py`, the snapshot/as-of read path, the watchlist, the sidebar, or any existing endpoint's payload contract.
- Adding/altering the global as-of switcher or introducing any date state on `/research`. New config keys or any numeric literal in `research.py`.

## Not GOAL_ACHIEVED after this iter
J-26, J-29, J-30, J-31 remain unbuilt `/research` labs (compute-only, now-unblocked) and J-22/J-23/J-24 remain externally data-walled — so failing journeys remain; the evaluator records pass/fail.
