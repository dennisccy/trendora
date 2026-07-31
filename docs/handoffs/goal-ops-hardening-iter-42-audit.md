# goal-ops-hardening-iter-42 Audit Report

**Date:** 2026-07-31
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's headline goal landed and proved itself on its own run: `Target journeys:` now get the
same fresh-evidence guarantee `Required-still-passing journeys:` has, and the first artifact produced
under it is this iteration's own merged `**Browser QA Verdict:** FAIL` over UT-J-05/UT-J-07 — the
exact clean-headline-over-an-unverified-target failure iter-41 shipped is now impossible, and
demonstrably so. The second headline item did not land: the `_BarCache.prefill` symbol filter was
recorded as a real 2.5% VmPeak reduction, but that measurement compared the wrong pair — re-measured
with the lazy loads the change itself forces, the shipped code costs **+34,072 kB (+5.1%) peak
memory**, a net regression on the very axis AG-8/J-07 govern. I also found and fixed a
newly-reachable `KeyError` race in the bar cache that this iteration's filter opened in the parallel
backfill path. Records corrected, race fixed with a regression test; the prefill filter's keep/revert
disposition is left to the owner, as the DoD's own fallback clause directs.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): iter-42's filter made a half-published lazy load reachable — concurrent
`bars_asof`/`bars_asof_window` raised `KeyError` in the parallel backfill**

`apps/backend/app/engine/prices.py:362-363` (and `:420-421`) publish a lazily-loaded symbol into
**two** dicts in sequence — `self._by_symbol[symbol] = full`, then
`self._dates_by_symbol[symbol] = [bar.date for bar in full]`. The second statement's list
comprehension walks the whole series (≈7,600 bars for these symbols at the 30-year basis), so the GIL
is released between the two publishes. Both accessors take a deliberately **lock-free** fast path as
soon as `self._by_symbol.get(symbol)` is non-None and then indexed `self._dates_by_symbol[symbol]`
blind. A second thread reading in that window got `KeyError`.

Before iter-42 this was unreachable in production: `prefill` eagerly loaded **every** symbol in
`daily_prices` on the single orchestrating thread before any worker fan-out, so no worker ever
entered the lazy branch. iter-42's `WHERE symbol IN (expected_symbols)` filter deliberately leaves 43
non-pool symbols out of that scan, and 36 of them are the `config.etfs` index/sector/industry/
volatility ETFs that `sectors.py:46`, `themes.py:58`, `regime.py:47/73/116` and
`market_phase.py:119/180` read **per snapshot date, from the parallel backfill's worker threads**.
The dev handoff documents the same new concurrency in its own words while fixing only the *test*
instrumentation it broke ("two threads can both observe 'not yet loaded'";
`max(load_counts.values()) == 3` observed live) — the product-code publish race one line below was
not noticed by dev, review or QA.

Failure scenario: two workers race the first read of `XLK` during a multi-date backfill; the loser
sees `_by_symbol["XLK"]` populated, skips the lock, and raises `KeyError('XLK')` out of `bars_asof`,
aborting that date's sector/regime compute.

*Severity note:* I considered CRITICAL and settled on IMPORTANT — it fails loudly inside the
already-isolated per-date compute rather than corrupting or silently mis-serving data.

**Fix applied** (`prices.py:364-377` and `:422-427`): when the lock-free date read misses, re-read
under `_load_lock` — the lock every writer holds across *both* publishes — instead of indexing blind.
Two dict lookups on the hot path, unchanged otherwise; no writer order was touched (the two
dates-first readers, `bars_after:429-435` and `close_on:452-458`, are already safe *because* every
writer publishes `_by_symbol` first, so reordering the writers would have broken them instead).
**Evidence:** new `test_lazy_load_is_published_atomically_to_a_concurrent_reader` (parametrised over
both accessors) fails on the shipped code with
`AssertionError: a concurrent reader saw a half-published lazy load: KeyError('SPY')` and passes
after the fix; full suite `tests/test_bar_cache.py` → **22 passed in 98.63s**;
`tests/test_backfill_coverage_shared_cache.py` → **3 passed in 133.96s**.

**B2 — IMPORTANT (fixed — record corrected; code disposition left to owner): the TC-6 measurement
compared the wrong pair; the shipped filter is a +5.1% peak-memory REGRESSION, not a 2.5% reduction**

`runs/goal-ops-hardening-iter-42/bar-cache-prefill-bench/measure_prefill_subset_vs_full.py:44-58`
measures `prefill(pool)` against `prefill(None)` **and stops there** — it never exercises what the
change does with the rows it stops prefilling. Those 43 symbols are not dropped; they fall to
`bars_asof`'s lazy path (`prices.py:353-363`), which builds `list[Bar]` — the representation iter-41
replaced with `_SymbolColumns` *precisely because it costs ~3.3× more per row* (measured:
**264.6 B/row vs 81.0 B/row**). And they are read: 36 of the 43 (162,885 of 195,457 rows, 83%) are
the ETFs `config.etfs` names, read every snapshot date and held for the life of the cache.

Re-measured with that arm included
(`bar-cache-prefill-bench/audit_measure_prefill_plus_lazy.py`, same `/proc/<pid>/status` methodology,
one process per arm, run under the host-guard caps `scripts/start-backend.sh` applies — `taskset -c
0-15`, BLAS threads 8, `ulimit -v` at `memory_cap_mb` 6144, `MALLOC_ARENA_MAX=2`):

| Arm | Symbols | Rows resident | Lazily loaded | VmPeak (kB) | VmHWM (kB) |
|---|---:|---:|---:|---:|---:|
| iter-41 baseline — `prefill(None)` | 591 | 3,301,686 | 0 | 664,328 | 635,612 |
| iter-42 as shipped — `prefill(pool)` + the 36 ETF reads a real job makes | 584 | 3,269,114 | 36 | **698,400** | **668,964** |
| **Delta** | | | | **+34,072 (+5.1%)** | **+33,352 (+5.2%)** |

`LAZY_LOADED_SYMBOLS=36` is the iter-37-lesson live-condition assertion: the lazy path genuinely
engaged, and only the 7 truly-unreferenced names (`DIA`, `^DJI`, `^DXY`, `^NDX`, `^SPX`, `^TNX`,
`^VXN`, 32,572 rows) stay out. This is the *same* lesson the spec's own NOTES quote — asserting the
filter fired is not the same as measuring what the filtered-out work costs elsewhere.

Served values remain byte-identical and the SELECT is genuinely no longer unconditional, so this is
not a correctness defect — it is a wrong-signed claim about the one axis this journey is judged on,
made in a process that was observed dying of address-space exhaustion during this very iteration's
browser QA (B5). **Fixes applied:** `reports/perf-budgets.md` gained an "AUDIT CORRECTION"
subsection with the numbers above; the QA report's AG-8 row (the spec's own TC-7 deliverable) and the
dev handoff's Known Issues now state the corrected disposition. Whether to keep the filter, revert
it, or extend `_SymbolColumns` to the lazy path (which would import T2's ~70-80× read-latency cost
onto the hottest symbols) is a product tradeoff for the evaluator/owner — the DoD's own fallback
clause routes exactly this outcome there rather than to a silent re-claim.

**B3 — GAP: `prefill`'s empty-series bookkeeping is no longer safe by construction**

`prices.py:291-296` records `[]` for every `expected_symbols` name not already in the cache. That was
safe while `prefill` always loaded the whole table (anything absent genuinely had no bars). With the
filter, a *second* `prefill` on the same cache instance carrying a **wider** `expected_symbols` would
memoise real, bars-having symbols as empty series — a silent wrong answer (zero trailing bars ⇒
`below_history` exclusion), not a crash. Not reachable today: both live call sites
(`data_manager.py:3161`, `:3380`) pass the identical `pool_symbols`, and the second only prefills
when no shared cache was handed down. Recorded because the invariant that used to make this
impossible is gone, and the next caller to pass a different set will not be warned.

**B4 — OBSERVATION: measurement scripts run outside the launch scripts (AG-10 letter vs. practice)**

AG-10 says measurement passes "MUST be launched only via the project launch scripts". Both dev bench
scripts were run as bare `.venv/bin/python` invocations, as iter-41's precedent script was and as
that audit accepted (it read AG-10 as "launch scripts and `host-guard.env` untouched" —
`git status` on `scripts/` and `project-extensions/` is still empty this iteration). Flagged for the
record, not as a violation. My own re-measurement replicated the caps explicitly (see B2); the
tracemalloc per-row comparison ran bare at ~50 MB.

**B5 — Live product evidence (NOT an iter-42 regression): the backend hit its 6 GB address-space cap
and cascaded to a full outage; J-05's stalled ingest jobs are downstream of it**

Both target journeys failed live, and the evaluator needs the attribution right. From
`logs/backend.log` (process 2451515, started `06:20:11Z`, i.e. running iter-42's code):

- `RuntimeError: can't start new thread` first appears at line 153074, **after** job 1's status polls
  (line 152718; job created `06:40:53Z`) and before `06:46:13Z`; 26 occurrences follow.
- The first `MemoryError` block lands at `07:46:52` local (`06:46:52Z`, line 154002), in
  `compute_forward_aggregates` → `_forward_agg_slice_map` → `fetchmany`, then repeatedly in
  `_resolved_universe` → `universe_resolver.py:194` → `prices.py:592` (the **uncached** module-level
  `bars_asof`, not the cache).
- `GET /api/health` → 500 ×3, `/api/backtest` → 500 ×2, then five consecutive `HTTP:000` timeouts.

`ulimit -v` is set to `memory_cap_mb` (6144) by `scripts/start-backend.sh:48`, and the process was at
5.59 GB RSS per the browser QA's own `ps` check — so "can't start new thread" and `MemoryError` are
the *same* ceiling being hit from two directions. This is pre-existing, not introduced here:
`MemoryError` recurs in this log on 2026-07-30 16:57, 22:49 and 2026-07-31 00:08/00:11/01:44/01:54,
all before iter-42's `prices.py` was written (mtime 06:42 local), and the failing frames sit in code
this spec froze (`compute_forward_aggregates`, OUT OF SCOPE). **J-05's finding is downstream:** two
independently-started single-day backfills sat at `dates_done 0/1`, `symbols_total 0`,
`last_progress_at` frozen at their own creation stamp — the signature of a job whose worker thread
never started at all, in a process that cannot start threads. iter-42's own contribution to that
pressure is B2's +33 MB — directionally wrong but ~0.5% of the cap, far too small to be the proximate
cause.

### Frontend Findings

None — `Frontend Present: no`, and the diff touches no `apps/frontend/` file. The B4 frontend-restart
re-probe (`common.sh:1285-1304`) is test-lane infrastructure, verified below.

### Test Findings

**T1 — GAP: nothing tests or measures a real job's end-to-end cache footprint**

The bench script encodes B2's incomplete comparison, and no unit test asserts anything about the
cache's resident size after the lazy loads a job performs. iter-41 shipped a memory win with no
latency test (T2 caught that this iteration); iter-42 shipped a memory claim with no whole-job memory
measurement. The next touch of this file should measure prefill **plus** the reads that follow it.

**T2 — OBSERVATION (positive): the target-guard and B4 tests are genuinely tight**

`merge_ui_test_results.py`'s 7 new self-tests assert exact headline verdicts and section presence in
both directions, including `t_no_target_journeys_arg_unchanged`'s byte-identity proof that a spec
with no targets is unchanged (29 passed, re-run independently).
`test-frontend-restart-reprobe.sh` proves the new re-probe is invoked, recovers a still-down
frontend, **stays honest when the frontend never comes up**, and never engages when
`QA_FRONTEND_REQUIRED != yes` (7 passed, re-run). `_wait_for_frontend_ready` (`common.sh:1359`)
returns 0 only on a 2xx/3xx and is defined in the same file as its caller, so the `declare -F` guard
is belt-and-braces, not a silent no-op. No escape hatch found.

**T3 — OBSERVATION: `test_prefill_symbol_filtered_query_when_expected_symbols_given` is the right
shape** — it asserts SPY is *absent* from the cache after a filtered prefill (a live-condition proof
that the filter fired, not merely that the code exists) and that the lazy fallback then serves
byte-identical values in exactly one query. It is also the test that, read alongside B1, shows the
lazy path was newly promoted from "defensive, never reached" to "load-bearing under concurrency".

---

## 3. Domain Assessment

**Definition of Done — risk-ranked verification.** Items 1, 6, 7, 8, 9, 11, 12 are mechanical and
were executed against the running system by the reviewer (PASS, `issues: []`, `definition_of_done:
complete`) plus an executed QA/replay row, and I accept them on that basis with citations: the
target-guard wiring (QA report §A, "29 self-tests pass; 68 replay-lane tests pass; 7 frontend-restart
tests pass" — all three re-run by me), TC-8 NULL-tolerance (QA §C, test row
`test_prefill_null_numeric_column_degrades_without_crashing — PASSED`), TC-9 (QA §A), TC-10 (QA §D),
and TC-11 (`reports/phase-goal-ops-hardening-iter-42-regression-replay-results.md`, 6/6 PASS with
dated screenshots at 07:32-07:34, against the 07:20 backend running this iteration's code).

I ran the full trace on the risk-class and contradicted items:

- **Item 1 (target-journey lane)** — traced end-to-end because it is the iteration's purpose, and it
  holds *live*, not just in tests: `ui-test-designer/body.md` now emits a row per journey on either
  metadata line (mirror re-rendered, `sync-cli-assets --check` 0 drift);
  `reports/phase-goal-ops-hardening-iter-42-ui-test-plan.md:143,230,339,341` carries UT-J-05/UT-J-07
  rows; `merge()` forces `BLOCKED` on a missing/all-SKIP target additively
  (`merge_ui_test_results.py:289-294`); `TARGET_JOURNEYS` is set at `goal-iter-lean.sh:204` in the
  parent shell (the SPEED-2 fork ships only the replay lane's own globals, and the merge at :858 runs
  in that same parent — no serialization gap, matching the dev's claim) and mirrored from
  `_bqa_targets` at `browser-qa-phase.sh:282`. **Verified achieved.**
- **Items 2 and 3 (J-05, J-07 re-checked)** — traced because both are contradicted across artifacts
  (QA report: PASS, "Browser Checks: SKIPPED"; merged results: FAIL 6/8). The QA report simply
  predates the browser lane (07:31 vs 08:03) and is scoped to backend tests; the merged artifact the
  evaluator reads is honest. J-07 steps 1-2 were replayed live and failed; J-05 was replayed live and
  failed. **The re-check happened — which is the guarantee working — but TC-4's cold-restart log
  check was never reached** (browser-qa correctly refused to restart the backend), so J-05's
  verification is partial, and the golden scripts `J-05.json`/`J-07.json` remain unused for a fourth
  iteration (the LLM lane covered them instead, and correctly wrote no new golden on a FAIL).
- **Item 4 (prefill footprint)** — traced; **not met as recorded** (B2).
- **Item 5 (QA AG-8 row)** — traced; the row honestly said "partially addressed, not resolved" but
  carried the wrong-signed 2.5% figure. Corrected (B2).
- **Item 10 (no anti-goal violation introduced)** — AG-1/2/3/4/5/6 untouched (no evidence claims, no
  displayed-value change, byte-identical serving proven by the unmodified byte-identity harness);
  AG-7 clean (no credentials in the diff); AG-9 clean (both benches are read-only local SELECTs);
  AG-10: no launch script or `host-guard.env` byte changed. **AG-8 is the exception in degree, not in
  class:** the whole-table load it targets already existed, and this iteration moved resident memory
  ~33 MB the wrong way while recording a win. That is the gap this verdict is named for.

**Core domain logic.** The `_BarCache` invariant that mattered — load-once-per-job, byte-identical
slices, no lookahead — survives intact, and the byte-identity and load-count proofs are real (they
run against the seed engine through the actual parallel backfill, not a mock). What this iteration
disturbed is the *shape* of that invariant: the cache is no longer uniformly columnar, and the "every
symbol is resident before fan-out" precondition that made three separate pieces of code safe
(publish-order, empty-series bookkeeping, the "defensive — never reached" lazy branch) is gone. One
of those three had already broken (B1); one is now a documented trap (B3). A future iteration
touching this file should treat the mixed `list[Bar]` / `_SymbolColumns` cache as the thing to
simplify, not extend.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/prices.py` | `bars_asof` (:364-377) and `bars_asof_window` (:422-427): re-read `_dates_by_symbol` under `_load_lock` when the lock-free read misses, closing the half-published-lazy-load `KeyError` race iter-42's filter made reachable |
| 2 | Important | `apps/backend/tests/test_bar_cache.py` | New `test_lazy_load_is_published_atomically_to_a_concurrent_reader[bars_asof, bars_asof_window]` — forces the interleaving deterministically; fails on the shipped code, passes after fix 1 |
| 3 | Important | `reports/perf-budgets.md` | "AUDIT CORRECTION" subsection under Iteration 42: the measured +5.1% VmPeak / +5.2% VmHWM regression, the 264.6 vs 81.0 B/row figures, and the 36-symbol live-condition assertion |
| 4 | Important | `reports/qa/goal-ops-hardening-iter-42-qa.md` | AG-8 disposition row (the spec's own TC-7 deliverable) corrected from "partially addressed" + 2.5% reduction to "not addressed — measured net regression", with the numbers |
| 5 | Important | `docs/handoffs/goal-ops-hardening-iter-42-dev.md` | Known Issues: audit-attributed correction so no future iteration carries the 2.5% figure forward |
| 6 | — | `runs/goal-ops-hardening-iter-42/bar-cache-prefill-bench/audit_measure_prefill_plus_lazy.py` | New measurement script (the arm the dev's TC-6 script omitted) |

**Post-fix verification:** `tests/test_bar_cache.py` → 22 passed in 98.63s;
`tests/test_backfill_coverage_shared_cache.py` → 3 passed in 133.96s;
`merge_ui_test_results.py self-test` → 29 passed, 0 failed;
`test-frontend-restart-reprobe.sh` → 7 passed, 0 failed;
`lint_contracts.py self-test` → "current tree lint → clean OK". My product-code diff is two guarded
re-reads and their comments; nothing else in `prices.py` was touched.

---

## 5. Recommended Next Step

Do **not** open the next iteration on `_BarCache.prefill` — that would be attempt #6 at a seam whose
fifth attempt just measured backwards. Three things, in order:

1. **Owner/evaluator disposition on the shipped filter (blocking B2).** Keep it and accept ~33 MB, or
   revert it, or make the lazy path columnar and pay T2's read-latency cost. This is a tradeoff
   decision, not an implementation task, and it should be settled before any further work on this
   file.
2. **The real J-07 blocker now has fresh, dated, live evidence for the first time in several
   iterations (B5):** the backend hits its 6 GB `ulimit -v` ceiling inside the historical
   forward-aggregate warm and cascades — thread exhaustion, `MemoryError` in
   `_forward_agg_slice_map`/`_fr_slice_map`'s `fetchmany`, `/api/health` 500s, then a multi-minute
   outage. That is an unbounded `fetchmany` accumulation in `research.py`/`forward_testing.py`, the
   same accumulator-vs-cursor shape this session has now learned twice — and it is where J-07 and
   J-05 both actually fail. It sits behind the "byte-frozen" fence, so unfreezing it is an owner
   call; nothing else will move J-07.
3. **Carry B1's lesson forward, not just its fix:** iter-42's own dev, reviewer and QA all read the
   new concurrency and none looked one line below the test it broke. When a change promotes a
   "defensive, never reached" branch to a live one, that branch's own invariants must be re-audited,
   not just its callers.

J-05 and J-07 should stay `failing`/`partial` in the journey history with this iteration's live
evidence attached, and J-01/J-03/J-04/J-06/J-08/J-09 stay `passing` on dated replay rows. The
verification lane itself is now trustworthy — which is what this iteration was for, and why its own
honest FAIL headline is the strongest artifact it produced.
