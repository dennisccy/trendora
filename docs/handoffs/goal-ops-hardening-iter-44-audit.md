# goal-ops-hardening-iter-44 Audit Report

**Date:** 2026-08-03
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** FAIL

The iteration's *mechanical* half is genuinely done and verified (launcher-flag wiring live on the real
process, Retry 503 parity, the first true SIGUSR1 stall diagnosis this session has produced), but its two
availability Definition-of-Done items — TC-2 (self-terminates on SIGTERM, no `kill -9`) and TC-7 (never
goes fully unreachable) — are **refuted by this same pipeline's own browser lane**, which reproduced a
**20m51s total outage** and needed a `SIGKILL`. Those are the phase GOAL's first clause ("Stop J-07's heavy
warm from taking the whole service unreachable"), they are worse than the iter-43 incident they were
written to close, and the root cause is outside this iteration's evidenced reach — so they cannot be fixed
here. Separately, two DoD items were claimed complete but were provably not: TC-10's message-honesty fix was
a **no-op for `MemoryError`** (the exception class this session's failures actually raise — live-observed on
run 272), and TC-8's induced-pressure abort did **not** hold (the real sanctioned hook failed with an
uncaught escape, mis-filed in the handoff as "fixture calibration drift"). Both were traced to their exact
lines and **fixed during this audit**, each proven by a re-run test; the system is materially stronger and
more honest than at handoff, but the phase goal itself was not achieved.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): TC-10's failed-job message honesty was a no-op for `MemoryError` — the one
exception class this session actually produces**

`apps/backend/app/engine/data_manager.py:4535-4559` (`_run_job`'s outer handler) set
`prog.message = scrub(str(exc))`. **`str(MemoryError())` is the empty string.** The empty message is falsy,
so `_run_detail`'s guard at `data_manager.py:4060`
(`"summary": prog.message if (prog.status == "failed" and prog.message) else _final_summary(prog)`) fell
straight back to `_final_summary`'s generic text — the exact string TC-10 exists to eliminate. The fix
therefore only worked for exceptions that carry text, and the entire chain (this fix → unblocking iter-43
audit's B2 `_run_detail` fix, which B5 had proved a no-op) stayed a no-op for the dominant real failure.

Reproduced before fixing, with the dev's own test methodology and only the exception class changed:

```
[AUDIT MemoryError]  prog.message=''   prog.errors=['']
[AUDIT MemoryError]  persisted run-history message='backfill: 0 snapshots over 0 dates, 0 forward returns'
[AUDIT RuntimeError-with-text] persisted run-history message='real text here'
```

That persisted string byte-matches the shape the browser lane observed on the **live** failed run 272
(`"backfill: 0 snapshots over 1 dates, 0 forward returns"`,
`reports/phase-goal-ops-hardening-iter-44-ui-test-results.llm.md` step 6) — i.e. this is not a theoretical
edge case, it is what the product did during this iteration's own verification. Note also `prog.errors`
became `['']`: a blank entry in the job's error list.

This is precisely the binding iter-43 lesson the spec cites **twice** ("keyed to the whole exception set the
diagnosed incident actually produces, not its headline exception") violated in the change made to honor it.
The dev was aware of the class — the TC-9 test parametrizes over `MemoryError()` — but TC-10's test used
only `RuntimeError("simulated trading-calendar read failure")`, so it passed while the real path stayed broken.

**Fix applied** (`data_manager.py:4535-4559`): compute the reason once with a type-name fallback —
`reason = scrub(str(exc)) or f"{type(exc).__name__} (no message)"` — and use it for both `_record_error`
and `prog.message`. Text-carrying exceptions are byte-identical to before.
**Proof:** new regression test `test_run_job_textless_exception_still_names_a_real_reason`
(`tests/test_data_manager.py:5464`); post-fix persisted message = `'MemoryError (no message)'`.
`pytest tests/test_data_manager.py tests/test_api_data.py -q` → **203 passed in 418.09s**.

---

**B2 — IMPORTANT (fixed): TC-8's induced-pressure abort did NOT hold — `_refresh_ingest_aggregates`
violated its "never raise" contract at two sites; the handoff mis-filed this as fixture calibration drift**

The dev handoff and QA both report TC-8 PASS, but they cite `test_ingest_finalize_fault_injection.py` (5
synthetic, env-var-injected `MemoryError`s raised with plenty of memory available). The test that actually
implements TC-8's own wording — *"a tightened `server.memory_cap_mb` in a throwaway process"* —
`tests/test_ingest_finalize_memory_pressure.py`, was **failing**, and was dismissed as
"pre-existing test-fixture calibration drift (`TIGHT_CAP_KB=750,000`)".

That diagnosis was wrong. I re-ran it and read the child probe's captured stderr: the warm did not "abort
honestly via the existing per-item `MemoryError` isolation handler" — the `MemoryError` **escaped
`_refresh_ingest_aggregates` uncaught** (child returncode 1) at two sites, each of which allocates *inside*
the memory-pressure path:

1. `data_manager.py:2888-2903` — `_resolve_libc_malloc_trim`'s `except (OSError, AttributeError)` does not
   catch `MemoryError`, yet `ctypes.util.find_library("c")` forks `ldconfig` and regexes its whole stdout.
   `_release_process_memory()` is called *from inside* the per-horizon `except MemoryError:` abort handler
   (`data_manager.py:3596`), so the handler's own cleanup re-raised
   (`ctypes/util.py:297 in _findSoname_ldconfig`).
2. `data_manager.py:3644` — the deferred `from app.engine import indexes` sat one line **above** its `try`,
   the only unguarded statement left in an otherwise fully isolated finalize sequence. Importing a
   not-yet-loaded module allocates (read + compile), so under an exhausted cap it escaped the function
   entirely (`<frozen importlib._bootstrap_external>:1191 in get_data`).

Same lesson as B1, applied to the abort handlers themselves: a guard keyed to the wrong exception set.

**Fixes applied:** (1) add an `except MemoryError: return None` branch that deliberately does **not** cache
the failure — caching it would permanently disable iter-27's `malloc_trim` memory-return path for the
process's life, an AG-8 regression; (2) move the deferred import inside the existing `try`, unchanged in
every other respect.
**Proof:** each fix removed its own escape from the captured stderr, and the next one surfaced —
`pytest tests/test_ingest_finalize_memory_pressure.py -q` went 1 failed/1 passed → 1 failed/1 passed (new
site) → **2 passed in 170.76s**. Regression check on every test file touching these symbols:
`test_ingest_finalize_fault_injection.py`, `test_indexes.py`, `test_backfill_coverage_shared_cache.py`,
`test_data_manager_backfill_parallel.py` → **43 passed in 534.75s**.

---

**B3 — CRITICAL (gap — not fixable within this iteration's evidenced reach): TC-2 and TC-7 are refuted by
this pipeline's own browser lane; the service went fully unreachable for 20m51s and required `SIGKILL`**

The dev handoff claims TC-7 PASS ("never returned non-200 across 240 polls") and "TC-2 confirmed, both live
and via a new automated regression test"; QA repeats both. Both are true **of the runs they measured** and
false as general claims — and the run that refutes them is this iteration's own, on the same build:

| Claim | Measured under | Refuted by |
|---|---|---|
| TC-7: never fully unreachable | one clean single trigger, fresh backend, no pre-existing background compute | 51 consecutive timed-out `/api/health` polls over **20m51s** (20:10:33→20:31:24 UTC), two independent pollers plus `curl --max-time 4` returning `http_code=000` |
| TC-2: exits within `graceful_timeout_seconds`, no `kill -9` | a 2-second-old backfill on a throwaway DB, event loop alive | `SIGTERM` 20:26:13 UTC → still alive at 20:31:12 (4m59s, past the configured 120s) → `SIGKILL` 20:31:37 UTC |

I verified the TC-2 refutation independently rather than taking the tester's word: **`logs/backend.log`
contains no shutdown output whatsoever for that process.** Its last line is a caught `MemoryError` in
`evidence.py` at 20:13:56 UTC (line ~170791); the next line in the file is
`=== start-backend.sh: launching at 2026-08-03T20:31:51Z ===`. No `Shutting down`, no `Waiting for
application shutdown`, no `Finished server process` — uvicorn's signal handling never ran at all.

That is the mechanism, and it matters for the next iteration: `--timeout-graceful-shutdown` is enforced
**by the asyncio event loop**. When the loop itself is wedged (all 19 threads `S`, cumulative CPU not
advancing, internal logging stopped — the tester's `/proc` sampling), the flag can never fire. The
perf-budgets §2 claim that "the launcher flag alone — TC-1 — is sufficient to close the 'held hostage'
failure mode" is therefore only true for the case where the process is still schedulable. The daemon-thread
reasoning quoted there is correct and irrelevant to this failure mode.

**Not fixed here, deliberately.** The two candidate root-cause fixes are the ones the spec itself defers
(the incremental membership-timeline redesign; a sixth `_SymbolColumns`/`bars_asof` bound attempt, whose
fifth attempt measured a +5.1% regression), and an in-process watchdog cannot escape a wedge in which no
Python thread advances — the evidenced next step is an **out-of-process** supervisor deadline
(systemd-style `TimeoutStopSec`, or the launcher backgrounding uvicorn and enforcing its own SIGKILL
escalation), which is a new mechanism this iteration's assumptions explicitly chose not to invent. I was
unsure between IMPORTANT and CRITICAL here: the iteration disclosed the underlying stall honestly and did
not introduce the defect, but the DoD lists TC-2 and TC-7 as done-criteria, both are refuted, and the outage
is longer than the one it set out to close — so per the tie-break rule I recorded the higher severity.

---

**B4 — GAP (not fixed): TC-5's own acceptance criterion was not met, and QA reported it as "constraints
held"**

TC-5 requires *"every poll returns HTTP 200 within the rescoped ≤2 s budget"*.
`runs/goal-ops-hardening-iter-44/j07-warm/clean-remeasure-summary.json` records
`over_2s_budget: 16` of 240 polls (6.7%), `max_latency_s: 2.354`. The dev disclosed this honestly as a WARN;
the QA report renders it as "TC-5/TC-6/TC-7: Clean re-measurement shows improvement and constraints held"
and then lists TC-5 with a ✓. The measurement is a real improvement over the confounded run (70.9% → 6.7%)
and I am not disputing the number — only that a DoD checkbox with a hard threshold is being reported as met
when its own artifact says otherwise.

---

**B5 — OBSERVATION: `--limit-concurrency 64` adds a path where `/api/health` can return 503 rather than a
slow 200**

The new flag is exactly what `ServerOpsCfg`'s docstring specifies ("the max simultaneous connections before
a 503"), so this is by design, and no evidence of it firing exists in this iteration (the incident produced
timeouts, not 503s). Recording it only because J-07's acceptance is worded as "returns 200 throughout": a
future connection pile-up above 64 would now fail that clause by design rather than by starvation. Related
and also pre-existing: `start-backend.sh:45-51`'s `read` gives no diagnostic if the venv-python config read
fails — all five variables would be empty and `ulimit -v $((MEMORY_CAP_MB * 1024))` would evaluate to
`ulimit -v 0`. iter-44 extended this pattern rather than introducing it; not in scope to change here.

### Frontend Findings

None. `Frontend Present: no`, and TC-11 verified independently: `git diff HEAD -- apps/frontend/tsconfig.json`
is empty — the iter-43 F1 stray `include` reordering is genuinely absent, not merely asserted.

### Test Findings

**T1 — IMPORTANT (fixed): the TC-10 test chose the one exception class that could not expose the bug.**
`test_run_job_outer_exception_preserves_real_message_not_final_summary` raises
`RuntimeError("simulated trading-calendar read failure")`. Every assertion in it passes against code that is
broken for `MemoryError`. Closed by the new test in B1, which pins the textless-exception case and also
asserts no blank entry lands in `prog.errors`.

**T2 — OBSERVATION: TC-2's automated test cannot fail the way production failed.**
`test_start_backend_self_terminates_on_sigterm_with_stuck_background_task` triggers a backfill, sleeps 2.0s,
asserts `status == "running"`, then SIGTERMs. A 2-second-old job on a throwaway DB has a live event loop, so
the test measures uvicorn's normal graceful path (0.40s against an 8s budget) — not the wedged-loop
condition that produced the incident. It is a valid TC-1-wiring regression test; it is not evidence for
TC-2's DoD claim, and B3 shows the two diverge. Not fixed: a test that reproduces a genuine wedge is new,
unevidenced work.

**T3 — OBSERVATION: the QA report's verdict is stale, not wrong-at-the-time, but it will mislead a reader.**
QA (written 20:52, verdict PASS) states "Browser QA: **SKIPPED** — no UI changes shipped this iteration",
while this iteration's TESTING REQUIREMENTS mandate browser tests for J-05, J-07 and six regression
journeys. The browser lane then ran at 21:37 and returned **FAIL**. Anything keying off QA's PASS without
reading `reports/phase-goal-ops-hardening-iter-44-ui-test-results.llm.md` will draw the wrong conclusion.

---

## 3. Domain Assessment

**Verified by full trace (risk class, contradiction, or my own leads):** TC-2, TC-7 (B3 — state/lifecycle,
artifacts in direct contradiction), TC-10 (B1 — data persistence, contradicted by a live QA observation),
TC-8 (B2 — my own lead from the "pre-existing flake" note), TC-11, TC-5 (B4).

**Accepted on reviewer + executed QA row, with citation, per the mechanical-item rule:**
TC-1 — reviewer `spec_alignment.definition_of_done: complete`, `issues: []` + QA row
"TC-1 … 1 passed in 1.88s"; independently corroborated by the browser lane reading the live process's
`/proc/<pid>/cmdline` (`--limit-concurrency 64 --timeout-keep-alive 65 --timeout-graceful-shutdown 120`) —
and I read the diff: values come from `get_config().server`, no magic numbers, the HOST-GUARD block and
`ulimit` are untouched, so AG-10 holds (the flags are additive, as required).
TC-9 — reviewer PASS + QA row (2 parametrized cases); I also read `data.py:306-315` against
`start_job`'s `:196-206` and confirmed exact parity, including the `MemoryError` arm.

**TC-3 is real work, and it is the iteration's genuine achievement.** I did not take the dumps on trust:
`logs/backend.log` carries the verbatim `faulthandler` output (line 167759+, faulthandler frame format),
naming `universe_resolver.resolve_with_reasons` ← `data_manager._excluded_counts_by_date` ←
`_membership_timeline` ← `membership_timeline_cached` ← `_refresh_ingest_aggregates`. After seven ESCALATEs
of guessing, this session finally has a named blocking call with two corroborating live samples, and the
honest TC-4 disclosure (option b) over a speculative sixth `_SymbolColumns` attempt is the correct call
under the binding iter-38/39/42 lessons. TC-12 and TC-13 also hold: J-05 was retested against genuinely
unsnapshotted dates in both lanes (2019-02-27 in-flight, 2019-02-26 terminal-failed, both honestly
reported), and the six regression screenshots carry six distinct md5s — iter-43/ai is closed.

The through-line across B1 and B2 is one domain fact this session keeps re-learning: **`MemoryError` is this
product's characteristic failure, and it is textless and raised from inside allocation-sensitive cleanup
paths.** Guards written against a "normal" exception — one with a message, raised where there is memory to
handle it — pass their tests and do nothing in production. Three separate handlers in this iteration's own
scope had that shape. The `_run_job` conditional (`if prog.status != "failed"`) and the `_run_detail`
truthiness guard are correct now, and the abort handlers no longer allocate their way out of their own
except blocks.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/data_manager.py:4535-4559` | `_run_job`'s outer handler: `reason = scrub(str(exc)) or f"{type(exc).__name__} (no message)"`, used for both `_record_error` and `prog.message` — a textless `MemoryError` no longer persists as a blank message that silently degrades to `_final_summary`'s generic text (B1) |
| 2 | Important | `apps/backend/app/engine/data_manager.py:2888-2903` | `_resolve_libc_malloc_trim`: added `except MemoryError: return None` (deliberately uncached — caching would permanently disable iter-27's `malloc_trim` path) so the per-horizon abort handler's own `_release_process_memory()` cleanup can never re-raise (B2) |
| 3 | Important | `apps/backend/app/engine/data_manager.py:3636-3646` | Moved the deferred `from app.engine import indexes` inside its existing `try` — the last unguarded statement in the finalize sequence, which escaped uncaught when the import itself allocated under an exhausted cap (B2) |
| 4 | — | `apps/backend/tests/test_data_manager.py:5464` | New regression test `test_run_job_textless_exception_still_names_a_real_reason` pinning the `MemoryError` case for TC-10 (T1) |
| 5 | — | `docs/handoffs/goal-ops-hardening-iter-44-dev.md` | Three inline AUDIT CORRECTION notes: the memory-pressure test's mis-diagnosis (now 2/2 passing), and the TC-2/TC-7 claims refuted by the browser lane |

**Verification of every fix** (`TMPDIR` isolated per the dispatch; no full-suite run — ~10h on this basis):
- `pytest tests/test_data_manager.py tests/test_api_data.py -q` → **203 passed in 418.09s** (includes the new test)
- `pytest tests/test_ingest_finalize_memory_pressure.py -q` → **2 passed in 170.76s** (was 1 failed, 1 passed)
- `pytest tests/test_ingest_finalize_fault_injection.py tests/test_indexes.py tests/test_backfill_coverage_shared_cache.py tests/test_data_manager_backfill_parallel.py -q` → **43 passed in 534.75s**
- `git diff` re-read: the audit's product diff is 3 hunks in one file, no unrelated edits.

---

## 5. Recommended Next Step

**Do not advance J-07 to passing.** Its two acceptance clauses were re-refuted on this build by this
pipeline's own browser lane, and this iteration's honest disclosure of the root cause (the O(dates × pool)
`_excluded_counts_by_date` recompute forced by `membership_timeline_cache`'s all-or-nothing
`dataset_version` invalidation) is now backed by named, corroborated live stacks — the first real lead in
seven ESCALATEs. The next iteration should spend itself on exactly that finding, and it is now an owner-level
decision because both candidate fixes exceed a single iteration's evidenced reach:

1. **Incremental membership-timeline invalidation** — the highest-value fix and the one the evidence points
   at. A single-date backfill currently recomputes ~2,860 dates × ~591 symbols. Scoping the cache key
   per-date (or merging incrementally) is a real design change to order-dependent `entries`/`exits` state,
   not a patch — it deserves its own iteration with a byte-identity proof against the current output.
2. **An out-of-process shutdown deadline** — the only thing that can actually close TC-2. Nothing in-process
   survives a wedge where no Python thread advances; the launcher must own the SIGKILL escalation (or a
   supervisor must). Small, mechanical, and independently valuable, but it is a new mechanism and needs to
   be specified as such rather than smuggled in as a "wiring" change.
3. **Recalibrate `TIGHT_CAP_KB`** *(now, and only now, a legitimate question)* — with B2's two real escapes
   fixed, `test_ingest_finalize_memory_pressure.py` passes at the existing 750,000 KB cap, so the fixture is
   not drifted. If it becomes flaky again, treat that as a new escape to trace, not a number to tune.

Carry forward as the standing lesson for whoever writes the next guard: **test every new `except` clause with
a textless `MemoryError` raised from inside the cleanup path, not a `RuntimeError` with a friendly message.**
Three of this iteration's handlers passed their tests and did nothing under the condition they were written for.
