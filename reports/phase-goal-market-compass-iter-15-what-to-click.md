# Phase goal-market-compass-iter-15 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-15
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Before you start

This iteration shipped **zero UI changes** — it was a backend-only J-11 Stage D readiness
diagnostic (headline outcome: `J-11 STAGE D READY: NO`, classification AVB-C; `J-11 STAGE D
AUTHORIZED: NO`). Nothing below is "new" this iteration. This guide instead re-checks that the 10
journeys this iteration is required to keep passing (J-01–J-10) still work, and that J-11's own
target — a diagnosis only, with no premature exposure of unrepaired data — held. None of these
steps have been run yet; you are the first person to execute them since this iteration completed.

**One safety rule that applies to every step below:** the app currently has 11 "incident dates"
with no fresh derived data behind them yet: `2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13,
2026-07-24, 2026-07-27, 2026-08-03, 2026-08-05, 2026-08-10, 2026-08-11, 2026-08-12`. **Never type
one of these into the `?asof=` part of the URL.** For most of them, doing so creates a permanent
data artifact the system isn't supposed to create yet. This is expected, authorized, mid-repair
state — not something to report as broken.

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running (prod scripts)
- No login required
- At least one completed scan session exists (true today — 3,117 stored sessions)

---

## Steps

1. Open `http://localhost:3255/` in your browser (do not add any `?asof=` to the URL)
   - **Expect:** the page loads with six sections top to bottom — a market-state band, a
     plain-English summary, "What changed", "Leadership rotation", "Next-session focus", and a
     manifest strip. The date shown as the current session is **not** one of the 11 dates listed
     above (it was `2026-07-23` when this guide was written — a later date is fine, one of the 11
     listed dates is not).

2. Look at the top market-state band's regime score and the phase tile's severity value
   - **Expect:** these are plain numbers/labels with no words like "GO", "NO-GO", "Ready", or
     "DEGRADED" mixed in — those readiness words only belong in the page chrome above this band,
     never inside it.

3. Read the plain-English summary card, then click `"Show cited facts"`
   - **Expect:** the card reads as a few plain sentences (state, direction, breadth, focus count) —
     no "buy", "sell", "will rise/fall", or "because of" language anywhere in it. Clicking "Show
     cited facts" reveals the specific numbers each sentence is based on.

4. Read the "What changed" card's header
   - **Expect:** it names a specific prior date and a gap in days (e.g. "vs. Jul 20, 2026 — 3 days
     ago"), and the entries below it are grouped market → breadth → sectors → themes → stocks.

5. Click into one card under "Next-session focus"
   - **Expect:** the opened card shows named reasons and cautions, each with both a threshold and
     an actual value (e.g. "ADV $2.1M vs. $1M minimum") — not a bare claim with no number.

6. Click "Market" in the left sidebar
   - **Expect:** navigates to `http://localhost:3255/market`; "Today" is listed above "Market" in
     the sidebar; the page shows two glance cards plus breadth cards, Top Sectors, Candidate
     Counts, Top Themes, and a Market Phase & Severity card — nothing looks missing compared to
     what you'd expect from a full dashboard.

7. Click "Stocks" (or navigate to `http://localhost:3255/stocks`), then set the Sector filter to
   `"Unassigned"`
   - **Expect:** a small minority of rows show — at most about 5% of the total. If most rows show
     up as Unassigned, that's a regression.

8. Navigate to `http://localhost:3255/methodology`
   - **Expect:** the page's universe/data section explicitly describes where sector labels come
     from (a curated list, falling back to pool data) and states plainly that sector history isn't
     tracked over time — only the current mapping is shown.

9. Navigate to `http://localhost:3255/data` and look at the most recent run's manifest info (do
   **not** click Remove or run a new backfill for this quick check — that's covered in the full
   test plan, `UT-J-05`/`UT-J-06`, if you have more time)
   - **Expect:** the latest ingested session shows a frozen manifest indicator with a version
     number and a generation timestamp — not a blank or "pending" state.

10. Re-read the safety rule at the top of this guide
    - **Expect:** you did not type any of the 11 listed incident dates into the URL at any point
      above. If you're unsure, reload `http://localhost:3255/` with no `?asof=` at all before
      finishing.

---

## What "Working Correctly" Looks Like

- `/` loads fast, reads like a short honest paragraph plus a few cards — no jargon, no trading
  advice language, no readiness/market vocabulary mixed together.
- Sector labels are consistent everywhere the same ticker appears, and mostly filled in (not stuck
  at "Unassigned").
- The 11 incident dates are simply absent from normal browsing — you never see them offered as a
  normal session, and you never had to visit them to complete this guide.

## If Something Looks Wrong

- **Blank page / error screen on `/`**: confirm the backend is actually running before assuming a
  regression.
- **One of the 11 incident dates shows up as a normal, undisclosed session anywhere** (a candidate
  list, an as-of picker entry with no "unavailable" label, etc.): this is a real, reportable
  finding — it would mean derived data was regenerated for an incident date before J-11 authorized
  it. Stop and escalate; do not try to "fix" it yourself.
- **Unassigned sector share is high (back near ~78%)**: this is a genuine regression of J-01 — file
  it with the specific ticker(s) you spot-checked.
- For anything else, the full test plan (`reports/phase-goal-market-compass-iter-15-ui-test-plan.md`,
  cases `UT-J-01` through `UT-J-11`) has the exact, longer steps this quick guide was distilled from.
