# goal-ops-hardening-iter-31 Audit Report

**Date:** 2026-07-29
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal is achieved: `/research/factor-lab?all=true` no longer raises `MemoryError`, the served
payload is byte-identical to the pre-iteration reference, and the `factor_lab_all_cached` single-flight
guard is proven by a test that genuinely fails at the rejected 45 s value. I re-verified the crash path
end-to-end myself (fresh backend boot, HTTP 200, 117,289-byte payload, 11 factors × 5 horizons, zero
console errors, zero `MemoryError` after boot-banner line 132970) rather than trusting the handoff.

Two IMPORTANT issues were found and fixed during this audit: the AG-8 "disclosure net" could never fire in
the one scenario `config.yaml` promises it covers (the check ran *after* the sweep that would crash), and
the DoD/TC-6 "shipped memory bound proven by a dedicated unit test" was in fact only a range check on a
config integer — no test looked at the returned structure at all. The remaining gaps are honest
limitations, chiefly that the redesign is a measured **2.63× constant-factor reduction (769 MB projected
vs 2,025 MB pre-fix at the live basis), not an asymptotic bound** — all five horizons' pools are still
held simultaneously, so the same crash class returns at roughly 2.5–3× today's data scale.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the AG-8 disclosure warning was unreachable in the exact scenario it documents**
`apps/backend/app/engine/research.py:623-631` (as shipped): the
`research.factor_pool_max_observations` ceiling was checked in a loop placed **after** the run-chunk sweep
completed:

```python
        # ... end of the per-run-chunk sweep ...
    for h, pool in pools.items():
        if len(pool) > pool_cap:
            logger.warning("research.factor_pool_max_observations exceeded: ...")
    return core_records, pools
```

`config.yaml:911-912` states this ceiling exists so "a future data-scale widening logs a WARNING ...
instead of silently repeating this crash at a larger scale", and the function docstring
(`research.py:586-589`) repeats the claim. That claim was false as implemented: a widening large enough to
exhaust memory raises `MemoryError` **inside** the sweep (exactly the frame the live traceback names —
`logs/backend.log:132300-132302`, `pools[h].append`), so control never reaches the post-loop check and the
promised log line is never written. The net could only ever fire on a widening that did *not* crash — i.e.
the case that needs no disclosure. Under AG-8 ("the UI degrades gracefully … honest placeholder, never a
blank application-error page"; honest disclosure of scale limits) a shipped resilience claim that cannot
hold in its own named scenario is a real defect, not a comment nit.

*Fix applied:* the ceiling check now runs **per run-chunk, inside the sweep**, once per horizon
(`warned_horizons` set guards against a per-chunk log storm). Still never raises, never truncates, so the
byte-identity contract is untouched. Cost is `O(len(runs)/run_chunk)` length reads — a handful on the live
basis. Docstring corrected to state where the check runs and why.

*Evidence:* new regression test `test_factor_pool_cap_warning_lands_even_when_the_sweep_dies_part_way`
(`apps/backend/tests/test_factor_lab_all.py`) makes the second run-chunk's slice read raise `MemoryError`
and asserts the warning is already in the log when it propagates. RED-verified by temporarily restoring
the shipped post-loop placement:
`AssertionError: the AG-8 disclosure WARNING never reached the log before the sweep died … assert
'factor_pool_max_observations exceeded' in ''` — then GREEN after restoring the fix.

**B2 — GAP: the return-value "bound" is a 2.63× constant-factor reduction, not a bound**
`apps/backend/app/engine/research.py:596-620`. The redesign (`core_records` + compact per-horizon
3-tuples) still holds **all five horizons' full pools resident simultaneously**; it makes each row cheaper,
it does not remove the `horizons × observations` term. The phase spec's IN SCOPE wording asks for peak
memory that "no longer scales with holding all 5 configured horizons' full pools simultaneously"; the
execution plan (`runs/goal-ops-hardening-iter-31/plan.md:41-46`) explicitly permitted "a more compact
per-observation encoding" as an alternative route, and that is what shipped — plan-conformant, but the
stronger spec sentence is not literally met. I measured it independently (two methods):

| | shipped encoding | pre-fix `{5-key dict}` shape |
|---|---|---|
| per core record | 372 B | 626 B |
| per pool row | 130 B | 411 B |
| **projected at the live basis** (781,417 core / 3,971,375 pool rows) | **769 MB** | **2,025 MB** |

(An independent `tracemalloc` simulation at 100k×5 scale gave 829 MB vs 1,759 MB — same order, same
direction.) So the fix buys ~1.25 GB of headroom on a 6,144 MB `ulimit -v`. Notably **the pre-fix structure
alone (2,025 MB) still fits under the cap** — which means the observed crash was the pools *plus* the rest
of the process (boot warm-up retained state, the SQLAlchemy identity map, the per-`(factor, horizon)`
`obs`/`sorted` lists `compute_factor_lab_all` builds on top, and — per audit B5 — a **concurrent duplicate
compute doubling the pools**). That is why the single-flight guard is load-bearing for the crash fix, not
merely an efficiency win. Carry-forward: at ~2.5–3× today's basis this crash class returns. Documented, not
fixed — out of this iteration's scope.

**B3 — OBSERVATION: the single-flight guard is in-process only**
`research.py:3055-3072`. `_FACTOR_LAB_ALL_LOCK` / `_FACTOR_LAB_ALL_INFLIGHT` are module-level
`threading` primitives. Today that covers every production caller: `scripts/start-backend.sh:95` execs
`uvicorn main:app` with **no `--workers`** (verified on the running process), and the only two callers,
`app/api/research.py:126` and `app/mcp/tools.py:344`, both go through `factor_lab_all_cached` in that one
process. Adding `--workers > 1`, or any out-of-process caller, would silently halve the guard's
effectiveness and re-open B5. The spec asked for an in-process guard, so this is conformant — worth
writing down because the failure would be silent.

**B4 — OBSERVATION: the 900 s bounded wait occupies a request thread**
`research.py:3070-3072`, `research.py:3113`. A waiter blocks an anyio worker thread for up to 900 s. A
genuinely wedged owner could therefore hold the whole default threadpool for 15 minutes. This is not a
regression — pre-fix those same threads were each running their own multi-minute compute *and* allocating
their own copy of the pools — and the owner always sets the event in its `finally`, so a healthy request
never approaches the ceiling. Recorded against J-07's availability lens.

### Frontend Findings

None. `git diff --stat -- apps/frontend` against `HEAD` is empty for this iteration (independently
confirmed; the working tree's `evidence.ts` / `evidence.test.ts` / `app/evidence/page.tsx` deltas belong to
iter-29). The Factor Lab page code is a 6-line route delegating to the unchanged `FactorLabPage`
(`apps/frontend/app/research/factor-lab/page.tsx`).

**F1 — GAP: browser-QA claimed "zero console errors" while its own evidence shows a "1 error" indicator**
`reports/qa/goal-ops-hardening-iter-31-evidence/TC-1-factor-lab-all-factors.png` carries a red Next.js
dev-overlay pill reading **"1 error"** in the bottom-left; the UT-FL-01 row in
`reports/phase-goal-ops-hardening-iter-31-ui-test-results.md` states "console capture showed only a
React-DevTools info line, zero errors" and never mentions it. DoD item 1 requires zero console errors, so
this contradiction had to be resolved rather than accepted. I could **not** reproduce it: two independent
Playwright sessions against a freshly booted backend + frontend (direct navigation, and client-side
navigation via the Research nav) recorded **zero** `error` / `pageerror` / `requestfailed` / HTTP≥400
events — only the React-DevTools `info` line and two `[Fast Refresh]` logs — and no overlay pill in my own
capture. The page rendered `Factors: 11` with real N values (771129 / 765882 / 769840), no "Backend
unavailable" card. Most likely the indicator was accrued earlier in the QA agent's long multi-page session
(the Next dev indicator persists its count across client-side navigations). Product state is fine; the
report should have accounted for a visible error badge in its own evidence.

### Test Findings

**T1 — IMPORTANT (fixed): TC-6 / the DoD "shipped memory bound proven by a dedicated unit test" was not
implemented as specified**
The shipped `test_shipped_factor_pool_max_observations_actually_covers_the_live_basis`
(`apps/backend/tests/test_factor_lab_all.py:622-637`) asserts only
`804_372 <= cfg.research.factor_pool_max_observations <= 16_087_440` — a range check on a **config
integer**. It never calls `_all_factor_observations_by_horizon`, never looks at the returned structure, and
would stay green after a complete revert of the memory redesign. The spec's TC-6 requires a test that
"observes the peak resident size of the returned pools structure and asserts it is bounded"; the DoD
requires "the shipped memory bound is proven against the REAL live run/observation count … by a dedicated
unit test". The reviewer recorded `definition_of_done: complete` and QA marked TC-06 PASS citing this test
plus the handoff's live figures — but no test measured memory at all, leaving the whole redesign covered
only by a one-off manual measurement.

*Fix applied:* added
`test_returned_pool_structure_projected_to_the_live_basis_stays_under_the_memory_cap`. It deep-sizes the
**actual returned** `(core_records, pools)` structure (identity-deduped `sys.getsizeof` walk — deterministic,
no clock/GC/tracemalloc sampling), derives per-core-record and per-pool-row costs, projects them onto the
real measured live basis (781,417 core records / 3,971,375 pool rows), and asserts (a) the projection fits
inside 35 % of `server.memory_cap_mb`, and (b) it is at least 1.5× smaller than the pre-fix shape rebuilt
from the same data. Conservative by construction: the fixture charges a distinct ticker string to nearly
every core record where the live basis shares ~591 across 781,417, so the projected per-core cost
overstates.

*Evidence:* `3 passed` on the targeted run; teeth demonstrated by feeding the pre-fix shape through the
same arithmetic — `RED: pre-fix*1.5 <= pre-fix ? False`, i.e. a revert (or re-inlining identity into the
per-horizon rows) fails assertion (b). Note assertion (a) alone does **not** discriminate (the pre-fix
2,025 MB also fits under 35 %); (b) is what carries the regression teeth, and B2 above records why.

**T2 — GAP: the QA report asserted PASS with two of its own blocking test cases unverified**
`reports/qa/goal-ops-hardening-iter-31-qa.md:187-204` marks TC-8 (required-still-passing journeys — a
blocking DoD item) and TC-9 as "PENDING / Deferred" and substitutes an expectation: *"Expected: All 6
journeys PASS … no regression expected from this backend-only memory fix."* An expectation is not evidence.
The outcome is fine — the replay lane ran afterwards and produced real artifacts, which I verified and cite
below — but the PASS verdict was written before that evidence existed.

**T3 — GAP: J-03 / J-04 / J-07 screenshots are byte-identical again (11th+ recurrence)**
`md5sum` over `reports/qa/goal-ops-hardening-iter-31-evidence/`: `J-03-verify.png`, `J-04-verify.png` and
`J-07-verify.png` all hash to `eff8f9adf4a501d7c5babb6b6860db12`. The phase spec's NOTES explicitly
instructed browser-qa-agent to "verify each required journey's screenshot is a genuinely fresh, distinct
capture this run"; that verification did not happen, so three journeys again have no independent visual
evidence. Their replay rows still asserted per-journey DOM expectations, so the PASS is not
screenshot-only. Framework issue, not product code — carried, as the spec already anticipates.

**D1 — OBSERVATION: the dev handoff's memory table mixes two different metrics**
`docs/handoffs/goal-ops-hardening-iter-31-dev.md:147-153` reports "Pre-request `VmHWM`" against
"Post-request `VmPeak`" and records no pre-request `VmPeak`, so the request's own virtual-memory delta —
the dimension `ulimit -v` actually enforces — cannot be derived from the table. The absolute figures
(2,518,784 kB peak vs a 6,144 MB cap) still support the conclusion, and the margin is stated plainly rather
than rounded, which is what the DoD asked for.

---

## 3. Domain Assessment

**Byte-identity (the load-bearing contract) is genuinely proven, by an oracle the developer did not touch.**
`test_all_horizons_per_factor_is_byte_identical_to_compute_factor_lab` compares the restructured
all-factors output against `compute_factor_lab` — the **single-factor path this iteration froze** — for
every catalog factor × every configured horizon × every decile, parametrized over all-history and an
`as_of` window, with non-vacuity guards (`saw_populated`, `saw_zero_n`). That test is unmodified in the
diff and passes. It is a much stronger proof than
`test_shared_pools_chunked_equal_the_pinned_unchunked_reference`, which now compares through two test-only
adapters written by the same agent as the fix (`_materialize_compact_pools` / `_reference_as_positional`)
and would be weak evidence on its own. Live confirmation: the served payload is byte-identical across the
developer's two cold-MISS restarts and across my own audit-fix restart (117,289 bytes each time).

**The positional-index redesign is safe.** `compute_factor_lab_all` now indexes factor values by position
(`factor_index[factor.key]`) into a tuple built from `parsed_by_key.values()`. That is only sound if the
factor catalog has no duplicate keys — and it doesn't silently: `FactorLabCfg._validate`
(`apps/backend/app/config.py:1231-1234`) raises at boot on duplicate keys. No latent `IndexError`.

**The single-flight guard mirrors the established idiom correctly, and its key test has real teeth.** The
lock/event/`finally`-release/independent-fallback structure matches
`forward_testing.forward_aggregates_ingest_cached:1223-1284` line for line in intent. The review round's
CRITICAL — a 45 s wait against a ~300 s compute — was a genuine catch, and the fix is not just a bigger
number: `_FACTOR_LAB_ALL_WAIT_TIMEOUT_S` is derived from two named integers, locked by a
shipped-value-vs-measurement test, and backed by
`test_factor_lab_all_single_flight_holds_across_a_compute_past_the_pre_fix_timeout`, which stretches the
owner's compute to 48 s of **real** wall time past the rejected ceiling and asserts exactly one compute.
The waiter's post-wait re-read through its own `Session` works in practice — that test would report two
computes if it didn't (it reports one), and the fixture is file-backed SQLite, matching production
semantics rather than an in-memory shortcut.

**Byte-frozen scope was respected.** `git diff` produces no hunk touching `_factor_observations`,
`_runs_with_fr`, `_fr_slice_map`, `compute_factor_lab`, or `forward_testing.py`. The four hunks in
`research.py` are confined to `_all_factor_observations_by_horizon`, `compute_factor_lab_all`'s consumption
loop, the new module constants, and `factor_lab_all_cached`. No scope creep into the three carried
deferrals (`stock_obs`, `warmup.py:194`, `prices.py:141`).

**AG-8 finding (a) is resolved, with the honest caveat in B2.** The crash is real and recent — the last
`MemoryError` with a `research.py` frame in `logs/backend.log` is line 132302 (`research.py:583`,
`pools[h].append`), from a boot preceding `2026-07-29T02:21:49Z`, i.e. pre-fix and on the current basis.
Zero `MemoryError` lines follow any boot banner after it, including my own (132970). No anti-goal
violation: the payload's values are unchanged, the "Not yet proven" evidence badges still render for every
unbacked cell (AG-1), the survivorship/descriptive caveats are intact (AG-2/AG-4), no ingest or network
path was touched (AG-9), and every command I ran used the host-guard CPU/BLAS caps and the project launch
scripts (AG-10).

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/research.py` | Moved the `factor_pool_max_observations` AG-8 disclosure check from after the sweep to **inside** the run-chunk loop (once per horizon, `warned_horizons` guard), so the warning actually lands before a memory-exhausting build dies; docstring corrected to say where it runs and why. Never raises, never truncates — byte-identity untouched. |
| 2 | Important | `apps/backend/tests/test_factor_lab_all.py` | Added `test_returned_pool_structure_projected_to_the_live_basis_stays_under_the_memory_cap` (TC-6 as specified: deep-sizes the **returned** structure, projects onto the real live basis, asserts it fits 35 % of `server.memory_cap_mb` **and** is ≥1.5× smaller than the pre-fix shape) and `test_factor_pool_cap_warning_lands_even_when_the_sweep_dies_part_way` (regression guard for fix 1). Added `import sys`. |

**Verification of these fixes (commands and results):**

- `pytest tests/test_factor_lab_all.py tests/test_research_streaming.py tests/test_config.py -q` →
  **138 passed in 63.97s** (host-guard `taskset -c 0-3,8-11` + BLAS caps, foreground, isolated `TMPDIR`),
  including the ~48 s slow single-flight test and `test_shipped_factor_join_run_chunk_actually_binds_on_the_live_basis`.
- `pytest tests/test_no_magic_numbers.py tests/test_research.py tests/test_evidence.py -q` →
  **112 passed, 1 failed**; the single failure is the pre-existing, spec-documented
  `test_engine_calc_code_has_no_magic_numbers` red on `indicators.py` (`0.5`, `0.95`) and
  `forward_testing.py` (`45.0`, `0.5`, `0.9`). `research.py` does **not** appear — my fix introduced no
  literal.
- RED check for fix 1: temporarily restored the shipped post-loop placement → the new test fails with
  `assert 'factor_pool_max_observations exceeded' in ''`; restored → passes.
- RED check for fix 2: feeding the pre-fix shape through the same projection arithmetic →
  `pre-fix*1.5 <= pre-fix ? False` (assertion (b) discriminates a revert).
- Live re-verification after the fix: restarted via `scripts/start-backend.sh` (host-guard caps applied),
  `GET /api/research/factor-lab?all=true` → **HTTP 200, 117,289 bytes, byte-identical** to the
  pre-audit-fix response, 11 factors, horizons `[1, 5, 10, 20, 60]`; `MemoryError` lines after this run's
  boot banner (line **132970**): **0**.
- Live browser re-verification (Playwright, fresh session, direct + client-side navigation):
  zero console `error`/`pageerror`/`requestfailed`/HTTP≥400 events; `Factors: 11`; real N values.

No dev-handoff claim was invalidated by these fixes (the handoff describes the ceiling as "logs a WARNING
and keeps going", which remains true and is now actually reachable), so it was left unedited.

**DoD verification ledger** (full trace where risk/contradiction warranted it; citation where a reviewer
PASS plus an executed test/replay row already covered a mechanical item):

| DoD item | Status | Evidence |
|---|---|---|
| 1. Real-browser `?all=true`, HTTP 200, real values, zero console errors, fresh screenshot | met (with F1) | `ui-test-results.md` UT-FL-01 + `TC-1-factor-lab-all-factors.png` (md5 `9002cdee…`, unique); independently re-verified by me |
| 2. Zero `MemoryError` (`research.py` frame) since this run's boot banner, line cited | met | QA cites 132545, browser-QA 132546; last such line in the whole log is 132302 (pre-fix); my own run: banner 132970, count 0 |
| 3. Single-flight proven live or by test | met | TC-3 / TC-4 / the 48 s past-the-old-ceiling test — all pass in my own run |
| 4. Byte-identical `(factor, horizon, decile)` output | met | unmodified `test_all_horizons_per_factor_is_byte_identical_to_compute_factor_lab` (all-history + `as_of`); live payload byte-identical across restarts |
| 5. Shipped memory bound proven vs the real live count by a dedicated unit test | **was not met — fixed** | see T1 |
| 6. J-01/J-03/J-04/J-05/J-08/J-09 remain green | met | `reports/phase-goal-ops-hardening-iter-31-regression-replay-results.md` — 6/6 PASS, 0 FAIL (supersedes the QA report's PENDING rows; see T2) |
| 7. Frozen `_factor_observations`/`_runs_with_fr`/`_fr_slice_map` tests pass unmodified | met | zero diff hunks on those functions; `test_research_streaming.py` 41/41 in my run |
| 8. No anti-goal violation; AG-8 (a) resolved or honestly recorded | met, with B2 recorded | see Domain Assessment + B2 |
| 9. Unit tests pass, no regressions | met | 138 + 112 passed; only the pre-existing documented `test_no_magic_numbers` red |
| 10. Dev handoff states measured peak and margin plainly | met (D1 nit) | handoff "Live verification" section |
| TC-9 ride-along artifact (non-blocking) | closed | `reports/phase-goal-ops-hardening-iter-31-j06-ridealong-replay-results.md` — UT-J-06 PASS |

---

## 5. Recommended Next Step

Proceed to the next iteration. The oldest still-open critical AG-8 finding is closed with live proof, and
the audit's two IMPORTANT fixes are verified by tests that fail on a revert.

Carry into the session's blocker list, in priority order:

1. **B2 — the Factor-Lab-all return value is bounded by a 2.63× constant factor, not asymptotically.**
   ~769 MB resident at today's basis; the same crash class returns at ~2.5–3× the data scale. The natural
   follow-on (already named out-of-scope here) is to restructure `compute_factor_lab_all`'s consumption so
   it does not require every horizon's pool resident at once — the second route the plan offered. Now that
   the disclosure warning actually fires (B1 fix), the next scale jump announces itself in
   `logs/backend.log` first.
2. **T2/T3 — QA evidence discipline.** A PASS verdict that substitutes "Expected: all 6 journeys PASS" for
   a replay artifact, and a third consecutive-iteration screenshot md5 collision across J-03/J-04/J-07,
   are both recurrences the spec had already flagged. Worth an explicit gate rather than another NOTES
   entry.
3. Unchanged carries: `stock_obs` (`forward_testing.py:988`), `warmup.py:194`, `prices.py:141`;
   `merge_ui_test_results.py`'s `_ROW_RE` framework bug; the owner-owned `GET /api/health` ≤0.1 s budget
   amendment; `test_no_magic_numbers.py`'s red on `indicators.py` / `forward_testing.py`.
