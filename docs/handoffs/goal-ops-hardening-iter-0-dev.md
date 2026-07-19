# goal-ops-hardening-iter-0 Dev Handoff

**Phase:** goal-ops-hardening-iter-0
**Date:** 2026-07-19
**Agent:** developer
**Status:** complete

## What Was Built

**baseline verify-only — no changes.** Per the iter spec's IN SCOPE section ("None — verify-only. No
source files are created or modified this iteration") and BACKGROUND note ("the developer step below is
a deliberate no-op"), this step made zero code, config, dependency, or migration changes. No servers were
started and no browser interaction was performed by this step — the iter spec explicitly assigns the
empirical live-app verification to the downstream browser-QA agent ("the browser-QA agent's empirical run
against the live app is what actually determines pass/fail/partial per journey; the goal-evaluator records
it"). I also have no browser/Chrome MCP tool access in this session, so a live UI check was not possible
even incidentally.

What this step DID do: a code-level (static-read) investigation of each of the five target journeys
(J-01, J-03, J-04, J-05, J-06) against the current codebase, confirming/expanding the decomposer's own
preliminary analysis in the iter spec's BACKGROUND section and `runs/goal-session-ops-hardening/state/
blueprint.md`, with concrete file:line evidence. These are **preliminary, code-level hypotheses**, not
empirical verdicts — the browser-QA agent's live run is authoritative, and only the goal-evaluator marks
pass/fail/partial in `journey-history.json`.

## Per-Journey Observations (code-level, preliminary)

### J-01 — Backfill honors requested range and explains zero-work: **preliminary FAIL**

- `DataProviderRun` (`apps/backend/app/models.py:105-134`) has fields `provider, started_at, finished_at,
  symbols_ok, symbols_failed, status, message, dismissed, job_id` — **no `dates_total`, no per-date
  exclusion-reason field, no non-trading/already-snapshotted/error-other breakdown.** Confirmed by grep:
  zero matches for `dates_total|exclusion_reason|non_trading|already_snapshotted` in `models.py`.
- More significant than the missing schema: `_do_backfill`'s target computation
  (`apps/backend/app/engine/data_manager.py:2496-2504`)
  ```python
  allowed = _cadence_allowed_dates(session, trading_days, cfg)
  targets = [
      d for d in trading_days
      if prog.start <= d <= prog.end
      and d not in snapshot_dates
      and (allowed is None or d in allowed)
  ]
  prog.dates_total = len(targets)
  ```
  filters by `_cadence_allowed_dates` (`data_manager.py:2381-2409`) **unconditionally, with no
  explicit-request-vs-automatic-warm-up distinction**. `config.yaml`'s `snapshot_cadence` is
  `deep_cadence: monthly`, `daily_start: "2026-06-01"` (`config.yaml:1264-1265`) — every day in May 2026 is
  BEFORE `daily_start`, so under the current code only the first trading day of May (plus any
  walk-forward/bootstrap date that happens to fall in range) is `allowed`. A backfill request for
  2026-05-02 → 2026-05-29 today would almost certainly compute `dates_total` far below the goal.md-required
  19 (likely 0 or 1), not `dates_total = 19` — directly contradicting J-01's acceptance criterion. Today's
  `prog.dates_total` also **excludes already-snapshotted dates from the count entirely** (`d not in
  snapshot_dates`), which is a different meaning than goal.md's contract ("`dates_total` counts trading
  days in the requested range" — ALL of them, with a separate breakdown partitioning them).
- goal.md's own "Additional binding notes" anticipates exactly this gap: "the `snapshot_cadence` gate ...
  remains for automatic warm-up density only; explicit backfill requests override it (J-01, 'requested
  range always wins')" — this override does not exist in code today.
- No structured breakdown of non-trading/already-snapshotted/error-other exists anywhere in the job
  progress or `DataProviderRun` — only `prog.dates_total`, `prog.snapshots_created`, `prog.date_failures`,
  and a free-text `prog.message` string (`f"snapshots {prog.dates_done}/{prog.dates_total} dates"`).
- **Verdict basis:** surface (structured exclusion-reason schema + explicit-range-overrides-cadence logic)
  is not yet implemented — per the spec's NOTES section this is "FAIL with reason 'surface not yet
  implemented'," not blocked/NA.

### J-03 — No per-run range cap: **preliminary FAIL**

- `config.yaml:57`: `max_range_days: 370` is present, unchanged.
- `validate_job_request` (`apps/backend/app/engine/data_manager.py:1834-1839`) still enforces it:
  ```python
  span_days = (end - start).days + 1
  if span_days > cfg.data_manager.max_range_days:
      raise ValueError(f"date range too large: {span_days} days exceeds the configured maximum {cfg.data_manager.max_range_days}")
  ```
- The three pinning tests goal.md names are all still present and still assert the cap:
  `test_validate_job_request_reads_config_max_range` (`test_data_manager.py`, asserts a small
  `max_range_days` rejects a larger span), `test_post_job_over_long_range_is_400`
  (`test_api_data.py:301-308`, "default max_range_days is 370; a ~3-year span exceeds it" → asserts HTTP
  400), and `test_config.py:477` (`assert cfg.data_manager.max_range_days == 370`).
- A backfill request spanning 2025-06-01 → 2026-07-17 (>370 days, TC-6) would raise `ValueError` → HTTP 400
  today, contradicting "the request is accepted — no 'date range too large' rejection."
- **Verdict basis:** surface not yet implemented (cap + its validation + its pinning tests all still
  present exactly as goal.md describes).

### J-04 — Non-blocking boot with visible status: **preliminary PARTIAL**

Substantial existing infrastructure (mcp-loop legacy, iter-28/iter-33) already covers part of this
journey — this is NOT a clean fail:

- `app.engine.readiness.compute_readiness`/`compute_preflight` (`apps/backend/app/engine/readiness.py`)
  already compute a single honest `ready` / `initializing` / `unavailable` state plus `{done, total}`
  warm-up progress, served only by `GET /api/health`.
- The frontend already renders visibly distinct states: `HealthBadge`
  (`apps/frontend/components/health-badge.tsx:39-74`) shows "Checking backend…" (loading), "Ready" (green,
  `data-state="ready"`), "Initializing… history n/m" (amber, pulsing, `data-state="initializing"`), or
  "Backend unavailable" (red, `data-state="unavailable"`) — four visually distinct presentations, not one
  generic state.
- `ReadinessProvider` (`apps/frontend/components/readiness-provider.tsx:54-78`) sets `state: "unavailable"`
  honestly in its poll `catch` block on ANY fetch failure (network error / connection refused) — so killing
  the backend process should flip the badge from "Initializing…"/"Ready" to "Backend unavailable" within one
  poll interval. This looks like it would satisfy TC-10's "visibly distinct" requirement, but I did not
  empirically trigger a kill+observe cycle (no browser tool; deferred to browser-QA).
- `main.py`'s boot sweep (`sweep_orphaned_runs`, called at `main.py:59-66`) already marks any orphaned
  `running` `DataProviderRun` row as `interrupted` on every boot — this looks like it already satisfies
  TC-12 ("that job shows an explicit interrupted/error state"), pending live confirmation.
- **Confirmed still missing:** `scripts/start-backend.sh` (full file read) execs uvicorn directly with no
  `ulimit`, no `MALLOC_ARENA_MAX` export, and no log redirection — `grep -rn "ulimit\|MALLOC_ARENA_MAX"
  scripts/` returns zero matches anywhere in `scripts/`. `config.yaml:1319-1320` declares
  `server.memory_cap_mb: 6144` / `malloc_arena_max: 2` but nothing reads or applies them at process start.
  TC-11 (persistent logfile that ends abruptly on a killed process, no clean-shutdown entry) cannot pass
  today — no such file is written; uvicorn's output only goes to the invoking terminal.
- **Discrepancy worth flagging:** `reports/perf-budgets.md` (the iter-25 mechanical-pass section) contains
  the prose "literal `ulimit -v 6291456` KB = 6144 MB cap applied by `start-backend.sh`" describing a past
  measurement. That does not match the current script's content (no ulimit anywhere in it). Either that
  cap was applied manually in the measuring shell at the time (not encoded in any committed script) or the
  script has since regressed/was never actually the enforcement point. Flagging for whoever builds J-04's
  enforcement so the fix targets the right layer.
- **Verdict basis:** the UI-state-distinction half of this journey looks likely to already work (pending
  live confirmation); the logfile + memory-cap-enforcement half is confirmed absent. Net: partial, not a
  clean pass or fail. The ≤5 s boot-time criterion (TC-8) itself was not measured by this step (no server
  started) — today's DB is warm with the latest trading date (2026-07-17) already snapshotted per goal.md's
  own "Ground truth" note, and `main.py`'s fast-ready boot design makes `ensure_latest_snapshot` an
  idempotent no-op on that warm date — which suggests boot COULD already be fast, but this is a hypothesis
  for the browser-QA agent to measure, not a developer-confirmed fact.

### J-05 — Aggregates precomputed at ingest, never on the fly: **preliminary FAIL**

- No `coverage_snapshot` table exists: `grep -n "coverage_snapshot" apps/backend/app/models.py` returns
  nothing.
- `_do_backfill` (`apps/backend/app/engine/data_manager.py:2467` onward)'s per-date finalize work is only
  `scanner.persist_run_payload` / `get_run_for_date` + `forward_testing.backfill_run_forward_returns`
  (see the `_persist` closure, `data_manager.py:2512-2560`) — **no call to warm coverage, market-phase, or
  research hot-key caches** at backfill finalize time. `grep -n "compute_coverage\|market_phase_cache\|
  membership_timeline_cached\|event_study_cache" data_manager.py` shows `membership_timeline_cached` is
  only invoked from inside `_compute_coverage_body` (`data_manager.py:882`) — i.e., still on the REQUEST
  path when coverage is computed, not proactively refreshed by ingest.
- `compute_coverage`/`_compute_coverage_uncached` (`data_manager.py:703-806`) is still the per-request
  compute path: an in-process single-flight + result cache (`_COVERAGE_RESULTS`, capped at
  `_COVERAGE_CACHE_MAX_KEYS`, keyed by membership stamp) that is **lost on restart** (not persisted to the
  DB) and whose cold path (`_compute_coverage_uncached` → `_compute_coverage_body`) calls
  `prefilled_bar_cache(session, expected_symbols=pool_symbols)` — a full-candidate-pool bar prefill,
  matching goal.md's documented "Ground truth" offender description almost exactly.
- `market_phase_cache` and `event_study_cache` do exist as persisted tables (this part of goal.md's
  Data Contract row is accurate — "tables and serving reads already exist"), but their warm trigger is
  still boot-time (`warmup.py`'s `_run_warmup` calls `_warm_membership_timeline` at the end of the
  background warm-up thread, itself launched from `main.py`'s `lifespan`, not from `_do_backfill`) — the
  "move the warm-from-boot trigger into ingest finalize" half of J-05 has not happened.
- **Verdict basis:** surface not yet implemented — no ingest finalize hook refreshes any of the five named
  aggregates (latest-date snapshot excepted, which already flows through the existing boot/backfill paths
  unchanged); coverage remains request-computed and restart-fragile.

### J-06 — Pages load only what they need: **preliminary PARTIAL**

- `reports/perf-budgets.md` (621 lines) already carries a substantial, actively-maintained budget history:
  item A (the iter-19 OOM fix), items B–K (iter-24/25 mechanical pass), and a full re-measurement as
  recently as iter-41 (2026-07-16) showing every existing committed budget (`/api/health` ≤0.1s,
  `/api/stocks` ≤1.5s, `/api/stocks/AAPL` ≤0.3s, `/api/data` ≤1.5s, four page loads ≤3s each) holding with
  "yes." So the EXISTING budget contract (mcp-loop legacy) looks well-maintained, not neglected.
- What is confirmed absent: I searched the whole file for a boot-specific row (`grep -in "process start|
  boot budget|≤ 5 s|first.*200"`) and found no committed "process start → first `/api/health` 200" budget
  row under the ≤5 s contract goal.md's Success Criteria names, and no cold `/api/data` row measured under
  the CURRENT (iter-41-rebuilt) data basis — the existing cold-path numbers in the file are from the
  iter-19/iter-25 OOM-fix investigations (older data basis, framed around memory footprint, not a
  committed never-regress latency row).
- No code-level audit statement (the spec's step 3: "a code-level audit that no on-load endpoint performs
  an unbounded `daily_prices` scan or recomputes an inventory aggregate") has been written yet as a
  committed artifact — though the J-05 findings above already surface the one standing violation
  (`compute_coverage`'s lazy full-pool prefill on the `/api/data` request path).
- **Verdict basis:** the existing warm-endpoint/page budgets look intact; the two NEW rows goal.md's J-06
  asks this cycle to add (boot budget, current-basis cold `/api/data` budget) plus the explicit code-audit
  writeup do not exist yet — a gap, not a regression of what is already committed.

## Files Changed

None (source). This step is read-only against the codebase. The only filesystem writes from this step are:

- `docs/handoffs/goal-ops-hardening-iter-0-dev.md` — this handoff.
- `runs/goal-ops-hardening-iter-0/status.json` — pipeline status marker.

(`docs/phases/goal-ops-hardening-iter-0.md`, `runs/goal-session-ops-hardening/state/blueprint.md`,
`runs/goal-session-ops-hardening/state/assumptions.md`, `reports/goal-lint.md`, and
`reports/goal-session-ops-hardening-index.html` were already present before this step — written by the
decomposer/prior pipeline steps, not by this one.)

`git status`/`git diff` show zero changes under `apps/` or `config.yaml` — confirmed before writing this
handoff.

## Tests Run

None required. Per the spec's TESTING REQUIREMENTS: "Unit/integration: none required (no code paths
changed this iteration)." No code was modified, so there is nothing new to test, and per project memory
the full backend suite is a ~10-11 hour run on this host's 30-year fixture — not run here. I did confirm
(via `grep`, not execution) that the three tests goal.md cites as pinning `max_range_days = 370` are still
present and unchanged in intent: `test_validate_job_request_reads_config_max_range`
(`test_data_manager.py`), `test_post_job_over_long_range_is_400` (`test_api_data.py:301`), and the
`max_range_days == 370` assertion (`test_config.py:477`).

## Known Issues

- **No live/browser verification was performed by this step, by design.** The iter spec assigns the
  empirical pass/fail/partial determination to the browser-QA agent; I also have no browser/Chrome MCP
  tool in this session. Everything above is a code-level hypothesis grounded in file:line evidence, not an
  observed runtime result. In particular, J-04's timing claims (≤5s boot, ≤250ms poll cadence, badge
  screenshot) and the crash-simulation steps (TC-9–TC-12) need an actual restart/kill cycle against the
  running app to confirm.
- **ulimit/MALLOC_ARENA_MAX discrepancy** (detailed under J-04 above): a `reports/perf-budgets.md` prose
  note from a past iteration claims `start-backend.sh` applies the `ulimit -v` cap; the current script does
  not, and no other script under `scripts/` does either. Whoever builds J-04's enforcement should resolve
  which layer historically applied it before assuming `start-backend.sh` is starting from zero.
- **J-01's cadence-vs-explicit-request gap is the load-bearing finding of this baseline.** It's a bigger
  gap than "missing exclusion-reason fields" — the current `_do_backfill` would likely under-deliver
  `dates_total` for the exact May-2026 range goal.md's J-01 walkthrough specifies, because
  `snapshot_cadence` (monthly before 2026-06-01) applies to every backfill call today with no
  explicit-request override. Whoever implements J-01 should treat "requested range always wins" as the
  primary code change, not an afterthought to the schema addition.
- No `journey-history.json` entries were written or modified by this step (only the goal-evaluator does
  that, per the spec's OUT OF SCOPE list) — it remains the empty placeholder
  (`{"journeys":{},"anti_goal_violations":[],"updated_at":""}`) seeded by the decomposer.
