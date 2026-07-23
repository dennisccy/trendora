# Demo Script — goal-ops-hardening-iter-13

**Mode:** record
**Date:** 2026-07-23
**Frontend URL:** http://localhost:3255
**Iteration:** 13

## Highlights

### Step 01 — Open the dashboard  [NEW]

- **Narration:** Let's start on Trendora's dashboard, where you can see the market's regime and phase at a glance.
- **Action:** Navigate to /
- **Point out:** The regime and phase chart appears right away now — this used to take over two seconds to show up, and it now loads in a fraction of a second.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-13/step-01.png

### Step 02 — Open the Data Manager  [NEW]

- **Narration:** Next, the Data Manager — where the data behind every chart is sourced and kept up to date.
- **Action:** Navigate to /data
- **Point out:** The list of index and benchmark data sources — each shown with its honest vendor, like Stooq, Yahoo, or a FRED-macro proxy — now resolves almost instantly instead of taking over two seconds.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-13/step-02.png

### Step 04 — No range cap enforced

- **Narration:** Even an eleven-year span is accepted without any warning or truncation — there's no cap on how much data a single job can pull in.
- **Action:** Type "2026-07-17" into the "End date" field
- **Point out:** Notice there's no error message or size warning — just a normal, ready-to-submit job form.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-13/step-04.png

### Step 05 — Spot-check another page

- **Narration:** Finally, a quick look at the Evidence page, to confirm this round's fix didn't slow anything else down.
- **Action:** Navigate to /evidence
- **Point out:** The Evidence page loads normally and just as quickly as before.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-13/step-05.png

## Full tour (text only)

### Step 03 — Try a wide date range

- **Narration:** The backfill form still accepts any historical range you like, with no artificial limit on how much history you can request in one go.
- **Action:** Type "2015-01-01" into the "Start date" field
