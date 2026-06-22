# Goal Iteration 47 — Bounded/streamed forward-return read path so the heavy Research labs serve on the full live dataset without MemoryError (J-105; closes the iter-46 J-25/J-26/J-29 regression)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 47
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-105, J-29, J-25, J-26
- **Required-still-passing journeys:** J-104, J-77, J-91, J-90, J-63, J-32, J-51, J-65, J-72, J-06, J-18, J-07
- **Resume flag:** `--acknowledge-regression` (the prior verdict was REGRESSION; this iteration is its authorized fix)
- **Anti-goal reminders:**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The relocated as-of-scoped evidence aggregate is likewise derived once per resolved as-of date, persisted/cached, and read from storage — never recomputed per request.
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. *(critical)*
  - **No fabricated data.** On a data-provider/compute failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Honest forward-test for partial windows.** Show NA/partial for horizons/cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate a return to fill a gap.
  - **No magic numbers.** Every scoring weight, threshold, cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated/overwritten; forward returns live in a separate append-only table keyed to the snapshot.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*

## GOAL

Make the heavy Research labs (Setup & Pattern event-study, Factor Lab, Multi-factor combination, Regime × Setup × Pattern, Downtrend Opportunity) and their `N=` samples drill-downs serve HTTP 200 on the full live `forward_returns` table within bounded memory — by streaming column-projected rows instead of materializing the whole table as ORM objects — with every served figure byte-identical, restoring J-25/J-26/J-29 (and J-104's "labs load reliably") to passing.

## BACKGROUND

The iter-46 verify-only pass (ZERO source diff) surfaced and the evaluator independently reproduced a genuine REGRESSION: `_event_study_members_by_horizon` (apps/backend/app/engine/research.py:823 — `select(ForwardReturn).where(horizon.in_(horizons)).all()`) materializes the entire `forward_returns` table as ORM objects and MemoryErrors on the live 3.3 GB / 3,081,454-row DB (peak RSS ~5,466 MiB in 172 s on a host whose available RAM oscillates 3–16 GiB). Three previously-`passing` Must-haves (J-25, J-26, J-29) now return an honest HTTP 500 / "Backend unavailable", and J-104's "labs load reliably" acceptance is `partial` (5/7 labs serve). The unbounded `.all()` is byte-identical since iter-20 (6733c1d) — the regression was exposed by data growth (the J-85 rebuild + restored daily-history backfills) plus a dropping host RAM ceiling, not by code. `docs/goal.md` now carries the new Must-have **J-105** (goal.md:2379-2388) authored specifically to close this: a bounded-memory / streaming read-path refactor with byte-identical figures, explicitly NOT data-dependent and non-halting. The evaluator recommended FULL depth; this is a backend data-read-path change on a regression that needs deep-equality + load verification beyond a browser smoke, so depth is **full**.

This iteration is set `Frontend Present: yes` deliberately (iter-36/39/42/43 + iter-45/46 lessons): although the diff is backend-only, the J-29/J-25/J-26 acceptance is a RENDERED lab loading live, and a `Frontend Present: no` iteration would AUTO-SKIP browser-QA — forcing yet another lean live-re-verify round-trip. The Playwright fallback MUST be planned UP FRONT (Chrome MCP CDP has emptied the evidence dir on iters 38/39/40/42; escaped only when Playwright was pre-planned, iters 34/37/40/43) and the labs MUST be re-captured on a FRESHLY-RESTARTED, WARMED, single-fetch-at-a-time backend (iter-45/46 lesson: a hung/saturated live backend produces "Backend unavailable"/"Loading…" false-negatives indistinguishable from a real defect).

## IN SCOPE

### Backend
- [ ] In `apps/backend/app/engine/research.py`, replace the unbounded `select(ForwardReturn)…all()` ORM materialization with a **column-projected, `yield_per`-streamed** read bounded to the cohort each study needs, in the per-observation builders that feed the heavy labs — the primary culprit `_event_study_members_by_horizon` (research.py:823/828) AND its per-horizon siblings that share the same shape (the `select(ForwardReturn).where(horizon == …).all()` reads at ~research.py:196/201, 392/397, 759/764, 1408/1413, 1633/1637, 2232/2239). Project to the lightweight tuple of fields the join + member shape actually consume (e.g. `horizon, run_id, symbol, realized_return, mae, mfe, max_drawdown`) rather than full `ForwardReturn` ORM rows. Where the cohort is subject-/factor-/horizon-scoped, push that filter into the SQL scan so the stream only yields rows the study reads.
- [ ] In `apps/backend/app/engine/forward_testing.py`, replace the warm-up idempotency-set materialization `existing = {(fr.run_id, fr.symbol, fr.horizon) for fr in session.exec(select(ForwardReturn)).all()}` in `_backfill_all_runs` (forward_testing.py:379-380) with a **streamed, key-projected** scan (`select(ForwardReturn.run_id, ForwardReturn.symbol, ForwardReturn.horizon)` consumed with `yield_per`) so `backfill_forward_returns` (reached from the warm-up daemon, warmup.py:155) no longer peaks on a full-table ORM load. Per-run idempotency reads already scoped by `run_id` (forward_testing.py:865-867, :907-908) are bounded and may stay as-is unless they share the unbounded shape.
- [ ] Add ONE new config key `research.read_batch_size` (an integer `>= 1`, validated at boot in `apps/backend/app/config.py` `ResearchCfg` exactly like `startup.warmup_batch_size` / `chunking.symbol_batch_size`), set it in `config.yaml` under the `research:` block, and read it for every `yield_per(...)` batch size — NO inline numeric literal in calculation code (anti-goal: No magic numbers; the existing `test_no_magic_numbers` guard will reject a raw batch literal). Add the new key to every inline test config fixture that constructs a `ResearchCfg`/full config dict (grep the config section key across `apps/backend/tests` — the lesson "config fixtures need new required keys" applies; the count grows over time, do not trust a fixed list).
- [ ] Preserve the documented **byte-identity contract** of `_event_study_members_by_horizon` and siblings: the returned `{horizon: [members]}` (member dict shape, enrichment, and insertion order — `ScannerResult.id` ascending) MUST be byte-identical per horizon to the prior implementation, across `as_of=None` (all-history) and `as_of` (≤ D scoping). The stream must preserve the exact ordering the prior `.all()` + `order_by(ScannerResult.id)` produced.

### Frontend (if applicable)
- [ ] No frontend source change is expected (the labs already render the served aggregates). `Frontend Present: yes` is set ONLY to force the live browser-QA render-capture step on the relocated labs in this same iteration — do NOT edit frontend files unless a genuine render defect is found during QA.

### New user-facing capability
The five heavy Research labs and their `N=` samples drill-downs load successfully on the full live dataset again (event-study, factor-lab, factor-combination, regime×setup×pattern, downtrend-opportunity) instead of showing "Backend unavailable"/"Loading…". No new feature — a restored capability.

### New information displayed
None. Every matrix cell, mean/win-rate/N, and every `N=` cohort is byte-identical to before.

### New user actions
None.

### UI surface changes
None — the `/research` hub and its `/research/*` sub-routes (built iter-45) are unchanged.

### Product surface delta
The product stops failing under its own data weight: research evidence that MemoryError'd on the grown live DB now serves reliably and identically, on the existing pages.

### Blueprint conformance
No new surfaces. The relocated heavy labs keep their existing Information-Architecture homes under **Research** (`/research/event-study`, `/research/factor-combination`, `/research/regime-setup-pattern`, `/research/downtrend-opportunity`, and the factor-lab on `/research`) registered at the iter-45 route-split. The blueprint's Event Study IA line and the Data Contract have been additively annotated with the J-105 bounded read-path property (same routes, same endpoints, same canonical values — a memory-safety refactor, not a new value). No nav-skeleton change → no `blueprint.reapproval-requested`.

### Data-contract additions
None — no new displayed value. `forward_returns` and all research aggregates are already-registered canonical Data-Contract values, read from their canonical sources. The ONLY new artifact is the config key `research.read_batch_size` (a streaming batch size, not a displayed value). The fix introduces **NO new `table=True` model** — J-105 explicitly "adds no table", so the `test_db.py` expected-tables guard stays UNCHANGED (the iter-20/iter-21 new-table trap does NOT apply here).

## OUT OF SCOPE

- Re-triggering the J-85 `kind:rebuild` (~11h, destructive; the data is correct — never re-trigger for QA).
- Any change to a canonical score / return / membership / aggregate value, or to the Risk-Off→Actionable gate.
- Adding a new endpoint, a new stored column, or a new `table=True` model.
- The J-84 cookie+crumb real-provider fetch / J-22/J-23/J-24 data-walled work (unchanged blocked-NA, non-vetoing per goal.md:105-108).
- Frontend feature edits (this is a backend read-path refactor; frontend is touched only if QA finds a genuine render defect).

## DEFINITION OF DONE

- [ ] Target journeys J-105, J-29, J-25, J-26 pass via browser-qa-agent on REAL rendered figures (event-study matrix, factor-lab decile/rank-IC + multi-factor composite, each with a working `N=` drill-down) — captured on a freshly-restarted, warmed, single-fetch-at-a-time backend; reject "Loading…"/"Backend unavailable"/skeleton frames.
- [ ] Required-still-passing journeys remain green (J-104 "labs load reliably" now MET for all 5 heavy labs; J-77/J-91/J-90/J-63/J-32/J-51/J-65/J-72 figures + drill-downs byte-identical; J-06/J-18/J-07 CRITICAL invariants intact).
- [ ] No anti-goal violation introduced — byte-identity proven (Single source of truth / No recompute / No lookahead / Honest partial windows), `research.read_batch_size` config-sourced (No magic numbers), no order/execution path.
- [ ] Unit tests pass; no regressions. The FLUSHED full backend suite reaches `0 failed, EXIT 0` (nohup-async via the pump; never block the evaluator on the in-flight suite; re-run any isolated `test_warmup.py`/`test_watchlist_persistence.py`/`test_data_manager_jobs_pipeline.py` E/F before attributing — the documented slow-boot/warm-up contention flake).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47-dev.md`.

## TESTING REQUIREMENTS

- **Browser (live, Playwright fallback planned UP FRONT; md5sum the evidence dir FIRST; one heavy fetch per page):**
  - J-29 — `/research/event-study`: event-study matrix renders REAL per-horizon mean/win-rate/N cells (not a skeleton); a `N=` chip drills into count-coherent `/research/samples`.
  - J-25 — `/research` Factor Lab: decile sort + rank-IC per factor render REAL figures; `N=` drill-down works.
  - J-26 — Factor Lab multi-factor composite cohort renders REAL figures.
  - J-105 — all five heavy labs + their `N=` drill-downs return HTTP 200 on the full live dataset; verify each renders figures and capture the rendered pixels.
  - Required-still-passing live smoke: J-77 (regime×setup×pattern), J-91 (downtrend-opportunity), J-90 (recovery-turn-edge), J-32 (As-of⇄All-history toggle), J-51/J-65 (`N=` count-coherence), J-06 (single source: NVDA detail == leaderboard), J-18 (0 native `input[type=date]`), J-07 (Risk-Off → 0 Actionable).
- **Unit/integration (offline, against the committed seed — the byte-identity is seed-verifiable):**
  - A **deep-equality** test asserting the bounded/streamed `_event_study_members_by_horizon` (and the per-horizon siblings) returns output byte-identical to the prior per-observation reference across: `as_of=None` (all-history) AND a historical `as_of` (≤ D scoping); pooled AND episodes views; and a zero-N cohort. Drive the REAL builder/endpoint, not a hand-rolled stand-in (iter-15 lesson).
  - `test_research.py` + `test_samples.py` count-coherence MUST stay green (J-29/J-63/J-51/J-65) — each figure's reported N still equals its `N=` samples drill-down.
  - A test that `_backfill_all_runs` / `backfill_forward_returns` builds the SAME idempotency set and inserts 0 duplicate rows after the streamed-key change (idempotency + INSERT-only contract preserved).
  - `research.read_batch_size` validated `>= 1` at boot; `test_no_magic_numbers` green (batch size config-sourced, no inline literal in CALC_FILES); `test_db.py::test_create_all_produces_expected_tables` green and UNCHANGED (no new table).
- **Error cases:**
  - A genuine compute fault still surfaces an honest error / unavailable state — never fabricated figures (No fabricated data).
  - A horizon/cohort lacking enough samples shows NA/partial with sample size — never an extrapolated return (Honest forward-test for partial windows).
  - An invalid `view`/`horizon`/cohort param is still rejected (no 4xx on a displayable `N=` cell — the J-82 count-coherence contract).

## NOTES

- **Lessons applied (surface to dev/reviewer/evaluator):**
  - *iter-46 (the regression being fixed):* an unbounded `.all()` / full-table ORM materialization over `forward_returns` is the exact defect — replace with column-projected `yield_per` streaming bounded to the cohort; verify the read path against the LIVE data volume, not just fixtures, before claiming done.
  - *iter-37:* an optimization justified by "byte-identical served value" can still silently break a load/compute-count or ordering invariant — pair the value-equality (deep-equality) assertion with the byte-identity-of-ordering and the backfill idempotency-count assertion; only the FLUSHED full suite caught the iter-36 load-count break.
  - *iter-20/21:* the full suite has guard tests targeted module runs miss — `test_no_magic_numbers` (the batch size MUST be config-sourced, no inline literal in CALC_FILES) and `test_db.py` expected-tables (here UNCHANGED — J-105 adds no table; do NOT register a new table). "Config fixtures need new required keys": add `research.read_batch_size` to EVERY inline test config dict (grep the section key across `apps/backend/tests`; the count grows).
  - *iter-45/46:* heavy-research browser-QA MUST run on a freshly-restarted, warmed, single-fetch-at-a-time backend — a hung/saturated backend yields "Backend unavailable"/500/timeout false-negatives. KILL any stale uvicorn first; wait for `GET /api/health` "ready"; NEVER concurrently probe heavy `/research/*` (the J-104 one-heavy-fetch-per-page invariant; the MEMORY pool-exhaustion lesson). When a curl-based "ignores param" FAIL appears, verify the EXACT query-param spelling (`as_of`, with underscore) before trusting it.
  - *iter-36/39/42/43:* `Frontend Present: yes` is set on this backend-only change precisely so browser-QA does NOT auto-skip and the J-29/J-25/J-26 render evidence is captured in THIS iteration; plan the Playwright fallback up front (Chrome MCP CDP keeps emptying the dir) and md5sum the dir, rejecting byte-identical/skeleton frames.
  - *iter-29:* on this daily-history host, seed-loading `loaded_engine`-style fixtures can exceed a subagent Bash cap (SIGKILL 137 in a bg wrapper is the harness kill, NOT a test failure) — split fast no-boot tests from slow seed-boot ones; verify the byte-identity legs via the fast set; gate GOAL_ACHIEVED candidacy on a `nohup`-launched flushed full suite via the pump.
- **Escalation / state:** Resume the loop with `--acknowledge-regression` (prior verdict REGRESSION). After J-25/J-26/J-29 flip back to passing on LIVE rendered figures, J-104 reliability is MET, the byte-identity deep-equality + count-coherence tests are green, and the full suite flushes `0 failed, EXIT 0` with COHERENCE-PASS and zero new anti-goal, the next evaluation is a sound GOAL_ACHIEVED candidate (every buildable Must-have J-01..J-21, J-25..J-105 positive-evidenced; J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing per goal.md:105-108).
- **Coherence:** iter-46 was COHERENCE-PASS; this iteration is a backend read-path refactor that preserves every canonical value and adds no surface — register nothing beyond the additive J-105 Data-Contract / IA annotations already made to `blueprint.md`.
