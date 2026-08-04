# goal-ops-hardening-iter-45 Dev Handoff

**Phase:** goal-ops-hardening-iter-45
**Date:** 2026-08-04
**Agent:** developer
**Status:** complete (code + tests), with one important honest caveat on live-scale outcome — see "Known Issues"

## What Was Built

- **The append-forward fast path for the membership-timeline finalize hook** —
  `app.engine.data_manager._membership_timeline_incremental` (new) + `membership_timeline_cached`'s MISS
  branch (modified): when an ingest lands snapshot date(s) that are all `>=` every date already present in
  the most recently cached membership-timeline payload, `resolve_with_reasons`/`_excluded_counts_by_date`
  is now invoked ONLY for the new date(s) — every already-cached date's `size`/`entries`/`exits`/`excluded`
  point is reused byte-for-byte, never recomputed. This bounds the O(dates × pool) resolver sweep that was
  running over ALL ~2,860 historical dates on every single-date ingest (iter-44's live SIGUSR1 dump named
  this exact call chain as the shared root cause of J-05's never-completing single-day backfill and J-07's
  forward-aggregate warm never advancing past `horizons_done: 0`).
  - **Fallback preserved exactly**: a historical gap-fill (a new date strictly earlier than an
    already-cached date), a previously-cached date now missing from the current date set, or the
    first-ever compute (no prior cache row) all fall through to the EXISTING, byte-for-byte UNCHANGED
    `_membership_timeline` full recompute — `entries`/`exits` are order-dependent on the full prior
    timeline, so an earlier insertion can retroactively change a later cached date's values
    (binding iter-27/iter-9 lesson); this iteration deliberately does not generalize the fast path to that
    case (per `assumptions.md` iter-45's second entry).
- **Closed the reviewer's third `MemoryError` escape** — added `_log_isolation_failure()`, a drop-in
  `logger.exception()` replacement used at EVERY per-item isolation handler inside
  `_refresh_ingest_aggregates` (12 call sites). `logger.exception()` itself allocates (rendering the full
  traceback) and can raise a second exception under the same exhausted `ulimit -v` cap that produced the
  exception being logged — that second exception is raised inside the caller's `except` clause, past the
  point that clause's own `try` protects, so it escaped the function entirely (the iter-44 review's
  live-reproduced flake: 1 failed/1 passed across two consecutive runs). The new helper tries the full
  traceback first (unchanged behavior for every normal failure), falls back to a minimal-allocation
  traceback-free record on any logging failure, and gives up silently if even that raises — logging must
  never be the reason the "log + continue, never raise" contract breaks. Applied to all 12 sites in the
  function (not just the one site the flaky repro happened to land on), since TC-8 requires no escape
  "anywhere," and the failure mode is allocator-timing-dependent (could land in any of them).
- **Refreshed `journey-scripts/J-07.json`'s stale dataset-size anchors** — `n=8878` → `n=8991`
  (Return Attribution, Bucket A, `/backtest`) and `3508` → `2533` (Backfill gaps, `/data`), both verified
  live against the running app (not guessed) and cross-checked against historical QA records
  (`reports/phase-goal-ops-hardening-iter-37-ui-test-results.llm.md` independently confirms both fields'
  identity: "Bucket A `+10.70% n=8878`" and "Backfill gaps 3508").
- **Corrected the stale comment in `_fail_unlaunched_job`** (`data_manager.py`, was near line 4730 in the
  pre-iteration tree — shifted by this diff's insertions). The comment claimed `_run_job`'s `finally` sets
  `prog.message = _final_summary(prog)` "on every in-flight failure" — this is now BACKWARDS: since
  iter-44's own B1 fix, that `finally` block explicitly SKIPS the assignment exactly when
  `prog.status == "failed"`. Corrected the comment to describe the current (correct) behavior; no code
  changed at this site, only the stale prose (matches the iter-44 review's carried NOTE finding, not a
  dataset-size figure as its own one-line description implied — see "Known Issues" for how this was
  triangulated).

## Files Changed

- `apps/backend/app/engine/data_manager.py` — `_membership_timeline_incremental` (new function),
  `membership_timeline_cached` (MISS branch now tries the fast path first), `_log_isolation_failure` (new
  helper) + 12 call-site substitutions inside `_refresh_ingest_aggregates`, and the corrected comment in
  `_fail_unlaunched_job`. `_membership_timeline` itself is byte-for-byte UNCHANGED (it is both the
  fallback path and the reference oracle used in the new byte-identity tests).
- `apps/backend/tests/test_data_manager.py` — four new tests: `test_append_forward_ingest_does_not_reinvoke_resolver_for_cached_dates`
  (TC-1, call-count via a `resolve_with_reasons` spy), `test_append_forward_reuses_cached_points_byte_for_byte`
  (TC-2), `test_append_forward_fast_path_byte_identical_to_full_recompute` (TC-3, against
  `_membership_timeline` as the pre-fix oracle — unmodified by this diff), and
  `test_historical_gap_fill_falls_back_to_full_recompute_not_stale_reuse` (gap-fill regression, pins that
  an earlier-inserted date correctly forces D1's entries/exits to recompute, never a stale reuse).
- `runs/goal-session-ops-hardening/journey-scripts/J-07.json` — the two anchor refreshes described above.

## Tests Run

Per-run isolation with `TMPDIR` set to the dispatch's isolated temp dir; `/tmp/pytest-of-*` cleared before
each invocation; no full-suite run (per this session's standing ~10-11h full-suite caution).

```
cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -k "append_forward or historical_gap_fill" -v
  → 4 passed in 1.30s

cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager_membership_cache.py -v
  → 10 passed in 1.90s  (the dedicated iter-36 membership-cache regression suite; includes
    test_cache_invalidates_on_dataset_change, which itself exercises the NEW append-forward branch on a
    real snapshot-add and independently asserts byte-identity against `_membership_timeline` — every one
    of its 10 tests passed unmodified)

cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -k "finalize_hook" -v
  → 30 passed in 266.17s  (every existing `_refresh_ingest_aggregates` finalize-hook test, including all
    of the MemoryError-isolation-handler tests now routed through `_log_isolation_failure`)

cd apps/backend && .venv/bin/python -m pytest tests/test_ingest_finalize_fault_injection.py -v
  → 5 passed in 0.68s

cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -k "test_coverage_from_storage_serves_stale_prior_snapshot_when_default_view_stamp_advances_outside_ingest or test_expand_that_lands_new_bar_refreshes_coverage_snapshot or test_fetch_that_lands_new_bar_refreshes_coverage_snapshot" -v
  → 3 passed in 0.88s
```

**TC-8 (5 consecutive clean runs of the memory-pressure file, binding iter-44 lesson — a single green run
mostly measures luck):**

```
cd apps/backend && .venv/bin/python -m pytest tests/test_ingest_finalize_memory_pressure.py -v
  run 1: 2 passed in 156.12s
  run 2: 2 passed in 154.49s
  run 3: 2 passed in 151.34s
  run 4: 2 passed in 148.89s
  run 5: 2 passed in 147.94s
```
All 5 runs (10 individual test executions) passed cleanly — no `MemoryError` escape anywhere, including
inside the logging path itself. TC-8 closed.

**Total: 62 unique test executions across 6 files/selections, all passing, zero failures, zero
regressions.**

## Live Verification (real backend, real committed DB — not mocked)

Backend/frontend started only via `scripts/start-backend.sh` / `scripts/start-frontend.sh` (AG-10). Both
anchor refreshes in `J-07.json` were verified via an actual Chrome-driven page load against the live app,
not read from the API JSON in isolation, then re-confirmed via a FRESH backend+frontend restart at the end
of this session (see "Known Issues" — the live drills below mutated the DB, so the anchors were checked
against the post-mutation served state, which is what QA will also see).

**Live single-day backfill drill (the exact TC-4/J-05 mechanism, at real ~2,862-date DB scale — not the
small hand-built unit-test fixtures above):** confirmed `2019-02-26` absent from `/api/runs` (a real
"Backfill gap," `GET /api/data` showed 2533 of them before this drill), then `POST /api/data/jobs`
`{"kind":"backfill","start":"2019-02-26","end":"2019-02-26"}`. Result and its implication are the single
most important item in "Known Issues" below — read it before treating this iteration as closing J-05.

## Known Issues

**CRITICAL — J-05's live/browser-qa replay will very likely still exceed its 300s budget against the
CURRENT committed database, through no defect in this diff; this is a direct, foreseeable consequence of
this iteration's own (deliberate, upstream-approved) scope decision, and the reviewer/auditor/evaluator
chain needs to weigh it explicitly:**

The append-forward fast path only accelerates an ingest whose new date(s) are `>=` every already-cached
date. I checked the live committed DB directly: `daily_prices`/`scanner_runs` for the SPY benchmark show
**zero backfill gaps after 2019-02-26** — every trading day from 2019-02-27 through the data horizon
(2026-07-31, which is ALSO the latest already-snapshotted date) already has a snapshot. The seed's own
`SPY.csv` tops out at 2026-07-01; the DB's later dates (through 2026-07-31) came from a real live fetch in
an earlier session, so there is no hidden seed data beyond the current snapshot horizon either. **This
means every "unsnapshotted historical trading day" available to backfill today is chronologically EARLIER
than the current latest cached date — i.e. every live-testable target is a historical gap-fill, which this
iteration's fast path explicitly (and, per `assumptions.md` iter-45's second entry, deliberately) does
NOT accelerate.**

I proved this live, not by inference: I backfilled the one real gap closest to the boundary
(`2019-02-26`), polling `GET /api/data/jobs/{id}` and `GET /api/health` throughout. The job was **still
`"status": "running"` at t=1106s** (I stopped observing there for this dev pass's own time budget, not
because it reached a terminal state) — past both TC-4's 300s budget and iter-44's own previously-measured
~1,001s reference point for the same class of stall. This is the code's EXISTING, UNCHANGED full-recompute
fallback running exactly as before this iteration — not a new regression, and not something this diff was
asked to fix (the plan's own "Out of Scope" section explicitly excludes "extending the incremental fast
path to historical gap-fill inserts"). But it does mean **J-05's own defining acceptance case (TC-4) is
very unlikely to pass in the browser-qa replay as currently formulated**, because there is no
append-forward target available to test against in this live DB, and AG-9 forbids fetching live/newer data
to manufacture one.

**One genuine positive from the same drill**: `GET /api/health` returned HTTP 200 on every single poll
across the full ~1,106s observation window — no freeze, no connection-refused, nothing resembling
iter-44's 20+-minute full outage. Whatever the coverage/membership-timeline storm does under this
iteration's tree, it does not appear to wedge request-serving the way the OLD incident did. This is
favorable evidence for J-07's "health stays responsive" class of acceptance criteria, independent of
whether J-07's own specific trigger mechanism turns out append-forward-friendly (I did not get a clean,
uncontaminated read on that: a second live drill I ran afterward, intended to isolate "does a genuinely
zero-new-date backfill hit the membership-timeline cache and let the forward-aggregate warm start
quickly," was itself contaminated by the FIRST drill's in-flight, never-completed cache write — the
dataset's version stamp had already moved past what was cached, forcing another full-recompute miss
regardless of the second job's own target date. A clean read of that scenario needs either a fresh DB with
no pending gap-fill in flight, or patience through one full ~1,000s+ catch-up recompute first; neither fit
this dev pass's remaining time budget.)

**Side effect of this dev pass's own live verification (disclosed, not hidden):** the committed DB
(`apps/backend/data/trendora.db`, not tracked by git) now has a real, immutable snapshot for `2019-02-26`
that did not exist before this pass (2863 scanner runs, was 2862). This is the SAME kind of side effect
every prior iteration's live dev/QA verification has left on this shared DB (see the `/data` page's own
"Run history" — it already carries runs from many earlier iterations' drills). The `J-07.json` anchors
above were verified AFTER this mutation, against a freshly restarted backend+frontend, and match what is
actually served today (both the coverage and evidence_by_horizon aggregates are themselves still serving
their PRE-mutation cached values, since the drill's finalize hook never completed to refresh them — this
is itself a live, unplanned illustration of exactly the staleness class J-05 exists to close). A second,
interrupted backfill job (`2026-07-31` → `2026-07-31`) was also left in an honest in-flight state when I
stopped the backend for cleanup; the existing boot-time orphan-sweep (`sweep_orphaned_runs`, unmodified by
this diff) will mark both interrupted rows `interrupted` on the next real restart, per this session's
already-established restart-resilience contract (exercised in iter-43).

**Recommendation for the next pipeline stage(s):** the code change itself is correct, scoped exactly to
the phase spec, and thoroughly proven at the unit level (TC-1/2/3, byte-identical to the pre-fix oracle,
zero regressions across 62 test executions). Whether to treat TC-4/J-05 as "correctly implemented but
untestable-as-currently-live" versus "not achieved" is a judgment call for review/audit/evaluator, not
something I resolved unilaterally — I did not expand scope to also accelerate the gap-fill path (that
would be a second risky change, explicitly against this session's rule 5 and the plan's own "Out of
Scope"). If a fast, clean live pass at TC-4 is needed, the only path within AG-9 I can see is: let the
`2019-02-26` job (or a similar gap-fill) run to natural completion once (a one-time ~1,000s+ catch-up cost
that brings the cache current), after which any FURTHER single-day backfill of a genuinely new date is
structurally impossible against this seed's fixed data horizon — so TC-4 as worded may need a scope
amendment (e.g. re-anchor it to a synthetic/smaller-fixture drill, or accept the gap-fill case as this
session's next scoped-fix target) rather than a code fix in this diff.

No other known limitations. No frontend work this iteration (Frontend Present: no, confirmed unchanged).

---

# Fix Notes — audit FAIL pass (2026-08-04)

**Input:** `docs/handoffs/goal-ops-hardening-iter-45-audit.md` (verdict **FAIL**).
**Scope:** ONLY the audit's own unfixed findings. B3, B4, B5 and T1 were already fixed *by the auditor*
during the audit pass and are untouched here (their six regression tests still pass — re-run below).

## What this pass fixed

### B6 — a fatal data job left NO log evidence (both halves)

The audit's decisive live observation: run 281 (`2019-02-25`) reached terminal `failed` with the persisted
reason `"MemoryError (no message)"` and wrote **nothing** to `logs/backend.log`
(`grep -n "no message"` → no match; `grep -c "backfill per-date compute aborted"` → **0**), so this
session's single most important live failure could not be root-caused — the audit could not even
distinguish which of two candidate origins raised it. Two changes, exactly the two the audit named:

1. **`_run_job`'s outer handler now logs** (`data_manager.py`, in the `except Exception as exc` block that
   sets `prog.status = "failed"`). It previously recorded the reason onto `prog` only and made no logging
   call at all. `prog` carries a one-line reason but never a traceback, and `_JOBS` is process-local — gone
   on the next restart, which is exactly what a wedge forces. The new record names the job id, the kind,
   and the same honest reason the job persisted. Placed AFTER `_record_error`/`prog.message = reason` (so
   the operator-visible state is durable even if logging is slow or fails) and BEFORE the checkpoint
   bookkeeping (which opens its own session and can fault under the same pressure).
2. **`data_manager.py:3451` — the last remaining bare `logger.exception` in an isolation handler**
   (`_do_backfill`'s per-date worker `except MemoryError`) now routes through `_log_isolation_failure`.
   This is the fifth of the five sites the audit's T4 listed; the auditor fixed four (`:3602`, `:3610`,
   `:4658`, `:4679`) and left this one as out-of-scope-for-an-audit. `_compute_one_isolated`'s own
   docstring promises it "never raises", and the per-date isolation contract rests on that.

Both call sites use `_log_isolation_failure`, never a bare `logger.exception` — in both, the logging call
sits in the OUTERMOST frame that still contains the failure, so a second `MemoryError` from the traceback
render would escape past the isolation the handler exists to provide.

**Self-caught regression while writing (1): the new fatal-failure log line was a KEY LEAK.** Only
`reason` is scrubbed (`reason = scrub(str(exc))`); `logger.exception` ALSO attaches the live exception, and
its formatted traceback carries the exception's **raw** text — which on a fetch/expand job embeds the
resolved provider key in a URL. That is the exact surface
`test_real_httpx_error_key_scrubbed_end_to_end` pins with "absent from the logs", and `_make_scrubber`'s
own docstring calls this "defense-in-depth on top of the `_http.py` URL redaction". Fixed before shipping:
`_log_isolation_failure` gained an `exc_info: bool = True` keyword (default preserves all 16 pre-existing
call sites byte-for-byte), and the fatal handler renders the traceback itself, runs it through the job's
own `scrub`, and passes it as an ordinary argument with `exc_info=False`. Covered by
`test_fatal_job_failure_log_never_leaks_the_provider_key`; the negative control below shows the raw key in
the log without the fix.

**Self-caught regression while writing (2): rendering the traceback inline would have re-opened B6's own
escape.** `traceback.format_exc()` allocates; evaluating it in `_log_isolation_failure`'s argument list
puts that allocation OUTSIDE the guard, so a `MemoryError` there would propagate out of `_run_job` — the
precise failure this whole pass exists to close. It is therefore rendered in its own `try` that degrades to
`"(traceback unavailable — rendering it failed)"`, so the job id / kind / reason line survives even when
the traceback cannot be produced.

### T2 — the `J-07.json` `n=8991` anchor was wrong (the audit's UNVERIFIED one)

Verified live against the canonical `GET /api/backtest` payload on the running backend
(`http://localhost:8255`, HTTP 200, 271,362 bytes):

- The string `8991` does **not appear anywhere** in the payload (nor does the pre-iteration `8878`), so
  step 2's strict text match could never have held.
- Reproduced the page's own horizon selection rather than guessing: `/backtest` picks
  `scorecard.by_horizon.find(row => row.attribution.distribution.n > 0)` and falls back to the LAST
  horizon. All five scorecard horizons currently have `distribution.n == 0` (the as-of-scoped scorecard has
  no observed window at as-of `2026-07-31`), so the page renders **horizon 60**, whose
  `evidence_by_horizon["60"].by_bucket` Bucket A is **`n=14647`** (`mean_return` 0.0817). `SampleSize`
  renders `n={n}` with no thousands separator (`components/forward-return.tsx:35`), so the on-page text is
  literally `n=14647`.
- **Anchor changed `n=8991` → `n=14647`.** Step 3's `2532` (the auditor's T2 fix) was independently
  re-confirmed live in the same pass: `GET /api/data` → `coverage.gap_count = 2532`, `gap_last =
  "2019-02-25"`, `snapshot_count = 2863`; the string `2533` no longer appears in the payload.

Honest caveat, stated because it has now bitten twice: this anchor pins a **derived aggregate that every
ingest changes** (8878 → [8991, never true] → 14647). It is correct as of this pass, and it must stay a
numeric anchor (AG-3 requires the displayed *numbers* to be checked, not merely that the page rendered) —
but any iteration that lands new snapshots will stale it again. Additionally, the payload is currently
served with `evidence_status: "refreshing"` (`evidence_asof 2026-07-30` vs `asof_date 2026-07-31`), i.e.
it is the labeled last-good version while a newer one warms; when that refresh lands, this number moves.

### F1 — the duplicate-screenshot defect, fixed at the source (TC-11)

Root cause found, and it is **not** the iter-43 defect TC-11 was written for. `demo_runner.py --mode
verify` captures ONE end-state screenshot per journey; **J-03 and J-04 both end their last step on
`/data`**, so two genuinely independent captures of the same page in the same state were byte-identical
(both `9d77429b8499e40ef04b2de00c1e8fdb`, both 172,246 bytes). No file was re-used or mislabelled — but a
pure md5 check cannot tell that honest case apart from the dishonest one it targets, and no amount of
re-capturing fixes it while two journeys share an end state.

Fix (`scripts/automation/lib/demo_runner.py`, one file — `scripts/` is a symlink into
`incredible_auto_dev/scripts/`, so there is a single copy and no resync step): each verify capture is
stamped with its own provenance as PNG `tEXt` chunks (`Journey`, `Phase`, `Created`, `Source`) inserted
after IHDR. `tEXt` is a standard **ancillary** chunk — decoders ignore it, so **not one pixel changes**;
the file merely says which journey it belongs to when read directly. Deliberately NOT an on-page banner
overlay: that would alter the very evidence being recorded. `png_with_provenance` returns its input
unchanged for anything that is not a PNG with a leading IHDR, and the call site wraps it in its own
`try` — evidence stamping must never be able to fail a passing replay.

**This does not make TC-11 pass for this iteration.** The two duplicate files already in
`reports/qa/goal-ops-hardening-iter-45-evidence/` were captured before the mechanism existed and are left
exactly as they are — re-stamping them retroactively would produce unique hashes that falsely imply the
capture lane was sound during this run. TC-11 stays **UNMET** here; it is closed by construction for the
next replay.

## Tests

Per-run isolation with the dispatch's `TMPDIR`; `/tmp/pytest-of-*` cleared before every invocation; no
full-suite run.

Every result below is from the FINAL tree (the whole set was re-run after the two self-caught regressions
above were fixed — no result here predates the shipped code).

```
# the four NEW B6 tests + the auditor's six + this iteration's four + the three pre-existing
# key-scrub invariant tests (one file, one pass)
.venv/bin/python -m pytest tests/test_data_manager.py -k "fatal_job_failure or per_date_memory_abort or \
  log_isolation_failure or aggregate_refresh_logging or bars_land or append_forward or \
  historical_gap_fill or per_date_coverage_warm_logging or key_scrubbed or key_never_persisted" \
  -q -p no:randomly
  → 17 passed in 10.93s

.venv/bin/python -m pytest tests/test_data_manager_membership_cache.py \
  tests/test_ingest_finalize_fault_injection.py -q -p no:randomly
  → 15 passed in 2.25s

.venv/bin/python -m pytest tests/test_data_manager.py -k "finalize_hook" -q -p no:randomly
  → 30 passed, 137 deselected in 206.40s

# TC-8, re-run in full because this pass touched `_run_job`'s failure path (binding iter-44 lesson:
# one green run under an exhausted cap mostly measures luck)
.venv/bin/python -m pytest tests/test_ingest_finalize_memory_pressure.py -q -p no:randomly   ×5
  run 1: 2 passed in 142.73s      run 2: 2 passed in 142.97s      run 3: 2 passed in 141.81s
  run 4: 2 passed in 151.51s      run 5: 2 passed in 140.99s
  → 5/5 consecutive clean runs (10 individual executions), no MemoryError escape. TC-8 holds.

python3 scripts/automation/lib/demo_runner.py self-test
  → 28 passed, 0 failed  (26 pre-existing + the 2 new PNG-provenance checks)
```

**Total: 90 test executions across 5 files/selections + the runner self-test, all passing, zero failures,
zero regressions.** No full-suite run (this session's standing ~10-11h full-suite caution).

**New tests (every induction uses a TEXTLESS `MemoryError()` — this product's characteristic exception,
whose `str()` is the empty string; the session's standing honesty rule):**

| Test | Proves |
|---|---|
| `test_fatal_job_failure_is_logged_with_job_id_kind_and_reason` | the outer handler emits exactly ONE record naming the job id, the kind, `"MemoryError (no message)"`, **and the traceback frames** (B6's actual purpose: name the frame) |
| `test_fatal_job_failure_logging_never_escapes_the_outer_handler` | with the first, fuller emit raising a textless `MemoryError`, the job still reaches terminal `failed` with `finished_at` set, and the minimal retry still names it |
| `test_fatal_job_failure_log_never_leaks_the_provider_key` | SECURITY — a wholesale fetch-stage failure carrying the resolved key in a URL reaches the outer handler; the key is absent from the log, the `***` marker proves the scrub fired, and `data_manager.py` frames prove the traceback survived the scrub |
| `test_backfill_per_date_memory_abort_survives_a_raising_logging_call` | the per-date abort is still recorded as an isolated failure (`aborted for memory pressure at 2024-01-03`), the breakdown invariant `snapshots_created + already_snapshotted + error_other == dates_total` still holds, and the abort line the audit found missing is emitted |
| `_t_png_provenance_makes_identical_captures_distinct` (demo_runner self-test) | two identical captures become distinct files, each naming its OWN journey, every chunk CRC valid, and every non-`tEXt` chunk byte-identical to the original (no pixel altered) |
| `_t_png_provenance_leaves_a_non_png_untouched` (demo_runner self-test) | empty / non-PNG / truncated input returns unchanged, never raises |

**Negative controls — every fix was reverted and its test re-run, so none passes vacuously:**

- **B6 outer handler removed entirely** (pre-fix behaviour) →
  `test_fatal_job_failure_is_logged_with_job_id_kind_and_reason` FAILED and
  `test_fatal_job_failure_logging_never_escapes_the_outer_handler` FAILED (`got [] out of []`).
- **B6 outer handler using a bare `logger.exception`** → `..._never_escapes_the_outer_handler` FAILED with
  `MemoryError` propagating **out of `run_data_job` itself** (`app/engine/data_manager.py:4836 in _run_job`)
  — the escape this guard exists to stop, reproduced exactly.
- **`:3451` reverted to a bare `logger.exception`** →
  `test_backfill_per_date_memory_abort_survives_a_raising_logging_call` FAILED with `MemoryError` raised at
  `app/engine/data_manager.py:3462 in _compute_one_isolated` — i.e. escaping the function that promises
  never to raise.
- **`exc_info=False` removed** (traceback left to `logger.exception`'s automatic render) →
  `test_fatal_job_failure_log_never_leaks_the_provider_key` FAILED, with the log showing the scrubbed
  `token=***` line immediately followed by the auto-attached raw one:
  `...prices?token=sk-FATAL-HANDLER-LEAK-9c4a2d`. The leak is real and the guard is what stops it.
- **F1, controlled live rather than by unit fixture:** two throwaway golden scripts with byte-identical
  steps (`goto /`, expect `Ready`) were replayed through the real Playwright verify path against the live
  frontend (`:3255`). Post-fix the two PNGs differ (`00f8459b…` / `0fc454ca…`) and each carries its own
  `Journey`. Stripping the `tEXt` chunks back off makes both image-byte streams hash **identically**
  (`6b668b744a6bc8e27c66028f893068db`) — proving the drill really did reproduce the J-03/J-04 collision and
  that the stamp, not rendering noise, is what separates them.

## What this pass did NOT fix — and why (unchanged FAIL findings)

- **B1 (CRITICAL) — the phase goal is not achieved; the service went fully unreachable for ~42 minutes.**
  Unchanged and still failing. The audit's mechanism (AnyIO worker-thread *creation* itself failing, so
  the event loop accepts connections no handler can ever be dispatched to) is not addressable by anything
  in this iteration's scope: the two remedies it points at — the out-of-process watchdog and the two
  unbounded evidence-path accumulators (`research.py:777`, `forward_testing.py:2343`) — are both listed
  verbatim in this phase spec's OUT OF SCOPE section. **TC-4, TC-5, TC-6 remain FAILED; TC-7 remains
  never-executed.** B6's fix makes the *next* such failure diagnosable; it does not prevent it.
- **B2 (CRITICAL) — the append-forward fast path still has zero live evidence.** Independently
  re-confirmed live this pass, and it is structural rather than an oversight: `GET /api/data` reports
  `gap_last = "2019-02-25"` against a latest snapshot of `2026-07-31`, so **every** backfill target
  available in this database is chronologically earlier than every cached date — a historical gap-fill,
  which the fast path deliberately does not accelerate. There is no append-forward target to drill, and
  AG-9 forbids fetching newer data to manufacture one. Unchanged from the original handoff's disclosure;
  no code change can close it.
- **F1's existing evidence files** — see above; deliberately left as captured.
- **B3, B4, B5, T1** — already fixed by the auditor; verified still green here, not re-touched.
- **T3 / T4** — observations about the QA verdict's wording and the review's grep claim. Both are
  statements about other agents' reports, not code; T4's substance (the five remaining bare
  `logger.exception` sites) is now fully closed by the auditor's four fixes plus this pass's fifth.

## Known Issues (new, found while fixing — NOT fixed, recorded for triage)

- **Two bare `logger.exception` calls remain in `data_manager.py`** at `_fail_unlaunched_job` (`:5031`)
  and `_fail_unlaunched_resume` (`:5064`), both in `except` blocks guarding `_finalize_run_record`. They
  were **not** on the audit's T4 list and are not in any per-item isolation loop, so they are deliberately
  left alone under fix-mode scope discipline. They are the same *class* as B3/B5/B6 (a logging allocation
  inside a failure handler that runs under pressure), and the honest reading is that they are the last two
  unguarded sites in this module. Recommend a one-line follow-up card rather than a silent fix here.
- **The `J-07.json` numeric anchors are structurally fragile** — see the T2 caveat above. Worth a card to
  re-point them at a value that does not move with every ingest (a *stable* displayed number that still
  satisfies AG-3), rather than re-verifying two moving aggregates every iteration.
