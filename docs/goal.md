# Project Goal

> This goal drives the **ops-hardening loop** for Trendora. Lineage: the original
> feature-complete product goal is archived at [`docs/goal-product.md`](goal-product.md);
> the decision-quality/evidence goal (GOAL_ACHIEVED 2026-07-16, 25/25 journeys, session
> `mcp-loop`) is archived at [`docs/archive/goal-mcp-loop.md`](archive/goal-mcp-loop.md).
> This file evolves Trendora from *"proves its signals out-of-sample"* to *"an instance the
> owner can operate and trust: available in seconds, honest about its own state, and
> unrestricted in historical data operations."* Session id: `ops-hardening`.

## Vision

Trendora's product purpose is unchanged — explainable, regime-aware, evidence-statused
equity-leadership rankings. This cycle makes the running instance **operationally solid**:
the backend boots to serving in seconds; every heavy aggregate is **computed at ingest time
and persisted to the database**, never recomputed on the fly at boot or on a request path;
each page loads **only the data it needs**; the UI tells the truth about the backend's own
state (starting with visible phase, crashed/unreachable, ready) and about data jobs
(progress, blocked dates, exclusion reasons, zero-work outcomes); and historical backfills
run over **any requested range without caps**, chunked and memory-bounded.

## Target Users

The same self-directed, quant-minded swing/position traders — now also in their role as
**operators of their own Trendora instance**, who need to trust that the app is up, see what
it is doing when it is not ready, and run any historical data operation without silent
no-ops or arbitrary limits.

## Success Criteria

- Backend process start → first `GET /api/health` HTTP 200 in **≤ 5 seconds** on the warm
  committed-seed DB (measured, recorded in `reports/perf-budgets.md`).
- Any historical trading day in the price basis is backfillable on demand: backfilling
  2026-05-02 → 2026-05-29 produces **~19 daily May snapshots visible in the UI**.
- **Zero silent zero-work jobs:** every job outcome shows date counts and per-date
  exclusion reasons, persisted across page reloads.
- **No per-run range cap:** the `max_range_days` rejection is removed; long spans execute
  in visible chunks.
- **No unbounded whole-table loads:** no code path streams the full `daily_prices` table
  into RAM; ingest-maintained aggregates serve every heavy read.
- Page loads stay within committed **never-regress budgets** in `reports/perf-budgets.md`.

## Key Capabilities

1. **Unrestricted-range backfill** — an explicit backfill request makes every trading day
   in the requested range a snapshot target (requested range always wins; cadence governs
   only automatic warm-up), chunked and memory-bounded.
2. **Persisted job history with exclusion reasons** — the `/data` job surface reads
   server-side run history: progress, outcomes, per-date exclusions, blocked/error states.
3. **Ingest-time aggregate maintenance** — the aggregation inventory (see Improvement
   direction) is refreshed at the end of every fetch/backfill/rebuild and served as stored
   rows.
4. **Instant-serving boot with phase-aware health** — boot performs existence checks only;
   `/api/health` exposes boot/loading phase and progress.
5. **Distinguishable backend states + persistent logfile** — starting (with phase) vs
   crashed/unreachable vs ready; crashes leave evidence in a logfile.
6. **Per-page minimal loading with budgets** — each page's on-load calls read persisted
   aggregates or indexed windowed queries, measured against committed budgets.

## Non-Goals

- No return/price prediction, "buy/sell" signals, price targets, or alpha claims. Decision
  support only.
- No order placement, broker keys, or trade simulation.
- Not a rewrite — the ops/performance layer is **additive** to the existing surfaces
  (Dashboard, Stocks, Sectors, Themes, Backtest, Research labs, Data, Watchlist, Evidence).

## Constraints

- Local-first, deterministic, offline against the committed seed; **strict no-lookahead**
  preserved (scoring uses bars ≤ as-of; forward returns use bars > as-of).
- **All "proven" status flows from the evidence ledger** as the single source of truth; the
  UI never computes proven-ness itself.
- A claim becomes "proven" only via the statistical **referee** (sealed holdout + controls +
  multiple-testing correction); the referee and ledger live in the project (read-only MCP
  "window" + `project-extensions/` gate), not in the shared framework.
- **Compute-at-ingest:** heavy aggregation (snapshots, coverage, market phase, research
  caches, membership timeline) happens inside ingest jobs (fetch/backfill/rebuild) and is
  persisted to the DB; boot and request paths serve stored values and never stream the full
  `daily_prices` table into RAM.

## Design Direction

- Visual style: minimal, data-dense, evidence-first — consistent with the existing Trendora UI.
- Mood: skeptical, rigorous, honest. Evidence status is calm and unmissable, never hype.
- Reference: existing Trendora surfaces; badges read like a quiet "proven ✓ / not yet
  proven" chip; status/health/job surfaces read like the existing preflight banner — calm,
  factual, unmissable, never a blank or frozen frame.

## Product Shape

### Navigation / information architecture
- Existing nav unchanged: Dashboard | Stocks | Sectors | Themes | Backtest | Research |
  Data | Watchlist | Evidence. No new nav entries this cycle — job history/status live on
  `/data`; the readiness badge is global (top bar).

### Canonical values (single source of truth)
- **Evidence status** and **certified-claim** for any (signal, as-of) — computed once by the
  referee, stored in the evidence ledger, displayed identically everywhere (unchanged).
- The three scores (Leadership / Entry Quality / Risk), regime score, market phase, and
  realized forward-returns remain single-source from the existing engine (unchanged).
- **Backend readiness / boot phase** — computed only in `app.engine.readiness`, served only
  by `GET /api/health`; the badge, preflight banner, and any status surface re-read it.
- **Job history & per-date exclusion reasons** — persisted in `data_provider_runs`
  (extended as needed), served only by the data-jobs endpoints; the `/data` panels re-read
  them and never recompute eligibility client-side.
- **Coverage payload** (universe counts, per-symbol coverage, gaps, capacity) — persisted at
  ingest, served only by `GET /api/data`.

## Must-have user journeys

- **J-01: Backfill honors the requested range**
  - Steps:
    1. With backend and frontend running, visit `/data`; in the job form select kind
       `backfill`, start `2026-05-02`, end `2026-05-29`; start the job
    2. Watch the live progress panel until the job completes
    3. Assert the job summary reports `dates_total` = 19 (every trading day in the range —
       2026-05-04 … 2026-05-29, Memorial Day 2026-05-25 excluded as non-trading) and
       `snapshots_created` equal to the eligible dates not already snapshotted, with any
       skipped date carrying an explicit reason
    4. Visit `/scanner-runs` and assert runs now exist for in-range May dates (e.g.
       2026-05-04, 2026-05-15, 2026-05-29); open one and assert its leaderboard renders
       stored values
  - Acceptance:
    - **Consistency (single source):** backfill eligibility and targets are computed once in
      the data-manager job engine; the UI renders the persisted run record — no client-side
      eligibility logic.
    - **Correctness:** after completion, `scanner_runs` holds a run for every trading day in
      2026-05-04 … 2026-05-29 (19 dates), and a spot-checked date's UI leaderboard matches
      the stored snapshot for that as-of.
    - **Honest status & anti-goals:** the explicit request densifies exactly the requested
      range (automatic warm-up cadence unchanged elsewhere); execution is chunked and
      memory-bounded (anti-goal #8); determinism and no-lookahead preserved (snapshots use
      bars ≤ as-of only).
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the May backfill and the resulting
      daily snapshots, viewable via `demo.sh ops-hardening --session-live`.

- **J-02: No silent zero-work jobs**
  - Steps:
    1. Visit `/data`; start a backfill over a range where no work is possible (e.g. the
       weekend-only span 2026-05-02 → 2026-05-03, or a fully-snapshotted range)
    2. Assert the completed job's summary states the outcome plainly: 0 snapshots created,
       with a per-reason breakdown (non-trading days, already snapshotted, other exclusions)
       whose counts sum to the days in the range
    3. Reload the page; assert the job history panel (persisted server-side) still lists
       this run with the same outcome and reasons — never "no job started this session"
    4. Assert the zero-work outcome is visually distinguished as an explanatory state, not
       the same unexplained green success badge as a productive run
  - Acceptance:
    - **Consistency (single source):** exclusion reasons and counts come from the persisted
      job record served by the data-jobs endpoints; the panel never recomputes them.
    - **Correctness:** the weekend-only range shows 2 non-trading days / 0 eligible; a
      fully-snapshotted range shows every date as already-snapshotted.
    - **Honest status & anti-goals:** no fabricated progress; zero-work is never rendered as
      unexplained success; wording is factual, no reassurance language.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of a zero-work job explaining itself,
      viewable via `demo.sh ops-hardening --session-live`.

- **J-03: No per-run range cap**
  - Steps:
    1. Visit `/data`; request a backfill spanning more than 370 calendar days (e.g.
       2025-06-01 → 2026-07-17)
    2. Assert the request is accepted — no "date range too large" rejection — and the job
       begins executing in visible chunks with live progress
    3. Assert at least the first chunk completes and progress continues without any
       cap-related failure (full completion may extend beyond the QA window; persisted
       progress per J-02 keeps it observable)
  - Acceptance:
    - **Consistency (single source):** the chunk plan derives from the config
      `import_chunking` values; the UI progress reflects the same plan the engine executes.
    - **Correctness:** the `max_range_days` rejection no longer exists in config, validation,
      or API behavior, and the tests that pinned 370 are updated to the new contract.
    - **Honest status & anti-goals:** memory stays bounded for the whole run (anti-goal #8);
      progress is honest and never reports done early.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of a >370-day request being accepted
      and chunk-executing, viewable via `demo.sh ops-hardening --session-live`.

- **J-04: Non-blocking boot with visible status**
  - Steps:
    1. Restart the backend via the documented start script; immediately poll `GET /api/health`
    2. Assert the first HTTP 200 arrives within 5 seconds of process start on the warm DB,
       even when background loading remains
    3. While any background loading runs, assert the top-bar badge shows an explicit
       initializing state with phase detail (what is loading, progress n/m) — never a bare
       "Backend unavailable"
    4. Kill the backend process (simulated crash); assert the UI transitions to an explicit
       unreachable/crashed presentation (preflight-banner language), visibly distinct from
       the initializing state
    5. Assert a persistent backend logfile exists and contains the boot and the crash events
  - Acceptance:
    - **Consistency (single source):** readiness/boot phase is computed only in
      `app.engine.readiness` and served only via `GET /api/health`; badge and banner re-read
      it.
    - **Correctness:** measured start→first-200 ≤ 5 s on the warm DB is recorded in
      `reports/perf-budgets.md`; the crashed presentation appears only when the health poll
      fails, the initializing presentation only while the backend reports loading.
    - **Honest status & anti-goals:** no "Ready" before real data is servable; boot performs
      no whole-table loads and no synchronous snapshot computation (moved to ingest).
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of restart→serving-in-seconds and
      crash→honest-unreachable, viewable via `demo.sh ops-hardening --session-live`.

- **J-05: Aggregates are precomputed at ingest, never on the fly**
  - Steps:
    1. Run an ingest job (fetch or backfill) that adds at least one new trading date
    2. Immediately after the job completes, assert each inventory aggregate is fresh for the
       new state via its serving endpoint: latest-date snapshot (dashboard payload),
       coverage payload (`GET /api/data`), membership timeline, market phase for the latest
       as-of, and the research hot-key caches — each responding from storage for the new
       as-of
    3. Restart the backend and visit `/data` cold; assert coverage renders from the
       persisted payload within its committed budget and the process performs no
       3.3M-row bar prefill
    4. While a heavy ingest job runs, poll `GET /api/health`; assert it stays responsive
       throughout
  - Acceptance:
    - **Consistency (single source):** each aggregate has exactly one producer (the ingest
      finalize hooks) and one serving endpoint; no request path recomputes it.
    - **Correctness:** aggregate values are byte-identical to the canonical computation for
      the same as-of — storage is re-served, never re-derived.
    - **Honest status & anti-goals:** no code path streams the full `daily_prices` table
      into RAM (anti-goal #8's unbounded-load ban enforced on serving paths); launch scripts
      enforce the declared `memory_cap_mb` / `malloc_arena_max`.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of ingest → fresh aggregates → cold
      `/data` within budget, viewable via `demo.sh ops-hardening --session-live`.

- **J-06: Pages load only what they need**
  - Steps:
    1. With a warm backend in prod mode (`scripts/start-backend.sh` /
       `scripts/start-frontend.sh` — never `dev.sh`), load each page (`/`, `/stocks`,
       `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`,
       `/backtest`, `/watchlist`, one `/research` lab) and record time-to-interactive plus
       each page's on-load API latencies
    2. Record the measurements in the committed budgets table `reports/perf-budgets.md`
       (existing budgets carry; the ≤ 5 s boot budget and the cold `/api/data` budget join
       the table) and assert every measurement is within budget
    3. Record in the dev handoff a code-level audit that no on-load endpoint performs an
       unbounded `daily_prices` scan or recomputes an inventory aggregate
  - Acceptance:
    - **Consistency (single source):** budgets live only in `reports/perf-budgets.md`; every
      later iteration touching the data path re-asserts them alongside fresh numbers.
    - **Correctness:** lazy/optimized paths return byte-identical values to the canonical
      computation for the same as-of.
    - **Honest status & anti-goals:** anything slower than its budget shows an honest
      progress or initializing state, never a frozen or blank frame; caching introduces no
      lookahead.
    - **Walkthrough:** a `[NEW]`-flagged walkthrough of the budgets table vs live page
      loads, viewable via `demo.sh ops-hardening --session-live`.

<!-- Continuous-improvement auto-journeys: the goal-proposer appends NEW Must-have journeys ONLY
     between the two markers below (see the goal-self-extension skill). The human-authored journeys
     above and the Anti-goals below are never machine-edited. An empty block = nothing auto-proposed yet. -->
<!-- AUTO:journeys -->
<!-- /AUTO:journeys -->

## Anti-goals

- A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
  **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
  values MUST render a "not yet proven" state. *(critical)*
- **Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
  claims; never place or simulate orders. *(critical)*
- A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
  for the same as-of date — not merely that the page renders. *(critical)*
- **No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
  out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
- **Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
  never introduce lookahead anywhere. *(critical)*
- No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the
  post-decompose gate. *(critical)*
- No hard-coded credentials, API keys, or tokens in source files. *(critical)*
- **Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every
  existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error
  boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
  whole-table ORM loads are forbidden on the deep basis. *(critical)*

## Loop mechanics (for the iteration planner)

- Journeys J-01 … J-06 are pure ops/performance/correctness work and carry **no Evidence
  Claims** — the post-decompose referee gate passes automatically. No iteration in this
  cycle may introduce proven-language (anti-goals #1/#4/#6 still veto).
- Suggested build order: the data-jobs cluster first (J-01, J-02, J-03 — unblocks the
  owner's immediate backfill need), then the aggregate/boot cluster (J-05 enabling J-04),
  then the measurement capstone (J-06). The decomposer may re-order with reasons.
- `docs/improvement-backlog.md` remains the owner-governed idea registry; the goal-proposer
  writes only between the AUTO markers above.
- Depth: lean by default; full when an iteration first lands user-visible UI changes.

## Improvement direction (engineering) — compute at ingest, serve from storage, load per page

**Principle:** every heavy computation runs inside ingest jobs (fetch / backfill / rebuild),
its result is persisted, and boot + request paths only read storage. Boot = config + engine +
tables + orphan sweep + existence checks. Nothing global loads at startup.

### Ground truth (measured 2026-07-18)
- DB ~811 MiB; `daily_prices` 3,299,561 rows / 590 symbols / 1996-01-02 → 2026-07-17;
  `scanner_results` 66,836 rows (**329 MB — largest table**, `record_json` blobs);
  `forward_returns` 344,334; `scanner_runs` 180 dates (2005-02-25 → 2026-05-01 monthly +
  recent dailies; the 2026-07-17 snapshot now exists, created at boot on 2026-07-18).
- All indexes needed for lazy per-symbol/per-date queries already exist
  (`uq_daily_prices_symbol_date`, `ix_daily_prices_date`, run/ticker/symbol indexes).

### The four offenders to retire
1. **`GET /api/data` coverage** (`data_manager.compute_coverage` →
   `_compute_coverage_uncached`, data_manager.py:771/805): whole-table prefill of 3.3M rows
   on the request path — the documented OOM-crash source (iter-24 evidence, reproduced 2/2);
   result cached only in-process (8 keys), lost on restart.
2. **Boot `ensure_latest_snapshot`** (main.py:73): synchronous full-universe scan whenever
   the newest trading date lacks a snapshot — blocks serving for minutes.
3. **Boot warm-up thread** (warmup.py:122): iterates cadence dates under `bar_cache`,
   lazily pulling the whole universe into RAM to run no-ops on a maintained DB.
4. **Lazy-only caches:** `market_phase_cache`, `event_study_cache` (+ research views) pay
   first-request compute per new date/dataset-version instead of being warmed at ingest.

### Aggregation candidates — compute at ingest, save to DB, serve as row reads
| # | Computation | Today | Persisted form | Ingest update hook | Pages faster |
|---|---|---|---|---|---|
| 1 | Latest-date snapshot (runs+results+sector/theme scores) | synchronous at boot | existing snapshot tables — guarantee the row exists at ingest | end of fetch/`_do_backfill`/rebuild when a new trading date lands | boot unblocks; `/`, `/stocks`, `/sectors`, `/themes` |
| 2 | Cadence snapshots + forward returns | boot warm-up loop | existing tables (backfill already writes them) — make ingest the SOLE path, delete the boot loop | `_do_backfill` (already there) | removes boot's whole-universe RAM load |
| 3 | Coverage payload (universe_count, universe_diagnostic, per-symbol table, gaps, capacity) | whole-table prefill per request | **new** `coverage_snapshot(dataset_version PK, as_of, payload_json)` | `_do_backfill` / rebuild / remove-data finalize | `/data` (3.3M-row scan → one keyed row) |
| 4 | Membership timeline | cached but warmed at boot | existing `membership_timeline_cache` | move warm from boot into `_do_backfill` | `/data` |
| 5 | Market phase & severity (latest as_of) | lazy cache; miss = O(all runs) + SPY/VIX bars | existing `market_phase_cache` — warm the latest key at ingest | `_do_backfill` / rebuild finalize | `/` home card, phase labs |
| 6 | Research event-study / factor-lab / regime-lab hot keys | lazy cache; miss streams results+returns | existing `event_study_cache` — warm default (subject,horizon,all-history) keys at ingest | `_do_backfill` / rebuild finalize | `/research/*` first loads |
| 7 | (optional) Normalized index series; per-date bars-present rollup for the availability heatmap | per-request per-ETF query / grouped scan | small keyed caches | ingest | `/`, `/data` (minor) |

### Cannot be precomputed (user-parameterized) — lazy INDEXED queries, never prefill
- `/api/stocks/{ticker}/bars` (ticker × as_of × range × through) — served by the existing
  `(symbol,date)` unique index; keep lazy.
- Cold arbitrary `as_of` snapshot (`run_scan` on a non-cadence date) — keep create-once with
  per-symbol bounded windows; must never wrap in a whole-table prefill.
- Arbitrary research selectors — the lazy `event_study_cache` is the right shape; precompute
  only the hot default keys.

### Additional binding notes
- The `snapshot_cadence` gate (`config.yaml` `deep_cadence: monthly`, `daily_start:
  2026-06-01`) remains for **automatic warm-up density only**; explicit backfill requests
  override it (J-01, "requested range always wins").
- `max_range_days` (config.yaml, currently 370) is removed with its validation and the tests
  that pin it (`test_data_manager.py:491-518`, `test_api_data.py:294-310`,
  `test_config.py:477-485`, fixture copies in `test_themes.py` / `test_sectors.py` /
  `test_indexes.py`); chunked execution (`import_chunking.date_window_days`) is the
  unbounded-span safety mechanism.
- Launch scripts must actually enforce the declared `server.memory_cap_mb` /
  `malloc_arena_max` (today `config.py:620` claims it; no script does it) and write a
  persistent backend logfile (today uvicorn writes only to the launching terminal).
- Job history must survive restarts: the `/data` progress/history panels read persisted
  `data_provider_runs` (extended with per-date exclusion reasons), not in-memory job state.
