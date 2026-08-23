# Phase goal-market-compass-iter-10 — Implementation Summary

**Phase:** goal-market-compass-iter-10
**Date:** 2026-08-23
**Written by:** developer

---

## Features Implemented

- **Pre-reset inventory snapshot**: a new one-off, read-only tool that takes a complete "before"
  picture of the 11 dates affected by the August incident (how many scan results, sector/theme
  scores, and forward-return rows exist for each date, plus the count and fingerprints of any
  decision manifests already on file for those dates). This snapshot is the safety net a future
  cleanup step will be checked against.
- **One frozen "recipe" identity for the eventual cleanup**: a new tool records exactly which
  version of the calculation code and which configuration values are in effect right now, as a
  single fingerprint. When the actual cleanup work happens (a later, separate step), every
  rebuilt date must match this SAME fingerprint — so it's impossible to accidentally rebuild half
  the dates with one version of the logic and the other half with a different version without
  anyone noticing.
- **A documented, honest fix to a database contract question**: the database previously *declared*
  (in code only, not actually enforced) that every decision manifest must always point at a
  scanner run that still exists. That declaration was never actually true in practice, and it
  directly conflicts with the design promise that manifests survive forever even if the
  underlying run is later rebuilt. This is now corrected in the code's documentation and
  declaration — no data was touched, no database file was migrated.

## Changed Behavior

- None. This iteration is entirely new, additive tooling plus a documentation-level correction to
  an internal, non-enforced database declaration. Nothing about how the product looks, responds,
  or computes values for a user changed.

## Backend-Only Items

- `apps/backend/scripts/run_j11_pre_reset_inventory.py` — a command-line tool an operator runs by
  hand; it has no UI. It is intentionally a one-off diagnostic/preparation step, not a
  user-facing feature.

## Incomplete Items

- **This is a deliberate partial slice.** The actual cleanup of the 11 affected dates (clearing
  and rebuilding the derived scan data, repairing missing forward-return rows, refreshing caches,
  and final verification) is explicitly NOT part of this iteration. That work is planned for a
  later iteration, once a single, carefully controlled maintenance window can be scheduled. This
  iteration only builds and proves the safety tooling that later step will depend on.
- No page, screen, or button changed. There is nothing new to click on.

## Config and Environment Changes

- None. No new environment variables, no config.yaml changes, no database schema migration.

## Known Limitations

- The two JSON files this iteration's tool produced
  (`runs/goal-market-compass-iter-10/j11-pre-reset-inventory.json` and
  `.../j11-frozen-identity.json`) are a snapshot of "right now." When the actual cleanup work
  happens in a future iteration, that step must take its OWN fresh snapshot immediately
  beforehand — it cannot simply reuse this iteration's files, since time will have passed and
  the code/config could have changed in between.
- One unrelated, pre-existing internal test (checking for hard-coded numeric constants in three
  calculation files this iteration never touched) was already failing before this iteration
  started and remains failing after. It is not caused by this iteration's changes and is flagged
  for a future cleanup, not fixed here (fixing it would mean editing files outside this
  iteration's assigned scope).
- The database file itself (`apps/backend/data/trendora.db`) was opened only for read-only lookups
  exactly once this iteration; it was proven, with before/after checks, to have received zero
  writes. No live data changed as part of this work.
