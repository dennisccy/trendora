# Phase goal-ops-hardening-iter-47 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-47
**Date:** 2026-08-04
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On the **Evidence** page (`/evidence`), users can now tell when a claim's "Historical drawdown & dry-spell
  expectations" table is showing a moment-behind (but real, honest) version of the data instead of the
  current one — a small amber **"Refreshing"** badge appears next to that panel's heading whenever this is
  the case, with an added sentence explaining that a newer version is computing in the background. This is
  new information disclosed on an existing page, not a new action.
- Users can now reliably open `/evidence` immediately after any data update (a backfill, a rebuild) and get
  a fast response every time. Previously, the FIRST request to `/evidence` after ANY unrelated data change
  anywhere in the system could hang for well over two and a half minutes (longer under a concurrently
  running ingest) while the server recomputed every claim's history from scratch. That failure mode is
  closed — this iteration does not add a click-able feature, but it removes a real, previously-observed
  path to the page appearing broken/frozen.

---

## What Changed in the Visible UI

- The Evidence page's per-claim **"Historical drawdown & dry-spell expectations"** panel (inside each
  certified-claim card) gains one additive element: a `Badge` (amber "warn" style, same visual treatment
  already used elsewhere on this page) reading **"Refreshing"**, positioned next to the panel's heading —
  shown ONLY while that specific claim's table is serving its previous generation.
- The same panel's descriptive paragraph gains one additional sentence, shown only alongside the badge:
  *"A newer version is computing in the background after a recent data update — the table below is the
  last complete version, not a partial or fabricated one."*
- No other visible element changed. The table's columns, row layout, other claim-card fields (verdict
  badge, hypothesis chips, registration date, etc.), and the panel's two other pre-existing states
  ("ready" with no badge, and "Unavailable — monitored and refreshed as new data arrives") render exactly
  as before.

---

## What Old Behavior Changed

- **Evidence page reliability after a data update**: previously, the first `/evidence` request after any
  new `forward_returns` row landed anywhere in the database — even for a claim completely unrelated to
  what changed — could fall onto a multi-minute cold recompute for every one of the page's 7 claim panels.
  Now the page always answers quickly; if a fresher generation is still catching up in the background, the
  page says so plainly (see "Refreshing" badge above) instead of either hanging or silently showing data
  that might be a moment stale with no indication.
- **No behavior change to what values are shown**: every figure in the drawdown/dry-spell table — median,
  p90, sample size, loss-streak counts — is unchanged in how it is computed; the only change is WHEN a
  slightly older (but never wrong or mixed-generation) version might be shown, and that it is now labeled
  honestly when it is.

---

## Not Visible Yet

None. Every backend change in this iteration either has a corresponding UI disclosure (the "Refreshing"
badge above) or is a purely internal performance/robustness fix with no user-facing state to expose:
- A memory-usage bound on one of the Evidence page's underlying calculations (`samples.py`'s
  decile-cohort resolver) — produces byte-identical numbers, just uses less memory. Nothing for a user to
  see or do differently.
- A database-query narrowing on the same page's drawdown-history lookup (`_drawdown_ticker_slice_map`) —
  reads far fewer rows for the same byte-identical answer.
- A logging robustness fix in the background boot-time warm-up routine (`warmup.py`) — affects only
  server log entries during a severe-memory-pressure edge case, never anything a user would encounter in
  the UI.
