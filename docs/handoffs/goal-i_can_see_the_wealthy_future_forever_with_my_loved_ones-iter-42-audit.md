# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-42 Audit Report

**Date:** 2026-06-21
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-100 (bounded-resource backend hardening) is genuinely implemented, not merely claimed. The four
scope items — single-flight + result cache around `compute_coverage` (a), a narrow membership-cache stamp
decoupled from forward-return churn (b), a reused re-entrant process-level bar cache (c), and config-sourced
ops guards in `start-backend.sh` (d) — were each verified by reading the actual code and by independently
re-running the J-100 tests (72 tests green locally during this audit, including the load test K=12→≤2 heavy
computes byte-identical, the FR-decoupling HIT-against-a-populated-row test, the J-46 load-COUNT invariant,
and the full config/expected-tables/overview-shape guard family). Two non-blocking gaps remain: the full
pytest suite's *flushed* `0 failed, EXIT 0` terminal line is not yet captured in the artifacts (the log
stops at 98% mid-`test_warmup.py` with 976 passed / 0 failed / 0 error — the documented pump nohup-async
gate), and the rendered required-still-passing journeys were browser-skipped (backend-only auto-skip),
deferred to a lean live re-verify per the iter-36→37 pattern. Byte-identity of every served value is proven
at the compute layer, so no displayed number can have changed; the live render check is confidence-building,
not load-bearing.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (verified): Single-flight (a) is correct, deadlock-free, and byte-identical.**
`apps/backend/app/engine/data_manager.py:691-746`. The owner/waiter pattern is sound: the first caller for a
key registers an unset `threading.Event` under `_COVERAGE_LOCK`, computes `_compute_coverage_uncached`
OUTSIDE the lock (so the ~8 s resolve never holds the global lock), publishes the payload, and `finally`
pops the in-flight slot + sets the event. Waiters `event.wait()` then return a `copy.deepcopy` of the cached
payload (so a caller mutating its result cannot corrupt the shared entry). The defensive fall-through (owner
raised → no cached payload → waiter recomputes) is correct and cannot deadlock. The cache is bounded
(`_COVERAGE_CACHE_MAX_KEYS = 8`, oldest-key prune). Independently re-ran
`test_concurrent_coverage_single_flight_byte_identical_and_bounded`: K=12 concurrent probes → ≤2 heavy
computes, every payload deep-equals the single-request baseline, light read responsive, RSS bounded. No fix
needed.

**B2 — OBSERVATION (verified): Cache key is consistent with the body's resolution.**
`data_manager.py:679-688` (`_coverage_cache_key`) resolves the as-of via `_resolve_coverage_asof` — the SAME
helper `_resolved_universe` (`:330`) uses inside the body — so `None`-falls-back-to-latest and explicit-latest
map to one key, and two callers share a compute iff they would produce the byte-identical payload. The key
also folds the bound DB URL (`_db_identity`, guarding the tmp-DB cross-serve class) and a full-config
fingerprint (`_config_fingerprint`, guarding the thin-threshold/filter class the membership stamp alone would
miss). Correct and defensive.

**B3 — OBSERVATION (verified): Narrow membership stamp (b) is truly decoupled from forward-return churn.**
`apps/backend/app/engine/research.py:1247-1295`. `_membership_dataset_version` depends on `max(scanner_runs.id)`
+ `count(scanner_runs)` + `max(daily_prices.date)` + `count(daily_prices)` + `indicators.min_history_bars` —
and references NO `ForwardReturn`. `_dataset_version` (the J-72/J-87 broad stamp, `:1229`) is UNCHANGED and
still folds `fr_count`. I confirmed this at the source level during the audit (broad stamp folds `fr_count`:
True; narrow stamp references `ForwardReturn`: False). `membership_timeline_cached` (`data_manager.py:571`)
adopts the narrow stamp; warm-up writes under it (`warmup.py`, comment-only change — behaviorally inherited).

**B4 — OBSERVATION (verified): Reused bar cache (c) preserves the J-46 load-once invariant.**
`_compute_coverage_uncached` (`data_manager.py:759-794`) wraps the whole derivation in one
`prefilled_bar_cache(session, expected_symbols=pool_symbols)`. The inner `_membership_timeline` (`:523`)
opens its own `prefilled_bar_cache` with the SAME `pool_symbols = {row["symbol"] for row in read_pool()}`;
`bar_cache` is re-entrant keyed by `id(session)` (`prices.py:172-188` — nested context yields the existing
cache, only the outermost clears it) and `prefill` skips already-loaded symbols (`prices.py:89`), so the
inner prefill is a no-op. Load-once holds. `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once`
re-run green during the audit (load-COUNT assertion, not only value).

**B5 — OBSERVATION (verified): Ops guards (d) carry no magic number and load cleanly.**
`scripts/start-backend.sh:38-64` reads `limit_concurrency` / `timeout_keep_alive_seconds` /
`graceful_timeout_seconds` / `memory_cap_mb` from `config.server` via the venv python (env `CHAIN_SERVER_*`
overrides win), applies `ulimit -v` (KiB conversion `*1024` is a unit factor, not a tunable) `|| true` (a
stricter inherited hard cap is respected), and passes the three uvicorn flags. No concurrency/timeout/memory
literal lives in the script. `ServerOpsCfg` (`config.py:481-521`) validates every value positive and is
default-populated, so configs/fixtures predating it load unchanged (`test_config.py` re-run green during the
audit). Verified the live config read returns `64 65 120 6144`.

### Frontend Findings

**F1 — OBSERVATION: No frontend diff, as required.** Backend-only iteration (Frontend Present: no). Git
status shows zero frontend file changes; the user-visible-changes report correctly reports N/A. No
coherence/IA red flag (a frontend diff here would have been one).

### Test Findings

**T1 — OBSERVATION (verified): J-100 tests have tight, load-bearing assertions.**
`test_data_manager_concurrency_load.py` asserts byte-identity (deep-equal vs single-request baseline),
single-flight COUNT (`heavy_calls["n"] <= 2` for K=12), zero-recompute on a warm cache (patches
`_compute_coverage_uncached` to raise), bounded latency, light-read non-starvation, and bounded RSS.
`test_data_manager_membership_cache.py::test_forward_return_insert_does_NOT_invalidate_membership_cache`
proves the decoupling against an ALREADY-POPULATED cache row with `_membership_timeline` patched to blow up
(the iter-38/39 cached-payload discipline — a real HIT, not a fresh compute that would mask a stale-cache
bug), and `test_bar_backfill_DOES_invalidate_membership_cache` proves the stamp is not so narrow it misses a
real change. Independently re-ran all 12 — passed in 7.74 s.

**T2 — GAP (not fixed — documented): The full-suite flushed terminal line is not in the artifacts.**
`reports/qa/...-iter-42-test.log` stops at 98% mid-`test_warmup.py::test_ensure_latest_persists_only_latest_before_warmup`
with **976 PASSED / 0 FAILED / 0 ERROR / 4 SKIPPED** and no terminal `=== passed ===` summary. This is the
standing GREEN-suite gate (Definition of Done bullet 5), which on this 1369/1371-date host is a ~3.5 h
nohup-async run the pump owns and the goal-evaluator reads the flushed line from — it cannot finish under a
subagent Bash cap, so the auditor cannot force it to completion. The captured portion has zero failures; the
remaining ~2 % is the documented seed-boot/flake `test_warmup.py` module, whose only iter-42 change is the
warmed-cache row-version assertion correctly re-pointed to the narrow stamp (logically required — without it
the test would fail). Not a defect in the implementation; a verification-evidence gap the pump closes.

**T3 — GAP (not fixed — documented): Rendered required-still-passing journeys were browser-skipped.**
QA TC-07..TC-10, TC-12 (J-94/J-96 on `/data`, J-93 on `/stocks`, the Dashboard cluster J-87..J-99, J-07) are
marked SKIPPED — the framework auto-skipped browser-QA on `Frontend Present: no`. Byte-identity of every
served `coverage` / `membership_timeline` / `universe_diagnostic` value is proven at the compute layer
(B1/T1) and no payload key was added, so no rendered number can have changed; J-07 (Risk-Off → 0 Actionable)
holds at the API layer per the suite. Per the explicit iter-36→37 pattern the plan/handoff planned for, a
lean live re-verify of the rendered numbers follows next iteration. Not load-bearing for byte-identity, but a
genuine deferral — do NOT silently treat these as "freshly live-verified this iter."

---

## 3. Domain Assessment

The core property J-100 asserts is a *negative* one — the absence of the intermittent whole-VM freeze under
concurrent `/api/data` load — coupled with a *strict invariant*: every served value stays byte-identical. The
implementation attacks the documented root cause precisely. Before this iteration, `compute_coverage`
resolved `_resolved_universe` (~8 s warm, each holding a DB connection ~10 s) on EVERY request with no
single-flight, so N concurrent probes cost N heavy resolves and exhausted the pool (size 5 + overflow 10) —
the pool-exhaustion / swap-thrash trigger. The single-flight (a) collapses N same-key probes to ~1 compute
(load-test proven), the narrow stamp (b) stops the warm-up's forward-return inserts from churning the
membership cache (the recompute storm), the reused re-entrant bar cache (c) bounds memory to one shared copy,
and the ops guards (d) cap concurrency/memory so a pathological spike is OOM-killed as one process. Crucially,
nothing in the diff touches a canonical score, return, bucket, setup, regime, membership set, the
Risk-Off→Actionable gate, or `_dataset_version` — the change is delivery-only, and byte-identity is asserted
by deep-equality against the single-request baseline rather than merely claimed. The membership-stamp
decoupling is the one piece with real correctness subtlety (a too-narrow stamp would serve stale membership
after a real change); it is correctly scoped to membership's actual inputs and is tested in BOTH directions
(FR-insert HITs, snapshot/bar add INVALIDATEs) against a populated cache row. The domain logic is sound and
the scope did not drift.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | None. No CRITICAL or IMPORTANT issue was found. The two remaining items (T2 full-suite flushed line, T3 live render re-verify) are GAPs that are out of the auditor's reach (the ~3.5 h pump suite cannot finish under a subagent cap; the live re-verify is a deferred next-iter step) and are documented above, not fixed. |

---

## 5. Recommended Next Step

Proceed — with two closure conditions handed to the pump/evaluator, not blockers on this iteration:

1. **Confirm the flushed full-suite terminal line** `0 failed, EXIT 0` from the pump's nohup-async run before
   the goal-evaluator declares GOAL_ACHIEVED (DoD bullet 5). The captured evidence is 976 passed / 0 failed
   up to the documented `test_warmup.py` seed-boot legs; re-run any isolated `test_warmup.py` `F` in isolation
   before attributing it to this iteration (known scanner_runs-race / slow-boot / warm-up-contention flake).
2. **Lean live re-verify next iter** of the rendered required-still-passing clusters (J-94/J-96 on `/data`,
   J-93 on `/stocks`, J-87..J-99 on the Dashboard) against the pre-iter-42 baseline — confirming the rendered
   numbers match (byte-identity already proven at the API/compute layer). Plan the Playwright fallback up
   front (Chrome MCP CDP has emptied the evidence dir on iters 38/39/40); single-load `/api/data`, never
   concurrently probe it outside the sanctioned load test.

J-100 is the last unbuilt buildable Must-have; with the flushed green suite confirmed, this iteration is a
sound GOAL_ACHIEVED candidate. J-22/J-23/J-24 remain correctly blocked-NA (data-walled, non-vetoing).
