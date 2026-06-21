# Goal Iteration 42 — J-100 bounded-resource backend hardening (single-flight + cached `/api/data`, byte-identical)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 42
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-100
- **Required-still-passing journeys:** J-18 (CRITICAL), J-07 (CRITICAL), J-06, J-96, J-94, J-93, J-36, J-37, J-39, J-87, J-88, J-89, J-90, J-97, J-98, J-99
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The scan is computed once per date (bootstrap, scheduled, or first view) and then read from storage. […] derived once per resolved as-of date […] persisted/cached, and read from storage — never recomputed per request […]. *(extends Single source of truth)*
  - **Vectorized scans are a pure refactor.** The memoized/vectorized backfill MUST produce identical [outputs] — a pure performance refactor, never a change to any canonical value.
  - **Coverage & missing-data are descriptive & honest.** The coverage figures, the per-symbol/per-universe-member table, and the insufficient-for-analysis diagnostic MUST be **read-only metadata derived from the stored bars + config** — they MUST NOT recompute or restate any canonical score, return, bucket, or setup. […] the **history threshold** […] and the trading calendar […] MUST come from config (`indicators.min_history_bars` and the benchmark-bar calendar) — **no magic number** in coverage/diagnostic code.
  - **Warm-up obeys every data invariant and is idempotent, concurrency-safe, and non-fatal.**
  - **Startup must not block serving on historical warm-up.** The boot path (FastAPI `lifespan`) MUST do [no blocking warm-up before serving].
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Exactly one date selector** (J-18). The single global as-of switcher is the only date control; no page-local or second date state. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation. *(critical)*

## GOAL

Under concurrent dashboard / goal-mode UI-test load the backend stays responsive and memory-bounded — the intermittent whole-VM freeze is eliminated — while every served coverage / membership value stays byte-identical to the pre-change output.

## BACKGROUND

J-100 is the LAST unbuilt buildable Must-have (iter-41 eval; goal.md:2312); after it lands green the next evaluation is a sound GOAL_ACHIEVED candidate. It is a **pure performance/stability property** — no canonical value changes — so depth is **full**: it touches the backend read path (`compute_coverage` / `membership_timeline_cached` / `prices` bar cache), the cache-key derivation, and the start script's server-concurrency/memory ops guards, and is gated by the full pytest suite plus a new concurrency load test. The iter-36 read-path fix already added a `MembershipTimelineCache` (table `membership_timeline_cache`, registered in `test_db.py`) keyed on `research._dataset_version` (`r{max_run_id}-f{fr_count}`) and warm-up precompute, which made the FIRST `/api/data` after boot a hit; J-100 hardens what remains: (a) `compute_coverage` still resolves `_resolved_universe` (~8 s warm) on EVERY call with no single-flight, so N concurrent probes cost N heavy computes (the documented pool-exhaustion / VM-freeze trigger); (b) the membership/coverage cache key's `f{fr_count}` term means warm-up's forward-return inserts churn the stamp and re-invalidate the membership cache (the recompute storm); (c) memory is a per-request prefill rather than one shared copy; (d) `start-backend.sh` has no `--limit-concurrency`, no heavy-endpoint timeout, and no process memory cap. This iteration is backend-only (Frontend Present: no) — the target journey is not a rendered surface but a measurable concurrency/byte-identity property — but the **required-still-passing rendered journeys (J-94/J-96/J-93/J-36/J-37/J-39 on `/data`, plus the Dashboard cluster) MUST be live-re-verified** so the optimization is proven not to change any served value. Closes open_item `iter35-api-data-timeline-uncached`.

## IN SCOPE

### Backend
- [ ] **(a) Single-flight + result cache around the coverage / membership compute.** Wrap `compute_coverage`'s heavy work (`_resolved_universe` + `membership_timeline_cached`) so concurrent `/api/data` callers for the SAME resolved as-of share ONE in-flight computation (or the already-cached payload) — reuse the SAME single-flight idiom the warm-up controller (`app.engine.warmup`) already uses (its in-process lock + "thread alive" guard). N parallel probes must cost ~one compute, not N. The served coverage payload MUST be byte-identical to today's single-request output.
- [ ] **(b) Decouple the membership/coverage cache key from forward-return churn.** Today `membership_timeline_cached` keys on `research._dataset_version` = `r{max_run_id}-f{fr_count}`; the `f{fr_count}` term invalidates the membership cache on every warm-up forward-return insert. Introduce a **membership-specific dataset stamp** that depends ONLY on the inputs membership actually reads (the bars manifest + the snapshot/`ScannerRun.asof_date` set + the relevant config), NOT the `forward_returns` row count — so warm-up's forward-return inserts STOP invalidating it (no recompute storm). This is a single-source refinement: the new stamp must change on a real backfill/removal/J-85 rebuild (the cases that DO change membership) and NOT on a pure forward-return insert. Keep `research._dataset_version` (the J-72/J-87 event-study/market-phase stamp) UNCHANGED — only the membership cache adopts the narrower stamp. A committed test must assert a forward-return-only insert does not invalidate the membership cache, and a snapshot add/remove DOES.
- [ ] **(c) Reuse one process-level bar cache (load-once, invalidate-on-data-change).** The read path for `_resolved_universe` + the membership timeline must reuse a single process-level bar cache (the existing `app.engine.prices` `attach_shared_cache` / `bar_cache` / `prefilled_bar_cache` machinery) rather than building a fresh ~1.3M-`DailyPrice` prefill per request, bounding memory to one copy regardless of concurrency; the shared cache invalidates on a real data change (the same data-change signal the membership stamp uses). Preserve the iter-37 J-46 load-once-per-job invariant (zero-bar candidate-pool symbols recorded as an empty series up front; assert load-COUNT, not only value — iter-37 lesson).
- [ ] **(d) Cap server concurrency + a heavy-endpoint timeout + a process memory cap in `scripts/start-backend.sh`.** Add uvicorn `--limit-concurrency` (a config-/env-sourced bound, no magic literal in the script) and a request timeout on the heavy `/api/data` path so `/health` + light reads stay responsive under load; run the backend process under an explicit memory cap (`ulimit -v` / cgroup / systemd `MemoryMax`, whichever is portable on this host) so a pathological spike is OOM-killed as ONE process, never a swap-thrash freeze of the whole VM. If heavy synchronous compute is not already off the event loop, offload it to a worker thread (`run_in_threadpool` / `to_thread`) — note `/api/data` is currently a sync `def`, which FastAPI already runs in the threadpool, so verify before adding redundant offloading (Simplicity First — do not add an abstraction that already exists).
- [ ] **(e) Codify test hygiene.** Document/enforce in the iteration's QA + handoff that `/api/data` is **single-loaded, never concurrently probed** during normal QA (the MEMORY pool-exhaustion lesson), with the `.pump-alive` toucher + `CHAIN_PUMP_HEARTBEAT_TIMEOUT` / `CHAIN_DISPATCH_INFLIGHT_TIMEOUT` envs for the long full-suite run. The single-flight (a) is what makes the load test's K concurrent probes safe — the load test is the ONE sanctioned concurrent probe.
- [ ] **Concurrency load test (new test).** Assert: K parallel `/api/data` calls all return within a bound; peak process RSS stays under a configured cap; `/health` latency stays low throughout the load; the served coverage equals the single-request baseline (byte-identical, deep-compared); and warm-up forward-return inserts do NOT invalidate the membership cache. Use the committed seed (offline). Mark seed-boot-heavy legs appropriately so the subagent Bash cap / the pump split applies (iter-29 lesson).

### Frontend (if applicable)
- None. Backend-only; no frontend file changes. (If a frontend diff appears, it is out of scope and a coherence/IA red flag.)

### New user-facing capability
None new. The user-visible effect is the ABSENCE of a defect: `/data` and the Dashboard stay responsive (no whole-VM freeze) under concurrent use, with identical numbers.

### New information displayed
None. Every served `coverage` / `membership_timeline` / `universe_diagnostic` value is byte-identical to today.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
The product becomes operationally robust under concurrent load — the intermittent freeze that blocked QA on a many-run host is eliminated — with zero change to any displayed figure.

### Blueprint conformance
No new surfaces. J-100 is a cross-cutting backend performance/stability property on the EXISTING `data_manager._membership_timeline` → `compute_coverage` → `GET /api/data` canonical source (blueprint Data Contract line 385, where the J-100 hardening is now registered as an additive performance annotation). No nav-skeleton change, no new page, no new IA home — so no blueprint re-approval is required.

### Data-contract additions
None — J-100 introduces NO new displayed value and NO new endpoint. It adds only an internal cache KEY refinement (a membership-specific dataset stamp), a single-flight wrapper, a reused process-level bar cache, and ops guards around the EXISTING registered canonical source. The served `membership_timeline` / `coverage` payload stays byte-identical. (The membership-specific stamp is an internal cache-invalidation input, not a served value — it appears in no payload.) If the implementation adds a new `table=True` SQLModel for the new cache (it should NOT need one — `membership_timeline_cache` already exists), it MUST be added to `test_db.py`'s expected-tables guard (iter-12/20/21 trap).

## OUT OF SCOPE

- Any change to a canonical score, return, bucket, setup status, regime, membership, the Risk-Off→Actionable gate, or `_dataset_version` (the J-72/J-87 stamp) — strictly forbidden; every served value stays byte-identical.
- Re-triggering the J-85 `kind:rebuild` (~11 h destructive; the data is correct — MEMORY lesson).
- Any resolver-math / scoring / forward-testing logic change (J-100 is delivery-only, not math).
- Any frontend change.
- The descoped FULL `/api/data` coverage-block cache beyond what (a)–(c) require for responsiveness — keep the change minimal (Surgical Changes); do not gold-plate a general cache layer the journey does not ask for.

## DEFINITION OF DONE

- [ ] J-100 verified: a committed concurrency load test asserts K parallel `/api/data` calls return within a bound, peak RSS under the configured cap, `/health` low-latency throughout, and the served coverage byte-identical to the single-request baseline; plus a test that warm-up forward-return inserts do NOT invalidate the membership cache.
- [ ] Required-still-passing rendered journeys remain green on LIVE evidence: J-94 + J-96 (`/data` universe diagnostic + rising membership-timeline step function with populated Entries/Exits + 3 honesty labels), J-93 (`/stocks` still slides), J-36/J-37/J-39 (co-located `/data` surfaces), and the Dashboard cluster J-87/J-88/J-89/J-90/J-97/J-98/J-99 — all numbers reconcile to the pre-change values (J-06 single-source).
- [ ] CRITICAL invariants hold: J-18 (0 native `input[type=date]`; no new date state — backend-only diff, trivially held but confirm), J-07 (Risk-Off → 0 Actionable).
- [ ] No anti-goal violation introduced (byte-identity of every served value asserted; no magic number in the start script / cache code; no recompute in the read path).
- [ ] Full backend pytest suite flushes `0 failed, EXIT 0` (the standing GOAL_ACHIEVED gate) — handed to the pump nohup-async; the evaluator is gated on the FLUSHED terminal line, NOT the in-flight stream.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-42-dev.md`.

## TESTING REQUIREMENTS

- **Browser (live, on this host — PLAN THE PLAYWRIGHT FALLBACK UP FRONT; Chrome MCP CDP has emptied the evidence dir on iters 38/39, escaped via Playwright on 34/37/40):** J-94, J-96, J-93, J-36, J-37, J-39 on `/data`/`/stocks`; J-87, J-88, J-89, J-90, J-97, J-98, J-99 on the Dashboard + `/data`; J-18 (0 native date inputs), J-07 (Risk-Off → 0 Actionable). **Single-load `/api/data`** during QA (~30 s hydration wait); **never concurrently probe `/api/data`** outside the load test (MEMORY pool-exhaustion lesson). `md5sum` the evidence dir FIRST; reject any un-hydrated skeleton or byte-identical "before/after" frame; scroll the below-the-fold `/data` membership-timeline + diagnostic into the viewport and VIEW the pixels (iter-18/33).
- **Unit/integration:** the new concurrency load test (K parallel `/api/data` → bounded latency, bounded RSS, `/health` responsive, coverage byte-identical to baseline); the membership-cache-not-invalidated-by-forward-return-inserts test (and invalidated-by-snapshot-add/remove); a byte-identity assertion that `compute_coverage` (and `membership_timeline_cached`) output is unchanged before/after the single-flight + reused-bar-cache change; the iter-37 J-46 load-COUNT invariant (`test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once`) stays green (assert load count, not only value).
- **Error cases:** an invalid `?as_of` to `/api/data` still gracefully falls back to the latest stored run date (descriptive coverage never 4xx); under the concurrency cap, light endpoints (`/health`) MUST NOT be starved (assert `/health` returns within a low bound while heavy probes are in flight); the memory cap OOM-kills ONE process, never freezes the VM (document the cap value + how it is enforced).

## NOTES

- **Standing GREEN-suite gate (iter-11/29/37 lessons).** This is a GOAL_ACHIEVED-candidate iteration, so the FULL backend suite must flush `0 failed, EXIT 0`. Hand it to the pump nohup-async; NEVER block the evaluator on the in-flight suite. On this 1369-run host, seed-boot `loaded_engine`-style tests cannot finish under a subagent Bash cap — split fast (no-boot) vs slow (seed-boot) and verify anti-goal legs via the fast set, then require the flushed terminal line from a nohup full suite via the pump (iter-29). Re-run any single `test_warmup.py` / `test_data_manager_jobs_pipeline.py` `F` in ISOLATION before attributing it to this iteration — those are the documented scanner_runs-race / slow-boot / warm-up-contention flakes, not regressions (iter-30/34/36).
- **Additive-trips-blanket-guard family (iter-20/21/23/24/32 lessons).** This iteration should add NO key to any served payload, so the `set(payload)==` / `served==score_*` / expected-tables guards SHOULD stay green. The `iter32-stale-data-overview-shape` guard (`test_api_data.py::test_get_data_overview_shape`) was already reconciled to a SUPERSET compare in iter-33, so the `macro` key no longer fails it — verify it stays green. If the new cache needs a new `table=True` model (it should reuse the existing `membership_timeline_cache`), add it to `test_db.py` expected-tables in the SAME iter.
- **Cached-payload schema-version trap (iter-38/39 lessons).** This iteration changes the membership cache KEY (the (b) decoupling). Verify the new key correctly invalidates on a real membership change and correctly HITS across forward-return churn — unit-test against an ALREADY-POPULATED cache row (a real HIT), never a fresh compute that masks a stale-cache bug; probe the LIVE current as-of (a cache HIT), not a fresh-compute date.
- **Byte-identity is the contract (iter-35/36/37 lessons).** The iter-35 regression was a correct DATA growth exposing a latent O(dates×pool) read cost; iter-36/37 fixed it but iter-37 caught (via the full suite) a load-COUNT regression the value-equality tests missed. For J-100: pair every "byte-identical served value" claim with the load/compute-COUNT invariant it preserves (single-flight ⇒ N probes cost ~1 compute — assert the compute count, not only the values).
- **Backend-only render-evidence trap (iter-36/39 lessons).** Frontend Present is `no`, so framework browser-QA may AUTO-SKIP — but the required-still-passing journeys are RENDERED pages, and the whole point is to prove the optimization changed no served value. The `Frontend Present: yes`-to-force-browser-QA workaround does NOT apply cleanly here (there is genuinely no frontend diff), so the QA/browser-qa step MUST be explicitly run for the live re-verify of J-94/J-96/J-93 + the Dashboard cluster; if the framework auto-skips on the `no` flag, a lean live re-verify follows next iter (the iter-36→37 pattern). Do NOT flip any required journey to "still passing" on API-layer byte-identity alone — confirm the rendered numbers live.
- **Reference (evaluator feedback that drove this scope):** iter-41 eval Next-Step Recommendation (this is the last unbuilt buildable Must-have); open_items `iter35-api-data-timeline-uncached` (the perf root cause closed here) and `iter32-stale-data-overview-shape` (already reconciled — confirm green). Do NOT mark J-22/J-23/J-24 anything but blocked-NA (data-walled, non-vetoing per goal.md:105-108).
- **Decomposer notes (no code written here):** the `MembershipTimelineCache` table + `membership_timeline_cached` + warm-up precompute already exist (iter-36, `apps/backend/app/engine/data_manager.py:545`); the per-request residual cost is `compute_coverage`'s `_resolved_universe` resolve (`data_manager.py:635`) + the cache lookup. The membership-stamp decoupling targets `research._dataset_version` (`research.py:1229`, the `f{fr_count}` term). The start-script ops guards target `scripts/start-backend.sh` (currently bare `uvicorn main:app`, no `--limit-concurrency`). Keep the change minimal and surgical.
