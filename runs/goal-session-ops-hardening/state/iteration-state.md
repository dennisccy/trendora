# Iteration State — ops-hardening

**After iteration:** 2 · **Date:** 2026-07-20 · **Verdict:** CONTINUE

## Journeys

3 passing (J-01 J-03 J-04) · 1 partial (J-05) · 1 failing (J-06) — 5 total. J-04 newly passing (logfile + memory-cap built); J-05 up from failing (coverage_snapshot + finalize hook shipped, heavy-job measurement pending).

## Active blockers

- **B1 (dev-owned, TOP next-step, blocks future GOAL_ACHIEVED):** a `fetch` that lands new bars blanks the DEFAULT `/data` coverage to false all-zeros until restart/backfill — `coverage_snapshot` keyed on the live `dataset_version` fingerprint; `fetch`/`expand` skip the finalize hook. `apps/backend/app/engine/data_manager.py` :3759 (kind gate) / :1101 (self-heal as_of gate) / :900 (sentinel). Fix at ingest-time (AG-8-safe), gated to skip when stamp unchanged — NOT via the `as_of=None` self-heal.
- **J-05 step 4 (dev/QA-owned):** TC-11/TC-12 (health responsiveness + VmPeak DURING a heavy job) never measured live — the one gap keeping J-05 partial.

## Last 2 verdicts

- iter 2: CONTINUE — J-04→passing (ulimit/malloc-arena + persistent logfile verified live), J-05→partial (coverage_snapshot + finalize hook shipped; heavy-job measurement pending); as-of AG-3 fixed; B1 out-of-scope gap queued; J-06 unbuilt.
- iter 1: CONTINUE — J-01, J-03 delivered (cadence bypass, cap removal, breakdown/chunking); interrupted-row AG-3 fabricated-breakdown fixed intra-iteration.

## Do not redo

- `coverage_snapshot` table + ingest finalize hook + `aggregates_refreshed` (gated on `_breakdown_computed`; null for fetch/expand/interrupted) — data_manager.py, models.py — J-05 core, verified.
- `scripts/start-backend.sh` enforces `ulimit -v` 6144 MB + `MALLOC_ARENA_MAX=2` + persistent `logs/backend.log` (append; abrupt-end on crash) — verified live via /proc + real-process test.
- As-of-switcher AG-3 fix (per-date persist + explicit-`as_of` read-path self-heal) — verified byte-exact (UT-05); do NOT revert.
- Default `/data` served from storage via `coverage_from_storage` (api/data.py:127), zero request-path whole-table load — do NOT re-introduce `compute_coverage` on the default `as_of=None` path.
- J-01/J-03 shipped fields (`dates_total`/breakdown/`chunk_index`, `max_range_days` removal) — do not touch.
- `docs/goal.md` is lint-final (commit 9c98cb3) — do not edit; the 25 mcp-loop journeys are archived — do not re-verify.
