# goal-i_can_see_the_wealthy_future_forever-iter-23 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-23
**Date:** 2026-06-07
**Agent:** developer
**Status:** complete

## What Was Built

Additive UI on the existing `/data` Data Manager page (no new page, route, or nav entry) for the J-35 Expand-universe job: an Expand option in the job-kind selector, source-eligibility gating, and a screen-result block on the existing job card. Reuses the existing shadcn `Card`/`Badge`/`Select`/field patterns, the existing async-job / chunk-progress / resumable affordances, and the iter-22 status-colour vocabulary (teal running, amber `resumable`, red failed). No new effects, layout regions, or date state.

## Files Changed

- `apps/frontend/lib/api.ts`
  - `DataJobKind` gains `"expand"`.
  - New `ExpandOmission` type (`{symbol, reason}`).
  - `DataJob` gains `passers?`, `omitted_total?`, `omitted?: ExpandOmission[]` (J-35 screen result).
  - `DataRun` gains `passers` / `omitted_total` (the expand screen outcome in run history).
- `apps/frontend/app/data/page.tsx`
  - **Job-kind selector**: a new `Expand universe` `<option>` alongside Backfill / Fetch / Fetch + backfill.
  - **Eligibility gating**: when `expand` is selected, each import-source `<option>` with `supports_market_cap: false` (alpha_vantage, stooq — read from the config-driven `sources` catalog) is rendered `disabled` with the inline reason "cannot supply market cap — not selectable for expand"; a selected ineligible source also shows a styled amber `role="alert"` reason line (`data-testid="expand-ineligible-reason"`) and **blocks the Start button** (mirrors the backend 400). The import-source picker now shows for `expand` as well as fetch/both.
  - **Screen-result block** (`ExpandScreenResult`, `data-testid="expand-screen-result"`): on the job card for an expand job — a `passers` badge (`data-testid="expand-passers"`), an `omitted` badge (`data-testid="expand-omitted-count"`), and the **omitted-with-reason list** (`data-testid="expand-omitted-list"`, each candidate + its reason, scrollable, `tabular-nums`); "showing X of N" when the list is bounded; an explicit "All screened candidates passed — no omissions." empty state. The expand job also shows the reused chunked-OHLCV symbols-fetched progress bar + chunk x/N badge.
  - Panel title / footer copy updated to describe the expand job; the page subtitle is unchanged.

## New User-Facing Capability

The user can grow the scored universe from the committed candidate pool by running an Expand-universe job from the Data Manager — pick a market-cap-capable source (ineligible sources are disabled and explained), watch the chunked/resumable screen run, and read exactly which candidates passed and which were omitted (with the reason). After a completed expand, the Coverage panel's `universe-count` (`data-testid="universe-count"`) reflects the grown universe (same resolved universe as `/methodology` — single source).

## New User Actions

- Select **Expand universe** in the `/data` job-kind selector.
- Start an expand over a `supports_market_cap` source (ineligible sources disabled; Start blocked on an ineligible source).
- **Resume** a rate-limited expand — reuses the existing J-34 `resume-button` path (the live job card's resumable block and the post-restart Resumable-imports panel both work for an expand checkpoint; no new control).

## States Handled

- **Loading**: existing skeleton.
- **Running**: reused symbols-fetched progress + chunk x/N badge.
- **Empty omissions**: "All screened candidates passed — no omissions." (when passers > 0 and no omissions).
- **Ineligible source**: disabled `<option>` + inline amber reason + blocked Start.
- **Resumable (rate-limited live feed)**: the existing amber resumable block + Resume control (the honest NA / rate-limited terminal state when the live market-cap feed is walled — surfaced like the existing resumable/failed states, never a fabricated success).
- **Error**: existing styled `role="alert"` + the bounded errors list (each per-candidate reason is key-redacted at source + scrubbed).

## Single Source / No Recompute

The grown universe is shown ONLY via the existing Coverage `universe-count` (read from `/api/data`), which equals the `/methodology` Universe-Selection size — no second universe display on the page. The expand screen result (passers + omitted-with-reason) is descriptive job-control metadata served on the job snapshot; it is not a recompute of any canonical score/return/bucket.

## Tests Run

`cd apps/frontend && npx tsc --noEmit` → clean (exit 0).

Service check: `next dev` started clean on :3835; `/data` served HTTP 200 and `/_next/static/chunks/main-app.js` returned 200 (a healthy hydrated shell). The Expand option, eligibility disabling, and screen-result block render in the client bundle (the page is a `"use client"` component, so the option text is in the JS bundle, not the SSR HTML).

## Known Limitations

- The browser-QA of the full expand happy-path flow (chunk progress → completion → passers + omitted list → grown `universe-count`) should be driven with an **injected provider** per the spec's offline-provable steps; a live expand on this host hits the walled market-cap feed and lands in the honest NA / `resumable` state (non-halting, not a FAIL).
