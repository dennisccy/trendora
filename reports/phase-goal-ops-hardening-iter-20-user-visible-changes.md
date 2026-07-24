# Phase goal-ops-hardening-iter-20 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-20
**Date:** 2026-07-24
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open **any** historical `/backtest` as-of date — including one nobody has ever viewed
  before — and get back a responsive page almost immediately (operator-measured **0.082 s** first response
  for a never-before-viewed date, `reports/perf-budgets.md` "Iteration 20"), instead of a browser tab that
  sat blank and unresponsive for as long as **9.6–54 seconds** with no loading indicator at all. This is not
  a brand-new feature — the historical "time-travel" capability on `/backtest` already existed (iter-14/17/18)
  — but a first-ever view of an ungenerated date was previously unusable in practice; this iteration is what
  makes it practically usable.
- On that same first view, users now see an honest "this is being computed" message right away — either the
  `RefreshingEvidenceBanner` (an older, labeled, complete evidence set shown while the requested date's own
  numbers finish) or the "Backtest evidence not yet computed" empty state — where before they saw nothing at
  all until the page eventually returned.
- Reloading the same historical URL roughly 30 seconds later (per the operator's live re-measurement) now
  shows that date's own real, per-horizon evidence (`evidence_status: "ready"`) — the same numbers a direct
  computation would have produced, just delivered on a later view instead of blocking the first one.

---

## What Changed in the Visible UI

- The `RefreshingEvidenceBanner` on `/backtest` now reads differently depending on whether you're viewing
  today's (latest) date or a historical one:
  - **Latest-date view (unchanged):** "The dataset has changed since this evidence was generated, and the
    newer version is not complete yet. ... Reload this page after the next ingest finishes to pick up the
    new version."
  - **Historical-date view (corrected this iteration):** "This date's own evidence is being computed in the
    background (started by viewing this page) and is not complete yet. ... Reload this page shortly to pick
    up this date's own evidence once the background compute finishes."
- The "Backtest evidence not yet computed" empty-state description also now differs by view:
  - **Latest-date view (unchanged, byte-identical to the iter-17 wording):** "No forward-tested evidence
    exists yet for this date. Backfilling or fetching data that covers it will compute this evidence — no
    numbers are fabricated in the meantime."
  - **Historical-date view (new this iteration):** "No forward-tested evidence exists yet for this date.
    Viewing this page has started computing it in the background — reload shortly to see it. No numbers are
    fabricated in the meantime."
- A first-ever view of a not-yet-computed historical date now finishes loading in a fraction of a second
  (operator-measured) instead of taking anywhere from several seconds up to nearly a minute.
- No new page, panel, button, field, or navigation entry was added — same `/backtest` route, same two
  pre-existing components (both first shipped iter-16/17), same three-state `evidence_status` contract
  (`ready` / `refreshing` / `not_yet_computed`) exactly as before.

---

## What Old Behavior Changed

- **First-ever view of a not-yet-computed historical `/backtest` date:** previously, the server computed
  that date's forward-tested evidence WHILE the browser waited for the HTTP response to come back — measured
  at 9.6 to 54 seconds across concurrent first-touch requests in the prior iteration's own live
  instrumentation, with literally nothing rendered the entire time (no spinner, no message — the request
  itself had not yet returned). Now the same request returns in about 0.082 s showing an honest interim
  state, the compute continues quietly in the background, and a reload roughly 30 seconds later shows the
  real numbers. The default (today's/latest) view is completely unaffected — it never reached this slow code
  path before, and does not reach the new mechanism either.
- **The `RefreshingEvidenceBanner`'s explanation of WHY evidence is incomplete, for a historical date
  specifically:** previously always said "the dataset has changed... reload after the next ingest finishes"
  — inaccurate for a historical view, where no ingest is necessarily involved at all (viewing the date is
  what starts its compute). This sentence is now corrected for historical views only; the latest-view
  wording, where the ingest explanation genuinely is accurate, is untouched.
- **The "Backtest evidence not yet computed" empty state, for a historical date specifically:** previously
  credited only "backfilling or fetching data" with starting a compute. For a historical view, viewing the
  page itself now also starts one, and the copy is corrected to say so. The latest-view wording is unchanged
  (still accurate there, since the latest branch never triggers a background compute itself).
- **Honest residual, not fully eliminated by this iteration** (operator-measured, `reports/perf-budgets.md`
  "Iteration 20"): while a triggered background compute is running (roughly a 30-second window), another
  `/backtest` request issued during that window — a second tab, a different date, another user — can see
  transient latency of 3.0–6.3 seconds instead of the normal sub-second response, from in-process compute
  resource contention, not a return of the old request-path recompute. This is far better than the prior
  9.6–54 s block and never a service outage: `GET /api/health` (the app's own readiness signal) kept
  returning HTTP 200/`"ready"` throughout every sampled check during the same window, even though its own
  response time also rose briefly (up to 1.60 s) under the same contention — so no user would ever see a
  "service unavailable" state, only an occasional slower `/backtest` load.

---

## Not Visible Yet

- **No live browser render of either corrected message has been captured this session.** The phase spec
  (TC-12) and both the dev and frontend handoffs draw an explicit line here: the *latency* claim (an operator
  `curl`/log capture of the timing fields, recorded in `reports/perf-budgets.md`) is an accepted stand-in for
  a live browser timing check, but the *rendered-copy* claim — whether `RefreshingEvidenceBanner` and the
  empty state actually display the corrected sentences above — still needs a live browser view that has not
  run yet. Treat the copy-change bullets above as "true per the code" (a clean TypeScript compile plus a
  manual trace against the exact backend condition each sentence corresponds to), not yet "confirmed on
  screen."
- **There is no live progress indicator or automatic refresh.** The page refetches only on mount, an as-of
  change, or a readiness transition — there is no polling. A user must manually reload the page to find out
  whether the background compute has finished; the banner/empty-state text says "reload shortly," but
  nothing on the page counts down, shows a percentage, or refreshes itself.
- **The identical fix is also live in the MCP `query_backtest` tool** (used by non-browser, agent/tool
  integrations rather than this Next.js web app). Those consumers get the same fast, honest response instead
  of a stalled call — but this is not a browser page and has no on-screen surface of its own in this
  application; nothing changes in the web UI beyond what is described above.
