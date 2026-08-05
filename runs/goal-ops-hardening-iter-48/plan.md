# goal-ops-hardening-iter-48 Execution Plan

## Context read
`docs/goal.md` (ops-hardening session, Must-have journeys J-01…J-09), the full phase spec at
`docs/phases/goal-ops-hardening-iter-48.md` (exhaustively detailed by the goal-decomposer — TC-1…TC-9 are
the authoritative, machine-checkable acceptance contract; this plan paraphrases, it does not supersede),
the iter-47 dev handoff (original pass + audit-fix pass) and iter-47 audit (PASS_WITH_GAPS, findings
B1-B5/P1-P5), `state/assumptions.md`'s iter-48 decomposer entry (why J-05's finalize-tail fix is bundled
with the trivial `samples.py:161`/`:168` bound while the Regime Lab fix and the rest of item (5) are
deferred), and `state/iteration-state.md` (current standing: 2 passing / 5 partial / 1 failing, J-05
failing 4 consecutive rounds, no lane has verified ANY journey against the iter-47-shipped build). Working
tree is clean under `apps/`/`apps/backend`/`apps/frontend` — no carried-over uncommitted product code from
a prior interrupted session to reconcile.

No drift: this iteration is a direct continuation of the iter-47 evaluator's own numbered next-step order
— item (1) (re-run all eight journeys) and item (3) (J-05's finalize-tail fix), plus the first bullet of
item (5) (`samples.py:161`/`:168`) bundled as a trivial, same-pattern addition. Item (4) (Regime Lab,
14th deferral) and the rest of item (5) are explicitly out of scope this round per rule 5 (never bundle
two risky/undiagnosed changes). Squarely inside the session's "compute at ingest, serve from storage"
hardening arc — no new capability, no scope creep.

## What to Build

1. **Diagnose and fix J-05's historical-gap-insert finalize-tail non-termination** (the session's sole
   `failing` Must-have journey, 4 consecutive rounds). Root-cause path already traced by the iter-47 dev
   handoff and confirmed by the code itself:
   - A backfill of a date EARLIER than `membership_timeline_cache`'s latest cached date cannot take the
     iter-45 append-forward fast path (`membership_timeline_cached`, `data_manager.py:788-871` —
     `append_forward` requires `min(new_dates) > prev_dates[-1]`; a historical gap fails that check by
     construction and falls through to the full, UNCHANGED `_membership_timeline(session, cfg,
     snapshot_dates)` recompute at `:871`).
   - `_membership_timeline` (`:522-582`) calls `_excluded_counts_by_date(session, cfg, dates,
     pool_symbols)` (`:585-632`) for **every** historical snapshot date (~2,860+ on the live basis), not
     just the new one. When `_do_backfill`'s shared whole-table `_BarCache` is attached (the normal case —
     `_refresh_ingest_aggregates` attaches it via `attach_shared_cache` before this call chain runs), the
     `active_bar_cache(session) is not None` branch (`:611-616`) runs `universe_resolver.resolve_with_reasons`
     **once per date, unbatched**, over the full candidate pool — an O(dates × pool) sweep with no
     per-date bound and no heartbeat inside the loop itself. The iter-47 dev handoff measured this
     concretely: the snapshot itself writes in ~12 s, then `status` stays `running` and
     `aggregates_refreshed` stays `[]` for 11+ minutes with no observed convergence before the dev
     restarted the backend.
   - Add phase-level timing/heartbeat instrumentation across `_refresh_ingest_aggregates`'s finalize-tail
     steps (per spec IN SCOPE bullet 1) to CONFIRM this is the dominant cost before committing to a fix —
     do not assume the trace above is complete; the coverage-snapshot warm, per-date coverage warm,
     market-phase warm, forward-aggregates warm, and drawdown-expectations warm are separate loops in the
     same function and any of them could also contribute for this specific historical-gap case. `prog.tick()`
     already exists as the per-step heartbeat primitive (see its use throughout `_refresh_ingest_aggregates`)
     — extend it with a named phase marker if the diagnosis needs to attribute wall-clock time to a specific
     sub-step in the logs.
   - Fix the identified blocking step(s) so the job reaches a terminal `status` within a bounded, measured
     time (TC-1: within 20 minutes of the snapshot write, on an idle host) — WITHOUT extending the iter-45
     append-forward fast path to this case (a deliberate, documented design decision protecting
     order-dependent entries/exits correctness, `assumptions.md` iter-45) unless the investigation itself
     proves a new, safe, tested alternative, in which case log it as a new `assumptions.md` entry with the
     correctness proof. A likely-safe direction (not prescribed, for the developer to validate): bound
     `_excluded_counts_by_date`'s active-outer-cache branch the same way its own no-outer-cache branch is
     already batched (`:618-632`), and/or add a heartbeat tick inside the per-date loop so a genuinely slow
     but progressing job does not read as stalled — but the actual fix must follow from what the
     instrumentation shows, not from this plan's guess.
   - Preserve byte-identical `entries`/`exits`/`excluded` output for the new date AND every already-cached
     date (TC-2) — this is a correctness-adjacent, order-dependent subsystem; do not change what is
     computed, only how fast/safely it completes.
   - Keep the existing `test_historical_gap_fill_falls_back_to_full_recompute_not_stale_reuse`
     (`apps/backend/tests/test_data_manager.py:5644`) green with its assertions UNMODIFIED — it is the
     correctness pin this fix must not disturb.

2. **Bound `_factor_samples`'s `total` and `regime` branches** (`apps/backend/app/engine/samples.py:161`
   and `:168`), which currently call `_factor_observations` (`research.py:226-326`) and use/return its
   full unfiltered population, using the SAME two-pass bounded pattern already shipped for the `decile`
   branch (`research._factor_decile_observations` + `_BoundedRankWindow`, iter-47, 5/5 pressure runs).
   Note for the developer: unlike `decile`, both `total` (the whole pool by definition) and `regime` (a
   filtered subset, but not by rank) cannot discard the majority of observations the way the decile window
   does — investigate what "bounded" means correctly for these two branches (e.g., avoiding a redundant
   second full materialization, keeping the existing per-chunk streaming discipline `_factor_observations`
   already applies, or a regime-side chunk-and-filter accumulator that never holds the full unfiltered pool
   at once) rather than mechanically reusing `_BoundedRankWindow`, which is decile-rank-specific. Whatever
   shape the fix takes, member rows must remain byte-identical to the pre-fix `_factor_observations`-based
   population for the same inputs (TC-5), and this iteration's diff must not introduce any new `MemoryError`
   anywhere (DEFINITION OF DONE).

3. **Full 8-journey re-verification** (J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09) against the CURRENT
   shipped build, run LAST — after both fixes above land, not before, and re-run again if any later
   fix/audit-fix pass changes product code (TC-7, the THIRD consecutive iteration this exact requirement
   has been written down — iter-46 and iter-47 both had it recur). Use the golden replay lane where a
   script exists and is content-verified (TC-8: read the JSON, not just the PASS/FAIL row — a script
   asserting page-wide persisted-history text is a null test per the binding iter-46 lesson); LLM/
   browser-qa fallback for J-04 and J-07 (retired to `runs/goal-session-ops-hardening/retired-journey-
   scripts/` at iter-47 — no golden on file, by design) and for anything the replay lane cannot express
   (a 20 s hard step-timeout cap, `demo_runner.py:1475`).
   - **J-05's golden needs the TC-9 fix before this run**: the iter-47 audit's P2 finding is that
     `journey-scripts/J-05.json` decays into a null test after its first productive run (`{dates_done}/
     {dates_total} dates` and `stage-timings` render for a zero-work re-run too). Apply the audit's
     prescribed one-line fix — assert the live job card's own snapshot count (`{job.snapshots_created}
     snapshots · … forward returns inserted`, `apps/frontend/app/data/page.tsx:2785`) so the script only
     passes on a genuinely productive run (TC-9) — AND rotate the target date off `2011-01-05` if that date
     was already ingested during this iteration's own TC-1 drill (the window `2005-05-24 … 2019-02-25`
     holds ~2,495 other gap days). Do not let the golden regress into the exact null-test shape the iter-47
     audit already named twice.
   - Use `http://localhost:3255` as the replay base URL, never `127.0.0.1` (CORS mismatch produces
     meaningless "Backend unavailable" failures — iter-47 dev handoff, confirmed the hard way).
   - Do not start a second data job while one is still finishing — the historical-gap-insert drill (TC-1)
     and any other journey's own ingest step must run sequentially, never concurrently (iter-47 evaluator's
     own operational note, repeated in this spec's TESTING REQUIREMENTS).
   - Watch memory around J-06 — its `/research/regime-lab` step drove the iter-47 process to within 84 kB
     of the 8192 MB cap and stalled the boot re-warm for ~20 minutes (iter-47 dev handoff finding, not
     caused by this iteration's diff, but it can poison every journey run after it in the same lane pass if
     it runs first and the process is left near the ceiling).

## Out of scope (per phase spec — do not implement)
- The Regime Lab's separate, undiagnosed 8192MB-cap hit (`research.py:3552`, iter-33/g, 14th deferral).
- The shared ingest-vs-request-vs-boot-warm "drawdown-expectations warm in flight" sentinel (audit B2,
  iter-47) — a real, disclosed gap, but a distinct cross-module design change, deliberately deferred.
- J-09's background-worker visibility gap for the new re-warm thread (iter-47/B3) — J-09 is currently
  `passing`; not touched this round.
- `GET /api/health`'s measured ≤2 s ceiling breach during an ingest finalize tail (8/20 polls over budget,
  iter-47 dev handoff B5) — re-measure only as part of J-04/J-07 required-still-passing verification; no
  fix attempted.
- Any change to `server.memory_cap_mb` / `malloc_arena_max` / host-guard cap VALUES (AG-10) — never
  re-tune, per the 2026-07-31 owner amendment.
- Every other item already carried in prior OUT OF SCOPE sections (QueuePool exhaustion, the sixth
  `_BarCache.prefill` bound attempt, iter-29/b through iter-46/ba, etc.) — untouched.

## Agents Required
- backend-data: yes -- implements the J-05 finalize-tail diagnosis + fix (data_manager.py), the
  `samples.py:161`/`:168` bound (samples.py / research.py), their tests (including the new live/integration
  termination test mirroring `test_start_backend_script.py`'s `test_start_backend_survives_back_to_back_
  heavy_ingest_under_memory_cap` heavy-ingest pattern, and the 5-consecutive-run memory-pressure drill for
  the new `total`/`regime` bound), and runs the full 8-journey live re-verification described above.
- frontend-ux: no -- the phase spec's own metadata states `Frontend Present: no`; no new field, page, or
  copy change is anticipated. The ONE allowed exception (an explicit "still finishing" job-card state, only
  if the diagnosis proves the finalize tail genuinely needs longer than any reasonable ceiling) is a minimal,
  additive fallback the developer may reach for if — and only if — the investigation forces it; if taken,
  log it as a new `assumptions.md` entry rather than silently expanding scope, and flag it to the reviewer.

Frontend Present: no

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` -- `_refresh_ingest_aggregates` (:3692-4033, its finalize-tail
  steps), `_membership_timeline` (:522-582), `_excluded_counts_by_date` (:585-632), and
  `membership_timeline_cached`'s full-recompute fallback (:860-871) — instrumentation, then the identified
  fix. Do not touch `_membership_timeline_incremental` (:704-785) or the `append_forward` gating logic
  itself (:844-857) — the append-forward fast path stays scoped exactly as iter-45 designed it.
- `apps/backend/app/engine/samples.py` -- `_factor_samples`'s `total` branch (:161) and `regime` branch
  (:168-169).
- `apps/backend/app/engine/research.py` -- `_factor_observations` (:226-326) and/or a new bounded helper
  alongside `_factor_decile_observations`/`_BoundedRankWindow` (:329-524+), depending on what the
  investigation in item 2 above settles on.
- `apps/backend/tests/test_data_manager.py` -- extend
  `test_historical_gap_fill_falls_back_to_full_recompute_not_stale_reuse` (:5644) with the new
  liveness/termination proof (TC-1, TC-2) without modifying its existing assertions; add the error-case test
  (a non-memory exception during the finalize tail leaves the run `failed` with a real reason; a
  `MemoryError` is caught per the existing per-item isolation convention).
- `apps/backend/tests/test_start_backend_script.py` (or a new dedicated test file) -- new live/integration
  test proving a historical-gap-insert job reaches a terminal status within the measured bound, mirroring
  `test_start_backend_survives_back_to_back_heavy_ingest_under_memory_cap`'s spawned-backend pattern (TC-1).
- `apps/backend/tests/test_research_streaming.py` and/or `apps/backend/tests/test_samples.py` -- pinned-
  reference byte-identity test for the `total`/`regime` bound (mirrors the existing decile-branch reference
  test).
- `apps/backend/tests/test_samples_memory_pressure.py` -- extend the existing pattern to the two new
  branches; the 5-consecutive-run protocol (TC-6) must show 5/5, not one green run (binding iter-44 lesson).
- `reports/perf-budgets.md` -- new dated item(s): TC-1's finalize-tail timing (before/after the fix), TC-5's
  VmPeak margin for the `total`/`regime` bound, TC-9's health-poll re-measurement during the finalize tail.
- `runs/goal-session-ops-hardening/journey-scripts/J-05.json` -- apply the audit's TC-9 self-invalidating-
  test fix (assert `snapshots_created`, not just page-wide dates/timing text); rotate its target date if
  `2011-01-05` gets consumed by this iteration's own TC-1 drill.
- `runs/goal-session-ops-hardening/state/assumptions.md` -- new entry ONLY if the finalize-tail
  investigation proves a safe alternative to the append-forward exclusion, or if the frontend exception
  ("still finishing" state) is taken.
- `docs/handoffs/goal-ops-hardening-iter-48-dev.md` -- required dev handoff (diagnosis findings, which
  step(s) actually dominated wall-clock time, the fix applied, live TC-1/TC-6 drill results, honest
  reporting of any TC not met).

## Key Test Scenarios
- TC-1: a backfill ingesting exactly one historical date earlier than `membership_timeline_cache`'s latest
  cached date (2011-01-05, or a rotated equivalent per J-05's own golden) reaches a terminal
  `data_provider_runs.status` (`ok`/`partial`/`failed` with an honest reason) within 20 minutes of the
  snapshot write, on an idle, live backend process — never `running` indefinitely.
- TC-2: `_membership_timeline`'s output for the ingested date AND every previously-cached date stays
  byte-identical to a pinned pre-fix reference (no `entries`/`exits`/`excluded` value changes anywhere).
- TC-3: after TC-1 completes, `/scanner-runs` for that date renders the stored snapshot (not a "not yet
  computed" placeholder).
- TC-4: `GET /api/health` polled at 1 Hz throughout the whole finalize tail answers HTTP 200 within its
  existing budget every time — no frozen or unresponsive window.
- TC-5: `_factor_samples`'s `total`/`regime` cohort reads return byte-identical member rows to the pre-fix
  `_factor_observations` population for the same inputs, with VmPeak staying under the 8192 MB cap and the
  margin recorded in `reports/perf-budgets.md`.
- TC-6: the extended `total`/`regime` memory-pressure drill passes 5/5 consecutive runs, zero flake (binding
  iter-44 lesson).
- TC-7: the full 8-journey browser-qa/replay pass is the LAST product-code-adjacent event before scoring —
  verify via results-file mtime vs newest product-code mtime; any later code change forces a re-run.
- TC-8: each Required-still-passing journey's golden replay script content (not just its PASS/FAIL row) is
  read and confirmed to assert against that run's own new row/testid, never page-wide persisted-history text
  (binding iter-46/iter-47 lesson).
- TC-9: the J-05 golden FAILS when run against a zero-work (already-snapshotted) job — i.e. it asserts
  positive evidence of new work, never text a pre-existing history row could already satisfy.
- Anti-goal checks: AG-3 byte-identity preserved on both changed read paths; AG-8 no new unbounded
  whole-table load introduced (including inside whichever `samples.py` fix is chosen, and inside whatever
  the finalize-tail fix does); AG-10 caps unchanged (8192 MB / `malloc_arena_max=2`, host-guard values
  untouched, launch scripts still enforce them); AG-9 offline-deterministic ingest preserved (no new live
  network path).
- Regression: J-01, J-03, J-04, J-06, J-08, J-09 (required-still-passing) replay/verify clean against the
  current build — this is the FIRST dedicated lane verification any of them has had against the shipped
  code in two rounds (iter-46's and iter-47's lanes both predated later fix passes); do not assume their
  prior `passing`/`partial` status still holds without fresh evidence.

## Risk Flags / Notes for Reviewer + QA
- **J-05 is a correctness-adjacent, order-dependent subsystem fix** (entries/exits depend on full timeline
  order — the exact class of bug iter-27/iter-9 and iter-45 already had to correct once). The reviewer
  should verify the fix does not silently generalize the append-forward fast path to the gap-fill case
  (explicitly forbidden unless proven safe and logged in `assumptions.md`) and that TC-2's byte-identity
  proof covers BOTH the new date and every already-cached date, not just the new one.
- **`samples.py`'s `total`/`regime` bound is NOT a mechanical copy-paste of the decile pattern** — flag any
  implementation that tries to force `_BoundedRankWindow` (rank-based, decile-specific) onto branches that
  must return their full/filtered population; verify the actual bound applied is sound for what these two
  branches structurally require.
- **TC-7 sequencing is the THIRD consecutive iteration this has been written down** (iter-46, iter-47,
  iter-48) — QA/audit must treat a lane run that predates a later fix-pass code change as void, full stop,
  regardless of how green its rows read.
- **J-05's golden is one-shot per target date** (iter-47 audit P2) — confirm the TC-9 assertion fix is
  applied AND verified (not just planned) before the lane run that scores this iteration, and confirm the
  target date is genuinely unsnapshotted going into that run.
- Environment: before running tests, `export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-e9cad6c2.18723" TMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-e9cad6c2.18723" TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-e9cad6c2.18723"`.
  Never run the full pytest suite (~10-11h on this 30-year basis — fork-locks the box); use targeted `-k`
  selections per file. Never `killall`/`pkill` broad patterns — target specific PIDs only. Launch services
  ONLY via `scripts/start-backend.sh` / `scripts/start-frontend.sh` (AG-10) — never `dev.sh` for
  measurement-conditions journeys (J-04).
