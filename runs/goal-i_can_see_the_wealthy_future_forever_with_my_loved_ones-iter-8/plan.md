# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8 Execution Plan

Target: **J-53** (parallel multi-date backfill ≥~2× + per-stage job timings) — the LAST failing buildable
journey. Plus the session's ONE-SHOT best-effort J-22/J-23/J-24 + DIA fetch attempt (non-vetoing).
Depth: **full** (concurrency-sensitive rewiring under critical immutability/idempotency contracts).
Spec conforms to goal.md (Capability 38, pre-approved blueprint amendment); no scope drift detected.

## What to Build

- **Parallel multi-date snapshot backfill** in `apps/backend/app/engine/data_manager.py::_do_backfill`
  (line ~1227, currently a sequential `for d in targets` loop calling `scanner.run_scan` +
  `forward_testing.backfill_run_forward_returns`). Mechanism open (parallel dates / parallel per-symbol
  compute within a date / vectorization / combo), but hard guards are non-negotiable:
  - **Workers must NEVER touch the SQLModel session** — SQLite sessions are not thread-safe. Follow the
    J-46 pattern: workers do pure compute; the orchestrating thread owns ALL DB reads/writes/commits.
  - The J-46 `prices.bar_cache(session)` is keyed by `id(session)` and is the single bar-loading path —
    either pre-populate it on the orchestrating thread before fan-out, or make its read path
    thread-safe (lock) if workers consult it concurrently. No second source of bar truth.
  - Create-once / idempotent / concurrency-safe per J-41: existing snapshot read, never overwritten; the
    `run_scan` single-flight + IntegrityError guards keep working; no UNIQUE crash on re-run/concurrent.
  - **Byte-identical canonical outputs** vs the sequential path (same scores/buckets/setups/returns).
  - `JobProgress` counts stay monotonic, never exceed totals; checkpoints stay consistent.
  - Every worker joined before the job thread returns (iter-28 TestClient determinism lesson).
- **New config knob** `data_manager.import_chunking.backfill_workers` (or a cleaner sibling — dev's
  call; assume `backfill_workers`, committed default 4) in repo-root `config.yaml`; required typed field
  on `ImportChunkingCfg` in `apps/backend/app/config.py` with `>= 1` boot validation mirroring
  `fetch_workers` (config.py ~1190–1201). **Grep `import_chunking` across `apps/backend/tests/` — it
  currently appears in SEVEN files** (test_config, test_config_engine, test_sectors, test_themes,
  test_indexes, test_data_manager, test_data_manager_parallel); update every inline config dict that
  constructs the section. Do not trust the old "five files" count.
- **Per-stage timings** on `JobProgress` (data_manager.py ~764) + `to_dict()`: for each EXECUTED stage
  (fetch, backfill) record elapsed wall-clock, items processed (symbols / dates), concurrency used; the
  backfill stage additionally records the **sum of per-date durations** so the job's own payload
  evidences the ≥~2× speedup (wall-clock vs per-date sum). Assumed shape: an additive `stages` object
  (e.g. `{"fetch": {...}, "backfill": {...}}`) — absent/NA for a stage that never ran, honest on
  in-flight/resumable/failed jobs, never fabricated. Served by the existing `GET /api/data` +
  `GET /api/data/jobs/{id}` — **no new endpoint, no new route**. Descriptive metadata, never canonical.
- **Benchmark extension**: `apps/backend/scripts/benchmark_pipeline.py` reports parallel backfill stage
  timing vs sequential baseline (advisory only; never a CI wall-clock gate, never imported by tests).
- **Frontend** (`apps/frontend/app/data/page.tsx`, ~1500 lines — job card + job detail): render a
  stage-timings block (fetch vs backfill: elapsed / items / concurrency; backfill per-date-sum vs
  wall-clock readable). Pure re-formatting of the payload — no derived figure beyond display formatting.
  Dates via shared `apps/frontend/lib/dates.ts`; durations human-readable. New stat labels ("Stage
  timings", "Concurrency") carry J-47 `TermInfo` tooltips backed by **new glossary entries added under
  `config.methodology`** (config.yaml ~754; catalog mechanism unchanged). Tooltip triggers are SIBLINGS
  of clickable affordances, never nested (iter-5 lesson).
- **One-shot best-effort data fetch (single attempt, never a loop)**: (a) J-22 expanded-universe via the
  committed runbook / Expand-universe job, (b) J-23/J-24 intraday seed, (c) DIA daily bars (J-44 leg;
  commit into seed if fetched). All through the existing chunked/resumable import engine — no second
  fetch path, no new code beyond what J-53 already adds. Each leg dispositioned independently in the
  handoff: real data committed, or explicit blocked/rate-limited NA — zero fabricated bars.

## Agents Required
- developer: yes — one developer implements backend (parallel backfill, config knob, timings, benchmark,
  tests) + frontend (stage-timings block, glossary entries) and performs the one-shot fetch attempt.
  - backend-data: yes
  - frontend-ux: yes

Frontend Present: yes

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` -- parallel `_do_backfill`, stage-timing recording, JobProgress fields + to_dict
- `apps/backend/app/config.py` -- `backfill_workers` typed field + `>= 1` boot validation
- `config.yaml` (repo root) -- `backfill_workers` knob + new `methodology` glossary entries for the new stat labels
- `apps/backend/app/engine/prices.py` -- bar-cache thread-safety IF workers share it concurrently (else untouched)
- `apps/backend/scripts/benchmark_pipeline.py` -- parallel-vs-sequential backfill stage report
- `apps/backend/tests/test_data_manager_parallel.py` (+ siblings) -- equality, concurrency-safety, timings, progress-honesty, error-path tests
- `apps/backend/tests/test_config.py` + every inline-config test file (grep!) -- knob fixtures + validation tests
- `apps/frontend/app/data/page.tsx` -- stage-timings block on job card + detail (re-format only)
- `apps/frontend/lib/api.ts` -- additive job-payload types for `stages`
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8-dev.md` -- handoff incl. one-shot fetch dispositions

## UI Evolution
- New user-facing capability: operator sees exactly where a fetch+backfill job spent its time, per stage; multi-date backfills finish ≥~2× faster.
- New information displayed: fetch elapsed/symbols/concurrency; backfill elapsed/dates/concurrency; backfill per-date-sum vs wall-clock.
- New user actions: none (existing start/Resume/Retry/Dismiss unchanged).
- UI surface changes: `/data` job card + job-status detail gain a stage-timings block. Nothing else.
- Navigation changes: none.

## Visual Requirements
- Component patterns: extend the existing job-card stat rows/blocks in `app/data/page.tsx` — same compact stat-label + monospace-value treatment already used for chunk progress; `TermInfo` markers on the new labels.
- Layout: inline block within the existing job card and job detail; no new page/panel.
- Key visual effects: match the existing dense dark analytical style; no new effects.
- States to handle: stage absent (never ran) → omit/NA honestly; in-flight job → timings for completed portion; resumable/failed → honest partial timings.

## Test Strategy

Unit/integration (targeted modules in dev turn; FULL suite ~45–65 min handed to the pump — never two
pytest runs concurrently, no server on :8835 during the run):
- **Parallel-vs-sequential equality** over a fixed multi-date range (workers>1 vs workers=1): identical snapshots + forward returns, row-level.
- Concurrency safety: concurrent creation for the same date → one snapshot, no UNIQUE crash (extends the J-41 `test_warmup.py` family); re-run idempotency.
- Stage timings: present per executed stage (elapsed > 0, items == processed counts, concurrency == config value); absent for a never-run stage; correct on resumable/failed paths.
- Config validation: knob `>= 1`, explicit rejection messages; every inline config dict updated (grep).
- Progress honesty under parallelism: monotonic counts ≤ totals; checkpoint consistency across pause/resume.
- Error cases: worker exception mid-range → explicit per-date failure, rest accounted, no partial snapshot (transactional); 429 during fetch → amber resumable with honest partial timings, Resume = zero duplicates; **new parallel error strings scrubbed for `?token=`/`?apikey=` — assert on the job-status response, not just the DB**.
- Existing scanner / forward-testing / immutability / no-lookahead / warm-up suites all green unchanged.

Browser (J-53 on :8835/:3835; backend restart required so new payload fields serve — kill by port only):
- Start a multi-date fetch+backfill job from `/data`; a **backfill-only job over an uncovered seed range** deterministically exercises the backfill stage; `alpha_vantage` + session key `demo` exercises the rate-limited/resumable fetch leg. Verify live progress + stage timings render.
- Verify backfill wall-clock ≥~2× below its per-date sum from the job's own timings; re-run the same range → idempotent (no duplicates, no crash, honest outcome).
- Corroborate against `data_provider_runs` / `import_checkpoints` in `apps/backend/data/trendora.db` — not the DOM alone.
- Required-still-passing: J-17, J-34, J-36, J-37, J-38, J-39 (**preview endpoint ONLY** — never live remove), J-40, J-41, J-44 (incl. toggle off→reload→still-off cycle — outstanding QA debt), J-46.
- Evidence hygiene: one md5-unique PNG per claimed surface (duplicates happened iters 0/3/6/7 — explicit iter-8 requirement); capture fragile legs before any restart; assert N-counts same-instant vs the live aggregate.
- Frontend gate: `cd apps/frontend && npx tsc --noEmit` (ESLint not installed).

## Risks / Watch-outs
- **Session thread-safety is the central trap**: `run_scan` currently couples compute and write on one session. Whatever split the developer chooses, workers must do compute only; orderly single-threaded writes. A subtle output difference is invisible to browser QA — the equality test + reviewer/audit are the safety net.
- Bar cache (`_BAR_CACHES` keyed by `id(session)`) must not be read concurrently without a lock, and must be fully populated (or safely lazy) before fan-out; do NOT introduce a second bar-loading path.
- Don't regress warm-up determinism (single-flight + conftest pre-warm); warm-up itself is OUT of scope — only shared seams must stay correct.
- ~2× is evidenced by the job's own timings + advisory benchmark — **no CI wall-clock assertion** (flaky).
- One-shot fetch: exactly ONE attempt per leg with existing backoff; provider reality — Yahoo historically 429s this IP (may have relaxed; try once), `alpha_vantage`+`demo` → resumable throttle, Stooq needs a key, nasdaq empty. Honest NA is an acceptable disposition; it must not veto.
- httpx error strings embed full URLs → key leakage in NEW parallel error paths; scrub like the existing ones.
- Inline test-config dict count GROWS — grep, don't assume.
- Out of scope: any new endpoint/page/route/nav; retry loops for walled fetches; CI perf gate; parallelizing warm-up/scheduler; changes to canonical scoring/returns or Research/Backtest/chart surfaces; destructive remove against live symbols.

## Definition of Done (gates)
- [ ] J-53 passes via browser QA: live accurate progress + per-stage timings on `/data`; backfill wall-clock ≥~2× below per-date sum from the job's own payload; idempotent re-run.
- [ ] Explicit parallel-vs-sequential equality test green; all existing scanner/forward-return/immutability/no-lookahead suites green.
- [ ] Required-still-passing set green (incl. J-44 persistence cycle, J-39 preview-only).
- [ ] One-shot J-22/J-23/J-24 + DIA attempt made exactly once; each leg honestly dispositioned (data committed or explicit NA; zero fabricated bars).
- [ ] No anti-goal violation; knob in config, boot-validated, no magic numbers.
- [ ] Full backend pytest green to completion (pump or foreground); `tsc --noEmit` clean.
- [ ] Dev handoff at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8-dev.md` with benchmark numbers + fetch-leg dispositions.

## Key Test Scenarios
- Backfill-only job over an uncovered seed range with workers=4 vs workers=1: identical snapshots/forward-returns; wall-clock ≥~2× below per-date sum; timings payload honest.
- Concurrent same-date creation → one snapshot, no UNIQUE crash; re-run of a covered range → "already present", zero new rows.
- Mid-job 429 (alpha_vantage demo) → resumable with partial honest timings; Resume → completion, zero duplicate fetches, no key leakage in `errors[]`.
- `/data` job card renders stage-timings block with TermInfo tooltips reading new config.methodology entries.
