# goal-ops-hardening-iter-61 Frontend Handoff

**Phase:** goal-ops-hardening-iter-61
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete

## What Was Built

- **`/data` now runs an ambient, idle-cadence coverage refresh** — the fix for the evaluator-reported
  stale coverage-count defect (root-caused as a frontend rendering gap, not a backend one; see the dev
  handoff's "What Was Built" for the full diagnosis). Before this change, `/data`'s coverage/availability
  panels refreshed ONLY on page mount and when this SAME tab's own tracked job left `"running"` — a
  backfill started elsewhere (another tab, a script, or a later browser-qa pass visiting `/data` well
  after an earlier pass's own ingest completed) left an already-open or later-visited `/data` view
  rendering pre-ingest numbers indefinitely. Now `/data` also reloads coverage + availability + the as-of
  run list on the SAME idle cadence (30 s, config-derived) the top-bar readiness badge already backs off
  to once ready — closing the staleness window to at most one idle-poll interval, regardless of who or
  what triggered the underlying ingest.
- **`ReadinessProvider` additively exposes `pollIdleIntervalSeconds`** so `/data` (or any future page)
  can reuse the SAME already-polling readiness fetch's cadence for its own ambient refresh, without a
  second poll literal and without a new backend field or config key (`GET /api/health`'s
  `poll_idle_interval_seconds` already existed; it just was not threaded through the shared context
  before this iteration).

## Files Changed

- `apps/frontend/components/readiness-provider.tsx` -- `ReadinessContextValue` gains
  `pollIdleIntervalSeconds: number | null`; populated on each successful poll from the already-fetched
  `data.poll_idle_interval_seconds`; `null` before the first poll resolves and on a failed poll (matches
  every sibling field's existing honesty convention — `state`, `warmup`, `preflight`, `backgroundCompute`
  are all treated the same way). Every existing reader of `useReadiness()` (health-badge, preflight-banner,
  warming-state, backtest page, research labs) is unaffected — this is a purely additive field.
- `apps/frontend/app/data/page.tsx` -- new `useReadiness()` destructure (`pollIdleIntervalSeconds`) + one
  new `useEffect` that arms a `setInterval` on that cadence, unconditionally (not gated on this tab's own
  job state), calling the SAME `loadOverview()` / `loadAvailability()` / `refresh()` (as-of run list) the
  existing job-completion branch already calls. No other page behavior changed; no new component, no new
  visual state.

## UI Evolution

- New user-facing capability: none — this is a repair of an already-shipped display path.
- New information displayed: none. New user actions: none. Navigation: unchanged.
- Visual states: unchanged — the SAME coverage panel, the SAME loading/error/empty states from before this
  iteration; only the cadence at which the panel's numbers can silently become current has changed (from
  "only on this tab's own job completion" to "at most every 30 s regardless").
- Product-visible delta: a user who runs a backfill (from this tab, another tab, or a script) and stays on
  `/data` now sees the Snapshot Dates / Backfill Gaps counts update within ~30 s of the job's finalize
  hook persisting them, instead of the previous pre-job pair persisting indefinitely until a manual reload.

## Tests Run

- `npx tsc --noEmit` — clean, zero errors (both changed files).
- All 13 `apps/frontend/lib/*.test.ts` files (`npx tsx <file>`, this project's documented convention —
  no React/DOM test harness exists here) — all pass, no regression.
- No new unit test was added for the new `useEffect`/`setInterval` itself: this project's existing
  precedent (the pre-existing job-polling `useEffect`/`setInterval` block in the SAME component, a few
  lines above the new one) is also untested at the unit level — its correctness is proven by TDD-style
  pure-function extraction only where there IS interesting decision logic to extract (e.g.
  `regime-cell-status.ts`, `background-compute-last-outcome.ts`); a bare "call this callback every N ms,
  unconditionally" has no such logic, so forcing an extraction here would be an abstraction the codebase
  does not otherwise use for this exact shape of wiring (this project's own simplicity bar). Verified
  instead by live/manual check: a real `scripts/dev.sh` backend+frontend pair, a real backfill, and a
  fresh `/data` load all showed the current (not stale) counts (`data-page-sanity.png`,
  `runs/goal-ops-hardening-iter-61/evidence-drill/`).
- Full DoD-relevant browser verification (TC-1/TC-2's "stays open, sees the update within one idle
  interval" behavior specifically) is left to the browser-qa-agent's pass, which can drive two tabs / wait
  the full 30 s window as part of its own dispatch.

## Known Issues

- See the dev handoff (`docs/handoffs/goal-ops-hardening-iter-61-dev.md`) for the full list, including the
  pre-existing, out-of-scope `last_run_date` bug on `GET /api/health` this pass diagnosed but did not fix.
- The 30 s ambient refresh means `/data`, once mounted, issues a `GET /api/data` + `GET /api/data/availability`
  pair roughly every 30 s for as long as the tab stays open — an intentional, bounded ambient cost (the
  SAME cadence the readiness badge already imposes on `GET /api/health` for every open tab in this app),
  not a new unbounded load pattern.
