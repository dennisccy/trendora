# assumptions.md — archive

Entries moved out of `assumptions.md` by scripts/automation/lib/condense.sh (maintenance protocol §4).
Append-only: nothing here is ever deleted or rewritten.

<!-- condense.sh 2026-07-20T21:02:41Z: moved 2 entries (keep-iters=5) -->

## iter-0 — goal-decomposer

**Ambiguity:** `docs/goal.md`'s Product Shape names only 9 nav sections as "existing nav
unchanged" (Dashboard | Stocks | Sectors | Themes | Backtest | Research | Data | Watchlist |
Evidence), but the actual sidebar (`apps/frontend/components/sidebar.tsx`) has 11 items —
also Scanner Runs and Methodology, neither mentioned in that prose list.
**We chose:** treated the actual 11-item sidebar as ground truth for the blueprint's
Information Architecture; read goal.md's 9-item list as "these stay, at minimum," not "exactly
these and no others" — removing/hiding Scanner Runs or Methodology would itself violate the
Non-Goal "not a rewrite — additive to existing surfaces."
**Reversible:** yes

## iter-0 — goal-evaluator

**Ambiguity:** The iter spec's NOTES steer "surface not yet implemented → FAIL," and browser-QA
scored all five journeys FAIL under a strict PASS/FAIL/SKIP contract, yet the journey-history
schema offers a distinct `partial` status ("only some assertion steps passed"). J-04 had 5 of 6
numbered steps reproduce live (fast boot, phase-aware initializing badge, distinct crash
presentation, interrupted-job-after-restart — all inherited working from mcp-loop iter-28/33),
with only the persistent-logfile + memory-cap-enforcement step confirmed missing.
**We chose:** scored J-04 `partial` (not `failing`) to signal to the decomposer that only the
logfile/memory-cap layer remains, while keeping J-06 `failing` (its 8/11 fast pages are
pre-existing baseline behavior, not progress toward J-06's own new deliverables, all of which are
absent). Either way neither counts toward GOAL_ACHIEVED, so the CONTINUE verdict is unaffected.
**Reversible:** yes

