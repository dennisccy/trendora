# Goal Session ops-hardening — Assumption Ledger

Append-only. Each entry logs a spec decision that required interpreting an ambiguity in
`docs/goal.md` rather than a routine scoping pick. Zero entries for most iterations is normal.

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

## iter-1 — goal-decomposer

**Ambiguity:** goal.md's lessons/binding notes establish "requested range always wins" for
explicit backfill requests, but the cadence gate `_cadence_allowed_dates` today filters both the
plain `backfill`/`both` kinds AND the `rebuild` kind (which internally widens the range to the
full historical calendar before calling the same `_do_backfill`); it is not stated whether the
cadence bypass should extend to `rebuild` too.
**We chose:** scoped the "requested range always wins" bypass to explicit `backfill`/`both`
requests only. `rebuild` keeps applying `_cadence_allowed_dates` unchanged — no Must-have journey
this cycle exercises `rebuild`, the user does not supply its date range (`validate_job_request`
already exempts it from range validation), and changing its snapshot density is outside this
iteration's tested scope.
**Reversible:** yes

## iter-1 — goal-decomposer

**Ambiguity:** J-03's acceptance states "the chunk plan derives from the config `import_chunking`
values; the UI progress reflects the same plan the engine executes," but `_do_backfill` today has
no date-window chunking at all — `chunk_index`/`chunk_total` are populated only by the fetch/expand
stage. It is not stated whether removing the `max_range_days` rejection alone satisfies J-03, or
whether real date-window chunking must be added to the backfill stage.
**We chose:** read the acceptance language literally and scoped J-03 to include adding real
date-window chunking to `_do_backfill` (splitting `[start,end]` into
`import_chunking.date_window_days`-sized windows, populating the existing dormant
`chunk_index`/`chunk_total` fields the frontend already renders for fetch jobs) — not just the cap
removal.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** browser-qa scored the whole J-04 journey row `UT-J-04` as PASS, but J-04's full
Acceptance also requires a `scripts/start-backend.sh`-written persistent logfile and enforced
`memory_cap_mb`/`malloc_arena_max` — both explicitly OUT OF SCOPE this iteration and confirmed
unbuilt (dev handoff). The UT-J-04 step-5 log check passed against the harness's own
`fanout-backend-8255.log` (written by run-phase's fanout), not a start-backend.sh persistent log.
**We chose:** kept J-04 at `partial` (not promoted to `passing`) — treating the Required-still-
passing mandate as a non-regression check of J-04's 5 already-working sub-behaviors, not a
completion claim. The logfile + memory-cap acceptance bullets remain the open gap.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** J-01's DoD pins the productive May run's exact breakdown (19/19/0/9/28), but the
prescribed 2026-05-02→05-29 range had already been backfilled by a prior functional-QA pass before
the browser session began, so no fresh same-session productive submission was captured live — the
live submission hit the zero-work path instead.
**We chose:** scored J-01 `passing` on the productive path via three corroborating sources rather
than a fresh live run: the still-on-screen historical Run-History row (DOM-read exact match
"28 calendar days · 0 already snapshotted · 9 non-trading", 19 snapshots), the re-run's
`already_snapshotted=19` (UT-04), and the unit test `test_backfill_breakdown_invariants_hold_on_
fresh_and_rerun` which proves the fresh-run 19/19/0 by construction.
**Reversible:** yes
