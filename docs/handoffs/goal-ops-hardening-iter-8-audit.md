# goal-ops-hardening-iter-8 Audit Report

**Date:** 2026-07-22
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The backend fix is real, correctly scoped, and does what the spec asked: all four ingest-finalize warm
loops now catch `MemoryError` distinctly, stop that one loop, release memory, and keep the
`aggregates_refreshed` honesty gate accurate on the early-abort path — proven by tight injected-error unit
tests and corroborated live (the hwmon telemetry independently confirms the claimed back-to-back heavy
ingest really ran at the stated time with the stated thermals). However, the *test* half of the diff
shipped broken: the new heavy-ingest test block was spliced into the middle of the existing TC-17 test,
silently deleting TC-17's real assertions (it still reported green) and leaving the new test with a
guaranteed `NameError`. Reviewer and QA both missed it. I fixed that, the byte-offset logfile bug blocking
DoD item 7, the unguarded ~16-minute heavy test, and a defect in the coverage loop's memory release; two
DoD verification items (J-05 via browser-qa, J-01/J-03/J-04 re-verification) remain genuinely unperformed
and are the reason this is not a clean PASS.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the coverage loop's memory release ran while its ~1.5 GB bar cache was still held**

`apps/backend/app/engine/data_manager.py:3037-3054`. `_persist_per_date_coverage_snapshots` opens
`with prefilled_bar_cache(session, expected_symbols=pool_symbols):` and the new `except MemoryError` branch
called `_release_process_memory()` **inside** that `with` block, then `break`. The `_BarCache` is dropped
only when the context manager exits, i.e. *after* the trim. `_release_process_memory`'s own docstring
(`data_manager.py:2728-2748`) states that this cache is "~1.5 GB of `Bar` lists" and is the dominant VSZ
lever the helper exists to reclaim. So on the abort path the single largest freeable block was still
referenced when `gc.collect()` + `malloc_trim(0)` ran, and the caller's next independent warm block
(market-phase → forward-aggregates → drawdown) resumed on the same un-trimmed arena — precisely the
headroom the spec's IN SCOPE bullet ("force `gc.collect()` before returning/continuing to the next
independent block") requires it to restore. The other three loops do not hold a prefilled cache, so only
this loop is affected — but it is the first and heaviest of the four.

**Fix applied:** an `aborted_for_memory` flag is set on the `MemoryError` break, and a second
`_release_process_memory()` runs after the `with` block exits and the cache is dropped, mirroring
`_do_backfill`'s own post-`prefilled_bar_cache` release in its `finally` (`data_manager.py:2993`). The
normal completion path is byte-unchanged.

**Evidence:** new regression guard
`tests/test_data_manager.py::test_persist_per_date_coverage_memory_error_releases_memory_after_bar_cache_drops`
asserts at least one release happens with `active_bar_cache(session) is None`.
`cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -v -k memory_error`
→ **10 passed, 121 deselected in 2.12s**. Negative control: with the new post-`with` release disabled
(`if False and aborted_for_memory:`), the same test **FAILS** — so the guard is not vacuous.

**B2 — GAP (not fixed, unsure between GAP and IMPORTANT): `_release_process_memory()` fork/execs `ldconfig` on every call, including on the new memory-pressure path**

`apps/backend/app/engine/data_manager.py:2749-2755` resolves libc through `ctypes.util.find_library("c")`
on **every** invocation. Verified empirically —
`strace -f -e trace=execve python -c "import ctypes.util; ctypes.util.find_library('c')"` shows one
`execve` of `ldconfig`. The new `except MemoryError` branches therefore spawn a subprocess at the exact
moment of memory exhaustion, and if that fork fails the resulting `OSError` is swallowed by the existing
`except (OSError, AttributeError): pass`, silently skipping the `malloc_trim` half of the release with no
log line. I chose GAP over IMPORTANT because Linux `fork()` does not itself enforce `RLIMIT_AS`, so the
failure mode is plausible but unproven, and this is a pre-existing iter-27 helper the spec explicitly
reused unchanged. **Recommendation for a follow-up:** memoize the successful `ctypes.CDLL` handle at
module level so the abort path performs no fork/exec at all (also removes a per-job subprocess spawn).

**B3 — OBSERVATION: two heavy non-loop calls in the finalize hook still have only generic handling**

`data_manager.py:3101` (`refresh_coverage_snapshot`, the whole-universe coverage compute) and
`data_manager.py:3159` (`scanner._latest_stored_run_date`) sit under plain `except Exception` with no
`MemoryError` distinction and no `_release_process_memory()`. Both are single calls, not per-item loops, so
they are outside the spec's four named loops and there is no "keep hammering the next item" pattern to
break. Noted only because a `MemoryError` there still leaves the process without a trim before the next
block runs.

### Frontend Findings

None — this iteration has no frontend surface (spec: Frontend Present: no; `app/api/health.py`,
`readiness.py`, `main.py` confirmed untouched by `git diff`).

### Test Findings

**T1 — IMPORTANT (fixed): the new heavy-ingest block was spliced INTO the existing TC-17 test, deleting its assertions and breaking the new test**

`apps/backend/tests/test_start_backend_script.py`. At `HEAD`, TC-17
(`test_start_backend_logfile_ends_abruptly_after_simulated_crash`) ended with four lines that are its
entire reason to exist — the assertion that no clean-shutdown phrase follows this spawn's own SIGKILL. The
iter-8 diff inserted the ~220-line heavy-ingest block **between** `assert not _pid_alive(pid)` and those
four lines. Two consequences, both live in the shipped diff:

- TC-17 was reduced to "the process died after SIGKILL" — its actual regression check was silently
  removed, and it still reported **PASSED** in the QA report (`reports/qa/goal-ops-hardening-iter-8-qa.md`
  line 71). A test that passes because its assertions were deleted.
- The orphaned lines landed at the end of
  `test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap(spawned_backend_throwaway_db)`
  (pre-fix line 421), referencing `spawned_backend` — a name that is not a parameter of that test. The
  iteration's headline TC-1/TC-2 regression guard would therefore have raised `NameError` on every run,
  regardless of whether the memory and health assertions held. It was never executed, so nobody found out.

**Fix applied:** the four assertions were restored to TC-17 (as a byte-offset slice, see T2) and removed
from the heavy test.

**T2 — IMPORTANT (fixed): DoD item 7 was unachievable — the byte-offset/char-offset logfile slice**

`SpawnedBackend.log_offset_before` is a **byte** offset (`LOG_FILE.stat().st_size`,
`test_start_backend_script.py:126`) but was sliced against `LOG_FILE.read_text(errors="replace")`, a
**character**-indexed string (pre-fix lines 183 and 421). `logs/backend.log` currently carries 6 non-ASCII
bytes (verified: 1,690,555 bytes vs 1,690,549 characters), so each spawn's slice started 6 characters too
far in and truncated the expected `"start-backend.sh: launching at"` marker. This made
`test_start_backend_writes_persistent_logfile_with_boot_events` fail, which in turn made the spec's DoD
item 7 / TC-8 ("runs to completion with 0 failures") unsatisfiable. It is pre-existing (the reviewer
independently confirmed it fails identically on pre-iter-8 `HEAD`), but it blocks a DoD item, so I fixed
it rather than deferring it a third time. Both call sites now use
`LOG_FILE.read_bytes()[offset:].decode(errors="replace")`.

**T3 — IMPORTANT (fixed): the new heavy real-process test ran by default, hanging the DoD command and risking the host**

`test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap` had no opt-in guard. Any plain
`pytest tests/test_start_backend_script.py` — including the exact command DoD item 7 specifies — would
copy the 2.5 GB dev DB, spawn a real backend, and run a full-universe rebuild (~16 min per Item L) plus a
heavy backfill. QA observed exactly this: "Last test timed out" (`...-iter-8-qa.md` line 75), so the DoD
command could not report a clean result at all. This is also the literal workload this host hard-reset
under on 2026-07-21 (`project-extensions/host-guard/README.md`), which is why the developer's first pass
correctly declined to run it — a workload with that history must never start by accident. **Fix applied:**
the fixture now skips unless `TRENDORA_RUN_HEAVY_INGEST_TEST=1`, with the reason stated in the skip
message.

**T4 — OBSERVATION: the heavy test accepts `"partial"` as success**

`test_start_backend_script.py` asserts `job.get("status") in ("ok", "partial")` for both jobs. A `partial`
rebuild (some dates failed) would still pass the capacity assertions. Defensible for a memory/availability
proof, but it is a looser assertion than the rest of this iteration's tests, and it does not assert the
absence of a `MemoryError` in the job record or logs.

**T5 — Positive finding: the unit tests are genuinely tight.** The nine dev-authored `MemoryError` tests
assert exact call counts (`calls["n"] == 1` / `== 2`) to prove no further item was attempted, exact
`refreshed` membership in both directions (omitted on first-item abort, present after partial success),
a real persisted-row check after a partial abort, byte-identity of a warmed payload against
`compute_drawdown_expectations` (AG-3), and an explicit non-`MemoryError` regression guard confirming the
generic isolate-and-continue path is unchanged. No loose "one of several outcomes" assertions found.

### Verification Findings (unresolved)

**V1 — IMPORTANT (gap, unresolved): DoD item 1 — "J-05 passes cleanly via browser-qa-agent" — was never performed**

`reports/phase-goal-ops-hardening-iter-8-ui-test-results.md` reads in full: "**Browser QA Verdict:**
SKIPPED — Backend-only phase (Frontend Present: no)." `runs/goal-ops-hardening-iter-8/status.json` line 19
confirms `"browser_checks_run": false`, and there is no
`reports/qa/goal-ops-hardening-iter-8-evidence/` directory and no `...-ui-test-results.llm.md`. The spec's
TESTING REQUIREMENTS explicitly demand "Browser: J-05 (all 4 steps, especially step 4 live-polled
`GET /api/health` throughout a real heavy ingest)". J-05 remains `"status": "regressed"` in
`runs/goal-session-ops-hardening/state/journey-history.json`.

What *does* exist is strong: the developer's own live orchestration covers J-05 step 4 directly (the
regressed step), and I independently corroborated it rather than taking it on trust —
`logs/hwmon/hwmon.csv` (8,156 samples, 21:04→23:27 on 2026-07-21) yields, over the claimed 22:38–22:56
window, **maxTctl 89 °C, maxDIMM 48 °C, maxNVMe 41 °C, maxPPT 59 W**, matching the handoff's numbers
exactly, with `mem_avail` never below 16.3 GB. The run happened as described. But steps 1–3 of J-05 (the
`/data` backfill UI flow, `/scanner-runs` leaderboard from storage, cold-restart coverage render) are
unverified this iteration, and the one measurement that matters was produced and reported by the same
agent that wrote the code. I did not close this gap myself: re-running the scenario is the host-crash-gated
workload and browser-qa is a separate agent's lane. **The evaluator must not flip J-05 `regressed →
passing` on this handoff alone.**

**V2 — GAP (unresolved): DoD item 5 — J-01/J-03/J-04 re-verification was not run this iteration**

The QA report marks TC-09 and TC-10 "INDIRECT — Not directly executed this session"
(`...-iter-8-qa.md` lines 95-96), and there is no `phase-goal-ops-hardening-iter-8-regression-replay-results.md`
(iter-7 has one). The reasoning — this diff touches only `data_manager._refresh_ingest_aggregates` and its
tests, none of J-01/J-03/J-04's surfaces — is sound and matches the diff I read, and the 134-test targeted
suite covers the backfill/coverage/range-cap logic those journeys exercise. Recorded as a gap rather than a
failure, but the DoD checkbox is not honestly tickable as written.

**V3 — GAP: no raw artifact was retained for the live VmPeak measurement**

`reports/perf-budgets.md`'s iter-8 section reports "1,129 samples, 1 Hz" and a 3,465.6 MB peak, but the
sampler output lived in the session scratch dir and is gone; only the narrative survives. The thermal half
is independently reproducible from `logs/hwmon/hwmon.csv` (see V1), the memory half is not. Future live
measurements should copy the sampler CSV into the iteration's `runs/` directory.

**V4 — OBSERVATION: the dev handoff duplicates Known Issues #2/#3/#4 verbatim** (once at lines 106-127 and
again at lines 188-209 of `docs/handoffs/goal-ops-hardening-iter-8-dev.md`), a copy-paste artifact of the
Fix Notes append. Cosmetic.

---

## 3. Domain Assessment

The root-cause analysis is correct, and I verified it against the code rather than the handoff.
`MemoryError` is a subclass of `Exception`, so the pre-existing `except Exception: log + continue` in each
per-item warm loop did exactly what the spec claims: caught the allocation failure and immediately
attempted the next item's allocation. Four loops carried that pattern, and iter-4/5/7 had made them
sequential on one finalize tail. Catching `MemoryError` before the generic handler and breaking is the
right minimal fix at the right choke point, and it is applied identically in all four places.

The honesty gating is the part I was most suspicious of, and it holds. Three loops already tracked an
"actually warmed" flag (`market_phase_warmed`, `drawdown_warmed`, and the per-date coverage loop which
never appended a category of its own). The fourth — forward-aggregates — appended `"forward_aggregates"`
**unconditionally** after its loop before this iteration; the dev correctly introduced
`forward_aggregates_warmed` so a first-horizon abort omits the category. That is a genuine honesty
improvement, not drift: it also fixes the pre-existing case where an empty `horizons` config would have
reported a category nothing warmed. `aggregates_refreshed` therefore still never names a category that
produced zero warmed items, under the new failure mode as well as the old ones.

Correctness is untouched, as required: the diff adds only `except MemoryError` branches, a flag, and a
gate — no computation, no cache key, no persisted value changes. The byte-identity guard
(`test_finalize_hook_drawdown_expectations_byte_identical_to_fresh_compute`, plus the new partial-abort
test re-asserting `stored == fresh`) passes. AG-8 is materially advanced for the tested scenario; AG-3,
AG-5, AG-7 and AG-9 are unaffected (no network, config, secret, or scoring code in the diff). Scope
discipline is good: `health.py`, `readiness.py`, `main.py`, `max_range_days`, `snapshot_cadence` and the
range-cap logic are all confirmed untouched, and the deferred `/api/backtest` on-load `MemoryError` is
carried forward in Known Issues as the spec's DoD item 9 required.

Where this iteration falls down is not the domain logic but the discipline around it: a 220-line block was
pasted into the middle of an existing test function, destroying that test's assertions and breaking the new
one, and three separate downstream gates (developer self-check, reviewer "test_quality: pass", QA
"2 PASSED ✓") reported green over it. The reviewer verified the *new* tests independently but read the
heavy test's body no further than the memory assertions. That is the failure mode worth recording in
`lessons.md`: when a large block is inserted into an existing test file, re-read the function boundaries
on both sides of the insertion point.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_start_backend_script.py` | T1 — restored TC-17's four orphaned clean-shutdown assertions to `test_start_backend_logfile_ends_abruptly_after_simulated_crash`, and removed them from the heavy-ingest test where they referenced an undefined `spawned_backend` (guaranteed `NameError`). |
| 2 | Important | `apps/backend/tests/test_start_backend_script.py` | T2 — both logfile slices now read `read_bytes()[offset:].decode(errors="replace")` so the byte offset and the slice share a unit; unblocks DoD item 7. |
| 3 | Important | `apps/backend/tests/test_start_backend_script.py` | T3 — `spawned_backend_throwaway_db` now skips unless `TRENDORA_RUN_HEAVY_INGEST_TEST=1`, so the DoD command completes and the host-crash-associated workload cannot start by accident. |
| 4 | Important | `apps/backend/app/engine/data_manager.py` | B1 — added `aborted_for_memory` flag; `_release_process_memory()` now also runs after the prefilled `_BarCache` context exits, so the abort path actually returns the ~1.5 GB cache's pages before the next warm block. Abort path only. |
| 5 | Important | `apps/backend/tests/test_data_manager.py` | B1 regression guard — `test_persist_per_date_coverage_memory_error_releases_memory_after_bar_cache_drops`, asserting a release occurs with no bar cache bound to the session. |
| 6 | — | `docs/handoffs/goal-ops-hardening-iter-8-dev.md` | Audit amendment section marking the handoff claims these fixes superseded (Known Issue #2 now fixed, TC-8 now clean, heavy test now opt-in, T1 splice). |

**Verification of the fixes (all commands run with the session-isolated `TMPDIR`):**

- `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -v -k "memory_error"`
  → **10 passed, 121 deselected in 2.12s** (the 9 dev tests + the new B1 guard).
- Negative control for fix 4/5: with `if aborted_for_memory:` disabled, the new guard **FAILS**; restored
  and re-verified passing.
- `cd apps/backend && .venv/bin/python -m pytest tests/test_start_backend_script.py -v`
  → **3 passed, 1 skipped in 4.15s** (was: 2 passed, 1 failed, 1 hanging). TC-16 and the repaired TC-17
  both pass; the heavy test skips with its opt-in reason.
- Literal DoD item 7 / TC-8 command, single invocation, nothing deselected:
  `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py tests/test_start_backend_script.py -q`
  → **134 passed, 1 skipped in 251.10s — 0 failures, 0 errors.** DoD item 7 is now satisfied as written,
  which it was not before this audit.
- `git diff` re-read on all four touched files: changes are confined to the four findings above; no
  unrelated edits, no assertions weakened, no new escape hatch (the added `MemoryError` handling was not
  broadened, and the skip guard is explicit and opt-in rather than silent).

---

## 5. Recommended Next Step

Do **not** treat J-05 as recovered yet. The code fix is sound and the live measurement is credible and
independently corroborated on its thermal half, but DoD item 1 — the browser-qa-agent pass over J-05's four
acceptance steps — has not happened (V1), and J-05 is still `regressed` in `journey-history.json`. Before
the evaluator flips it:

1. Run browser-qa for J-05 against the current build, with the host-guard protections active, and read the
   RAW `...-ui-test-results.llm.md` verdict rather than the merged summary (the iter-3/iter-4 lesson). Step
   4's heavy ingest can now be driven by the repaired pytest test — `TRENDORA_RUN_HEAVY_INGEST_TEST=1
   pytest tests/test_start_backend_script.py::test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap`
   — which, having never been executable before this audit, should be run at least once so the regression
   guard is proven rather than assumed. Copy its sampler output into `runs/goal-ops-hardening-iter-8/` (V3).
2. Re-verify J-01/J-03 by golden replay and J-04 by LLM acceptance to close DoD item 5 honestly (V2).
3. Then proceed to the deferred `/api/backtest` → `forward_aggregates_cached` → `ScannerResult` on-load
   `MemoryError` (iter-7 eval item 3), which this iteration correctly refused to bundle.
4. Carry B2 (memoize the libc handle so `_release_process_memory()` stops fork/exec-ing `ldconfig` on the
   memory-pressure path) and T4 (tighten the heavy test to reject `"partial"` and assert no `MemoryError`
   in the job record) into that iteration's scope as small cleanups.
5. Add to `lessons.md`: *when a large block is inserted into an existing test file, re-read the function
   boundaries on both sides of the insertion point* — this iteration silently deleted a live test's
   assertions and shipped a guaranteed-`NameError` test past three green gates.
