# Phase goal-mcp-loop-iter-35 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-35
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable (you'll know it isn't if `/data` shows a red "Backend unavailable"
  box instead of numbers)
- No login, no seed data setup, and no special permissions needed — this is a read-only report that
  appears automatically; there is nothing to configure before you start

---

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** The "Data Manager" page loads with a "Dataset coverage" card showing real numbers
     (not a blank page, not a red error box)

2. Scroll down slightly until you see a card titled "Live-vs-seed drift" (it has a small two-arrow
   compare icon next to the title). It sits directly below the "Storage footprint" card
   - **Expect:** This card is new this phase. Read the gray sentence directly under its title — it
     should explain in plain language what the check does, with no need to hover or click anything

3. Read the card's main status line. It will say ONE of the following:
   - Gray: "No fetch has run yet — nothing to compare against the committed seed."
   - Green: "The most recent fetch matched the committed seed over the last `N` common date(s)."
   - Amber (loud): "Live-vs-seed drift detected — the provider re-adjusted already-committed history
     for `N` symbol(s)." followed by a list of ticker symbols and dates
   - Amber (loud): "The drift report exists but could not be read. Re-run a Fetch job to regenerate
     it."
   - **Expect:** Any of the first three is a normal, healthy state. Only the last one ("could not be
     read") signals an actual problem worth reporting

4. Press F5 (or Cmd+R) to refresh the page, then look at the same card again
   - **Expect:** The exact same status line from step 3 is still shown — this confirms the card is
     reading a real, saved report from the server, not something made up on the fly by your browser

5. Click "Dashboard" at the top of the left sidebar (this takes you away from `/data`)
   - **Expect:** A thin strip appears at the very top of the page, just below the header bar. If step
     3 showed gray or green, this strip should be a quiet green line reading "GO — today's board is
     current." If step 3 showed either amber state, this strip should instead be a wider amber (or
     red) banner whose bulleted list mentions "Live-vs-seed drift"

6. Without touching anything else, scroll back down to `/data` (click "Data Manager" in the sidebar
   again) and look at the "Rebuild snapshots for current universe" panel just below the drift card
   - **Expect:** It still renders normally with its own heading and content — the new card did not
     push it off-screen, overlap it, or break it

7. Click "Stocks" in the left sidebar
   - **Expect:** The leaderboard loads with ranked rows, and each row shows a small "Proven" or "Not
     yet proven" badge next to its scores — unrelated to this phase, and should look exactly as it did
     before

---

## What "Working Correctly" Looks Like

- The "Live-vs-seed drift" card is visible on `/data`, directly under "Storage footprint," and always
  shows one clear, plain-language sentence — never a blank space, never raw JSON, never "undefined"
- The banner strip at the top of every page (not just `/data`) always agrees with what the drift card
  says: both quiet, or both mentioning the same drift symbols — they read the same underlying report
- Everything that existed on `/data` and `/stocks` before this phase (coverage numbers, the rebuild
  panel, the leaderboard, evidence badges) still looks and behaves the same

## If Something Looks Wrong

- **Blank page / red error box on `/data`**: the backend isn't running or isn't reachable — this is
  unrelated to the drift feature specifically; confirm the backend process is up
- **The amber "could not be read" message on the drift card**: this is a handled, honest state (not a
  crash), but if it persists across multiple page loads with no explanation, flag it — it usually
  means the underlying report file on the server got corrupted and needs a fresh Fetch job to
  regenerate it
- **The drift card says "no fetch yet" (gray) but the top banner is amber and mentions drift, or vice
  versa**: these two must always agree, since they read the exact same report — a mismatch between
  them is a real bug, not expected behavior
- **The banner is permanently amber/red even though you never ran a Fetch job and this is a fresh
  install**: this would be a regression — before this phase, a never-fetched board always read "GO"
