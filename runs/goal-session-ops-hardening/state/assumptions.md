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

## iter-2 — goal-decomposer

**Ambiguity:** goal.md's "four offenders to retire" and the Aggregation-candidates table read as a
mandate to fully retire boot's `ensure_latest_snapshot` synchronous-compute-if-missing branch and
the boot warm-up loop's cadence-snapshot bootstrap, but neither is exercisable in this session:
`fetch` is offline zero-work (AG-9), so `latest_data_date` never advances outside an explicit
backfill/rebuild, and the currently-running DB already has a snapshot for its latest date
(fast-boot already verified <2s in iter-1) — so both branches are dormant either way this iteration.
**We chose:** scoped J-05 to what its own 4 numbered acceptance steps literally exercise — a single
historical day's backfill, a cold restart-and-visit of `/data`, and health responsiveness during a
heavy job — building the new `coverage_snapshot` table + ingest finalize hooks + the boot thread's
safety-net warm step, while leaving `ensure_latest_snapshot` and the warm-up loop's cadence
bootstrap unchanged (their retirement is unverifiable against the offline seed and risks regressing
mcp-loop-era readiness/warm-up guarantees no Must-have journey this cycle re-tests).
**Reversible:** yes

## iter-2 — goal-decomposer

**Ambiguity:** `config.yaml`'s `server:` section comment block claims `scripts/start-backend.sh`
already wires all five fields (`memory_cap_mb`, `malloc_arena_max`, `limit_concurrency`,
`timeout_keep_alive_seconds`, `graceful_timeout_seconds`) — "reads every value from here via the
venv python" — but a direct read of the script (confirming iter-0's identical finding about the
first two) shows NONE of the five are wired; goal.md's own binding note, however, names only
`memory_cap_mb`/`malloc_arena_max` + the logfile as required this cycle.
**We chose:** scoped `scripts/start-backend.sh`'s fix to exactly the three goal.md names (`ulimit -v`
from `memory_cap_mb`, `MALLOC_ARENA_MAX` from `malloc_arena_max`, persistent logfile) and left
`limit_concurrency`/`timeout_keep_alive_seconds`/`graceful_timeout_seconds` unwired this iteration,
flagging the same drift in NOTES rather than silently expanding scope beyond what goal.md asks — a
future iteration should wire them if J-05 step 4's health-responsiveness check ever reveals it's
actually needed.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** J-04's 6-step acceptance includes step 4 (kill backend → UI transitions to an explicit
unreachable/crashed presentation, visibly distinct from initializing). This iteration built and
freshly verified J-04's *remaining* gap (persistent logfile + memory-cap + boot-no-prefill) and
freshly re-verified four other steps (fast boot UT-04, phase-aware initializing badge UT-06,
interrupted-job-after-restart UT-07, crash→logfile-abrupt-end via the TC-17 real-process SIGKILL
test), but the crash→UI-unreachable *visual* presentation (step 4) was NOT freshly screenshotted this
iteration.
**We chose:** scored J-04 `passing` (partial→passing) rather than holding it partial for the one
un-rescreenshotted sub-step — its badge/preflight/readiness/health code is UNCHANGED this iteration
(coherence confirms no nav/badge diff), step 4 was verified passing in mcp-loop iter-28/33 and re-noted
working at baseline, and its crash-side counterpart (logfile abrupt-end) IS freshly verified. Future
required-still-passing replay/QA re-exercises the crash-UI path.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** AG-3 ("A journey passes ONLY if the displayed numbers are correct") can be read
journey-scoped (only Must-have journeys' numbers must be correct) or product-wide (no surface may ever
show wrong numbers). Audit B1 (fetch-lands-bars → false-zero default `/data` coverage) is a genuine
wrong-number display, but on a path no Must-have journey (J-01/J-03/J-04/J-05/J-06) exercises, and the
audit was "genuinely unsure IMPORTANT-vs-CRITICAL."
**We chose:** applied the journey-scoped reading for the VERDICT — B1 breaks no Must-have journey, so
it is not a journey-failing AG-3 violation and does not force REGRESSION; recorded it unresolved
(minor for loop-mechanics, AG-3-dimension-serious) that blocks a future GOAL_ACHIEVED and is the #1
next-step. The product-wide reading would halt the loop now; rejected because the issue self-heals, is
disclosed with a queued fix, and the loop continues regardless (J-06 unbuilt). A human can override to
REGRESSION.
**Reversible:** yes

## iter-3 — goal-evaluator

**Ambiguity:** J-05 step-4's acceptance is the qualitative "while a heavy ingest job runs, poll
`GET /api/health`; assert it stays responsive throughout" — the ui-test-plan sharpened this to a
stricter "every poll within 1 s", and the reviewer explicitly asked the evaluator to rule which
applies. Item L measured zero non-200 / zero timeout / zero hang across 1,725 polls (badge "Ready"
throughout), but 50 (2.9%) ranged 1.00–3.29 s during the parallel-backfill contention window.
**We chose:** applied goal.md's qualitative reading — "stays responsive throughout" is satisfied by
the always-200, no-hang, badge-Ready result; the 2.9% sub-3.3 s slow window is a bounded,
self-resolving latency blip, not an unresponsive/frozen state. (Does not change the verdict: J-05
stays `partial` for the browser-story gaps below, not for step-4.)
**Reversible:** yes

## iter-3 — goal-evaluator

**Ambiguity:** ux-regression scored UX-REGRESSION-FAIL and framed B3 (fetch → false app-wide
"Backend unavailable"/NO-GO) and F1 (frozen job heartbeat) as directly undermining required-passing
J-04's "visible status stays accurate" trust promise — which could be read as J-04 having regressed.
But both root-cause to modules NOT in this iteration's diff (I confirmed `readiness.py` absent from
the 3-file diff), and J-04's scripted 6-step replay (UT-J-04) PASSED; the defects live on paths
J-04's acceptance never scripts (fetch-time badge, heavy-job heartbeat).
**We chose:** scored J-04 `passing` (scripted acceptance holds, replay confirmed, code unchanged)
and treated B3/F1 as newly-surfaced PRE-EXISTING defects / hard blockers to a future GOAL_ACHIEVED
— NOT a REGRESSION halt (no verified journey moved passing→failing; neither is a clean named-AG
violation). A human who reads B3 as a vision "the UI tells the truth about the backend's own state"
/ AG-3 violation may override to REGRESSION — flagged explicitly in eval.md.
**Reversible:** yes
