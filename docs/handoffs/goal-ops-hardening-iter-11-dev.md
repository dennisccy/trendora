# goal-ops-hardening-iter-11 Dev Handoff

**Phase:** goal-ops-hardening-iter-11
**Date:** 2026-07-22
**Agent:** developer
**Status:** complete — zero source files changed (this was a verification-only iteration, as the spec
anticipated). TC-3 (boot re-measurement) and TC-4 (code audit) are both closed with live evidence; TC-5
(byte-identity spot-check) ran two existing tests live and both passed; TC-6/TC-7 (confined targeted
pytest) ran under host-guard confinement. TC-1/TC-2/TC-8 (the real-browser 11-page sweep and the
J-01/J-03/J-04/J-05 golden-replay verification) are browser-qa-agent/QA responsibilities per this
project's own established pipeline split (see "What Was Built" below) — not reproduced here.

## What Was Built

**Nothing — this iteration changed zero source files, exactly as the spec anticipated.** `git status`
confirms the only file this developer session modified is `reports/perf-budgets.md` (a measurement
artifact, not source). The iteration's deliverable is fresh, live evidence closing J-06's two remaining
gaps: the boot-to-health re-measurement under the now-hardened launcher, and a static code-level audit of
the four Data-Contract rows the spec named. Per this session's own established precedent (iter-9's dev
handoff makes the identical point), the real-browser 11-page TTI/on-load sweep (TC-1/TC-2) and the
J-01/J-03/J-04/J-05 deterministic golden-replay verification (TC-8) are browser-qa-agent's/QA's own
pipeline stage (`.claude/workflow.md` stage 6, `browser-qa-phase.sh`), not a developer deliverable — the
IN SCOPE section's own "Frontend" bullet states this explicitly ("the real-browser TTI/on-load-latency
sweep... is browser-qa-agent's own Chrome-MCP measurement pass, not a code change").

### TC-3 — boot-to-health re-measurement (`reports/perf-budgets.md`, new section "J-06 re-sweep — TC-3
boot-to-health re-measurement under the host-guard-hardened launcher + TC-4 code audit (iter-11,
developer pass)")

Ran `bash scripts/measure-perf.sh --boot` (`CHAIN_BACKEND_PORT=8255 CHAIN_FRONTEND_PORT=3255`) myself —
the operator-assisted fallback in the spec's NOTES was not needed; the permission classifier did not
block this specific measurement-harness invocation (unlike a bare direct `start-backend.sh` call, which
the pump note describes as blocked). Confirmed nothing was listening on :8255 beforehand (`000` on
`GET /api/health`), so this is a genuine cold process-start timing:

- **Boot-to-health: 1.364s** (holds ≤ 5s budget: yes). Launcher PID **2192247**, started
  `2026-07-22T20:15:29Z` (`logs/backend.log` banner). The launcher's own boot-line confirms the host-guard
  caps are live on this exact boot: `port=8255 memory_cap_mb=6144 malloc_arena_max=2` /
  **`host-guard: cpu_list=0-3,8-11 blas_threads=4`** — matching `host-guard.env`'s committed
  `HOST_GUARD_CPU_LIST`/`HOST_GUARD_BLAS_THREADS` values exactly, never weakened or stripped (AG-10).
- This is the first boot measurement since iter-9 added that launcher-cap block; it reads statistically
  indistinguishable from the pre-cap baseline (1.387s/1.459s, iter-5) — the caps add no material boot cost.
- The backend was left running afterward (`measure-perf.sh --boot`'s documented behavior) so a subsequent
  browser-qa pass does not need a second cold start.

### TC-4 — static, read-only code audit of the four named Data-Contract rows

Full file:line citations are in `reports/perf-budgets.md`'s new section (table under "TC-4 — static,
read-only code audit"). Summary, confirmed by reading the current source (unchanged by this iteration):

| Data-Contract row | Verdict |
|---|---|
| **Coverage payload** (`GET /api/data` → `data_manager.coverage_from_storage`, `api/data.py:127` → `data_manager.py:1095-1131`) | Bounded — serves the persisted `CoverageSnapshot` row via an indexed point lookup; zero `daily_prices` queries on the default/common path. |
| **Backfill run-summary** (`GET /api/data` → `data_manager.recent_runs`, `api/data.py:128` → `data_manager.py:4305-4314`) | Bounded — `select(DataProviderRun).order_by(...).limit(run_history_limit)`; never a whole-table load. |
| **Job history** (`GET /api/data/jobs/{job_id}` → `data_manager.get_job`, `api/data.py:207-214` → `data_manager.py:2091-2095`) | Bounded — an in-memory dict lookup, zero DB query. |
| **Membership-timeline** (`membership_timeline_cached`, `data_manager.py:571-608`, embedded in the Coverage payload above) | Bounded/cached — a HIT returns the persisted `MembershipTimelineCache` row verbatim, skipping the O(dates × pool) resolver loop entirely; warmed at ingest time (`data_manager.py:891`), never recomputed on the request path. |
| **Research-hot-key** (`GET /api/research/event-study` → `event_study_cached`, `research.py:291-293` → `app/engine/research.py:1606-1662`) | Bounded/cached — a HIT returns the persisted `EventStudyCache` row verbatim; the default `(first subject, default horizon, episodes, all-history)` key is warmed at ingest time (`data_manager.py:3243-3250`), never recomputed on a repeat default-view request. |

**No genuine violation found.** The 7 endpoints iter-5's own dev handoff already tabulated with file:line
evidence (Dashboard cluster, `/sectors`, `/themes`, `/scanner-runs`'s measured-safe `/api/runs` N+1,
`/backtest`'s `forward_aggregates_cached`, `/watchlist`, `/research/event-study`) are reconfirmed
byte-for-byte unchanged (this iteration's diff is empty) — not re-derived here to avoid duplicating that
citation; see `docs/handoffs/goal-ops-hardening-iter-5-dev.md`'s "TC-13" table.

### TC-5 — AG-3 byte-identity spot-check (≥2 already-registered ingest-time-warmed values)

Ran two EXISTING tests live (no new test written — this iteration adds no source/test file):

- `tests/test_data_manager.py::test_finalize_hook_coverage_snapshot_byte_identical_to_fresh_compute` —
  asserts the persisted Coverage-payload row (which embeds the Membership-timeline derivation) equals a
  direct uncached `_compute_coverage_uncached` call, field-by-field (`stored == fresh`).
- `tests/test_forward_testing.py::test_forward_aggregates_cached_byte_identical_and_single_row` — asserts
  `forward_aggregates_cached`'s MISS and HIT payloads are both `json.dumps`-identical to a direct uncached
  `compute_forward_aggregates` call.

Both **PASSED** (see Tests Run below for the exact command/output). `market_phase_cached`'s own
byte-identity test (`test_market_phase.py::test_cache_byte_identical_and_single_row`) needs the
session-scoped `loaded_engine` fixture (full 30-year/587-symbol bootstrap) — documented across
iter-4's/iter-9's own dev/audit handoffs as exceeding any reasonable dev-session time budget, so it was
not run live here; the Coverage/Membership-timeline pair substitutes as the second already-warmed value,
both from a fast hand-built fixture (`finalize_hook_engine`). Stated explicitly, not silently.

## Files Changed

- `reports/perf-budgets.md` — appended one new dated section: the TC-3 boot re-measurement (1.364s,
  holds ≤5s) and the TC-4 code-audit table for the four named Data-Contract rows. **No other file changed**
  — confirmed via `git status` before writing this handoff.

## Tests Run

All runs wrapped in host-guard confinement (TC-6): `taskset -c "$HOST_GUARD_CPU_LIST"` plus
`OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`/`NUMEXPR_NUM_THREADS` set to
`$HOST_GUARD_BLAS_THREADS`, both sourced from `project-extensions/host-guard/host-guard.env`
(`HOST_GUARD_CPU_LIST=0-3,8-11`, `HOST_GUARD_BLAS_THREADS=4`) — this session's own outer wrapper already
carries the identical affinity, so the explicit wrap is a re-confirmation, not a new restriction.

Command (TC-5 byte-identity spot-check):
```
cd apps/backend && source ../../project-extensions/host-guard/host-guard.env && \
OMP_NUM_THREADS=$HOST_GUARD_BLAS_THREADS OPENBLAS_NUM_THREADS=$HOST_GUARD_BLAS_THREADS \
MKL_NUM_THREADS=$HOST_GUARD_BLAS_THREADS NUMEXPR_NUM_THREADS=$HOST_GUARD_BLAS_THREADS \
taskset -c "$HOST_GUARD_CPU_LIST" .venv/bin/python -m pytest \
  tests/test_data_manager.py::test_finalize_hook_coverage_snapshot_byte_identical_to_fresh_compute \
  tests/test_forward_testing.py::test_forward_aggregates_cached_byte_identical_and_single_row -v
```
Result: **2 passed in 0.48s** — both `stored == fresh` (coverage/membership-timeline) and
`json.dumps(fresh) == json.dumps(miss) == json.dumps(hit)` (forward-aggregates) held.

Commands (TESTING REQUIREMENTS' named targeted subset, TC-7 — run as two separate invocations, same
host-guard wrap each time):
```
cd apps/backend && source ../../project-extensions/host-guard/host-guard.env && \
OMP_NUM_THREADS=$HOST_GUARD_BLAS_THREADS OPENBLAS_NUM_THREADS=$HOST_GUARD_BLAS_THREADS \
MKL_NUM_THREADS=$HOST_GUARD_BLAS_THREADS NUMEXPR_NUM_THREADS=$HOST_GUARD_BLAS_THREADS \
taskset -c "$HOST_GUARD_CPU_LIST" .venv/bin/python -m pytest tests/test_data_manager_jobs_pipeline.py -q

# second invocation, same wrap:
taskset -c "$HOST_GUARD_CPU_LIST" .venv/bin/python -m pytest \
  tests/test_start_backend_script.py -k "not heavy_ingest" -q
```
`TRENDORA_RUN_HEAVY_INGEST_TEST` left unset throughout — the heavy back-to-back-ingest test self-skips
without it regardless of `-k` selection (its own opt-in env-var guard inside the fixture), per its
settled "do NOT re-run" status this iteration (iter-9 evidence already on disk). The explicit
`-k "not heavy_ingest"` on the second file mirrors iter-9/iter-10's own precedent command, avoiding even
collecting that fixture's setup path.

Result:
- `test_data_manager_jobs_pipeline.py` → **21 passed in 575.97s (0:09:35)**
- `test_start_backend_script.py -k "not heavy_ingest"` → **8 passed, 1 deselected in 56.02s** (the
  deselected test is `test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap` — the
  settled, do-NOT-re-run heavy-ingest test; it also self-skips via its own opt-in env-var guard even if
  collected)

**Zero failures across both files** — no NEW failure, and no re-triggering of the one pre-existing
documented unrelated failure (`tests/test_db.py::test_create_all_produces_expected_tables`, not part of
this targeted subset, not touched this iteration). No stray processes leaked: `ps aux` after both runs
shows no orphaned test-spawned `uvicorn`/`next dev` processes (each spawning fixture's own teardown
cleaned up its isolated test-port instance); the one live backend on :8255 is the TC-3 boot-measurement
instance this developer session itself started and deliberately left running.

## Known Issues

- The real-browser 11-page TTI/on-load sweep (TC-1/TC-2) and the J-01/J-03/J-04/J-05 deterministic
  golden-replay verification (TC-8) are not in this handoff — they are browser-qa-agent's/QA's own pipeline
  stage, per this iteration's own IN SCOPE "Frontend" bullet and this session's established precedent
  (iter-9's dev handoff makes the identical point). The backend (:8255) was left running after the TC-3
  boot measurement specifically so that pass can proceed without a second cold start.
- `market_phase_cached`'s own byte-identity test needs the `loaded_engine` fixture and was not run live
  this iteration (see TC-5 above) — a pre-existing, documented cost, not a new gap this iteration
  introduces.
- No new violation was found by the TC-4 audit, so there is nothing to file for a future iteration's scope
  on that front.
- AG-8's deferred `GET /api/backtest` → `forward_aggregates_cached` MemoryError dimension and
  `HOST_GUARD_REQUIRE_MARKERS` remain open owner decisions, unaffected by this iteration (unchanged from
  iter-9/iter-10's own state — restated per the spec's OUT OF SCOPE list, not re-litigated here).
