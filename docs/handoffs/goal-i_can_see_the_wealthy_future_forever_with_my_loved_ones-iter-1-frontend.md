# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-1
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built (UI)

Two cross-cutting frontend contracts now hold across the existing information architecture — no new
page, no nav change, no layout change.

### J-42 — every displayed date reads `yyyy-MM-dd` (locale-proof)
- **One shared date module** (`lib/dates.ts`) is the format authority. Every surface that shows a
  calendar date re-formats through `formatIsoDate` (and `formatIsoDateTime` for run/scan timestamps),
  so output is `yyyy-MM-dd` regardless of browser locale. No component holds its own date-format literal
  and nothing renders a date through a locale-dependent path (no `toLocaleDateString`, no native date
  widget). Surfaces swept: as-of switcher + historical indicator, dashboard / stocks / sectors / themes
  / stock-detail / watchlist / scanner-runs (list + detail) / backtest date badges, the forward-tested
  evidence window header + range, the **chart tooltip/crosshair date**, and on `/data` the coverage
  ranges, missing-data diagnostic ranges, job-card range, run-history timestamps + ranges, unfinished
  imports, and remove-preview ranges + cascade dates. Visually unchanged where the value was already ISO
  — the change is that one module now guarantees the format.
- **`/data` date entry is now locale-proof.** The four native `<input type="date">` pickers
  (fetch/backfill start + end, remove-data start + end) are replaced by validated ISO **text** inputs
  (`IsoDateInput`):
  - Placeholder `yyyy-MM-dd`, monospace (`num`) field matching the existing design tokens (`FIELD`).
  - Exact-format + calendar validation: typing `2026-13-40` or `10/06/2026` shows a visible inline
    error (red border + amber/red alert text with a warning icon, `role="alert"`, `aria-invalid`).
  - Submit is blocked while invalid — the fetch **Start** button disables until both dates are valid
    ISO (with an Enter-submit guard); the remove **Preview** button disables while a non-empty date is
    invalid. A valid submit sends exactly the typed date string.
  - These remain **job parameters** — they never write `?asof` or touch the global as-of control.

### J-43 — the historical as-of view is shareable and durable
- The single global as-of state is serialized into the URL as `?asof=yyyy-MM-dd` while a historical
  date is selected, and the URL is **date-free at the latest date**. The top-bar switcher is the one
  control; the provider is the only reader/writer of the param.
- Restore paths that now preserve the date: **reload**, **a fresh tab / shared link**, and a
  **leaderboard row → `/stocks/[ticker]` click-through** (the param is re-stamped onto the new route).
- An invalid/unknown `?asof` (malformed, or a date with no run) degrades safely to the latest view — the
  switcher shows "Latest", no crash, no fabricated date.

## UI Surfaces Changed
- `/data` — four date fields are now validated ISO text inputs with inline error states; submit/preview
  gated on validity. (No other restyle.)
- URL bar on every date-scoped page — carries `?asof=yyyy-MM-dd` while historical; date-free at latest.
- Chart tooltip/crosshair dates and all remaining date renders — formatted through the shared formatter
  (visually unchanged where already ISO).

## Design System Adherence
- Reused existing tokens/components only: the shared `FIELD` input class, `Badge`, `Card`, lucide
  `AlertTriangle`, and the `--neg` / `--warn` palette tokens for the inline error. No arbitrary colors,
  no new effects, no new component library elements. The error state is consistent with the page's other
  `role="alert"` messages.
- Loading/empty/error states on `/data` are unchanged and still present (the new validation error is an
  additional inline state on the inputs, not a replacement).

## Tests / Verification
- TypeScript strict typecheck `npx tsc --noEmit` → exit 0.
- `next dev` live compile of all changed routes → HTTP 200, zero compile errors/warnings; `<Suspense>`
  around `useSearchParams` verified (no deopt). `?asof` valid/malformed/unknown all render 200.
- Date-validation logic asserted against the spec error cases (`2026-13-40`, `10/06/2026`, `not-a-date`
  rejected; valid ISO accepted; datetime normalised to date).
- Full backend pytest suite: **622 passed, 4 skipped, 0 failed** (exit 0, 36m39s) — no backend change;
  guard run closing the iter-0 collect-only gap.

## Notes for Browser-QA
- Drive the as-of switcher via a native-setter + bubbled `change` event in an evaluate call, then assert
  the live DOM — the Chrome MCP `select` action does not fire React `onChange` on this frontend
  (session memory).
- J-18 is judged on "no page-local independent date state" — `?asof` in the URL while historical is
  REQUIRED by J-43 and is the serialization of the one state; never judge J-18 on URL date-freeness.
- A live backend is needed to populate the run list for the J-43 round-trip; if every page renders as a
  dead un-hydrated shell (404 on `_next/static/chunks/main-app.js`), the dev `.next` was clobbered by a
  prod build — record SKIPPED, not FAIL.
