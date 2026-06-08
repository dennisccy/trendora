# goal-i_can_see_the_wealthy_future_forever-iter-24 Execution Plan

Full depth. Three target journeys, all homing on the existing approved `/data` (Data Manager) — no new
route, no nav entry, no blueprint re-approval. Goal alignment: advances Key Capability #20 (Data Manager
coverage clarity + seed-safe curation) and J-36/J-39/J-35 in `docs/goal.md`. Coherence-auditor concern is
pre-addressed: both new contract values read the single canonical universe membership
(`config.universe.symbols`) — no second universe computation.

## What to Build
- **J-36 — per-symbol coverage + plain-language definitions (descriptive, read-only).** Extend
  `app.engine.data_manager:compute_coverage` (the single canonical coverage producer — no parallel module)
  to also return a per-symbol table: one row per stored `DailyPrice.symbol` AND one row per
  `config.universe.symbols` member, each with `symbol`, `in_universe` (membership from
  `config.universe.symbols`), `has_data`, `first`/`last` (NA when no bars), `bar_count`, `thin`
  (`0 < bar_count < indicators.min_history_bars` — threshold from config, **no magic number**), and
  `missing` (a universe member with `has_data=false`). A universe member with no bars → `has_data=false` +
  `missing=true` + NA range — never a fabricated range or a zero-bar row faked as present. Internal
  consistency: distinct-symbol row count == existing `symbol_count`; in-universe row count ==
  `universe_count`. Empty dataset → null range / zero counts / empty table (no error).
- **J-39 — seed-safe Remove-data with confirm-preview + cascade (the session's FIRST destructive data path).**
  Add (a) a read-only **seed-vs-user-added classifier** sourced from `apps/backend/data/seed/meta.json`
  (`symbols: [{symbol, first, last, bars}]`, 158 entries) — a `(symbol, date)` inside a seed window is
  **protected**; (b) a **preview endpoint** (read-only, deletes nothing) that, for a scope (`symbols`
  and/or `[start, end]`), returns removable `(symbol, date)` bar count + range, the not-removable
  committed-seed breakdown with reason `"committed seed"`, and the cascade (dependent `scanner_runs` +
  `scanner_results` + `sector_scores` + `theme_scores` + `forward_returns` that derive **solely** from the
  to-be-removed bars); (c) a **removal endpoint** (destructive) that deletes only user-added `DailyPrice`
  rows in scope and cascade-removes only the dependent snapshot/forward-return rows, recording the removal
  as a new append-only `DataProviderRun` audit entry. A wholly-committed-seed scope is **refused** with an
  explicit reason (400/422), never a silent partial.
- **J-35 — Expand-universe happy-path browser capture (no code expected).** Machinery already built+green
  in source (iter-23). Bring the dev server up cleanly and capture the injected-provider expand flow
  end-to-end (chunk x/N → passers + omitted-with-reason list → grown `universe-count`; `/methodology` size
  matches) to lift J-35 partial → passing. A small presentational fix is in scope only if needed to make
  the screen-result block capturable; otherwise no change.

## Agents Required
- **backend-data: yes** — extend `compute_coverage` (per-symbol table); add the seed classifier + preview
  endpoint + destructive removal endpoint + cascade + audit entry; unit/integration tests asserting exact
  values (full-history member / thin member / no-bars member / non-universe ETF/`^VIX`; preview deletes
  nothing; removal cascades only solely-dependent rows and leaves a fully-covered snapshot untouched;
  seed-only refused; committed seed un-deletable; no scanner/scoring recompute reachable from remove).
- **frontend-ux: yes** — Coverage definitions block + per-symbol coverage table (sortable/filterable
  UI-only, universe-members-only filter) on `/data`; Remove-data control with a confirm-preview dialog
  (scope → preview → confirm) using the established `/data` primitives; ensure the Expand result block
  renders cleanly for the J-35 capture. Re-formats backend values only — computes no coverage figure and
  adds **no second date state** (the remove date-range inputs are action parameters, not a viewing as-of
  control — J-18 preserved).

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` -- extend `compute_coverage` with the per-symbol table
  (rows from `daily_prices` range/count + `config.universe.symbols` membership + `indicators.min_history_bars`
  thin threshold; consistency-bound to `symbol_count`/`universe_count`); add the seed-vs-user-added
  classifier (reads `meta.json` windows); add `preview_removal` (read-only) and `remove_data` (destructive
  whole-row delete + cascade + `DataProviderRun` audit insert). No score/return/bucket recomputed.
- `apps/backend/app/api/data.py` -- add the preview endpoint (read-only) and removal endpoint (destructive)
  under the `/api/data` surface; typed request models (scope = symbols and/or date range as **job/action
  parameters**); map bad/empty/invalid scope → explicit 4xx; seed-only scope → refused with reason; the
  extended `coverage` payload flows through `GET /api/data`. Error strings carry no key/secret (J-33 carry).
- `apps/frontend/lib/api.ts` -- types for the per-symbol coverage rows + the remove preview/result payloads;
  client fns for preview + removal.
- `apps/frontend/app/data/page.tsx` -- Coverage definitions block (every figure labelled + universe-vs-symbols
  + backfill-gap definition); per-symbol coverage table (in-universe / has-data / date-range / bar-count /
  thin-or-missing) with UI-only sort/filter + universe-members-only filter; Remove-data control + confirm-
  preview dialog (removable bars + range, not-removable committed-seed line + reason, cascade list, destructive
  confirm); re-read coverage after a successful removal.
- `apps/backend/tests/test_data_manager.py` -- per-symbol table exact-value tests + seed classifier +
  preview-deletes-nothing + removal-cascade-solely + fully-covered-snapshot-untouched + seed-only-refused +
  committed-seed-undeletable + audit-recorded + no-recompute-reachable tests.
- `apps/backend/tests/test_api_data.py` -- preview/removal endpoint shape + 4xx error cases + key-safety.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-24-dev.md` -- dev handoff (required by DoD).

## UI Evolution
- **New user-facing capability:** understand exactly what data the app holds at per-symbol granularity, and
  safely remove user-added (non-seed) data behind a confirm-preview; finally see an Expand run captured.
- **New information displayed:** a Coverage definitions block (each aggregate figure + the universe-vs-symbols
  + backfill-gap definitions, in plain language); a per-symbol coverage table (in-universe / has-data /
  date-range / bar-count / thin-or-missing); a Remove-data confirm-preview (removable bars + range,
  not-removable committed-seed breakdown with reason, cascade of dependent snapshot/forward-return rows).
- **New user actions:** open / sort / filter the per-symbol table (incl. universe-members-only filter);
  open Remove-data, choose a scope, read the confirm-preview, confirm a seed-safe removal (seed-only refused).
- **UI surface changes:** `/data` Coverage panel becomes richer (definitions + per-symbol table); a new
  Remove-data control + confirm-preview dialog. All additive on the existing page.
- **Navigation changes:** none (no new route, no nav entry).

## Visual Requirements
- **Component patterns:** reuse the **existing `/data` primitives** — `Card` (`@/components/ui/card`) for
  panels, `Badge` (`@/components/ui/badge`) for in-universe / thin / missing / seed-protected flags, raw
  semantic table markup over a `Card` for the per-symbol table (this is the established `/data` pattern —
  `RunHistoryPanel`). NOTE: there is **no shadcn `Table` or `Dialog` primitive** in
  `apps/frontend/components/ui/` (only `badge`, `card`, `info-tooltip`, `select`). The confirm-preview
  "dialog" must be built as an in-page modal/confirm panel using `Card` + an overlay (matching the
  established style) — do not import a non-existent Dialog. Reuse the existing `Metric`/`PanelTitle`/
  `statusVariant` helpers in `page.tsx`.
- **Layout:** keep the single-column `/data` panel stack; insert the definitions block + per-symbol table
  inside (or directly under) the existing `CoveragePanel`, and the Remove-data control as a sibling panel.
- **Key visual effects:** dense, dark, data-forward analytical style consistent with the existing page;
  tabular/monospace numerics (`num` class already used); thin/missing rows get a distinct amber/muted
  treatment (`warn` Badge variant + muted text); the destructive confirm uses a clearly destructive
  affordance (negative/`neg` styling already present, e.g. `border-neg`/`text-neg`).
- **States to handle:** loading (skeleton/placeholder consistent with the page), empty dataset (empty table
  + zero/NA definitions, not an error), error (styled error card — the page already has a `border-neg`
  error card pattern), and the removal refusal/disabled state (seed-only scope → explicit reason shown).

## Critical design boundary (flag to dev/reviewer/auditor — the highest-risk seam)
- **Cascade "derives solely" rule (J-39).** `forward_returns` is keyed `(run_id, symbol, horizon)`;
  `scanner_results`/`sector_scores`/`theme_scores` are keyed by `run_id` → `scanner_runs.asof_date` (D).
  A removed `DailyPrice (symbol, date)` invalidates a snapshot only when, after removal, that snapshot no
  longer has the bar coverage it was built from (a date ≤ D input bar removed, or a forward-measurement bar
  date > D removed). The cascade MUST be a **whole-row delete of the derived row together with its
  provenance — NEVER an in-place UPDATE/overwrite of a retained snapshot** (the *Snapshots are immutable*
  identity = "never overwritten in place"; a consistency-preserving whole-row delete respects it). A
  snapshot that still has ALL its underlying bars after the removal MUST be left **untouched**. Dev defines
  the exact dependency predicate and proves it by value; reviewer/auditor must verify (a) no
  `score_stocks`/`run_scan`/scanner recompute is reachable from the remove path, (b) no remaining row
  references an absent bar, and (c) the committed seed (`meta.json` windows) is genuinely un-deletable.

## Assumptions (documented per token policy — not blocking)
- **No new `table=True` model** is added (J-39 deletes rows from existing tables; preview/remove use typed
  request models, not new tables) — so the iter-22 `tests/test_db.py` stale-expected-tables trap does NOT
  recur. If a model is unexpectedly added, update `tests/test_db.py` expected-tables set.
- **No live provider** is needed: J-36 reads stored bars + config; J-39 reads `meta.json` + stored data and
  deletes — both fully deterministic/offline. The current committed-seed-only host has **zero user-added
  bars**, so the live removal cascade is a no-op here; correctness MUST be proven by a fixture that **adds
  user bars beyond the seed** (the spec's required acceptance), not by the no-op live path.
- **`config.universe.symbols`** is the single universe-membership source for `in_universe` and the
  `universe_count` consistency check (already read by `/api/data` + `/api/methodology`). No second universe
  computation is introduced. The iter-23 `universe.json` merge means `universe_count` is the resolved
  membership (currently the YAML 122 on this host).
- Spec class-name note: the cascade tables are `SectorScoreRow` (`sector_scores`) and `ThemeScoreRow`
  (`theme_scores`) — the spec's loose `sector_scores`/`theme_scores` shorthand maps to these.

## Out of scope (excluded — flagged per CORE RULES)
- **J-37** (missing-data diagnostic + one-click pull-missing) and **J-38** (unified Unfinished-imports
  Resume/Retry/Remove generalization) — explicitly deferred to **iter-25** (data-dependent pull/retry
  semantics on the J-34 engine). Do NOT build the missing-data diagnostic, the pull-missing action, or the
  Unfinished-imports Retry/Remove generalization here.
- **J-22 / J-23 / J-24** live fetches — Yahoo-429 data-walled, **non-halting / non-vetoing** per
  `docs/goal.md:989-1012`. Do NOT autonomously re-probe/retry. J-36's table honestly shows current
  coverage; J-39 needs no provider; J-35's capture uses an **injected provider** for the happy-path (the
  live market-cap expansion outcome stays NA / non-halting).
- Any change to scoring / scanner / regime / patterns / buckets / forward-testing **compute** paths, or to
  `/stocks` · `/backtest` · `/research` · the as-of provider. **No DB regen** (J-06/J-07 stay byte-identical).
- A live Expand fetch to completion (data-walled).
- **Do NOT declare GOAL_ACHIEVED on these landings** (the iter-20 re-scope trap): after J-36/J-39 land green
  + J-35 captures green, **J-37 and J-38 remain** (iter-25) before the buildable set is complete; J-22/J-23/
  J-24 stay honestly blocked (NA) / non-halting.

## Key Test Scenarios
- **J-36 (browser):** on `/data`, the Coverage definitions block (universe-vs-symbols + every figure
  labelled) and the per-symbol table (in-universe / has-data / date-range / bar-count / thin-or-missing)
  render with values matching `GET /api/data`; the universe-members-only filter narrows to membership and
  every member shows data-or-missing; DOM-assert distinct-symbol rows == displayed `symbol_count` and
  in-universe rows == `universe_count` (`data-testid="universe-count"`).
- **J-36 (unit):** exact `in_universe`/`has_data`/`first`/`last`/`bar_count`/`thin`/`missing` for (a) a
  full-history universe member, (b) a thin member (`0 < bars < min_history_bars`), (c) a no-bars universe
  member (`has_data=false`, `missing=true`, NA range — not fabricated), (d) a non-universe priced symbol
  (ETF / `^VIX` → `in_universe=false`); distinct-symbol rows == `symbol_count`, in-universe == `universe_count`;
  thin threshold read from `indicators.min_history_bars` (no literal); empty dataset → null/zero/empty, no error.
- **J-39 (browser):** open Remove data → choose a user-added scope → confirm-preview shows removable bar
  count + range + the not-removable committed-seed line + the cascade; attempt a seed-only scope → refused
  with the explicit "committed seed" reason (no deletion); (on a fixture/test host with user-added bars)
  confirm a removal → the per-symbol table + as-of dates reflect the smaller dataset. Distinct screenshots
  for preview, refusal, post-removal.
- **J-39 (unit/integration):** seed classifier (date inside a seed window → protected; beyond → removable);
  **preview** returns exact removable bars + range + not-removable committed-seed breakdown + cascade set and
  deletes **nothing** (DB unchanged after preview); **removal** on a fixture with user-added bars deletes
  only those bars and cascade-removes only the snapshot/forward-return rows that derive **solely** from them
  (a snapshot still holding all its bars is **untouched**; no remaining row references an absent bar); a
  wholly-seed scope is **refused** (explicit error, nothing deleted); the removal is recorded on
  `DataProviderRun`; `score_stocks`/scanner compute is never called by the cascade; the committed seed is
  never deletable.
- **J-35 (browser):** select Expand universe over a market-cap-capable injected source → chunk x/N progress
  → completion screen-result (passers + omitted-with-reason list) → grown `universe-count`; `/methodology`
  Universe-Selection size matches. Bring the dev server up cleanly first (stop strays **by port** — frontend
  :3835, backend :8835; `rm -rf apps/frontend/.next`; confirm `GET /_next/static/chunks/main-app.js` → 200
  and the health badge cleared) — do NOT run `npm run build` against the live dev `.next`.
- **J-33 carry:** the new coverage/remove error strings carry no key/secret (no `?token=`/`?apikey=` could
  appear — these paths take no provider key, so the surface is small but MUST be asserted).
- **J-18 cross-check:** exactly one date `<select>` per page on `/data` (the global top-bar as-of switcher);
  the new Coverage table + Remove-data date-range controls add zero date state (confirm in frontend source,
  not just the browser summary).
- **Required-still-passing:** J-17, J-34, J-33, J-22, J-08, J-15, J-18, J-06, J-07 remain green (full
  backend suite green; no DB regen → scoring/snapshot byte-identical).
