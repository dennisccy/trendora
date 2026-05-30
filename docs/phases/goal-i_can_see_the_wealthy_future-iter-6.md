# Goal Iteration 6 — Walk-forward forward-testing engine + System Health evidence (J-09, J-10)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-09, J-10
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Honest limitations surfaced.** Breadth and new-high/new-low metrics MUST be labelled "universe-relative"; **walk-forward evidence MUST be labelled as carrying survivorship bias** (current-membership universe) so results are never overstated.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)* — must not regress (J-07).
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable. *(critical)*
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere.

## GOAL

Deliver the keystone "prove its own usefulness" capability: a strict no-lookahead **walk-forward forward-testing engine** that replays scans as-of past dates and measures realized 1/5/10/20/60-day forward returns from post-snapshot data, surfaced on a populated **System Health** page — forward return by score bucket (A–E), by setup, and by regime; excess vs SPY/QQQ/sector; and a control-group comparison (top-ranked cohort vs random same-sector cohort vs SPY/QQQ/sector-ETF) — every cell carrying its sample size `n` and a survivorship-bias label.

## BACKGROUND

iter-5 landed the immutable snapshot spine (J-07, J-08): `scanner_runs` + child result tables, `run_scan` (idempotent, INSERT-only), and `GET /api/runs`. All ten earlier journeys hold; J-01–J-08 are green. This iteration consumes the **scaffolded `walk_forward` config** (`history_years: 2`, `asof_cadence: weekly`, `horizons: [1,5,10,20,60]`, `min_sample: 30`) — currently real config but unused — to build the forward direction of no-lookahead. It is the hardest anti-goal test yet: scoring already proves *date ≤ D* via `bars_asof`; now forward returns must prove *date > D* via a strict inverse accessor, and the realized returns must live in a **separate append-only table** so the immutable snapshot is never mutated. The forward-return aggregates value is **already registered in the Data Contract** (`app.engine.forward_testing:compute_forward_aggregates` → `GET /api/system-health`); this iteration creates that module, the `forward_returns` table, and the page that graduates from its iter-1 EmptyState stub. The evaluator (per the roadmap and iter-5 recommendation) scoped iter-6 = J-09 + J-10; J-11 (Watchlist) is iter-7.

**Applied lessons (from `lessons.md`):**
- **iter-2 lesson (future-duplicate risk):** the contract attributes forward-return aggregates to `app.engine.forward_testing:compute_forward_aggregates`. Use that **exact** module/function name and the **exact** table name `forward_returns` and endpoint `GET /api/system-health` so the coherence-auditor finds no drift. The aggregates engine must **READ** the stored canonical bucket/setup/sector from `scanner_results` — it must NEVER recompute a score, bucket, or setup from a second formula.
- **iter-3 / iter-5 lessons (harness, not product):** the dedicated browser-qa SKIP-vs-PASS flap and the missing audit handoff are **runner-script** gaps that spec/DoD text has demonstrably failed to fix across 5 iterations. They are **NOT** in this spec's product DoD (see NOTES → "Known harness gaps"). The evaluator should reconcile J-09/J-10 from on-disk QA evidence PNGs + unit/API proofs + direct source reads, never from a lone browser-qa SKIP.

## IN SCOPE

### Backend

- [ ] **New no-lookahead forward accessor** in `app/engine/prices.py`: `bars_after(session, symbol, d)` → all bars for `symbol` with **date > d**, ascending (the strict inverse of `bars_asof`'s `date ≤ d`). This is the forward no-lookahead boundary.
- [ ] **New append-only table** `forward_returns` in `app/models.py`, keyed `(run_id, symbol, horizon)` (unique together): the realized forward return of a `symbol` over `horizon` trading days, measured from `bars_after(run.asof_date)`. `symbol` covers universe stocks **and** the benchmark ETFs (SPY, QQQ, the 11 sector ETFs). INSERT-only — never UPDATEd; keyed to the snapshot so the snapshot itself is never mutated. Store enough to make excess a stored subtraction (the realized return; horizon; symbol). Honor the "No SQLite-only SQL / Postgres-ready" rule.
- [ ] **New engine module** `app/engine/forward_testing.py`:
  - `forward_return(bars_after_list, entry_close, horizon)` (pure): realized return = `close[h-th post-bar] / entry_close − 1`, where `entry_close` is the close **on** `asof_date` (≤ D). Returns NA (`None`) when fewer than `horizon` post-snapshot bars exist — never a fabricated/truncated number. Horizons come from `config.walk_forward.horizons` (no literal).
  - `backfill_forward_returns(session_or_engine, config)`: idempotent, frozen-seed-only (like `bootstrap_runs`). (1) Generate the walk-forward as-of date set from `config.walk_forward.{history_years, asof_cadence}` intersected with actual seed trading days; (2) persist a `scanner_run` snapshot for each by calling the **existing idempotent `run_scan`** (recompute nothing — the snapshot is the canonical bucket/setup/sector source); (3) for every persisted run with ≥1 post-snapshot bar, INSERT the per-`(run, symbol, horizon)` realized returns for all universe stocks + benchmark ETFs. Idempotent: a second boot inserts no duplicates.
  - `compute_forward_aggregates(session, horizon, config)`: the **single** canonical aggregation. READS stored `scanner_results` (bucket/setup/sector/rank/leadership — verbatim, never recomputed) joined with stored `forward_returns`, and returns, for the requested horizon: **by-bucket (A–E)** mean return + n; **by-setup** mean + n; **by-regime** mean + n (regime from the run's stored `regime_label`); **excess vs SPY** and **excess vs QQQ** (mean stock return − mean benchmark return over matched runs); and the **control-group cohorts** — top-ranked cohort, random-same-sector cohort, SPY, QQQ, and sector-ETF — each numeric, labelled, with n. Every cell carries `n`; the payload carries a `survivorship_bias` honesty label and a `min_sample` threshold from config. Runs with no post-snapshot bars contribute n=0 (excluded), never a fabricated 0%.
- [ ] **Config (additive, no magic numbers):** add `walk_forward.control_group: { seed: <int>, top_n: <int>, peers_per_sector: <int> }` to `config.yaml`. The random-same-sector cohort is drawn with a **config-seeded** deterministic RNG (reproducible across restarts — never `random` without the config seed). The top-ranked cohort cutoff (`top_n`) and per-sector peer count come from config. No new scoring literal in calc code.
- [ ] **New endpoint** `GET /api/system-health` in `app/api/system_health.py` (router registered in `main.py` under `/api`): query param `horizon` (default a stated horizon = **20**; validated ∈ `config.walk_forward.horizons`, else 422). Returns `compute_forward_aggregates(...)` verbatim. `503` when no price data exists; honest low-sample / empty states (no fabrication). Wire `backfill_forward_returns` into the lifespan after `bootstrap_runs` (idempotent).

### Frontend

- [ ] Replace the `/system-health` EmptyState stub (`apps/frontend/app/system-health/page.tsx`) with the evidence dashboard, in the established dense-dark workstation style (shared `Card`, `PageHeading`, `ScoreBadge`/bucket colours, tabular-nums for all numbers):
  - A **horizon selector** (1 / 5 / 10 / 20 / 60), default 20, that re-fetches `GET /api/system-health?horizon=…`.
  - **Forward return by score bucket** table (rows A–E) — mean return + `n` per bucket (J-09).
  - **Excess vs SPY** and **Excess vs QQQ** — numeric (J-09).
  - **By setup type** and **By market regime** breakdowns — each numeric + `n` (J-09).
  - **Control-group comparison** panel (J-10): top-ranked cohort, random same-sector cohort, SPY, QQQ, and sector ETF — each numeric, labelled, with `n`, at the selected horizon.
  - A prominent **survivorship-bias** disclaimer and **sample sizes (`n`) shown beside every figure**; low-sample (n < `min_sample`) figures visibly flagged (warn token). Positive/negative returns use the pos/neg palette tokens.
  - All values come from the single `/api/system-health` payload — the page **re-formats only**, never recomputing a return, excess, or bucket.

### New user-facing capability

The user can open **System Health** and read hard, forward-tested evidence — whether higher-ranked buckets, stronger setups, and risk-on regimes actually produced better realized forward returns than SPY/QQQ/sector ETFs and than random same-sector peers — at a chosen horizon, with sample sizes and an explicit survivorship-bias caveat so the evidence is never overstated.

### New information displayed

Forward return by bucket A–E (mean + n); excess vs SPY and QQQ; forward return by setup type and by regime (+ n); a control-group table (top-ranked vs random-same-sector vs SPY/QQQ/sector-ETF, + n); a survivorship-bias label and per-figure sample sizes.

### New user actions

Select a forward-return horizon (1/5/10/20/60) on `/system-health` and see all tables/panels update.

### UI surface changes

`/system-health` graduates from an EmptyState stub to a populated, multi-panel evidence dashboard. No other page changes. Sidebar unchanged (System Health link already present).

### Product surface delta

Trendora moves from "it ranks and explains" to "it ranks, explains, **and shows whether the rankings have positive forward-tested evidence**" — the product's core trust-earning promise. The Scanner Runs history (J-08) now also includes the walk-forward cadence snapshots (more dated runs), which is the intended product behavior (immutable as-of history), not a regression.

### Blueprint conformance

All new work lives under the existing **System Health** Information-Architecture home (`/system-health`, already in the sidebar nav). No nav-skeleton change → **no** `blueprint.reapproval-requested`. The iter-6 serving note has been added to `blueprint.md` (Iteration serving notes section); the Data Contract row for forward-return aggregates was already registered at baseline.

### Data-contract additions

**No new contract row** — the forward-return aggregates value is already registered (`app.engine.forward_testing:compute_forward_aggregates` → `GET /api/system-health`, with the `forward_returns` append-only table named in its Notes). This iteration *implements* that registered row. The new `forward_returns` table and `bars_after` accessor are implementation of that single registered value; the iter-6 serving note in `blueprint.md` documents them. **Never introduce a second computation or endpoint** for any value already in the contract — buckets/setups/sectors/regime are READ from the stored snapshot (`scanner_results` / `scanner_runs`), not recomputed.

## OUT OF SCOPE

- **J-11 Watchlist** (persistence) — iter-7.
- The optional live EOD provider / any network fetch — the backfill reads ONLY the committed frozen seed.
- Editing scoring weights from a config view; historical charts of a stock's scores (nice-to-haves).
- Re-pointing or modifying any existing endpoint (`/api/dashboard`, `/api/stocks`, `/api/sectors`, `/api/themes`, `/api/stocks/{ticker}/bars`, `/api/runs`, `/api/runs/{run_id}`) — they must stay byte-for-byte behaviourally identical so J-01–J-08 cannot regress.
- Any order/execution/brokerage/paper-portfolio code path.

## DEFINITION OF DONE

- [ ] **J-09** passes via browser-qa-agent: `/system-health` renders a by-bucket (A–E) forward-return table with numeric means at a stated horizon, numeric excess-vs-SPY and excess-vs-QQQ, a by-setup-type breakdown, and a by-regime breakdown — each with sample size `n` shown, derived from the walk-forward snapshots.
- [ ] **J-10** passes via browser-qa-agent: the control-group panel shows, at a stated horizon, the top-ranked cohort's forward return alongside a random-same-sector cohort and SPY/QQQ/sector-ETF returns — each numeric and labelled.
- [ ] Required-still-passing journeys **J-01–J-08 remain green** (live + run endpoints untouched; re-shoot or reconcile from evidence).
- [ ] No anti-goal violation introduced — in particular: forward returns use only `bars_after` (date > D); `forward_returns` is INSERT-only and the snapshot is never mutated; aggregates read stored buckets/setups (single source); horizons/min_sample/control-group params come from config; survivorship-bias label + per-figure `n` are present; no order path; no secrets.
- [ ] Unit + integration tests pass (see TESTING REQUIREMENTS); backend `pytest` green; frontend `npm run build` green; coherence audit PASS.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-6-dev.md`, documenting the chosen walk-forward cadence + as-of date count + first-boot backfill time, and confirming both Risk-on and Risk-off as-of dates are present in the by-regime sample.

## TESTING REQUIREMENTS

- **Browser (Chrome MCP, by ID):** **J-09** and **J-10** on `/system-health` — assert structural/relational properties (a by-bucket A–E table renders numbers; excess-vs-SPY and excess-vs-QQQ render numbers; by-setup and by-regime render numbers; the control-group panel shows top-ranked vs random-same-sector vs SPY/QQQ/sector-ETF; `n` and a survivorship-bias caveat are visible; the horizon selector changes the figures). Do NOT assert exact return numbers.
- **No-lookahead boundary (THE keystone — unit):**
  - `bars_after(session, sym, d)` returns only bars with date > d (none with date ≤ d), ascending.
  - `forward_return` for horizon h is unchanged when bars with date > d+h are removed (only the first h post-bars matter); it is NA when fewer than h post-snapshot bars exist; entry close is the close on d.
  - Prove no future bar influences an as-of score: a run's stored scores are byte-identical whether or not post-snapshot bars / `forward_returns` exist (forward returns never feed back into a snapshot).
- **Immutability (unit/integration):** computing/backfilling forward returns performs only INSERTs — no UPDATE/overwrite of any `scanner_runs` / `scanner_results` / `*_scores` row (assert row counts + a faithful-equality check on a pre-existing run before/after backfill); `backfill_forward_returns` is idempotent (second call inserts zero new `forward_returns` rows).
- **Single source / aggregates correctness (unit):** on a small hand-built fixture, `compute_forward_aggregates` yields the exact by-bucket / by-setup / by-regime means, excess vs SPY/QQQ, control-group cohort means, and `n` you compute by hand; assert the by-bucket grouping uses `scanner_results.leadership_bucket` (or the relevant stored bucket) verbatim — no re-bucketing.
- **No magic numbers (unit):** extend the no-literal guard to `forward_testing.py` (and `prices.bars_after`) — horizons, min_sample, history_years, asof_cadence, and control-group `{seed, top_n, peers_per_sector}` all read from config.
- **Control-group determinism (unit):** same config seed → identical random-same-sector cohort across two calls / a simulated restart (reproducibility).
- **No fabrication (unit/integration):** a run with zero post-snapshot bars (the latest seed-date run) contributes n=0 and no fabricated return; the by-regime breakdown contains BOTH a Risk-on and a Risk-off entry given the seeded as-of dates.
- **API (integration):** `GET /api/system-health` returns by-bucket/setup/regime + excess + control groups, each with `n` and the survivorship label, for a default and a non-default horizon; an out-of-range `horizon` is rejected (422); `503` when no price data; the iter-5 `/api/runs` and the live endpoints are unaffected (J-01–J-08 regression guard).
- **Error cases:** invalid/unknown horizon → 422; empty/low-sample buckets render an explicit low-sample state (n shown), not a hidden or fabricated number.

## NOTES

- **Walk-forward window must span both regimes.** The configured 2-year as-of window (ending far enough before the latest seed date to leave ≥60 post-snapshot bars) includes the known Risk-off seed date **2025-04-04**, so the by-regime breakdown will contain both Risk-on and Risk-off evidence. Verify against the seed; if the cadence misses a risk-off stretch, widen via `walk_forward.history_years`/`asof_cadence` (config, not code). The existing bootstrap runs (2022-10-07, 2025-04-04, latest) remain; the latest run (no post-bars) is the natural n=0 demonstration.
- **First-boot cost.** The backfill calls `run_scan` once per cadence as-of date (idempotent), then computes forward returns — the first boot of a fresh DB is slower than iter-5's 3-run bootstrap; subsequent boots skip already-persisted work. Keep the as-of set bounded enough that the first boot stays tractable while the 60-day-horizon sample meets/▸reports `walk_forward.min_sample` (30). Document the chosen cadence + first-boot time in the handoff. A longer first boot can aggravate the browser-qa HTTP-000 readiness flap — see below.
- **Known harness gaps (route to the runner/orchestrator — NOT product scope, and NOT gating this iteration's DoD).** Per `lessons.md` (iter-3, iter-5), these are chronic runner-script gaps that spec/DoD text has demonstrably failed to fix; the durable fix is in `scripts/automation/*.sh`, not here:
  1. **Dedicated browser-qa must own/self-heal its frontend** (5 consecutive SKIP-on-HTTP-000 flaps). The fix belongs in `scripts/automation/browser-qa-phase.sh` (start/await the frontend the way QA mode-2 does), ideally with an extended readiness timeout to absorb iter-6's longer first-boot backfill. Until fixed, the evaluator MUST reconcile J-09/J-10 from the on-disk QA evidence PNGs + unit/API proofs + direct source reads, never from a lone browser-qa SKIP.
  2. **Emit the audit handoff** (`reports/audits/` has not existed for 5 full-depth iters). The fix belongs in the runner/audit step (`scripts/automation/phase-audit.sh`), not the spec.
  These are surfaced here only so whoever drives the runner can finally apply the script-level fix; they do not block J-09/J-10.
- **Evaluator guidance (flaky-harness lesson, iter-4):** under a queuing/flaky tool harness, a negative file-existence result is not trustworthy — re-confirm evidence PNGs with `ls`/Glob before letting "missing evidence" lower a verdict; treat demo-narrator Playwright soft-notes as non-gating capture-timing artifacts.
