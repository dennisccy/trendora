# goal-mcp-loop-iter-40 Dev Handoff

**Phase:** goal-mcp-loop-iter-40
**Date:** 2026-07-15
**Agent:** developer
**Status:** complete (see "Known Issues" for one deferred operational step and one deferred test lane)

## What Was Built

J-24 (backlog B-201) — a per-stock "how much can this hurt" risk-budget card and matching leaderboard
columns, computed once in the engine and served additively from the existing stock endpoints.

- **Two new PURE indicator functions** in `app/engine/indicators.py`:
  - `overnight_gap_profile(opens, closes, window)` — median/p95/worst of `|open − prior close| / prior
    close` (linear-interpolation percentiles) plus the overnight share of the same window's
    close-to-close return variance. All expressed as percent numbers (matching the existing
    `atr_pct`/`hist_volatility` convention). NA (`None`) on insufficient history; `overnight_variance_share`
    alone drops to NA on a zero-variance window while median/p95/worst still report.
  - `worst_20d_window(closes, window)` — the most negative trailing `window`-day return anywhere in the
    given closes series (a percent number). NA on insufficient history.
  - Both raise `ValueError` on a non-positive window (mirrors every other indicator in the module) and
    never fabricate a value.
- **`app/engine/prices.py`**: added an `opens(bars)` extractor, mirroring the existing
  `closes`/`highs`/`lows`/`volumes` structural extractors (needed because the gap profile reads open
  prices; not previously exposed). This file was not in the plan's explicit file list but is a
  one-line, in-pattern addition required by the architecture (bars may be `DailyPrice` or `Bar`, both
  need uniform structural extraction).
- **`scoring.py` pass-3**: computes the risk-budget bundle once per ticker from bars already in hand:
  - `atr_pct` and `downside_vol` are **reused** (not recomputed) from pass-1's `raws["atr_pct"]` and
    pass-3's existing `downside_vol` local — verified by a call-count test (see below).
  - The gap profile reads the SAME bounded `bars` slice (`bars_asof_window(..., max_lookback_bars)`)
    already fetched for `inv_closes` — no extra bar fetch.
  - `worst_20d_window` reads the name's FULL as-of history via `bars_asof(session, ticker, asof)` (not
    the `max_lookback_bars`-bounded slice) — the interpretation the goal-decomposer logged in
    `runs/goal-session-mcp-loop/state/assumptions.md` (iter-40, reversible). When a `bar_cache` context
    is active (bootstrap/backfill), this slices the already-resident cached series — no new DB round
    trip.
  - `distance_to_invalidation_pct` reuses the existing `_pct_from_ma` helper against the already-built
    `invalidation` dict's `level`/`price` — no second level computation.
  - A new post-row-assembly pass (`_apply_risk_budget_percentile`, called 8 times, once per leaf)
    attaches CROSS-SECTIONAL percentiles computed over the same as-of scan's resolved members —
    oriented so a HIGHER percentile always means MORE risk (`worst_20d_window` and
    `distance_to_invalidation_pct` are negated before ranking, since a smaller/more-negative raw value
    is more dangerous there).
  - The new `risk_budget` field enters **no weighted score** — Leadership/Entry Quality/Risk are
    unaffected (verified — see Tests below).
- **Config**: `IndicatorsCfg` gained `gap_window: int` and `worst_window_days: int` (both required,
  validated positive, folded into the `max_lookback_bars` `max_needed` guard alongside
  `hv_window`/`semivol_window`). `config.yaml` sets both to `20`. Three new `factor_stats` glossary
  entries document the new components (`overnight-gap profile`, `worst 20-day window`,
  `distance-to-invalidation %`), mirroring the existing ATR%/HV entries, served automatically by the
  existing `app.engine.methodology:build_catalog` (no code change there).
- **No `scanner.py` / `snapshot_serving.py` change** — confirmed by reading both: `record_json =
  json.dumps(row)` already persists the whole row dict losslessly, and both `stocks_payload` /
  `stock_detail_payload` re-serve `json.loads(record_json)` verbatim, so the new `risk_budget` key
  flows through `GET /api/stocks` and `GET /api/stocks/{ticker}` automatically.
- **`runs/goal-session-mcp-loop/state/blueprint.md`**: already carried the correct Data Contract row and
  IA-table clarification row for J-24/iter-40 (pre-populated, committed at `ef88bd6`, before this dev
  pass started) — verified the content matches this implementation exactly (single source, no
  weighted-score entry, NA-graceful, worst-20d full-history-via-bar-cache framing) and made no edit
  (editing an already-correct, already-committed row would only risk introducing drift/duplication).

### Frontend

- **`apps/frontend/lib/api.ts`**: added `RiskBudgetComponent` (`{value, percentile}` — the
  `raw`/`percentile` pairing convention `ScoreComponent` already uses), `GapProfile`, and `RiskBudget`
  interfaces; extended `StockRow` with `risk_budget?: RiskBudget` (optional — a scanner row persisted
  before iter-40 carries no `risk_budget` key at all, an honest absence rather than a fabricated NA).
- **`apps/frontend/lib/risk-budget.ts`** (new file, not in the plan's explicit list but a natural small
  helper mirroring the existing `high-proximity.ts` pattern): `fmtRiskValue`, `fmtRiskPercentile`,
  `isRiskBudgetNa` — the single formatting source shared by the card and the leaderboard columns so the
  same stock's number reads identically in both places.
- **`apps/frontend/app/stocks/[ticker]/page.tsx`**: a new `RiskBudgetCard` (with a `RiskMetricTile`
  sub-component), placed directly after `ThemeAndInvalidationCard`. Renders ATR%, downside volatility,
  the gap profile (p95 headline + median/worst as supporting lines + overnight variance share), worst
  20-day window, and distance-to-invalidation, each with a "pXX of universe" percentile chip when
  present. NA renders warn-colored "NA — insufficient history" text (mirrors the existing
  `naInvalidation` treatment). Renders nothing (`return null`) when `row.risk_budget` is absent.
- **`apps/frontend/app/stocks/page.tsx`**: five new sortable leaderboard columns (ATR%, Downside vol, Gap
  p95, Worst 20d, Dist. to invalidation), config-driven via a `RISK_BUDGET_COLUMNS` array (mirrors the
  existing `PATTERNS` array pattern) so header/cell/comparator all read one list. Comparator logic
  mirrors the existing `high_proximity` column exactly: NA always sorts last regardless of direction.
  Each column's `term` links to its new methodology glossary entry via the existing `TermInfo`
  component.
- No business logic in the frontend — every value and percentile is read verbatim from the server.

## Files Changed

- `apps/backend/app/engine/indicators.py` — `overnight_gap_profile`, `worst_20d_window`, `_percentile` helper
- `apps/backend/app/engine/prices.py` — `opens()` extractor (additive, not in the original file list)
- `apps/backend/app/engine/scoring.py` — pass-3 risk-budget computation + post-loop percentile pass
- `apps/backend/app/config.py` — `IndicatorsCfg.gap_window` / `.worst_window_days`
- `config.yaml` — `indicators.gap_window`/`.worst_window_days`; 3 new `factor_stats` glossary entries
- `apps/backend/tests/test_indicators.py` — 8 new fixture tests (exact-value + NA paths)
- `apps/backend/tests/test_scoring.py` — 6 new tests (fields+percentiles, 2 byte-match spot checks,
  reuse call-count proof, score-invariance/no-leakage proof)
- `apps/backend/tests/test_config_engine.py` — 3 new boot-validation tests; `VALID` fixture extended
- `apps/backend/tests/test_config.py` — inline fixture extended (2 new required keys)
- `apps/backend/tests/test_sectors.py`, `test_indexes.py`, `test_themes.py` — inline synthetic-config
  fixtures extended (2 new required keys each) — necessary because `gap_window`/`worst_window_days`
  became required `IndicatorsCfg` fields; NOT in the plan's explicit file list but unavoidable
- `apps/backend/tests/test_api_methodology.py` — `GLOSSARY_SPOT_CHECK_TERMS` extended with the 3 new terms
- `apps/frontend/lib/api.ts` — `RiskBudgetComponent`/`GapProfile`/`RiskBudget` types; `StockRow.risk_budget?`
- `apps/frontend/lib/risk-budget.ts` — new formatting-helper module (not in the plan's explicit list)
- `apps/frontend/app/stocks/[ticker]/page.tsx` — `RiskBudgetCard` + `RiskMetricTile`
- `apps/frontend/app/stocks/page.tsx` — 5 new leaderboard columns + `RiskBudgetCell`

## Tests Run

**Fast lanes — all confirmed GREEN this session:**

```
cd apps/backend && .venv/bin/python -m pytest tests/test_indicators.py tests/test_config.py \
  tests/test_config_engine.py tests/test_api_methodology.py -q
```
Result: **162 passed** (38 in `test_indicators.py` incl. 8 new; 118 in `test_config*.py` incl. 6 new;
6 in `test_api_methodology.py`).

```
cd apps/backend && .venv/bin/python -m pytest \
  tests/test_sectors.py::test_min_history_bars_floor_reports_na_for_short_history \
  tests/test_sectors.py::test_synthetic_industry_members_and_empty_state \
  tests/test_themes.py::test_theme_with_no_member_history_degrades_to_na_not_crash \
  tests/test_indexes.py -v
```
Result: **20 passed** — the synthetic-config subset of these 3 files that exercises the fixture edits
(the OTHER tests in these files use the session-scoped `loaded_engine` real-seed fixture and were not
re-run here to avoid re-paying its build cost twice in one session; they are unaffected by this
change's scope — see "Known Issues").

**Real-seed verification — a standalone script, NOT part of the pytest suite** (written to sidestep the
`loaded_engine` fixture's full 5-date `bootstrap_runs` + `backfill_forward_returns` cost, since I only
needed ONE `score_stocks` call against the real committed seed to validate this change; ~191s total:
~25s seed load + ~77s for one full-universe `score_stocks` call at the latest date, 541 rows):
```python
# loads the real committed seed into a temp DB, calls score_stocks(session, latest_date, cfg) once
```
All 5 checks **PASSED**:
1. every `risk_budget` leaf present with a float value and a percentile in `[0,1]` for NVDA (ample history)
2. percentiles are genuinely cross-sectional (not a fabricated constant — >1 distinct value across rows)
3. **byte-match**: `risk_budget.gap_profile.p95.value` and `risk_budget.worst_20d_window.value` both
   match an independent offline recomputation (`ind.overnight_gap_profile`/`ind.worst_20d_window`
   called directly on the same bars) to full float precision
4. **no score leakage**: forcing `ind.overnight_gap_profile`/`ind.worst_20d_window` to return `999.0`
   via monkeypatch leaves every row's Leadership/Entry Quality/Risk score+bucket, setup status, and
   rank byte-identical to baseline, while confirming the monkeypatch really took effect on the
   `risk_budget` fields
5. **reuse, not recompute**: `risk_budget.atr_pct.value` (rounded to 4dp) equals the existing
   `risk.components[].raw` value for `atr_pct` — the same underlying number

TypeScript: `cd apps/frontend && ./node_modules/.bin/tsc --noEmit -p tsconfig.json` — **zero errors**.

**NOT confirmed via pytest this session (deferred to the reviewer):** the full
`pytest tests/test_scoring.py tests/test_scoring_window.py` run — including my 6 new `test_scoring.py`
functions AS ACTUAL PYTEST ASSERTIONS (as opposed to the equivalent logic in the standalone script
above) and the pre-existing `test_scoring_window.py` byte-identity harness
(`max_lookback_bars=320` vs. an effectively-disabled window, over real cadence dates) — was launched
and run for **31+ minutes** without completing even the FIRST test's `loaded_engine` fixture setup (a
known, pre-existing characteristic of this session-scoped real-30-year-seed fixture — see
`.claude`-memory "30y test suite slow, not the product"), then killed per explicit operator direction
rather than left to fork-lock the box or run indefinitely. I have HIGH but not pytest-certified
confidence this lane is green:
  - Every one of my 6 new `test_scoring.py` functions asserts the SAME properties my standalone script
    already confirmed PASS against the real seed (I wrote the standalone checks by translating the
    pytest assertions 1:1, including the same `pytest.approx`-equivalent tolerances and the same
    `round(..., 4)` fix — see "Known Issues" for the one bug that fix caught).
  - `test_scoring_window.py`'s byte-identity harness compares `score_stocks` under `max_lookback_bars=320`
    vs. `1_000_000` (disabled). `worst_20d_window` reads via `bars_asof` (NOT `bars_asof_window`), so its
    value is structurally independent of `max_lookback_bars` in both configurations — by construction it
    cannot break this harness. `overnight_gap_profile` reads the `max_lookback_bars`-bounded `bars` slice
    but only ever consumes the trailing `gap_window+1` (=21) elements — identical in both configurations
    as long as the slice has >= 21 bars (true in both: 320 and 1,000,000 are both >> 21) — so it is also
    structurally invariant to the window-size knob under test. I did not touch `score_regime` at all.
  - This reasoning is NOT a substitute for running the harness; it is the basis for my confidence
    level, not a claim of verification. **The reviewer should re-run
    `pytest tests/test_scoring.py tests/test_scoring_window.py -v` to completion** (budget 20-40+
    minutes for the `loaded_engine`/`seed_engine` fixture builds) as the authoritative confirmation
    before sign-off.

## Known Issues

- **Operational step NOT performed this session (blocking for browser-qa):** the spec's own NOTES
  flag that `run_scan` is immutable and `apps/backend/data/trendora.db` is NOT rebuilt automatically —
  the served bootstrap + latest snapshots must be regenerated under this new code (delete
  `apps/backend/data/trendora.db` [+ `-shm`/`-wal` sidecars] and let a fresh boot's
  `ensure_latest_snapshot` + background `start_warmup` recompute them) before `/api/stocks/{ticker}`
  will show real (non-null) `risk_budget` values instead of every row reading the honest-but-unhelpful
  "not yet computed for this run" absence. I deliberately did NOT perform this rebuild in this pass —
  it was deferred to keep this turn bounded per explicit operator direction, given the pytest run above
  had already consumed the turn's time budget. **This is a real, not cosmetic, gap**: browser-qa will
  see `risk_budget` absent (frontend renders no card / NA leaderboard cells) on the CURRENT
  `apps/backend/data/trendora.db` until this rebuild runs. Based on the standalone script's measured
  timing (~25s seed load + ~77s for the latest date's `score_stocks`), the fast-ready `ensure_latest_snapshot`
  boot step (which per J-40 design does exactly ONE `score_stocks` call, at the latest date, before
  serving) should complete in roughly 1-2 minutes; the background warm-up of the 4 configured
  `bootstrap_dates` + the full forward-return cadence will take longer and is not on the critical path
  for a liquid-name browser-qa check at the default (latest) as-of. **Recommended next step**: `rm -f
  apps/backend/data/trendora.db*` then start the backend (`scripts/start-backend.sh`), poll
  `GET /api/health` until `readiness: "ready"`, then confirm `GET /api/stocks/AAPL` (or another liquid
  name) carries non-null `risk_budget` values before the browser-qa lane runs.
- **`test_scoring.py`/`test_scoring_window.py` full pytest confirmation deferred to the reviewer** — see
  "Tests Run" above for the detailed reasoning on why I have high (but not pytest-certified) confidence.
- **B-201's adjustment-seam trap acknowledged, not implemented:** the backlog card's Traps section notes
  "worst-window on adjusted prices spanning an adjustment seam — cite B-113/B-116 markers in the tooltip
  when applicable." B-113 (data-quality sentinel) and B-116 (corporate-actions awareness) are both
  UNBUILT (confirmed — no such module exists anywhere in `apps/backend/app/`), so there is no marker to
  cite yet; the `worst_20d_window` tooltip carries no seam disclosure. This is out of scope for this
  iteration (nothing in the DoD mentions it) and is recorded here only so a future B-113/B-116
  implementer knows to wire this tooltip in.
  `apps/backend/data/seed/meta.json` shows the 548-name equities span was ingested from one consistent
  Stooq-local basis (per goal.md §A "Status: DONE offline"), so this is a low-probability, forward-looking
  concern, not a known live defect.
- **`.claude/project-template.md` still unfilled** (symlinked to the framework's generic template) — a
  pre-existing, previously-flagged gap (iter-34/37/39 dev handoffs); test/start commands were sourced
  from the actual `apps/`/`scripts/` structure instead, as before. `docs/architecture/*.md` also does not
  exist in this project (goal-mode sessions track architecture via `runs/goal-session-mcp-loop/state/
  blueprint.md` instead) — confirmed the directory is absent, not a new gap.
- No regression to any existing score, bucket, setup status, evidence badge, or ledger — this iteration
  registers no `## Evidence Claim` and touches no evidence/ledger file (confirmed: `git status` shows
  no diff under `runs/goal-session-mcp-loop/state/{certified-claims,staging-ledger,pre-registrations}.jsonl`).
- Frontend dev/prod servers were NOT started this session (deferred alongside the DB rebuild, for the
  same turn-budget reason) — no server process was left running by this pass (confirmed via `ps aux`
  before finishing).
