# goal-ops-hardening-iter-63 Execution Plan

## What to Build

- **Backend latency fix (J-07, the only target journey):** profile — never assume — the live GIL-hold /
  latency source inside the ingest finalize tail's `coverage_membership_timeline_refresh` phase
  (`app.engine.data_manager._refresh_ingest_aggregates`, `data_manager.py:4237-4327`), which iter-61's
  reconciled drill measured breaching the owner's relaxed ≤2.0 s `GET /api/health` bounded-background-
  compute-window ceiling by 0.849 s (2.849 s, at 08:23:13.091Z, the very FIRST second of the phase —
  `reports/perf-budgets.md` Addendum 28). Candidates named by the spec, in the order this session's own
  precedent (iter-53/54) suggests checking them: (a) `universe_resolver.resolve_with_reasons`'s per-symbol
  loop (`universe_resolver.py:234-243`) — already bounded to `bars_asof_window` at iter-53; confirm whether
  residual cost remains now that the phase's OWN entry (before the loop even starts — e.g. the coverage
  gate check, cache attach, or `refresh_coverage_snapshot`/`_compute_coverage_uncached`/
  `_compute_coverage_body` call at `data_manager.py:1125-1185`) is the true first-second cost; (b)
  `refresh_coverage_snapshot`/`_compute_coverage_uncached`'s own compute. Apply whichever bounded /
  cooperative-yield construct the profile actually supports — mirror `_cooperative_sorted`'s chunked
  `time.sleep(0)` hand-off or `_cyclic_gc_paused`'s GC-pause suspension (both `research.py:143-205`,
  iter-52 precedent) if the profile finds a sort/GC-pause culprit, or a further-bounded fetch in
  `universe_resolver.py`'s iter-53 style if it finds something else — do not force-fit a construct without
  profiling first (iter-48/50/53's own standing rule; iter-52's own history shows a first guess measured
  WORSE before profiling found the real cause). Output must stay byte-identical:
  `admitted`/`excluded_counts`/`resolutions` and the served coverage payload unchanged for the same inputs
  — only HOW CPU time / GIL hold is yielded changes, never WHAT is computed.
- **If profiling finds zero residual latency risk** (iter-61's 2.849 s does not reproduce under a fresh
  measurement): record that honestly in the dev handoff rather than shipping a speculative fix with no
  measured effect. J-07 then rests entirely on the owner's still-open one-sentence policy question
  (restate it plainly, do not resolve it — it is explicitly OUT OF SCOPE this iteration).
- **Unit test:** a byte-identity test proving the bounded construct's output matches a pinned pre-fix
  reference oracle, mirroring `test_universe_resolver.py`'s existing iter-53 tests (e.g.
  `test_resolve_with_reasons_adv_window_boundary_exact_short_and_long_history` at line 406-427, which uses
  `resolve_candidate` called on the full unbounded bars as the reference oracle — the same pattern applies
  here regardless of which function the fix lands in).
- **TC-1 drill:** a fresh live 1 Hz `GET /api/health` poll for the FULL duration of a real backfill/rebuild
  job's finalize tail (bounded by the phase's own `J-05 finalize-tail phase timing` OPEN/CLOSED log
  markers at `data_manager.py:4324-4327`, never a hand-picked segment — iter-57/58 lesson), reconciled
  against the raw poll log's own line count (mirror `runs/goal-ops-hardening-iter-59/evidence-drill/
  reconcile_drill.py`'s fail-loud reconciliation, reused per the session's own convention). Record the
  result as a new dated addendum in `reports/perf-budgets.md`, appended (never edited in place).
- **Test-infrastructure fix 1 — rotate J-05's consumed golden date:** `2010-11-17` was consumed by iter-62's
  own replay (`scanner_runs.id=2958`), so `runs/goal-session-ops-hardening/journey-scripts/J-05.json`
  currently asserts "0 already snapshotted" on a day that now HAS a snapshot — a guaranteed false FAIL on
  a currently-passing journey next replay. Live-verify (direct read-only sqlite query against
  `apps/backend/data/trendora.db`) a fresh unsnapshotted trading day BEFORE editing, then rotate steps 2/3's
  fill targets AND steps 13-15's asserted date (currently `2010-11-16`, already two rotations stale) to
  that SAME new date. Append a dated rotation-history entry to the file's own `_notes`, per its established
  convention (see the file's docstring for the pattern).
- **Test-infrastructure fix 2 — replay-lane restart race:** the deterministic replay lane's first step must
  gate on the backend's own READINESS signal (the `GET /api/health` payload's ready state / the UI's
  `data-testid="readiness-badge" data-state="ready"` — `apps/frontend/components/health-badge.tsx:58` —
  not merely a 2xx/3xx HTTP status code, which is all `ensure_services_running`'s current liveness probe
  checks, per `scripts/automation/lib/common.sh:832-979`/`1243`). A lane invoked within ~60 s of the
  pipeline's pre-QA backend restart reported two false FAILs (J-01 step 09, J-04 step 02) on journeys that
  were honestly still warming up (iter-62 lesson #2). Locate the actual restart-to-lane-start ordering —
  likely inside `scripts/automation/goal-iter-lean.sh`'s `run_browser_qa_boot_and_replay()`
  (`goal-iter-lean.sh:249-350`, between `ensure_services_running` at line 294/311 and
  `replay_lane_partition_and_verify` shortly after line 350) and/or `scripts/automation/lib/replay-lane.sh`
  — and fix it there. Do NOT touch `browser-qa-phase.sh`'s TARGET_JOURNEYS line-286-before-272 ordering bug
  (explicitly OWNER-gated, out of scope).
- **Test-infrastructure fix 3 — doc-comment correction:** `apps/frontend/lib/data-overview-refresh.test.ts`'s
  header comment (lines 1-8) currently documents `node lib/data-overview-refresh.test.ts` as the run
  command; only `npx tsx lib/data-overview-refresh.test.ts` actually exits 0 on this Node 22 install (plain
  `node` errors `ERR_UNKNOWN_FILE_EXTENSION`). Fix the comment only — the test itself is already correct
  and green (do not touch its logic).

## Agents Required
- backend-data: yes -- the `coverage_membership_timeline_refresh` GIL-hold profiling + bounded fix,
  its byte-identity unit test, the TC-1 live health-poll drill, and the J-05 golden rotation (a sqlite
  read + JSON edit, not application code) all sit in the backend/data-manager/test-infrastructure surface.
- frontend-ux: no -- the only frontend-adjacent touch is the one-line doc-comment fix in a non-shipping
  test file; no UI code, component, or user-visible behavior changes.

## Frontend Present: no

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` -- profile + bound the `coverage_membership_timeline_refresh`
  phase (exact lines TBD by profiling result; likely inside `_refresh_ingest_aggregates`'s
  `data_manager.py:4237-4327` block, or in `_compute_coverage_uncached`/`_compute_coverage_body`
  `data_manager.py:1125-1185` if profiling points there).
- `apps/backend/app/engine/universe_resolver.py` -- only if profiling confirms `resolve_with_reasons`'s
  per-symbol loop (`universe_resolver.py:234-243`) still carries residual cost after iter-53's bound.
- `apps/backend/tests/test_universe_resolver.py` and/or
  `apps/backend/tests/test_data_manager_membership_cache.py` -- new byte-identity test against a pinned
  pre-fix reference oracle (whichever file matches where the fix actually lands).
- `reports/perf-budgets.md` -- new dated addendum recording the TC-1 drill result (append-only).
- `runs/goal-session-ops-hardening/journey-scripts/J-05.json` -- rotate steps 2/3/13-15's date off
  `2010-11-17`/`2010-11-16`; append a `_notes` rotation-history entry.
- `scripts/automation/goal-iter-lean.sh` and/or `scripts/automation/lib/replay-lane.sh` -- gate the
  replay lane's first step on the backend's real readiness signal instead of a bare HTTP 2xx/3xx probe.
- `apps/frontend/lib/data-overview-refresh.test.ts` -- header comment correction only (lines 1-8).
- `docs/handoffs/goal-ops-hardening-iter-63-dev.md` -- dev handoff (required by DoD).

## UI Evolution
N/A -- Frontend Present: no. No new page, control, displayed value, or user action this iteration
(spec: "New user-facing capability: None", "New information displayed: None", "New user actions: None",
"UI surface changes: None").

## Visual Requirements
N/A -- Frontend Present: no.

## Key Test Scenarios
- TC-1: 1 Hz `GET /api/health` polled for the full `coverage_membership_timeline_refresh` phase (and
  ideally the whole finalize tail) during a real live backfill/rebuild job records ZERO polls over 2.0 s,
  reconciled against the raw poll log's line count via the phase's own OPEN/CLOSED log markers.
- TC-2/TC-5: the bounded construct's `resolutions`/`admitted`/`excluded_counts` values and the served
  `GET /api/data` coverage payload are byte-identical (not merely equal-looking) to a pinned pre-fix
  reference oracle for the same inputs; all pre-existing tests in the touched module stay green.
- TC-3: a live read-only sqlite query confirms a fresh unsnapshotted trading day BEFORE the J-05 golden
  edit; steps 2/3 fill values and steps 13-15's asserted date all match that SAME new date; a
  rotation-history `_notes` entry is appended.
- TC-4: the deterministic replay lane invoked within 60 s of a pipeline pre-QA backend restart (reproducing
  iter-62's exact false-FAIL condition) blocks on the backend's own readiness signal before its first
  step, and J-01 step 09 / J-04 step 02 report PASS rather than a warm-up-induced false FAIL.
- TC-6: `data-overview-refresh.test.ts`'s corrected header documents `npx tsx
  lib/data-overview-refresh.test.ts`; running that exact command still reports 3/3 checks passed.
- Required-still-passing regression (full, per widen-after-ESCALATE convention): J-01, J-03, J-04, J-05,
  J-06, J-08, J-09 all still pass via deterministic replay + LLM fallback -- zero regressions.
- Error case (regression check, not new): `TRENDORA_FAULT_INJECT_MEMORY_ERROR=coverage_membership_timeline`
  still isolates cleanly at its current probe site (`data_manager.py:4297`), unaffected by the bound.
- Anti-goal checks: AG-3 (displayed numbers still match engine computation), AG-5 (no lookahead
  introduced), AG-8 (no unbounded whole-table load added by the fix), AG-9 (every ingest row stays
  `provider='seed'`, no live network call), AG-10 (no change to `memory_cap_mb`/`malloc_arena_max`/
  `host-guard.env` -- explicitly OUT OF SCOPE this iteration).

## Out of Scope (per spec, do not implement)
- The owner's outstanding ≤2 s-ceiling-applicability policy question -- the fix is designed to make the
  measured answer moot (zero breaches) regardless of which reading is eventually chosen.
- `browser-qa-phase.sh`'s TARGET_JOURNEYS line-286-before-272 ordering bug (OWNER-gated).
- The replay lane's cost decision (a real ~15-minute ingest job every round) -- owner-gated.
- Any change to `server.memory_cap_mb`, `malloc_arena_max`, or `host-guard.env` values (AG-10).
- All long-carried backlog items listed in the spec's OUT OF SCOPE section (iter-29/b, 31/e, 32/f, 35/k,
  36/n, 37/o, 37/q, 39/u, 46/az/ba, 47/bd/bf/bi, 48/bj, 57/f/l, 59/g/h/k, 33/g Regime Lab).

## Notes for downstream agents
- This plan aligns with `docs/goal.md`'s Key Capability 6 ("Per-page minimal loading with budgets") and
  the Constraints' "Compute-at-ingest" principle -- it closes the last measured exception to
  `GET /api/health` staying responsive throughout ingest, without introducing a second aggregation path
  (goal.md's canonical-value rule for the Job history / Coverage payload Data Contract rows is preserved).
- No Data Contract addition, no new Information Architecture surface, no blueprint re-approval needed --
  this iteration extends the already-registered "Job history & per-date exclusion reasons" row's Notes
  cell only (already appended per the spec's "Blueprint conformance" section).
- The two test-infrastructure fixes (J-05 golden rotation, replay-lane race) are framework/pipeline
  hygiene, not product code -- per this session's iter-9/18/23 precedent they need no blueprint update and
  are not scored as a second risky journey; they exist to prevent a false regression halt on the
  required-still-passing set next round.
