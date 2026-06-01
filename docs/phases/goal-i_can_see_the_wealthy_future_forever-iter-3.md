# Goal Iteration 3 — Data Manager: grow the dataset by date / date range (J-17)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-17
- **Required-still-passing journeys:** J-07, J-08, J-09, J-13, J-14
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Live fetch is real-data-only.** The Data Manager MUST use the config-selected live provider to fetch real EOD bars; on a provider failure it MUST surface an explicit error and MUST NOT synthesize prices to fill a gap or force a successful run. *(critical)*
  - **Range backfill stays immutable & lookahead-free.** Snapshots created for a fetched or backfilled date range are create-once: an existing snapshot MUST be read, never overwritten, and an as-of-D snapshot MUST use only bars with date ≤ D. *(critical)*
  - **On-demand snapshots stay immutable & lookahead-free.** Creating a snapshot for a newly selected date is create-once: an existing snapshot MUST be read, never overwritten; an as-of-D snapshot MUST use only bars with date ≤ D. *(critical)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. Unit-tested.
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file.
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere; the default seed path requires none, and any live-provider key is read only from the environment.
  - **Exactly one date selector.** The frontend MUST NOT maintain a second, independent date state; every date-scoped page (including Backtest) reads the single global as-of control. *(extends Single source of truth)*
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable. *(critical)*
  - **Honest limitations surfaced.** Walk-forward evidence MUST be labelled as carrying survivorship bias (current-membership universe); breadth/new-high-low are universe-relative.

## GOAL

A user can open **Data Manager** (`/data`), see current dataset coverage (price-history date range, symbol count, the set of snapshot/as-of dates, and gaps), pick a date or date range, start an **async fetch + backfill job**, watch its live progress and final summary, and afterward find **new as-of dates selectable in the global switcher** and the **System Health forward-test sample size (n) grown** — all real-data-only, immutable, and lookahead-free.

## BACKGROUND

J-17 is the **last failing must-have** (the only remaining unbuilt journey; J-01–J-16, J-18, J-19 pass). The iter-2 evaluator and the session blueprint both target it next at **full** depth: a new page, new endpoints, an async background job, a live provider, plus engine + config work and a cluster of *critical* anti-goals (live fetch real-data-only; range backfill immutable & lookahead-free; no fabricated data). A baseline + iter-2 file-scan confirms `/data`, `api/data.py`, a data-manager engine module, and any `data` config section are all **absent**.

Two facts (verified against the codebase) shape the design and make J-17 testable in the **offline** loop:

1. **The backfill path grows `n` deterministically with no network.** Boot bootstraps snapshots at `walk_forward.asof_cadence: quarterly` over `history_years: 2` (~8 dates), but the committed seed holds **1356 daily bars per symbol** (2021-01-04 → 2026-05-28) across **158 symbols**. Thousands of seed-bar trading days therefore have **no snapshot** — abundant offline backfill headroom. Backfilling such dates creates new immutable snapshots + forward returns purely from committed bars, so new dates appear in the switcher and System Health `n` rises — all reproducibly, no live fetch.
2. **The create-once snapshot machinery already exists and MUST be reused, never reimplemented.** `scanner.get_run_for_date` (create-once guard, line 50), `scanner.run_scan` (one immutable snapshot per date, ≤ D, line 55), `scanner.bootstrap_runs` (batch pattern, line 168), and `forward_testing.backfill_run_forward_returns` (INSERT-only realized returns, line 569) / `forward_testing.backfill_forward_returns` (bulk pattern, line 280) are the canonical paths. New `ScannerRun` rows automatically surface via `GET /api/runs` (`runs.py:31`), which is exactly what the as-of switcher reads (`components/asof-provider.tsx::fetchRuns`). The Data Manager **orchestrates** these; it does NOT contain a second scan/return computation.

The **live fetch** path (config-selected `stooq` provider, declared in `config.py:535` but unimplemented per `data_providers/base.py:6`) is the *going-forward* refresh beyond the seed's last date — network-dependent, so it is covered by an integration test (may be skipped offline, documented) plus an offline **forced-failure** unit test for the explicit-error / no-fabrication path.

**Lessons applied (from `lessons.md`):**
- *iter-1:* the global as-of date lives in an **in-memory** app-shell provider (`components/asof-provider.tsx`), fetched once on mount with no localStorage/URL persistence; it survives client-side nav but resets on hard reload. So for J-17 step 4 ("new as-of dates are now selectable"), the `/data` page MUST cause the run list to **re-fetch** on job completion (e.g. expose/​call a `refresh()` on the as-of provider, or re-fetch `/api/runs`) so new dates appear **without a hard reload**; browser-QA must verify via that mechanism, not a reload.
- *iter-0:* never trust a browser-QA *negative* date-control finding on degraded tooling — confirm "exactly one date selector" claims against frontend source. **Critical for this iter:** the `/data` date/range inputs are **job parameters** (which dates to fetch/backfill), NOT a viewing as-of control. They MUST NOT be wired into the global `useAsOf` provider or create a second viewing date state — J-18 must stay intact.
- *iter-2:* an opportunistic single-screenshot re-verify confirms a surface exists but does NOT satisfy a multi-step acceptance flow. J-17 browser-QA MUST exercise the **full** flow (coverage → start job → live progress → final summary → new date selectable → n grew), not just load `/data`.

## IN SCOPE

### Backend

- [ ] **Data Manager engine** — new module `apps/backend/app/engine/data_manager.py`:
  - [ ] `compute_coverage(session, cfg) -> dict` — read-only: price-history date range (min/max `DailyPrice.date`), distinct symbol count, the sorted set of snapshot/as-of dates (`ScannerRun.asof_date`), and **gaps** = trading-day dates that have bars but no snapshot (the actionable backfill targets). No recomputation of any canonical score/return — purely descriptive metadata.
  - [ ] `run_data_job(...)` — orchestrates a fetch and/or backfill job over a single date or `[start, end]` range:
    - **Backfill (offline/deterministic):** for each trading day D in range with bars present and `date ≤ D`, call the **existing** `scanner.run_scan(session, D, cfg)` (create-once via `get_run_for_date`) then `forward_testing.backfill_run_forward_returns(session, run, cfg)`. Never overwrite an existing snapshot (read it). Auto-generates the new days' snapshots + forward returns so the forward-test sample grows.
    - **Fetch (live, real-data-only):** for the chosen date/range, pull real EOD OHLCV via the **config-selected live provider** and persist new `DailyPrice` rows (unique on `(symbol, date)`; never overwrite committed seed bars). On provider failure, surface an explicit error and persist **zero fabricated bars** for the failed symbols.
    - Emit **live progress** (e.g. `fetched 80/158 symbols`, `snapshots 23/120 dates`) and a **final success/partial/failure summary** (symbols ok vs failed, dates done vs total).
  - [ ] All tunables (e.g. max range length / job limits, if any) come from a new `data_manager` block in `config.yaml` — **no magic numbers** in calc/control code.
- [ ] **Live provider** — `apps/backend/app/data_providers/stooq_provider.py`: `StooqProvider(PriceProvider)` fetching real EOD bars via `httpx` from Stooq (free, no key). On any failure it RAISES `ProviderUnavailableError` and returns **no synthesized bars** (mirrors `SeedProvider`'s contract). Any provider credential, if ever needed, is read **only from the environment** — never committed.
- [ ] **Async background job + progress store** — the `POST` returns immediately with a `job_id`; the job runs in-process (FastAPI `BackgroundTasks` or a worker thread/asyncio task) and updates a pollable progress record. **Recommended (lowest-risk):** keep live progress in an in-memory job registry keyed by `job_id`, and persist only the final summary to the existing append-only `DataProviderRun` row (reuse `provider/started_at/finished_at/symbols_ok/symbols_failed/status/message`; structured detail — kind=fetch|backfill, date range, snapshots_created, dates_done/total — encoded in `message` as JSON). If you instead add columns to `DataProviderRun`, note `SQLModel.metadata.create_all()` does NOT `ALTER` existing SQLite tables — keep additions additive and recreate the runtime/QA DB (it is gitignored, bootstrapped on boot); do **not** put a destructive migration in the boot path. Keep `DataProviderRun` append-only.
- [ ] **API** — new `apps/backend/app/api/data.py` (router included in `main.py`):
  - [ ] `GET /api/data` → current coverage + recent fetch/backfill **run history** (from `DataProviderRun`).
  - [ ] `POST /api/data/jobs` → validate the date/range + job kind (fetch | backfill | both), start the async job, return `{ job_id }` immediately. Reject invalid ranges (start > end, empty, malformed dates) with an explicit 4xx — no silent no-op.
  - [ ] `GET /api/data/jobs/{job_id}` → live status/progress for polling, ending with the final summary.

### Frontend

- [ ] **Data Manager page** — `apps/frontend/app/data/page.tsx`:
  - [ ] **Coverage panel** — price-history date range, symbol count, count + list (or compact view) of snapshot/as-of dates, and gaps.
  - [ ] **Job form** — pick a single date or a date range and a job kind (fetch and/or backfill); a **Start** action that calls `POST /api/data/jobs`. (These date inputs are **job parameters only** — they MUST NOT touch the global `useAsOf` viewing state.)
  - [ ] **Live progress** — poll `GET /api/data/jobs/{job_id}`; show a progress indicator (e.g. `fetched 80/158 symbols`, `snapshots 23/120 dates`) and a final success/partial/failure **summary** (counts ok vs failed). Loading / empty / **error** states styled per the design system (explicit error on provider/job failure — never a fake-success).
  - [ ] **Run history** — list recent fetch/backfill runs (date, kind, range, status, counts) from `GET /api/data`.
  - [ ] On job completion, **refresh the as-of run list** so newly created dates become selectable in the global switcher **without a hard reload** (see iter-1 lesson).
- [ ] **Sidebar nav** — add one entry `{ href: "/data", label: "Data Manager", icon: Database }` to `components/sidebar.tsx` `NAV` (additive; `/data` is already the blueprint-approved home for J-17).
- [ ] **API client** — add `fetchDataCoverage()`, `startDataJob(...)`, `fetchDataJob(jobId)` (typed) to `apps/frontend/lib/api.ts`. Frontend re-formats server values only — it computes no coverage figure, count, or return client-side.

### New user-facing capability

The user can grow the dataset on demand: view coverage/gaps, start an async fetch+backfill job for a date or range, watch live progress + a final summary, and then browse the **newly created as-of dates** across the whole dashboard while System Health shows **more evidence (higher n)** — all from committed real data, with provider failures surfaced honestly.

### New information displayed

Dataset coverage (price-history date range, symbol count, snapshot/as-of date set, gaps); live job progress (symbols fetched x/y, snapshots a/b dates); a final job summary (ok vs failed); a fetch/backfill run-history log.

### New user actions

Date / date-range picker + job-kind selection on `/data`; a **Start fetch/backfill** button; polling-driven progress view; a sidebar link to Data Manager.

### UI surface changes

New page `/data` (coverage panel, job form, live-progress panel, run-history table); one new sidebar nav entry.

### Product surface delta

Trendora stops being a fixed-window dataset: the user controls how much history/evidence exists, turning "the seed is what it is" into "grow the evidence base on demand" — while the default boot path stays the committed offline seed.

### Blueprint conformance

`/data` is the **existing** blueprint home for J-17 (nav skeleton + journey-homes table already list it as the target). Adding the sidebar entry implements the approved skeleton — **no nav-skeleton change, no re-approval**. All reads serve persisted/descriptive values; the backfill reuses the registered canonical `scanner.run_scan` / `forward_testing.backfill_run_forward_returns` modules — **no second computation path** for snapshots or forward returns.

### Data-contract additions

Refine the existing J-17 row in `blueprint.md` (status `⛔ NOT BUILT` → `building iter-3`) with the real names — these are **new descriptive values**, not duplicates of any canonical score/return:
- **Dataset coverage** (price range, symbol count, snapshot dates, gaps) — computed once by `app.engine.data_manager:compute_coverage`; served by `GET /api/data`.
- **Fetch/backfill job progress + final summary** — from the in-memory job registry + the persisted `DataProviderRun` summary; served by `GET /api/data/jobs/{job_id}` (live) and `GET /api/data` (history).
- The snapshots + forward returns the backfill creates are the **same canonical values** via the **same** `scanner.run_scan` / `forward_testing.backfill_run_forward_returns` modules — registered already; **not** re-registered and **not** recomputed.

## OUT OF SCOPE

- The five iter-0 partials (J-02 filter interaction, J-06 cross-page numeric compare, J-11 add+restart, J-15 warm-load timing, J-16 VCP filter→badge→detail→glossary) — these are the **next** closure / re-verify pass, not this iter. They must not regress, but their full acceptance flows are not exercised here.
- Committing fetched live bars back into the committed seed (a manual, optional reproducibility step per `docs/goal.md` Constraints) — not automated here.
- A scheduled / APScheduler auto-refresh of live data — J-17 is **on-demand** only.
- Nice-to-haves: editing config weights from a UI view (cap 14); historical score charts (cap 15).
- Any change to the default boot path — it MUST remain the committed offline seed, deterministic.
- Changing the global as-of viewing control or any other page's date behaviour (J-18 must stay intact).

## DEFINITION OF DONE

- [ ] J-17 passes via browser-qa-agent through the **full** flow: load `/data` → read coverage → start a **backfill** job over a date range with offline seed-bar headroom → watch live progress → read the final summary → confirm new as-of dates are selectable in the global switcher (no hard reload) → confirm `/system-health` sample size (n) increased.
- [ ] A **forced provider failure** on the fetch path surfaces an explicit error state in the UI and the run summary, and writes **zero fabricated `DailyPrice` rows / zero snapshots** for the failed symbols.
- [ ] Required-still-passing journeys J-07, J-08, J-09, J-13, J-14 remain green.
- [ ] No anti-goal violation introduced — in particular: range backfill is create-once/immutable/lookahead-free; live fetch is real-data-only; the default boot path is unchanged; the `/data` date inputs are job parameters, not a second viewing as-of state.
- [ ] Unit/integration tests pass; no regressions in the existing suite.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-3-dev.md`, explicitly stating whether the live Stooq fetch was tested against the real provider (integration) or only via the forced-failure stub (per `core.md` External Integration Testing).

## TESTING REQUIREMENTS

- **Browser (J-17, full multi-step flow):** coverage renders; start a backfill job; live progress advances and a final summary shows ok/failed counts; after completion a previously-absent as-of date is selectable in the global switcher (via re-fetch, not reload) and resolves on `/stocks`/`/`; `/system-health` n is higher than before the job. Re-verify (no regression): J-13 switcher still works, J-14 a backfilled date yields a valid per-date scorecard, J-08 run list shows the new immutable runs, J-07 a backfilled Risk-Off date still marks zero Actionable, J-09 aggregate stays coherent.
- **Unit/integration (backend):**
  - **Backfill grows n, deterministically:** backfilling a range of older seed-bar dates increases `compute_forward_aggregates(...).n` (`n_after > n_before`) and adds the expected `ScannerRun` rows.
  - **Lookahead-free:** a range-backfilled snapshot for date D equals a direct `scanner.run_scan(D)` and uses only bars ≤ D; forward returns use only bars > D.
  - **Create-once / immutable:** backfilling a date that already has a snapshot is a no-op (same row id, unchanged `created_at`, result rows unchanged); re-running the same range twice yields identical content; `DataProviderRun` stays append-only.
  - **Coverage correctness:** `compute_coverage` reports the true price-range / symbol-count / snapshot-date set / gaps on a small fixture.
  - **Config-driven:** any `data_manager` tunable is read from config; `test_no_magic_numbers` (or equivalent) stays green.
  - **Async job/status:** `POST /api/data/jobs` returns a `job_id` immediately; `GET /api/data/jobs/{job_id}` reports progress then a final summary; invalid ranges are rejected with 4xx.
- **Error cases:**
  - **Live fetch failure (offline, forced):** a stub/`stooq` provider raising `ProviderUnavailableError` → job ends failed/partial with an explicit error message and **no fabricated bars/snapshots** written for the failed symbols.
  - **Live fetch real provider (integration, may skip offline):** one `@pytest.mark.integration` test hits Stooq for a single symbol; document success/skip honestly in the handoff (do not silently pass).
  - Invalid job inputs (start > end, empty range, malformed date) rejected with explicit 4xx.

## NOTES

- **Reuse, don't reimplement.** The single biggest coherence risk is a *second* scan/return code path. The backfill MUST call `scanner.run_scan` + `forward_testing.backfill_run_forward_returns` (and the `get_run_for_date` create-once guard). Any new scoring/return math inside `data_manager.py` is a FAIL.
- **`/data` date inputs ≠ viewing as-of.** They select what to fetch/backfill (action parameters). Do not bind them to `useAsOf`/the global switcher or create a second viewing date state — J-18 / "exactly one date selector" must hold. (This is a deliberate, expected presence of date inputs on a page that is *not* a second as-of control; reviewer/coherence-auditor should read it as such.)
- **In-memory as-of provider caveat (iter-1 lesson):** new dates appear in the switcher only after `/api/runs` is re-fetched; the page must trigger that on job completion so J-17 step 4 passes without a hard reload.
- **Default boot unchanged:** `main.py` lifespan still bootstraps the quarterly seed snapshots; the Data Manager job is on-demand and additive. Do not move live fetch into the boot path (it would make the walk-forward evidence irreproducible — see project-template "BUILD THE SEED IN iter-1").
- **Honest evidence labelling:** any walk-forward evidence remains labelled survivorship-biased / universe-relative; backfilled-from-seed evidence is the same committed data, so no new honesty caveat is needed — but live-fetched data, if ever used for evidence, must be labelled as such.
- After J-17 lands, the planned final step is a single **closure / re-verify** pass to convert the five iter-0 partials via their full acceptance flows → GOAL_ACHIEVED if nothing regresses.
