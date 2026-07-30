# Phase goal-ops-hardening-iter-36 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-36
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Backend running (`scripts/start-backend.sh`) and frontend running at `http://localhost:3255` (`scripts/start-frontend.sh`)
- No login required
- Chrome DevTools available (for the throttling step) — optional but recommended

---

## Verification Steps

1. Open `http://localhost:3255/research/factor-lab` in your browser
   - **Expect:** Page loads with heading "Research — Factor Lab"; a data table of factors eventually renders (no "Backend unavailable" card, no blank screen)

2. Open `http://localhost:3255/research/phase-severity-lab`
   - **Expect:** Page loads with heading "Research — Market Phase & Severity Lab"; tables render normally

3. Open `http://localhost:3255/research/regime-phase-factor`
   - **Expect:** Page loads with heading "Research — Regime × Phase × Factor"; the study table renders normally

4. Open `http://localhost:3255/research/severity-velocity`
   - **Expect:** Page loads with heading "Research — Severity-velocity × Regime"; the study body renders normally

5. Stop the backend service (kill the process running on port 8255), then reload `http://localhost:3255/research/factor-lab`
   - **Expect:** After a moment, a red-bordered "Backend unavailable" card appears with a "Retry" button — not a blank page and not an unstyled browser error

6. Restart the backend service, then click the "Retry" button on the Factor Lab error card
   - **Expect:** The error card disappears, a brief loading state appears, and the data table renders — never a second frozen error card

7. Repeat step 5's backend-stop, then reload `http://localhost:3255/research/regime-phase-factor`
   - **Expect:** A "Backend unavailable" card appears with its own "Retry" button (same visual pattern, page's own inline card design)

8. Restart the backend, click that page's "Retry" button
   - **Expect:** The error card disappears and the Regime × Phase × Factor table renders

9. Open `http://localhost:3255/data`
   - **Expect:** The universe count, coverage status, and membership-timeline chart display real numbers (not blank, not an error) — confirms the internal batching fix did not break the Data page

10. Open `http://localhost:3255/evidence` and click into any certified claim's row
    - **Expect:** The "drawdown & dry-spell expectations" panel shows real computed figures (max drawdown, underwater days, etc.), not a "not available right now" placeholder — confirms the internal chunking fix did not break the Evidence page

---

## What "Working Correctly" Looks Like

- All 4 sibling Research lab pages (`factor-lab`, `phase-severity-lab`, `regime-phase-factor`, `severity-velocity`) load their tables normally under a healthy backend, matching Regime Lab's existing behavior.
- When the backend is down, each of the 4 pages shows a clearly labelled "Backend unavailable" card with a working "Retry" button — never a blank page, never a frozen error with no way forward.
- `/data` and `/evidence` show the same numbers as before this phase — these two pages should look completely unchanged.

## Common Issues

- **Blank page / raw browser error instead of a styled "Backend unavailable" card**: the backend may not actually be reachable at all (check `curl http://localhost:8255/api/health`); this is a real regression if the styled error card is missing.
- **Retry button does nothing / page stays on the error card after backend restart**: confirm the backend was fully restarted (not just still starting up) before clicking Retry; if the card still doesn't clear, this is a regression.
- **`/data` or `/evidence` shows different numbers than before**: this would indicate the backend memory-bounding fix broke byte-identical output — flag immediately, this must not happen.
