# Iteration 2 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-2
**Date:** 2026-07-20
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->
<!-- COHERENCE-WARN: only advisory issues; does NOT block GOAL_ACHIEVED -->
<!-- COHERENCE-FAIL: ≥1 objective violation; blocks GOAL_ACHIEVED, forces a consolidation iteration -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Coverage payload (universe counts, per-symbol coverage, gaps, capacity) | OK, with one advisory note (see below) | `apps/backend/app/api/data.py:127` calls `data_manager.coverage_from_storage(...)`, replacing the prior live `compute_coverage` call — matches the registered endpoint (`GET /api/data`) and module (`app.engine.data_manager`). `coverage_from_storage` (`data_manager.py:1067-1103`) reads the persisted `CoverageSnapshot` row for the resolved `(asof_key, dataset_version)` key; the finalize hook (`data_manager.py:3008-3072`) and boot warm-up safety net (`warmup.py` new `_warm_coverage_snapshot`) both write it via the SAME canonical `_compute_coverage_uncached` (verified still the sole compute path: `data_manager.py:1037`, `:1025-1040`). No second derivation anywhere in the diff. |
| Backfill run-summary contract — new `aggregates_refreshed` field | OK | `JobProgress.aggregates_refreshed` (`data_manager.py:1865`), live-poll serialization in `to_dict()` (`:2018`), gated null/non-empty in `_run_detail()` (`:3375-3381`, mirrors the existing `calendar_days`/`_breakdown_computed` gate), populated only on a successful backfill/both/rebuild by `_run_job` (`:3764`) calling `_refresh_ingest_aggregates` (`:3008`). Read verbatim (no recompute) by `summarize_provider_run` for the `runs` list. Matches the Data Contract row and the iteration spec's field/nullability spec exactly. |
| Market phase (WARM TRIGGER only) | OK | `_refresh_ingest_aggregates` calls the existing canonical `market_phase.market_phase_cached(session, d, cfg)` (`data_manager.py:3049`) for each newly-created snapshot date — no new market-phase derivation; reuses the pre-existing cache/compute exactly as registered. |
| Membership timeline / research hot-key caches | OK | Membership timeline: verified `_compute_coverage_body` (pre-existing, unchanged) itself calls `membership_timeline_cached(session, cfg, snapshot_dates)` at `data_manager.py:889` — so `refresh_coverage_snapshot`'s call into `_compute_coverage_uncached` warms it as a genuine free side effect, not a fabricated claim. Research hot-keys: explicit call to the existing canonical `event_study_cached(...)` at `data_manager.py:3062`. Both reuse the registered functions verbatim; no second derivation. |
| Frontend display of `aggregates_refreshed` | OK — re-format only | `apps/frontend/app/data/page.tsx`'s `BackfillBreakdown` reads `run.aggregates_refreshed`/`job.aggregates_refreshed` (typed in `apps/frontend/lib/api.ts`) straight from the existing `GET /api/data` / `GET /api/data/jobs/{id}` payloads and only joins/relabels the strings for display (underscore→space, comma-join). No new fetch, no client-side recomputation. |

**Advisory note (not a FAIL — see reasoning):** `coverage_from_storage`'s "self-heal" branch
(`data_manager.py:1099-1102`, guarded by `_scanner_run_exists` at `:1058-1063`) performs a **live
call to the canonical compute** (`refresh_coverage_snapshot_for` → `_compute_coverage_uncached`) **synchronously
inside the `GET /api/data` request path** when an explicit `?as_of=` selects an already-ingested historical
date that predates this table and has no persisted `CoverageSnapshot` row yet. This is narrower than the
blueprint's Data Contract Notes column, which states the coverage value is served "never [via] a live
whole-table compute on this serving path." I did not FAIL this because: (a) it calls the exact same
canonical function in the exact same canonical module the finalize hook and boot warm-up already use — no
second implementation, so the served value can never diverge ("the numbers don't match" cannot happen
here); (b) it is served from the same, sole registered endpoint (`GET /api/data`) — no new/parallel
endpoint or client-side recompute; (c) it is documented in-code (`data_manager.py:1069-1082`) and in
`reports/phase-goal-ops-hardening-iter-2-ui-surface-map.md` as a deliberate, reviewed fix for a real AG-3
bug (a historical as-of was incorrectly serving an all-zero sentinel) rather than an undisclosed drift.
Recommended for next iteration: tighten the blueprint's "Coverage payload" Notes column to name this
narrow historical-legacy-date exception explicitly (rather than the current unqualified "never"), and have
the goal-evaluator/QA confirm this fallback's cost is bounded (it is gated behind `_scanner_run_exists`, so
it can only fire for a real already-ingested date, at most once per legacy date since the result is then
persisted) — this narrow case sits outside TC-9's exact zero-row scenario and is worth an explicit look if
not already covered by browser-qa evidence.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` — new "Refreshed: …" line in `BackfillBreakdown` | OK | `apps/frontend/app/data/page.tsx`: additive optional `aggregatesRefreshed` prop on the existing `BackfillBreakdown` component, threaded through its 3 existing call sites (`LastRunSummary`, `JobProgressPanel`, `RunHistoryPanel`) — all already part of `/data`, the canonical home per blueprint.md's IA table. No new component tree, no new panel, no new page. |
| `/`, `/scanner-runs`, `/research/*` (aggregates now warm sooner) | OK — no code change | `apps/frontend/components/sidebar.tsx` last modified 2026-06-29 (pre-dates this iteration's snapshot SHA `e62793b0`) and does not appear in `git diff --name-only` against that SHA — nav skeleton unchanged. `reports/phase-goal-ops-hardening-iter-2-ui-surface-map.md` confirms these 3 pages are named as regression-check targets only (byte-identical output, faster because pre-warmed), 0 new pages/routes, 0 navigation changes. |
| `scripts/start-backend.sh` (memory cap / logfile) | OK — not a UI surface | Ops-only launch-script change (`ulimit -v`, `MALLOC_ARENA_MAX`, persistent `logs/backend.log`); no displayed value, no route, not subject to IA rules. |

No new page/route was introduced this iteration; the blueprint's own note ("No Information
Architecture change this iteration") is confirmed by the diff — no `sidebar.tsx`/nav/router file
appears in the changed-files list, and no new API route was added anywhere under
`apps/backend/app/api/` (checked for new route decorators across the whole `api/` diff — none found;
`api/data.py`'s only change is the one-line `compute_coverage` → `coverage_from_storage` swap).

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `coverage_from_storage`'s historical-as-of self-heal path (`data_manager.py:1099-1102`) computes
  live on the `GET /api/data` request path for a narrow, gated, already-reviewed edge case — same
  canonical module/function/endpoint throughout, so no duplicate-source risk, but it slightly
  overshoots the blueprint's current unqualified "never a live whole-table compute on this serving
  path" wording. Suggest the next blueprint revision add this one-sentence carve-out so the Data
  Contract's Notes column stays precisely accurate.
- No other coherence drift found: the `coverage_snapshot` table, the `aggregates_refreshed` field,
  and the market-phase/membership-timeline/research-hot-key warm calls are all built exactly through
  the single canonical module/function/endpoint the blueprint names for each, with no new pages, nav
  entries, or parallel UI surfaces introduced.
