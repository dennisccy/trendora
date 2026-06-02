# Phase goal-i_can_see_the_wealthy_future_forever-iter-13 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-13
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

<!-- "What to Test" is a specific action with an expected result. -->

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research` | `FactorSelector` dropdown (`data-testid="factor-select"`) | Changed behavior (grouping) | Options now grouped by `family` via `<optgroup>` (config-driven) | Open the Factor dropdown; confirm options appear under family sub-headings (Score, Momentum, Trend, Volatility…) and that a **"Volatility"** group lists exactly four entries: ATR % (volatility level), Historical volatility (HV), Volatility contraction (VCP-style), Downside volatility (semivol). |
| `/research` | `FactorSelector` dropdown | New options | Three new volatility factors added to config-driven catalog | Select **Historical volatility (HV)**; confirm the header line shows `volatility · lower better` and the page re-fetches/re-points to HV (does not stay on the previous factor). |
| `/research` | Decile table (`FactorLab` decile rows) | New data | New factors render their decile means + downside-risk-adjusted column | Select **Volatility contraction (VCP-style)**; confirm the decile table populates with a raw mean forward-return column **and** a downside-risk-adjusted column, each showing a per-decile `n`. |
| `/research` | Decile table — risk-adjusted column | New data (honest NA) | Downside-risk-adjusted is downside-only; undefined when a decile has no downside / n<2 | Select **Downside volatility (semivol)**; find a decile whose downside-risk-adjusted cell shows **NA** (not 0) and confirm an `n` is shown beside it — confirm "risk" is downside-only, never penalising a healthy all-up decile. |
| `/research` | Rank-IC card | New data | Spearman rank-IC computed for the new factors | Select **Historical volatility (HV)**; confirm a numeric rank-IC value with its `n` is shown (per dev handoff hv rank-IC ≈ +0.028, downside_vol ≈ +0.116, vcp_contraction ≈ −0.015 — a numeric value, not blank). |
| `/research` | `RegimeEffectivenessTable` (by-regime split) | New data | Per-regime rank-IC / top-bottom decile spread for new factors | Select **Volatility contraction (VCP-style)**; confirm the by-regime table renders per-regime rows; locate at least one genuinely empty/low-sample regime (e.g. Strong risk-on / Defensive at n=0) showing **NA + `n`**, not a fabricated 0. |
| `/research` | `CaveatBanner` | Unchanged (re-verify still visible) | Honest-limitations labels must show for new factors | With a new volatility factor selected, confirm the survivorship-bias + "descriptive, not predictive" caveat banner is still visible. |
| `/research` | Global as-of date control vs Factor Lab (J-18) | Unchanged (regression guard) | Factor Lab must have no second date state | Toggle the global as-of date control; confirm the Factor-Lab tables for a volatility factor stay **byte-identical** and no `as_of`-scoped request fires from the lab. |
| `/stocks` | Leaderboard score columns (J-06 / J-07 regression after DB regen) | Changed behavior (DB regen — values must be identical) | DB regenerated; scores must be byte-identical | Open a seeded **Risk-Off** run; confirm **zero** stocks are marked "Actionable". Then compare NVDA's Leadership/Entry/Risk number+bucket on the leaderboard against `/stocks/NVDA` — confirm byte-identical (47.48/E, 66.24/D, 33.79/E). |
| `/stocks/NVDA` | Stock-detail score breakdown | Unchanged (regression guard) | New volatility values must NOT appear here | Confirm the new volatility values (hv, vcp_contraction, downside_vol) are **NOT** shown in the stock-detail score breakdown and that the three displayed scores match the leaderboard. |

---

## Backend-Only Changes (No UI Impact)

<!-- Backend changes with no direct UI surface a user reads, beyond feeding the Factor Lab above. -->

- `apps/backend/app/engine/indicators.py` — added `hist_volatility`, `vol_contraction`, `downside_vol` (pure math, NA-graceful) — no UI surface; their outputs surface only via the Factor Lab.
- `apps/backend/app/engine/scoring.py` — computes the three values per stock (bars ≤ D, no lookahead) and adds them to the canonical row dict — backend compute path; `_build_score` and all weight dicts untouched (the score-invariance keystone).
- `apps/backend/app/engine/scanner.py` — mirrors the three values onto the new `ScannerResult` columns in the existing `run_scan` transaction — persistence only.
- `apps/backend/app/models.py` — three new `Optional[float]` columns (`hv`, `vcp_contraction`, `downside_vol`) on `ScannerResult` — schema only; ride the canonical `/api/stocks(/…)` rows but are not rendered on the leaderboard/detail.
- `apps/backend/app/config.py` — extended `FACTOR_TYPED_COLUMNS`; four new validated `IndicatorsCfg` windows (`hv_window`, `semivol_window`, `vol_contraction_recent`, `vol_contraction_prior`) — config wiring.
- `apps/backend/app/engine/research.py` — docstring-only note (NULL volatility columns excluded). No logic change; the read-only lab seam is unchanged.
- `config.yaml` — four new `indicators` windows + three new `research.factor_lab.factors` catalog entries (the source of the new dropdown options).
- Backend test files (`test_indicators.py`, `test_scoring.py`, `test_research.py`, `test_config_engine.py`, `test_config.py`, `test_sectors.py`, `test_themes.py`) — test-only changes.
- **Database regeneration** — `apps/backend/data/trendora.db` rebuilt so snapshots carry the new values; no UI surface directly, but it is the cause of the J-06/J-07 regression re-verify above.

---

## Summary

- **Frontend surfaces changed:** 1 page (`/research` Factor Lab) — dropdown grouping + three new selectable factors that populate existing decile/IC/regime surfaces.
- **New pages/routes:** 0 (additive catalog members on an existing page; no new page, route, endpoint, or nav entry).
- **Modified components:** 1 (`FactorSelector` — `<optgroup>` grouping); the `FactorLab`, decile table, rank-IC card, and `RegimeEffectivenessTable` render the new factors verbatim with no code change.
- **Navigation changes:** no.
- **Backend-only changes:** ~10 files + DB regen (indicator math, scoring compute, persistence column, config, tests) — surfaced to the user only through the Factor Lab; deliberately not shown on `/stocks` or `/stocks/[ticker]`.
