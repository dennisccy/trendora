# Goal Iteration 23 — Themes/Sectors forward-return columns (J-81) + Regime×Setup×Pattern table fixes (J-82)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 23
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-81, J-82
- **Required-still-passing journeys:** J-03 (Theme Leaderboard), J-04 (Sector/industry Leaderboard), J-06 (score consistency across pages), J-09 (Backtest forward-tested evidence), J-21 (Backtest cohorts horizon-linked returns), J-29 (Setup & Pattern lab event study), J-32 (Research as-of toggle), J-48 (column sorting view-transform), J-51 (research sample-count drill-down count-coherence), J-63 (event-study Episodes/Pooled), J-75 (per-stock forward-return columns), J-77 (Regime×Setup×Pattern study)
- **Anti-goal reminders:**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The relocated as-of-scoped evidence aggregate is likewise derived once per resolved as-of date over the snapshots dated ≤ D, persisted/cached, and read from storage. *(extends Single source of truth)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **No fabricated data.** Partial horizons / low samples → NA + n; never synthesize a return to fill a gap. *(critical)*
  - **Honest forward-test for partial windows.** The forward-return surfaces MUST show NA/partial for horizons or cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate. *(extends No fabricated data)*
  - **No magic numbers.** Horizons, min-sample, and every vocabulary (regime labels / setups / patterns) MUST come from config — no hardcoded horizon list `[1,5,10,20,60]`, no hardcoded status/pattern list in calculation or validation code.
  - **Honest limitations surfaced.** Walk-forward evidence MUST be labelled as carrying survivorship bias.

## GOAL

Surface the five stored forward-return columns (1/5/10/20/60-day) on the Themes and Sectors leaderboards reading the same `forward_returns` Backtest reads (J-81), and fix the four read-only view/serve defects on the Research Regime × Setup × Pattern table — NA-last sorting, Regime/Setup/Pattern filter dropdowns, an N= drill-down that works for every emitted combination, and a Pooled default (J-82).

## BACKGROUND

These are the two remaining buildable (non-data-dependent) Must-have journeys queued in `goal.md` (J-79..J-82, commit 481d8b3); J-79 and J-80 landed green in iter-22 with a verified zero-backend diff. The iter-22 evaluator returned CONTINUE with an explicit full-depth recommendation to build exactly J-81 and J-82, and iter-22 coherence was COHERENCE-PASS (no consolidation owed). Both journeys touch the backend (J-81 adds a forward-return read surface to the themes/sectors payloads; J-82 reconciles the samples validation/vocabulary and tweaks the study default) so they require the full 11-step pipeline and the full pytest gate per the iter-21/iter-22 standing rule for any backend-touching journey. After both land green with a GREEN full suite, every buildable Must-have is passing and J-22/J-23/J-24 remain honestly blocked-NA (non-vetoing) — at which point GOAL_ACHIEVED is appropriate for the evaluator to declare.

The canonical source for J-81 already exists: `forward_testing:_leadership_returns` (`apps/backend/app/engine/forward_testing.py:519`) is the exact read-only projection Backtest's Top Themes / Top Sectors already use — sector = the ETF's OWN stored return, theme = the EQUAL-WEIGHT mean of its member stocks' stored returns over only the members that have a stored return. J-75 (iter-20) already established the mirror pattern on `/stocks` via `snapshot_serving._forward_returns_by_symbol` / `_forward_returns_for_row` (`apps/backend/app/engine/snapshot_serving.py:55-107`) — J-81 follows the same discipline on `themes_payload` / `sectors_payload` (same file, lines 178 / 156).

## IN SCOPE

### Backend
- [ ] **J-81 — Themes leaderboard forward returns.** In `apps/backend/app/engine/snapshot_serving.py`, additively attach to each `/api/themes` row (`_theme_row` / `themes_payload`, ~line 190/209) five forward-return entries (one per `config.walk_forward.horizons` value — NO hardcoded `[1,5,10,20,60]` literal). Each theme value is the EQUAL-WEIGHT mean of its member stocks' realized forward returns at that horizon, computed by the SAME `forward_testing:_leadership_returns` builder Backtest uses (read VERBATIM from the stored `forward_returns` table for the resolved as-of run; absent members skipped, never counted as 0; `None`/NA when no member has a stored return). Build per-horizon `ret_by_symbol` maps once from the stored `forward_returns` for the run (reuse the `_forward_returns_by_symbol` read pattern; do not issue a second query per horizon per row).
- [ ] **J-81 — Sectors leaderboard forward returns.** In the same file, additively attach to each `/api/sectors` row (`_sector_row` / `sectors_payload`, ~line 156/178) the same five forward-return entries, each being the sector/industry ETF's OWN realized forward return at that horizon read via the SAME `_leadership_returns` builder (ETF `sector_etf` → its stored `realized_return`; `None`/NA when no stored row). Industry ETFs without a stored bar render NA honestly.
- [ ] **J-81 — Backtest-coherence assertion.** Add unit/integration tests asserting that, for a historical as-of date with post-D bars, a theme's and a sector's forward return on `/api/themes` / `/api/sectors` is IDENTICAL to the value `GET /api/backtest` exposes for the same date + horizon (Top Themes / Top Sectors via `_leadership_returns`) — single-source proof (J-06). Assert NA at/near latest (insufficient post-bars). Assert no new query path and no recompute (values trace to the stored `forward_returns` rows).
- [ ] **J-82(c) — Samples validation accepts every emitted combination.** In `apps/backend/app/engine/samples.py` `_regime_setup_pattern_samples` (~line 343), reconcile the validation/vocabulary so EVERY `(regime, setup, pattern)` combination the J-77 study (`research:compute_regime_setup_pattern_study`, `apps/backend/app/engine/research.py:1449`) actually emits is accepted — including `pattern = none` (PATTERN_NONE) rows and any regime value the study can group on (note the study tie-break uses `r["regime"] or ""`, so an empty/None regime grouping must not 4xx if it is a displayable row). The drill-down `total` MUST still EQUAL the row's published `n` in BOTH Episodes and Pooled and BOTH All-history and As-of, using the SAME `_regime_setup_pattern_observations` builder + `_rsp_combination_filter` predicate the study aggregates — never a second grouping. Vocabularies stay config-backed (`cfg.regime.labels`, `ALL_STATUSES`, `pattern_keys(cfg)` + PATTERN_NONE) — no hardcoded lists. SELECT-only; recompute nothing.
- [ ] **J-82(d) — Pooled default for the RSP section only.** Make the Regime × Setup × Pattern study section default to `view=pooled` while the rest of the event study (J-29/J-63) keeps its `view=episodes` default. Prefer doing this in the frontend (the section's own toggle initial state) so the canonical `compute_regime_setup_pattern_study` default param is untouched; if a backend default is the cleaner single source, keep it scoped to this section's call site only and assert J-29/J-63 figures stay Episodes-default and byte-identical.

### Frontend
- [ ] **J-81 — Themes page columns.** In `apps/frontend/app/themes/page.tsx`, render five forward-return columns (1d/5d/10d/20d/60d) per theme row from the new served `forward_returns` field, colour-graded by sign (existing design tokens), client-side sortable under the J-48 view-transform contract (re-orders the rendered rows ONLY — recomputes/refetches nothing; default order stays the served theme rank), NA-honest (render NA, never a fabricated 0%). Reuse the existing J-75 forward-return cell/format helper rather than introducing a parallel formatter.
- [ ] **J-81 — Sectors page columns.** In `apps/frontend/app/sectors/page.tsx`, render the same five sortable, colour-graded, NA-honest columns per ETF row from the served `forward_returns` field, same J-48 contract.
- [ ] **J-82(a) — NA-last sorting.** In the RSP table (`apps/frontend/app/research/page.tsx`), make every numeric-column sort treat a cell as NA using the SAME predicate the cell display uses (`low_sample` OR `n === 0` OR `value === null`) so every displayed-NA row sorts LAST in both ascending and descending order; present values sort numerically and label columns lexically, with a stable tie-break preserving the served rank.
- [ ] **J-82(b) — Regime/Setup/Pattern filter dropdowns.** Add three client-side filter dropdowns built from the config-driven vocabulary already in the study payload (`regime_labels` / `setups` / `patterns` / `pattern_none`), each defaulting to "All" — pure view transforms (J-56/J-48 contract) that compose with the sort and recompute nothing.
- [ ] **J-82(c) — N= chip works for every displayed row.** Ensure each displayed row's `N=` chip (incl. `pattern = none` rows) opens `/research/samples` for that exact `(regime, setup, pattern)` combination in a new tab (J-65) without a 4xx, total == the row's n.
- [ ] **J-82(d) — Pooled default toggle.** The RSP section's Episodes ⇄ Pooled toggle initialises to Pooled (Episodes one click away); the rest of `/research` keeps its J-63 Episodes default.

### New user-facing capability
The user can read each theme's and each sector/industry ETF's realized forward return at 1/5/10/20/60 days directly on the Themes and Sectors leaderboards (no longer only on Backtest), sort by any horizon, and cross-check them against Backtest. On Research, the Regime × Setup × Pattern table sorts NA rows to the bottom honestly, can be narrowed by Regime / Setup / Pattern, drills into the exact sample cohort for every visible row, and defaults to the Pooled view.

### New information displayed
Five per-row forward-return columns on `/themes` and `/sectors`. Three filter controls and corrected NA-aware sort on the `/research` RSP table.

### New user actions
Click a forward-return column header on `/themes` / `/sectors` to sort. Select Regime / Setup / Pattern filters on the `/research` RSP table. Click an N= chip on any RSP row to open its samples cohort.

### UI surface changes
`/themes` and `/sectors` leaderboards gain five sortable forward-return columns. The `/research` Regime × Setup × Pattern section gains three filter dropdowns, NA-last sorting, and a Pooled default.

### Product surface delta
Forward-tested evidence becomes legible at the leaderboard level (themes and sectors), not just on Backtest, and the combinations study becomes filterable, correctly sortable, and fully drill-downable — turning a partially-broken evidence table into a usable one.

### Blueprint conformance
No new pages and no new top-level nav section. J-81 lands on the existing **Themes** (`/themes`) and **Sectors** (`/sectors`) homes; J-82 amends the existing **Research** (`/research`) Regime × Setup × Pattern study and its **Research Samples** (`/research/samples`) drill-down. All four homes are already registered in `blueprint.md`'s Information Architecture.

### Data-contract additions
No NEW canonical value. J-81 is a NEW READ SURFACE of the EXISTING stored `forward_returns` table (the "Per-stock forward returns" Data Contract row) via the EXISTING `forward_testing:_leadership_returns` builder — the same value Backtest's Top Themes / Top Sectors already serve. J-82 is read-only view/serve fixes over the EXISTING Regime × Setup × Pattern study + samples drill-down rows — no canonical value changes. The blueprint's "Per-stock forward returns", "Theme score", "Sector/industry score", "Regime × Setup × Pattern combination study", and "Research samples drill-down" rows already register J-81/J-82 as `[TARGET iter-23+]`; this iteration promotes them from TARGET to built.

## OUT OF SCOPE

- Any change to how forward returns are COMPUTED or STORED (J-81 reads existing stored rows only; no new column, no new endpoint).
- Any change to the canonical theme score, sector score, six stock scores, buckets, or setup status.
- Any change to the J-29/J-63 event-study figures or the Episodes default for the rest of `/research` (J-82's Pooled default is scoped to the RSP section only).
- A live data fetch — J-22/J-23/J-24 remain data-walled / non-halting; do not attempt to unblock them here.
- New top-level nav, new pages, or any second date control.

## DEFINITION OF DONE

- [ ] Target journeys J-81, J-82 pass via browser-qa-agent
- [ ] Required-still-passing journeys remain green (especially J-06 single-source, J-21/J-29/J-63/J-77 byte-identity, J-03/J-04 leaderboards)
- [ ] No anti-goal violation introduced (single source of truth, no recompute in read path, no lookahead, snapshot immutability, no fabricated data, no magic numbers all held)
- [ ] Theme/sector forward returns proven IDENTICAL to Backtest's Top Themes / Top Sectors for the same date + horizon (J-06 single-source assertion)
- [ ] RSP samples drill-down proven count-coherent (total == row n) for EVERY emitted combination incl. `pattern = none`, in Episodes + Pooled and All-history + As-of
- [ ] J-29/J-63 event-study figures asserted byte-identical (J-82 changed no canonical value)
- [ ] Unit tests pass; full pytest suite GREEN (handed to the pump — see NOTES); no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-dev.md`

## TESTING REQUIREMENTS

- **Browser:**
  - J-81 — set the global as-of to a historical date with post-D bars; on `/themes` confirm five forward-return columns (1/5/10/20/60d, equal-weight member basket), colour-graded, sortable (J-48); on `/sectors` confirm the same five columns (ETF's own return), sortable; cross-check a theme value and a sector value against Backtest's Top Themes / Top Sectors at the same date+horizon (identical); return to latest → all five honestly NA, never fabricated.
  - J-82 — on `/research`, sort a numeric RSP column both directions and confirm NA rows sink to the bottom; use the Regime/Setup/Pattern filters (combine with a sort); click an N= chip on a displayed row (including a `pattern = none` row) → `/research/samples` opens that exact combination in a new tab without error, total == the row's n; confirm the section defaults to Pooled (Episodes one click away).
  - Required-still-passing re-verify: J-03, J-04, J-06, J-09, J-21, J-29, J-32, J-48, J-51, J-63, J-75, J-77.
- **Unit/integration:**
  - J-81: `/api/themes` and `/api/sectors` rows carry `forward_returns` matching the `_leadership_returns` projection Backtest serves for the same run+horizon (byte-equal); NA where no stored return; horizons read from `config.walk_forward.horizons`; no recompute, no second query path.
  - J-82: `_regime_setup_pattern_samples` accepts every combination `compute_regime_setup_pattern_study` emits (including `pattern = none` and any groupable regime value); drill-down total == study row n in Episodes + Pooled and All-history + As-of; J-29/J-63 event-study figures byte-identical (additive/no-op assertion); RSP Pooled default does not change the rest of the event study's Episodes default.
- **Error cases:**
  - A genuinely invalid `(regime, setup, pattern)` combination the study does NOT emit still returns an honest 4xx (the fix widens acceptance to emitted combinations, it does not disable validation).
  - A theme with no member having a stored return → NA (not 0%); a sector ETF with no stored bar → NA.

## NOTES

- **Depth = full** because both journeys touch the backend read path and the standing iter-21/iter-22 rule requires the full pytest gate for any backend-touching journey. The prior verdict was CONTINUE with an explicit full-depth recommendation for exactly this J-81 + J-82 pairing.
- **Full pytest suite handoff (lessons applied).** Per the project lessons: the full backend suite now runs ~34 min (639+ tests, heavy walk-forward boot) and a SUBAGENT cannot finish it (10-min Bash cap + bg job dies on turn-end). The developer should run TARGETED modules (themes/sectors snapshot-serving + forward_testing leadership-returns coherence + samples regime-setup-pattern + research event-study byte-identity) and hand the FULL suite to the pump; NEVER make the pump wait for the background full-suite before answering a CLAIMED dispatch (esp. the goal-evaluator) — run it nohup-async and answer promptly with "v1 green + targeted fix tests green + re-run in progress" if the suite is not done. Launch any toucher/full-suite run via `nohup bash -c '...' &` so it outlives the wrapper-kill. (Lessons: backend-test-suite-runtime, goal-pump-never-block-evaluator-on-suite, goal-pump-background-helpers-need-nohup.)
- **Config fixtures lesson.** J-81/J-82 should not add new required config keys; if any new typed config field is unavoidable, add it to EVERY inline test config dict — grep the new section key across `apps/backend/tests` (the count GROWS over time). (Lesson: config-fixtures-need-new-required-keys.)
- **Dev-server cleanup lesson.** This is a multi-project machine — never broad-`pkill` `next dev` / `uvicorn`; kill by port (backend 8835 / frontend 3835). (Lesson: dev-server-cleanup-by-port.)
- **J-06 keystone.** The J-81 coherence proof (theme/sector leaderboard == Backtest for the same date+horizon) is the load-bearing assertion the evaluator and coherence-auditor will check; ground every forward-return value in the same `_leadership_returns` output Backtest reads — do NOT build a parallel theme-basket or sector-return computation.
- **J-82 keystone.** The samples 4xx fix is a serve-side reconciliation, not a recompute: widen `_regime_setup_pattern_samples` validation to exactly the set `compute_regime_setup_pattern_study` emits, reusing the same observation builder + combination predicate so `total == n` stays true by construction in both modes and both scopes.
- After J-81 + J-82 land green with a GREEN full suite and zero regressions, every buildable Must-have is passing and J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing) — GOAL_ACHIEVED is then appropriate for the evaluator to decide. The decomposer does not declare it.
