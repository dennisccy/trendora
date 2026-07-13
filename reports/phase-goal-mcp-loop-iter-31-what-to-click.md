# Phase goal-mcp-loop-iter-31 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-31
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`, backend running at `http://localhost:8255` (start via
  `scripts/start-backend.sh` / `scripts/start-frontend.sh` — prod mode; run `rm -rf apps/frontend/.next`
  first if either service has been up since before this iteration's code landed, so the new page isn't
  served from a stale build).
- No login required — this product has no authentication.
- Both ledger data files must be present for steps 1–7 to show real data:
  `runs/goal-session-mcp-loop/state/certified-claims.jsonl` (7 rows) and
  `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` (7 rows) — 14 total.
- This iteration adds ONE new page, ONE new card on an existing hub page, and ONE small anchor addition to
  an existing page — everything else in the app should look and behave exactly as it did before.

---

## Verification Steps

1. Open `http://localhost:3255/research` in your browser
   - **Expect:** "Research" heading loads with its usual grid of 10 lab cards, no errors. Scroll down past
     the last card to "Governance & process" and you should now see **two** cards there: "Pre-registration
     registry" (unchanged, first) and a new one, "Negative-results graveyard" (second, archive icon).

2. Click the "Negative-results graveyard" card
   - **Expect:** The browser navigates to `http://localhost:3255/research/graveyard`. A "Back to Research"
     link appears at the top, followed by the heading "Negative-results graveyard".

3. Wait for the table to finish loading
   - **Expect:** A table appears with 6 columns — Selectors, Verdict, Date, Deflation, Ledger, Lineage —
     containing exactly **14 rows**: 7 tagged `canonical` and 7 tagged `staging` in the Ledger column.
     Every Verdict badge reads `FAIL` in red (none read `PASS` or use green/accent styling).

4. Find the row whose Selectors chips include `factor=ma_stack`
   - **Expect:** Beside its red `FAIL` badge, a second small muted badge reads `permanent` — this is the
     one hypothesis in the table flagged as never-to-retry. No other row shows this badge.

5. Click that row's Lineage link (reads `factor-ma_stack-d10-h20 →`)
   - **Expect:** The browser navigates to
     `http://localhost:3255/research/registry#registration-factor-ma_stack-d10-h20`, and the page scrolls
     down to and highlights the exact matching row (Rationale text starting "Moving-average-stack") — not
     just the top of the page.

6. Go back to the graveyard tab and scroll to the bottom of the page
   - **Expect:** A card titled "Revisit protocol" is visible, with rule text beginning "A referee
     FAIL/INSUFFICIENT is final for that hypothesis; a re-test requires a materially changed
     precondition...".

7. Navigate to `http://localhost:3255/evidence`
   - **Expect:** The pre-existing "Evidence" page still loads normally, showing 7 claim cards each with a
     red "FAIL" badge — exactly as it looked before this iteration. This confirms the new page didn't
     break anything else in the app.

8. Stop the backend process, then reload `http://localhost:3255/research/graveyard`
   - **Expect:** A single card reading "Backend unavailable" appears — not a blank page, not a browser
     error screen. Restart the backend afterward and reload once more to confirm the 14-row table comes
     back.

---

## What "Working Correctly" Looks Like

- The Research hub (`/research`) shows its original 10 lab cards **plus** a "Governance & process" section
  now holding two cards — "Pre-registration registry" and the new "Negative-results graveyard" — reachable
  in exactly 2 clicks from the Dashboard.
- `/research/graveyard` shows a calm, read-only table of 14 rows (7 canonical + 7 staging), every Verdict
  badge red/amber (FAIL/INSUFFICIENT) and never green/"Proven", the `ma_stack` row carrying a "permanent"
  pill, and a Revisit-protocol panel every row links to.
- Clicking a Lineage link lands precisely on the matching row on `/research/registry`, not just the page
  top.
- Stopping the backend shows one contained "Backend unavailable" card on the new page — never a blank
  crash.
- `/research/registry` and `/evidence` look and behave exactly as they did before this iteration — nothing
  regressed.

## Common Issues

- **`/research/graveyard` gives a 404 or "This page could not be found"**: the frontend is likely serving a
  stale build. Run `rm -rf apps/frontend/.next` and restart the frontend.
- **The "Governance & process" section shows only one card**: check you're not looking at a cached page —
  hard-refresh. The section should now hold two cards after this iteration.
- **The table shows fewer than 14 rows, or any cell is blank**: one of the two ledger files may be missing
  or partially written — check both `certified-claims.jsonl` and `staging-ledger.jsonl` exist under
  `runs/goal-session-mcp-loop/state/` with 7 lines each.
- **A Verdict badge shows green/accent styling, or the word "Proven" appears anywhere on the page**: flag
  this immediately — this page must only ever show red (FAIL) or amber (INSUFFICIENT), and "Proven"
  language belongs exclusively to the separate `/evidence` page.
- **Clicking a Lineage link lands at the top of `/research/registry` instead of the matching row**: the
  row-anchor addition may not have deployed — check `apps/frontend/app/research/registry/page.tsx` has the
  `id={`registration-${row.id}`}` attribute on each table row.
- **Blank page instead of the "Backend unavailable" card**: check the browser console for an unhandled
  JavaScript error and report it — the page is designed to always show a contained error card, never a
  blank crash.
