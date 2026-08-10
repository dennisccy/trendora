# goal-ops-hardening-iter-57 Frontend Handoff

**Phase:** goal-ops-hardening-iter-57
**Date:** 2026-08-10
**Agent:** developer
**Status:** complete

## What Was Built

- **Availability heatmap "updating" banner (`apps/frontend/components/availability-heatmap.tsx`):** when
  `GET /api/data/availability`'s response carries `stale: true` (the backend served the most recent
  persisted reading instead of the not-yet-computed empty sentinel, because an ingest is mid-flight and
  its finalize-tail warm has not yet re-run), the component now renders a calm "Data as of
  `<served_dataset_version>` — updating" notice above the (unchanged, real) heatmap grid — `data-testid=
  "availability-stale-notice"`. Placed BEFORE the loading/error/empty/ok conditional blocks so it renders
  alongside the real cells, never gating them. Mirrors the EXISTING Coverage panel's
  `coverage-stale-notice` treatment byte-for-byte in styling (`border-b border-border bg-surface-2 px-4
  py-2 text-xs text-text-muted`) — same calm/factual tone this page's other status text already uses, no
  alarm styling (matches the plan's Visual Requirements). `stale: false` with non-empty cells renders
  unchanged from before this iteration; `stale: false` with empty cells still shows today's "No
  availability yet — Fetch real EOD prices" empty state (the only case that message remains honest for).
- **`apps/frontend/lib/api.ts`:** `AvailabilityResponse` gains two additive fields — `stale: boolean`,
  `served_dataset_version: string | null` — matching the backend's new response shape exactly.
  `apps/frontend/app/data/page.tsx` needed NO change: it already passes the raw fetched
  `AvailabilityResponse` straight into `AvailabilityState.data` with no field narrowing, so the two new
  fields flow through automatically to the component.

## Files Changed

- `apps/frontend/lib/api.ts` — `AvailabilityResponse` interface extended.
- `apps/frontend/components/availability-heatmap.tsx` — new stale-banner render path + updated top-level
  doc comment.

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit`
Result: clean, zero type errors.

This project has no configured frontend test runner (`package.json` has no `test` script; only `dev`,
`build`, `start`, `lint`) — matches the established convention across this session's prior
frontend-touching iterations (e.g. iter-47's own handoff uses the same `tsc --noEmit` + live-verification
pattern, with `.test.ts` files reserved for pure-logic modules like `lib/evidence.test.ts`, which this
change has no equivalent of — it is a presentation-only conditional render, not new logic to unit-test).

## Live verification

Started via `scripts/start-frontend.sh` (prod build, port 3257) against a real backend (port 8257,
host-guard caps applied). The `/data` page's availability heatmap was exercised indirectly through this
iteration's own `journey-scripts/J-06.json` golden replay (`demo_runner.py --mode verify`), which asserts
an `availability-cell` renders from the real response — 2 clean PASSes. The `stale: true` banner path
itself was NOT visually screenshotted this dispatch (it requires an ingest genuinely mid-flight, which
this dispatch deliberately did not trigger against the shared dev DB to avoid mutating its state for other
concurrent work) — its correctness is proven at the backend/API-contract level (unit tests + a live
`GET /api/data/availability` check showing `stale: false, served_dataset_version: "<the current stamp>"`
on the idle dev DB) and by direct source review of the new JSX against the established
`coverage-stale-notice` precedent it mirrors. Recommend the browser-qa-agent stage trigger a real backfill
job and screenshot the banner mid-flight (TC-4) as part of its own verification pass.

## Known Issues

- The `stale: true` banner's live rendering was not visually confirmed this dispatch (see above) — the
  underlying data contract and component logic are proven, but an operator-visible screenshot of the
  banner itself mid-ingest is deferred to the QA stage's own live job drill.
- No frontend-side changes were needed to `apps/frontend/app/data/page.tsx` — flagged in case a reviewer
  expects a diff there per the plan's conditional note; confirmed by direct read that the page does not
  narrow `AvailabilityResponse` before handing it to `AvailabilityHeatmap`.
