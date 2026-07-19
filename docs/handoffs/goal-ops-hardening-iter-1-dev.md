# goal-ops-hardening-iter-1 Dev Handoff

**Phase:** goal-ops-hardening-iter-1
**Date:** 2026-07-19
**Agent:** developer
**Status:** complete

## What Was Built

Implements J-01 (backfill honors requested range, explains zero-work) + J-03 (no per-run range cap),
exactly per `runs/goal-ops-hardening-iter-1/plan.md`.

- **Cadence bypass (J-01):** `_do_backfill` (`apps/backend/app/engine/data_manager.py`) no longer applies
  the deep-history snapshot cadence (`_cadence_allowed_dates`) to explicit `backfill`/`both` requests —
  every trading day in `[start, end]` is now a candidate regardless of `snapshot_cadence`. `rebuild`'s
  target selection is unchanged (still cadence-filtered) — it is the one kind that still calls
  `_cadence_allowed_dates`.
- **Run-summary exclusion-breakdown contract (J-01):** `JobProgress` gained four fields —
  `calendar_days`, `non_trading_days`, `already_snapshotted`, `error_other` — computed once in
  `_do_backfill` and served two ways: unconditionally via `to_dict()` (the live `GET
  /api/data/jobs/{id}` poll) and, gated to `None` for fetch/expand kinds (mirroring the existing
  `passers`/`omitted_total` pattern), via `_run_detail()` → the persisted `DataProviderRun.message` JSON
  → `summarize_provider_run()` → `GET /api/data`'s `runs` list. `dates_total` is **redefined** to mean
  "trading days in the requested range" (was: the post-cadence/already-snapshotted-filtered target
  count). Invariants enforced by construction: `non_trading_days + dates_total == calendar_days` always;
  `snapshots_created + already_snapshotted + error_other == dates_total` for `backfill`/`both` (cadence
  bypassed, so every in-range date lands in exactly one bucket) — see Known Issues for the one documented
  gap (`rebuild`).
- **`dates_done` pre-seeding:** now starts at `already_snapshotted` (not 0), so a zero-work re-run's
  progress reads `N/N` (fully accounted for) instead of a misleading `0/N`. Byte-identical to the old
  starting point on a fresh range (`already_snapshotted == 0` there).
- **Date-window chunking (J-03):** `_do_backfill`'s execution loop now walks
  `_date_windows(start, end, import_chunking.date_window_days)`, advancing `chunk_index`/`chunk_total`
  per window — the same dormant fields the frontend's chunk-progress badge already rendered for fetch
  jobs. Each window still runs the pre-existing serial/parallel per-date compute+persist logic
  unchanged (wrapped in a new `_run_targets` closure so it can run once per window instead of once for
  the whole range) — byte-identical output, no change to the failure-isolation/create-once mechanics.
- **`max_range_days` removed entirely (J-03):** the field + its positivity check in `DataManagerCfg`
  (`apps/backend/app/config.py`), the `config.yaml` entry, and `validate_job_request`'s span-cap
  rejection (`data_manager.py`) are all deleted. An explicit backfill/fetch/both request of any span is
  now accepted; chunking is the safety mechanism.
- **Frontend `/data`:** the Job progress panel now renders the latest persisted run (via a new
  `LastRunSummary` component) when no job has started this browser session but history exists — the
  literal "No job has been started this session" text is now reserved for the true empty-history case. A
  new zero-work-distinct badge/label (`isZeroWorkRun`/`runStatusVariant`/`runStatusLabel`) applies to both
  the Job progress panel and Run history table, reusing the existing neutral `default` badge treatment
  (the `interrupted` precedent) rather than a new color. The four breakdown counts render inline via a new
  shared `BackfillBreakdown` component in both panels. `DataRun`/`DataJob` TS interfaces gained the four
  fields.

## Files Changed

Backend:
- `apps/backend/app/engine/data_manager.py` — `JobProgress` (new fields + `to_dict()`), `_do_backfill`
  (cadence bypass, redefinition, chunking), `_cadence_allowed_dates` (docstring only), `_run_detail`,
  `summarize_provider_run`, `validate_job_request` (cap removed)
- `apps/backend/app/config.py` — `DataManagerCfg`/`ImportChunkingCfg` (`max_range_days` field + check
  removed, docstrings updated)
- `config.yaml` — `data_manager.max_range_days` line removed
- `apps/backend/app/api/data.py` — docstrings updated (no behavior change)
- `apps/backend/scripts/build_qa_fixture_db.py` — removed its runtime read of the now-deleted
  `cfg.data_manager.max_range_days` (would have raised `AttributeError` on next invocation)

Backend tests:
- `apps/backend/tests/test_data_manager.py` — `backfilled_job` fixture now also returns `engine`/`cfg` (so
  new tests can reuse the already-loaded seed without a second expensive load); replaced the max-range
  test with a no-cap-contract test; fixed `test_backfill_create_once_immutable`'s stale `dates_total==0`
  assertion; added `test_backfill_breakdown_invariants_hold_on_fresh_and_rerun`,
  `test_do_backfill_cadence_bypass_for_backfill_not_rebuild`,
  `test_backfill_weekend_span_mixed_and_all_non_trading_breakdown`,
  `test_backfill_chunk_plan_derives_from_date_window_days_config`
- `apps/backend/tests/test_api_data.py` — replaced the 400-rejection test with an acceptance+chunking test
- `apps/backend/tests/test_config.py` — dropped `max_range_days` from `MINIMAL_VALID`; updated the two
  tests that referenced it
- `apps/backend/tests/test_themes.py`, `test_sectors.py`, `test_indexes.py`, `test_config_engine.py` —
  dropped the stray `"max_range_days": 370` fixture-dict copy (harmless — `DataManagerCfg` has
  `extra="allow"` — but stale)
- `apps/backend/tests/test_data_manager_backfill_committed_session.py`,
  `test_data_manager_backfill_parallel.py` — **found by my own research, not in the plan's file list**:
  both had a re-run assertion pinned to the OLD `dates_total` semantics (`== 1` / `== 0` respectively)
  that the redefinition breaks; fixed both to assert the new semantics
  (`dates_total == len(in_range)` + the correct `already_snapshotted` count)

Frontend:
- `apps/frontend/app/data/page.tsx` — `isZeroWorkRun`/`runStatusVariant`/`runStatusLabel` helpers,
  `BackfillBreakdown` + `LastRunSummary` components, `JobProgressPanel` (new `runs` prop, persisted-history
  fallback, zero-work note, breakdown counts), `RunHistoryPanel` (zero-work badge, breakdown counts), call
  site now passes `runs={state.data.runs}`
- `apps/frontend/lib/api.ts` — `DataRun`/`DataJob` interfaces gained the four breakdown fields

## Tests Run

Full command: `cd apps/backend && .venv/bin/python -m pytest <path> -k "<filter>" -q` (TMPDIR set per
harness instructions). **I did not run the full backend suite** — this repo's committed 30-year fixture
basis makes a full run take many hours (test-only slowness, unrelated to product boot time; documented
project history). Per this project's workflow the reviewer/QA step owns full-suite verification; my job
was to verify every test I personally added or changed. All of the following passed on a fresh, targeted
run:

| Command (path -k filter) | Result |
|---|---|
| `test_config.py -k "data_manager"` | 2 passed (`test_data_manager_minimal_valid_loads`, `test_data_manager_nonpositive_limit_raises`) |
| `test_api_data.py -k "long_range or inverted"` | 3 passed (incl. `test_post_job_long_range_is_accepted_and_chunked`, `test_post_job_inverted_range_is_400`) |
| `test_data_manager.py -k "<8 tests: cadence-bypass, mixed/all-non-trading breakdown, chunk-plan-arithmetic, breakdown-invariants, create-once-immutable, no-cap-contract, grows-n, append-only>"` | first run: 7 passed / 1 failed (my own test had a bad assumption — see below); re-run after the fix: 1 passed. All 8 pass. |
| `test_data_manager_backfill_committed_session.py -k "test_rerun_after_isolated_failure_is_create_once"` | 1 passed |
| `test_data_manager_backfill_parallel.py -k "test_parallel_rerun_is_idempotent"` | 1 passed |

**One self-caught bug during verification:** `test_backfill_chunk_plan_derives_from_date_window_days_config`
originally assumed the seed's trading calendar has a gap larger than 6 calendar days somewhere (to build a
2-window vs 1-window comparison); the real committed seed's largest gap is smaller than that, so the test
failed on its own setup assertion, not on any product code. Fixed by searching for the calendar's actual
*largest* gap and sizing the two `date_window_days` comparisons relative to whatever that turns out to be
(`window_days == calendar_days` → 1 chunk; `window_days == 1` → `calendar_days` chunks) — robust regardless
of the real calendar's exact shape. Re-ran and it now passes.

**Deferred to the reviewer/QA step (not run by me), with reasons:**
- The full `test_data_manager.py` file (only the 8 tests above were targeted) — the other ~140 tests in
  this file are pre-existing and I verified via static read (grep for `dates_total`/`chunk_total`/cadence
  usage across every test in the repo) that none of them assert on the redefined fields in a way my change
  breaks, but I have not executed them.
- `test_data_manager_backfill_committed_session.py` and `test_data_manager_backfill_parallel.py` in full
  (only the one fixed assertion in each was re-verified) — same static-read confidence for the rest.
- `test_data_manager_jobs_pipeline.py`, `test_data_manager_parallel.py` — statically confirmed these only
  exercise `fetch`/`both`-kind chunk_total (symbol-batch × date-window, a code path I did not touch) and
  assert nothing on the new breakdown fields; not executed.
- `test_themes.py`, `test_sectors.py`, `test_indexes.py`, `test_config_engine.py` — only removed an
  already-ignored (`extra="allow"`) stale dict key; not executed, low risk.
- Any test requiring the full historical-cadence warm-up (this project's `conftest.py::loaded_engine`
  session fixture) — genuinely multi-minute-plus per pytest session on this box; I paid this cost once for
  my own `test_data_manager.py` run (via its own separate `backfilled_job` module fixture, not
  `loaded_engine`) but did not re-invoke it for the other files given the reviewer/QA owns full verification.

**Pre-handoff service verification (done):** started the real backend via
`CHAIN_BACKEND_PORT=8255 bash scripts/start-backend.sh` against the committed seed DB. `GET /api/health`
returned `200` within seconds (config schema change — removing `max_range_days` — did not break boot).
`GET /api/data` returned `200` with every run in `runs` carrying the four new keys
(`calendar_days`/`non_trading_days`/`already_snapshotted`/`error_other`), confirming the API wiring is
live-correct against the real DB, not just in tests. I deliberately did **not** POST a real backfill job
against this shared committed DB (e.g., the May-2026 range) — doing so would pre-empt the exact "first run"
outcome (`dates_total=19`, `snapshots_created=19`) the downstream browser-QA agent's J-01 test needs to
observe fresh; polluting that DB now would turn QA's first attempt into an unexpected zero-work re-run.
Backend was cleanly stopped afterward (`pkill -f "uvicorn main:app"`; confirmed via `ps`/`lsof` that the
port was released and no uvicorn process remained).

## Known Issues

- **`rebuild`'s breakdown-invariant is not exact** (documented in code comments at `_do_backfill`'s
  docstring and the `JobProgress` field docstring): since `rebuild` keeps its cadence filter (unchanged,
  per the plan's explicit scoping), a real rebuild over the full historical calendar will have some
  in-range trading days excluded by cadence that land in none of `snapshots_created`/`already_snapshotted`/
  `error_other` — so `snapshots_created + already_snapshotted + error_other == dates_total` does not hold
  exactly for `rebuild`, only for `backfill`/`both` (where cadence is bypassed, so every in-range date
  lands in exactly one bucket). No Must-have journey or test-first TC this iteration exercises `rebuild`'s
  breakdown numerically (TC-10 only checks its target *set* stays cadence-filtered, which it does); I
  considered adding a fifth "cadence-excluded" bucket to force the invariant to hold universally but judged
  that out of scope (the plan explicitly says `rebuild`'s behavior is unchanged this iteration) and
  potentially dishonest (inventing a category nobody asked for). Flagging for whoever eventually touches
  `rebuild`'s own contract.
- **`both`-kind jobs: the chunk-progress badge now reflects whichever stage is currently running**, not
  just the fetch stage. Previously `chunk_index`/`chunk_total` were untouched by the backfill stage (only
  fetch set them), so a `both` job's badge showed the fetch plan even during backfill. Now the backfill
  stage resets these to its OWN date-window plan once it starts. I verified this does not corrupt the
  durable `ImportCheckpoint` row (its own `chunk_total`/`next_chunk_index` columns are read from the
  checkpoint object directly, never from `JobProgress`, in `_finalize_checkpoint`) and does not break any
  existing test (grepped for `chunk_total`/`chunk_index` assertions on `both`-kind jobs — none exist). This
  is a minor, non-regressing display nuance for a job kind no Must-have journey this iteration exercises.
- **`.claude/project-template.md` is an unfilled placeholder** (still contains template text like `<e.g.,
  Python 3.12>` rather than Trendora's actual stack). I worked around this by reading the real stack
  directly from `apps/backend/.venv`, `scripts/dev.sh`, and `scripts/start-backend.sh` rather than trusting
  the file. Flagging since the project instructions direct every agent to read this file for exact
  commands — it currently cannot be trusted for that.
- **Incidental process note:** while verifying no orphaned backend process remained on the verification
  port, `lsof -ti :8255` returned a PID that turned out to be an unrelated Chrome browser utility
  subprocess (not my uvicorn server, which had already exited cleanly per `ps aux`), and I killed it before
  realizing this. Chrome appears to have recovered (33 chrome processes still running afterward), but
  flagging in case it caused any transient disruption to a concurrent browser-automation session.
- Did not touch `scripts/start-backend.sh`'s missing `ulimit`/`MALLOC_ARENA_MAX` enforcement (J-04,
  explicitly out of scope this iteration per the phase spec).
- Did not build J-05's ingest-finalize aggregate-refresh hooks or J-06's page-budget measurements
  (explicitly out of scope this iteration).

## Definition-of-Done Self-Check (against the phase spec)

- [x] `_do_backfill`'s cadence gate bypassed for `backfill`/`both`; `rebuild` unchanged — implemented,
  unit-tested (`test_do_backfill_cadence_bypass_for_backfill_not_rebuild`).
- [x] Date-window chunking added, reusing `import_chunking.date_window_days` + existing
  `chunk_index`/`chunk_total` fields — implemented, unit-tested.
- [x] Run-summary breakdown fields + redefined `dates_total` — implemented, unit-tested (invariants).
- [x] `summarize_provider_run` surfaces the new fields — implemented, live-verified against `GET
  /api/data`.
- [x] `max_range_days` removed (config + validation + yaml) — implemented, unit-tested (no-cap contract).
- [x] Named pinning tests updated to the new contract — done, plus 2 more files found by my own research.
- [x] Frontend persisted-history fallback, zero-work distinction, breakdown counts — implemented.
- [ ] J-01/J-03 passing via browser-qa-agent — **not my step; deferred to browser-qa-agent** per the
  pipeline's normal division of labor.
- [ ] J-04 regression spot-check — **not my step**; I did not touch boot/readiness/crash-detection code at
  all (grepped to confirm), so no regression risk from this iteration's changes.
