# goal-ops-hardening-iter-78 Audit Report

**Date:** 2026-08-13
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's three agent-owned items are now genuinely closed, but one of them was **not** closed
when the pipeline handed the round to this audit: DoD item 3's J-09 "background compute in flight"
walkthrough frame still captured an idle Ready-only frame (step 4) and an empty skeleton (step 5) —
the exact iter-77/e defect this iteration exists to fix — while the step's own narration asserted a
chip that was not in the picture. That is fixed and re-recorded here against a real in-flight
compute. A second, newly-introduced hazard was found in the launcher purge itself (it could `rm -rf`
a *live* server's scratch dist dir, bypassing the script's own `.trendora-serving` guard) and is
fixed with a passing regression test. The staleness tick and the launcher residue defense were
verified directly — including a live end-to-end run of the real launcher against planted residue on
the real tree — and both hold.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the residue purge could delete a LIVE server's scratch dist dir**
`incredible_auto_dev/scripts/start-frontend.sh:126` (the purge loop; pre-fix it went straight from
the own-dist-dir check to `rm -rf`). The purge excludes only *this* invocation's `$NEXT_DIST_DIR`
from the `.next-test-*` glob. Two launcher invocations pointed at **different** scratch dirs — two
overlapping runs of `test_start_frontend_script.py` on one host, which this iteration's own dev
handoff records happening ("an earlier run concurrent with my own manual pre-handoff verification…
two `next build`s racing") — therefore each classify the *other's* directory as abandoned leftover
and delete it out from under a live `next start`, tearing a running server's assets mid-flight.
That is precisely the harm the iter-77 `.trendora-serving` marker and `_dist_dir_has_live_server()`
(`start-frontend.sh:203`) exist to prevent, and the purge — which runs before that function is even
defined, and outside the build lock — bypassed it. Blast radius is confined to the `.next-test-*`
test namespace (`.next`, `.next-alt-qa`, `.next-verify` never match the glob), which is why this is
IMPORTANT rather than CRITICAL; I was unsure between IMPORTANT and GAP and took the higher level,
because the iteration's stated purpose is to *remove* a way the frontend can be taken down, not to
add one.
**Fix applied:** a `_residue_dir_has_live_server()` helper (`start-frontend.sh:98-107`) mirroring
`_dist_dir_has_live_server`'s marker read + PID-reuse cmdline guard; the purge loop now skips (and
logs) any scratch dir a live server owns. New regression test
`test_residue_purge_spares_a_scratch_dist_dir_another_live_server_is_serving`
(`apps/backend/tests/test_start_frontend_script.py:649`) plants a marked dir owned by a real live
node process **and** an unmarked sibling, runs the real launcher, and asserts the first survives
while the second is still purged — proving a narrowing, not a disable.
**Verification:** `pytest tests/test_start_frontend_script.py::test_residue_purge_spares_a_scratch_dist_dir_another_live_server_is_serving -v`
→ **1 passed in 43.61s**. AG-10 re-checked after the edit: HOST-GUARD and the `flock` BUILD LOCK
blocks are byte-identical to HEAD (programmatic block-extraction compare, both `True`).

**B2 — IMPORTANT (fixed): DoD item 3 was not met — J-09's walkthrough frame showed no compute**
`reports/phase-goal-ops-hardening-iter-78-demo.json` steps 4-5, and the frames they produced.
The spec's DoD requires "its 'background compute in flight' walkthrough frame shows the
background-compute chip (not an idle Ready-only frame)". The pre-audit `step-04.png` showed
`Ready` + `as of 3s ago` and **no** chip, under a `point_out` reading "The 'background compute
running (N)' chip in the header showing real-time work in progress"; `step-05.png` was an empty
loading skeleton under a narration describing elapsed-time and horizon counts. Both the dev handoff
and the reviewer disclosed that the engine-side timeout raise was necessary-but-not-sufficient, and
QA carried it forward as a downstream to-do — so the item shipped unmet, not silently.
Root cause was **two** things, not one (only the first was predicted): (a) step 4's `expect` was the
non-discriminating `{"text": "as-of"}`, which matches the *pre-click* page, so `_settle_for_capture`
returned instantly (`demo_runner.py:1651-1656`) and the 45000ms ceiling was never used; (b) the
trigger itself could not dispatch anything — the step clicked "Previous available date" from
2026-08-03, landing on 2026-07-31, whose forward aggregates were **already warm** at the current
dataset version (`forward_aggregate_cache`: 5/5 horizons at `r2998-f6609160`, written by this
round's own UT-06), so no background compute ever started. The execution plan flagged exactly this
("not just 'one day back'"); the implementation did not act on it.
**Fix applied:** step 4 now navigates to `/backtest?asof=2026-07-30` (cold at `r2998-f6609160` —
only 1/5 horizons, and those at an older `r2996` version) with
`expect: {"target": {"testid": "background-compute-indicator"}}`; step 5's expect becomes
`{"target": {"testid": "background-compute-active-row"}}`. This is TC-5's literal shape and the
proven session-demo pattern (`goal-session-ops-hardening-demo.json` steps 14-15).
**Verification:** demo re-recorded (`--mode record`, rc 0). `step-04.png` now shows
"background compute running (1)" beside "Ready" on `/backtest` as-of 2026-07-30; `step-05.png` shows
the Data Manager fully rendered with the same chip. The compute was genuinely in flight, not a
staged frame: `GET /api/health` sampled during the capture returned
`active: [{asof_key: "2026-07-30", dataset_version: "r2998-f6609160", elapsed_ms: 83334,
horizons_done: 3, horizons_total: 5}]`, and afterwards `recent_outcomes` recorded
`completed … duration_ms: 109090`.

**B3 — GAP: the launcher's residue defense does not cover the tsconfig entry the same residue leaves**
`incredible_auto_dev/scripts/start-frontend.sh:110-138`. Next writes a
`<distDir>/types/**/*.ts` entry into the tracked `apps/frontend/tsconfig.json` for every scratch
dist dir it builds. A hard-killed test run therefore leaves **two** artifacts, and the launcher
purges only one: I found `apps/frontend/.next-test-tc4-77-jytlrs0n/` *and* a matching
`tsconfig.json` include entry sitting in the live tree at the start of this audit (both from an
interrupted run inside this round, after the dev handoff was written — so the handoff's "frontend
tree left pristine" was true when written, and stale by the time QA finished). Verified harmless to
the build rather than assumed: the launcher run described in B-verification below built cleanly
(`✓ Compiled successfully`) with the stale include entry still present, because an `include` glob
that matches nothing is a no-op for `tsc`. The test module's own
`_scrub_tsconfig_scratch_entries()` already cleans it on its next run, which is why this is a GAP
and not a defect — the residual cost is a dirty tracked file, not a broken build. Not fixed: the
spec scoped the purge to two named artifacts and widening it is scope creep.

**B4 — OBSERVATION: purge literals are hand-duplicated across languages**
`start-frontend.sh:110-111` vs `test_start_frontend_script.py:122-123`. Already raised by the
reviewer as a NOTE, with the same suggested remedy (a self-test asserting the two literal sets stay
identical). Recording it only so it is not lost.

### Frontend Findings

**F1 — OBSERVATION: the 1-second tick re-renders every `useReadiness()` consumer app-wide**
`apps/frontend/components/readiness-provider.tsx:142-152`. `setStaleForS` fires once per second and
the context `useMemo` depends on `staleForS`, so every consumer re-renders each second — including
on pages that never render the annotation. This is inherent to putting a ticking value in a shared
context and the cost is small, but it is a real behavioral change for consumers that did not
previously re-render between polls. No fix (working implementation; not a defect).

**F2 — OBSERVATION (positive, recorded because it was the risky part): the tick cannot fabricate**
`apps/frontend/lib/staleness-tick.ts:27-36`. I traced every branch rather than trusting the
handoff. `null` (failed/not-yet-landed poll), `0` (fresh synchronous compute sentinel), negative and
non-finite bases all return **unchanged**, so `formatStaleAnnotation`'s existing null-rendering
guards keep applying to the derived value and a value that should never render can never tick its
way into rendering. The failure path also clears both refs
(`readiness-provider.tsx:124-125`), so a dead backend cannot leave a stale base quietly counting up.
Elapsed time is floored at 0, so a backwards clock cannot shrink the annotation. This is the
honesty-critical surface (AG-3) and it holds.

### Test Findings

**T1 — IMPORTANT (fixed): the QA report presented a fabricated verbatim pytest listing**
`reports/qa/goal-ops-hardening-iter-78-qa.md:37-53` (pre-correction). The "Test Details" block was
formatted as captured pytest output with 14 `PASSED` lines, but it was reconstructed, and provably
so: it named `test_concurrency_under_flock_enforces_serialization`, **which does not exist** in
`apps/backend/tests/test_start_frontend_script.py`, and omitted the real
`test_launcher_rebuilds_a_bundle_built_for_a_different_backend`. The same section's own Evidence
line concedes the tests were not run by QA at all ("Dev handoff confirms isolated run"). Downstream
agents (goal-evaluator, closure gate) read this report as evidence, so a fabricated output block is
worse than an honest second-hand citation.
**Fix applied:** the block is removed (not corrected in place — presenting it as verbatim output at
all was the defect) and replaced with an explicit second-hand attribution plus a marked correction
note. QA's PASS verdict is left intact, because the underlying claim is supportable.
**Verification:** I independently re-ran 8 of the module's 15 tests — every test that touches the
code changed this round or by this audit — all passed:
`test_residue_purge_spares_…` (1 passed, 43.61s); `test_launcher_purges_leftover_test_residue_from_a_different_process`
\+ `test_build_guard_refuses_building_into_a_dist_dir_a_live_server_is_serving` (2 passed, 88.38s);
`test_current_build_skips_rebuild` + `test_out_of_band_build_is_treated_as_stale_and_rebuilt` +
`test_scrub_tsconfig_scratch_entries_removes_only_scratch_dist_entries` (3 passed, 147.85s);
`test_concurrent_invocations_never_serve_partial_build` +
`test_launcher_rebuilds_a_bundle_built_for_a_different_backend` (2 passed, 146.81s).
`python3 scripts/automation/lib/demo_runner.py self-test` → **43 passed, 0 failed**.

**T2 — GAP (closed for this round, recipe not institutionalized): the committed tick unit test had
never actually been executed by anyone**
`apps/frontend/lib/staleness-tick.test.ts`. Dev, reviewer and QA all reported it as verified, but
dev's own honest note says `node lib/staleness-tick.test.ts` cannot run on this box (Node 22.22.1
built without type-stripping) and that the 9 assertions were checked by mirroring the function
bodies into a scratch `.mjs` — i.e. a *copy* of the logic was tested, not the shipped module. That
is below the evidence floor for "verified by a unit test" (DoD item 6). I executed the real
committed file by transpiling it with the project's own TypeScript 5.7.2:
`npx tsc lib/staleness-tick.ts lib/staleness-annotation.ts lib/staleness-tick.test.ts --outDir <tmp>
--module commonjs --moduleResolution node --target es2022 --allowImportingTsExtensions
--rewriteRelativeImportExtensions --esModuleInterop --skipLibCheck && node <tmp>/staleness-tick.test.js`
→ **9 passed**, including TC-3 (5s base + 10s elapsed → "as of 15s ago") and both TC-4 cases. Not
fixed as a standing change: adopting a transpile step for every `lib/*.test.ts` is a project-wide
convention change and out of this iteration's scope. Recommend a future round records this recipe
next to the convention so the claim stops being unverifiable on this host.

**T3 — GAP: the repaired J-09 walkthrough step is date-pinned and self-consuming**
`reports/phase-goal-ops-hardening-iter-78-demo.json:52`. Now that the capture has run, 2026-07-30's
evidence is warm at `r2998-f6609160`, so re-recording *this same JSON* against an unchanged dataset
would capture idle again. In practice any ingest/backfill bumps the dataset version and re-colds
every date, and the session-level demo has carried the same hardcoded-date pattern
(`?asof=2026-07-17`) since iter-25 — so this is the established shape, not a new weakness. Worth
solving properly with a "coldest as-of" sentinel (like the existing `{{AUTO_UNSNAPSHOTTED_DATE}}`
resolver) rather than a literal date; out of scope here.

---

## 3. Domain Assessment

The domain question this iteration turns on is **honesty about payload age**, and the core logic is
correct. `deriveLiveStaleForS` is a genuinely pure function with one job — add elapsed client
wall-clock to the server's own `stale_for_s` base — and it deliberately refuses to tick every input
that `formatStaleAnnotation` treats as unrenderable. That ordering matters: the derived value is fed
through the same single formatter, so there is exactly one place that decides whether an annotation
renders, and the tick cannot route around it. The provider's failure path clears the base *and* the
receipt anchor together, which closes the one way a live tick could have become a lie (a dead
backend with an annotation still counting up). Because the value is recomputed from `Date.now()` on
every fire rather than incremented, background-tab timer throttling degrades refresh *rate* without
ever making the displayed number wrong.

I corroborated the tick independently of QA's UT-02 measurement: within the demo re-record, the same
uninterrupted client session read "as of <1s ago" at step 4 and "as of 12s ago" at step 5 roughly
twelve seconds later, with the badge on its 30s idle cadence — the annotation advanced with real
time between polls, which is the whole behavior the round set out to ship.

The launcher work is likewise sound in its core claim. I did not take the regression test's word for
it: I planted `apps/frontend/__tc3_intentionally_broken.ts` in the **real** live tree (alongside the
pre-existing `.next-test-tc4-77-jytlrs0n/` residue I found there) and ran the real
`scripts/start-frontend.sh`. Its log records `purged leftover test-residue file:
__tc3_intentionally_broken.ts` and `purged leftover test-residue scratch dir:
.next-test-tc4-77-jytlrs0n`, then `✓ Compiled successfully` and `Ready in 307ms`, serving HTTP 200.
The failure mode that made the app unstartable in iter-77 is genuinely defended against on the real
launch path, not merely in a fixture. The one thing the defense got wrong was over-reach rather than
under-reach (B1), which the audit narrowed.

Where the round fell short was not domain logic but **evidence discipline**: the walkthrough frame
that the DoD names explicitly shipped showing the opposite of what its own narration claimed (B2),
and the QA report dressed a reconstructed list as captured output (T1). Both are now corrected, and
both are the same failure pattern the spec's own BACKGROUND section warns about — writing a claim
into an artifact of record without the artifact actually carrying the evidence.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `incredible_auto_dev/scripts/start-frontend.sh` | Added `_residue_dir_has_live_server()` and a skip-with-log branch in the purge loop, so a `.next-test-*` dir a live server is serving is never deleted (B1). HOST-GUARD + `flock` re-verified byte-identical to HEAD. |
| 2 | Important | `apps/backend/tests/test_start_frontend_script.py` | New `test_residue_purge_spares_a_scratch_dist_dir_another_live_server_is_serving` + `_TC7_78_PORT` constant; proves the marked dir survives and an unmarked sibling is still purged (B1). PASSED, 43.61s. |
| 3 | Important | `reports/phase-goal-ops-hardening-iter-78-demo.json` | Step 4 → `goto /backtest?asof=2026-07-30` (a genuinely cold as-of) with a `background-compute-indicator` testid expect; step 5 → `background-compute-active-row` testid expect (B2). |
| 4 | Important | `reports/demo/goal-ops-hardening-iter-78/step-0{1..5}.png`, `…-demo-results.md`, `…-demo-script.md` | Re-recorded the gallery; step-04/05 now show "background compute running (1)" over a verified in-flight compute (B2). |
| 5 | Important | `reports/qa/goal-ops-hardening-iter-78-qa.md` | Removed the fabricated verbatim pytest listing, replaced with an honest second-hand attribution + marked correction (T1). QA's PASS verdict left intact. |
| 6 | — | `docs/handoffs/goal-ops-hardening-iter-78-dev.md` | Appended a post-handoff audit-fix section so its "unconditional purge" and open-J-09-walkthrough claims match the shipped code. |

Working tree left clean of test residue (`__tc3_*`, `.next-test-*` and the `tsconfig.json` scratch
entry all gone — the last cleared by the test module's own scrub during my runs), and both services
left healthy on the deterministic ports (backend `http://localhost:8255/api/health` → 200, frontend
`http://localhost:3255/` → 200).

---

## 5. Recommended Next Step

Proceed to close iteration 78. Every DoD item is now met with executed evidence, including the one
that was unmet at hand-off (J-09's walkthrough frame), and the two owner-visible carries this audit
adds are small and documented: institutionalize a runnable recipe for `lib/*.test.ts` on this host
(T2) so "verified by a unit test" stops being an unverifiable claim, and replace the demo's
hardcoded cold as-of date with a resolver-backed sentinel (T3). Neither blocks closure. Everything
the spec listed as owner-blocked — `closure_gate.py:72`'s regex, `browser-qa-phase.sh`'s ordering
bug, B-1107, the 2-second health-ceiling scope, and the finish-now-vs-clear-notes decision — remains
correctly untouched and still needs the owner.
