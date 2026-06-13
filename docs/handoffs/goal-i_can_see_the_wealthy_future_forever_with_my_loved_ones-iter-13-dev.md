# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-13
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## What Was Built

- **J-61 backend — `compute_availability(session, cfg)`** in `apps/backend/app/engine/data_manager.py`: a
  READ-ONLY per-trading-date availability derivation over the SAME stored bars + stored runs
  `compute_coverage` reads. For every benchmark (SPY) trading day in `_trading_days` it emits
  `{date, symbols_with_bars, total_symbols, snapshot_exists}`. `symbols_with_bars` is the point-in-time
  DISTINCT count of symbols with a bar on that date (NOT cumulative); `total_symbols` is the distinct
  stored-symbol universe == `compute_coverage`'s `symbol_count` (the SAME density denominator — no second
  universe); `snapshot_exists` reads the SAME `ScannerRun.asof_date` set coverage uses. Recomputes NO
  canonical score/return/bucket/setup. Empty/bars-less DB → `{total_symbols: 0, trading_day_count: 0,
  cells: []}` (no fabricated cells).
- **J-61 backend — `GET /api/data/availability`** in `apps/backend/app/api/data.py`: one additive
  read-only route serving the derivation. `/api/data` overview and all existing endpoints are
  byte-unchanged.
- **J-61 frontend — availability heatmap** (`apps/frontend/components/availability-heatmap.tsx`, NEW): a
  month-banded trading-day calendar grid colored by `symbols_with_bars` density (a 6-step frontend-only
  sequential ramp), a positive-toned ring marker on snapshot days, a legend, and exact figures on
  hover/focus (date, `symbols_with_bars / total`, snapshot yes/no). Sparse days are visibly fainter than
  full days. Clicking a day prefills the JOB FORM Start/End (start == end); shift-click a second day
  prefills a range. Loading / error (no fabricated cells) / empty-DB states handled. Mounted on
  `/data` near the coverage panel; re-reads after any job completes / a removal.
- **J-62 frontend — as-of calendar popover** (`apps/frontend/components/asof-calendar.tsx` NEW +
  `apps/frontend/components/asof-switcher.tsx` rewritten): the flat `<Select>` dropdown is replaced by a
  month-grid popover. Selectable snapshot dates (the existing `dates` array from `asof-provider`) are
  buttons; every other day is a disabled, muted placeholder. Month nav clamps to the oldest/newest stored
  month (the oldest is always reachable). A "Latest" affordance returns to latest. Keyboard operable
  (Tab through nav/Latest/days; Enter selects; Escape closes; focus moves into the popover on open;
  outside-click closes). Dates render `yyyy-MM-dd` via the shared formatter.

## Files Changed

- `apps/backend/app/engine/data_manager.py` -- new `compute_availability` read-only derivation.
- `apps/backend/app/api/data.py` -- new `GET /api/data/availability` route.
- `apps/backend/tests/test_data_manager.py` -- 4 new fixture tests for the derivation (exact per-date
  counts, coverage-consistency, zero/sparse-day honesty, empty-DB).
- `apps/backend/tests/test_api_data.py` -- 2 new endpoint tests (shape + empty-DB graceful).
- `apps/frontend/lib/api.ts` -- `fetchDataAvailability()` + `AvailabilityResponse` / `AvailabilityCell` types.
- `apps/frontend/app/data/page.tsx` -- mount the heatmap card; `loadAvailability` (mount + re-read after
  a job/removal/retry); `handleHeatmapPrefill` wires day/range clicks into `setStart`/`setEnd`.
- `apps/frontend/components/availability-heatmap.tsx` (NEW) -- the heatmap grid component.
- `apps/frontend/components/asof-calendar.tsx` (NEW) -- the month-grid popover body.
- `apps/frontend/components/asof-switcher.tsx` -- dropdown → calendar popover (drives the existing `setAsOf`).

## Invariants Preserved (verified)

- **No new stored column, no new config knob, no `config.yaml` change** — `git diff` on
  `models.py`/`db.py`/`config.py`/`config.yaml` is empty. The iter-12 unregistered-column 500 class is
  avoided; `db.py` `_ADDITIVE_COLUMNS` did not need touching. The legend color mapping is frontend-only.
- **Exactly one date selector (J-62 anti-goal).** `asof-provider.tsx` is byte-unchanged. The switcher's
  only local state is `open` (popover visibility); the calendar's only local state is `view` (the viewed
  MONTH navigation cursor — not an as-of value). Both route every selection to the existing `setAsOf`.
  `?asof` serialization (J-43) and href stamping (J-50) are untouched.
- **No recompute in the read path / coverage is descriptive (J-61 anti-goal).** The availability endpoint
  recomputes no canonical value; it reuses the SAME `_trading_days` calendar, `DailyPrice` bars, and
  `ScannerRun.asof_date` set `compute_coverage` reads. Live verification on the real persistent DB
  confirmed `total_symbols` (159) == coverage `symbol_count`, `trading_day_count` (1356) == coverage's,
  and snapshot-cell count (134) == coverage `snapshot_count`.
- **Heatmap click never writes the as-of control (J-18).** `handleHeatmapPrefill` calls only
  `setStart`/`setEnd` (job parameters); no `setAsOf`.
- **No nested-interactive (iter-5).** Each heatmap day and each calendar day is a single `<button>`; the
  day number, snapshot ring, and tooltip readout are non-interactive `<span>`s.

## Tests Run

Command (targeted, dev-run within turn):
`apps/backend/.venv/bin/python -m pytest tests/test_api_data.py tests/test_data_manager.py -k "<availability/coverage/...>"`

Results:
- New + regression targeted set (`coverage|availability|overview|per_symbol|diagnostic|empty`): **25 passed**.
- Full `tests/test_api_data.py`: **42 passed**.
- `tests/test_data_manager.py` minus the one heavy realistic-backfill test: **71 passed, 1 deselected**.
- `npx tsc --noEmit` (frontend): **clean (exit 0)**.

Live (non-mocked) backend check against `apps/backend/data/trendora.db` via a direct `compute_availability`
import (read-only, no server, no writes): all coverage-consistency assertions matched (see Invariants).

## Hand to the pump (full-suite)

The full backend suite (~46–59 min, 639+ tests) CANNOT finish in a dev turn. Please run:
`cd apps/backend && .venv/bin/python -m pytest tests/ -q`
The ONE deselected heavy test is `test_data_manager.py` realistic-backfill (`n_grows`/realistic) — it is
unaffected by this iteration's change (additive read-only function) but should run in the full suite.

## Known Issues

- The running QA backend on **:8835** (pump-owned, pid 491274, no `--reload`) predates this change, so it
  still 404s on `GET /api/data/availability` until the pump restarts it for browser-QA. The route is
  correct and live-verified via direct import; a fresh backend start picks it up. I did NOT restart the
  pump's instance (it belongs to the QA pipeline). The :8835 backend + :3835 frontend were left running
  and untouched; I started no servers of my own.
- The heatmap renders one `<button>` per trading day (1356 on the live seed history → ~65 month bands). It
  scrolls inside a `max-h` card; performance is fine at seed scale. A much larger history would warrant
  virtualization (out of scope; noted).
