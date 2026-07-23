# goal-ops-hardening-iter-15 Audit Report

**Date:** 2026-07-23
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration delivers a correct, well-scoped, byte-identity-preserving single-flight de-dup fix to
`forward_aggregates_cached`'s MISS path, and it measured/disclosed the outcome with unusually rigorous
honesty (every raw operator-CSV figure I independently recomputed matched exactly; the developer even
surfaced discrepancies the operator's own summary omitted). The stacking pathology UT-04 exhibited is
genuinely eliminated (independently re-verified: TC-1 call-count == 1). However, the phase's literal GOAL
— closing the 211.8 s finding to the ≤1.5 s budget — is **not** met: the live deep-basis cold MISS is
still **178.74 s (WARN, ~119x over)**, because the dominant cost is one cold full-basis compute the
wrapper-scoped fix cannot touch. That residual is honestly recorded and is a legitimate owner/evaluator
decision per the spec's own escalation discipline, so it is a documented gap, not a failure. One IMPORTANT
consistency defect — the root-cause section overclaiming that redundant stacking "fully accounts for a
211.8 s finding," contradicted by the fix's own 15.6%-reduction live result — was fixed during this audit.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): root-cause conclusion overclaims candidate (a)'s share of the deep-basis finding**
`reports/perf-budgets.md:2284` (and the mirror at `docs/handoffs/goal-ops-hardening-iter-15-dev.md:33`)
concluded that candidate (a)'s redundant same-key stacking — extrapolated from the 60,000-row fixture's
9.91x ratio to "up to 10 redundant concurrent passes" at deep basis — "**fully accounts for a 211.8 s
finding**." The iteration's own live TC-4 pass contradicts this: post-fix the cold MISS is **178.74 s**, a
mere **15.6% reduction** from 211.8 s. Arithmetic: at deep-basis scale the pre-fix 211.8 s was only ~1.19x
a single cold `compute_forward_aggregates` pass (178.74 s), **not** the ~10x the fixture predicted — so
stacking accounts for ~15.6% of the deep-basis finding, and the dominant ~84% is one cold full-basis
compute the wrapper fix does not and cannot reduce. The reviewer flagged this as MINOR (review line ~2279)
but did not fix it; I upgraded it to IMPORTANT because per judgment-rubric §7.2 a headline claim that
contradicts the iteration's own measured artifact is a real honesty/consistency defect, and because it
directly feeds the developer's "escalation flag not triggered" decision (dev handoff Known Issue #3),
which under-signals to the evaluator that the real blocker (a 178 s single compute) needs an owner-level
decision.
**Fix applied:** added an evidence-cited "AUDIT RECONCILIATION" caveat immediately after the overclaim in
both files, pointing forward to the TC-4 RESULTS section and Known Issue #3, and stating plainly that
wrapper-only sufficiency for the ≤1.5 s budget is an open evaluator/owner call. The de-dup's correctness is
untouched by this edit (documentation only). Verified: numbers in the caveat recomputed
(`(211.8−178.74)/211.8 = 15.6%`; `211.8/178.74 = 1.185x`); the 3 fix tests still pass after the edit
(re-run below); no source/code file was touched by the fix.

**B2 — GAP (observation): the phase GOAL (≤1.5 s) is not met; the escalation flag is arguably mis-set**
The GOAL statement ("closing the 211.8-second concurrent-cache-miss finding") is not achieved — the live
result is 178.74 s WARN. Dev handoff Known Issue #3 states the escalation flag is "not triggered" because
"candidate (a) … dominates," but the live evidence shows the residual 178.74 s is exactly the class of
cost the escalation flag was written for: "a hard … limit that a targeted [wrapper-scoped] fix cannot
meaningfully reduce." This is not fixed here because (a) the spec makes the next step — an affordance, a
precompute-before-serve redesign, or accept-as-permanent — an explicit owner/evaluator call, not a
developer or auditor decision, and (b) the honest data required to make that call **is** surfaced (the
TC-4 RESULTS section says in terms that wrapper-fix sufficiency "is an evaluator call, not a
self-certification made here"). Recorded so the evaluator does not read Known Issue #3's "no escalation" in
isolation. My B1 fix connects the two.

**B3 — GAP (observation): four sibling ingest-time caches share the same no-dedup shape (out of scope, honestly disclosed)**
Dev handoff Known Issue #5 discloses that `research.event_study_cached`, `market_phase.market_phase_cached`,
`forward_testing.compute_drawdown_expectations_cached`, and `indexes.index_series_cached_with_status` have
no single-flight guard. I validated this: `research.py`, `market_phase.py`, and `indexes.py` each have
**zero** `threading`/`_LOCK`/`INFLIGHT` references (`grep`); the new `_FORWARD_AGG_*` globals live only in
`forward_testing.py` and key only on forward-aggregate keys, so `compute_drawdown_expectations_cached` is
also unguarded. This is a real latent concurrency/latency risk but was explicitly scoped out of iter-15
(the confirmed UT-04 culprit was `forward_aggregates_cached` only) and none has shown a live symptom.
Correctly a future-iteration scope call, not this one's.

**B4 — GAP (observation): unexplained second `/api/backtest` budget breach (5.37 s), undiagnosed**
`tc4-backtest-timings.csv` epoch 1784818231 = 5.373490 s (~3.6x over budget), ~8.6 min into the warm,
distinct from the 178.74 s cold MISS. Independently confirmed from the raw CSV. The operator's summary did
not mention it; the developer surfaced and flagged it honestly and did not diagnose it. Cause undetermined
(candidate: a later in-job dataset-version bump forcing a fresh compute, or transient contention). Left for
the evaluator; not diagnosable without another AG-10-restricted heavy pass.

### Frontend Findings

**F1 — n/a:** `Frontend Present: no`; the git diff confirms **no** file under `apps/frontend/` was touched.
No UI surface, page, nav entry, or displayed value changed. Correct per spec.

### Test Findings

**T1 — GAP (observation): TC-6 health liveness is "materially PASS" (498/500), not the DoD's literal "200 throughout"**
Two of 500 1 Hz health polls returned `000` (client-side curl 4 s cutoff, not a server 5xx) — epochs
1784817865 (4.002 s) and 1784818241 (4.003 s), both isolated and self-recovered on the next poll
(independently recomputed from `tc456-health.csv`; median 0.168 s, max 3.573 s all match exactly). The
first coincides with the tail of the 178 s cold compute — i.e. the single cold compute intermittently
starves concurrent health polls past a 4 s client cutoff. The DoD wording is "stays HTTP 200 throughout";
the artifacts honestly record "materially PASS" with the two exceptions stated plainly rather than rounded
to 500/500. No sustained wedge → not a blocker, but it is the same single-compute-monopolization symptom
as B2, worth the evaluator's note.

**T2 — GAP (observation): TC-7 (J-01/J-03/J-04/J-05 regression) deferred to the downstream browser-qa lane**
Not executed in the dev/QA snapshot I audited; the QA report and status.json defer it to the separate
browser-qa lane (framework fix `d0799803`). Standard for this pipeline, but it means "required-still-passing
journeys remain green" is asserted-pending, not yet evidenced, at this point in the chain. Flagged so the
evaluator confirms the browser lane actually ran green before certifying.

**T3 — OBSERVATION: thermal reporting discrepancy (84 °C measured vs 64 °C reported), no safety trip**
Recomputed from `logs/hwmon/hwmon.csv` for the exact window (655 samples): Tctl max **84 °C**, 620/655
(94.7%) above 64 °C — materially higher than the operator's reported "peaked 64 °C / 42 °C idle band," and
matching the developer's own flagged discrepancy exactly. No abort threshold breached (84 < 95 °C trip;
NVMe/DIMM well under limits), so "no trip" holds. Given this host's documented thermal/memory crash
history, the developer correctly flagged it as a priority reconciliation item rather than absorbing it.
Not an iter-15 code defect; a measurement-integrity item for the operator/evaluator.

---

## 3. Domain Assessment

**The fix is correct and the core mechanism is sound.** I traced every edge case of the single-flight
guard in `forward_aggregates_cached` (`forward_testing.py:1016-1125`):

- The owner-claim (`is_owner` check-and-set) is under `_FORWARD_AGG_LOCK` — two threads cannot both own a
  key. The wake `event` is sticky, so an owner that finishes before a late waiter calls `event.wait()`
  causes no lost-wakeup (the waiter's `wait()` returns immediately, re-reads → HIT).
- The `finally` releases the slot and wakes waiters on **both** success and exception (`if is_owner:`
  only — a fallback computer correctly does not touch the real owner's slot). TC-8 verifies a waiter never
  hangs past the bounded 45 s when the owner raises; the developer independently proved that test
  non-vacuous by disabling `event.set()` and observing the correct FAILURE.
- `_FORWARD_AGG_INFLIGHT` cannot leak — only owners insert, and always pop in `finally`.
- The commit-race path keeps its iter-14 `except Exception: session.rollback()` and still returns the
  freshly-computed (byte-identical) payload — WHO persists changes, never WHAT is returned.
- A genuinely-wedged owner degrades future same-key MISS callers to "wait ≤45 s, then compute
  independently" — bounded, never an infinite hang. Acceptable for a pathological state.

**Byte-identity (AG-3) is genuinely preserved.** The `git diff` shows `compute_forward_aggregates`
(lines 782-985) is untouched — the only changes are the `threading` import, the three module-level
`_FORWARD_AGG_*` globals, and `forward_aggregates_cached`'s MISS path. `app.db` is untouched, with a
measured justification (candidate (c) isolated at 1.59x, inside the 5.0x bound). All three call sites
(`api/backtest.py:72`, `mcp/tools.py:205`, `data_manager.py:3230`) are unchanged. AG-8 is not regressed —
the fix adds no whole-table ORM load; the streamed producer is unchanged.

**Independent verification I ran (host-guard-confined, `taskset -c 0-3,8-11`, BLAS/OMP threads=4):**
re-ran the three new iter-15 tests → `3 passed in 13.12s`; TC-1 asserts `compute_forward_aggregates` is
invoked **exactly once** for 5 concurrent same-key MISSes with byte-identical payloads — confirming waiters
correctly re-read the owner's committed row with their own fresh session (resolving the theoretical
SQLite-snapshot-isolation concern for the fresh-session-per-caller shape that both the test and production
request handlers use). Every operator-CSV figure I recomputed — 178.743092 s cold MISS, 5.373490 s spike,
498/500 health with the two exact non-200 epochs, VmPeak 4,005,376 KB, 84 °C thermal peak — matched the
transcription exactly.

**Honesty is the strongest attribute of this iteration.** The developer transcribed the operator pass by
recomputing from raw CSVs rather than trusting arithmetic, surfaced the operator's *own* unreported 5.37 s
spike and 84 °C peak, flagged that the operator's cited MemoryError log path (`/tmp/trendora-be15-tc4.log`)
is empty (0 bytes — I confirmed) while proving the underlying zero-MemoryError claim via the correct
`logs/backend.log` current-boot window, and refused to self-certify any J-06/J-07 pass. That is exactly
the disclosure discipline the spec's iter-9/iter-11 lessons demand.

**Minor freshness note (not a finding):** pid 4166118 (the measurement process) is no longer alive at
audit time — `logs/backend.log` shows two later boot banners (15:21:09Z, 16:06:20Z) that post-date the
measurement. The CSV data was captured under pid 4166118 and stands; the "process still alive" claim was a
point-in-time check that has since expired, not a fabrication.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/perf-budgets.md` (root-cause conclusion, ~line 2284) | Added an evidence-cited "AUDIT RECONCILIATION" caveat correcting the "fully accounts for a 211.8 s finding" overclaim — states the live TC-4 pass shows only a 15.6% reduction, so stacking accounts for ~15.6% of the deep-basis finding and the dominant residual is a single cold compute the wrapper fix cannot reduce; points to the TC-4 RESULTS section and Known Issue #3; notes wrapper-fix sufficiency is an open evaluator/owner call. |
| 2 | Important | `docs/handoffs/goal-ops-hardening-iter-15-dev.md` (line 33) | Added the matching reconciliation caveat to the identical overclaim in the dev handoff's root-cause narrative, pointing to its own Operator-Supervised Live Reproduction results and Known Issue #3. |

Both fixes are documentation-only (no code/behavior change). Post-fix verification: re-read both diffs
(they add only the caveat, preserve the original text, introduce no new inaccuracy); recomputed the caveat
arithmetic (15.6%, 1.185x — correct); re-ran the three iter-15 fix tests after editing → still
`3 passed in 13.12s`, confirming no code was disturbed.

---

## 5. Recommended Next Step

**Proceed to the evaluator with two explicit decisions to make — do not treat this as a clean close.**

1. **The ≤1.5 s `/backtest` budget is still not met (178.74 s WARN).** The correct read — now reconciled in
   both artifacts — is that iter-15 eliminated the *redundant-stacking* contributor (~15.6%) but the
   *dominant* cost is one cold full-basis `compute_forward_aggregates` pass that a wrapper-scoped fix
   cannot reduce. This is the escalation the spec reserved for the owner: choose among (a) a `/backtest`
   elapsed-time/progress affordance (the deferred iter-16 candidate), (b) a precompute-before-serve /
   incremental-aggregate redesign so a request never eats a cold full-basis compute, or (c) accept the
   deep-basis cold-MISS cost as a disclosed constraint. This is a genuine product decision, appropriately
   an owner/evaluator call, not something to resolve silently.
2. **Confirm the downstream browser-qa lane actually ran J-01/J-03/J-04/J-05 green (TC-7)** before
   certifying "required-still-passing" — it is deferred, not yet evidenced, at this snapshot.
3. **Reconcile the 84 °C-vs-64 °C thermal reporting gap** with the operator given the host's crash history,
   and note the undiagnosed 5.37 s spike and the four unguarded sibling caches (B3) as candidate future
   work — none blocks this iteration.

The backend fix itself is correct, tested, byte-identity-preserving, and honestly measured; it materially
strengthens the system by removing the stacking pathology. Ship it as a correct fix while routing the
still-open latency question to the owner.
