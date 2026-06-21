# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-42 Execution Plan

J-100 — bounded-resource backend hardening for the `compute_coverage` / membership-timeline read path.
Pure performance/stability property: **every served value stays byte-identical**. Backend-only.

## What to Build
- **(a) Single-flight + result cache around the coverage / membership compute.** Wrap `compute_coverage`'s
  heavy work (`_resolved_universe` resolve at `data_manager.py:635` + `membership_timeline_cached` at `:690`)
  so concurrent `/api/data` callers for the SAME resolved as-of share ONE in-flight computation (or the
  already-cached payload). Reuse the warm-up controller's existing idiom (`warmup.py`: `_WARMUP_LOCK`
  `threading.Lock` + `_WARMUP_THREAD.is_alive()` guard, `:60`/`:192-193`) — do NOT invent a new lock
  abstraction. N parallel probes must cost ~one compute. Served payload byte-identical to today.
- **(b) Decouple the membership/coverage cache key from forward-return churn.** `research._dataset_version`
  (`research.py:1229`) returns `r{max_run_id}-f{fr_count}`; the `f{fr_count}` term invalidates the membership
  cache on every warm-up forward-return insert. Introduce a **membership-specific dataset stamp** that depends
  ONLY on membership's real inputs (bars manifest + the `ScannerRun.asof_date` snapshot set + relevant config)
  and NOT on `ForwardReturn` row count. **Keep `research._dataset_version` UNCHANGED** (it is the J-72/J-87
  event-study/market-phase stamp — out of scope to touch). Only `membership_timeline_cached`'s key adopts the
  narrower stamp.
- **(c) Reuse one process-level bar cache (load-once, invalidate-on-data-change).** The `_resolved_universe` +
  membership-timeline read path must reuse a single process-level bar cache (existing
  `prices.attach_shared_cache` / `bar_cache` / `prefilled_bar_cache` machinery) instead of rebuilding a
  fresh ~1.3M-row prefill per request — bound memory to one shared copy regardless of concurrency. Invalidate
  on a real data change (the same signal the (b) stamp uses). **Preserve the iter-37 J-46 load-once-per-job
  invariant** (zero-bar candidates recorded as empty series up front; assert load-COUNT, not only value).
- **(d) Ops guards in `scripts/start-backend.sh`.** Add uvicorn `--limit-concurrency` (config-/env-sourced
  bound — NO magic literal in the script) + a heavy-endpoint request timeout so `/health` + light reads stay
  responsive under load; run the backend under an explicit process memory cap (`ulimit -v` is the portable
  choice on this host) so a pathological spike OOM-kills ONE process, never swap-thrashes the VM. **Do NOT add
  redundant threadpool offloading** — verified: `data_overview` (`app/api/data.py:94`) is a plain sync `def`,
  so FastAPI already runs it in the threadpool (Simplicity First).
- **(e) Test hygiene codified** in QA + handoff: `/api/data` is single-loaded, never concurrently probed in
  normal QA (the load test is the ONE sanctioned concurrent probe); document the `.pump-alive` toucher +
  `CHAIN_PUMP_HEARTBEAT_TIMEOUT` / `CHAIN_DISPATCH_INFLIGHT_TIMEOUT` envs for the long nohup full suite.
- **New concurrency load test** (see Key Test Scenarios).

## Agents Required
- developer: yes -- implement (a)-(d) in `data_manager.py` / `research.py` (membership stamp only) /
  `prices.py` (if shared-cache wiring needed) / `scripts/start-backend.sh`; add the concurrency load test, the
  membership-stamp-not-invalidated-by-FR-inserts test, and the byte-identity assertion; keep the iter-37 J-46
  load-COUNT test green. TDD. Hand the full pytest suite to the pump nohup-async.

## Frontend Present
no

> Backend-only diff, no frontend file changes. **However** the required-still-passing journeys are RENDERED
> pages and the whole point is to prove no served value changed — so the QA/browser-qa live re-verify of
> J-94/J-96/J-93 + the Dashboard cluster MUST still run (do NOT pass them on API-layer byte-identity alone).
> Per iter-36/39 lesson, if framework browser-QA auto-skips on `Frontend Present: no`, a lean live re-verify
> follows next iter. A frontend diff appearing in this iteration is OUT OF SCOPE and a coherence/IA red flag.

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` -- single-flight wrapper around `compute_coverage`'s heavy work;
  membership cache adopts the narrow stamp; reuse one process-level bar cache.
- `apps/backend/app/engine/research.py` -- ADD a membership-specific stamp helper (bars + snapshot set +
  config; NOT `fr_count`). **Do NOT modify `_dataset_version` (`:1229`).**
- `apps/backend/app/engine/prices.py` -- only if shared-cache reuse/invalidation needs wiring; preserve the
  iter-37 `expected_symbols` load-once behaviour.
- `scripts/start-backend.sh` -- `--limit-concurrency` (env/config-sourced), heavy-endpoint timeout, `ulimit -v`
  memory cap. No magic literals.
- `apps/backend/tests/test_<concurrency_load>.py` -- NEW: K parallel `/api/data` → bounded latency, bounded
  peak RSS, `/health` responsive throughout, coverage byte-identical to single-request baseline.
- `apps/backend/tests/test_data_manager_membership_cache.py` (or sibling) -- ADD: a forward-return-only insert
  does NOT invalidate the membership cache (probe an ALREADY-POPULATED row = a real HIT, iter-38/39 lesson);
  a snapshot add/remove DOES invalidate it; `compute_coverage` byte-identical before/after.
- `docs/handoffs/goal-...-iter-42-dev.md` -- dev handoff with the test-hygiene note (e).
- `apps/backend/tests/test_db.py` -- ONLY if a new `table=True` model is added (it should NOT be —
  `membership_timeline_cache` already exists). If added, register in the expected-tables guard same iter.

## Risks/Unknowns
- **Byte-identity is the contract.** Pair every "byte-identical value" claim with the compute/load-COUNT
  invariant it preserves (single-flight ⇒ N probes cost ~1 compute — assert the COUNT, not only the values).
  iter-35/36/37 showed value-equality tests miss load-count regressions.
- **Membership-stamp correctness trap (iter-38/39).** The new stamp must HIT across forward-return churn AND
  invalidate on a real membership change. Unit-test against an already-populated cache row, not a fresh
  compute that masks a stale-cache bug; probe the LIVE current as-of (a HIT), not a fresh-compute date.
- **Pool exhaustion (MEMORY lesson).** One `/api/data` holds a DB connection ~10 s; pool is size 5 + overflow
  10. NEVER concurrently probe `/api/data` outside the sanctioned load test. Single-load `/data` (~30 s
  hydration wait) in QA.
- **Suite runtime + slow-boot flakes.** Full pytest ~3.5 h on this 1369/1371-date host; cannot finish under a
  subagent Bash cap. Split fast (no-boot) vs slow (seed-boot); verify anti-goal legs via the fast set; hand
  the flushed `0 failed, EXIT 0` to the pump nohup-async; NEVER block the evaluator on the in-flight suite.
  Re-run any isolated `test_warmup.py` / `test_data_manager_jobs_pipeline.py` `F` BEFORE calling it a
  regression (known scanner_runs-race / slow-boot / warm-up-contention flakes, iter-30/34/36).
- **`ulimit -v` portability.** Verify it applies cleanly on this host without OOM-killing legitimate warm-up;
  document the chosen cap value and how it is enforced. Set it high enough to clear the ~1.3M-row one-copy
  prefill plus normal headroom (the cap protects against pathological N-copy spikes, not the bounded baseline).
- **Browser-QA auto-skip on `Frontend Present: no`** (iter-36/39). If the live re-verify of the rendered
  required journeys is skipped, flag it and require a lean live re-verify next iter — do NOT silently mark
  them "still passing" on byte-identity alone.
- **Plan the Playwright fallback UP FRONT** for any live render evidence — Chrome MCP CDP has emptied the
  evidence dir / timed out on iters 38/39/40 (cached Chromium at `~/.cache/ms-playwright/chromium-1208`).
- **Out-of-scope guardrails:** no change to any canonical score/return/bucket/setup/regime/membership, the
  Risk-Off→Actionable gate, or `_dataset_version`; no J-85 rebuild (~11 h destructive); no resolver/scoring
  math change; no frontend change; no general coverage-cache layer beyond what (a)-(c) require (Surgical).

## Acceptance Criteria mapping
- **J-100 (target):** scope (a)+(b)+(c)+(d) + the concurrency load test (K parallel `/api/data` → bounded
  latency, peak RSS under the configured cap, `/health` low-latency throughout, coverage byte-identical to the
  single-request baseline) + the membership-cache-not-invalidated-by-FR-inserts test (and invalidated-by-
  snapshot-add/remove). → Definition of Done bullets 1 & 4.
- **J-94 / J-96 (`/data` universe diagnostic + rising membership-timeline step function w/ populated
  Entries/Exits + 3 honesty labels), J-93 (`/stocks` slides), J-36/J-37/J-39 (`/data` co-located surfaces),
  Dashboard cluster J-87/J-88/J-89/J-90/J-97/J-98/J-99:** LIVE re-verify, all numbers reconcile to pre-change
  values (J-06 single-source). → Definition of Done bullet 2.
- **J-18 (CRITICAL):** 0 native `input[type=date]`, no new date state (backend-only diff — trivially held,
  confirm). **J-07 (CRITICAL):** Risk-Off → 0 Actionable unchanged. → Definition of Done bullet 3.
- **No anti-goal violation:** byte-identity of every served value asserted; no magic number in the start
  script / cache code; no recompute in the read path. → Definition of Done bullet 4.
- **Standing green-suite gate:** full backend pytest flushes `0 failed, EXIT 0` (pump nohup-async). →
  Definition of Done bullet 5.
- **Dev handoff** at `docs/handoffs/goal-...-iter-42-dev.md`, including the (e) test-hygiene codification. →
  Definition of Done bullet 6.

## Key Test Scenarios
- **Concurrency load test (new, sanctioned concurrent probe):** K parallel `/api/data` calls all return
  within a configured latency bound; peak process RSS under the configured cap; `/health` latency stays low
  throughout (light endpoint NOT starved); served coverage deep-equals the single-request baseline
  (byte-identical); plus assert N probes cost ~1 heavy compute (single-flight COUNT), not N. Committed seed
  (offline). Mark seed-boot-heavy legs for the subagent-cap / pump split (iter-29).
- **Membership-stamp decoupling:** a forward-return-only insert does NOT invalidate the membership cache (HIT
  against an already-populated row); a snapshot add/remove DOES invalidate it.
- **Byte-identity:** `compute_coverage` and `membership_timeline_cached` output unchanged before/after the
  single-flight + reused-bar-cache change.
- **iter-37 J-46 invariant stays green:** `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once`
  (assert load COUNT == 1, not only value).
- **Error cases:** invalid `?as_of` to `/api/data` still falls back to the latest stored run date (descriptive
  coverage never 4xx); under the concurrency cap `/health` returns within a low bound while heavy probes are
  in flight; the memory cap OOM-kills ONE process (document the cap value + enforcement).
- **Additive-guard family stays green (no payload key added):** `test_db.py` expected-tables,
  `test_api_data.py::test_get_data_overview_shape` (already a SUPERSET compare since iter-33).
