# Goal Iteration 28 — Fast-ready boot + background warm-up (J-40, J-41): FIX-FORWARD the QA-failed in-flight build, restore test-suite determinism

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 28
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-40, J-41
- **Re-judge under re-scoped acceptance (no code work, no browser capture):** J-35, J-37, J-38, J-39
- **Required-still-passing journeys:** J-01, J-02, J-05, J-06, J-07, J-08, J-09, J-13, J-14, J-15, J-17, J-18, J-19, J-21, J-25, J-26, J-29, J-32, J-33, J-34, J-36
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. *(critical)*
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. *(extends Single source of truth)*
  - **Startup must not block serving on historical warm-up.** The boot path (FastAPI `lifespan`) MUST do only the minimal synchronous work needed to serve the **latest** as-of snapshot, then begin serving; the historical walk-forward cadence + `forward_returns` MUST be produced by a **background warm-up** after the server is accepting connections. The server MUST NOT withhold all requests (including `/health`) for the duration of the full backfill. *(operational)*
  - **Warm-up obeys every data invariant and is idempotent, concurrency-safe, and non-fatal.** Background (and any concurrent) snapshot / forward-return creation MUST reuse the **same canonical engines** (no second compute path), MUST stay immutable + strict-no-lookahead + single-source, MUST be **idempotent and concurrency-safe** (a duplicate create for an as-of date returns the existing snapshot — never a UNIQUE-constraint crash or a duplicate row), and a warm-up **failure MUST be logged and non-fatal** (it never prevents serving already-persisted snapshots). *(extends Snapshots are immutable + No recompute in the read path)*
  - **Readiness is reported honestly.** The health / readiness signal MUST distinguish **serving-ready** from **warming (with real progress)** from **unavailable**; it MUST NOT report ready before the latest snapshot is servable, MUST NOT mislabel a still-warming backend as "unavailable", and MUST NOT present a still-loading analytics aggregate as a complete or fabricated result. *(extends No fabricated data)*
  - **Precomputed snapshot seed is a reproducible cache, never fabricated.** Any committed precomputed `scanner_runs` / `forward_returns` seed MUST be a **byte-reproducible** materialization of the deterministic, no-lookahead computation over the **committed price seed** … loaded **verbatim** on a fresh DB exactly like the price seed — it MUST NOT be hand-authored, edited, or allowed to diverge from what the engines produce. *(extends No fabricated data + Single source of truth — relevant only because capability #34 stays OUT OF SCOPE)*

## GOAL

The backend serves the core read pages for the latest as-of date within the config-set readiness budget on a cold start, warms the historical evidence in the background with honest live progress, never crashes on a concurrent or failed warm-up — **and the full backend test suite is green and deterministic again**, which is the single thing that blocked this exact build at the iter-28 QA gate.

## BACKGROUND

This is the SECOND dispatch of iteration 28. The first dispatch (2026-06-09 22:01 → 2026-06-10 11:51) built the complete J-40/J-41 implementation — it sits UNCOMMITTED in the working tree at HEAD `d5963e5` (new `apps/backend/app/engine/warmup.py` / `readiness.py` / `tests/test_warmup.py`, new `apps/frontend/components/readiness-provider.tsx` / `warming-state.tsx`, modified `main.py`, `scanner.py`, `forward_testing.py`, `api/health.py`, `config.py`, `config.yaml`, `health-badge.tsx`, `layout.tsx`, `backtest/page.tsx`, `research/page.tsx`, `lib/api.ts`, + 5 updated test files) — and got dev `complete`, review `PASS_WITH_NOTES`, coherence `COHERENCE-PASS`. Then the QA gate **FAILED**: `runs/goal-i_can_see_the_wealthy_future_forever-iter-28/status.json` is `blocked` / `qa_failed` / `next_action: fix_qa` — the full backend suite was killed at ~19% after ~69 minutes with **~60+ FAILED tests across `test_api_backtest.py`, `test_api_engine.py`, `test_api_research.py`, `test_api_runs.py`, `test_api_watchlist.py`, `test_api_data.py`** (`reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-28-qa.md` + `-test.log`). The dev handoff never claimed those files green ("see the QA full-suite run").

**Primary root-cause hypothesis (decomposer-verified in source — the developer MUST confirm against an actual failure trace before fixing):** the API test suite had an implicit determinism contract with the OLD synchronous lifespan. Tests boot via `with TestClient(main.app)` (e.g., `tests/test_api_watchlist.py:61` and ~8–10 more entries per file) against the session-scoped shared `loaded_engine` DB (`tests/conftest.py:39`), and previously the lifespan ran `bootstrap_runs` + `backfill_forward_returns` **synchronously** — so by the first assertion the DB deterministically held the FULL historical cadence (a test even comments "counted AFTER lifespan bootstrap, so the counts are stable", `test_api_watchlist.py:150`). The new lifespan persists only the latest snapshot and spawns `start_warmup` as a daemon thread, so now: (a) tests assert against an **incomplete, concurrently-mutating** DB (research/backtest/runs/as-of tests need the full cadence; count/immutability assertions race the warm-up writes); (b) **every** `TestClient` entry spawns **another** full warm-up thread over the same SQLite DB — `start_warmup` has **no single-flight guard** (`warmup.py:129-151` unconditionally registers + spawns; a re-launch just overwrites the registry record) — explaining both the failures and the 69-minute crawl (write contention); (c) the warm-up `JobProgress` record (`job_id="warmup"`, `kind="warmup"`, `start=end=date.min`) now lives in the shared `data_manager._JOBS` registry and may leak into `/api/data` job-listing payloads tests assert on (note `test_api_data.py::test_post_seed_source_job_dispatches_without_key FAILED`). This is a test-harness/scheduling seam, not a value defect — `test_warmup.py` (12 passed) proves the warmed output byte-identical, and the live host reports `readiness: ready, warmup 10/10`.

The operator also re-scoped `docs/goal.md` post-iter-27 in TWO ways (iter-17/iter-20 lessons — always evaluate against the CURRENT goal text): (1) commit `6758c8b` added J-40/J-41 as Must-haves (this iteration's targets; not yet in `journey-history.json`, which tracks J-01..J-39); (2) an uncommitted goal.md edit adds a **"Verification basis (re-scoped 2026-06-09, post iter-27)"** block under each of J-35/J-37/J-38/J-39: their acceptance is met by **API-layer behaviour + the green automated suite + source-level proof** — a multi-step **browser capture is explicitly NOT a gate** and "its absence MUST NOT keep this journey `partial` or block GOAL_ACHIEVED". That evidence already exists on file (iters 23–27); the goal-evaluator MUST re-judge those four against the CURRENT acceptance this iteration. **No browser re-capture of those flows is attempted** — that would recur the documented five-iteration harness miss that drove the iter-27 STALLED.

Full depth is mandatory: prior verdict STALLED, prior QA verdict FAIL, the work touches the boot path + the snapshot-create concurrency seam (protected by the *Snapshots are immutable* critical anti-goal), spans backend + frontend, and the load-bearing proof is real unit/integration tests.

## IN SCOPE

### Backend

- [ ] **Confirm the QA-failure root cause from a real failure trace FIRST.** Run ONE previously-failing test file (e.g. `cd apps/backend && .venv/bin/python -m pytest tests/test_api_watchlist.py -x -v`), read the actual assertion/error, and confirm (or correct) the warm-up-nondeterminism diagnosis above before changing anything. Record the confirmed root cause in the dev handoff.
- [ ] **Restore the API test suite's deterministic warm-DB contract** without weakening the product's fast-boot behavior. Acceptable shapes (developer picks; no second compute path either way): bring the shared session test DB to the fully-warm state ONCE in the conftest fixture via the SAME canonical engines (`bootstrap_runs` + `backfill_forward_returns` — `test_warmup.py::test_scheduling_change_only_old_synchronous_path_is_a_noop` already proves this byte-identical), and/or expose a deterministic `wait_for_warmup()`-style join the test harness uses. Tests must never assert against a mid-warm-up mutating DB. Any new tunable comes from config (No magic numbers; per episodic memory `config-fixtures-need-new-required-keys`, any new required key goes into ALL inline test-config dicts).
- [ ] **Add a single-flight guard to `start_warmup` (`apps/backend/app/engine/warmup.py`).** While a warm-up is running in-process, a re-invocation MUST NOT spawn a duplicate concurrent worker (return the existing job id); re-launch after completion/failure stays allowed (the next boot finishes the idempotent remainder). This is product behavior J-41 step 1 itself names (readiness-probe re-spawn / `--reload` double-fire), not just a test fix — cover it with a unit test.
- [ ] **Verify the warm-up `JobProgress` record does not corrupt or leak into the Data-Manager job/run payloads** (`GET /api/data`, `GET /api/data/jobs`, `resumable_imports`, run history). If it does (the `test_api_data.py` seed-source dispatch failure suggests it may), exclude or explicitly label the `warmup`-kind record in those listings — the registry reuse (capability #32) must not change any J-33/J-34/J-36/J-38 served shape.
- [ ] **Keep the existing in-flight J-40/J-41 implementation — verify, complete, and fix it; do NOT re-implement, do NOT revert.** The fast-`lifespan` split (`main.py`), `ensure_latest_snapshot`, the `IntegrityError` catch-and-return-existing guards in `scanner.run_scan` (flush + commit) and the forward-returns insert path, `compute_readiness` (single producer) served ONLY on the extended `GET /api/health`, and the boot-validated `config.yaml` `startup` block are already built and review-passed. Fold in the review's non-blocking notes only if trivial.

### Frontend

- [ ] **Keep and verify the existing in-flight readiness UI** — the three-state top-bar badge (`health-badge.tsx`: Ready / Initializing… with live "history n/m" / Unavailable, polling at the config-derived cadence served by `/api/health` — no client-side poll literal, the client never computes readiness), the shared `readiness-provider.tsx`, and the `/backtest` + `/research` "warming up — historical evidence still loading (n/m)" states (`warming-state.tsx`) that auto-populate on completion. No new page/route/nav entry; NO new date state (J-18). `cd apps/frontend && npm run build` must pass — but NEVER against the live dev server's `.next` (iter-15 lesson / MEMORY `browser-qa-dead-shell-next-cache`).

### New user-facing capability

A cold-started Trendora is usable almost immediately: core read pages serve the latest snapshot within the readiness budget instead of after a multi-minute backfill. The header tells the truth about backend state, and Backtest/Research honestly say "warming up (n/m)" until the historical evidence finishes loading in the background.

### New information displayed

- Three-state readiness badge in the top bar with live warm-up progress (e.g. "Initializing… history 4/11").
- A transient "warming up — historical evidence still loading (n/m)" state on `/backtest` and `/research`.

### New user actions

None. Readiness is observed, not driven. (No new control, no new date state — J-18.)

### UI surface changes

The existing top-bar health badge gains the three-state readiness display; `/backtest` and `/research` gain a transient warming state. No new pages, routes, panels, or nav entries.

### Product surface delta

The product feels instantly available on boot and is honest about what is still loading, instead of appearing dead ("Backend unavailable") for minutes. Operationally it stops crashing on a boot race (`UNIQUE constraint failed: scanner_runs.asof_date`) and survives a failed warm-up.

### Blueprint conformance

No nav-skeleton change. The badge lives in the EXISTING layout shell / top bar; the warming states live on the EXISTING `/backtest` and `/research` homes. `state/blueprint.reapproval-requested` is confirmed ABSENT and none is written.

### Data-contract additions

None new this dispatch. The ONE new value — **backend readiness state + warm-up progress**, computed once by `app.engine.readiness:compute_readiness`, served only by the extended `GET /api/health` — is **already registered** in `state/blueprint.md` (Data Contract row + the health-probe "iter-28 (DELIVERED)" note, written during the first dispatch; verified current at re-planning). No second readiness read path, no frontend-local readiness computation, no second compute path for snapshots/returns (same canonical engines — only scheduling moved).

## OUT OF SCOPE

- **Code changes to the J-35 / J-37 / J-38 / J-39 `/data` feature paths, and ANY browser re-capture of their flows.** Under the re-scoped verification basis in the CURRENT `docs/goal.md`, the **goal-evaluator re-judges them on the existing API-layer + suite + source evidence**. The only interaction this iteration has with them is the FULL green suite (their tests are part of it) and proving this diff leaves their paths git-clean.
- **J-22, J-23, J-24** — externally data-walled, NON-HALTING / NON-VETOING per goal.md. Not re-probed, not touched.
- **Capability #33 (memoized/vectorized scan engine)** — the per-snapshot scan cost (~12–40 s) is a documented, accepted cost this iteration; do NOT fold a scan-engine optimization in. **Capability #34 (committed precomputed snapshot seed)** — *(optional accelerator)*, not a J-40/J-41 acceptance step; do not build.
- Any change to the six canonical scores, A–E bucket, setup status, regime label, or forward-return *values* — engine outputs stay byte-identical; only scheduling, concurrency handling, failure handling, and test-harness determinism change.

## DEFINITION OF DONE

- [ ] **The FULL backend suite passes, run ONCE at the QA gate** (`cd apps/backend && .venv/bin/python -m pytest tests/`) with a real final summary line — including the six previously-failing API test files — and completes in a sane runtime (~15–30 min given `test_warmup.py`'s ~10 min; the 69-minute-at-19% crawl must be GONE; treat a recurrence as remaining warm-up contention, i.e. NOT done). Never two concurrent pytest invocations (MEMORY `backend-test-suite-runtime`).
- [ ] Target journeys **J-40** and **J-41** pass per their goal.md acceptance — the load-bearing proof is the deterministic offline tests: server serving while cadence snapshots/forward returns are still being produced; readiness honest in all three states (never `ready` before the latest snapshot is servable, never `unavailable` while warming); the create-between-check-and-insert race returns the existing immutable snapshot (no UNIQUE-constraint crash, no duplicate, two-sessions AND real-threads variants); forced warm-up exception is caught + logged + honestly reported + next boot completes the idempotent remainder; single-flight re-spawn covered.
- [ ] **Scheduling-only invariant proven:** warmed cadence snapshots + forward returns + the `/api/backtest` aggregate byte-identical to the pre-change synchronous output (`test_warmup.py` invariant test green); J-06/J-07 re-asserted in the suite.
- [ ] Required-still-passing journeys remain green — especially J-08/J-15 (immutability / snapshot-served reads), J-18 (the badge + warming states add NO date state), J-09/J-14/J-19/J-21/J-25/J-26/J-29/J-32 (backtest/research correct once warm), J-33/J-34/J-36 (the Data-Manager payloads unchanged by the warmup-record seam).
- [ ] **The goal-evaluator re-judges J-35/J-37/J-38/J-39 against the CURRENT goal.md verification basis** and registers **J-40/J-41** as newly tracked journeys in `journey-history.json`; this iteration's diff is verified to leave their `/data` feature paths untouched.
- [ ] No anti-goal violation introduced (same canonical engines, snapshots immutable, readiness honest, every startup/poll number from config, exactly one date selector).
- [ ] `runs/goal-i_can_see_the_wealthy_future_forever-iter-28/status.json` progresses past `qa_failed` to a passing QA verdict; dev handoff at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-28-dev.md` UPDATED with the confirmed root cause + the fix.

## TESTING REQUIREMENTS

- **Unit / integration (the load-bearing proof — J-40/J-41 are deterministic and offline):**
  - The confirmed-root-cause fix has a dedicated regression test (e.g., repeated `TestClient` entries on a warm DB spawn no duplicate concurrent warm-up and leave the DB byte-stable; the data-manager job listings exclude/label the warmup record).
  - `tests/test_warmup.py` (12 tests) stays green: fast-boot lifecycle, readiness three-state honesty, warm-up completion, concurrency race (sessions + threads), forward-returns idempotency, non-fatal failure + recovery, empty-DB `unavailable`, scheduling-only byte-identity.
  - The previously-failing API files (`test_api_backtest`, `test_api_engine`, `test_api_research`, `test_api_runs`, `test_api_watchlist`, `test_api_data`) green individually, then the FULL suite ONCE at the QA gate.
  - `startup` config boot-validation + no-magic-numbers tests green; all inline test-config fixtures carry the `startup` block.
- **Browser (confirmatory, NOT the gate for the transient states):** against the live warm host — the header badge shows **Ready**; `/backtest` and `/research` render fully populated (no stuck warming state on a warm DB); **J-18 watch:** exactly one date `<select>` app-wide (badge + warming states add no date state). Bring the frontend up cleanly (stop strays BY PORT, `rm -rf apps/frontend/.next`, confirm `main-app.js` → 200 + hydrated shell BEFORE driving UI — MEMORY `dev-server-cleanup-by-port` / `browser-qa-dead-shell-next-cache`; a dead-shell SKIP is environmental, never a code FAIL). Capturing the transient **Initializing…/warming(n/m)** states live requires a fresh/fixture DB boot — **best-effort only**; the deterministic integration tests are the acceptance proof per goal.md J-40 ("an integration test asserts the server is serving … while the cadence snapshots / forward-returns are still being produced"). Do NOT block this iteration on a fixture-harness browser capture (the iter-23–27 lesson).
- **Error cases:** DB-unreachable / no-latest-snapshot → `unavailable` (never fabricated `ready`); warm-up exception → caught + logged + honestly reported (never silent green, never blocks serving); still-warming analytics → warming state (never an empty result presented as complete); invalid/missing `startup` keys → boot-validation error; duplicate concurrent create → existing immutable row.

## NOTES

- **Why this spec supersedes the first iter-28 spec:** the first dispatch progressed past dev/review and FAILED at QA after the spec was written; the binding new fact is the QA FAIL and its root cause. Everything still true from the first spec (scope boundaries, blueprint registration, anti-goal framing) is carried forward here.
- **Lessons applied:** iter-22 (a QA FAIL with dev/review green — read the ACTUAL failing assertions, distinguish harness/maintenance failures from product defects; here the whole failure class is a test-determinism seam, but it still BLOCKS completion per core.md "test failures BLOCK phase completion"); `config-fixtures-need-new-required-keys` (the `startup` block in ALL inline config dicts); `backend-test-suite-runtime` (full suite once, ~14 min baseline + `test_warmup.py` ~10 min; never concurrent); `backend-slow-boot-and-scanner-runs-race` (this iteration IS that fix — serve-fast + background warm-up + race guard); iter-4/15/23–27 multi-step-capture lessons (do not gate on a fixture-dependent browser capture; the deterministic tests are the proof); iter-20 (evaluator reads the CURRENT goal.md fresh — 41 journeys now — and checks for any further operator re-scope before verdict).
- **Resume discipline:** `status.json` is `blocked`/`qa_failed`/`next_action: fix_qa`. If the pipeline resumes mid-stream, the developer fixes the suite seam, the reviewer re-confirms, QA re-validates (QA-loop retry per workflow.md). If any step re-runs from scratch, it must treat the working tree as the in-flight iteration output — verify/fix, never re-implement or revert.
- **Coherence guidance:** the only registered new value (readiness + warm-up progress) keeps its single producer (`app.engine.readiness:compute_readiness`) and single endpoint (extended `GET /api/health`). Watch for: a second readiness read path (forbidden), the frontend computing readiness locally (forbidden), a second compute path for snapshots/returns (forbidden), and any conftest pre-warm helper that re-implements rather than CALLS the canonical engines (forbidden — same engines only).
- **Process expectations (iters 2/3/6/9–27 pattern):** full-depth iters here typically produce no `-audit.md`; `status.json` lives at the PHASE-namespace path `runs/goal-i_can_see_the_wealthy_future_forever-iter-28/`. The evaluator should verify critical seams in source rather than trusting report tables, sha256-dedupe browser evidence, and read `reports/qa/...-test.log` for the real pytest summary line.
- **GOAL_ACHIEVED outlook (do not jump early):** if the suite goes green, J-40/J-41 pass, nothing regresses, and the evaluator converts J-35/J-37/J-38/J-39 under the re-scoped basis, the board reaches 38 passing + J-22/J-23/J-24 (data-walled, NON-HALTING/NON-VETOING — iter-19 precedent) → GOAL_ACHIEVED is reachable THIS iteration. The evaluator must still confirm against the then-current goal.md. Do NOT autonomously re-probe J-22/J-23/J-24; do NOT declare completion while any buildable journey (including the suite-green DoD here) is unmet.
- Manage dev servers by port, never broad `pkill` (MEMORY `dev-server-cleanup-by-port`). The backend on :8835 is warm and healthy (`readiness: ready, warmup 10/10`) — do not restart it gratuitously.
