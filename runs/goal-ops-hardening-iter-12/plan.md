# goal-ops-hardening-iter-12 Execution Plan

Verification/documentation-only iteration (Depth: FULL solely because the prior dispatched verdict was
ESCALATE — trigger 3, mandatory). Target journey: J-06 (its last two agent-owned evidence gaps, G1 + G2).
Required-still-passing: J-01, J-03, J-04, J-05. **No source-file change is anticipated** — the whole
expected diff is `reports/perf-budgets.md` transcription/addenda plus the dev handoff. This matches
`docs/goal.md`'s J-06 acceptance criteria (budgets live only in `reports/perf-budgets.md`) and introduces
no new capability, so it advances the goal (closing J-06 honestly) without duplicating iter-5/9/11's prior
audit work — it explicitly extends iter-11's TC-4 audit (cache-HIT paths only) to the MISS/compute path,
rather than re-deriving it.

No drift from `docs/goal.md` found. No scope creep: the spec's own OUT OF SCOPE list already excludes the
AG-8 `forward_aggregates_cached`→`compute_forward_aggregates` MemoryError fix, `HOST_GUARD_REQUIRE_MARKERS`,
the `demo.sh --session-live` walkthrough, and any `scripts/automation/*` framework fix — all correctly kept
out by the spec itself; this plan carries those exclusions forward unchanged.

## What to Build

- **G1 (transcription):** copy the already-captured, already-on-disk 11-page TTI sweep + endpoint-latency
  table from `reports/qa/goal-ops-hardening-iter-11-evidence/UT-J-06-perf-sweep-summary.txt` into a new
  dated section of `reports/perf-budgets.md`. Preserve the original capture window (2026-07-22
  ~21:38–21:49Z) alongside today's transcription date; include both `/api/indexes?full=true` over-budget
  readings (2066.3ms, 2671.8ms) and the `/api/health` 2948.8ms outlier as disclosed WARNs — no cherry-picking
  the favorable re-read.
- **G2 (controlled re-measurement):** three independent, cache-disabled, fresh-navigation real-Chrome loads
  of `/data` measuring `GET /api/indexes?full=true`. Before/during each, confirm via `logs/backend.log`
  that no backfill/fetch/rebuild job is in-flight and via `logs/hwmon/hwmon.csv` that load1/MemAvailable at
  that exact timestamp sit in the already-established idle range (both files exist and are live-appending
  on this host right now). Record all three readings + the idle-confirmation evidence in
  `reports/perf-budgets.md`, honestly WARN-flagged if still over the ≤1.5s budget.
- **TC-4 audit correction addendum:** append a blockquote to `reports/perf-budgets.md`'s existing "J-06
  re-sweep … TC-4 code audit" section (iter-11), mirroring the iter-9 P1 "AUDIT CORRECTION" blockquote
  convention already in the same file (see line ~1606). Name — do not fix —
  `apps/backend/app/engine/forward_testing.py:826`
  (`session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()`, the MISS/
  compute path inside `compute_forward_aggregates`, reached via `forward_aggregates_cached` on a cache
  miss) as the unbounded-load site iter-11's cache-HIT-only audit never examined. State explicitly that
  iter-11's "no genuine violation found" conclusion covered only HIT paths.
- **`data_provider_runs` rows 120/121/122 read + handoff statement:** read the three rows directly
  (sqlite3 or a short read-only Python snippet against the committed DB — no ORM write), state in the dev
  handoff whether the persisted 4-of-7 `aggregates_refreshed` outcome is design-consistent (i.e.
  `latest_snapshot`/`market_phase` legitimately skipped because no new trading date landed on those
  zero-new-date runs) and that `forward_aggregates`'s absence on runs 121/122 is solely attributable to the
  MemoryError abort (cite `logs/backend.log:27185` / `:27233`) — confirming J-05's contract intact, or
  flagging it for re-open if the evidence doesn't support that reading.
- **Required-still-passing replay:** J-01 and J-03 via deterministic golden replay (LLM fallback if the
  replay harness itself is unavailable); J-04 and J-05 via LLM-fallback re-verification against the current
  build, with cited evidence (log grep / DB row / screenshot) per TC-6.
- **Targeted backend pytest subset**, host-guard-confined only: `test_data_manager_jobs_pipeline.py` and
  `test_forward_testing.py` (excluding the opt-in `TRENDORA_RUN_HEAVY_INGEST_TEST` lane). Do **not** run the
  full suite, do **not** touch `test_start_backend_script.py`'s heavy-ingest test (settled "do NOT re-run"
  per iteration-state), do **not** run any opt-in heavy-ingest workload.
- **Dev handoff** at `docs/handoffs/goal-ops-hardening-iter-12-dev.md` stating explicitly that no source
  file changed, citing the exact `reports/perf-budgets.md` sections that close J-06's G1/G2, and carrying
  forward the AG-8/`HOST_GUARD_REQUIRE_MARKERS`/`demo.sh --session-live` open owner decisions unchanged.

## Agents Required

- developer: yes -- perform the G1 transcription, the G2 idle-window log/hwmon cross-read (the actual
  three-load browser measurement itself is browser-qa-agent's Chrome-MCP pass — see below), the TC-4
  correction addendum, the `data_provider_runs` 120/121/122 read + handoff statement, the targeted pytest
  subset (host-guard-confined), and the dev handoff. No product source file is expected to change.
- backend-data: yes -- same scope as `developer` above (report-file transcription/addenda, a read-only DB
  query, and host-guard-confined pytest are all backend/ops-surface work; this project has no separate
  backend-data role — `developer` covers it, per iter-9's own established convention).
- frontend-ux: no -- zero frontend/UI source changes anticipated this iteration (spec's own "Frontend"
  bullet: "No product source changes anticipated"). `Frontend Present: yes` below exists solely so
  browser-qa-agent actually runs its Chrome-MCP lane for G2's three-load `/api/indexes` control measurement
  and the J-01/J-03/J-04/J-05 required-still-passing replay — not because any UI surface changes.

## Frontend Present: yes

(No UI code changes. Set to `yes` because TESTING REQUIREMENTS names a mandatory real-Chrome pass — G2's
three independent, cache-disabled, fresh-navigation `/data` loads measuring `GET /api/indexes?full=true`,
each cross-checked against `logs/backend.log` + `logs/hwmon/hwmon.csv` for a genuinely idle window — plus
the J-01/J-03/J-04/J-05 required-still-passing golden-replay/LLM-fallback verification. Per this session's
own established precedent (iter-9), QA MUST run the Chrome MCP browser-qa lane; do not skip it on the basis
of "no frontend files in the diff." Operator note: backend is already up on :8255 and frontend on :3255
with host-guard caps live — no service start/restart is needed for any of this iteration's measurements.)

## Files to Create/Modify

- `reports/perf-budgets.md` -- (1) new dated section transcribing the iter-11 11-page sweep +
  endpoint-latency table verbatim from `reports/qa/goal-ops-hardening-iter-11-evidence/
  UT-J-06-perf-sweep-summary.txt` (G1); (2) new dated section recording the three fresh-navigation
  `/api/indexes?full=true` readings + idle-window log/hwmon evidence (G2); (3) a TC-4 "AUDIT CORRECTION"
  blockquote addendum naming `forward_testing.py:826`'s MISS/compute path (mirrors the existing iter-9 P1
  blockquote convention in the same file).
- `docs/handoffs/goal-ops-hardening-iter-12-dev.md` -- new dev handoff: states no source file changed,
  cites the exact `reports/perf-budgets.md` section headers/line ranges supporting G1/G2 closure, states
  the `data_provider_runs` 120/121/122 finding, lists the targeted pytest command + host-guard wrap +
  result, and carries forward the open owner decisions (AG-8 MemoryError fix, `HOST_GUARD_REQUIRE_MARKERS`,
  `demo.sh --session-live` walkthrough) unchanged.
- No `apps/backend/**` source file is expected to change (read-only audit + a read-only DB query only).
  If any dev-session finding surprises this expectation, the developer must flag it rather than silently
  editing scope — this spec explicitly forbids touching `forward_testing.py`, `app/api/health.py`,
  `app/engine/readiness.py`, `main.py`'s boot sequence, `warmup.py`, `max_range_days`/`snapshot_cadence`,
  the `/evidence` drawdown warm, and `server.memory_cap_mb`.

## UI Evolution

- New user-facing capability: none.
- New information displayed: none (perf-budgets.md is a measurement artifact, not a served runtime value).
- New user actions: none.
- UI surface changes: none — `/data` is exercised read-only for the G2 measurement, not modified.
- Navigation changes: none.

## Visual Requirements

- No new visual/component work. Browser-qa exercises the EXISTING `/data` page (job form + coverage/
  `/api/indexes` panel) three times for G2, plus whatever existing surfaces J-01/J-03/J-04/J-05's replay
  touches (`/data`, `/scanner-runs`, top-bar readiness badge, preflight banner). No new component patterns,
  layout, or effects to design.
- States to verify (not build): the `/data` coverage panel's honest "still loading" state for the
  `/api/indexes` widget if a reading is slow (never a frozen/blank whole-page state) — pre-existing,
  re-confirmed live, not created this iteration.

## Key Test Scenarios

- TC-1: `reports/perf-budgets.md` gains a new dated section with all 11 pages' TTI + every endpoint-latency
  reading transcribed from the iter-11 evidence file, including both over-budget `/api/indexes?full=true`
  values and the `/api/health` 2948.8ms outlier, WARN-marked, with both the original and transcription
  timestamps stated.
- TC-2: three fresh-navigation, cache-disabled `/api/indexes?full=true` readings recorded, each preceded by
  a `logs/backend.log` no-in-flight-job check and a `logs/hwmon/hwmon.csv` idle-range check at that exact
  timestamp; each reading marked "holds: yes" or an honest WARN with the exact overage.
- TC-3: the TC-4 audit-correction blockquote names `forward_testing.py:826`'s
  `session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()` as the
  MISS/compute-path site not covered by iter-11's cache-HIT-only audit, with zero modification to that
  function.
- TC-4: `data_provider_runs` rows 120/121/122 read directly; dev handoff states explicitly whether the
  4-of-7 `aggregates_refreshed` outcome is design-consistent and that `forward_aggregates`'s absence traces
  solely to the MemoryError abort at `logs/backend.log:27185`/`:27233`.
- TC-5/TC-6: J-01 and J-03 golden replay PASS; J-04 and J-05 LLM-fallback re-verification PASS with cited
  evidence.
- TC-7/TC-8: any pytest this iteration runs is `taskset -c "$HOST_GUARD_CPU_LIST"`-wrapped with
  `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS`/`NUMEXPR_NUM_THREADS`=`$HOST_GUARD_BLAS_THREADS`
  (sourced from `project-extensions/host-guard/host-guard.env`); the targeted subset
  (`test_data_manager_jobs_pipeline.py`, `test_forward_testing.py`, heavy-ingest lane excluded) completes
  with zero NEW failures beyond the pre-existing `tests/test_db.py::test_create_all_produces_expected_tables`.
- TC-9: `docs/handoffs/goal-ops-hardening-iter-12-dev.md` exists, states explicitly whether any source file
  changed (expected: none), and cites the specific `reports/perf-budgets.md` sections supporting closure.

## Notes / Out-of-scope carry-forwards (do not build these this iteration)

- The AG-8 `forward_aggregates_cached` → `compute_forward_aggregates` unbounded-load MemoryError fix —
  critical, unresolved, explicit OWNER decision (scope/amend/defer); named, not fixed.
- `HOST_GUARD_REQUIRE_MARKERS` — owner/framework decision, not touched.
- The J-05/J-06 `demo.sh ops-hardening --session-live` walkthrough — confirmed this iteration (per spec) as
  having no autonomous production mechanism in this framework; stays an open owner/framework item, not
  developer scope.
- `merge_ui_test_results.py`'s dropped `**FAIL**` cells, the `Frontend Present: no` browser-qa-skip
  misrouting, and `runs/goal-ops-hardening-iter-11/status.json`'s stuck bookkeeping — framework-maintainer
  items; do not patch `scripts/automation/*` from inside this product iteration.
- Do not re-run `test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap` (settled, iter-9
  evidence stands). Do not run the full pytest suite. Do not run any opt-in heavy-ingest workload or
  full-universe backfill without explicit owner authorization (AG-10; two hard-resets this host, last week).
- Do not touch `app/api/health.py`, `app/engine/readiness.py`, `main.py`'s boot sequence, `warmup.py`,
  `max_range_days`/`snapshot_cadence`, the `/evidence` drawdown warm, or `server.memory_cap_mb` — all
  BINDING "Do not redo" items.

## Environment note

Before running any test or measurement command that writes temp files, export:
`TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-ae4ffb93.791787"`
`TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-ae4ffb93.791787"`
`TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-ae4ffb93.791787"`

## Operator constraints (relayed via pump)

- Agents in this pipeline cannot start/stop services this session (permission classifier blocks it; the
  subagent-resume channel is also broken). Services are already up: backend :8255 (host-guard caps live),
  frontend :3255 — no start/stop is needed for anything in this plan. If a future step ever needs one
  anyway, write it as an operator-performed fallback request (pid + timestamp recorded by the operator),
  never a direct agent-issued start/kill/restart.
- No full pytest suite (multi-hour on the 30-year basis). No opt-in heavy-ingest workload or full-universe
  backfill without explicit owner authorization.
