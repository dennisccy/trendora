# Phase goal-ops-hardening-iter-6 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-6
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Backend running in **prod mode**: `scripts/start-backend.sh` (not `dev.sh`)
- Frontend running in **prod mode**: `scripts/start-frontend.sh` (not `dev.sh`), serving at
  `http://localhost:3255`
- No login required
- Nothing looks different this time — this iteration only changed WHEN two widgets fetch their data, not
  what they show. Your job is to confirm both pages still load correctly and feel snappy, and that nothing
  ever goes blank while data is loading.

---

## Verification Steps

1. Open `http://localhost:3255/` in your browser
   - **Expect:** Dashboard loads, no error page, cards populate with numbers/charts normally

2. Scroll down to the bottom of the Dashboard, past the "Market Phase & Severity" card
   - **Expect:** A card titled "Regime × phase cross-view" is there. Briefly you may see a plain grey
     pulsing rectangle where the chart goes — that's the loading placeholder, expected and brief. Within
     about a second it should be replaced by an actual two-pane chart (or, rarely, a message saying "No
     index history is available for this date.")

3. Reload the page (press F5) 2 more times, watching the "Regime × phase cross-view" card each time
   - **Expect:** Each reload, the card shows its grey pulsing skeleton first, then quickly (under ~1.5
     seconds) fills in with the chart. It should never sit blank/empty and never look frozen showing an
     old chart from before the reload.

4. On the same Dashboard, click the "◀" arrow button in the top bar (next to the amber/grey date badge)
   twice quickly, right after the page loads
   - **Expect:** The "Viewing as-of ... (historical)" badge updates to a date two trading days earlier, and
     the "Regime × phase cross-view" card at the bottom shows its grey skeleton again briefly, then settles
     to the chart for the new date. It should never go blank or stay stuck.

5. Open `http://localhost:3255/data` in your browser
   - **Expect:** "Data Manager" heading loads, "Dataset coverage" numbers populate normally

6. Scroll down past "Rebuild snapshots for current universe" until you find a calendar-style grid of
   colored day-cells (the availability heatmap)
   - **Expect:** For roughly the first 2.5 seconds you'll see a spinning icon with the text "Loading
     availability…" — that wait is intentional and expected this iteration. It should then be replaced by
     the actual colored calendar grid with a legend underneath. It should never sit blank with no spinner
     and no grid.

7. Reload `/data` (F5) 2 more times, watching the heatmap panel each time
   - **Expect:** Same pattern each time — spinner + "Loading availability…" for a couple of seconds, then
     the colored grid appears. Total time to see the grid should stay under ~3 seconds.

8. Back on `/data`, in the "Start a fetch / backfill job" panel: type `2026-05-02` into "Start date" and
   `2026-05-03` into "End date" (leave "Job kind" as "Backfill snapshots"), then click "Start"
   - **Expect:** The job runs briefly and finishes; somewhere in its summary you should see the text
     "2 non-trading" (both of those calendar dates are weekend days, so this run intentionally creates no
     new data).

9. Reload `/data` and scroll to the "Run history" table at the very bottom of the page
   - **Expect:** The newest row shows the date range `2026-05-02 → 2026-05-03` with a grey badge that says
     **"no new snapshots"** — this is deliberately a different-looking badge from the green "ok" badge a
     normal productive run gets, so a zero-work run is never mistaken for a real success.

10. Optional deeper check (needs Chrome DevTools): on either page, open DevTools → Network tab, filter by
    `indexes?full=true` (on `/`) or `data/availability` (on `/data`), and reload. The "Time" column should
    read under 1500ms both times.

---

## What "Working Correctly" Looks Like

- Both the Dashboard's cross-view chart and the Data Manager's availability heatmap always show either
  their loading placeholder (skeleton/spinner) OR their real content — never a blank gap, never a frozen
  stale view, even right after a fast reload or a quick as-of date change.
- Reloading either page repeatedly feels quick — the cross-view chart and heatmap should visibly fill in
  well under 2 seconds after their brief loading placeholder.
- Submitting the weekend-only backfill in step 8 produces a clearly distinct "no new snapshots" badge, not
  the same green badge as a real data-producing run.

## If Something Looks Wrong

- **Cross-view card or heatmap stuck on the loading placeholder forever / never fills in**: confirm the
  backend is actually running (`curl http://localhost:8255/api/health` — or the port your backend uses —
  should return `200`). If the backend is up and it's still stuck, that's a real regression, worth a bug
  report.
- **Cross-view card or heatmap goes completely blank (no skeleton, no spinner, no chart) at any point**:
  this is exactly what this iteration was supposed to prevent — report it.
- **`/evidence` or `/research/event-study` take a very long time to load (up to several minutes)**: this is
  a known, pre-existing issue unrelated to this iteration's fix — already flagged for a future fix, not a
  new bug to report.
- **Run history's newest row shows a green "ok" badge instead of "no new snapshots" after the weekend
  backfill in step 8**: report it — the zero-work run should never look like a normal success.
