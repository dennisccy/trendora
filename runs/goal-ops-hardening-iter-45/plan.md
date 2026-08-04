# goal-ops-hardening-iter-45 Execution Plan

## What to Build

- **The one risky change:** an incremental (append-forward) fast path for the membership-timeline
  finalize hook. Today `membership_timeline_cached` → `_membership_timeline` invalidates its ENTIRE
  cached payload on any `_membership_dataset_version` bump (i.e. on every ingest) and recomputes
  `_excluded_counts_by_date` — an O(dates × pool) `resolve_with_reasons` sweep over ~2,860 historical
  snapshot dates × the ~591-symbol pool — even when only ONE new date landed. This is the live-dump-
  confirmed (iter-44 SIGUSR1) root cause of BOTH: (a) J-05's single-day backfill never reaching a
  terminal outcome (three attempts, longest 1,001s, none finished), and (b) J-07's forward-aggregate
  warm never advancing `horizons_done` past 0 (the coverage/membership-timeline refresh runs BEFORE
  the warm loop in `_refresh_ingest_aggregates`'s finalize tail, so the warm never even starts).
  - Scope: when the new snapshot date(s) are all `>=` every already-cached historical date
    (append-forward), compute `resolve_with_reasons`/`_excluded_counts_by_date` ONLY for the new
    date(s) and reuse every previously-cached date's `size`/`entries`/`exits`/`excluded` point
    unchanged (byte-identical).
  - Fallback: when an ingest lands a date strictly EARLIER than an already-cached date (a historical
    gap-fill — can retroactively change order-dependent `entries`/`exits` for later dates), fall back
    to the EXISTING full recompute, unchanged. Do not attempt to generalize the fast path to this case
    (explicitly out of scope per the phase spec and `assumptions.md` iter-45's second entry).
  - This is a scoped, evidence-driven fix, not a speculative rewrite — the exact call chain was named
    by iter-44's live SIGUSR1 dumps (see `reports/perf-budgets.md` iteration-44 §2 and the "For the
    evaluator" section) and by two prior evaluator entries independently naming it "the fix the
    evidence actually points at."
- **Small, mechanical items riding along (per this session's established convention — never a second
  risky product-code change, rule 5):**
  1. Close the reviewer's THIRD `MemoryError` escape (iter-44 CRITICAL finding) inside
     `_refresh_ingest_aggregates`'s own error-LOGGING path — `logger.exception()` itself allocating
     under the tightened test cap in one of the per-item isolation handlers. Must be re-verified
     across **5 consecutive runs** of `test_ingest_finalize_memory_pressure.py`, not one (binding
     iter-44 lesson: a single green run under an exhausted cap mostly measures luck).
  2. Refresh `runs/goal-session-ops-hardening/journey-scripts/J-07.json`'s stale dataset-size anchors
     (currently `n=8878` on step 2's `/backtest` expectation, `3508` on step 3's `/data` expectation)
     to the CURRENT live dataset's actual, verified counts — verify live against the running backend,
     never guess/carry forward a number.
  3. Correct the stale comment near `data_manager.py:4730` (the phase spec flags it as predating the
     grown dataset; line numbers have shifted from prior edits — locate it by its stale dataset-size
     numbers, e.g. an outdated "~590 symbols" / "~2,860 dates" / row-count figure, not by that literal
     line number, and correct it against the live counts used for item 2 above).

## Agents Required

- backend-data: yes -- all of the above is backend Python (`app/engine/data_manager.py`) plus test
  files; no API contract or schema changes.
- frontend-ux: no -- phase spec states "None — this iteration is a backend algorithm/correctness fix
  with no UI-visible change in shape" and Frontend Present is `no` in the spec's own metadata.

## Frontend Present
no

This is a pure backend algorithm/reliability fix. No new component, page, route, or nav entry; the
global readiness badge and `/data`'s panels keep their existing shape (confirmed by the phase spec's
"UI surface changes: None" and "New information displayed: None"). The QA lane's required verification
is entirely browser-driven JOURNEY REPLAY (J-05/J-07 target + J-01/J-03/J-04/J-06/J-08/J-09 regression)
against already-existing UI surfaces, not a check for new UI — do not skip the browser-qa-agent step on
the strength of "Frontend Present: no"; this session's journey-script replay lane still requires it.

## Files to Create/Modify

- `apps/backend/app/engine/data_manager.py` -- the incremental fast path: modify
  `_membership_timeline` (~line 521) and/or `membership_timeline_cached` (~line 634) so an
  append-forward ingest computes `_excluded_counts_by_date`/`resolve_with_reasons` ONLY for the new
  date(s), reusing cached points for every date `<= D_prev` unchanged; preserve the existing full
  recompute as the historical-gap-fill fallback (triggered when any new date is `<` an already-cached
  date). Also close the third `MemoryError` escape inside `_refresh_ingest_aggregates`'s
  `logger.exception()` call (~line 3430 onward — the finalize-tail function; the escape is in one of
  its per-item isolation `except MemoryError` handlers' own error-logging, not the primary compute).
  Also correct the stale-numbers comment near line 4730 (locate by content, not line number).
- `apps/backend/tests/test_data_manager.py` -- new tests:
  - a call-count/mock test proving `resolve_with_reasons`/`_excluded_counts_by_date` is invoked ONLY
    for the new date(s) on an append-forward ingest, never for any `<= D_prev` date (TC-1);
  - a test asserting every `<= D_prev` date's `size`/`entries`/`exits`/`excluded` fields are
    byte-for-byte unchanged after an append-forward ingest, and the new stamp's payload has exactly
    one more point than the prior stamp's (TC-2);
  - a fixture-backed byte-identity test comparing (a) a pinned PRE-FIX full-recompute reference oracle,
    (b) this iteration's append-forward fast-path output, and (c) this iteration's historical-gap-fill
    fallback output, all for the same DB state/`snapshot_dates` — all three byte-identical (TC-3);
  - a regression test pinning that a historical gap-fill (new date `<` an already-cached date) still
    produces correct full-recompute-equivalent output via the fallback path, never a stale/incorrect
    reused value.
- `apps/backend/tests/test_ingest_finalize_memory_pressure.py` -- no new test required unless the
  logging-path fix needs a dedicated regression case for the specific escape site; at minimum this file
  must be RUN 5 consecutive times post-fix as verification (not necessarily edited). If the escape site
  needs its own targeted case (e.g. forcing `logger.exception()` to allocate under the tightened cap),
  add it here.
- `runs/goal-session-ops-hardening/journey-scripts/J-07.json` -- update the `n=8878` (step 2,
  `/backtest`) and `3508` (step 3, `/data`) anchors to the live dataset's current verified counts.
- `docs/handoffs/goal-ops-hardening-iter-45-dev.md` -- required dev handoff (DoD item).

No frontend files, no API route files, no schema/migration files are expected to change. If the
developer finds the fast path requires touching `membership_timeline_cached`'s cache-key/storage shape
beyond the described scope, that would be scope creep beyond this iteration's "implementation-only
change to the ALREADY-registered Data-Contract row" framing — flag it rather than silently expanding
the diff (same table, same tables, same serving paths, byte-identical output required per the phase
spec's "Data-contract additions: None").

## Out of Scope (flagged, do not build)

- The out-of-process watchdog/shutdown-deadline mechanism (explicitly deferred to its own iteration
  per `assumptions.md` iter-45 and the phase spec's OUT OF SCOPE section).
- A sixth `_BarCache.prefill`/`_SymbolColumns`/`bars_asof` bound attempt.
- Extending the incremental fast path to historical gap-fill inserts.
- iter-44/al's two unbounded evidence-path accumulators (`research.py:777`, `forward_testing.py:2343`).
- The `warmup.start_warmup` thread-launch-guard gap (`forward_testing.py:1691`).
- Any `docs/goal.md` edit or `memory_cap_mb`/host-guard cap change.
- Recording J-07's `[NEW]` walkthrough / J-05's real acceptance frames as this iteration's own goal
  (capture-only, rides along with whichever iteration lands the passing evidence — the browser-qa lane
  still runs the full replay per Key Test Scenarios below, but "produce a walkthrough" is not a
  dev-scope deliverable in itself).

None of the above should appear in the diff. This plan intentionally carries only ONE risky
product-code change (the membership-timeline fast path) alongside strictly mechanical items, per this
session's rule 5 ("never bundle two risky changes").

## UI Evolution
N/A — Frontend Present: no. No new user-facing capability, information, actions, or UI surface changes
this iteration (confirmed by the phase spec's own "New user-facing capability" / "New information
displayed" / "New user actions" / "UI surface changes" sections, all "None" or reliability-only).

## Visual Requirements
N/A — no frontend work this iteration.

## Key Test Scenarios

Mirrors the phase spec's TC-1 … TC-11 and DEFINITION OF DONE verbatim; do not narrow or reinterpret:

- TC-1: append-forward ingest of one new date does NOT re-invoke `resolve_with_reasons`/
  `_excluded_counts_by_date` for any date `<= D_prev` (call-count unit test).
- TC-2: every `<= D_prev` date's timeline point is byte-for-byte unchanged; the new stamp's payload has
  exactly one more point than the prior stamp's.
- TC-3: fixture-backed byte-identity — pre-fix full-recompute oracle == fast-path output == fallback
  output, same DB state.
- TC-4: a backfill of a day CONFIRMED absent from `/scanner-runs` beforehand (checked live, not
  assumed) reaches terminal `ok` within 300s, `/scanner-runs` lists it with a rendered leaderboard, and
  the run record's `aggregates_refreshed` includes `"membership_timeline"`.
- TC-5: the full-deep-basis forward-aggregate warm (ONE single ingest-finalize trigger, no manual
  mid-run probing) advances `background_compute.active[].horizons_done` past 0 within 120s of
  `started_at` — no repeat of the prior 137s stuck-at-0/5 stall.
- TC-6: during that same single-trigger warm, `GET /api/health` polled at 1Hz returns HTTP 200 within
  its rescoped ≤2s bounded-compute-window budget on EVERY poll — record a fresh dated
  `reports/perf-budgets.md` section; port never connection-refused, never fully unreachable.
- TC-7 (regression): the existing induced-pressure abort (J-07 step 4, tightened `memory_cap_mb` in a
  throwaway process via `start-backend.sh`) still aborts honestly while the SAME process's
  `/api/health` and cached reads keep serving 200 — no deadlock/wedge/restart.
- TC-8: `test_ingest_finalize_memory_pressure.py` passes **5 consecutive runs**, no `MemoryError`
  escape anywhere, including inside `logger.exception()` itself.
- TC-9: `journey-scripts/J-07.json`'s dataset-size anchors match the current live, verified dataset.
- TC-10: the stale comment near `data_manager.py:4730` is corrected against live counts.
- TC-11: full regression replay of J-01, J-03, J-04, J-06, J-08, J-09 all report PASS with unique,
  dated evidence — `md5sum` check confirms no two journeys share one screenshot file (closes/keeps
  closed iter-43/ai).

Browser-qa-agent must run BOTH the target-journey replay (J-05 via `journey-scripts/J-05.json`
re-triggered against a date freshly confirmed absent from `/scanner-runs`, not a stale default date;
J-07 via `journey-scripts/J-07.json`, all 4 steps) AND the full required-still-passing regression
(J-01, J-03, J-04, J-06, J-08, J-09) — this is a FULL-depth iteration (mandatory, per the prior
ESCALATE verdict) and the phase spec requires all eight journeys re-verified in one build.

## Environment Note (for all dispatched agents)

Before running tests or any command that writes temp files, run:
```
export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-a288af9f.18723" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-a288af9f.18723" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-a288af9f.18723"
```

**Do NOT run the full pytest suite** (~10-11h on this data basis; it fork-locks the box — this is a
test-suite-scale issue only, not a product slowness issue). Run only the targeted files named above
(`test_data_manager.py`, `test_ingest_finalize_memory_pressure.py`, and any other file whose symbols
this diff touches, e.g. `test_ingest_finalize_fault_injection.py` for the isolation-handler regression
class), plus the required live/browser drills. All heavy compute (backfills, warms, live drills) MUST
launch only via `scripts/start-backend.sh` / `scripts/dev.sh` per AG-10 — never bypass host-guard caps.

## Alignment Notes

- This plan advances `docs/goal.md` directly: it targets J-05 and J-07, the session's two currently-
  failing Must-have journeys, via the exact mechanism the goal's own "Improvement direction" section and
  `reports/perf-budgets.md`'s evaluator-facing notes name as the root cause.
- It builds on existing architecture (the already-registered "Membership timeline / research hot-key
  caches" Data-Contract row, `app.engine.data_manager`, `membership_timeline_cache` table) without
  duplicating or forking it — same producer, same tables, same serving paths, per the phase spec's
  "Data-contract additions: None."
- No drift from the phase spec detected — this plan mirrors its IN SCOPE / OUT OF SCOPE / DEFINITION OF
  DONE sections verbatim rather than reinterpreting them, per this session's own established
  spec-fidelity convention (multiple prior evaluator entries penalize plans/diffs that narrow or
  overclaim relative to the spec).
