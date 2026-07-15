# Phase goal-mcp-loop-iter-36 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-36 — Certifier calibration: referee placebo + lookahead-tripwire audit (J-22)
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running (the page will show a red "Backend unavailable" card if it isn't — see Common Issues below)
- No login is required — this product has no user accounts
- No setup needed: the real calibration report is already generated and stored in this repo, so the page shows real numbers on first visit

---

## Verification Steps

1. Open `http://localhost:3255/research` in your browser
   - **Expect:** The Research hub loads. Scroll down to the "Governance & process" section — it shows 4 cards, and the last one is titled "Referee audit."

2. Click the "Referee audit" card
   - **Expect:** The page navigates to `http://localhost:3255/research/referee-audit` and a heading reading "Referee audit" appears near the top.

3. Look at the row of 4 number cards near the top of the page
   - **Expect:** "Null trials" shows **200**; "Empirical false-pass rate" shows **0.08**; "Configured α" shows **0.05**; "Run date" shows **2026-07-01**.

4. Scroll down to the large card just below those 4 number cards
   - **Expect:** A **red** card with the heading "Tripwire: the lookahead-contaminated factor was NOT rejected," and a red "PASS" badge next to the words "expected: rejected." (This red card is correct — it means the safety check is working and honestly reporting a real problem with today's data, not that something is broken.)

5. Click "Back to Research" near the top of the page
   - **Expect:** You return to `http://localhost:3255/research`, and the same 4 cards under "Governance & process" are still there (Pre-registration registry, Negative-results graveyard, Certification-budget accounting, Referee audit).

6. Click the "Certification-budget accounting" card (one of the 3 original cards, not the new one)
   - **Expect:** It navigates to `http://localhost:3255/research/budget` and loads normally with its own numbers — confirms the older cards still work exactly as before.

7. Type `http://localhost:3255/evidence` directly into the address bar and press Enter
   - **Expect:** The page shows a card headed "No certified claims yet" — the same honest empty state this page showed before this feature existed. This confirms the new audit did not leak a fake "proven" claim into the real evidence ledger.

---

## What "Working Correctly" Looks Like

- The "Governance & process" section on `/research` shows **4** cards, not 3.
- `/research/referee-audit` shows real numbers immediately (200 / 0.08 / 0.05 / 2026-07-01) — never a row of dashes or an endless spinner.
- A vivid **red** warning card is the first thing you see below the numbers. That is the expected, correct state for today's real data — the point of this feature is that the certifier honestly flags a problem instead of hiding it.
- `/evidence` still shows its old "No certified claims yet" message, unchanged.

## Common Issues

- **Blank page or error screen on `/research/referee-audit`**: the backend is probably not running. Ask a developer to confirm it, or check that `http://localhost:8255/api/research/referee-audit` responds when opened directly in a browser tab.
- **Only 3 cards under "Governance & process" (no "Referee audit" card)**: the frontend is likely serving a stale build from before this phase shipped — ask a developer to rebuild the frontend.
- **The verdict card is a plain gray/green card instead of red**: this means the underlying report file was swapped out for a test fixture (see the full UI test plan, UT-06) — restarting the backend normally without any special environment variable should bring back the real red-card data.
- **The numbers on the page don't match those listed above**: someone may have re-run the offline audit job with different settings since this guide was written — check with a developer before treating this as a bug.
