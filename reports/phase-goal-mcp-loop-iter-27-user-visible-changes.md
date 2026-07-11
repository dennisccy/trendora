# Phase goal-mcp-loop-iter-27 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-27
**Date:** 2026-07-11
**Written by:** ui-impact-analyst

---

## Summary

This iteration is a **de-regression / memory-hardening pass**, not a feature iteration. No frontend
source file changed — `git diff` against `apps/frontend/` is empty. Every changed file is backend engine
code, backend config, the backend launch script, tests, or a perf report. The plan and phase spec both
say so explicitly: "New user-facing capability: none... this is a de-regression, not a new capability."

Two dev passes were required, and both matter to what a user actually experiences:

1. **First pass** (read-side windowing): `regime.py` and `scoring.py` were routed through a new bounded
   accessor (`bars_asof_window`) instead of materializing an entire multi-decade price history per
   symbol/date. This reduced peak memory but the audit found it was **not sufficient** — a live
   **second** consecutive full-universe rebuild still crashed the backend (audit finding B1).
2. **Second pass** (allocator/process hygiene, after the audit FAIL): capped glibc's memory-arena count
   (`MALLOC_ARENA_MAX=2`, exported by `start-backend.sh`) and added a `gc.collect()` +
   `malloc_trim(0)` cleanup step run after every backfill/rebuild stage
   (`data_manager._release_process_memory()`). This targets memory that accumulates **across** jobs in
   the same long-lived server process, which the first pass's read-side fix did not touch.

Both passes are described as byte-identity-neutral — they change *when/how* memory is allocated and
released, never a computed or displayed value.

---

## What Users Can Now Do

- Users can run the **"Rebuild snapshots for current universe"** job on `/data` over the full 322-date ×
  541-member universe and have it reach a genuinely-completed state, **and can immediately run it a
  second time in the same session without restarting the backend**, without the backend crashing either
  time. Per the dev handoff's live re-verification: run 1 peaked at VmPeak ≈5,027 MB (≈1,116 MB margin
  under the 6,144 MB cap); run 2, run back-to-back with no restart, showed **no VSZ growth** over run 1
  and produced bit-for-bit identical forward-return counts (597,044 both times).
  - Previously (iter-26, and iter-27's own first attempt before the second pass), a single full-universe
    rebuild reliably crashed the backend with a `MemoryError` once it reached deep-history dates
    (dot-com/GFC/COVID era) — taking down the whole application, not just the job. The audit's own repro
    of the first-pass fix showed a first run barely surviving (212 MB margin) and a second consecutive
    run pinning the process at the memory ceiling and crashing.
- Users can trust that after finishing a heavy rebuild, every other page and API on the product
  (`/data`, `/stocks`, `/api/health`) stays reachable — instead of the whole app going dark behind a
  crashed backend process.

## What Changed in the Visible UI

- **Nothing.** No `.tsx`/`.ts`/`.css` file under `apps/frontend/` was touched this iteration (confirmed
  by an empty `git diff` scoped to `apps/frontend/`). Every component on `/data` — the job form, the
  "Rebuild snapshots for current universe" confirm-gated action (`RebuildPanel`), the live job-progress
  card (`JobProgressPanel`), and the per-date availability heatmap — is byte-for-byte the same file as
  before this iteration. Every other page is likewise unchanged.
- What DID change is invisible in isolation: the **Market Regime figure on the Dashboard (`/`)**
  (computed by `regime.score_regime`, one of the functions this iteration's first pass rewrote to read a
  bounded window instead of full history) is asserted byte-identical before/after by an automated test
  (`test_score_regime_windowed_equals_unwindowed_across_dates`) — a user should see no numeric
  difference on that card, but it is the one already-displayed value whose underlying computation path
  changed this iteration, so it is called out here for regression awareness rather than silently assumed
  unaffected.
- The **only observable difference** a user gets is behavioral, not visual: the existing "Rebuild
  snapshots" progress display on `/data` now keeps advancing all the way to completion (twice in a row)
  instead of the browser losing its connection to a crashed backend partway through.

## What Old Behavior Changed

- **"Rebuild snapshots for current universe" (Data Manager, `/data`):** previously, running this job over
  the full universe crashed the backend outright — the job, the rest of `/data`, and every other page all
  became unreachable mid-run. A second consecutive run (no restart) crashed even faster, because memory
  freed by the first run was not being returned to the operating system between jobs. Now: the same job,
  run once or twice back-to-back, completes with an `ok` status and leaves comfortable headroom under the
  memory cap on both runs.
- **Nothing else.** The regime score, per-stock scores, forward returns, and every other value currently
  displayed anywhere in the product are asserted unchanged by the developer's byte-identity test suite
  (`test_scoring_window.py` 4/4, `test_bar_cache.py` 12/12, `test_forward_testing.py` cache-awareness
  cases 5/5, `test_config.py` + `test_config_engine.py` 111/111) — this is a memory-allocation and
  process-cleanup change underneath those values, not a computation change.

## Not Visible Yet

- None. This iteration adds no new endpoint, no new displayed value, no new config surfaced to the UI,
  and no nav-skeleton change (per the phase spec and plan). The new `bars_asof_window` accessor
  (`prices.py`), the `server.malloc_arena_max` config field, and `data_manager._release_process_memory()`
  are all purely internal — none has (or is meant to have) any independent UI surface, now or in a future
  iteration.
- **What still needs live confirmation beyond this analysis:** the dev handoff is explicit that its own
  isolated in-process memory harness peaks only ~3.0–3.8 GB and cannot reproduce the live ~6 GB shape
  (the live process carries additional uvicorn/threadpool baseline overhead the isolated script does not).
  The authoritative evidence for both passes is the **live** two-consecutive-rebuild HTTP-level run cited
  above and in `reports/perf-budgets.md` ("Item H"); the canonical browser-qa J-16 lane re-driving `/data`
  live (not merely an engine-level test) is what this pipeline still needs to confirm the fix end-to-end,
  per the iter-24 lesson that an engine-level fix alone is not sufficient to mark anti-goal #8 resolved.
