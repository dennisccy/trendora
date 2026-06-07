# goal-i_can_see_the_wealthy_future_forever-iter-22 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-22
**Date:** 2026-06-05
**Agent:** developer
**Status:** complete

## What Was Built (UI)

All changes are additive, on the **existing `/data` (Data Manager)** page — **no new page, route, or
nav entry**.

- **Chunk x/N indicator** on the job card. When a fetch job is chunked (`chunk_total > 0`), a
  `chunk {chunk_index}/{chunk_total}` badge renders beside the status badge (monospace `tabular-nums`).
- **"rate-limited — resumable" state** on the job card. When `job.status === "resumable"` the status
  badge reads *rate-limited — resumable* in **amber `--warn`** (explicitly distinct from red `--neg`
  `failed`), and an amber callout shows the pause point (chunk x/N), **symbols done vs remaining**, and a
  **Resume** button.
- **Resume control** (`ResumeControl`). A Resume button (amber, `RotateCcw` icon) that re-POSTs to the
  resume endpoint. For a needs-key source with no env key, it reveals a `type="password"` **session-only**
  key field (held in component memory only, **cleared the instant Resume is submitted**, never written to
  localStorage / URL / cookie). On success the resumed job is pulled back into the job card and polling
  resumes; on a 4xx the backend's honest `detail` is shown inline.
- **Resumable imports panel** (`ResumableImportsPanel`). A new card listing `data.resumable_imports` from
  `GET /api/data` — the paused imports that **survive a backend restart** (the in-memory job is gone but
  the durable checkpoint persists). Each row shows the source, date range, chunk x/N, symbols
  done/remaining/failed, bars-so-far, and its own Resume button. The panel is hidden when the list is empty.

## Files Changed

- `apps/frontend/lib/api.ts` — added `chunk_index?`/`chunk_total?` to `DataJob` (+ `resumable` noted in the
  status union); added the `ResumableImport` type + `resumable_imports` to `DataOverviewResponse`; added
  `resumeDataJob(importId, opts?: { api_key? })` (POST, session-only key sent only when non-blank).
- `apps/frontend/app/data/page.tsx` — `statusVariant` maps `resumable → warn`; `JobProgressPanel` now
  takes `sources` + `onResumed` and renders the chunk badge + the amber resumable callout + `ResumeControl`;
  added `ResumeControl` and `ResumableImportsPanel`; the page wires an `onResumed` callback that re-pulls
  the resumed job and lets the existing poll effect take over.

## Data-testids for browser QA

- `chunk-progress` — the chunk x/N badge on the live job card.
- `resumable-state` — the amber "rate-limited — resumable" callout on the job card.
- `resumable-imports` — the post-restart resumable-imports panel card.
- `resume-button` — every Resume button (job card + each resumable-imports row).
- (existing) `source-availability`, `universe-count`, `Import source` / `Job kind` selects, the
  `type="date"` start/end inputs (still the only date inputs — J-18: the chunk/Resume controls add **no**
  date state).

## Design-system conformance

- Amber `--warn` (#fbbf24) for the resumable/paused state; red `--neg` reserved for `failed`; teal
  `--accent` for running. Monospace `tabular-nums` (`.num`) for all chunk/symbol counts. shadcn
  `Card`/`Badge` + the existing field/button styles reused; hover/focus/active/disabled states on the
  Resume button.

## Tests Run

- `npx tsc --noEmit` → clean (exit 0).
- Isolated production build `NEXT_DIST_DIR=.next-verify npx next build` → clean (exit 0); `/data` route
  compiled (6.49 kB). Built to a separate dist dir so the running `next dev` `.next` was **not** clobbered
  (MEMORY `browser-qa-dead-shell-next-cache`); the verify dir was removed afterward.

## Known Issues

- The live-fetch *completion* is externally data-walled (Yahoo 429 / Stooq key-gated for this host), so a
  fully-completed live chunked import is not browser-reachable; the chunk indicator, amber resumable state,
  Resume affordance, and post-restart resumable-imports list are all exercisable (a real Yahoo 429 drives
  the retry → resumable → Resume path). This is the spec's expected non-halting outcome.
