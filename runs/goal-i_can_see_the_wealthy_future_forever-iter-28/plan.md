# goal-i_can_see_the_wealthy_future_forever-iter-28 Execution Plan

Target journeys: **J-40** (fast-ready boot + background warm-up + honest readiness), **J-41** (boot resilience — concurrency-safe idempotent warm-up, non-fatal failures). Depth: full.

**RESUME STATE (read first):** this iteration was dispatched once and interrupted AFTER the developer completed. The working tree (HEAD `d5963e5`, uncommitted) holds the full J-40/J-41 implementation; dev + frontend handoffs exist (`docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-28-dev.md` / `-frontend.md`); `status.json` is at `dev_complete` / `next_action: review`. All downstream agents MUST treat the working tree as the in-flight iteration output: **verify, complete, and fix it — do NOT re-implement from scratch, do NOT revert it.** The FULL backend suite has NOT yet run this iteration — that is the QA gate's job (run ONCE, ~14+ min).

## What to Build

Already implemented in the working tree — this iteration's remaining work is review → QA → evaluation, with fixes only as findings demand:

- **Lifespan split (`apps/backend/main.py`)** — minimal sync before `yield` (config → tables → seed → `ensure_latest_snapshot`, one `run_scan` over the latest data date), then serve; historical walk-forward cadence + `backfill_forward_returns` run as a background warm-up after `yield` via `app/engine/warmup.py`, reusing the EXISTING `data_manager` daemon-thread + `JobProgress` machinery and the SAME canonical engines (no second compute path — scheduling only).
- **Single readiness producer + single endpoint** — `app.engine.readiness:compute_readiness` returns one honest state ∈ {`ready`, `initializing`, `unavailable`} + `{done, total}`; served ONLY by the **extended `GET /api/health`**. This choice is PINNED: the blueprint Data Contract already carries the row + "iter-28 (DELIVERED)" note — verify it matches the implementation; **no sibling `GET /api/readiness` may be added**, and no further blueprint edit is required.
- **Concurrency-safe creates** — `run_scan` (`scanner.py`) catches duplicate-insert `IntegrityError` at flush AND commit → rollback → re-read → return the existing immutable row (never raises/duplicates/overwrites); same guard on both forward-returns commit paths (`forward_testing.py`).
- **Non-fatal warm-up** — any warm-up exception is caught + logged, job marked failed, server keeps serving persisted snapshots, readiness reports it honestly, next boot completes the idempotent remainder.
- **Startup tunables in config** — typed boot-validated `StartupCfg` (`config.startup`): readiness budget, warm-up batch size, health-poll cadences. No startup/poll/budget literal in `main.py` / `readiness.py` / `warmup.py`. The required `startup` block is in ALL four inline test config fixtures (test_config, test_config_engine, test_sectors, test_themes) — reviewer verifies (episodic memory `config-fixtures-need-new-required-keys`).
- **Frontend readiness UI** — shared `ReadinessProvider` (single client poll of `/api/health`, config-derived cadence, never computes readiness locally); three-state `health-badge.tsx` (Ready / Initializing… history n/m with pulse / Unavailable); `WarmingState` card on `/backtest` + `/research` that auto-populates on the readiness flip. No new page/route/nav entry; NO new date state (J-18).

## Agents Required

- **backend-data: yes** — fix-only against the existing working-tree implementation if review/QA find gaps (verify/complete, never re-implement or revert). No fresh build expected.
- **frontend-ux: yes** — same fix-only discipline for the badge / warming-state / provider files.

## Frontend Present
yes

## Files to Create/Modify

All already present in the working tree (verify, do not revert):

- `apps/backend/main.py` -- lifespan split: minimal sync before `yield`, `start_warmup` after.
- `apps/backend/app/engine/warmup.py` (new) -- `ensure_latest_snapshot`, `start_warmup`, non-fatal `_run_warmup`, progress via `JobProgress`.
- `apps/backend/app/engine/readiness.py` (new) -- `compute_readiness`, the single readiness producer.
- `apps/backend/app/engine/scanner.py` -- IntegrityError guards (flush + commit) on `run_scan`.
- `apps/backend/app/engine/forward_testing.py` -- `_commit_forward_returns_concurrency_safe` on both backfill paths.
- `apps/backend/app/api/health.py` -- extended with `readiness`, `warmup`, config-derived poll cadences.
- `apps/backend/app/config.py` + `config.yaml` -- typed `StartupCfg` / `startup` block.
- `apps/backend/tests/test_warmup.py` (new, 12 tests) + `test_health.py` + the four fixture files.
- `apps/frontend/lib/api.ts`, `components/readiness-provider.tsx` (new), `components/health-badge.tsx`, `components/warming-state.tsx` (new), `app/layout.tsx`, `app/backtest/page.tsx`, `app/research/page.tsx`.
- `runs/goal-session-i_can_see_the_wealthy_future_forever/state/blueprint.md` -- Data Contract row already recorded (verify only; no further edit).

## UI Evolution

- **New user-facing capability:** a cold-started Trendora is usable almost immediately — core read pages serve the latest snapshot within the config readiness budget; the header tells the truth about backend state; analytics pages honestly say "warming up (n/m)" until the historical evidence finishes loading. No misleading multi-minute "Backend unavailable".
- **New information displayed:** three-state readiness badge with live warm-up progress ("Initializing… history 4/11"); a "warming up — historical evidence still loading (n/m)" state on `/backtest` and `/research`.
- **New user actions:** none — readiness is observed, not driven. No new control, no new date state (J-18 preserved).
- **UI surface changes:** existing top-bar health badge gains the three-state display; `/backtest` and `/research` gain a transient warming state. No new pages, routes, or panels.
- **Navigation changes:** none.

## Visual Requirements

- **Component patterns:** existing `Badge` variants — Ready → `ok` green dot, Initializing → `warn` + `animate-pulse` dot + monospace `n/m`, Unavailable → `danger`; warming state = existing `Card` + `Loader2` spinner. No raw-div soup (already implemented this way per the frontend handoff).
- **Layout:** no change — badge stays in the existing top-bar shell next to the global as-of switcher; warming cards render in the existing `/backtest` / `/research` content regions.
- **Key visual effects:** dense dark analytical workstation style; tabular/monospace `n/m`; reuse of the established pulse-dot pattern. Nothing invented.
- **States to handle:** initial-poll loading ("Checking backend…"), ready, initializing-with-progress, unavailable; on Backtest/Research: warming(n/m) vs populated — warming is never an error and never a partial result presented as complete.

## Key Test Scenarios

- **QA gate: the FULL backend suite runs ONCE** (~14+ min; never two concurrent pytest invocations — episodic memory `backend-test-suite-runtime`). Note `test_warmup.py` is heavy (~10–11 min, module-scoped real warm-up fixture).
- **J-40 fast-boot (deterministic integration — the load-bearing proof):** lifespan yielded + latest snapshot present + dashboard endpoint 200 WHILE cadence snapshots / forward returns are still being produced; readiness honest in all three states; never `ready` before the latest snapshot is servable; empty/unreachable DB → `unavailable`.
- **J-41 concurrency:** create-between-check-and-insert race for the same as-of date (two sessions AND real threads) → exactly one snapshot, loser returns the existing immutable row, no `UNIQUE constraint` crash, no duplicate. Same for a concurrent forward-returns INSERT.
- **J-41 non-fatal:** forced warm-up exception → boot survives, persisted snapshots served, failure logged + honestly reported, next boot completes the idempotent warm-up.
- **Scheduling-only invariant:** warmed cadence snapshots + forward returns + `/api/backtest` aggregate byte-identical to pre-change synchronous output; J-06/J-07 re-asserted; `startup` config boot-validates; no-magic-numbers green. Reviewer verifies `test_warmup.py` assertions are REAL (exact values, race actually exercised), not smoke.
- **Browser (J-40):** badge shows the three states; `/backtest` + `/research` show warming(n/m) and auto-populate; **J-18 watch:** exactly one date `<select>` app-wide. The live warm DB warms near-instantly — drive Initializing against a fresh/fixture DB **or accept the deterministic integration test as the load-bearing proof for the transient states** (per spec). Bring the frontend up cleanly: stop strays BY PORT, `rm -rf apps/frontend/.next`, confirm `main-app.js` → 200 + hydrated shell BEFORE driving UI; a dead-shell is an environmental SKIP, not a code FAIL.
- **Required-still-passing:** J-01, J-02, J-05–J-09, J-13–J-15, J-17–J-19, J-21, J-25, J-32 — especially J-08 (the guard returns the existing row, never overwrites), J-15 (no per-request recompute), J-25/J-32 (`/research` still serves its labs + as-of mode after the warming-gate change).

## Evaluation Directives (this iteration)

- **Re-judge J-35 / J-37 / J-38 / J-39 under the CURRENT goal.md verification basis** ("Verification basis (re-scoped 2026-06-09, post iter-27)": API-layer behaviour + green automated suite + source-level proof; a multi-step browser capture is explicitly NOT a gate). The evidence already exists on file (iters 23–27). **No code work and NO browser re-capture of these flows** — that would recur the documented five-iteration miss. Precondition: verify their `/data`-path files are git-clean apart from the listed iter-28 files (they are, per the dev handoff). This supersedes the first iter-28 spec's stale framing (iter-20 trap, corrected in the current spec).
- Register **J-40/J-41** as newly tracked journeys in `journey-history.json`.
- **GOAL_ACHIEVED outlook (do not jump early):** if J-40/J-41 pass, nothing regresses, and the four partials convert, the board reaches 38 passing + J-22/J-23/J-24 (data-walled, NON-HALTING/NON-VETOING per goal.md) → GOAL_ACHIEVED is reachable this iteration. The evaluator must still confirm against the current goal.md directly.
- **Coherence watch items:** a second readiness read path (forbidden), the frontend computing readiness locally (forbidden), a second compute path for snapshots/returns (forbidden — same canonical engines only). No nav-skeleton change; `state/blueprint.reapproval-requested` stays absent.

## Operational Notes / Assumptions

- Known issue (accepted, flagged not built): the per-date scan is genuinely slow (~29 s latest-snapshot compute, near the 30 s readiness budget; full cold warm-up ≈ 4+ min). Capability #33 (memoized scan engine) and #34 (precomputed snapshot seed) remain OUT OF SCOPE — J-40/J-41 are satisfied without them.
- No new `table=True` model exists (readiness is computed, not stored) → `tests/test_db.py` expected-tables needs no change; reviewer confirms.
- `run_scan`'s guard handles `IntegrityError` only; a `database is locked` `OperationalError` under extreme SQLite contention is environmental, not a J-41 correctness failure (dev handoff Known Issues — do not treat as a blocker).
- Manage dev servers BY PORT, never broad `pkill` (episodic memory `dev-server-cleanup-by-port`).
- Dev handoff exists; update it only if the implementation changes during review/QA fixes.

## Out of Scope (do NOT build this iteration)

- Code changes to J-35/J-37/J-38/J-39 paths, and any browser re-capture of their flows (evaluator re-judges on existing evidence).
- J-22/J-23/J-24 (Yahoo-429 data-walled) — not re-probed, not touched.
- Capability #34 (precomputed snapshot seed) and #33 (memoized/vectorized scan engine).
- Any change to the six canonical scores, A–E bucket, setup status, regime label, or forward-return VALUES — only scheduling, concurrency handling, and failure handling changed; engine outputs stay byte-identical.

The spec is consistent with `docs/goal.md` (Success Criterion "The stack is ready together (fast boot)", Key Capability #32, journeys J-40/J-41 added in commit `6758c8b`, and the 2026-06-09 22:47 verification-basis re-scope of J-35/J-37/J-38/J-39). No goal contradiction found.
