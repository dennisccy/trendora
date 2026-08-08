# Phase goal-ops-hardening-iter-52 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-52
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode — standing in for ui-test-designer)

---

## Prerequisites

- Frontend running at `http://localhost:3255`; backend running at `http://localhost:8255`
- No login required — no authentication gate exists in this codebase
- At least one backfill/fetch job has completed previously (true on this build right now) — this guide
  reads existing state and does not require you to trigger a fresh job. Step 8 mentions starting one only
  as an *optional* extension if you have more time; the full reliability re-check (which needs a full job
  run) lives in `reports/phase-goal-ops-hardening-iter-52-ui-test-plan.md` (UT-03/UT-04), not here.

---

## Important context before you click anything

This iteration tried to stop the small pill in the header from occasionally flashing red during a heavy
data-loading job. **It did not succeed** — the developer's own measurement found this happens *more* often
now (22 times in one drill) than before the attempted fix (9 times). Nothing below will make that pill flash
on its own (no job is running), so you will not see the unresolved issue in this 5-minute guide — you're
instead confirming that everything else still works exactly as before, and that the pill/banner behave
honestly (not stuck, not lying) if you choose to do the optional step 8.

---

## Verification Steps

1. Open `http://localhost:3255/` in your browser
   - **Expect:** the Dashboard loads, no error page. In the top-right of the header, a small pill reads
     "Ready" with a solid green dot.

2. Look at the thin strip directly below the header
   - **Expect:** either nothing there, or a quiet green line reading "GO — today's board is current." It
     must NOT be a loud red banner right now (no job is running).

3. Click "Data Manager" in the left sidebar
   - **Expect:** navigates to `http://localhost:3255/data`; the page shows a "Job progress" card and a
     "Run History" table with existing runs.

4. In that card (or the Run History table below it), find the small grey line starting "Refreshed:"
   - **Expect:** a comma-separated list of category names (e.g. "coverage", "research hot keys"). This
     list's format and content are unchanged by this iteration — nothing here should look different from
     before.

5. Click "Research" in the left sidebar, then click the tile titled "Factor Lab"
   - **Expect:** navigates to `http://localhost:3255/research/factor-lab`; within a few seconds a sortable
     table with several real factor rows appears (not stuck on a "Still computing" message).

6. Click the "N" column header in that table
   - **Expect:** rows re-order immediately, no page reload, no error.

7. Click "Data Manager" in the left sidebar again, then in the top-right header, note the pill is still
   "Ready" (green)
   - **Expect:** unchanged from step 1 — confirms the badge renders identically across different pages.

8. **Optional, if you have 20–45+ minutes free:** in the "Start a fetch / backfill job" panel, leave the
   pre-filled "Start date"/"End date" as-is, leave "Job kind" as "Backfill snapshots", and click "Start" —
   then watch the header pill on and off for the job's duration
   - **Expect:** the job eventually reaches a normal completed status. The pill may occasionally flash red
     "Backend unavailable" during the run — if it does, this is the known, disclosed, not-yet-fixed
     condition described above, and it should always recover back to green on its own within a few
     seconds. It should never stay stuck red. If you try this, see "Common Issues" below for what would
     actually be a NEW problem versus the known one.

---

## What "Working Correctly" Looks Like

- Every page (Dashboard, Data Manager, Research → Factor Lab, Factor Combination) loads and behaves exactly
  as it did before this iteration — this was a backend-only scheduling change with zero frontend edits.
- The header pill and the strip beneath it show "Ready"/"GO" during normal Browse with no job running.
- If you run the optional step 8: the pill may flash red during the job (a known, still-unresolved issue —
  not something you need to report as new), but it always recovers on its own, and the job itself still
  finishes cleanly.

## Common Issues

- **Blank page / error screen:** confirm both servers are up —
  `curl http://localhost:8255/api/health` should return `200`, and `curl http://localhost:3255` should
  return `200`.
- **The header pill stays red "Backend unavailable" (or the banner stays "NO-GO") for more than about 30
  seconds with no recovery, and both servers are confirmed still running:** this WOULD be a genuinely new
  problem beyond this iteration's known finding — the badge is designed to always self-heal on its next
  successful poll. Note the exact time and what you were doing.
- **The "Refreshed:" line is missing an expected category after a job you ran completes:** first check
  whether the job's "Job progress" card shows an isolated failure for that specific piece — the product is
  designed to honestly drop only the broken category while still completing everything else, which is
  correct behavior, not a bug.
- **Want the precise reliability numbers (exact count of red flashes, exact job duration) instead of just
  eyeballing them?** That requires the longer, timed drill described in UT-03/UT-04 of
  `reports/phase-goal-ops-hardening-iter-52-ui-test-plan.md` — it does not fit inside this 5-minute guide.
