# Iteration State — ops-hardening

**After iteration:** 3 · **Date:** 2026-07-20 · **Verdict:** CONTINUE

## Journeys

3 passing (J-01 J-03 J-04) · 1 partial (J-05) · 1 failing (J-06) — 5 total. No status change this iter: J-05's backend B1/B2 fix + step-4 measurement are done & verified, but it has no clean browser pass (B3/F1 below). J-06 out of scope this iter.

## Active blockers

- **B3 (dev-owned, TOP next-step, blocks clean J-05 + future GOAL_ACHIEVED):** an ordinary "Fetch EOD prices" landing a bar past SPY's latest snapshot flips the app-wide HealthBadge/PreflightBanner into a crash-identical false "Backend unavailable"/"NO-GO", no in-app recovery. Root `app/engine/readiness.py:129` (`latest_servable = latest_run >= latest_data`) — PRE-EXISTING, NOT in the iter-3 diff. Fix: give "new data landed, snapshot pending" its own calm label + recovery pointer (compare vs the benchmark's own latest bar).
- **F1 (dev-owned):** job-progress heartbeat freezes ~83% of a heavy job → false "· possibly stalled" while healthy. Root: `_refresh_ingest_aggregates` per-date loop emits no `tick()` (`data_manager.py:3034+`, iter-2-shipped, untouched). Fix: add `tick()` in the finalize loop.
- **UT-04 (QA-owned, minor):** cold-boot honest-all-zero live check SKIPPED (no pristine DB); rests on unit tests this round — re-run live next iteration.

## Last 2 verdicts

- iter 3: CONTINUE — B1 (session's #1 blocker) closed & audit-verified + J-05 step-4 measured (VmPeak 40.9% margin, /api/health all-200, badge Ready); but browser/ux/closure FAIL surfaced PRE-EXISTING B3+F1 → J-05 stays partial, no regression (no verified journey moved passing→failing; QA PASS was overstated — audit T1/closure caught it).
- iter 2: CONTINUE — J-04→passing (ulimit/malloc-arena + logfile verified); J-05→partial (coverage_snapshot + finalize hook shipped; heavy-job measurement pending); as-of AG-3 fixed; B1 queued.

## Do not redo

- B1 fetch/expand coverage-freshness: `_run_job` new elif → canonical `refresh_coverage_snapshot`, gated by `_coverage_snapshot_is_current` (zero-work fetch pays nothing) — `data_manager.py:3793-3813`/`:1060-1081`; audit + 6 unit tests verified. Do NOT re-open the fetch/expand finalize gate.
- B2 stale-row reclaim: one bulk `DELETE ... WHERE dataset_version != current` in `_upsert_coverage_snapshot` — verified (one-DELETE test).
- J-05 step-4 measured: perf-budgets Item L (VmPeak 3,633.7 MB / 40.9% under 6144 MB cap; 1,725 health polls all 200) — do NOT re-measure.
- coverage_snapshot table + ingest finalize hook + `aggregates_refreshed` (null for fetch/expand); default `/data` served from storage (`coverage_from_storage`), no request-path whole-table load — do NOT re-introduce compute on the `as_of=None` path.
- `scripts/start-backend.sh` enforces `ulimit -v` 6144 MB + `MALLOC_ARENA_MAX=2` + persistent `logs/backend.log`; J-01/J-03 shipped fields (`dates_total`/breakdown/`chunk_index`, `max_range_days` removal) — do not touch.
- `docs/goal.md` lint-final (commit 9c98cb3) — do not edit; the 25 mcp-loop journeys are archived — do not re-verify.
