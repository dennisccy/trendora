# Goal Iteration 0 (Baseline) — Trendora `i_can_see_the_wealthy_future_forever`

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15, J-16, J-17, J-18, J-19 (ALL must-have journeys)
- **Required-still-passing journeys:** N/A — baseline establishes the initial pass/fail/partial state; nothing is established yet
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere; the default seed path requires none, and any live-provider key is read only from the environment.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Scores must be explainable.** Every displayed score MUST carry its named component breakdown — no score may be shown as a bare number with no reasons.
  - **Honest limitations surfaced.** Breadth and new-high/new-low metrics computed from the seed universe MUST be labelled "universe-relative"; walk-forward evidence MUST be labelled as carrying survivorship bias.
  - **Frontend MUST NOT store auth tokens in `localStorage`** (applies only if auth is ever added; this version has no auth).
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **On-demand snapshots stay immutable & lookahead-free.** Creating a snapshot for a newly selected date is create-once: read an existing snapshot, never overwrite; an as-of-D snapshot uses only bars ≤ D. *(critical)*
  - **Setup & pattern vocabulary is config-driven in the UI too.** The glossary and tooltips MUST be generated from the single config-backed catalog — no hard-coded per-entry copy or status/pattern list in the frontend.
  - **Honest forward-test for partial windows.** The per-date forward-test scorecard and the VCP-vs-non-VCP breakdown MUST show NA/partial for horizons/cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate.
  - **VCP is a pattern, not a status.** VCP MUST NOT enter the mutually-exclusive setup-status enum and MUST NOT by itself promote a name to "Actionable"; it rides as a separate flag, price+volume only, date ≤ D, part of the immutable snapshot, thresholds from config. *(critical)*
  - **Live fetch is real-data-only.** The Data Manager MUST use the config-selected live provider to fetch real EOD bars; on failure it MUST surface an explicit error and MUST NOT synthesize prices. *(extends No fabricated data)*
  - **Range backfill stays immutable & lookahead-free.** Snapshots created for a fetched/backfilled range are create-once: read existing, never overwrite; as-of-D uses only bars ≤ D.
  - **Attribution is read-only.** The attribution slices MUST be derived from stored per-observation forward returns; the API and frontend MUST NOT recompute returns to build them. *(extends No recompute in the read path)*
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. *(extends Single source of truth)*

## GOAL

Establish a verified, evidenced baseline of the existing Trendora product — boot it offline against the committed seed and run all 19 must-have journeys to record which already pass, which fail, and which are partial. **No code is written this iteration.**

## BACKGROUND

This is a baseline assessment, **not** a feature delivery. The decomposer writes no Backend/Frontend scope; the developer step is a no-op and the value comes entirely from running every journey against the current tree (browser QA + the unit suite). The prior goal session (`i_can_see_the_wealthy_future`) reached GOAL_ACHIEVED at iter 12 building this same Trendora codebase, so this session likely starts with most or all journeys already implemented — the point of the baseline is to *verify* that against the current working tree and seed, not to assume it. The goal-evaluator will mark already-passing journeys `already_passing` so later iterations skip them and target only real gaps/regressions. The companion blueprint at `runs/goal-session-i_can_see_the_wealthy_future_forever/state/blueprint.md` is part of this baseline and is the artifact the loop pauses on for human approval.

## IN SCOPE

### Backend
- [ ] None — baseline is verify-only (no code changes).

### Frontend
- [ ] None — baseline is verify-only (no code changes).

### Verification activities (no code changes)
- [ ] Boot the backend offline against the committed seed (`bash scripts/start-backend.sh`); confirm `GET /api/health` returns ok with no network/keys.
- [ ] Build the frontend (`cd apps/frontend && npm run build`) — compiles + typechecks clean.
- [ ] Run the backend unit suite (`cd apps/backend && .venv/bin/python -m pytest tests/ -v`); record pass/fail counts (do not modify tests to make them pass).
- [ ] Start the frontend (`bash scripts/start-frontend.sh`) and run all 19 must-have journeys via browser-qa-agent; record pass / fail / partial per journey with evidence (screenshots/logs).

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
No new surfaces. This iteration also produces the blueprint (Information Architecture + Data Contract) for human approval.

### Data-contract additions
None.

## OUT OF SCOPE

- Any code change, refactor, dependency upgrade, or UI edit.
- Fixing journeys that fail — failures are recorded for later iterations to address, not fixed here.
- Re-fetching live data mid-loop (the build/verify loop reads only the committed offline seed).
- Tuning `config.yaml` weights/thresholds.

## DEFINITION OF DONE

- [ ] Every must-have journey (J-01 … J-19) is verified against the current state, with a pass / fail / partial result and evidence recorded for the evaluator.
- [ ] The backend boots offline on the seed and `/api/health` is green; the frontend builds.
- [ ] The backend unit suite has been run and its pass/fail counts recorded (including the no-lookahead and snapshot-immutability tests, which are baseline-critical).
- [ ] No anti-goal violation is introduced (none can be — no code changes).
- [ ] The coherence blueprint exists at the session `state/blueprint.md` for human approval.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-0-dev.md` recording the verify-only no-op and pointing to the journey results.

## TESTING REQUIREMENTS

- **Browser:** all 19 journeys — J-01 (dashboard), J-02 (leaderboard filters), J-03 (themes), J-04 (sectors), J-05 (stock detail), J-06 (score consistency), J-07 (Risk-Off gates Actionable), J-08 (immutable run history), J-09 (System Health evidence), J-10 (control-group honesty), J-11 (watchlist persistence — incl. backend restart), J-12 (glossary + inline), J-13 (global as-of switcher), J-14 (backtest scorecard incl. NA for short windows), J-15 (fast loads from snapshots), J-16 (VCP detected/explained/filterable/forward-tested), J-17 (grow dataset via Data Manager), J-18 (one date control / no duplicate), J-19 (attribution).
- **Unit/integration:** run the existing pytest suite; specifically confirm the no-lookahead guarantee and snapshot-immutability tests exist and report their result.
- **Error cases:** record (not fix) any journey whose acceptance criteria are unmet; note partials (e.g. a horizon showing NA honestly is a *pass*, not a fail).

## NOTES

- Journeys assert **relational/structural** properties (same value in two places, buckets ordered, zero Actionable in Risk-Off, a number renders, filters change rows) — **not** exact score numbers — so verification must not depend on specific score values.
- Watch for the as-of-date contract during verification: J-13 and J-18 require that the single global switcher drives every date-scoped page (including Backtest) and that no page keeps its own date picker.
- If verification finds all 19 journeys already passing on the current tree, the evaluator should consider GOAL_ACHIEVED (or near-it); do not manufacture work — report the true state.
- **Baseline file-scan signal** (decomposer evidence to guide QA — *not* a pass/fail verdict): the Data Manager surface required by J-17 (a `/data` page, an `/api/data` router, a data-manager engine module, a `data`/`data_manager` `config.yaml` section) was **NOT found** in the current tree, so J-17 is expected NOT-implemented. Commit `043a456` claims "Data Manager, unified as-of date control, and return attribution," but its Data Manager files are absent — so do **not** assume J-18 (no page-local date picker on `/backtest`) or J-19 (attribution on `/system-health` + `/backtest`) are present either; verify them explicitly. **Confirmed-present surfaces (J-01…J-16):** pages `/`, `/stocks`, `/stocks/[ticker]`, `/themes`, `/sectors`, `/scanner-runs(/[runId])`, `/system-health`, `/watchlist`, `/methodology`, `/backtest`; routers dashboard/stocks/sectors/themes/runs/system_health/watchlist/methodology/backtest/health; engine modules incl. `scanner`, `scoring`, `forward_testing`, `patterns`, `snapshot_serving`, `methodology`.
