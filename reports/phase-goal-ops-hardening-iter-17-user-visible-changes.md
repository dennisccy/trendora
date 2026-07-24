# Phase goal-ops-hardening-iter-17 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-17
**Date:** 2026-07-24
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On `/backtest`, when the latest trading day has just landed and its behind-the-scenes forward-aggregate
  computation hasn't finished yet (the single most common daily data-update shape), users now see
  yesterday's real, labeled numbers with a small "Refreshing" notice — instead of the evidence section
  going blank with a "not yet computed" message. This is the load-bearing fix this iteration ships.
- From the "Refreshing" banner's own text, a user can now tell **which date's** evidence is on screen
  ("evidence as of `<date>`"), not only when it was generated. A user can compare that date against the
  "Viewing as-of `<date>`" badge near the top of the same page and see directly how stale the shown numbers
  are — previously the banner gave no way to know this.
- When the "Backtest evidence not yet computed" empty state does appear (now reserved for a genuinely
  brand-new, never-used database), its wording no longer tells the user to "run an ingest" — phrasing that
  could previously read as though the user hadn't already started one, even when they had.

---

## What Changed in the Visible UI

- The `/backtest` "Refreshing — showing the last complete evidence" banner text changed from "...the last
  complete version, generated `<timestamp>`..." to "...the last complete version — evidence as of
  `<date>`, generated `<timestamp>`..." — a new as-of date is now named before the generation time.
- The "Backtest evidence not yet computed" empty-state description changed from "Backtest evidence not yet
  computed — run an ingest to populate the forward-tested evidence for this date. No numbers are
  fabricated in the meantime." to "No forward-tested evidence exists yet for this date. Backfilling or
  fetching data that covers it will compute this evidence — no numbers are fabricated in the meantime."
  The title above it, "Backtest evidence not yet computed," is unchanged.
- The empty state itself now shows up far less often: previously it could appear briefly every time a new
  trading day's data landed, while the forward-aggregate warm caught up. That same moment now shows the
  populated evidence section plus the Refreshing banner instead, so most users may never see the empty
  state at all during normal day-to-day use.

---

## What Old Behavior Changed

- **The "Backtest evidence not yet computed" empty state**: previously triggered any time the
  currently-viewed date's own evidence was incomplete, even when an older date's evidence was complete and
  could have been shown instead. Now it is reserved for the case where NO date has ever had complete
  evidence (a truly fresh, never-ingested database) — every other "current date still catching up" case
  now falls back to the Refreshing banner with a labeled older date's numbers instead of going empty.
- **Revisiting an already-viewed historical date on `/backtest`** is very slightly faster behind the
  scenes — a duplicate internal re-read of the same stored data was removed. The numbers shown are
  unchanged (byte-identical); this is not something a user would be able to perceive or measure by eye.

---

## Not Visible Yet

- **The new "evidence as of `<date>`" banner text for the cross-date fallback has not been captured live
  in a browser this iteration.** The working database currently has no trading day beyond 2026-07-22 to
  advance into (there is no future price data to backfill, by design — this project never makes live
  external data calls), so the exact scenario the fix targets could not be produced end-to-end through the
  UI this session. It is verified today by 5 passing backend unit tests and a clean type-check of the new
  banner prop, not yet by a screenshot. The next real daily data update that lands a new latest trading day
  will be the first live opportunity to see this render.
- **The "Backtest evidence not yet computed" empty state WAS captured live**, but only against a
  disposable, throwaway backend/frontend pair on alternate ports pointed at a never-used database copy —
  never against the main application most users actually visit.
- **The same `evidence_asof` value is also served, identically, through the `query_backtest` tool used by
  connected AI-agent/MCP clients** (a separate interface from this web app, used by tools like an AI
  assistant querying the data directly). This is not a browser page and has no in-app screen of its own —
  it is a parallel channel that already works, not an unfinished or hidden one.
- **The intermittent slow page loads of `/backtest` during data updates (previously measured at roughly 1
  in 6 loads, several seconds instead of under 1.5) were investigated but not fixed this iteration** — no
  code changed as a result, so this behavior is unchanged and not yet re-measured. There is no new
  indicator anywhere in the UI for this; the page still always loads correctly, just occasionally slower
  during an active data update.
