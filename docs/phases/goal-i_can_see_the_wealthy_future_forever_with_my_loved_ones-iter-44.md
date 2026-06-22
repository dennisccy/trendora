# Goal Iteration 44 — Dashboard cross-view cleanup + served severity-velocity line (J-101 + J-102)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 44
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-101, J-102
- **Required-still-passing journeys:** J-97, J-98, J-87, J-88, J-89, J-90, J-44, J-49, J-06, J-18, J-07
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. Chart **visualization** MAY render bars dated > D strictly as a labelled forward/after-as-of display; this display path MUST NOT feed any score, bucket, setup status, pattern flag, factor value, or ranking — all of which remain computed from bars with date ≤ D — and the moving-average lines drawn past D are visualization only, never as-of signals. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Exactly one date selector.** The global as-of control drives every date-scoped page; `?asof` is its serialization, never a second state. *(critical — invariant 5)*
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.

## GOAL

On the Dashboard, the user sees exactly one market chart (the duplicate Major-indexes card is gone), the cross-view's phase pane bands span the full history at any as-of, and the phase pane now plots a zero-centered severity-velocity line (replacing the low-signal P(bear) line) while the hover tooltip gains the market-regime label + score.

## BACKGROUND

This is an in-place resume after the iter-43 GOAL_ACHIEVED. `docs/goal.md` (commit touching the goal doc, 2026-06-22) appended four new buildable Must-haves J-101..J-104, none of which has a `journey-history.json` entry yet — so per the **iter-22 lesson** ("every journey in journey-history is green" is NOT GOAL_ACHIEVED when goal.md has queued new buildable Must-haves; diff the goal's Must-have IDs against journey-history) the goal is NOT achieved and the prior verdict's halt does not apply. goal.md:2379-2387 states J-101..J-104 are NOT data-dependent — all four are buildable/verifiable offline against the committed 2021-2026 seed; none may be recorded blocked-NA, none may halt the loop.

This iteration takes the cohesive Dashboard cross-view cluster **J-101 + J-102** (the larger research-labs cluster J-103 + J-104 follows next iteration). Depth is **full**: it crosses backend (a new `severity_velocity` field on the cached market-phase timeline + a `SCHEMA_VERSION` cache-key bump + a new typed config window) and frontend (chart re-format + tooltip + a full-history display-clamp alignment + a duplicate-card removal), touches a config-validated block, and requires new unit tests beyond a browser smoke — the full 11-step pipeline + the flushed-GREEN pytest gate apply. `Frontend Present: yes` so browser-QA captures the live render in the SAME iteration (the iter-43 lesson: do not split a render-bearing change into a backend-only iter + a follow-up verify iter).

## IN SCOPE

### Backend
- [ ] Add a new typed/validated lookback-window key to the EXISTING `config.market_phase` block (e.g. `severity_velocity_window`, **default 5 snapshots**) in `apps/backend/app/config.py` (`MarketPhaseCfg`), validated positive at load — NO magic-number literal in any engine module (the lookback comes from config; the module still passes `test_no_magic_numbers`). Add the key to `config/config.yaml` (and any inline test config dicts — see NOTES, the config-fixtures lesson).
- [ ] In `apps/backend/app/engine/market_phase.py` `_timeline_series` (line ~380), ADDITIVELY compute a per-date **`severity_velocity`** = the deterministic config-windowed slope of the served 0-100 `severity` over the prior `severity_velocity_window` snapshots, sign **positive = severity worsening**; **strictly causal** (severity at dates ≤ each date only); **NA** at the warm-up head where the window is unavailable; never smoothed with future data. Add `severity_velocity` to each point of `timeline_full` (and therefore the bounded `timeline` tail) — read VERBATIM from the SAME single derived series; no second computation.
- [ ] Bump `SCHEMA_VERSION` `"s1"` → `"s2"` at `apps/backend/app/engine/market_phase.py:797` so `_cache_version` (line ~800) refreshes EVERY `MarketPhaseCache` row to the new shape — a stale pre-iter-44 row (missing `severity_velocity`) must never be served (the iter-38/39 cache-schema discipline). Mirror to the `retrospective` cache path if it shares the same schema risk.
- [ ] DO NOT change any canonical score, regime label/score, the filtered/smoothed P(bear) values, the J-89 episode/retrospective fence, the J-90 recovery signal, or the Risk-Off→Actionable gate. `severity_velocity` is a NEW additive timeline field only.

### Frontend
- [ ] **J-101 (a):** In `apps/frontend/app/page.tsx`, REMOVE the standalone `<MajorIndexesCard />` (line ~158) and its import — the J-97 `<PhaseCrossViewCard />` pane 0 already IS that chart, reading the SAME `/api/indexes?full=true` + `/api/regime-history?full=true` series. The Dashboard now renders exactly one market chart.
- [ ] **J-101 (b):** In `apps/frontend/components/phase-cross-view-chart.tsx` (and the phase-band primitive), ensure the bottom phase pane's bands span the FULL stored history at any as-of — the phase-band primitive's clip stays `null` and `timeline_full` is fetched UNFILTERED by the global as-of (mirroring how the top pane already serves the regime bands full-history via `/api/regime-history?full=true`, J-49). The selected as-of renders ONLY as the marker; stored history dated after D is display-only behind the marker and feeds no as-of-scoped value. An honest-empty timeline → honest-empty phase pane (no fabricated band).
- [ ] **J-102 (chart):** In `phase-cross-view-chart.tsx`, REMOVE the plotted filtered-P(bear) line (lines ~200-213, the `PBEAR_SCALE_ID` overlay series) and draw a ZERO-CENTERED `severity_velocity` line on that retired overlay scale slot (with a 0 reference) so the index % lines stay undistorted.
- [ ] **J-102 (tooltip):** In the cross-view tooltip (`CrossTooltipBox`, lines ~234-288), ADD the stored market-regime **label + 0-100 score** for the hovered date (read VERBATIM from the already-fetched `/api/regime-history` points — Single source of truth, Scores must be explainable) and the served `severity_velocity` value, while RETAINING the existing date, index %, phase, severity, and **P(bear)** rows (only the plotted P(bear) line is removed; the P(bear) value stays in the tooltip).
- [ ] The frontend RE-FORMATS only: it computes no velocity / regime / probability itself. It adds NO second date state (J-18) and changes no canonical value or the as-of contract. The Market-Phase card and the J-98 at-a-glance keep showing P(bear) unchanged.

### New user-facing capability
The Dashboard market view is de-cluttered to a single chart, its phase context now reads consistently across the full history regardless of the selected as-of, and a new severity-velocity line lets the user see at a glance whether market stress is worsening or easing — with the regime status now legible on hover.

### New information displayed
A per-date **severity-velocity** value (zero-centered line + tooltip row; positive = worsening) on the Dashboard cross-view phase pane, and the stored **market-regime label + 0-100 score** added to the cross-view hover tooltip.

### New user actions
None new — hover/zoom/pan on the existing single cross-view chart (the synced two-pane behavior is unchanged). No new control, no new date state.

### UI surface changes
Dashboard `/`: the duplicate Major-indexes & regime card is removed; the cross-view phase pane plots a severity-velocity line instead of the P(bear) line, with full-history bands and an enriched tooltip.

### Product surface delta
The headline daily-snapshot view becomes a single, internally consistent market chart (no duplicate home for the index/regime series) and surfaces a more decision-useful stress-momentum signal, while staying strictly causal and explainable.

### Blueprint conformance
No new surfaces and no nav-skeleton change. Both journeys land on the EXISTING Dashboard `/` home (`blueprint.md` Information Architecture, Dashboard line). The J-97 timeline Data-Contract row was edited additively to register `severity_velocity` on the SAME `market_phase` module + SAME `GET /api/market-phase` endpoint, and the Dashboard nav line notes J-101's duplicate-`MajorIndexesCard` removal. These are additive edits only — no `blueprint.reapproval-requested` is filed.

### Data-contract additions
- **`severity_velocity`** (per-date, on the served market-phase `timeline_full` / `timeline` points) — canonical computing module: `apps/backend/app/engine/market_phase.py` `_timeline_series` (the SAME module that already computes `phase` / `severity` / `p_bear`); serving endpoint: the SAME `GET /api/market-phase` (and `?full=true`). It is an ADDITIVE field on the already-registered J-97 timeline series — NOT a new value computed a second way and NOT a new endpoint. The regime label/score the tooltip adds is read VERBATIM from the already-registered `GET /api/regime-history` series (canonical module `regime_history:get_regime_history`) — no second computation. Registered in `blueprint.md` this iteration.

## OUT OF SCOPE

- J-103 (severity-velocity × regime forward-return study on `/research/severity-velocity`) and J-104 (research-labs caching / query-bounding / lazy-load + page-split) — next iteration (iter-45). This iteration does NOT touch `/research`, `research.py`, the research routes, or the nav skeleton.
- Any change to the Market-Phase CARD or the J-98 at-a-glance summary (they keep showing P(bear) unchanged).
- Any new endpoint, any new snapshot column, any snapshot rebuild, any change to a canonical score/return/regime/gate.
- The J-89 SMOOTHED/retrospective fence and the J-90 recovery signal — untouched.

## DEFINITION OF DONE

- [ ] Target journeys J-101 and J-102 pass via browser-qa-agent on LIVE rendered evidence (Playwright fallback pre-planned; md5sum the evidence dir first; reject any blank/skeleton/byte-identical frame).
- [ ] Required-still-passing journeys remain green (J-97/J-98 Dashboard cross-view + at-a-glance; J-87/J-88/J-89/J-90 market-phase card; J-44/J-49 indexes/regime card; J-06 single source; J-18 exactly-one-date-selector; J-07 Risk-Off gate).
- [ ] No anti-goal violation introduced (no lookahead — severity-velocity strictly causal + NA at warm-up; no magic number — lookback from config; single source — regime in tooltip read from `/api/regime-history`; no second date state; no order/execution path).
- [ ] Unit tests pass; no regressions. The full backend pytest suite flushes `0 failed, EXIT 0` (the standing GOAL_ACHIEVED gate; nohup-async via the pump — never block the evaluator on the in-flight suite).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-dev.md`.

## TESTING REQUIREMENTS

- **Browser (live, Playwright fallback pre-planned):**
  - **J-101:** the Dashboard renders exactly ONE market chart — assert the standalone Major-indexes & regime card is absent (no duplicate). Capture the cross-view phase pane bands spanning the FULL history at a HISTORICAL as-of (bands do not truncate at the as-of marker), plus the honest-empty phase pane at an early-as-of (no fabricated band) — TWO byte-distinct frames.
  - **J-102:** the phase pane plots a zero-centered severity-velocity line (no plotted P(bear) line); the hover tooltip shows the regime label + 0-100 score + severity-velocity AND still retains phase, severity, and P(bear) rows. Capture the tooltip-visible frame.
  - **Required-still-passing live smoke:** J-97 (two synced panes draw, shared axis), J-98 (compact at-a-glance still shows P(bear), expand works), J-87/J-88 (Market-Phase card P(bear) unchanged), J-06 (figures == served), J-18 (0 native `input[type=date]` on `/`), J-07 (Risk-Off → 0 Actionable — API invariant).
- **Unit/integration:**
  - `severity_velocity` is the deterministic config-windowed slope: assert it on a known severity series; assert sign convention (positive = worsening); assert NA at the warm-up head where the window is unavailable.
  - **No-lookahead tail-invariance:** removing bars dated > D does not change `severity_velocity` at any date ≤ D (unit-asserted, mirroring the existing `forward_return`/filtered-P(bear) tail-invariance tests).
  - **Cache-schema correctness (the iter-38/39 keystone):** SEED a genuine OLD-schema (`s1`) `MarketPhaseCache` row with `severity_velocity` STRIPPED (a real cache HIT, NOT a fresh compute), then assert the served `timeline_full` `severity_velocity` is byte-identical to a fresh `compute_market_phase` — proving the `s1`→`s2` bump forces the recompute. Probe the LIVE current as-of (a cache HIT), not a fresh-compute date.
  - **Byte-identity of everything else:** assert `phase` / `severity` / `p_bear` / the J-89 episodes + retrospective fence / the J-90 recovery signal in the served payload are byte-identical to pre-change (severity-velocity is purely additive).
  - `test_no_magic_numbers` stays green (the lookback window is config-sourced); the config-validation legs cover the new key.
- **Error cases:** a non-positive `severity_velocity_window` fails the boot loudly (config validation); an as-of with insufficient history yields NA velocity (never a fabricated slope); an honest-empty timeline yields an honest-empty phase pane (no fabricated band).

## NOTES

- **iter-22 lesson (drives this CONTINUE):** journey-history shows J-01..J-100 all green but has NO J-101..J-104 entry; goal.md:2379-2387 queued them as buildable, non-data-dependent Must-haves, so they are `unknown` Must-haves with no positive evidence — the goal is NOT achieved. Verified by diffing goal.md Must-have IDs against journey-history keys.
- **MarketPhaseCache schema-version trap (memory + iter-38/39 lessons — load-bearing here):** `severity_velocity` is a NEW key in a CACHED payload, invisible at every already-cached key until the cache invalidates. `_dataset_version` tracks DATA changes, not the payload SCHEMA — so the `SCHEMA_VERSION` `s1`→`s2` bump at `market_phase.py:797` (folded into `_cache_version`) is MANDATORY, and the additive field MUST be unit-tested against an ALREADY-POPULATED old-schema row (a real HIT), never a fresh compute that masks the bug. Prove the cache fix by probing an already-populated HIT at the live as-of.
- **Config fixtures need new required keys (memory lesson):** the new `config.market_phase.severity_velocity_window` must be added to EVERY inline test config dict and every config-narrowing script (the count GROWS over time) — grep the new key across `apps/backend/tests` and `apps/backend/scripts` (e.g. `build_qa_fixture_db.py`, `apply_universe_to_config.py`) before declaring done, not a fixed list.
- **Render-evidence + Playwright fallback (iter-38/39/40/43 lessons):** Chrome MCP CDP has emptied the evidence dir on iters 38/39/40/42/43; live evidence was captured only when the Playwright fallback was PLANNED UP FRONT. The browser-qa-agent MUST plan it up front. md5sum the evidence dir FIRST; a differential leg (full-history bands vs as-of marker; the severity-velocity line replacing P(bear)) REQUIRES byte-distinct frames — reject byte-identical "before/after" pairs (the recurring iter-38/39/40 synced-zoom trap).
- **`Frontend Present: yes` is deliberate (iter-43 lesson):** this is a render-bearing change; setting it forces the browser-QA render-capture step in the SAME iteration so J-101/J-102 can flip to passing without a follow-up verify-only iter.
- **Suite gate (iter-11/29/37 lessons):** the full backend suite is the GOAL_ACHIEVED gate for the cluster, but it is NOT a GOAL_ACHIEVED candidate this iter (J-103/J-104 unbuilt) — still, gate the iter's correctness on a flushed `0 failed, EXIT 0` line from a nohup-async pump run; never block the evaluator on the in-flight suite. On this 1369-run host the heavy `loaded_engine`-seeded `test_market_phase.py` tests may not finish under a subagent Bash cap — verify the anti-goal-critical legs (no-lookahead tail-invariance, determinism, config-validation, `test_no_magic_numbers`) via the FAST no-boot tests and hand the full suite to the pump (iter-29 lesson).
- **Additive-guard traps (iter-20/23/32 lessons):** if any `set(payload) == {...}` exact-shape guard covers `/api/market-phase`, update it to accept the additive `severity_velocity` key IN THIS ITER (not a consolidation iter later). No new `table=True` model is added (so no `test_db.py` expected-tables change), and no new column on an existing table (so no `_ADDITIVE_COLUMNS` change) — `severity_velocity` is an in-memory additive field on a derived/cached payload.
- **Next iteration (iter-45, FULL):** J-103 (`/research/severity-velocity` study, `EventStudyCache`+`_dataset_version`, regime-family × velocity-sign × forward-SPY-return matrix, N= drill-down) + J-104 (cache `compute_factor_combination` + `compute_regime_setup_pattern_study`; bound the `select(ScannerRun)).all()` full-table scan at `research.py:1904` with `where(asof_date <= as_of)`; as-of-bound `_run_position_index` callers; lazy-load + SPLIT the four heavy labs into their own `/research/*` sub-routes). J-104's route split is a **nav-skeleton change** (new `/research/*` sub-routes under the Research section) — that iteration's decomposer must file `blueprint.reapproval-requested` with the one-line reason. J-103's empirical finding on the committed seed: rising stress-velocity under a red regime preceded a BOUNCE, not continuation (the stated hypothesis is NOT supported on this bull-dominated window) — the study must surface that verdict + the underpowered-for-crashes caveat verbatim.
