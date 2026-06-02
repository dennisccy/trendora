# goal-i_can_see_the_wealthy_future_forever-iter-13 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-13
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete
**Target journey:** J-30 — Volatility as a first-class factor family on the `/research` Factor Lab.

## What Was Built

- **Three new volatility indicator functions** (`app/engine/indicators.py`), pure / DB-free / NA-graceful,
  each taking its window(s) as an argument (periods from config — no magic numbers):
  - `hist_volatility(closes, window)` — population stdev of the last `window` daily simple returns,
    expressed as a percent (comparable to ATR%). NA if `< window+1` bars.
  - `vol_contraction(closes, recent, prior)` — continuous VCP-style ratio = recent realized vol / prior
    realized vol; `< 1` = contracting. NA if `< recent+prior+1` bars OR the prior vol is zero (undefined
    ratio — never infinite/fabricated).
  - `downside_vol(closes, window)` — trailing downside semideviation about MAR=0, `sqrt(mean(min(r,0)**2))`,
    negative leg only (an all-up window → 0.0, never penalising upside). NA if `< window+1` bars.
- **Three new stored per-stock factor values on the immutable snapshot** (`ScannerResult.hv`,
  `.vcp_contraction`, `.downside_vol` — typed `Optional[float]` columns, the established `is_vcp`
  append-only-column precedent). Computed ONCE per stock in `score_stocks` from the as-of bars already in
  hand (date ≤ D, no lookahead) and mirrored to the columns in the SAME `run_scan` transaction. Read
  VERBATIM by the existing read-only `compute_factor_lab` (the bare-column `source` resolves via
  `FACTOR_TYPED_COLUMNS`) — no new research function, no new endpoint.
- **Three new Factor-Lab catalog members** (`config.yaml` → `research.factor_lab.factors`): `hv`,
  `vcp_contraction`, `downside_vol`, all `family: volatility`, `direction: lower_better`. They appear in
  the config-driven `/research` factor dropdown automatically.
- **Four new config windows** (`config.yaml` → `indicators`, typed + validated positive on
  `IndicatorsCfg`): `hv_window: 21`, `semivol_window: 63`, `vol_contraction_recent: 21`,
  `vol_contraction_prior: 63`.
- **Frontend**: the `/research` Factor selector now groups options by `family` via native `<optgroup>`
  (config-driven; the four volatility measures collect under a "Volatility" heading). Purely
  presentational — see the frontend handoff.
- **Database regenerated** so every immutable snapshot carries the three new values and the forward-return
  pool is intact (rebuilt deterministically from the committed seed; no network fetch).

## Files Changed

- `apps/backend/app/engine/indicators.py` — added `hist_volatility`, `vol_contraction`, `downside_vol`
  (+ two private helpers `_daily_returns`, `_population_stdev`); `from math import sqrt`.
- `apps/backend/app/engine/scoring.py` — compute the three values per stock in `score_stocks` from the
  as-of closes and add them to the canonical row dict. `_build_score` and all weight dicts UNTOUCHED.
- `apps/backend/app/engine/scanner.py` — mirror the three row values onto the new `ScannerResult` columns
  in the existing `run_scan` transaction (alongside the `is_vcp`/pattern mirrors).
- `apps/backend/app/models.py` — added `hv` / `vcp_contraction` / `downside_vol` `Optional[float]` columns
  to `ScannerResult` (+ docstring).
- `apps/backend/app/config.py` — extended `FACTOR_TYPED_COLUMNS` with the three column names; added the
  four typed validated window fields to `IndicatorsCfg`.
- `apps/backend/app/engine/research.py` — docstring-only note (the volatility columns may be NULL → excluded). No logic change.
- `config.yaml` — four new `indicators` windows + three new `research.factor_lab.factors` entries.
- `apps/frontend/app/research/page.tsx` — `FactorSelector` renders `<optgroup>` groups by family.
- `apps/backend/tests/test_indicators.py` — 11 new exact-value/NA/guard tests for the three functions.
- `apps/backend/tests/test_scoring.py` — score-invariance keystone (see below).
- `apps/backend/tests/test_research.py` — 2 new tests (volatility column factor decile/IC/by-regime from
  stored values + all-NULL honest-empty) + `_add_result` helper extended with the volatility columns.
- `apps/backend/tests/test_config_engine.py` — 3 new tests (real config windows; non-positive window →
  ConfigError; the three factor sources resolve) + `VALID` fixture windows.
- `apps/backend/tests/test_config.py` — `MINIMAL_VALID` fixture windows.

## Critical anti-goal seams (verified in source + live)

- **Single source of truth / Risk-Off gate (the keystone risk).** The three values enter NO weighted
  score: they are absent from every `config.scores.{leadership,entry_quality,risk}.weights` and never pass
  through `_build_score`. `test_volatility_values_ride_the_row_but_enter_no_score` forces the three
  indicators to an absurd constant and asserts every stock's three scores + A–E buckets + setup status +
  rank are BYTE-IDENTICAL to baseline (mirrors the proven `test_vcp_is_a_pattern_not_a_status`).
- **No lookahead.** The values are computed from `closes(bars_asof(... ≤ asof))` — the same as-of bars
  already read for the row; no future bar is touched.
- **Read-only lab / no recompute.** `research.py` gained only a docstring note; the existing patch-to-raise
  keystone (`run_scan`/`score_stocks`/`forward_return`/`detect_*`/`score_regime` → raise) still passes —
  the lab reads the stored column via `getattr`, recomputing nothing. A NULL value is excluded honestly.
- **No magic numbers.** The windows + labels live in config; `test_no_magic_numbers` stays green
  (indicators.py uses only structural literals 0/1/2/100).

## Live post-regen verification (against the regenerated DB on :8835)

- **J-30** — all four volatility factors render populated evidence: `atr_pct`/`hv` n_total=1218,
  `vcp_contraction`/`downside_vol` n_total=1217 (one short-history observation honestly excluded), each
  with a numeric rank-IC, numeric decile means, and a downside-risk-adjusted column. Reported directions
  (honest, descriptive): hv rank-IC ≈ **+0.028**, vcp_contraction ≈ **−0.015** (essentially flat),
  downside_vol ≈ **+0.116**, atr_pct ≈ **−0.006**.
- **Contraction cross-check** — `vcp_contraction`'s decile/IC is read from the SAME stored `forward_returns`
  pool the System Health VCP-vs-non-VCP breakdown uses (both join `forward_returns` to `scanner_results`;
  no recomputation). The continuous contraction ratio shows essentially **no** forward-return edge in this
  seed (IC ≈ −0.015) — a valid honest finding (acceptance is descriptive, not the textbook assumption).
- **J-07 (CRITICAL re-verify after regen)** — both seeded Risk-Off runs show **zero** Actionable:
  `2025-04-04` Actionable=0, `2022-10-07` Actionable=0. (Non-risk-off runs legitimately carry actionable
  candidates — e.g. 2026-02-27 Narrow-leadership=1, 2025-02-28 Choppy=1 — so the gate is meaningfully gating.)
- **J-06 (CRITICAL re-verify after regen)** — NVDA's full detail row == its list row (byte-identical),
  scores Leadership 47.48/E, Entry 66.24/D, Risk 33.79/E; NVDA carries hv=2.45, vcp_contraction=1.04,
  downside_vol=0.014.
- **Error case** — unknown factor → 422 (extended catalog still validates).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`  (run after the DB regen)
Result: **428 passed, 4 skipped, 0 failed** (~20 min). The 4 skips are the offline-skipped
`@integration` external-network tests (e.g. the Stooq live fetch). 411 (iter-12 baseline) + 17 new =
428: 11 in `test_indicators.py` (exact-value/NA/guard for the three new functions), 1 in `test_scoring.py`
(score-invariance keystone), 2 in `test_research.py` (volatility-column factor decile/IC/by-regime from
stored values + all-NULL honest-empty), 3 in `test_config_engine.py` (real-config windows; non-positive
window → ConfigError; the three factor sources resolve). `test_no_magic_numbers` green.

Note: the FIRST full run after regen reported 2 failures — `test_sectors.py` and `test_themes.py` each
build a small SYNTHETIC config dict that was missing the four newly-REQUIRED `indicators` windows (a
`ValidationError`, no production code involved). Both fixtures were updated (added the windows at the
synthetic scale) and the suite re-run is the clean 428/4 above. (Lesson logged: a newly-required typed
config field must be added to EVERY inline test config fixture, not only `MINIMAL_VALID`/`VALID`.)

Targeted (pre-suite, all green): `test_indicators.py` + `test_no_magic_numbers.py` 32 passed; `test_config.py` +
`test_config_engine.py` 67 passed; `test_scoring.py` (pre-keystone) 15 passed; `test_research.py` +
`test_api_research.py` 62 passed. Frontend `npm run build` PASS (typechecks; `/research` builds).

## Known Issues

- The three volatility values are stored for the Factor Lab only — intentionally NOT surfaced on the
  `/stocks` leaderboard or stock-detail breakdowns (per scope). They ride the canonical `/api/stocks(/…)`
  rows via `record_json`, so the J-06 list↔detail byte-identity is preserved.
- The reported predictive directions are weak/near-zero (see live verification) — reported honestly; the
  lab is descriptive evidence, not a forecast.
- The backend is left running and healthy on :8835 serving the regenerated DB (the goal-mode harness keeps
  a backend up across iterations; `browser-qa-phase.sh` reuses a healthy backend). The DB FILE itself is
  the durable artifact — a fresh boot would idempotently reuse it.

## Suggested Next Phase

J-29 (Setup & Pattern event study — MAE/MFE excursion path + expectancy + exit-horizon), which unlocks the
`return/MAE` risk-adjustment and the deeper contraction event-study cross-check, then J-31 (synthesis,
needs J-29 + J-27). GOAL_ACHIEVED is not autonomously reachable while J-22/J-23/J-24 remain externally
data-walled — do not autonomously retry them.
