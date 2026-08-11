# Phase goal-ops-hardening-iter-61 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-61
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running normally — no fault-injection environment variable set (a plain
  `scripts/dev.sh` launch)
- No login required

---

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** The "Data Manager" page loads. No "Backend unavailable" message appears.

2. Look at the "Dataset coverage" panel near the top of the page
   - **Expect:** Stat tiles labeled "Snapshot dates" and "Backfill gaps" are both visible,
     each showing a plain number (not blank, not "—", not an error).

3. Look at the "Start a fetch / backfill job" panel below the coverage panel
   - **Expect:** Two date fields ("Start date", "End date"), a "Job kind" dropdown, and a
     "Start" button are all visible and clickable — this panel is unchanged by this
     iteration and should look exactly as before.

4. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The same "Snapshot dates" and "Backfill gaps" numbers from step 2 are
     still shown — the numbers persist across a reload, and no error appears.

5. Navigate to `http://localhost:3255/research/regime-lab?asof=2010-11-05`
   - **Expect:** The Regime Lab page loads with the "As of date" toggle selected, and the
     factor grid's sample-size chips show normal, clickable, underlined `n=...` values
     (e.g. `n=16452`) — NOT a grey "Unavailable" label. This confirms the page's normal
     (non-degraded) state still renders correctly.

6. Look at the top-right corner of the page (top bar)
   - **Expect:** The readiness badge shows "Ready" — this confirms the internal plumbing
     change this iteration made to the app-wide readiness check (`ReadinessProvider`) did
     not break the badge every page in the app relies on.

---

## What "Working Correctly" Looks Like

- The Data Manager page's coverage numbers never show as blank or an error, and survive a
  page refresh.
- The Regime Lab page's sample-size chips are normal clickable links under a healthy
  backend (the "Unavailable" degraded state only appears when the backend is deliberately
  relaunched under a special test-only environment variable — not something a normal user
  will ever see, and not part of this 5-minute check).
- The top bar's readiness badge reads "Ready" on every page, unchanged from before.

## What This Guide Does NOT Cover (and why)

- **The actual 30-second ambient auto-refresh cannot be demonstrated live in a 5-minute
  check.** This iteration's fix makes `/data` silently pick up coverage changes made by a
  job started anywhere else (another tab, a script, a teammate) within ~30 seconds, instead
  of staying stale indefinitely. Proving that end-to-end requires a real backfill/fetch job
  to actually finish and change the database — and in this system, even a single-day job
  takes roughly 17–23 minutes to complete (this project's data model recomputes long
  rolling-window aggregates on every ingest, regardless of range size). Rather than write a
  step that can't actually be completed in 5 minutes, this guide is limited to confirming
  the page still renders correctly and the surrounding surfaces (Regime Lab, readiness
  badge) weren't broken by the change. To see the fix work end-to-end, either watch this
  iteration's recorded walkthrough (`demo.sh ops-hardening --session-live`) or run test case
  UT-02 in `reports/phase-goal-ops-hardening-iter-61-ui-test-plan.md`, which budgets the
  full wait.

## Common Issues

- **"Backend unavailable" card on `/data`**: the backend isn't running or isn't reachable —
  confirm with `curl http://localhost:8255/api/health` (should return 200 with a `status`
  field).
- **Regime Lab shows "Unavailable" chips even without setting the fault-injection
  variable**: the backend may have been left running from a prior fault-injection test —
  restart it with a plain `scripts/dev.sh` (no `TRENDORA_FAULT_INJECT_MEMORY_ERROR` set).
- **Readiness badge stuck on something other than "Ready"**: check the backend logs for
  startup/warm-up errors — this is unrelated to this iteration's change, which only added a
  new field to the existing readiness payload.
