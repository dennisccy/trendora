# goal-ops-hardening-iter-52 Audit Report

**Date:** 2026-08-08
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** FAIL

The engineering in this iteration is good and I verified it independently: the GIL-stall diagnosis is
real, the chunked cooperative sort is genuinely byte-identical at live scale (I reproduced it at 260K
rows, tie-heavy and unique-key, plus the `range()` path `_average_ranks` uses), the frozen AG-10
surfaces are untouched, and the developer disclosed the residual TC-3 miss instead of rounding it up.
What fails is the iteration's verification contract, and it fails on an objective, machine-checkable
rule: **`apps/backend/app/engine/research.py` was modified at 2026-08-08 02:39:48, fifty-eight minutes
AFTER the 8-journey lane wrote its own results file at 01:41:48.** TC-9 is breached, so the only
independent journey evidence this round — which returned **FAIL for J-05 and FAIL for J-07**, the two
journeys the iteration exists to close — was measured against code that no longer exists, and the
headline TC-1 claim (0 non-answers) now rests solely on the implementing agent's own drill. The spec's
own remedy is mandatory and is not the auditor's to apply: "any fix-mode/audit-fix pass that changes
product code after the lane runs triggers a mandatory re-run before this iteration is scored."

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (gap — cannot be fixed in this audit): TC-9 breached; the 8-journey lane ran against
superseded code, and its FAIL verdicts on J-05/J-07 are the only independent evidence on record.**

Objective timestamps (`find apps -newermt "2026-08-08 01:41:48"`):

| file | mtime |
|---|---|
| `reports/phase-goal-ops-hardening-iter-52-ui-test-results.md` (the lane's own results file) | 2026-08-08 **01:41:48** |
| `reports/phase-goal-ops-hardening-iter-52-regression-replay-results.md` | 2026-08-08 **00:19:56** |
| `apps/backend/app/engine/research.py` (**product code**) | 2026-08-08 **02:39:48** |
| `apps/backend/tests/test_research_streaming.py` | 2026-08-08 02:20:58 |

TC-9 as written: "no product-code file under `apps/backend/` or `apps/frontend/` has an mtime later
than the lane's own results-file mtime." `research.py` does. This is not an inference from mtimes
alone — the developer's own artifact confirms it. `reports/perf-budgets.md:8082-8083` cites
`factor_lab_all_warm` at "643.32s on a **pre-fix** job run earlier the same day (`bc49c33b…`, whose own
tail totalled 1,327.86s)"; those are exactly the lane's own figures for job 332
(`ui-test-results.md:24` records `factor_lab_all_warm`'s 643.32s span; `:25` records the job at
1344.55s). Addendum 13 therefore classifies the lane's job as pre-fix in the developer's own words.
The lane's rows also cite Item U / Addendum 12 as the latest evidence (`ui-test-results.md:32`),
which is the first pass.

Consequences, stated exactly:

- `ui-test-results.md:32` — **UT-J-05 FAIL**: step 4 "did NOT hold", 47/1007 (4.67%) `/api/health`
  polls unanswered, clustered inside `factor_lab_all_warm`.
- `ui-test-results.md:34` — **UT-J-07 FAIL**: step 2 "did NOT hold", same shared measurement.
- Addendum 13's contradicting result (0 non-answers over 1,021 polls,
  `reports/perf-budgets.md:8051`) is a **developer-lane self-measurement** produced after the lane
  closed. It is a good measurement — dedicated poller process, real launch script, real
  `POST /api/data/jobs`, terminal `ok` — but nothing independent has reproduced it, and the framework's
  non-self-verification rule plus `.claude/judgment-rubrics.md` §2.1 ("journey-level evidence… not just
  unit tests") both point the same way.
- The two measurements do not actually contradict each other; they measured different trees. That is
  precisely the state TC-9 exists to prevent, and this session's history makes it load-bearing: the
  rule "held for the first time last round after 5 broken rounds — keep it held"
  (`docs/phases/goal-ops-hardening-iter-52.md:226-227`).

Not fixed here, deliberately: re-running the lane is browser-qa-agent work, and this spec binds the
auditor to findings-only (BACKGROUND, restating iter-51's second lesson,
`runs/goal-session-ops-hardening/state/lessons.md:462-471`). Any edit I made under `apps/backend/`
would deepen the same breach.

**B2 — IMPORTANT (gap): the DoD's perf-budgets requirement is unmet — J-06's Factor Lab browser
measurement is not in `reports/perf-budgets.md`.**

The DoD requires the addendum to carry three things: the health-poll result, the reconciled
finalize-tail total, "**and J-06's Factor Lab browser measurement** (never silently loosened or
silently omitted)". The third is absent. `reports/perf-budgets.md:8111` says outright: "**TC-7 (Factor
Lab real-browser TTI + on-load latency) — browser-lane work, not run here.**" The browser lane *did*
take the numbers — `domInteractive=45.4ms`, `domContentLoadedEventEnd=45.5ms`, `loadEventEnd=46.8ms`,
`GET /api/research/factor-lab?all=true` 200 in 0.0094s (`ui-test-results.md:33`) — but recorded that it
"NOT yet transcribed into `reports/perf-budgets.md` myself — that file is developer/audit-owned".
Neither side wrote it, so TC-7 is unmet and this is the **second consecutive round** the same debt is
carried (the spec's own BACKGROUND calls it "currently owed — it exists only inside a test report per
iter-51's own finding").

Not fixed here: appending to a report is not product code and would not itself breach TC-9, but the
numbers on offer were measured at 00:50-01:41 against the superseded tree (B1). Transcribing them now
would bake a stale measurement into the budgets file under a fresh 2026-08-08 date — the opposite of
what TC-7 asks for. The re-run in B1 will produce the correct numbers.

**B3 — IMPORTANT (gap): TC-2 was never executed, so the DoD's first line ("TC-1 through TC-12 all
pass") is false — and the review recorded `definition_of_done: complete` anyway.**

`reports/perf-budgets.md:8108-8110`: "**TC-2 (the concurrent drill) — not run this pass**… a solo run
cannot speak for the concurrent case." The QA report marks TC-2, TC-7, TC-8, TC-9 and TC-12 "DEFERRED"
(`reports/qa/goal-ops-hardening-iter-52-qa.md:103-113`), while the review report records
`spec_alignment.definition_of_done: complete` (`reports/reviews/goal-ops-hardening-iter-52-review.md:17`).
TC-2 is the *worst* historical case (19/892 non-answers, UT-08) and is the one scenario a solo drill
provably cannot cover — it is also the scenario that would stress B5. The execution plan predicted this
exact recurrence: "iter-51's DoD checkbox falsely read 'TC-1 through TC-9 all pass' while TC-5/TC-6 were
unmet — reviewer/QA/auditor must verify each TC individually" (`runs/goal-ops-hardening-iter-52/plan.md:143-145`).

**B4 — IMPORTANT (gap): TC-6's live evidence predates the shipped implementation of the function it
exercises.** (Unsure between IMPORTANT and GAP; chose the higher because QA scored TC-6 "PASS".)

`test_ingest_finalize_factor_lab_all_fault_is_honestly_omitted_health_stays_live` is opt-in gated
(`apps/backend/tests/test_start_backend_script.py:939`). It was among the "5 skipped" in the
developer's fix-pass run (`status.json` `tests_result`), the reviewer's 373-test run, and QA's 363-test
run. Its only live execution — "1 passed in 838.77s" — was on **2026-08-07**, during the initial build.
The fix pass then rewrapped the exact code path it drives: the fault-injection site now sits inside
`with _cyclic_gc_paused():` (`research.py:1410`, injection at `:1412`). The handoff's "the TC-6 live
fault-injection test [is] unchanged and still pass[es]" is therefore an unverified claim about the
shipped tree. Mitigation on record: the unit-level
`test_compute_factor_lab_all_restores_the_collector_after_an_injected_memory_error` does cover
collector-restore-under-fault and honest `unavailable` degradation — I ran it (see §4).

**B5 — GAP: `_cyclic_gc_paused` does not compose across threads, and its aggregate effect is the whole
phase, not "seconds".**

Half of this is the reviewer's MINOR (`review.md:24-30`) and I reproduced it. With two overlapping
windows (the finalize tail plus a live `?all=true` request, which `research.py` explicitly still
serves), the second entrant reads `gc.isenabled() == False`, so when the first exits and re-enables,
**the second runs its entire remaining window with the collector ON**. My probe: `5b. B still saw
collector ON inside its own window: True`. The final state is always restored correctly (`5c: True`),
so it shrinks the fix's effect and never leaks a permanently-disabled collector — the reviewer's
characterisation is right.

The half nobody flagged is the aggregate. The window is entered once per (factor, horizon) at
`research.py:1410`, with nothing but loop bookkeeping and a `time.sleep(0)` between one exit and the
next entry. Across `factor_lab_all_warm`'s 55 entries / 486.62s the automatic cyclic collector is
therefore suppressed for effectively the **entire phase**, not for "one item of one loop (seconds, not
the whole phase)" as `research.py:165` states, nor "for the seconds it is in effect" as the handoff's
Known Issues says. Every concurrent request's cyclic garbage (SQLAlchemy sessions being the obvious
producer) is deferred for that whole window, on a host with a hard 8,192 MB `ulimit -v` and a
documented MemoryError history that is J-07's entire reason for existing.

I am recording this as GAP, not IMPORTANT, because there is **no measured failure**: the post-fix drill
held VmPeak at 4,147.4 MB with 49.4% margin while a 1/s health poller ran throughout
(`perf-budgets.md:8054`). But 1/s polling is the lightest possible concurrency, and the drill that
would actually stress this — TC-2 — was not run (B3). The lane separately measured the *pre-fix*
backend at VmPeak 8,192.0 MB (0% headroom on virtual) and VmHWM 7,570.6 MB / 92.4% of cap over a ~2h
process lifetime (`ui-test-results.md:34`); that is a process-lifetime high-water mark on superseded
code, so it does not indict this change, but it does say the ceiling this defers work against is not
comfortable.

**B6 — OBSERVATION: `_cooperative_sorted`'s "byte-identical, by construction, not by hope" comment is
unconditional where it needs a stated precondition (a total order on the key).**

I verified the invariant independently rather than accepting the argument (`research.py:100-125`):

| probe | result |
|---|---|
| 260K rows, unique key `(factor, ticker, run_id)`, real `_SORT_YIELD_CHUNK=50_000` — identical by object identity | **True** |
| 260K rows, key deliberately excluding the unique element (stability load-bearing) | **True** |
| `range()` input, exactly as `_average_ranks` passes it (`research.py:213`); `_average_ranks` output equality | **True / True** |
| same input with NaN present in the key | **False — diverges** |

The divergence is real (NaN makes `<` non-total, so a merge of runs is not the same permutation as one
Timsort pass), and it is unreachable at these three call sites: every key element is a DB-sourced float,
and SQLite stores NaN as NULL — I checked (`sqlite roundtrip of NaN -> (None, 'null')`) — which the
`_has[core_idx]` / NULL filters already exclude. Documentation precision only; no code change warranted.

### Frontend Findings

None. No frontend file is touched and none should be (spec: "Frontend: None"). `git status` confirms
zero changes under `apps/frontend/`. The UX-regression reviewer was shed for budget
(`reports/phase-goal-ops-hardening-iter-52-ux-regression.md:3`, UX-REGRESSION-SKIPPED) — non-blocking
and correctly disclosed.

### Test Findings

**T1 — OBSERVATION: TC-6's health poller is materially more forgiving than TC-1's client, so its
"health stays 200 throughout" is a weaker statement than it reads.** `_HealthPoller`
(`apps/backend/tests/test_start_backend_script.py:630-647`) polls every ~2s with a **10.0s** timeout;
TC-1's drill polls 1/s with a **5.0s** ceiling. A 6-second answer is a clean `200` here and a
non-answer there. To its credit there is no escape hatch: a refused/timed-out poll is appended as
`{"status": None}` (`:645-646`) and the assertion `r.get("status") != 200` does catch it — I checked
this specifically, because "assert no non-200" over a list that silently drops failures is exactly the
shape that passes by accident.

**T2 — OBSERVATION: the reviewer's two NOTE-level test items are still open.** (a) The TC-6 test
asserts only `"coverage" in refreshed` where TC-6's text says "the other categories still appear"
(plural) — `test_start_backend_script.py:1040`; (b) no test spies on `_cyclic_gc_paused` /
`_cooperative_sorted` invocation counts inside `compute_factor_lab_all` itself, unlike the
`time.sleep` spies, so a partial revert of just the call-site wiring at `research.py:1410`/`:1439`
would leave the helpers defined, independently tested, and green. Both are correctly scoped as
optional by the reviewer.

**T3 — OBSERVATION: `runs/goal-session-ops-hardening/journey-scripts/J-05.json` still did not
execute — a third consecutive round.** The regression-replay lane ran J-01/J-03/J-08/J-09 only
(`regression-replay-results.md:19-22`); J-05 got an LLM-lane row instead
(`ui-test-results.md:32`), which satisfies TC-8 but not the spec's golden-script caution
("confirm they actually RUN this time"). J-06.json **was** replayed via `demo_runner.py --mode
verify`, 1/1 passed (`ui-test-results.md:33`) — first execution in three rounds, worth recording as
progress.

---

## 3. Domain Assessment

The domain reasoning in this iteration is the strongest I have seen in this session, and I want that on
the record separately from the verdict.

The first pass added `time.sleep(0)` yields and the live drill got *worse* (22 non-answers vs a
baseline of 9). The developer published that negative result as Item U rather than burying it, then
profiled instead of hypothesising: a worker thread running the real `compute_factor_lab_all` against
the committed DB, a probe thread measuring GIL-acquisition stalls, and the worker's stack captured **at
the instant each stall resolved**. That named the line — `sorted(obs, key=…)` at 1.09–1.23s a call —
and surfaced the half nobody had guessed, 154 gen-2 collections totalling 121.37s of a 571.94s phase.
The explanation for why the first pass could not have worked is exactly right: a `list.sort()`
comparison phase and a GC pass are each a single C-level call that never reaches an eval-breaker check,
so a yield placed *before* an iteration cannot interrupt work happening *inside* it.

The fix follows the diagnosis rather than the symptom, and each of its three parts was chosen from a
measured curve, not from taste (chunk size 50K → 0.037s/−4% against 100K → 0.082s/+7% and 200K →
0.201s/+20%; `gc.freeze()` measured ineffective and **dropped**). The byte-identity argument is
correct — a merge of contiguous stably-sorted runs, tie-broken by iterable index, *is* the stable sort
of the whole population — and, unusually, it is proved rather than asserted: object-identity assertions
so a re-derived-but-equal value still fails, plus end-to-end `json.dumps(..., sort_keys=True)`
comparison with `_SORT_YIELD_CHUNK = 1`. I re-derived it independently at 260K rows and it holds
(§2/B6). `_deciles` (`research.py:786-815`) retains only scalars, so the bounded release at
`research.py:1483` cannot strand a served value; `_BoundedRankWindow._trim`'s rebinding of `self._buf`
(`:595`) is safe because no external alias to that list exists. The honesty is real too: TC-3 is
"improved but NOT fully met, and is not claimed as met", the two remaining >2s contributors are named
rather than left implicit, and the residual is attributed by anchor timestamp — with **zero** slow
polls inside `factor_lab_all_warm`'s own 486.62s window, which is the cleanest evidence in the addendum
that the fix acted where it was aimed.

None of that is in question. What is in question is that the iteration's central claim was verified by
the agent that made the change, after the independent lane had already closed and returned FAIL on the
two journeys concerned. Good engineering plus stale independent evidence is still an unscoreable
iteration under this spec's own rules.

---

## 4. Fixes Applied During This Audit

**None — findings-only, by binding instruction, not by choice or by running out of room.**

The phase spec restates iter-51's second lesson as this round's expectation: "findings-only during
audit when the TC-8/TC-13 lane-runs-last rule is in force… stated as the expectation, not left to the
auditor's judgement" (`docs/phases/goal-ops-hardening-iter-52.md:92-95`;
`runs/goal-session-ops-hardening/state/lessons.md:462-471`). Editing anything under `apps/backend/`
here would deepen the very breach B1 reports. B2's transcription is not product code, but its only
available numbers were measured against the superseded tree and would be misleading under a fresh date.

Verification I ran (read-only; no product file touched — `git status` on `apps/` is unchanged from
what I inherited):

| # | check | command / probe | result |
|---|---|---|---|
| 1 | cooperative-sort + gc-pause unit tests | `.venv/bin/python -m pytest tests/test_research_streaming.py -q -p no:randomly -k "cooperative_sorted or cyclic_gc_paused"` | **14 passed**, 92 deselected, 0.06s |
| 2 | independent byte-identity at live scale | 260K rows unique-key / 260K tie-heavy / `range()` path (§2/B6) | identical by object identity |
| 3 | NaN precondition probe | same, NaN in key | diverges — unreachable via SQLite (verified) |
| 4 | `_cyclic_gc_paused` thread overlap | two overlapping windows, one exiting first | later window runs with GC ON; final state correctly restored |
| 5 | TC-10 frozen surfaces | `git diff --stat config.yaml project-extensions/host-guard/host-guard.env scripts/start-backend.sh scripts/dev.sh scripts/start-frontend.sh` + `git status --porcelain` on those paths | **EMPTY** — AG-10 intact |
| 6 | AG-7 secret scan | `git diff apps/backend \| grep -Ei "api[_-]?key\|secret\|token\|password\|bearer "` | no hits |
| 7 | TC-9 sequencing | `find apps -newermt "2026-08-08 01:41:48"` | **`research.py` at 02:39:48 → breach (B1)** |

---

## 5. Definition-of-Done Verification

| # | DoD item | Verdict | Evidence |
|---|---|---|---|
| 1 | TC-1 … TC-12 all pass | **NOT MET** | TC-2 never run (`perf-budgets.md:8108`); TC-7 not met (B2); TC-9 breached (B1). Per-TC table below. |
| 2 | J-04/J-05/J-06/J-07 each produce a REAL executed row | **MET in letter** | `ui-test-results.md:31,32,33,34` — UT-J-04 PASS, UT-J-05 FAIL, UT-J-06 PASS, UT-J-07 FAIL. None deferred, none zero-row. All four measured against superseded code (B1). |
| 3 | J-01/J-03/J-08/J-09 remain green | **MET in letter** | `regression-replay-results.md:19-22`, 4/4 PASS — replayed 00:19:56, i.e. before both the chunked sort and the GC pause landed (B1). |
| 4 | No anti-goal violation introduced | **MET** | AG-10 §4 row 5 (verified myself, empty); AG-9 `"source": null` (`perf-budgets.md:8118`, QA TC-11 row); AG-7 §4 row 6; AG-3/AG-5 §4 rows 1-2 plus the pre-existing pinned-reference tests. |
| 5 | Unit tests pass; no regressions | **MET** | Reviewer independently re-ran 373 tests (`review.md:13-15`); QA 363 passed / 5 skipped (`qa.md:34`); dev 500 passed / 5 skipped across 8 files. `test_ingest_finalize_fault_injection.py` exists and is in the run set. Caveat: the 5 skipped include TC-6 (B4). |
| 6 | perf-budgets addendum carries health-poll + finalize-tail + **J-06 browser measurement** | **PARTIAL** | First two present (`perf-budgets.md:8043-8085`); third absent (B2). |
| 7 | Lane runs LAST, no product-code change afterward (TC-9) | **NOT MET** | B1. |
| 8 | Dev handoff written | **MET** | `docs/handoffs/goal-ops-hardening-iter-52-dev.md`, rewritten for the fix pass 03:08. |

Per-TC, verified individually as the plan demanded (no blanket checkbox):

| TC | Verdict | Note |
|---|---|---|
| TC-1 | MET, not independently confirmed | 0/1,021 (`perf-budgets.md:8051`) — developer-lane self-measurement; the lane's own contrary 47/1007 is pre-fix (B1) |
| TC-2 | **NOT RUN** | `perf-budgets.md:8108` |
| TC-3 | MET as written | TC-3 requires honest recording, not compliance; recorded honestly (`perf-budgets.md:8087-8099`). The ≤2s ceiling itself is **not** met — 16/1,021, worst 3.818s |
| TC-4 | MET | §4 rows 1-2 + object-identity and json byte-comparison tests |
| TC-5 | MET, not independently confirmed | 955.75s vs 1,200s (`perf-budgets.md:8072`); the lane's own pre-fix job ran 1,327.86s tail |
| TC-6 | MET on stale evidence | B4 |
| TC-7 | **NOT MET** | B2 |
| TC-8 | MET | all four target journeys have real executed rows |
| TC-9 | **BREACHED** | B1 |
| TC-10 | MET | verified myself, §4 row 5 |
| TC-11 | MET | `"source": null`, `backfill` never enters the fetch branch |
| TC-12 | MET in letter | replayed pre-fix (B1) |

---

## 6. Recommended Next Step

**Do not score this iteration yet. Re-run the 8-journey lane against the current tree, then re-audit.**
The remedy is cheap and fully specified; nothing about the fix needs redesigning.

1. **Re-run the full 8-journey browser/replay lane** against the tree as it stands now, with **zero**
   product-code changes afterward (TC-9). This is the whole of B1 and it also re-scores TC-8 and TC-12.
   J-05 and J-07 are the rows that matter: their FAIL verdicts were measured on the first-pass code and
   the fix specifically targets what failed. Freeze `apps/backend/` before dispatching.
2. **While the lane is out, run TC-2** — the concurrent drill (`GET /research/factor-lab?all=true` or
   `/research/factor-combination` issued mid-warm). It is the only unmeasured acceptance case, it
   carries the worst historical evidence (19/892), and it is the one drill that would exercise B5's
   whole-phase collector suspension under real concurrency.
3. **Re-run TC-6's live test** (`TRENDORA_RUN_HEAVY_INGEST_TEST=1`) against the shipped tree so its
   evidence stops predating the function it exercises (B4).
4. **Transcribe J-06's Factor Lab TTI and on-load `?all=true` latency into a dated
   `reports/perf-budgets.md` section** from the *new* lane run, closing TC-7 and the DoD's third
   addendum item (B2) — second round carried, do not let it become a third.
5. **Correct the two documentation overstatements** whenever the next product-code change is licensed
   (not before, and not as an audit edit): `research.py:165`'s "seconds, not the whole phase" and
   `research.py:100-125`'s unconditional byte-identity claim (B5, B6).
6. **Carry forward, do not fix now:** the reviewer's depth-counter suggestion for `_cyclic_gc_paused`
   (B5), the plural-category assertion and call-site invocation spies (T2), and J-05.json's third
   unexecuted round (T3).
7. **For the pipeline, not this iteration:** TC-9 is a two-line mechanical check
   (`find apps -newermt <lane-results-mtime>`). It was breached this round with a reviewer verdict of
   `definition_of_done: complete` and a QA table that marked TC-9 "DEFERRED" rather than checking it.
   Making that `find` a gate in the QA step would have caught this in seconds — this is the sixth round
   in seven that the lane-last rule has been at issue.
