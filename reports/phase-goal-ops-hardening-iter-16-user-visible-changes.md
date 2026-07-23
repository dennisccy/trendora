# Phase goal-ops-hardening-iter-16 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-16
**Date:** 2026-07-23
**Written by:** ui-impact-analyst

---

## Context

This iteration is genuinely `Frontend Present: yes` — unlike most of this session's recent iterations
(iter-8 through iter-15), which touched zero files under `apps/frontend/`, iter-16 changes two frontend
files (`apps/frontend/lib/api.ts`, `apps/frontend/app/backtest/page.tsx`) alongside the backend
compute-vs-serve split (J-08). Confirmed via `git diff`/`git status`: 14 files changed at the
product/test/reporting level per the dev handoff — 2 frontend, 12 backend/test/reporting (see the
companion UI Surface Map report for the full per-file classification). Every user-visible effect is
confined to ONE existing page's ONE existing section: the "Forward-tested evidence" panel at the bottom of
`/backtest`. No new page, route, or navigation entry was added.

---

## What Users Can Now Do

- On `/backtest`, users can now tell — just by reading the page — whether the "Forward-tested evidence"
  section is showing the fully current version, a labeled last-good version being served while a newer one
  finishes processing in the background, or has never been computed at all for this date. Previously there
  was no way to know this: the page either silently hung during a fresh calculation, or (on a never-warmed
  date) silently showed nothing.
- When the section is showing a prior ("refreshing") version, users can now read exactly when that version
  was generated — a formatted date and time (e.g. `2026-07-23 14:44:52`) — printed right next to the
  refreshing notice.
- When no forward-tested evidence has ever been computed for the date/store being viewed, users now see an
  explicit "Backtest evidence not yet computed" message with guidance to run an ingest, instead of the
  section silently rendering nothing.

---

## What Changed in the Visible UI

- The "Forward-tested evidence" section at the bottom of `/backtest` (rendered by `BacktestResults` in
  `apps/frontend/app/backtest/page.tsx`) now branches into three distinct visual treatments driven by a new
  `evidence_status` value the backend returns, instead of the single previous behavior (render if present,
  otherwise render nothing):
  - **Normal / current ("ready"):** renders exactly as it did before this iteration — no visual change,
    no banner, no empty state.
  - **Refreshing:** a new small warn-toned card (`RefreshingEvidenceBanner`) appears directly ABOVE the
    still-fully-populated evidence section — a spinning icon plus the text "Refreshing — showing the last
    complete evidence," followed by the generation timestamp of the version being shown. The evidence
    numbers below it remain fully visible the whole time (never hidden, never replaced by a loading
    skeleton).
  - **Not yet computed:** the evidence section is replaced by the project's existing dashed-border "empty
    state" card (the same visual pattern already used elsewhere on this same page, e.g. the Scorecard
    section) — icon, title "Backtest evidence not yet computed," and a description explaining that running
    an ingest will populate it. Before this iteration, this case rendered literally nothing
    (`{evidence ? (...) : null}`), with no message at all.
- No new page, route, or navigation link was added — everything happens inside the EXISTING `/backtest`
  page's existing evidence section.
- No new interactive controls were added — no buttons, forms, filters, toggles, or links; this is a
  read-only status disclosure only, matching the phase spec's own framing ("New user actions: none").

---

## What Old Behavior Changed

- **Cold-recompute blocking removed for the current date's view.** Previously, opening `/backtest` for the
  current (latest) date could silently trigger a full recalculation of the forward-tested evidence the
  moment the cached copy was missing or not yet warmed — and per this session's own iter-15 live
  measurement, that recalculation could take on the order of ~179 seconds with no on-screen explanation for
  the delay. As of this iteration, viewing the page NEVER triggers that recalculation on request — the
  evidence section only ever reads numbers that were already computed during the last background data
  ingest.
- **Never-computed store: silent blank → explicit message.** Previously, if evidence for a date had never
  been computed, the section simply rendered nothing, with no indication anything was missing. It now shows
  the explicit "Backtest evidence not yet computed" message described above.
- **Response time during an active background data refresh: much improved, but not fully within budget —
  reported honestly, not smoothed over.** This iteration's own live, operator-supervised measurement
  (`reports/perf-budgets.md`, the "TC-16 ... RESULTS" section, 2026-07-23) found that while a background
  data-ingest job was actively warming a new dataset version (a ~380-second window in the live test),
  `/backtest` still occasionally responded slowly: 11 of 68 sampled loads (7 of 16 sampled while
  "refreshing," 4 of 49 sampled just after the switch back to "ready") exceeded the page's own committed
  ≤1.5-second budget, ranging from 1.615s up to 12.655s at the worst. This is a stored-row database read
  slowed by concurrent write contention, not a live recalculation, and is roughly 14x faster than the
  worst-case pre-fix delay (178.74s) — but it means the page can still occasionally feel slow to load
  specifically WHILE new data is being ingested in the background. Outside that ~380-second ingest window,
  loads were fast and stable (roughly 0.12–0.3 seconds). Whether this residual is acceptable is left as an
  evaluator/owner judgment call by the developer's own handoff — not self-certified here.
- **Historical ("time machine") dates are unaffected.** Viewing a past date via the existing as-of
  time-machine control behaves exactly as before: the first view of a given historical date may still take
  a moment to compute, then is instant on later views. This iteration intentionally left that path
  unchanged (confirmed unaffected by test TC-13).

---

## Not Visible Yet

- This status disclosure (ready / refreshing / not-yet-computed) exists ONLY on `/backtest`'s evidence
  section this iteration. Four other backend-computed views built on similar ingest-time caches — the
  Event Study research view, the Market Phase status, the `/evidence` page's drawdown-expectations panel,
  and the dashboard/Data Manager index-series chart — were explicitly out of scope and show no equivalent
  disclosure; they keep their pre-existing lazy-compute behavior unchanged.
- The same two new fields (`evidence_status`, `evidence_generated_at`) are also returned by the MCP
  `query_backtest` tool, mirroring the endpoint's response exactly — but that is a machine/AI-agent
  interface (used by tools like Claude, not a page in the web app), so there is no on-screen surface for it.
  A person using only the browser only ever sees this disclosure on `/backtest`.
- The one live measurement pass (TC-16) did not exercise the "not yet computed" state live — the date it
  tested already had complete evidence before the pass began, so that state is currently confirmed only by
  automated unit tests, not by a live/browser observation.
- **No one has viewed the new banner or empty-state in an actual browser yet.** Per both the dev and
  frontend handoffs' "Known Issues," the backend services were down for the entire development pass this
  iteration, so the actual rendered appearance (colors, spacing, wording as displayed) has been verified
  only by TypeScript compilation and by reading the code against the design system's existing conventions
  — not by a screenshot or live DOM inspection. This is expected to be closed by the next browser-qa pass
  (see the companion UI Surface Map's "What to Test" entries).
