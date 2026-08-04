# Iteration 45 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This round built the right thing for the wrong problem. The team fixed a slow calculation that
rebuilds the whole company-membership history every time one day of data is added — and the fix is
correct, carefully guarded, and well tested. But it never ran even once in the live app, and it did
not help either of the two journeys it was built for. J-05 "Aggregates are precomputed at ingest"
failed again: the one-day backfill of 2019-02-25 stopped after 4 minutes 46 seconds with an
out-of-memory error and created nothing. J-07 "Heavy aggregates never take the service down" failed
again, for the fourth round in a row: the whole app went silent for about 42 minutes. Six other
journeys were re-checked and still work. The real cause is now known and written down with exact
file and line numbers, and it is work an agent can do next round.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `ui-test-results.md` UT-J-01 PASS; `reports/qa/goal-ops-hardening-iter-45-evidence/J-01-verify.png` (md5 `10ed982b…`) |
| J-03 No per-run range cap | passing | passing (capture defect) | `ui-test-results.md` UT-J-03 PASS; `reports/qa/goal-ops-hardening-iter-45-evidence/J-03-verify.png` — opened by me; byte-identical to J-04's file (md5 `9d77429b…`), so `evidence_makeup: true` |
| J-04 Non-blocking boot with visible status | passing | passing (capture defect) | `ui-test-results.md` UT-J-04 PASS; `reports/qa/goal-ops-hardening-iter-45-evidence/J-04-verify.png` — same md5 `9d77429b…`; `evidence_makeup: true` |
| J-05 Aggregates are precomputed at ingest, never on the fly | failing | failing (2nd consecutive) | `ui-test-results.md` UT-J-05 **FAIL**; `reports/qa/goal-ops-hardening-iter-45-evidence/UT-J-05-fail.png` — opened by me. Verified independently in the DB: `data_provider_runs` id 281 = `failed`, `snapshots_created: 0`, `dates_done: 0/1`, `summary: "MemoryError (no message)"`, 00:38:14→00:43:00; `select count(*) from scanner_runs where asof_date like '2019-02-25%'` → **0** |
| J-06 Pages load only what they need | passing | passing | `ui-test-results.md` UT-J-06 PASS; `reports/qa/goal-ops-hardening-iter-45-evidence/J-06-verify.png` (md5 `4a3647e9…`) |
| J-07 Heavy aggregates never take the service down | failing | failing (4th consecutive) | `ui-test-results.md` UT-J-07 **FAIL**; `reports/qa/goal-ops-hardening-iter-45-evidence/UT-J-07-fail.png` — opened by me. Verified independently: `logs/backend.log` has **zero** access-log lines between `:172574` (01:52Z) and `:172965` (02:34Z) — ~42 min — with 22 `MemoryError`s inside that window |
| J-08 Backtest evidence serves from storage only | passing | passing | `ui-test-results.md` UT-J-08 PASS; `reports/qa/goal-ops-hardening-iter-45-evidence/J-08-verify.png` (md5 `2ec1cdb1…`) |
| J-09 The backend discloses its own background-compute activity | passing | passing | `ui-test-results.md` UT-J-09 PASS; `reports/qa/goal-ops-hardening-iter-45-evidence/J-09-verify.png` — opened by me; shows the live "background compute running (1)" chip (md5 `031ccc97…`) |

Deferred (`DEFERRED-BUDGET`): none. No `browser-infra.json`. No `journeys-changed.md`; I ran
`goal_gate.py hash-journeys docs/goal.md` myself and all eight `spec_hash`es match the recorded
values, so no journey text moved and no prior pass is void.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (nothing "proven" without a ledger entry) | OK | No evidence/claim surface touched. Diff is `data_manager.py`, its tests, `demo_runner.py`, one JSON anchor. |
| AG-2 (no return promises / orders) | OK | No product-copy or trading surface in the diff. |
| AG-3 (displayed numbers must be correct) | **Violated and CLOSED in-iteration** | Audit B4: the new fast path reused stale per-date `excluded` tallies when bars land at or before a cached date — a Data-Contract row serving `/data`, `/sectors`, `/themes`, `/research/*`, `/evidence`. Proven by removing the guard. Fixed at `data_manager.py:634/:656/:852` with a negative-controlled test plus a positive control. Ledger `iter-45/aq`, severity critical, **resolved**. |
| AG-4 (no overfit edges) | OK | No referee/claim path touched. |
| AG-5 (determinism / no lookahead) | OK | Byte-identity is the fix's own contract; TC-1/2/3 plus the gap-fill fallback test re-run green by the auditor before and after his five fixes (`43 passed, 135 deselected`). |
| AG-6 (no ship without referee verdict) | OK | No evidence-derived claims this iteration. |
| AG-7 (no hard-coded credentials) | OK — scan CRITICAL verified as a false positive | `scan-report.md` flags `secret-assignment` "sk-FATAL-HANDLER-LEAK-9c4a2d" in `apps/backend/tests/test_data_manager.py:6055`. I opened it: it is a synthetic sentinel inside `test_fatal_job_failure_log_never_leaks_the_provider_key`, fed to `_KeyLeakingProvider` to prove the key is scrubbed OUT of logs. It authenticates to nothing, and three identical-shape fixtures predate it (`test_api_data.py:329,487,878`). Not a credential; see `assumptions.md`. |
| AG-8 (no crash / no memory exhaustion / no unbounded loads) | **Violated, open, minor** | The service exhausted its memory and was fully unreachable ~42 min (`iter-45/ao`), and the exhaustion is reachable from ordinary page browsing — 16 of 24 wedge-window `MemoryError`s entered through `evidence.py:168` on the `/api/evidence` render path (`iter-45/ap`). Kept minor on stated grounds: this iteration's diff neither introduced nor widened it (the new path provably never executed — `grep` for `_membership_timeline_incremental`/`append-forward` over 173k log lines → **0** matches), the UI degraded honestly rather than breaking, and every remedy is agent-actionable at a known file:line. |
| AG-9 (offline-deterministic ingest) | OK | No manifest change; `git diff` over `apps/backend/app` shows no new network call. Notably the lanes *respected* AG-9 rather than fetching newer data to manufacture an easier test target. |
| AG-10 (host resource ceiling) | OK — checked at the source | `start-backend.sh`: `ulimit -v` at `:56`, `MALLOC_ARENA_MAX` at `:60`, HOST-GUARD block intact `:76-101`; `config.yaml:1363` still `memory_cap_mb: 8192`; `host-guard.env:89` still lists all three launchers. `git diff` vs the snapshot SHA over `config.yaml`, `project-extensions/` and `docs/goal.md` is **empty**. No cap removed, weakened, or bypassed. |
| Licenses / paid dependencies | OK | No `requirements*.txt`, `pyproject.toml`, `package.json` or `LICENSE` change (checked with `git status` over those paths). |
| Fabricated / substituted data | OK | `2019-02-25` has 0 rows in `scanner_runs` and every report says so. The dev disclosed his own drill's DB side effect (a real `2019-02-26` snapshot) rather than hiding it. |

Ledger after this iteration: **57 entries, 20 unresolved, 0 unresolved critical.** New:
`iter-45/ao`, `ap`, `ar`, `at` (minor, open) and `aq` (critical, resolved in-audit). Closed:
`iter-44/am`. Five carried items given an ITER-45 UPDATE recording what I verified rather than
inherited. Coherence: **COHERENCE-PASS** (zero blocking, two advisories). Review **FAIL**
(1 CRITICAL); QA **FAIL** (re-validated); audit **FAIL** (2 CRITICAL gaps, 5 fixes applied
in-audit); browser QA **FAIL 6/8**.

## Next-Step Recommendation

Give the next round one job: **stop the app running out of memory while somebody is just looking at
a page.** The cause is no longer a guess. When the Evidence page loads, it works out drawdown
figures for every claim on the page, and two places keep one entry in memory for every single row
they read — `apps/backend/app/engine/research.py:777` and
`apps/backend/app/engine/forward_testing.py:2343`. Sixteen of the twenty-four out-of-memory errors
during the silent window came in through that page. Put a firm limit on those two places, then prove
it by loading the Evidence page while a data job is running.

Then, in order: (2) make the next failure readable — a job that dies of memory wrote **nothing** to
the log, so run 281's failure cannot be explained today; add a log line to the outer failure handler
and guard the one at `data_manager.py:3451`. (3) Add the outside-the-app safety net that stops and
restarts a frozen backend; this round proved an inside-the-app deadline cannot work, because the app
could no longer create the thread it needs to answer anything. (4) Re-run all eight journey checks
afterwards and make sure each one gets its own picture — J-03 "No per-run range cap" and J-04
"Non-blocking boot with visible status" currently share one file, so one of them has no picture of
its own. (5) Keep the membership fix; it is correct and cheap, but it has still never run for real,
so nobody should claim it works at full scale yet. (6) SMALL AND ALREADY WRITTEN DOWN: guard the
last two unprotected log calls at `data_manager.py:5058` and `:5091`; re-check the `n=8991` number
in `journey-scripts/J-07.json`, which is still unverified. (7) CARRIED, untouched: iter-29/b and the
badge wording after a permanently failed warm-up (SEVENTEEN rounds unmade); iter-31/e; iter-32/f;
iter-33/g deferred an ELEVENTH time; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-43/ag, whose
clean re-measurement could not happen because the app was unreachable the whole window.
(8) CAPTURE ONLY, never a round's goal: J-07's `[NEW]` walkthrough, fifteenth round unrecorded.
(9) OWNER: nothing needs his decision — but he should know two things. The app now goes dark for
about 42 minutes, twice as long as last round, and it can be triggered by ordinary browsing.
And J-05 asks for a backfill of a day that has no snapshot yet, while every such day left in this
database sits *before* dates already stored — so the shortcut built this round can never apply to
it. Closing J-05 means making that older-day case fast too, which is a normal next piece of work,
not a decision only he can make.

**One sentence for approval:** next round should bound the two memory hot spots on the Evidence page
and prove the app stays reachable while a data job runs.
