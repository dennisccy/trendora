# goal-i_can_see_the_wealthy_future-iter-6 Execution Plan

**Walk-forward forward-testing engine + populated System Health evidence — J-09, J-10.**
Delivers the product's keystone "prove its own usefulness" capability: a strict no-lookahead engine
that replays scans as-of past dates and measures realized 1/5/10/20/60-day forward returns from
**post-snapshot** data, surfaced on a populated `/system-health` dashboard (returns by bucket / setup /
regime, excess vs SPY/QQQ, and a control-group comparison — every cell with sample size `n` and a
survivorship-bias label). This is the hardest anti-goal test yet: scoring already proves *date ≤ D*;
forward returns must now prove *date > D* through a strict inverse accessor, with realized returns in a
**separate append-only table** so the immutable snapshot is never mutated.

Frontend Present: yes

## Goal Alignment / Drift Check

- **On-goal, on-roadmap.** Roadmap iter-6 = "Walk-forward + forward returns + aggregates + control
  groups + System Health → J-09, J-10." Spec matches exactly. Directly realizes goal.md Success Criteria
  #5 (the walk-forward forward-testing engine) and Key Capabilities #10–#11.
- **Blueprint-conformant — no new contract row, no nav change.** The forward-return aggregates value is
  **already registered** in the Data Contract (`app.engine.forward_testing:compute_forward_aggregates` →
  `GET /api/system-health`, with the `forward_returns` append-only table named in its Notes). This
  iteration *implements* that registered row. `/system-health` is already the sidebar IA home for
  J-09/J-10 and the iter-6 serving note is already in `blueprint.md` → **no `blueprint.reapproval-requested`.**
- **No drift / no scope creep.** Out-of-scope items (J-11 Watchlist, live EOD provider/network fetch,
  config-edit views, historical score charts, re-pointing any existing endpoint, any
  order/execution/brokerage path) are excluded per spec. No anti-goal conflict. Nothing to flag as drift.

## What to Build

**Backend — the forward direction of no-lookahead (reads stored snapshots, recomputes NO score):**

- **`app/engine/prices.py`** — add `bars_after(session, symbol, d)` → all bars for `symbol` with
  **date > d**, ascending. The strict inverse of the existing `bars_asof` (date ≤ d); this is the
  forward no-lookahead boundary. (Keep `bars_asof` byte-identical.)
- **`app/models.py`** — add ONE new append-only table `ForwardReturn` (`__tablename__ =
  "forward_returns"`), unique together on `(run_id, symbol, horizon)`. Columns: `run_id`
  (FK `scanner_runs.id`), `symbol` (universe stocks **and** benchmark ETFs — SPY, QQQ, the 11 sector
  ETFs), `horizon` (int trading days), `realized_return` (float; the stored value so excess is a stored
  subtraction), plus the entry/measurement context needed to keep it auditable (e.g. `entry_close`,
  `asof_date`). INSERT-only — never UPDATEd; keyed to the snapshot so the snapshot itself is never
  mutated. Integer PK, ISO dates, Postgres-ready (no SQLite-only SQL). Update the module docstring
  (forward_returns graduates from DESIGNED-but-not-created; `paper_portfolio*` stays not-created).
- **`app/engine/forward_testing.py`** *(new)* — the Data Contract's exact module name:
  - `forward_return(bars_after_list, entry_close, horizon)` *(pure)* — realized return =
    `close[h-th post-bar] / entry_close − 1`, where `entry_close` is the close **on** `asof_date` (≤ D)
    and the post-bars come from `bars_after` (date > D). Returns `None` (NA) when fewer than `horizon`
    post-snapshot bars exist — never a fabricated/truncated number. Horizons from
    `config.walk_forward.horizons` (no literal).
  - `backfill_forward_returns(session_or_engine, config)` — idempotent, frozen-seed-only (mirrors
    `scanner.bootstrap_runs`). (1) Generate the walk-forward as-of date set from
    `config.walk_forward.{history_years, asof_cadence}` **intersected with actual seed trading days**;
    (2) persist a `scanner_run` snapshot for each by calling the **existing idempotent `run_scan`**
    (recompute nothing — the snapshot is the canonical bucket/setup/sector source); (3) for every
    persisted run with ≥1 post-snapshot bar, INSERT the per-`(run, symbol, horizon)` realized returns
    for all universe stocks + benchmark ETFs. Idempotent: a second boot inserts **zero** duplicates.
  - `compute_forward_aggregates(session, horizon, config)` — the **single** canonical aggregation.
    READS stored `scanner_results` (bucket / setup / sector / rank / leadership — **verbatim, never
    recomputed**) joined with stored `forward_returns`, and returns for the requested horizon:
    **by-bucket (A–E)** mean + n; **by-setup** mean + n; **by-regime** mean + n (regime from the run's
    stored `regime_label`); **excess vs SPY** and **excess vs QQQ** (mean stock return − mean benchmark
    return over matched runs); and the **control-group cohorts** — top-ranked cohort, random-same-sector
    cohort, SPY, QQQ, sector-ETF — each numeric, labelled, with n. Every cell carries `n`; the payload
    carries a `survivorship_bias` honesty label and a `min_sample` threshold from config. Runs with no
    post-snapshot bars contribute n=0 (excluded), never a fabricated 0%.
- **`config.yaml`** — additive only: add `walk_forward.control_group: { seed: <int>, top_n: <int>,
  peers_per_sector: <int> }`. The random-same-sector cohort is drawn with a **config-seeded**
  deterministic RNG (re-seeded from `control_group.seed` each computation → reproducible across calls
  and restarts; never bare `random`). `top_n` = top-ranked cutoff; `peers_per_sector` = per-sector peer
  count. No new scoring literal in calc code.
- **`app/config.py`** — promote `walk_forward` from the scaffolded `extra="allow"` passthrough to a typed
  `WalkForwardCfg` (`history_years`, `asof_cadence`, `horizons: list[int]`, `min_sample`, and
  `control_group: ControlGroupCfg{seed, top_n, peers_per_sector}`); wire `walk_forward: WalkForwardCfg`
  into `Config`. Mirror the iter-5 `ScannerCfg` pattern (validation, no silent default). Update shared
  test config fixtures that now need a `walk_forward` section.
- **`app/api/system_health.py`** *(new, router registered in `main.py` under `/api`)* —
  `GET /api/system-health` with query param `horizon` (default **20**; validated ∈
  `config.walk_forward.horizons`, else **422**). Returns `compute_forward_aggregates(...)` verbatim.
  **503** when no price data exists; honest low-sample / empty states (no fabrication).
- **`main.py`** — register `system_health.router`; wire `backfill_forward_returns(engine, config)` into
  the lifespan **after** `bootstrap_runs` (idempotent; coexists with the existing bootstrap).

**Frontend — graduate the System Health stub to the evidence dashboard (re-format only, never recompute):**

- **`apps/frontend/app/system-health/page.tsx`** — replace the EmptyState stub with the dense-dark
  evidence dashboard (shared `Card`, `PageHeading`, `ScoreBadge`/bucket colours, `tabular-nums`):
  - A **horizon selector** (1 / 5 / 10 / 20 / 60), default 20, that re-fetches `GET /api/system-health?horizon=…`.
  - **Forward return by score bucket** table (rows A–E) — mean return + `n` per bucket (J-09).
  - **Excess vs SPY** and **Excess vs QQQ** — numeric (J-09).
  - **By setup type** and **By market regime** breakdowns — each numeric + `n` (J-09).
  - **Control-group comparison** panel (J-10): top-ranked cohort, random same-sector cohort, SPY, QQQ,
    sector ETF — each numeric, labelled, with `n`, at the selected horizon.
  - A prominent **survivorship-bias** disclaimer; **sample size `n` beside every figure**; low-sample
    (`n < min_sample`) figures visibly flagged (warn token); positive/negative returns use the pos/neg
    palette tokens. Loading / "Backend unavailable" / empty / low-sample states all explicit.
  - All values come from the single `/api/system-health` payload — the page re-formats only.
- **`apps/frontend/lib/api.ts`** — add `SystemHealthResponse` types + `fetchSystemHealth(horizon, signal)`
  (throws on non-200 → explicit unavailable state, matching the existing fetchers).

## Agents Required
- developer: **yes** — backend (`bars_after` + `forward_returns` model + `forward_testing.py` +
  `WalkForwardCfg` + `/api/system-health` + lifespan wiring + config) **and** frontend (System Health page
  + api client). Single developer agent handles both per project convention.
- backend-data: **yes**
- frontend-ux: **yes**

## Files to Create/Modify

**Backend**
- `apps/backend/app/engine/prices.py` — add `bars_after(session, symbol, d)` (date > d, ascending)
- `apps/backend/app/models.py` — add append-only `ForwardReturn` (`forward_returns`, unique `(run_id, symbol, horizon)`); update docstring
- `apps/backend/app/engine/forward_testing.py` *(new)* — `forward_return` (pure) + `backfill_forward_returns` (idempotent) + `compute_forward_aggregates` (single canonical aggregation)
- `apps/backend/app/api/system_health.py` *(new)* — `GET /api/system-health?horizon=` (default 20; 422 invalid; 503 no data)
- `apps/backend/main.py` — register `system_health.router`; call `backfill_forward_returns(engine, config)` in lifespan after `bootstrap_runs`
- `apps/backend/app/config.py` — typed `WalkForwardCfg` + `ControlGroupCfg`; wire `walk_forward` into `Config`
- `config.yaml` — add `walk_forward.control_group: { seed, top_n, peers_per_sector }` (additive)

**Backend tests** (`apps/backend/tests/`)
- `test_forward_testing.py` *(new)* — `bars_after` boundary; `forward_return` (NA / unchanged-when-later-bars-removed / entry-close-on-D); aggregates correctness on a hand-built fixture (by-bucket/setup/regime means + excess + control-group means + n, asserting buckets are read verbatim — no re-bucketing); control-group determinism (same seed → identical cohort); no-fabrication (zero-post-bar run → n=0; by-regime has BOTH Risk-on and Risk-off)
- `test_immutability.py` (or extend `test_scanner.py`) — backfill performs only INSERTs (row counts + faithful-equality on a pre-existing run before/after backfill; no UPDATE of any `scanner_runs`/`scanner_results`/`*_scores` row); `backfill_forward_returns` idempotent (second call inserts 0 new `forward_returns` rows); a run's stored scores are byte-identical with/without post-snapshot bars (forward returns never feed back)
- `test_api_system_health.py` *(new)* — `/api/system-health` returns by-bucket/setup/regime + excess + control groups each with `n` + survivorship label, for a default and a non-default horizon; out-of-range `horizon` → 422; `503` when no price data; `/api/runs` + live endpoints unaffected (J-01–J-08 regression guard)
- `test_no_magic_numbers.py` — extend the guard to `forward_testing.py` and `prices.bars_after` (horizons, min_sample, history_years, asof_cadence, control-group `{seed, top_n, peers_per_sector}` all from config)
- Shared config fixtures (`test_config*.py`, `test_sectors.py`, `test_themes.py`, etc.) — add a `walk_forward` section where the validated `Config` now requires it (mirror the iter-5 `scanner` fixture update)

**Frontend**
- `apps/frontend/app/system-health/page.tsx` — real evidence dashboard (replaces stub)
- `apps/frontend/lib/api.ts` — `SystemHealthResponse` types + `fetchSystemHealth(horizon)`

## Single-Source / No-Lookahead / Immutability Guardrails (the critical part — get these right)

- **THE keystone — no lookahead (forward direction).** Forward returns use **only** `bars_after`
  (date > D); the as-of `entry_close` is the close **on** D (≤ D). Unit-prove: `bars_after` returns no
  bar with date ≤ d; `forward_return` for horizon h is **unchanged** when bars dated > d+h are removed
  (only the first h post-bars matter) and is **NA** when < h post-bars exist; and a run's stored scores
  are **byte-identical** whether or not post-snapshot bars / `forward_returns` exist (forward returns
  never influence an as-of score).
- **Immutable = separate append-only table, never mutate the snapshot.** Backfilling forward returns
  performs **only INSERTs** into `forward_returns` — no UPDATE/overwrite of any `scanner_runs` /
  `scanner_results` / `*_scores` row (assert row counts + faithful-equality on a pre-existing run before
  vs after backfill). `backfill_forward_returns` is idempotent (second call inserts zero new rows).
- **Single source — use the EXACT registered names; READ, don't recompute.** Module/function
  `app.engine.forward_testing:compute_forward_aggregates`, table `forward_returns`, endpoint
  `GET /api/system-health` — verbatim, so the coherence-auditor finds no drift (iter-2 lesson). The
  aggregator **READS** the stored canonical `bucket` / `setup` / `sector` / `regime_label` from
  `scanner_results` / `scanner_runs` — it must **never** recompute a score, bucket, or setup from a
  second formula. The frontend re-formats the single payload — it recomputes no return/excess/bucket.
- **No magic numbers.** Horizons, min_sample, history_years, asof_cadence, and control-group
  `{seed, top_n, peers_per_sector}` all come from config; the random cohort RNG is seeded from
  `control_group.seed`. Benchmark symbols come from `config.etfs` (SPY/QQQ/sector ETFs), not literals.
- **No fabricated data.** A run with zero post-snapshot bars (the latest seed-date run) contributes n=0
  and **no** fabricated return; low-sample (`n < min_sample`) cells render an explicit flagged state (n
  shown), never a hidden or fabricated number; `503` when no price data; `422` for an invalid horizon.
- **Honest limitations.** Walk-forward evidence carries an explicit **survivorship-bias** label
  (current-membership universe) so results are never overstated.
- **Live + run endpoints NOT re-pointed.** `/api/dashboard`, `/api/stocks`, `/api/stocks/{ticker}`,
  `/api/sectors`, `/api/themes`, `/api/stocks/{ticker}/bars`, `/api/runs`, `/api/runs/{run_id}` stay
  byte-for-byte behaviourally identical → **J-01–J-08 cannot regress.** No order/execution path; no secrets.

## UI Evolution
- **New user-facing capability:** open **System Health** and read hard, forward-tested evidence —
  whether higher-ranked buckets, stronger setups, and risk-on regimes actually produced better realized
  forward returns than SPY/QQQ/sector ETFs and than random same-sector peers — at a chosen horizon, with
  sample sizes and an explicit survivorship-bias caveat.
- **New information displayed:** forward return by bucket A–E (mean + n); excess vs SPY and QQQ; forward
  return by setup type and by regime (+ n); a control-group table (top-ranked vs random-same-sector vs
  SPY/QQQ/sector-ETF, + n); a survivorship-bias label and per-figure sample sizes.
- **New user actions:** select a forward-return horizon (1/5/10/20/60) on `/system-health` and see all
  tables/panels update.
- **UI surface changes:** `/system-health` graduates from an EmptyState stub to a populated, multi-panel
  evidence dashboard. No other page changes.
- **Navigation changes:** none (System Health is already in the sidebar).

## Visual Requirements
- **Component patterns:** shadcn `Card` for each panel; HTML `<table>` inside a `Card` (matching the
  existing `/stocks` and `/scanner-runs` tables) for the by-bucket / by-setup / by-regime / control-group
  tables; reuse `ScoreBadge` / bucket colours for the A–E rows; a segmented/`Button`-group horizon
  selector; reuse `EmptyState` for empty/unavailable.
- **Layout:** persistent sidebar + main content (unchanged shell). A header with the horizon selector,
  then a panel grid: by-bucket table + excess-vs-SPY/QQQ, by-setup and by-regime breakdowns, and the
  control-group comparison panel; the survivorship-bias disclaimer prominent near the top.
- **Key visual effects:** monospace `tabular-nums` for ALL numbers (returns, excess, n); positive returns
  in `--pos` / negative in `--neg`; low-sample figures flagged with the `--warn` token; colour-graded A–E
  bucket rows. Palette tokens only — no arbitrary hex.
- **States to handle:** loading skeleton; "Backend unavailable" (fetch failure, styled like `/stocks`);
  empty / low-sample (n shown, flagged) — all explicit, never fabricated.

## Key Test Scenarios (must pass for the phase to be complete)
- **J-09 (browser):** `/system-health` renders a by-bucket (A–E) forward-return table with numeric means
  at a stated horizon, numeric excess-vs-SPY and excess-vs-QQQ, a by-setup-type breakdown, and a
  by-regime breakdown — each with sample size `n` shown; a survivorship-bias caveat is visible; changing
  the horizon selector changes the figures. (Assert structural/relational properties — NOT exact numbers.)
- **J-10 (browser):** the control-group panel shows, at a stated horizon, the top-ranked cohort's forward
  return alongside a random-same-sector cohort and SPY/QQQ/sector-ETF returns — each numeric and labelled.
- **Regression sweep (browser/evidence):** confirm J-01 (dashboard), J-02 (stocks + filters), J-03
  (themes), J-04 (sectors), J-05 (stock detail chart), J-06 (list==detail consistency), J-07 (Risk-Off
  zero Actionable), J-08 (immutable run history ≥2 dated runs) — no regression. **Note:** the walk-forward
  cadence adds more dated runs to `/scanner-runs` (intended immutable as-of history), which is product
  behavior, not a J-08 regression.
- **Unit/integration:** the no-lookahead boundary proofs, immutability (INSERT-only + idempotent),
  aggregates correctness on a hand fixture (buckets read verbatim), control-group determinism, no-magic-
  numbers extension, no-fabrication (n=0 + both regimes present), and the `/api/system-health` API cases
  (default + non-default horizon, 422 invalid, 503 no data). Backend `pytest` all green; frontend
  `npm run build` typechecks all routes; coherence audit PASS.

## Process & Harness Requirements (fold in — chronic runner gaps; NOT product code)

> Per `lessons.md` (iter-3 + iter-5), these are runner-script gaps that spec/DoD text has demonstrably
> failed to fix across 5 iterations — the durable fix is in `scripts/automation/*.sh`, **not** this spec.
> They are **outside the orchestrator's planning-only mandate to *edit*** (framework files with
> cross-project blast radius), so they are flagged here for whoever drives the runner, per `.claude/core.md`
> ("flag conflicts — do not silently skip or silently implement"). They do **not** gate J-09/J-10's DoD.

1. **Browser-QA must own/self-heal its frontend** — the dedicated browser-qa SKIP-on-HTTP-000 flap has
   recurred **5 consecutive iterations**. The structural fix belongs in
   `scripts/automation/browser-qa-phase.sh` (start/await the frontend the way QA mode-2 does), with an
   **extended readiness timeout** to absorb iter-6's longer first-boot backfill. Until fixed, the
   evaluator MUST reconcile J-09/J-10 from the on-disk QA evidence PNGs + unit/API proofs + direct source
   reads — **never** from a lone browser-qa SKIP.
2. **Emit the audit handoff** at `reports/audits/goal-i_can_see_the_wealthy_future-iter-6-audit.md` — that
   directory has not existed for **5 full-depth iters running**. The fix belongs in the runner/audit step
   (`scripts/automation/phase-audit.sh`), not the spec.
3. **Longer first boot — allow extra backend-readiness time.** The backfill calls `run_scan` once per
   cadence as-of date (idempotent) **then** computes forward returns; a fresh-DB first boot is slower than
   iter-5's 3-run bootstrap (subsequent boots skip persisted work). Keep the as-of set bounded enough that
   the first boot stays tractable while the 60-day-horizon sample meets/reports `min_sample` (30). A slow
   first boot can aggravate the browser-qa HTTP-000 readiness flap (see #1) — probe readiness generously.
4. **Negative file-existence under a flaky harness is not trustworthy** (iter-4 lesson): re-confirm with
   `ls`/Glob/re-read before letting "missing evidence" lower a verdict; don't blind-retry appends; treat
   demo-narrator Playwright soft-notes as non-gating capture-timing artifacts.

## Assumptions (documented, not blocking)
- **Default horizon = 20** (spec-stated); validated against `config.walk_forward.horizons` = [1,5,10,20,60].
- **Walk-forward cadence = `weekly` over `history_years: 2`**, intersected with actual seed trading days,
  ending far enough before the latest seed date to leave ≥60 post-snapshot bars for the 60-day horizon.
  The configured 2-year window includes the known Risk-off seed date **2025-04-04**, so the by-regime
  breakdown contains BOTH Risk-on and Risk-off evidence (developer verifies against the seed; widen via
  `history_years`/`asof_cadence` in config if a risk-off stretch is missed — config, not code).
- **`forward_returns` stores `realized_return` per `(run_id, symbol, horizon)`** so excess-vs-benchmark is
  a stored subtraction; `symbol` covers universe stocks AND benchmark ETFs (SPY, QQQ, the 11 sector ETFs,
  read from `config.etfs`). The latest seed-date run (no post-bars) is the natural **n=0** demonstration.
- **`control_group` defaults are illustrative/tunable** (e.g. `seed`, `top_n`, `peers_per_sector`); the
  developer picks reasonable values and documents them. The random-same-sector RNG is re-seeded from
  `control_group.seed` per computation so the cohort is reproducible across calls and restarts.
- **`backfill_forward_returns` coexists with `bootstrap_runs`** in the lifespan (both idempotent,
  frozen-seed-only); the existing `scanner.bootstrap_dates` runs remain.
- **Developer writes the dev handoff** to `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-6-dev.md`,
  documenting the chosen walk-forward cadence + as-of date count + first-boot backfill time, and confirming
  both a Risk-on and a Risk-off as-of date are present in the by-regime sample.
