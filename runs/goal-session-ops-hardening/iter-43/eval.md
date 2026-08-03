# Iteration 43 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The owner raised the memory limit, and that decision worked: the heavy background calculation ran for
about 17 minutes and its memory use stayed completely flat at about one third of the new limit. The
job that could not even start last round now starts, runs and finishes honestly, so J-05 "Aggregates
are precomputed at ingest" is no longer broken. But J-05 was tested on a day that had already been
saved, so the part of the journey that matters most — bringing in a brand-new day of data — was never
actually tried, and I score it part-done rather than working. J-07 "Heavy aggregates never take the
service down" fails again: while a heavy calculation was running the app stopped answering completely
for several minutes, and separately 64 of every 100 health checks were slower than the owner's new
2-second promise. The cause changed — last round the app ran out of memory, this round it had plenty
of memory and simply got stuck — so the raised limit fixed the old problem and uncovered a different
one underneath it.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | reports/phase-goal-ops-hardening-iter-43-ui-test-results.md:18 · reports/qa/goal-ops-hardening-iter-43-evidence/J-01-verify.png |
| J-03 No per-run range cap | passing | passing | ui-test-results.md:19 · reports/qa/goal-ops-hardening-iter-43-evidence/J-03-verify.png (byte-identical to J-04's frame — see Anti-goal check) |
| J-04 Non-blocking boot with visible status | passing | passing | ui-test-results.md:20 · reports/qa/goal-ops-hardening-iter-43-evidence/J-04-verify.png (I opened it: badge Ready, "provider: seed", "seed 2026-07-22") |
| J-05 Aggregates are precomputed at ingest, never on the fly | regressed | **partial** | ui-test-results.md:24 (row PASS) · reports/qa/goal-ops-hardening-iter-43-evidence/UT-J-05-result.png (I opened it) · reports/phase-goal-ops-hardening-iter-43-ui-test-results.llm.md:80-124 |
| J-06 Pages load only what they need | passing | passing | ui-test-results.md:21 · reports/qa/goal-ops-hardening-iter-43-evidence/J-06-verify.png |
| J-07 Heavy aggregates never take the service down | failing | failing | ui-test-results.md:25 (row FAIL) · ui-test-results.llm.md:22-57, :140-153 · reports/perf-budgets.md "Iteration 43" §5 · docs/handoffs/goal-ops-hardening-iter-43-audit.md B1/B2 |
| J-08 Backtest evidence serves from storage only | passing | passing | ui-test-results.md:22 · reports/qa/goal-ops-hardening-iter-43-evidence/J-08-verify.png |
| J-09 The backend discloses its own background-compute activity | passing | passing | ui-test-results.md:23 · reports/qa/goal-ops-hardening-iter-43-evidence/J-09-verify.png (I opened it: green "background compute running (1)" chip present) |

Deferred (`DEFERRED-BUDGET`): none. No `browser-infra.json`. No `journeys-changed.md`; all eight
`spec_hash` values match `goal_gate.py hash-journeys docs/goal.md` run by me, so the owner's
2026-07-31 goal amendment did indeed leave every journey's text untouched, as it claimed.

**Why J-05 is `partial` and not `passing`, stated plainly.** The row says PASS and the repair is real:
job 258 started 13:10:59 UTC, reached terminal `ok` at 13:16:25 UTC (325.4 s), `/scanner-runs/1882`
rendered "as of 2005-04-12" with a full 152-row leaderboard instantly, the badge stayed Ready, the run
record's "Refreshed:" line named forward aggregates, and 16 of 16 health polls answered in
0.118–1.678 s. Three gaps stop it short, each disclosed by the browser-QA lane itself: (1) J-05 step 1
requires an **unsnapshotted** trading day, and 2005-04-12 was already snapshotted (run id 237, scanned
2026-07-30) — the job created 0 snapshots, so the ingest→fresh-aggregates half was never exercised,
and the developer's own attempt at the genuinely-new-data case ran 1,001 s without finishing;
(2) the restart + cold `/data` steps were not run against this job; (3) J-05's own "no code path
streams the full `daily_prices` table into RAM" clause is knowingly unmet, since the owner-commissioned
revert restores the unfiltered whole-table scan. `evidence_makeup: true` is set: the confirmed
behaviour was never captured in a frame that shows it.

**Stable-journey spot-checks (2, as required).** I opened `J-03-verify.png`/`J-04-verify.png` (one
frame, two journeys) and `J-09-verify.png`. Neither contradicted its recorded status, so I did not
widen to a full walk. `J-09-verify.png` also gave me the trigger for this iteration's outage
first-hand: it shows a live background compute at 13:53, minutes before the process hung.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (no unbacked "proven" claims) | OK | No evidence claims added; the diff is 9 backend/tooling/script files with no UI or ledger surface. |
| AG-2 (decision-quality only) | OK | No return promise, price target, signal, or order path in any changed file. |
| AG-3 (displayed numbers correct) | OK | The only serving-shape change is `_run_detail` preferring `prog.message` on a terminal `failed` row; the auditor traced all three callers and proved it a no-op on every pre-existing path (B5), and the coherence audit reached the same conclusion independently. The coverage figures in the frames I opened (540 / 122 / 591 / 5383 / 1920) are consistent across all four captures. |
| AG-4 (no overfit edges) | OK | No new claim, no referee surface touched. |
| AG-5 (determinism / no lookahead) | OK | The prefill revert is proven byte-identical to the pre-iter-42 body by a dedicated oracle test; reviewer and auditor each independently re-ran `test_bar_cache.py` 22/22. |
| AG-6 (referee gate) | OK | No evidence-derived claims this iteration. |
| AG-7 (no hard-coded credentials) | OK | `iter-43/scan-report.md`: CLEAN — no secret, dependency, or license findings on added lines. |
| AG-8 (resilience; no unbounded whole-table loads) | **VIOLATED — minor, open (iter-43/af)** | The service was fully connection-refused for several minutes under a stalled background compute (`horizons_done: 0/5` after 137 s; uvicorn alive at 82-98% CPU, hung mid-shutdown; needed `kill -9`). New mechanism, not iter-42's: VmPeak was flat at 32.4% of the raised cap, so this is a stall, not memory exhaustion. Separately the whole-table `_BarCache.prefill` scan is restored by owner direction (carried iter-29/d, "compression not a bound", 13th iteration). |
| AG-9 (offline-deterministic ingest) | OK | No manifest change and no new dependency (scan-report CLEAN); dev handoff records no new adapter, scraper, or external API. |
| AG-10 (host resource ceiling) | OK — **strengthened** | I checked both halves myself: `project-extensions/host-guard/host-guard.env:89` now lists all three launchers, and `incredible_auto_dev/scripts/start-frontend.sh:28-58` carries a HOST-GUARD marked block (`scripts` is a repo symlink to `incredible_auto_dev/scripts`, so spec path and diff path are one file). `git diff 9165b2ea..HEAD` over `config.yaml`/`docs/goal.md` is empty — the 8192 MB cap is the owner's own committed value, untouched here. No cap removed, weakened, or bypassed. |
| Framework honesty rail | **VIOLATED — minor, open (iter-43/ah)** | The QA report records `**Verdict:** PASS`, marks TC-8 PASS on another criterion's evidence, and says "No blockers to shipping" — written 32 minutes before the browser lane returned FAIL on a target journey, and while `status.json`'s own `blockers[]` was populated (audit T1; I verified all three sites). |
| Framework evidence rail | **VIOLATED — minor, open (iter-43/ai)** | My own `md5sum`: `UT-J-05-result.png` == `UT-J-07-fail.png`, and `J-03-verify.png` == `J-04-verify.png`. One generic capture is cited as evidence for a PASS row and a FAIL row at once (audit T3). |
| "Zero silent zero-work jobs" | Violated then **resolved in-audit** (iter-43/aj) | The new launch guard caught `RuntimeError` only; the auditor live-proved `MemoryError` — the sibling exit of the same CPython path, and one iter-42 actually produced — still orphaned the job at `running` with no run-history row at all. Both guards now catch `Exception` and always re-raise; the two 503 mappings widened. Regression-tested (audit B3). |

Ledger after this iteration: **48 total, 15 unresolved, 0 critical.** Three items closed: **iter-33/i**
(`start-frontend.sh` host-guard — owner item, done and verified by me), **iter-34/j** (the
`GET /api/health` budget — the owner has now rescoped rather than waived it, so the *decision* is
settled; its first measurement's failure is filed separately as iter-43/ag), and **iter-42/ac** (the
+5.1% prefill regression — reverted, oracle-tested, and the post-revert VmPeak is flat).
Coherence: **COHERENCE-PASS**, zero blocking, zero advisories. Review: PASS_WITH_NOTES (2 MINOR).
QA: PASS (over-claimed — see iter-43/ah). Audit: PASS_WITH_GAPS. ux-regression: SKIPPED (budget-shed).
Closure: CLOSURE-PASS — returned over a merged file whose own headline reads `Browser QA Verdict: FAIL`.

## Next-Step Recommendation

Full depth again, and the order matters. **(1) Stop the app from going silent when a heavy
calculation gets stuck.** This is the one thing that took the service down this round and there is a
ready lead nobody has followed: the backend start script launches its web server with no shutdown
time limit, so a stuck job holds the whole app hostage forever. Give shutdown a deadline, and make a
calculation that stops making progress give up and say so instead of freezing. **(2) Find out why the
calculation stalled at zero of five horizons after 137 seconds** — the thread-dump tool for exactly
this was put in place three rounds ago and has still never been used on a live freeze. **(3) Re-test
J-05 "Aggregates are precomputed at ingest" on a day that has NOT been saved before**, which is what
the journey actually asks for; this round used an already-saved day, so the important half was never
tried. **(4) Deal with the slow health checks**: 64 of every 100 were over the owner's new 2-second
promise and getting worse. The suspect is a known slow price-reading path from two rounds ago; either
measure it cleanly on its own (one trigger, no side probes) or fix it. **(5) Small and already
written down:** make a failed job's saved message name the real reason instead of a generic summary
(reviewer MINOR); give the Retry button the same honest error code as its two siblings (audit B4);
drop the stray editor-config change that rode along in the frontend (audit F1). **(6) Fix how
evidence is captured** — two pairs of screenshots this round were the same file, one of them serving
as proof for both a pass and a failure. **(7) Carried, untouched:** iter-29/b and the badge wording
after a permanently failed warm-up (FIFTEEN rounds unmade); iter-31/e; iter-32/f; iter-35/k;
iter-36/n; iter-37/o; iter-37/q; iter-39/u. **(8) Deferred a NINTH time:** iter-33/g, Regime Lab's
cold pooled view. **(9) Capture only, never a round's goal:** J-07's `[NEW]` walkthrough (thirteenth
round unrecorded) and J-05's real acceptance frames. **In one sentence: the next round should make
the app stay reachable when a background calculation hangs, then re-test the "new day of data" case
that was skipped this time.**
