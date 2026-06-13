# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## What Was Built

All UI work lands on the existing `/data` (Data Manager) page — the live job card, Run history, and
Unfinished-imports sections. No new page, route, or nav change. Every new field is a re-format of a value
the backend computed (the frontend derives nothing new).

- **Live job card (J-66):**
  - **Current-activity line** (`JobLiveActivity`) — names what is being worked on right now ("scanning
    2021-03-11 (12/22)" during backfill, the symbol being fetched during fetch) — server-supplied,
    rendered verbatim.
  - **"Updated Ns ago" heartbeat** — from the job's `last_progress_at`, ticking via a 1s `useNow` clock
    while the job is live; turns **amber + "possibly stalled"** past the config `heartbeat_stale_seconds`,
    so a slow-but-alive job is visually distinct from a stalled one.
  - **Per-symbol-advancing symbols counter** capped at its total (the `318/159` defect is gone — the
    backend counts distinct symbols; the display is also defensively clamped).
  - **Backend-supplied speedup figure** — `StageTimings` now renders `stages.backfill.speedup_factor`
    (computed server-side). The client-side `speedupFactor()` division was **deleted** (clears the iter-8
    coherence-WARN residual).
  - **Live per-stage timings** already render during the run (J-53 carry, unchanged).
- **Unfinished imports (J-59):** a `failed_backfill` checkpoint renders with the server-built plain-language
  state **"Failed at backfill — … Resumable from the backfill stage (the fetch is skipped — zero provider
  calls)."** and the **Resume** action (the existing `ResumeControl`, no new control). Its status badge is
  amber (distinct from a hard red `failed`).
- **Run history (J-60):** the table now shows **`running`** (with an inline spinner, from job start),
  **`resumable`**, and **`interrupted`** rows alongside the terminal `ok`/`partial`/`failed`. A friendly
  `statusLabel` renders `failed_backfill` as "failed at backfill".
- **Partial job detail (J-67):** a `partial` job surfaces a **per-date failure block** — which dates failed
  (honest error), with the note that the rest completed and no snapshot was fabricated for a failed date.
- **Config-driven polling (J-66):** the live-job poll cadence + heartbeat-stale threshold now come from the
  backend `job_progress` config (served on `GET /api/data`) — no hardcoded `1000`ms literal.

## Files Changed

- `apps/frontend/lib/api.ts` — new/extended types (see dev handoff): `JobStageTiming.speedup_factor`,
  `JobDateFailure`, `DataJob` progress fields, `UnfinishedImport.completed_stages`, `DataRun` statuses,
  `JobProgressConfig`, `DataOverviewResponse.job_progress`.
- `apps/frontend/app/data/page.tsx` — `heartbeatAgo`, `useNow`, `JobLiveActivity`; config-driven
  `pollIntervalMs`/`heartbeatStaleSeconds`; `JobProgressPanel` heartbeat/activity + per-date failure block;
  symbols-counter clamp; `statusVariant`/`statusLabel` for `failed_backfill`/`interrupted`/`running`;
  Run-history `running` spinner; `StageTimings` reads the backend `speedup_factor` (client division deleted).

## Design Notes

- Reused the existing `/data` job-card / Unfinished-imports / Run-history components + the shared
  `ProgressBar`. New fields slot into the existing dense dark analytical layout; monospace/tabular numbers;
  status colors consistent with the existing badges (added an amber `failed_backfill` and a neutral
  `interrupted` treatment, both distinct from red `failed`).
- States handled: live (running, ticking heartbeat) / paused-`resumable` / `failed_backfill`
  (resumable-at-backfill) / `interrupted` / `partial` (per-date failure detail) / terminal `ok`/`failed`.
  A counter never renders above its total; an absent speedup renders honest-NA (no fabricated ratio).
- The new Resume affordance reuses the existing `ResumeControl` (a sibling control in a non-clickable row)
  — no nested interactive element (iter-5 hazard respected).

## Tests Run

- `npx tsc --noEmit` — clean. No frontend unit-test harness is configured; the UI is verified by the
  browser-QA pipeline against the committed seed / QA fixture.
- A production `next build` was intentionally NOT run (it would clobber the dev server's `.next` cache —
  project memory "Browser QA dead-shell / .next cache").

## Known Issues

- None beyond the backend handoff's. The UI re-formats backend values only; no client-side derived figure
  was introduced (the speedup derivation moved server-side).
