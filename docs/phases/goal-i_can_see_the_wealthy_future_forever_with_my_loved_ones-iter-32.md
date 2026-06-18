# Goal Iteration 32 — Downtrend-conditioned opportunity study (J-91) + optional FRED macro feed (J-92)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 32
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-91, J-92
- **Required-still-passing journeys:** J-87, J-88, J-89, J-90, J-06, J-18, J-07, J-29, J-32, J-63, J-51, J-65, J-77, J-82
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Live fetch is real-data-only.** The Data Manager MUST use the config-selected live provider to fetch real EOD bars; on a provider failure it MUST surface an explicit error and MUST NOT synthesize prices to fill a gap or force a successful run.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere; the default seed path requires none, and any live-provider key is read only from the environment.
  - **Import keys are env-or-session, never persisted.** A provider key MUST be read from the environment, or — if pasted into the import UI — held in memory for that run only, never written to disk, the run log, the DB, or any committed file, and never echoed back in any response.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Honest limitations surfaced.** Walk-forward evidence MUST be labelled as carrying survivorship bias (current-membership universe) so results are never overstated.
  - **Honest forward-test for partial windows.** Cohorts lacking enough samples MUST show NA/partial and sample size — never fabricate or extrapolate a return to fill a gap. *(extends No fabricated data)*
  - **Attribution & lab analytics read-only.** Derived from stored returns/excursions/factor values; risk-adjusted uses downside only.
  - **Exactly one date selector.** The global as-of control drives every date-scoped page; `?asof` is its serialization, never a second state; the Research as-of toggle is a mode, not a second date state. *(critical)*

## GOAL

Let the user condition the existing forward-return evidence on the causal as-of downtrend state — three side-by-side angles (held-up-best / fell-hardest evidence / recovery-turn edge) on `/research` (J-91) — and add a real, optional, publication-lag-aligned FRED macro feed wired off-by-default into the severity/regime-switching/study layer so price-only figures stay byte-identical until macro is enabled (J-92).

## BACKGROUND

The iter-31 evaluator (CONTINUE) prescribed J-91 + J-92 at FULL depth as the next backend cluster consuming the iter-29/30/31 market-phase + recovery-turn layer; both add backend code so the full pytest suite is the GOAL_ACHIEVED gate. J-91 is the third consumer of the now-passing market-phase derivation (`market_phase.py`) and the enriched event-study observation set (`research:_event_study_observation_set` / `compute_regime_setup_pattern_study`): it groups the SAME stored observations, additively tagged with the CAUSAL as-of phase / severity band / P(bear) band at each observation's snapshot date (≤ D), and surfaces the J-90 recovery-turn edge in the same panel — recomputing no return, score, regime, phase, or signal. J-92 adds a real macro provider + a STANDALONE `MacroSeries` table + the OHLCV macro proxies (`^TNX`/`^DXY`/`^VXN`) as plain `DailyPrice` bars beside the seeded `^VIX`, wired as config-default-OFF inputs so every J-87..J-91 figure is byte-identical with macro absent or disabled. Both are buildable/verifiable OFFLINE against the committed 2021-2026 seed (the 2022 bear + `^VIX`) plus a small committed macro seed for J-92; only the live FRED/proxy pull is data-gated and honestly blocked-NA (non-vetoing, the J-22 contract). Depth is FULL: backend engine + new endpoint(s) + a new standalone table + frontend `/research` surface + config blocks, gated on the full ~880-test pytest suite.

## IN SCOPE

### Backend

**J-91 — Downtrend-conditioned opportunity study (`/research`):**
- [ ] Add a new read-only study `research:compute_downtrend_opportunity_study` (in `apps/backend/app/engine/research.py`, a `CALC_FILES` member — no threshold/band literal) that GROUPS the SAME enriched event-study observation set (`_event_study_observation_set` / `_event_study_members`: stored realized return + MAE/MFE + `max_drawdown` + stored `regime_label` + `sector` + setup/pattern flags, read VERBATIM) and ADDITIONALLY tags each observation with the CAUSAL as-of **phase**, **severity band**, and **P(bear) band** at the observation's snapshot date — read from the existing read-only `market_phase` derivation (≤ D, never recomputed; strictly causal so no future bar sets a conditioning tag). The enrichment is ADDITIVE: existing `compute_event_study` (J-29/J-63) and `compute_regime_setup_pattern_study` (J-77) figures and existing samples drill-downs stay BYTE-IDENTICAL (assert).
- [ ] The study returns the THREE required angles, each as ranked rows with per-horizon forward-return stats (n, mean, median, %-positive/hit-rate, expectancy, downside-only risk-adjusted — return/downside-dev, return/|MAE|, max-drawdown): **(a) "held up best"** (strongest forward returns / leadership cohorts within downtrend-conditioned dates), **(b) "weakness / short-research evidence"** (worst forward returns, deepest max-drawdown within downtrend dates — EVIDENCE ONLY, no order/execution), **(c) "recovery-turn edge"** (the existing J-90 `compute_recovery_turn_edge` surfaced in the same panel — reuse, do not re-derive).
- [ ] Serve via a NEW read-only endpoint `GET /api/research/downtrend-opportunity` (`horizon` / `view` [Episodes⇄Pooled, J-63] / `as_of` [All-history⇄As-of FILTER-only, J-32] params mirroring `/api/research/event-study`). Horizons from `config.walk_forward.horizons` (no hardcoded list); min-sample from the EXISTING config (`config.walk_forward.min_sample`) → NA + n below it; the phase/severity-band/P(bear)-band conditioning vocabulary from a config-backed catalog (no hardcoded lists). Downside-only risk (never total volatility). The As-of⇄All-history toggle FILTERS the stored observations only (a mode reading the single global as-of — NO second date state).
- [ ] Add a new `kind` to `samples.py` `compute_samples` (mirroring `_regime_setup_pattern_samples` / `_recovery_turn_samples`) so EACH displayed row's `N=` chip drills down through the SAME shared-membership observation builder via the EXISTING `GET /api/research/samples` — drill-down total == published row n in BOTH Episodes+Pooled and BOTH All-history+As-of (J-51/J-65 count-coherence; one membership rule, never a second grouping). The samples validation/vocabulary MUST accept EVERY conditioned combination the study emits so no displayable row returns a 4xx (the J-82 lesson).

**J-92 — Optional FRED macro feed + macro proxies (config-default-OFF):**
- [ ] Add a new **macro provider** registered like the OHLCV providers in `apps/backend/app/data_providers/__init__.py` `make_provider` (a STANDALONE provider with its FRED key read FROM THE ENVIRONMENT ONLY — never persisted, logged, committed, or echoed) that fetches a configured set of FRED series (yield-curve 10y–2y inversion, unemployment trend, credit spreads) into a dedicated additive **`MacroSeries(symbol, date, value, source, published_date)`** STANDALONE `create_all`-managed table (so the `_ADDITIVE_COLUMNS` trap does NOT apply, and NO snapshot rebuild is required — the same standalone-table reasoning `event_study_cache` / `market_phase_cache` use). Register the new table in the `test_db.py` expected-tables guard (a new group, e.g. `MACRO_TABLES = {"macro_series"}` — the iter-20 lesson).
- [ ] Store the OHLCV macro proxies `^TNX` / `^DXY` / `^VXN` as plain `DailyPrice` bars beside the already-seeded `^VIX` (any symbol accepted — no universe FK).
- [ ] Wire the macro series as **optional, config-default-off** inputs to the J-87 severity score, the J-88 regime-switching observation vector + emissions, and the J-91 study conditioning — each leg OFF by default in config until enabled, so with macro absent/disabled every J-87..J-91 figure is BYTE-IDENTICAL to the price/breadth/VIX-only path (assert).
- [ ] Publication-lag alignment: a macro value used for date D is only one whose `published_date ≤ D` (config publication-lag per series — using the reference-date value on D is lookahead and is forbidden), carrying an honest publication-lag limitation label.
- [ ] Commit a small macro seed over the seed window so the macro-conditioned features are buildable + fully testable OFFLINE with injected fixtures (mirroring the `^VIX` seed). The live FRED/proxy refresh + any series not committed to the seed are data-dependent / NON-HALTING — recorded honestly blocked / unavailable (NA), never fabricated, never halting the loop or vetoing GOAL_ACHIEVED.
- [ ] New typed/validated config block(s) for the macro feed (provider list / env-var name / per-series id + publication-lag + the default-off enable flags) in `config.py` — no provider list or threshold literal in calculation code; the macro-wiring code stays `test_no_magic_numbers`-clean.

### Frontend

- [ ] **J-91:** a new **Downtrend Opportunity** study panel on `/research` rendering the three angles side by side as ranked, client-side-sortable tables (J-48/J-82 view-transform contract — re-orders only, recomputes nothing). Conditioning controls (phase / severity band / P(bear) band from the config vocabulary in the payload), horizon toggle, Episodes⇄Pooled (J-63) and As-of⇄All-history (J-32) toggles, all re-pointing consistently. `N=` chips open the samples drill-down in a NEW tab (J-65). Low-sample/empty conditioned cohorts show NA + n; the survivorship-bias + universe-relative labels persist; the weakness angle is labelled EVIDENCE ONLY (no order/execution affordance). Column headers read the SAME J-47 glossary.
- [ ] **J-92:** an honest **publication-lag limitation label** wherever a macro-conditioned figure is shown, and (since macro is config-default-OFF) the surfaces stay byte-identical to today by default — the macro provider appears in the existing Data Manager provider catalog / import surface; a walled/uncommitted macro series renders an honest blocked/unavailable (NA) state, never a fabricated value.

### New user-facing capability
The user can condition the forward-return evidence on the causal downtrend state (phase / severity band / P(bear) band, all ≤ D) and read three angles — what held up best, what fell hardest (evidence only), and the recovery-turn edge — on `/research`. Optionally, with macro enabled, the severity / regime-switching / study layer can incorporate publication-lag-aligned FRED macro inputs.

### New information displayed
The Downtrend Opportunity three-angle tables (per-horizon mean/median/%-positive/expectancy + downside-only risk-adjusted + max-drawdown, conditioned by phase/severity-band/P(bear)-band); the publication-lag limitation label for macro-conditioned figures.

### New user actions
Phase / severity-band / P(bear)-band conditioning controls; horizon, Episodes⇄Pooled, As-of⇄All-history toggles; client-side column sort; `N=` chips opening count-coherent samples in a new tab.

### UI surface changes
A new Downtrend Opportunity panel on the EXISTING `/research` page (Research home). No new page, no new top-level nav section.

### Product surface delta
Research gains a downtrend-conditioned opportunity lens over the SAME stored evidence; the analytical layer optionally ingests real macro inputs without changing any default figure.

### Blueprint conformance
J-91 and J-92 land on EXISTING Information-Architecture homes — J-91 the Downtrend Opportunity panel under **Research** (`/research`) with `N=` drill-down under **Samples** (`/research/samples`, link-reached); J-92's macro provider/import under **Data Manager** (`/data`), and its optional inputs feed the EXISTING Dashboard Market-Phase panel (J-87/J-88) + the J-91 Research study. No new top-level nav section, no new page. The blueprint IA skeleton + Data Contract are updated additively (new rows for the Downtrend Opportunity study and the macro feed/`MacroSeries` table) — no nav-skeleton change, no re-approval required.

### Data-contract additions
- **Downtrend Opportunity study (J-91)** — per (phase / severity-band / P(bear)-band × angle) the per-horizon forward-return stats (n, mean, median, hit-rate, expectancy, downside-only risk-adjusted, max-drawdown). Canonical computing module: `research:compute_downtrend_opportunity_study` (a pure GROUPING of the SAME enriched `_event_study_observation_set` tagged with the read-only `market_phase` causal phase/severity/P(bear) ≤ D — recomputes no return/excursion/score/regime/phase/signal; angle (c) reuses `research:compute_recovery_turn_edge`). Serving endpoint: `GET /api/research/downtrend-opportunity`. Drill-down: a new `kind` on the EXISTING `GET /api/research/samples`. ADDITIVE — J-29/J-63/J-77/J-90 figures + existing samples drill-downs stay byte-identical.
- **Macro series (J-92)** — `MacroSeries(symbol, date, value, source, published_date)` (publication-lag aligned: `published_date ≤ D`). Canonical computing module: a NEW macro provider in `data_providers/` (FRED key env-only) writing the STANDALONE `macro_series` table + the `^TNX`/`^DXY`/`^VXN` OHLCV proxies as plain `DailyPrice` bars. Wired as config-default-OFF inputs into `market_phase` (severity + regime-switching emissions) and `research:compute_downtrend_opportunity_study` — additive; with macro disabled every figure is byte-identical to the price/breadth/VIX-only path. Live FRED/proxy pull is data-dependent / non-halting (honest NA). Standalone table → register in `test_db.py` expected-tables (new group), NOT `_ADDITIVE_COLUMNS`.

## OUT OF SCOPE

- J-93 / J-94 / J-96 (dynamic point-in-time universe cluster) and J-95 (backward-history / constituent-feed envelope) — the NEXT cluster, dispatched after J-91/J-92 land.
- Any change to a canonical stock score, A–E bucket, setup status, pattern flag, the regime score, or the Risk-Off→Actionable gate (all untouched — critical).
- Any new snapshot column or snapshot rebuild for J-91/J-92 (J-91 is a read-only derivation; J-92 uses a standalone table + `DailyPrice` proxies).
- EM-fitting the regime-switching params at serve time (params come verbatim from committed config).
- Serving the SMOOTHED (full-sample) P(bear) or true-bear dating on any live/causal path — that stays fenced on the J-89 retrospective surface only.
- Any order/execution/short-deployment affordance on the weakness angle (evidence only).
- Persisting/logging/echoing any FRED key or provider secret.
- Enabling macro inputs by default (they ship config-default-OFF; default figures stay byte-identical).

## DEFINITION OF DONE

- [ ] Target journeys J-91, J-92 pass via browser-qa-agent (J-92's offline-testable legs — provider/table/wiring/publication-lag/byte-identity-when-disabled + the committed-macro-seed conditioning — go green; the live FRED/proxy pull + any uncommitted series are honestly recorded blocked-NA, non-vetoing).
- [ ] Required-still-passing journeys remain green — especially J-87/J-88 (consumed layer byte-identity), J-89/J-90 (the surfaces this cluster extends), J-06 (single source), J-18 (CRITICAL: exactly one date selector), J-07 (Risk-Off gate), J-29/J-32/J-63/J-51/J-65/J-77/J-82 (research labs + samples count-coherence).
- [ ] No anti-goal violation introduced (no lookahead; no recompute in read path; no magic numbers; no fabricated data; no order/execution path; no secrets in source; Risk-Off gate untouched; exactly one date selector).
- [ ] Unit/integration tests pass; no regressions. The FULL ~880-test backend pytest suite is the gate — hand it to the pump nohup-async; gate the GOAL_ACHIEVED candidacy on the FLUSHED `0 failed, EXIT 0` line, NEVER block the evaluator dispatch on the in-flight suite (iter-11 lesson).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-32-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by ID):** J-91 (Downtrend Opportunity three-angle panel: conditioning controls, ranked sortable tables, Episodes⇄Pooled + As-of⇄All-history toggles re-point, `N=` chip → count-coherent samples in a new tab with total == published n, low-sample NA + n, survivorship-bias label, weakness angle labelled evidence-only with no order affordance), J-92 (publication-lag limitation label; macro provider visible in the Data Manager catalog; byte-identical default figures with macro disabled; honest blocked-NA for a walled/uncommitted series). Plus the required-still-passing smoke: J-87/J-88 (Dashboard Market-Phase panel unchanged at the same date), J-89/J-90, J-06, J-18 (CRITICAL — 0 page-local date inputs; the new panel/conditioning controls add NO date state, NO window/document keydown listener), J-07, J-29/J-32/J-63/J-51/J-65/J-77/J-82.
- **Unit/integration:**
  - J-91: byte-identity that the additive causal-tag enrichment leaves `compute_event_study` (J-29/J-63) + `compute_regime_setup_pattern_study` (J-77) + `compute_recovery_turn_edge` (J-90) figures + existing samples drill-downs unchanged; no-lookahead (the conditioning phase/severity/P(bear) tag at a signal date uses only ≤ D — tail-invariance idiom like `forward_return`; forward returns use only bars > D); count-coherence SAME-INSTANT (drill-down total == published n) in Episodes AND Pooled AND All-history AND As-of; every displayable conditioned row resolves without a 4xx (J-82 lesson); downside-only risk; horizons from `config.walk_forward.horizons`; min-sample → NA + n.
  - J-92: macro provider registered in `make_provider`; `MacroSeries` standalone table created by `create_all` and present in the `test_db.py` expected-tables guard; publication-lag (`published_date ≤ D`, never the reference-date value); macro-disabled byte-identity of every J-87..J-91 figure to the price/breadth/VIX-only path; FRED key read from env only and never persisted/logged/echoed; walled provider → honest blocked-NA, never fabricated; macro-wiring code passes `test_no_magic_numbers`.
- **Error cases:** invalid `horizon` / `view` / conditioning-band on `/api/research/downtrend-opportunity` → 4xx; a samples drill-down for a non-emitted combination → 4xx (but EVERY displayable row must resolve 2xx); a macro series with no committed seed or a walled FRED provider → honest NA (never a fabricated value, never a halt); using a macro value whose `published_date > D` → forbidden (lookahead).

## NOTES

- **Suite-gate (iter-11 / iter-29 lesson):** the full pytest suite is the GOAL_ACHIEVED gate and is the ONLY authoritative pass signal for the backend; run it via `nohup` in the background and gate the next evaluator on the FLUSHED `0 failed, EXIT 0` line — never block the evaluator dispatch on the in-flight suite. An `exit=137` in the suite log is the known background-helper harness-kill, NOT a test failure.
- **Fast vs slow tests on this host (iter-29 lesson):** any test using the `loaded_engine` seed fixture boots the heavy backend and cannot finish under a subagent Bash cap; split fast (no-boot synthetic + config-validation) from slow (seed-boot) tests and verify the anti-goal-critical legs (no-lookahead, determinism, byte-identity-when-disabled, count-coherence) via the fast set.
- **Additive-field guard lesson (iter-12 / iter-20 / iter-23 / iter-24):** J-92 adds a STANDALONE `macro_series` table — add it to a new `test_db.py` expected-tables group (NOT `_ADDITIVE_COLUMNS`, which is only for new columns on EXISTING tables; `^TNX`/`^DXY`/`^VXN` ride the existing `DailyPrice` table → no schema change there). If any new field is additively attached to an endpoint covered by a `served == engine_output` byte-equality guard, update that guard in the SAME iter (strip only the additive key, keep canonical equality). J-91 is additive on the research surfaces — assert J-29/J-63/J-77/J-90 byte-identity in the same iteration.
- **CRITICAL anti-goal under this edit:** J-91's conditioning is a MODE over stored observations and J-92 adds NO date control — confirm the new `/research` panel + macro surfaces hold NO date `useState` and NO window/document keydown listener so J-18 (exactly one date selector) is preserved by construction.
- **Fence discipline (J-89 precedent):** J-91's causal conditioning MUST read only the FILTERED (causal) P(bear) / causal phase / severity ≤ D — never the SMOOTHED full-sample probability or true-bear dating (those stay fenced on the J-89 retrospective surface and feed no as-of value/study).
- **Data-dependency honesty (J-22 / J-44-DIA contract):** J-92's live FRED/proxy pull and any uncommitted series are data-dependent / NON-HALTING — recorded honestly blocked / unavailable (NA), never fabricated, never halting the loop or vetoing GOAL_ACHIEVED. The offline-testable legs (provider/table/wiring/publication-lag/byte-identity/committed-macro-seed conditioning) are expected to go green.
- **Evidence-hygiene (recurring lesson):** browser-QA must `md5sum` the evidence dir FIRST (blank/byte-shared frames have recurred every iteration); resolve sort / `N=` controls by `aria-label`, not visible `text()`; assert `N=` count-coherence SAME-INSTANT against the live aggregate (published Ns drift across backend boots as warm-up matures forward returns — iter-7 lesson); scroll any below-the-fold `/research` panel into view full-viewport and VIEW the pixels.
- After J-91/J-92 land green with the full suite GREEN, zero regression, and COHERENCE-PASS, the next cluster is J-93/J-94/J-96 (dynamic universe, full depth) + J-95's data-walled envelope; J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md:105-109).
