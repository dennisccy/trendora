# Iteration 36 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration built the work that iteration 35 planned but never shipped, and it built it well. The
biggest win: the part of the system that prepares data coverage used to pull every price ever stored
into memory at once (about 1.13 GB); it now works through the stock list in small groups and uses
about 330 MB — a 70.7% drop — and two separate tests prove the numbers it produces are exactly the
same as before. On screen, four Research pages that used to show a blank grey box while they were
working now say "Still computing — 28s elapsed" with a clear explanation, and a failed load now
offers a **Retry** button. I opened four screenshots and confirmed each one myself. J-06 "Pages load
only what they need" is back to passing.

But J-07 "Heavy aggregates never take the service down" was never actually tested. The browser test
run has no J-07 row at all: the test agent shut the backend down on purpose for the failure tests,
was then refused permission to start it again (three tries), and the two remaining tests were
abandoned. So the iteration's own first completion requirement was not met. The auditor checked part
of J-07 by hand afterwards and it looked healthy, but the main scenario — a long heavy warm-up while
the health check is watched every second — never ran. J-07 stays partial for a second iteration in a
row.

Two things a reader should not miss. First, the pipeline's final automatic check reported a failure,
and I checked it and it is a false alarm: the checker looks for the words "backend-only" in the
change summary and concludes "this change is invisible to users", but here that phrase is only a
section label inside a document that correctly lists four changed pages. Second, a leftover backend
process from the test run is still alive right now, holding 4.1 GB of memory and answering nothing.
It must be shut down before anyone measures memory again.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | reports/qa/goal-ops-hardening-iter-36-evidence/J-01-verify.png (opened — spot-check 1) |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-36-evidence/J-03-verify.png (replay UT-J-03 PASS) |
| J-04 Non-blocking boot with visible status | passing | passing | reports/qa/goal-ops-hardening-iter-36-evidence/J-04-verify.png (replay UT-J-04 PASS) |
| J-05 Aggregates are precomputed at ingest, never on the fly | passing | passing | reports/qa/goal-ops-hardening-iter-36-evidence/J-05-verify.png (opened — spot-check 2) |
| **J-06 Pages load only what they need** | **partial** | **passing** | reports/qa/goal-ops-hardening-iter-36-evidence/UT-05-computing.png (opened); also UT-03-error.png, UT-08-error.png, UT-11-error.png (all opened) |
| **J-07 Heavy aggregates never take the service down** | **partial** | **partial** (gap: never run — no J-07 row in the merged results; UT-13/UT-14 SKIPPED) | docs/handoffs/goal-ops-hardening-iter-36-audit.md §2/B2 (live 30/30 health polls, VmPeak 42.8% of cap); reports/perf-budgets.md "Iteration 36" (TC-1/TC-2/TC-3/TC-8) |
| J-08 Backtest evidence serves from storage only | passing | passing | reports/qa/goal-ops-hardening-iter-36-evidence/J-08-verify.png (replay UT-J-08 PASS) |
| J-09 The backend discloses its own background-compute activity | passing | passing | reports/qa/goal-ops-hardening-iter-36-evidence/J-09-verify.png (replay UT-J-09 PASS) |

Deterministic golden replay: **6/6 PASS, 0 FAIL, 0 reconciliation overturns**
(`reports/phase-goal-ops-hardening-iter-36-regression-replay-results.md`), and the merged file agrees
with it — merged PASS 15/20 with 5 SKIP = 6 replay + 9 LLM lab tests. No `DEFERRED-BUDGET` row. No
`browser-infra.json`. No `journeys-changed.md`, and all 8 `spec_hash` values match
`goal_gate.py hash-journeys` — so no journey's goal text moved under a recorded pass.

Screenshot integrity: all 6 `J-*-verify.png` carry **distinct** md5s, so the byte-identical-screenshot
nit that recurred at iter-35 (J-01 and J-04 sharing `414f9e66`) did **not** recur. One duplicate does
exist — `UT-03-error.png` and `ENV-backend-down.png` are byte-identical (`d586eb07`) — but I opened it
and the content is genuinely the Factor Lab error card with its own copy and a Retry button, so it is
a duplicated file, not a wrong frame.

### Why J-06 moves back to passing

Iteration 35 downgraded J-06 on one stated premise: all four sibling Research labs rendered a bare
unlabelled grey skeleton during a genuinely slow load, with no Retry on failure. That premise is now
falsified by frames I opened myself, not by prose:

- `UT-05-computing.png` — `/research/phase-severity-lab` during a real ~1m45s cold compute, showing
  "Still computing — 28s elapsed" with a spinner and the honest sentence "nothing is shown in the
  meantime rather than a partial or fabricated result", sitting **above** the skeleton. (The report's
  prose says "20s elapsed"; the screenshot says 28s. The screenshot wins; both are past the 3-second
  grace window, so nothing turns on it.)
- `UT-03-error.png` — `/research/factor-lab`, "Backend unavailable / The Factor-Lab evidence could
  not load from the API. No figures are shown rather than fabricated values." with a working Retry.
- `UT-08-error.png` — `/research/regime-phase-factor`, its own bespoke card now carrying a Retry.
- `UT-11-error.png` — `/research/severity-velocity`, the one lab where Retry was actually **clicked**:
  it re-fired the fetch and settled into a single fresh error card, not a frozen or duplicated one.

Corroboration I checked rather than assumed: `coherence.md` confirms all four call the **same**
unmodified `resolveLabLoadPanel` (0 diff to `lib/lab-load-panel.ts`) with no fork; the auditor re-read
all four wirings and found each adds `attempt` to its fetch effect's dependency array, byte-for-byte
the pattern already proven for Regime Lab (F1); 13/13 resolver tests pass; `tsc --noEmit` reports 0
errors. J-06's step-1/step-2 page-load budgets carry forward under evidence durability (methodology
A.6): the pages' on-load request path is unchanged — `/api/data` still serves the persisted
`coverage_snapshot` row, and only the cache-MISS compute path was touched.

And for the first time in six iterations J-06's `[NEW]`-flagged walkthrough clause got a recording:
demo steps 01-04 are all flagged `New: yes` against J-06
(`reports/phase-goal-ops-hardening-iter-36-demo-results.md`). Its subject is the labs' honest loading
states rather than "the budgets table vs live page loads" that J-06's Acceptance text names, so the
`evidence_makeup` flag is cleared per the mechanical A.7 rule while the narrower subject gap is
carried below as a capture-only ride-along.

### Why J-07 stays partial

The iteration's own Definition of Done item 1 — "J-07 passes via browser-qa-agent" — was **NOT MET**,
and the auditor says so in those words. The merged results file contains no J-07 row at all. `UT-13`
(`/data` panel unchanged) and `UT-14` (`/evidence` expectations panel) are both SKIPPED, for a reason
recorded verbatim at `reports/phase-goal-ops-hardening-iter-36-ui-test-results.llm.md:239-249`: the
test agent stopped the backend for the error-state tests and "was blocked by the permission system
from restarting it … three attempts denied". `runs/goal-ops-hardening-iter-36/status.json` records
`"browser_checks_run": false`.

Verified this iteration (auditor, first-hand, against a real `scripts/start-backend.sh` boot with
`ulimit -v` 6,291,456 KB confirmed in the banner): 30/30 `GET /api/health` HTTP 200 at 1 Hz, max
132 ms, readiness `ready`; VmPeak 2,691,796 / 6,291,456 KB = **42.8% of cap**; `/api/data`
internally consistent (548 pool − 8 excluded = 540 universe); `/api/evidence` serving 7 claims **all**
with real expectations panels and no `"unavailable"`; TC-8's real `ulimit -v` subprocess drill 3/3.

Not verified: step 1's full-horizon forward-aggregate warm; step 2's 1 Hz poll **during** that warm;
step 4's induced-pressure drill re-verified against the newly bounded paths in a live serving
process; and step 3's requirement that the VmPeak **margin** be recorded in
`reports/perf-budgets.md` — the iteration-36 section records call-level `tracemalloc`/RSS figures, not
the process VmPeak margin, so that number still lives only in the audit handoff.

I record one departure from the auditor: he recommends J-07 be scored `unknown`. I scored it
`partial`, because "only some assertion steps passed" is literally what happened and several steps do
carry this iteration's own first-hand evidence. Both readings block GOAL_ACHIEVED identically; the
call is logged in `assumptions.md`.

## Anti-goal Check

Worked from `iter-36/scan-report.md` (**CLEAN** — no secret, dependency, or license findings over the
product diff, tracked plus 2 untracked) and `iter-36/iter-diff.md` (13 files, all shown in full), then
re-derived the diff scope myself: `git diff c72a396b..HEAD -- apps scripts project-extensions
config.yaml` is EMPTY (nothing committed yet) and `git status --porcelain` over the same paths shows
exactly 11 modified + 2 new untracked test files.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 — unproven values must render "not yet proven" | OK | No proven-language added. The only new UI copy is honest-wait and honest-failure text ("No figures are shown rather than fabricated values"), read directly in the four screenshots I opened. Coherence: "no new field, no new endpoint, no new displayed value." |
| AG-2 — decision-quality only, no promises/orders | OK | No new displayed value at all. Every frame I opened carries the standing "Research-only · decision support · no orders" header and the "Descriptive evidence, not a predictive model … never a forecast" banners. |
| AG-3 — displayed numbers must be correct | OK, one recorded residual (**iter-36/n**, minor) | Byte-identity is this iteration's core requirement and it is proven, not asserted: TC-2 (membership timeline, `git show HEAD`-pinned, live seed DB) PASS; the coverage-payload half the spec named and the dev's test omitted was **found and fixed by the auditor** (B1) — 16 resolver comparisons over 4 real 50-symbol batches × 4 as-of dates + the 5,383-date benchmark calendar, 0 divergences — and **negative-controlled** (T2: a gate-crossing count perturbation and a bar-content perturbation were both detected), so it is not a vacuous oracle. Drawdown payload byte-identical at chunk widths [1,2,3,50]. Live `/api/data` internally consistent. My own check: `J-01-verify.png`'s "Candidate universe 122" is `candidate_universe_count`, a **different** field from `candidate_pool_count` (548) — I read the binding at `apps/frontend/app/data/page.tsx:785-787` rather than calling it a discrepancy. Residual: `_excluded_counts_by_date` double-counts a duplicated snapshot date (audit B5, `data_manager.py:592-612`), unreachable in production because `ScannerRun.asof_date` is `unique=True` (`models.py:204`) — filed as iter-36/n. |
| AG-4 — no overfit edges | OK | Referee, ledger, and claim paths untouched; not in the 13-file diff. |
| AG-5 — determinism and no-lookahead | OK | The batching changes only WHICH symbols one call resolves; `resolve_with_reasons` still reads `bars_asof` (date ≤ D) only, and `_membership_timeline`'s "Strictly causal" contract is retained verbatim. No scoring or forward-return path is in the diff. Coherence PASS on every Data Contract row. |
| AG-6 — evidence claims need a referee verdict | OK | No evidence claims introduced; `docs/goal.md` Loop mechanics put J-01…J-06 outside the claim gate. |
| AG-7 — no hard-coded credentials | OK | scan-report CLEAN on added lines; the only new config is two documented integers in `config.yaml:916-928` (`membership_timeline_batch_symbols: 50`, `drawdown_expectations_ticker_chunk: 50`). No new env/config file. |
| AG-8 — resilience to data-scale; no unbounded whole-table ORM loads | Net strongly improved; **2 residuals carried, 1 new** (all minor) | Improved: the coverage cold-compute's whole-table prefill is gone (70.7% peak reduction, proven byte-identical on both halves), and one of the three whole-table prefills on a K-date backfill is eliminated (test count 3→2; the reviewer confirmed 11/3 on unmodified HEAD via `git stash`, so a net gain, never a regression). Residuals: **iter-36/l (new)** — `_persist_per_date_coverage_snapshots` (`data_manager.py:3183`) and `_do_backfill` (`data_manager.py:3085`) still each prefill the whole table on a multi-date backfill, so J-07's "no unbounded whole-table ORM materialization remains" clause is still not literally true; **iter-35/k** — the evidence-path chunking is a measured ~4% (50 MB of 1.19 GB), not an architectural bound, disclosed in three places; **iter-33/g** — UT-12's cold Regime Lab load pushed VmPeak to ~100 KB under cap with one `MemoryError` at `research.py:3339`, endpoint still HTTP 200 (a third accumulator site, explicitly out of scope). |
| AG-9 — offline-deterministic ingest, no live network / paid services | OK | No manifest change of any kind (no `package.json`, `requirements*.txt`, `pyproject.toml` in the diff); scan-report reports no dependency findings; every frame I opened shows `provider: seed`. |
| AG-10 — host resource ceiling; launch scripts must apply the caps | OK, **1 new live hygiene item** (iter-36/m, minor) | Verified first-hand: `scripts/start-backend.sh`, `scripts/dev.sh`, `scripts/start-frontend.sh` and `project-extensions/host-guard/` are ALL byte-unchanged (both `git diff` and `git status` empty over them), so AG-10's own REGRESSION trigger — stripping a HOST-GUARD marked block — did not fire. The auditor ran every command under `taskset -c 0-3,8-11` with BLAS/OMP capped to 4 and booted via `start-backend.sh`. TC-8's new drill **tightens** caps in throwaway subprocesses, never weakens them (the iter-34 precedent). New item **iter-36/m**: PID 2944679 is still alive as I write this — I checked with `ps`/`ss`/`curl` — holding 4.1 GB RSS at VmPeak 6,291,352 KB (~100 KB under cap), 3h46m after the lane's own `kill -TERM`, with no listener on 8255 and no answer from `/api/health`. The caps contained the failure and the host never went down, so this is hygiene, not a cap violation — but it must be reaped before the next memory measurement. |

**No critical violation introduced.** Ledger: 11 open findings, all `minor` — iter-29/b, iter-29/d,
iter-31/e, iter-32/f, iter-33/g, iter-33/i, iter-34/j, iter-35/k (carried, each given an ITER-36
update recording what I verified) plus **iter-36/l, iter-36/m, iter-36/n** (new). **iter-33/h is now
RESOLVED** — the four sibling labs' honest-wait/Retry gap, open for three iterations, is closed with
four screenshots I opened.

Coherence: **COHERENCE-PASS**, no blocking violations, one non-blocking advisory (Regime × Phase ×
Factor keeps its own pre-existing bespoke error card with its own test id rather than switching to the
shared component — pre-dates this iteration, copy is verbatim-matched, disclosed in an inline comment).

## Pipeline Health

- Review: **PASS_WITH_NOTES** — 1 MINOR (TC-2's oracle covered only the membership half; the auditor
  then fixed exactly that) + 1 NOTE. Not a fail-open situation.
- QA: **PASS**. No UI Evolution Audit block is present in the report.
- Audit: **PASS_WITH_GAPS** — 9 backend findings, 2 frontend observations, 2 test observations; one
  IMPORTANT finding fixed during the audit (test-only, no production code touched).
- UX regression: **SKIPPED** — shed as a non-blocking lane because the iteration exceeded its
  wall-clock budget (SPEED-15 trim rung 3b). I credited nothing to it.
- Closure: **CLOSURE-FAIL**, and it is a **false alarm** I verified in the gate's own source. The
  blocking issue reads "user-visible-changes claims no visible changes but frontend files were
  modified". The check is a regex — `backend-only|no user-visible|no visible changes|frontend
  present:\s*no`, `closure_gate.py:71-74` — and its single match in the document is the phrase
  "Backend-only" at `…-user-visible-changes.md:35`, used as a **scoping label** inside a file that
  documents four changed pages in detail. `ui-surface-map.md` is equally accurate (it names 4 changed
  frontend surfaces at line 41 and puts the backend work under its own "Backend-Only Changes (No UI
  Impact)" heading). So the iter-33 defect — official UI documents describing a tree that no longer
  existed — did **not** recur; the gate cannot tell "this phase has no visible changes" from "here is
  the backend-only part of a phase that also has visible changes". `status.json` is `blocked` at
  `closure_failed` as a result.

## Next-Step Recommendation

Run the next iteration at **full** depth.

0. **First, before anything measures memory:** shut down process 2944679. It is holding 4.1 GB and
   serving nothing. Every remaining J-07 step is a memory measurement, and stale memory would spoil
   the readings.
1. **Then finish J-07 "Heavy aggregates never take the service down" — the only journey not passing.**
   It needs no new feature; it needs to actually be run in the browser test lane. Two concrete fixes
   make that possible: give the test agent permission to restart the backend (the auditor restarted
   it himself with the ordinary launch script, so nothing in the environment forbids it), and order
   the test plan so the tests that deliberately switch the backend off run **last** — this time they
   ran early and stranded the two tests behind them. Then record the peak-memory margin in
   `reports/perf-budgets.md`, which J-07's own text asks for and which still exists only inside the
   audit report.
2. **Then close the last unbounded whole-table load** (finding iter-36/l): a multi-date backfill still
   pulls the entire price table into memory in two places, `data_manager.py:3183` and
   `data_manager.py:3085`. This is the single thing standing between the current state and J-07's
   promise being literally true, and it is what keeps one bar-cache test red.
3. **Then the item deliberately held back this time** (iter-33/g): give the Regime Lab's cold "all
   history" view the same background handling the backtest page already has, and diagnose the reply
   that returns "success" while carrying the words "Internal Server Error". This iteration's own test
   run saw the same page push memory to within about 100 KB of the ceiling.
4. **Small, cheap, already written down:** the stale docstring at `data_manager.py:650-654` that
   describes code this iteration deleted (audit B7); the "591 symbols" figure in
   `reports/perf-budgets.md:4466` that should read 548 (audit B8); and the extra work the new batching
   adds by re-reading the candidate list from disk once per batch per date (audit B6) — worth a look
   because it is a real added cost on the cold path.
5. **Capture only, never an iteration's goal:** the `[NEW]` walkthrough steps J-07's own text names
   (a crash-free warm-up plus a healthy health check — six iterations unrecorded), and a J-06
   walkthrough of the budgets table against live page loads, which is the subject J-06's text asks for
   even though a `[NEW]` J-06 walkthrough finally exists.
6. **Framework, outside the journey loop:** the closure checker's "backend-only" regex fails any
   iteration whose change summary correctly labels its backend-only portion. It should look at whether
   the document **claims no visible changes**, not at whether the phrase appears anywhere. This is the
   second time in four iterations that a UI-impact bookkeeping check has cost a clean finish.
7. **Owner, unchanged and both still waiting:** iter-34/j — the health check's 0.1-second budget,
   which was missed again this iteration (max 132 ms over 30 quiet polls); and iter-33/i — whether
   `start-frontend.sh` should join the host-guard marker list.

The single sentence for the owner: approve one more full-depth round whose only real target is running
the J-07 test properly and removing the last whole-table memory load — everything else on this list is
small or is waiting on your decision.
