# Iteration State — ops-hardening

**After iteration:** 27 · **Date:** 2026-07-27 · **Verdict:** CONTINUE

## Journeys

4 passing (J-01 J-03 J-04 J-09) · 1 partial (J-06) · 3 unknown (J-05 J-07 J-08) — 8 total

## Active blockers

- **dev — browser-QA evidence missing for J-05/J-07/J-08.** The agent was killed mid-run by an account
  usage limit; `...-iter-27-ui-test-results.md` holds only the 5-row replay lane — no UT-02 (stale
  coverage) or UT-06 (concurrent `/backtest` race) row; closure = CLOSURE-FAIL. UT-06 needs a
  never-scanned date: 2011-03-10 and 2015-09-09 are consumed.
- **dev — the J-06 golden is self-defeating.** `journey-scripts/J-06.json` step 1 expects the incidental
  string "DEGRADED", from `config.yaml:1152` -> `runs/goal-session-mcp-loop/state/drift-report.json`
  (another session's file, which J-01's own replay rewrites). Product healthy: the banner reads "GO".
- **dev — new AG-8 finding, unresolved.** Unhandled `MemoryError` 500s on `GET /api/evidence`
  (`logs/backend.log:81850`, `:81932`) + ingest finalize (`data_manager.py:3361`); cause is the unbounded
  `ret_by_run_symbol` dict at `research.py:215`. Untouched by iter-27; no browser captured at failure.
- **owner, non-blocking** — historical `/backtest` took 738-1442 s in iter-27's logs vs the 16-23 s the
  open cold-load budget question was framed around. Card B-1107 (dispatch cap) stays optional.

## Last 2 verdicts

- iter 27: CONTINUE — both iter-26 anti-goal findings CLOSED in code and verified, but the browser lane was
  quota-killed before testing the 3 target journeys; one new minor AG-8 finding opened.
- iter 26: ESCALATE — a lean pass surfaced two unresolved anti-goal findings needing the full pipeline.

## Do not redo

- **iter-26 AG-8 (concurrent `/backtest` 500) FIXED + verified** — `_insert_run_forward_returns` tolerates
  the mid-loop duplicate-key collision narrowly; live races answered 200. Audit B1 fixed too.
- **iter-26 AG-3 (all-zero coverage panel) FIXED + verified** — `coverage_from_storage` serves a labeled
  stale prior row; the three new fields shipped and typed. TC-10 done (`perf-budgets.md` 19:14 -> 18:14Z).
- **Byte-frozen** — `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`, J-08's serving split, the demo JSON, the OWNER BUDGET
  AMENDMENT. Audit B2 (`_backfill` rollback residual) needs its own iteration.
- **Never** re-trigger a live memory-pressure background-compute failure (proven by test); never run the
  full pytest suite or two concurrent pytest invocations on this host.
