# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12
**Date:** 2026-06-13
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Resume a data import that failed during the backfill stage (after price-history download was already complete) by clicking the "Resume" button in the Unfinished Imports section of the Data Manager page — the resume skips re-downloading any data and picks up directly at the snapshot-building stage.
- Re-run a data import job over a date range that is already fully downloaded and have it skip straight to the snapshot-building stage in seconds, rather than spending ~45 minutes re-downloading data already on disk.
- See every job appear in Run History the moment it starts (as a "running" entry with its kind, date range, and source), rather than only seeing it after the job finishes.
- Watch a live job card show a "now working on…" current-activity line (e.g. "scanning 2021-03-11 (12/22)") that updates as the job progresses through each symbol and date.
- See an "updated Ns ago" heartbeat text in the live job card that turns amber and says "possibly stalled" if the job stops advancing — giving a clear visual signal between a slow-but-running job and a hung one.
- See a per-date failure breakdown for any job that ended in "partial" status — showing exactly which dates failed (with their error) and confirming the remaining dates completed.

---

## What Changed in the Visible UI

- The live job card on the Data Manager page (`/data`) now shows a current-activity line below the progress bar, updated each poll tick by the server.
- The live job card now shows an "updated Ns ago" heartbeat line that turns amber when the job stops advancing for longer than the configured stale threshold (default 20 seconds).
- The symbols counter in the live job card is now guaranteed to never show an impossible value like "318/159" — the counter counts each symbol once and the display is also defensively clamped at its total.
- The "× faster" speedup figure in the Stage Timings section is now supplied directly by the server (no longer computed in the browser). The displayed value is unchanged in appearance; the source of the calculation moved server-side.
- The Unfinished Imports section now shows a `failed_backfill` checkpoint with an amber status badge labeled "failed at backfill", with copy reading "Resumable from the backfill stage (the fetch is skipped — zero provider calls)." and a Resume button.
- The Run History table now shows rows with three new statuses: `running` (with an inline spinner, appearing as soon as a job starts), `resumable`, and `interrupted` — in addition to the existing terminal statuses `ok`, `partial`, and `failed`.
- A `partial` job in Run History now shows a per-date failure detail block listing which specific dates failed and their errors, with a note that the remaining dates still completed.
- The poll interval of the live job card is now driven by the backend configuration value (default 1 second) rather than a hardcoded literal in the frontend.

---

## What Old Behavior Changed

- Run History: previously a job appeared in Run History only when it finished. Now it appears immediately with `running` status when started, and updates in place to its final state (`ok`, `partial`, `failed`, `resumable`, or `interrupted`).
- A multi-date parallel backfill that encounters a single failing date now ends in `partial` status with that date's error recorded — previously a single date failure could abort the entire backfill stage.
- Re-running an import job over a date range already fully downloaded now completes near-instantly (skipping the download stage entirely) — previously it would re-download all the data, taking ~45 minutes and adding 0 new bars.
- If the backend process is killed mid-job, the next startup marks the abandoned Run History entry as `interrupted` instead of leaving it permanently stuck as `running`.

---

## Not Visible Yet

- None. All backend state-machine changes (stage-aware checkpoints, lifecycle records, per-date failure isolation, covered-range planner, boot sweep) are fully surfaced in the `/data` Data Manager page through the live job card, Unfinished Imports, and Run History panels.
