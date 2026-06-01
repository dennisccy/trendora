# goal-i_can_see_the_wealthy_future_forever-iter-3 Execution Plan

**Target journey:** J-17 — Grow the dataset by date / date range (Data Manager, full depth). This is
the **last failing must-have** (J-01–J-16, J-18, J-19 pass).
**Critical anti-goals in play:** *Live fetch is real-data-only* · *Range backfill stays immutable &
lookahead-free* · *No fabricated data* · *No recompute in the read path* · *Exactly one date selector*
(the `/data` date inputs are **job parameters, NOT** a second viewing as-of state).

**Verified against source before planning (the reuse contract this iter rides on):**
- `app/engine/scanner.py` — `get_run_for_date` (create-once guard, :50), `run_scan` (one immutable
  snapshot per date, bars ≤ D, idempotent, :55), `bootstrap_runs` (batch pattern, :168). ✅
- `app/engine/forward_testing.py` — `backfill_run_forward_returns(session, run, cfg)` (INSERT-only
  realized returns, create-once, :569), `backfill_forward_returns` (bulk, :280), `compute_forward_aggregates`
  (the `n` that must grow, :464). ✅
- `app/models.py` — `DataProviderRun` (:99) already carries `provider/started_at/finished_at/
  symbols_ok/symbols_failed/status/message`. ✅ Append-only.
- `app/data_providers/base.py` — `PriceProvider` ABC + `ProviderUnavailableError` + frozen `Bar`;
  `seed_provider.py` shows the raise-don't-fabricate contract `StooqProvider` must mirror. ✅
- `config.py:535` — `provider: Literal["seed","stooq"]` (currently `seed`); no `data_manager` block yet. ✅
- `main.py` — routers included under `/api`; lifespan runs `bootstrap_runs` + `backfill_forward_returns`
  (the default boot — MUST stay untouched, :43/:49). ✅
- `components/asof-provider.tsx` — in-memory, fetched once on mount; **exposes no `refresh()`** today
  (`value` = `{asOf,setAsOf,latest,dates,isHistorical,ready}`). ✅ → J-17 step-4 needs an additive `refresh()`.
- `app/data/page.tsx`, `api/data.py`, `engine/data_manager.py`, `data_providers/stooq_provider.py` — **absent**. ✅

**The single biggest coherence risk: a SECOND scan/return code path.** `run_data_job` ORCHESTRATES
the existing canonical create-once paths; any new scoring/return math inside `data_manager.py` is a FAIL.

## What to Build

- **Engine — `app/engine/data_manager.py` (new, orchestration only):**
  - `compute_coverage(session, cfg) -> dict` — read-only descriptive metadata: price-history date range
    (min/max `DailyPrice.date`), distinct symbol count, sorted set of snapshot/as-of dates
    (`ScannerRun.asof_date`), and **gaps** = trading-day dates that have bars but no snapshot (the
    actionable backfill targets). Recomputes **no** canonical score/return.
  - `run_data_job(job_id, kind, start, end, ...)` — over a single date or `[start,end]`:
    - **Backfill (offline/deterministic):** for each in-range trading day D with bars present, call the
      **existing** `scanner.run_scan(session, D, cfg)` (create-once via `get_run_for_date`) then
      `forward_testing.backfill_run_forward_returns(session, run, cfg)`. Existing snapshot ⇒ read, never
      overwrite. This is what makes new dates appear in the switcher and grows System Health `n`.
    - **Fetch (live, real-data-only):** resolve the **live** provider (Stooq) via a provider factory,
      pull real EOD OHLCV for the chosen date/range, persist new `DailyPrice` rows (unique on
      `(symbol,date)`; never overwrite committed seed bars). On a per-symbol provider failure: count it
      failed, persist **zero** bars for it, surface an explicit error — **never fabricate**.
    - Emit **live progress** (`fetched x/158 symbols`, `snapshots a/b dates`) to an **in-memory job
      registry** keyed by `job_id`; on completion write **one** `DataProviderRun` row (final summary;
      structured detail — kind / date-range / snapshots_created / dates_done-total — JSON-encoded in
      `message`). Registry holds live state; the DB row is written **once at the end** (append-only).
  - All tunables (max range length / job limits / live-provider name) come from a new `data_manager`
    config block — **no magic numbers** in calc/control code.
- **Live provider — `app/data_providers/stooq_provider.py` (new):** `StooqProvider(PriceProvider)`
  fetching real EOD bars via `httpx` from Stooq (free, no key). Any failure ⇒ `raise
  ProviderUnavailableError`, **no synthesized bars** (mirrors `SeedProvider`). Plus a tiny provider
  **factory** (`seed`→`SeedProvider`, `stooq`→`StooqProvider`) so the fetch path resolves the *live*
  provider while boot stays on `provider: seed`. Any credential (none needed for Stooq) read only from env.
- **API — `app/api/data.py` (new router, included in `main.py`):**
  - `GET /api/data` → coverage + recent fetch/backfill **run history** (from `DataProviderRun`).
  - `POST /api/data/jobs` → validate date/range + kind (`fetch`|`backfill`|`both`), start the async job,
    return `{job_id}` immediately. Reject invalid ranges (start>end, empty, malformed) with explicit 4xx.
  - `GET /api/data/jobs/{job_id}` → live status/progress for polling, ending in the final summary.
- **Frontend — `app/data/page.tsx` (new):** Coverage panel · Job form (date or range + kind; **Start**)
  · Live-progress panel (polls `GET /api/data/jobs/{job_id}`) · Run-history table · honest loading/empty/
  **error** states. On job completion, **call `refresh()`** so new as-of dates become selectable in the
  global switcher **without a hard reload**.
- **Frontend — `components/asof-provider.tsx`:** add an additive `refresh()` to the context that re-runs
  the `/api/runs` fetch (extract the existing mount effect into a `useCallback`). Backfilling **older**
  dates leaves `latest` unchanged, so `refresh()` only adds options — it must **not** disturb the user's
  current `asOf` selection or the `setAsOf` normalization.
- **Frontend — `components/sidebar.tsx`:** add `{ href: "/data", label: "Data Manager", icon: Database }`
  (import `Database` from lucide-react). Additive — `/data` is the blueprint-approved home; no skeleton change.
- **Frontend — `lib/api.ts`:** typed `fetchDataCoverage()`, `startDataJob(...)`, `fetchDataJob(jobId)`.
  Frontend re-formats server values only — computes no coverage figure, count, or return.

## Agents Required
- developer: yes — one developer covers both tracks.
  - backend-data: yes — `data_manager.py` (coverage + orchestration job + in-memory registry),
    `stooq_provider.py` + factory, `api/data.py`, `data_manager` config block + `DataManagerCfg`,
    `main.py` router include, and the full backend/integration test set.
  - frontend-ux: yes — `app/data/page.tsx`, `asof-provider.refresh()`, sidebar entry, `lib/api.ts` client.

Frontend Present: yes

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` — **new.** `compute_coverage`, `run_data_job`, in-memory job
  registry. Orchestrates `scanner.run_scan` + `forward_testing.backfill_run_forward_returns` — **no new
  scan/return math.**
- `apps/backend/app/data_providers/stooq_provider.py` — **new.** `StooqProvider(PriceProvider)` via httpx;
  raises `ProviderUnavailableError`; no fabrication.
- `apps/backend/app/data_providers/__init__.py` (or a small `factory.py`) — name→provider factory.
- `apps/backend/app/api/data.py` — **new** router (3 endpoints; async job start).
- `apps/backend/main.py` — `app.include_router(data.router, prefix="/api")` only. **Do not touch the
  lifespan boot.**
- `config.yaml` — add a `data_manager` block (e.g. `live_provider: stooq`, `max_range_days`, any job limit).
- `apps/backend/app/config.py` — typed `DataManagerCfg`; add to `Config` with validation.
- `apps/backend/tests/test_data_manager.py` — **new** (coverage correctness; backfill-grows-n;
  lookahead-free; create-once/immutable; config-driven).
- `apps/backend/tests/test_api_data.py` — **new** (job lifecycle; 4xx validation).
- `apps/backend/tests/test_stooq_provider.py` — **new** (forced-failure no-fabrication unit test +
  one `@pytest.mark.integration` real-fetch test that may skip offline).
- `apps/backend/tests/test_config*.py` — add `data_manager` to the valid/minimal config fixtures.
- `apps/frontend/app/data/page.tsx` — **new** Data Manager page.
- `apps/frontend/components/asof-provider.tsx` — add `refresh()` (additive).
- `apps/frontend/components/sidebar.tsx` — add the Data Manager nav entry + `Database` icon import.
- `apps/frontend/lib/api.ts` — `fetchDataCoverage`, `startDataJob`, `fetchDataJob` + types.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-3-dev.md` — dev handoff (must state
  explicitly whether the live Stooq fetch was tested against the real provider or only the forced-failure stub).

## UI Evolution
- **New user-facing capability:** grow the dataset on demand — view coverage/gaps, start an async
  fetch+backfill job for a date or range, watch live progress + a final summary, then browse the newly
  created as-of dates across the whole dashboard while System Health shows higher `n` — all real-data-only.
- **New information displayed:** dataset coverage (price range, symbol count, snapshot/as-of date set,
  gaps); live job progress (symbols x/y, snapshots a/b dates); a final ok-vs-failed summary; a
  fetch/backfill run-history log.
- **New user actions:** date / date-range picker + job-kind selection on `/data`; a **Start** button;
  polling-driven progress view; a sidebar link to Data Manager.
- **UI surface changes:** new page `/data` (coverage panel, job form, live-progress panel, run-history
  table); one new sidebar nav entry.
- **Navigation changes:** one additive sidebar entry `Data Manager → /data` (blueprint-approved home; no
  re-approval).

## Visual Requirements
- **Component patterns:** dense dark analytical-workstation tokens. `Card`/panel headers for Coverage,
  Job form, Live progress, Run history. Coverage + summary figures in **monospace/tabular-nums**. A
  compact table for run history (date · kind · range · status · ok/failed counts). Progress shown as a
  determinate indicator/bar with `fetched x/y` · `snapshots a/b` text.
- **Layout:** sidebar + main content; Coverage panel on top, Job form + Live progress beside/below it,
  Run-history table at the bottom (single-column stack on mobile; tables scroll horizontally).
- **Key visual effects:** palette tokens only — `--accent` for the Start CTA, `--pos`/`--neg` for
  ok/failed counts, `--warn` for partial/low/stale, `--surface`/`--border` for panels. No ad-hoc colours.
- **States to handle:** loading (coverage fetch + while polling), empty (no runs yet / no gaps),
  **error** (provider/job failure → explicit error card + failed counts; **never** a fake success),
  in-progress (Start disabled while a job runs), done (final summary + history refreshed).

## Key Test Scenarios
- **Browser — J-17 (primary, FULL multi-step flow — not a single screenshot):** load `/data` → read
  coverage → start a **backfill** job over a date range with offline seed-bar headroom (thousands of
  seed trading days have bars but no snapshot) → watch live progress advance → read the final ok/failed
  summary → confirm a previously-absent as-of date is now selectable in the **global switcher (via
  `refresh()`, NOT a hard reload)** and resolves on `/stocks` / `/` → confirm `/system-health` sample
  size **`n` increased** vs before the job.
- **Browser — forced provider failure:** a fetch job with the provider stubbed to fail surfaces an
  explicit error state in the UI + run summary, and writes **zero** fabricated `DailyPrice` rows / zero
  snapshots for the failed symbols.
- **Browser — regression (must stay green):** J-13 switcher still works; J-14 a backfilled date yields a
  valid per-date scorecard; J-08 run list shows the new immutable runs; J-07 a backfilled Risk-Off date
  still marks zero Actionable; J-09 aggregate stays coherent. (J-07/08/09/13/14 are the
  required-still-passing set.) **Drive date changes via in-app nav, not a hard reload** (iter-1 lesson).
- **Backend — backfill grows `n`, deterministically:** backfilling a range of older seed-bar dates
  increases `compute_forward_aggregates(...).n` (`n_after > n_before`) and adds the expected `ScannerRun`
  rows.
- **Backend — lookahead-free:** a range-backfilled snapshot for D equals a direct `scanner.run_scan(D)`
  and uses only bars ≤ D; forward returns use only bars > D.
- **Backend — create-once / immutable:** backfilling a date that already has a snapshot is a no-op (same
  row id, unchanged `created_at`, result rows unchanged); re-running the same range twice yields
  identical content; `DataProviderRun` stays append-only.
- **Backend — coverage correctness:** `compute_coverage` reports the true price-range / symbol-count /
  snapshot-date set / gaps on a small fixture.
- **Backend — config-driven:** every `data_manager` tunable is read from config; `test_no_magic_numbers`
  (or equivalent) stays green.
- **Backend — async job/status + validation:** `POST /api/data/jobs` returns a `job_id` immediately;
  `GET /api/data/jobs/{job_id}` reports progress then a final summary; invalid ranges (start>end, empty,
  malformed date) are rejected with explicit **4xx**.
- **Backend — live fetch failure (offline, forced):** a stub/`stooq` provider raising
  `ProviderUnavailableError` ⇒ job ends failed/partial with an explicit message and **no fabricated
  bars/snapshots** for the failed symbols.
- **Backend — live fetch real provider (integration, may skip offline):** one
  `@pytest.mark.integration` test hits Stooq for a single symbol; document success/skip honestly in the
  handoff (do not silently pass).
- **Backend regression:** full pytest suite stays green (iter-2 baseline **266/0**).

## Assumptions & Coherence Guardrails
- **REUSE, DON'T REIMPLEMENT (the #1 coherence guard).** `run_data_job` MUST call `scanner.run_scan`
  (create-once via `get_run_for_date`) + `forward_testing.backfill_run_forward_returns`. New scoring or
  forward-return math inside `data_manager.py` is a FAIL — coherence-auditor will hard-fail a second
  computation path for snapshots/returns.
- **`/data` date inputs ≠ viewing as-of (J-18 / *Exactly one date selector*).** They are **job
  parameters** (which dates to fetch/backfill). They MUST NOT bind to `useAsOf`/the global switcher or
  create a second viewing date state. This is a deliberate, expected presence of date inputs on a page
  that is *not* an as-of control — call it out in the dev handoff so the reviewer / coherence-auditor /
  J-18 re-verify read it as such.
- **`refresh()` is additive and non-disruptive (iter-1 lesson).** New dates appear in the switcher only
  after `/api/runs` is re-fetched; `/data` triggers that on job completion. `refresh()` must preserve the
  user's current `asOf` and (for older-date backfills) leave `latest` unchanged — it only adds options.
  Browser-QA must verify via this mechanism, **not** a hard reload.
- **`DataProviderRun` is written once, at job end (append-only).** Live progress lives in the in-memory
  registry; the DB row is INSERTed at completion with the final status/counts and JSON detail in
  `message`. Never UPDATE a persisted row. If you instead add columns: additions must be additive,
  `SQLModel.metadata.create_all()` does NOT `ALTER` SQLite — recreate the gitignored runtime/QA DB; no
  destructive migration in the boot path.
- **Live provider is selected from config, distinct from boot.** Boot stays `provider: seed`
  (deterministic). The fetch path resolves the **live** provider (Stooq) via the factory + the new
  `data_manager.live_provider` key — so default boot/runtime is untouched and reproducible.
- **Async job opens its OWN DB session.** Do not reuse the request session (closed after the response).
  Use `BackgroundTasks` / a worker thread / asyncio task with a fresh `Session`, updating the registry as
  it goes. SQLite is single-writer — assume one active job at a time (concurrent jobs are out of scope).
- **Default boot unchanged.** `main.py` lifespan still bootstraps the quarterly seed snapshots; the Data
  Manager job is on-demand and additive. Do NOT move live fetch into the boot path.
- **Operational note (machine memory):** full backend pytest is ~14 min (heavy walk-forward boot). Run
  targeted modules during TDD; run the full suite once; do **not** launch two pytest invocations
  concurrently.

## Out of Scope (excluded; do not start)
- The five iter-0 partials (J-02 / J-06 / J-11 / J-15 / J-16 full re-verify) — the **next** closure pass,
  not this iter. They must not regress, but their full acceptance flows are not exercised here.
- Committing fetched live bars back into the committed seed (manual reproducibility step) — not automated.
- A scheduled / APScheduler auto-refresh of live data — J-17 is **on-demand** only.
- Nice-to-haves: editing config weights from a UI (cap 14); historical score charts (cap 15).
- Any change to the default boot path, or to the global as-of viewing control / any other page's date
  behaviour (J-18 must stay intact).
- No order/execution/brokerage path — must not exist or be reachable.
