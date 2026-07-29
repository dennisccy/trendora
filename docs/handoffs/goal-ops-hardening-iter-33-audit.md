# goal-ops-hardening-iter-33 Audit Report

**Date:** 2026-07-29
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's central claim survives independent verification: `scripts/start-frontend.sh` genuinely
serves production mode (I re-launched it myself — the process bound to :3255 resolves through its own
ancestry to `sh -c next start -p 3255`, the served HTML carries zero dev-client/HMR markers, and the
skip-rebuild branch fired correctly), and the J-06 sweep in `reports/perf-budgets.md` is a real
Navigation-Timing browser measurement, not the curl proxy the QA report's own summary table makes it look
like. Three evidence-integrity defects were found and fixed during this audit: the QA report reported a
warm health latency (0.0927 s) as a "fresh boot-to-health reading" that the measurement artifact itself
says was never taken; TC-4's fresh boot-to-health deliverable was therefore missing (I measured it:
**1.325 s**, inside the ≤5 s budget); and the merged browser-QA artifact the goal-evaluator reads still
carries a pre-fix `FAIL` headline that contradicts the shipped code. Real remaining limitations — the
60–90 s cold compute itself, the sibling labs' identical unlabelled-skeleton shape, and the pipeline's
failure to regenerate UI artifacts after a fix-mode round — are documented, not hidden.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no change needed): no backend code path changed, so AG-8 is satisfied structurally**
`git diff --stat` over `apps/backend/app` is empty; the only backend-tree file added is the test module
`apps/backend/tests/test_start_frontend_script.py`. AG-8's "no new unbounded scan" therefore cannot have
been violated by this iteration. I spot-verified the two load-bearing rows of the dev handoff's on-load
audit against the real code rather than accepting the table: `compute_availability`
(`apps/backend/app/engine/data_manager.py:1181-1198`) is the single grouped pass the handoff discloses,
and `resolved_forward_aggregate_evidence` (`apps/backend/app/engine/forward_testing.py:1737-1745`) does
document itself as "structurally incapable of calling `compute_forward_aggregates`" with no
compute-fallback branch. The handoff's audit table is accurate where I checked it.

**B2 — GAP (not fixed, out of scope): the 60–90 s cold compute is per-`dataset_version`, and its one
observed "Internal Server Error" remains undiagnosed**
`regime_lab_cached` (`apps/backend/app/engine/research.py:3509-3559`) caches into the persisted
`EventStudyCache` table keyed by `(subject, view, asof_key, dataset_version+schema token, horizon)`. I
confirmed the practical consequence live: after a **fresh backend boot** (cold process, warm DB)
`GET /api/research/regime-lab?view=pooled` answered **200 in 49.4 ms**, so the 60–90 s wait recurs once
per dataset version, not once per restart. That materially narrows the CRITICAL WARN's blast radius, and
I have recorded it in `reports/perf-budgets.md` so the next iteration does not over-scope a fix. The
request thread still blocks for the whole cold compute (no background dispatch, unlike iter-32's
`/api/backtest` path), and QA's single observed `"Internal Server Error"` under two concurrent cold
computes of the same key is disclosed-but-undiagnosed by the developer. Both are real, both are outside
this iteration's declared scope ("Backend: None"), and both belong in a future iteration's spec.

### Frontend Findings

**F1 — IMPORTANT (fixed, evidence-only): TC-4's "fresh ≤5 s boot-to-health reading" was never taken, and
the QA report presented a warm request latency as that reading**
`reports/perf-budgets.md` (Iteration 33 section) states honestly: "A fresh, precisely-timestamped backend
restart was NOT performed this pass". `reports/qa/goal-ops-hardening-iter-33-qa.md` nonetheless recorded
"**Boot-to-health (fresh ≤5s reading):** 0.0927s (well within budget)" — that number is the dev handoff's
warm `GET /api/health` curl (0.092 s), not a boot measurement, and it made a missing deliverable look
complete. Fixed two ways: (a) I took the real reading — both services were down when the audit began, so
this was a genuine cold start through `scripts/start-backend.sh`, wall clock captured immediately before
launch and `/api/health` polled at 100 ms until the first 200: **1.325 s**, inside the ≤5 s budget and
consistent with iter-30's 1.354 s; (b) both artifacts now carry the correction (see section 4).

**F2 — IMPORTANT (fixed, evidence-only): the merged browser-QA artifact still declares `FAIL` for code
that no longer ships**
`reports/phase-goal-ops-hardening-iter-33-ui-test-results.md` (12:35) has headline `FAIL` and UT-11 FAIL;
the fix landed at 12:48–12:49 and no lane regenerated the file. The goal-evaluator reads exactly this
file, so the iteration's own evidence trail contradicts itself — the mirror image of the laundering
failure this iteration's `_ROW_RE` fix was written to prevent. The ux-regression reviewer flagged the same
staleness (`reports/phase-goal-ops-hardening-iter-33-ux-regression.md`, "Pipeline-artifact staleness"); I
confirmed it independently by mtime and by reading the shipped source. Fixed by appending an attributed
reconciliation note; **the headline and the UT-11 row are deliberately left untouched** — rewriting a
recorded FAIL as PASS without re-executing the browser lane is precisely the shape this project has been
burned by (iters 9/12). I verified afterwards that the file still parses to exactly one
`**Browser QA Verdict:**` line and 22 rows with `UT-11` still the only FAIL.

**F3 — OBSERVATION (no change needed): the UT-11 fix itself is correct, surgical, and verified end to end**
I traced it rather than trusting the handoff. `apps/frontend/lib/lab-load-panel.ts:45-52` cannot return an
unlabelled skeleton past the grace window; `apps/frontend/app/research/_labs.tsx:4231-4271` wires it, and
critically the retry path re-enters `setState({kind:"loading"})` at line 4233 because `attempt` is in the
effect's dependency list (4240) — so clicking Retry gives immediate feedback rather than leaving the error
card frozen for another 90 s, which is the obvious way this kind of fix goes wrong. `ResearchError`'s
`onRetry` is optional and the button is conditionally rendered (`_labs.tsx:186-196`), so the three
untouched call sites are byte-identical. I re-ran the 13 resolver unit tests myself (the reviewer could
not — Node 22.22 rejects the `.ts` import; I compiled with `tsc` into a scratch dir and executed:
**13 passed**), and I opened both fix screenshots: `UT-11-fix-computing-notice.png` shows
"Still computing — 6s elapsed" with the honest explanatory copy above the skeleton, and
`UT-11-fix-error-retry.png` shows the "Backend unavailable" card with a real Retry control. This fix also
directly serves J-06's own acceptance clause ("anything slower than its budget shows an honest progress
or initializing state, never a frozen or blank frame") — it is goal-aligned work, not scope creep.

**F4 — OBSERVATION (no change needed): the launcher is a genuine prod-mode serve with no fallback path**
`incredible_auto_dev/scripts/start-frontend.sh:28-66`. `git diff` confirms lines 1-27 (port detection,
`NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_API_PORT`) are byte-unchanged; only the final `exec` line was replaced.
The staleness test is `BUILD_ID`-based, not directory-existence-based (line 41), which is the one design
detail that makes a dev-mode `.next` correctly read as stale. On build failure it prints the build's own
output and exits 1 with no `next dev` fallback and no stale serve (lines 56-60). My own live run took the
skip-rebuild branch and reached `✓ Ready in 284ms`; ancestry resolution gave
`next-server (v15.1.3)` ← `sh -c next start -p 3255` ← `npm exec next start -p 3255`, and the served HTML
contains zero `hot-update`/`webpack-hmr`/`__nextDevClientId` markers. All 11 J-06 pages answered 200
(7.2–11.0 ms server time).

**F5 — GAP (not fixed, spec-excluded): `next build` now runs from an automated launcher with no
host-guard cap of its own**
`start-frontend.sh` is not in `HOST_GUARD_MARKER_FILES` (`project-extensions/host-guard/host-guard.env`:
`"scripts/dev.sh scripts/start-backend.sh"`), and the spec explicitly rules expanding that out of scope.
The behaviour change is nonetheless real: before this iteration the automated lanes (`qa-phase.sh:82-83`,
`demo-phase.sh:170-171`) started a lazily-compiling `next dev`; now they can trigger a full multi-worker
production build on a host whose caps exist because of two hardware resets under all-core bursts (AG-10).
Mitigating and worth recording: the pipeline shell itself already inherits the host-guard affinity mask —
`taskset -cp` on my own shell returned `0-3,8-11`, matching `HOST_GUARD_CPU_LIST` — so a build launched
from these lanes inherits the mask in practice. Not raised higher because the spec considered and excluded
it deliberately, and because the letter of AG-10 is keyed to the marker files. Recommend iteration 34+
decide explicitly rather than leaving it implicit.

**F6 — GAP (not fixed, carried): sibling research labs keep the exact shape UT-11 just proved defective**
`/research/phase-severity-lab`, `/research/regime-phase-factor`, `/research/factor-lab` and
`/research/severity-velocity` still render a bare `LabSkeleton` with no labelled state and no Retry. The
developer disclosed this honestly and the ux-regression reviewer flagged it; `resolveLabLoadPanel` is
already generic and exported, so the remaining work is wiring. Correctly out of scope for a fix-mode round
(only UT-11 was blocked), but it is one slow measurement away from reproducing the same P1.

**F7 — OBSERVATION (no change needed): the staleness scan does not prune sibling scratch dist dirs**
`start-frontend.sh:48-50` prunes only `./node_modules` and `./$DIST_DIR`. The checkout also contains
`.next-alt-qa`, `.next-iter25` and `.next-verify` (and this iteration's tests create `.next-test-*`). If a
future verification build writes into any of them after the real `.next` was built, the next default
launch sees a "newer source file" and does one gratuitous full rebuild. The failure direction is safe (an
extra build, never a stale serve), and today it does not fire — my live run correctly logged
"skipping rebuild". Recorded so a future operator does not spend time on the mystery.

### Test Findings

**T1 — OBSERVATION (no change needed): the launcher smoke tests are tight, not loose**
`apps/backend/tests/test_start_frontend_script.py`. TC-1 asserts the build branch was taken *and* a
`BUILD_ID` was produced *and* the socket owner resolves to `start` (lines 362-377). TC-2's skip-rebuild
proof is genuinely falsifiable: it compares `BUILD_ID`'s mtime in nanoseconds (line 420) under a separate
short 120 s start timeout (line 417), so a rebuild it exists to catch cannot pass silently by hiding
inside the 900 s build ceiling. TC-3 asserts a non-zero exit, the script's own failure message, *and* the
build's own TypeScript error text (lines 458-467), so a swallowed failure fails the test. The setup-time
`_purge_test_residue()` (lines 114-126, 138) is the right fix for SIGKILL-proof cleanup and is keyed to
this module's own names, so it cannot touch the real `.next`. I did not re-run these (the reviewer already
re-ran all three: 3 passed ~130 s, and separately planted simulated hard-kill residue to prove the purge)
— re-running them would mean two more full production builds on a shared host for no new information.

**T2 — OBSERVATION (no change needed): `merge_ui_test_results.py`'s fix is real and its new case is a true
RED-before test**
`_ROW_RE` is now `^\|\s*((?:UT|TC)-[^|]+?)\s*\|(.*)\|\s*$` (line 40) and `t_tc_prefixed_fail_survives`
(lines 280-300) merges a TC-only input whose headline is FAIL and asserts the merged headline is still
FAIL plus the row survives into "## Failed Tests" — against the old `UT-`-only regex `parse_rows` returns
`[]`, so the case genuinely fails before the fix. I ran the self-test myself: **7 passed, 0 failed**. The
residual behaviour worth naming: a file-level FAIL headline still loses to later-wins row verdicts when
rows *do* parse (`compute_overall`, lines 95-110). That is the documented, intended design (a replay FAIL
the LLM later re-confirms as PASS must not stick), and the spec's own wording scopes the requirement to
the parse-failure path, so it is not a gap.

**T3 — OBSERVATION (fixed by note, see F1/F2): the QA report's summary tables misdescribe their own
evidence**
Two places, neither affecting a verdict: TC-04's table is headed "Curl Latency (ms)" with seven pages
marked "Verified via curl", which reads as though the iteration measured what the spec forbids — the real
browser numbers (`domInteractive`/`loadEventEnd` from `performance.getEntriesByType('navigation')`) are in
`reports/perf-budgets.md`, so the sweep is genuine and only the QA summary undersells it. TC-02's note
("Startup completes in 42.24s … significantly faster than TC-01 (21.45s)") is arithmetically incoherent —
those are whole-test durations for a two-invocation test versus a one-invocation test, not build times.
Reporting quality only.

**T4 — GAP (not fixed): the post-fix regression evidence in the artifact trail is the developer's own
self-report; I replaced it with an independent run**
`reports/phase-goal-ops-hardening-iter-33-regression-replay-results.md` (6/6 PASS) was written at 11:52,
before the 12:49 UI change; the only post-fix replay on record was the developer's own dry run. Because
`_labs.tsx` is shared by every research route and J-06's golden script visits `/research/event-study`, I
re-ran the deterministic replay myself against the live prod-mode frontend:
**7/7 PASS, 0 failed** (J-01, J-03, J-04, J-05, J-06, J-08, J-09; evidence written to the audit scratch
dir, summarized in the reconciliation note I added to the merged UI results file). The artifact on disk is
still the pre-fix one — regenerating pipeline artifacts is the pipeline's job, not the auditor's.

---

## 3. Domain Assessment

The domain question this iteration answers is narrow and it answers it correctly: *were the page-load
numbers this session has been quoting measured against the product, or against a dev server?* They were
measured against a dev server, and now they are not. The fix is the right shape — a `BUILD_ID`-keyed
staleness check rather than a directory-existence check is what distinguishes a dev cache from a
production build, and refusing to serve on a failed build is the honest failure mode. The measurement it
unblocked is credible: ten of eleven pages under 100 ms `loadEventEnd`, on-load endpoints inside the 1.5 s
budget, and the two over-budget readings disclosed rather than dropped.

On the honesty axis the iteration is mostly strong and once weak. Strong: `reports/perf-budgets.md`
explicitly says the fresh boot reading was not taken instead of inventing one, and it publishes the
regime-lab cold-compute finding as CRITICAL even though the warm re-read looked clean. Weak: the QA
report then converted that same missing reading into a passing number, and the merged browser-QA artifact
still tells a reader the iteration failed. Both are downstream-of-the-work reporting defects rather than
product defects, but the goal-evaluator consumes exactly those files, so they matter — hence the fixes in
section 4.

One domain nuance worth carrying forward: the regime-lab cold compute is cached in the DB, not in process
memory. The evaluator should not carry "every restart re-exposes a 60–90 s stall" into iteration 34's
scoping — the correct framing is "every dataset-version change re-exposes it, once, to whoever visits
first, and that visitor now sees an honest labelled wait with a way out."

---

## 4. Fixes Applied During This Audit

All three are evidence-integrity fixes; no product code was touched by this audit (`git diff` over the
three files shows insertions only, zero deletions).

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/perf-budgets.md` | Appended "Iteration 33 — auditor addendum": the fresh boot-to-health reading the sweep deferred (**1.325 s**, ≤5 s budget, PASS), plus `GET /api/health` at rest (**93.4 ms**, inside the ≤0.1 s budget — evidence the standing WARN is contention, not a code regression), the independent prod-mode proof (socket-owner ancestry + zero HMR markers), all 11 pages' server response times, and the post-fresh-boot regime-lab read (49.4 ms) establishing the cache is DB-persisted. Explicitly labelled as *not* browser measurements so it cannot be mistaken for a second TTI sweep. |
| 2 | Important | `reports/qa/goal-ops-hardening-iter-33-qa.md` | Added an attributed correction under TC-04's boot-to-health line: the 0.0927 s figure is a warm request latency, not a boot reading; the real measurement is 1.325 s. Verdict lines untouched. |
| 3 | Important | `reports/phase-goal-ops-hardening-iter-33-ui-test-results.md` | Added an attributed reconciliation note: this merged file predates the fix-mode round, UT-11's defect was fixed at 12:48–12:49 and re-verified (13 unit tests re-run green, both fix screenshots inspected, source read), the cold compute itself is unchanged, and an independent 7/7 golden replay found no regression. Headline and UT-11 row deliberately left as recorded. |

**Post-fix self-verification.** Fix 3's risk is breaking the machine-readable contract of a generated
file, so I re-parsed it with the module that consumes it:
`merge_ui_test_results.parse_rows`/`file_top_verdict` still return exactly **one** `**Browser QA Verdict:**`
line (`FAIL`), 22 rows, `UT-11` still the only FAIL — my prose lines are not row-shaped and cannot be
mis-parsed. `merge_ui_test_results.py self-test` re-run: **7 passed, 0 failed**. Fixes 1 and 2 assert only
numbers I produced myself in this session (boot 1.325 s; health 93.4 ms; 49.4 ms regime-lab; launcher log
`skipping rebuild` → `Ready in 284ms`; ancestry `sh -c next start -p 3255`), each reproducible from the
commands quoted in this report. `git diff` over all three files: insertions only.

**Live services left running** (both were down when this audit started, and I started them through the
project launch scripts): backend `:8255` — my boot banner in `logs/backend.log` shows the HOST-GUARD block
applied at runtime (`port=8255 memory_cap_mb=6144 malloc_arena_max=2`, `host-guard: cpu_list=0-3,8-11
blas_threads=4`) — and frontend `:3255` in genuine `next start` production mode.

---

## 5. Recommended Next Step

Proceed to iteration 34 as the spec already plans (J-07's health-latency recording and the
induced-memory-pressure drill), with three carried items folded into its scoping:

1. **Decide the regime-lab cold compute explicitly.** The honest-wait UX is shipped and satisfies J-06's
   acceptance clause, but the 60–90 s first read per `dataset_version` and the undiagnosed
   `"Internal Server Error"` under two concurrent cold computes of the same key are real. Warming
   `regime_lab_cached` on an ingest finalize hook is the durable remedy and is the same shape as this
   session's existing "precompute at ingest, never on the fly" contract (J-05) — treat it as a J-05-style
   backend item, not a UI item.
2. **Regenerate UI artifacts after any fix-mode round that ships UI**, or teach the evaluator to prefer
   the later QA verdict. My reconciliation note patches this instance; the pipeline gap that produced it
   is still open and will recur on the next fix-mode round (the ux-regression reviewer filed the same
   recommendation).
3. **Decide the frontend-build host-guard question on the record** (F5): either add `start-frontend.sh` to
   `HOST_GUARD_MARKER_FILES` with a build-step cap, or document the exemption as deliberate now that an
   automated lane can trigger a full production build.

Also worth one line in the next spec: my at-rest `GET /api/health` reading of 93.4 ms is *inside* the
≤0.1 s budget, which is new information for the owner's standing budget-amendment decision — the endpoint
appears to breach only under concurrent browser-automation load.
