# goal-ops-hardening-iter-4 Frontend Handoff

**Phase:** goal-ops-hardening-iter-4
**Date:** 2026-07-20
**Agent:** developer
**Status:** complete

## What Was Built

A 4th visual state for the existing global readiness badge (`HealthBadge`, top bar, every page). No new
page, panel, form, or navigation — this is an honesty fix to an EXISTING capability (the badge already
had 3 states: Ready / Initializing… / Backend unavailable; this adds a calmly-distinct 4th: **"Snapshot
pending"**), so the operator can tell "new data landed but the analytical snapshot hasn't caught up yet"
apart from an actual crash.

- **New badge state — `awaiting_snapshot`.** Renders when the backend's readiness state (from the shared
  `useReadiness()` context, itself fed by the single canonical `GET /api/health` poll) is
  `"awaiting_snapshot"`:
  - `data-testid="readiness-badge"` `data-state="awaiting_snapshot"` (same testid convention as the
    other 3 states, so existing/new automated checks can select it the same way).
  - Visible label: **"Snapshot pending"** — deliberately NOT "Backend unavailable" and not a reuse of any
    other state's wording.
  - Visual treatment: the existing `Badge` component's `accent` variant (`border-accent bg-surface-2
    text-accent` — already defined in `apps/frontend/components/ui/badge.tsx`, no new color token, no new
    component). A static (non-pulsing) status dot in `bg-accent` — deliberately different from
    `initializing`'s pulsing dot, since this condition does not resolve itself; it persists until an
    operator runs a backfill/rebuild.
  - Recovery-pointer text: when the backend supplies a non-null `readiness_detail` string, it renders
    inline after an em-dash (e.g. "Snapshot pending — New data has landed for the benchmark (SPY) through
    2026-07-18, but no snapshot has been produced for that date yet. Run a backfill or rebuild on Data
    Manager to produce it."). No new navigation/link — this is plain text naming where to act, reusing the
    existing Data Manager page operators already know (`/data`).
- **Type widening (`apps/frontend/lib/api.ts`).** `ReadinessState` gained the `"awaiting_snapshot"`
  literal; `HealthStatus` gained `readiness_detail: string | null` alongside the existing `readiness`/
  `warmup` fields. Purely additive — no existing field renamed or removed.

## Files Changed

- `apps/frontend/lib/api.ts` — widened `ReadinessState` (line ~115) with the new literal; added
  `readiness_detail: string | null` to `HealthStatus`; doc-comments updated.
- `apps/frontend/components/health-badge.tsx` — new `else if (state === "awaiting_snapshot")` branch
  (placed between the existing `initializing` and the final `unavailable` `else`); the component's own
  context-detail fetch (`useEffect`, previously mount-once) now re-fires on `state` transitions (see
  "Deviation" below).

## UI Evolution

- **New user-facing capability:** none new — this is an honesty fix to the EXISTING global readiness
  badge (shipped in a prior iteration).
- **New information displayed:** the badge can now show a 4th, calm, visually distinct state instead of
  conflating "new data landed, snapshot pending" with the crash-identical "Backend unavailable" red
  presentation.
- **New user actions:** none — no new button/form. The recovery-pointer text names where to act (Data
  Manager) but is plain text, not a link/button.
- **UI surface changes:** `HealthBadge` only (global, top bar, every page). No new page or panel.
- **Navigation changes:** none.
- **States handled:** the 4 states are now mutually exclusive and each visually/textually distinct —
  `loading` (neutral, pulsing), `ready` (positive, static), `initializing` (warning, pulsing, "history
  n/m"), `awaiting_snapshot` (accent, static, recovery text), `unavailable` (danger, static, "Backend
  unavailable"). No other loading/empty/error treatment changed this iteration.

## Visual Requirements Compliance

- **Component library:** used the existing `Badge` component exclusively (no raw HTML/new component) —
  `variant="accent"`, already defined and already used elsewhere in this codebase (e.g. `sidebar.tsx`,
  `market-phase-card.tsx`).
- **Color tokens:** `bg-accent`/`text-accent`/`border-accent` — all pre-existing CSS variables (`--accent:
  #4fd1c5`), no arbitrary hex/new token introduced.
- **Layout:** no layout change — renders in the badge's existing top-bar slot via the same `if/else if`
  chain the other 3 states already use.
- **Interactive states:** N/A — the badge is a read-only status pill, not an interactive control (matches
  the existing 3 states, none of which have hover/focus/active treatments either).
- **Responsive behavior:** unchanged — the badge sits inside the existing `flex flex-wrap` container that
  already wraps the other badges at narrow widths.

## Tests Run

- `cd apps/frontend && npx tsc --noEmit` — **clean, zero errors.** This project has no configured JS test
  runner (`package.json` has no `test` script, no jest/vitest config) — TypeScript's own type-checker is
  the closest automated frontend verification available, and it passed cleanly against both changed files
  (the widened `ReadinessState`/`HealthStatus` types and the new badge branch's usage of them).
- **No component/visual test was run** (none exist in this project for `HealthBadge`). Visual
  correctness (badge renders the right label/color/testid for the new state, and the recovery text
  actually appears) is **deferred to browser-qa-agent**, per the phase spec's own TC-4 acceptance test,
  which is explicitly a browser-level check.
- **No dev server was started this iteration** (see the companion dev handoff's Pre-Handoff Verification —
  time-boxed by the coordinator's explicit instruction to stop blocking and finish). A direct Python import
  of the backend's `main:app` succeeded cleanly, which is evidence the backend wiring this component
  depends on (the new `readiness_detail` JSON key) is structurally sound, but the actual rendered badge in
  a browser has not been visually confirmed by this developer step.

## Known Issues

- **The one-shot context-detail fetch inside `HealthBadge` now re-fires on every `state` transition**
  (previously exactly once, on mount). This is a deliberate, small behavior change — see the companion dev
  handoff's "Known Issues / Deviations" section for the full reasoning (in short: the recovery-pointer text
  needs to be reasonably fresh at the moment the badge flips to the new state, and re-fetching on state
  transitions achieves that without touching `readiness-provider.tsx`, which the plan said not to touch).
  State transitions are infrequent (not a per-poll-tick refetch), so this does not meaningfully increase
  request volume, but it is a change in when this fetch runs and is worth reviewer attention.
- **The exact wording "Snapshot pending" is a developer choice**, not a spec-pinned literal string — the
  phase spec only fixed the `state` value and field shape, not the visible label. If the reviewer or a
  later UX pass wants different wording, it is a one-line change in `health-badge.tsx`, not a contract
  change.
- **Visual/browser confirmation of the new pill (color, spacing, actual rendered text) has not been done
  by this developer step** — deferred to browser-qa-agent (see Tests Run above).
