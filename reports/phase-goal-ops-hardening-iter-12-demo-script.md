# Demo Script — goal-ops-hardening-iter-12

**Mode:** record
**Date:** 2026-07-23
**Frontend URL:** http://localhost:3255
**Iteration:** 12

## Highlights

### Step 01 — Today's market read, ready instantly

- **Narration:** The Dashboard opens straight to today's Market Phase & Severity read. There's no waiting for a live recalculation — it's served from data that was already worked out ahead of time.
- **Action:** Navigate to /
- **Point out:** The phase badge and the 'as of' date fill in almost immediately, and the top-bar status badge already reads Ready.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-12/step-01.png

### Step 02 — Open the Data Manager

- **Narration:** One click from the dashboard reaches the Data Manager, where the team can see exactly what data is covered and where the gaps are.
- **Action:** Click the "Data Manager" link
- **Point out:** The provenance panel lists every index and benchmark with its real data vendor and first-bar date — never a guess or a placeholder.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-12/step-02.png

### Step 03 — Friendly, immediate validation

- **Narration:** Typing an impossible date is caught right away, with a clear message and the submit button disabled — no confusing errors after the fact.
- **Action:** Type "2026-13-40" into the "Start date" field
- **Point out:** The red inline message appears the instant the date fails to parse.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-12/step-03.png

### Step 04 — Backfill history is real, and it sticks

- **Narration:** The Run History table remembers every backfill exactly as it finished — even a request spanning more than a year — with an honest breakdown of what was already covered.
- **Action:** Navigate to /data
- **Point out:** A 2025-06-01 to 2026-07-17 request (412 days) is listed with its full breakdown: already-snapshotted and non-trading days accounted for, no artificial cap on the range, and nothing lost on a page reload.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-12/step-04.png

### Step 05 — Every trading day's scan, ready the instant the page loads

- **Narration:** The Scanner Runs list shows every day's market regime and candidate counts the moment the page finishes loading — pulled from work that was already done, never calculated on the spot.
- **Action:** Navigate to /scanner-runs
- **Point out:** Rows are fully populated the instant the loading skeleton clears — no spinners, no dashes standing in for real numbers.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-12/step-05.png

### Step 06 — Drill into one day's leaderboard

- **Narration:** Clicking any date opens that day's exact, unchanging scanner leaderboard — the same numbers stored from that day, never recomputed after the fact.
- **Action:** Click the "2026-07-17" link
- **Point out:** The top-ranked tickers and candidate counts match the underlying stored data exactly.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-12/step-06.png
