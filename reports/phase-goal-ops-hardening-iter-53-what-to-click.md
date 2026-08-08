# Phase goal-ops-hardening-iter-53 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-53
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode — standing in for ui-test-designer)

---

## Prerequisites

- Frontend running at `http://localhost:3255`; backend running at `http://localhost:8255`
- No login required — no authentication gate exists in this codebase
- At least one backfill/fetch job has completed previously (true on this build right now) — this guide
  reads existing state and does not require you to trigger a fresh job or restart the backend. The deeper
  reliability re-check and the backend-restart-based evidence capture (which need a long job run and
  terminal access) live in `reports/phase-goal-ops-hardening-iter-53-ui-test-plan.md` (UT-03 through
  UT-07), not here.

---

## Important context before you click anything

This iteration made two background steps that run during a data-loading job faster and less likely to
briefly freeze the small "backend" pill in the header. Unlike a prior attempt in this session, this one
worked for both of its two specific targets — the developer's own measurement found zero occurrences of
the freeze caused by either targeted step, down from one each. It did **not** make every possible freeze
disappear: the same measurement still found one freeze, now caused by a third, different step nobody has
fixed yet. Nothing below will trigger any of this (no job is running), so you will not see either the fix
or the remaining gap in this 5-minute guide — you're instead confirming that every page still loads and
shows correct numbers exactly as before, since this iteration changed how much old price data gets loaded
behind the scenes, not what gets shown.

---

## Verification Steps

1. Open `http://localhost:3255/` in your browser
   - **Expect:** the Dashboard loads, no error page. In the top-right of the header, a small pill reads
     "Ready" with a solid green dot.

2. Look at the "Market Phase & Severity" card on the Dashboard
   - **Expect:** it shows a real phase label (e.g. "Risk-on", "Choppy") and a numeric severity score out
     of 100 — not a blank dash. This card is fed by one of the two steps this iteration changed; it should
     look exactly as it did before.

3. Look at the thin strip directly below the header
   - **Expect:** either nothing there, or a quiet green line reading "GO — today's board is current." It
     must NOT be a loud red banner right now (no job is running).

4. Click "Data Manager" in the left sidebar
   - **Expect:** navigates to `http://localhost:3255/data`; the "Dataset coverage" panel and the
     "Universe resolution as of …" panel below it both show real numbers (not "—" or an error) for
     "Universe," "Admitted," and the excluded-reason counts.

5. In the "Job progress" card (or the "Run History" table below it), find the small grey line starting
   "Refreshed:"
   - **Expect:** a comma-separated list of category names (e.g. "coverage", "membership timeline",
     "market phase"). This list's format and content are unchanged by this iteration — nothing here should
     look different from before.

6. Click "Backtest" in the left sidebar
   - **Expect:** navigates to `http://localhost:3255/backtest`; within a few seconds a forward-test
     scorecard with real rows appears, and scrolling down shows an evidence section reading "Snapshots
     contributing" with a real count.

7. Click "Data Manager" in the left sidebar again, then in the top-right header, note the pill is still
   "Ready" (green)
   - **Expect:** unchanged from step 1 — confirms the badge renders identically across different pages.

8. **Optional, if you have 30–45+ minutes free:** in the "Start a fetch / backfill job" panel, leave the
   pre-filled "Start date"/"End date" as-is, leave "Job kind" as "Backfill snapshots", and click "Start" —
   then watch the header pill on and off for the job's duration
   - **Expect:** the job eventually reaches a normal completed status. The pill may occasionally flash red
     "Backend unavailable" during the run — the developer's own measurement traced its one remaining
     occurrence to a step this iteration did not touch, so this is a known, disclosed condition, not
     something you need to report as new. It should always recover back to green within a few seconds and
     never stay stuck red. For the rigorous version of this check — including the backend-restart steps
     needed to capture this iteration's other evidence requirement — see UT-03 through UT-07 in
     `reports/phase-goal-ops-hardening-iter-53-ui-test-plan.md`.

---

## What "Working Correctly" Looks Like

- Every page (Dashboard, Data Manager, Backtest) loads and shows the same numbers it did before this
  iteration — this was a backend-only change to how much old price history gets fetched behind the scenes,
  with zero frontend edits.
- The header pill and the strip beneath it show "Ready"/"GO" during normal browsing with no job running.
- The Dashboard's "Market Phase & Severity" card and the Data Manager's coverage/universe panels show real
  numbers, not blanks or errors.
- If you run the optional step 8: the job finishes cleanly, and any red pill flash during it always
  recovers on its own.

## Common Issues

- **Blank page / error screen:** confirm both servers are up —
  `curl http://localhost:8255/api/health` should return `200`, and `curl http://localhost:3255` should
  return `200`.
- **The "Market Phase & Severity" card or the Data Manager's "Universe resolution" panel shows "—"/NA/an
  error where you'd expect a number:** this WOULD be worth flagging — this iteration's fix is specifically
  about the code behind these two panels, and their numbers must be unchanged, not blank.
- **The header pill stays red "Backend unavailable" (or the banner stays "NO-GO") for more than about 30
  seconds with no recovery, and both servers are confirmed still running:** this WOULD be a genuinely new
  problem — the badge is designed to always self-heal on its next successful poll. Note the exact time and
  what you were doing.
- **The "Refreshed:" line is missing an expected category after a job you ran completes:** first check
  whether the "Job progress" card shows an isolated failure for that specific piece — the product is
  designed to honestly drop only the broken category while still completing everything else, which is
  correct behavior, not a bug.
- **Want the precise reliability numbers (exact non-answer count, exact job duration) instead of just
  eyeballing them?** That requires the longer, timed drill described in UT-03/UT-04 of
  `reports/phase-goal-ops-hardening-iter-53-ui-test-plan.md` — it does not fit inside this 5-minute guide.
