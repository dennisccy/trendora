# Phase goal-mcp-loop-iter-27 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-27
**Time required:** ~15–30 minutes (longer than the usual 5 — this iteration's whole point is watching a
real heavy job survive TWICE in a row; there is no shortcut)
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`, backend running via
  `bash incredible_auto_dev/scripts/start-backend.sh` (prod mode — never `dev.sh`, which is intentionally
  left uncapped this iteration)
- No login required
- The standing large, full-history price database is already loaded (the normal dev-environment state) —
  this is what makes step 2 the real crashing shape, not a toy dataset
- Ability to stop/restart the backend process (needed for steps 8–9)
- **Nothing in the UI changed this iteration.** You are verifying one thing above all else: that the
  backend's heaviest job — rebuilding every score for the entire history — survives running TWICE in a row
  without crashing.

---

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** "Data Manager" heading loads; the "Dataset coverage" and "Storage footprint" panels show
     real numbers, not blank, not a red "Backend unavailable" error card

2. Click the "Rebuild snapshots for current universe" button, then click "Rebuild snapshots" in the
   confirmation dialog ("Confirm snapshot rebuild") that appears
   - **Expect:** The "Job progress" panel shows a "running" status badge with a spinning icon, and a
     "Snapshots backfilled" counter (e.g. "45/322 dates")

3. Watch that counter every 1–2 minutes without closing the tab, all the way through to completion —
   pay special attention once it passes ~240/322 (the deep-history stretch where the original crash
   happened)
   - **Expect:** The count climbs step by step every time you check (e.g. `12/322` → `88/322` →
     `210/322` → `322/322`) and the status badge turns to "ok" only once the counter reaches the total.
     The page stays responsive throughout — you can still scroll and click other things normally.
   - **Broken looks like:** the tab going unresponsive, a "connection refused"/"can't reach this page"
     error appearing mid-run, or the "Job progress" panel being replaced by a red "Backend unavailable"
     card. This is the crash this iteration is supposed to fix — flag it as a FAIL immediately and note
     the counter value at the moment it happened.

4. **Immediately after run 1 reaches "ok"** — in the SAME browser tab, with the backend NOT restarted —
   click "Rebuild snapshots for current universe" again and confirm a SECOND run
   - **Expect:** The job starts a second time cleanly (no "already running" block, since run 1 finished)
     and the counter resets and climbs through 322 dates again
   - **Broken looks like:** the exact same crash symptoms as step 3. **This second run is the one that
     actually failed before this iteration's fix** — a first run barely survived while memory from it
     wasn't returned to the system, so a second run back-to-back crashed the backend outright. If run 1
     passed but run 2 crashes, this is still a FAIL of the phase's core objective, not a partial pass.

5. Once run 2 also reaches "ok" (counter at `322/322 dates`), open a new tab and go to
   `http://localhost:3255/stocks`
   - **Expect:** The stock leaderboard loads normally with populated rows — confirms the whole backend
     process survived TWO consecutive heavy jobs, not just that one request slipped through

6. Fully stop the backend, then start it fresh and wait about 130 seconds (this host's normal cold-start
   time) before doing anything else
   - **Expect:** The old process exits and a new one starts listening again

7. Immediately open a **new** browser tab and go straight to `http://localhost:3255/data` — this must be
   the very first page you open against the freshly-restarted backend (do not check `/api/health` first)
   - **Expect:** The "Data Manager" page loads fully with real numbers in "Dataset coverage" and "Storage
     footprint", no error card
   - **Broken looks like:** a blank white tab, a browser "can't reach this page" error, or the backend
     crashing again right after this one request — this is the separate, previously-fixed iter-24 crash
     pattern; flag it distinctly if it reappears

8. Navigate to `http://localhost:3255/stocks/AAPL` and click the "Full history" toggle on the chart
   - **Expect:** The chart extends to many years of history with no crash, blank chart, or console error
     — confirms ordinary features still work unaffected

9. Navigate to `http://localhost:3255/` (Dashboard) and look at the "Market Regime" card
   - **Expect:** A colored regime label and a numeric score render normally, no error card, no blank card
     — this is the exact value the backend's changed calculation code produces; it must look the same as
     it always has

10. Stop the backend one more time, wait 5 seconds, then reload `http://localhost:3255/stocks`
    - **Expect:** Exactly ONE contained red card reading "Backend unavailable" appears (not a blank page),
      with the left sidebar navigation still visible and clickable around it. Restart the backend and
      confirm the leaderboard comes back within about a minute.

---

## What "Working Correctly" Looks Like

- The full-universe "Rebuild snapshots" job runs all the way to `322/322 dates` **twice in a row, in the
  same session, with no backend restart in between** — without ever making the backend unreachable, and
  the counter visibly climbs step by step both times, never jumping straight from a low number to "done"
- Restarting the backend and immediately opening `/data` never produces a blank page or connection error
- A genuinely-down backend shows exactly one contained "Backend unavailable" card, never a blank crash page
- Every other page you check (`/stocks`, a stock detail page, the Dashboard) looks and works exactly as it
  did before this iteration — nothing new to discover, nothing regressed

## Common Issues

- **The job's tab goes unresponsive, or "Job progress" is replaced by a red "Backend unavailable" card
  while the counter is still below the total — especially on the SECOND run**: this is the exact
  `MemoryError` crash this iteration was supposed to fix; report it as a FAIL with which run (1st or 2nd)
  and the `done/total` value you last saw before it happened
- **The progress counter jumps straight from a low number to the final total in one refresh**: a dishonest
  "done early" state — flag it even if the backend didn't crash
- **Blank page / connection error right after a cold restart, loading `/data` first**: this is the
  separate, already-fixed iter-24 crash pattern reappearing — flag it distinctly from the job-crash issue
  above
- **A score on the Dashboard or `/stocks` looks different from what you remember**: this iteration is
  supposed to be byte-identical (same numbers, just computed more cheaply) — note the exact page/value and
  flag it as a possible correctness regression
