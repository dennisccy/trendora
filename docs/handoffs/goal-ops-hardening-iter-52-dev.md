# goal-ops-hardening-iter-52 Dev Handoff

**Phase:** goal-ops-hardening-iter-52
**Date:** 2026-08-07 (initial build) · 2026-08-08 (FIX PASS after QA FAIL) · 2026-08-08 (AUDIT-FIX PASS)
**Agent:** developer
**Status:** complete

> Newest pass first. Each earlier pass's content is preserved below, because each one's measurement is
> the evidence that motivated the next and must not disappear.

---

# AUDIT-FIX PASS (2026-08-08) — Fix Notes

Input: `docs/handoffs/goal-ops-hardening-iter-52-audit.md`, verdict **FAIL**.

## What the audit asked for, and what this pass did

| audit item | action taken |
|---|---|
| **B1 / TC-9 (CRITICAL)** — the 8-journey lane ran 58 min BEFORE `research.py` last changed, so its FAIL verdicts on J-05/J-07 were measured against superseded code | **Cannot be fixed here — the lane must re-run.** This pass makes exactly one product-code edit (comments only, below) and then freezes `apps/backend/`. The lane must run LAST, after this pass. See "What the next step must be". |
| **B2 / TC-7 (IMPORTANT)** — J-06's Factor Lab browser measurement absent from `reports/perf-budgets.md`, second round carried | **CLOSED.** Both numbers measured against the SHIPPED tree and written into `reports/perf-budgets.md` Item W / Addendum 14 — real-browser `domInteractive` 21.0-25.3 ms, `loadEventEnd` 246.9-251.6 ms, heading visible 52.8-57.5 ms, page settled 1,144.9-1,252.9 ms; on-load `?all=true` 0.0098-0.0646 s warm. |
| **B3 / TC-2 (IMPORTANT)** — the concurrent drill was never executed | **RUN. Result: TC-2 NOT MET — 2 non-answers of 1,285 polls (0.156%)** against UT-08's 19 of 892 (2.13%). 13.7x better, not zero, and reported as not met. |
| **B4 / TC-6 (IMPORTANT)** — TC-6's only live run predated the code it exercises | **CLOSED.** Re-run live on the shipped tree: `1 passed, 15 deselected in 1076.19s (0:17:56)`. |
| **B5 (GAP)** — `_cyclic_gc_paused` does not compose across threads, and its aggregate effect is the whole phase, not "seconds" | **Documentation corrected** in `research.py` (the audit licensed exactly this). The depth counter is deliberately NOT added (audit item 6, carry forward). The concurrency evidence B5 wanted is now on record: VmPeak 4,886.2 MB / 40.4% margin, no `MemoryError`, under continuous concurrent load. |
| **B6 (OBSERVATION)** — the byte-identity claim is unconditional where it needs a stated precondition | **Documentation corrected** in `research.py`: the total-order precondition is now stated, the NaN divergence is named, and why it is unreachable at all three call sites is given. Also fixed the same block's inaccurate "every call site has a UNIQUE key" — `_average_ranks` deliberately does not, and relies on stability. |
| **T1, T2, T3 (OBSERVATIONS)** | Left as the audit scoped them (optional / carry forward). No change. |
| audit item 6 — depth counter, plural-category assertion, call-site invocation spies, J-05.json | **Not fixed, by instruction.** Carried forward. |

## The only product-code change in this pass

`apps/backend/app/engine/research.py` — **two comment/docstring blocks, no executable line touched**:

1. `_cooperative_sorted`'s header block: the byte-identity claim now states its precondition (a total
   order on the key), names the NaN case that breaks it, records that it was checked and does diverge,
   and gives the reason it is unreachable here (DB-sourced floats; SQLite stores NaN as NULL; the
   `_has[core_idx]`/NULL filters already exclude those rows). It also corrects the block's own claim that
   every call site has a unique key — `_average_ranks` orders `range(n)` by a constantly-tying value and
   depends on stability instead.
2. `_cyclic_gc_paused`'s docstring: "for one item of one loop (seconds, not the whole phase)" is replaced
   with the accurate aggregate statement — 55 back-to-back entries mean the collector is suspended for
   effectively the whole `factor_lab_all_warm` phase — and the implication that the pause composes across
   threads is replaced with what actually happens: a second overlapping entrant reads
   `gc.isenabled() == False`, so when the first window exits and re-enables, the second runs its
   remaining window with the collector ON. Overlap WEAKENS the pause; it cannot leak one.

Edit landed **2026-08-08 03:55:25**. Every measurement below started **03:58:21 or later**, so all of it
is against the shipped tree. `git status --porcelain` over `apps/frontend/` is empty; no other product
file was touched.

## Measurements taken this pass (all in `reports/perf-budgets.md` Item W / Addendum 14)

**TC-2 — concurrent drill.** Addendum 13's exact methodology plus a third dedicated process keeping one
heavy research request outstanding throughout (`?all=true` / `factor-combination`, alternating, 2s gap).
Job `ff98726ddd2942eaa70e88a54dd675eb`, 2019-02-15, `"source": null`, terminal **`ok`** in 1,375.67s.

- **1,285 health polls, 1,283 HTTP 200, 0 error statuses, 2 non-answers (0.156%)** — vs UT-08's 19/892.
- Both non-answers have **`connect_s = 0.000`**: the socket was accepted instantly and the server then
  missed the 5.0s first-byte ceiling. Not a dead socket, not an accept-backlog failure.
- Both fall in **`coverage_membership_timeline_refresh`** (t+152.8s) and **`market_phase_warm`**
  (t+191.2s) — precisely the two phases the previous pass's Known Issues named as untreated. **Zero** in
  `forward_aggregates_warm` (738.70s here) and zero in `factor_lab_all_warm`.
- TC-3 concurrent: **34 of 1,283 (2.65%) over 2.0s, worst 4.901s** — worse than solo's 16/1,021, as a
  second CPU-bound compute in one process should be. Not met; not claimed as met.
- TC-5 concurrent: finalize tail **1,261.42s — 61.42s (5.1%) OVER the 1,200s budget**. Disclosed, not
  loosened. Solo on the same tree three hours earlier was 955.75s, under budget.
- Memory (the audit's B5 stress): VmPeak **4,886.2 MB** / VmHWM 4,245.6 MB against the 8,192 MB cap →
  **40.4% margin**, no `MemoryError`, no traceback, no `ERROR` line in the drill window.

**One honest caveat that shapes how this drill should be read.** The concurrent `?all=true` request fired
at t+270s computed the all-history Factor Lab payload itself (it outran the load client's own 600s
ceiling), so by the time the finalize tail reached `factor_lab_all_warm` the value was cached and the
phase took 0.05s. **This drill therefore does not exercise the phase iter-52's fix targets** — the work
moved into the request path, which runs the same function with the same fix, but the phase table does not
show it. Addendum 13 remains the measurement that speaks for `factor_lab_all_warm` itself.

**TC-6 — re-run live on the shipped tree:** `1 passed, 15 deselected in 1076.19s (0:17:56)`.

**TC-7 — both numbers, measured (developer lane, disclosed as such):** real-browser `domInteractive`
21.0/22.8/25.3 ms, `domContentLoadedEventEnd` 21.0/22.8/25.4 ms, `loadEventEnd` 246.9/250.5/251.6 ms,
Factor Lab heading visible 52.8/57.1/57.5 ms, whole page settled (`networkidle`) 1,144.9/1,156.0/1,252.9
ms, 11 factor rows rendered each run; on-load `?all=true` 0.0516/0.0098/0.0646 s warm from the same
still-running post-ingest process. Disclosed: the page fires `?all=true` **twice** per load (React dev
double-invoke, ~10ms each), and `networkidle` is 5x `loadEventEnd` because this is a client-rendered page.

## Anti-goals re-verified this pass

- **AG-10 / TC-10:** `git diff --stat` **and** `git status --porcelain` over `config.yaml`,
  `project-extensions/host-guard/host-guard.env`, `scripts/start-backend.sh`, `scripts/dev.sh`,
  `scripts/start-frontend.sh` — EMPTY. Every service in this pass was launched by
  `scripts/start-backend.sh` / `scripts/dev.sh`.
- **AG-9 / TC-11:** persisted job record `"source": null`; `/api/health` reports `"provider": "seed"`.
  The `source: 'yahoo'` that `POST /api/data/jobs` echoes is the endpoint echoing
  `cfg.data_manager.default_source`, not what the job runs against — a `backfill` is not in
  `_FETCH_KINDS`, so `_resolve_live_provider` is unreachable.
- **AG-7:** `git diff apps/backend | grep -Ei "api[_-]?key|secret|token|password|bearer "` — no hits.

## Files Changed (audit-fix pass)

- `apps/backend/app/engine/research.py` — **two comment/docstring blocks only** (the byte-identity
  precondition and the `_cyclic_gc_paused` aggregate/threading correction). No executable line changed;
  `git diff` on this pass is comments end to end.
- `reports/perf-budgets.md` — new `## Item W` / `### Addendum 14` (append-only; Items T, U and V
  untouched).
- `docs/handoffs/goal-ops-hardening-iter-52-dev.md` — this section, plus one correction inside the FIX
  PASS's own Known Issues where the audit named the same overstatement (marked as a correction, the
  original left visible).
- `reports/phase-goal-ops-hardening-iter-52-implementation-summary.md` — updated for this pass.
- `runs/goal-ops-hardening-iter-52/status.json` — `current_step: dev_complete`.

No test file changed this pass. No schema, migration, config key or environment variable.

## Tests Run (audit-fix pass)

Command: `cd apps/backend && .venv/bin/python -m pytest <paths> -q -p no:randomly`

- **TC-6 live**, opt-in: `TRENDORA_RUN_HEAVY_INGEST_TEST=1 ... -k
  test_ingest_finalize_factor_lab_all_fault_is_honestly_omitted_health_stays_live` →
  **1 passed, 15 deselected in 1076.19s**.
- **Helper unit tests** (`-k "cooperative_sorted or cyclic_gc_paused"`) → **14 passed, 92 deselected**.
- **Targeted + downstream-of-diff files** (`test_data_manager.py`, `test_research_streaming.py`,
  `test_research.py`, `test_forward_testing_aggregates_streaming.py`, `test_forward_testing_streaming.py`,
  `test_factor_lab_all.py`, `test_ingest_finalize_fault_injection.py`, `test_start_backend_script.py`) →
  **500 passed, 5 skipped (heavy, opt-in-gated), 0 failed, in 521.14s** — identical to the fix pass's own
  500/5/0, so this pass introduced no regression. The 5 skips are the opt-in heavy fixtures; TC-6, one of
  them, was executed separately above.
- The full 30-year backend suite was NOT run (this project's established convention — ~10-11h; targeted
  and downstream-of-diff files only).

## Raw evidence for this pass — re-checkable, not just quoted

Everything in `runs/goal-ops-hardening-iter-52/evidence-audit-fix/` (durable, in the iteration's own run
directory — not the QA lane's evidence directory):

| file | what it is |
|---|---|
| `tc2-health-polls.csv` | every one of the 1,285 health polls: `epoch_ms, http_code, total_s, connect_s, ttfb_s`. The two `000` rows are the non-answers; both show `connect_s=0.000`. |
| `tc2-concurrent-research-load.csv` | all 164 concurrent research requests with their own latencies |
| `tc2-summary.json` / `tc2-job-record.json` / `tc2-drill.log` | job id, target date, terminal status, VmPeak/VmHWM, `"source": null`, phase progression |
| `tc6-live-pytest.log` | the TC-6 live run's own pytest output (`1 passed ... 1076.19s`) |
| `tc7-j06-browser-tti.json` / `tc7-j06-factor-lab.png` | all three browser runs' raw navigation + resource timings, and the rendered page |
| `targeted-tests.log` | the 500-passed/5-skipped run |
| `run_drill_concurrent.py`, `load_research.py`, `poll_health.py`, `analyze.py`, `measure_j06_tti.py` | the exact scripts, so any of this can be re-run rather than taken on trust. `poll_health.py` and `analyze.py` are byte-identical to the ones Addendum 13 used, which is why the two drills are comparable. |

## What the next step must be (TC-9)

**The 8-journey browser/replay lane must re-run against the current tree, and nothing under
`apps/backend/` or `apps/frontend/` may change afterward.** That was true before this pass (audit B1) and
it is still true after it: this pass's comment edit is itself a product-code change, so the lane's
existing results file is superseded either way. J-05 and J-07 are the rows that matter — their FAIL
verdicts were measured on the first-pass code, and the fix specifically targets what failed there.

## Known Issues added by this pass

- **TC-2 is NOT met** (2 non-answers) and **TC-3 is not met in either drill**. Both residuals now sit in
  `coverage_membership_timeline_refresh`, `market_phase_warm` and `forward_aggregates_warm`, none of which
  received the chunked-sort / bounded-GC treatment. Giving them the same treatment is the obvious next
  named change; it is deliberately NOT attempted here, because this pass is licensed to fix the audit's
  listed findings only and a new risky change would immediately invalidate the lane run that must follow.
- **The finalize tail exceeds its 1,200s budget under concurrency** (1,261.42s vs 955.75s solo). Either
  the budget is a solo-only budget and should say so, or the phases above need the work. An owner call.
- **A live `?all=true` request can still block for more than 600s during an ingest** — one of the 164
  concurrent requests did, and answered nothing to that client. Same starvation class, seen from the
  request side. Worth its own measurement; not diagnosed here.
- **The TC-2 drill did not exercise `factor_lab_all_warm`** (see the caveat above). A repeat drill that
  issues its concurrent requests only AFTER the tail reaches that phase would close that gap.
- **TC-7's numbers are a developer-lane measurement.** They were taken against the shipped tree with a
  real browser, which is what TC-7 asks for, but the browser lane's own re-run should corroborate them —
  and if the two disagree, the lane's number governs.

---

## FIX PASS (2026-08-08) — what changed and why

### The QA blockers

1. **TC-1 NOT MET** — 22 connection-level `/api/health` non-answers, against a pre-fix baseline of 9.
2. **TC-5 NOT MET** — finalize-tail wall-clock 1,670.95s (partial run) vs the 1,200s budget.
3. (disclosed, not a blocker) 3 of the 22 fell inside the `backfill`/snapshot-write stage.

### First correction: the failure class was mis-named

Item U counted these as *connection-level* non-answers (`curl code=000`, "no response at all"). A direct
read of `logs/backend.log` over the drill's own window (strictly between the first and last
`GET /api/data/jobs/a24c8604…` access line) shows **1,476 `GET /api/health` responses, every one HTTP 200,
zero non-200**. The client recorded 1,471 answered + 22 unanswered = 1,493 polls in a slightly wider
window. **The server never refused, dropped, or failed a connection — it produced a 200 for every request;
22 of those answers simply arrived after the client's own 5.0s ceiling.** The class is "slower than 5s",
not "dead socket". That matters because it rules out the accept-backlog / connection-handling theories and
points squarely at request latency under GIL contention.

### Root cause (measured, with the offending line named)

`_release_process_memory` was ruled out first: all six of its logged calls are ≤ 0.21s
(`gc_collect=… malloc_trim=…` lines in `logs/backend.log`).

A GIL-stall profile was then run against the **real committed DB**: `compute_factor_lab_all` in a worker
thread, a probe thread measuring GIL-acquisition stalls, and the worker's **stack captured at the instant
each stall resolved**. 571.94s, 69,608,603 observations across 55 (factor, horizon) entries, pool sizes
1,244,600–1,276,566 per horizon. Result:

- **197 stalls > 0.30s**, overwhelmingly on ONE line — `research.py:1332`,
  `sorted(obs, key=lambda o: (o.factor, o.ticker, o.run_id))` — at **1.09–1.23s each**.
- **154 gen-2 GC pauses > 50ms totalling 121.37s**, worst **1.088s**, driven by the ~1.27M
  `_FactorLabAllObs` alive per entry.

**Why iter-52's first pass could not have worked:** a `list.sort()` comparison phase and a garbage
collection are each a *single C-level call* that never reaches an eval-breaker check. A `time.sleep(0)`
placed at the top of an iteration cannot interrupt work happening inside that iteration. The dev handoff's
own hypothesis about the sort was right; the GC half was not known before this pass.

### The fix (three parts, all byte-identical, all measured)

1. **`_cooperative_sorted`** (`research.py`) — a stable sort that sorts contiguous 50,000-row slices,
   yielding between them, then merges the already-sorted runs with `heapq.merge`. Applied at the three
   large-population sort sites the finalize tail reaches: `compute_factor_lab_all`'s per-(factor,horizon)
   sort, `_average_ranks` (rank-IC orders ~1.27M values twice per factor at the default horizon), and
   `_BoundedRankWindow._trim` (drawdown-expectations PASS 1, ~504K keys per trim).
   Measured at the live scale (800K rows, heavy ties): worst GIL hold **0.99s → 0.037s**, and **4% faster**.
   Chunk size chosen from the measured curve: 50K → 0.037s/−4%; 100K → 0.082s/+7%; 200K → 0.201s/+20%.
2. **`_cyclic_gc_paused`** (`research.py`) — pauses CPython's automatic cyclic collector for the duration
   of ONE (factor, horizon) entry and restores the previous state on every exit path. Everything the entry
   allocates in bulk is acyclic, so reference counting reclaims all of it regardless; the collector's work
   there was pure overhead. A/B on the real per-entry body: base worst stall 1.168s / GC 3.5s / 44.6s;
   +chunked sort 0.282s / 4.7s / 46.7s; +`gc.freeze()` 0.283s / 3.9s / 46.2s (**measured ineffective —
   dropped**); +paused collector **0.293s / 0.0s / 42.0s (6% FASTER)**. All variants byte-identical to base.
3. **Bounded release of the spent entry** — the entry's ~1.27M records are dropped in 50,000-row slices
   before the collector is switched back on. Two measured effects drove this: leaving them referenced made
   the first collection after the window a 0.83s gen-0 pass, and then dropping both lists in one statement
   became the largest remaining stall (0.42–0.45s) because freeing 1.27M records is itself one
   uninterruptible C-level sweep.

The first pass's `time.sleep(0)` yield points are **kept**: they cost microseconds and they do help the
ordinary per-item loops; they simply could never reach the three operations above.

### Effect on the same profile (identical inputs, `sum_n_total` 69,608,603 in every run)

| | pre-fix | after (1) + (2) | after (1)+(2)+(3) |
|---|---|---|---|
| `compute_factor_lab_all` wall-clock | 571.94s | 473.17s | **462.49s (−19.1%)** |
| stalls > 0.30s | 197 | 49 | **50** |
| worst single stall | 1.23s | 0.69s | **0.453s** |
| gen-2 GC pauses > 50ms | 154 / 121.37s | 34 / 18.31s | **4 / 0.20s** |
| VmPeak | 1,904,896 kB | 2,119,420 kB | **1,771,404 kB** |

### Why this is byte-identical (argued, then tested)

The slices are contiguous and taken in original order, `sorted` is stable, and `heapq.merge` breaks ties by
iterable index while preserving each iterable's own order — so the concatenation is exactly the stable sort
of the whole population. Every call site additionally has a **unique** key (`(ticker, run_id)` is unique
per observation), so the total order is strict and the sorted permutation is unique regardless of
stability. `_average_ranks`' output is invariant to the order chosen among tied values by construction.
`_BoundedRankWindow`'s retained SET (and therefore its returned slice) cannot change.

Tested, not just argued: the new tests assert equality **by object identity** (`a is b`), so a re-derived
but equal value still fails; and `compute_factor_lab_all` / `_factor_decile_observations` are each run
end-to-end with `_SORT_YIELD_CHUNK = 1` (every element its own chunk) and compared to the unchunked run
with `json.dumps(..., sort_keys=True)`.

### Live/in-app verification — the acceptance drill (TC-1 / TC-3 / TC-5 / TC-11, and J-04 step 2)

Backend launched by `scripts/start-backend.sh` (AG-10 caps live), a real backfill through the product API
(`POST /api/data/jobs`, `kind: backfill`, target **2019-02-19**, chosen at run time from the instance's own
`GET /api/data/availability` as the latest unsnapshotted trading day with ≥ 90 trading days of following
calendar — never a hardcoded literal). Job `ba8c202f15d949f28b5ed11b4fa3e1e0`, **reached terminal status
`ok`** in 1,005.85s: 1 snapshot, 2,290 forward returns, all eight aggregate categories refreshed.

**One methodology change worth flagging to the reviewer:** Addendum 12 polled `/api/health` from a thread
inside a busy Python process, so a "no answer" could not be told apart from the CLIENT thread being
starved. This drill polls from a **dedicated process that does nothing else**, same 5.0s ceiling, and
records the connect/first-byte split. Job status is polled by yet another process.

| | Addendum 11 (pre-fix) | Addendum 12 (first pass) | **Addendum 13 (this pass)** |
|---|---|---|---|
| Job reached terminal status | yes | **no** (ceiling fired mid-phase) | **yes — `ok`** |
| Health polls / HTTP 200 | 653 / 644 | 1,493 / 1,471 | **1,021 / 1,021** |
| **Non-answers (TC-1)** | 9 | 22 | **0** |
| Polls > 2.0s (TC-3) | 0 / 644 | 94 / 1,471 (6.4%) | **16 / 1,021 (1.6%)**, worst 3.818s |
| `factor_lab_all_warm` | 583.76s | 702.99s | **486.62s** |
| **Finalize-tail total (TC-5)** | 1,048.17s | 1,670.95s, incomplete, 470.95s OVER | **955.75s — 244.25s (20.4%) UNDER the 1,200s budget** |
| VmPeak | 3,652.4 MB | 4,405.0 MB | **4,147.4 MB → 4,044.6 MB (49.4%) margin** |

Latency across the whole run: min 0.088 / median 0.231 / p90 0.908 / p99 2.584 / max 3.818 (seconds). The
30s-past-completion tail Addendum 12 could not capture **was** captured (the drill held 40s past terminal
status); no non-answer occurred in it. Boot measured **2.2s** start → first `/api/health` 200 (J-04's ≤5s).

**TC-3 is improved but NOT fully met, and is not claimed as met.** Where the 16 slow polls fall, attributed
by anchor timestamp against each phase's own logged window: 11 in the opening ~90s (1 in the
`backfill`/snapshot-write stage, 2 in `coverage_membership_timeline_refresh`, 3 in `per_date_coverage_warm`,
5 in `market_phase_warm`) and 5 at the hand-over into `drawdown_expectations_warm`.
**Zero in `factor_lab_all_warm`'s entire 486.62s window** — the phase this fix targeted, and the one that
produced 19 of Item U's 22 non-answers and all 9 of Item T's. That attribution is the cleanest evidence
that the fix acted where it was aimed.

**Honest reading of the phase table:** the two drills ran on different single dates, so most per-phase
deltas mix the fix with ordinary date-to-date variation. The one genuinely apples-to-apples row is
`factor_lab_all_warm` — the ingest warms it with `as_of=None` (all-history), so its cost does not depend on
the targeted date — corroborated by the controlled same-DB profile (571.94s → 462.49s). **The 1,200s budget
was not touched or reinterpreted**; the number landed inside it this time.

TC-11/AG-9: the persisted job record reads `"source": null`; `kind="backfill"` is not in `_FETCH_KINDS`, so
the fetch branch (`_resolve_live_provider`) is unreachable — no live network call exists on this path.
TC-10: `git diff --stat` over the five frozen surfaces is EMPTY before and after.

Full numbers, the phase table, and the deferred items are in `reports/perf-budgets.md` Item V / Addendum 13.

---

## Files Changed (fix pass)

- `apps/backend/app/engine/research.py` — `_cooperative_sorted` + `_cyclic_gc_paused` helpers; applied at
  `_average_ranks`, `_BoundedRankWindow._trim`, and `compute_factor_lab_all` (sort + gc window + bounded
  release). `import gc`, `import heapq`, `from contextlib import contextmanager` added.
- `apps/backend/tests/test_research_streaming.py` — 12 new tests (see Tests Run).
- `reports/perf-budgets.md` — new `## Item V` / `### Addendum 13` (append-only; Item U untouched).
- `docs/handoffs/goal-ops-hardening-iter-52-dev.md` — this file.
- `reports/phase-goal-ops-hardening-iter-52-implementation-summary.md` — rewritten for the fix pass.

Unchanged from the initial build and still in the diff: `data_manager.py`, `forward_testing.py`, and the
first pass's tests in `test_data_manager.py` / `test_forward_testing_aggregates_streaming.py` /
`test_start_backend_script.py`.

No schema or migration change. No new config key — the chunk size is an in-code constant by design (TC-10).

---

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest <paths> -q -p no:randomly`

- Targeted + downstream-of-diff files: `test_data_manager.py`, `test_research_streaming.py`,
  `test_research.py`, `test_forward_testing_aggregates_streaming.py`, `test_forward_testing_streaming.py`,
  `test_factor_lab_all.py`, `test_ingest_finalize_fault_injection.py`, `test_start_backend_script.py` —
  **500 passed, 5 skipped (heavy, correctly opt-in-gated behind `TRENDORA_RUN_HEAVY_INGEST_TEST=1`),
  0 failed, in 526.81s.** Every pre-existing byte-identical-to-a-pinned-reference test in these files
  still passes with the chunked sort and the GC window in place — that IS the TC-4 proof.
- The full 30-year backend suite was NOT run (this project's established convention — ~10-11h; targeted
  and downstream-of-diff files only).

**12 new tests this pass**, all in `tests/test_research_streaming.py`:
- `_cooperative_sorted` vs `sorted()` across the chunk boundary (0/1/6/7/8/13/14/15/40 rows, heavy ties on
  the key plus a unique trailing element outside it) — asserted **by object identity**, so a re-derived but
  equal value still fails;
- the keyless path (`_BoundedRankWindow._trim`'s plain tuple sort);
- the yield contract: one `sleep(0)` per chunk plus one before the merge, and **none at all** at or below
  the bound (a small caller pays nothing);
- `compute_factor_lab_all` end-to-end byte-identical with `_SORT_YIELD_CHUNK = 1` vs unchunked
  (`json.dumps(..., sort_keys=True)`) — this covers `_average_ranks`/`_rank_ic` too;
- `_factor_decile_observations` the same way, at deciles 1 / 5 / 10;
- `_cyclic_gc_paused`: suspends inside the window, restores on the normal path, restores on an exception,
  and leaves an ALREADY-disabled collector disabled (it restores, never blindly enables);
- `compute_factor_lab_all` restores the collector after an injected `MemoryError`, with every entry still
  degrading to the honest `unavailable` status (AG-8).

The initial build's 8 yield-firing tests and the TC-6 live fault-injection test are unchanged and still pass.

---

## Known Issues

- **TC-3 is not fully met** — 16 of 1,021 polls exceeded the 2.0s ceiling (worst 3.818s), down from 94 of
  1,471 (worst 4.999s). None of them are in the phase this fix targeted. Recorded as a residual, not
  rounded up to compliance.
- **Two un-fixed contributors, named:** the `backfill`/snapshot-write stage (`_do_backfill`, whose bar-cache
  prefill loads the whole price basis) and `market_phase_warm` together account for 11 of the 16 slow polls.
  Neither was in this iteration's IN-SCOPE list and neither received the treatment above. They are the
  strongest candidates for the next iteration's named change.
- **`GET /api/health` is not a cheap probe.** Every call runs `SELECT max(date)` and
  `COUNT(DISTINCT symbol)` over `daily_prices` plus `compute_readiness` and `compute_preflight` — ~0.14s of
  real DB work at rest, already above the 0.1s steady-state ceiling before any job runs. Untouched here;
  worth its own iteration.
- **This pass makes TWO changes to one subsystem, not one.** The chunked sort and the bounded GC pause are
  parts of a single diagnosed fix ("bound every uninterruptible GIL hold in the finalize tail's longest
  phase"), but a reviewer should treat them as two: each is separately measured, separately tested, and
  separately revertible.
- **`_cyclic_gc_paused` touches global interpreter state** ~~for the seconds it is in effect~~ —
  **CORRECTED by the audit-fix pass (audit B5): for effectively the WHOLE `factor_lab_all_warm` phase**,
  because the window is entered once per (factor, horizon) with only loop bookkeeping between 55
  back-to-back entries. Anything else the process is doing in that window has its own cycle collection
  deferred until a window closes. It restores rather than blindly enabling, and it restores on every exit
  path including exceptions — both covered by tests — but this is a genuine global side effect and is
  called out as such. It also does NOT compose across threads: an overlapping second entrant reads an
  already-disabled collector, so the first window's exit re-enables it under the second — overlap weakens
  the pause, it cannot leak one. Measured under concurrency by the audit-fix pass: VmPeak 4,886.2 MB,
  40.4% margin, no `MemoryError` (Addendum 14).
- **`compute_factor_lab_all` also serves the live `?all=true` request path**, so both changes apply there
  too. That is intended (the same starvation hurts a live request), but it means a user-triggered Factor Lab
  load now also pauses the collector per entry.
- **TC-2 (concurrent drill), TC-7 (Factor Lab browser TTI), TC-8/TC-9/TC-12 (the 8-journey lane)** are not
  developer-lane work and were not run here. The lane runs LAST, per TC-9 — no product code should change
  after it.
- **Single-date sample.** Like every addendum before it, this is one drill on one date. The controlled
  same-DB profile is the stronger evidence for the mechanism; the drill is the stronger evidence for the
  end-to-end outcome.

---

## Suggested Next Phase

1. Give the `backfill`/snapshot-write stage and `market_phase_warm` the same treatment — they now carry all
   the remaining >2s polls, and the mechanism is already diagnosed and tooled.
2. Make `/api/health` cheap: it is the one surface every page polls, and it does whole-basis database work
   on every call. Serving its two `daily_prices` figures from the ingest-maintained aggregates would fit the
   goal's own "compute at ingest, serve from storage" principle exactly.
3. Run the deferred TC-2 concurrent drill against this fix — it is the scenario that produced the worst
   historical evidence (19/892), and it is the one thing this pass's solo result cannot speak for.

---

## Initial build (2026-08-07) — superseded

The initial build added `time.sleep(0)` yield points at every finalize-tail per-item/per-chunk loop
boundary (`_persist_per_date_coverage_snapshots`, `_refresh_ingest_aggregates`'s market-phase and
forward-aggregates loops, `compute_factor_lab_all`, `_combination_observations`,
`_factor_decile_observations` both passes, `_all_factor_observations_by_horizon`,
`compute_forward_aggregates`), the TC-6 live fault-injection test
(`test_ingest_finalize_factor_lab_all_fault_is_honestly_omitted_health_stays_live`, opt-in via
`TRENDORA_RUN_HEAVY_INGEST_TEST=1`, verified live in 838.77s), 8 yield-firing tests, and
`reports/perf-budgets.md` Item U / Addendum 12. Its own live measurement reported TC-1 and TC-5 NOT MET —
honestly, and that report is what made this fix pass possible. All of that work stands; only the
*conclusion* that yield points would close TC-1 was wrong, for the reason profiled above.
