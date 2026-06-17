# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27 Execution Plan

Goal-mode iteration. Depth: FULL. Target journeys: J-85, J-86 (the last two buildable Must-haves).
Both touch the snapshot/forward-returns backend and require the full pytest gate. Coherence was
COHERENCE-PASS at iter-26 — new scope is permitted (not a consolidation pass). On GREEN full suite +
COHERENCE-PASS + zero regression, the next evaluation is a GOAL_ACHIEVED candidate (J-22/J-23/J-24 stay
honestly blocked-NA, non-vetoing).

## What to Build

**J-85 — confirm-gated regenerate-from-scratch snapshot rebuild + coverage diagnostic**
- New `kind="rebuild"` background job in the EXISTING import-job runner that CLEARS the scanner snapshot
  set (`scanner_runs` / `scanner_results` / `*_scores` / `forward_returns`) then CREATE-ONCE recomputes
  every covered trading date over `config.universe.symbols`, reusing the EXISTING J-53 parallel
  multi-date backfill path (`_do_backfill` → `scanner.persist_run_payload` create-once +
  `forward_testing.backfill_run_forward_returns` INSERT-only) and J-66 progress machinery. NEVER an
  in-place UPDATE/overwrite of a live snapshot row (wholesale rebuild only). The committed PRICE seed
  (`bars`/`daily_prices` table + `apps/backend/data/seed/`) is NEVER deleted. Strict no-lookahead
  preserved. Changes NO canonical formula — only the membership scanned over.
- Expose via the EXISTING `POST /api/data/jobs` contract (the new `kind`), confirm-gated by the
  operator; recorded in EXISTING run-history (J-60); progress through EXISTING J-66 surface. NO new
  endpoint, NO new stored column, NO second compute path.
- ADDITIVELY extend `data_manager:compute_coverage` to derive a read-only `absent_from_latest_snapshot`
  count: resolved-universe members (`config.universe.symbols`) absent from the latest scanner snapshot's
  scored set (descriptive derivation over stored bars + resolved universe). Serve it on the SAME
  `GET /api/data` `coverage` block. 0 absent → no diagnostic.

**J-86 — max-drawdown stored once, surfaced everywhere**
- New nullable `max_drawdown` column on the append-only `forward_returns` table (`ForwardReturn`,
  `Optional[float] = Field(default=None)`), computed ONCE per `(run, symbol, horizon)` in the SAME
  `_insert_run_forward_returns` INSERT path beside `realized_return`/`mae`/`mfe`, via a pure helper that
  shares the EXACT no-lookahead NA gate `forward_return`/`forward_excursions` use (a row's `max_drawdown`
  is non-None iff `realized_return` exists — `< horizon` post-bars → no row). This is the iter-14
  `mae`/`mfe` pattern applied verbatim. Definition:
  `MDD = min over j of ( low_j / max(entry_close, high_1…high_j) − 1 )` over the FIRST `horizon`
  post-snapshot bars (date > D), ≤ 0, running peak seeded at the as-of-D close. Horizons from
  `config.walk_forward.horizons` (no hardcoded list).
- Register the column in `apps/backend/app/db.py` `_ADDITIVE_COLUMNS`
  (`ALTER TABLE forward_returns ADD COLUMN max_drawdown <type>`, nullable) so a live DB gains it in
  place. NO new `table=True` model → `test_db.py` SNAPSHOT_TABLES guard unchanged; verify the
  `test_every_model_column_on_existing_table_is_covered_by_additive_registry` guard passes.
- Surface five PAIRED max-drawdown columns/values read VERBATIM from `forward_returns.max_drawdown` (NO
  read-path recompute): `GET /api/stocks` + `GET /api/stocks/{ticker}` (via
  `snapshot_serving:_forward_returns_for_row` / `_forward_returns_by_symbol`, mirroring the J-75
  `realized_return` carrier); `GET /api/themes` + `GET /api/sectors` via the SAME
  `forward_testing:_leadership_returns` builder (theme = equal-weight member-basket drawdown;
  sector/industry = the ETF's own drawdown) — IDENTICAL to Backtest for the same date+horizon (J-06).
- Add an AGGREGATE mean-max-drawdown beside each return stat on Backtest evidence aggregates
  (`GET /api/backtest`) and Research event-study + Regime×Setup×Pattern tables (`GET /api/research/*`),
  with the SAME `n`/min-sample/NA discipline as the return aggregates (mirror the existing
  `mean_mae`/`mean_mfe` aggregation in `research.py`). Derived read-only over stored values.
- Update the `apps/backend/tests/test_api_engine.py` byte-equality guards
  (`test_api_stocks_equals_engine_output`, `test_api_themes_equals_engine_output`,
  `test_api_sectors_equals_engine_output`) for the additive `max_drawdown` served field IN THIS SAME
  ITERATION — strip ONLY the additive key before the canonical byte-equality, then separately assert the
  field + configured horizons exist (the recurring iter-20/23/24 lesson — a correct additive field MUST
  NOT leave the full suite red).

**Frontend**
- `/data`: J-85 coverage diagnostic banner ("N universe members absent from the latest snapshot —
  rebuild to include them"; no banner when N=0) + a confirm-gated "Rebuild snapshots for current
  universe" action that POSTs `kind="rebuild"` and shows progress through the existing
  job-card/Unfinished-imports surfaces (J-66). Confirm modal reuses the J-69 `RemoveConfirmModal`
  pattern (Card + fixed overlay; persistently visible Confirm button outside the scroll region). Dates
  remain job/action parameters — never a second global date control (J-18).
- `/stocks`, Stock Detail, `/themes`, `/sectors`: five paired max-drawdown columns beside the existing
  forward-return columns, colour-graded by magnitude (≤ 0), client-side sortable under J-48 (re-order
  only; recompute/refetch nothing), NA where the return is NA. Reuse/extend the shared
  `apps/frontend/components/forward-return.tsx` cell helper (`fmtPct`/`returnClass`/`Return`) rather than
  authoring a second formatter.
- Backtest + Research tables: display the aggregate mean-MDD beside each return stat (read from the
  served aggregate; no client recompute).

## Agents Required

- developer: yes — implement J-85 (rebuild job kind + coverage diagnostic) and J-86 (MDD column +
  serving + aggregates + frontend columns/banner), TDD, full backend pytest + `tsc --noEmit` gates,
  write the dev handoff.

## Frontend Present
yes

## Files to Create/Modify

Backend
- `apps/backend/app/models.py` — add nullable `max_drawdown: Optional[float] = Field(default=None)` to
  `ForwardReturn` (beside `mae`/`mfe`).
- `apps/backend/app/db.py` — register `("forward_returns", "max_drawdown", "ALTER TABLE forward_returns
  ADD COLUMN max_drawdown <type>")` in `_ADDITIVE_COLUMNS` (nullable).
- `apps/backend/app/engine/forward_testing.py` — new pure `max_drawdown` helper (running-peak, ≤ 0,
  shares the `forward_return`/`forward_excursions` window + NA gate); populate it in
  `_insert_run_forward_returns` beside `mae`/`mfe`; extend `_leadership_returns` (or a paired projection)
  to carry per-row max-drawdown read verbatim from the stored value for themes/sectors/cohort; extend
  `compute_forward_aggregates` to add aggregate mean-MDD beside each return stat.
- `apps/backend/app/engine/snapshot_serving.py` — carry the stored `max_drawdown` on the stocks /
  stock-detail / themes / sectors `forward_returns` row payloads (mirror the J-75/J-81 `realized_return`
  carrier; verbatim read, no recompute).
- `apps/backend/app/engine/research.py` — add aggregate mean-MDD beside each return stat on the event
  study + Regime×Setup×Pattern tables (mirror the existing `mean_mae`/`mean_mfe` aggregation + NA gate).
- `apps/backend/app/engine/data_manager.py` — add `"rebuild"` to `JOB_KINDS`; wire a rebuild branch that
  CLEARS the snapshot set then drives the EXISTING `_do_backfill` create-once recompute over all covered
  dates (reuse J-53 parallel path + J-66 progress); ADDITIVELY extend `compute_coverage` with the
  `absent_from_latest_snapshot` count. Refuse to delete the committed price seed.
- API layer (the `GET /api/data`, `POST /api/data/jobs`, `GET /api/stocks*`, `GET /api/themes`,
  `GET /api/sectors`, `GET /api/backtest`, `GET /api/research/*` routers) — accept the new `kind` and
  serve the additive fields. NO new endpoint.

Frontend
- `apps/frontend/app/data/page.tsx` (+ any helper/modal component) — coverage diagnostic banner +
  confirm-gated rebuild action reusing the `RemoveConfirmModal` (J-69) pattern; re-read coverage +
  run-history + availability after the job completes (the existing reload path).
- `apps/frontend/components/forward-return.tsx` — extend with a max-drawdown cell helper (reuse
  `fmtPct`/`returnClass`); MDD is ≤ 0 so it grades on the negative scale.
- `apps/frontend/app/stocks/page.tsx`, `apps/frontend/app/stocks/[ticker]/page.tsx`,
  `apps/frontend/app/themes/page.tsx`, `apps/frontend/app/sectors/page.tsx` — five paired MDD columns
  (sortable, J-48), NA where return NA.
- Backtest + Research table components (`components/evidence-panels.tsx`,
  `components/return-attribution.tsx`, and the Research RSP/event-study tables) — aggregate mean-MDD
  cells beside each return stat.

Tests
- `apps/backend/tests/test_api_engine.py` — update the three `*_equals_engine_output` byte-equality
  guards (strip the additive `max_drawdown` key, separately assert the field + config horizons).
- New/extended tests in `forward_testing` / `data_manager` / `db` / `research` / `snapshot_serving`
  suites (see Key Test Scenarios).
- Dev handoff: `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-27-dev.md`.

## UI Evolution
- New user-facing capability: the operator can trigger a confirm-gated full snapshot rebuild so
  newly-expanded universe members appear in every read surface; every forward-return figure is now
  paired with a max-drawdown read from the same stored data.
- New information displayed: a `/data` coverage diagnostic ("N members absent from the latest
  snapshot"); five max-drawdown columns on `/stocks`/`/themes`/`/sectors` and the Stock-Detail panel;
  aggregate mean-MDD on Backtest and Research tables.
- New user actions: a confirm-gated "Rebuild snapshots for current universe" button on `/data`; sortable
  max-drawdown column headers (J-48).
- UI surface changes: `/data` (diagnostic banner + rebuild action + its progress card); `/stocks`,
  `/stocks/[ticker]`, `/themes`, `/sectors` (paired MDD columns); `/backtest`, `/research` (aggregate
  mean-MDD cells).
- Navigation changes: none — all work lands on existing IA homes; nav skeleton unchanged (additive
  `[TARGET iter-27]` annotations only, no re-approval).

## Visual Requirements
- Component patterns: reuse the existing leaderboard tables and the `forward-return.tsx` cell helpers
  (`Return`/`fmtPct`/`returnClass`/`SampleSize`); reuse the J-69 `RemoveConfirmModal` (Card + fixed
  overlay) for the rebuild confirm; the diagnostic uses the existing amber/warn banner treatment already
  on `/data` (e.g. the gaps/thin-coverage advisory).
- Layout: sidebar + main content workstation; MDD columns sit to the RIGHT of the existing forward-return
  columns (capture wide/scrolled in QA). The `/data` diagnostic banner sits above the coverage card; the
  rebuild action sits beside the existing job/remove controls.
- Key visual effects: palette tokens only — `text-pos`/`text-neg`/`text-warn`/`text-text-muted` for
  graded cells (MDD is ≤ 0 → grade on the negative/red scale); the warn token for the absent-member
  banner and low-sample aggregates. No arbitrary hex, no invented effects.
- States to handle: loading (job in flight → J-66 progress card + counters never exceeding totals);
  empty (0 absent → NO banner; NA MDD at/near latest → em dash, never a fabricated 0); error (backend
  unavailable → existing "Backend unavailable" treatment, no fabricated cells).

## Key Test Scenarios

Browser (by journey ID)
- J-85: on `/data`, the coverage diagnostic banner renders when members are absent (exercise via the
  served `coverage` absent-count; if 0 absent, source-corroborate the banner branch and assert the
  rebuild action + its confirm-gated modal exist and POST `kind="rebuild"`); trigger the rebuild, confirm
  live J-66 progress, and after completion the snapshot set is regenerated (run-history shows the rebuild
  record; `/stocks` still serves its rows). Verify the committed price seed is intact post-rebuild.
- J-86: at a historical as-of D with post-D seed bars, `/stocks` shows five MDD columns beside the
  forward-return columns (≤ 0, colour-graded, sortable); Stock-Detail shows the same five for that ticker
  (J-06 identity); `/themes` + `/sectors` show paired MDD columns matching Backtest for the same
  date+horizon; Backtest + Research show aggregate mean-MDD; at/near latest every MDD is NA (never
  fabricated). Capture wide/scrolled — MDD columns are to the right.

Unit/integration
- J-85: a test driving the REAL rebuild orchestration over the committed seed asserting (a) it CLEARS
  then CREATE-ONCE recomputes (no in-place UPDATE — assert via row identity/timestamps or a create-once
  guard), (b) determinism (a fresh recompute is byte-identical to itself — reuse the existing
  scanner/forward-test equality suites), (c) the price `bars`/seed table is untouched, (d) strict
  no-lookahead holds; plus a `compute_coverage` test for the absent-member count (correct N; 0 when
  full).
- J-86: an MDD-math test (running-peak, ≤ 0, the no-lookahead tail-invariance the way
  `forward_return`/`forward_excursions` are tested); a test that `forward_returns.max_drawdown` is NULL
  exactly when `realized_return` is absent (same NA gate); the `db.py` `_ADDITIVE_COLUMNS` registry guard
  for `max_drawdown`; J-06 byte-identity of the served MDD to Backtest's `_leadership_returns` for
  themes/sectors; and the updated `test_api_*_equals_engine_output` guards.
- Error cases: the rebuild action MUST be confirm-gated (no destructive surprise); horizons with
  `< horizon` post-bars MUST yield NULL MDD (no fabricated 0); a config without `walk_forward.horizons`
  MUST be rejected (no hardcoded fallback list); the rebuild MUST refuse to delete the committed price
  seed.

Gates
- FULL backend pytest suite GREEN (0 failed, EXIT_CODE=0) — the standing GOAL_ACHIEVED gate. Hand it to
  the pump nohup-async; gate the evaluator on the FLUSHED `0 failed` line, NEVER on the in-flight stream
  (iter-11 lesson; suite ~50-60 min, ~862 tests — do not run inside a dev-turn background).
- `tsc --noEmit` EXIT 0 (the frontend gate — ESLint is not installed).
- Required-still-passing journeys remain green (esp. J-06 single-source, J-08 immutability, J-75/J-81
  forward-return columns unchanged, J-18 one date control).

## Assumptions
- `max_drawdown` column DDL type follows the existing `Optional[float]` columns (`mae`/`mfe`) — a
  nullable REAL/float; the developer matches the exact DDL convention already in `_ADDITIVE_COLUMNS`.
- The `kind="rebuild"` job ignores user-supplied start/end and rebuilds ALL covered trading dates (the
  J-85 acceptance: "for every covered trading date") — confirm the date inputs on `/data` are not
  required for the rebuild action; the rebuild scope is the full covered calendar, not a range.
- The aggregate mean-MDD on Research follows the EXISTING `mean_mae`/`mean_mfe` aggregation already in
  `research.py` (same `_mean_or_none` + NA discipline) — no new aggregation primitive.

## Out of Scope (excluded — flagged per CORE RULES)
- Re-committing the regenerated snapshots into the optional Capability-34 snapshot seed (a separate
  deterministic-script step).
- Any change to the J-84 Yahoo cookie+crumb expand auth path beyond consuming its members.
- A real successful Yahoo ≥500-member screen (J-22) — data-walled, non-halting; not required.
- Any new canonical score/return formula; any in-place UPDATE of a snapshot row; any second global date
  control; any new top-level nav section or page.
- J-22 / J-23 / J-24 (data-walled, non-vetoing blocked-NA).
