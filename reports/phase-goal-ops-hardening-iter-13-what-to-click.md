# Phase goal-ops-hardening-iter-13 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-13
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`, backend at `http://localhost:8255`
- No login required
- Backend has completed at least one ingest run so the new index-series cache is warmed (ask the
  operator running this session to confirm, or just check that `/data` loads data at all in step 1)
- Chrome DevTools available (this phase is a pure loading-speed fix — you need the Network tab to
  see the improvement)

---

## Verification Steps

1. Open Chrome DevTools (F12), go to the **Network** tab, and check **"Disable cache."** Then, in
   a **new tab**, navigate to `http://localhost:3255/data`
   - **Expect:** Page loads with no blank screen and no error overlay. A card titled "Index &
     benchmark data provenance" appears with a populated table of index/benchmark symbols.

2. In the Network tab, find the request row named `indexes?full=true` and read its **Time** column
   - **Expect:** The value is **1500ms or less**. (This is the exact request this whole iteration
     was built to speed up — it previously measured 2100–2300ms.)
   - **Broken looks like:** the Time value is 1500ms or higher, or the request never appears in
     the list at all.

3. Close that tab completely, open a fresh new tab, and repeat step 1–2 two more times (three
   total fresh loads of `/data`)
   - **Expect:** All three readings of `indexes?full=true`'s Time column are ≤1500ms.
   - **Broken looks like:** any one of the three readings is ≥1500ms — even one slow reading means
     this phase's fix is not yet confirmed working for a real user.

4. Open one more new tab (cache still disabled) and navigate to `http://localhost:3255/`
   - **Expect:** The "Major indexes & regime" card loads with visible chart lines within a couple
     of seconds; in the Network tab, `indexes?full=true`'s Time column also reads **≤1500ms**.

5. On that same Dashboard page, click the range dropdown in the top-right of the "Major indexes &
   regime" card (it shows "All" by default) and select **"3M"**
   - **Expect:** The chart re-draws showing a visibly shorter time window (roughly the last 3
     months instead of the whole history). No error message appears.
   - **Broken looks like:** the chart goes blank, shows an error box, or does not change at all
     after selecting "3M" — this would mean the fix broke the older, unrelated range-selector path.

6. Back on `/data`, scroll down and read every row of the "Index & benchmark data provenance"
   table
   - **Expect:** Each row shows a symbol, a vendor (Stooq / Yahoo / FRED-macro proxy, or an honest
     "—" if none), and a first-bar date — the same data you'd expect from before this change, just
     loaded faster. Nothing looks blank, garbled, or duplicated.

7. (Optional, if you want to see this phase's one new bit of text) In the "Start a fetch /
   backfill job" card on `/data`, type a start date and a later end date, choose **"Fetch EOD
   prices"** from the "Job kind" dropdown, and click **"Start"**
   - **Expect:** Once the job finishes, the "Job progress" panel's "Refreshed: ..." line may now
     include the phrase **"index series"** among its comma-separated items — but only if that
     fetch actually landed a new price bar for one of the 10 index-chart symbols (SPY, QQQ, IWM,
     RSP, DIA, ^SPX, ^NDX, ^DJI, ^VIX, ^TNX). If it didn't touch one of those symbols, "index
     series" correctly does NOT appear — that's expected, not a bug.

---

## What "Working Correctly" Looks Like

- All Network-tab Time readings for `GET /api/indexes?full=true` — on both `/` and three fresh
  `/data` loads — are ≤1500ms
- Both pages show the same chart lines, table rows, and values you'd see from before this fix —
  only faster
- The "3M" range selector on `/` still works exactly as before

## Common Issues

- **`indexes?full=true` still reads ≥1500ms**: this phase's fix is not confirmed working yet —
  report this plainly; do not round it into "close enough." Check that the backend was actually
  restarted after this iteration's code changes (ask the operator) and that an ingest run has
  completed to warm the new cache.
- **Blank page / error overlay on `/` or `/data`**: check the backend is running
  (`curl http://localhost:8255/health`) and reachable from the frontend.
- **"Index & benchmark data provenance" table never leaves its gray loading skeleton**: the
  `indexes?full=true` call may be failing — check the DevTools Console and Network tab for a
  red/failed request.
