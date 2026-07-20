# Goal Iteration 4 — Fix the false "Backend unavailable" badge on an ordinary fetch (B3) and the frozen job heartbeat during aggregate refresh (F1); close J-05's last unverified step

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 4
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-03, J-04
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the committed seed / local provider fixtures — no live external network calls or paid data services may be introduced without an explicit goal.md amendment. *(critical)*

## GOAL

An ordinary "Fetch EOD prices" job that lands a bar past the last persisted snapshot no longer flips
the app-wide readiness badge into the crash-identical "Backend unavailable"/NO-GO state, and a
heavy ingest job's live progress heartbeat stays honest through its aggregate-refresh finalize
phase — completing J-05's browser story so it can pass cleanly.

## BACKGROUND

The iter-3 evaluator (`runs/goal-session-ops-hardening/iter-3/eval.md`) scored J-05 `partial`:
its backend correctness (B1/B2) and step-4 measurement are done and verified, but browser-QA,
ux-regression, and closure all converged on two **pre-existing, out-of-scope** trust-surface
defects first exposed by driving a real fetch + heavy job through the browser — **B3** (an
ordinary fetch flips the global badge to a false "Backend unavailable"/NO-GO) and **F1** (the job
heartbeat freezes during the aggregate-refresh tail, showing a false "possibly stalled"). The
eval's explicit next-step order is B3 (highest), F1, then re-running the one skipped regression
check (UT-04, cold-boot on a fresh DB) — this iteration executes exactly that order and nothing
past it (**do NOT advance to J-06 yet**, per the eval and rule 5 below).

**Root causes, confirmed by direct code read this iteration** (so the developer does not need to
rediscover them):
- **B3** — `app/engine/readiness.py:129`: `latest_servable = bool(latest_data is not None and
  latest_run is not None and latest_run >= latest_data)`, where `latest_data` is
  `prices.latest_data_date(session)` — the **whole-table** max `daily_prices.date` across all 590
  symbols. An ordinary fetch that lands a bar for **any single symbol** dated after the last
  persisted `ScannerRun.asof_date` pushes `latest_data` forward with no run yet for that date,
  flipping `latest_servable` to `False` → `state = "unavailable"` → `health-badge.tsx`'s `else`
  branch renders "Backend unavailable" — even though the last valid, complete snapshot is still
  being served correctly on every page.
- **F1** — `app/engine/data_manager.py:3034` (`_refresh_ingest_aggregates`, iter-2-shipped): its
  per-date `market_phase_cached` loop (:3072-3078) and the per-date coverage warm call run **after**
  the main per-date backfill scan loop finishes (which already ticks correctly via
  `prog.tick(...)` at :2863), but this finalize loop never calls `prog.tick()` — so
  `last_progress_at` freezes for the whole finalize tail. The frontend's `stale` flag
  (`apps/frontend/app/data/page.tsx:2483`, vs the configured `job_progress.heartbeat_stale_seconds`
  threshold) then renders "· possibly stalled" (`:2501`) on a perfectly healthy job.

**Priority rubric applied:** no journey regressed (rule 1 N/A); last coherence was
`COHERENCE-PASS`, not FAIL (rule 2 N/A — no consolidation mandate); J-05 is the clear unblocker
(rule 3) — it is this session's only partial journey and the eval's named top priority; only one
candidate scope exists so rule 4 is trivially satisfied; **J-06 is deliberately excluded** (rule 5,
never bundle two risky journeys) — B3+F1 already touch shared, every-page-read machinery
(`readiness.py`, the global badge) which is itself the one risky change this iteration carries;
adding J-06's own seven-page audit on top would make a joint failure undiagnosable. B3/F1 are both
dev-owned with concrete fixes named above — no human-owned blocker (rule 6 N/A).

**Depth is full.** **Trigger 1 (structural/cross-cutting):** the fix touches `app/engine/readiness.py`
(the servability check), `app/engine/data_manager.py` (`_refresh_ingest_aggregates`),
`apps/frontend/lib/api.ts` (the `ReadinessState` type), and `apps/frontend/components/health-badge.tsx`
(the badge render branch) — four modules whose interaction (a value computed once and read by the
**global, every-page** badge + preflight banner) is not covered by any single journey's existing
tests; J-04's own 6-step acceptance never scripts "an ordinary fetch outruns the last snapshot."
**Trigger 2 (Data model):** this iteration changes the blueprint Data-Contract's own "Backend
readiness / boot phase + preflight verdict" row's computing module (`app.engine.readiness.
compute_readiness`) — widening its served `state` enum and adding a new field — which is exactly
the kind of change the coherence-auditor is watching this row for.

**Lesson applied** (`lessons.md`, iter-3 — this iteration is literally its named "Applies to"
pattern): "A tightly-scoped, correct backend fix can still fail to advance its journey to `passing`
because the FIRST iteration to drive a realistic load pattern... exposes latent trust-surface
defects on SHARED components... Always cross-check the QA verdict against the raw
`ui-test-results.md` browser verdict; never score a target journey clean on backend-correctness
alone." This iteration IS that named fix (`readiness.py`, `_refresh_ingest_aggregates`, the shared
`HealthBadge`/`PreflightBanner`/`JobProgressPanel` surfaces) — the evaluator must read the raw
browser-qa output directly before scoring J-05, not only the QA report's summary (which iter-3
itself overstated as a clean 12/12).

## IN SCOPE

### Backend
- [ ] `app/engine/readiness.py` — `compute_readiness`'s servability check compares `latest_run`
      against the **benchmark symbol's own latest bar** (`cfg.etfs.index[0]` — the exact same
      symbol `warmup._warmup_dates`/`forward_testing.walk_forward_asof_dates` already use to define
      the trading calendar, "SPY defines the trading calendar") via one new indexed per-symbol max
      query (mirrors `latest_data_date`'s shape, filtered to one symbol — never a whole-table scan,
      AG-8) instead of the current whole-table `latest_data_date` max. An unrelated non-benchmark
      symbol's fetch no longer affects servability at all.
- [ ] Add one new, distinct readiness state (this spec names it `awaiting_snapshot`; the developer
      may pick a clearer name but must use exactly one name everywhere it is read) for "a servable
      last run exists, but the benchmark's own latest bar has advanced past it with no run yet for
      that date" — visually and semantically distinct from both `unavailable` (nothing ever
      servable — DB down or no run ever persisted) and `initializing` (cadence warm-up in flight,
      unchanged). `latest_run is None` (a true never-scanned DB) MUST still resolve unconditionally
      to `unavailable` — regression guard for the existing `unscanned_engine` fixture in
      `test_readiness.py` and for J-04's crash-detection acceptance.
- [ ] `compute_readiness`'s return payload gains one new optional field (a short, honest,
      human-readable detail string), populated only for the new state (`null` for the other three)
      — naming the condition and pointing at the recovery action (run a backfill/rebuild on Data
      Manager to produce the missing snapshot). `compute_preflight` needs no logic change (its
      existing `servable = readiness_result["state"] != UNAVAILABLE` check already treats the new
      state as non-breaching) — add a test pinning that this stays true, do not re-derive it.
- [ ] `app/engine/data_manager.py` — `_refresh_ingest_aggregates` calls `prog.tick(...)` at the
      start of the function and at each per-date step of its market-phase warm loop (mirroring the
      existing per-date convention at the main scan loop, `data_manager.py:2863`, and the
      per-symbol convention at `:1968`/`:1974`) so the heartbeat advances throughout the finalize
      phase, not only during the main scan.
- [ ] No change to: `ensure_latest_snapshot`, the boot warm-up loop, the `coverage_snapshot`
      table/finalize gate, `aggregates_refreshed`'s nullability contract, or any J-01/J-03 shipped
      field — see OUT OF SCOPE.

### Frontend
- [ ] `apps/frontend/lib/api.ts` — widen `ReadinessState` (currently `"ready" | "initializing" |
      "unavailable"`, line 115) to add the new literal; add the new optional detail field to the
      health-payload type.
- [ ] `apps/frontend/components/health-badge.tsx` — add a fourth pill branch for the new state: a
      distinct `data-state` value, a non-danger visual treatment (reuse an existing `Badge` variant,
      e.g. `accent` — no new color token), visible text that is **not** "Backend unavailable", plus
      the recovery-pointer detail text (e.g. naming the pending date and pointing at Data Manager).
- [ ] No change to `readiness-provider.tsx` — confirmed by inspection: its `=== "ready"` poll-cadence
      check and its own-failure fallback (`setState("unavailable")`) both remain correct unmodified
      for the new state; do not touch this file.
- [ ] No change to `preflight-banner.tsx` — it reads only the composed `preflight.verdict`, which
      stays `GO` for this condition once `compute_preflight`'s servability logic is confirmed
      unaffected (see Backend, above); do not touch this file.

### New user-facing capability
None new — this fixes an honesty defect in the EXISTING global readiness badge and job-progress
heartbeat capabilities (both shipped in mcp-loop/ops-hardening prior iterations).

### New information displayed
The badge surfaces a new, distinct, calm label for "new data has landed, snapshot pending" instead
of conflating it with the crash-identical "Backend unavailable" presentation; the job-progress
heartbeat ("updated Ns ago") stays fresh through the aggregate-refresh tail of a heavy job instead
of freezing and falsely reading "possibly stalled".

### New user actions
None new — no new form/button. The new badge state carries a recovery-pointer hint (text naming
the condition + where to act), reusing existing navigation to Data Manager (`/data`).

### UI surface changes
`HealthBadge` (global, top bar, every page) gains a fourth visual state. No new page or panel.

### Product surface delta
The app's single global "is the backend OK" signal becomes honest about a third real-world
condition — new raw price data has landed but the analytical snapshot hasn't caught up yet — instead
of collapsing it into the same red "Backend unavailable" presentation used for an actual crash or a
never-scanned DB; a heavy job's live progress no longer falsely claims to be stalled during its
aggregate-refresh tail.

### Blueprint conformance
Global readiness badge (top bar, every page) + preflight banner — J-04's existing canonical home;
job-progress heartbeat on `/data` (Data Manager) — J-01/J-03/J-05's existing canonical home. No new
Information Architecture entry, no nav-skeleton change (no `blueprint.reapproval-requested` file).

### Data-contract additions
Amends (does not duplicate) the existing "Backend readiness / boot phase + preflight verdict" row —
computed by `app.engine.readiness.compute_readiness`/`compute_preflight`, served by
`GET /api/health` (unchanged module, unchanged endpoint):
- `readiness.state` (frontend `ReadinessState`): widens from `"ready" | "initializing" |
  "unavailable"` to add `"awaiting_snapshot"`.
- `readiness.detail: string | null` (new sibling field on the SAME payload): `null` for `ready` /
  `initializing` / `unavailable`; a short, honest sentence naming the pending-snapshot condition +
  recovery pointer when `state == "awaiting_snapshot"`.

Both fields are served on the exact same `GET /api/health` response, computed by the exact same
`compute_readiness` — no second computing module, no second serving endpoint. `blueprint.md`'s
existing readiness row is updated to document both (see this iteration's blueprint edit).

## OUT OF SCOPE

- J-06 (the measurement capstone) — deferred again; per the iter-3 eval's explicit "do NOT advance
  to J-06 yet," this iteration finishes J-05's browser story first (rule 5 above).
- Any change to `ensure_latest_snapshot` (boot's synchronous latest-snapshot step, `main.py:73`) or
  the boot warm-up loop's cadence bootstrap — unchanged; iter-2's scoping decision still stands
  (still dormant/unverifiable against the offline seed this session).
- Any change to the `coverage_snapshot` table, the B1/B2 fetch/expand finalize gate, or
  `aggregates_refreshed`'s nullability contract — "Do not redo" per `iteration-state.md`.
- Reusing or modifying the `initializing` state's own warm-up `done`/`total` semantics — the new
  state is an additive sibling, not a replacement; `initializing`'s existing behavior stays
  byte-identical.
- `scripts/start-backend.sh`'s `ulimit`/`MALLOC_ARENA_MAX`/logfile enforcement, or wiring
  `limit_concurrency`/`timeout_keep_alive_seconds`/`graceful_timeout_seconds` — untouched, "Do not
  redo."
- J-05's `[NEW]`-flagged `demo.sh ops-hardening --session-live` walkthrough artifact — not attempted
  this iteration (a showcase/demo-chain concern, not a browser-qa-verifiable behavior); flagged in
  NOTES for whenever the session nears closure.
- Editing `docs/goal.md` (lint-final, commit `9c98cb3`) — not touched. Re-verifying the 25 archived
  mcp-loop journeys — not in scope.

## DEFINITION OF DONE

- [ ] Target journey J-05 passes cleanly via browser-qa-agent — read the raw `ui-test-results.md`
      browser verdict directly (not only the QA report's summary — iter-3's lesson): no FAIL on the
      badge/heartbeat scenarios, and UT-04 (cold-boot check) actually executes against a fresh DB
      copy instead of being skipped.
- [ ] B3 fixed and evidenced live: an ordinary fetch that lands a bar past the last persisted run no
      longer renders the crash-identical "Backend unavailable"/NO-GO state; true unavailability (no
      run ever persisted, or DB unreachable) still renders correctly.
- [ ] F1 fixed and evidenced live: a real heavy multi-date job's heartbeat keeps advancing through
      the aggregate-refresh finalize phase; no false "possibly stalled".
- [ ] Required-still-passing journeys J-01, J-03, J-04 remain green (deterministic replay + LLM
      fallback — mechanically verified at both depths).
- [ ] No anti-goal violation introduced (AG-3: the new state's detail text is honest and accurate,
      never fabricated; AG-8: the new benchmark-scoped query is index-bounded, never a whole-table
      scan).
- [ ] Unit tests pass; no regressions (existing `test_readiness.py` fixture-matrix suite passes
      unedited; new tests cover the new state and F1's `tick()` calls).
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-4-dev.md`, documenting the exact
      new state name/field and the before/after badge behavior.

## TESTING REQUIREMENTS

- Browser: J-05 (target — the badge/heartbeat scenarios, TC-2 through TC-8 below); J-01, J-03, J-04
  (required-still-passing regression, deterministic replay with LLM fallback).
- Unit/integration: extend `test_readiness.py`'s fixture matrix with (a) a servable run persisted for
  date D plus a non-benchmark symbol's bar dated after D (expect unchanged `ready`/`initializing`),
  and (b) a variant where the benchmark's own bar is dated after D with no run yet (expect the new
  state); a test pinning `compute_preflight`'s servability stays `ok` for the new state; extend
  `test_data_manager.py` for `_refresh_ingest_aggregates`'s new `tick()` calls (assert
  `last_progress_at` advances across the per-date market-phase loop, not just the main scan).
- Error cases: `latest_run is None` (a never-scanned DB) must still resolve to `unavailable`, never
  the new calm state — the one case where "nothing is servable" must never be softened.

Test-first contract:

- TC-1: given a warm DB where a `ScannerRun` is persisted for the benchmark's own latest bar date,
  when `GET /api/health` is computed, then `state` is `"ready"` (or `"initializing"` per existing
  warm-up rules) exactly as before this iteration — unaffected-baseline regression guard.
- TC-2: given a `ScannerRun` persisted for date D and a NON-benchmark symbol's `DailyPrice` row
  dated D+1 landed by an ordinary fetch (the benchmark's own latest bar stays D), when
  `GET /api/health` is computed, then `state` is NOT `"unavailable"` and is unchanged from what it
  was before the fetch.
- TC-3: given a `ScannerRun` persisted for date D and the BENCHMARK symbol's own latest bar advances
  to D+1 with no run yet for D+1, when `GET /api/health` is computed, then `state ==
  "awaiting_snapshot"` (not `"unavailable"`, not `"ready"`, not `"initializing"`) and
  `readiness.detail` is a non-null string naming the condition and a recovery action.
- TC-4: given the TC-3 DB state, when the `HealthBadge` component renders, then
  `[data-testid="readiness-badge"][data-state="awaiting_snapshot"]` is present, its visible text is
  NOT "Backend unavailable", uses a non-danger visual treatment, and shows the recovery-pointer text.
- TC-5: given the TC-3 DB state, when `compute_preflight` is computed, then the `servability`
  component's `ok` is `true` and the overall verdict is not forced to `NO-GO`/`DEGRADED` by this
  condition alone.
- TC-6: given NO `ScannerRun` has ever been persisted (the existing `unscanned_engine` fixture or
  equivalent), when `GET /api/health` is computed, then `state == "unavailable"` — unchanged
  (regression guard: the new state must never mask a genuine no-servable-snapshot condition).
- TC-7: given a real multi-date `backfill`/`rebuild` job is dispatched against a
  `scripts/start-backend.sh`-launched process, when the job reaches its post-scan aggregate-refresh
  (finalize) phase, then `JobProgress.last_progress_at` advances at least once per date processed in
  that phase, and the `/data` live job card never shows "· possibly stalled" while the job remains
  healthy.
- TC-8: given a fresh, never-ingested DB copy (no `coverage_snapshot` rows, no prior run), when the
  backend cold-boots against it and `/data` is visited, then the coverage panel renders from the
  persisted payload within its committed budget and no full `daily_prices`-table prefill occurs
  (closes J-05 step-3's previously-SKIPPED UT-04 check; re-verification of already-shipped
  iter-2/iter-3 behavior, no new code).
- TC-9: given the existing J-01/J-03/J-04 scripted acceptance (breakdown/chunking/boot/badge/
  logfile), when the required-still-passing regression replay runs after this iteration's
  `readiness.py`/`data_manager.py` edits, then every previously-passing assertion still passes
  unedited.
- TC-10: given the new benchmark-scoped latest-bar query executes, when its query plan/row-read
  count is inspected, then it reads via the `(symbol, date)` index for one symbol only — never a
  `daily_prices` whole-table scan (AG-8).

## NOTES

- **Lesson applied** (`lessons.md`, iter-3): this iteration is that lesson's own named
  "Applies to" pattern — touching `app/engine/readiness.py`, `_refresh_ingest_aggregates`, and the
  shared `HealthBadge`/`PreflightBanner`/`JobProgressPanel` surfaces. The evaluator must read the raw
  browser-qa output directly before scoring J-05, not only the QA report's summary (iter-3's QA
  report overstated a clean 12/12 and buried the real browser FAIL — only the audit and closure
  caught it).
- **Root-cause citations** (confirmed by direct code read this iteration): B3 =
  `app/engine/readiness.py:129`; F1 = `app/engine/data_manager.py:3034`
  (`_refresh_ingest_aggregates`)'s per-date loop at `:3072-3078`, missing the `tick()` the main scan
  loop already calls at `:2863`.
- **Benchmark symbol:** `cfg.etfs.index[0]` — the exact same symbol
  `forward_testing.walk_forward_asof_dates` (called via `warmup._warmup_dates`) already uses to
  define the trading calendar ("SPY defines the trading calendar").
- **`blueprint.md` updated this iteration:** the "Backend readiness / boot phase + preflight
  verdict" row's Notes column documents the widened `state` enum + the new `detail` field — same
  module, same endpoint, no new row. No nav-skeleton change — no
  `runs/goal-session-ops-hardening/state/blueprint.reapproval-requested` file written.
- **Assumption logged:** one entry appended to `runs/goal-session-ops-hardening/state/
  assumptions.md` — the eval's B3 fix direction was qualitative ("its own calm label", "compare vs
  the benchmark's own latest bar"); this spec commits to a concrete literal name
  (`awaiting_snapshot`) and field shape (`readiness.detail: string | null`) so the developer has one
  unambiguous target. Reversible.
- Once J-05 is scored `passing`, J-06 (the measurement capstone — the last remaining Must-have
  journey this session) is the natural next target per goal.md's suggested build order.
- The J-05 `[NEW]`-flagged `demo.sh` walkthrough acceptance item remains open (not attempted this
  iteration, see OUT OF SCOPE) — worth picking up once J-05/J-06 both pass and the session nears a
  GOAL_ACHIEVED review, not before.
