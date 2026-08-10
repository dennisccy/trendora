# Phase goal-ops-hardening-iter-57 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-57
**Date:** 2026-08-10
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now trust the `/data` page's per-date availability heatmap during an active Fetch/Backfill/rebuild
  job: it keeps showing the real, previously-computed chart (colored day cells) instead of falsely claiming
  "No availability yet — Fetch real EOD prices" for the job's entire ~20-minute duration.
- Users can now see an honest "Data as of `<version>` — updating" notice on that same heatmap whenever the
  chart they are looking at is a moment behind the very latest ingest (i.e., a job is mid-flight and hasn't
  finished its finalize step yet) — so they know the numbers are real but not the newest possible.
- Users benefit from the global "Ready" status badge (visible in the header on every page) updating roughly
  10x faster at rest (about 10-15ms instead of 160-241ms) — no visible difference in what it says, just how
  quickly it settles.
- Users benefit from the Stock Detail page's price chart (with its moving-average lines) rendering faster,
  especially for stocks with long price histories, because a hidden inefficiency in the moving-average
  calculation was fixed.

No new buttons, forms, or navigation entries were added this iteration — this is a passive display-honesty
fix plus two backend speed fixes to calls the UI already made.

---

## What Changed in the Visible UI

- The `AvailabilityHeatmap` component on `/data` gained one new conditional banner: a calm text row reading
  "Data as of `<served_dataset_version>` — updating" (`data-testid="availability-stale-notice"`), rendered
  directly above the calendar grid. It only appears when the backend reports `stale: true`; the grid itself
  is unchanged, and the banner uses the exact same visual treatment (border, background, text size/color) as
  the page's existing "Coverage as of a prior scan" notice on the Dataset Coverage panel below it, so it
  reads as part of the same established "as-of" pattern rather than a new visual style or an error/alarm.
- No layout change: the heatmap card keeps its current position on `/data`, no new card/dialog/section was
  added.

---

## What Old Behavior Changed

- **Availability heatmap during a job:** previously, for the entire duration of any Fetch/Backfill/rebuild
  job, the heatmap showed the empty "No availability yet — Fetch real EOD prices" message even though the
  database already held millions of real price rows. Now it shows the real, most-recent chart plus the
  "updating" banner instead. The empty-state message itself is unchanged in wording/appearance and is now
  reserved strictly for a database that has genuinely never completed an ingest.
- **Global "Ready" status badge (header, every page):** previously took 160-241ms to answer at rest; now
  answers in about 10-15ms. Same states ("Checking backend…", "Ready", "Initializing…", "Snapshot pending",
  "Unavailable"), same wording — only the wait is shorter.
- **Stock Detail price chart (`/stocks/{ticker}`):** the underlying `bars?through=latest` call is
  substantially faster (was measured at 6.2s in a prior round; now well under 1.5s), especially noticeable
  on stocks with a long price history. The chart's numbers — bar count, as-of date, the moving-average lines
  themselves — are unchanged; only the wait before they appear is shorter.
- **Job history "Refreshed: …" note (`/data`, under a completed job's row):** in the rare case where a
  background aggregate save silently fails partway through a job (a database commit that has to roll back),
  this note will no longer claim the aggregate was refreshed. Previously it always said "Refreshed" even on
  that failure path; now it honestly omits the aggregate from that list. A normal, successful job's
  "Refreshed: …" note is completely unaffected — this only changes what happens in the rare failure case,
  and that case cannot be triggered through normal use of the UI.

---

## Not Visible Yet

- The MCP `list_runs` tool (used only by AI-assistant/agent integrations that talk to this project via MCP,
  not by the web UI) now runs a faster grouped database query instead of a per-run loop — same numbers,
  faster — but this has no web UI surface at all; there is no page or button in the product that calls it.
- The corrected calendar-span note in `reports/perf-budgets.md` and the new `docs/test-infra-tickets.md`
  ticket are internal project records for developers/reviewers, not part of the product UI.
