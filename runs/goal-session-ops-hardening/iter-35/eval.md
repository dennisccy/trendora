# Iteration 35 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration built nothing. The planner wrote a full work plan (bound the price load that
eats memory; add the honest "still computing" panel to four Research lab pages), but the
engine ran the iteration in **evidence** mode, so no developer and no reviewer were ever
started. The dev note says it plainly: "no code changes were planned or made." I checked the
code myself and it is byte-for-byte the same as after iteration 34.

The browser test then measured the app against that unbuilt plan and reported two failures.
The failures are not a step backwards — nothing got worse — but they are not empty either.
They are the first live proof of two problems this session has been carrying on paper for
six iterations: during a heavy background job the backend used up every last byte of its
memory limit and gave up on four pieces of work, and four Research lab pages sat showing a
blank grey placeholder with no message while they waited. Both had been recorded as "not
seen happening yet". Now they have been seen. I moved J-06 "Pages load only what they need"
and J-07 "Heavy aggregates never take the service down" from passing to partly-passing, and
I am asking for the full pipeline next time.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | reports/qa/goal-ops-hardening-iter-35-evidence/J-01-verify.png (golden replay PASS) |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-35-evidence/J-03-verify.png (golden replay PASS) |
| J-04 Non-blocking boot with visible status | passing | passing | reports/qa/goal-ops-hardening-iter-35-evidence/J-04-verify.png (golden replay PASS) |
| J-05 Aggregates are precomputed at ingest | passing | passing | reports/qa/goal-ops-hardening-iter-35-evidence/J-05-verify.png (golden replay PASS) |
| J-06 Pages load only what they need | passing | **partial** | reports/qa/goal-ops-hardening-iter-35-evidence/J-06-phase-severity-lab.png + J-06-factor-lab.png + J-06-severity-velocity.png + J-06-regime-phase-factor.png (all four opened; all four show a bare unlabelled skeleton during a live slow load) |
| J-07 Heavy aggregates never take the service down | passing | **partial** | reports/qa/goal-ops-hardening-iter-35-evidence/J-07-result.png (opened: honest "Refreshing" banner + full evidence tables + badge "Ready · background compute running (5)"); logs/backend.log 138021-139328 (read by me: 506/506 health 200s, 4 memory-pressure aborts) |
| J-08 Backtest evidence serves from storage only | passing | passing | reports/qa/goal-ops-hardening-iter-35-evidence/J-08-verify.png (golden replay PASS; spot-checked by me — honest "Warming up — historical evidence still loading (89/89)" card) |
| J-09 Backend discloses its background-compute activity | passing | passing | reports/qa/goal-ops-hardening-iter-35-evidence/J-09-verify.png (golden replay PASS; spot-checked by me — /data coverage cards render, provider: seed) |

Merged results file: `reports/phase-goal-ops-hardening-iter-35-ui-test-results.md` (FAIL, 6/8).
Sources agree: replay lane 6/6 PASS, LLM lane 0/2, no reconciliation footer, no `DEFERRED-BUDGET`
row, no `browser-infra.json`, no `journeys-changed.md`. All 8 `spec_hash` values match
`goal_gate hash-journeys` output, so no goal text drifted.

**Coherence:** `iter-35/coherence.md` = **COHERENCE-PASS** — no structural veto. It is a
deterministic zero-change pass (the auditor was not dispatched because the product diff is empty),
not a crash-stub: the file gives that reason in full and does not contain the "Coherence auditor
produced no output" marker. I treated it as clean but drew no positive assurance from it, since
nothing was audited.

### Why J-06 and J-07 are `partial`, not `failing`

Neither journey's promise is broken, so neither is a regression:

- **J-07** — the service demonstrably never went down. I read the backend log for the one
  process myself (PID 2351049, `logs/backend.log` 138021-139328): **506 of 506** `/api/health`
  calls returned 200, zero non-200 of any kind, the process never restarted, and it kept
  answering immediately after every memory abort. The screenshot shows the honest
  "Refreshing — showing the last complete evidence … no partial or fabricated figures are
  shown" banner over complete prior-date tables. What is unmet is step 3's number: peak
  memory reached **exactly** the declared cap (6,291,456 kB = 6144 MiB), leaving **zero**
  margin where the step requires it to stay *under* the cap with the margin written into
  `reports/perf-budgets.md` — and I confirmed that file was not touched this run.
- **J-06** — all pages still load and the budget table from iteration 33 still stands
  (the code is unchanged, so that evidence is still valid). What is unmet is its
  "honest status" rule: *anything slower than its budget shows an honest progress or
  initializing state, never a frozen or blank frame*. Four Research lab pages showed a bare
  grey placeholder with no label, no elapsed-time text and no Retry button while the app was
  busy. This is the same shape that was scored a serious defect on Regime Lab at iteration 33.

### The browser test's own reasoning was narrower than mine

The browser test failed J-06 because "the iteration's own scope was not implemented" — that
is testing the plan, not the journey, and by itself it would not fail J-06. But the four
pictures it attached tell a stronger story than its words do. Its text says the four pages
"render correct data (functionally fine)". **The pictures show the opposite**: empty grey
placeholder blocks. I also checked the backend log for the same minutes and found **zero**
completed requests to any Research lab endpoint, meaning those page loads were genuinely
still waiting. The picture wins over the prose. That is why I acted on the honest-status rule
rather than on the unbuilt-plan reasoning.

### One thing the browser test missed

It reported 2 memory failures. There were **4**. The two it did not report are worse in one
respect: they happened on a page-serving path, not a background one — `/api/evidence`'s
per-claim drawdown numbers (`evidence.py:168` → `forward_testing.py:2440`). The app handled
them correctly (it marks that claim `expectations_status="unavailable"` and keeps rendering
every other claim), so no user saw a wrong number or a broken page. But it means the memory
ceiling is reachable from something a user can click, not only from a background job.

## Anti-goal Check

Basis: `iter-35/scan-report.md` = **CLEAN**; `iter-35/iter-diff.md` = "(no changes)". I did
not stop there — I re-derived the diff myself: `git diff 8233429b..HEAD -- apps scripts
project-extensions config` is empty and `git status --porcelain` over the same paths is
empty. There is no product change this iteration, so no anti-goal can have been *introduced*.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven values shown as proven | OK | No code changed. Screenshots show NA / "—" / `n=0` markers and the "not fabricated" wording intact. |
| AG-2 decision-quality only | OK | No code changed. Top bar still reads "Research-only · decision support · no orders" in every capture I opened. |
| AG-3 displayed numbers correct | OK | No code changed. The `/api/evidence` memory abort sets an honest "unavailable" marker (`evidence.py:174`) rather than a made-up number. |
| AG-4 no overfit edges | OK | No code changed; no new evidence claims (no developer ran). |
| AG-5 determinism / no-lookahead | OK | No code changed. |
| AG-6 referee gate on evidence claims | OK | No new evidence-derived claims this iteration. |
| AG-7 no hard-coded credentials | OK | scan-report CLEAN; 0 untracked files to scan; no config or env file exists in the diff because the diff is empty. |
| AG-8 resilience / no memory exhaustion | **VIOLATED — minor, unresolved (new: iter-35/k)** | Memory was genuinely exhausted: peak = exactly the cap, 4 aborts at 2 code sites (`research.py:308`; `forward_testing.py:2325`). Kept `minor` because AG-8's own remedy held — no crash, no blank page, honest NA, and the host caps contained it. Root cause is the unfixed iter-29/d whole-table load in `prices.py:131-152`. |
| AG-9 offline-deterministic ingest | OK | No manifest changed (empty diff). Every screenshot's badge reads "provider: seed". |
| AG-10 host resource ceiling | OK | Launch caps applied and proven in the boot banner (`logs/backend.log` 138019-138020: `memory_cap_mb=6144 malloc_arena_max=2`, `host-guard: cpu_list=0-3,8-11 blas_threads=4`). Marker scripts byte-unchanged. The caps did their job — the memory failures were contained inside one process; the host was never at risk. |
| License | OK | scan-report reports no license findings; diff is empty. |
| Fabricated / substituted data | OK | Verified in the J-07 screenshot: honest refresh banner, real n-counts, NA where data is thin. |

**Ledger position: 9 unresolved findings, 0 critical.** Eight carried (iter-29/b, iter-29/d,
iter-31/e, iter-32/f, iter-33/g, iter-33/h, iter-33/i, iter-34/j), each given an ITER-35 note
recording that I confirmed the code byte-identical. One new: **iter-35/k**.

**Two carried findings had their stated reason for being "minor" disproved this run** — I
recorded this in the ledger rather than leaving the old wording standing:
- iter-29/d was called minor partly because "no memory is exhausted today". Memory was exhausted today.
- iter-33/h was called minor explicitly because "no such lab is measured slow today". Four of them were slow today, and I have the pictures.

Both stay `minor` because in each case the app still behaved honestly — but they are now
proven live, not theoretical, and they are the top of the queue.

## Next-Step Recommendation

Run **iteration 36 at full depth, using the plan that was already written for iteration 35**
(`docs/phases/goal-ops-hardening-iter-35.md`). It does not need rewriting; it needs running.
It already targets exactly the two problems that were proven real today.

1. **First and biggest — stop loading the whole price table into memory.**
   `apps/backend/app/engine/prices.py:131-152` reads every row of the price table into RAM
   (about 1.5 GB) on the same path J-07 exercises. This is the direct cause of today's
   memory exhaustion and it contradicts a line the project goal states word for word.
   Prove the fix the way iteration 35's plan says: a before/after memory measurement written
   into `reports/perf-budgets.md`, and a test that fails if the fix is undone.
2. **Second — give the four Research lab pages the honest waiting message.** The shared panel
   already exists, already works, and is already switched on for one lab. Wiring it into the
   other four (Market Phase & Severity, Regime × Phase × Factor, Factor Lab,
   Severity-velocity) is mechanical. Today's four pictures are the proof it is needed.
3. **Third — write down the memory number.** J-07 asks for the peak-memory margin to be
   recorded in `reports/perf-budgets.md`. Today's reading (at the cap, zero margin, under
   five simultaneous background jobs) is written nowhere except this evaluation. Record it,
   then re-measure after fix 1 so the two numbers sit side by side.
4. **Also worth a look, cheap:** the evidence page's per-claim drawdown calculation builds one
   unbounded lookup in memory (`forward_testing.py:2325`). It failed twice today. It is a
   small, contained fix in the same family as item 1.
5. **Carried, unchanged:** iteration 33's Regime Lab background-dispatch item and its
   undiagnosed error-body; `warmup.py:194`; iter-31/e; iter-32/f (watch only).
6. **Capture-only ride-alongs, never a goal of their own:** the demo recorder produced an
   empty recording this run (zero steps), so the walkthroughs J-06 and J-07 ask for are still
   missing — the fifth iteration in a row.
7. **For the owner, unchanged and still open:** the `/api/health` 0.1-second budget question
   (iter-34/j) and whether the frontend launch script should join the host-guard list
   (iter-33/i). Neither blocks the work above.

**One sentence for the owner:** the last run built nothing because it was started in the wrong
mode, so please let it run again at full depth with the plan that is already written — the
one real problem it uncovered (the app using up all its memory during heavy background work)
is exactly what that plan was designed to fix.

## Process Note (not a journey finding)

The iteration spec's own metadata says `Depth: full` and its Definition of Done lists code
work, but `iter-35/depth-dispatched` reads `evidence` and only two pipeline steps ran
(`decomposer`, `browser-qa`). The previous evaluator recommended full depth. An
evidence-depth run means "capture pictures of things that already work" — it should not be
paired with a spec that requires building something, because the test lane will then measure
the app against work nobody was asked to do. Worth a look at how the depth was chosen, since
this cost a whole iteration.
