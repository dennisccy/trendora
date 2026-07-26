# Iteration State — ops-hardening

**After iteration:** 25 · **Date:** 2026-07-26 · **Verdict:** GOAL_ACHIEVED

## Journeys

8 passing (J-01 J-03 J-04 J-05 J-06 J-07 J-08 J-09) · 0 partial · 0 failing · 0 unknown — 8 total.
All 8 re-verified with iter-25 evidence (replay 6/7 + LLM lane J-07/J-09; the J-07 replay FAIL was
environment-caused and overturned); all 8 `spec_hash`es match current `docs/goal.md`.

## Active blockers

- None blocking. Open, non-blocking: (a) audit T1's two rewritten backend tests NEVER finished a real pytest
  run (`test_health.py`, `test_readiness.py`; 1h+ `loaded_engine` fixture — needs an unloaded box, 5 reps);
  (b) OWNER, audit B5 — does the at-rest `<= 0.1 s` `/api/health` target stand as written? (`perf-budgets.md`
  iter-24 section: 0.100023 s official, 10-sample max 0.127788 s); (c) NEW — a FAILED boot warm-up leaves the
  badge on "Initializing… history 89/89" forever (`logs/backend.log:79986` this iter) — never a false
  "Ready", but not one of goal.md's three states; (d) audit B2 — a `Thread.start()` failure leaves the badge
  on "running (1)" for the process lifetime (decomposer-planned; needs the dispatch freeze lifted).

## Last 2 verdicts

- iter 25: GOAL_ACHIEVED — J-09's only gap (the `--session-live` walkthrough manifest) closed and verified by
  diffing the manifest; audit F1's honest "unknown" copy live-confirmed; scan CLEAN, coherence PASS, no AG.
- iter 24: CONTINUE — J-09 built and correct (badge + `/data` panel) but `partial` on its unbuilt walkthrough
  clause plus audit F1.

## Do not redo

- **J-09 demo steps n=13-16 are written and verified** (`reports/goal-session-ops-hardening-demo.json`;
  n=1-12 byte-unchanged, `highlights` at its 8-step cap). Never re-author, re-order, or re-cap.
- **Audit F1 is FIXED** — `apps/frontend/lib/background-compute-panel-branch.ts` + the panel branch in
  `app/data/page.tsx`. The genuine-idle copy is a regression guard: leave it byte-exact.
- **Audit T1 is FIXED in code** (identity/shape compare excluding `elapsed_ms`); only EXECUTION is owed.
- **Budget amendment = settled owner policy** (`perf-budgets.md` § "OWNER BUDGET AMENDMENT" + "Revision 1")
  and **TC-13/TC-14 DONE/PASS 2026-07-25** — never edit, re-litigate, or re-run.
- Byte-frozen: `app.engine.forward_testing` (incl. `ensure_historical_forward_aggregates_dispatched`
  keying/single-flight, except the planned B2 carve-out), `compute_readiness`, `compute_forward_aggregates`,
  `resolved_forward_aggregate_evidence`, J-08's serving split/empty-state machine — and never a 2nd poll or
  endpoint for J-09's disclosure (verified single-producer/single-endpoint).
