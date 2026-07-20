# Phase goal-ops-hardening-iter-4 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-4
**Date:** 2026-07-20
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- When an ordinary "Fetch EOD prices" (or "Fetch + backfill") job lands a new price bar for the
  benchmark index (SPY) dated after the last completed snapshot, operators now see the top-bar status
  badge (visible on every page) switch to a calm, distinct **"Snapshot pending"** message — with a
  plain-language sentence naming the benchmark, the pending date, and the recovery action ("Run a
  backfill or rebuild on Data Manager to produce it.") — instead of the alarming "Backend unavailable"
  message that used to appear in this exact situation. This lets an operator tell "new data landed, the
  snapshot just hasn't caught up yet" apart from "the backend is genuinely down," without guessing.
- Operators can run an everyday "Fetch EOD prices" job for any ordinary stock (i.e., any symbol other
  than the benchmark) without it ever flipping the app-wide status badge at all. Previously, landing a
  new bar for literally any one of the ~590 tracked symbols could trip the badge into "Backend
  unavailable," even though every page was still serving correct, up-to-date information.
- While watching a large "Backfill snapshots" / "Fetch + backfill" job's live progress card on the Data
  Manager page (`/data`), operators can now trust the "updated Ns ago" heartbeat line all the way through
  the job's final wrap-up stretch (after the main scan finishes, while the app is still finishing
  internal bookkeeping) — it keeps advancing instead of freezing, so a perfectly healthy multi-date job
  no longer falsely displays "· possibly stalled" near the end.
- Operators who leave a browser tab open across a backend status change (e.g. Ready → Initializing, or
  into/out of the new "Snapshot pending" state) now see the small "provider", "seed date", and "N
  symbols" badges next to the status pill refresh to current values — previously these mini-badges were
  fetched once when the tab first loaded and never updated again for the life of that tab.

---

## What Changed in the Visible UI

- The top-bar readiness badge (header, every page) gained a 4th possible message, **"Snapshot
  pending"**, shown in a calm accent color with a steady (non-blinking) status dot and a short
  explanatory sentence — visually and textually distinct from the pulsing amber "Initializing…" message
  and the red "Backend unavailable" message.
- On `/data`, a running job's live progress card keeps its "updated Ns ago" heartbeat line fresh for the
  job's entire duration, including the slow final stretch after the main scan completes — previously
  that line could stop advancing partway through the final stretch.
- The small "provider: …", "seed `<date>`", and "N symbols" badges beside the top-bar status pill now
  refresh whenever the status pill's state changes, not only once at page load.

---

## What Old Behavior Changed

- **Top-bar readiness badge:** previously, an ordinary fetch job landing a new price bar for any single
  tracked stock — even one completely unrelated to the app's benchmark index — could flip the whole
  app's status badge to "Backend unavailable," the same message shown for a genuine crash. Now, only the
  benchmark index's (SPY's) own new data can trigger a status change, and it triggers the new calm
  "Snapshot pending" message, not "Backend unavailable." Genuine unavailability (the backend unreachable,
  or a database that has never produced a single scan) still shows "Backend unavailable" exactly as
  before — that message was not softened or hidden.
- **Data Manager job-progress heartbeat:** previously, the "updated Ns ago" line on a large job's live
  card could stop advancing during the last part of the job (after fetching finished, while the app was
  still computing coverage figures and other bookkeeping behind the scenes), making a healthy job look
  stuck. Now it keeps advancing through that entire stretch — this was fixed in two passes within this
  same iteration; the first pass only covered part of that final stretch, and a follow-up pass closed
  the rest. Two very brief, one-time steps inside that same final stretch (a single coverage recompute
  and a one-time price-data preload, each expected to take a second or two) are still not individually
  covered — in practice these are short enough that they should never trip the "possibly stalled"
  threshold on their own, but it means the fix covers "every date processed across the finalize loops,"
  not literally every single internal step.
- **The preflight verdict banner (the GO / DEGRADED / NO-GO strip shown on every page) is unaffected by
  the new badge state** — seeing "Snapshot pending" on the status badge does not, by itself, turn this
  banner to a caution/stop state. This is a deliberate, verified non-effect, not an oversight.

---

## Not Visible Yet

None — every change this iteration is either directly visible (the new "Snapshot pending" badge state)
or made visible through an existing, already-wired display (the job-progress heartbeat, which already
existed on `/data` and is simply now accurate). Unlike some earlier iterations, this one leaves no
backend capability without a matching UI element.
