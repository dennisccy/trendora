# Iteration 58 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The work this round was asked to do was done, and I checked it myself in the code, in the database
and in the raw logs. The Data page no longer says "updating" when no data job is running, the false
"no data yet" message can no longer appear on a saved reading, and the wrong health record from last
round was corrected in all three places without deleting the original text. The scoreboard did not
move: six of the eight journeys still pass and the same two — J-05 "Aggregates are precomputed at
ingest" and J-07 "Heavy aggregates never take the service down" — are still part-done. I found two
things no lane reported: the test report for J-07 says every health check answered in at most 1.18
seconds while its own log holds two answers over the 2-second limit, and the test report for J-05
calls a real 3.5-second answer a "gap in the recording". This round ran shallow even though its own
plan asked for deep, so the review step that catches exactly this did not happen.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `reports/qa/goal-ops-hardening-iter-58-evidence/J-01-verify.png` (replay PASS); ingest rows 377-382 all `provider='seed'` re-read by me in sqlite |
| J-03 No per-run range cap | passing | passing | `reports/qa/goal-ops-hardening-iter-58-evidence/J-03-verify.png` — opened by me: "backfill job · 2025-06-01 → 2026-07-17" (412 calendar days) accepted, no cap rejection |
| J-04 Non-blocking boot with visible status | passing | passing | `reports/qa/goal-ops-hardening-iter-58-evidence/J-04-verify.png` (replay PASS); zero HTTP-500s in `logs/backend.log` after 19:00 local — last round's wedge did not recur |
| J-05 Aggregates are precomputed at ingest, never on the fly | partial | partial | `reports/qa/goal-ops-hardening-iter-58-evidence/UT-J-05-result.png` + `data_provider_runs.id=382` / `scanner_runs.id=2949` read by me; step 3 NOT executed; `j05-health-poll.log:114` = 3.474644 s inside the warm window |
| J-06 Pages load only what they need | passing | passing | `reports/qa/goal-ops-hardening-iter-58-evidence/J-06-verify.png` — opened by me: honest "Still computing — 16s elapsed" state, which this journey allows |
| J-07 Heavy aggregates never take the service down | partial | partial | `reports/qa/goal-ops-hardening-iter-58-evidence/J-07-warm-inflight.png` + `j07-health-poll.log` read by me: 0 non-200, but 2.097 s / 2.064 s polls and VmPeak 8,388,608 kB == the 8192 MB cap |
| J-08 Backtest evidence serves from storage only | passing | passing | `reports/qa/goal-ops-hardening-iter-58-evidence/J-08-verify.png` (replay PASS) |
| J-09 The backend discloses its own background-compute activity | passing | passing | `reports/qa/goal-ops-hardening-iter-58-evidence/J-09-verify.png` — opened by me: SNAPSHOT DATES 2948 / SYMBOLS 591 / TRADING DAYS 5391 match my own sqlite counts at capture time |

No journey changed status. No `DEFERRED-BUDGET` rows, no `browser-infra.json`, no `journeys-changed.md`.
All 8 `spec_hash` values match `goal_gate.py hash-journeys` run by me — no goal-text drift.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials (AG-7) | OK | `iter-58/scan-report.md` CLEAN; the 8-file diff holds no config/env file (README, `data_manager.py`, `models.py`, 2 test files, `availability-heatmap.tsx`, 2 new frontend lib files) |
| Paid / external SaaS | OK | No manifest, lockfile or `pyproject.toml` in the diff; scan-report reports no dependency finding |
| License changes | OK | No LICENSE or license field in the diff file list |
| Fabricated / substituted data (AG-3) | OK | Verified at row level: `data_provider_runs` 377-382 are all `provider='seed'`; the only non-seed row since 2026-08-10 is id=369 (iter-57, already in the ledger). J-09's screenshot figures (2948 / 591 / 5391 / 1996-01-02→2026-08-03) equal my own sqlite counts; `availability_cache` holds exactly 1 row whose stamp `r2949-rc2949-b2026-08-03-bc3306390-h200` matches the live DB's own max/count values |
| AG-1 / AG-2 / AG-4 / AG-5 / AG-6 | OK | Nothing in the diff touches scoring, evidence status, forward returns, or claim language; it changes one boolean's computation, two docstrings, one display gate and tests |
| AG-8 (critical) | VIOLATED — minor | `iter-58/f`. Forward-aggregate warm stalled at 1/5 horizons; VmPeak reached 8,388,608 kB = exactly the declared 8192 MB `memory_cap_mb`; `MemoryError` count 8,127 → 8,131 (counted by me). Scored minor: the triggering code (`_regime_lab_members_by_horizon`) is pre-existing and untouched by this diff, degradation was honest (0 non-200 in 227 polls, zero HTTP-500s after the event, same process kept serving and finished an 18-minute backfill), and this session's own precedent books this class against J-07. Logged in `assumptions.md` |
| AG-9 (critical) | OK | No new live-fetch row. Both dev drills and the QA backfill used Backfill, never the live-fetch button — the iter-57 process rule held |
| AG-10 (critical) | OK | `git status --porcelain` AND `git diff --stat` over `config.yaml`, `host-guard.env`, `start-backend.sh`, `dev.sh`, `start-frontend.sh` are BOTH empty; `config.yaml:1363-1364` still reads 8192 / 2; `logs/backend.log` shows `host-guard: cpu_list=0-15 blas_threads=8` on this round's launches |
| Verification integrity / evidence hygiene (session-local) | VIOLATED — minor ×5 | `iter-58/a` (J-07 "0.006s-1.18s" over a 2.097 s log), `iter-58/b` (J-05's 3.474 s answer re-labelled a recording gap), `iter-58/c` (blank `J-05-job-running.png`; `UT-J-05-result.png` shows none of its asserted state), `iter-58/d` ("8/8 journeys passed" over two journeys whose steps were not all executed), `iter-58/e` (spec says `Depth: full`, `depth-dispatched` reads `lean`) |

Ledger after this round: **150 total, 69 unresolved, 0 unresolved critical** (4 iter-57 items closed and
verified by me: the wrong health record, the always-"updating" banner, the empty-state gate, the
`models.py` docstring; 7 new minor items opened).

Coherence: **COHERENCE-PASS** (`iter-58/coherence.md`) — no blocking violation; the banner wording now
matches the sibling Coverage panel. Review: **PASS** (`definition_of_done: complete`, `scope_creep:
none`, `issues: []`). Merged browser QA: PASS 8/8 (see `iter-58/d` above). Deterministic replay: PASS
6/6. Audit / QA / closure / demo / ux-regression: **DID NOT RUN** (lean depth).

## Next-Step Recommendation

Run the next round at full depth — this is now required, not advised.

1. **Finish the two checks that were skipped, using the right team.** J-05 "Aggregates are precomputed
   at ingest" needs one thing to close: restart the backend and confirm the Data page still shows its
   coverage numbers quickly from saved data. The browser tester is not allowed to restart the app, and
   was blocked when it tried; the developer restarts the backend routinely. Give this step to the
   developer, not to the browser tester.
2. **Fix the way health checks are reported before trusting any of them.** This round's own hand-written
   record (Addendum 24) was honest and counted every line; the two browser-test records were not. One
   claimed a maximum of 1.18 seconds while its log holds 2.10 seconds, and the other called a real
   3.5-second answer a recording gap. Require every drill to publish the raw log's line count, its
   slowest answer, and the window it was measured in — the same way Addendum 24 does.
3. **Take the memory ceiling seriously now.** The heavy calculation stopped after 1 of 5 parts because
   the process reached its exact memory limit. The good news, which I checked myself: nothing broke this
   time — no page returned an error and no restart was needed. The one calculation that has never been
   made memory-safe (`_regime_lab_members_by_horizon`) is named, small, and has never been touched.
   Measure it first, then bound it. This is what keeps J-07 "Heavy aggregates never take the service
   down" open.
4. **Record a proper walkthrough.** J-05 and J-07 both require a recorded walkthrough to close, and the
   recorder only runs at full depth. This is a passenger of the round's real work, never a round's goal.
5. SMALL AND ALREADY WRITTEN DOWN: one screenshot saved as evidence is completely blank; the failed
   calculation records "failed" with an empty reason; `/api/regime-history` at 1.2-3.0 s has still never
   been re-measured on a quiet machine; a test file that has not finished five rounds running and a test
   that has never executed (both ticketed in `docs/test-infra-tickets.md`).
6. CARRIED, untouched: iter-29/b and the badge wording after a permanently failed warm-up (31st round
   unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az;
   iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj; iter-57/f; iter-57/l. Deferred a
   TWENTY-FOURTH time: iter-33/g, the Regime Lab.
7. OWNER: the same two questions, now asked nine rounds running — (a) may heavy calculation move into its
   own separate process, and (b) does the twenty-minute finishing budget apply while the app is also
   serving people? Plus three facts worth knowing: nothing broke when the app hit its memory limit this
   time; the wrong health record from last round has been corrected in writing; and this round ran
   shallow against a plan that asked for deep, for the third time in four rounds.

## Halt Justification (if halting)

Not halting. ESCALATE does not stop the session — it forces the next round to run the full pipeline.
Three reasons, each mechanical rather than a matter of taste. First, this was a shallow round
(`iter-58/depth-dispatched` = `lean`) run against a plan whose own header says `**Depth:** full` with
`Full trigger: 1` — the third mismatch in four rounds. Second, it surfaced a problem that spans several
lanes and that no lane reported: two test records that contradict their own raw logs, a blank picture
saved as evidence, and a headline reading "8/8 journeys passed" over two journeys whose own steps were
not all carried out. The deep-review step is precisely the one that caught the identical problem last
round, and it did not run. Third — and this is decisive — the two journeys still open both require a
recorded walkthrough in their acceptance text, and the recorder only runs at full depth, so **neither
journey can ever be closed by a shallow round**. In this session a recommendation is advice and an
ESCALATE is binding; that is why this is an ESCALATE and not another recommendation.
