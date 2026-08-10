# Iteration State — ops-hardening

**After iteration:** 57 · **Date:** 2026-08-10 · **Verdict:** CONTINUE

## Journeys

6 passing (J-01 J-03 J-04 J-06 J-08 J-09) · 2 partial (J-05 J-07) · 0 failing — 8 total

## Active blockers

- **J-07 + J-05 step 4 — the memory ceiling (owner + dev).** 1 health poll of 1,212 got no answer for 10 s
  inside an ingest heavy-warm window (`runs/goal-ops-hardening-iter-57/tc7-health-poll.log`, last line);
  after a later MemoryError the process wedged — `/api/health` 200 "ready" while `/api/data`, `/api/runs`,
  `/api/stocks/AAPL/bars`, `/api/data/availability` all 500 (`logs/backend.log` ~11:28); MemoryErrors 8,104
  → 8,127. Owner decision (a), off-process compute, unanswered since round 50.
- **The TC-7 record is wrong (dev).** `reports/perf-budgets.md` Addendum 23 + the iter-57 dev handoff +
  `status.json` say "1,211 polls, ZERO non-200, no unresponsive gap"; the log has 1,212 records and one
  `000`. Replacement text is verbatim in `docs/handoffs/goal-ops-hardening-iter-57-audit.md` B1.
- **Two dev residuals.** `journey-scripts/J-05.json`'s date 2010-11-10 is consumed (`scanner_runs` 2946) —
  rotate before any replay. `data_manager.py:1722` sets `stale` from stamp inequality alone, so "updating"
  can show with no job running, and `availability-heatmap.tsx:247` gates the empty state on
  `cells.length === 0`, not on `stale === false`.

## Last 2 verdicts

- iter 57: CONTINUE — J-06 newly passing (all four recorded budget gaps closed, two re-measured by the
  evaluator); no regression; coherence PASS; 12 new minor ledger items, 0 critical.
- iter 56: ESCALATE — dispatched lean against its own `Depth: full`; its availability fix left a false "no
  data" message on `/data` for the length of every ingest job.

## Do not redo

- **J-06's four budget fixes are DONE and verified** — `/api/health` recursive-CTE (591 == 591, 0.002 s vs
  0.175 s, re-run by the evaluator), bounded `sma_series`, plus iter-56's `/api/runs` + `/api/data/availability`.
- **The during-a-job availability lie is FIXED** — three-way branch in `availability_from_storage`; banner +
  real 5,391 cells proven in `reports/qa/goal-ops-hardening-iter-57-evidence/UT-03-result.png`.
- **`persisted_this_call` rollback honesty FIXED** in `data_manager.py` + `indexes.py` (TC-10); MCP
  `list_runs` grouped-aggregate rewrite DONE (`tools.py:715-744`), closing iter-56's coherence advisory.
- **J-06's golden has real paired budget gates** (sabotage-proven); its only weakness is a 4.5 s page-level
  bound, not per-call. **Framework track, NOT product scope:** that `demo_runner` resource-timing primitive, the replay lane, QA verdict-reading, the demo recorder (vendored `incredible_auto_dev/`).
