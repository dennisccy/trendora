# Phase goal-ops-hardening-iter-19 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-19
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255` (backend at `http://localhost:8255`) — both are already
  running; you do not need to start, stop, or restart anything.
- No login exists in this app.
- **Nothing new to discover this time.** This iteration made no visual or feature change — you are
  confirming that one existing page (`/backtest`) still looks exactly right, and that it now loads fast
  even under heavy traffic. (If you're an automated agent relying on Chrome MCP and it's still unreachable
  on port 9224 this session, that only blocks automated browser control — a live person with a normal
  browser can follow every step below unaffected.)

---

## Verification Steps

1. Open `http://localhost:3255/backtest` in your browser.
   - **Expect:** the page loads in about a second or less — no long spinner, no blank page. A "Backtest"
     heading appears near the top, with a "Viewing as-of `<date>` (latest)" badge just below it.

2. Scroll down to the "Forward-test scorecard" section.
   - **Expect:** a table appears with one row per horizon (1d, 5d, 10d, 20d, 60d). Seeing a small card
     that says "No elapsed forward window for this date yet" right above the table is normal here — it
     just means today's scan is too recent for its own forward return to be knowable yet, not an error.

3. Keep scrolling to the "Leadership cohorts" section.
   - **Expect:** "Top Sectors", "Top Themes", and a "Ranked cohort" table are all populated with real
     tickers, ranks, and score badges — nothing blank, nothing showing a red error message.

4. Scroll to the very bottom of the page.
   - **Expect:** a "Forward-tested evidence" section with real, populated numbers underneath it — not an
     empty state, not an error card.

5. Reload the page (press F5) and pay attention to how quickly it comes back.
   - **Expect:** it reloads about as fast as step 1 did — no noticeable slow-down, no spinner that hangs.
     **This is the entire point of this iteration:** this exact page used to be able to take over a second
     to load under heavy traffic (measured mean 1083 ms under 6 simultaneous requests); it now consistently
     loads in roughly a tenth of that time (measured mean 112 ms) — you should be able to feel the
     difference even with nobody else hitting the page but you.

6. Click the small calendar button near the top of the page (it currently reads "Latest"), then pick any
   older date from the calendar that opens.
   - **Expect:** the badge changes to "Viewing as-of `<the date you picked>` (historical)", and the
     "Forward-test scorecard" table now shows real numbers instead of "—" in most rows — older dates have
     had time for their forward returns to actually happen, unlike the "latest" view in step 2.

7. Confirm you never saw a red "Backend unavailable" error card at any point above.
   - **Expect:** no red error card, on any of the pages/dates you visited.

---

## What "Working Correctly" Looks Like

- Every load of `/backtest` (steps 1 and 5) feels close to instant — no spinner that hangs for more than a
  second or two.
- The scorecard, leadership lists, and evidence section all show the same kind of real, populated data they
  always have — nothing looks different, blank, or broken from before this iteration.
- Switching to a historical date (step 6) still works, and switches the numbers from mostly "—" to mostly
  real figures.

## If Something Looks Wrong

- **Red "Backend unavailable" card anywhere**: the backend may be down. Do not try to restart it yourself —
  report it. (Both services were confirmed running before this check began, so this would be unexpected.)
- **The page takes noticeably longer than a second or two to load**, especially with several browser tabs
  open to it at once: this would mean the speed fix did not actually take effect on the running backend —
  flag this immediately, since it is the one thing this entire iteration was about.
- **The scorecard, leadership, or evidence numbers look different than they used to** (if you have a prior
  screenshot to compare): flag this as a possible regression — this iteration was designed to change ONLY
  how fast the page loads, never any displayed number.
