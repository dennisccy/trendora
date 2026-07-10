# goal-mcp-loop-iter-26 Audit Report

**Date:** 2026-07-10
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** FAIL

The live browser lane (which QA had deferred) reproduced a **`MemoryError` that took the entire backend
down** while running the `/data` "Rebuild snapshots for current universe" backfill — the exact job class
J-16 is about. The target journey **J-16 FAILED** at its direct proof point (UT-02) and all eight
required-still-passing journeys (J-01/03/04/05/10/12/13/15) are **UNVERIFIED** (SKIPPED behind the
outage), so three DoD items and the critical data-scale anti-goal are not satisfied. The DoD's
"no memory regression under the 6144 MB cap" claim was substantiated only on a 12-date subset with an
**RSS** probe, but the failure is **VSZ (virtual-address-space) exhaustion** at the `ulimit -v` ceiling on
the full 322-date × 541-member shape — a metric and a shape the measurement never tested. I did **not**
apply a speculative memory fix: the crash cannot be reproduced or verified live (backend terminated; the
full-universe repro is a long run), and the real fix is architectural memory work that must be measured at
the crashing shape — an honest FAIL with a precise repro recipe is the correct outcome here.

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (gap; not fixed — see rationale): full-universe backfill crashes the entire backend with a `MemoryError` (VSZ = `ulimit -v` ceiling)**

Browser-qa's UT-02 ran the sanctioned J-16 path ("Rebuild snapshots for current universe", 322 dates ×
541 members) and the backend crashed with a `MemoryError` at `apps/backend/app/engine/prices.py:191`
(`_BarCache.bars_asof`, `return full[:cut]`), reached via
`data_manager._compute_one_backfill_date` → `scanner.compute_run_payload` → `regime.score_regime` →
`regime._index_ma_stack` (`regime.py:39`) → `prices.bars_asof` (`prices.py:333`). After the crash every
data endpoint returned HTTP 500; `/api/health` returned a **false-positive 200** for a window before it
too failed (a recurrence of the iter-24 risk). Evidence:
`reports/phase-goal-mcp-loop-iter-26-ui-test-results.md` (Critical Finding + UT-02);
`reports/qa/goal-mcp-loop-iter-26-evidence/UT-02-backend-log-tail.txt`. The coordinator independently
confirmed the wedged process was pinned at **VSZ 6,291,456 KB = 6144 MB** (the `ulimit -v` ceiling
`scripts/start-backend.sh` sets from `server.memory_cap_mb`) with **RSS 4,932 MB** — i.e. a
virtual-address-space exhaustion, a *different signal* than peak RSS.

This defeats the phase's primary purpose (fast **and crash-free** data jobs on the deep basis) and
violates the spec's critical anti-goal #8 ("widening the data basis … must never … exhaust a service's
memory"). The honest-degradation UI worked (see OBS-1), but the backend itself went down.

Root-cause attribution (git-verified): the crash **frame** (`_BarCache.bars_asof:191`) and the crashing
**job** (`data_manager._do_backfill` / `_compute_one_backfill_date`, which prefills every symbol's full
30-year series — `data_manager.py:2500`, `prefilled_bar_cache(session, expected_symbols=pool_symbols)`)
are **pre-existing, unmodified code** — `git diff --name-only HEAD` shows iter-26 touched only
`config.py`, `prices.py`, `scoring.py`, `warmup.py`, `config.yaml`; `regime.py`, `data_manager.py`,
`scanner.py`, `forward_testing.py` are NOT in the diff. So I cannot prove iter-26 *caused* this crash;
the 322-date full-universe rebuild at 30-year scale may have been a latent VSZ bomb. **But the verdict
does not depend on causation:** the phase's own DoD requires J-16 to pass via browser-qa (it FAILED), the
8 required journeys to replay green (all SKIPPED/unverified), and no memory regression under the cap
(measured on the wrong shape). Whether iter-26 caused it or merely failed to prevent/detect it, the phase
goal is not achieved.

*Why not fixed:* per the coordinator's explicit guidance and this agent's evidence floor, a speculative
memory fix that cannot be verified live is worse than an honest FAIL. The backend is terminated (I cannot
observe endpoints), the full-universe repro is a long run, and the crash frame is not even in iter-26's
diff — a surgical patch here would be unverifiable and risk trading one defect for a byte-identity bug.
See §5 for the concrete repro + fix recipe handed to the next fix-mode pass.

**B2 — CRITICAL (gap; not fixed): DoD memory/perf evidence does not cover the shape that crashed, and uses the wrong metric**

The fix-mode measurement (`reports/perf-budgets.md` Item F; dev handoff "Fix Notes") timed `score_stocks`
and an isolated 6,110-pair `close_on`/`bars_after` loop over a **12-date deep-history subset inside one
shared prefilled cache**, reporting **peak RSS = 1,330.6 MB** via `getrusage(...).ru_maxrss` and "no
MemoryError under `ulimit -v 6144`". This never exercised the full-universe **322-date `_do_backfill`
under the live cap** — the exact shape browser-qa crashed — and it probes **RSS**, which by construction
cannot catch the observed **VSZ** ceiling hit (RSS was ~4.9 GB, comfortably under 6144 MB, *while* VSZ was
pinned at 6144 MB). Consequently the DoD item "Peak process RSS during warmup/backfill stays under the
6144 MB cap — no memory regression" is **unsubstantiated at the shape that matters**, and the downstream
claims are false-positives: QA verdict PASS, `status.json` `performance_targets_met: true` /
`no_regressions: true`, and the dev handoff's "cannot raise the ceiling." The Item-F CPU-speedup numbers
(81% / 78% / 89%) are plausibly real *as an isolated scoring/forward-read CPU delta*, but they do not
represent the actual backfill job, which does not complete.

**B3 — IMPORTANT (gap; not fixed): iter-26's cache-aware `close_on`/`bars_after` add large transient list-slice allocations to the very job that crashed**

Diff-confirmed (`git diff HEAD -- prices.py`): the new module-level cache paths materialize the entire
`≤ D` prefix on every forward-return lookup —
- `close_on` (`prices.py:354-357`): `bars = cache.bars_asof(session, symbol, d); return bars[-1].close …`
  — allocates `full[:cut]` (up to ~5,300 `Bar` tuples) **only to read `[-1].close`**;
- `_BarCache.bars_after` (`prices.py:202-206`): `self.bars_asof(session, symbol, d)` allocates and
  **discards** `full[:cut]`, then allocates `full[cut:]` and `after[:limit]`.

These run inside `_do_backfill`'s per-date forward-return step (`data_manager.py:2441`
`attach_shared_cache` → `2450` `backfill_run_forward_returns`), which previously issued tiny single-row
SQL (`SELECT … LIMIT 1` / `LIMIT horizon`) with negligible Python-side allocation. iter-26 replaced
"many tiny SQL round-trips" with "many transient large-list-slice allocations" — a textbook way to grow
VSZ under CPython arena fragmentation without growing RSS proportionally, which matches the observed
symptom (VSZ at the ceiling, RSS well under it). This is a **genuine, diff-confirmed memory regression in
that job's forward-return step**; it is a *plausible contributor* to the VSZ exhaustion (not provably the
sole cause, since the crash surfaced in the pre-existing unwindowed regime `full[:cut]`). The
`close_on`/`bars_after` slices are also **avoidable** — see §5 fix (1)/(2). Byte-identity is preserved by
the current form (`test_forward_testing.py` cache-awareness cases green), so this is IMPORTANT, not
CRITICAL, on its own — but it means iter-26 cannot be waved off as a bystander.

**B4 — OBSERVATION: the scoring window (the actual feature) is implemented correctly and is byte-identity-gated**

`scoring.py:121` (`_raw_components`) and `scoring.py:351` (pass-3) slice `bars = bars[-icfg.max_lookback_bars:]`
immediately after each `bars_asof` call, before any indicator/detector runs; a short-history member keeps
its whole series. `config.yaml` sets `indicators.max_lookback_bars: 320` with validators in `config.py`.
The byte-identity harness (`test_scoring_window.py`, 2 passed, 3 dates × full pool + a short-history date,
0 diffs) is the correct correctness authority and is green; the reviewer independently corroborated the
harness and the perf log against scratchpad artifacts. Note the window was applied **only** at the two
scoring sites, **not** at the regime path (`regime._index_ma_stack`/`_universe_stats` still feed the full
unwindowed series through `bars_asof`) — consistent with scope, but it means the window change did not
reduce the memory of the crash frame.

### Frontend Findings

**F1 — n/a: no frontend source change (correct).** `git diff --stat HEAD -- apps/frontend` is empty
(confirmed by the ux-regression review). The failure is a backend outage, not a UI defect. The
honest-degradation UI is a positive — see OBS-1.

### Test Findings

**T1 — IMPORTANT (gap): no test/gate exercises the full-universe long-job memory shape**

The iter-26 tests that are green (byte-identity harness; `test_bar_cache.py` 12; `test_forward_testing.py`
50 incl. 2 new cache-awareness cases; `test_config*`/`test_indexes.py` 128; the warmup query-count proof)
prove **correctness/byte-identity and query-count**, not **memory under load**. No committed test or
perf-budget gate runs the 322-date × full-universe `_do_backfill` under the `ulimit -v` cap — precisely
the shape that crashed and, per the ux-regression review, the second time this session a VSZ (`ulimit -v`)
ceiling has downed the backend (iter-24 was the first). The regression gate needs this long-job case, not
only the cold-`/api/data` and 12-date-subset cases it currently covers.

**T2 — GAP: DoD "existing scoring/forward-return suites UNEDITED and green" only partially executed**

`test_scoring.py`, `test_sectors.py`, `test_themes.py`, `test_data_manager.py` were NOT run (deferred to
the full-suite lane); `test_warmup.py` had 5 tests fail on an environment disk-I/O artifact (1 later
confirmed environmental, 4 unrun). git confirms these files are UNEDITED or carry only a one-line
mechanical `max_lookback_bars` fixture field, and the green byte-identity harness makes an UNEDITED
scoring test safe-by-construction — a reasonable argument, so this is a GAP, not a blocker. It is not the
reason for the FAIL (B1/B2/B3 are).

---

## 3. Domain Assessment

The core domain change — bounding the scoring-input window to the true maximum lookback and gating it on a
byte-identity harness — is sound, correctly scoped, and correctly implemented (B4). The
session-vs-engine cache-registry fix in `warmup.py` and the cache-aware `close_on`/`bars_after` are also
correct for byte-identity. The domain problem is **memory discipline on the deep basis**, which is the
phase's own stated purpose and critical anti-goal:

- The `_do_backfill` "rebuild" job prefills the **entire** 3.29M-bar universe as `Bar` tuples up front,
  then per date materializes `full[:cut]` slices in the (unwindowed) regime path, and — new in iter-26 —
  additional `full[:cut]`/`full[cut:]` slices in the forward-return step. At 30-year full-universe scale
  under a 6144 MB `ulimit -v`, this crosses the virtual-address-space hard cap.
- The feature that was supposed to make this *safe and fast* (a bounded window) was applied to the two
  scoring sites but **not** to the regime path where the crash actually lands, and iter-26 simultaneously
  **added** allocation to the forward-return path (B3). Net direction of iter-26 on this specific job's
  peak allocation is genuinely uncertain and was never measured at the crashing shape.

The honest-failure surfacing was good on the read side (the `/data` "Backend unavailable — no figures
shown rather than fabricated" card), but the compute side violated the memory anti-goal outright.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | **None.** No fix applied — deliberately. The failure is a memory exhaustion whose fix cannot be verified live (backend terminated; the full-universe repro is a long run; the crash frame is outside iter-26's diff). Per the coordinator's guidance and this agent's evidence floor, an unverifiable speculative memory patch is worse than an honest FAIL. The repro + fix recipe is handed to the next fix-mode pass (§5). |

---

## 5. Recommended Next Step

**Do not close this phase.** Return to a fix-mode developer pass with a live backend. In priority order:

1. **Restore the backend** (harness-owned process was terminated; browser-qa lacked permission to
   restart it). Bring up both prod-mode services; confirm HTTP-200.

2. **Reproduce the crash deterministically** and make it a committed regression gate: run the full
   `_do_backfill` "Rebuild snapshots for current universe" (full universe × full cadence, ~322 dates)
   under the real `ulimit -v 6291456` (6144 MB), sampling **both VSZ and RSS** (VSZ is the failing
   metric — an RSS-only probe cannot catch it). This is the exact shape the DoD's Item-F measurement
   omitted; add it to `reports/perf-budgets.md` as a before→after, never-regress budget.

3. **Reduce iter-26's added allocation (surgical, byte-identity-preserving) —** verify each with the
   existing `test_forward_testing.py` cache-awareness cases plus the byte-identity harness before trusting:
   - `close_on` cache path: avoid materializing the prefix — `cut = bisect.bisect_right(dates, d);
     return full[cut-1].close if cut > 0 else None` instead of `cache.bars_asof(...)[-1].close`.
   - `_BarCache.bars_after`: replace the discarded `self.bars_asof(...)` slice with a load-ensuring call
     that does not allocate `full[:cut]`, then `full[cut:][:limit]`.

4. **The real fix is architectural memory work** (likely outside iter-26's original 4-file scope): bound
   or stream the regime/backfill path's `full[:cut]` allocations and/or the full-universe prefill so the
   deep-basis rebuild stays under the `ulimit -v` cap. This is the crash frame's own pre-existing code and
   should be owned as its own memory-hardening iteration if it exceeds surgical scope — do not force it
   into an audit patch.

5. **Re-run the browser lane in full** on the fixed, live backend: J-16 (UT-02/UT-03 to a *verified
   completed* state), the UT-04 cold-`/data` OOM repro (iter-24 lesson, mandatory), and a genuine PASS
   (not SKIPPED) on all eight required-still-passing journeys before this iteration is reconsidered for
   closure. GOAL_ACHIEVED is not in reach this iteration regardless (J-02/06/07/08/09 remain
   sanctioned-partial per the iter-25 evaluator).

**OBS-1 (carry-forward note):** the honest-degradation UI worked correctly and the false-positive
`/api/health` 200-before-death recurred the iter-24 risk — worth hardening the health probe to exercise
the data path, tracked separately.
