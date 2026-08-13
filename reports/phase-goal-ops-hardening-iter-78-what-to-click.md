# Phase goal-ops-hardening-iter-78 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-78
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Backend running at `http://localhost:8255` (health endpoint answering)
- Frontend running at `http://localhost:3255`
- No login required (this project has no auth)
- No seed data required beyond the normal running instance

---

## Verification Steps

1. Open `http://localhost:3255/` in your browser
   - **Expect:** The dashboard page loads with no blank screen or error page. In the top-right of
     the header you see a green "Ready" pill.

2. Look immediately to the right of the "Ready" pill (small gray text)
   - **Expect:** Text reading "as of <1s ago" or "as of Ns ago" (some small number N). Note the
     exact number down.

3. Wait 10 seconds without clicking anything or refreshing the page

4. Look at the same gray text again
   - **Expect:** The number is now about 10 higher than what you noted in step 2 (e.g. if it read
     "as of 3s ago" in step 2, it should read approximately "as of 13s ago" now). It must NOT be
     frozen at the same number, and it must NOT have jumped back down to "<1s ago".

5. Scroll down (or look just below the header) at the thin strip that reads "GO — today's board is
   current." with a "(as of Ns ago)" suffix
   - **Expect:** The number in that parenthetical also increases in step 7 below — it moves in
     sync with the header's number.

6. Wait another 10 seconds without clicking anything

7. Look at the "(as of Ns ago)" text in the GO banner again
   - **Expect:** The number increased by about 10 since step 5, exactly like the header's number
     did.

8. Click "Data" in the left sidebar to navigate to `http://localhost:3255/data`
   - **Expect:** The page loads normally. The "Ready" pill and its "as of Ns ago" text are still
     present in the header (unchanged surface, confirming the tick works on every page, not just
     the dashboard).

9. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The "Ready" pill and a staleness annotation reappear after the page reloads and
     the first health check lands — the annotation resumes counting, it does not stay permanently
     blank.

10. Stop and restart the backend once (optional, if you have terminal access), then reload the
    frontend page
    - **Expect:** While the backend is down, the pill reads "Backend unavailable" and NO "as of Ns
      ago" text is shown at all (it must disappear, not freeze on a stale number). Once the backend
      is back up and you reload, the "Ready" pill and a fresh "as of <1s ago" annotation return.

---

## What "Working Correctly" Looks Like

- The "as of Ns ago" number next to the "Ready" pill visibly climbs every few seconds even when you
  are just sitting on the page doing nothing — it should never look stuck for more than a second or
  two.
- The same behavior is visible in the "GO" banner's "(as of Ns ago)" parenthetical, and both numbers
  stay roughly in sync with each other.
- When the backend is unreachable, the annotation vanishes entirely instead of showing a frozen or
  fabricated number.

## Common Issues

- **Number never moves / stays frozen**: The live tick (`readiness-provider.tsx`'s 1-second
  interval) is not firing — check the browser console for a JavaScript error on page load.
- **Number resets to "<1s ago" every few seconds instead of counting smoothly**: The frontend may
  be polling far more often than the configured 30-second idle cadence — check
  `config.yaml`'s `health_poll_idle_interval_seconds` and confirm the backend is reporting
  `readiness: "ready"` (a still-warming backend polls faster by design, which is expected, not a
  bug).
- **Blank page / error screen**: Check that the backend is running
  (`curl http://localhost:8255/api/health`) and the frontend dev/prod server is up on port 3255.
