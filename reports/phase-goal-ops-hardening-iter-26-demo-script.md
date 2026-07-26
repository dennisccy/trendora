# Demo Script — goal-ops-hardening-iter-26

**Mode:** record
**Date:** 2026-07-26
**Frontend URL:** http://localhost:3255
**Iteration:** 26

## Highlights

### Step 01 — Open Trendora's home page

- **Narration:** Let's take a tour of Trendora, starting on the home page where the current market regime is summarized at a glance.
- **Action:** Navigate to /
- **Point out:** The regime chart appears right away, with no error banner or blank space.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-26/step-01.png

### Step 02 — Check the Data Manager's honest status

- **Narration:** Now let's visit the Data Manager, where new market data arrives. The status badge in the top bar is visible on every page and always reflects the backend's real, current health — never a guess, and never stuck mid-boot without saying so.
- **Action:** Navigate to /data
- **Point out:** The badge reads "Ready" with a green dot.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-26/step-02.png

### Step 03 — See every backfill job that's ever run

- **Narration:** Scrolling down, the Run history table keeps a permanent record of every data job that's completed — including ones that found nothing new to do.
- **Action:** Click "Run history"
- **Point out:** A zero-work run is explained plainly, not just silently marked "done" like a real one.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-26/step-03.png

### Step 04 — Confirm the backfilled dates in Scanner Runs

- **Narration:** Every date a backfill touched shows up here, each one an exact, immutable snapshot of what the scanner saw that day.
- **Action:** Navigate to /scanner-runs
- **Point out:** Real dates in the "As of" column, each opening its own stored leaderboard.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-26/step-04.png

### Step 11 — An older date, served honestly while a new one warms up

- **Narration:** Ask Backtest for a date whose own evidence hasn't finished computing yet, and it never leaves you staring at a blank spinner — it instantly shows the last complete version it has, clearly labeled, while the new one finishes in the background.
- **Action:** Navigate to /backtest?asof=2026-07-20
- **Point out:** A visible "Refreshing — showing the last complete evidence" banner discloses exactly which older date is being shown, while the page still renders full evidence in well under a second — never a blank wait.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-26/step-11.png

### Step 12 — The banner disappears the moment the new evidence is ready

- **Narration:** Once the background computation finishes, reloading the same date now shows its own freshly stored evidence — banner gone, nothing recomputed on the spot, just a normal read from storage.
- **Action:** Navigate to /backtest?asof=2026-07-20
- **Point out:** The refreshing banner is gone and this date's own forward-tested evidence now renders directly, exactly like the always-ready latest view.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-26/step-12.png

### Step 14 — A background compute window, disclosed live

- **Narration:** Asking Backtest for an older date whose evidence hasn't finished computing starts a background compute — and the top bar says so immediately, right alongside the Ready pill.
- **Action:** Navigate to /backtest?asof=1996-02-01
- **Point out:** When a window is running, a badge reads "background compute running (N)" next to "Ready" — never a bare Ready hiding real background work, and never a misleading "initializing" or "unavailable".
- **Screenshot:** reports/demo/goal-ops-hardening-iter-26/step-14.png

### Step 16 — The Data Manager panel names exactly what's happening

- **Narration:** Scrolling to that last panel shows the same disclosure in detail: which date is involved, how long it's taken, and how it finished — real numbers, never a guess.
- **Action:** Click "background-compute-panel"
- **Point out:** The panel always ends with the same honest line: this history lives only in the backend's memory since its last restart, never persisted.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-26/step-16.png

## Full tour (text only)

### Step 05 — Try a wide date range

- **Narration:** Back on the Data Manager, the backfill form accepts any historical range you like, with no artificial limit on how much history you can request in one go.
- **Action:** Navigate to /data

### Step 06 — No range cap enforced

- **Narration:** Filling in an eleven-year span, from 2015 to today, is accepted without any warning or truncation — there's no cap on how much data a single request can cover.
- **Action:** Type "2015-01-01" into the "Start date" field
- **Point out:** Notice there's no error message or size warning — just a normal, ready-to-submit form.

### Step 07 — Aggregates computed once, at ingest

- **Narration:** One more look at the Job progress panel: everything it lists — including the forward-looking aggregates used elsewhere in the app — was computed once when the data arrived, not recalculated every time someone looks.
- **Action:** Click "Job progress"
- **Point out:** The summary line lists "forward aggregates" among the things refreshed by that run.

### Step 08 — Every page is checked against a committed budget

- **Narration:** Trendora doesn't just feel fast — every page's loading time is measured and checked against a budget committed in the project's own performance report.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** This stock detail page — scores, risk detail, and all — loads well inside its own committed budget.

### Step 09 — Heavy number-crunching never slows down the rest of the app

- **Narration:** When Trendora computes a big batch of forward-looking evidence in the background, the rest of the app keeps answering normally the whole time — measured, not just claimed.
- **Action:** Navigate to /backtest
- **Point out:** The service keeps answering every request through the whole process, with no downtime.

### Step 10 — Backtest evidence, served instantly from storage

- **Narration:** At the latest date, Backtest doesn't calculate anything on the spot — it simply displays evidence that was already computed and stored ahead of time.
- **Action:** Navigate to /backtest
- **Point out:** The full forward-tested evidence panel renders immediately, with no refreshing banner and no waiting.

### Step 13 — The backend discloses its own background work — starting from a quiet baseline

- **Narration:** Trendora's top bar doesn't just say the backend is healthy — it also discloses whenever it's quietly computing something big in the background. Right now, at rest, it simply reads "Ready": no extra badge, because nothing is running.
- **Action:** Navigate to /data
- **Point out:** The badge shows only the plain "Ready" pill — no background-compute indicator, because there is nothing to disclose right now.

### Step 15 — Back to the Data Manager to see the same disclosure

- **Narration:** The same disclosure also lives on the Data Manager page, in a panel of its own — right at the bottom, after every other data-management tool on the page.
- **Action:** Navigate to /data

### Step 17 — Honest afterward — and honest about its own memory

- **Narration:** Once the background compute finishes, the panel moves it into a last-outcome line with its real, measured duration. Because this history lives only in the backend's own memory, a restart makes it say so plainly instead of guessing.
- **Action:** Navigate to /data
- **Point out:** A completed outcome shows its real duration and the exact date it covered; after an actual backend restart, the panel correctly resets to "Last outcome: none yet" — honest that this history never survives a restart.
