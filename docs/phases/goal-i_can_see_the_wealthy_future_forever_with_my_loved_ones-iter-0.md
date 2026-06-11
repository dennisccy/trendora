# Goal Iteration 0 (Baseline) — Trendora `i_can_see_the_wealthy_future_forever_with_my_loved_ones`

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15, J-16, J-17, J-18, J-19, J-20, J-21, J-22, J-23, J-24, J-25, J-26, J-27, J-28, J-29, J-30, J-31, J-32, J-33, J-34, J-35, J-36, J-37, J-38, J-39, J-40, J-41, J-42, J-43, J-44, J-45, J-46, J-47 (ALL must-have journeys)
- **Required-still-passing journeys:** N/A — baseline establishes the initial pass/fail/partial state; nothing is established yet
- **Anti-goal reminders (from `docs/goal.md` — full text there is authoritative):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D; the walk-forward MUST be unit-tested to prove it. Chart visualization MAY render bars > D strictly as a labelled forward/after-as-of display that feeds NO score/bucket/setup/pattern/factor/ranking. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten; forward returns live in a separate append-only table. *(critical)*
  - **Single source of truth.** Each canonical score (and A–E bucket and setup status) computed exactly once and read identically by every page; API/frontend MUST NOT recompute. *(critical)*
  - **No magic numbers.** Every weight, threshold, cutoff, bucket edge, universe entry, theme definition comes from config.
  - **No fabricated data.** On provider failure, surface an explicit stale/unavailable state; never synthesize prices or scores to force a green journey.
  - **No order/execution path.** Research-only; no brokerage/order/capital-deployment code reachable. *(critical)*
  - **No secrets in source.** No hard-coded credentials/keys; live-provider keys env-only.
  - **Risk-Off must gate Actionable.** Risk-Off regime ⇒ zero stocks "Actionable". *(critical)*
  - **Scores must be explainable.** Every displayed score carries its named component breakdown.
  - **Honest limitations surfaced.** Breadth/new-high metrics labelled "universe-relative"; walk-forward evidence labelled survivorship-biased.
  - **No auth tokens in `localStorage`** (no auth in this version).
  - **No recompute in the read path.** Read endpoints serve persisted-snapshot values for the resolved as-of date; the as-of-scoped evidence aggregate is derived once per resolved date and never includes a snapshot dated > D.
  - **On-demand snapshots stay immutable & lookahead-free.** Create-once; existing snapshots read, never overwritten. *(critical)*
  - **Setup & pattern vocabulary is config-driven in the UI too.** Glossary and tooltips generated from the single config-backed catalog.
  - **Honest forward-test for partial windows.** NA/partial + sample size for horizons/cohorts lacking samples — never fabricate or extrapolate.
  - **VCP is a pattern, not a status.** Never enters the setup-status enum; never alone promotes Actionable. *(critical)*
  - **Live fetch is real-data-only.** Explicit error on failure; no synthesized prices.
  - **Import keys are env-or-session, never persisted.** Provider catalog + key requirements from config; a pasted key held in memory only — never written to disk/run log/DB and never echoed back. Import dates are job parameters, not a second date control.
  - **Range backfill stays immutable & lookahead-free.** Create-once for fetched/backfilled ranges.
  - **Coverage & missing-data are descriptive & honest.** Read-only metadata from stored bars + config; missing/thin shown NA, never fabricated; thresholds and calendar from config; universe-vs-symbols surfaced in plain language.
  - **Pull-missing fetches exactly the gap, real-data-only, idempotently.** Only the diagnosed shortfall, via the existing chunked/resumable path; INSERT-new-only.
  - **Unfinished-imports actions are idempotent and audit-preserving.** Resume/Retry re-fetch only outstanding work; Remove/Dismiss drops only the job-control record — never a snapshot, forward-return, or audit entry.
  - **Data removal is seed-safe & consistency-preserving.** Only user-added bars; committed seed never deletable; confirm-preview before deletion; whole-row cascade of solely-derived dependents — never an in-place snapshot mutation.
  - **Attribution is read-only.** Slices derived from stored per-observation forward returns; never recomputed.
  - **Exactly one date selector.** One global as-of control; the timeframe selector and the Research as-of toggle are not date controls; the `?asof` URL param (J-43) is the **serialization** of the single global state — never a second state; invalid `?asof` degrades to latest. *(critical)*
  - **Intraday stays deterministic & coverage-honest.** Committed seed only; per-timeframe no-lookahead; NA where history is insufficient.
  - **Universe screen is reproducible & honest.** Config-recorded screen; real committed data only; universe-relative/survivorship labels.
  - **Research lab is read-only, honest & not predictive.** Derived once from stored observations; composite cohort is a transparent rank-blend, never a fitted model; as-of mode only filters.
  - **New patterns are patterns, not statuses.** Follow the VCP contract.
  - **Risk-adjusted reporting is honest.** Downside vol / MAE / drawdown — never total volatility; raw and risk-adjusted side by side; NA + n.
  - **Startup must not block serving on historical warm-up.** Lifespan serves the latest snapshot fast; historical backfill warms in the background. *(operational)*
  - **Warm-up obeys every data invariant; idempotent, concurrency-safe, non-fatal.** Duplicate create returns the existing snapshot; warm-up failure logged, never fatal.
  - **Readiness is reported honestly.** serving-ready vs warming (with real progress) vs unavailable; never a still-loading aggregate presented as complete.
  - **Precomputed snapshot seed is a reproducible cache, never fabricated.** (optional accelerator — byte-reproducible only)
  - **One date format, displayed — ISO contracts unchanged.** Every user-facing date renders `yyyy-MM-dd` via one shared formatter/constant; date inputs validate the exact format; API/DB/config dates stay ISO.
  - **The `?asof` URL param is a serialization, not a second date state.** Restored through the one global control; invalid → latest view.
  - **Regime overlays read stored regime only.** Bands built from persisted per-run regime values; same date = same label/color everywhere; never past the resolved as-of.
  - **The index chart is honest and never data-gated.** A configured series without stored bars is omitted, never synthesized; renders fully without DIA; normalized % computed server-side.
  - **Parallel import preserves every import contract.** Rate-limit behavior, checkpoints, idempotency, honest progress, serialized/transactional writes — a faster pipeline must not regress J-34/J-37/J-38 semantics.
  - **Vectorized scans are a pure refactor.** Identical canonical outputs; strict per-date no-lookahead preserved.
  - **Glossary copy lives in one catalog.** Every definition and tooltip from the single config-backed catalog; never duplicated.

## GOAL

Establish a verified, evidenced baseline of the existing Trendora product — boot it offline against the committed seed and verify all 47 must-have journeys to record which already pass, which fail, and which are partial/blocked. **No code is written this iteration.**

## BACKGROUND

This is a baseline assessment, **not** a feature delivery. The prior session (`i_can_see_the_wealthy_future_forever`) reached GOAL_ACHIEVED at iter-28 on the J-01..J-41 set (commit `8c566d8`), and the operator then added six new Must-haves (commit `e0b5864`): **J-42** (ISO `yyyy-MM-dd` dates everywhere), **J-43** (deep-linkable `?asof`), **J-44** (dashboard major-indexes + regime-bands chart), **J-45** (regime bands on the stock-detail chart), **J-46** (parallel fetch + vectorized backfill + benchmark), **J-47** (full ≥100-term glossary + inline term help). This session verifies the carried 41 and builds the new 6. The goal-evaluator will mark already-passing journeys `already_passing` so later iterations target only real gaps/regressions. The companion blueprint at `runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/blueprint.md` is part of this baseline and has **already been human-approved** (`blueprint.approved` present) — it is left untouched this iteration.

**Decomposer file-scan signal (re-verified 2026-06-11 against the clean tree — evidence to guide QA, not a verdict):** all J-01..J-41 surfaces are present (pages `/`, `/stocks(/[ticker])`, `/themes`, `/sectors`, `/scanner-runs(/[runId])`, `/backtest`, `/watchlist`, `/methodology`, `/research`, `/data`; engine modules incl. `scanner`, `scoring`, `forward_testing`, `patterns`, `research`, `data_manager`, `readiness`/`warmup`). The six NEW journeys are expected NOT-implemented: no shared frontend date formatter exists and `/data` still uses native `type="date"` inputs (J-42); `components/asof-provider.tsx` contains no `?asof` URL read/write (J-43); no regime-history or index-series endpoint or chart component exists (J-44/J-45); no parallel worker-pool config key and no committed benchmark script (J-46); the only config "glossary" is the J-12 setup/pattern methodology catalog — no ≥100-term UI vocabulary catalog (J-47).

## IN SCOPE

### Backend
- [ ] None — baseline is verify-only (no code changes).

### Frontend
- [ ] None — baseline is verify-only (no code changes).

### Verification activities (no code changes)
- [ ] Boot the backend offline against the committed seed (`bash scripts/start-backend.sh`, port 8835); confirm `GET /api/health` reports `ready` (or honest `initializing` progress that flips to ready) with no network/keys.
- [ ] Start the frontend (`bash scripts/start-frontend.sh`, port 3835); confirm pages hydrate (if every page is a dead un-hydrated shell, that is the known `.next`-cache condition — record SKIPPED with reason, not FAIL).
- [ ] Run the backend unit suite once (`cd apps/backend && .venv/bin/python -m pytest tests/ -v` — ~14 min; never two pytest invocations concurrently); record pass/fail counts. Do not modify tests.
- [ ] Verify all 47 journeys per the TESTING REQUIREMENTS verification bases below; record pass / fail / partial / blocked-NA per journey with evidence.

### New user-facing capability
None — this iteration delivers a verified baseline, not new capability.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — the product is exercised, not changed.

### Blueprint conformance
No new surfaces. The session blueprint (Information Architecture + Data Contract) already exists at `runs/goal-session-i_can_see_the_wealthy_future_forever_with_my_loved_ones/state/blueprint.md` and is human-approved; its J-42..J-47 [TARGET] rows are the contract iter-1+ builds to.

### Data-contract additions
None this iteration (the blueprint already registers the J-42/J-44/J-45/J-47 TARGET values for future iterations; J-43 amends the existing resolved-as-of row; J-46 adds no displayed value).

## OUT OF SCOPE

- Any code change, refactor, dependency upgrade, or UI edit.
- Fixing journeys that fail — failures are recorded for later iterations to address, not fixed here.
- Live-provider fetches (the committed offline seed only; live legs of J-22/J-23/J-24/J-33/J-34/J-35/J-37/J-38 are recorded honestly as blocked/NA, non-halting).
- Destructive operations against the live DB — **never** run the real `POST /api/data/remove` against a live symbol (NVDA carries user-added bars beyond the seed; `trendora.db` is gitignored and unrestorable). Use the read-only preview endpoint only.
- Tuning `config.yaml` weights/thresholds.
- Editing the approved blueprint.

## DEFINITION OF DONE

- [ ] Every must-have journey (J-01 … J-47) is verified against the current state with a pass / fail / partial / blocked-NA result and evidence recorded for the evaluator.
- [ ] The backend boots offline on the seed with honest readiness; the frontend serves hydrated pages.
- [ ] The backend unit suite has been run once and its counts recorded (including the no-lookahead, snapshot-immutability, and warm-up concurrency tests — baseline-critical).
- [ ] No anti-goal violation is introduced (none can be — no code changes).
- [ ] The coherence blueprint exists at the session `state/blueprint.md` (already drafted and human-approved).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-0-dev.md` recording the verify-only no-op and pointing to the journey results.

## TESTING REQUIREMENTS

- **Browser (full journey verification):** J-01 (dashboard), J-02 (leaderboard filters), J-03 (themes), J-04 (sectors), J-05 (stock detail), J-06 (score consistency), J-07 (Risk-Off gating), J-08 (immutable run history), J-09/J-10 (backtest evidence + control groups, as-of-scoped), J-11 (watchlist persistence incl. restart-survival), J-12 (glossary + inline setup/pattern explanations), J-13 (global as-of switcher), J-14 (per-date scorecard incl. honest NA), J-15 (fast warm loads), J-16 (VCP end-to-end), J-17 (Data Manager coverage/job UI), J-18 (one date control — judge on "no page-local independent date state", NEVER on URL date-freeness), J-19 (attribution), J-20 (through-latest chart + as-of marker), J-21 (cohorts below attribution + horizon-linked returns), J-25–J-32 (Research labs + as-of mode), J-33/J-34/J-36 (Data Manager import source/resumable/coverage surfaces), and the six NEW journeys **J-42, J-43, J-44, J-45, J-47** (expected FAIL — record precisely what is missing) plus J-46's UI-adjacent progress accuracy if observable.
- **API-layer / test-suite verification basis (browser capture NOT a gate, per `docs/goal.md`):** J-35, J-37, J-38, J-39 — verify via the running backend's `/api/data` behavior + the green test suite, per their re-scoped "Verification basis" sections. J-40/J-41 — verify via `GET /api/health` readiness behavior + the existing integration/unit tests. J-46 — source-scan (no worker-pool config, no benchmark script) is sufficient evidence of FAIL.
- **Data-walled (record blocked-NA, non-halting):** J-22 (~500-name universe), J-23/J-24 (intraday seed + timeframe selector), and the live-fetch legs of J-33/J-34/J-35/J-37/J-38. One best-effort live probe at most; never an autonomous retry loop.
- **Unit/integration:** the full pytest suite once; confirm the no-lookahead, snapshot-immutability, and `run_scan` concurrency-race tests exist and report their result.
- **Error cases:** record (not fix) any journey whose acceptance criteria are unmet; an honest NA (short horizon, low sample, missing DIA series) is a *pass* of honesty, not a fail.

## NOTES

- **Likely outcome:** J-01..J-21, J-25..J-41 already passing (carry `already_passing`); J-22/J-23/J-24 blocked-NA; J-42..J-47 failing. Subsequent iterations should target only the failing six.
- **Applied lessons (episodic memory / lessons ledger):**
  - Backend boot: serve-fast lifespan + background warm-up landed in iter-28 — a warming backend reads "Initializing (n/m)", not unavailable; if a page shows "Backend unavailable" wait for warm-up or do one clean restart; the DB is warm on this host.
  - Browser QA: if every page is a dead un-hydrated shell (404 on `_next/static/...`), the dev server's `.next` was clobbered by a prod build — record SKIPPED, not FAIL.
  - Chrome MCP `select` doesn't fire React onChange on this frontend — use the native-setter + bubbled change event, then assert live DOM.
  - J-18 vs J-43: `?asof=` in the URL when historical is REQUIRED by J-43 and is the serialization of the one global state — never judge J-18 against a date-free URL. `/api/stocks?as_of=` on fetches is the single global date transmitted, not a second state.
  - To exercise the J-34 amber resumable surface offline-safely, the alpha_vantage `demo` key path induces a real RateLimitError; the env-gated `seed` import source (`TRENDORA_ENABLE_SEED_IMPORT_SOURCE`) drives deterministic pull/expand flows without network.
  - Kill dev servers by port (8835/3835), never by broad `pkill -f` patterns, on this multi-project machine.
- If verification finds all 47 journeys already passing (unexpected), the evaluator should consider GOAL_ACHIEVED — do not manufacture work; report the true state.
- Journeys assert relational/structural properties (same value in two places, ordered buckets, zero Actionable in Risk-Off, a number renders) — never exact score values.
