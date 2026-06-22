# Goal Iteration 45 — Research-labs cluster: severity-velocity × regime study + lab reliability/route-split

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 45
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-103, J-104
- **Required-still-passing journeys:** J-101, J-102, J-97, J-98, J-77, J-91, J-72, J-29, J-32, J-63, J-65, J-51, J-18, J-07
- **Anti-goal reminders (verbatim from docs/goal.md coherence invariants):**
  - **Single source of truth** — six scores + bucket + setup computed once; read identically everywhere (J-06).
  - **No recompute in the read path** — reads serve persisted-snapshot values; create-once on first view is the only blessed compute.
  - **Snapshots immutable** — `scanner_runs`/`scanner_results`/`*_scores` never mutated; `forward_returns` separate append-only.
  - **No lookahead** — as-of-D uses bars ≤ D; forward returns bars > D; unit-tested. Post-D chart region is labelled display-only.
  - **Exactly one date selector** — the global as-of control drives every date-scoped page; `?asof` is its serialization, never a second state; the Research as-of toggle is a MODE, not a second date state.
  - **No fabricated data** — partial horizons / low samples → NA + n; never a fabricated row.
  - **No order/execution path** — research-only. *(critical)*
  - **Every feature navigable** from the sidebar; no second home for an existing entity.
  - **Honest limitations surfaced** — the J-103 verdict must state verbatim that on the committed seed rising stress-velocity under a red regime preceded a bounce, not continuation (hypothesis NOT supported on this bull-dominated window), plus the survivorship / underpowered-for-crashes caveats.

## GOAL

Deliver the final two buildable Must-haves: a new **Severity-velocity × Regime forward-return study** at its own `/research/severity-velocity` sub-route (J-103), and a **research-labs reliability pass** that caches the two remaining uncached studies, bounds the downtrend full-table scan, and splits the monolithic `/research` page into lazy-loaded `/research/*` sub-routes behind a hub so at most one heavy fetch fires per page (J-104).

## BACKGROUND

J-103 and J-104 are the last two FAILING buildable Must-haves (journey-history: both `failing`, first recorded in iter-44 which built only J-101/J-102). The iter-44 evaluator (CONTINUE) explicitly prescribed this iteration: "iter-45 FULL — build the research-labs cluster J-103 + J-104." Both are NOT data-dependent (goal.md:2379-2387) — fully buildable and verifiable offline against the committed 2021-2026 seed. J-104's route split is a NAV-SKELETON change (the `/research` monolith becomes a hub linking to new `/research/factor-combination`, `/research/event-study`, `/research/regime-setup-pattern`, `/research/downtrend-opportunity`, plus the J-103 `/research/severity-velocity`), so a `blueprint.reapproval-requested` is filed this iteration and the blueprint Information Architecture + Data Contract are updated additively. Depth is **full** because the work crosses backend (new study + cache + as-of-bounded query) and frontend (new route + page-split) boundaries, adds backend tests beyond browser smoke, and gates GOAL_ACHIEVED candidacy on the full pytest suite.

Lessons applied (from lessons.md / evaluator log):
- **iter-38/39/44 cache-schema keystone:** J-103's study is served through the `EventStudyCache` + `_dataset_version` idiom — if a new cache `kind`/schema is introduced, fold a schema token into the cache key and unit-test the additive field against an ALREADY-POPULATED cache row, never a fresh compute.
- **iter-20/21 test_db trap:** J-103/J-104 reuse the EXISTING `event_study_cache` table (a new `kind` on `compute_samples`/`EventStudyCache`, not a new table). If any new `table=True` model is added, register it in `apps/backend/tests/test_db.py`'s expected-tables guard (`RESEARCH_CACHE_TABLES`-style group). Any float/int literal in an engine CALC_FILE must be a named/config constant (`test_no_magic_numbers`).
- **iter-23/24/32 blanket-guard trap:** before declaring done, grep `apps/backend/tests/` for `set(payload) ==` / `served == ...` byte-equality guards on any touched research endpoint and update them in the SAME iter (J-104 must keep every served figure byte-identical — assert it).
- **iter-27/28 selector false-negative:** browser-QA must resolve `N=` sort/drill controls by `aria-label`, not visible `text()` (labels live in nested `<span>`).
- **iter-38/39/40/42/43 Playwright-fallback + md5 hygiene:** Chrome MCP CDP has emptied the evidence dir on iters 38/39/40/42; PLAN the Playwright fallback UP FRONT, md5sum the evidence dir FIRST, reject blank/skeleton/byte-identical frames; on any honest-empty / early-as-of leg capture the RENDERED NA card, not a "Checking backend…" skeleton (iter-44 UT-09 caveat).
- **MEMORY pool-exhaustion:** NEVER concurrently probe heavy `/research/*` (or `/api/data`) endpoints while load-testing — the pool exhausts. J-104's whole point is at-most-one-heavy-fetch-per-page; verify it without firing them all at once.
- **iter-11/29/37 suite gate:** hand the full pytest suite to the pump nohup-async; gate GOAL_ACHIEVED candidacy on the FLUSHED `0 failed, EXIT 0` line; NEVER block the evaluator on the in-flight suite.

## IN SCOPE

### Backend

**J-103 — Severity-velocity × Regime forward-return study**
- [ ] New read-only study `research:compute_severity_velocity_study(session, horizon, view, as_of, cfg)` — a regime-family × velocity-sign matrix (mean forward return, win-rate, N per horizon 5/10/20/60) over the stored append-only `forward_returns` (benchmark SPY) joined to the served `severity_velocity` (J-102, from the market-phase timeline) + the stored regime label per snapshot date. A pure GROUPING of stored data — recomputes NO canonical return (Single source of truth; No recompute in the read path).
- [ ] Served from a **derived-once, cached aggregate** via the EXISTING `EventStudyCache` + `_dataset_version` idiom (a new study `kind`; figures byte-identical, refresh only on dataset change — the J-72 performance contract). Do NOT add a new table if the existing cache table suffices; if a new cache shape is needed, fold a schema token into the cache key (iter-38/39 discipline) and register any new `table=True` model in `test_db.py`.
- [ ] New read-only endpoint `GET /api/research/severity-velocity` (`horizon`/`view`/`as_of` params mirroring `/api/research/event-study`). Forward returns use only bars dated > D (No lookahead); NA/partial-honest where samples are insufficient.
- [ ] New `N=` cohort `kind` on `samples.py` `compute_samples` (mirroring `_regime_setup_pattern_samples`/`_recovery_turn_samples`) so each cell's `N=` chip drills into `GET /api/research/samples` reproducing the exact cohort; per-cell total == published N in both Episodes+Pooled and All-history+As-of (count-coherence keystone; reconcile validation so every displayable cell resolves without a 4xx — the J-82 lesson).
- [ ] Regime-family + velocity-sign vocabularies config-backed (no hardcoded lists; no magic numbers).

**J-104 — Research-labs reliability**
- [ ] (a) Cache `compute_factor_combination` and `compute_regime_setup_pattern_study` via the EXISTING `EventStudyCache` + `_dataset_version` pattern (already used by `event_study_cached` / `downtrend_opportunity_cached`), refreshing on dataset change — so repeat requests are cache hits, not full recomputes. Served figures BYTE-IDENTICAL (asserted).
- [ ] (b) Bound the full `select(ScannerRun)` table scan in `_downtrend_opportunity_observation_set` with `where(ScannerRun.asof_date <= as_of)`, and pass the as-of bound through the shared `_run_position_index` callers, so episodes-mode reads no longer load the entire run table.

### Frontend

**J-103**
- [ ] New lazy-loaded sub-route `app/research/severity-velocity/page.tsx` rendering the regime-family × velocity-sign matrix (mean forward return / win-rate / N per horizon), horizon selector, Episodes⇄Pooled (J-63) + As-of⇄All-history (J-32) modes, defaulting to the all-history aggregate. Every `N=` chip opens `/research/samples` in a NEW tab (J-65) carrying `?asof` (J-50).
- [ ] A plain-language **verdict** computed from the served figures plus the honest caveats VERBATIM — documenting that on the committed seed **rising stress-velocity under a red regime preceded a bounce, not continuation** (hypothesis NOT supported on this window), with the survivorship / bull-dominated-sample / underpowered-for-crashes caveats. NA/partial cells shown honestly, never fabricated.

**J-104**
- [ ] Split the monolithic `app/research/page.tsx` so `/research` becomes a **hub** that links to the new sub-routes `/research/factor-combination`, `/research/event-study`, `/research/regime-setup-pattern`, `/research/downtrend-opportunity`, and `/research/severity-velocity`. Each heavy lab lives on its own route and fetches only on that route (lazy / fetch-on-expand-or-visible) so at most ONE heavy computation runs per page.
- [ ] The existing `N=` samples drill-downs keep working from the relocated labs (deep-linkable; no orphan surface). Each lab reachable from the sidebar Research home.

### New user-facing capability
A new Research study answers "does rising/falling stress under a given regime predict the next move?" with a regime × velocity-sign forward-return matrix and an honest plain-language verdict. The Research section becomes a hub of fast, individually-loaded labs instead of one page that fires four heavy fetches at once.

### New information displayed
The severity-velocity × regime matrix (mean forward return, win-rate, N per 5/10/20/60-day horizon) and its verdict + caveats. No new canonical value — the matrix is a grouping of already-stored forward returns by the already-served severity-velocity and stored regime label.

### New user actions
Navigate into each research lab from the `/research` hub; select horizon and Episodes/Pooled / As-of/All-history modes on the severity-velocity study; click any `N=` chip to open the reproducing cohort in `/research/samples` (new tab).

### UI surface changes
New routes: `/research/severity-velocity`, `/research/factor-combination`, `/research/event-study`, `/research/regime-setup-pattern`, `/research/downtrend-opportunity`. `/research` becomes a hub. `/research/samples` unchanged (drill-downs keep working).

### Product surface delta
Research moves from a single heavy monolith to a hub-of-labs IA; a new conditional forward-return study is added. No canonical score, return, membership, or the Risk-Off→Actionable gate changes.

### Blueprint conformance
All new pages live UNDER the existing **Research** top-level nav home in the Information Architecture (no new top-level section). The split into `/research/*` sub-routes restructures the Research home's child layout (a nav-skeleton change within Research), so a `blueprint.reapproval-requested` is filed AND the blueprint IA + Data Contract are edited additively this iteration. `/research/severity-velocity` and the four relocated labs are reachable and deep-linkable from the `/research` hub (≤2 clicks from the persistent nav; no orphan surface).

### Data-contract additions
- **Severity-velocity × Regime forward-return matrix (J-103)** — a regime-family × velocity-sign matrix of mean forward return / win-rate / N per horizon (5/10/20/60). Single canonical computing module: `research:compute_severity_velocity_study` (a read-only GROUPING over stored `forward_returns` joined to the served `severity_velocity` (J-102) + stored regime label — recomputes no canonical return). Single serving endpoint: `GET /api/research/severity-velocity` (cached via the EXISTING `EventStudyCache` + `_dataset_version`). This introduces NO new canonical value — `severity_velocity` is already a registered Data-Contract value (J-102 row, served by `/api/market-phase`); the forward returns are already the registered `forward_returns` stored value. The study READS both from their registered canonical sources and never recomputes either. J-104 adds NO new displayed value (a pure caching / query-bounding / lazy-load + page-split performance refactor — byte-identical figures).

## OUT OF SCOPE

- Any change to a canonical score / return / membership / regime / phase / severity value, or the Risk-Off→Actionable gate (J-07).
- Any new date state (the Research As-of toggle is a MODE; the single global as-of stays the only date control — J-18).
- Any order/execution / trade-signal path (research evidence only — critical anti-goal).
- The J-85 snapshot rebuild (~11h destructive; the data is correct — do NOT trigger `kind:"rebuild"`).
- The pre-2021 deep-history (J-95) leg of J-103's empirical power — non-halting; the study is green on the seed now.
- J-22 / J-23 / J-24 (data-walled, non-vetoing — honest blocked-NA).
- A new public macro endpoint or any macro change (J-92 unchanged).

## DEFINITION OF DONE

- [ ] J-103 passes via browser-qa-agent on LIVE rendered evidence: the regime × velocity-sign matrix renders at `/research/severity-velocity` with mean forward return / win-rate / N per horizon; the verdict states the hypothesis is NOT supported (rising stress under a red regime → bounce) with the verbatim survivorship / bull-dominated / underpowered-for-crashes caveats; an `N=` chip opens the reproducing cohort in `/research/samples` (new tab) whose total equals the published N.
- [ ] J-104 passes: `/research` is a hub linking to each lab; navigating to any one lab fires at most one heavy fetch (the other labs do not load on that page); every relocated lab's figures are byte-identical to before (asserted); the `N=` drill-downs still work.
- [ ] Required-still-passing journeys remain green (replay / live smoke): J-101, J-102, J-97, J-98 (Dashboard cross-view + severity-velocity); J-77, J-91, J-72, J-29, J-32, J-63, J-65, J-51 (existing labs + samples count-coherence); J-18 (0 native `input[type=date]`, CRITICAL) and J-07 (Risk-Off → 0 Actionable, CRITICAL).
- [ ] No anti-goal violation introduced (verify by source: no new date state, no recompute in the read path, no order/execution path, no magic numbers in engine CALC_FILES, every relocated lab navigable from the Research home).
- [ ] Unit/integration tests pass; full pytest suite flushes `0 failed, EXIT 0` (nohup-async via the pump — never block the evaluator on the in-flight suite). Any `set(payload) ==` / `served == ...` byte-equality guard on a touched research endpoint is updated in this same iter.
- [ ] `blueprint.reapproval-requested` filed (one-line reason for the `/research/*` nav split) and the blueprint IA + Data Contract edited additively.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-dev.md`.

## TESTING REQUIREMENTS

- **Browser (LIVE, Playwright fallback pre-planned; md5sum the dir FIRST):**
  - J-103: `/research/severity-velocity` matrix rendered (regime × velocity-sign cells with mean fwd return / win-rate / N per horizon); the verdict + verbatim caveats text visible; an `N=` chip (resolved by `aria-label`, not visible text) opens `/research/samples` in a new tab with total == published N. On an early/honest-empty leg capture the rendered NA card, not a "Checking backend…" skeleton.
  - J-104: from `/research` (hub), navigate to one lab and confirm only that lab's heavy fetch fires (the others do not load on that route); confirm each relocated lab is reachable + deep-linkable and its figures match the pre-split values.
  - Required-still-passing live smoke: J-18 (0 native date inputs), J-07 (Risk-Off → 0 Actionable), J-101/J-102/J-97/J-98 (Dashboard cross-view + severity-velocity line/tooltip unchanged), J-65/J-51 count-coherence on a relocated lab.
- **Unit/integration:**
  - `compute_severity_velocity_study`: regime-family × velocity-sign grouping correctness on a synthetic seed; strictly-causal (forward returns from bars > D only — no-lookahead tail-invariance like `forward_return`); NA/partial below min-sample; cache byte-identity (figures identical fresh-compute vs cache HIT, refresh on dataset change — assert against an ALREADY-POPULATED cache row, not a fresh compute).
  - Samples cohort `kind` for the severity-velocity study: drill-down total == published cell N in Episodes+Pooled and All-history+As-of; every displayable cell resolves without a 4xx.
  - J-104(a): `compute_factor_combination` + `compute_regime_setup_pattern_study` served from cache return figures byte-identical to a direct compute; cache refreshes on dataset change.
  - J-104(b): `_downtrend_opportunity_observation_set` + `_run_position_index` are as-of-bounded — assert the run set scanned excludes `asof_date > as_of` (no full-table scan) and figures stay byte-identical.
  - Reconcile any `set(payload) ==` / `served == ...` byte-equality / shape guard on touched research endpoints (grep `apps/backend/tests/` first).
  - `test_no_magic_numbers` and `test_db::test_create_all_produces_expected_tables` pass (no new magic literal; if any new `table=True`, it is registered).
- **Error cases:** an empty / insufficient-sample cohort renders an honest NA cell (never a fabricated row); an invalid `view`/`horizon` param → 422; an `N=` drill-down for a zero-N cell → explicit honest empty state, not a 4xx that breaks the chip.

## NOTES

- All 7 research backend endpoints already exist (`factor-lab`, `factor-combination`, `event-study`, `regime-setup-pattern`, `recovery-turn-edge`, `downtrend-opportunity`, `samples`); J-103 adds the 8th (`severity-velocity`). The `severity_velocity` value + its `config.market_phase.severity_velocity_window` already exist (built iter-44 for J-102) — J-103 READS the served value, never recomputes a slope.
- The current frontend `/research` is a single ~140KB `app/research/page.tsx` with only a `samples` child — J-104's split into `/research/*` sub-routes is therefore a genuine nav-skeleton restructure (hence the `blueprint.reapproval-requested`). Run-goal.sh auto-approves the blueprint change by default and continues; it pauses only under `--require-blueprint-approval`.
- Reuse the EXISTING `event_study_cache` table for J-103's cached aggregate and J-104(a)'s caching (a new study/cohort `kind`), avoiding the iter-20 new-table trap. If a new `table=True` model is unavoidable, register it in `test_db.py`'s `RESEARCH_CACHE_TABLES`-style group in the SAME iter.
- After J-103 + J-104 land green with a flushed-GREEN suite + COHERENCE-PASS + zero regression, every buildable Must-have (J-01..J-21, J-25..J-104) is positive-evidenced and the next evaluation is a sound GOAL_ACHIEVED candidate. J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md:105-108).
