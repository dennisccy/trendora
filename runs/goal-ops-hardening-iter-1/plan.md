# goal-ops-hardening-iter-1 Execution Plan

Implements J-01 (backfill honors requested range, explains zero-work) + J-03 (no per-run
range cap), per `docs/phases/goal-ops-hardening-iter-1.md`. This is exactly the "data-jobs
cluster" `docs/goal.md`'s suggested build order and the iter-0 evaluator both name as the
correct next step — no drift from the project goal, no scope creep against CORE RULES or the
Anti-goals detected in the phase spec. Depth: full (data-contract change + first user-visible
UI change this session, per goal.md's own trigger rules).

## What to Build

- **Cadence bypass:** `_do_backfill` stops applying `_cadence_allowed_dates` to explicit
  `backfill`/`both` requests — every trading day in `[start,end]` becomes a target regardless
  of `snapshot_cadence`. `rebuild`'s target selection is unchanged (still cadence-filtered) —
  confirmed by `assumptions.md` iter-1 this is a deliberate, reversible scoping choice.
- **Run-summary exclusion-breakdown contract:** `dates_total` is redefined to mean "trading
  days in the requested range" (today it means post-cadence/already-snapshotted-filtered
  count). Four new fields join the same `_run_detail()` JSON blob persisted in
  `data_provider_runs.message` (no new DB column): `calendar_days`, `non_trading_days`,
  `already_snapshotted`, `error_other`. Surfaced through `summarize_provider_run` into
  `GET /api/data`. Invariants: `non_trading_days + dates_total == calendar_days`;
  `snapshots_created + already_snapshotted + error_other == dates_total`.
- **Date-window chunking** added to `_do_backfill`'s execution loop, reusing the existing
  `_date_windows()` helper / `import_chunking.date_window_days` config and the dormant
  `chunk_index`/`chunk_total` fields (today populated only by the fetch stage's `_chunk_plan`).
- **`max_range_days` removed entirely:** the `DataManagerCfg` field + its positivity check
  (`config.py`), the `config.yaml` entry, and `validate_job_request`'s span-cap rejection
  (`data_manager.py`) are all deleted. Chunking becomes the safety mechanism for unbounded
  spans (AG-8).
- **Frontend `/data`:** the Job progress panel renders the latest persisted run
  (status/summary/breakdown) when no job has started this browser session but history exists
  — never the literal "No job has been started this session" text once `runs` is non-empty. A
  new visually-distinct zero-work state (badge/label) on both the Job progress panel and Run
  history table, mirroring the existing `interrupted`-vs-`failed` precedent in `statusVariant`.
  The four new breakdown counts render inline on both panels. `DataRun`/`DataJob` TS interfaces
  gain the four nullable fields.
- Test suite updated to the new no-cap / new-breakdown contract across the spec's 6 named
  files, plus 2 more this research found (see **Flags** below).

## Agents Required

- **developer: yes** — implements both backend (`data_manager.py`, `config.py`, `config.yaml`,
  8 test files) and frontend (`page.tsx`, `api.ts`) changes. Trendora's roster has one
  implementation agent covering both; this is a single dispatch, not two.
- **backend-data: yes** — cadence bypass, run-summary contract, chunking loop, cap removal.
- **frontend-ux: yes** — persisted-history fallback, zero-work visual distinction, inline
  breakdown counts on an already-shipped page (no new page/route).

Frontend Present: yes

## Files to Create/Modify

**Backend:**
- `apps/backend/app/engine/data_manager.py` — `_do_backfill` (~2467-2510: scope the cadence
  bypass to `backfill`/`both` only, not `rebuild`; add a date-window chunking loop over
  `_date_windows(start, end, import_chunking.date_window_days)`, advancing
  `prog.chunk_index`/`chunk_total`); `_run_detail` (~2912-2938: add `calendar_days` /
  `non_trading_days` / `already_snapshotted` / `error_other` to the JSON blob);
  `summarize_provider_run` (~3486-3516: surface the 4 new fields into the API payload);
  `validate_job_request` (~1834-1839: delete the `span_days > max_range_days` check)
- `apps/backend/app/config.py` — `DataManagerCfg` (~2068, ~2084-2091: delete `max_range_days`
  field + its positivity check)
- `config.yaml` — delete the `data_manager.max_range_days: 370` line (~57)
- `apps/backend/app/models.py` — **intentionally NOT touched.** No new DB column/migration;
  the breakdown fields live in the existing JSON `message` blob (same mechanism
  `date_failures`/`stages`/`omitted` already use).

**Backend tests (named in the phase spec):**
- `apps/backend/tests/test_data_manager.py` (~491-518) — replace the shrink-and-reject cap
  test with cadence-bypass (`backfill`/`both` vs `rebuild`-unchanged) + breakdown-invariant +
  chunk-plan-arithmetic tests. Use a small `date_window_days` override or a narrow date
  fixture — **never execute a full 370+ day backfill to completion** in a test (spec NOTES:
  documented hang risk on this codebase's multi-decade basis).
- `apps/backend/tests/test_api_data.py` (~294-310) — replace the 400-rejection test with a
  >370-day acceptance test asserting `chunk_total > 1`.
- `apps/backend/tests/test_config.py` (~23, ~477-485) — drop the `max_range_days` fixture key
  + assertion.
- `apps/backend/tests/test_themes.py` (~80), `test_sectors.py` (~74), `test_indexes.py` (~35)
  — drop the `"max_range_days": 370` fixture-dict copy.

**Backend files NOT in the phase spec's named list, found by this research (see Flags):**
- `apps/backend/tests/test_config_engine.py` (~26) — same stray `"max_range_days": 370`
  fixture-dict copy as the 3 files above. Harmless if left (`DataManagerCfg` has
  `extra="allow"`, confirmed at `config.py:2065`) but stale — drop for consistency.
- `apps/backend/scripts/build_qa_fixture_db.py` (~149-160) — a **real runtime read** of
  `cfg.data_manager.max_range_days` (not a test fixture literal) that bounds its benchmark
  window's span. Deleting the config field without touching this raises `AttributeError` the
  next time the script runs. Remove the check (no cap left to compare against) or replace with
  a local constant if a sanity bound on window size is still wanted.

**Frontend:**
- `apps/frontend/app/data/page.tsx` — `JobProgressPanel`'s null-job branch (~2481-2490: when
  `runs.length > 0`, render the latest persisted run instead of the empty-history copy);
  `statusVariant`/`statusLabel` (~92-114: add a zero-work-distinct variant, keyed off
  `snapshots_created === 0` for a `backfill`/`both`/`rebuild`-kind `ok` run), applied in both
  `JobProgressPanel` (~2502-2606) and `RunHistoryPanel` (~3281-3339); render the 4 new
  breakdown counts inline in both panels.
- `apps/frontend/lib/api.ts` — `DataRun` (~2347-2367) and `DataJob` (~2555+) interfaces: add
  `calendar_days`, `non_trading_days`, `already_snapshotted`, `error_other` (all
  `number | null`, matching the existing `dates_total` nullability pattern).

**Implementation note (not a blocker):** `DataRun` (persisted row) and `DataJob` (live
in-session job) are different shapes — `DataRun` has no `symbols_total`/`chunk_index`/
`chunk_total`. The "render the latest persisted run" branch should build a reduced view from
`DataRun` fields (status, summary/message, the new breakdown counts), not force-fit `runs[0]`
into the full live-job rendering path.

## UI Evolution

- **New user-facing capability:** an operator can submit a backfill over any explicit date
  range — including >370 calendar days — and it actually executes: every trading day in range
  is a real target, no cadence-driven silent no-op, no size rejection.
- **New information displayed:** on `/data`'s existing Job progress panel and Run history
  table — the calendar/non-trading/already-snapshotted/error breakdown for a completed
  backfill; a distinct zero-work visual state vs. a productive run's success state; chunk N/M
  progress for a large backfill (previously fetch-only); the most recent persisted run's
  outcome on page load even with no job started this browser session.
- **New user actions:** none — the existing job form (kind selector, start/end inputs, Start
  button) is unchanged.
- **UI surface changes:** `/data`'s existing Job progress panel and Run history table only —
  no new page or panel.
- **Navigation changes:** none.

## Visual Requirements

- **Component patterns:** extend the existing `Badge` + `statusVariant`/`statusLabel` helpers
  (do not introduce a new badge component) for the zero-work-distinct state; reuse the
  existing `chunk-progress` badge pattern (`data-testid="chunk-progress"`, today shown only
  for fetch jobs) so backfill chunk progress looks identical to fetch chunk progress.
- **Layout:** no new layout — same `Card`/`PanelTitle` structure for Job progress, same
  `<table>` structure for Run history; breakdown counts are additional inline text/small stat
  rows within existing panels.
- **Key visual effects:** none new. Per goal.md's explicit anti-goal language ("never the same
  unexplained green success badge"), the zero-work state must read as visually distinct from
  the plain `ok` green success look — follow the existing calm/factual palette (ok=green,
  warn=amber, danger=red, default/neutral=grey), reusing the neutral treatment already used for
  `interrupted` as the nearest precedent rather than inventing a new color.
- **States to handle:** zero-work success (distinct from productive success); still-running
  backfill with chunk progress; persisted-history-only initial render (no session job,
  `runs.length > 0`); existing failed/partial/interrupted/resumable states unchanged and must
  not regress (J-04 spot-check).

## Key Test Scenarios

(condensed from the phase spec's Test-first contract — exact figures the spec pins)

- **TC-1/TC-2:** 2026-05-02→2026-05-29 backfill → `dates_total=19`, `snapshots_created=19`,
  `already_snapshotted=0`, `non_trading_days=9`, `error_other=0`, `calendar_days=28`;
  `/scanner-runs` gains 2026-05-04/05-15/05-29 with stored-snapshot leaderboards.
- **TC-3:** weekend-only 2026-05-02→05-03 → `dates_total=0`, `calendar_days=2`,
  `non_trading_days=2`, rendered in the distinct zero-work state (not the plain green success
  badge).
- **TC-4:** identical re-run of the May range → `snapshots_created=0`, `already_snapshotted=19`,
  `non_trading_days=9`, `dates_total=19`, `calendar_days=28`, same distinct zero-work state as
  TC-3.
- **TC-5/TC-6:** page reload after all 3 runs → Run history still lists all three with the same
  counts; no panel shows the literal "No job has been started this session" text; a fresh load
  with history-but-no-session-job shows the latest persisted run's status/summary/breakdown.
- **TC-7/TC-8:** a >370-day request (e.g. 2025-06-01→2026-07-17, 412 days) is accepted (no
  4xx), `chunk_total > 1`, and polling shows `chunk_index` advancing to ≥1 and `dates_done`
  advancing above 0 with no cap-related error.
- **TC-9:** `max_range_days` absent from `DataManagerCfg`/`config.yaml`; the 6 spec-named test
  files (+2 flagged) assert the new no-cap contract.
- **TC-10:** a `rebuild` job's target-date set is still governed by `_cadence_allowed_dates`
  unchanged, even though its execution now shares `_do_backfill`'s date-window chunking loop.
- **TC-11:** an all-non-trading-day range (e.g. one weekend) completes with `error_other=0` and
  no fabricated per-date failure.
- **Regression spot-check (J-04, required-still-passing, not this iteration's build target):**
  fast boot, phase-aware initializing badge, distinct crash presentation, and the
  interrupted-job-after-restart state must remain observable — this iteration's changes touch
  the exact same `_do_backfill` / `data_provider_runs` / `/data` page J-04 depends on.

## Flags / Alignment Notes

- No drift from `docs/goal.md` found: this iteration builds exactly the journeys/order goal.md
  and the iter-0 evaluator recommend; no evidence-ledger/proven-language claims are introduced
  (AG-1/AG-4/AG-6 N/A — this cycle carries no Evidence Claims per goal.md's Loop Mechanics).
- Two files outside the phase spec's own file list should be added to the developer's worklist
  (also listed above under Files to Create/Modify): `test_config_engine.py` (cosmetic) and
  `build_qa_fixture_db.py` (real `AttributeError` risk on next invocation of that tool — it is
  not exercised by this iteration's own browser-QA, which runs J-01/J-03 against the main
  committed seed DB, not a fixture DB, but must not be left broken).
- This iteration's cadence-gate fix also happens to unblock J-05's single-day-backfill
  precondition (same root cause per `lessons.md` iter-0) — building J-05's aggregate-refresh
  hooks themselves stays out of scope per the phase spec's OUT OF SCOPE list; do not expand
  into that work.
- J-04 (partial) is required-still-passing, not a build target this iteration — no code change
  should target J-04; it is re-verified only because this iteration's changes touch the same
  file/table/page it depends on.
