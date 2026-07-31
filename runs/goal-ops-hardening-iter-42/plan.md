# goal-ops-hardening-iter-42 Execution Plan

## What to Build

Two headline closures, carried per the spec's own framing (Frontend Present: no — backend/tooling only):

1. **Close the target-journey verification gap** (the iter-41 audit's B2 finding, and iter-41's own
   binding lesson: "promoting a journey to `Target journeys:` silently removes its verification"). Give
   `Target journeys:` the same fresh-evidence guarantee `Required-still-passing journeys:` already has
   (from iter-41's A2/A3), end-to-end through `ui-test-designer` → `merge_ui_test_results.py` → every
   shell call site that wires `--required`. Then actually re-run J-05 and J-07 (this iteration's own
   targets) through the now-fixed lane.
2. **A fifth, differently-leveraged `_BarCache.prefill` bound attempt** (iters 35/36/37/41 each fell
   short — iter-41's own columnar rewrite compressed per-row cost ~2x but left the accumulator O(all
   rows) resident, per iter-41 audit finding B3). This iteration's lever, not tried before: reuse
   `load_only`'s already-proven `WHERE symbol IN (...)`-filtered, `yield_per`-streamed query shape for
   `prefill` when `expected_symbols` is given, PLUS audit whether `_compute_coverage_uncached`'s /
   `_membership_timeline`'s resolver loops actually need a symbol's full history or only a bounded
   trailing window.

Plus three small ride-along items that live in the same two files already being touched (B4, B6, T2 —
see IN SCOPE below).

### A. Target-journey verification lane (mirrors iter-41's A1-A4 shape, one level up)

- `incredible_auto_dev/agents/ui-test-designer/body.md` ("Backend-only phase handling"): also emit one
  `UT-<journey-id>` regression test case per journey named on `Target journeys:` (not only
  `Required-still-passing journeys:`), sourced the same way (that journey's own Steps/Acceptance text in
  `docs/goal.md`). Re-render `.claude/agents/ui-test-designer.md` via `sync-cli-assets.py --cli claude`
  after editing the neutral source — never hand-edit the mirror.
- `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py`: add a `target_journeys`
  parameter to `merge()`, plus `missing_target_journeys()`/`skipped_target_journeys()` (siblings of the
  existing `missing_required_journeys()`/`skipped_required_journeys()`, iter-41's A3/audit-B1) —
  additive: a target journey with zero rows OR an all-SKIP-only row forces the merged headline to
  `BLOCKED`, on top of (never replacing) the existing required-journey guard. Add a sibling `--target`
  CLI flag next to the existing `--required` flag. Extend the "Missing/Skipped Required Journeys"
  section (or a parallel "Target Journeys" section) so the gap is named explicitly.
- Thread the already-parsed `TARGET_JOURNEYS` (goal-iter-lean.sh, global) / `_bqa_targets`
  (browser-qa-phase.sh, local) values into the new `--target` flag at every `replay_lane_merge_results`
  call site in `incredible_auto_dev/scripts/automation/lib/replay-lane.sh`, mirroring the existing
  `REQUIRED_JOURNEYS` → `--required` wiring at `replay-lane.sh:454-461` exactly (same empty-set no-op
  behavior when target journeys is unset — plain phase mode is unaffected).
- `incredible_auto_dev/scripts/automation/lib/common.sh` (`ensure_services_running` /
  `_wait_for_frontend_ready`, B4): the frontend-readiness race that actually voided iter-40's browser
  lane (iter-41 audit finding B4 — the frontend missed its 90s window mid-restart, not the health-URL
  bug iter-41 fixed) is still open. `_wait_for_frontend_ready` (common.sh:1339) already exists as a
  bounded, corruption-aware re-probe; the gap is that not every restart path in the regression/replay
  flow re-probes through it before concluding SKIP. Investigate the call sites feeding the replay/browser
  lane's readiness decision after a mid-run backend/frontend restart and make sure a bounded wait-or-
  re-probe happens there too, instead of the whole regression run going silently all-SKIP on one
  premature timeout (TC-9).

### B. `_BarCache.prefill` bound attempt #5 (`apps/backend/app/engine/prices.py`)

- `_BarCache.prefill` (lines ~161-254): when `expected_symbols` is given, apply a `WHERE symbol IN
  (...)`-filtered query — the same shape `load_only` (lines 256-296) already proves — instead of an
  unconditional whole-table scan. Byte-identical `Bar` output required for whatever window each existing
  consumer actually reads (see `test_bar_cache.py`'s existing byte-identity harness from iter-41).
- **Known context for this investigation** (do not re-discover from scratch): both call sites that pass
  `expected_symbols` to `prefilled_bar_cache` (`_do_backfill` at `data_manager.py:3161` and
  `_persist_per_date_coverage_snapshots`'s fallback at `data_manager.py:3380`) currently pass
  `pool_symbols = {row["symbol"] for row in read_pool()}` — i.e. the full candidate-pool listing
  (`universe_pool.csv`, S&P 500 ∪ Nasdaq-100 ∪ prior-universe), not a caller-narrowed subset. Whether a
  `WHERE symbol IN (...)` filter against that set is a genuine bound depends on whether `daily_prices`'
  590-symbol population is a strict superset of that pool (e.g. historical/delisted names with bars but
  no current pool membership) — this is exactly the "differently-leveraged" lever the spec names, but it
  is unverified. The developer must check this empirically (row/symbol counts, `EXPLAIN`, or a live
  measurement) before claiming any reduction, per the binding iter-37 lesson quoted in the spec's NOTES
  ("assert the condition was actually live... an absence of a particular allocation in a trace is not
  proof it didn't happen if the code path was never reached").
- Separately audit `_compute_coverage_uncached`'s / `_membership_timeline`'s resolver loops
  (`_excluded_counts_by_date`, `data_manager.py:584-631`) — these ALREADY do not call `prefill`'s
  whole-table scan when standalone (iter-36 closed that; they use `load_only`'s batched, symbol-filtered
  path, or reuse an active outer job-scoped cache). Confirm this is still true post-change and note it —
  do not re-claim it as new work.
- **Honest fallback required by DoD**: if analysis shows every current caller of `prefill` genuinely
  needs the (near-)full universe's full history with no reachable bound short of a caller-semantics
  redesign, document that precise finding in the dev handoff and `reports/perf-budgets.md` for
  evaluator/owner disposition — do not re-claim AG-8 resolved on `prefill` if the measurement doesn't
  support it. This is the fifth attempt at this exact code (35, 36, 37, 41); a partial/negative result is
  an acceptable, expected outcome here, not a failure to hide.
- `_SymbolColumns`'s columnar accumulation and `prefill`'s row loop (B6, iter-41 audit observation):
  `array.array('d')` raises `TypeError` on a NULL numeric column, where the `list[Bar]` it replaced would
  have accepted `None`. Add NULL-tolerance — an honest NA sentinel or documented skip — so a NULL numeric
  column in `daily_prices` degrades instead of crashing (AG-8). `app/models.py:98-102` currently declares
  all five numeric columns NOT NULL, so this cannot fire on the current schema, but AG-8 explicitly names
  "new nulls" as a widening to survive.
- `reports/perf-budgets.md`: a fresh dated iteration-42 section with (a) a before/after latency figure
  for representative `bars_asof`/`bars_asof_window` reads over `_SymbolColumns` vs. the pre-iter-41
  baseline (T2, iter-41 audit observation — never measured), and (b) this iteration's own peak-memory
  (VmPeak) measurement for the `prefill` change (TC-6), following the same live-subprocess methodology
  iter-41 used (`/proc/<pid>/status`, identical fixture N_SYMBOLS/N_ROWS across arms).
- Correct the QA report's AG-8 disposition row (whichever report `qa` writes this iteration) to the
  accurate current state — bounded / partially bounded with the specific gap named / still open — never
  an unqualified "✓ PASS / no whole-table loads" unless the TC-6 measurement literally supports it
  (iter-41 audit finding B3: the QA report overstated this last time).

### Explicitly out of scope (do not touch)

- `GET /api/health` ≤0.1s budget (iter-34/j) — owner decision.
- `start-frontend.sh` → `HOST_GUARD_MARKER_FILES` (iter-33/i) — owner decision.
- Regime Lab's cold `view=pooled` background dispatch (iter-33/g) — deferred again.
- Any `docs/goal.md` edit (including the J-07 acceptance's "no unbounded whole-table load" wording).
- `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched`,
  `compute_forward_aggregates` — byte-frozen.
- `server.memory_cap_mb` re-tuning — byte-frozen.

No scope creep identified beyond the spec's own IN SCOPE list — everything above traces to a DoD/TC line.

## Agents Required

- backend-data: yes — `apps/backend/app/engine/prices.py` (`_BarCache.prefill`, `_SymbolColumns` NULL
  tolerance), `reports/perf-budgets.md`, plus the framework-tooling changes in `incredible_auto_dev/`
  (Python: `merge_ui_test_results.py`; shell: `common.sh`, `replay-lane.sh`; agent neutral source:
  `ui-test-designer/body.md`). All of this iteration's work is backend/tooling code — no frontend-ux
  agent needed.
- frontend-ux: no

## Frontend Present: no

## Files to Create/Modify

- `incredible_auto_dev/agents/ui-test-designer/body.md` — emit `UT-<journey-id>` for `Target journeys:`
  too, not only `Required-still-passing journeys:`.
- `incredible_auto_dev/.claude/agents/ui-test-designer.md` — re-rendered mirror via
  `sync-cli-assets.py --cli claude` (do not hand-edit).
- `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` — `target_journeys` param on
  `merge()`, `missing_target_journeys()`/`skipped_target_journeys()`, `--target` CLI flag, new self-tests.
- `incredible_auto_dev/scripts/automation/lib/replay-lane.sh` — thread `TARGET_JOURNEYS`/`_bqa_targets`
  into `--target` at the `replay_lane_merge_results` call site(s), mirroring the `--required` wiring.
- `incredible_auto_dev/scripts/automation/browser-qa-phase.sh`,
  `incredible_auto_dev/scripts/automation/goal-iter-lean.sh` — pass their already-computed target-journey
  variable through to the merge call (only if `replay-lane.sh`'s shared helper doesn't already cover both
  callers transparently — confirm before duplicating wiring).
- `incredible_auto_dev/scripts/automation/lib/common.sh` — B4: bound the frontend re-probe after a
  mid-run restart in the regression/replay readiness path.
- `apps/backend/app/engine/prices.py` — `_BarCache.prefill` symbol-filtered query path when
  `expected_symbols` given; `_SymbolColumns`/`prefill` NULL-tolerance (B6).
- `apps/backend/tests/test_bar_cache.py` — TC-6 (byte-identity within the actually-used window; the
  measurement's live-condition assertion per the iter-37 lesson), TC-8 (NULL-tolerance).
- `reports/perf-budgets.md` — new dated iteration-42 section: TC-6 VmPeak comparison, TC-10
  before/after `bars_asof`-family latency.
- `incredible_auto_dev/tests/automation/` — new/extended shell-level tests for the `--target` guard
  (TC-1/TC-2 shape, mirroring iter-41's `test-backend-only-regression-gate.sh` /
  `merge_ui_test_results.py self-test` pattern) and the bounded frontend re-probe (TC-9).
- `docs/handoffs/goal-ops-hardening-iter-42-dev.md` — dev handoff (required by DoD).

## UI Evolution

N/A — Frontend Present: no. No new user-facing capability, no new information displayed, no new user
actions, no UI surface changes, no navigation changes. J-05/J-07's existing surfaces (Data Manager,
global readiness badge, Backtest) are unchanged in shape.

## Visual Requirements

N/A — backend/tooling only.

## Key Test Scenarios

(Mirrors the spec's own TC-1 … TC-11, DoD-mapped; see the phase spec for full acceptance text.)

- TC-1/TC-2: a backend-only spec with `Target journeys: J-05` gets a `UT-J-05` row from
  `ui-test-designer`; a merged run with a target journey's row entirely missing (or all-SKIP-only) merges
  to `BLOCKED`, never a clean `PASS`/`SKIPPED`.
- TC-3/TC-4: J-05's golden script (`journey-scripts/J-05.json`) replays live — a fresh single-day
  backfill, `/scanner-runs` lists it with the stored snapshot, zero recompute-on-read; a cold restart's
  `/data` coverage payload renders from storage within budget with no 3.3M-row prefill trace in
  `logs/backend.log`.
- TC-5: J-07's golden script (`journey-scripts/J-07.json`) steps 1-2 replay live — `GET /api/health`
  stays 200 at 1Hz throughout a forward-aggregate warm, zero frozen windows.
- TC-6/TC-7: `_BarCache.prefill`'s peak resident memory for a subset-vs-full-universe job is measured
  live (with the iter-37 lesson's "assert the condition was actually live" check) and recorded in
  `reports/perf-budgets.md`; the QA report's AG-8 row states the exact disposition that measurement
  supports.
- TC-8: a NULL numeric column in `daily_prices` degrades honestly (NA sentinel/documented skip) through
  `_BarCache.prefill` instead of raising `TypeError`.
- TC-9: the browser-qa/replay lane re-probes a restarting frontend within a bounded window instead of
  going all-SKIP on one premature timeout.
- TC-10: before/after `bars_asof`/`bars_asof_window` latency over `_SymbolColumns` recorded in
  `reports/perf-budgets.md`.
- TC-11: full regression replay of J-01, J-03, J-04, J-06, J-08, J-09 (widened Required-still-passing
  set per ESCALATE cadence) all report PASS with dated evidence; refresh any golden script found to have
  selector drift.
- Unit tests pass; no regressions; `merge_ui_test_results.py self-test`, `goal_gate.py self-test`,
  `closure_gate.py self-test`, `artifact_schemas.py self-test`, `lint_contracts.py self-test`, and the
  shell integration suites (`test-replay-lane.sh`, `test-closure-gate.sh`) all still pass after the
  `--target` addition (additive-only — a spec with no target journeys must be byte-unchanged from before
  this iteration, mirroring iter-41's own `t_no_required_journeys_arg_unchanged` precedent).
