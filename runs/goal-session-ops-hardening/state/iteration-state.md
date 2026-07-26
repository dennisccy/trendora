# Iteration State — ops-hardening

**After iteration:** 24 · **Date:** 2026-07-26 · **Verdict:** CONTINUE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-07 J-08) · 1 partial (J-09, NEW this iter, steps 1-6 verified live)
· 0 failing · 0 unknown — 8 total. All 7 old journeys re-verified at iter-24 (replay 6/6 + LLM lane J-07);
all 8 `spec_hash`es match current `docs/goal.md`.

## Active blockers

- **J-09 walkthrough clause UNBUILT (agent-owned; the one item blocking closure):**
  `reports/goal-session-ops-hardening-demo.json` still holds iter-23's 12 steps and ZERO J-09 steps; the
  iter-24 spec never mapped that Acceptance bullet into DoD and `run-goal.sh` has no auto session-demo pass.
- Audit F1 (agent): on a failed health poll the `/data` panel prints "No background compute running…" for a
  state it does not know — `readiness-provider.tsx:87` + `app/data/page.tsx:3593,3603`.
- Audit T1 (agent): two new single-source tests compare two reads of live registry state
  (`test_health.py:113`, `test_readiness.py:292`) — false-alarm risk on any whole-file run.
- OWNER, non-blocking: at-rest `/api/health` `<= 0.1 s` — two runs on the SAME build disagree (max
  0.127788 s vs 0.094604 s); this diff adds zero DB work (audit B5). B-1107 stays owner-optional.

## Last 2 verdicts

- iter 24: CONTINUE — J-09 built and correct (badge + `/data` panel; AG-3 re-derived from the DB to 1.68 ms)
  but `partial` on its unbuilt walkthrough clause plus audit F1; scan CLEAN, coherence PASS, no AG violation.
- iter 23: GOAL_ACHIEVED — closed the two iter-22 CONFIRM-reject findings (demo steps for J-06/J-07/J-08;
  `J-06.json` timeout reverted 18000→8000); zero `apps/` diff.

## Do not redo

- **Budget amendment = settled owner policy** (`perf-budgets.md` § "OWNER BUDGET AMENDMENT" + "Revision 1"):
  never edit or re-litigate it, and never "fix" the transient BCW contention in code.
- **TC-13 and TC-14 are DONE/PASS, dated 2026-07-25** — never re-run. `J-06.json`'s `default_timeout_ms`
  = 8000 is investigated and cited. Demo steps n=1-12 stay byte-unchanged (`highlights` at its 8-step cap).
- `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, J-08's serving split/empty-state
  machine — byte-unchanged; cutover pruning (`forward_testing.py:1135-1156`) is load-bearing evidence.
- `ensure_historical_forward_aggregates_dispatched`'s keying/single-flight stays frozen EXCEPT one planned
  carve-out: audit B2 (pop the in-flight slot if `Thread.start()` raises) needs the freeze lifted on purpose.
- J-09's disclosure is verified single-producer/single-endpoint — never add a second poll or endpoint.
