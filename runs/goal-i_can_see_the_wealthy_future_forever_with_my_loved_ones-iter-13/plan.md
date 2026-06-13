# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13 Execution Plan

Per-date availability heatmap (J-61) on `/data` + as-of calendar popover (J-62). Both are
**presentation / read-only upgrades of existing single-source state** — no new stored column, no new
canonical value, no second date state.

## What to Build

- **J-61 backend (read-only derivation + ONE new endpoint).** Add a per-trading-date availability
  derivation in `apps/backend/app/engine/data_manager.py` over the **already-stored** bars + runs,
  keyed to the SPY trading calendar (the same `_trading_days` / `compute_coverage` machinery at
  `data_manager.py:114`/`292`). For each calendar trading date emit
  `{ date, symbols_with_bars, total_symbols, snapshot_exists }`. Expose it on **one** new read-only
  endpoint `GET /api/data/availability` (added to the existing `data.py` router, prefix `/api`).
  Descriptive metadata only — recompute NO canonical score / return / bucket / setup; read the SAME
  source `compute_coverage` reads (never a second derivation of an existing coverage figure).
  Honest empty-DB behavior: empty/bars-less DB → empty-but-valid payload (no fabricated cells); a
  zero-bar trading day is `symbols_with_bars=0`, never omitted-as-if-covered. `/api/data` overview
  and all existing data endpoints stay byte-unchanged.
- **J-61 frontend (heatmap on `/data`).** New availability-heatmap card/component on
  `apps/frontend/app/data/page.tsx`: trading-day calendar grid colored by `symbols_with_bars`, a
  distinct marker on days that also have a snapshot, a legend, and exact figures on hover (date,
  `symbols_with_bars / total_symbols`, snapshot yes/no). A sparse day (e.g. 3-of-158) is visually
  distinct from a full day; a zero-bar trading day is visibly empty. All dates render `yyyy-MM-dd`
  via `apps/frontend/lib/dates.ts`. Clicking a day (or selecting a range) **prefills the job form's
  Start/End inputs** (the page already lifts `start`/`end` + `setStart`/`setEnd` — wire into those) —
  these are **job parameters, NEVER the global as-of control** (J-18). After a fetch/backfill/removal
  job completes, the heatmap re-reads (re-fetch the availability endpoint via the existing
  reload-on-complete path) and shows the new coverage. Renders gracefully on an empty DB.
- **J-62 frontend (as-of calendar popover).** Replace the flat `<Select>`/`<option>` dropdown in
  `apps/frontend/components/asof-switcher.tsx` with a **calendar popover** (month grid): the existing
  `dates` array from `asof-provider` marks selectable snapshot dates; other days are disabled; month
  navigation reaches the oldest stored month; a **"Latest"** affordance returns to latest; fully
  keyboard operable (open / navigate months & days / select / dismiss). Textual dates render
  `yyyy-MM-dd` via the shared formatter (J-42). The calendar holds **NO second date state** — it is a
  renderer of the one global control: selecting a date calls the existing `setAsOf` from
  `asof-provider` (unchanged), so the historical badge, `?asof` serialization (J-43), and href
  stamping (J-50) all stay byte-unchanged. Invalid `?asof` on load still degrades to latest (J-43).
  No dates available → disabled control.

## Agents Required

- **backend-data: yes** — add the read-only per-date availability derivation in `data_manager.py` and
  the single `GET /api/data/availability` endpoint in `app/api/data.py`; tests on a known fixture.
  NO stored column, NO write path, NO canonical recompute.
- **frontend-ux: yes** — the `/data` availability-heatmap card (hover figures, legend, sparse-vs-full
  distinction, click-prefills-job-form, re-read after a job, empty-DB) and the as-of calendar-popover
  swap in `asof-switcher.tsx` (driving the existing `setAsOf`, no second state).
- developer: yes -- implement both the backend endpoint and the frontend surfaces above following
  TDD; run targeted backend modules locally; hand the full ~46–59-min suite to the pump.

## Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/engine/data_manager.py` -- new `compute_availability(session, cfg)` read-only
  derivation (per-date `symbols_with_bars` + `snapshot_exists` over `_trading_days`), reusing the
  coverage machinery; no canonical recompute.
- `apps/backend/app/api/data.py` -- new `GET /api/data/availability` route serving the derivation;
  `/data` overview untouched.
- `config.yaml` (`data_manager:` block) -- ONLY if any numeric coverage-density legend cutoff is
  computed server-side, add it here (next to `gap_preview`) — no magic numbers. Pure presentation
  color mapping MAY instead live in the frontend (preferred if no numeric classification is needed).
- `apps/backend/app/config.py` -- typed field for the above knob, ONLY if a config knob is added
  (then also add it to EVERY inline test-config dict + `scripts/build_qa_fixture_db.py` — grep the new
  key across `apps/backend/tests`).
- `apps/frontend/lib/api.ts` -- `fetchDataAvailability()` + `AvailabilityResponse` /
  `AvailabilityCell` types.
- `apps/frontend/app/data/page.tsx` -- mount the availability-heatmap card; wire day/range click into
  the existing `setStart`/`setEnd`; re-read availability on job completion (reuse `loadOverview`-style
  refresh).
- `apps/frontend/components/availability-heatmap.tsx` (NEW) -- the heatmap grid component (cells,
  legend, hover tooltip, snapshot marker, sparse/empty rendering).
- `apps/frontend/components/asof-switcher.tsx` -- replace the `<Select>` dropdown with the calendar
  popover (drives the existing `setAsOf`; reads `dates`/`latest`/`asOf`/`isHistorical`/`ready`).
- `apps/frontend/components/asof-calendar.tsx` (NEW, optional split) -- the month-grid popover body
  (selectable vs disabled days, month nav, "Latest", keyboard handlers) if `asof-switcher.tsx` grows
  too large.
- `apps/backend/tests/test_data_manager.py` (or a new `test_data_manager_availability.py`) --
  fixture-based assertions on the new derivation.
- `apps/backend/tests/test_api_data.py` -- the new endpoint shape + empty-DB graceful payload.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13-dev.md` -- dev
  handoff.

## UI Evolution (Frontend Present: yes)

- **New user-facing capability:** (1) see at a glance, per trading day, how much data exists and
  whether a snapshot was computed — and click a day to prefill the next fetch/backfill; (2) pick the
  as-of date from a calendar that visibly distinguishes selectable snapshot dates from unavailable
  days.
- **New information displayed:** a `/data` per-trading-date availability heatmap (symbols-with-bars
  density + snapshot marker, exact figures on hover, legend); a calendar month grid in the as-of
  popover marking selectable dates.
- **New user actions:** hover a heatmap day (read exact figures); click a heatmap day / drag a range
  (prefill the job-form dates); open the as-of calendar popover, navigate months, pick a selectable
  date, press "Latest", operate by keyboard.
- **UI surface changes:** `/data` (Data Manager) gains a new availability-heatmap card; the top-bar
  as-of switcher changes dropdown → calendar popover (same single state).
- **Navigation changes:** none. No new top-level nav section, no new page. J-61 lands on the existing
  `/data` home; J-62 is the cross-cutting top-bar control (no page of its own). Both homes already
  exist in `blueprint.md` Information Architecture (stamped `[TARGET iter-13]` additively; no
  re-approval).

## Visual Requirements (Frontend Present: yes)

- **Component patterns:** reuse the existing `Card`/panel pattern on `/data` for the heatmap card
  (mirror `CoveragePanel`). Hover figures via a lightweight tooltip/popover (shadcn pattern already in
  use). The as-of calendar should use the existing shadcn popover/button primitives; a **hand-rolled
  Tailwind month grid is preferred** over adding a heavy date-picker dependency (OUT OF SCOPE per
  spec — a small dependency is permitted only if it holds no internal date state and fits Next 15 / TS
  / Tailwind / shadcn).
- **Layout:** heatmap = a trading-day calendar grid (weeks as rows or a compact month-banded grid)
  inside a full-width card on `/data`, placed near the existing coverage panel. As-of popover = a
  compact month grid anchored under the top-bar control, with a month-nav header and a "Latest"
  action row.
- **Key visual effects:** dense dark analytical styling consistent with the rest of the app; color
  cells by `symbols_with_bars` density (a sequential ramp), a distinct snapshot marker (dot/ring), a
  clear legend. Disabled calendar days visibly muted; selectable days emphasized; the selected/latest
  day highlighted. Monospace/tabular figures in the tooltip. Keep effects subtle — no flashy
  consumer aesthetic.
- **States to handle:** loading (skeleton/placeholder), empty DB (heatmap renders an honest empty
  state, no fabricated cells; calendar control disabled when `dates.length === 0`), error (the
  availability fetch failing shows no fabricated cells — mirror the page's existing
  "could not load … no figures shown rather than fabricated" treatment), and the post-job re-read.

## Lessons Applied (from spec + project memory)

- **NO new stored column this iteration** (J-61 is a read-only derivation; J-62 is frontend-only). If
  one becomes unavoidable, register it in `db.py` `_ADDITIVE_COLUMNS` + add a regression test + migrate
  the live DB — but prefer not to. (iter-12 QA-FAIL root cause was two unregistered columns 500ing the
  live persistent DB.)
- **Any new config knob → EVERY inline test-config dict + `scripts/build_qa_fixture_db.py`.** Grep the
  new key across `apps/backend/tests`; don't trust a fixed list. Prefer keeping the legend color
  mapping frontend-only to avoid this entirely.
- **Nested-interactive hazard (iter-5):** heatmap cells and calendar day cells are clickable — keep
  any inner button/link as a SIBLING of the cell's own click handler, never nested inside a parent
  `role="button"`/interactive element (avoids the React dev-overlay "nested interactive" error).
- **React controlled inputs need the native setter for Chrome MCP:** if the popover keeps any
  `<select>`/controlled input that browser-QA drives, use the native-setter + bubbling change event in
  eval, then assert live DOM. (Prefer plain buttons for calendar days so this doesn't apply.)
- **Full pytest is ~46–59 min — hand it to the pump, never block the evaluator on it.** Dev runs the
  targeted new modules + the data-manager / coverage / as-of-related modules locally.
- **md5 evidence hygiene:** each browser-QA capture must be a distinct, correctly-named file for the
  surface it claims (heatmap-hover, sparse-vs-full-day, click-prefill, calendar-popover, etc.).

## Build Steps (ordered)

1. **Backend derivation (TDD).** Write `test_data_manager` (or `test_data_manager_availability`)
   fixture tests first: per-date `symbols_with_bars` + `snapshot_exists` exactly match stored bars +
   stored runs over the SPY trading calendar; figures consistent with (never a second derivation of)
   `compute_coverage`; assert a sparse day, a fully-covered day, a zero-bar trading day, and a
   date-with-snapshot vs without; empty/bars-less DB → empty-but-valid payload (no fabricated cells).
   Then implement `compute_availability` reusing `_trading_days` + the bar/run scans.
2. **Backend endpoint.** Add `GET /api/data/availability` to `app/api/data.py`; assert shape + empty-DB
   graceful payload (no 500, no fabricated cells) in `test_api_data.py`. Confirm `/api/data` overview
   and existing endpoints read byte-unchanged.
3. **Frontend API client.** Add `fetchDataAvailability()` + types in `lib/api.ts`.
4. **Heatmap component.** Build `availability-heatmap.tsx`: calendar grid, density coloring, snapshot
   marker, legend, hover tooltip (exact figures via `formatIsoDate`), sparse/empty rendering, loading
   & empty/error states. Cell click/range → callback (no nested-interactive).
5. **Wire into `/data`.** Mount the card on `app/data/page.tsx`; click/range prefills `setStart`/
   `setEnd` (job parameters only — assert no as-of write); re-read availability on job completion via
   the existing reload path. Verify `npx tsc --noEmit` clean.
6. **As-of calendar popover.** Replace the `<Select>` in `asof-switcher.tsx` with the month-grid
   popover (selectable/disabled days, month nav to oldest stored month, "Latest", keyboard ops),
   driving the existing `setAsOf` ONLY — no local date state. Keep the historical badge unchanged.
   Verify `tsc --noEmit` clean and that `?asof`/href stamping are untouched.
7. **Targeted backend tests + tsc.** Dev runs the new/availability modules + `test_api_data.py` +
   `test_data_manager*.py` + the coverage/config-touched modules locally; **hand the full suite to the
   pump.** Write the dev handoff.
8. **Browser-QA (J-61 + J-62)** with distinct, correctly-named captures per surface.

## Key Test Scenarios

- **J-61 (browser-QA):** `/data` renders the availability heatmap with a legend; hover shows exact
  figures (date, symbols-with-bars / total, snapshot yes/no); a sparse day is visually distinct from a
  full day; a zero-bar trading day is visibly empty; clicking a day prefills the job-form date inputs
  (and the **as-of state is provably unchanged** after the click); after a job completes the heatmap
  re-reads; empty-DB renders gracefully with no fabricated cells.
- **J-62 (browser-QA):** the as-of switcher opens a calendar popover; selectable snapshot dates are
  marked + selectable, others disabled; month navigation reaches the oldest stored month; "Latest"
  returns to latest; keyboard-operable (open / navigate / select / dismiss); selecting a historical
  date re-points the app exactly as today (historical badge + `?asof` serialization + href stamping
  unchanged); an invalid `?asof` URL degrades to latest.
- **Backend unit/integration:** the availability derivation's per-date counts exactly match stored
  bars + runs over the benchmark calendar and are consistent with `compute_coverage`; empty/bars-less
  DB → empty-but-valid payload (no 500, no fabricated cells); a zero-bar trading day renders as `0`,
  never covered.
- **Required-still-passing journeys remain green:** especially **J-13/J-18/J-43/J-50** (one date
  control, `?asof` serialization, href stamping — all byte-unchanged) and **J-36/J-17/J-37** (coverage
  / data-manager surfaces on `/data`). Plus J-42 (shared ISO formatter), J-06/J-08/J-15/J-40.
- **Anti-goal guards:** **Exactly one date selector** — the calendar holds no second date state
  (coherence-auditor hard-fails a second date selector). **Coverage & missing-data are descriptive &
  honest / No recompute in the read path** — the availability endpoint recomputes no canonical value
  and reads the same source `compute_coverage` reads. **No fabricated data** — empty/zero-bar days are
  honest. **No magic numbers** — any server-side density cutoff is config-backed.

## Risks / Open Questions (assumptions recorded; not blocking)

- **Legend bucketing location.** Assumption: keep the coverage-density color mapping **frontend-only**
  (pure presentation) to avoid touching `config.py` + every inline test-config dict + the QA fixture
  builder. Only if a *numeric* density-classification cutoff is genuinely needed server-side does it go
  to `config.yaml` `data_manager:` with the full fan-out (iter-12 lesson). Prefer frontend-only.
- **Calendar widget mechanism.** Assumption: **hand-rolled Tailwind month grid** (no heavy date-picker
  dependency — OUT OF SCOPE per spec). A small dependency is permitted only if it fits the stack and
  holds no internal date state; default to hand-rolled.
- **`total_symbols` semantics.** Assumption: `total_symbols` = the distinct stored-symbol universe the
  density denominator is taken against (consistent with `compute_coverage`'s `symbol_count` — all
  priced symbols incl. ETFs + `^VIX`), so "3-of-158" reads against the same denominator the coverage
  surfaces already use. Dev should make the denominator explicit and consistent with `compute_coverage`
  and document it in the handoff; a per-date `symbols_with_bars` counts symbols with a bar **on that
  date** (not cumulative).
- **Heatmap span on a large history.** A long stored history could make the grid tall. Assumption: a
  compact month-banded calendar grid (weeks as rows) scrolls within the card; no truncation that hides
  a covered day (honesty). Performance is fine for the seed-scale history.
- **Out of scope (excluded):** J-63 (event-study episodes — next iteration), any new stored
  column/table, changing the as-of state machine / `?asof` serialization / href stamping, recomputing
  any coverage figure or canonical value, and J-22/J-23/J-24 (data-walled, honest NA — no work). No
  scope drift from the goal: J-61/J-62 are explicit goal.md Capabilities 20/21 and named success
  criteria.
