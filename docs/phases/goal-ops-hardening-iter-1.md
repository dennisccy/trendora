# Goal Iteration 1 — Backfill honors the requested range; no per-run range cap (J-01 + J-03)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 1
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-01, J-03
- **Required-still-passing journeys:** J-04 (partial status, not currently "passing" — but this iteration's changes to `_do_backfill` / `data_provider_runs` / the `/data` page touch the exact same file, table, and page J-04 depends on, so its 5 already-working sub-behaviors — fast boot, phase-aware initializing badge, distinct crash presentation, and especially the interrupted-job-after-restart state — must be re-verified, not disturbed)
- **Anti-goal reminders** (verbatim from `docs/goal.md`):
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the committed seed / local provider fixtures — no live external network calls or paid data services may be introduced without an explicit goal.md amendment. *(critical)*

## GOAL

An operator can request a backfill over any explicit date range — including spans over 370 days — and see every requested trading day actually targeted, chunked progress that is never rejected for size, and an honest, visually distinct explanation for zero-work outcomes that survives a page reload.

## BACKGROUND

The iter-0 baseline confirmed J-01 and J-03 share one root cause: `_do_backfill`'s cadence gate (`_cadence_allowed_dates`, `apps/backend/app/engine/data_manager.py` ~:2497) filters explicit backfill requests, so a May-2026 backfill computes `dates_total=0` even though 19 real trading days exist in range, while `config.yaml`'s `max_range_days: 370` separately rejects any longer span outright — exactly the "Data-jobs cluster (J-01 + J-03), depth = full" the iter-0 evaluator recommended next, and what goal.md's own suggested build order names first. This iteration lands the lesson-flagged fix first ("requested range always wins" — `lessons.md` iter-0, applies to any iter touching `_do_backfill`/`_cadence_allowed_dates`), extends the same `_do_backfill` / `data_provider_runs` path with the run-summary exclusion-breakdown contract goal.md's Product Shape already specifies as `[TARGET]` in `blueprint.md`, and removes the range cap together with real date-window chunking (reusing the `chunk_index`/`chunk_total` fields and frontend badge already built for fetch jobs, per J-03's own acceptance: "the chunk plan derives from the config `import_chunking` values"). Depth is **full**: Trigger 2 (data model — two blueprint Data-Contract rows, "Backfill run-summary contract" and "Job history & per-date exclusion reasons," change their served JSON shape) and Trigger 1 (structural/cross-cutting — the change spans `_do_backfill`'s execution loop, `config.py`, `config.yaml`, `validate_job_request`, and 6 test files) both hold, and this is also the session's first shipped user-visible UI change (the zero-work-distinct badge and the persisted-history Job-progress panel), matching goal.md's own "full when an iteration first lands user-visible UI changes" rule. Target selection follows the priority rubric's rule 3 (unblockers) exactly as the iter-0 evaluator recommended — no rubric deviation.

## IN SCOPE

### Backend
- [ ] `_do_backfill`'s cadence gate (`apps/backend/app/engine/data_manager.py`): make an explicit user-requested `backfill`/`both` job's date range always win over `_cadence_allowed_dates` — every trading day in `[start, end]` becomes a candidate regardless of `snapshot_cadence`. The `rebuild` kind keeps its current cadence-filtered target selection unchanged (out of scope — see NOTES).
- [ ] `_do_backfill`'s execution loop: chunk the target-date list into `import_chunking.date_window_days`-sized windows, advancing the existing (currently fetch/expand-only) `chunk_index`/`chunk_total` progress fields. No new config keys — reuses `import_chunking` and the frontend's existing chunk-progress badge.
- [ ] `_run_detail`'s persisted run-summary JSON + `JobProgress` (`data_manager.py`): add the exclusion-reason breakdown for `backfill`/`both`/`rebuild` kinds — `calendar_days`, `non_trading_days`, `already_snapshotted`, `error_other` — and redefine `dates_total` to mean "trading days in the requested range" (not the old post-already-snapshotted-filter target count). See Data-contract additions below for exact fields/invariants. No new DB column — the same JSON blob `data_provider_runs.message` already holds `date_failures`/`stages`/`omitted`.
- [ ] `summarize_provider_run` (`data_manager.py`): surface the new breakdown fields from the same parsed JSON blob into the `GET /api/data` `runs` payload — no second computation path.
- [ ] Remove `max_range_days` entirely: the field + its positivity check in `DataManagerCfg` (`config.py`), the `config.yaml` entry, and `validate_job_request`'s span-cap rejection (`data_manager.py`). An explicit backfill/fetch/both request of any span is accepted; the chunking above is the safety mechanism.
- [ ] Update the pinning-test locations goal.md names to the new no-cap contract: `test_data_manager.py` (~491-518), `test_api_data.py` (~294-310), `test_config.py` (~23, ~477-485), and the `max_range_days: 370` fixture-dict copies in `test_themes.py`, `test_sectors.py`, `test_indexes.py`.

### Frontend
- [ ] `/data` Job progress panel (`apps/frontend/app/data/page.tsx`): when no job has started this browser session but persisted run history exists, render the latest persisted run's outcome (status, summary, breakdown) instead of "No job has been started this session" — reserve that exact copy for the true no-history-ever case (empty `runs`).
- [ ] Run history table + Job progress panel (`page.tsx`): give a zero-work outcome (`backfill`/`both`/`rebuild` kind, status `ok`, `snapshots_created === 0`) a visually distinct badge/label from a productive `ok` run — mirroring the existing precedent of `interrupted` already reading as a distinct neutral badge from `failed`/`ok` in `statusVariant` — and render the new breakdown counts (already-snapshotted / non-trading / error) inline on both panels.
- [ ] `DataRun` / `DataJob` TypeScript interfaces (`apps/frontend/lib/api.ts`): add the four new nullable breakdown fields, matching the existing `dates_total`/`snapshots_created` nullability pattern (null for non-backfill kinds).

### New user-facing capability
An operator can submit a backfill over any explicit date range — including a >370-calendar-day span — and it actually executes: every trading day in range is a real target (no silent cadence-driven no-op), and the range-size rejection is gone.

### New information displayed
On `/data`'s existing Job progress panel and Run history table: the calendar-day / non-trading / already-snapshotted / error breakdown for a completed backfill run; a distinct "zero-work" visual state (vs. a productive run's success state); chunk N/M progress for a large backfill (previously shown only for fetch jobs); the most recent persisted run's outcome shown on page load even when no job has started this browser session.

### New user actions
None new — the existing job form (kind selector, start/end date inputs, Start button) is unchanged; it now simply accepts any range and produces honest, persisted results.

### UI surface changes
`/data`'s existing Job progress panel and Run history table only — no new page or panel.

### Product surface delta
The Data Manager surface (`/data`) goes from silently no-op-ing on realistic backfill requests (any May-2026 range, any >370-day span) to honestly executing and explaining every request, with zero-work and productive outcomes visually distinguishable and durable across reloads.

### Blueprint conformance
Extends the existing "Data Manager" (`/data`) canonical home already registered in `blueprint.md`'s Information Architecture for J-01/J-03 — no new page, no nav change, no `blueprint.reapproval-requested` needed.

### Data-contract additions
Extends two **already-registered** `[TARGET]` blueprint rows (no new Data-Contract entry) — "Backfill run-summary contract" and "Job history & per-date exclusion reasons" — both computed by `_do_backfill`'s finalize (`app.engine.data_manager`) into the existing `data_provider_runs.message` JSON blob (no new DB column) and served by the existing `GET /api/data` (`runs` list) + `GET /api/data/jobs/{job_id}` (live poll) — never a second computation path. `blueprint.md` has been updated this iteration to record these exact fields and to correct an inaccurate "served by" description. Exact fields, present for `backfill`/`both`/`rebuild` kinds only (null for `fetch`/`expand`, matching the existing `dates_total` nullability):
- `dates_total: int >= 0` — REDEFINED this iteration to mean trading days in the requested range (was: post-cadence/already-snapshotted-filtered target count).
- `calendar_days: int >= 0` — inclusive calendar-day span of `[start, end]`.
- `non_trading_days: int >= 0` — calendar days in range that are not trading days.
- `already_snapshotted: int >= 0` — trading days in range that already had a snapshot before this run started.
- `error_other: int >= 0` — trading days in range whose scan/persist failed this run (mirrors `len(date_failures)`).
- `snapshots_created: int >= 0` — unchanged existing field.
- Invariants: `non_trading_days + dates_total == calendar_days`; `snapshots_created + already_snapshotted + error_other == dates_total`.

## OUT OF SCOPE

- J-04's persistent logfile + `ulimit`/`MALLOC_ARENA_MAX` enforcement in `scripts/start-backend.sh` — the only remaining gap in J-04's `partial` status, deferred per the "Do not redo" list.
- J-05's ingest-finalize aggregate-refresh hooks (latest-date snapshot trigger, `coverage_snapshot` table, membership-timeline/market-phase/research-cache warm-from-ingest) and J-06's page-load-budget measurements/lazy-loading fixes — both deferred per the evaluator's explicit recommendation. This iteration's cadence-gate fix happens to make J-05's single-day-backfill precondition newly ingestable as a side effect; it does not build J-05's aggregate-refresh contract.
- `rebuild` kind's cadence-filtered target selection — unchanged (still governed by `_cadence_allowed_dates` exactly as today); only its execution now shares `_do_backfill`'s date-window chunking loop.
- Any new nav item, page, or route — J-01/J-03 extend the existing `/data` (Data Manager) surface only.
- Any new `data_provider_runs` DB column or migration mechanism — the exclusion-breakdown fields live in the existing JSON `message` blob, matching `date_failures`/`stages`/`omitted`'s existing pattern.
- Full completion of a >370-day backfill within the QA/test window — goal.md's own acceptance allows completion to extend beyond it; only acceptance (no rejection) + first-chunk/first-dates progress is required.
- Changing `resumable`/`interrupted`/`failed`/`partial` status semantics or the `dismissed` soft-delete mechanism — unrelated to this iteration.
- Introducing any live/network data provider call for backfill — backfill remains the offline, seed-only create-once path (AG-9).
- Re-verifying the 25 archived mcp-loop journeys (not tracked in this session's `journey-history.json`).
- Editing `docs/goal.md` (lint-final, commit `9c98cb3`).

## DEFINITION OF DONE

- [ ] J-01 passes via browser-qa-agent: a 2026-05-02→2026-05-29 backfill reports `dates_total=19` / `snapshots_created=19` / `already_snapshotted=0` / `non_trading_days=9` / `calendar_days=28`, and `/scanner-runs` gains the expected dates; a weekend-only run and an identical re-run each report an honest, visually-distinct zero-work outcome with the calendar/trading-day breakdown; a page reload still lists all runs and never shows the literal text "No job has been started this session" when history exists.
- [ ] J-03 passes via browser-qa-agent: a >370-calendar-day backfill request is accepted (no "date range too large" rejection), begins executing with visible chunk progress (`chunk_index`/`chunk_total`) derived from `import_chunking.date_window_days`, and its first chunk completes.
- [ ] Required-still-passing journey J-04 (partial) does not regress: its already-working sub-behaviors — fast boot, phase-aware initializing badge, distinct crash presentation, and the interrupted-job-after-restart state — remain observable via replay/browser-qa.
- [ ] No anti-goal violation introduced: AG-8 (chunked, memory-bounded execution for large ranges; `rebuild`'s existing behavior undisturbed), AG-9 (no live network calls introduced), AG-3 (the exclusion-breakdown arithmetic invariants hold exactly, never approximated).
- [ ] Unit tests pass (`_do_backfill`'s cadence-bypass-for-explicit-requests vs. `rebuild`-unchanged; the breakdown-field invariants; `validate_job_request`'s cap removal; the chunk-plan arithmetic); no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-1-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** J-01, J-03 (named journeys, full walkthrough per goal.md's steps). Spot-check J-04's interrupted-job/badge states as a regression check (replay lane, or LLM browser-qa fallback since no golden script exists yet for a never-passed journey).
- **Unit/integration:** `_do_backfill`'s cadence-bypass applies to `backfill`/`both` but not `rebuild`; the four new breakdown fields and the two invariants (`non_trading_days + dates_total == calendar_days`; `snapshots_created + already_snapshotted + error_other == dates_total`) over at least one range with a mix of trading/non-trading days and one all-non-trading range; `validate_job_request` no longer raises on a >370-day span; the chunk-plan window count derives from `import_chunking.date_window_days` (verified via a small override or narrow fixture, NOT by executing a full multi-hundred-day run to completion — see NOTES).
- **Error cases:** an inverted range (`start > end`) is still rejected 400 (unchanged); an unknown `kind` is still rejected (unchanged); a request whose entire span is non-trading days (e.g. one weekend) must not crash and must report `dates_total=0`/`error_other=0` without fabricating a per-date failure.

Test-first contract:

- TC-1: given the committed seed (`snapshot_cadence.daily_start=2026-06-01`, no May-2026 dates yet snapshotted between 2026-05-02 and 2026-05-29), when an operator submits a `/data` backfill job for start=2026-05-02, end=2026-05-29, then the completed job summary reports `dates_total=19`, `snapshots_created=19`, `already_snapshotted=0`, `non_trading_days=9`, `error_other=0`, `calendar_days=28`.
- TC-2: given TC-1's run has completed, when the operator opens `/scanner-runs`, then runs exist for 2026-05-04, 2026-05-15, and 2026-05-29, and opening one renders a leaderboard from the stored snapshot for that as-of.
- TC-3: given the backend is running, when an operator submits a backfill for the weekend-only span start=2026-05-02, end=2026-05-03, then the job summary reports `dates_total=0`, `calendar_days=2`, `non_trading_days=2`, and the run renders in a visually distinct zero-work state, not the plain green success badge.
- TC-4: given TC-1 has completed, when the operator re-submits the identical start=2026-05-02, end=2026-05-29 range, then the job summary reports `snapshots_created=0`, `already_snapshotted=19`, `non_trading_days=9`, `dates_total=19`, `calendar_days=28`, rendered in the same distinct zero-work state as TC-3.
- TC-5: given TC-1, TC-3, and TC-4 have all completed in the same browser session, when the operator reloads `/data`, then the Run history table still lists all three runs with the same status/counts, and no panel on the page displays the literal text "No job has been started this session."
- TC-6: given a fresh page load where persisted run history exists but no job has started this browser session, when the Job progress panel renders, then it shows the most recent persisted run's status, summary, and breakdown instead of the empty "no job started" copy.
- TC-7: given the backend is running, when an operator submits a backfill spanning more than 370 calendar days (e.g. 2025-06-01 to 2026-07-17, 412 days), then the API returns a non-4xx acceptance (no "date range too large" rejection) and the created job's `chunk_total` is populated and greater than 1.
- TC-8: given TC-7's job is running, when the UI polls its progress, then `chunk_index` advances to at least 1 and `dates_done` advances above 0, with no cap-related entry in `job.errors`.
- TC-9: given `config.yaml`'s `data_manager` block after this iteration, when the backend boots and the backend unit suite runs, then `max_range_days` is absent from `DataManagerCfg` and from `config.yaml`, and `test_data_manager.py`, `test_api_data.py`, `test_config.py`, `test_themes.py`, `test_sectors.py`, and `test_indexes.py` assert the new no-cap contract instead of the old 370-day rejection.
- TC-10: given an existing `rebuild` job request, when it executes after this iteration's changes, then its target-date set is still governed by `_cadence_allowed_dates` exactly as before (unchanged density), even though its execution now proceeds through the same date-window chunks `_do_backfill` uses for `backfill`.
- TC-11: given a backfill request whose `[start,end]` span is entirely non-trading days (e.g. one weekend), when it completes, then `error_other=0` and no per-date failure is recorded for a day that was never a trading day.

## NOTES

- **Lesson applied** (iter-0 `lessons.md`, applies to any iter touching `data_manager.py` `_do_backfill`/`_cadence_allowed_dates`): the cadence gate — not a missing exclusion-reason schema — is J-01's real blocker; `snapshot_cadence.daily_start=2026-06-01` makes every May-2026 date compute `dates_total=0` today. This iteration lands "requested range always wins" first, per the lesson's own guidance, before either J-01 or J-05 can be meaningfully exercised.
- Two interpretive calls are logged to `runs/goal-session-ops-hardening/state/assumptions.md` (iter-1): (1) the cadence bypass is scoped to explicit `backfill`/`both` requests only, not `rebuild`, since no journey exercises `rebuild` and it takes no user-supplied range; (2) J-03 is read to require real date-window chunking of `_do_backfill` (not just the `max_range_days` cap removal), since goal.md's acceptance explicitly names "the chunk plan derives from the config `import_chunking` values."
- **Test-runtime guidance:** do NOT write a unit/integration test that executes a full 370+ day (or larger) backfill to completion against the full historical calendar — that risks a slow/hanging suite (a documented pitfall on this codebase's multi-decade basis). Verify the chunk-count arithmetic and first-window completion with a small `date_window_days` override or a narrow date-range fixture; reserve the true long-range run for the browser-QA journey (TC-7/TC-8), which only needs first-chunk progress + non-rejection, not full completion.
- `scripts/start-backend.sh`'s `ulimit -v`/`MALLOC_ARENA_MAX` claim in `reports/perf-budgets.md` is documented-but-not-implemented (iter-0 finding, confirmed by source read + `/proc/<pid>/environ`) — out of this iteration's scope (J-04 deferred) but flagged so a future iteration does not assume that doc reflects reality.
- Depth = full for two independent, sufficient reasons (either alone would trigger it): Trigger 2 (data model — the "Backfill run-summary contract" and "Job history & per-date exclusion reasons" blueprint Data-Contract rows both change their served JSON shape) and Trigger 1 (structural/cross-cutting — `_do_backfill`'s execution loop, `config.py`/`config.yaml`/`validate_job_request`, and 6 test files all change together). This also happens to be the session's first shipped user-visible UI change, matching goal.md's own "full when an iteration first lands user-visible UI changes" rule.
- Target selection followed the priority rubric's rule 3 (unblockers) exactly as the iter-0 evaluator recommended (Data-jobs cluster, J-01 + J-03, depth full) — no deviation. J-01 and J-03 are bundled deliberately (not as two unrelated risky changes): both are complementary fixes to the same function (`_do_backfill`) and are called out together by both goal.md's suggested build order and the iter-0 evaluator; their changes are kept separable (cadence-bypass + breakdown fields for J-01 vs. cap removal + chunking loop for J-03) and separately covered by TC-1..6 vs. TC-7..9, so a QA failure will point at a specific piece rather than an undiagnosable mixed bag.
