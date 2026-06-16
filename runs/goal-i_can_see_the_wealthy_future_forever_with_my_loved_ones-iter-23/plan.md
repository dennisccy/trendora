# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23 Execution Plan

Target journeys: **J-81** (Themes/Sectors forward-return columns) + **J-82** (Regime × Setup × Pattern table fixes). Depth: **full** (both touch the backend read path → full 11-step pipeline + full pytest gate per the standing iter-21/iter-22 rule). After both land green with a GREEN suite and zero regressions, every buildable Must-have is passing; J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing). The decomposer does NOT declare GOAL_ACHIEVED — that is the evaluator's call.

## What to Build

**J-81 — forward-return columns on Themes & Sectors leaderboards (NEW READ SURFACE of the existing stored `forward_returns`, no new canonical value):**
- Additively attach a `forward_returns` field (one entry per `config.walk_forward.horizons` value — NO hardcoded `[1,5,10,20,60]`) to each `/api/themes` row and each `/api/sectors` row.
- Theme value = EQUAL-WEIGHT mean of member stocks' realized forward returns at that horizon; sector value = the ETF's OWN realized forward return. Both computed by the SAME `forward_testing:_leadership_returns` builder Backtest's Top Themes / Top Sectors already use — read VERBATIM from the stored `forward_returns` table for the resolved as-of run. Absent members skipped (never counted as 0); `None`/NA when no member / no stored row.
- Build the per-horizon `ret_by_symbol` map ONCE per request (reuse the `_forward_returns_by_symbol` read pattern) — no second query per horizon per row.
- Render five sortable, colour-graded, NA-honest columns (1d/5d/10d/20d/60d) per row on `/themes` and `/sectors`, REUSING the existing shared `@/components/forward-return` helper (`fmtPct` + `returnClass`) — no parallel formatter. Sort is the J-48 view-transform contract (re-orders rendered rows only; default stays served theme/sector rank; recomputes/refetches nothing).

**J-82 — Regime × Setup × Pattern table view/serve fixes (read-only; no canonical value changes):**
- (a) NA-last sorting: every numeric RSP column sort treats a cell as NA using the SAME predicate the cell DISPLAY uses (`low_sample` OR `n === 0` OR `value === null`) so every displayed-NA row sinks LAST in both directions; present values sort numerically, label columns lexically, stable tie-break preserves served rank.
- (b) Three client-side filter dropdowns (Regime / Setup / Pattern), each default "All", built from the config-driven vocabulary already in the study payload (`regime_labels` / `setups` / `patterns` / `pattern_none`). Pure view transforms (J-56/J-48 contract) that compose with the sort and recompute nothing.
- (c) Samples validation reconciliation: widen `_regime_setup_pattern_samples` to accept EVERY `(regime, setup, pattern)` combination `compute_regime_setup_pattern_study` actually emits — including `pattern = none` (PATTERN_NONE) rows and any groupable regime value (study tie-break is `r["regime"] or ""`, so an empty/None displayable regime must not 4xx). Drill-down `total` MUST EQUAL the row's published `n` in BOTH Episodes & Pooled and BOTH All-history & As-of, using the SAME `_regime_setup_pattern_observations` builder + `_rsp_combination_filter` predicate the study aggregates — never a second grouping. SELECT-only; recompute nothing.
- (d) Pooled default for the RSP section ONLY (Episodes one click away); the rest of `/research` (J-29/J-63) keeps its Episodes default. Prefer the frontend section toggle's initial state so the canonical `compute_regime_setup_pattern_study` default param stays untouched.

## Agents Required

- developer: yes
  - backend-data: yes — J-81 attaches `forward_returns` to `themes_payload`/`sectors_payload` via `_leadership_returns`; J-82(c) widens `_regime_setup_pattern_samples` validation/vocabulary.
  - frontend-ux: yes — J-81 five columns on `/themes` + `/sectors`; J-82 NA-last sort, three filter dropdowns, N= chips for every row incl. `pattern = none`, Pooled default toggle.

## Frontend Present
yes

## Files to Create/Modify

- `apps/backend/app/engine/snapshot_serving.py` — attach `forward_returns` to `_theme_row`/`themes_payload` (~190/209) and `_sector_row`/`sectors_payload` (~156/178) via the `_leadership_returns` projection; build the per-horizon `ret_by_symbol` map once (reuse `_forward_returns_by_symbol` pattern); horizons from `config.walk_forward.horizons`.
- `apps/backend/app/engine/samples.py` — reconcile `_regime_setup_pattern_samples` (~343) validation to accept exactly the combinations `compute_regime_setup_pattern_study` emits (incl. PATTERN_NONE + empty/None displayable regime) reusing the same observation builder + `_rsp_combination_filter`; keep an honest 4xx for genuinely non-emitted combinations.
- `apps/backend/tests/...` — J-81 coherence tests (themes/sectors `forward_returns` byte-equal to Backtest `_leadership_returns` for same run+horizon; NA at/near latest; no recompute/no second query path); J-82 tests (samples accepts every emitted combination incl. `pattern = none`; `total == n` in Episodes+Pooled and All+As-of; J-29/J-63 byte-identical; honest 4xx for a non-emitted combination). Grep any new config key across all inline test config dicts (count grows).
- `apps/frontend/app/themes/page.tsx` — render five sortable, colour-graded, NA-honest forward-return columns reusing `@/components/forward-return`; J-48 sort contract.
- `apps/frontend/app/sectors/page.tsx` — same five columns/contract from the served `forward_returns`.
- `apps/frontend/app/research/page.tsx` — RSP table: NA-last sort using the display predicate; three "All"-default Regime/Setup/Pattern filter dropdowns; ensure every displayed row's N= chip (incl. `pattern = none`) opens `/research/samples` for its exact combination in a new tab without 4xx; RSP section toggle initialises to Pooled.

## UI Evolution (required if Frontend Present: yes)

- New user-facing capability: read each theme's and each sector/industry ETF's realized forward return at 1/5/10/20/60 days directly on the Themes and Sectors leaderboards (no longer only on Backtest), sort by any horizon, and cross-check against Backtest; on Research, sort RSP NA rows honestly to the bottom, narrow by Regime/Setup/Pattern, drill into the exact cohort for every visible row, and default to the Pooled view.
- New information displayed: five per-row forward-return columns on `/themes` and `/sectors`; three filter controls + corrected NA-aware sort on the `/research` RSP table.
- New user actions: click a forward-return column header on `/themes`/`/sectors` to sort; select Regime/Setup/Pattern filters on the RSP table; click an N= chip on any RSP row (incl. `pattern = none`) to open its samples cohort in a new tab.
- UI surface changes: `/themes` and `/sectors` leaderboards gain five sortable forward-return columns; the `/research` Regime × Setup × Pattern section gains three filter dropdowns, NA-last sorting, and a Pooled default.
- Navigation changes: none. No new pages, no new top-level nav. Lands on existing Themes (`/themes`), Sectors (`/sectors`), Research (`/research`), and the Research Samples (`/research/samples`) drill-down — all already in the blueprint Information Architecture. (Blueprint promotes the relevant rows from `[TARGET iter-23+]` to built.)

## Visual Requirements (required if Frontend Present: yes)

- Component patterns: reuse the existing leaderboard table + sortable column-header pattern already on `/themes`/`/sectors` (matching the J-75 forward-return columns on `/stocks`); reuse the shared `@/components/forward-return` cell (`fmtPct` + `returnClass`) for colour-grading — do NOT introduce a parallel formatter. For J-82 use the project's existing select/dropdown control pattern for the three filters and the existing Episodes ⇄ Pooled toggle component.
- Layout: no layout restructure — additive columns within the existing leaderboard tables; the three filter dropdowns sit in the RSP section's existing controls row alongside its toggle.
- Key visual effects: sign-based colour grading on return cells using existing design tokens (positive/negative/neutral); no new effects invented.
- States to handle: NA-honest cells (render NA, never a fabricated 0%) on `/themes`/`/sectors` — especially at/near latest where post-D bars are insufficient; "All"-default filters with an empty-after-filter state on the RSP table; existing loading/empty/error treatments of these pages unchanged.

## Out of Scope (flagged — exclude)

- Any change to how forward returns are COMPUTED or STORED (J-81 reads existing stored rows only; no new column, no new endpoint).
- Any change to the canonical theme/sector scores, the six stock scores, buckets, or setup status.
- Any change to the J-29/J-63 event-study figures or the Episodes default for the rest of `/research` (J-82's Pooled default is scoped to the RSP section only — assert byte-identity).
- A live data fetch — J-22/J-23/J-24 stay data-walled / non-halting; do not attempt to unblock them.
- New top-level nav, new pages, or any second date control.

## Assumptions

- The J-75 forward-return cell helper is already extracted to `@/components/forward-return.tsx` (`fmtPct`, `returnClass`) — verified — so J-81 reuses it directly with no pre-extraction.
- J-82(d) Pooled default is implemented in the frontend section toggle's initial state (cleaner single source; leaves the canonical study default param untouched).
- No new required config key is introduced. If one is unavoidable, the developer adds it to EVERY inline test config dict (grep the new section key across `apps/backend/tests` — the count grows; currently five+).
- The research RSP table already has NA-last sort logic; J-82(a) is a reconciliation to use the SAME NA predicate as the cell display (`low_sample` OR `n === 0` OR `value === null`), not a from-scratch rewrite.

## Full-Suite Handoff (lessons applied)

- Full backend pytest is ~34 min (639+ tests); a subagent cannot finish it (10-min Bash cap + bg job dies on turn-end). The developer runs TARGETED modules (themes/sectors snapshot-serving + forward_testing leadership-returns coherence + samples regime-setup-pattern + research event-study byte-identity) and hands the FULL suite to the pump.
- NEVER make the pump wait for the background full-suite before answering a CLAIMED dispatch (esp. the goal-evaluator) — run it `nohup bash -c '...' &` async and answer promptly with "v1 green + targeted fix tests green + re-run in progress" if the suite isn't done.
- Dev-server cleanup: this is a multi-project machine — never broad-`pkill` `next dev`/`uvicorn`; kill by port only (backend 8835 / frontend 3835).
- Controlled `<select>` browser-QA: drive the new filter dropdowns via native-setter + bubbling `change` event in `eval`, then assert live DOM (Chrome MCP `select` doesn't fire React `onChange` on this frontend).

## Key Test Scenarios

**J-81 (must pass):**
- Set the global as-of to a historical date WITH post-D bars; `/themes` shows five forward-return columns (equal-weight member basket), colour-graded, sortable (J-48, default stays served rank); `/sectors` shows the same five (ETF's own return), sortable.
- A theme value and a sector value on the leaderboards are IDENTICAL to Backtest's Top Themes / Top Sectors at the same date + horizon (J-06 single-source keystone) — value traces to the stored `forward_returns` rows via `_leadership_returns`, no recompute, no second query path.
- Return to latest → all five honestly NA, never fabricated. A theme with no member having a stored return → NA (not 0%); a sector ETF with no stored bar → NA.
- Unit/integration: `/api/themes` and `/api/sectors` rows carry `forward_returns` byte-equal to the `_leadership_returns` projection for the same run+horizon; horizons read from `config.walk_forward.horizons`.

**J-82 (must pass):**
- On `/research`, sort a numeric RSP column both directions → all displayed-NA rows sink to the bottom (predicate matches the cell display).
- Use the Regime / Setup / Pattern filters (each "All" by default) and combine with a sort — pure view transforms, nothing recomputed.
- Click an N= chip on a displayed row INCLUDING a `pattern = none` row → `/research/samples` opens that exact combination in a new tab without error; `total == the row's n`. Proven count-coherent in Episodes + Pooled and All-history + As-of.
- The RSP section defaults to Pooled (Episodes one click away); the rest of `/research` stays Episodes-default and J-29/J-63 figures are byte-identical.
- A genuinely invalid (non-emitted) `(regime, setup, pattern)` combination still returns an honest 4xx (acceptance widened, validation not disabled).

**Required-still-passing (re-verify, no regression):** J-03, J-04, J-06, J-09, J-21, J-29, J-32, J-48, J-51, J-63, J-75, J-77.

**Gate:** unit/targeted tests pass; full pytest suite GREEN (handed to the pump); no anti-goal violation (single source of truth, no recompute in read path, no lookahead, snapshot immutability, no fabricated data, no magic numbers); dev handoff at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-23-dev.md`.
