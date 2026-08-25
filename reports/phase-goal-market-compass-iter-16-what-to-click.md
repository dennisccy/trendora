# Phase goal-market-compass-iter-16 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-16
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Before you start

This iteration shipped **zero UI changes** — it was backend-only. What it actually did: applied the
ONE owner-authorized correction to AVB's stored `daily_prices.volume` on `2026-08-11`/`2026-08-12`
(from `1,549,436`/`10,350,885` to `554,757`/`3,706,010`; OHLC untouched — this fixes a prior ~2.79×
dollar-volume inflation, it is a repair, not a new defect), established that as J-11's new certified
raw-input baseline, built and proved (on disposable test data only, never the live app) a fail-closed
guard against booting into an unrepaired incident date, and re-ran Stage D readiness. Headline result:
AVB reclassified **C → B**, and **`J-11 STAGE D READY: YES`** for the first time — but
**`J-11 STAGE D AUTHORIZED: NO`** unconditionally. Nothing about the 11 incident dates' missing derived
data has changed, and Stage D itself has not run. **`READY: YES` is a diagnostic result, not a green
light** — the single most important thing to verify below is that nothing in the app treats it as one.

This guide re-checks that the 10 journeys this iteration is required to keep passing (J-01–J-10) still
work, and adds new checks for what iteration 16 actually touched (J-11). None of these steps have been
run yet; you are the first person to execute them since this iteration completed.

**One safety rule that applies to every step below:** the app currently has 11 "incident dates" with
no fresh derived data behind them yet: `2026-05-12, 2026-05-13, 2026-07-10, 2026-07-13, 2026-07-24,
2026-07-27, 2026-08-03, 2026-08-05, 2026-08-10, 2026-08-11, 2026-08-12`. **Never type one of these into
the `?asof=` part of the URL.** For most of them, doing so creates a permanent data artifact the system
isn't supposed to create yet. This is expected, authorized, mid-repair state — not something to report
as broken.

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running (prod scripts) — note this presumes maintenance isolation has, by the time you run
  this, been legitimately lifted by the owner; as of this writing it is still active, and a guard built
  this iteration to make booting safer has only ever been tested against disposable fixture data, never
  the live app
- No login required
- At least one completed scan session exists (true today — 3,117 stored sessions)

---

## Steps

1. Open `http://localhost:3255/` in your browser (do not add any `?asof=` to the URL)
   - **Expect:** the page loads with six sections top to bottom — a market-state band, a
     plain-English summary, "What changed", "Leadership rotation", "Next-session focus", and a
     manifest strip. The date shown as the current session is **not** one of the 11 dates listed
     above (it was `2026-07-23` when this guide was written — a later date is fine, one of the 11
     listed dates is not, and would mean Stage D ran without authorization).

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
     Counts, Top Themes, and a Market Phase & Severity card — nothing looks missing.

7. Click "Stocks" (or navigate to `http://localhost:3255/stocks`), search for symbol `AVB`, and open
   its stock detail page
   - **Expect:** the page loads without error. If the price/volume chart's date range reaches back to
     `2026-08-11`/`2026-08-12`, those two days' volume bars look consistent with the surrounding week
     — no visible spike about 2.8× the neighboring days' height. If the chart doesn't reach that far
     (e.g. it's scoped to the current session window), that's fine — this check simply doesn't apply
     today.

8. Navigate to `http://localhost:3255/data` and look at the manifest count on the most recent runs
   - **Expect:** still shows 24 manifests total, unchanged — this iteration's AVB correction and new
     certified baseline touch no manifest.

9. Re-read the safety rule near the top of this guide, and confirm two things: you never typed one of
   the 11 incident dates into a URL, and nothing you saw on any page suggested Stage D has already run
   or been authorized
   - **Expect:** no incident date appeared anywhere as a normal, undisclosed session; `READY: YES` (if
     you saw it referenced anywhere, e.g. in an admin/status view) is presented as a diagnostic result,
     never as confirmation that the 11 dates were rebuilt. If you're unsure, reload
     `http://localhost:3255/` with no `?asof=` at all before finishing.

---

## What "Working Correctly" Looks Like

- `/` loads fast, reads like a short honest paragraph plus a few cards — no jargon, no trading
  advice language, no readiness/market vocabulary mixed together.
- AVB's price/volume history (wherever it's visible) shows no anomalous spike around
  `2026-08-11`/`2026-08-12` — the correction is reflected, not flagged as broken.
- The 11 incident dates are simply absent from normal browsing — you never see them offered as a
  normal session, and nowhere does the app act as if Stage D already ran.

## If Something Looks Wrong

- **Blank page / error screen on `/`**: confirm the backend is actually running before assuming a
  regression.
- **One of the 11 incident dates shows up as a normal, undisclosed session anywhere** (a candidate
  list, an as-of picker entry with no "unavailable" label, etc.): this is a real, reportable
  finding — it would mean derived data was regenerated for an incident date before J-11 authorized
  it. Stop and escalate; do not try to "fix" it yourself.
- **Anything implies Stage D already executed, or that `READY: YES` was itself an approval**: this is
  a real, reportable finding — `J-11 STAGE D AUTHORIZED: NO` is unconditional this iteration regardless
  of the readiness outcome. Stop and escalate.
- **AVB's 08-11/08-12 volume still looks spiked (~2.8× neighbors) where visible**: a real finding —
  the correction may not have taken, or a display layer is re-introducing the old figure. Do not
  attempt to "fix" AVB's data yourself; report it.
- **Unassigned sector share is high (back near ~78%) on `/stocks`**: this is a genuine regression of
  J-01 — file it with the specific ticker(s) you spot-checked.
- For anything else, the full test plan
  (`reports/phase-goal-market-compass-iter-16-ui-test-plan.md`, cases `UT-J-01` through `UT-J-11`) has
  the exact, longer steps this quick guide was distilled from.
