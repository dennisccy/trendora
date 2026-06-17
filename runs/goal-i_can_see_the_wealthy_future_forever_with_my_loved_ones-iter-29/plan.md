# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29 Execution Plan

Foundational read-only **Market Phase & Severity** layer for target journeys **J-87 + J-88**. A new
strictly-causal derivation (phase label + 0–100 severity + named breakdown + deterministic filtered
P(bear)), served by a NEW cached `GET /api/market-phase` keyed by `dataset_version` (the J-72
`event_study_cache` pattern), rendered as a NEW Dashboard panel. NO new snapshot column, NO rebuild,
NO change to any canonical stock score / bucket / setup / regime / Risk-Off→Actionable gate.

This is an **in-place resume after GOAL_ACHIEVED** (goal.md extended with J-87..J-96). It is NOT a
GOAL_ACHIEVED candidate — J-89..J-96 remain unbuilt; expect the evaluator to verdict CONTINUE on a
clean pass.

## What to Build

- **Config — `market_phase:` section** (new typed, validated `BaseModel` in `config.py`): phase labels
  (Expansion / Pullback / Correction / Bear / Recovery) + phase edges; severity component **weights**
  (trailing-peak drawdown depth, time-underwater, stored regime score/trend, breadth-below-200DMA,
  `^VIX` gate) with a **weights-sum-~1.0 validator mirroring `RegimeCfg._validate` / `_require_complete_weights`**;
  drawdown + time-underwater thresholds; the `^VIX` gate parameter. NO literal in calc code.
- **Config — `regime_switching:` block** (new typed, validated `BaseModel`): the 2×2 transition matrix
  and per-state (bear / risk-on) emission parameters, consumed **verbatim** — NEVER EM-fit at serve
  time. (An optional committed offline calibration script may produce these params; running it live is
  OUT OF SCOPE — only the committed config params are read.)
- **New derivation engine `app/engine/market_phase.py`** — added to `test_no_magic_numbers` `CALC_FILES`,
  carrying NO threshold literal. For a resolved as-of date D, a pure function of stored immutable
  snapshots + index bars dated ≤ D:
  - discrete **phase** + 0–100 **severity** with each named component value disclosed. Trailing peak =
    `max(close)` over `[start, D]` via `bars_asof`; time-underwater counts trading days ≤ D; regime /
    breadth / trend read **VERBATIM from the stored `ScannerRun` rows ≤ D** (the same rows
    `regime_history.get_regime_history` reads) — regime is NEVER recomputed.
  - deterministic forward **Hamilton FILTERED** P(state=bear | observations ≤ D): a closed-form
    recursion over observations dated ≤ D only, using the config transition matrix + emission params
    verbatim. The **SMOOTHED** (full-sample) probability is NEVER computed/served here (reserved for the
    later J-89 retrospective surface).
  - **NA / partial** for any window with insufficient history — never a fabricated phase / severity /
    probability.
- **New read-only endpoint `GET /api/market-phase?as_of=…`** (`app/api/market_phase.py`): resolves the
  as-of via the SAME `resolve_as_of_date` semantics every read endpoint uses, **computes-once-per-
  resolved-as-of and caches behind a `dataset_version` stamp** by REUSING `research._dataset_version`
  (single-source the stamp with J-72). Registered in `apps/backend/main.py` (import tuple + an
  `app.include_router(market_phase.router, prefix="/api")` line). NO new column on
  `scanner_runs`/`scanner_results`/`forward_returns`; NO rebuild.
- **New Dashboard panel** `components/market-phase-card.tsx` (mirrors `major-indexes-card.tsx`),
  mounted on `app/page.tsx` beside `<MajorIndexesCard />`. Fetches `GET /api/market-phase` for the
  SINGLE global as-of read from `useAsOf()` — **NO new date `useState`, NO `window`/`document` keydown
  listener**. Renders the phase label, the 0–100 severity with its **named component breakdown**
  (explainable — never a bare number), and the 0–1 **P(bear)** with its observation vector disclosed.
  NA / partial → explicit honest empty/partial treatment. Dates via `lib/dates.ts` (J-42). Add a
  `fetchMarketPhase` + types to `lib/api.ts`.

## Caching decision (resolve before coding)

Prefer a **standalone create-all-managed cache table** (e.g. `MarketPhaseCache`, mirroring
`EventStudyCache`) keyed by `(asof_key, dataset_version)`, OR a **compute-once-per-request keyed by
`dataset_version` with NO new table**. Either is acceptable per the spec.
- If a NEW `table=True` model is added → it MUST be registered in `test_db.py`'s expected-tables set
  (add to `RESEARCH_CACHE_TABLES` or a sibling set; see `test_create_all_produces_expected_tables`)
  AND it is a STANDALONE table so the `_ADDITIVE_COLUMNS` trap does not apply (it is mutable
  derived/cache state, NOT a snapshot — same reasoning `EventStudyCache` documents).
- Reuse `research._dataset_version(session)` for the stamp either way — do NOT duplicate the stamp
  logic. The cache MUST refresh when `dataset_version` changes (no stale figure); cached == uncached
  byte-for-byte.

## Agents Required

- backend-data: yes -- config sections + validators, the `market_phase` derivation engine (phase +
  severity + filtered Hamilton P(bear)), the cached `GET /api/market-phase` endpoint + registration,
  and all backend unit/integration tests.
- frontend-ux: yes -- the Market Phase & Severity Dashboard panel + `lib/api.ts` client wiring,
  mounted on `app/page.tsx`, reading the single global as-of.
- developer: yes -- this project runs a single developer agent handling both backend and frontend per
  the plan above (TDD; full backend pytest suite is the gate, handed to the pump nohup-async).

## Frontend Present
yes

## Files to Create/Modify

- `apps/backend/app/config.py` -- add `MarketPhaseCfg` (weights + edges + thresholds + VIX gate, sum-~1.0 validator) and `RegimeSwitchingCfg` (2×2 matrix + per-state emission params), wired into the root `Config` model + validated at load.
- `apps/backend/config.yaml` (or the active config file) -- add the `market_phase:` and `regime_switching:` sections with real weights (summing ~1.0), edges, thresholds, transition matrix, emission params. NO magic number left in code.
- `apps/backend/app/engine/market_phase.py` -- NEW. The read-only causal derivation: phase + 0–100 severity + named breakdown + forward FILTERED Hamilton P(bear), over stored `ScannerRun` rows + index bars ≤ D; NA/partial on insufficient history. Added to `CALC_FILES`.
- `apps/backend/app/api/market_phase.py` -- NEW. `GET /api/market-phase?as_of=…` router; resolves as-of, serves the cached derived layer keyed by `_dataset_version`.
- `apps/backend/main.py` -- add `market_phase` to the `from app.api import (...)` tuple + an `app.include_router(market_phase.router, prefix="/api")` line.
- `apps/backend/app/models.py` -- NEW `MarketPhaseCache` model ONLY IF the standalone-table cache approach is chosen (mirror `EventStudyCache`; otherwise omit).
- `apps/backend/tests/test_no_magic_numbers.py` -- add `app/engine/market_phase.py` to `CALC_FILES`.
- `apps/backend/tests/test_db.py` -- add the new cache table to the expected-tables set ONLY IF a new `table=True` model was added.
- `apps/backend/tests/test_market_phase.py` -- NEW. No-lookahead tail-invariance, determinism, filter causality, config-weights validation, cache correctness, 2022-bear reproduction, single-source/gate invariance, error/NA cases (see Key Test Scenarios).
- `apps/frontend/components/market-phase-card.tsx` -- NEW. The Dashboard Market Phase & Severity panel (mirrors `major-indexes-card.tsx`).
- `apps/frontend/app/page.tsx` -- mount `<MarketPhaseCard />` beside `<MajorIndexesCard />`.
- `apps/frontend/lib/api.ts` -- add `fetchMarketPhase(asof, signal)` + the response types.
- `apps/frontend/components/market-phase-card.test.ts(x)` (or equivalent) -- optional frontend unit per existing convention.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-29-dev.md` -- dev handoff.

## UI Evolution

- New user-facing capability: At any as-of date the user sees the market's discrete phase, a 0–100
  severity score with its named drivers, and a deterministic bear-probability — context for *where in
  the cycle the market is*, derived only from information available at D.
- New information displayed: A **Market Phase** label, a **0–100 severity** score + its component
  breakdown, and a **0–1 filtered P(bear)** + its observation vector — for the resolved as-of date.
- New user actions: None beyond reading the panel; it re-points with the single global as-of (no new
  control, no new date state).
- UI surface changes: One new panel on the Dashboard (`/`), beside the existing Major-indexes & regime
  card. No new page, no new route.
- Navigation changes: none.

## Visual Requirements

- Component patterns: `Card` / `CardHeader` / `CardTitle` / `CardContent` (mirror
  `major-indexes-card.tsx`); reuse `ComponentBreakdown` / `ScoreBadge` / `Badge` for the named severity
  breakdown and phase label so the explainable-score treatment matches the existing regime/score cards.
- Layout: full-width card in the Dashboard grid flow, placed directly after `<MajorIndexesCard />`;
  phase label + P(bear) on the header row, severity + named component breakdown in the body.
- Key visual effects: match the established Dashboard card style (existing surface/border tokens,
  `lib/dates.ts` ISO date stamp "as of D"); regime label color via the existing `regimeVariant` helper
  so the panel's regime read matches the Dashboard regime card (J-06 coherence).
- States to handle: loading (skeleton like the index card), NA/partial (explicit honest empty
  treatment — never a fabricated phase/severity/probability), error (backend-unreachable message
  styled like the index card's error state — nothing fabricated).

## Key Test Scenarios

- **Browser (J-87):** Dashboard panel renders phase label + 0–100 severity + named component
  breakdown; stepping the GLOBAL as-of into the 2022 window deepens to Bear / high severity; a 2024
  date reads Expansion/Recovery; the SAME date reads the SAME phase/severity on reload (coherence).
- **Browser (J-88):** the panel shows a 0–1 P(bear) with its observation vector beside the phase;
  2022 → P(bear) toward 1; 2023/2024 → falls back; an insufficient-history early date → NA (never a
  fabricated probability).
- **Browser smoke:** J-06 (regime label on the panel == Dashboard regime card == `/stocks` header for
  the same date), J-18 (no second date input introduced), J-49 (major-indexes card unchanged).
- **Unit — no-lookahead tail-invariance (critical):** removing bars dated > D never changes D's phase /
  severity / filtered P(bear) — asserted the way `forward_return` proves tail-invariance.
- **Unit — determinism:** fixed config params + fixed seed observations → byte-identical severity and
  byte-identical filtered P(bear) (the filter is NEVER EM-fit at serve time).
- **Unit — filter causality:** the FILTERED P(bear) at D is a function of observations ≤ D only; a
  later observation never changes a past date's filtered value.
- **Unit — config validation:** severity weights must sum ~1.0 or config is rejected at load (mirror
  `regime.weights`); a missing emission param / malformed transition matrix is rejected at load; the
  new module passes `test_no_magic_numbers`.
- **Unit — cache correctness:** computed once per resolved-as-of, served from cache, refreshes when
  `dataset_version` changes (no stale figure); cached == uncached byte-for-byte.
- **Unit — 2022-bear reproduction:** a 2022-window as-of → phase=Bear, high severity reproducing the
  seed SPY peak-to-trough, P(bear) trending toward 1; a 2024 as-of → Expansion/Recovery, low P(bear).
- **Unit — single-source / gate invariance:** the panel's regime input equals the stored `ScannerRun`
  regime; NO canonical stock score / bucket / setup / Risk-Off gate changes (a Risk-Off date still has
  ZERO Actionable).
- **Error cases:** invalid/unknown `?as_of` degrades like existing endpoints (latest, never fabricated);
  insufficient-history window → NA/partial.
- **Gate:** full backend pytest suite GREEN (`0 failed`, EXIT 0) — handed to the pump nohup-async, NOT
  blocking the evaluator (iter-11 lesson). No regressions in J-01/J-06/J-07/J-18/J-43/J-44/J-49/J-50/
  J-72.

## Anti-goal guardrails (must hold — flag any violation, do not silently implement around)

- **Strictly causal (≤ D):** every input bar/snapshot used for date D is dated ≤ D; forward-only smoothed
  probability is forbidden on this live path.
- **No recompute of canonical values:** regime/breadth/trend read VERBATIM from stored `ScannerRun`; no
  call into `app.engine.regime`; no stock score/bucket/setup/pattern touched.
- **No magic numbers:** every weight/edge/threshold/VIX-gate/transition-matrix/emission-param from
  config; the new module added to `CALC_FILES`; a sort-tie sentinel must be a named/structural fallback,
  never inline `0.0`.
- **Exactly one date selector:** the panel reads `useAsOf()` only — NO new date `useState`, NO
  `window`/`document` keydown listener. (Cheap decisive static check: grep the panel diff.)
- **No fabricated data:** insufficient history → explicit NA/partial, never a synthesized figure.
- **No new snapshot column, no rebuild, no second date state, no order/execution path.**

## Out of scope (excluded — flag if dev drifts in)

- J-89 (timeline + the SMOOTHED retrospective view), J-90 (recovery-turn edge), J-91 (downtrend-
  conditioned study), J-92 (FRED macro feed / `MacroSeries`), J-93/J-94/J-95/J-96 (dynamic universe).
- Computing/serving the SMOOTHED (full-sample) Markov probability anywhere on the live as-of path.
- Running the offline calibration script live at serve time (only committed config params consumed).
- Any change to a canonical stock score, bucket, setup, pattern, regime score, or the Risk-Off→
  Actionable gate; any new snapshot column or rebuild; any second date state.

## Assumptions (documented, not blocking)

1. **Router registration site:** the spec says `app/api/__init__.py` "or the equivalent registration
   site". The real site is `apps/backend/main.py` — `app/api/__init__.py` is an empty package marker
   and routers are modules under `app/api/` imported by `main.py` (lines 18-32) and mounted via
   `app.include_router(...)` (lines 99-111). The new `market_phase` router is registered there.
2. **Macro leg honestly omitted (J-92 deferred):** the J-88 filter runs on the price / breadth / `^VIX`
   observation vector with the macro leg off-by-default per goal.md:2198 — no FRED dependency this
   iteration.
3. **Cache stamp single-sourced:** `research._dataset_version` is reused for the new layer's stamp
   rather than duplicated (goal.md / spec NOTES explicitly require single-sourcing with J-72).
4. **Seed is sufficient:** the committed 2021-2026 seed holds the 2022 bear (≈ −24.5% SPY peak-to-
   trough) and `^VIX`, so J-87/J-88 are fully offline-provable — neither may be recorded blocked-NA
   for provider reasons, and neither may halt the loop.
