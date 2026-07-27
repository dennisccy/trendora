# goal-ops-hardening-iter-27 Dev Handoff

**Phase:** goal-ops-hardening-iter-27
**Date:** 2026-07-26
**Agent:** developer
**Status:** complete

## What Was Built

Hardening-only iteration closing the two ESCALATE-flagged anti-goal findings from iter-26. No new
journey, page, endpoint, or user-facing capability — J-05/J-07/J-08 become more robust and more honest
under conditions this session's own QA already proved occur live.

- **Fix 1 (AG-8, `apps/backend/app/engine/forward_testing.py`)** — `_insert_run_forward_returns`'s
  per-symbol loop now wraps `close_on`/`bars_after` + the insert body in a `try`/`except IntegrityError`.
  SQLAlchemy's default autoflush means one symbol's still-pending `session.add(...)` is actually flushed
  by the NEXT symbol's `close_on`/`bars_after` read; when a concurrent sibling call (e.g. two racing
  `/backtest` requests for the same never-scanned historical as-of) already committed that exact
  `(run_id, symbol, horizon)` key, the collision now fires as a caught, narrowly-matched `IntegrityError`
  instead of an unhandled 500. On a match: `session.rollback()`, undo the optimistic `existing`/`inserted`
  bookkeeping for **every row this call staged** (so the returned count stays truthful — never a
  fabricated insert count), and `continue` to the remaining symbols.
  - **Corrected by the iter-27 audit (finding B1):** as originally shipped this undid only the CURRENT
    symbol's bookkeeping. `session.rollback()` is transaction-wide and this function never commits, so
    earlier symbols' already-autoflushed rows were destroyed too while still being counted — a
    reproducible fabricated `rows_inserted` (returned 2, persisted 0). Fixed in the audit; regression
    test `test_iter27_audit_returned_count_is_truthful_when_collision_follows_earlier_flushed_symbols`. A new helper,
  `_is_forward_return_duplicate_key_collision`, matches ONLY on the DBAPI's own UNIQUE-constraint message
  for `forward_returns.run_id, forward_returns.symbol, forward_returns.horizon` (verified directly —
  SQLite reports the constrained column list, not the constraint name) — any OTHER `IntegrityError` still
  propagates unchanged (TC-4). `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`'s keying/single-flight semantics, and J-08's serving
  split are untouched — the freeze was lifted ONLY for `_insert_run_forward_returns`, on purpose, as
  scoped by the spec.
- **Fix 2 (AG-3, `apps/backend/app/engine/data_manager.py`)** — `coverage_from_storage` now stamps every
  returned payload with `coverage_status` (`"current"` / `"stale"` / `"not_yet_computed"`) plus
  `stale_dataset_version`/`stale_computed_at` (non-null only for `"stale"`), via a new small helper
  `_tag_coverage_status`. A NEW fallback branch, tried AFTER the existing exact-match lookup and the
  existing explicit-`as_of` self-heal (both unchanged), does one bounded, indexed lookup by `asof_key`
  alone (never a `daily_prices`/`scanner_runs` scan): if a `CoverageSnapshot` row exists for this exact
  `asof_key` under an OLDER `dataset_version` (the root cause: `_membership_dataset_version` is a GLOBAL
  stamp any new `ScannerRun` row bumps, including a request-path historical `/backtest` create-once view,
  and `_upsert_coverage_snapshot` only reclaims old-version rows at the END of an ingest — so the old row
  survives exactly when no ingest has run since the bump), serve that row's real figures labeled `"stale"`
  instead of falling through to the all-zero `"not yet computed"` sentinel. Confirmed the mechanics
  directly (not assumed) via a live reproduction — see "Live Verification" below.
- **API plumbing (`apps/backend/app/api/data.py`)** — confirmed, no code change needed: `data_overview`'s
  `"coverage"` key already embeds `coverage_from_storage(...)`'s full return dict verbatim, so the three
  new fields flow through `GET /api/data` automatically.
- **Frontend (`apps/frontend/app/data/page.tsx`, `CoveragePanel`)** — when
  `data.coverage.coverage_status === "stale"`, renders a new calm, muted notice directly below the panel
  title: "Coverage as of a prior scan (version {stale_dataset_version}) — refreshes on the next data job".
  The existing metric grid renders unchanged (it already reads `c.price_start`/`c.universe_count`/etc.
  verbatim — no client-side derivation needed for the stale case). The `not_yet_computed` empty-state
  rendering is untouched (byte-identical).
- **`reports/perf-budgets.md` timestamp correction** — the Iteration 26 section's `uptime` line read
  `2026-07-26T19:14:25Z` while the table header for the SAME reading window read
  `2026-07-26T18:14:25Z–18:14:42Z`, a one-hour mismatch. Re-derived the true UTC boot time from
  `logs/backend.log`'s own `date -u`-stamped `=== start-backend.sh: launching at ... ===` line
  (`2026-07-26T18:11:43Z`, immediately preceding a long health-poll-heavy block consistent with that
  iteration's TC-1 measurement method) — confirming the table header (`18:14:25Z`) was the correct label
  and the `uptime` line was the mislabeled one. Corrected the `uptime` line to `18:14:25Z`; no other content
  in that section changed (append/correct-only, per TC-10).

## Files Changed

- `apps/backend/app/engine/forward_testing.py` -- `_insert_run_forward_returns` tolerates a mid-loop
  autoflush collision (new `_is_forward_return_duplicate_key_collision` helper + narrow try/except); docstrings updated
- `apps/backend/app/engine/data_manager.py` -- `coverage_from_storage` gains the stale-fallback branch +
  new `_tag_coverage_status` helper; every returned payload now carries `coverage_status`/
  `stale_dataset_version`/`stale_computed_at`
- `apps/backend/tests/test_forward_testing_concurrency.py` -- two new tests: TC-3 (mid-loop collision
  tolerated, loop continues) and TC-4 (unrelated `IntegrityError` still propagates)
- `apps/backend/tests/test_data_manager.py` -- one new test (TC-5, the stale-fallback live-shaped
  scenario) + a shared `_strip_coverage_status`/`_strip...` helper + regression-guard assertions added to
  three EXISTING tests whose byte-equality checks needed to account for the new additive fields (TC-7/TC-8
  regression coverage; see "Existing Tests Touched" below)
- `apps/backend/tests/test_api_data.py` -- one existing test's equality assertion updated the same way
  (TC-8 regression guard)
- `apps/frontend/app/data/page.tsx` -- `CoveragePanel` renders the new stale notice (TC-6)
- `apps/frontend/lib/api.ts` -- `DataCoverage` interface gains `coverage_status`/`stale_dataset_version`/
  `stale_computed_at`
- `reports/perf-budgets.md` -- corrected the Iteration 26 section's mislabeled boot timestamp (TC-10)
- `runs/goal-ops-hardening-iter-27/coverage-stale-panel.png`, `coverage-stale-label-only.png` -- live
  browser evidence of the new stale label (see "Live Verification")

### Existing tests touched (regression guards, not new scenarios)

`coverage_from_storage` now additively stamps 3 new keys onto every returned payload, which broke 4
pre-existing byte-equality assertions against a raw `_compute_coverage_uncached`/similar result (neither of
which carries the new fields). Fixed by asserting the new `coverage_status` value explicitly, then
stripping the 3 additive keys before the byte-equality compare (via the new shared
`_strip_coverage_status` helper in `test_data_manager.py`, and an inline equivalent in `test_api_data.py`):
- `test_data_manager.py::test_fetch_that_lands_new_bar_refreshes_coverage_snapshot` (TC-8 regression guard: "current")
- `test_data_manager.py::test_finalize_hook_persists_per_date_coverage_for_historical_switcher_date` (TC-8: "current")
- `test_data_manager.py::test_coverage_from_storage_self_heals_explicit_legacy_historical_asof` (TC-8/TC-7:
  "current" for the self-heal branch, "not_yet_computed" for the genuinely-dataless-date branch)
- `test_api_data.py::test_get_data_overview_serves_coverage_from_storage_zero_prefill_calls` (TC-8: "current")

## Tests Run

The shared 30-year `loaded_engine` fixture is NOT required by any of the new/changed tests above (none
take it as a fixture parameter — verified by reading each file's fixtures before running). Ran three
targeted files directly instead of paying the 1h+ fixture-build cost:

```
cd apps/backend && .venv/bin/python -m pytest tests/test_forward_testing_concurrency.py -v
  15 passed in 24.08s   # includes the pre-existing iter-19 concurrent-race test (unaffected by the refactor)

cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -q
  137 passed in 258.42s (0:04:18)   # every test in the file, not just the touched ones

cd apps/backend && .venv/bin/python -m pytest tests/test_api_data.py -q
  48 passed in 6.04s   # every test in the file
```
200 passed, 0 failed, 0 skipped across all three files. No stray pytest process was left running
afterward (`ps aux` confirmed clean before finishing).

**Not run:** the full repo suite, and the 5 OTHER files that reference `_insert_run_forward_returns`/
`backfill_run_forward_returns` via the expensive `loaded_engine` fixture (`test_backtest_scorecard.py`,
`test_backtest_timing.py`, `test_forward_testing.py`, `test_forward_testing_serving_split.py`,
`test_data_manager_backfill_committed_session.py`). Confidence these are unaffected: the refactor is
byte-identical for the happy (no-collision) path — same operations, same order, same values; only a
`try`/`except` wrapper and bookkeeping variables were added around the existing body. Grepped these 5
files for any assertion sensitive to the change (e.g. `rows_inserted` counts) — all are happy-path
assertions unaffected by a change that only alters collision-handling.

Frontend: `npx tsc --noEmit -p tsconfig.json` (whole-project type-check) — zero errors, touched files
included.

## Live Verification

Started `scripts/start-backend.sh` (port 8255, host-guard confirmed in `logs/backend.log`) +
`scripts/start-frontend.sh` (port 3255), both warmed/ready with no errors.

**AG-8 fix, live concurrent-race reproduction (TC-1):** picked `2011-03-10`, a genuinely never-scanned
historical trading day (absent from `GET /api/runs`'s 1868 existing dates), and fired two REAL concurrent
`GET /api/backtest?as_of=2011-03-10` requests in parallel (`curl ... & curl ... & wait`).
- Both returned HTTP 200 (`logs/backend.log:81448`, `:81450`).
- `backtest_timing` log lines show `write_taken=True` for the first request and `write_taken=False` for
  the second (`~80.6-80.8s resolved_run_ms` each — a genuinely expensive cold historical create-once scan
  over the full 30-year basis, not a cached path).
- `grep -c "Exception in ASGI application" logs/backend.log` found 1 occurrence in THIS boot's window,
  at line 81004 — BEFORE this boot's own marker at line 81392 (`launching at 2026-07-26T19:56:13Z`).
  Zero occurrences during or after this test's own request window. That one occurrence is the iter-26
  evidence this fix closes, not a new failure.
  - **Corrected by the iter-27 audit:** the original wording claimed "exactly 1 occurrence in the whole
    81,450-line file". That is false — the file holds 12 further `Exception in ASGI application` entries
    from much earlier boots (lines 11888, 11988, 13057, 13202, 13283, 16123, 26150, 26931, 27355, 27497,
    27602, 27661). The per-window claim above still holds and was re-verified by the auditor; only the
    whole-file count was wrong. See the audit report's finding T1.
- Direct SQLite check after the race: exactly one `scanner_runs` row for `2011-03-10` (create-once held),
  zero duplicate `(run_id, symbol, horizon)` keys in `forward_returns` (1375 rows, all unique), confirming
  the concurrent collision was caught and resolved without a duplicate or a crash.

**AG-3 fix, live stale-coverage reproduction (TC-5/TC-6):** the concurrent-race request above itself
created a new `ScannerRun` row for a historical date, which — exactly as the root-cause analysis predicts —
bumped `_membership_dataset_version` without any ingest running. Immediately after, `GET /api/data`'s
default view served:
```
coverage_status: "stale"
stale_dataset_version: "r1868-rc1868-b2026-07-22-bc3301686-h200"
stale_computed_at: "2026-07-26T19:57:36.945385"
price_start/end: 1996-01-02 / 2026-07-22   (real, non-zero)
universe_count: 540                          (real, non-zero)
```
Never the old all-zero sentinel. Loaded `/data` in a real browser (Chrome via the browsing skill) and
confirmed the new label rendered exactly as specified:
"Coverage as of a prior scan (version r1868-rc1868-b2026-07-22-bc3301686-h200) — refreshes on the next
data job" — calm, muted text tone, no alarming treatment. Screenshots saved to
`runs/goal-ops-hardening-iter-27/coverage-stale-label-only.png` (cropped label) and
`coverage-stale-panel.png` (full page).

Both services stopped cleanly afterward; confirmed via `ps aux` (no `uvicorn`/`next dev`/`next-server`
process on ports 8255/3255 remaining) and via `curl` (both ports return connection-refused).

## Pre-Handoff Verification

- **Service startup:** both `scripts/start-backend.sh` and `scripts/start-frontend.sh` started cleanly,
  first `/api/health` 200 arrived within 1 poll (~0.5s) of process start, frontend `/data` compiled and
  returned 200 in ~2s. No port conflicts (used the SAME session throughout, no restart-cycle needed this
  iteration since no prior instance was running).
- **External integrations:** N/A — no new adapters/scrapers/external calls this iteration.
- **Native dependency binaries:** N/A — no new dependencies.

## Known Issues

- **Browser QA / smoke replay of the required-still-passing journeys (J-01, J-03, J-04, J-06, J-09; TC-9)
  and the FULL-PAGE (not viewport) evidence capture the spec's DoD calls for** were not run by this
  developer pass — left to the downstream browser-qa-agent, consistent with how this pipeline splits
  developer vs. QA responsibilities. I did perform a live, real (not staged/mocked) concurrent-request
  reproduction of both fixes myself (see "Live Verification" above) for extra confidence beyond the unit
  tests, including one real browser screenshot of the new stale label — but a full QA pass with the golden
  replay scripts and viewport-vs-full-page capture convention is still needed.
- **`.claude/project-template.md` is the generic unfilled template**, not this project's actual
  stack/commands (confirmed: `git ls-files .claude/project-template.md` returns nothing — it is untracked,
  landed only as a byproduct of the vendored `incredible_auto_dev/` subtree pull). Used `README.md`'s
  documented test command (`cd apps/backend && .venv/bin/python -m pytest tests/ -v`) and this session's
  own accumulated dispatch/coordinator notes instead. Pre-existing condition, out of this iteration's
  scope to fix (not a code file, not named in the spec) — flagging for the maintainer's awareness.
- Everything the spec places OUT OF SCOPE was left untouched: audit finding B2 (`Thread.start()` badge-
  stuck issue), backlog card B-1107, the cold historical `/backtest` load's owner budget decision, the
  `test_forward_testing_serving_split.py` monkeypatch retargeting / dangling imports at `backtest.py:75`
  and `mcp/tools.py:38`, `compute_forward_aggregates`/`resolved_forward_aggregate_evidence`/
  `ensure_historical_forward_aggregates_dispatched`'s keying/single-flight semantics, J-08's serving split,
  the OWNER BUDGET AMENDMENT/Revision 1/TC-13/TC-14 sections of `perf-budgets.md`, `resolved_run`'s
  concurrent-create-once behavior, and `reports/goal-session-ops-hardening-demo.json`.
- `runs/goal-session-ops-hardening/state/blueprint.md` was re-verified (not re-edited): the decomposer's
  additive iter-27 paragraph + Notes-column appends already state the exact field names
  (`coverage_status`, `stale_dataset_version`, `stale_computed_at`) that were actually built — verbatim
  match confirmed (TC-12), no drift found.
