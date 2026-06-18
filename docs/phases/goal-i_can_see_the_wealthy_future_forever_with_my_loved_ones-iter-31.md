# Goal Iteration 31 — Live UI re-verification of the Market-Phase timeline (J-89) + Recovery-Turn Edge (J-90)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 31
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-89, J-90
- **Required-still-passing journeys:** J-87, J-88, J-06, J-07, J-18, J-43, J-50, J-13, J-44, J-49, J-01
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. Chart **visualization** MAY render bars dated > D strictly as a labelled forward/after-as-of display; this display path MUST NOT feed any score, bucket, setup status, pattern flag, factor value, or ranking — all of which remain computed from bars with date ≤ D — and the moving-average lines drawn past D are visualization only, never as-of signals. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Honest limitations surfaced.** ... walk-forward evidence MUST be labelled as carrying survivorship bias (current-membership universe) so results are never overstated.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Exactly one date selector** (coherence invariant 5) — the global as-of control drives every date-scoped page; `?asof` is its SERIALIZATION, never a second state; the Research As-of⇄All-history toggle is a MODE, never a second date state.
  - **The SMOOTHED (full-sample) bear probability and the peak-to-trough "true bear" dating are LOOKAHEAD by construction** and MUST appear ONLY on the J-89 retrospective surface, explicitly fenced as analysis-only — they MUST NOT feed any as-of score, signal, episode, or study-conditioning tag (the J-49 fenced-context precedent).

## GOAL

Bring the environment up (backend :8835, frontend :3835, Chrome DevTools :9222) and capture the missing LIVE UI evidence that closes J-89 (Dashboard Market-Phase HISTORY timeline + dated causal downtrend episodes + the fenced "Retrospective (full-sample / analysis-only)" sub-view) and J-90 (the causal recovery-turn signal on the Market-Phase panel + the `/research` Recovery-Turn Edge lab with count-coherent `N=` drill-down) to `passing`, with no rework of the already-correct backend.

## BACKGROUND

J-89 and J-90 were built and backend-verified at iter-30 (FULL depth) — the evaluator independently confirmed the structural smoothed/true-bear FENCE, no-lookahead tail-invariance for the timeline/episode/recovery legs, filtered byte-identity of the timeline to the J-87/J-88 panel series, recovery-turn-edge count-coherence, config validation, no-magic-numbers, the new `event_study_cache`/`MarketPhaseCache` reuse (no new table), and the J-18 single-date invariant. The only thing missing is LIVE UI evidence: browser-QA was SKIPPED ENTIRELY in iter-30 (Chrome MCP `ECONNREFUSED` on :9222, evidence dir empty, 0/31 UI tests), so both target journeys are stuck `unknown` — and the strict rule forbids marking a Must-have `passing` without positive live evidence (iter-17/iter-25/iter-30 precedent). The iter-30 evaluator's explicit recommendation is therefore "iter-31 = a LEAN live re-verification pass for J-89 + J-90 (no code rework expected — the backend is correct and the data legs are proven)". This iteration is NOT a GOAL_ACHIEVED candidate: J-91..J-96 remain unbuilt buildable Must-haves (iter-22 lesson). The one code touch is the trivial review NOTE carried from iter-30: drop the redundant local import `from datetime import date as _date` at `apps/backend/app/engine/market_phase.py:472` (a no-behavior-change cleanup — `date` is already imported module-level).

**Lessons applied (from the inlined lessons file):**
- **iter-17 / iter-25 / iter-30 (env-down → hard-SKIP):** confirm :3835 / :8835 / :9222 reachability BEFORE scoring; a UI/SSR journey cannot be upgraded to `passing` without live evidence. Verify the env is actually up first; if Chrome :9222 is down again, the correct outcome is a documented SKIP with a concrete reason, not a fabricated pass.
- **iter-3 / iter-7 / iter-18 (blank / wrong-frame / shared-byte captures):** `md5sum` the evidence dir FIRST; the Market-Phase panel sits BELOW THE FOLD on the Dashboard — scroll the timeline AND the fenced retrospective sub-view into view and capture FULL-VIEWPORT, then VIEW the pixels. A blank frame or a wrong-surface frame is a REJECTED capture, not evidence. Cite a shared file once; do not pass a journey on a recycled image.
- **iter-27 / iter-28 / iter-28b (selector false-negative):** resolve the `/research` lab sort headers and `N=` drill-down chips by `aria-label`, NEVER by visible `text()` (the labels live in nested `<span>`s, so XPath `text()` matches nothing). Before recording a sort "regression", confirm the sort code path is byte-unchanged in the diff.
- **iter-7 (Ns drift between boots):** assert the recovery-turn-edge `N=` count-coherence SAME-INSTANT against the live aggregate, never against a hardcoded N from an earlier capture or report.
- **iter-11 / iter-29 (suite gating):** this is a lean iteration and NOT a GOAL_ACHIEVED candidate, so the full backend suite is NOT the gate. The redundant-import cleanup is a no-op for behavior; targeted `test_market_phase.py` FAST (no-boot, lines ~92–307) + `test_no_magic_numbers` + `test_db::test_create_all_produces_expected_tables` are sufficient to confirm no regression. Do NOT block on a `loaded_engine`-seed-booting full suite under a subagent cap.

## IN SCOPE

### Backend
- [ ] Remove the redundant local import `from datetime import date as _date` at `apps/backend/app/engine/market_phase.py:472` and use the module-level `date` already imported — a no-behavior-change cleanup (the iter-30 review PASS_WITH_NOTES note). No other backend change. The served `GET /api/market-phase` and `GET /api/research/recovery-turn-edge` payloads MUST stay byte-identical.

### Frontend (if applicable)
- [ ] None expected. The J-89 timeline overlay, the fenced retrospective sub-view, the recovery-turn badge (Market-Phase panel), and the `/research` Recovery-Turn Edge lab were all built at iter-30 and are committed (`apps/frontend/components/market-phase-card.tsx`, `apps/frontend/app/research/page.tsx`, `apps/frontend/app/research/samples/page.tsx`). Only fix a genuine UI defect if live re-verification surfaces one (e.g. a sort that is truly broken when resolved by `aria-label`, or a fence label that is missing) — otherwise make NO frontend code change.

### New user-facing capability
None new this iteration — this is a verification pass. After it, the already-built capabilities are CONFIRMED visible: the user can see the Market-Phase HISTORY timeline + dated 2022 downtrend episode + the fenced retrospective view on the Dashboard, and run the Recovery-Turn Edge lab on `/research`.

### New information displayed
None new (verification of already-built surfaces).

### New user actions
None new (verification of already-built controls: the retrospective toggle, the horizon / Episodes⇄Pooled / As-of⇄All-history toggles, column sort, the `N=` drill-down chips).

### UI surface changes
None new — Dashboard Market-Phase panel (`/`) and the `/research` Recovery-Turn Edge lab are confirmed, not modified.

### Product surface delta
No delta — the verification confirms the iter-30 surfaces render and behave correctly against a live backend; the backend cleanup leaves served payloads byte-identical.

### Blueprint conformance
No new surfaces. J-89 lands on the EXISTING Dashboard home (the Market-Phase panel overlay on the major-indexes/regime card) and J-90 on the EXISTING Dashboard panel (recovery-turn signal) + the EXISTING `/research` home (Recovery-Turn Edge lab) + the EXISTING `/research/samples` drill-down — all already registered in `blueprint.md` Information Architecture under Dashboard / Research / Samples (the `[TARGET iter-30]` rows). The blueprint's J-89/J-90 `[TARGET iter-30]` tags are updated to `[built iter-30; live re-verify iter-31]` (additive housekeeping; no nav-skeleton change → no re-approval).

### Data-contract additions
None. J-89's timeline `{date, phase, p_bear}` series + causal downtrend-episode dating and the retrospective FENCE (smoothed P(bear) + peak-to-trough true-bear dating), and J-90's recovery-turn signal `{is_recovery_turn, reason}` + the Recovery-Turn Edge study, are ALL already registered in the `blueprint.md` Data Contract (the J-87/J-88 market-phase rows + the dedicated J-90 Recovery-Turn Edge row + the J-90 samples `kind` on the existing `GET /api/research/samples`). All are read VERBATIM from the existing single derived `market_phase` series + the stored append-only `forward_returns` — no second computation, no second endpoint, no new value.

## OUT OF SCOPE

- Any new feature, endpoint, stored column, or config key.
- J-91..J-96 (the downtrend-opportunity study, FRED macro feed, and the dynamic point-in-time universe cluster) — they are the next clusters, not this iteration (J-91 + J-92 at FULL depth come next, then the J-93/J-94/J-96 universe cluster + J-95's data-walled envelope).
- Re-running the full ~880-test backend pytest suite under a subagent cap (this is not a GOAL_ACHIEVED candidate; the full suite is not the gate this iteration — iter-11/iter-29 lessons).
- Any change to canonical stock scores / buckets / setups / patterns / regime / the Risk-Off→Actionable gate (untouched — the market-phase layer is read-only/additive).
- Triggering a destructive `kind:"rebuild"` data-manager job for QA (clears ~1370 daily snapshots, ~11h — NEVER for verification; memory note).

## DEFINITION OF DONE

- [ ] Environment confirmed up (backend :8835 `/api/health` ready, frontend :3835 serving a hydrated app shell, Chrome DevTools :9222 reachable) BEFORE scoring; if Chrome :9222 is unreachable, record a documented SKIP with the concrete reason (do NOT upgrade J-89/J-90 to passing on source review alone).
- [ ] Target journeys J-89, J-90 pass via browser-qa-agent with FULL-VIEWPORT, evaluator-viewable captures (md5-distinct, correct-surface).
- [ ] Required-still-passing journeys (J-87, J-88, J-06, J-07, J-18, J-43, J-50, J-13, J-44, J-49, J-01) remain green via a live smoke.
- [ ] No anti-goal violation introduced (esp. the smoothed/true-bear FENCE, no-lookahead, exactly-one-date-selector, no order/execution path).
- [ ] The redundant `market_phase.py:472` local import is removed; FAST targeted tests pass (`test_market_phase.py` no-boot legs + `test_no_magic_numbers` + `test_db::test_create_all_produces_expected_tables`); the `GET /api/market-phase` + `GET /api/research/recovery-turn-edge` payloads are byte-identical to before the cleanup.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-31-dev.md`.

## TESTING REQUIREMENTS

- **Browser (the primary gate this iteration):**
  - **J-89** — On the Dashboard (`/`): scroll the Market-Phase panel into view full-viewport and confirm (1) the per-snapshot-date phase + FILTERED P(bear) STEP-FUNCTION timeline overlays the major-indexes/regime card with the J-44/J-49 treatment; (2) the 2022 bear appears as ONE dated CAUSAL downtrend episode with its first-trigger date + severity-at-trigger + open/closed state at D; (3) the fenced "Retrospective (full-sample / analysis-only)" sub-view is clearly LABELLED analysis-only, is fetched only on toggle, and shows the SMOOTHED series + peak-to-trough true-bear dating; (4) under a historical as-of D the causal timeline/episodes render only dates ≤ D while the retrospective is the only future-aware surface; (5) an early as-of (e.g. 2021-01-05) yields an HONEST EMPTY timeline (no fabricated phase/episode/probability).
  - **J-90** — (1) the Market-Phase panel surfaces the recovery-turn signal + its `reason` (never a bare flag); (2) the `/research` Recovery-Turn Edge lab reports the per-horizon edge (mean / median / %-positive / expectancy + downside risk-adjusted + aggregate max-drawdown); (3) the horizon, Episodes⇄Pooled (J-63), and As-of⇄All-history (J-32) toggles re-point the table; (4) columns sort (resolve sort headers by `aria-label`, not `text()`); (5) the survivorship-bias label is shown; (6) an `N=` chip opens the samples drill-down in a NEW tab with total == published n, verified SAME-INSTANT in BOTH Episodes/Pooled AND BOTH All-history/As-of.
  - **Required-still-passing smoke:** J-87/J-88 (same-date Market-Phase panel values unchanged after the import cleanup), J-01 (Dashboard loads), J-06 (single-source score consistency), J-18 (exactly one date selector — CRITICAL; the Market-Phase panel + retrospective toggle hold NO date state and add no window/document keydown listener), J-43/J-50 (`?asof` serialization + href-stamping), J-13 (browse past date), J-44/J-49 (indexes card full history + as-of marker), J-07 (Risk-Off gate).
- **Unit/integration:** targeted FAST `apps/backend/tests/test_market_phase.py` no-boot legs (the fence + no-lookahead tail-invariance + filtered byte-identity + determinism + config-validation legs, ~lines 92–307) + `test_no_magic_numbers.py` + `test_db.py::test_create_all_produces_expected_tables` — all GREEN after the import cleanup. Additionally assert (curl + a small offline diff) that `GET /api/market-phase` and `GET /api/research/recovery-turn-edge` are byte-identical before/after the cleanup.
- **Error cases:** an invalid/unknown `?asof` still degrades to latest with no fabricated date (J-43); an early/empty-history as-of yields an honest empty timeline and NA episode list (J-89); a low-sample recovery-turn-edge cohort shows NA + n, never a fabricated figure (J-90); the recovery-turn-edge `N=` drill-down resolves WITHOUT a 4xx for every displayable row (the J-82 every-emitted-combination lesson) and the samples endpoint rejects an unknown cohort `kind` with a 4xx.

## NOTES

- Drives directly from the iter-30 evaluator recommendation (`runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/iter-30/eval.md`): "iter-31 = a LEAN live re-verification pass for J-89 + J-90 (no code rework expected)". iter-30 coherence was COHERENCE-PASS.
- Current journey state (`journey-history.json`): J-89 = `unknown`, J-90 = `unknown` (backend built/verified iter-30, no live UI evidence); J-87/J-88 = `passing`; J-91..J-96 = `failing` (unbuilt); J-22/J-23/J-24 = `unknown` honestly blocked-NA (data-walled, non-vetoing per `docs/goal.md` lines 105-108).
- **Evidence hygiene is load-bearing this iteration** (the only new gate is the browser captures): `md5sum` the evidence dir FIRST; capture the below-the-fold Market-Phase panel AND the fenced retrospective sub-view full-viewport and VIEW the pixels; resolve `/research` lab sort/`N=` controls by `aria-label`. A blank / wrong-surface / shared-byte frame is a rejected capture (recurring iters 3/5/6/7/9/13/15/17/18/26/27).
- **The FENCE is critical** — verify in the UI that the smoothed P(bear) + true-bear dating appear ONLY under the explicitly-labelled "Retrospective (full-sample / analysis-only)" sub-view, are fetched only on toggle, and that nothing future-aware leaks into the live causal timeline / episode list / recovery signal at a historical as-of D.
- **Do NOT trigger a `kind:"rebuild"` data-manager job** during QA (memory: ~11h, clears ~1370 daily snapshots). If the live host's daily history is in any way degraded, prefer corroborating J-89/J-90 against the live `GET /api/market-phase` (incl. `?retrospective=true`) + `GET /api/research/recovery-turn-edge` payloads (curl) plus the FAST targeted tests over a destructive rebuild.
- After J-89/J-90 close green on LIVE evidence with no regression and COHERENCE-PASS, the next cluster is J-91 + J-92 at FULL depth (J-91 the downtrend-conditioned three-angle opportunity study consuming this market-phase + recovery-turn layer; J-92 the FRED macro feed + `MacroSeries` table, config-default-off so existing figures stay byte-identical), then the J-93/J-94/J-96 dynamic point-in-time universe cluster with J-95's data-walled envelope.
