# Goal Iteration 8 — J-53 parallel multi-date backfill + per-stage job timings (final buildable journey) + one-shot J-22/J-23/J-24 + DIA best-effort fetch

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 8
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-53
- **Best-effort data journeys (non-vetoing, single attempt):** J-22, J-23, J-24 (+ the J-44 DIA series leg) — one-shot fetch attempt; honest blocked-NA is an acceptable disposition per goal.md "Data-dependent journeys (non-halting)"
- **Required-still-passing journeys:** J-17, J-34, J-36, J-37, J-38, J-39, J-40, J-41, J-44, J-46
- **Anti-goal reminders:**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **On-demand snapshots stay immutable & lookahead-free.** Creating a snapshot for a newly selected date is create-once: an existing snapshot MUST be read, never overwritten; an as-of-D snapshot MUST use only bars with date ≤ D. *(critical)*
  - **Range backfill stays immutable & lookahead-free.** Snapshots created for a fetched or backfilled date range are create-once: an existing snapshot MUST be read, never overwritten, and an as-of-D snapshot MUST use only bars with date ≤ D.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code. *(the new backfill-concurrency knob is explicitly covered)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Live fetch is real-data-only.** The Data Manager MUST use the config-selected live provider to fetch real EOD bars; on a provider failure it MUST surface an explicit error and MUST NOT synthesize prices to fill a gap or force a successful run.
  - **Import keys are env-or-session, never persisted.** A provider key MUST be read from the environment, or — if pasted into the import UI — held in memory for that run only, never written to disk, the run log, the DB, or any committed file, and never echoed back.
  - **Unfinished-imports actions are idempotent and audit-preserving.** Resume and Retry MUST re-fetch only outstanding work and produce no duplicate fetch or row; the append-only `data_provider_runs` audit trail MUST remain the permanent record of what ran.
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.
  - **No order/execution path.** Research-only. *(critical)*

## GOAL

The Data Manager's multi-date snapshot backfill completes at least ~2× faster than the sequential per-date sum with byte-identical snapshots/forward-returns, and every fetch+backfill job's status payload and `/data` job card surface honest per-stage timings (fetch vs backfill: elapsed, items processed, concurrency used).

## BACKGROUND

J-53 is the LAST remaining failing buildable journey (journey-history: 50 passing/already_passing, J-22/J-23/J-24 blocked-NA non-vetoing, J-53 failing). The iter-7 evaluator (CONTINUE, COHERENCE-PASS, full suite 710/4/0) explicitly recommended this exact scope at **full** depth: J-53 rewires the concurrency-sensitive import/backfill pipeline under critical contracts — create-once/idempotent/concurrency-safe snapshot creation (J-41), serialized SQLite writes, honest progress (J-34/J-37/J-38), and outputs identical to the sequential path — where a subtle corruption would be invisible to browser QA, so the full pipeline's review + audit steps earn their cost. This mirrors the J-46/iter-3 shape (which parallelized the FETCH stage; this iteration parallelizes the multi-date BACKFILL stage and adds the timings surface). The blueprint's import-job-control Data Contract row carries the human-pre-approved J-53 amendment (tag flipped to "[TARGET — iter-8 in flight]"); no new endpoint, no new route — everything rides `/data` and the existing `GET /api/data` / `POST /api/data/jobs*` family.

Per goal.md's "Data-dependent journeys (non-halting)" section and the iter-7 recommendation, this iteration ALSO makes the session's one-shot best-effort attempt at the J-22 expanded-universe data, the J-23/J-24 intraday seed, and the J-44 DIA series — a SINGLE attempt with backoff, never an autonomous retry loop. `/data` is exercised anyway this iteration, so this is the natural place. If the providers stay walled, those journeys are recorded honestly blocked/limited-coverage NA — they MUST NOT halt the loop, drive STALLED, or veto GOAL_ACHIEVED.

**This is the final buildable iteration.** If J-53 passes, the required journeys hold, and the data journeys are honestly dispositioned, the next evaluation is a GOAL_ACHIEVED candidate.

## IN SCOPE

### Backend

- [ ] **Parallel multi-date snapshot backfill** in `apps/backend/app/engine/data_manager.py` (`_do_backfill`, currently a sequential per-date loop): the per-date snapshot computation runs concurrently (mechanism open per goal.md — parallel dates with serialized writes, parallel per-symbol computation within a date, further vectorization, or any combination) so the backfill stage's wall-clock lands at least **~2× below the sequential per-date sum** on a multi-date range. Hard guards, all preserved:
  - SQLite writes stay **serialized/transactional** (compute concurrent, write single-threaded/orderly — the J-46 pattern: workers do compute/IO, the orchestrating thread owns the session).
  - **Create-once / idempotent / concurrency-safe** snapshot creation per J-41: an existing snapshot is read, never overwritten; no `UNIQUE constraint` crash on re-run or concurrent creation; the existing `run_scan` single-flight + IntegrityError guards keep working under the new concurrency.
  - **Identical canonical outputs**: the snapshots/forward-returns produced by the parallel path are identical to the sequential output (same scores/buckets/setups/returns — asserted by the existing scanner/forward-test/immutability/no-lookahead suites plus a new explicit parallel-vs-sequential equality test).
  - **Honest progress**: `JobProgress` counts stay monotonic and never exceed totals; checkpoints stay consistent (J-34/J-37/J-38 intact).
  - The J-46 job-scoped bars-once cache at the `prices:bars_asof` seam remains the single bar-loading path (no second source of bar truth); make it thread-safe if dates share it concurrently.
- [ ] **New concurrency knob in `config.yaml`** (e.g. `data_manager.import_chunking.backfill_workers` or a sibling key the developer judges cleaner; `>= 1`, 1 = serial), boot-validated in `apps/backend/app/config.py` like `fetch_workers` — **no magic numbers**. If the field is required, add it to EVERY inline test config dict (grep the section key across `apps/backend/tests` — now FIVE files incl. `test_indexes.py`; see NOTES).
- [ ] **Per-stage timings** recorded once by the job runner into the job progress/status payload (descriptive operational metadata per the blueprint contract row — never a canonical score): for each executed stage (fetch, backfill) — **elapsed wall-clock**, **items processed** (symbols for fetch / dates for backfill), and **concurrency used**. The backfill stage additionally records the **sum of per-date durations** (or equivalent), so the ≥~2× speedup is evidenced by the job's own timings (wall-clock vs per-date sum), as J-53 step 3 requires. Served through the existing job-status payload (`GET /api/data` job list + `GET /api/data/jobs/{id}`) — **no new endpoint**. Timings appear for completed AND in-flight/resumable/failed jobs honestly (a stage not yet run shows absent/NA, never fabricated).
- [ ] **Benchmark script extension**: `apps/backend/scripts/benchmark_pipeline.py` reports the parallel backfill stage timing vs the sequential baseline (advisory only — never a CI wall-clock gate).
- [ ] **One-shot best-effort data fetch (single attempt, never a loop)**: one attempt, with the existing backoff machinery, to pull (a) the J-22 expanded-universe daily OHLCV + market-cap via the committed runbook / Expand-universe job, (b) the J-23/J-24 intraday seed, and (c) the DIA daily bars (J-44 legend leg; if fetched, commit into the seed per goal.md). Route every fetch through the existing chunked/resumable import engine (no second fetch path). On provider failure: explicit error / rate-limited resumable state, zero fabricated bars, and an honest blocked-NA disposition recorded for the evaluator. This task can succeed partially (e.g. DIA only) — each leg is dispositioned independently.

### Frontend

- [ ] **`/data` job card + job detail render the per-stage timings** (fetch vs backfill: elapsed, items processed, concurrency used; the backfill speedup readable from wall-clock vs per-date sum) — pure re-formatting of the job status payload (the backend computes everything; the frontend renders no derived figure beyond display formatting). Dates via the shared `apps/frontend/lib/dates.ts` formatter (J-42); durations human-readable.
- [ ] New stat labels on the job card (e.g. "Stage timings", "Concurrency") carry the J-47 `TermInfo` info-tooltips reading **config-backed glossary entries added under `config.methodology`** (no code change to the catalog mechanism, no hard-coded copy; tooltip buttons are SIBLINGS of any clickable affordance, never nested — iter-5 lesson).
- [ ] Frontend gate: `tsc --noEmit` (ESLint is not installed in `apps/frontend`).

### New user-facing capability
The operator can see exactly where a fetch+backfill job spent its time — fetch stage vs backfill stage, with elapsed, items, and concurrency — and multi-date backfills finish materially (≥~2×) faster.

### New information displayed
Per-stage timings on the `/data` job card and job detail: fetch elapsed/symbols/concurrency, backfill elapsed/dates/concurrency, and the backfill per-date-sum vs wall-clock evidence of the speedup.

### New user actions
None — no new buttons/forms/controls. Existing job start/Resume/Retry/Dismiss controls are unchanged.

### UI surface changes
`/data` job card and job-status detail gain a stage-timings block. No other page changes.

### Product surface delta
The Data Manager's job reporting goes from "live progress + final summary" to "live progress + final summary + per-stage operational timings", and the multi-date backfill is no longer a sequential wall-clock sum.

### Blueprint conformance
No new surfaces, no new route, no nav change. Everything rides the existing **Data Manager** home (`/data`) and the existing `GET /api/data` / `POST /api/data/jobs*` endpoint family — exactly as pre-registered in the blueprint's import-job-control Data Contract row (J-53 amendment, "[TARGET — iter-8 in flight]", human-approved this resume).

### Data-contract additions
None beyond the pre-registered J-53 amendment: **job stage timings** (fetch vs backfill: elapsed, items processed, concurrency used) — recorded once by the data-manager job runner into the job progress/status payload, served by the existing `GET /api/data` / `GET /api/data/jobs/{id}` reads, re-formatted only by the `/data` job card. Descriptive operational metadata, NOT a canonical score. No value already in the Data Contract gains a second computation or serving path.

## OUT OF SCOPE

- Any new endpoint, page, route, or nav change (J-53 rides `/data` — pre-approved as an additive contract amendment).
- An autonomous retry loop for the data-walled fetches — goal.md mandates a SINGLE best-effort attempt per resume; if walled, record honest NA and move on.
- A CI wall-clock performance gate — the benchmark script and the job's own timings are advisory evidence; no flaky timing assertion in the test suite.
- Parallelizing the background **warm-up** controller or the scheduler — J-53 targets the data-manager multi-date backfill job; warm-up keeps its current behavior (shared seams — `run_scan` guards, the bars-once cache — must simply remain correct under the new concurrency).
- Any change to canonical scoring/forward-return computation, Research/Backtest surfaces, or the J-49/J-45 chart surfaces.
- Code changes for J-22/J-23/J-24 themselves — they auto-complete via data + the committed runbook with no code change; only the one-shot fetch attempt is in scope.
- Destructive `POST /api/data/remove` against any live symbol during QA — preview-only (J-39 lesson; NVDA carries user-added bars that cascade ~5 snapshots if removed).

## DEFINITION OF DONE

- [ ] J-53 passes via browser-qa-agent: a multi-date fetch+backfill job from `/data` shows live accurate progress plus per-stage timings; the backfill stage wall-clock is materially below its per-date sum (≥~2×, evidenced by the job's own timings); a re-run of the same range is idempotent (snapshots read, nothing duplicated, no UNIQUE crash).
- [ ] Parallel-vs-sequential equality proven: existing scanner / forward-returns / immutability / no-lookahead suites all green, plus an explicit test asserting the parallel backfill produces identical snapshots/forward-returns to the sequential path over the same range.
- [ ] Required-still-passing journeys remain green: J-17, J-34, J-36, J-37, J-38, J-39 (preview-only), J-40, J-41, J-44 (including the toggle off→reload→still-off persistence cycle — outstanding QA debt since iter-6), J-46.
- [ ] The one-shot J-22/J-23/J-24 + DIA fetch attempt was made exactly once and each leg is honestly dispositioned (real data committed, or explicit blocked/rate-limited NA — zero fabricated bars).
- [ ] No anti-goal violation introduced; new concurrency knob lives in config (boot-validated, no magic numbers).
- [ ] Full backend pytest suite green to completion (~45–65 min — foreground or handed to the pump; see NOTES); `tsc --noEmit` clean.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8-dev.md`.

## TESTING REQUIREMENTS

- Browser (J-53, on :8835/:3835):
  - Start a multi-date fetch+backfill job from `/data` (the one-shot best-effort live attempt doubles as the fetch leg where a provider responds; per lessons, `alpha_vantage` + session key `demo` reliably exercises the rate-limited/resumable path; a backfill-only job over an uncovered seed range deterministically exercises the backfill stage regardless of provider reachability). Verify live progress stays accurate and per-stage timings render (elapsed, items, concurrency) on the job card.
  - Verify the backfill stage timing evidences ≥~2× vs its per-date sum; re-run the same range and verify idempotency (no duplicates, no crash, honest "already present" outcome).
  - Corroborate job-card claims against persistent backend state (`data_provider_runs` / `import_checkpoints` in `apps/backend/data/trendora.db`) — not the DOM alone.
  - Re-verify the required-still-passing set: J-17 (as-of dates appear, Backtest n grows), J-34 (amber resumable + Resume), J-36 (coverage), J-37/J-38 (pull-missing/unfinished-imports via suite + UI presence), J-39 (preview endpoint ONLY), J-40/J-41 (cold-start readiness badge honest while warming), J-44 toggle off→reload→still-off cycle, J-46 (fetch-pool semantics unchanged).
  - Evidence hygiene (iter-7 evaluator requirement): one md5-unique PNG per claimed surface (or cite a shared file once, honestly); capture fragile legs early before any backend restart; assert any N-counts same-instant against the live aggregate (Ns drift as warm-up matures forward returns).
- Unit/integration:
  - Parallel-vs-sequential snapshot/forward-return **equality** over a fixed multi-date range (workers > 1 vs workers = 1).
  - Concurrency safety: concurrent creation attempts for the same date → one snapshot, no UNIQUE crash (extends the J-41 `test_warmup.py` family); re-run idempotency.
  - Stage timings: present per executed stage with sane values (elapsed > 0, items == processed counts, concurrency == config value); absent/NA for a stage that never ran; correct on the resumable/failed paths.
  - Config validation: new knob boot-validated (`>= 1`); rejection messages explicit; EVERY inline test config dict updated if the field is required (grep across `apps/backend/tests` — five files incl. `test_indexes.py`).
  - Progress honesty under parallelism: counts monotonic, never exceeding totals; checkpoint consistency after a mid-job pause/resume.
- Error cases:
  - Provider failure / persistent 429 during the fetch stage under the parallel backfill build → amber resumable state with honest timings for the completed portion; Resume continues from the checkpoint with no duplicate fetch.
  - A backfill worker raising mid-range → job surfaces an explicit failure for that date, completes/accounts the rest honestly, leaves no partially-written snapshot (transactional writes).
  - Job-status error strings must not leak provider keys (`?token=`/`?apikey=` in `str(httpx.HTTPStatusError)` embeds the full URL — sanitize every NEW parallel error path like the existing ones; grep the job-status response, not just the DB).
  - Invalid backfill range / unknown source → explicit 4xx, unchanged.

## NOTES

- **Re-plan after interruption (scope unchanged):** this spec was re-issued on resume after the prior engine hit an inflight timeout mid-dev-turn. The iter-8 dev work for J-53 is already complete on disk; the pipeline proceeds to review/QA against this same spec. Downstream agents should not be surprised that implementation commits/artifacts predate this file's timestamp — judge the work against the scope above, which is identical to the pre-interruption plan.
- **Evaluator framing:** after this iteration the session is a GOAL_ACHIEVED candidate — J-53 was the last failing buildable journey; J-22/J-23/J-24 blocked-NA are explicitly NON-VETOING per goal.md's "Data-dependent journeys (non-halting)" section. Do not manufacture further scope.
- **Depth = full** per the iter-7 evaluator recommendation: concurrency-sensitive pipeline rewiring whose failure mode (subtly different snapshots) is invisible to browser QA — the reviewer/audit steps are the real safety net here, alongside the equality test.
- Applied lessons (from `state/lessons.md` + session memory):
  - Full backend pytest is ~45–65 min and a dev-turn background run does NOT survive the turn — run targeted modules in the dev turn, hand the full suite to the pump (or run foreground to completion); never two trendora pytest runs concurrently.
  - A new required typed config field must be added to EVERY inline test config dict — count GROWS over time (now FIVE files incl. `test_indexes.py`); grep the section key across `apps/backend/tests`, don't trust a fixed list.
  - The iter-28 serve-fast-boot fix relies on single-flight + `run_scan` IntegrityError guards; keep SQLite writes serialized/transactional and preserve the create-once guards under the new concurrency. The warm-up single-flight + conftest pre-warm pattern keeps API tests deterministic — don't regress it.
  - Provider reality for the one-shot attempt: Yahoo EOD has historically rate-limited this IP (persistent 429; one recent observation suggests it may have relaxed — attempt it once with backoff); `alpha_vantage`+`demo` throttles to resumable (~3–16 min/chunk); Stooq needs a key; nasdaq is empty; Wikipedia works for membership lists. ONE attempt with backoff, then honest NA.
  - Kill dev servers by port (8835/3835), never broad `pkill -f`.
  - Browser-QA PNGs have silently degraded to byte-identical duplicates three times (iter-0/3/6/7) — md5-check captures; the iter-7 evaluator made md5-unique evidence an explicit iter-8 requirement.
  - J-39 smoke ONLY via the preview endpoint — the live host has user-added NVDA bars whose removal cascades snapshots, and `trendora.db` is gitignored (no git restore).
- The `/data` date/symbol inputs remain job parameters, not the global as-of control (one date selector — invariant 5).
- Benchmark evidence is advisory: report numbers in the handoff and the job timings; never gate CI on wall-clock.
