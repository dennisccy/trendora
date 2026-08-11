# Phase goal-ops-hardening-iter-61 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-61
**Date:** 2026-08-11
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None. This iteration adds no new capability — it repairs an already-shipped display path
(`/data`'s coverage counts) and captures missing evidence for an already-shipped indicator
(Regime Lab's "Unavailable" chip). See "What Old Behavior Changed" below for the one thing
that IS different for a user.

---

## What Changed in the Visible UI

None. No new page, component, label, field, button, or navigation entry was added. The
Data Manager (`/data`) coverage panel — "Snapshot dates", "Backfill gaps", and the other
`DefinedMetric` stat tiles — renders with the exact same labels, layout, and definitions as
before this iteration. The Regime Lab (`/research/regime-lab`) page and its sample-size
chips are visually unchanged (the "Unavailable" indicator itself was already shipped in
iteration 60; this iteration only produced the first opened, inspected screenshot proving
it renders correctly).

---

## What Old Behavior Changed

- **Data Manager (`/data`) coverage panel auto-refresh.** Previously, the "Snapshot dates"
  and "Backfill gaps" figures (and the rest of the coverage panel) only re-fetched when the
  page first loaded, or when a job **this same browser tab had started** finished. If a
  backfill or fetch job was started somewhere else — another tab, a script, a teammate's
  session — an already-open or later-opened `/data` tab kept showing the numbers from
  before that job, indefinitely, until the user manually reloaded the page. Now `/data`
  also silently re-checks and refreshes the coverage/availability numbers on its own, at
  least once every ~30 seconds, regardless of who or what triggered the underlying data
  change. A user who leaves `/data` open while a colleague or automation runs a backfill
  will now see the counts catch up within about half a minute instead of staying stale.

---

## Not Visible Yet

- The Regime Lab's "Unavailable" degrade indicator (grey triangle icon + "Unavailable"
  text, replacing a clickable `n=...` sample-size chip) only appears when the backend is
  deliberately relaunched with a memory-pressure fault-injection flag
  (`TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab`) for testing purposes. A user on a
  normal, healthy backend will not see this state in day-to-day use — it exists to prove
  the app degrades gracefully rather than crashing when memory pressure forces a cell's
  computation to be skipped.
- A separate, pre-existing backend defect was found during this iteration's
  investigation but was **not fixed** (out of scope): `GET /api/health`'s `last_run_date`
  field always reports "no scanner run" even though thousands of runs exist in the
  database. Nothing in the current UI reads this field, so it causes no visible problem
  today — it is recorded for a future iteration to pick up.
- The J-07 owner question (whether the app's 2-second health-check promise should apply to
  an 18–23 minute background job, or only to the ~30-second job it was originally written
  for) remains open and unanswered for an 11th consecutive round. This iteration only
  re-measured and honestly wrote up the current numbers (a real ~17-minute backfill: 100%
  of health-check polls answered, 1 of 1078 polls slightly over the relaxed 2-second
  ceiling) — it does not change any user-facing behavior related to that promise.
