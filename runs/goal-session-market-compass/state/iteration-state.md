# Iteration State — market-compass

**After iteration:** 4 · **Date:** 2026-08-20 · **Verdict:** CONTINUE

## Journeys

4 passing (J-01 J-02 J-03 J-04) · 3 partial (J-05 J-06 J-09) · 2 failing (J-07 J-08) — 9 total

## Active blockers

- **human** — J-09 target missed: 3,439,100 kB vs ≤2,621,440 kB (`reports/perf-budgets.md:12114`).
  Real 28.9% cut, no owner-only cap touched. Owner picks: accept 3.44 GB · keep 2.5 GB and approve
  the `_BarCache.prefill` re-bound (goal.md Constraints (c)) · set another target. Agents may NOT move it.
- **human** — J-06 step 2: "the underlying run is unavailable" can never render, because opening
  the page rebuilds the deleted day (iter-3 auditor B2). Reword, or change dated-page as-of resolution.
- **human** — J-01 steps 1-2 unexecutable as written (destructive backfill; an "Unassigned" filter
  option gone at 0%). Plus: is an empty "next-session focus" on the newest date acceptable? (AG-15)
- **dev** — J-05's flagship state was never seen live: no real close has ever sealed a manifest
  (`at_ingest` / version 1 / `prospective_eligible: true`); every one seen came from regenerate.
- **dev** — the J-01 replay golden has cried wolf twice with the identical false FAIL (the sector
  cell wraps across two DOM lines). Fix the golden's text match.

## Last 2 verdicts

- iter 4: CONTINUE — J-09 measured for the first time; 4 of 5 steps met, the memory number missed
  honestly; J-01–J-04 re-verified passing; coherence PASS; no new anti-goal violation.
- iter 3: CONTINUE — J-05/J-06 built and largely correct but never journey-verified end-to-end; a
  critical AG-12 export-overwrite bug was found AND fixed inside the iteration.

## Do not redo

- `database.pragmas.cache_size` is DONE at `-65536` (`config.yaml:109`). Do not re-tune it; do not
  touch `pool_size` 24 / `max_overflow` 44 / `memory_cap_mb` 8192 / `malloc_arena_max` 2.
- VmPeak re-measurement DONE and dated (`reports/perf-budgets.md` Addendum 40). Do not re-run the
  ~31-min heavy drill; do not re-measure until a lever actually changes.
- Byte-identity across `/api/dashboard`, `/api/stocks`, `/api/market-phase`, `/api/compass` PROVEN.
  AG-12 export-overwrite FIXED (`compass.py:860`). AG-2 advice-tail CLOSED, guard covers candidates.
- STILL OWED: the `[NEW]` walkthroughs for J-01–J-04 (three iterations overdue — needs the demo
  lane, so full depth), plus goal.md Constraints (a) memory-pressure test gating and (b) `next
  build` ≤4 workers, both unassigned and both due before two backends run.
