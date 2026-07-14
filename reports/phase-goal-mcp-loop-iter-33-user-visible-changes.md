# Phase goal-mcp-loop-iter-33 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-33
**Date:** 2026-07-14
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now tell at a glance, on every single page of the app (Dashboard, Stocks, any stock's detail
  page, Watchlist, Evidence, Research and its sub-pages, Sectors, Themes, Backtest, Data, Methodology,
  Scanner Runs), whether today's board is safe to rely on — a small status strip near the top of every
  page now carries one shared verdict: `GO`, `DEGRADED`, or `NO-GO`.
- Users can now read the specific, plain-English reason(s) behind a `DEGRADED` or `NO-GO` verdict (for
  example, "Latest data (...) is 6 trading day(s) old, exceeding the configured maximum of 5 day(s).")
  instead of having to guess why something might be wrong.
- Users can now recognize a serious "don't trust this" situation unmistakably — the `NO-GO` banner is
  always red, full-width, and always contains the exact sentence "do not rely on today's board."
- There are no new buttons, forms, or clickable actions to learn — the new banner is read-only status
  information; it doesn't need to be discovered or operated, it is simply present on every page.

---

## What Changed in the Visible UI

- Every page now shows a new status strip directly below the header and above the page's own content
  (mounted once in the shared app shell, so it looks and behaves identically everywhere).
- On a healthy day, the strip is quiet and small: a thin line reading "GO — today's board is current."
  with a small green dot — deliberately unobtrusive so it doesn't distract on a normal day.
- When something needs attention, the SAME strip becomes a loud, full-width amber banner with the bold
  headline "DEGRADED — treat today's board with caution." followed by a bulleted list of the concrete
  reason(s).
- When something serious is wrong, the strip becomes a loud, full-width red banner with the bold headline
  "NO-GO — do not rely on today's board." followed by a bulleted list of the concrete reason(s).
- Before the very first status check finishes loading, the strip shows a neutral gray placeholder reading
  "Checking board status…" rather than guessing or defaulting to a green "all clear."
- If the backend itself cannot be reached at all, the strip still renders (the page does not go blank) —
  it shows the same red treatment as NO-GO, with the reason "Backend is unavailable — the preflight check
  could not run."

---

## What Old Behavior Changed

- None of the existing header status indicator's behavior changed (the small "readiness badge" next to
  the as-of date switcher still shows the same Ready / Initializing / Unavailable states it always did).
  This phase adds the new strip as a separate, additional element beneath the header — it does not
  replace or alter anything that was already there, and the underlying `GET /api/health` response keeps
  every field it had before, unchanged.
- On a DEGRADED or NO-GO day, every page now has slightly less vertical space for its own content,
  because the loud banner variant is taller than the quiet GO strip. On a normal (GO) day the space taken
  is minimal. This is a deliberate, spec-required design (the banner is meant to be attention-grabbing
  when something is wrong), not a defect — but it does mean page content now starts a little lower than
  before, and shifts further down on a DEGRADED/NO-GO day.

---

## Not Visible Yet

- The backend now computes and serves a detailed breakdown of each individual check (whether the backend
  is serving data, whether the data is fresh, whether the underlying record-keeping files are intact —
  each with its own ok/severity/detail), but the banner only shows the combined, flattened list of reasons
  for whichever checks failed. There is no UI element that displays the three checks' individual status.
- The backend now also serves the specific reference date used to judge data freshness, but this date is
  not shown anywhere on any page.
- The backend now keeps a small log file recording every time the verdict actually changed (for example,
  from GO to DEGRADED), but there is no page in the product to view this history — it exists purely as a
  backend record for now (intended to feed a future "digest" capability).
- Three additional input signals planned for a future iteration (an anomaly-detector check, a "did live
  data quietly drift from what was validated" check, and a "replay as of a past date" check) are not built
  yet, so the banner cannot yet reflect any of those specific problem types — only the three inputs
  described above (servability, freshness, record-keeping integrity) currently feed it.
