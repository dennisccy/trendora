# Phase goal-i_can_see_the_wealthy_future_forever-iter-8 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-8
**Time required:** ~4 minutes
**Written by:** ui-test-designer

---

## What this iteration did (read first)

This iteration **STALLED with zero changes** — the offline data fetch (real OHLCV + market cap for the
~426 new candidate symbols) was blocked by an external rate limit (Yahoo HTTP 429), so `universe.json`
was never produced and **no code, config, or UI changed**.

So you are **not** verifying a new feature. You are verifying that the product is **unchanged and
honest**: the still-unbuilt Universe-Selection surfaces remain correctly hidden (no fake/empty screen),
and the existing product still works over the 122-name universe.

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running and reachable (pages fetch `/api/methodology` and `/api/data`)
- No login required

---

## Verification Steps

1. Open `http://localhost:3835/methodology` in your browser
   - **Expect:** Methodology page loads with no error; the setup/pattern glossary content is visible

2. Scroll the entire `/methodology` page top to bottom, looking for a "Universe Selection" card
   - **Expect:** There is **NO** "Universe Selection" card, no threshold block, and no "resolved size
     ≈ 500" line — the section is fully absent (not a blank/placeholder card)
   - **Broken looks like:** a visible Universe Selection card, an empty card frame, or zero/fake
     thresholds — that would mean the honest gate leaked

3. Navigate to `http://localhost:3835/data`
   - **Expect:** Data coverage page loads with no error; the existing coverage grid is visible

4. Look for a "Universe" coverage metric and read its number
   - **Expect:** Either no expanded Universe metric, or a count reflecting the **122-name** universe —
     it must **NOT** show ~400–500 names
   - **Broken looks like:** a Universe count of ~500 (or 426) — that would mean fabricated data appeared

5. Navigate to `http://localhost:3835/` (dashboard)
   - **Expect:** Dashboard loads with ranked rows/scores rendering normally, exactly as before

6. Navigate to `http://localhost:3835/leaderboard`
   - **Expect:** Leaderboard loads with ranked rows over the 122-name universe (not 400–500 rows);
     no errors, no empty states

7. Glance at the top navigation on any page
   - **Expect:** Existing links (Dashboard, Leaderboard, Methodology, Data) work; there is **NO** new
     "Universe" link leading to an empty or fake screen

---

## What "Working Correctly" Looks Like

- Every page loads cleanly and looks **identical to the end of iter-7**
- The Universe-Selection card (`/methodology`) and expanded Universe count (`/data`) are **absent** —
  the honest gate is doing its job
- Nothing anywhere shows a fabricated ~400–500-name universe

## Common Issues

- **Blank page / error screen**: Confirm the backend is running (`curl http://localhost:8000/health`
  or the configured backend port) and the frontend dev server is up on port 3835
- **A Universe Selection card or ~500 count appears**: This is a FAIL for this iteration — it means
  fake/placeholder data surfaced even though `data/seed/universe.json` was never produced. Flag it.
