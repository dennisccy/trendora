# goal-ops-hardening-iter-6 Frontend Handoff

**Phase:** goal-ops-hardening-iter-6
**Date:** 2026-07-20
**Agent:** developer
**Status:** complete

## What Was Built

Two fetch-scheduling (request-timing-only) fixes closing J-06's last two real-browser latency violations
carried over from iter-5. No new UI surface, no new displayed value, no new user action — every card/panel
keeps its existing appearance and states; only WHEN each on-load request fires changed.

- **Dashboard (`/`)** — `PhaseCrossViewCard`'s on-mount `Promise.all` fetch (indexes-full + regime-history-full
  + market-phase-full) is now deferred 250ms after mount via `window.setTimeout` (cleared alongside the
  existing `AbortController` on unmount/deps-change). The existing `status === "loading"` skeleton
  (`h-[28rem] animate-pulse`) is set synchronously before the deferral, so the deferred window shows the
  same skeleton it always did — never a blank gap. Fixes `GET /api/indexes?full=true` real-browser latency:
  1.68-2.19s (iter-5) -> 821-872ms (3/3 reloads, this iteration).
- **Data Manager (`/data`)** — `loadAvailability()` (feeding `AvailabilityHeatmap`) is now deferred 2500ms
  after `loadOverview()` fires in the page's mount effect, via the same `window.setTimeout`/cleanup pattern.
  The heatmap's own `{ kind: "loading" }` initial state (its `Loader2` spinner) already covers the deferred
  window unchanged. Fixes `GET /api/data/availability` real-browser latency: 2.8-3.0s (previously
  unbudgeted) -> 1000-1052ms (3/3 reloads, this iteration).

## Root cause (more specific than iter-5's working hypothesis)

iter-5 hypothesized pure Chrome 6-connections-per-origin queuing for both. Direct measurement this
iteration (isolated `fetch()` timing + a controlled concurrent-`curl` probe — see the dev handoff and
`reports/perf-budgets.md` for the full evidence) shows the Data Manager case is specifically **GIL
contention between two CPU-bound Python request handlers** (`GET /api/data/availability` and
`IndexVendorPanel`'s own `GET /api/indexes?full=true`, both independently fired on `/data`'s mount) — not a
literal browser connection-queue artifact. The fix shape (defer one request past the other's completion) is
the same either way; only the diagnosis differs, and is documented in-code and in `perf-budgets.md` for
accuracy.

## Files Changed

- `apps/frontend/components/phase-cross-view-card.tsx` — 250ms deferred fetch, preserving loading/ok/empty/
  error states and AbortController cleanup verbatim.
- `apps/frontend/app/data/page.tsx` — 2500ms deferred `loadAvailability()` call in the mount effect only
  (every other call site — job completion, retry/dismiss, removal — calls both together, unchanged).
- `runs/goal-session-ops-hardening/journey-scripts/J-01.json` — step 6 rewritten (see dev handoff; not a UI
  code change, a golden-script fix).

`apps/frontend/app/page.tsx` was NOT touched — no coordination signal was needed; the deferral lives
entirely inside `PhaseCrossViewCard`'s own effect.

## UI Evolution

- New user-facing capability: none.
- New information displayed: none.
- New user actions: none.
- UI surface changes: none — same cards, same content, same loading/error/empty affordances. Verified live
  (screenshot + DOM inspection): the Dashboard's cross-view skeleton and the Data Manager's availability
  spinner render identically to before; only the timing of the underlying fetch changed.
- Navigation changes: none.

## States Verified (live, real browser)

- **Loading (deferred window):** confirmed via screenshot — the Dashboard shows its `animate-pulse`
  skeleton and the Data Manager shows its `Loader2` spinner + "Loading availability…" text throughout each
  deferral window; never a blank gap.
- **Ok:** both cards render their real data once the deferred fetch resolves (indexes chart / availability
  heatmap), confirmed via DOM text checks (`"Regime × phase cross-view"` present, heatmap cells present).
- **Error/abort (TC-10):** live-tested by rapidly stepping the global as-of date twice in immediate
  succession right after a Dashboard page load (aborting `PhaseCrossViewCard`'s in-flight/deferred fetch
  mid-flight via its `AbortController`). Observed: the card showed its existing loading skeleton through the
  transition (screenshot captured), then settled cleanly to the "ok" state with the new as-of's data (0
  stray skeletons remaining, `"Regime × phase cross-view"` text present) — never a blank or frozen frame.
  This exercises the exact code path TC-10 describes: the cleanup function clears the pending timer AND
  aborts the controller, so an in-flight (already-fired) fetch's `.catch` correctly no-ops
  (`!controller.signal.aborted` guard) rather than clobbering the new effect's fresh "loading" state.

## Known Issues

See the dev handoff (`docs/handoffs/goal-ops-hardening-iter-6-dev.md`) for the full account — most
importantly, a severe, PRE-EXISTING, unrelated-to-this-diff backend regression was discovered on
`/evidence` (555.97s cold) and `/research/event-study` (91.95s cold / 1.46s warm) during this iteration's
own re-measurement pass. Neither page's frontend code was touched this iteration; both are backend compute
regressions from live-DB data growth, flagged for a fresh decomposer pass, not fixed here.
