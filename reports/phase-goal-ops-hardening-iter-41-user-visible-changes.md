# Phase goal-ops-hardening-iter-41 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-41
**Date:** 2026-07-31
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None. This iteration shipped no new Trendora capability. Per the phase spec's own metadata
(`Frontend Present: no`, "New user-facing capability: None", "New user actions: None") and the dev
handoff ("no new UI capability"), no code under `apps/frontend/` was touched. A Trendora trader using
`/data`, `/backtest`, `/scanner-runs`, or any other page cannot do anything today that they could not do
before this iteration.

---

## What Changed in the Visible UI

None. Zero files under `apps/frontend/` appear in the dev handoff's "Files Changed" list, and the
execution plan explicitly states "this plan does not add or change any UI code." No page, component,
label, form, or navigation element changed.

---

## What Old Behavior Changed

None that a user can observe. The two backend behavior changes this iteration made are both explicitly
proven output-preserving:

- `_BarCache.prefill` (the routine backing `/data`'s coverage payload and backfill jobs) now stores
  price bars in a more memory-efficient internal structure, but a fixture-backed byte-identity test
  (`test_prefill_old_vs_new_implementation_byte_identical`) confirms every returned value is identical
  to before — same numbers on `/data`, same backfill results, just ~52% less server RAM used to produce
  them.
- The job-progress checkpoint write (`_checkpoint_run_record`) now also fires on a count-based floor (at
  least every 5th completed date), not only on the existing 1-second timer. This can only make a
  mid-flight job's progress reporting on `/data` slightly MORE up-to-date after an interruption — it
  writes to the same `message` field with the same serializer, adds no new field, and changes no display
  logic. Under normal (uninterrupted) operation there is no observable difference.

---

## Not Visible Yet

- **`_BarCache.prefill`'s memory reduction** (~1.34 GB → ~0.65 GB resident, measured on the live
  591-symbol / 3.3M-row basis) is a backend-only efficiency change. It makes the server less likely to
  hit its memory ceiling during a full-universe coverage read or backfill, but there is no UI element
  that shows memory usage — a user cannot see this improvement directly, only benefit from fewer
  memory-pressure failures over time.
- **The count-based checkpoint floor** (`_RUN_RECORD_CHECKPOINT_DATE_FLOOR = 5` in
  `apps/backend/app/engine/data_manager.py`) has no UI surface of its own — it only bounds how stale a
  persisted run's progress can get if the process is killed mid-job.
- **`TRENDORA_DIAG_FAULTHANDLER_SIGUSR1`** is a new opt-in, default-off environment variable
  (`apps/backend/main.py`) that arms a live thread-dump diagnostic for operators debugging a frozen
  backend process. It is a command-line/ops tool, never surfaced in the UI, and off by default.
- **The verification-pipeline repair** (health-check URL fix, the `ui-test-designer` agent's
  backend-only-handling rewrite, the `merge_ui_test_results.py` missing-required-journey detection, the
  new `BLOCKED` verdict) is entirely internal to this project's own AI-development-automation tooling
  under `incredible_auto_dev/` and `.claude/`. It is not part of the Trendora product in any form — it
  changes how future iterations of this pipeline get automatically re-verified, not anything a Trendora
  trader interacts with. It has zero UI surface by construction.

None of the above is a gap or an oversight — the phase spec's own "Product surface delta" section states
this precisely: "None visible to the end user."
