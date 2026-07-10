# Phase goal-mcp-loop-iter-26 — UX Regression Review

**Date:** 2026-07-10

**Verdict:** UX-REGRESSION-FAIL

---

## Summary

This iteration shipped zero frontend source changes by design (confirmed: `git diff --stat HEAD -- apps/frontend` and `git status --short apps/frontend` both return nothing). There is no new capability to make discoverable, so Step 1 of the standard review (discoverability) is trivially satisfied — nothing new was hidden because nothing new was added. The failure here is **Step 2 (regression)**: browser-qa's UT-02 run reproduced a full, unrecovered backend outage (`MemoryError` → HTTP 500 on every data endpoint, `/api/health` included) while exercising a job path this iteration's changed module (`prices.py`'s `_BarCache`) executes through. As a direct result, **none of the 8 required-still-passing journeys (J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-15) were verified this iteration** — they were SKIPPED, not passed — and the target journey J-16 itself FAILED at its direct proof point (UT-02). I independently confirmed at review time that both the backend (`:8255`) and frontend (`:3255`) are currently unreachable (`curl` → exit/connect-fail on both), consistent with the coordinator's note that the wedged process was terminated and not yet restarted.

A UX regression review exists precisely to catch "current changes touch a component prior features depend on, and the prior feature may now be broken." Here that is not a theoretical risk — it is an observed, reproduced, still-unresolved outage. That is definitionally UX-REGRESSION-FAIL, independent of whether the eventual root-cause attribution lands on this iteration's diff or a pre-existing latent issue (see Root-Cause Attribution below).

---

## New Capability Discoverability

Nothing new to assess. Per `reports/phase-goal-mcp-loop-iter-26-user-visible-changes.md` and the execution plan's "UI Evolution" section: no new page, endpoint, button, form, nav entry, or displayed value. The one user-visible effect (jobs finish faster) is a timing change to the existing Fetch/Backfill/warmup controls on `/data`, which was already reachable via the persistent sidebar ("Data Manager" — confirmed present in `runs/goal-session-mcp-loop/state/blueprint.md`'s nav list) before this iteration. No discoverability gap exists because no new capability was built.

---

## Regression Risk

| Shared component touched | Prior feature it serves | Current-phase change | Observed status | Risk |
|---|---|---|---|---|
| `apps/backend/app/engine/prices.py` — `_BarCache` class (`close_on`, `bars_after` made cache-aware; new `_BarCache.bars_after` method) | J-16 itself, plus every journey reading price/score data (J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-15) — all route through `bars_asof`/the shared bar cache | `close_on`/`bars_after` now route through the SAME `_BarCache` class whose (unmodified) `bars_asof` method crashed | **Confirmed broken** — `MemoryError` in `prices.py:191` inside `_BarCache.bars_asof`'s `full[:cut]`, backend down since | **Confirmed regression**, not merely potential |
| `apps/backend/app/engine/scoring.py` (bounded window slice) | J-01/J-03/J-10/J-12 (every displayed score/pattern) | Slices `bars_asof`'s output to `max_lookback_bars` before indicator computation | Not independently exercisable — backend down; byte-identity harness (`test_scoring_window.py`, 2 passed) is the only evidence this path is safe, and it does not exercise the crashing job shape (322-date × 541-member full universe rebuild under a live `ulimit -v` cap) | Medium — unit-proven correctness, but no live confirmation this iteration |
| `apps/backend/app/engine/warmup.py` (`backfill_forward_returns` moved inside `bar_cache`, passed `session` not `engine`) | J-16 (warm-up job progress) | Warm-up now shares one session/cache for cadence loop + forward-return backfill | Not live-verified — UT-02/UT-03 (the direct proof of honest warm-up/backfill progress) FAILED/blocked by the crash before reaching a clean completed state | High — this is the exact journey the crash blocked |

### Regression detail — the UT-02 crash

Per `reports/phase-goal-mcp-loop-iter-26-ui-test-results.md`: starting the sanctioned "Rebuild snapshots for current universe" job (322 dates × 541 members — used because the primary pre-filled Backfill range was a genuine 0/0 no-op) ticked its progress counter honestly (0→117→246/322, no premature "done") for a while, then the backend logged 20+ `sqlite3.OperationalError: disk I/O error` entries followed by a fatal `MemoryError`:

```
data_manager._compute_one_backfill_date → scanner.compute_run_payload → regime.score_regime
→ regime._index_ma_stack → prices.bars_asof (prices.py:333) → _BarCache.bars_asof (prices.py:191)
→ full[:cut] → MemoryError
```

After this, `GET /api/data`, `/api/stocks`, `/api/evidence`, and `/api/data/jobs/{id}` all returned HTTP 500; `/api/health` briefly gave a **false-positive 200** before it too failed — the exact false-"OK" risk the iter-24 lesson (`docs/handoffs/goal-mcp-loop-iter-24-audit.md`) already named once, now reproduced in a second, different code path. The backend process (PID 499553) stayed alive but frozen (VSZ pinned at exactly 6,291,456 KB = the `server.memory_cap_mb` 6144 MB `ulimit -v` ceiling; RSS ~4.93 GB, under the RSS budget but irrelevant once VSZ hits the hard cap). Browser-qa attempted the prescribed recovery (stop → cold-start via `start-backend.sh`) but the sandbox denied the signal (process not started this session); the backend was still down at UT-02's write time, and I independently confirmed both `:8255` and `:3255` are unreachable right now (`curl` connect failure on both).

### Root-cause attribution (why this matters for how the fix is scoped, not for the verdict)

The crashing frame (`_BarCache.bars_asof`, `prices.py:191`) is **pre-existing, unmodified code** (the J-46/iter-19 load-once cache) — it is not part of this iteration's diff. The job that triggered it, `data_manager._do_backfill` / `_compute_one_backfill_date`, is also entirely unmodified this iteration (not in `git diff --stat`); it already prefills ONE shared `_BarCache` with **every** symbol's **full** 30-year series up front (`prefilled_bar_cache(session, expected_symbols=pool_symbols)`, `data_manager.py:2500`, an iter-19/iter-37 design predating this phase) before fanning the 322-date compute across worker threads. That full-universe, whole-history prefill is the standing memory-pressure source, not the two lines iter-26 added.

That said, iter-26 is not a bystander: it is what makes `close_on`/`bars_after` (called inside the SAME job's forward-return backfill step) route through that identical `_BarCache` for the first time in this job — previously those calls were cheap, single-row raw SQL queries with minimal Python-side allocation; now they go through `cache.bars_asof(...)` → `full[:cut]`/`full[cut:]`, allocating a fresh list slice (up to ~5,300-element `Bar` tuples) on every one of the ~6,110 stock-date forward-return lookups this job performs. `ulimit -v` limits **virtual address space**, and CPython's allocator does not reliably return freed-arena memory to the OS — a shift from "many tiny SQL round-trips" to "many transient large-list-slice allocations" is a textbook way to grow VSZ under allocator fragmentation without growing RSS proportionally, which matches the observed symptom (VSZ pinned exactly at the ulimit ceiling while RSS stayed comfortably under the separate 6144 MB RSS cap). I could not confirm this mechanism by profiling (no live backend to attach to), so it is a plausible hypothesis, not a proven cause — but it means the fix cannot be waved off as "unrelated pre-existing bug, out of scope." At minimum, this exact 322-date/541-member full-rebuild job path needs to be added to this iteration's own before/after perf-budget measurement (the dev handoff's `reports/perf-budgets.md` Item-F measurement covers a 12-date subset, not a full-universe rebuild under the live `ulimit -v` cap) before the fix in `prices.py` can be trusted not to have worsened this specific job's memory profile.

---

## UI vs Backend Parity

No new backend capability is hidden from the UI — the phase intentionally ships zero new displayed values (confirmed by `ui-surface-map.md`'s "Backend-Only Changes" section: config/scoring/prices/warmup changes are all internal compute-path only, re-serving the same registered values byte-identically per the byte-identity harness). The only "new" content is the before/after timing rows in `reports/perf-budgets.md`, which the phase spec explicitly scopes as a committed report, not a UI value — this is a correct, intentional backend-only artifact, not a parity gap.

---

## Flags

### Hidden Capabilities
None — no new capability shipped this iteration.

### Undiscoverable Capabilities
None — no new capability shipped this iteration.

### Potential Regressions
- **CONFIRMED (not potential), CRITICAL:** the "Rebuild snapshots for current universe" Backfill job (the sanctioned fallback path for J-16 verification, and a pre-existing production capability on `/data`) crashes the entire backend with a `MemoryError` inside `prices.py`'s `_BarCache.bars_asof`, and the backend has not self-recovered. Every required-still-passing journey this iteration was supposed to replay green (J-01 `/stocks` scores, J-03 unproven/noise marking, J-04 Dashboard regime, J-05 `/evidence` ledger, J-10 deep-history chart, J-12 universe/membership counts, J-13 `/data` legend, J-15 perf budgets/storage card + cold-path `/data`) is **unverified this iteration**, not passing — browser-qa recorded them SKIPPED, and the coordinator's own note says to treat SKIPPED as unverified, not passing.
- **Recurrence of a known failure class:** this is the second time this session a `ulimit -v` (VSZ, not RSS) exhaustion has crashed the backend with `MemoryError` (the first was iter-24's `mmap_size × connection pool` cold-`/api/data` crash, fixed by `docs/handoffs/goal-mcp-loop-iter-24-audit.md`). The failure signature (false-positive `/api/health` 200 before the endpoint itself dies) is also a second occurrence of the exact iter-24-named risk. This suggests the project's perf-budget/OOM regression gate needs a full-universe/long-job case, not only the cold-boot-`/api/health` and 12-date-sample cases it currently covers.

### Visual Consistency
Not applicable — zero frontend files changed. No new page or component to assess against the design system.

---

## Recommendation

Do not close this phase. In priority order:
1. Someone with permission to manage the harness-owned backend process must stop and cold-restart it (the sandbox denied browser-qa this action).
2. Re-run UT-02 through UT-16 against a live backend once restarted, including the UT-04 cold-path repro the plan itself calls out as mandatory (iter-24 lesson).
3. Investigate and fix the `_BarCache`/full-universe-rebuild `MemoryError` before re-closing J-16 — at minimum, extend the dev's Item-F perf-budget measurement to cover a full-universe, many-date rebuild job under the live `ulimit -v` cap (not just the 12-date subset already measured), since that is the exact shape that crashed and the exact shape the current perf-budget section does not cover.
4. Only after all 9 journeys (J-16 + the 8 required-still-passing) show a genuine PASS on a live backend should this iteration be considered for closure.
