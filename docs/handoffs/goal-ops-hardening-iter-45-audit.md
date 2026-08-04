# goal-ops-hardening-iter-45 Audit Report

**Date:** 2026-08-04
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** FAIL

The iteration's stated goal — make J-05's single-day backfill and J-07's heavy forward-aggregate warm
"actually reach a terminal outcome instead of stalling for ten-plus minutes or freezing the whole process"
— was not achieved. Both target journeys FAILED live: J-05's run 281 died with an uncaught `MemoryError`
producing no snapshot, and the backend then went **fully unreachable for ~42 minutes** (zero access-log
lines between `logs/backend.log:172574` and `:172965`), which is a *worse* observable outcome than the
stall this iteration set out to remove. Worse for the evaluator's purposes: the new fast path was **never
executed even once** in the live run — the ingest finalize hook is unreachable for a `failed` job
(`data_manager.py:4651`), so the iteration's central mechanism has zero live evidence behind it. The code
itself is well-built and I strengthened it (five fixes applied, each with a negative-controlled regression
test), but code correctness at 4-date unit scale is not the phase goal.

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (gap): the phase goal was not achieved; the service was fully unreachable for ~42 minutes.**
`reports/phase-goal-ops-hardening-iter-45-ui-test-results.llm.md` returns **FAIL, 0/2**.
- **J-05:** run 281 (`2019-02-25`) reached terminal `failed` at t≈4m46s, message `"MemoryError (no
  message)"`, `snapshots_created: 0`, `aggregates_refreshed: null`. Independently confirmed against the
  committed DB: `select count(*) from scanner_runs where asof_date like '2019-02-25%'` → **0**.
- **J-07:** last access-log line before the wedge is `logs/backend.log:172574`
  (`GET /api/health 200 OK`); the first after the restart is `:172965`. **Zero** access-log lines in
  between — a total response blackout, against TC-6's "never fully unreachable".
- **Mechanism** (this is the part no per-item isolation can fix): `logs/backend.log:172575`
  `Exception ignored in thread started by: <object repr() failed>` followed by `:172576` `MemoryError:` —
  **AnyIO worker-thread *creation* itself failed**. FastAPI dispatches sync endpoints through
  `run_in_threadpool`, so the event loop kept accepting connections (`ss` showed `Recv-Q=8`) while no
  handler could ever be dispatched: process alive, executing, logging — and answering nothing. The same
  signature appears 9 times across the log, so it is a recurring mode, not a one-off.
- **DoD impact:** TC-4 FAILED, TC-5 FAILED, TC-6 FAILED, TC-7 **never executed** (the browser lane could
  not reach step 4), and "Target journeys J-05, J-07 pass via browser-qa-agent" FAILED.

Not fixable in this audit: the out-of-process watchdog and the two unbounded evidence-path accumulators
(`research.py:777`, `forward_testing.py:2343` — 16 of 24 wedge-window `MemoryError`s enter through
`evidence.py:168`, a request-serving path) are all explicitly OUT OF SCOPE for iter-45.

**B2 — CRITICAL (gap): the iteration's central mechanism was never exercised; it has zero live evidence.**
`_refresh_ingest_aggregates` is reached ONLY when `final_status in ("ok", "partial")`
(`data_manager.py:4651-4653`). Run 281 was `failed`, so the finalize hook — the only path that drives the
new fast path during an ingest — never ran. Three independent confirmations:
- The hook's unconditional per-job liveness line (`data_manager.py:3617-3621`, `"J-07 finalize-tail
  cache_ctx liveness: job=%s"`) has **no entry** for job `79867db8...`; the last two in that process are at
  00:23Z, 15 minutes *before* the job was even created.
- `grep -n "_membership_timeline_incremental\|append-forward\|append_forward" logs/backend.log` → **no
  match** in 173,043 lines.
- The only membership-timeline work in that process was the boot warmup at 00:14:41Z.

Combined with the dev handoff's own honest disclosure that every live-testable backfill target is a
historical gap-fill (which the fast path deliberately does not accelerate), the claim that this fix
unblocks J-05/J-07 is **unproven**. TC-1/2/3 are sound but run at 3-4 dates against a hand-built fixture,
not the ~2,860-date live basis where the storm actually occurs.

**B3 — IMPORTANT (fixed): an unguarded `logger.exception` in `_run_job` could flip a successful ingest job to `failed`.**
`data_manager.py:4759` and `:4782` (pre-fix: bare `logger.exception`). This is the *same* third-escape
class iter-45 was chartered to close, one frame out of the guarded function.
- *Live-confirmed the path fires:* `logs/backend.log:172668` — a `MemoryError` raised inside
  `Session.__exit__` (SQLAlchemy `expunge_all()` → `identity.all_states()`), outermost frame
  `data_manager.py:4655 in _run_job / with Session(eng) as agg_session` — i.e. OUTSIDE every per-item
  handler iter-45 guarded.
- *Failure scenario:* that handler's own `logger.exception` allocates under the same exhausted cap and
  raises; the second exception escapes to `_run_job`'s outer `except`, which sets `prog.status = "failed"`.
  A **completed** backfill is then reported as failed — breaking this branch's own documented contract
  ("an aggregate-refresh failure must never flip an otherwise-successful ingest job to failed").
- **Fix:** `_log_isolation_failure` at both sites. **Test:**
  `test_aggregate_refresh_logging_failure_never_flips_a_successful_job_to_failed`.
  **Negative control: FAILS without the fix** (job flips to `failed`).

**B4 — IMPORTANT (fixed): the append-forward fast path served STALE per-date `excluded` counts.**
`data_manager.py:852` (the `append_forward` predicate). The precondition checked snapshot-**date** ordering
only. That is sufficient for `size`/`entries`/`exits` (pure membership) but **not** for the reused
`excluded` tallies, which `resolve_with_reasons` derives from **bars `<= d`** and `min_history_bars` — and
`_membership_dataset_version` (`research.py:1714-1762`) folds in `max(daily_prices.date)` +
`count(daily_prices)`, so a bar change alone bumps the stamp.
- *Failure scenario:* a `both` job (in `_BACKFILL_KINDS`, so it reaches the hook — see
  `data_manager.py:4664`'s own comment) whose FETCH stage lands bars at a **historical** date (a symbol's
  gap backfill, a newly-added pool symbol's history) while its BACKFILL stage creates one new **later**
  snapshot date. `append_forward` was `True`, so every already-cached date's `excluded` tally was reused
  verbatim although the resolver would now return different numbers. This breaks the phase spec's own
  "byte-identical output required" and **AG-3** ("displayed numbers match the engine's computation for the
  same as-of date") on a Data-Contract row serving `/data`, `/sectors`, `/themes`, `/research/*`,
  `/evidence`.
- *Proven, not theorised:* with the guard removed, the resolver ran for **only** `2024-04-01` while
  `2024-01-03`/`2024-02-01`/`2024-03-01` silently reused stale tallies.
- **Fix:** `_parse_membership_stamp` (`:634`) + `_membership_bars_are_forward_only` (`:656`) — require
  `min_history_bars` unchanged AND every bar added since the cached payload to lie strictly after that
  payload's own `max(daily_prices.date)`. Fail-safe by construction: an unparsable stamp, a bar removal, or
  any count mismatch all fall back to the existing full recompute (the pre-iteration behaviour).
- **Tests:** `test_append_forward_falls_back_when_bars_land_at_or_before_a_cached_date` plus the positive
  control `test_append_forward_still_used_when_bars_land_strictly_after_every_cached_date` (proving the
  guard did not simply disable the fast path for the ordinary forward flow).
  **Negative control: FAILS without the fix.**
- This is the reviewer's MINOR #1, which asked for "a regression test **or** documentation of why it cannot
  occur" — neither was delivered. I was genuinely unsure between MINOR and IMPORTANT and chose the higher,
  because it breaks an explicit spec requirement on a reachable path and touches an AG-3 surface.

**B5 — IMPORTANT (fixed): the per-date coverage warm loop's own isolation handlers were missed by the iter-45 guard.**
`data_manager.py:3612` and `:3620` in `_persist_per_date_coverage_snapshots`. The dev handoff claims the
guard covers "EVERY per-item isolation handler inside `_refresh_ingest_aggregates` (12 call sites)" — but
that function's own docstring names four per-item warm loops it "drives directly **or calls into**", and
this is one of them. `_log_isolation_failure`'s own docstring even states the iter-44 live flake reproduced
"inside the coverage/membership-timeline refresh path (`data_manager.py` ~3506-3517)" — this very region.
- *Failure scenario:* `logger.exception` raises there → escapes the per-date `except MemoryError` →
  `_release_process_memory()` never runs and `aborted_for_memory` is never latched, so the memory back-off
  is skipped under exactly the pressure it exists for. (The escape is then contained by the caller's own
  `_log_isolation_failure` wrapper, so the "never raise" contract still holds — but the per-date isolation
  and the back-off do not.)
- **Fix:** `_log_isolation_failure` at both sites. **Test:**
  `test_per_date_coverage_warm_logging_failure_does_not_skip_the_memory_backoff`.
  **Negative control: FAILS with `MemoryError` without the fix.**

**B6 — IMPORTANT (gap, deliberately NOT fixed): run 281's fatal `MemoryError` produced ZERO log output, so J-05's actual failure is undiagnosable.**
`_run_job`'s outer handler (`data_manager.py:~4781-4793`) records the reason onto `prog` only and makes
**no logging call at all**; `grep -n "no message" logs/backend.log` → no match. The single most important
live failure of this iteration therefore cannot be root-caused from the log. Two candidate origins, and the
evidence cannot distinguish them: (a) `_do_backfill`'s per-date worker `except MemoryError` at
`data_manager.py:3451`, whose own `logger.exception` is still unguarded and would escape silently; or (b)
elsewhere in `_do_backfill` (shared bar-cache prefill / orchestrator persist). Decisive negative evidence
that no worker abort was *successfully* logged: `grep -c "backfill per-date compute aborted"` → **0** and
`grep -c "aborted for memory pressure at"` → **0**.
**Not fixed here** because `_do_backfill` is outside this iteration's declared scope, and a fix there cannot
be verified without the ~1,000 s live backfill drill an audit must not launch. Recommend the next iteration
add a log call in the outer handler and guard `:3451` — this is the cheapest single change that would make
the *next* J-05 failure diagnosable.

### Frontend Findings

**F1 — IMPORTANT (gap, not fixable here): TC-11 fails — two required-still-passing journeys share one byte-identical screenshot.**
`md5sum reports/qa/goal-ops-hardening-iter-45-evidence/*.png`: `J-03-verify.png` and `J-04-verify.png` both
hash `9d77429b8499e40ef04b2de00c1e8fdb` (both exactly 172,246 bytes). TC-11 requires precisely this check to
pass — "an `md5sum` check over the evidence directory confirms no two journeys share one screenshot file
(closes/keeps closed iter-43/ai)" — so the iter-43/ai defect this DoD item exists to keep closed has
**re-opened**. (The `UT-J-05-check1/check2` and `UT-J-05-fail/outage-state` duplicate pairs are within a
single journey and are not a TC-11 violation.) Not fixed: regenerating evidence needs a live browser-QA
run, and re-labelling or fabricating captures would be dishonest.

### Test Findings

**T1 — IMPORTANT (fixed): the new `_log_isolation_failure` fallback branch was covered by nothing.**
The iteration's entire evidence for closing the third escape is TC-8's 5 consecutive `ulimit -v` runs.
Those exercise the **primary** (`logger.exception`) path. `tests/test_ingest_finalize_memory_pressure.py`
contains no monkeypatch of `logger.exception` — it is a real ulimit induction only — and
`grep -n "traceback omitted" logs/backend.log` → **0 matches**, so the fallback never fired in the live
incident either. The DoD item "no `MemoryError` escape … **including inside the `logger.exception()` call
itself**" was therefore claimed on evidence that never executed the new code. This is exactly the session's
standing honesty rule about `MemoryError` being textless and not provable by proxy.
**Fix:** two deterministic tests forcing the branch with a textless `MemoryError` —
`test_log_isolation_failure_swallows_a_raising_logger_exception` (asserts the fallback record is emitted
once, retains its `%s` arg order, and carries the marker) and
`test_log_isolation_failure_swallows_even_when_the_fallback_also_raises`.

**T2 — IMPORTANT (fixed): TC-9's refreshed anchor did not match the live dataset.**
`J-07.json` step 3 was refreshed to `2533`, but the live value is **2532**. Two independent sources: the
browser QA read "Backfill gaps = 2532" live at 00:37Z, and I reproduced 2,532 from the committed DB
(SPY bar dates with no snapshot) — a reproduction validated by its exact agreement with the live
`coverage.gap_last = "2019-02-25"` and with `gap_count = len(gaps)` at `data_manager.py:1137`. The dev
appears to have written the **pre-drill** number: their own `2019-02-26` backfill closed one gap
(2533 → 2532), yet the handoff states the anchor was verified *after* that mutation. Because step 3 is a
strict text match, a golden-script replay would have failed on it. **Fixed to `2532`.**
The other anchor (`n=8991`) remains **UNVERIFIED** — the browser QA explicitly did not re-check it and the
backend is not currently running (`curl` → connection refused, no listener on 8255).

**T3 — OBSERVATION: the QA verdict is not supportable as written.**
`reports/qa/goal-ops-hardening-iter-45-qa.md` states "**Verdict: PASS**" while explicitly deferring TC-4
through TC-7, TC-11 and both target journeys to the browser-qa-agent, which then returned **FAIL** for both.
A PASS that excludes every acceptance criterion the DEFINITION OF DONE actually hinges on misleads any
reader who stops at the verdict line. It also grades TC-8 PASS on the dev's evidence while its own first
run was still "[in progress at QA boundary]".

**T4 — OBSERVATION: the review's grep claim is inaccurate.**
The review states "verified by grep: 0 remaining `logger.exception`, 12 `_log_isolation_failure` calls".
At review time bare `logger.exception` calls remained at `data_manager.py:3451`, `:3602`, `:3610`, `:4658`
and `:4679`. The claim holds only for the literal body of `_refresh_ingest_aggregates`; B3 and B5 above are
the direct consequences of that gap.

---

## 3. Domain Assessment

**The incremental algorithm is correct for what it claims.** I traced
`_membership_timeline_incremental`'s state reconstruction against `_membership_timeline`'s own loop rather
than trusting the handoff: `seen` is the union of `members_by_date` over all cached dates and
`prev_members` is the membership of the last cached date — exactly what the original per-date loop leaves
behind after processing those dates. Not an approximation. `_membership_timeline` is byte-for-byte
untouched by the diff, so using it as TC-3's oracle is legitimate (though it is the *live* function, not
the "pinned" fixture the spec worded).

**The gap-fill fallback is genuinely correct and genuinely tested.** The regression test asserts D1's
`entries` actually *change* after an earlier insertion, so it cannot pass by stale reuse — a tight
assertion, not a loose one.

**The blind spot was the `excluded` dimension (B4).** `size`/`entries`/`exits` depend only on membership;
`excluded` depends on bars. Only the membership dimension was guarded, so the byte-identity guarantee the
spec demanded held for three of the four fields and silently failed for the fourth. That asymmetry is the
single genuine correctness defect in the diff, and it is now closed.

**Blast radius is contained.** Only two callers reach `membership_timeline_cached` (`warmup.py:116`,
`data_manager.py:1081`), both passing the full snapshot-date set, so the payload-subset hazard the
no-date-term cache key would otherwise expose is not reachable today.

**AG-10 is intact.** `start-backend.sh`'s banner shows `memory_cap_mb=8192 malloc_arena_max=2
cpu_list=0-15 blas_threads=8`; no host-guard cap is removed, weakened, or bypassed anywhere in the diff.

**Pre-existing, not introduced, not fixed (GAP):** `_membership_dataset_version` carries no candidate-pool
term, so a `read_pool()` change alone never invalidates the membership cache. Under the fast path this also
makes `candidate_pool_count` (recomputed fresh) inconsistent with the reused `excluded` tallies. Worth a
future card; out of scope here.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/data_manager.py:4759`, `:4782` | B3 — `logger.exception` → `_log_isolation_failure` in `_run_job`'s two aggregate-refresh handlers, so a logging allocation can no longer flip a successful ingest job to `failed`. |
| 2 | Important | `apps/backend/app/engine/data_manager.py:634`, `:656`, `:852` | B4 — added `_parse_membership_stamp` + `_membership_bars_are_forward_only` and tightened the `append_forward` predicate, so the fast path can no longer reuse stale `excluded` tallies when bars land at or before an already-cached date. Fail-safe: any doubt → the existing full recompute. |
| 3 | Important | `apps/backend/app/engine/data_manager.py:3612`, `:3620` | B5 — `logger.exception` → `_log_isolation_failure` in `_persist_per_date_coverage_snapshots`' per-date isolation handlers, so the `MemoryError` back-off is no longer skipped when logging fails. |
| 4 | Important | `apps/backend/tests/test_data_manager.py` | T1/B3/B4/B5 — six regression tests (two deterministic `_log_isolation_failure` fallback tests, the B3 job-status test, the B4 fallback test + its positive control, the B5 back-off test). |
| 5 | Important | `runs/goal-session-ops-hardening/journey-scripts/J-07.json` | T2 — step 3 anchor `2533` → `2532`, the actual live value. |

**Verification of every fix (commands and results):**

```
# All targeted suites, post-fix:
cd apps/backend && .venv/bin/python -m pytest \
  tests/test_data_manager.py -k "finalize_hook or run_job or log_isolation_failure or \
    aggregate_refresh_logging or bars_land or append_forward or historical_gap_fill or \
    per_date_coverage_warm_logging" \
  tests/test_data_manager_membership_cache.py tests/test_ingest_finalize_fault_injection.py -q
  → 43 passed, 135 deselected in 211.19s
```

Every fix was negative-controlled — the product change was temporarily reverted and the new test re-run to
confirm it fails without the fix (so none of them pass vacuously):

- **B3** reverted → `test_aggregate_refresh_logging_failure_never_flips_a_successful_job_to_failed` FAILED.
- **B4** reverted → `test_append_forward_falls_back_when_bars_land_at_or_before_a_cached_date` FAILED with
  `Resolver saw only [datetime.date(2024, 4, 1)]` — i.e. the stale reuse reproduced exactly.
- **B5** reverted → `test_per_date_coverage_warm_logging_failure_does_not_skip_the_memory_backoff` FAILED
  with `MemoryError`.

The iteration's own four tests (TC-1/TC-2/TC-3 + gap-fill) were re-run independently before any change
(`4 passed in 0.92s`) and again after all five fixes — still passing, confirming the B4 guard did not
disable the fast path for the append-forward case it exists to serve.

Diff hygiene: my changes are confined to four marked sites (`grep -n "iter-45 AUDIT"` → 6 comment anchors)
plus the appended tests and the one-character JSON anchor. Nothing else was touched. The dev handoff's
claim that `_log_isolation_failure` covers "EVERY per-item isolation handler" is now true only after fix 3;
its "(12 call sites)" figure is superseded (16 sites).

---

## 5. Recommended Next Step

**Do not advance on this iteration's target journeys.** J-05 and J-07 remain failing, and the honest
reading of the live evidence is that this iteration fixed a real bottleneck that *was not the binding
constraint* on either journey — the binding constraint is process-wide memory exhaustion severe enough to
break thread creation itself.

Ranked next actions:

1. **Fix the two unbounded evidence-path accumulators** (`research.py:777` `_combination_observations`'
   `ret_by_run_symbol`, `forward_testing.py:2343` `compute_drawdown_expectations`' `stored_by_key`). This
   is now the highest-value item on the board, not a carried one: 16 of the 24 wedge-window `MemoryError`s
   entered through `evidence.py:168`, a **request-serving** path, and it is that request-path pressure —
   not the ingest hook — that drove the process to the point where AnyIO could not create a worker thread.
   The iteration that deferred these was written before this evidence existed.
2. **Make the next failure diagnosable (B6).** Add a log call to `_run_job`'s outer handler and guard
   `data_manager.py:3451`. Cheap, mechanical, and without it the next J-05 failure will be just as silent
   as run 281's.
3. **Then** the out-of-process watchdog. B1's mechanism vindicates it: an in-process guard cannot recover a
   process that can no longer create the thread needed to serve `/api/health`.
4. **Re-run the full eight-journey regression with unique evidence (F1)** once the backend is healthy — and
   fix the evidence-capture step that produced two byte-identical files, since TC-11 exists precisely to
   catch that.
5. **Re-verify `J-07.json`'s `n=8991` anchor** against a live backend; it is currently unverified.
6. **Keep the append-forward fast path.** It is correct, now correctly guarded, and cheap. But it needs one
   genuine live append-forward drill before anyone claims it works at the ~2,860-date scale — today that
   claim rests entirely on a 4-date fixture.
