# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

This LEAN iteration delivered the two target journeys J-42 (uniform ISO date presentation) and
J-43 (deep-linkable as-of) — both frontend-only, on existing surfaces. No backend code changed.

### J-42 — Uniform ISO date presentation (Capability 35)
- **New shared date authority** `apps/frontend/lib/dates.ts` — the single module that formats every
  displayed calendar date as `yyyy-MM-dd` and validates typed dates:
  - `ISO_DATE_FORMAT` / `ISO_DATE_PLACEHOLDER` constant (one source of truth for the format token).
  - `formatIsoDate(value)` — locale-proof formatter. It slices/validates the ISO string (no
    `toLocaleDateString`, no timezone shift); normalises an ISO datetime to its date part; renders an
    em-dash for null/unparseable (never a fabricated date).
  - `formatIsoDateTime(value)` — `yyyy-MM-dd HH:mm:ss` for run/scan timestamps.
  - `isValidIsoDate(value)` — exact `yyyy-MM-dd` shape **and** calendar validity via a UTC round-trip,
    so `2026-13-40` and `10/06/2026` (and `2026-02-30`, `2026/05/01`, `2026-2-1`) are all rejected.
- **Every date-display surface routed through the shared formatter** (the format authority sweep):
  as-of switcher options + "(historical)" indicator, the dashboard "Data as-of" badge, stocks /
  sectors / themes "as of D" badges, stock-detail "as of D" + forward-region labels, scanner-runs list
  (run date link) and detail (as-of + "Scanned" timestamp + regime title), watchlist "as of D" +
  date-added column, backtest "Viewing as-of D" badges, the evidence-panels expanding-window header +
  as-of range, and (on `/data`) coverage ranges, gap ranges, the per-symbol date-range column,
  intra-series-gap diagnostic ranges, job-card hint range, run-history started-at + range columns,
  unfinished-import range, and the remove-preview removable range + cascade snapshot dates. The data
  page's pre-existing per-component `fmtDate` is now a thin alias of the shared `formatIsoDate`, so the
  module is the one authority (no per-component format literal remains).
- **Chart tooltip/crosshair dates** (`components/price-chart.tsx`) now render `yyyy-MM-dd` via
  Lightweight-Charts `localization.timeFormatter` → `formatIsoDate`. Compact axis **tick** labels stay
  the library default (abbreviated scale marks, per the J-42 acceptance carve-out).
- **Four native `<input type="date">` pickers on `/data` replaced with validated ISO text inputs**
  (new in-page `IsoDateInput` component): fetch/backfill start+end and remove-data start+end. Each is a
  `type="text"` field with a `yyyy-MM-dd` placeholder, exact-format + calendar validation, a visible
  inline error (`role="alert"`), and `aria-invalid` wiring. The fetch form's **Start** is blocked while
  either date is empty/invalid (with an Enter-submit guard); the remove form's **Preview** is blocked
  while a non-empty date is invalid (those two are optional). The submitted job uses exactly the typed
  string — these remain job parameters, never the global as-of control.

### J-43 — Deep-linkable as-of (URL-serialized single state, Capability 36)
- Extended `components/asof-provider.tsx` so the ONE global as-of state is serialized to the URL:
  - A new inner `AsOfUrlSync` component (mounted inside the provider, behind a `<Suspense fallback={null}>`
    boundary because it reads `useSearchParams()` — App-Router requirement) is the **single reader/writer**
    of the `?asof` param.
  - **Restore on load:** once the canonical run list is ready, a URL `?asof=D` where D is a valid,
    KNOWN historical run date is restored into the global control (switcher reflects it). A malformed
    value, the latest date, or an unknown date is ignored → latest view, and the stale param is stripped.
  - **Serialize on change:** historical selection → `?asof=D` via `router.replace` (`scroll: false`, no
    history spam), preserving other query params; latest/null → the param is removed (URL date-free at
    latest).
  - **Survives client-side navigation:** the serialize effect also re-runs on `pathname`, so a
    leaderboard row `<Link>` → `/stocks/[ticker]` (which drops query params) RE-STAMPS `?asof` onto the
    new route — the historical view survives the click-through (the provider, mounted in the shell, kept
    the state). Reload and a fresh tab restore via the load-restore path.
  - No page parses or holds its own date state; J-18 is honored (no page-local date state) per the J-43
    amendment.

## Files Changed
- `apps/frontend/lib/dates.ts` -- NEW. The single ISO date format authority: `ISO_DATE_FORMAT`,
  `formatIsoDate`, `formatIsoDateTime`, `isValidIsoDate`.
- `apps/frontend/components/asof-provider.tsx` -- `?asof` URL serialization/restore (J-43) via a
  Suspense-wrapped `AsOfUrlSync`; provider is the sole reader/writer of the param.
- `apps/frontend/components/asof-switcher.tsx` -- switcher options + "(historical)" indicator routed
  through `formatIsoDate`.
- `apps/frontend/components/price-chart.tsx` -- crosshair/tooltip date via `localization.timeFormatter`
  → `formatIsoDate` (`isoFromTime` normalises the lightweight-charts `Time`).
- `apps/frontend/components/evidence-panels.tsx` -- expanding-window header + as-of range via shared formatter.
- `apps/frontend/app/data/page.tsx` -- new `IsoDateInput` (validated ISO text input); four native date
  pickers replaced; `fmtDate` re-pointed to the shared `formatIsoDate`; all remaining `/data` date
  renders (coverage / diagnostics / job card / run history / unfinished imports / remove preview) routed
  through it; submit/preview blocked while a date is invalid.
- `apps/frontend/app/page.tsx`, `app/stocks/page.tsx`, `app/stocks/[ticker]/page.tsx`,
  `app/sectors/page.tsx`, `app/themes/page.tsx`, `app/watchlist/page.tsx`,
  `app/scanner-runs/page.tsx`, `app/scanner-runs/[runId]/page.tsx`, `app/backtest/page.tsx`
  -- date/timestamp renders routed through the shared formatter.

No backend, DB, config, or API-contract change — dates remain ISO end-to-end (anti-goal respected).

## Tests Run
- **Frontend typecheck (gate):** `cd apps/frontend && npx tsc --noEmit` → **exit 0** (TypeScript strict,
  all changed routes/components). ESLint is not installed in this project (no `eslint` binary / no
  `eslint-config-next`, and `next lint` only offers its interactive first-run setup) — prior iterations
  used the Next.js production build as the frontend gate. `next build` was intentionally NOT run because
  a prod build clobbers the dev-server `.next` and breaks browser-QA (documented session gotcha); the
  equivalent coverage was obtained via `tsc --noEmit` PLUS a live `next dev` compile of every changed
  route (all returned HTTP 200, zero compile errors/warnings — see below).
- **Frontend runtime smoke (next dev on :3835):** every route compiled clean and returned HTTP 200 —
  `/`, `/data`, `/stocks`, `/stocks/NVDA`, `/sectors`, `/themes`, `/backtest`, `/scanner-runs`,
  `/watchlist`. J-43 param handling: `/stocks?asof=2026-05-01`, `/stocks?asof=not-a-date`,
  `/stocks?asof=2026-01-01`, `/backtest?asof=2026-05-01`, `/?asof=2026-05-01` all rendered HTTP 200
  (no crash on valid/malformed/unknown param). The `<Suspense>` boundary works (no `useSearchParams`
  deopt error in the dev log). Server stopped afterward (port 3835 free).
- **Date-logic assertion (J-42 core):** the `isValidIsoDate` / `formatIsoDate` logic was asserted
  against the exact spec error cases — `2026-13-40` → invalid, `10/06/2026` → invalid, `not-a-date` →
  invalid, `2026-02-30` → invalid; `2026-05-01` valid; `2026-05-01T13:30:00` → `2026-05-01`;
  null → em-dash. All assertions PASS.
- **Backend full pytest suite (gate — closes the iter-0 collect-only gap):**
  `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
  Result: **622 passed, 4 skipped, 0 failed** in 2199.13s (36m39s), exit 0. No regressions — this is
  +1 vs the recorded baseline (621 pass / 4 skip), consistent with the suite having grown by a test at
  the same product commit; no backend code was touched this iteration. (The full suite is slow because
  of the walk-forward boot-resilience tests, as documented in session memory.)

## Known Issues
- The live, in-browser round-trip of the J-43 `?asof` restoration through the switcher state (select D →
  param appears → reload/new-tab/click-through restores D → return to latest → param disappears →
  invalid param → "Latest") is structurally complete and renders without error at the HTTP level, but
  the client-side state restoration itself is best confirmed by the browser-QA agent (a live backend is
  required for the run list; one was deliberately NOT started during the pytest run to avoid the
  documented `scanner_runs` DB-race when two backends share the session DB). Per session memory, drive
  the switcher in QA via a native-setter + bubbled change event (the Chrome MCP `select` action does not
  fire React `onChange` on this frontend).
- No frontend unit-test runner exists in this project (by design per the iter spec); ISO-input
  validation and `?asof` restore are verified via the browser error-state / deep-link checks.
