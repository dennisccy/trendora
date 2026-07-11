# goal-mcp-loop-iter-27 — Implementation Summary

**Phase:** goal-mcp-loop-iter-27
**Date:** 2026-07-11
**Written by:** developer (fix-mode, second pass — resolves the audit FAIL)

---

## Features Implemented

This iteration adds no new user-facing feature. It **stops the backend from crashing** when an operator runs
the "Rebuild snapshots" job on the full data set more than once without restarting.

- **Crash-proof repeated full-universe rebuilds**: the Data Manager's "Rebuild snapshots for current
  universe" job can now be run twice (or more) in a row on a running backend without exhausting the
  process's memory and freezing the service. Previously the *second* rebuild in a row locked up the backend.

---

## Changed Behavior

- **"Rebuild snapshots" job (the `/data` page's rebuild action)**: Previously, running it a second time in
  the same running backend drove memory to the hard ceiling and the backend stopped responding to every page
  and API (a `MemoryError` freeze). Now two consecutive rebuilds each finish successfully, produce identical
  results, and the backend and every page stay responsive throughout — with a comfortable ~18% memory
  headroom, versus the near-zero headroom that used to trigger the crash.
- The numbers each rebuild produces are **exactly the same as before** (verified bit-for-bit): this change
  only affects how memory is managed, never any score, ranking, snapshot, or forward-return value.

---

## Backend-Only Items

- None. This is an internal memory-management hardening of an existing job; there is no new endpoint, model,
  or value to wire to the UI. The `/data` rebuild button, its progress display, and every other page are
  unchanged.

---

## Incomplete Items

- **Final "resolved" confirmation for the memory anti-goal** is pending the automated browser test lane
  (browser-qa), which re-drives the rebuild through the real `/data` page. The developer verification here
  drove the identical job twice against a live backend at the HTTP level and it passed cleanly; the browser
  lane is the contract's final authority and runs as a later pipeline step.
- Two smaller, pre-existing items the audit flagged as non-blocking were intentionally **left for a future
  iteration** (to keep this fix's change small and easy to review): (1) a config-validation guard for two
  breadth moving-average settings, and (2) a UI safeguard that discourages clicking "Rebuild" twice plus a
  page-side timeout so a frozen backend shows the "Backend unavailable" card instead of a perpetual
  "Checking backend…" spinner.

---

## Config and Environment Changes

- **`server.malloc_arena_max`** (new setting in `config.yaml`, default: **2**) — controls the
  `MALLOC_ARENA_MAX` value the backend start script (`scripts/start-backend.sh`) applies to the backend
  process. It caps how many separate memory pools the system allocator creates; on this 16-core host the
  default (up to 128 pools) is what let repeated heavy jobs fragment memory and pin the ceiling. An operator
  can override it with the `CHAIN_SERVER_MALLOC_ARENA_MAX` environment variable. It only affects the
  allocator layout — no data or behavior change.
- No database migration and no schema change.
- No secrets, credentials, or `.env` changes.

---

## Known Limitations

- **Memory headroom is comfortable but finite (~18%, about 1.1 GB under the cap).** Two consecutive
  full-universe rebuilds were verified to stay well under the limit and the second run does not use more than
  the first. If the data set later grows substantially deeper/wider, that headroom would need re-checking;
  the next available levers (not needed today) are a tighter allocator cap and a smaller bar pre-load set.
- **The fix is verified on the production-style backend launcher (`start-backend.sh`), not the local
  developer launcher (`dev.sh`).** The local dev launcher runs without the memory cap, so it never hit this
  crash; the automated QA/production path uses `start-backend.sh`, which carries the fix.
- The definitive "the crash is gone" sign-off comes from the browser-QA lane re-running the rebuild on the
  live `/data` page (plus re-checking the other core journeys that were blocked behind last iteration's
  outage). This summary reports a strong live HTTP-level pass, not that lane's verdict.
