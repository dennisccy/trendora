# Phase goal-ops-hardening-iter-20 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-20
**Time required:** ~5 minutes (includes one ~30-second wait)
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running (you'll confirm this in Step 1 — no separate check needed)
- No login required — this is a local, single-operator tool
- Do not touch the Data Manager / backfill pages during this check — nothing below needs them

---

## What changed, in one sentence

Opening a historical `/backtest` date you've never viewed before used to freeze the tab for anywhere from
several seconds to almost a minute with nothing on screen; it now responds almost instantly and tells you
honestly that it's computing that date's numbers in the background.

---

## Verification Steps

1. Open `http://localhost:3255/backtest` in your browser
   - **Expect:** Page loads with data. Top-right header shows a green **"Ready"** badge and a **"Latest"**
     button.

2. Click the **"Latest"** button in the top-right header. A small calendar pops up. Click the year dropdown
   inside it and pick the **earliest year** listed, then click any colored day you see (if the month shown
   has no colored days, click the "▶" arrow a few times until one does).
   - **Expect:** The calendar closes and the page updates in well under 2 seconds — never a blank, frozen
     tab. Near the bottom of the page you'll see either an amber box that says **"Refreshing — showing the
     last complete evidence"** or a card that says **"Backtest evidence not yet computed."** Either one is
     correct.

3. Read the message you just saw.
   - **Expect:** It says the computation was **"started by viewing this page"** (or "Viewing this page has
     started computing it in the background"). It must NOT say anything about "the dataset has changed" or
     an "ingest" — that wording only belongs to a different scenario.

4. Note the date shown in the page's "Viewing as-of ..." badge, then wait about **30 seconds** without
   closing the tab.
   - **Expect:** Nothing to check yet — just let the background work finish.

5. Reload the page (press F5).
   - **Expect:** The "Refreshing"/"not yet computed" message is gone. A heading **"Forward-tested evidence
     (expanding window ≤ `<your date>`)"** now shows real numbers, with a "Snapshots contributing" count
     greater than 0.

6. Click the "as-of" button again (now showing your date, not "Latest"), then click **"Latest · `<date>`"**
   at the bottom of the calendar.
   - **Expect:** Instantly back to the "Latest" / "(latest)" badge, with normal data — no delay, no
     refreshing message. This confirms today's default view was never touched by this change.

7. Glance back at the green header badge from Step 1.
   - **Expect:** It said **"Ready"** the whole time, through every step above — it should never have flipped
     to "Backend unavailable."

---

## What "Working Correctly" Looks Like

- Step 2 feels instant (not a multi-second freeze) and shows an honest "computing in the background" message
  instead of a blank page.
- Step 5's reload shows real numbers where the message used to be.
- Step 6 proves the everyday "Latest" view was never at risk from this change.

## If Something Looks Wrong

- **Page freezes/stays blank for several seconds in Step 2**: this is the exact bug this iteration fixed —
  note how long it took and the exact date you clicked.
- **Step 3's message mentions "ingest" or "dataset has changed"**: copy regression — note the exact text
  shown.
- **Step 5 still shows the old message after reloading**: wait another 30 seconds and reload once more before
  calling it broken — the background compute time can vary a little with host load.
- **Step 2 shows full evidence immediately with no message at all**: you picked a date that was already
  computed by an earlier check (this happens to `2026-07-09` and `2026-07-08` specifically, already warmed
  by this iteration's own measurement) — pick a different colored day and repeat Step 2.
- **Header badge ever says "Backend unavailable"**: that would be a real problem — a brief slow response
  (a few seconds) on OTHER pages while the background compute runs is expected and fine, but the badge itself
  should never say the backend is down.
