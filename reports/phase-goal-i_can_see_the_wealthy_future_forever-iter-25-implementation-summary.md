# goal-i_can_see_the_wealthy_future_forever-iter-25 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-25
**Date:** 2026-06-09
**Written by:** developer

---

## Features Implemented

- **Missing-data diagnostic (J-37)**: The Data Manager now tells you, in plain language, which scored
  universe members are insufficient for analysis — split into three honest categories: members with no
  stored history, members with too little history ("thin"), and members with internal gaps inside their
  own date range. Each entry names the symbol and the exact shortfall (how many bars it has vs needs, or
  how many trading days are missing and over what span). A member that is fine is not listed.

- **One-click "Pull the missing data" (J-37)**: Each fixable diagnostic entry has a button that fetches
  EXACTLY the missing data for that one symbol over exactly its gap — not the whole universe, not the whole
  window. A "Pull all missing" button does this for every fixable entry in turn. The fetch reuses the same
  rate-limit-aware import machinery as the normal fetch, so re-pulling never duplicates data, and a
  provider failure shows an explicit error rather than inventing prices.

- **Unified Unfinished-imports panel (J-38)**: Every import that did not finish cleanly now appears in one
  place — paused (rate-limited), partial (some symbols failed), or fully failed — each with a plain-language
  explanation (e.g. "Paused — hit a provider rate-limit (429); progress saved", "Partial — 149/158 symbols
  ok, 9 failed", "Failed — every symbol failed; provider unreachable") plus done/remaining/failed counts.

- **Resume / Retry / Remove actions (J-38)**: Each unfinished import shows the right action — Resume a
  paused import (continues from where it stopped), Retry a partial/failed run (re-fetches only the
  outstanding work, never duplicating data), or Remove/Dismiss a stuck record. Remove/Dismiss only drops
  the actionable job-control record; it never deletes the permanent run-history audit entry, any scanner
  snapshot, or any forward-return result.

---

## Changed Behavior

- **"Resumable imports" panel → "Unfinished imports" panel**: The page previously listed only paused
  (resumable) imports. It now lists ALL unfinished imports (paused + partial + failed) in one unified
  panel, each with a plain-language state and the appropriate action. The underlying paused-imports data is
  still served by the API unchanged.

- **Dataset coverage payload**: The `GET /api/data` response now also carries the missing-data diagnostic
  (under coverage) and the unified unfinished-imports list. The coverage figures themselves (universe
  count, symbol count, gaps, per-symbol table) are unchanged.

---

## Backend-Only Items

- None — every backend capability added this iteration (diagnostic, pull-missing, unfinished-imports list,
  retry, dismiss) is wired into the `/data` UI.

---

## Incomplete Items

- **J-39 and J-35 re-capture**: No code change was needed for these (they are built and integration-proven).
  This iteration only requires re-capturing their browser flows on a clean hydrated build — that is the
  QA/browser gate's job, not a code task.

---

## Config and Environment Changes

- No new environment variables. No `config.yaml` changes (the diagnostic reads the existing
  `indicators.min_history_bars` threshold and the existing benchmark trading calendar; the pull/retry reuse
  the existing import-source catalog).
- **Schema (additive, no regen)**: a `dismissed` flag column was added to the existing data-provider-runs
  table to support soft-dismiss. There is no Alembic in this project, so startup now performs an additive,
  idempotent in-place column backfill — an existing database gains the column without being regenerated,
  and existing rows default to not-dismissed.

---

## Known Limitations

- On this host every scored universe member already has enough history and no gaps, so the live diagnostic
  is empty (the honest healthy state). The three categories were exercised against fixtures in unit tests
  and are rendered by the UI; a host with thin/missing/gapped members will populate them.

- A real successful live pull or retry over a needs-key or rate-limited provider is data-gated and
  non-blocking (Yahoo rate-limits this IP; keyed providers need a key). The offline behavior is fully
  proven in tests, and any provider failure surfaces an explicit error / rate-limited state and fabricates
  nothing.

- The live market-cap universe expansion (J-22/J-35 live) remains externally data-walled and is recorded
  honestly as not-available / non-halting, per the project goal's carve-out — it does not block this
  iteration.
