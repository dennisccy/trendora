# Goal Iteration 30 — Market-phase history timeline + fenced retrospective view (J-89) and causal recovery-turn signal + edge study (J-90)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 30
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-89, J-90
- **Required-still-passing journeys:** J-87, J-88, J-06, J-07, J-18, J-43, J-50, J-32, J-63, J-72, J-44, J-49, J-51, J-65
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. Chart **visualization** MAY render bars dated > D strictly as a labelled forward/after-as-of display; this display path MUST NOT feed any score, bucket, setup status, pattern flag, factor value, or ranking — all of which remain computed from bars with date ≤ D. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **Exactly one date selector** (coherence invariant 5) — the global as-of control drives every date-scoped page; `?asof` (J-43) is its SERIALIZATION, never a second state; the Research As-of ⇄ All-history toggle is a MODE, not a second date state.
  - **Honest limitations surfaced.** Breadth/new-high-low metrics from the seed universe MUST be labelled "universe-relative"; walk-forward evidence MUST be labelled as carrying survivorship bias.
  - **Honest forward-test for partial windows.** Show NA/partial + sample size for horizons/cohorts lacking enough samples — never fabricate or extrapolate a return to fill a gap.

## GOAL

Give the user a market-phase HISTORY view — a per-date timeline of the J-87 phase + J-88 filtered P(bear) with dated causal downtrend episodes and a clearly-fenced retrospective (smoothed) "true bear dating" sub-view — and a causal recovery/turn signal on the Market-Phase panel whose forward-return edge is studied in a new read-only Research lab.

## BACKGROUND

iter-29 shipped the foundational market-phase layer J-87 (phase + 0-100 severity) and J-88 (deterministic forward Hamilton FILTERED P(bear)) as a strictly-causal, read-only, additive derivation served by the cached `GET /api/market-phase` (the evaluator + coherence both confirmed it touches no canonical score/gate). iter-29's eval and recommendation both call for the **J-89 + J-90 cluster at FULL depth** — both consume that layer, both are offline-provable against the committed seed (the 2022 bear ≈ −24.5% SPY peak-to-trough + the 2022→2023 recovery turn), and neither is data-walled. They cross backend (new derivations in the SAME `market_phase` engine + a new Research study + samples builder + new endpoints) and frontend (a Dashboard timeline overlay + a fenced retrospective sub-view + a new `/research` lab), touch the full pytest gate, and warrant the audit step — hence FULL depth.

The keystone discipline for this cluster is the FILTERED-vs-SMOOTHED fence: the served live value is the FILTERED (forward, causal) P(bear) the panel already computes; the SMOOTHED (full-sample) probability is lookahead by construction and MUST live ONLY on the J-89 retrospective surface, visibly fenced as analysis-only, never feeding any as-of score / signal / episode / study-conditioning tag (the J-49 "full-history market context never looks ahead" precedent). The existing engine already computes `_filtered_bear_path` (the per-step causal series) and discloses a bounded observation tail — J-89's timeline reads the SAME single derived series; the smoothed path is a NEW backward pass surfaced only on the retrospective sub-view.

## IN SCOPE

### Backend

- [ ] **J-89 timeline series (causal):** In `app/engine/market_phase.py`, add a single read-only derivation that returns, for the resolved as-of D, the per-snapshot-date series of `{date, phase, p_bear}` — the SAME per-date FILTERED values the existing `_filtered_bear_path` + `_phase_for` already produce (the timeline and the panel read ONE derived series, never a second computation). Clamp to dates ≤ D for the clamped consumer (J-45 semantics).
- [ ] **J-89 causal downtrend-episode dating:** add a deterministic grouping of the causal (≤ D) per-date phase / P(bear) into maximal Bear/Correction runs (or P(bear) ≥ a NEW config `market_phase.downtrend_pbear_threshold`), each episode carrying first-trigger date, the as-of severity at trigger, and still-open/closed state at D. Each episode is observed at information available on its dates only (no future bar). Empty/early history → honest empty episode list (never a fabricated episode).
- [ ] **J-89 retrospective (smoothed) view — FENCED:** add a NEW backward smoother pass over the SAME committed-config 2-state Markov params (`config.regime_switching`) producing the per-date SMOOTHED P(bear), plus a peak-to-trough Bry-Boschan/NBER-style "true bear dating" over the index closes. This is served ONLY on a clearly-labelled retrospective endpoint/field and is NEVER consumed by `compute_market_phase`, the live panel value, the episode dating, J-90's signal, or any study conditioning.
- [ ] **J-89 serving:** serve the causal timeline series + causal episodes from the SAME `GET /api/market-phase` cached payload (additive fields beside the existing phase/severity/p_bear) OR a sibling cached read under the SAME `market_phase` engine + `dataset_version` stamp; serve the retrospective smoothed series + true-bear dating behind a SEPARATE, explicitly-named field/endpoint (e.g. `retrospective`) so the fence is structural, not just a label. Reuse the SAME `_dataset_version` cache key (single-sourced, J-72) — no second cache mechanism.
- [ ] **J-90 causal recovery/turn signal:** In `app/engine/market_phase.py`, add a config-defined downtrend-exit transition computed for D from data ≤ D only (e.g. phase leaves Bear/Correction, OR filtered P(bear) crosses below a NEW config `market_phase.recovery_signal_pbear_exit` while the index reclaims a trailing MA whose window is a NEW config key) — every threshold from config, no magic numbers. Surface it (boolean + its triggering reason) on the SAME `GET /api/market-phase` payload (additive, explainable — never a bare flag).
- [ ] **J-90 Recovery-Turn Edge study (Research):** add a NEW read-only study `research:compute_recovery_turn_edge` (or a sibling in a dedicated module) that, for each recovery-signal date, reads VERBATIM the stored append-only `forward_returns` (realized return + MAE/MFE + `max_drawdown`) via the SAME observation-builder discipline `compute_event_study` uses, joined to `scanner_results`/`scanner_runs`, with each observation tagged with the CAUSAL as-of phase/severity/P(bear) at the signal date (read from the SAME read-only market-phase derivation, ≤ D, never recomputed). Reports per `config.walk_forward.horizons` (no hardcoded list) the forward-return distribution (mean/median/%-positive/expectancy + downside-only risk-adjusted + aggregate max-drawdown). Honors the `view` Episodes ⇄ Pooled mode (J-63) and the `as_of` All-history ⇄ As-of FILTER (J-32 — a mode, not a second date state). Low-sample cohorts → NA + n (min-sample from config). It recomputes NO return/score/regime/signal.
- [ ] **J-90 serving:** a NEW read-only endpoint `GET /api/research/recovery-turn-edge` (`horizon`/`view`/`as_of` params mirroring `/api/research/event-study`).
- [ ] **J-90 samples drill-down (count-coherence):** add a new `kind` to `app/engine/samples.py` `compute_samples` (mirroring `_regime_setup_pattern_samples`) that reproduces the recovery-turn cohort from the SAME shared-membership observation builder, so each `N=` chip drills down via the EXISTING `GET /api/research/samples` and the drill-down `total` EQUALS the published `n` in BOTH Episodes and Pooled modes AND both All-history and As-of scopes (J-51/J-65) — every displayable row resolves without a 4xx (the J-82 lesson).
- [ ] **Config (`config.yaml`):** add the new typed/validated keys under the EXISTING `market_phase` block (downtrend-episode P(bear) threshold; recovery-signal P(bear) exit threshold + trailing-MA reclaim window) with config-validation in `app/config.py` (`MarketPhaseCfg`). No new top-level section unless required. NO threshold literal in any engine module — `market_phase.py` (and any new study module) stays in the `test_no_magic_numbers` `CALC_FILES` list.

### Frontend

- [ ] **J-89 Dashboard timeline overlay:** add a market-phase history timeline overlaying the Dashboard major-indexes/regime card — a per-date band of the J-87 phase + J-88 filtered P(bear) drawn as a step function across snapshot dates using the J-44/J-49 overlay treatment, read from the SAME single served derived series; clamps at the resolved as-of for the clamped consumer while the card may render the full series behind the J-49 as-of marker. Render the dated causal downtrend-episode list (first-trigger date, severity-at-trigger, open/closed).
- [ ] **J-89 fenced retrospective sub-view:** a separate, EXPLICITLY-LABELLED "Retrospective (full-sample / analysis-only)" sub-view showing the smoothed P(bear) + the peak-to-trough true-bear dating, visibly fenced from the as-of path (mirroring the J-49 post-as-of display-only marker treatment). It must read ONLY the retrospective field/endpoint, never the live causal value.
- [ ] **J-90 recovery-turn signal on the Market-Phase panel:** surface the causal recovery/turn signal for the resolved as-of (the boolean + its config-defined triggering reason — explainable, never a bare flag), reading the SAME `GET /api/market-phase` payload.
- [ ] **J-90 Recovery-Turn Edge lab on `/research`:** a new lab section reporting the per-horizon forward-return edge with horizon toggle, Episodes ⇄ Pooled (J-63), As-of ⇄ All-history (J-32), ranked client-side-sortable tables under the J-48 view-transform contract, the survivorship-bias label, and `N=` chips opening the count-coherent samples drill-down in a new tab (J-65). NA + n for low-sample cohorts. No order/execution affordance — forward-return evidence only.

### New user-facing capability

The user can read the FULL HISTORY of market phase + bear-probability as a dated step-function timeline, see when each downtrend episode causally triggered (and whether it is still open at the as-of), inspect a clearly-fenced retrospective "true bear dating" view, see whether the resolved as-of date is a causal recovery/turn, and study the forward-return edge of entering at recovery-turn dates with a count-coherent samples drill-down.

### New information displayed

- A per-date market-phase + filtered P(bear) timeline (step function) over snapshot dates on the Dashboard.
- A dated causal downtrend-episode list (first-trigger date, severity-at-trigger, open/closed at D).
- A fenced retrospective smoothed P(bear) series + peak-to-trough true-bear dating (analysis-only).
- A causal recovery/turn signal + its triggering reason on the Market-Phase panel.
- A Recovery-Turn Edge study (per-horizon forward-return distribution + downside risk-adjusted + aggregate max-drawdown), conditioned on the causal as-of phase/severity/P(bear) at the signal date.

### New user actions

- Toggle the retrospective sub-view on the Dashboard timeline.
- On the new Research lab: horizon select, Episodes ⇄ Pooled toggle, As-of ⇄ All-history toggle, column sort, and `N=` chips → samples drill-down in a new tab.

### UI surface changes

- Dashboard (`/`): the existing Market-Phase panel / major-indexes card gains the timeline overlay + episode list + the fenced retrospective sub-view + the recovery-turn signal line.
- Research (`/research`): a new Recovery-Turn Edge lab section (existing home, no new top-level nav).
- Samples (`/research/samples`): the existing drill-down gains the recovery-turn cohort (link-reached).

### Product surface delta

The Dashboard moves from a single-date phase snapshot to a phase HISTORY with dated episodes and an honest retrospective overlay; Research gains a downtrend-recovery edge study. No canonical stock score, bucket, setup, pattern flag, regime, or the Risk-Off→Actionable gate changes; no new date control is introduced.

### Blueprint conformance

All surfaces land on EXISTING Information-Architecture homes (per blueprint): J-89 on Dashboard (`/`), J-90's signal on the Dashboard Market-Phase panel and its study on Research (`/research`) with the drill-down on the existing `/research/samples`. NO new top-level nav section and NO new page (the SESSION EXTENSION 2026-06-17 J-87..J-96 note: "J-87..J-92 land on the EXISTING Dashboard + Research homes"). The fenced-retrospective discipline matches the registered blueprint rule: "the served bear-probability is the FILTERED (causal) Hamilton value while the SMOOTHED (full-sample) probability is lookahead and may appear ONLY on the J-89 retrospective surface (the J-49 fenced-context precedent)."

### Data-contract additions

These are registered in `blueprint.md` (Data Contract) as additive rows/annotations under the EXISTING `market_phase` engine + `GET /api/market-phase` canonical source (no second computing module, no duplicate of the J-87/J-88 phase/severity/P(bear) values — the timeline reads the SAME single derived series):

1. **Market-phase history timeline series (J-89)** — per-snapshot-date `{date, phase, p_bear}` (the FILTERED causal series). Computed by: `market_phase` engine (the SAME `_filtered_bear_path` + `_phase_for`). Served by: `GET /api/market-phase` (additive field or sibling cached read under the same engine + `dataset_version`).
2. **Causal downtrend episodes (J-89)** — dated `{first_trigger_date, severity_at_trigger, open|closed}`. Computed by: `market_phase` engine (deterministic causal grouping of the timeline series). Served by: `GET /api/market-phase`.
3. **Retrospective smoothed P(bear) + true-bear dating (J-89, FENCED)** — full-sample smoothed series + peak-to-trough dating. Computed by: `market_phase` engine (a NEW backward smoother pass over the SAME `config.regime_switching` params + a peak-to-trough dater). Served by: a SEPARATE explicitly-named retrospective field/endpoint — NEVER fed into any as-of value (lookahead by construction; J-49 fence).
4. **Causal recovery/turn signal (J-90)** — `{is_recovery_turn, reason}` for the resolved as-of (≤ D). Computed by: `market_phase` engine (config-defined downtrend-exit). Served by: `GET /api/market-phase`.
5. **Recovery-Turn Edge study (J-90)** — per-horizon forward-return distribution (mean/median/%-positive/expectancy + downside risk-adjusted + aggregate max-drawdown) over recovery-signal-date observations, tagged with the causal phase/severity/P(bear) at the signal date. Computed by: a NEW read-only study (`research:compute_recovery_turn_edge`) reading VERBATIM the stored `forward_returns` + the read-only market-phase derivation — recomputes nothing. Served by: `GET /api/research/recovery-turn-edge`; the `N=` drill-down via the EXISTING `GET /api/research/samples` (new `kind`).

No NEW way to compute or fetch any value already in the Data Contract: phase / severity / filtered P(bear) are read from the registered `market_phase` engine; realized forward returns / MAE / MFE / `max_drawdown` are read VERBATIM from the stored append-only `forward_returns` (the same data Backtest/J-21/J-75/J-81/J-86 read); the regime/breadth inputs stay read VERBATIM from the stored `ScannerRun`.

## OUT OF SCOPE

- J-91 (downtrend-conditioned three-angle opportunity study) — the NEXT iteration; this iteration only delivers the J-90 recovery-turn edge that J-91 later surfaces in its panel.
- J-92 (FRED macro feed + `MacroSeries` table) — a later iteration; the macro-z observation leg stays off (config-default-off) so every figure is byte-identical to the price/breadth/VIX-only path.
- J-93/J-94/J-96 (dynamic point-in-time universe) and J-95 (data-walled backward-history/constituent envelope) — later cluster; no universe-membership change here.
- Any change to a canonical stock score, A–E bucket, setup status, pattern flag, regime score/label, or the Risk-Off→Actionable gate.
- Any new snapshot column or any snapshot rebuild (J-89/J-90 are strictly read-only derivations over stored snapshots + bars ≤ D; the cache is the existing standalone `MarketPhaseCache` / `event_study_cache` pattern).
- EM-fitting the Markov params at serve time (both the filtered and the new smoothed pass read `config.regime_switching` VERBATIM).
- Serving the SMOOTHED probability on any live/as-of path (it is permitted ONLY on the fenced retrospective sub-view).

## DEFINITION OF DONE

- [ ] Target journeys J-89, J-90 pass via browser-qa-agent (live Dashboard timeline + fenced retrospective sub-view; live `/research` Recovery-Turn Edge lab with horizon/Episodes-Pooled/As-of toggles + a count-coherent `N=` drill-down).
- [ ] Required-still-passing journeys remain green — especially J-87/J-88 (the consumed layer stays byte-identical and causal: the served FILTERED P(bear) for any date is unchanged), J-06/J-07 (no canonical regime/gate change), J-18/J-43/J-50 (single date selector + `?asof`), J-32/J-63 (mode toggles, not second date states), J-72 (shared cache machinery), J-51/J-65 (count-coherent drill-down).
- [ ] No anti-goal violation introduced — in particular: SMOOTHED never feeds an as-of value (fenced); episodes/signal computed from ≤ D only (no-lookahead tail-invariance unit-asserted exactly as `forward_return`/`forward_excursions` are); no magic number in any engine module; recovery-turn edge recomputes nothing (reads stored `forward_returns` verbatim); no order/execution path on the weakness/short angle (N/A this iter — J-90 is recovery-only, descriptive evidence).
- [ ] Unit/integration tests pass; the FULL backend pytest suite reaches a FLUSHED `0 failed, EXIT 0` (handed to the pump nohup-async — NEVER block the evaluator dispatch on the in-flight suite; iter-11 lesson). No regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-30-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by ID):**
  - J-89 — Dashboard timeline renders the per-date phase + filtered P(bear) step function over snapshot dates; the 2022 bear appears as ONE dated causal episode (first-trigger date + severity-at-trigger + open/closed at D); the fenced "Retrospective (full-sample / analysis-only)" sub-view shows the smoothed series + peak-to-trough true-bear dating and is visibly labelled analysis-only; under a historical as-of D the causal timeline/episodes render only dates ≤ D while the retrospective is the only future-aware surface; an early as-of (e.g. 2021-01-05) yields an honest empty timeline.
  - J-90 — the Market-Phase panel surfaces the causal recovery/turn signal + reason for the resolved as-of; the `/research` Recovery-Turn Edge lab reports the per-horizon forward-return edge (with downside risk-adjusted + aggregate max-drawdown), the horizon / Episodes⇄Pooled / As-of⇄All-history toggles re-point consistently, columns sort, the survivorship-bias label shows, and an `N=` chip opens the samples drill-down in a new tab with total == published n (verify in BOTH Episodes and Pooled, BOTH All-history and As-of).
  - Required-still-passing smoke: J-87/J-88 (panel phase/severity/filtered-P(bear) unchanged for the same date), J-01, J-06, J-18 (CRITICAL — exactly one date selector, the new panel/lab adds NO date useState and NO window/document/keydown listener), J-43/J-50 (`?asof`), J-13 (browse past date), J-44/J-49 (major-indexes card), J-07 (Risk-Off zero Actionable — gate unchanged).
- **Unit/integration (what code paths must have tests):**
  - No-lookahead tail-invariance for the timeline series, the causal episode dating, and the recovery-turn signal: removing bars/runs dated > D never changes any value at a date ≤ D (the `forward_return`/`forward_excursions` idiom).
  - The FENCE: the SMOOTHED probability and the true-bear dating are NOT read by `compute_market_phase`'s live phase/severity/filtered-p_bear, the episode dating, the recovery-turn signal, or the recovery-turn edge study (assert no code path from the retrospective field into an as-of value).
  - Filtered series byte-identity: the per-date filtered P(bear) the timeline serves equals the existing `_filtered_bear_path` value at each date (single source — the panel and the timeline read ONE series); J-87/J-88's served P(bear) for any date is unchanged.
  - Recovery-turn edge count-coherence: the samples drill-down `total` EQUALS the published `n` for the same cohort SAME-INSTANT in BOTH Episodes and Pooled and BOTH All-history and As-of; the edge figures are read VERBATIM from the stored `forward_returns` (no recompute).
  - Determinism: fixed config params + fixed seed → byte-identical timeline / smoothed / episode / signal / edge outputs.
  - Config validation: the new `market_phase` threshold keys are typed/validated (positive / in-range) and rejected when malformed at load. Add the new keys to EVERY inline test config dict and every config-narrowing script (`build_qa_fixture_db.py`, `apply_universe_to_config.py`) — grep the new key across `apps/backend/tests` AND scripts (iter-11/config-fixtures lesson).
  - Guard tests: `test_no_magic_numbers` stays green for `market_phase.py` + any new study module (add new calc modules to `CALC_FILES`); `test_db.py::test_create_all_produces_expected_tables` stays green (NO new table expected — reuse the existing cache; if a new `kind`/endpoint needs a stored cache, prefer the existing `event_study_cache`/`MarketPhaseCache` pattern and register any new standalone table in the expected-tables set, iter-20 lesson). If ANY additive field is attached to a payload covered by a `served == engine_output` byte-equality guard in `test_api_engine.py`, update that guard IN THE SAME ITER (strip-the-additive-key, keep the canonical equality — iter-23/24 lesson).
- **Error cases:**
  - Invalid `as_of` on `GET /api/market-phase` / `GET /api/research/recovery-turn-edge` → 4xx/503 via the SAME shared `resolved_date` resolver (unparseable → 422, out-of-range → 400, no data → 503) — never a fabricated date.
  - Invalid `view`/`horizon` on the new study + samples kind → 4xx (mirror the event-study/RSP validation); a genuinely non-emitted recovery-turn cohort → honest 4xx, but EVERY displayable row's `N=` chip resolves without a 4xx (J-82 lesson — validation reconciled to the set the study actually emits).
  - Insufficient-history as-of → honest empty timeline / NA phase&p_bear / NA edge cohorts (NA + n), never a fabricated episode/probability/return.

## NOTES

- **Lessons applied (surfaced for dev/reviewer/evaluator):**
  - **iter-16 / iter-29 (CRITICAL — exactly one date selector):** the cheap decisive check is static — grep the new Dashboard panel/timeline + the new Research lab diff for `window/document.addEventListener` keydown (must be NONE) and confirm the panel keeps only component-internal useStates (`data`/`status`-style) reading the SINGLE global as-of via `useAsOf()`; NO new date `useState`. J-18 is guarded by construction.
  - **iter-29 (daily-history host test split):** any `test_market_phase.py` test using the seed-loading `loaded_engine` fixture boots the heavy backend (~1369 daily runs) and cannot finish under a subagent Bash cap — split FAST synthetic + config-validation tests (no-lookahead tail-invariance, the fence, determinism, count-coherence on injected fixtures, config validation) from the slow seed-boot tests; verify every anti-goal-critical leg via the fast set in ~20s; on this GOAL_ACHIEVED-bound cluster additionally require the FLUSHED full-suite `0 failed, EXIT 0` via a `nohup`-launched run through the pump. `exit=137` in a `/tmp/*suite*.log` is the known background-helper SIGKILL, NOT a test failure.
  - **iter-11 / iter-20 / iter-21 (full-suite guard traps):** run the FULL suite, not just targeted modules, before any GOAL_ACHIEVED candidacy — `test_no_magic_numbers` blanket-forbids EVERY float/int literal in `CALC_FILES` (source any sentinel/threshold from config or a named constant — e.g. the Bry-Boschan minimum-phase-length / drawdown-amplitude cutoffs must be config keys, not literals), and `test_db::test_create_all_produces_expected_tables` fires on any new `table=True` model.
  - **iter-23 / iter-24 (additive served field trips byte-equality guards):** if any J-89 timeline/episode field is attached additively to `GET /api/market-phase` (or any scored endpoint), grep `apps/backend/tests` for `== expected` / `equals_engine_output` byte-equality asserts on that payload and reconcile them in the SAME iteration (strip the additive key, keep the canonical equality, separately assert the field's shape).
  - **iter-3 / iter-7 / iter-18 (evidence hygiene):** md5sum the QA evidence dir FIRST; the Dashboard market-phase panel sits below the fold (~1060px) — scroll the timeline + the retrospective sub-view into view and capture full-viewport, then VIEW the pixels; a blank/duplicate frame is a rejected capture (corroborate with live DOM/computed-CSS or the live endpoint + targeted tests when a capture degrades). For the recovery-turn edge `N=` drill-down, resolve sort/header buttons by `aria-label`, not visible `text()` (iter-27/28 selector false-negative lesson).
  - **iter-1 (frontend gate):** ESLint is not installed in `apps/frontend` — use `tsc --noEmit` as the frontend gate, not `npm run lint`.
- **Evaluator-feedback driver:** iter-29 eval "Next-Step Recommendation" explicitly scopes J-89 + J-90 at FULL depth and names the FILTERED-vs-SMOOTHED fence (J-89 smoothed behind a clear future-aware marker per the J-49 precedent, never feeding an as-of value) and the offline-provability (2022 bear + 2022→2023 recovery + `^VIX`).
- **Not a GOAL_ACHIEVED candidate** by itself: goal.md still queues buildable Must-haves J-91/J-92 (offline/partly-data-dependent legs) + J-93/J-94/J-96 (and J-95's data-walled envelope) with no positive evidence (iter-22 lesson — diff goal.md's Must-have IDs against journey-history before considering done). J-22/J-23/J-24 remain honestly blocked-NA (non-vetoing).
