# goal-i_can_see_the_wealthy_future_forever-iter-25 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-25
**Date:** 2026-06-09
**Agent:** developer
**Status:** complete

## What Was Built
Two additive panels on the EXISTING `/data` Data Manager page (no new page, route, or sidebar entry; no
nav-skeleton change; the global as-of switcher is untouched — the pull/retry date inputs are job
parameters, not a viewing-date control).

### J-37 — Missing-data diagnostic panel (`MissingDataDiagnosticPanel`)
- Renders directly below the Coverage panel. Three honest categories — No history, Thin history,
  Intra-series gaps — each as a category section listing rows of symbol + EXACT shortfall, read verbatim
  from `coverage.diagnostic` (the page re-formats; it computes no shortfall).
  - No history: `bars_have / bars_needed bars`.
  - Thin: `bars_have / bars_needed bars` (no Pull button — transparency only).
  - Intra-series gap: `N missing (first_gap → last_gap)`.
- A per-row "Pull the missing data" button on every PULLABLE row (no-history + intra-series-gap) and a
  "Pull all missing" button (dispatches each gap-exact shortfall sequentially). Each pull starts a fetch
  over EXACTLY that `(symbol, [start,end])` scope via `pullMissingData` and surfaces in the existing live
  job card; on completion the page reloads coverage (the row clears/shrinks; the J-36 table reflects new
  bars). The chosen import source + (for a needs-key source) the session-only pasted key ride along.
- Empty state: `affected_count === 0` renders a clean "No missing data" empty-state — no spurious pull.

### J-38 — Unified Unfinished-imports panel (`UnfinishedImportsPanel`)
- REPLACES the old `ResumableImportsPanel`. Lists every unfinished import (resumable + partial + failed)
  from `unfinished_imports`, each row showing a status badge, chunk progress where applicable, the
  server-built plain-language `state` (rendered verbatim), and done/remaining/failed counts.
  - Checkpoint rows (resumable): `ResumeControl` (Resume, re-prompting the session-only key for a needs-key
    source) + `DismissControl` (Remove — deletes the resumable checkpoint).
  - Run rows (partial/failed): new `RetryControl` (Retry remaining — re-prompts the session-only key for a
    needs-key source) + `DismissControl` (Dismiss — soft-dismiss; the run stays in Run history below).
- Hidden when there are no unfinished imports.

## Design / States
- Reuses the existing `/data` `Card` panels, `Badge`, `EmptyState`, the `statusVariant` palette mapping
  (ok green / partial+resumable amber / failed red / running teal), and the established button treatments.
  Thin/missing rows use the amber/muted treatment; failed uses the danger treatment; resumable/paused amber.
- States handled: loading (job polling reuses the existing job card), empty (empty diagnostic / no
  unfinished imports → hidden or empty-state), error (provider-unreachable pull/retry → the job card / a
  styled inline alert; needs-key without key → an explicit re-prompt). Every interactive control has
  hover/focus/active + disabled states.
- Session-only keys live in component memory only — never persisted to localStorage/URL/cookie, cleared on
  submit/completion.

## Files Changed
- `apps/frontend/lib/api.ts` — `MissingDataDiagnostic` (+ `DiagnosticNoHistory`/`DiagnosticThin`/
  `DiagnosticGap`) on `DataCoverage`; `UnfinishedImport` on `DataOverviewResponse`; `pullMissingData`,
  `retryDataJob`, `dismissUnfinishedImport` clients; a `symbols` option on `startDataJob`.
- `apps/frontend/app/data/page.tsx` — `MissingDataDiagnosticPanel` + `DiagnosticCategory`;
  `UnfinishedImportsPanel` + `RetryControl` + `DismissControl` (replacing `ResumableImportsPanel`); the
  `handlePull` / `onUnfinishedChanged` handlers; wiring into the page.

## Tests Run
`cd apps/frontend && npx tsc --noEmit` → clean (no type errors). The browser captures (J-37/J-38 flows +
J-39/J-35 re-capture + J-18 one-date-selector re-confirm) are the QA/browser-qa-agent gate's job on a
clean hydrated build (env-fix first: stop strays by port, `rm -rf .next`, restart `next dev`, confirm
`main-app.js` → 200 and the health badge cleared BEFORE driving the UI).

## Known Issues
- `data-testid` hooks added for the browser gate: `missing-data-diagnostic`, `pull-all-button`,
  `pull-row-button`, `diagnostic-no-history` / `diagnostic-thin-history` / `diagnostic-intra-series-gaps`,
  `unfinished-imports`, `unfinished-checkpoint` / `unfinished-run`, `unfinished-state`, `retry-button`,
  `dismiss-button` (the existing `resume-button` is reused).
