# Phase goal-market-compass-iter-27 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-27
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running at `http://localhost:8255` (check with `curl http://localhost:8255/api/health` —
  expect `"preflight": {"verdict": "GO", ...}`)
- No login required
- No seed data setup needed — the two as-of dates below already exist in the live database

---

## Verification Steps

1. Open `http://localhost:3255/?asof=2025-04-15` in your browser
   - **Expect:** The Today page loads; a card titled "Manifest" appears near the bottom of the page,
     showing badges "retrospective" and "version 2"

2. Inside the Manifest card, find the badge row just below the small hash chips (labeled "Engine
   identity", "Candidate rule", etc.)
   - **Expect:** A green badge reading exactly "Basis: available", with no gray text next to it

3. Open `http://localhost:3255/?asof=2026-08-12` in your browser
   - **Expect:** The Today page loads; the Manifest card shows badges "at ingest" and "version 6"

4. Find the same badge row inside the Manifest card
   - **Expect:** An amber/yellow badge reading exactly "Basis: rebuilt", with the gray text "the source
     scanner run was recreated after this manifest was frozen" beside it

5. On this same page, click the outlined amber "Regenerate manifest" button (with a circular-arrow icon)
   near the bottom of the Manifest card
   - **Expect:** A modal titled "Confirm manifest regenerate" pops up over the page

6. Click the "Cancel" button in the modal's bottom-right corner (do **not** click the amber "Regenerate
   manifest" button inside the modal — that would create a real new manifest version in the live
   database)
   - **Expect:** The modal closes; the Manifest card looks exactly as it did before step 5

7. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The Manifest card still shows "version 6" and the amber "Basis: rebuilt" badge —
     nothing changed from the refresh

---

## What "Working Correctly" Looks Like

- The 2025-04-15 page shows a **green** "Basis: available" badge with no extra text
- The 2026-08-12 page shows an **amber** "Basis: rebuilt" badge with its explanatory gray text
- Clicking "Regenerate manifest" opens a confirm modal, and "Cancel" closes it without changing anything

## About the Red "Basis: unavailable" Badge

This iteration's actual fix makes a fourth badge state — a **red** "Basis: unavailable" badge — reachable
for the first time on a real request. It is not possible to see it live in this environment right now: no
date in the current database is in the specific state that triggers it (a frozen manifest whose underlying
scan data was later deleted), and deliberately deleting live data to manufacture that state is outside
this iteration's authorization. This state is proven only by an automated backend test, not by clicking
through the app — see the UI test plan (UT-04) for the exact command
(`cd apps/backend && .venv/bin/python -m pytest tests/test_api_compass.py -v -k unavailable`).

## If Something Looks Wrong

- **Blank page / error screen**: check that the backend is running
  (`curl http://localhost:8255/api/health`) and the frontend is running
  (`curl -I http://localhost:3255`)
- **Manifest card shows "Manifest strip is unavailable — backend not reachable..."**: the backend is down
  or unreachable — restart it with `bash scripts/start-backend.sh`
- **Badge shows a different status than expected** (e.g. "Basis: available" instead of "Basis: rebuilt" on
  step 4, or vice versa): the underlying data for that date may have changed since this guide was written
  — re-run `curl "http://localhost:8255/api/compass?as_of=<date>"` and check the `basis.status` field
  directly before assuming a regression
