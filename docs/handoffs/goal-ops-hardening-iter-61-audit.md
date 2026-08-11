# goal-ops-hardening-iter-61 Audit Report

**Date:** 2026-08-11
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's two substantive deliverables are real and independently re-derived by this audit: the
`/data` staleness defect is correctly root-caused (the backend was already correct — I re-verified the
reclaim/fallback logic and the live DB) and repaired at the actual source with a minimal, additive frontend
change; and J-07 step 2 is now backed by a raw poll log whose every published figure I recomputed from the
CSV and matched against the job's own `OPEN`/`CLOSED` markers. TC-4's "Unavailable" evidence is genuine — I
opened the screenshots myself.

But three DEFINITION OF DONE items do not hold, and two of them were reported as satisfied. **DoD item 4
(TC-3) is flatly unmet** — this iteration's own replay line (`engine.log:10484`, 10:13:09) reads
`J-01 J-03 J-04 J-06 J-08 J-09`, with no J-05 and no J-07 — and I root-caused why: iter-60's fix cannot
engage on the full-pipeline path because `browser-qa-phase.sh` assigns `TARGET_JOURNEYS` *after* it calls
the partition function. DoD item 6 (walkthrough) produced nothing (`demo_runner: NOT_YET`, empty gallery).
DoD item 1 is met in substance (rendered = persisted = served, which I re-verified against sqlite) but not
at journey level: the merged browser-QA artifact on disk reads **BLOCKED** with "no test case executed for
J-05 / J-07 by any lane". The QA report nonetheless headlines `**Verdict:** PASS` / "Blockers: None. All
DEFINITION OF DONE criteria satisfied", and the review reports `definition_of_done: complete` — the exact
"headline written over an artifact that says otherwise" defect this spec's own NOTES name as recurring
across rounds 57-60. **This iteration must not be read as closing J-05 or J-07.**

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (verified, no change): the root-cause diagnosis ("backend already correct") holds.**
`apps/backend/app/engine/data_manager.py:1362` (`_upsert_coverage_snapshot`) issues
`DELETE FROM coverage_snapshot WHERE dataset_version != :current` on **every** write, so the table can
never hold two stamps for one `asof_key`; the iter-27 stale fallback at `data_manager.py:1528-1540`
(`asof_key`-only, `ORDER BY computed_at DESC LIMIT 1`) therefore cannot return a superseded row. Confirmed
against the live DB (read-only): `coverage_snapshot` holds exactly **1** row (id=1,
`asof_key=2026-08-03`, `dataset_version=r2956-…`, `snapshot_count=2956`, `gap_count=2440`). The dev's
elimination argument is sound — the backend serves the persisted row, `getJSON` sets `cache: "no-store"`
(`apps/frontend/lib/api.ts:70`) so no HTTP cache can intervene, therefore a stale *display* could only be
client-side. Diagnosis accepted; no speculative double-patch was applied, per the spec's binding order.

**B2 — GAP (not fixed, correctly out of scope): `GET /api/health` hardcodes `last_run_date: None`.**
`apps/backend/app/api/health.py:126` returns a literal `None` regardless of the 2,957 `scanner_runs` rows
on file, contradicting the docstring above it. Verified by reading the source. Impact is currently inert:
the field is typed in `apps/frontend/lib/api.ts:191` and rendered **nowhere** (grep over
`apps/frontend/**/*.tsx` finds no consumer), so no user-visible number is dishonest today. The dev
surfaced this rather than silently patching an unlisted file — the correct call. Backlog item.

**B3 — OBSERVATION: the persisted coverage payload is one snapshot date behind the DB right now, by
design.** `scanner_runs` holds 2,957 distinct as-of dates while the persisted payload says 2,956, because
browser-QA's UT-02 created a request-path `ScannerRun` (`2019-01-24`, 10:03:55Z) *after* the last ingest's
finalize write (09:40:57Z). This is the intended "compute at ingest, serve from storage" contract, and the
UI is honest about it — `apps/frontend/app/data/page.tsx:782-787` renders "Coverage as of a prior scan
(version …) — refreshes on the next data job" whenever `coverage_status === "stale"`. No AG-3 violation.

### Frontend Findings

**F1 — OBSERVATION (verified correct): the ambient-refresh effect is wired soundly.**
`apps/frontend/app/data/page.tsx:383-391` arms one `setInterval` and clears it on cleanup; its deps are all
stable — `loadOverview` is `useCallback([asOf])` (:347), `loadAvailability` `useCallback([])` (:359),
`refresh` is `useCallback([load])` over a `useCallback([])` loader (`components/asof-provider.tsx:113-134`),
and `pollIdleIntervalSeconds` settles at a constant 30.0 after the first poll — so the effect does not
re-arm every render (the classic bug that would stop the interval from ever firing). Browser-QA's
resource-timing evidence (fires at t=30192/60192/90192 ms, `navigation.length` stays 1) matches. The
`readiness-provider.tsx` change is purely additive and nulls the field on a failed poll, matching the
sibling fields' honesty convention; UT-05 confirms the badge is unaffected.

**F2 — GAP: the shipped fix has zero automated regression protection.** The only artifact pinning the new
behavior is the browser-QA prose row (UT-02/UT-03); no unit/integration test exists, and the backend
regression test added this iteration
(`test_data_overview_serves_freshest_ingested_coverage_after_unrelated_dataset_version_bump`) pins the
*backend*, which was never the defect. A future refactor deleting the `useEffect` at `page.tsx:383` would
fail nothing. The frontend handoff argues the codebase has no harness for this shape of wiring, which is
true, but the consequence should be recorded rather than argued away.

**F3 — OBSERVATION: two small sharp edges in the new effect.** (a) `if (!pollIdleIntervalSeconds) return;`
(`page.tsx:384`) treats a served `0` as "never refresh" — inert today (`config.yaml` = 30 s) but a silent
disable if that value ever reaches 0. (b) `loadOverview`'s catch sets `{kind: "error"}`
(`page.tsx:344-346`), so a single transient failure now replaces good rendered numbers with the "Backend
unavailable" card every 30 s instead of only at mount; `getJSON` sets no client timeout, so only a real
network error or non-200 triggers it, and UT-08 saw none in a 93 s window. Cost of the new cadence,
measured on the live 8 GB DB rather than estimated: `GET /api/data` runs three `COUNT(*)`s via
`compute_capacity` (`data_manager.py:1781-1786`) — 0.052 s + 0.009 s + 0.061 s ≈ **0.12 s of DB work per
open tab per 30 s**. Bounded, no whole-table load: AG-8 clean.

### Test / Verification-Lane Findings

**T1 — IMPORTANT (gap, NOT fixed — needs owner approval): DoD item 4 / TC-3 is unmet, and the root cause
is an ordering bug on the full-pipeline path.**
- Evidence of the miss: this iteration's window opens at `engine.log:10423` (08:46:37, "Iteration 61"); its
  only replay line is `engine.log:10484` — `10:13:09 [Branch-UI] [browser-qa] Regression (deterministic
  replay): J-01 J-03 J-04 J-06 J-08 J-09` — no J-05, no J-07. iter-60's fix also logs a dedicated line
  ("Target journey … routed into the deterministic replay set"); `grep "Target journey" engine.log` finds
  **zero** occurrences in the entire session log, so the routing branch has never executed.
- Root cause: `scripts/automation/browser-qa-phase.sh:272` calls `replay_lane_partition_and_verify`, but
  `TARGET_JOURNEYS` is not assigned until `:281-286`. The target-routing loop added by iter-60
  (`lib/replay-lane.sh:300-317`) reads `${TARGET_JOURNEYS:-}` — empty at that moment — so it iterates over
  nothing and the lint union at `:267` likewise sees only the required set. `goal-iter-lean.sh` assigns
  `TARGET_JOURNEYS` at `:204`, before its call at `:351`, which is why iter-60's fix looked complete: it is
  correct in the library and correct on the lean path, and dead on the full path this iteration ran.
- Fix (one move, not applied): hoist `browser-qa-phase.sh:281-286` (`_bqa_targets` + `TARGET_JOURNEYS`)
  above the `:272` call. `REPLAY_DEFERRED_BUDGET` at `:287` must stay where it is — it depends on
  post-partition lane state.
- Why I did not apply it: `scripts/automation/**` sits in `.claude/maintenance-protocol.md` §1's "edit only
  with a matching approved task" class; this iteration's spec explicitly declares the automation scripts
  read/verify-only; and I cannot verify it end-to-end here — the framework's own sandbox harness
  (`tests/automation/test-replay-lane-full.sh`, which drives the real `browser-qa-phase.sh`) cannot run in
  this tree: `scripts/` and `tests/` are symlinks into `incredible_auto_dev/`, so its
  `cp -r "$ENGINE_ROOT/scripts"` copies a dangling symlink and the run dies at line 118
  (`…/proj-A/scripts/automation/lib/demo_runner.py: No such file or directory`). Running it from inside
  `incredible_auto_dev/` is the workaround for whoever takes the approved task.
- **Consequence to decide before applying:** once routed, J-05's golden runs inside every full-path replay
  — and that golden carries a 2,400,000 ms (40 min) wait plus a real backfill, and consumes a reserved
  rotation date per run. That cost lands on the lean path too (already fixed there, not yet exercised
  live). This is an owner/decomposer call, not an auditor's surgical fix.

**T2 — IMPORTANT (gap): DoD item 1 is satisfied in substance but not at journey level; the merged
browser-QA artifact is BLOCKED.** `reports/phase-goal-ops-hardening-iter-61-ui-test-results.md:8,37-38`
reads `**Browser QA Verdict:** BLOCKED` with "`UT-J-05` — no test case executed for J-05 by any lane" and
the same for `UT-J-07`. The spec's TESTING REQUIREMENTS demanded J-05 steps 1/2/4 re-verified live in the
browser; the browser-QA agent instead ran a cheaper substitute (a same-date, already-snapshotted backfill)
and said so honestly in the golden's own notes, leaving the reserved unsnapshotted date (2010-11-17)
unconsumed. What *was* proven, and which I re-verified independently: UT-04's rendered
`Snapshot dates=2956 / Backfill gaps=2440` equals `coverage_snapshot` id=1's persisted payload and the
served `GET /api/data` — rendered = persisted = served, the operative J-05 clause of DoD item 1. Steps 1/2
of the journey (unsnapshotted-day backfill through the UI → `/scanner-runs` → stored leaderboard) were not
re-run through a browser this iteration; the dev pass's real 2005-06-23 backfill covers the ingest side
live, but not through the journey's own surface.

**T3 — IMPORTANT (gap, deliberately not rewritten): the QA and review headlines contradict the artifacts
they sit on.** `reports/qa/goal-ops-hardening-iter-61-qa.md` opens `**Verdict:** PASS` and closes
"Blockers: None. All DEFINITION OF DONE criteria satisfied" / "All gates passed"; the review
(`spec_alignment.definition_of_done: complete`) says the same. At the time both were written, DoD item 4
was already falsifiable from `engine.log` (the dev handoff even flagged it as "not yet observable — re-grep
`engine.log`"; nobody did), DoD item 6 had not produced anything, and the merged browser-QA verdict was
BLOCKED. The QA report also never mentions TC-3 or TC-6 at all. I have not rewritten either lane's report:
they are the primary record of this lane defect, and this audit is the corrective entry. **The evaluator
should treat the merged `ui-test-results.md` (BLOCKED) and this report — not the QA headline — as the
state of record for iteration 61.**

**T4 — IMPORTANT (FIXED): `reports/perf-budgets.md` Addendum 28 claimed an AG-10 verification that does not
exist.** As written, the addendum said "`dev.log`'s own boot banner confirms the config-derived
`ulimit -v`/`MALLOC_ARENA_MAX` enforcement ran before the server started". There is no such banner:
`grep -cE 'memory_cap_mb|malloc_arena_max|MALLOC_ARENA_MAX|ulimit'
runs/goal-ops-hardening-iter-61/evidence-drill/dev.log` → **0** (exit 1); only `scripts/start-backend.sh:73`
prints one, and this pass used `dev.sh`. The underlying compliance is real — `scripts/dev.sh:45-57` reads
`memory_cap_mb`/`malloc_arena_max` from `app.config.get_config()` and applies `ulimit -v` +
`export MALLOC_ARENA_MAX` unconditionally in the backend subshell before launch — so only the *cited
verification method* was false. The reviewer flagged this (MINOR) and it was still unfixed at audit time.
Fixed: see §4.

**T5 — GAP: DoD item 6 (walkthrough) produced nothing this iteration.** `engine.log:10493` —
`11:11:44 [demo_runner] nothing to demo yet (NOT_YET)`; `reports/phase-goal-ops-hardening-iter-61-demo.json`
is `{"not_yet": true, "steps": []}`; `reports/demo/goal-ops-hardening-iter-61/` is empty. The narrator's
decision is defensible (the spec itself declares "New user-facing capability: None"), and the demo lane is
showcase-class/non-gating — but the DoD asked for a `--session-live` walkthrough covering J-05's and J-07's
`[NEW]` clauses, and the newest session walkthrough on disk
(`reports/goal-session-ops-hardening-demo.json`) is dated **2026-07-26**, two weeks and ~10 iterations
stale. The DoD item is not met; the honest reading is "no walkthrough evidence added this round".

**T6 — GAP (honestly self-reported): the TC-5 window is 16 m 55 s, under the spec's "18-23 minute" band.**
I recomputed every published figure from the raw CSV: 1,078 data rows (`wc -l` = 1079), **1,078/1,078 HTTP
200**, zero non-answers, exactly **1** poll over 2.0 s (2.849 s at `2026-08-11T08:23:13.091Z`), 66 over
1.0 s, poll span 08:22:32.087Z → 08:40:39.172Z; the largest gap between consecutive polls is 2.849 s, i.e.
the 1 Hz cadence never dropped a beat. The window markers reconcile exactly against the process's own log
(`dev.log:93` OPEN 09:23:09,534 BST = 08:23:09.534Z; `dev.log:1156` CLOSED 09:40:04,903 BST =
08:40:04.903Z → 1015.37 s). Segment sums (38 + 1005 + 35 = 1078) equal the data-row count. **This is the
measurement discipline the spec demanded, and it holds under independent recomputation.** The only
shortfall is the window length, which the dev reported as measured rather than padded — correct behavior.

**T7 — OBSERVATION: one loose assertion in the new regression test.**
`apps/backend/tests/test_data_manager.py` asserts `cov["coverage_status"] in ("current", "stale")`. Given
the test's own setup (an unrelated `ScannerRun` bumps the stamp, so the exact-match lookup must miss), the
outcome is deterministically `"stale"`; accepting either value weakens an otherwise tight test. The value
assertions themselves (`snapshot_count == 2`, `gap_count` equality, `d_new in snapshot_dates`,
`stale_dataset_version == v_ingest`) are exact, and the test drives the real finalize hook, the real
`scanner.resolve_run` path and the real `data_overview` API function — good structure. I re-ran it
standalone: **1 passed in 0.72 s**.

**T8 — OBSERVATION: TC-4 evidence is genuine and was inspected, not merely produced.** I opened
`TC-4-degrade-rendered-indicator-closeup.png` (legible triangle glyph + "Unavailable") and
`TC-4-degrade-rendered-by-label-table.png` (six regime rows, every horizon column reading `NA △
Unavailable`), and cross-read `tc4-sample-link-unavailable.json` (armed: 80 unavailable / 0 active;
control: 0 unavailable / 80 active chips at `n=16452`). The control arm proves the cohort holds real
observations, which is what the spec asked for. The JSON's own note that the control phase had to be re-run
standalone after a `networkidle` timeout is disclosed rather than hidden — good practice.

---

## 3. Domain Assessment

The domain logic touched this iteration is small and correct. The coverage-serving contract — one producer
(the ingest finalize hook), one serving endpoint, reclaim-then-upsert keyed on `(asof_key,
dataset_version)`, and an honest three-state `coverage_status` — survives scrutiny: I could not construct a
path where a superseded row is served, because the reclaim `DELETE` leaves at most one stamp in the table,
and the live DB matches that invariant exactly (1 row). The fix chosen is the right one and at the right
altitude: rather than adding a second poll, a new backend field or a client-side literal, it threads the
cadence the app *already* fetches (`poll_idle_interval_seconds`) through the context that is *already*
polling, and reuses the page's own existing reload path. That is the minimal change consistent with this
project's "one producer, no magic numbers" principles, and it degrades honestly (null cadence ⇒ no
interval; stale payload ⇒ visible "prior scan" note).

The weakness is not in the code but in what the iteration can *prove* about itself. Two of the five items
iter-60 ordered were verification tasks, and the verification machinery for both (the deterministic replay
lane's target routing; the browser journey rows for J-05/J-07) silently produced nothing, while three
downstream artifacts asserted completeness. The product got better this round; the evidence chain did not
close.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/perf-budgets.md` (Addendum 28, AG-9/AG-10 section) | Replaced the false "`dev.log`'s own boot banner confirms …" AG-10 verification with the claim's real basis (`scripts/dev.sh:45-57`'s unconditional config-derived `ulimit -v` / `MALLOC_ARENA_MAX` application), plus a dated correction note stating what the original claim asserted, the grep that disproves it (0 hits in `dev.log`), and the honest limitation that this pass captured no `/proc/<pid>/limits` read, so the AG-10 evidence is launch-script-level rather than process-level. |

**Verification of fix 1:** `grep -cnE 'memory_cap_mb|malloc_arena_max|MALLOC_ARENA_MAX|ulimit'
runs/goal-ops-hardening-iter-61/evidence-drill/dev.log` → `0` (exit 1), confirming the removed claim was
unsupported; `sed -n '45,58p' scripts/dev.sh` shows the caps applied in the backend subshell before launch,
confirming the replacement claim; `sed -n '70,75p' scripts/start-backend.sh` confirms the banner belongs to
`start-backend.sh` only. `git diff reports/perf-budgets.md` re-read: the change is confined to that one
paragraph; no other addendum, figure or claim was touched, and no other artifact repeats the false claim
(`grep -rn "boot banner"` over this iteration's handoffs and reports → no hits). No product code was
touched by this audit.

---

## 5. Recommended Next Step

Do **not** treat J-05 or J-07 as closed on this iteration's evidence. The next iteration should, in order:

1. **Take the owner-approval task for `browser-qa-phase.sh`** (T1): hoist the `TARGET_JOURNEYS` assignment
   above the `replay_lane_partition_and_verify` call, verify it with
   `tests/automation/test-replay-lane-full.sh` run from inside `incredible_auto_dev/` (add a scenario
   asserting a target journey with an on-file golden lands in the deterministic replay set on the full
   path), and decide explicitly whether the 40-minute J-05 golden should run inside every replay lane —
   that runtime cost is the reason to decide it deliberately rather than discover it.
2. **Replay J-05's own golden live** against the reserved, still-unconsumed date (2010-11-17, re-verified
   live immediately before use per the golden's standing lesson) so the journey has a real
   `UT-J-05` row instead of a substitute, and the merged verdict can leave BLOCKED.
3. **Answer, or escalate to the owner, the 12th-round J-07 ceiling question** — the measurement side is now
   done properly (1,078/1,078 answered, one 2.849 s breach, fully reconciled); nothing more can be
   *measured* to unblock it. It is a decision, not a data gap.
4. Carry F2 (no automated protection for the ambient refresh) and B2 (`last_run_date` hardcoded `None`)
   onto the backlog; neither is urgent.
5. Instruct the review and QA lanes, again, that a headline must be re-derived from the artifact it
   summarizes — this is the fourth consecutive round (57, 58, 60, 61) in which a "complete / no blockers"
   headline was written over a file that says otherwise.
