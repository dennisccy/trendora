# goal-ops-hardening-iter-24 Frontend Handoff

**Phase:** goal-ops-hardening-iter-24
**Date:** 2026-07-26
**Agent:** developer
**Status:** complete

## What Was Built

J-09's new user-facing capability: any operator, on any page, can see live whether the backend is
currently running the iter-20 background historical forward-aggregate compute, and on `/data` see the
full detail (which as-of date(s), horizon progress, and the most recent outcome). Read-only disclosure —
no new user action, no new fetch (everything reads the SAME shared `/api/health` poll `ReadinessProvider`
already runs).

- **`lib/api.ts`** — three new types: `BackgroundComputeActive` (`asof_key`, `dataset_version`,
  `started_at`, `elapsed_ms`, `horizons_done`, `horizons_total`), `BackgroundComputeOutcome` (`asof_key`,
  `dataset_version`, `outcome: "completed" | "failed"`, `started_at`, `finished_at`, `duration_ms`,
  `reason: string | null`), and `BackgroundComputeStatus` (`{active, recent_outcomes}`). `HealthStatus`
  gains `background_compute: BackgroundComputeStatus`.
- **`readiness-provider.tsx`** — `ReadinessContextValue` gains `backgroundCompute:
  BackgroundComputeStatus | null`, set from the SAME `fetchHealth()` poll (`data.background_compute`),
  and reset to `null` (honest, never fabricated) on a failed poll — mirrors how `preflight` already
  degrades to `null` on a network error.
- **`health-badge.tsx`** — one additional inline `Badge` (`variant="accent"`,
  `data-testid="background-compute-indicator"`), rendered right after the existing readiness pill
  whenever `backgroundCompute.active.length > 0`, in ANY readiness state (`loading`, `ready`,
  `initializing`, `awaiting_snapshot`, `unavailable` — it's a sibling element, not gated by `state`).
  Reads `useReadiness()` (already imported by this component) — no second fetch. Text: "background
  compute running (N)".
- **`app/data/page.tsx`** — new `BackgroundComputePanel` (plus two small helpers,
  `BackgroundComputeRow` and `LastOutcomeSummary`), placed immediately after the existing
  `RunHistoryPanel` in the page's panel stack (matching the plan's Layout requirement). Uses the
  existing `Card`/`PanelTitle` convention (same as `JobProgressPanel`/`RunHistoryPanel`), the existing
  `Badge` component (`variant="accent"` for an active window, `variant="ok"`/`"danger"` for a
  completed/failed outcome), and reuses the ALREADY-EXISTING `fmtDuration()` helper (converting
  `elapsed_ms`/`duration_ms` to seconds) rather than inventing a new duration formatter. States handled:
  - **idle, never dispatched**: "No background compute running. Last outcome: none yet."
  - **idle, with history**: "No background compute running." + the most recent outcome's summary.
  - **active**: one row per in-flight window (as-of badge, elapsed, `horizons_done`/`horizons_total`,
    dataset version) + the most recent outcome (if any) below the active list.
  - **failed outcome**: a `danger`-variant "Failed" badge + the non-null `reason` string shown inline.
  - A one-line process-lifetime disclosure note ("Since the last backend restart — this history is
    process-lifetime only, never persisted.") is always shown, in every state.

## Visual conformance

- No new component primitives — `Card`, `PanelTitle`, `Badge` only (all pre-existing).
- No new visual effect — the active-window badge reuses the SAME `variant="accent"` +
  `animate-pulse` dot convention `HealthBadge`'s own `awaiting_snapshot`/`initializing` pills already use.
- Layout: appended to the existing vertical panel stack on `/data`, after `RunHistoryPanel` — no new grid
  or page structure.
- No new nav entry, no new route (per the plan's explicit scope boundary).

## Files Changed

- `apps/frontend/lib/api.ts` -- `BackgroundComputeActive`/`BackgroundComputeOutcome`/
  `BackgroundComputeStatus` types; `HealthStatus.background_compute`.
- `apps/frontend/components/readiness-provider.tsx` -- `backgroundCompute` field on
  `ReadinessContextValue`, read from the existing poll, reset honestly to `null` on a failed poll.
- `apps/frontend/components/health-badge.tsx` -- the conditional `background-compute-indicator` badge.
- `apps/frontend/app/data/page.tsx` -- new `BackgroundComputePanel`/`BackgroundComputeRow`/
  `LastOutcomeSummary`; new import of `useReadiness` + the two new `lib/api.ts` types; panel wired into
  the render after `RunHistoryPanel`.

## Tests Run

This project has no frontend unit-test runner (no `test` script in `package.json`; this codebase's
convention for pure-logic modules is a standalone `node lib/*.test.ts` file, e.g. `lib/api-base.test.ts`
— none of this iteration's changes introduced a new pure logic function; `BackgroundComputePanel` reuses
the existing `fmtDuration` verbatim). Verification used instead:

```
cd apps/frontend && npx tsc --noEmit -p tsconfig.json
```

Result: **0 errors.**

Additionally, the data this panel/badge render was verified against a REAL running backend end-to-end
(see the dev handoff's "Tests Run" section and `reports/perf-budgets.md`'s Iteration 24 entry): two live
historical `/backtest` requests produced real `active` windows with live-incrementing `horizons_done`
(0→1→2→4 of 5) and `elapsed_ms`, followed by newest-first `recent_outcomes` entries with real
`duration_ms` — confirming the exact shape `lib/api.ts`'s new types and the panel's rendering logic
expect.

## Known Issues

- **No live browser screenshot/render captured by me this session** — I verified the underlying JSON
  shape end-to-end against a real backend (see above) and type-checked the component tree, but did not
  drive an actual browser to confirm the DOM renders as designed (badge presence/absence timing, panel
  copy in each state). That is the browser-qa-agent's job (TC-10, the primary J-09 browser test) — a
  narrow test-only force-dispatch hook is available per the phase spec's own notes if a real BCW proves
  hard to trigger deterministically inside the QA window, but I did not need one for my own live check
  (a genuinely uncomputed historical `as_of` triggered a real window on the first try).
- The idle-copy sentence ("No background compute running. Last outcome: none yet.") is a single fixed
  string for the "never dispatched since boot" case; once ANY outcome exists it switches to showing that
  outcome's summary instead of concatenating both sentences — matches the plan's phrasing ("...or the most
  recent entry"), not a combination of both.
