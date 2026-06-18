# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33 Execution Plan

Dynamic point-in-time universe: per-as-of-date resolver (price + ADV + ≥`min_history_bars`),
min-history warm-up gate, membership timeline + per-date coverage diagnostic, J-95 data-walled
backward-history envelope, and the one-line stale-guard consolidation. **The last buildable
Must-haves in `docs/goal.md` — a GOAL_ACHIEVED candidate once green + COHERENCE-PASS + full suite GREEN.**

This is FULL depth: it changes the universe-source semantics (`score_stocks` iteration set +
`forward_symbols`), adds a new engine module + read-only derivations, migrates the `universe_count`
contract to as-of-dependence, and the full backend pytest suite is the GOAL_ACHIEVED gate.

## What to Build

- **Consolidation (DO FIRST, one line):** reconcile the stale guard
  `apps/backend/tests/test_api_data.py::test_get_data_overview_shape` to accept J-92's additive
  `macro` key — change the `set(payload) == {…}` (line 74) to a superset compare
  (`{…} <= set(payload)`) OR add `"macro"` to the expected set (mirrors the iter-21/iter-24
  reconciliations). Re-run the suite so the baseline is clean before the cluster lands.
- **J-93/J-94 — Per-as-of-date universe resolver (keystone):** a SINGLE new typed, config-reading
  engine module `apps/backend/app/engine/universe_resolver.py` (NO threshold literal — source every
  cutoff from config; add it to `test_no_magic_numbers` `CALC_FILES`). For a given D it reads the
  committed candidate pool via the existing `universe_screen.read_pool` and admits each candidate
  that, from **bars dated ≤ D only** (`prices.bars_asof`), clears config **price**
  (`universe.filters.min_price`) AND **ADV** (over `universe.filters.adv_window_days`) AND has
  **≥ `indicators.min_history_bars` trailing bars** (the J-94 gate). The **market-cap criterion is
  DROPPED** from the per-date screen (current-only scalar → applying per-historical-date is
  lookahead-or-fabrication; document the dropped criterion).
- **J-93 — Repoint the universe source:** the resolver becomes the PRIMARY universe path, replacing
  the global `cfg.universe.symbols` list as the set `score_stocks` iterates (`scoring.py:282`/`:307`).
  The scored `ScannerResult` rows ARE the persisted membership — no second universe computation, no
  recompute in the read path. Touch NO canonical scoring formula — only the membership scanned over.
- **J-93 — Repoint `forward_symbols`** (`forward_testing.py:89-99`): each run's forward returns derive
  from **that run's stored `ScannerResult` tickers ∪ `benchmark_symbols`** (SPY/QQQ/sector ETFs always
  present) rather than the global `universe ∪ benchmarks`, keeping the no-lookahead boundary
  (entry close on D, exits date > D) byte-identical.
- **J-93 — Migrate `universe_count` to as-of-dependence:** the THREE current `len(cfg.universe.symbols)`
  sites — `compute_coverage` (`data_manager.py:374`), `_coverage_diagnostic_absent`
  (`data_manager.py:316/326/343`), and `_universe_selection.resolved_size`
  (`methodology.py:137`) — report **members-resolved-at-D** (carry the full-pool candidate count
  alongside). Re-express the J-22 invariant as `universe_count == members-resolved-at-D`. Drop/relabel
  the `/methodology` Universe-Selection market-cap row to match the per-date rule.
- **J-94 — Per-date coverage diagnostic:** a read-only descriptive derivation in the SAME
  `compute_coverage` producer over the SAME stored bars + config thresholds the J-36/J-37 diagnostics
  use (recompute NO canonical value), reporting for the resolved as-of: the admitted count + the
  **excluded-by-reason counts** (below-history / below-price / below-ADV) against the candidate-pool
  denominator, reusing the existing `thin`/`no_history` vocabulary. Served on the existing
  `GET /api/data` coverage block (no new endpoint).
- **J-96 — Membership-timeline derivation:** a read-only descriptive derivation over the stored
  per-snapshot `ScannerResult` membership (the `ScannerRun.asof_date` set `compute_coverage` already
  reads) + bars + config (recompute NO score/return/membership), producing per snapshot date: the
  **resolved size** (step function), deterministic **entries** (first date a name appears) / **exits**
  (any date it disappears after having been present), and the per-date excluded-by-reason counts.
  Strictly causal (each date observed from its own ≤ D snapshot). Serve on the Data Manager coverage
  surface — prefer extending `GET /api/data`; if a new `GET /api/data/universe-timeline` endpoint is
  chosen instead, **register the final path in `blueprint.md` Data Contract** (it is already
  pre-registered at blueprint line 337 — confirm the chosen field/endpoint matches).
- **J-95(a) — Backward-history extension flow (buildable legs):** a confirm-gated clear + re-import +
  rebuild that REUSES the existing J-85 regenerate-from-scratch mechanism + the J-34/J-35
  chunked/checkpointed/resumable import path (NO second fetch engine) targeting an earlier price start.
  On resume the session attempts the fetch ONCE (best-effort, never an autonomous retry loop); a walled
  provider → honest **blocked / limited-coverage (NA)**, MUST NOT halt, drive STALLED, or veto
  GOAL_ACHIEVED. The committed price seed is NEVER deleted by the clear step
  (`clear_snapshot_set` already asserts `bars_before == bars_after`).
- **J-95(b) — Point-in-time index-membership label (buildable leg):** the candidate pool carries its
  explicit survivorship-bias label (current-constituent, not as-of-date-constituent). A true
  point-in-time constituent feed is offered ONLY as a data-dependent, non-halting enhancement and is
  NEVER faked; when absent the pool stays the documented current-constituent listing with its honest
  label, and the as-of-dependent `universe_count` is screened from that pool. No index-feed key
  persisted (env-only).

## Agents Required

- **backend-data: yes** — new `universe_resolver` engine module; repoint `score_stocks` iteration set
  + `forward_symbols`; migrate the `universe_count`/`resolved_size` contract; add the J-94 per-date
  coverage diagnostic + the J-96 membership-timeline derivation to `compute_coverage`; J-95 backward-
  history flow on the existing J-85/J-34/J-35 machinery; all unit/integration tests + the additive-
  guard reconciliations + the one-line stale-guard fix.
- **frontend-ux: yes** — the J-94 per-date coverage-diagnostic panel + the J-96 membership-timeline
  view (step function + entries/exits + excluded counts + the three honest labels) on `/data`; the
  J-95 confirm-gated backward-history control (reuse the J-85 rebuild confirm UI + J-66 progress);
  the J-93/J-94 honest empty/smaller-universe state on `/stocks` (+ `/themes` / `/sectors` /
  `/scanner-runs`) at early dates. All read the single global as-of (`useAsOf`) — NO second date state.
- developer: yes — single developer agent handles both the backend and frontend work above following TDD.

## Frontend Present
yes

## Files to Create/Modify

- `apps/backend/app/engine/universe_resolver.py` (NEW) -- the per-as-of-date resolver (price + ADV +
  ≥`min_history_bars` over bars ≤ D; reads `read_pool` + `bars_asof`; market-cap dropped). NO literal.
- `apps/backend/app/engine/scoring.py` -- repoint `score_stocks` (`:282`/`:307`) to iterate the
  resolver's resolved set instead of `cfg.universe.symbols`. No scoring-formula change.
- `apps/backend/app/engine/forward_testing.py` -- repoint `forward_symbols` (`:89-99`) to per-run
  stored `ScannerResult` tickers ∪ `benchmark_symbols`; no-lookahead boundary byte-identical.
- `apps/backend/app/engine/data_manager.py` -- migrate `universe_count` in `compute_coverage` (`:374`)
  + `_coverage_diagnostic_absent` (`:316/326/343`) to members-resolved-at-D (+ full-pool count); add
  the J-94 per-date coverage diagnostic + the J-96 membership-timeline derivation.
- `apps/backend/app/engine/methodology.py` -- `_universe_selection.resolved_size` (`:137`) →
  members-resolved-at-D (+ candidate count); drop/relabel the market-cap row.
- `apps/backend/app/api/data.py` -- surface the J-94 diagnostic + J-96 timeline on `GET /api/data`
  coverage (or add `GET /api/data/universe-timeline` — register the final path).
- `apps/backend/app/engine/universe_screen.py` -- the J-95(b) explicit current-constituent
  survivorship label on the candidate pool (if not already present).
- `apps/backend/app/api/data.py` / `data_manager.py` -- J-95(a) confirm-gated backward-history
  extension flow reusing the J-85 rebuild + J-34/J-35 resumable import path (non-halting blocked-NA).
- `apps/backend/tests/test_api_data.py` -- FIX `test_get_data_overview_shape` (superset/add `macro`);
  add J-94 diagnostic + J-96 timeline payload-shape assertions; reconcile any `set(payload) ==` guard
  the migration/timeline touches.
- `apps/backend/tests/test_no_magic_numbers.py` -- add `universe_resolver.py` to `CALC_FILES`.
- `apps/backend/tests/test_universe_resolver.py` (NEW) -- resolver no-lookahead tail-invariance;
  admit-iff price∧ADV∧trailing-bars (each leg, incl. a name entering on its first qualifying date);
  warm-up boundary = seed-start + `min_history_bars` (empty before, full after). Split fast
  no-seed-boot tests from `loaded_engine`-fixture tests (iter-29 lesson).
- `apps/backend/tests/test_scoring.py` / `test_forward_testing.py` -- per-stock scores/returns/MDD
  byte-identical for the SAME resolved membership; `forward_symbols` = per-run members ∪ benchmarks
  keeps the boundary byte-identical and benchmarks present every run.
- `apps/backend/tests/test_data_manager.py` -- `universe_count == members-resolved-at-D`;
  J-96 entries/exits deterministic + causal; `clear_snapshot_set` asserts `bars_before == bars_after`
  (seed un-deletable).
- `apps/backend/app/db.py` `_ADDITIVE_COLUMNS` + `apps/backend/tests/test_db.py` -- ONLY if a new
  stored column/table is introduced (the J-94/J-96 derivations are read-only over existing stored
  rows; J-95 reuses existing tables — expect NO schema change. If one is added, register it this iter).
- `apps/frontend/app/data/page.tsx` -- extend `CoveragePanel` with the J-94 per-date diagnostic
  (admitted + excluded-by-reason); add the J-96 membership-timeline panel (size step function +
  entries/exits + excluded counts + the three honest labels); add the J-95 backward-history control
  (reuse `RebuildPanel`/`RebuildConfirmModal` chrome; honest blocked/NA state). Reads `useAsOf` only.
- `apps/frontend/lib/api.ts` -- types + fetchers for the J-94 diagnostic + J-96 timeline fields.
- `apps/frontend/app/stocks/page.tsx` (+ `/themes`, `/sectors`, `/scanner-runs` as needed) --
  honest empty/smaller-universe state at early/warm-up dates (no new control).

## UI Evolution
- **New user-facing capability:** stepping the single global as-of now slides the scored stock
  universe — early dates honestly show a small/empty universe (warm-up), full membership ~2022-01.
  A new `/data` membership-timeline view explains which names entered/exited on which date and why a
  date's resolved size is what it is.
- **New information displayed:** per-snapshot-date resolved size (step function); per-name
  entries/exits; per-date excluded-by-reason counts (below-history / below-price / below-ADV) against
  the candidate-pool denominator; the as-of-dependent `universe_count` (members-resolved-at-D) with
  the full-pool candidate count beside it; the survivorship-bias / warm-up / universe-relative labels.
- **New user actions:** a confirm-gated "extend history backward" control on `/data` (reuses the J-85
  rebuild confirm UI + J-66 progress). Stepping the existing single global as-of now visibly changes
  the resolved universe (no new control).
- **UI surface changes:** Data Manager (`/data`) — new membership-timeline + per-date coverage-
  diagnostic panels + the backward-history extension control. `/stocks` (+ `/themes` / `/sectors` /
  `/scanner-runs`) — honest smaller/empty universe at early dates.
- **Navigation changes:** none. No new top-level nav section, no new page — all surfaces land on
  EXISTING IA homes (blueprint lines 282/290/293; IA skeleton unchanged → no blueprint re-approval).

## Visual Requirements
- **Component patterns:** reuse the existing `/data` `CoveragePanel` chrome for the per-date
  diagnostic; reuse the J-44/J-49 step-function overlay treatment for the timeline size series; the
  entries/exits as a compact dated list; reuse `RebuildPanel`/`RebuildConfirmModal` + `PanelTitle`/
  `Metric`/`DefinedMetric` for the backward-history control. No new component library — match the
  dense dark analytical-workstation surfaces already on `/data`.
- **Layout:** existing left-sidebar + top-bar + main-content `/data` page; the new panels sit on the
  coverage home (the timeline + step-function may be below the fold).
- **Key visual effects:** carry the three honest labels VERBATIM beside the timeline (candidate-pool
  survivorship caveat / warm-up boundary / universe-relative breadth) — plainly stating the dynamic
  universe REDUCES survivorship vs the static current-membership universe while residual pool-
  survivorship remains until the J-95 constituent feed. Step-function uses the existing chart palette
  (design tokens, no magic hex).
- **States to handle:** empty/early DB → honest empty timeline + empty stock universe (no fabricated
  dates/members); walled backward-history fetch → honest blocked/limited-coverage (NA) state; loading
  skeletons consistent with the existing `/data` panels.

## CRITICAL invariants to preserve (inspect statically)
- **J-18 (CRITICAL):** the membership timeline + coverage diagnostic add NO date `useState`, NO
  window/document keydown listener — they read `useAsOf()`. Zero `<input type=date>` on the affected
  pages.
- **J-07 (CRITICAL):** the scanner/regime path is byte-unchanged — only the iterated membership set
  changes → Risk-Off still marks zero Actionable.
- **J-06 (CRITICAL):** per-stock scores/returns read identically on leaderboard and detail for the
  resolved membership; the `universe_count` migration leaves every per-stock score/return byte-identical.
- **No lookahead:** resolver admission at D reads only bars ≤ D (tail-invariance unit-asserted like
  `forward_return`); no market-cap fabrication per historical date; resolver passes `test_no_magic_numbers`.

## Out of scope (excluded — flagged per spec)
- Any change to a canonical scoring formula / six scores / A–E bucket edges / setup status / pattern
  detection / the regime engine / the Risk-Off→Actionable gate (membership changes; formulas do not).
- The J-87…J-92 downtrend/regime/macro machinery + the sector/benchmark/ETF infrastructure
  (stocks-only; ETFs / ^VIX are never universe members).
- Fabricating or estimating any market cap per historical date (dropped, not approximated).
- A real successful backward-history fetch + the true point-in-time constituent feed (data-walled →
  J-95 records those legs honestly blocked-NA, non-halting, NEVER faked).
- Re-committing regenerated snapshots into the optional snapshot seed; adding any second date control.

## Key Test Scenarios

- **Suite gate:** `test_get_data_overview_shape` accepts `macro`; the FULL backend pytest suite is
  GREEN (flushed `0 failed, EXIT 0`). Hand the ~945+-test suite to the pump nohup-async — NEVER block
  the evaluator on the in-flight suite (iter-11/29 lesson). `exit=137` in a `/tmp` log is the known
  background-helper harness-kill, not a test failure.
- **Browser J-93:** step the as-of — membership slides (early date small/empty on `/stocks`, full
  ~2022-01); `/stocks`/`/themes`/`/sectors`/`/scanner-runs` reflect D's membership, never padded.
- **Browser J-94:** per-date coverage diagnostic shows admitted + excluded-by-reason counts; an as-of
  before the warm-up boundary renders an explicit honest empty universe (not an error, not fabricated).
- **Browser J-96:** membership timeline shows the per-date size step function + entries/exits +
  excluded counts + the three honest labels (md5sum evidence dir FIRST; scroll the colored timeline
  into the viewport, capture full-viewport, VIEW the pixels — a blank/table-only frame is rejected).
- **Browser J-95:** the confirm-gated backward-history control renders + the survivorship-bias label
  is present; the real-fetch leg honestly shows blocked / limited-coverage (NA) — non-halting.
- **Unit/integration:** (1) resolver no-lookahead tail-invariance (removing bars > D never changes D's
  members); (2) admit-iff price∧ADV∧trailing-bars (each leg, incl. first-qualifying-date entry);
  (3) `forward_symbols` = per-run members ∪ benchmarks keeps the boundary byte-identical + benchmarks
  present every run; (4) `universe_count == members-resolved-at-D` with the full-pool count beside it;
  (5) warm-up boundary = seed-start + `min_history_bars` (empty before, full after); (6) J-96
  entries/exits deterministic + causal; (7) per-stock scores/returns/MDD byte-identical for the SAME
  resolved membership; (8) `clear_snapshot_set` asserts `bars_before == bars_after` (seed un-deletable).
- **Required-still-passing smoke:** J-06 (NVDA leaderboard==detail at a full-universe date), J-18
  (0 `<input type=date>`; timeline adds no second date state), J-07 (Risk-Off date → zero Actionable),
  J-87/J-88 Dashboard panel unchanged at a full-universe date.

## Coherence & data-contract notes
- The blueprint already PRE-REGISTERS every iter-33 data-contract addition: the `universe_resolver`
  primary path + `universe_count` migration (blueprint line 335, IA lines 282/290), the J-94 per-date
  coverage diagnostic (line 336), and the J-96 membership timeline (line 337). The IA nav skeleton is
  unchanged → **no blueprint re-approval requested.** No duplicate of any existing contract value: the
  per-stock scores/forward-returns/MDD read from their existing canonical sources unchanged — this
  iteration changes ONLY which names are in the scanned set + adds read-only descriptive derivations.
- **Data-dependency:** J-93/J-94/J-96 are NOT data-dependent — none may be recorded blocked-NA, none
  may halt. J-95 is partly data-dependent — its offline legs go green; the real backward-history fetch
  + the constituent feed are data-walled → honest blocked-NA, non-vetoing (the J-22/J-44-DIA contract).
  J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing).
- **Additive-guard discipline (apply THIS iter):** any new `table=True` SQLModel → `test_db.py`
  expected-tables set; any new column on an existing table → `db.py` `_ADDITIVE_COLUMNS`; the resolver
  CALC module carries NO float/int threshold literal + is in `test_no_magic_numbers` `CALC_FILES`; any
  new payload key on a `set(payload) ==`-guarded endpoint → reconcile that guard in the SAME iter (the
  `universe_count` migration in particular moves values asserted by existing coverage/methodology tests).

## GOAL_ACHIEVED candidacy
After the cluster lands green with the full suite GREEN, zero regression, and COHERENCE-PASS, every
buildable Must-have in `docs/goal.md` is passing — the next evaluation is a GOAL_ACHIEVED candidate
(J-22/J-23/J-24 + J-95's data-walled legs stay honestly blocked-NA, non-vetoing).
