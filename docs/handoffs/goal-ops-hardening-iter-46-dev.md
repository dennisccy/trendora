# goal-ops-hardening-iter-46 Dev Handoff

**Phase:** goal-ops-hardening-iter-46
**Date:** 2026-08-04
**Agent:** developer
**Status:** complete (code + tests), with an important honest caveat on the live-drill outcome — see "Known Issues"

## What Was Built

- **`app.engine.research._combination_observations` bounded (research.py:748-813)** — refactored from a
  single unbounded `ret_by_run_symbol` dict built over the ENTIRE horizon's `forward_returns` population
  (1,285,609 rows measured live at horizon=20) into the SAME discover-once/chunk-and-discard pattern its
  sibling `_factor_observations` already uses (iter-29): `_runs_with_fr` discovers the distinct run ids
  once, walked in slices of the EXISTING `research.factor_join_run_chunk` knob; each slice reuses the
  SAME `_fr_slice_map` helper `_factor_observations` already uses (its `max_drawdown` half simply unused
  here) instead of a second near-duplicate builder. No new config knob. `observations` output is
  byte-identical (proven by TC-3).
- **`app.engine.forward_testing.compute_drawdown_expectations` bounded (forward_testing.py:2270-2434)** —
  the `stored_by_key` read was already ticker-chunked (`research.drawdown_expectations_ticker_chunk`,
  iter-36) and `yield_per`-streamed, but every chunk's rows landed in the SAME dict, retained WHOLE until
  the separate phase-aggregation loop ran afterward over the full `rows` list — a bounded READ, unbounded
  RETENTION (the exact shape the session's iter-40 lesson names). Restructured so each chunk's slice
  (now built by a new named helper, `_drawdown_ticker_slice_map`, mirroring `research.py`'s
  `_fr_slice_map`) is folded into `by_phase_mdd`/`by_phase_uw`/`by_phase_ttr`/`by_phase_returns`
  immediately and discarded before the next chunk's query starts. This required indexing the
  already-in-memory `rows` list (the `compute_samples` cohort — bounded by claim resolution already, NOT
  the accumulator being bounded) by ticker once (`rows_by_ticker`). The four by-phase accumulators are
  order-insensitive (`_median_p90` sorts internally; `_loss_streak_cell` collapses-by-date and sorts
  chronologically internally), so folding per chunk instead of in the original `rows` order changes
  nothing about the emitted `by_phase` payload — byte-identical (proven by the existing pinned-reference
  test at multiple chunk widths, plus the new TC-2 size-bound test). No new config knob.
- **Guarded the last two unprotected `logger.exception` calls in `data_manager.py`** —
  `_fail_unlaunched_job` (`:5058`-area, its own `_finalize_run_record` persistence-failure handler) and
  `_fail_unlaunched_resume` (`:5091`-area, its own checkpoint-rebuild-failure handler), disclosed as a
  "Known Issues" carry-forward by the iter-45 dev handoff (not on the iter-45 audit's own T4 list, so
  left alone under that pass's fix-mode scope discipline). Both now call the existing
  `_log_isolation_failure` degrade-to-marker helper (already applied at the other 19 sites, iter-44/45),
  closing the module's LAST two bare `logger.exception` sites in an isolation handler.
- **TC-6 verification** — checked `journey-scripts/J-07.json`'s two dataset-size anchors against the live
  running backend BEFORE the TC-7 backfill drill: `"n=14647"` (`/backtest`, horizon-60 Bucket A) and
  `"2532"` (`/data`, gap count) both matched the live, current values exactly — no correction needed at
  that point. **Caveat:** the TC-7 live drill below (a single-day backfill) inserted 840 new
  `forward_returns` rows, which will shift the `/backtest` figure once its cache re-warms after the
  backfill's finalize tail completes (still in flight as of this handoff — see "Known Issues"). QA should
  re-verify `"n=14647"` against the THEN-current live value before relying on it, per iter-45's own
  disclosed caveat that this is a derived aggregate that moves with every ingest. The `/data` gap-count
  anchor (`2532`) will also shift once the backfill's coverage snapshot finally persists.

## Live drills (TC-4, TC-7) — run against the real backend via `scripts/start-backend.sh` / `scripts/start-frontend.sh`

**TC-7 (J-05's defining case):** confirmed `2005-05-16` genuinely absent from `/api/runs` (the first date
in `/api/data`'s `gaps_preview`, `gap_first`), then submitted it as a single-day backfill via
`POST /api/data/jobs`. **Result: did NOT reach a terminal state within 300 seconds — still `running` at
handoff time** (~16+ minutes elapsed). This is the outcome `assumptions.md`'s iter-46 entry explicitly
predicted: every currently gap-fillable date in this DB is chronologically EARLIER than the latest cached
snapshot (`gap_last = 2019-02-25` vs latest `2026-07-31`), so every live-testable case is a **historical
gap-fill**, which hits the EXISTING full membership-timeline recompute fallback (iter-45's already-built
append-forward fast path only accelerates dates chronologically AFTER the cache — out of scope for this
iteration's diff, per `assumptions.md`). The job's own snapshot+forward-return insert finished in ~22s
(`stages.backfill.elapsed_seconds: 22.4`, `forward_returns_inserted: 840`), then it entered the finalize
tail (`J-07 finalize-tail cache_ctx liveness` logged once) and has been silently inside
`refresh_coverage_snapshot` → `_compute_coverage_uncached` → `membership_timeline_cached`'s full
(non-fast-path) recompute ever since — `current_activity` and `last_progress_at` both frozen at the same
value for the whole window, zero further log lines. **Not wedged**: VmRSS grew slowly but steadily
throughout (6,045,344 kB → 6,057,560 kB over 150s, ~80 kB/10s) and one worker thread stayed in the
kernel's `R` (running) state the entire time — genuine (if very slow) forward progress, not a deadlock.
Scored honestly as **NOT MET within the 300s window** — neither outcome (a) reach `ok` nor (b) fail with a
now-traceable reason; a third, undisclosed-by-the-spec outcome (still running, no error, matching the
already-known-slow gap-fill path). `logs/backend.log` names nothing because nothing has failed.

**TC-4 (Evidence page under concurrent load):** while the same backfill's finalize tail ran, polled
`GET /api/health` at ~1 Hz and issued `GET /api/evidence` roughly every 20s for the ~320s drill window,
then a follow-up single `GET /api/evidence` with a 40s budget. **Result: `GET /api/evidence` never
returned within 40 seconds on any attempt** (15 attempts during the timed drill, all timed out at the
15s client budget; one dedicated follow-up attempt timed out at 40s). `GET /api/health` degraded
severely but stayed intermittently reachable: 27 polls, 6 outright client-timeouts (>5s), the rest
ranging 0.1s (before the job started) up to 4.5s once it was running — both well outside the committed
≤2s bounded-compute-window budget and the ≤0.1s steady-state budget. **Root cause, confirmed via
`/proc/<pid>/task/*/stat`: exactly ONE of the process's 31 threads was in the kernel `R` state, all
others `S`** (sleeping) — classic GIL starvation, not memory exhaustion. **Zero `MemoryError` entries
appear in `logs/backend.log` anywhere in the drill's time window** (grep confirmed) — the SPECIFIC
mechanism this iteration bounds (`_combination_observations`'s and `compute_drawdown_expectations`'s
accumulators) never fired a `MemoryError` this run, and VmRSS never approached the 8192 MB cap
(peaked ~6.1 GB, 74% of cap, growing at a rate that would take many hours to reach it). **So the narrower
"no MemoryError-triggered outage" objective this iteration's code change targets was met; the STRICTER
DoD wording ("the page returns HTTP 200 within its committed budget… `GET /api/health` stays responsive
throughout") was NOT met**, because the single Python process's GIL is monopolized by the SAME slow
synchronous historical-gap-fill membership-timeline recompute TC-7 hit — a pre-existing, disclosed,
out-of-scope mechanism (CPU/GIL contention from one long synchronous call), not a new regression this
diff introduced and not the memory-accumulator bug this iteration fixes. Reported honestly as **NOT MET**
on the strict acceptance wording rather than rounded to a pass — see "Known Issues" for the scope
argument and a recommended follow-up.

## Files Changed

- `apps/backend/app/engine/research.py` — `_combination_observations` refactored to the chunked
  discover-once/slice-and-discard pattern; docstring updated. No other function changed.
- `apps/backend/app/engine/forward_testing.py` — `compute_drawdown_expectations` restructured to fold
  each ticker chunk into the by-phase accumulators immediately; new `_drawdown_ticker_slice_map` helper
  extracted (mirrors `research.py`'s `_fr_slice_map`) so tests can wrap/observe its live per-slice size.
- `apps/backend/app/engine/data_manager.py` — `_fail_unlaunched_job` (`:5058`-area) and
  `_fail_unlaunched_resume` (`:5091`-area) now call `_log_isolation_failure` instead of a bare
  `logger.exception`.
- `apps/backend/tests/test_research_streaming.py` — new `combination_chunked_engine` fixture (5 runs x 3
  tickers, `record_json` carrying the live certified-claims ledger's own two component factors,
  `rs_spy_3m` + `high_proximity`), a pinned pre-fix reference (`_combination_observations_reference_unchunked`),
  and three new tests: TC-1 size-bound (`test_combination_observations_accumulator_is_chunk_bounded`),
  TC-3 byte-identity at as_of=None and a historical as_of
  (`test_combination_observations_chunked_equals_unchunked_reference`), and a no-lookahead guard
  (`test_combination_observations_chunked_as_of_excludes_runs_after_cutoff`).
- `apps/backend/tests/test_forward_testing.py` — new TC-2 size-bound test
  (`test_drawdown_expectations_stored_by_key_accumulator_is_chunk_bounded`, wraps
  `_drawdown_ticker_slice_map` via monkeypatch on the existing `dd_expectations_engine` fixture at
  `drawdown_expectations_ticker_chunk=1`). TC-3 byte-identity for this function was already fully covered
  by the EXISTING `test_drawdown_expectations_chunked_byte_identical_to_pinned_reference` (parametrized
  chunk widths 1/2/3/50 against the iter-36 pinned reference) and
  `test_compute_drawdown_expectations_combination_claim_kind_resolves` (a real combination-kind claim
  shape resolving end-to-end) — both re-run green against the refactor, no changes needed to either.
- `apps/backend/tests/test_data_manager.py` — two new tests (TC-5):
  `test_fail_unlaunched_job_persistence_failure_survives_a_raising_logging_call` and
  `test_fail_unlaunched_resume_checkpoint_rebuild_failure_survives_a_raising_logging_call`, both driving a
  TEXTLESS `MemoryError()` from inside the guarded logging call, mirroring the session's established B3/
  B5/B6 test convention.
- `runs/goal-session-ops-hardening/journey-scripts/J-07.json` — checked, NOT modified (both anchors
  verified current at check time — see the "Caveat" above for why they may drift once the TC-7 job's
  finalize tail completes).

## Tests Run

Commands (targeted selections only, per the session's standing ~10-11h full-suite caution):

```
cd apps/backend
.venv/bin/python -m pytest tests/test_research_streaming.py -q -p no:randomly
  → 45 passed in 10.99s

.venv/bin/python -m pytest tests/test_forward_testing.py -k "drawdown" -q -p no:randomly
  → 27 passed, 62 deselected in 504.45s

.venv/bin/python -m pytest tests/test_data_manager.py \
  -k "fail_unlaunched or log_isolation_failure or fatal_job_failure" -q -p no:randomly
  → 7 passed, 162 deselected in 1.09s
```

**Total: 79 test executions across 3 targeted files/selections, zero failures, zero regressions.** No
full-suite run.

Live drills (not unit tests): TC-4 and TC-7, both run against the real backend/frontend started via
`scripts/start-backend.sh` / `scripts/start-frontend.sh` on the committed seed DB — see the dedicated
section above for full results.

## Known Issues

- **TC-7 did not complete within its 300s window; still running at handoff time.** Job
  `70b3085dfb9d46dba741ef7f7a820259` (backfill, `2005-05-16`) was still `status: "running"` ~16+ minutes
  after submission, stuck in the historical gap-fill's full membership-timeline recompute (NOT the
  append-forward fast path — every currently-gap-fillable date in this DB is chronologically earlier than
  the latest cached snapshot, so no live-testable append-forward case exists, per `assumptions.md`
  iter-46). This is the SAME `iteration-state.md` "Do not redo" item this session has carried since
  iter-45: extending the fast path to historical gap-fill inserts is explicitly out of scope for this
  iteration. The job is not deadlocked (VmRSS still growing, one thread still runnable) and will very
  likely eventually reach `ok`, but not inside any bounded interactive window. **Recommend**: QA should
  either poll this SAME job to completion before scoring J-05 (it may finish before QA runs), or trigger
  a fresh drill and expect the same multi-minute-plus duration; either way, score J-05/TC-7 on the actual
  observed outcome, never assume success.
- **TC-4's strict response-budget acceptance was not met, root-caused to GIL/CPU contention, not memory.**
  During the SAME concurrent historical gap-fill, `GET /api/evidence` never returned within 40s and
  `GET /api/health` degraded to several seconds per poll (some client-timed-out at 5s). Confirmed via
  `/proc/<pid>/task/*/stat`: exactly one of 31 threads was CPU-runnable throughout — the single Python
  process's GIL is monopolized by the synchronous, unlogged-per-iteration membership-timeline full
  recompute the SAME historical gap-fill triggers. Zero `MemoryError`s were logged in this window and
  VmRSS stayed well under the 8192 MB cap (peaked ~6.1 GB) — this iteration's two accumulator bounds are
  NOT implicated; the two functions they bound were never even reached long enough to matter, because the
  bottleneck is earlier in the SAME job's finalize tail (`refresh_coverage_snapshot`), a call chain this
  iteration's spec explicitly scoped OUT (only the two named accumulators, plus the two logger sites, plus
  the J-07.json anchor check — the out-of-process watchdog, the sixth `_BarCache.prefill` attempt, and
  `warmup.start_warmup`'s thread-launch-guard gap all remain carried/unrelated). **Recommend a future
  iteration's card**: the historical gap-fill's full membership-timeline recompute is a single long
  synchronous call that starves the WHOLE process (not just its own request) — bounding its OWN peak
  footprint won't fix this; it needs either genuinely cooperative chunking (yielding the GIL between
  batches) or a real incremental algorithm for the gap-fill case (the class of work iter-45 deliberately
  deferred). This is a NEW, distinct finding from this iteration's own two named accumulator sites — not
  a rediscovery of the out-of-process-watchdog idea already carried.
- **`journey-scripts/J-07.json`'s `"n=14647"` anchor is expected to drift** once job
  `70b3085dfb9d46dba741ef7f7a820259`'s finalize tail eventually completes (840 new horizon-spanning
  forward returns already inserted, not yet reflected in the cached `/backtest` aggregate as of this
  handoff — `aggregates_refreshed` was still `[]`). Not corrected here because the live value was still
  in flux at write time; QA must re-verify against the THEN-current value, per TC-6's own instruction and
  iter-45's identical disclosed caveat.
- Every other item from `iteration-state.md`'s "Do not redo" list and the phase spec's OUT OF SCOPE
  section is unchanged and untouched by this diff (the out-of-process watchdog, the sixth
  `_BarCache.prefill` attempt, `warmup.start_warmup`'s thread-launch-guard gap, the Regime Lab pooled
  dispatch, etc.).

---

# Fix Notes — FIX PASS (QA FAIL, 2026-08-04)

**Input:** `reports/qa/goal-ops-hardening-iter-46-qa.md` (Verdict: FAIL, 3/8 journeys PASS).
No failure-digest file existed for this phase.

## The QA report's root-cause attribution was wrong, and that changed the fix

Both this handoff's original "Known Issues" and the QA report attributed the `/evidence` budget failure to
**GIL contention from a concurrently-running backfill's finalize tail** — and concluded it was an
out-of-scope architectural issue to be escalated, not fixed. I measured it instead of accepting it.

**On a fully idle backend with NO ingest job running at all**, a cold `GET /api/evidence` took
**163.3 s** (HTTP 200, 100% CPU, exactly one runnable thread, ~1.0 GB RSS). The requests immediately after
took **11–53 ms**. A concurrent job was never needed to blow the budget — so this was never GIL contention,
and it was never out of scope: it is the Evidence serving path, which is precisely this iteration's target
surface.

Two of the QA report's four blockers were therefore fixable inside this iteration, and are now fixed.

## What was fixed

**1. `/evidence` cold miss after a restart — the boot-warm gap (QA blocker 3 → J-06, J-07)**
`warmup._warm_drawdown_expectations` (new). The per-claim `drawdown_expectations` `EventStudyCache` was
warmed by the INGEST finalize tail (iter-7/audit B1) but by *nothing* after a plain restart — so every
backend restart left the next Evidence viewer paying the full 7-claim cold compute synchronously on the
request path. QA restarted the backend immediately before its browser sweep, which is exactly why it hit
this twice (UT-J-06 step 7, UT-J-07 step 4/8) and why "in isolation" did not help.

The new step mirrors its two established neighbours (`_warm_membership_timeline` iter-36,
`_warm_coverage_snapshot` iter-2) verbatim: own session on the engine, idempotent (a warm row is a cheap
HIT), non-fatal at BOTH the ledger-read and per-claim levels, and the same
`type == FORWARD_WALK_TYPE` / `entry.get("claim")` filters `build_evidence_payload` applies, so the warmed
cache subjects match exactly what a live request looks up. It is sequenced **after** the warm-up record
settles `ok` and gated on a successful warm-up — deliberately OFF the readiness path, because the badge
J-04 and J-07 step 1 depend on must flip `Ready` on its existing schedule.

**2. Zero-work backfills never reaching a terminal state (QA blockers 1 + 4 → J-01, J-03)**
`data_manager._refresh_ingest_aggregates` called `refresh_coverage_snapshot` **unconditionally** on every
backfill/both/rebuild. Every other heavy step in that tail is already `dataset_version`-cached (a cheap HIT
on a zero-work job), so this was the ONE uncached heavy call left — a full `_compute_coverage_uncached`
derivation with its own whole-bar prefill, paid even when the persisted row already reflected the exact
current stamp. That is why QA run 287 (`dates_total: 0`, two weekend dates) sat in `running` for 15+ min.

The fix applies the SAME `_coverage_snapshot_is_current` gate that iter-3 (audit B1) added for exactly this
purpose and that the fetch/expand branch has used ever since — no new mechanism. It is a redundancy check,
never a freshness compromise: any job that actually lands a bar or snapshot moves
`_membership_dataset_version`, so the canonical refresh still runs (proven by TC-A2).

**3. TC-6 — the J-07 dataset anchor was genuinely stale (QA recommendation 5)**
QA left TC-6 PENDING. Checked against the live DB: `/backtest`'s `n=14647` still holds, but `/data`'s
canonical `coverage.gap_count` is now **2526**, not the committed `2532` (the original pass's own TC-7
backfill filled six gaps, exactly the drift this handoff predicted). The literal `2532` still appears in the
`/api/data` payload, but only as an unrelated symbol's `bar_count` — a coincidental substring, not the stat
the journey anchors on. `journey-scripts/J-07.json` step 3 corrected `2532` → `2526`.

## Live verification (prod-mode launch scripts only, per AG-10)

Backend restarted via `scripts/start-backend.sh`; for the cold-path drill the 7
`drawdown_expectations` cache rows were deleted first (a pure recomputable cache) to force a genuine miss.

| Signal | Before | After |
|---|---|---|
| `/api/health` 200 | 28–35 s | **35 s** (unchanged) |
| readiness `ready` (J-04 / J-07 step 1 badge) | 41 s | **41 s** (unchanged — warm is off the readiness path) |
| evidence cache warmed | never on a restart | **385 s**, entirely in background, all 7 claim panels |
| first `/api/evidence` a user can hit | **163.3 s** | **17–64 ms** |
| zero-work backfill (2026-07-25→26, `dates_total: 0` — QA run 287's shape) | `running` 15+ min | **`ok` in 5 s** |
| 412-calendar-day backfill (2025-06-01→2026-07-17 — J-03's shape) | `running` 10+ min | **`ok` in 5 s** (283 trading days) |

The zero-work job's `aggregates_refreshed` came back
`['forward_aggregates', 'research_hot_keys', 'drawdown_expectations']` — `coverage`/`membership_timeline`
honestly ABSENT because nothing was recomputed, per the module's "actually did something" convention.

Post-drill: backend `/api/health` 200 (0.09 s), frontend :3255 200, `/api/evidence` 200 (0.028 s). Both
services left running.

## Tests

Targeted selections only (never the full suite — ~10-11 h on this basis).

```
tests/test_ingest_finalize_zero_work_coverage.py  (NEW)          2 passed
tests/test_ingest_finalize_fault_injection.py                    5 passed
tests/test_backfill_coverage_shared_cache.py                     3 passed
tests/test_data_manager_jobs_pipeline.py                        21 passed
tests/test_research_streaming.py            (TC-1/TC-3)         45 passed
tests/test_data_manager.py -k "fail_unlaunched or ..." (TC-5)    7 passed
tests/test_warmup.py -k "nonfatal or single_flight or ..."       7 passed  (incl. 3 NEW)
```
**Total: 90 test executions, 0 failures, 0 regressions.**

New tests: TC-A1 (a zero-work finalize reaches `_compute_coverage_uncached` ZERO times — a call-count
contract mirroring iter-3's own TC-2, never a wall-clock assertion) and TC-A2 (a genuinely stale stamp
still refreshes and still reports both categories); plus three warm-up proofs — every ledger claim warmed
with `forward_walk` records skipped, a **textless** `MemoryError` (`str(MemoryError())` is `""`, per the
session's standing lesson) proven non-fatal, and a sequencing proof reading the job's own status at the
moment the warm is invoked (so the readiness badge cannot regress).

## Known Issues (honest status after this pass)

- **J-05 / TC-7 remains UNMET and is still out of scope.** A historical gap-fill still hits the full
  membership-timeline recompute. The phase spec's OUT OF SCOPE section excludes extending iter-45's
  append-forward fast path to historical gap-fill inserts, and this pass did not touch it. Every
  live-testable gap in this DB (`gap_first` now 2005-05-24, `gap_last` 2019-02-25) is chronologically
  earlier than the latest snapshot, so no live append-forward case exists to drill. Not fixed, not rounded
  to a pass.
- **A cold window remains between `ready` (41 s) and warm completion (385 s).** An Evidence view landing
  inside it still pays the cold miss. Disclosed, not closed — closing it means attacking the cost itself
  (below), not the warm's placement. **QA should let the warm finish before scoring J-06 step 7 / J-07**,
  or expect that window's cold read.
- **NEW FINDING, deliberately NOT fixed here (recorded per fix-mode scope discipline).**
  `_drawdown_ticker_slice_map` — the helper this iteration itself introduced — filters only on
  `(horizon, symbol)`, never on the cohort's snapshot dates, so it reads **7,994,388 forward-return rows
  across 71 calls to serve 7 claims**, when only the cohort's `(ticker, snapshot_date)` keys are ever
  looked up. A date filter would be provably byte-identical (the surplus rows are never read) and would
  further tighten the very AG-8 bound this iteration set out to establish. Measured cost breakdown of the
  163 s cold miss: `compute_samples` 272.5 s / 85%, `_drawdown_ticker_slice_map` 40.0 s / 12%,
  `phase_context_by_date` (uncached, called once per claim) 4.2 s / 1%. Full detail:
  `reports/perf-budgets.md` Item N.
- **`/backtest`'s `n=14647` anchor may drift again** on the next ingest that lands forward returns — it is
  a derived aggregate. Verified current as of this pass.
- The two accumulator bounds from the original pass are unchanged and still green; no `MemoryError`
  appeared anywhere in this pass's logs, and RSS peaked ~1.6 GB against the 8192 MB cap.

---

# Fix Notes — AUDIT FIX PASS (audit FAIL, 2026-08-04)

**Input:** `docs/handoffs/goal-ops-hardening-iter-46-audit.md` (Verdict: FAIL). No failure-digest file
exists for this phase (`reports/qa/` carries only the QA report and the evidence directory).

This is a **deliberately small** pass. The audit's own §5 is explicit — *"Keep the code. The accumulator
work is sound, proven, and should not be reverted or redone"* — and it classifies its two IMPORTANT open
gaps (B2, B3) plus B4 as work for the **next** iteration, outside this phase's IN SCOPE list. I did not
override that: opening the Evidence serving path a second time in the same iteration would be a second
risky change (session rule 5) and would make the re-review diff unreviewable. What I fixed is what was
both listed and inside this phase's scope; everything else is reported unmet, with evidence, below.

## Per-finding disposition (every audit finding, no omissions)

| # | Severity | Disposition |
|---|---|---|
| **B1** — zero-work coverage gate skips a clear-and-recreate rebuild | IMPORTANT | **Already fixed in-audit; verified by me, not taken on faith.** The `not prog.new_snapshot_dates` clause is present at `data_manager.py:3803` and `test_ingest_finalize_zero_work_coverage.py` carries all three tests (TC-A1/A2/**A3**). Re-run green + re-drilled live (below). |
| **B2** — the evidence cache stamp folds `count(forward_returns)`, so any concurrent ingest cold-starts all 7 claims → **TC-4 unmet** | IMPORTANT | **NOT fixed — remains UNMET.** Rationale and the operational consequence for the pending browser lane are below. |
| **B3** — third unbounded whole-cohort materialization at `samples.py:145/156` | IMPORTANT | **NOT fixed.** Audit's next-step #3; needs its own pinned byte-identity oracle. |
| **B4** — `_drawdown_ticker_slice_map` has no snapshot-date filter | GAP | **NOT fixed.** Audit's next-step #4. I accept the audit's correction of the handoff's wording: the *query* is character-identical to the pre-fix inline query, so this is an iter-36 characteristic that the extracted helper inherited, not something this diff introduced. |
| **B5** — `refresh_coverage_snapshot`'s docstring is now false | OBSERVATION | **FIXED** (`data_manager.py:1312-1323`). |
| **T1** — browser lane is entirely pre-fix | IMPORTANT | **Not a developer action** — the lane must be re-run. The build is left live, warm and ready; prerequisites and an ordering hazard are listed below. |
| **T2** — TC-9 screenshot uniqueness violated (no J-05 capture at all) | IMPORTANT | **Not a developer action.** Flagged for the lane; the audit's own recommendation (an `md5sum` + journey→file injectivity gate inside the runner) is a framework change, out of this product phase's scope. |
| **T3** — QA's `-k` selection missed two of the three new warm-up tests | GAP | **Addressed by giving the exact node IDs** (below) so the selection cannot miss them again. The auditor already ran all three green (2 passed in 203.50 s + the `-k` selection). |
| **T4** — TC-8's VmPeak-margin record was never written | GAP | **FIXED** — freshly measured live and recorded as **Item O** in `reports/perf-budgets.md`. |

## What changed in this pass (2 files, both listed findings)

- `apps/backend/app/engine/data_manager.py` — **B5 only**: `refresh_coverage_snapshot`'s docstring now
  states the real contract (called on every fetch/expand and every backfill/both/rebuild that the
  `_coverage_snapshot_is_current` gate finds **stale** *or* that created a new snapshot date; the only
  skip is a genuinely zero-work re-run), plus a note that this is the ingest tail's one uncached heavy
  call, so the gate is load-bearing. **No behavior change** — docstring text only.
- `reports/perf-budgets.md` — **T4 only**: new **Item O**, the dated VmPeak margin record TC-8 step 3
  requires, with provenance and an explicit statement of what the number does and does not cover.

Nothing else was touched. `git diff --stat` for this pass: `data_manager.py` (docstring) +
`perf-budgets.md` (Item O).

## Verification evidence gathered this pass (all live, all against the audit-fixed tree)

**Targeted tests** (never the full suite — ~10-11 h on this 30-year basis):

```
tests/test_ingest_finalize_zero_work_coverage.py                              3 passed in 0.61s
tests/test_data_manager.py -k "fail_unlaunched or log_isolation_failure
                               or fatal_job_failure"            7 passed, 162 deselected in 0.78s
```

**Live re-drill of B1's fix (the audit proved it by unit test only).** Zero-work backfill
`2026-07-25 → 2026-07-26` (Sat/Sun) on the audit-fixed build, submitted via `POST /api/data/jobs`:

| Signal | Value |
|---|---|
| Terminal status | **`ok` in 2 s** (`dates_total: 0`, `snapshots_created: 0`) |
| `aggregates_refreshed` | `['forward_aggregates', 'research_hot_keys', 'drawdown_expectations']` — `coverage`/`membership_timeline` honestly ABSENT because nothing was recomputed |

So the fix pass's J-01/J-03 improvement survives B1's added clause: the zero-work case still skips, and a
snapshot-creating job still cannot.

**Live state of the build I am handing over** (uvicorn PID 1761825, launched 09:05:06 via
`scripts/start-backend.sh`; banner `memory_cap_mb=8192 malloc_arena_max=2`, `host-guard: cpu_list=0-15
blas_threads=8`; `/proc/<pid>/limits` `Max address space = 8192 MB` — AG-10 confirmed on the process,
not assumed):

| Endpoint | Result |
|---|---|
| `GET /api/health` | 200 in 0.12 s — `readiness: "ready"`, `warmup 89/89 "ok"`, preflight `GO` |
| `GET /api/evidence` | 200 in **0.013–0.022 s**, **7/7 claims**, `expectations` populated on every one |
| `GET /api/backtest` | 200 in 0.020–0.052 s |
| `GET /api/data` | 200 in 0.063 s |
| frontend :3255 | 200 |
| `MemoryError` since this process booted | **0** (7,075 in the whole file, all historical) |

**TC-6 re-verified live at fix time** (it is a derived aggregate that moves with every ingest, so I
re-checked rather than trusting the audit's earlier reading): `/api/data` `coverage.gap_count` = **2526**,
matching `journey-scripts/J-07.json` step 3; `/api/backtest` contains **14647**, matching step 2. Both
anchors current — no correction needed. The zero-work drill above inserted **zero** forward returns, so
it did not move either anchor.

**T4 — the VmPeak margin record (now written).** 120 consecutive 1 Hz samples of `/proc/1761825/status`
+ `GET /api/health`, over 120.03 s on the fully-warmed fixed build:

| | Value |
|---|---|
| Cap enforced on the process (`ulimit -v`) | 8,388,608 kB = **8192 MB** |
| `VmPeak` — **flat across all 120 samples**, zero growth | **3,197,988 kB = 3,123.0 MB** |
| **Margin** | **5,190,620 kB ≈ 5,069.0 MB — 61.9% headroom (38.1% utilized)** |
| `VmHWM` / `VmRSS` max | 2,604.6 MB / 1,469.2 MB |
| `GET /api/health` | **120/120 HTTP 200**, mean 96.4 ms, max 104.0 ms, **0** polls over 2 s |

This process's lifetime includes the full boot warm (89/89 history, 2,869-date membership timeline, the
7-claim evidence warm), so the high-water mark already contains those peaks. **It is a steady-state
reading, NOT the under-load bounded-compute-window measurement** — TC-8 steps 1, 2 and 4 are *not*
re-verified by it, and Item O says so in the file.

## Why B2 was not fixed, and what it means for the pending browser lane

I agree with the audit's diagnosis and verified the mechanism: `compute_drawdown_expectations_cached`
keys on `_dataset_version` = `r{max(scanner_runs.id)}-f{count(forward_returns)}`, so a single inserted
forward return misses all 7 claims. The two closes the audit itself names are (a) re-warm right after the
backfill stage commits, or (b) serve the previous stamp behind an honest "recomputing" marker.

I evaluated (a) concretely before rejecting it: re-ordering the warm ahead of the finalize tail does
**not** satisfy TC-4, because the warm itself costs ~163 s idle (385 s measured live in background) while
the DoD budget is ≤3 s — the request landing during that window still pays a cold read. It would change
finalize-tail ordering (a real behavioral change with its own correctness surface) and buy nothing
against the acceptance wording. (b) is a new serving mechanism with a UI-visible marker in an iteration
whose spec says *Frontend: None* and *UI surface changes: None*. Both are the audit's next-iteration
items, not this pass's.

**TC-4 is therefore reported UNMET.** So is the GOAL's second clause (J-05's append-forward fast path —
no live case exists in this DB to prove it), and the GOAL's first clause is two-thirds delivered (B3).

**Operational hazard the lane must handle (this is the practical face of B2):** the evidence cache is
warm right now. **A journey that lands forward returns invalidates it and hands the next Evidence step a
~163 s cold read.** J-01's and J-03's shapes do not (zero-work and already-snapshotted ranges insert
nothing — re-confirmed above), but **J-05's does** (its backfill inserted 840 forward returns in the
original drill). Recommendation for the re-run: **execute J-05 LAST**, after J-06/J-07's evidence steps,
or re-warm before scoring them. Do not restart the backend immediately before the sweep without letting
the boot warm finish (~385 s) — that is precisely the trap the pre-fix lane fell into twice.

## Exact test node IDs for QA (closes T3's selection gap)

```
tests/test_warmup.py::test_warmup_warms_every_ledger_claim_and_skips_forward_walk_records
tests/test_warmup.py::test_warmup_evidence_warm_runs_only_after_readiness_reaches_ok
tests/test_warmup.py -k "nonfatal or single_flight or drawdown"
tests/test_ingest_finalize_zero_work_coverage.py          # TC-A1 / TC-A2 / TC-A3
tests/test_data_manager.py -k "fail_unlaunched or log_isolation_failure or fatal_job_failure"   # TC-5
tests/test_research_streaming.py                          # TC-1 / TC-3
tests/test_forward_testing.py -k drawdown                 # TC-2 + pinned byte-identity (~500 s)
```

The first two do **not** match `nonfatal`/`single_flight`/`drawdown` — they must be named explicitly.

## Known Issues (honest status at the end of this pass)

- **TC-4 UNMET (audit B2)** — unchanged and not attempted; see the scope argument above. This is the
  iteration's headline DoD item and it is not met.
- **The Evidence page's third unbounded site is still open (audit B3)** — `samples.py:145/156` builds and
  whole-sorts the entire observation list on the same `/api/evidence` path, and `logs/backend.log` has it
  `MemoryError`-ing at 02:20:31 on 2026-08-04. Two of three evidenced sites are closed; the GOAL sentence
  is partially achieved, not achieved.
- **B4 not fixed** — `_drawdown_ticker_slice_map` still reads 7,994,388 rows across 71 calls to serve 7
  claims. Provably byte-identical to fix; deliberately left for the next iteration per the audit's order.
- **T1/T2 remain open until the lane re-runs** — no browser journey has yet executed against the fixed
  build, and there is still no J-05 capture at all. Neither is closable by a developer pass.
- **J-05 / TC-7 remains unmet and out of scope** — every live-testable gap (`gap_first` 2005-05-24,
  `gap_last` 2019-02-25) predates the latest snapshot (2026-07-31), so this DB cannot present an
  append-forward case to drill. Unchanged from the previous pass.
- **No new defect was discovered during this pass**, so nothing is being carried silently.
- Services were left running as found: backend :8255 (PID 1761825, warm), frontend :3255. No process was
  killed or restarted by this pass.
