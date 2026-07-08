# goal-mcp-loop-iter-21 Audit Report

**Date:** 2026-07-08
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

This verification-only iteration genuinely achieved its primary goal: it produced the **clean
canonical live browser-QA evidence trail for J-13** that iter-20 lacked. I independently confirmed
— by viewing the pixels, reading the live computed-style values, and reading the source — that every
J-13 DoD criterion passed live against real running services (two-group legend; density top bucket
blue `#a6c8f2` not amber; snapshot ring violet `#a78bfa` not green; hover distinguishes a Backfill-gap
day from a snapshotted day naming Fetch/Backfill), the evidence dir holds 12 md5-distinct on-topic
PNGs, and `git diff HEAD` on all five J-13 files is empty. The gaps are verification-chain / test-plan
issues on **non-J-13, non-regression** cases (UT-21/J-12 names the wrong page; UT-16 is a
test-wording granularity mismatch against a compliant honest-degrade), plus a stale QA report I
reconciled and an `ux-regression WARN` that is harness-acceptable. Closure (Step 10) has not run yet —
it is downstream of this audit (Step 9), so its absence is expected, not a failure.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no change needed): backend confirmed verification-only and green**
`git diff HEAD -- apps/backend/app/engine/data_manager.py` is empty (independently re-run); no file
under `apps/` is dirty. The scoped suite (`test_data_manager.py`, `test_data_manager_jobs_pipeline.py`,
`test_data_manager_parallel.py`, `test_seed_loader_pool.py`) passed **102/102**, including
`test_compute_availability_byte_identical_after_fetch_scope_widening` (anti-goal #3 byte-identity) and
`test_fetch_job_symbol_set_covers_committed_pool_and_context`. The live 588/588 Fetch counter
(UT-03/UT-05) corroborates the 548-pool∪context scope-widening against a real run. No defect.

### Frontend Findings

**F1 — GAP (verification-chain, not a regression): UT-21/J-12 literal replay could not close because
`/methodology`'s universe-count lives elsewhere**
`ui-test-results.md` marks UT-21 (P1) **FAIL** because `/methodology` shows no universe count. I did
NOT accept the browser-qa-agent's "stale test-plan reference" theory at face value — I read the
source and confirmed the more precise root cause the ux-regression reviewer found:
`apps/backend/app/api/methodology.py:34-36` deliberately does `catalog.pop("universe_selection", None)`
whenever `load_universe_screen_record(DEFAULT_SEED_DIR)` is falsy, and
`apps/backend/data/seed/universe.json` **is confirmed absent** (only `universe_pool.csv` exists). The
`UniverseSelectionCard` (`apps/frontend/app/methodology/page.tsx:60-61,237-289`,
`data-testid="universe-selection"`) is real and wired but conditionally rendered, so it correctly shows
nothing. This is a **pre-existing anti-fabrication honesty gate (J-22)** in files that neither iter-20
nor iter-21 touched — **not a regression** (the section has never rendered in this environment; nothing
that worked now fails). The substantive J-12 claim (cross-page universe-count consistency) holds and was
live-verified: `/data` "Universe (as of date): 541" == `/stocks` "541 / 541". The test-plan's UT-21
targets a page where the number is (correctly) absent. Non-blocking; test-plan needs a retarget, not a
product fix.

**F2 — GAP (verification-chain, not a regression): UT-16 fails literal text but anti-goal #8 holds**
`ui-test-results.md` marks UT-16 (P2) **FAIL** because the specific "Availability could not load…"
card text never appeared. I viewed `UT-16-backend-down.png` directly: with the backend killed, `/data`
renders a single honest page-level card — "Backend unavailable / Dataset coverage could not load from
the API. No figures are shown rather than fabricated values." — with the sidebar fully intact and no
blank application-error page and no fabricated data. That is exactly what **anti-goal #8** requires
(contained, honest, degrades gracefully, nav usable). The "failure" is only against the test's literal
expectation of *which* honest message (a narrower per-card branch) appears; the browser-qa-agent
honestly disclosed it had no request-interception primitive to isolate a single-endpoint failure, and
this coarser gate is an app-wide pattern (~15 pages) unrelated to iter-20/21. Non-blocking; test-plan
wording should be loosened.

**F3 — OBSERVATION (pre-existing, out of scope): `/methodology` universe-selection is an inert
capability for current users**
Because `universe.json` has never been committed, the Universe Selection section is invisible to every
user of this deployment until an operator runs `scripts/screen_universe.py` and commits the screen
record. This is correct-by-design (see F1), pre-existing, and outside this iteration's zero-code scope.
Recorded for visibility only; do not fix here.

### Test Findings

**T1 — IMPORTANT (fixed): QA report Browser-Checks section was stale and contradicted the real browser
run (DoD item 5)**
The QA report (written ~10:25) states "Frontend Reachability: SKIPPED" and "Functional Test Plan
Execution: DEFERRED", while the canonical browser-qa-agent then executed **live** from ~10:37–11:33
(trace.jsonl step 67, exit 0, 3527s; engine.log "Done" 11:33:11) reaching both `:3255` and `:8255` at
`200`. Left unreconciled, this is the exact self-contradicting QA-vs-browser artifact split the iter-20
lesson and this iteration's DoD item 5 forbid. **Fix applied:** I added a dated, auditor-attributed
reconciliation note at the top of the QA report's Browser Checks section pointing to
`ui-test-results.md` as authoritative and annotating the "SKIPPED" line as superseded — without
altering QA's original observations or its PASS verdict. Note in QA's favor: it never asserted a false
code-inspection PASS for a browser case (the iter-20 sin); it honestly deferred them to the lane that
then ran. This was staleness, not dishonesty.

**T2 — GAP (documented, for closure's attention): `ui-test-results.md` overall verdict is FAIL while
DoD item 2 requires overall PASS + 14/14 P1**
Overall is 20/22, 13/14 P1 — the single P1 miss is UT-21/J-12 (F1) and the P2 miss is UT-16 (F2), both
verified non-defects on non-J-13 cases. **Every J-13-specific case the spec names for "J-13 passes"
(UT-02/03/04/05, UT-10/11/12, UT-14) PASSED live.** Risk: a naive machine-parse of the "Browser QA
Verdict: FAIL" headline could wrongly block CLOSURE-PASS. Closure/evaluator should judge J-13 on its
own per-case result + md5-distinct pixels + the real browser-qa telemetry record (all present), per the
spec's own NOTES, not on the aggregate headline driven by two unrelated cases.

**T3 — OBSERVATION (positive): browser-qa correctly overrode a stale SKIP flag**
The harness precondition probe saw the frontend at `000` (10:34) and instructed the lane to mark all
cases SKIPPED — the identical failure mode as iter-20. The browser-qa-agent, per its own precondition
rule, independently re-verified reachability (`200`, stable, real content), and executed live rather
than emitting another blanket SKIP. This is precisely the behavior this iteration existed to guarantee,
and it is why the evidence dir is non-empty this time.

---

## 3. Domain Assessment

The J-13 domain logic is correct and now live-proven, not merely code-inspected. The presentation-layer
re-encode is faithful: live `:root` CSS vars read `--heat-0:#39516f … --heat-5:#a6c8f2` (monotonic blue
ramp, top bucket blue not amber) and `--snapshot:#a78bfa` (violet ring not green), and ux-regression
independently cross-checked those live values against `apps/frontend/app/globals.css` source — ruling
out iter-20's stale-`.next`-bundle failure. The two-signal semantics (cell fill = Fetch coverage; ring =
Backfill snapshot; "a day can have one without the other = a Backfill gap") are carried consistently
across legend labels, the header blurb, the caption, and the per-cell `title`/hover readout, all
naming Fetch and Backfill. Anti-goal discipline holds: no return/price/buy-sell language anywhere in the
rendered copy (header even reads "Research-only · decision support · no orders"); availability figures
are byte-identical (test-enforced); provider failures (162/588 live Yahoo `HTTP 400`) are surfaced
honestly with nothing fabricated. The only domain-adjacent surprise — the inert `/methodology`
universe-selection section — is itself a *correct* anti-fabrication behavior (F1/F3), not a defect.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/qa/goal-mcp-loop-iter-21-qa.md` | Added a dated auditor-attributed reconciliation note to the Browser Checks section pointing to `ui-test-results.md` as the authoritative live-browser record (services reachable, 22 cases executed live 10:37–11:33) and annotating the stale "Frontend Reachability: SKIPPED" line as superseded. QA's original observations and PASS verdict left intact. Satisfies DoD item 5. No source code touched. |

Post-fix verification: the reconciliation is factually correct against `trace.jsonl` (step 67, exit 0,
3527s), `engine.log` (browser-qa Done 11:33:11), and `ui-test-results.md`; the edit adds only the note +
annotation and changes no verdict; `git status -- apps/` remains empty (no source drift introduced).

---

## 5. Recommended Next Step

**Proceed to Step 10 (phase-closure).** J-13's canonical evidence is clean and complete — its own P1
cases all PASSED live, the evidence dir is non-empty with 12 md5-distinct on-topic PNGs, there is a real
browser-qa-agent telemetry record (trace step 67), and the five J-13 source files show an empty
`git diff HEAD`. Under the spec's own judging rule ("judge J-13 on the canonical `ui-test-results.md`
P1 pass + md5-distinct pixels + a real browser-qa-agent telemetry record + CLOSURE-PASS"), **J-13 is
ready to flip `partial → passing` once closure clears.**

Closure should be told plainly (T2): the `ui-test-results.md` "overall FAIL" is driven entirely by
UT-21/J-12 and UT-16 — both independently verified here as non-regressions on non-J-13 cases — so it
should not be read as a J-13 failure. Four of five required-still-passing replays (J-01/J-03/J-05/J-10)
came back cleanly live-verified; J-12's substantive claim holds via `/data` (541) vs `/stocks`
(541/541).

Non-blocking follow-ups to file (do NOT fix in this zero-code iteration):
1. Retarget UT-21's universe-count consistency check at `/data` ("Universe (as of date)") vs `/stocks`
   ("{visible}/{total}"), or make the `/methodology` check conditional on `universe.json` existing so
   "section correctly absent" scores as PASS (F1).
2. Loosen UT-16's expected text to the actual compliant page-level "Backend unavailable" gate, or add a
   request-interception-capable QA tool to exercise the narrower single-endpoint-failure branch (F2).
3. Carry forward the pre-existing `start-frontend.sh` freshness-stamp gap (iter-20 audit O1) — the
   `rm -rf apps/frontend/.next` workaround remains the operational mitigation.
