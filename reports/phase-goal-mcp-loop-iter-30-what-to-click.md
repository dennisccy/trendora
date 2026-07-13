# Phase goal-mcp-loop-iter-30 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-30
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`, backend running at `http://localhost:8255` (start via
  `scripts/start-backend.sh` / `scripts/start-frontend.sh` — prod mode; run `rm -rf apps/frontend/.next`
  first if either service has been up since before this iteration's code landed, so the new page isn't
  served from a stale build).
- No login required — this product has no authentication.
- The registry data file `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` must be present (11
  rows) for steps 1–6 to show real data.
- This iteration adds ONE new page and ONE small addition to an existing hub page — everything else in the
  app should look and behave exactly as it did before.

---

## Verification Steps

1. Open `http://localhost:3255/research` in your browser
   - **Expect:** "Research" heading loads with its usual grid of 10 lab cards, no errors. Scroll down past
     the last card and you should now also see a new heading, "Governance & process", with one card below
     it titled "Pre-registration registry".

2. Click the "Pre-registration registry" card
   - **Expect:** The browser navigates to `http://localhost:3255/research/registry`. A "Back to Research"
     link appears at the top, followed by the heading "Pre-registration registry".

3. Wait for the table to finish loading
   - **Expect:** A table appears with 5 columns — Selectors, Rationale, Registered, Source, Status —
     containing exactly **11 rows**, none of them blank.

4. Look at the Status column for any row
   - **Expect:** A small plain gray badge reading either `tested` or `closed`, with a second small gray
     badge reading `backfill` right beside it. These should look muted/neutral — never green or red, and
     never the words "Proven" or "Not yet proven" (that language belongs only to the separate `/evidence`
     page, not here).

5. Look at the Selectors column for any row
   - **Expect:** A handful of small readable tags like `factor=vcp_contraction`, `horizon=60`,
     `direction=positive` — never a raw block of `{ "key": "value" }`-style text.

6. Refresh the page (F5)
   - **Expect:** The same 11 rows reappear identically — confirms the table is reading real backend data,
     not something cached only in the browser.

7. Navigate to `http://localhost:3255/evidence`
   - **Expect:** The pre-existing "Evidence" page still loads normally, showing 7 claim cards each with a
     red "FAIL" badge — exactly as it looked before this iteration. This confirms the new page didn't break
     anything else in the app.

8. Stop the backend process, then reload `http://localhost:3255/research/registry`
   - **Expect:** A single card reading "Backend unavailable" appears — not a blank page, not a browser
     error screen. Restart the backend afterward and reload once more to confirm the 11-row table comes
     back.

---

## What "Working Correctly" Looks Like

- The Research hub (`/research`) shows its original 10 lab cards **plus** one new "Governance & process"
  section with a single "Pre-registration registry" card — reachable in exactly 2 clicks from the
  Dashboard.
- `/research/registry` shows a calm, read-only table of 11 rows with readable chips (not JSON) and
  neutral gray status badges (never colored "Proven"/"Not yet proven" language).
- Stopping the backend shows one contained "Backend unavailable" card on the new page — never a blank
  crash.
- `/evidence` and every other existing page look and behave exactly as they did before this iteration —
  nothing regressed.

## Common Issues

- **`/research/registry` gives a 404 or "This page could not be found"**: the frontend is likely serving a
  stale build. Run `rm -rf apps/frontend/.next` and restart the frontend.
- **The new "Governance & process" section never appears on `/research`**: check you scrolled all the way
  past the 10 existing lab cards — it's a separate section below the main grid, not mixed into it.
- **The table shows fewer than 11 rows, or any cell is blank**: the registry file may be missing or
  partially written — check `runs/goal-session-mcp-loop/state/pre-registrations.jsonl` exists and has 11
  lines.
- **A Status badge shows colored green/red styling, or the words "Proven"/"Not yet proven"**: flag this
  immediately — the registry's status column must always stay neutral/gray and use only "tested"/"closed",
  never the proven-language reserved for the `/evidence` page.
- **Blank page instead of the "Backend unavailable" card**: check the browser console for an unhandled
  JavaScript error and report it — the page is designed to always show a contained error card, never a
  blank crash.
