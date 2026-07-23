# Iteration State — ops-hardening (after iter-13)

**Last verdict:** REGRESSION (iter-13) · **Prior:** CONTINUE (iter-12) · **Date:** 2026-07-23

## Journeys (5 Must-have)
| J | Status | Note |
|---|--------|------|
| J-01 | passing | replay PASS iter-13 |
| J-03 | passing | replay PASS iter-13 |
| J-04 | passing | CARRIED, not re-verified (boot-path files byte-unchanged); owes a live boot spot-check |
| J-05 | passing | replay PASS iter-13 (screenshot spot-checked) |
| J-06 | partial | over-budget blocker CLOSED (218/218/219ms /data, 70.5ms / — was 2138-2258ms); residual = perf-budgets.md transcription + walkthrough + AG-8 froze a frame |

## Active blockers (all owner-owned — session out of autonomous runway)
- **AG-8 CRITICAL (drove the REGRESSION):** forward_testing.py:826 unbounded ScannerResult load — byte-unchanged (TC-12) but this iter wedged the whole backend ~12min (health hung, operator hard-restart; UT-01-blocked-backend-hang.png + audit + closure all concur). Full outage, not a silent abort — the "mitigation holds / smaller than iter-7" premise is FALSIFIED. Owner: bounded rewrite / goal.md amend (+fail-fast +auto worker-recover) / raise cap.
- HOST_GUARD_REQUIRE_MARKERS — owner decision.
- demo.sh --session-live walkthrough (J-05/J-06) — no autonomous mechanism (iter-12 finding); owner/framework.

## Last 2 verdicts — why
- iter-13 REGRESSION: J-06 target fix landed & verified in budget, but critical AG-8 escalated to a full ~12-min availability outage (C.1 first-match). Resume with --acknowledge-regression into a FULL recovery iter.
- iter-12 CONTINUE: J-06 held partial — /api/indexes genuinely 43-51% over budget on an idle host (now fixed by iter-13).

## Do not redo (binding unless goal.md changes)
- iter-13 IndexSeriesCache / candidate #7 WORKS — do not re-implement; hot key is in budget.
- Do NOT touch forward_testing.py:826 as a product iter (owner-scoped rewrite); do NOT bundle it with other work.
- Do NOT re-measure the 10 in-budget J-06 pages, boot budget (1.364s iter-11), or re-run heavy-ingest pytest (settled iter-9).
- Do NOT touch health.py/readiness.py/main.py-boot/warmup.py/max_range_days/server.memory_cap_mb.
- Do NOT patch scripts/automation/* (merge FAIL-cell drop, Frontend-Present misroute) from a product iter.
- AG-10 launcher confinement + host-guard blocks DONE (iter-9/11) — do not re-open.

## Recovery-iter cleanup (agent-tractable, non-blocking)
- Transcribe iter-13 passing readings into reports/perf-budgets.md (closes J-06 single-source clause).
- Add a live J-04 boot spot-check (DoD-#7 literal); retire/rewire dead major-indexes-card.tsx (UT-07).
