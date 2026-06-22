# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45 Execution Plan

Research-labs cluster: the last two buildable Must-haves. J-103 = a new Severity-velocity × Regime
forward-return study at its own `/research/severity-velocity` sub-route. J-104 = a research-labs
reliability pass (cache the two remaining uncached studies, bound the downtrend full-table scan, split the
`/research` monolith into lazy `/research/*` sub-routes behind a hub). Aligned with goal.md (J-103/J-104
are explicitly the final FAILING buildable Must-haves; both flagged NOT data-dependent, goal.md:2379-2387).
No scope drift detected.

## What to Build
- **J-103 backend** — read-only study `research:compute_severity_velocity_study(session, horizon, view, as_of, cfg)`: a regime-family × velocity-sign matrix (mean forward return, win-rate, N per horizon 5/10/20/60) GROUPING the stored append-only `forward_returns` (benchmark SPY) joined to the already-served `severity_velocity` (J-102) + the stored regime label per snapshot date. Recomputes NO canonical return.
- **J-103 cache** — serve it derived-once via the EXISTING `EventStudyCache` + `_dataset_version` idiom under a NEW sentinel `subject` slot (mirror `recovery_turn_edge_cached`'s `_RECOVERY_TURN_EDGE_SUBJECT` pattern). No new table. If a cache-shape token is needed, fold it into the cache key (iter-38/39 discipline).
- **J-103 endpoint** — `GET /api/research/severity-velocity` (`horizon`/`view`/`as_of` params mirroring `/api/research/event-study`). Forward returns use bars dated > D only (No lookahead); NA/partial-honest below min-sample; invalid `view`/`horizon` → 422.
- **J-103 samples kind** — new cohort `kind` (e.g. `KIND_SEVERITY_VELOCITY`) in `samples.py` `compute_samples` + a `_severity_velocity_samples` builder (mirror `_regime_setup_pattern_samples`/`_recovery_turn_samples`) so each cell's `N=` chip reproduces its exact cohort via `GET /api/research/samples`; per-cell total == published N in Episodes+Pooled AND All-history+As-of; every displayable cell resolves without a 4xx.
- **J-103 config** — regime-family + velocity-sign vocabularies config-backed (no hardcoded lists, no magic numbers).
- **J-103 frontend** — new lazy `app/research/severity-velocity/page.tsx` rendering the matrix + horizon selector + Episodes⇄Pooled (J-63) + As-of⇄All-history (J-32) modes, defaulting to the all-history aggregate; each `N=` chip opens `/research/samples` in a NEW tab (J-65) carrying `?asof` (J-50); a plain-language verdict + the VERBATIM honest caveats.
- **J-104(a)** — cache `compute_factor_combination` + `compute_regime_setup_pattern_study` via the EXISTING `EventStudyCache` + `_dataset_version` pattern; figures byte-identical; refresh on dataset change.
- **J-104(b)** — bound the full `select(ScannerRun)` scan in `_downtrend_opportunity_observation_set` with `where(ScannerRun.asof_date <= as_of)` and pass the as-of bound through the shared `_run_position_index` callers; figures byte-identical.
- **J-104(c) frontend** — split `app/research/page.tsx` so `/research` becomes a HUB linking to `/research/factor-combination`, `/research/event-study`, `/research/regime-setup-pattern`, `/research/downtrend-opportunity`, and `/research/severity-velocity`; each heavy lab on its own route fetching only there (at most ONE heavy fetch per page). Existing `N=` drill-downs keep working from the relocated labs.
- **Blueprint** — file `blueprint.reapproval-requested` (one-line reason: the `/research/*` nav split) and edit the blueprint IA + Data Contract ADDITIVELY. Marker dir: `runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/`.

## Agents Required
- backend-data: yes -- new severity-velocity study + endpoint + samples cohort kind + config vocab; cache factor-combination & regime-setup-pattern; bound the downtrend scan; backend tests.
- frontend-ux: yes -- new `/research/severity-velocity` page (matrix + modes + verdict + `N=` chips); split `/research` into a hub + lazy `/research/*` sub-routes; relocate existing labs preserving drill-downs.
- developer: yes -- implements both backend-data and frontend-ux per TDD; reuse existing cache/samples idioms (no new abstraction); writes the dev handoff.

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/engine/research.py` -- add `compute_severity_velocity_study` + `severity_velocity_cached` (new sentinel `subject`); cache `compute_factor_combination` + `compute_regime_setup_pattern_study` via existing idiom; bound `_downtrend_opportunity_observation_set` + `_run_position_index` callers by `asof_date <= as_of`.
- `apps/backend/app/api/research.py` -- new `GET /api/research/severity-velocity` route; route factor-combination + regime-setup-pattern through the new cached wrappers.
- `apps/backend/app/engine/samples.py` -- new `KIND_SEVERITY_VELOCITY` + `_severity_velocity_samples` cohort builder; register in `ALL_KINDS`.
- `apps/backend/app/config.py` + `config.yaml` -- config-backed regime-family + velocity-sign vocabularies (no magic numbers).
- `apps/frontend/app/research/severity-velocity/page.tsx` -- NEW: regime × velocity-sign matrix, horizon + Episodes/Pooled + As-of/All-history modes, `N=` chips (new tab + `?asof`), verdict + verbatim caveats.
- `apps/frontend/app/research/page.tsx` -- becomes a HUB (links to each lab); heavy lab bodies move out to sub-routes.
- `apps/frontend/app/research/factor-combination/page.tsx`, `event-study/page.tsx`, `regime-setup-pattern/page.tsx`, `downtrend-opportunity/page.tsx` -- NEW lazy sub-routes hosting the relocated labs (fetch-on-route-only); preserve `N=` drill-downs.
- `apps/frontend/lib/api.ts` -- types for the severity-velocity matrix payload + samples cohort.
- `apps/backend/tests/test_research*.py` (+ `test_samples*.py`) -- study grouping correctness on a synthetic seed; strictly-causal no-lookahead tail-invariance; NA/partial below min-sample; cache byte-identity asserted against an ALREADY-POPULATED row (not a fresh compute); samples drill-down total == cell N (both modes); J-104(a) factor-combination + regime-setup-pattern cache byte-identity; J-104(b) run set excludes `asof_date > as_of`; reconcile any `set(payload) ==` / `served == ...` byte-equality guards on touched endpoints (grep `apps/backend/tests/` FIRST); `test_no_magic_numbers` + `test_db::test_create_all_produces_expected_tables` stay green (no new `table=True`).
- `runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/blueprint.md` + `blueprint.reapproval-requested` -- additive IA + Data Contract edits; file the reapproval marker.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-45-dev.md` -- dev handoff.

## UI Evolution
- New user-facing capability: a Research study answering "does rising/falling stress under a given regime predict the next move?" via a regime × velocity-sign forward-return matrix with an honest verdict; the Research section becomes a hub of fast, individually-loaded labs instead of one page firing four heavy fetches at once.
- New information displayed: the severity-velocity × regime matrix (mean forward return, win-rate, N per 5/10/20/60-day horizon) + verdict + caveats. NO new canonical value — a grouping of already-stored `forward_returns` by the already-served `severity_velocity` + stored regime label.
- New user actions: navigate into each lab from the `/research` hub; pick horizon + Episodes/Pooled + As-of/All-history modes on the severity-velocity study; click any `N=` chip to open its reproducing cohort in `/research/samples` (new tab).
- UI surface changes: new routes `/research/severity-velocity`, `/research/factor-combination`, `/research/event-study`, `/research/regime-setup-pattern`, `/research/downtrend-opportunity`; `/research` becomes a hub; `/research/samples` unchanged (drill-downs keep working).
- Navigation changes: `/research` stays the single top-level Research nav home; the labs become its child routes (a nav-skeleton restructure WITHIN Research — no new top-level section, no orphan/second home). Each lab ≤2 clicks from the persistent nav and deep-linkable.

## Visual Requirements
- Component patterns: match the EXISTING research labs exactly — same matrix/table component, horizon selector, mode toggles (Episodes/Pooled, As-of/All-history), and `N=` chip styling already used by event-study / regime-setup-pattern. The hub uses the established lab-card/link pattern. No new component vocabulary.
- Layout: standard page layout under the shared app shell + sidebar; `/research` hub is a list/grid of lab links; each lab page is the relocated lab body, full-width.
- Key visual effects: none new — reuse the existing research-page styling so relocated labs and the new study are visually indistinguishable from before.
- States to handle: loading skeleton per lazy lab; honest NA/partial cells (rendered NA card, NEVER a fabricated row or a "Checking backend…" skeleton on an early/honest-empty as-of leg — iter-44 UT-09 / iter-38-43 lesson); zero-N `N=` chip → explicit honest empty state, not a 4xx that breaks the chip; invalid param → graceful (backend 422).

## Key Test Scenarios
- J-103 (browser, LIVE; Playwright fallback pre-planned, md5sum the evidence dir FIRST, reject blank/skeleton/byte-identical frames): the regime × velocity-sign matrix renders at `/research/severity-velocity` with mean fwd return / win-rate / N per horizon; the verdict states the hypothesis is NOT supported (rising stress under a red regime → bounce, not continuation) with the verbatim survivorship / bull-dominated / underpowered-for-crashes caveats; an `N=` chip (resolved by `aria-label`, NOT visible text — iter-27/28) opens `/research/samples` in a new tab whose total == the published N.
- J-104 (browser): from the `/research` hub, navigate to ONE lab and confirm only that lab's heavy fetch fires (the others do not load on that route — verify WITHOUT concurrently probing all four; pool-exhaustion lesson); each relocated lab is reachable + deep-linkable and its figures match the pre-split values.
- Required-still-passing live smoke: J-18 (0 native `input[type=date]`, CRITICAL), J-07 (Risk-Off → 0 Actionable, CRITICAL), J-101/J-102/J-97/J-98 (Dashboard cross-view + severity-velocity line/tooltip unchanged), J-65/J-51 count-coherence on a relocated lab, plus J-77/J-91/J-72/J-29/J-32/J-63.
- Unit/integration: study grouping correctness on a synthetic seed; strictly-causal no-lookahead tail-invariance; NA/partial below min-sample; cache byte-identity vs an ALREADY-POPULATED row + refresh on dataset change; samples drill-down total == cell N (Episodes+Pooled AND All-history+As-of, every cell resolves, no 4xx); J-104(a) factor-combination + regime-setup-pattern cache byte-identity; J-104(b) run set excludes `asof_date > as_of`; `test_no_magic_numbers` + `test_db` green; any byte-equality guard on a touched endpoint reconciled in-iter.
- GOAL_ACHIEVED gate: full pytest suite flushes `0 failed, EXIT 0` (run nohup-async via the pump — NEVER block the evaluator on the in-flight suite; iter-11/29/37 lesson). After J-103+J-104 land green + COHERENCE-PASS + zero regression, every buildable Must-have (J-01..J-21, J-25..J-104) is positive-evidenced; J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing).

## Assumptions (documented, not blocking)
- Reuse the EXISTING `event_study_cache` table for both J-103's cached aggregate and J-104(a)'s caching via a new sentinel `subject` slot (the `recovery_turn_edge_cached` pattern) — NO new `table=True` model, avoiding the iter-20 new-table trap.
- J-103 READS the already-served `severity_velocity` (J-102, from `/api/market-phase` / the market-phase timeline) and the stored regime label per snapshot date — it recomputes no slope and no canonical return.
- `run-goal.sh` auto-approves the blueprint reapproval by default and continues; the pipeline does NOT pause for blueprint approval unless launched with `--require-blueprint-approval`.

## Out of Scope (excluded — flagged per spec)
- Any change to a canonical score / return / membership / regime / phase / severity value, or the Risk-Off→Actionable gate (J-07).
- Any new date state (the Research As-of toggle is a MODE; the single global as-of stays the only date control — J-18).
- Any order/execution / trade-signal path (research evidence only — CRITICAL anti-goal).
- The J-85 snapshot rebuild (~11h destructive; data is correct — do NOT trigger `kind:"rebuild"`).
- The pre-2021 deep-history (J-95) leg of J-103's empirical power (non-halting; study is green on the seed now).
- J-22 / J-23 / J-24 (data-walled, non-vetoing — honest blocked-NA).
- A new public macro endpoint or any macro change (J-92 unchanged).
