# Goal Iteration 29 — Dashboard Market Phase & Severity panel + deterministic filtered P(bear) (J-87 + J-88)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 29
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-87, J-88
- **Required-still-passing journeys:** J-01, J-06, J-44, J-49, J-18, J-43, J-50, J-07 (Risk-Off gate), J-13, J-72
- **Anti-goal reminders:**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page reads the single global as-of control. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation. *(critical)*
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **Honest limitations surfaced.** Breadth metrics computed from the seed universe MUST be labelled "universe-relative".

## GOAL

At any as-of date D, the Dashboard shows a new **Market Phase & Severity** panel — a discrete phase (Expansion / Pullback / Correction / Bear / Recovery), a 0–100 severity score with its named component breakdown, and a deterministic 0–1 filtered P(bear) — all derived strictly causally from stored snapshots + index bars dated ≤ D, never altering any stock score, bucket, setup, or the Risk-Off→Actionable gate.

## BACKGROUND

The prior session reached GOAL_ACHIEVED at iter-28 (every buildable Must-have J-01..J-86 green; J-22/J-23/J-24 honestly blocked-NA). `docs/goal.md` was then extended in two commits with TEN new buildable Must-haves: J-87..J-92 (long/severe-downtrend detection) and J-93..J-96 (dynamic point-in-time universe). Per the iter-22 lesson ("every journey in journey-history is green is NOT sufficient for GOAL_ACHIEVED while goal.md has queued new *buildable* Must-haves — they are `unknown` with no positive evidence"), these ten must be built before GOAL_ACHIEVED is appropriate. None of J-87..J-91 / J-93 / J-94 / J-96 is data-dependent (goal.md:2298-2308, 2272-2282); all are offline-provable against the committed 2021-2026 seed (which contains the 2022 bear ≈ −24.5% SPY peak-to-trough and the seeded `^VIX`).

This iteration takes the **foundational** cluster J-87 + J-88. They are the SINGLE read-only derived market-phase/severity layer that everything downstream (J-89 timeline, J-90 recovery edge, J-91 conditioning, J-92 macro wiring) reads — so building them first and getting the derivation + cache + panel right unblocks the rest. J-88's UI is literally an addition to J-87's panel and its filter shares J-87's observation inputs, so they form one tight unit. **Full depth** because this crosses backend (new typed/validated config sections, a new read-only derivation module, a new cached endpoint via the `event_study_cache` pattern) + frontend (a new Dashboard panel), adds new tests beyond a browser smoke (no-lookahead tail-invariance + determinism + weights-sum-validation + `test_no_magic_numbers`), and the full backend pytest suite is the gate.

Applicable lessons (surfaced for the developer/reviewer/evaluator):
- **iter-20 / iter-21:** the full-suite `test_no_magic_numbers` blanket-forbids EVERY float/int literal in `CALC_FILES` (the new derivation module must be added to `CALC_FILES` and carry NO threshold literal — every weight/edge/threshold/VIX-gate/transition-matrix/emission-param from config; a sort-tie sentinel must be a named/structural fallback, never inline `0.0`). The weights-sum-~1.0 validator pattern is `config.py` `_validate_*_weights` (regime at line 322-336) — mirror it so the severity score is rejected at load if its weights don't sum ~1.0.
- **iter-20 / iter-21:** if a NEW standalone `table=True` model is added (e.g. a phase/severity cache distinct from `event_study_cache`), it MUST be added to `test_db.py`'s expected-tables set. **Prefer reusing the existing `EventStudyCache` pattern semantics** (a standalone cache keyed by subject + asof_key + `dataset_version`) — but if a separate cache table is created, register it in `test_db.py`. A pure compute-once-per-request-keyed-by-dataset_version with no new table avoids both traps; either is acceptable if registered.
- **iter-25:** any acceptance leg whose evidence is runtime-only (a rendered panel) requires a live browser-QA capture; confirm `:3835`/`:8835`/`:9222` reachable before scoring. iter-17/18: Chrome `:9222` ECONNREFUSED → hard-SKIP leaves the journey `unknown` (CONTINUE, not a code failure).
- **iter-16:** the cheap decisive "Exactly one date selector" check is static — grep the diff for any new date `useState` / `window`/`document` keydown listener in the panel; it MUST read the single global as-of from the existing provider only.
- **iter-11:** never block the goal-evaluator on the in-flight full pytest suite — hand it to the pump nohup-async and gate on the flushed `0 failed` line.
- **Evidence hygiene (iters 3/7/10/18/26):** md5sum the evidence dir first; capture the panel full-viewport per surface; the panel sits on the Dashboard — scroll it into view and VIEW the pixels (do not accept a blank/duplicate frame).

## IN SCOPE

### Backend
- [ ] Add a new typed, validated `config` section for the deterministic market-phase + drawdown-severity score (e.g. `market_phase:`) holding: the phase labels + phase edges, the severity component **weights** (trailing-peak drawdown depth, time-underwater, the stored regime score/trend, breadth-below-200DMA, the `^VIX` gate) with a **weights-sum-~1.0 validator mirroring `regime.weights`**, the drawdown/time-underwater thresholds, and the `^VIX` gate parameter. NO literal in calc code.
- [ ] Add a new typed, validated `config.regime_switching` block for J-88 holding the 2×2 transition matrix and the per-state (bear / risk-on) emission parameters — verbatim, **never EM-fit at serve time**. (Optionally materialized by a committed deterministic offline calibration script over the seed and loaded verbatim; that script is out of scope to *run live* — only the committed params are consumed.)
- [ ] New read-only derivation engine module (e.g. `app/engine/market_phase.py`) — added to `test_no_magic_numbers` `CALC_FILES` — that computes, for a resolved as-of date D, a pure function of the stored immutable snapshots + index bars dated ≤ D:
  - the discrete **phase** + the 0–100 **severity** with its **named component breakdown** (each component value disclosed), all strictly causal: trailing peak = `max(close)` over `[start, D]` via `bars_asof`; time-underwater counts trading days ≤ D; regime/breadth/trend read **verbatim** from the stored `ScannerRun` rows dated ≤ D (no recompute of regime).
  - the deterministic forward **Hamilton FILTERED** P(state = bear | observations ≤ D) — a closed-form recursion over only observations dated ≤ D, using the config transition matrix + emission params verbatim. The **SMOOTHED** (full-sample) probability MUST NOT be computed/served on this live path (it is reserved for the J-89 retrospective surface in a later iteration).
  - **NA / partial** for any window with insufficient history (never a fabricated phase / severity / probability).
- [ ] Serve the derived layer via a new read-only endpoint (e.g. `GET /api/market-phase?as_of=…`) that is **computed-once-per-resolved-as-of and cached behind a `dataset_version` stamp** (reuse the `event_study_cache` semantics: `_dataset_version(session)` / a cache keyed by `asof_key + dataset_version`; refresh after any dataset change; never serve a stale figure). NO new column on `scanner_runs`/`scanner_results`/`forward_returns`; NO snapshot rebuild triggered.
- [ ] Register the new endpoint router in `app/api/__init__.py` (or the equivalent registration site).

### Frontend
- [ ] New **Market Phase & Severity** panel on the Dashboard (`app/page.tsx` + a new component, mirroring `major-indexes-card.tsx` styling) that fetches `GET /api/market-phase` for the **single global as-of** (read from the existing as-of provider — NO new date `useState`, NO `window`/`document` keydown listener) and renders: the phase label, the 0–100 severity with its **named component breakdown** (explainable — never a bare number), and the 0–1 **P(bear)** beside the phase with its observation vector disclosed. NA / partial states render an explicit honest empty/partial treatment. Dates use the shared `lib/dates.ts` formatter (J-42).

### New user-facing capability
At any as-of date the user sees the market's discrete phase, a 0–100 severity score with its drivers, and a deterministic bear-probability — context for *where in the cycle the market is*, derived only from information available at D.

### New information displayed
A Market Phase label, a 0–100 severity score + its component breakdown, and a 0–1 filtered P(bear) + its observation vector — for the resolved as-of date.

### New user actions
None beyond reading the panel; it re-points with the single global as-of (no new control).

### UI surface changes
One new panel on the Dashboard (`/`). No new page, no new route, no nav change.

### Product surface delta
The Dashboard gains a market-cycle context read alongside the existing Major-indexes & regime card — descriptive market context, never a stock signal.

### Blueprint conformance
The panel lives on the existing **Dashboard** home (`/`) — additive, no new nav section, no nav-skeleton change. Annotated in `blueprint.md` under the Dashboard IA row and the cross-cutting note.

### Data-contract additions
TWO new derived values, each with ONE canonical computing module + ONE serving endpoint (registered in `blueprint.md`):
- **Market phase + drawdown-severity (phase label, 0–100 severity, named component breakdown)** — computed once by `market_phase` (read-only derivation over stored `ScannerRun` rows + index bars ≤ D; cached behind `dataset_version`) → served by `GET /api/market-phase`. NOT a new snapshot column, NO rebuild.
- **Filtered P(bear) 0–1 (+ observation vector)** — computed once by the SAME `market_phase` module (deterministic forward Hamilton FILTER over committed-config params + observations ≤ D) → served by the SAME `GET /api/market-phase`. The SMOOTHED probability is NOT a served value here.
- It reads the EXISTING canonical regime score/label/breadth (`regime:score_regime` → `GET /api/dashboard`) and the index bars (`prices`) verbatim — it does NOT recompute or duplicate them.

## OUT OF SCOPE

- J-89 (market-phase history timeline + the fenced retrospective/SMOOTHED view), J-90 (recovery-turn signal + edge study), J-91 (downtrend-conditioned opportunity study) — they consume this layer; later iterations.
- J-92 (real FRED macro feed + OHLCV macro proxies + `MacroSeries` table) — later iteration; the J-88 filter runs on the price/breadth/VIX observation vector with the macro leg honestly omitted/off-by-default per goal.md:2198.
- J-93/J-94/J-95/J-96 (dynamic point-in-time universe) — a separate cluster; later iterations.
- Computing or serving the SMOOTHED (full-sample) Markov probability anywhere on the live as-of path (lookahead — reserved for the J-89 retrospective surface).
- Any change to a canonical stock score, bucket, setup status, pattern flag, regime score, or the Risk-Off→Actionable gate.
- Any new snapshot column or snapshot rebuild; any second date state.
- Running the offline calibration script live at serve time (only committed config params are consumed).

## DEFINITION OF DONE

- [ ] Target journeys J-87, J-88 pass via browser-qa-agent (live capture of the rendered Dashboard panel: phase + severity + breakdown + P(bear); stepping the as-of back into the 2022 window deepens to Bear/high-severity/high-P(bear), and a 2024 date reads Expansion/Recovery/low-P(bear)).
- [ ] Required-still-passing journeys remain green — especially J-06 (regime label/score identical Dashboard↔/stocks; the panel re-displays, never recomputes, regime), J-07 (Risk-Off still zero Actionable — the panel changes no gate), J-18/J-43/J-50 (single date selector + `?asof` serialization unchanged), J-44/J-49 (major-indexes & regime card unchanged), J-72 (event-study cache unbroken if its `dataset_version` helper is shared/extended).
- [ ] No anti-goal violation introduced — strictly causal (≤ D), no recompute of canonical values, no magic numbers, no second date state, no fabricated NA, no order/execution path, severity weights rejected at load if they don't sum ~1.0.
- [ ] Unit/integration tests pass; full backend pytest suite GREEN (`0 failed`, EXIT 0) — handed to the pump nohup-async, NOT blocking the evaluator; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** J-87 (Dashboard Market Phase & Severity panel: phase label + 0–100 severity + named component breakdown render; stepping the global as-of into 2022 deepens to Bear/high severity, 2024 reads Expansion/Recovery; the same date reads the same phase/severity on reload — coherence) and J-88 (the panel shows a 0–1 P(bear) with its observation vector beside the phase; 2022 → P(bear) toward 1, 2023/2024 → falls back; insufficient-history early date → NA, never a fabricated probability). Also smoke J-06 (regime label on the panel == Dashboard regime card == `/stocks` header for the same date), J-18 (no second date input introduced), J-49 (major-indexes card unchanged).
- **Unit/integration:**
  - **No-lookahead tail-invariance** (critical): removing bars dated > D never changes D's phase / severity / filtered P(bear) — asserted exactly the way `forward_return` / `forward_excursions` prove their tail-invariance.
  - **Determinism:** fixed config params + fixed seed observations → a byte-identical severity and a byte-identical filtered P(bear) (the filter is NEVER EM-fit at serve time).
  - **Causality of the filter:** the FILTERED P(bear) at D is a function of observations ≤ D only; a later observation does not change a past date's filtered value.
  - **Config-weights validation:** the severity weights must sum ~1.0 or the config is rejected at load (mirror `regime.weights`); the new derivation module passes `test_no_magic_numbers` (added to `CALC_FILES`).
  - **Cache correctness:** the layer is computed once per resolved-as-of, served from cache, and the cache refreshes when `dataset_version` changes (no stale figure); figures byte-identical cached-vs-uncached.
  - **2022-bear reproduction:** an as-of in the 2022 window yields phase=Bear, a high severity reproducing the seed's SPY peak-to-trough, and P(bear) trending toward 1; a 2024 as-of reads Expansion/Recovery with low P(bear).
  - **Single-source / gate invariance:** the panel's regime input equals the stored `ScannerRun` regime; no canonical stock score / bucket / setup / Risk-Off gate changes (assert a Risk-Off date still has zero Actionable).
  - If a new standalone cache table is added, it is in `test_db.py`'s expected-tables set; if the served payload rides an existing `*_equals_engine_output`-guarded endpoint, update that guard (it does not — this is a new endpoint — but verify no existing byte-equality guard is tripped).
- **Error cases:** invalid `?as_of` / unknown date degrades like the existing endpoints (latest, never a fabricated date); an insufficient-history window returns NA / partial (never a fabricated phase/severity/probability); a malformed `market_phase` / `regime_switching` config (weights not summing ~1.0, missing emission param) is rejected at load with an explicit error.

## NOTES

- This is an **in-place resume after GOAL_ACHIEVED** with goal.md extended by J-87..J-96 (two recent commits). The blueprint has been updated additively for this iteration (two new Data Contract rows + a Dashboard IA annotation + a cross-cutting note); the nav skeleton is unchanged, so no re-approval is required.
- J-88 explicitly forbids serving the SMOOTHED probability live — only the FILTERED (forward, causal) probability is the served value. Treat the smoothed/full-sample path as a future J-89 retrospective surface and keep it out of this iteration entirely; this is the J-49 "future-aware context only behind a clear marker, never feeding an as-of value" precedent.
- The seed contains the 2022 bear and `^VIX` (goal.md:2298-2308), so both being-in and having-emerged-from a downtrend are deterministically provable offline — none of J-87/J-88 may be recorded blocked-NA for provider reasons, and neither may halt the loop.
- Reuse — do not duplicate — the existing `event_study_cache` `dataset_version` machinery (`research.py:_dataset_version` / `event_study_cached`) so the new layer's cache invalidation is single-sourced with J-72's, and read the canonical regime via the stored `ScannerRun` rows (the same rows `regime_history` reads) rather than recomputing regime.
- This iteration is NOT a GOAL_ACHIEVED candidate: J-89, J-90, J-91, J-92, J-93, J-94, J-95, J-96 remain unbuilt afterward. Expect the evaluator to verdict CONTINUE on a clean pass and recommend the next cluster (likely J-89 + J-90, then J-91, then J-92 at full depth, then the J-93/J-94/J-96 dynamic-universe cluster with J-95's data-walled envelope).
