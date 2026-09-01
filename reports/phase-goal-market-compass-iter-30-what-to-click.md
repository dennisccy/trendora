# Phase goal-market-compass-iter-30 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-30
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running at `http://localhost:8255` (health check: `curl http://localhost:8255/api/health`)
- No login required
- No seed data action needed — this iteration's one database mint (`as_of=2026-08-12`, version 7)
  has already been performed by the dev lane before this guide is used; do not repeat the
  `POST /api/compass/regenerate` call

---

## Verification Steps

1. Open `http://localhost:3255/` in your browser (no query string — the plain default landing page)
   - **Expect:** The Today page loads with no error screen; you see a "Market state" card near the top
     and a "Summary" card below it

2. In the "Market state" card, look at the "Regime" tile (left side) and the "Market phase" tile
   (right side)
   - **Expect:** Each tile shows a small badge next to its main number. Both badges read
     "little changed" — NOT "NA"

3. Look at the "Breadth" row directly below the two tiles
   - **Expect:** Its badge, on the right side of the row, also reads "little changed" — NOT "NA"

4. Scroll down to the "Summary" card and read its second line (the "Conditions are..." sentence)
   - **Expect:** The text reads "Conditions are little changed since the prior session
     (-0.3 regime-score points)." — the word "little changed" matches the Regime badge you read in
     step 2, not a contradictory word

5. Refresh the page (press F5 or Cmd+R)
   - **Expect:** All three badges and the Summary sentence show the exact same values as before —
     this is stored, served data, not something computed fresh on each visit

6. Click the "Full market context (regime × phase, sectors, themes)" link in the top-right of the
   "Market state" card
   - **Expect:** The browser navigates to `http://localhost:3255/market` and the page loads without
     error (confirms the surrounding card still functions normally)

7. Navigate back and open `http://localhost:3255/?asof=2026-08-03` (a different, previously-verified
   date)
   - **Expect:** The three badges here read "improving", "improving", "little changed" respectively —
     different from the default view's "little changed" across the board, confirming this iteration's
     change is scoped to the default date only and did not overwrite this other date

---

## What "Working Correctly" Looks Like

- The default page (`http://localhost:3255/`, no parameters) shows three "little changed" badges,
  never "NA", in the Market state card
- The Summary card's own sentence uses the same wording as the Regime badge — no card on the page
  contradicts another

## Common Issues

- **Badges still show "NA" on `/`**: the one-time database mint for `as_of=2026-08-12` may not have
  been applied yet, or you may be looking at a stale cached page — hard-refresh (Ctrl+Shift+R) first;
  if still "NA", check that the backend's database file matches the one the mint was written to
  (`apps/backend/data/trendora.db`)
- **Blank page / error screen**: check that the backend is running
  (`curl http://localhost:8255/api/health`) and the frontend dev/start server is up on port 3255
- **Summary sentence missing or different wording**: confirm you are looking at the sentence with
  `data-testid="compass-sentence-direction"` (the second sentence in the Summary card, not the first
  "Market regime is..." sentence, which is a different, unrelated sentence)
