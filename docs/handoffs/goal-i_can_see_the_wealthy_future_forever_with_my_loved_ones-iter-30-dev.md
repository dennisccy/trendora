# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30
**Date:** 2026-06-18
**Agent:** developer
**Status:** complete

## What Was Built

J-89 (market-phase HISTORY timeline + dated causal downtrend episodes + a FENCED retrospective view) and
J-90 (causal recovery/turn signal + a read-only Recovery-Turn Edge study). Both are strictly-causal,
read-only, ADDITIVE derivations over the iter-29 `market_phase` layer. NO canonical stock score / A–E
bucket / setup / pattern / regime / Risk-Off→Actionable gate changed; NO snapshot column; NO snapshot
rebuild; NO new top-level nav; NO new page; NO new date selector; NO new DB table.

### Backend — all in/around the SAME `app/engine/market_phase.py` engine (single source)

- **J-89 causal timeline series** — `compute_market_phase` now ADDITIVELY returns a per-snapshot-date
  `timeline` of `{date, phase, p_bear, severity}` — the SAME single derived series the panel value reads
  (the per-date filtered P(bear) is element i of the EXACT `_filtered_bear_path` whose LAST element is the
  served P(bear); the per-date phase is the SAME `_phase_for(_severity_reading)`). Bounded to the
  most-recent `observation_disclosure_limit` tail; `total_timeline_dates` discloses the full causal count.
- **J-89 dated causal downtrend episodes** — `episodes`: a deterministic grouping of the (≤ D) timeline
  into maximal Bear/Correction runs (or P(bear) ≥ the new config `downtrend_pbear_threshold`); each
  `{first_trigger_date, severity_at_trigger, last_date, peak_p_bear, peak_severity, open}` is observed on
  its dates only. Empty/early history → honest empty list. `open` = still in the downtrend at D.
- **J-90 causal recovery/turn signal** — `recovery_turn`: `{is_recovery_turn, reason, p_bear, prev_p_bear,
  exit_threshold, ma_reclaimed, ma_window_days}` for the resolved as-of, computed from data ≤ D only (a
  fresh filtered-P(bear) cross below the new config `recovery_signal_pbear_exit` confirmed by the index
  reclaiming its trailing MA over the new config `recovery_trailing_ma_days` window). Explainable — never a
  bare flag.
- **J-89 FENCED retrospective** — a NEW SEPARATE `compute_retrospective(...)` + `retrospective_cached(...)`:
  the full-sample SMOOTHED P(bear) (a Hamilton-Kim backward smoother over the SAME `config.regime_switching`
  params VERBATIM — lookahead by construction) + a peak-to-trough "true bear dating" (a Bry-Boschan/NBER-
  style dater over the index closes, censored by the new config `bry_boschan_min_phase_days` +
  `bry_boschan_min_amplitude_pct`). Served ONLY behind the `retrospective` field when the endpoint is called
  with `?retrospective=true`. STRUCTURAL FENCE: no causal function reads anything this path produces.
- **J-90 Recovery-Turn Edge study** — `compute_recovery_turn_edge(...)` + `recovery_turn_edge_cached(...)`
  in `app/engine/research.py`: pools the stored `forward_returns` (realized return + MAE/MFE +
  `max_drawdown`, read VERBATIM) of the CAUSAL recovery-turn signal dates (from the read-only
  `market_phase.recovery_turn_dates` derivation — never recomputed), tagged with the causal phase/severity/
  P(bear) at the signal date. Reports per `config.walk_forward.horizons` the forward-return distribution +
  expectancy + mean MAE/MFE + aggregate max-drawdown + downside-only risk-adjusted, plus a by-signal-phase
  conditioning slice. Honors `view` Episodes⇄Pooled (J-63) and `as_of` (J-32). Low-sample → NA + n.
- **J-90 samples drill-down** — a new `recovery-turn` `kind` in `app/engine/samples.py` reproducing the
  cohort from the SAME `_recovery_turn_observation_set` builder, so each `N=` chip's drill-down `total`
  EQUALS the published `n` in BOTH Episodes/Pooled and BOTH All-history/As-of (count-coherence keystone).
- **Endpoints** — `GET /api/market-phase` gains `?retrospective=true` (the fenced sibling read) + the
  additive causal fields; NEW `GET /api/research/recovery-turn-edge` (horizon/view/as_of); `GET
  /api/research/samples` widened to the `recovery-turn` kind (slice total|phase + a `phase` selector).
- **Config** — NEW typed/validated `market_phase` keys: `downtrend_pbear_threshold`,
  `recovery_signal_pbear_exit` (validated ≤ downtrend threshold + in [0,1]), `recovery_trailing_ma_days`,
  `bry_boschan_min_phase_days`, `bry_boschan_min_amplitude_pct` (all positive). `market_phase.py` stays in
  `test_no_magic_numbers`'s `CALC_FILES` (no threshold literal). NO new top-level config section. NO new
  DB table — the causal cache reuses `MarketPhaseCache` (a namespaced `retro:<date>` key for the
  retrospective); the edge study reuses `EventStudyCache` under a `__recovery_turn_edge__` sentinel subject.

### Frontend

- **`components/market-phase-card.tsx`** (Dashboard `/`): the existing Market-Phase panel gains (a) the
  J-89 per-date phase + filtered-P(bear) step-function timeline (SVG band + line + an as-of marker), (b)
  the dated causal downtrend-episode list (first-trigger → last, severity-at-trigger, open/closed badge),
  (c) the J-90 recovery-turn signal line (explainable badge + reason), and (d) the FENCED retrospective
  sub-view toggle (a "Retrospective (full-sample / analysis-only)" panel showing the smoothed P(bear) +
  peak-to-trough true-bear dating, visibly fenced — only fetched when toggled on). NO new date `useState`,
  NO window/document keydown listener (keeps `useAsOf()` as the only date source — J-18 by construction).
- **`app/research/page.tsx`** (`/research`): a NEW `RecoveryTurnEdgeLab` section appended after the
  Regime×Setup×Pattern lab — its own read-only data source, an Episodes⇄Pooled view toggle, the per-horizon
  edge table (reusing the event-study cell renderer: distribution + expectancy + MAE/MFE + aggregate MDD +
  downside risk-adjusted), a client-side-sortable by-signal-phase table, the survivorship-bias label, and
  `N=` chips opening the count-coherent samples drill-down in a NEW tab (J-65). No order/execution affordance.
- **`app/research/samples/page.tsx`**: the drill-down's cohort header now describes the `recovery-turn`
  cohort (view + total / by-phase).
- **`lib/api.ts`** / **`lib/samples-link.ts`**: new response/cohort types + `fetchRecoveryTurnEdge`;
  `fetchMarketPhase(asof, signal, retrospective)`; the recovery-turn cohort serialization for the chip→
  drill-down link.

## Files Changed

- `apps/backend/app/engine/market_phase.py` -- timeline/episode/recovery-turn derivations + the FENCED
  backward-smoother + peak-to-trough true-bear dater + `recovery_turn_dates` accessor + `retrospective_cached`.
- `apps/backend/app/engine/research.py` -- `compute_recovery_turn_edge` + `_recovery_turn_observation_set`
  (shared with the drill-down) + `recovery_turn_edge_cached`.
- `apps/backend/app/engine/samples.py` -- `KIND_RECOVERY_TURN` + `_recovery_turn_samples` + dispatch + `phase` selector.
- `apps/backend/app/api/market_phase.py` -- `?retrospective=true` flag.
- `apps/backend/app/api/research.py` -- `GET /api/research/recovery-turn-edge` + the `recovery-turn` samples kind/selectors.
- `apps/backend/app/config.py` -- five new validated `MarketPhaseCfg` keys.
- `config.yaml` -- the new keys under the existing `market_phase:` block (real values).
- `apps/backend/tests/test_market_phase.py` -- 16 new FAST synthetic tests (tail-invariance, the fence, byte-identity, determinism, config validation).
- `apps/backend/tests/test_research.py` -- 6 new recovery-turn-edge tests (count-coherence Episodes×Pooled, verbatim reads, as-of scoping, error cases).
- `apps/backend/tests/test_config.py`, `test_config_engine.py`, `test_indexes.py`, `test_sectors.py`, `test_themes.py` -- the new `market_phase` keys added to all 5 inline from-scratch config dicts.
- `apps/backend/tests/test_no_magic_numbers.py` -- unchanged (market_phase.py already in CALC_FILES; the new keys are config-sourced).
- `apps/frontend/components/market-phase-card.tsx`, `apps/frontend/app/research/page.tsx`, `apps/frontend/app/research/samples/page.tsx`, `apps/frontend/lib/api.ts`, `apps/frontend/lib/samples-link.ts`.

## Tests Run

Command (backend, targeted): `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
- `tests/test_market_phase.py` (fast synthetic, no seed boot): 30 passed (timeline/episode/recovery tail-invariance, the FENCE, filtered byte-identity, smoothed-vs-filtered, true-bear censoring, determinism, the 5 new config-validation tests).
- `tests/test_research.py -k recovery_turn`: 6 passed (count-coherence total==n in Episodes & Pooled, by-phase coherence, verbatim reads, as-of scoping, unknown-view + invalid-phase 4xx).
- `tests/test_no_magic_numbers.py`: 2 passed.
- `tests/test_config.py` + `tests/test_config_engine.py`: 99 passed. The `test_indexes/sectors/themes` inline config dicts each build a valid `Config` with the new keys (verified directly).
- Frontend gate: `cd apps/frontend && npx tsc --noEmit` → exit 0 (clean typecheck).

**FULL backend pytest suite:** handed to the pump nohup-async (`/tmp/iter30_full_suite.log`) per the iter-11
lesson — NOT blocking the evaluator dispatch. The targeted modules above (incl. the no-magic-numbers gate,
the five byte-equality-prone config-fixture suites, and the recovery-turn count-coherence) are green. NOTE:
there is NO `*_equals_engine_output` byte-equality guard on `/api/market-phase` in `test_api_engine.py`
(it is a new endpoint), so the additive fields trip no existing guard.

## Live verification (real backend on :8835, the 1369-run daily-history host)

- `GET /api/market-phase` (latest, 2026-06-16) → phase=Expansion, p_bear=0.0027; **timeline 60 of 1170
  dates; 11 dated causal episodes** (the 2022 bear shows as `2022-04-08→2023-02-01`, peak P(bear)=1.0,
  closed); recovery_turn=False (calm tape). **Byte-identity verified: served p_bear == timeline[-1].p_bear.**
- `?as_of=2022-10-07` → phase=Bear, severity=92.45, p_bear=0.999958 (UNCHANGED from iter-29 — J-87/J-88
  byte-identity); the 2022 downtrend episode is **open** at that as-of; recovery_turn=False (P(bear)=1.0).
- `?as_of=2021-01-05` (early) → available=False, empty timeline/episodes, recovery_turn unavailable (honest).
- `?retrospective=true` → analysis_only=True; smoothed 60 of 1170; **true-bear dated `2022-01-03→2022-10-12`,
  −24.5% over 282 days** (matches the seed's documented SPY ~−24.5% 2022 bear). FENCE confirmed: the causal
  payload carries NO smoothed/true_bear key.
- `GET /api/research/recovery-turn-edge` → **6 causal recovery-turn signal dates** incl. the 2022→2023 turn
  (`2023-02-02`); n=725 @ 20d, mean +2.22%, 52% positive, mean MDD −12.2%, return/downside-dev 0.26;
  by-phase: Pullback 243 + Recovery 482 = 725. **Count-coherence verified LIVE: drill-down total == n in
  BOTH Episodes (725) and Pooled (725), and the Recovery by-phase slice (482).**
- Error cases: recovery-turn-edge bad view/horizon→422, bad as_of→422, future as_of→400; samples bad
  phase→422, valid total→200; market-phase bad as_of→422, future as_of→400.

## Known Issues / Limitations

- **Stale cache on first read after deploy (intended cache contract):** the daily-history host had iter-29
  `MarketPhaseCache` rows keyed to the current `dataset_version` (which has NOT changed), so the FIRST read
  of an as-of served the OLD iter-29 payload (no timeline/episodes/recovery_turn). This is the documented
  same-dataset_version → same-payload contract; in production it self-heals on the next backfill/removal.
  For QA verification I cleared the `MarketPhaseCache` table once (a pure derived cache — safe to clear, not
  a snapshot). **Operator note: if the timeline/episodes are absent on a host with pre-iter-30 cache rows,
  clear `MarketPhaseCache` (or trigger any dataset change) once to force a fresh compute.** No correctness
  impact — a fresh compute is byte-identical and carries the new fields.
- **Cold-compute latency on the daily-history host:** a fresh causal compute is ~30–55s (it was contended by
  the concurrent background warm-up during QA); the retrospective smoother adds ~30s; both are CACHED behind
  the dataset_version stamp, so every subsequent read is sub-second. The panel shows a loading skeleton; the
  retrospective sub-view is OFF by default so the heavy smoother runs only when the user opts in. On the
  committed test seed the compute is instant. No correctness impact.
- **Retrospective is "full-sample WITHIN the resolved window":** for a historical as-of D the retrospective
  reads runs ≤ D only (never a run dated > D), so it is the full-sample analysis over the window up to D —
  future-aware WITHIN that window, fenced from every as-of value, never reading beyond D.
- **The macro (FRED) leg stays off** (J-92 deferred): every figure is byte-identical to the price/breadth/
  ^VIX-only path.
