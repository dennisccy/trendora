# goal-i_can_see_the_wealthy_future_forever-iter-11 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-11
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete

## What Was Built

J-27 — **regime-conditioned factor effectiveness** on the Factor Lab (`/research`). The smallest
additive extension of J-25 (iter-10): the existing read-only Factor-Lab analysis now also reports, for
each configured market regime, whether the chosen factor still sorts forward returns *within that
regime*. No new endpoint, no new query param, no nav change, no new config key, no schema/DB change.

- **`_factor_observations` extended (backend):** each read-only observation now also carries the run's
  **stored** `scanner_runs.regime_label`, read VERBATIM via one added `select(ScannerRun)` over the runs
  already in `runs_with_fr` (mirrors `forward_testing.py:534-538`). No regime is recomputed.
- **`_regime_effectiveness(observations, cfg, horizon)` (new read-only helper):** for each label in
  `config.regime.labels` (in config order — no hard-coded regime list) it emits one row: `regime`, `n`,
  `low_sample` (`n < walk_forward.min_sample`), Spearman `rank_ic`, the raw `top_decile_mean` /
  `bottom_decile_mean` from a per-regime decile split (reusing `_deciles`), and the long-short
  top-minus-bottom-decile `spread` both raw and downside-`risk_adjusted_spread`. Both spreads are honest
  `None` (NA) when the regime is low-sample or either leg is None.
- **`by_regime` added to `compute_factor_lab(...)`** — same observation pool, same module, no second
  computation. Existing payload keys unchanged. It rides the SAME `GET /api/research/factor-lab`
  response verbatim (the API view was not touched).
- **Frontend `RegimeEffectivenessTable` panel** on `/research`, below the existing decile table + rank-IC
  card. One server-driven row per configured regime label (never a hard-coded frontend regime list);
  low-sample/null cells render **NA + the honest `n` chip**. New `RegimeEffectivenessRow` type +
  `by_regime` field on `FactorLabResponse`. No date control added (J-18 preserved).

## Files Changed

- `apps/backend/app/engine/research.py` — **modify.** Imported `ScannerRun`; attach the stored
  `regime` per observation in `_factor_observations`; added `_regime_effectiveness(...)`; added the
  `by_regime` key to `compute_factor_lab`. SELECT-only throughout; no scoring/return/factor/regime call.
- `apps/backend/tests/test_research.py` — **modify.** Extended the read-only keystone to ALSO patch
  `app.engine.regime.score_regime` to raise (proving the regime is read, never recomputed) and added 6
  J-27 scenarios + a `multi_regime_engine` fixture + a `_cfg_with(...)` config helper.
- `apps/frontend/lib/api.ts` — **modify.** Added the `RegimeEffectivenessRow` interface and the
  `by_regime: RegimeEffectivenessRow[]` field on `FactorLabResponse`.
- `apps/frontend/app/research/page.tsx` — **modify.** Added the `RegimeCell` cell + the
  `RegimeEffectivenessTable` panel and rendered it inside `FactorLab` below the decile/rank-IC grid.

**Not touched (per spec OUT OF SCOPE):** `app/api/research.py`, `config.yaml`, `app/config.py`,
`forward_testing.py`, `scoring.py`, `scanner.py`, `patterns.py`, `regime.py`, the sidebar, the as-of
switcher, any other page or endpoint. No DB regeneration, no schema change.

## Tests Run

Command (backend): `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

Targeted (run and confirmed PASS):
- `tests/test_research.py` — **29 passed** (22 pre-existing + 6 new J-27 scenarios + the extended
  read-only keystone). New tests: `test_by_regime_n_sums_to_total`,
  `test_by_regime_rows_are_config_labels_in_order_with_honest_empty_rows`,
  `test_by_regime_exact_spread_and_rank_ic`,
  `test_by_regime_risk_adjusted_spread_na_when_top_decile_all_non_negative`,
  `test_by_regime_low_sample_regime_is_na_with_honest_n`, and the extended
  `test_factor_lab_is_read_only_no_scoring_or_return_or_pattern_call`.
- `tests/test_no_magic_numbers.py` — **2 passed** (confirms `research.py` introduced no float literal and
  no forbidden tunable integer — the by-regime math uses only structural ints + config values).
- `tests/test_api_research.py` — **6 passed** (the `by_regime` key rides the live payload safely; the
  J-18 "no date field" assertion still holds — `by_regime` is not a date field).

Full backend suite: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` — **384 passed, 4 skipped,
0 failed in 1181.78s (19:41).** No regressions. The 4 skips are the offline-skipped `@integration`
external-network tests (e.g. the stooq live fetch), exactly as recorded in iter-10. (379 in iter-10 + 5
new J-27 test functions = 384.)

Frontend: `cd apps/frontend && npm run build` — **compiled successfully, types valid, all 14 routes
generated** (`/research` 5.79 kB, grown by the new panel).

Live data check (real committed seed DB, via `compute_factor_lab` directly — no server boot needed):
- 11 scanner_runs spanning 4 distinct stored regimes (Risk-on:7, Risk-off:2, Choppy:1, Narrow
  leadership:1). `by_regime` returns exactly the 6 configured labels in order.
- **Σ per-regime n == n_total** at both h=5 (732+122+122+242 = 1218) and h=60 (1217). ✓
- Honest **NA + n=0** for the two regimes with no runs (Strong risk-on, Defensive). Numeric rank-IC +
  spreads for the four populated regimes (all clear `min_sample=30`).
- The J-27 insight is visible: `leadership_score` has a mildly positive rank-IC in Risk-on (+0.063) but
  strongly negative in Narrow leadership (−0.602) and Choppy (−0.302) at h=5 — a pooled-"ok" factor
  shown to be regime-dependent.

## Known Issues

- **None functional.** The feature is additive and fully covered by unit tests + a live seed-data check.
- **Test-suite runtime:** the full backend suite (~14 min; heavy walk-forward boot in shared fixtures)
  must not be run concurrently with another pytest invocation. My change is isolated to `research.py`;
  the three files that exercise it (`test_research`, `test_no_magic_numbers`, `test_api_research`) all
  pass, and the full suite is green.
- **Process note (for the evaluator, per iter-3/6/9/10 lessons):** `status.json` is written to the
  **phase-namespace** path `runs/goal-i_can_see_the_wealthy_future_forever-iter-11/status.json` (NOT
  `runs/goal-session-.../iter-11/`, which holds only `coherence.md` + snapshot-sha). No `-audit.md` is
  produced by the developer step — the auditor runs later in the pipeline. Verify the read-only /
  downside-only / single-source seams directly in `apps/backend/app/engine/research.py` (only SELECTs;
  the extended patch-to-raise keystone proves no scoring/return/factor/regime call).
- **Browser-QA hygiene (iter-6 lesson):** serialize Chrome access between the `qa` and
  `browser-qa-agent`; de-dup evidence by sha256; ground "re-points on factor change" and "byte-identical
  on as-of change" claims on DISTINCT shots + a DOM/network assertion, never a single screenshot pair.
  Note the new table carries `data-testid="regime-effectiveness-table"` for stable selection.
- **Stale warm backend cleared (for QA):** a backend was already running on :8835 from an earlier
  pipeline step, serving PRE-`by_regime` code (it does not auto-reload, and `start-backend.sh` reuses a
  running backend). I confirmed it lacked `by_regime` and **freed port 8835 by port** (kill-by-port only,
  per the multi-project-machine rule — no broad `pkill`; no other project's server was touched). The
  QA/browser step will start a fresh backend on :8835 serving the new code. The frontend `next dev` on
  :3835 was left running (it hot-reloaded the new `page.tsx`/`api.ts`). I started no server of my own.

## Suggested Next Phase

Continue the `/research` lab build-out with another now-unblocked, compute-only, additive lab on the
same read-only seam: **J-26 (multi-factor combination cohorts)** — combine two catalog factors into
joint top/bottom cohorts and report their forward-return spread — or **J-29 (event study / MAE-MFE)**.
Both reuse the same stored forward-return + stored-factor observation pool and the `/research` home; no
nav re-approval. J-22/J-23/J-24 remain externally Yahoo-429 data-walled — do not autonomously retry.
This iteration is NOT GOAL_ACHIEVED: J-26/J-29/J-30/J-31 remain unbuilt and J-22/J-23/J-24 data-walled.
