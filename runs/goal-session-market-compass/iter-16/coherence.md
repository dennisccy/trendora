# Iteration 16 — Coherence Audit

**Iteration:** goal-market-compass-iter-16
**Date:** 2026-08-25
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope note

This iteration is backend-only maintenance/safety work under active maintenance isolation: one
authorized `daily_prices.volume` correction (AVB, 2026-08-11/12), a certified-baseline supersession
helper, a fail-closed pre-boot guard, and a re-run of Stage D readiness. Per the spec's own "Blueprint
conformance" / "Data-contract additions" fields (`docs/phases/goal-market-compass-iter-16.md`): no new
page, nav entry, endpoint, or displayed value. I independently verified this rather than taking the
spec's word for it — see evidence below. No frontend file changed (`git status --porcelain` shows zero
entries under `apps/frontend/`); no `apps/backend/app/api/*` file changed (`git diff
a99b16c9962f9d6dc8e8f7fed6278e069dd28dfa --stat -- apps/backend/app/api/` is empty).

**Packet-hazard note (per coordinator's dispatch):** `git status --porcelain` shows 7 new untracked
files invisible to a plain `git diff HEAD`/snapshot-SHA diff: `apps/backend/app/engine/
j11_avb_correction.py`, `apps/backend/app/engine/j11_preboot_guard.py`, `apps/backend/scripts/
run_j11_avb_correction.py`, `apps/backend/scripts/run_j11_iter16_stage_d_readiness.py`,
`apps/backend/tests/test_j11_avb_correction.py`, `apps/backend/tests/
test_j11_avb_correction_cli_script.py`, `apps/backend/tests/test_j11_preboot_guard.py` — plus 5 tracked
files modified (`j11_stage_d.py`, `warmup.py`, `models.py`, `test_j11_stage_d.py`,
`test_j11_stage_d_cli_scripts.py`). I read all 7 untracked files in full (not just the 5-file review
packet) and the tracked diff in full before reaching this verdict.

## Data Contract check

No row in the blueprint's Data Contract (`runs/goal-session-market-compass/state/blueprint.md`) names
`daily_prices`, a Stage-D certified baseline, or a maintenance/incident-boundary state as a *displayed*
value — all of it is a raw input / internal safety artifact, never served through any endpoint or UI,
matching iterations 13-15's own determination for the same class of J-11 tooling. Checked anyway for
drift against every registered row:

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Stock leadership/entry/risk scores, buckets, setup status (`GET /api/stocks`) | OK — untouched | No scoring/setups module edited this iteration (`git diff --stat` shows zero touches to `app/engine/scoring.py`, `setups.py`); Stage D (the only path that would re-derive scores from the corrected `daily_prices`) explicitly does not execute this iteration (spec OUT OF SCOPE, `docs/phases/goal-market-compass-iter-16.md:86`) |
| Sector/theme scores + ranks (`GET /api/sectors`, `GET /api/themes`) | OK — untouched | Same reasoning; no scan re-run this iteration |
| `daily_prices_fingerprint` (Stage-D certified-baseline field, internal, not a Data Contract row) | OK — single producer, single supersession point | `apps/backend/app/engine/j11_stage_d.py:9-56` (`build_avb_correction_superseded_baseline`) takes the new fingerprint as a caller-supplied parameter — it does **not** recompute it. The one live caller (`apps/backend/scripts/run_j11_iter16_stage_d_readiness.py:164,191-196`) sources `fresh_daily_prices_fingerprint` from the existing, unchanged `jsd.capture_stage_d_preflight` → `pre_reset_inventory.daily_prices.fingerprint` path — the same single computation Stage D preflight has always used. Every other composed field (`manifest_ddl`, `manifest_dump`, `manifest_row_count`, `data_provider_runs_count`, `watchlist_count`) is copied unchanged from `original_certified_baseline` (`j11_stage_d.py:41-42`) — no parallel baseline authority created |
| AVB classification (`classify_avb`, internal J-11 tooling) | OK — canonical, unmodified source | `git diff a99b16c9962f9d6dc8e8f7fed6278e069dd28dfa -- apps/backend/app/engine/j11_avb_diagnostic.py` is empty — the file is byte-identical to the snapshot; `run_j11_iter16_stage_d_readiness.py:258` calls `diag.classify_avb` unchanged. The new `j11_avb_correction.py` module reuses `diag._RATIO_RELATIVE_TOLERANCE` and `diag._within_relative_tolerance` (`j11_avb_correction.py:75,420-421`) rather than reimplementing the calibration tolerance check |
| `_now_iso` timestamp helper | OK — reused, not duplicated | `j11_stage_d.py:77` defines it once; the new `build_avb_correction_superseded_baseline` calls the existing one (no second definition added in the diff) |

No new UI surface exists this iteration (none touched), so Part A.2 ("non-canonical source") is
vacuous. No new *displayed* value is introduced (Part A.4/A.5 vacuous) — the correction evidence, the
superseded-baseline artifact, and the `MaintenanceBoundary` guard state are all backend-internal,
persisted only to `runs/goal-market-compass-iter-16/*.json` and a new additive table, never routed
through an endpoint or component.

## Information Architecture check

No new page, route, or feature this iteration — table is vacuous.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no frontend/API surface changed) | OK | `git status --porcelain` under `apps/frontend/` returns nothing; `git diff --stat -- apps/backend/app/api/` is empty |

**Boot-path check (specifically requested by the coordinator):** the new pre-boot guard is wired into
the *existing single* startup path, not a second lane. `apps/backend/app/engine/warmup.py:107` calls
`j11_preboot_guard.evaluate_boundary_for_date` **inside** `ensure_latest_snapshot`, immediately before
the existing `run_scan(session, latest, cfg)` call at `warmup.py:113` — no new entry point, no second
`main.py` hook (`grep -n "preboot" apps/backend/main.py` returns nothing; the only caller of
`j11_preboot_guard` outside its own module and tests is `warmup.py`). On an exception it fails closed
(`warmup.py:98-104`) and returns the same `None` shape `ensure_latest_snapshot` already returns for an
empty database (`warmup.py:112`) — confirmed by reading the full diff, not merely the docstring's claim.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Guard has no production activation path yet — by design, not drift.** `register_j11_incident_boundary` (`apps/backend/app/engine/j11_preboot_guard.py:109-119`) is the only function that would populate the `maintenance_boundaries` table for the current J-11 incident, and it has zero callers anywhere outside its own module docstring and its own tests (`grep -rn "register_j11_incident_boundary" apps/` matches only the definition and prose references). With an empty table, `evaluate_boundary_for_date` returns `blocked=False` (`j11_preboot_guard.py:144-145`) — i.e., the guard is mechanically correct and sits on the one real boot path, but is not yet armed against the live database. This is consistent with the spec's own scope: Goal 6 is "build" and Goal 7 is "prove on disposable fixtures only," and registering against the live DB is explicitly forbidden this iteration (maintenance isolation). Not a Data Contract or IA violation — there is exactly one producer (`register_boundary`/`register_j11_incident_boundary`) and one consumer (`evaluate_boundary_for_date`) of `MaintenanceBoundary` state, so there is no scattered/duplicated source of truth here, just an not-yet-exercised production wiring step. Recorded here only so it isn't lost, per the coordinator's note that this is exactly why maintenance isolation must stay active until a future iteration performs that registration.
- No label/formatting drift to note — no UI was touched this iteration.
