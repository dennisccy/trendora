# Iteration State — ops-hardening

**After iteration:** 65 · **Date:** 2026-08-12 · **Verdict:** CONTINUE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-08 J-09) · 1 partial (J-07) · 0 failing — 8 total. Raw replay 8/8 zero overturns; merged QA 8/8; 9 byte-distinct frames; 8/8 spec_hashes verified.

## Active blockers

- **J-07's last measured gap finally has an address (dev):** 1 poll of 1,057 took 2.370s, inside
  `coverage_membership_timeline_refresh`'s own 6.81s window — NOT `factor_lab_all_warm` (569.03s, zero
  breaches). Bound that step in `apps/backend/app/engine/data_manager.py`.
- **The instrument disagrees with itself (dev):** `poll_health.py` 1/1,057 over 2.0s vs the browser-QA
  lane's subprocess-per-poll loop 8/240 (max 4.194s), same evening (iter-65/a). Use one shared
  single-process counter in every lane, and record concurrent host load next to the poll CSV — the
  clean/elevated alternation (61 clean, 63/64 elevated, 65 clean) is unexplained on identical code.
- **OWNER-gated, 17th round:** does the ≤2s health ceiling apply to 17-minute jobs or only ~30s ones?
  J-07 cannot close either way without that sentence.
- **OWNER-gated:** `browser-qa-phase.sh` line-286-before-272 fix; cost sanction for two real ~17-minute
  ingest jobs per round (5th consecutive over-budget round: 8,247s vs 3,600s).

## Last 2 verdicts

- iter 65: CONTINUE — zero product diff; four escalating profiles found NO third GIL hold to bound, and
  the live drill came back clean (1,057/1,057 answered, 1 breach, 0 in `factor_lab_all_warm`).
- iter 64: CONTINUE — sentinel-date mechanism fixed and self-renewing; latency breach reproduced (59/930),
  since contradicted by iter-65.

## Do not redo

- **Do NOT re-profile `compute_factor_lab_all` for a third GIL/lock hold** — four independent escalating
  tests found none (perf-budgets.md Item Y / Addendum 31). A fifth profile buys nothing.
- **Do NOT re-run a control drill to attribute the iter-63/64 elevation** — four drills exist; the open
  question is the environment, not another repetition.
- `CHAIN_BACKEND_READY_WAIT_S` 90s is LIVE, verified in engine.log:10892 (iter-63/f closed).
- J-05's golden picks its own unused date at run time; self-renewed twice (2005-06-27/-28/-29).
- `/scanner-runs`'s iter-64 boundary: investigated, did not recur, no backend cause (iter-64/a closed) —
  reopen only on a new occurrence, frontend-side.
- J-05 walkthrough capture rides along as a passenger task only; never an iteration goal.
