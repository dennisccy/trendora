# Phase goal-market-compass-iter-39 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-39
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255` and backend running at `http://localhost:8255`
  (start with `bash scripts/start-backend.sh` / `bash scripts/start-frontend.sh` if not already up).
- No login required.
- No seed data setup required — this repair uses the already-committed 30-year seed database.

---

## Verification Steps

1. Open `http://localhost:3255/` in your browser
   - **Expect:** The "Today" heading with subtitle "The ten-second read after the close" loads, along with the "Market state", summary, "What changed", leadership rotation, "Next-session focus", and manifest strip cards. No error card of any kind.

2. Navigate to `http://localhost:3255/?asof=2026-08-11`
   - **Expect:** The full page renders exactly as in step 1 — this is one of the 21 dates that used to crash with a "Something went wrong on this page" card before this fix. That crash card must NOT appear.

3. Scroll down to the "Next-session focus" card and find the "Not priority (...)" line
   - **Expect:** The text reads exactly `Not priority (20 shown — held-back counts unavailable for this manifest version)`.

4. Click that "Not priority (...)" line to expand it
   - **Expect:** A list of ticker names appears below it, each with its own reasons. None of them shows a "ranked #... cap ..." phrase (that data is honestly unavailable for this older date, never faked).

5. Navigate to `http://localhost:3255/?asof=2026-08-12`
   - **Expect:** The "Not priority (...)" line now reads the fuller text `Not priority (20 shown of 52 held back — 27 cap-excluded, 25 below-floor near-miss)` — this is the newest date, unaffected by the bug, and this text is unchanged from before the fix.

6. Click that "Not priority (...)" line to expand it
   - **Expect:** At least one entry in the list shows a phrase like "— ranked #N of the above-floor names, cap 20".

7. Navigate to `http://localhost:3255/?asof=1996-01-02` (the oldest of the previously-crashing dates)
   - **Expect:** The page still renders fully with no crash card — confirms the fix works across the full 30-year date range, not just recent dates.

8. Click "Full market context (regime × phase, sectors, themes)" in the "Market state" card (top of the page)
   - **Expect:** Navigates to `http://localhost:3255/market?asof=1996-01-02` and that page renders normally with no error card — confirms an unrelated page that was reachable through the crashed page is still fine.

---

## What "Working Correctly" Looks Like

- Every historical date you try via `?asof=<date>` shows the full Today page — no red "Something went
  wrong on this page" card, ever.
- On older dates, the "Not priority" line says "held-back counts unavailable for this manifest
  version" instead of crashing. On the newest date (`2026-08-12`), it still shows the full
  "N shown of M held back — X cap-excluded, Y below-floor near-miss" breakdown, unchanged.

## Common Issues

- **Blank page / error screen**: check that both services are running — `curl http://localhost:8255/api/health` and confirm `http://localhost:3255` responds. If the backend is down you'll see a distinct "Backend unavailable" card instead (that one is expected and unrelated to this fix).
- **"Not priority" text missing entirely**: hard refresh (Cmd/Ctrl+Shift+R) — this is a text-only change and does not require clearing any data, but a stale cached JS bundle can mask it.
- **Old crash still appears on `?asof=2026-08-11` or similar**: this means the fix regressed — capture a screenshot and the browser console error, then flag it immediately; this was the exact bug this iteration repairs.
