# Phase goal-ops-hardening-iter-7 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-7
**Time required:** ~5 minutes (plus job-completion wait, typically under a minute)
**Written by:** ui-test-designer

---

## Prerequisites

- Backend running in **prod mode** at `http://localhost:8255` (start with `scripts/start-backend.sh`)
- Frontend running in **prod mode** at `http://localhost:3255` (start with `scripts/start-frontend.sh`) —
  do NOT use `dev.sh` for this check; dev mode's extra overhead makes the "fast first view" claim
  unverifiable
- No login required
- No special seed data required — the existing dataset already has certified evidence claims

---

## What this iteration changed

No page, button, or form is new. One background computation ("expected drawdown" panels on the Evidence
page) now runs automatically the moment a data-update job finishes, instead of lazily the first time
someone opens the Evidence page. You're checking that (a) the Evidence page is fast on its very first
view after a job, and (b) the Data Manager's job-summary text picks up one new phrase.

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** Data Manager page loads, no error banner; a panel titled "Start a fetch / backfill job"
     is visible

2. Type `2015-06-18` into the "Start date" field, then type `2015-06-18` into the "End date" field. Leave
   "Job kind" set to "Backfill snapshots". Click the "Start" button.
   - **Expect:** The Job progress panel appears/updates and shows a spinning icon with the text "Job
     running…"
   - **If broken:** the "Start" button stays disabled and never runs — check that both date fields show a
     valid date (no red/invalid state) before clicking

3. Wait for the job to finish (the spinner stops; the status badge changes to a completed state such as
   "ok"). This usually takes a few seconds to under a minute.
   - **Expect:** Below the job's snapshot count, a small gray line appears reading "Refreshed:" followed
     by a comma-separated list that now includes the phrase **"drawdown expectations"**

4. Immediately open a new browser tab and navigate to `http://localhost:3255/evidence`
   - **Expect:** The page heading "Evidence" appears, followed within about 3 seconds by one or more
     claim cards — no extended spinner, no blank white space where a panel should be
   - **If broken:** the page hangs on a loading skeleton for many seconds (10s+) — this would mean the
     ingest-time warm did not actually run before this view

5. On any claim card that has a section titled "Historical drawdown & dry-spell expectations", confirm
   its table (columns: Phase, Max-DD depth, Underwater, Time to recover, Longest losing streak) shows real
   numbers, not blank cells
   - **Expect:** Every visible row in that table has populated values (or a clearly formatted "insufficient
     data" label — never a blank cell or a raw error)

6. Refresh the Evidence page (press F5)
   - **Expect:** The same claim cards and the same expectations-table numbers reappear — values did not
     change or disappear after the refresh (confirms nothing was corrupted by the timing change)

7. Go back to `http://localhost:3255/data` and scroll down to the "Run history" table. Find the row whose
   "Range" column shows "2015-06-18 → 2015-06-18" (the job you started in step 2).
   - **Expect:** That row's Snapshots column has a small gray note beneath the number reading "Refreshed:"
     and that note also includes "drawdown expectations"

---

## What "Working Correctly" Looks Like

- The Data Manager's "Refreshed:" text (in the live job panel, and later in the Run History row) includes
  "drawdown expectations" after the job you started completes
- The Evidence page's very first view after that job — opened in a brand-new tab — renders its claim cards
  and expectations tables within a few seconds, with no unusually long spinner
- Refreshing the Evidence page shows identical figures — nothing changed, only the wait got shorter

## Common Issues

- **Evidence page hangs for 10+ seconds on first view after a job**: the ingest-time warm step likely did
  not run (or errored silently) — check backend logs for messages around `_refresh_ingest_aggregates`
  during the job's finalize phase
- **"drawdown expectations" never appears in the Refreshed line**: this is honestly expected if the
  evidence ledger has zero claims, or all claims are unresolvable for that cohort — check
  `http://localhost:3255/evidence` directly; if it shows real certified claims with expectations panels,
  but the Refreshed line still omits the phrase, that is a regression worth flagging
- **Blank page / error screen on either page**: confirm the backend is reachable —
  `curl http://localhost:8255/api/health`
