# Iteration 52 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-52
**Date:** 2026-08-08
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

---

## Scope of this iteration (confirmed from the diff, not just the spec)

`git diff cfbac3e6709e490181d3995b47a8da66cc0b20a9 --stat` (noise-excluded) touches only:

- `apps/backend/app/engine/data_manager.py` (+31/-4)
- `apps/backend/app/engine/forward_testing.py` (+10)
- `apps/backend/app/engine/research.py` (+281/-56)
- 4 test files (`test_data_manager.py`, `test_forward_testing_aggregates_streaming.py`,
  `test_research_streaming.py`, `test_start_backend_script.py`)
- `incredible_auto_dev/*` + `project-extensions/host-guard/host-guard.env` — vendored framework/host-guard
  hardening, unrelated to this product's IA or Data Contract; outside this audit's mandate.

`git diff --stat -- apps/backend/app/api apps/frontend` against the same SHA is **empty** — zero API
routes and zero frontend files changed. This independently confirms the iter spec's "Frontend Present:
no" / "Blueprint conformance: No new page, route, or nav entry" claims and the
`reports/phase-goal-ops-hardening-iter-52-ui-surface-map.md` summary ("Frontend surfaces changed (code):
0 ... New pages/routes: 0 ... Navigation changes: no").

## Data Contract check

Every touched function is a per-item/per-chunk loop **inside** an already-canonical producer; none of
them is a new endpoint, a new table, or a rival implementation of a registered value.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Job history & per-date exclusion reasons (finalize hook) | OK | `apps/backend/app/engine/data_manager.py:3706-3709` (coverage per-date `time.sleep(0)`), `:4128` (market-phase per-date), `:4176-4178` (forward-aggregates per-horizon) — same `_refresh_ingest_aggregates`/`_persist_per_date_coverage_snapshots`, same `_run_detail()` serializer, no new field |
| Regime score / realized forward-returns (`compute_forward_aggregates`) | OK | `apps/backend/app/engine/forward_testing.py:1263` — one `time.sleep(0)` per run-id chunk inside the existing loop; same producer, same 3 call sites (`GET /api/backtest`, MCP `query_backtest`, ingest warm), untouched signature |
| Membership timeline / research hot-key caches (`compute_factor_lab_all`, `_combination_observations`, `_factor_decile_observations`, `_all_factor_observations_by_horizon`) | OK | `apps/backend/app/engine/research.py:1427-1466` (per-(factor,horizon) yield + `_cyclic_gc_paused` + `_cooperative_sorted`), `:716`, `:768`, `:1264`, `:1586` (per-run-chunk yields) — same `app.engine.research` module, same `GET /api/research/factor-lab?all=true` endpoint, no second producer |
| Coverage payload (`_persist_per_date_coverage_snapshots` → `_compute_coverage_uncached`) | OK | `apps/backend/app/engine/data_manager.py:3706-3709` — yield only, same `refresh_coverage_snapshot_for` call, same `GET /api/data` endpoint |

**On `_cooperative_sorted` / `_cyclic_gc_paused` (`research.py:98-129`):** these are new **private helpers**
inside `app.engine.research`, not a second computing module. `_cooperative_sorted` replaces bare
`sorted()` calls at three call sites (`_average_ranks:240`, `_BoundedRankWindow._trim:622`,
`compute_factor_lab_all:1466`) with a chunked stable-sort + `heapq.merge` that the diff's own comments
argue is order-identical under a documented precondition (total order on the key), and the new tests
(`test_cooperative_sorted_is_byte_identical_to_sorted_across_the_chunk_boundary`, `..._without_a_key...`,
both in `test_research_streaming.py`) assert output by object **identity**, not just equality. This is a
mechanism swap inside the existing canonical function, not a new producer or a new served value — no Data
Contract violation. Whether the correctness argument actually holds (test coverage, edge cases) is a
reviewer/auditor question, out of this audit's mandate.

No new displayed value, no new field, no new endpoint appears anywhere in the diff — confirmed by the
`apps/backend/app/api` / `apps/frontend` empty-stat check above. Part A rules 4/5 (new-value
registration) do not apply; nothing new is displayed.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK | `git diff --stat -- apps/frontend` is empty against `cfbac3e6709e490181d3995b47a8da66cc0b20a9`; `apps/frontend/components/sidebar.tsx` unchanged |

The UI surface map lists only two categories for existing surfaces: "regression check" (unaffected: the
`/data` "Refreshed:" line, `/research/factor-lab`, `/research/factor-combination`, sidebar nav) and
"changed behavior, targeted-but-not-confirmed" (the global `HealthBadge`/`PreflightBanner` reliability and
`/data` job duration — reliability/timing claims about existing surfaces, not new ones). No IA check
applies since no feature moved, gained, or lost a home.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Blueprint row-Notes lag behind the shipped mechanism (Part C, precedented in this session).** The
  blueprint's iter-52 changelog paragraph (`runs/goal-session-ops-hardening/state/blueprint.md:361`) and
  the "Job history" row's Notes (`blueprint.md:418`) were written by the decomposer *before* dev ran (the
  blueprint diff against the snapshot SHA is only the changelog paragraph + that one row, and both predate
  the code diff) and describe only "periodic cooperative-yield points" (`time.sleep(0)`). The actual build
  went further after its first pass measured **worse**, not better (22 vs. 9 connection-level
  `GET /api/health` non-answers, `reports/perf-budgets.md` Item U/Addendum 12): a second fix pass added
  `_cooperative_sorted` (chunked stable-sort + `heapq.merge`, `research.py:98-129,143`) and
  `_cyclic_gc_paused` (`research.py:160`) to bound GIL-holding `sorted()` calls and stop-the-world gen-2 GC
  pauses — the actual measured stall sources. This is not a Data Contract violation (same module, same
  endpoint, byte-identity asserted by both the code's own precondition argument and new identity-based
  tests) — it is a documentation-completeness gap of exactly the kind this session has flagged and closed
  before: iter-9's `_checkpoint_run_record` landed undocumented in the Job history row and iter-10 named it
  explicitly; iter-46's boot-time `_warm_drawdown_expectations` trigger landed undocumented and iter-47
  named it. **Fix:** the next iteration's decomposer should append a short Notes update to the
  "Membership timeline / research hot-key caches" row (`blueprint.md:421`, which already covers
  `compute_factor_lab_all`/`factor_lab_all_cached`) naming `_cooperative_sorted`/`_cyclic_gc_paused` and
  the two-pass discovery (plain yield → measured worse → sort/GC-chunking fix), mirroring the iter-9→10 and
  iter-46→47 precedent already established in this file. Non-blocking; does not affect the goal.

- No other coherence-relevant observations. `incredible_auto_dev/*` and
  `project-extensions/host-guard/host-guard.env` changes in this diff are vendored-framework/host-guard
  operational hardening (thermal gate tightening, headless pump QA) unrelated to the product's IA or Data
  Contract — outside this audit's mandate (AG-10 compliance on that file is the evaluator/auditor's
  determination, not a coherence question).
