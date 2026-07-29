# Goal Iteration 30 Audit Report

**Date:** 2026-07-29
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's own target — bounding `compute_forward_aggregates`'s join accumulator byte-identically
and proving the bound binds on the real basis — is genuinely achieved and independently re-verified here
(measured live: peak traced memory 1103.1 MB → 922.3 MB, peak RSS 2492.3 MB → 1953.0 MB at horizon 20 on
the 1,858-run / 771,129-observation live basis, with identical output). J-06's last mechanical gap
(TC-07, the `J-06.json` replay) was left **unexecuted** by the pipeline; I executed it during this audit
and it **PASSES** (rc=0, 1/1, zero FAIL rows), so J-06's DoD is now met with evidence. Two real gaps
remain: `stock_obs` — the container at the exact frame that raised the live `MemoryError` this iteration
was dispatched to fix — is still unbounded, and the canonical merged browser-QA artifact reports
"PASS 6/6" while the authoritative browser-QA report says FAIL 3/5. I also found that the escalation
narrative in the browser-QA and UX-regression reports ("the MemoryError terminated the entire backend
process", "materially worse than iter-29") is **contradicted by the log** and should not drive the next
iteration's targeting decision on its own.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap): the fix bounds the accumulator's *neighbours*, not the allocation that actually failed.**
`apps/backend/app/engine/forward_testing.py:988` (`stock_obs.append({`).
The spec's IN SCOPE names **three** containers to bound: `ret_by_run_symbol`, `mdd_by_run_symbol` and
`stock_obs`. Only the first two are bounded (merged into the chunk-scoped `_forward_agg_slice_map`).
`stock_obs` is still assembled to full horizon-partition size. This matters more than the disclosure
implies: the live `MemoryError` frame that motivated this whole iteration —
`logs/backend.log:130046-130048`, `forward_testing.py, line 965, in compute_forward_aggregates` — is,
in the *pre-change* file (`git show HEAD:.../forward_testing.py`, line 965), literally
`stock_obs.append({`. The failing allocation site is the one container left unbounded; the fix freed
headroom around it rather than removing the unbounded growth.

Quantified by direct measurement during this audit (live DB, horizon 20, host-guard-equivalent caps
`ulimit -v 6144M`, `MALLOC_ARENA_MAX=2`, `taskset -c 0-3,8-11`, BLAS=4):

| run-chunk width | chunks | tracemalloc peak | peak RSS | output |
|---|---|---|---|---|
| 100 (shipped) | 19 | **922.3 MB** | **1953.0 MB** | `overall_n=771129`, `n_runs=1858` |
| 100000 (≡ pre-iter-30) | 1 | 1103.1 MB | 2492.3 MB | `overall_n=771129`, `n_runs=1858` |

→ a real but partial win: **−16.4 % traced peak / −21.6 % peak RSS**, identical output. The residual
922 MB is dominated by `stock_obs` and still scales linearly with the horizon-partition, so J-07's
acceptance clause ("chunked into bounded accumulators") is satisfied *empirically* (TC-01's live warm
completed) but not *structurally*.

**Not fixed, deliberately.** Bounding `stock_obs` requires changing `_attribution_slices`'s frozen,
test-pinned `(stock_obs, cfg)` signature (`test_attribution_is_pure_over_passed_observations_no_new_query`
asserts it by `inspect.signature`, and several other tests call it directly with hand-built lists). That
is a multi-test re-pin — well beyond surgical audit scope, and bundling it here would violate the
session's own rule 5. Honestly disclosed by the developer (Known Issues), the reviewer (MINOR/spec) and
QA — not a silent shortcut.

**B2 — verified correct (no finding): the `bm_returns` substitution is byte-identical.**
I did not take the handoff's word for it. `_control_groups`
(`apps/backend/app/engine/forward_testing.py:649-704`) reads the passed map at exactly three places —
`(run_id, etf_by_sector.get(sector))`, `(r, bm["spy"])`, `(r, bm["qqq"])`. `_sector_etf_by_name`
(line 151) inverts `cfg.etfs.sector` (`{ticker: name}`), so every value it can return is a key of
`cfg.etfs.sector`, i.e. a member of `benchmark_symbols(cfg)["sector_etfs"]` (line 104). The new
`benchmark_symbol_set` (line 979) is exactly `{spy, qqq, *sector_etfs}` — a superset of every key the
consumer can look up. Passing `bm_returns` instead of the full dict is therefore provably lossless.

**B3 — verified correct (no finding): `stock_obs` ordering is preserved on the live basis.**
The pre-change scan was one `WHERE run_id IN (all runs) ORDER BY ScannerResult.id`; it is now
per-chunk `ORDER BY ScannerResult.id` concatenated in ascending-run-id order. These agree only if each
run's `scanner_results` id-block is disjoint and ascending in run_id. Verified directly against the live
DB: **1,878 run blocks, 0 non-monotonic** (`select run_id, min(id), max(id) ... group by run_id`). Order
matters for exactly one output cell (`_per_stock_attribution`'s
`sector_by_ticker.setdefault` first-occurrence pick, line 731); every other consumer uses
`statistics.mean/median/stdev` (exact-`Fraction` accumulation, order-independent) or an explicitly
sorted tie-break. No divergence.

**B4 — OBSERVATION: the NA gate changed from value-is-None to key-presence.**
`apps/backend/app/engine/forward_testing.py:1002-1005`. Old: `realized = ret_by_run_symbol.get(...)`,
`if realized is None: continue`. New: `fr = slice_map.get(...)`, `if fr is None: continue`. These differ
if `realized_return` could ever be NULL — a stored `None` would now flow into `stock_obs["return"]`
instead of being skipped. Safe today because `ForwardReturn.realized_return: float`
(`apps/backend/app/models.py:397`) is non-Optional / NOT NULL, and the model docstring pins the
row-exists-iff-computed invariant. Worth one inline note; not a defect.

**B5 — OBSERVATION (out of scope, useful for scoping the next iteration): the Factor-Lab compute path has no single-flight guard.**
`factor_lab_all_cached` (`apps/backend/app/engine/research.py:2995-3040`) is a plain check-then-compute
against the DB-backed `event_study_cache` — unlike `forward_aggregates_ingest_cached`, which carries
iter-15's per-key single-flight lock. New evidence found during this audit points at that gap as the
actual TC-05 trigger: the `__all_factors__` cache row for the post-backfill dataset version
(`r1879-f3971375-allh-mdd-v1`) was written successfully at **02:10:54** — i.e. one compute of that exact
identity *succeeded* — while a concurrent duplicate compute of the same identity was still running and
blew the 6 GB cap minutes later. Whoever scopes the `_all_factor_observations_by_horizon` fix should
consider the de-dup guard alongside the accumulator bound.

### Test / QA-process Findings

**T1 — IMPORTANT (fixed by execution): TC-07 (`J-06.json` deterministic replay) was never run.**
It is an explicit DoD item ("`J-06.json` runs through the deterministic replay lane with a PASS row and
zero FAIL rows") and browser-QA correctly marked it **SKIP**, blocked by the backend being down. With
that item unexecuted, J-06's DoD was literally unmet. I executed it during this audit against freshly
launch-script-started services:

```
python3 scripts/automation/lib/demo_runner.py --mode verify \
  --scripts-dir runs/goal-session-ops-hardening/journey-scripts --journeys J-06 \
  --base-url http://localhost:3255 --phase-id goal-ops-hardening-iter-30-audit ...
→ [demo_runner] verify: 1 journey(s), 0 failed (verdict: PASS)   RC=0
```
Results artifact: `**Browser QA Verdict:** PASS`, `1/1 journeys passed (0 skipped)`, row
`UT-J-06 … PASS`. **TC-07 PASSES**; J-06's DoD is now met on evidence, not on assumption.

**T2 — CRITICAL (gap, reporting integrity): a P1 FAIL is laundered into "PASS 6/6" in the canonical merged artifact.**
`reports/phase-goal-ops-hardening-iter-30-ui-test-results.md` — the file the goal-evaluator reads —
states `**Browser QA Verdict:** PASS` / `6/6 journeys passed (0 skipped)`. The authoritative browser-QA
report, `reports/phase-goal-ops-hardening-iter-30-ui-test-results.llm.md`, states
`**Browser QA Verdict:** FAIL` / `3/5 tests passed (1 failed, 1 skipped)`. Root cause proven, not
inferred, by running the merger's own parser:

```
merge_ui_test_results.parse_rows(llm_file)    → 0 rows      (file_top_verdict → "FAIL")
merge_ui_test_results.parse_rows(replay_file) → 6 rows      (file_top_verdict → "PASS")
```

`_ROW_RE` (`scripts/automation/lib/merge_ui_test_results.py:37`) matches only `UT-`-prefixed test IDs.
The browser-qa-agent emitted `TC-01 … TC-07` rows — a deviation from the documented convention
(`templates/ui-test-plan.md:12`: "Test IDs use UT-XX prefix to distinguish from functional test plan
TC-XX IDs") — so **every one of its rows was silently dropped**, and `compute_overall`'s
file-headline-verdict fallback (same file, ~line 95) never fired because the *replay* rows parsed. The
FAIL headline was discarded. The script's own docstring warns about exactly this class ("that once
laundered a raw FAIL into a merged PASS at the achievement gate; ops-hardening iters 9/12") — it has
recurred by a different route.

**Not fixed, deliberately.** The defect lives in framework/pipeline code
(`scripts/automation/lib/merge_ui_test_results.py`, byte-identical to the vendored
`incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py`), not in this phase's diff, and
editing it touches the resync invariant in `.claude/maintenance-protocol.md` §3 — a framework
maintenance change, not an audit fix. The one-line remedy, for whoever owns it: widen
`_ROW_RE` to `r"^\|\s*((?:UT|TC)-[^|]+?)\s*\|(.*)\|\s*$"` (both copies, plus a `self-test` case), and/or
make `compute_overall` fold in any input file's headline FAIL whose rows all failed to parse. The
browser-qa-agent should also be held to the `UT-XX` convention.

**T3 — IMPORTANT: browser-QA's TC-05 causal claim is not supported by the log.**
The report asserts the `MemoryError` "**terminated the entire backend process**". The log says
otherwise. In `logs/backend.log`:

- **132229** `INFO: Shutting down` ← uvicorn's *signal-initiated* shutdown path
- **132230** `Waiting for connections to close.`  · **132231** `Waiting for background tasks to complete.`
- **132232-132302** `ERROR: Exception in ASGI application` … `research.py:583` … `MemoryError`
- **132303-132305** `Waiting for application shutdown.` / `Application shutdown complete.` / `Finished server process [3667601]`

The shutdown was already in progress **three lines before** the traceback began. The control case is in
the same log: the *identical* `factor-lab` MemoryError at lines **127815** and **129033** returned a
clean `500 Internal Server Error` with the process surviving and serving subsequent requests — exactly
what iter-29's audit recorded. A MemoryError in a request worker does not stop uvicorn here. The process
death was externally initiated; the MemoryError surfaced during the drain. (Note the crashing request has
no `500` access-log line, unlike 127815/129033 — consistent with the connection being drained.)

**T4 — IMPORTANT: the UX-regression escalation rests on T3 and is further contradicted by the log.**
`reports/phase-goal-ops-hardening-iter-30-ux-regression.md` records **UX-REGRESSION-FAIL** on the
narrative "survivable 500 → full process death", "materially worse than iter-29", "every page and journey
… unreachable", and recommends retargeting the next iteration on that severity trend. Beyond T3, the same
log shows **six** subsequent `GET /api/research/factor-lab?all=true` requests all returning **200 OK**
(lines 132315, 132330, 132358, 132362, 132374, 132390) across the two following boots. I reproduced it
live during this audit: HTTP **200**, 117,289-byte payload, 11 factors × 5 horizons × 10 populated
deciles with real numerics (`rank_ic.value = -0.00327853…`, `n_total = 771129`, `low_sample: false`),
backend process alive afterwards, `/api/health` 200.

**Honest caveat on my own evidence:** that 200 was a DB cache **HIT** (`event_study_cache`,
`subject='__all_factors__'`), so it does **not** re-exercise the compute path. What it does establish is
that (a) the page is not unconditionally broken, (b) the compute path *did* succeed on this dataset
version at 02:10:54, and (c) the "whole product down" framing overstates a memory-pressure-and-concurrency
failure. TC-05's own FAIL is legitimate and the underlying fragility of
`_all_factor_observations_by_horizon` (unbounded `pools[h]`, ~4-minute compute, no de-dup guard) is real
and unresolved — it is just not the escalation the two reports describe.

**T5 — verified correct (no finding): the byte-identity oracle is genuine and was not weakened.**
iter-29's lesson (a golden/reference can be silently overwritten to hide a regression) applies directly
here. `git diff` on `apps/backend/tests/test_forward_testing_aggregates_streaming.py` is **append-only**
past line 318 — `_reference_compute_forward_aggregates` (lines 62-176) is untouched, and it is a real
independent pre-chunk implementation (whole-partition `.all()` reads, its own accumulator construction,
and it passes the **full** `ret_by_run_symbol` to `_control_groups` where production now passes
`bm_returns`). So the equality assertion genuinely proves the substitution. Coverage is what the DoD
requires: `HORIZONS = (1, 5, 10, 20, 60)` (all 5 configured) × `as_of ∈ {None, 2024-07-15}` × run-chunk
widths {1, 2, 4, 100}, deep-equal on the whole payload. Re-run independently by me:
`pytest tests/test_forward_testing_aggregates_streaming.py -q` → **46 passed in 6.84s**, zero skips —
including `test_shipped_forward_agg_run_chunk_binds_against_the_real_committed_seed`, which really did
execute against the committed DB.

**T6 — verified correct (no finding): the shipped knob binds on the real basis (iter-29's lesson held).**
Independently measured on the live DB: `SELECT COUNT(DISTINCT run_id) FROM forward_returns WHERE
horizon=20` = **1,858** → 19 chunks at the shipped `walk_forward.forward_agg_run_chunk: 100`. The knob is
its own RUN-count key on `WalkForwardCfg` (`apps/backend/app/config.py:768`) with a `>= 1` boot validator
(line 787) — it does not reuse `research.read_batch_size` (rows) or `research.factor_join_run_chunk`
(another function's run knob). This is not iter-29's inert-knob failure repeating.

**T7 — verified correct (no finding): TC-01/TC-04's "zero MemoryError" claim holds under re-count.**
Re-counted the cited window myself rather than trusting the report (TC-9's whole point):
`logs/backend.log` lines **131633** (boot banner `Application startup complete.`, preceded by the
host-guard banner at 131628-131630: `memory_cap_mb=6144`, `cpu_list=0-3,8-11`) through **132226**
(job completion) → `grep -c MemoryError` = **0**, `Traceback` = **0**,
`forward_testing.py|compute_forward_aggregates|stock_obs|ret_by_run_symbol` = **0**. The claim is exact.

**T8 — verified correct (no finding): TC-06 / `reports/perf-budgets.md`.**
The Iteration-30 section (lines 3946-4022) carries the boot-to-health reading (1.354s vs ≤5s, PASS), all
11 J-06 pages and 15 on-load endpoints each scored, and honestly labels `GET /api/health` at 0.127787s
vs its ≤0.1s budget as **WARN** with the prior-iteration history rather than rounding it to a PASS. No
budget was quietly loosened.

### Frontend Findings

None. Zero frontend files in the diff; `Frontend Present: no` is accurate and consistent across
`plan.md`, the ui-surface-map and the user-visible-changes report. The one frontend behaviour observed —
Factor Lab rendering "Backend unavailable … No figures are shown rather than fabricated values" instead
of a blank crash page — is AG-8's degradation clause working as specified.

---

## 3. Domain Assessment

The domain logic is correct and the correctness argument is airtight in the places that matter.

`compute_forward_aggregates` remains the single canonical producer at the same signature, called from the
same three sites; `_group_means`, `_group_mdd`, `_control_groups`, `_attribution_slices` and the
VCP/pullback/breakout groupings are untouched. The rewrite changes only *how* the containers they consume
are assembled, and the three ways that could have broken byte-identity are all closed: the benchmark-map
substitution is provably lossless (B2), the `stock_obs` ordering is preserved on the real data (B3), and
the aggregation math is order-independent by construction. `runs_with_fr`'s `SELECT DISTINCT` discovery
returns the same set the old full iteration collected, and the `as_of` filter is correctly applied once
at discovery (so the per-chunk `_forward_agg_slice_map`, which carries no `as_of` clause, is still
correctly scoped by membership). No-lookahead is preserved.

Where the domain work falls short is scope, not correctness: this is a **partial** memory bound
(B1). The two dominant join dicts are genuinely gone; the largest single container — and the exact one
whose `append` raised the production `MemoryError` — remains. The measured 16-22 % peak reduction was
enough to let the real full-basis warm complete (TC-01, live, independently re-counted), which is a real
operational win, but it is headroom, not a structural fix. The evaluator should score J-07 on that
distinction rather than on "zero MemoryError observed once".

---

## 4. Fixes Applied During This Audit

**No source files were modified.** `git status` after this audit shows exactly the five files the
developer changed (`forward_testing.py`, `config.py`, `config.yaml`, the test file, `perf-budgets.md`)
plus `runs/` bookkeeping — nothing from me.

| # | Severity | Action | Evidence |
|---|----------|--------|----------|
| 1 | Important | **Executed the unrun DoD item TC-07** (`J-06.json` deterministic replay) rather than leaving it SKIPped | `demo_runner.py --mode verify --journeys J-06` → rc=0, `1/1 journeys passed (0 skipped)`, `UT-J-06 … PASS` |
| 2 | Important | **Quantified the actual memory bound** (nobody had measured whether it binds beyond ">1 chunk") | shipped width 100: traced peak 922.3 MB / RSS 1953.0 MB vs unchunked: 1103.1 MB / 2492.3 MB, identical output, live DB, horizon 20 |
| 3 | Important | **Disproved the escalation narrative** in the browser-QA and UX-regression reports | `logs/backend.log:132229` precedes `:132232-132302`; control cases at `:127815`, `:129033` (500, process survived); six later factor-lab `200 OK` at `:132315/132330/132358/132362/132374/132390`; live re-check HTTP 200 with populated numerics |

Two CRITICAL/IMPORTANT findings were deliberately **not** fixed, with reasons stated at the finding:
T2 (merge-script laundering — framework code outside this phase's diff, governed by the resync
invariant; one-line remedy specified) and B1 (`stock_obs` — requires re-pinning a frozen test-asserted
signature; its own iteration under rule 5).

**Environment left running:** backend :8255 and frontend :3255 are up and healthy (both HTTP 200),
started via `scripts/start-backend.sh` / `scripts/start-frontend.sh` with host-guard caps applied
(`memory_cap_mb=6144`, `cpu_list=0-3,8-11`, `blas_threads=4`) — the next pipeline step will not have to
re-launch them.

---

## 5. Recommended Next Step

**Proceed to the goal-evaluator**, with three corrections carried forward:

1. **J-06 is closed.** TC-07 passed under this audit (§4 #1); the only reason it was open is that the
   backend was down when browser-QA reached it. Do not score J-06 `partial` for an unrun replay.
2. **Score J-07 on the measured figures, not the binary.** The targeted AG-8 finding is resolved
   operationally (live warm completed, zero MemoryError, health 200 on 273/273 polls), and the bound is
   real (−16.4 %/−21.6 % peak, byte-identical). But `stock_obs` — the frame that actually failed — is
   still unbounded, and the residual 922 MB still scales with the horizon-partition. `pass` on the
   acceptance clause is defensible; a note that the structural half is outstanding is mandatory.
3. **Do not let the UX-regression FAIL retarget the next iteration on its stated severity.** The
   "worse than iter-29 / whole process death" trend is not supported by the log (T3, T4). The *real*
   next target is still `research.py`'s `_all_factor_observations_by_horizon` — but for the reason
   iter-29's audit already gave (unbounded `pools[h]` on the deep basis), now with two extra facts to
   scope it: the compute succeeds when it runs alone (`event_study_cache` row written 02:10:54) and the
   path has **no single-flight guard** (B5), so a concurrent duplicate compute is the likely trigger.
   Bound the accumulator *and* add the de-dup guard.

Also queue, outside the journey loop: the **merge-script laundering fix** (T2). Until it lands, any
browser-QA report whose rows use non-`UT-` IDs can turn a P1 FAIL into a canonical "PASS" for the
achievement gate — the precise failure this session has already had twice (iters 9/12).
