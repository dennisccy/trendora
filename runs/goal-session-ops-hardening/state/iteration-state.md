# Iteration State — ops-hardening (after iter-14)

**Last verdict:** CONTINUE (iter-14) · **Prior:** REGRESSION (iter-13) · **Date:** 2026-07-23

## Journeys (6 Must-have)
| J | Status | Note |
|---|--------|------|
| J-01 | passing | golden replay PASS iter-14 (+ evaluator spot-check) |
| J-03 | passing | golden replay PASS iter-14 |
| J-04 | passing | RE-VERIFIED LIVE iter-14 (real kill/restart UT-J-04; boot 1.80s TC-7) — carried gap closed |
| J-05 | passing | golden replay PASS iter-14 (spot-checked) |
| J-06 | partial | single-source gap CLOSED (TC-8 in perf-budgets.md); residual = walkthrough (owner) + UT-04 latency |
| J-07 | partial | NEW; AG-8 fix — memory/crash guarantee PROVEN (61.8% margin, 250/250 health); gaps = TC-6-partial + UT-04 + walkthrough |

## Active blockers
- **UT-04 (agent, cross-cutting — the item between J-07 & passing):** `/backtest` cache-MISS 211.8s under a CONCURRENT warm — honest/non-catastrophic, undiagnosed (audit F1: streamed-read longer lock-window). Lives in `app/engine/forward_testing.py` / shared DB contention; spot-check other data pages under a warm.
- demo.sh --session-live walkthrough (J-05/J-06/J-07) — owner/framework, no autonomous mechanism (iter-12).
- TC-6 live-process induction — owner: authorize a live pass, or accept TC-3 synthetic + TC-5 organic (evaluator ruled reasonable, not literal PASS).

## Last 2 verdicts — why
- iter-14 CONTINUE: AG-8 (the critical that drove the REGRESSION) RESOLVED — bounded/streamed rewrite, full-basis warm completes at 61.8% margin (evaluator-recomputed CSVs); J-06/J-07 partial (walkthrough + UT-04) → not GOAL_ACHIEVED.
- iter-13 REGRESSION: critical AG-8 escalated to a ~12-min full outage (now fixed by iter-14).

## Do not redo (binding unless goal.md changes)
- **AG-8 RESOLVED (iter-14): the `compute_forward_aggregates` bounded/streamed rewrite WORKS** — byte-identity 32/32, real ulimit-v induction, 61.8% margin. Do NOT re-open the streaming rewrite; it stays the SINGLE canonical producer (no 2nd path).
- J-04 live-verified + boot 1.80s (TC-7); J-06 TC-8 transcription DONE — do not redo either.
- Do NOT raise `server.memory_cap_mb` / `malloc_arena_max` (out of scope iter-13/14); do NOT touch health.py/readiness.py/main.py-boot/warmup.py; AG-10 launcher blocks DONE (iter-9/11).
- Do NOT patch scripts/automation/* (fixed d0799803) or the dead major-indexes-card.tsx from a product iter.
- Do NOT re-measure the 10 in-budget J-06 pages or re-run heavy-ingest pytest (settled iter-9/11).
