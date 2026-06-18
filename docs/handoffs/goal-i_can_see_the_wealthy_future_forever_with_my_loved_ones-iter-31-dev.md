# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-31 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-31
**Date:** 2026-06-18
**Agent:** developer
**Status:** complete
**Depth:** lean (live re-verification pass — NOT a GOAL_ACHIEVED candidate)

## Summary

This is a LEAN verification iteration. J-89 (Dashboard Market-Phase HISTORY timeline + dated
causal downtrend episodes + the fenced "Retrospective (full-sample / analysis-only)" sub-view)
and J-90 (the causal recovery-turn signal + the `/research` Recovery-Turn Edge lab with
count-coherent `N=` drill-down) were already built and backend-verified at iter-30. The only
thing missing was LIVE evidence (iter-30 browser-QA was SKIPPED entirely — Chrome :9222
`ECONNREFUSED`, evidence dir empty, 0/31 UI tests).

The single intended code change this iteration is the trivial review NOTE carried from iter-30:
remove the redundant local import in `market_phase.py`. The environment is now UP
(backend :8835 ready, frontend :3835 serving a hydrated shell, **Chrome DevTools :9222 reachable
— the gate that failed at iter-30**), so the browser-qa stage can now capture the missing live
pixel evidence. I corroborated the J-89/J-90 data legs against the LIVE served payloads (curl)
and the FAST targeted tests, and proved the cleanup is byte-identical.

## What Was Built / Changed

- **Backend (the only code touch):** Removed the redundant function-local import
  `from datetime import date as _date` at `apps/backend/app/engine/market_phase.py:472` and
  switched line 478 to use the module-level alias `date_cls` (`from datetime import date as date_cls`,
  line 37) already imported. A no-behavior-change cleanup inside `_recovery_turn_dates_with_context`.
  `_date` and `date_cls` were the IDENTICAL object (`market_phase.date_cls is datetime.date == True`),
  so the swap is provably behavior-preserving.
- **Frontend:** NO change. The J-89 timeline overlay + fenced retrospective sub-view, the J-90
  recovery-turn badge (Market-Phase panel), and the `/research` Recovery-Turn Edge lab were all
  built at iter-30 and are committed and unchanged. Live re-verification surfaced no UI defect
  to fix.
- **New capability / endpoint / column / config key:** NONE. Verification pass only.

## Files Changed

- `apps/backend/app/engine/market_phase.py` -- removed the redundant local `date as _date` import; `_date.fromisoformat` -> `date_cls.fromisoformat` (one function, `_recovery_turn_dates_with_context`).

(No other source file modified. `git status` shows exactly one tracked `apps/` change.)

## Byte-Identity Proof (DoD: served payloads must stay byte-identical)

Captured the LIVE OLD-server (pre-cleanup-in-memory) baselines, then computed the SAME three
endpoints in-process via `TestClient(main.app)` running the NEW code on the SAME live DB, and
diffed normalized JSON:

| Endpoint | NEW-code vs live-OLD baseline |
|---|---|
| `GET /api/market-phase` | **byte-identical (True)** |
| `GET /api/market-phase?retrospective=true` | **byte-identical (True)** |
| `GET /api/research/recovery-turn-edge` | **byte-identical (True)** |

Baseline payloads retained (md5-distinct) at
`runs/goal-session-.../iter-31/evidence/curl/` →
`market-phase.before.json` (`1fa1cc3e…`), `market-phase-retro.before.json` (`782394b6…`),
`recovery-turn-edge.before.json` (`b83d2ef3…`).

## Live Backend Corroboration of the Target Journeys (curl, same-instant)

**J-89 (Market-Phase HISTORY timeline + causal episodes + fenced retrospective):**
- Causal `GET /api/market-phase` (latest, as_of=2026-06-16): `timeline` = 60 step-function points
  `{date, phase, p_bear, severity}`; `episodes` = 11 dated CAUSAL downtrend episodes each with
  `first_trigger_date` + `severity_at_trigger` + `last_date` + `open` (incl. the 2022 bear,
  first trigger `2022-01-20`). NO `retrospective`/`smoothed` key present in the causal payload
  (FENCE holds).
- `?retrospective=true` adds `retrospective` with `analysis_only: True`, the SMOOTHED series
  (60 pts `{date, p_bear_smoothed}`) + 1 peak-to-trough true-bear episode
  (`peak 2022-01-03 → trough 2022-10-12, -24.5%, 282 days`). Fetched only on the toggle.
- **No-lookahead under historical as_of=2022-12-30:** causal timeline all dates ≤ D
  (first 2022-10-06, last 2022-12-30, NONE > D), 3 episodes all with first_trigger ≤ D, NO
  retrospective key in the causal payload. The retrospective sub-view (analysis_only) is the
  separately-toggled future-aware surface.
- **Honest empty (early as_of=2021-01-05, before sufficient history):** `available: False`,
  `phase/severity/p_bear: None`, empty `timeline`, empty `episodes` — no fabricated phase/
  episode/probability.

**J-90 (recovery-turn signal + Recovery-Turn Edge lab + N= drill-down):**
- Causal `recovery_turn` block on `/api/market-phase` carries `{is_recovery_turn, reason, p_bear,
  prev_p_bear, ma_reclaimed, exit_threshold, ma_window_days}` — a named `reason` string, never a
  bare flag.
- `GET /api/research/recovery-turn-edge`: `by_horizon` for all 5 config horizons (1/5/10/20/60),
  each with `mean_return / median / pct_positive / expectancy{win_rate,avg_win,avg_loss} +
  return_per_downside_dev + return_per_mae (downside risk-adjusted) + mean_max_drawdown
  (aggregate max-drawdown)`. `by_phase` for all 5 phases (low-sample phases honestly show
  `mean_return: None` + `low_sample: True`, never fabricated). `survivorship_bias` label present.
  `signal_count: 6`, `n_total: 725`, `unique_symbols: 122`.
- **`N=` count-coherence (SAME-INSTANT, live):**
  - episodes h=20: aggregate `n_total=725` == samples `total=725` == `len(rows)=725` ✓
  - pooled  h=20: aggregate `n_total=725` == samples `total=725` == `len(rows)=725` ✓
  - by_phase drill (every emitted combination, no 4xx — J-82 lesson): Expansion 200/total=0,
    Pullback 200/total=243 (== by_phase n=243), Correction 200/total=0, Bear 200/total=0,
    Recovery 200/total=482 (== by_phase n=482).
- **Error cases:** samples `kind=bogus-kind` → 422; `horizon=999` → 422.

## Tests Run

Command (FAST targeted, per the lean-iteration gate — iter-11/iter-29 lessons; the full
~880-test boot-heavy suite is NOT the gate this iteration):

- `cd apps/backend && .venv/bin/python -m pytest tests/test_market_phase.py -q`
  → **40 passed in 479s** (the fence, no-lookahead tail-invariance, filtered byte-identity to the
  J-87/J-88 panel series, determinism, config-validation legs).
- `.venv/bin/python -m pytest tests/test_no_magic_numbers.py -q` → **2 passed**
  (confirms `market_phase.py` still carries no threshold literal after the cleanup).
- `.venv/bin/python -m pytest tests/test_db.py::test_create_all_produces_expected_tables -q`
  → **1 passed** (no new table; `event_study_cache`/`MarketPhaseCache` reuse intact).

Result: **43 passed, 0 failed** across the targeted set.

## Environment Verified UP (the iter-30 gate that failed)

- Backend `:8835` `/api/health` → `status: ok, db_ok: true, readiness: ready, symbol_count: 585,
  warmup 10/10 ok`.
- Frontend `:3835` → HTTP 200, hydrated SSR shell ("Trendora" present, valid
  `_next/static/chunks/main-app.js` chunk — NOT a dead `.next` shell). `/research` SSR markup
  contains "Recovery-Turn" + "Research".
- **Chrome DevTools `:9222`/json/version → HTTP 200 (reachable).** This is the key change from
  iter-30 where it was `ECONNREFUSED` → browser-QA can now run.

## J-18 (exactly one date selector) — CRITICAL, holds by construction

The diff is backend-only (one function, alias swap). NO frontend change → no new date state, no
new `window`/`document` keydown listener added by this iteration. The Market-Phase panel +
retrospective toggle add no second date state (they read the single global as-of). `?asof`
remains the serialization, the Research As-of⇄All-history toggle remains a MODE.

## Anti-goal check

- **FENCE intact:** smoothed P(bear) + peak-to-trough true-bear dating appear ONLY under
  `?retrospective=true` (`analysis_only: True`); absent from the causal payload; nothing
  future-aware leaks into the causal timeline/episodes/recovery signal at a historical as-of.
- **No lookahead:** causal timeline/episodes confined to dates ≤ D (verified at as_of=2022-12-30).
- **No fabricated data:** honest empty at early as-of; low-sample cohorts show NA + n.
- **No recompute / single source / no magic numbers:** byte-identity proof + `test_no_magic_numbers`
  green; no canonical stock score/bucket/setup/pattern/regime/Risk-Off gate touched.
- **No order/execution path:** none added.

## Known Issues / Limitations

- **Live browser pixel evidence is the primary gate and is the NEXT pipeline stage's job**
  (browser-qa-agent via Chrome :9222). This dev pass confirmed the environment is ready (Chrome
  :9222 = 200) and that the underlying data + surfaces are correct, but did NOT itself drive the
  browser. Per the strict rule (iter-17/25/30 precedent), J-89/J-90 must NOT be upgraded to
  `passing` on source/curl review alone — they require the full-viewport, md5-distinct,
  correct-surface captures from browser-QA. Evidence hygiene for that stage: `md5sum` the evidence
  dir FIRST; the Market-Phase panel is BELOW THE FOLD on the Dashboard (scroll the timeline AND
  the fenced retrospective sub-view into view, capture FULL-VIEWPORT, VIEW the pixels); resolve the
  `/research` lab sort headers + `N=` chips by `aria-label` (NEVER `text()` — labels are in nested
  `<span>`s); assert recovery-turn-edge `N=` count-coherence SAME-INSTANT against the live
  aggregate.
- This iteration is intentionally NOT a GOAL_ACHIEVED candidate: J-91..J-96 remain unbuilt
  buildable Must-haves (iter-22 lesson). J-22/J-23/J-24 remain honestly blocked-NA (data-walled).
- The full ~880-test backend suite was NOT run (boot-heavy, ~34 min, exceeds the subagent cap; not
  the gate this iteration — iter-11/iter-29). The pump will handle any full-suite gating.
