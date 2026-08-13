# goal-ops-hardening-iter-77 Audit Report

**Date:** 2026-08-13
**Auditor:** Hard audit pass — skeptical, evidence-based (second pass, after the developer's fix-mode
response to this audit's earlier FAIL)

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's goal — restore the code lane after two empty-diff rounds — was achieved: all six planned
items landed as real, independently checkable code, and the round's own headline capability (`stale_for_s`
disclosed on the readiness badge and preflight banner, with the "Ready" pill no longer hidden at 1280×800)
is verified live in captures I opened myself, not on a handoff claim. The fix pass also converted the
previous audit's B1 from an asserted root cause into a demonstrated one with a mechanical guard, which I
re-probed branch-by-branch first-hand.

One CRITICAL defect existed in the delivered state and is fixed in this pass: the working tree shipped a
stray intentionally-broken TypeScript file that made `next build` fail, so the very next
`scripts/start-frontend.sh` launch would have refused to serve a frontend at all (§2/B1 — both services
were already down at audit time). Two IMPORTANT gaps remain unfixed and are documented rather than
papered over: the same test module can re-create that residue whenever it is interrupted (B2), and the
merged browser artifact of record still reads `BLOCKED` with three target journeys marked "no test case
executed" while the QA report headline reads PASS (T1).

---

## 2. Findings

### Backend / Launcher Findings

**B1 — CRITICAL (fixed): the delivered tree could not be built, so the launcher would have refused to
start the frontend**

`apps/frontend/__tc3_intentionally_broken.ts` (mtime 16:01:49, i.e. AFTER the launcher's own 15:56:38
build) was present in the delivered working tree. It contains
`const __trendora_test_tc3_broken__: string = 12345;` — a deliberate type error.

Full chain, each link executed by me rather than reasoned about:

1. `incredible_auto_dev/scripts/start-frontend.sh:230-235` decides staleness with
   `find . \( -path ./node_modules -o -path ./$DIST_DIR \) -prune -o -type f -newer "$BUILD_ID_FILE" -print -quit`.
   Running that exact command returned `./__tc3_intentionally_broken.ts` → the build is classified STALE.
2. Stale ⇒ line 239 runs `next build`. Next type-checks the whole project on a production build
   (`next.config.mjs` sets only `eslint.ignoreDuringBuilds`, never `typescript.ignoreBuildErrors`). I ran
   the real build (`NEXT_DIST_DIR=.next-verify NEXT_PUBLIC_API_URL=… npx next build`): **rc 1**,
   `./__tc3_intentionally_broken.ts:3:7 Type error: Type 'number' is not assignable to type 'string'.`
3. `start-frontend.sh:240-245` then prints "next build FAILED … refusing to fall back to 'next dev' or
   serve a stale build" and `exit 1`. No frontend at all.

This was not hypothetical at handoff time: `curl localhost:3255` and `curl localhost:8255/api/health` both
returned `000` during this audit — the stack was already down, so the next launch was the failing one.

Cause: `apps/backend/tests/test_start_frontend_script.py:533` (TC-3) writes that file into the LIVE
frontend source tree on purpose. Its autouse `_pristine_frontend_tree` fixture (line 167) purges at setup
*and* teardown, precisely because "a SIGKILLed pytest runs no teardown" — and that is what happened: the
QA lane's own report records "The backend test suite times out in the QA environment (2-minute Bash tool
limit)", so its run was killed mid-module and the teardown never ran.

**Fix applied:** deleted the residue file (untracked; no tracked file touched).
**Verification:** the same real production build now exits **rc 0** (full 29-route build, complete type
check); live `.next/BUILD_ID` byte-identical before and after (`af0fd50be9a7e985cadd29fbbf350baf` =
`GleH8MCVrnujj2tbsXxOO`); `apps/frontend/.next-verify` restored to HEAD and its untracked build residue
cleaned, so `git status` for that path is empty.

**B2 — IMPORTANT (gap, not fixed): the residue in B1 can recur on any interrupted run of that module**

The self-healing in `_pristine_frontend_tree` only fires on the *next* pytest run of that module. Nothing
in the launch path is defended: between an interrupted run and the next pytest invocation, the live
frontend is unbuildable, and the only symptom is a launcher `exit 1`. This round is the proof — an
11-minute module was dispatched into a 2-minute-limited lane.

Not fixed here because every candidate remedy is a design choice with a real trade-off, not a surgical
edit: excluding `__tc3_*` in `tsconfig.json` would defeat TC-3's own assertion (the build must fail);
moving the broken file outside the project would too; the cleanest fix is a lane-level rule (never run
`test_start_frontend_script.py` under a short-timeout tool, or run it with an explicit
`--timeout`/setsid wrapper as the pump lessons already prescribe). Recommend the owner/next round pick one
rather than an auditor imposing it inside a fix diff.

**B3 — OBSERVATION: the shipped `flock` closes a race that was never shown to be the iter-72/c cause**

The DoD item ("named cause and a regression test, or definitively ruled out") is satisfied — but by the
*second* cause, not the first. The original hypothesis (two concurrent `start-frontend.sh` invocations
racing one dist dir) is still asserted from code reading only; the demonstrated cause is the out-of-band
`npx next build` rewriting the live `.next` without `NEXT_PUBLIC_API_URL`. The dev handoff's AUDIT ADDENDUM
states this honestly and does not claim otherwise, and the flock is defensible defense-in-depth with its
own passing test (TC-2). Recorded so a future round does not read "the race is fixed" as "the race was
real".

**B4 — no defect: build-guard branches verified first-hand**

I probed `apps/frontend/next.config.mjs`'s exported `(phase) => config` directly (importing the real
module, not a copy) across five states:

| probe | result |
|---|---|
| bare build into live `.next`, no `NEXT_PUBLIC_API_URL` | **REFUSED** (guard message) |
| `NEXT_DIST_DIR=.next-verify`, no API URL | ALLOWED, `distDir=.next-verify` |
| configured build into live `.next` | ALLOWED |
| `phase-production-server` (`next start`) | ALLOWED — guard is build-phase only |
| `phase-development-server` (`next dev`) | ALLOWED |

Corroborated end-to-end: my own verification build into `.next-verify` left the served `.next/BUILD_ID`
byte-identical, and the live server started fine under this config at 15:56 (`.trendora-serving` written,
QA browsed the app at 16:02). `TRENDORA_LAUNCH_BUILD=1` is not a blanket escape hatch — it bypasses only
the "dist dir is being served" rule, never the "live dist without an API URL" rule.

**B5 — no defect: AG-10 (HOST-GUARD) intact.** The whole `start-frontend.sh` diff deletes exactly one
line (`if ! "${HOST_GUARD_CMD_PREFIX[@]}" npx next build; then`), re-added with the same prefix plus
`TRENDORA_LAUNCH_BUILD=1`. The HOST-GUARD block (lines 28-58) is untouched and the prefix is still applied
to both `next build` (line 241) and the `exec … next start` (line 266).

**B6 — no defect: the spec's frozen list was respected.** No backend Python source changed this round
(`git status` shows only `apps/backend/tests/test_start_frontend_script.py`); `app/engine/readiness.py`
and `compute_forward_aggregates` are untouched. `stale_for_s` is genuinely server-computed
(`apps/backend/app/api/health.py:217,268`), so the UI is a pure consumer — AG-5 and the "Do not redo" list
hold.

### Frontend Findings

**F1 — GAP: the annotation freezes between polls, so it can understate real staleness ~60×**

`formatStaleAnnotation` is honest about the value it is given, and the plumbing is correct: one shared
poll, `staleForS` set to `null` on a failed poll (`readiness-provider.tsx:105`), no annotation for
`null`/`0`/negative/non-finite. But the rendered text only updates when a poll lands, and
`config.yaml:1327` sets `health_poll_idle_interval_seconds: 30.0` once Ready, while the server's cache
ticks every 0.5s (`config.yaml:1352`). Steady state is therefore a badge reading "as of <1s ago" for a
full 30 seconds.

I considered IMPORTANT and settled on GAP: TC-4 explicitly scopes the acceptance to "the same poll", the
displayed number always matches the payload it came from (no AG-3 violation), and the annotation never
fabricates. A client-side tick (`stale_for_s + elapsed-since-poll`) would close it; the reviewer flagged
the same thing as a NOTE.

**F2 — no defect: the disclosure and the layout fix are real, verified in opened captures**

- `reports/demo/goal-ops-hardening-iter-77/step-01.png` (15:00) — the shipped app rendering "Ready" +
  "as of <1s ago" and "GO — today's board is current. (as of <1s ago)". A real styled dashboard, not the
  crash boundary the pre-fix gallery captured.
- `…-evidence/dev-verify-TC-5-ready-pill-plus-compute-chip-1280x800.png` — at 1280×800 the "Ready" pill,
  the staleness text AND "background compute running (5)" are all on-screen, with the row wrapping to a
  second line. This is TC-5's required "screenshot showing both elements on-screen", and it is genuine.
- `…-evidence/TC-04-readiness-badge.png` (16:02) and `QA-header-layout-1280x800.png` (16:03) — QA's own
  post-fix captures; the text in each matches what QA quoted.
- `…-evidence/TC-8-data-fault-injection-honest-fallback.png` — `/data` under the armed fault-injection
  hook shows exactly "Backend unavailable — Dataset coverage could not load from the API. No figures are
  shown rather than fabricated values." with **no** coverage numbers. TC-8/DoD item satisfied.
- Every touched source file's mtime (≤ 14:44:03) predates the 15:03/15:44 replays, the 15:00 demo record
  and the 15:56 build, so all of that evidence was produced against the delivered code — no post-evidence
  source drift.

### Test / Harness Findings

**T1 — IMPORTANT (gap, not fixed): the merged browser artifact of record contradicts the shipped verdict**

`reports/phase-goal-ops-hardening-iter-77-ui-test-results.md` (13:41) reads **"Browser QA Verdict:
BLOCKED"** and lists `UT-J-04`, `UT-J-07`, `UT-J-09` under "Missing Target Journeys — no test case executed
… by any lane", while `reports/qa/goal-ops-hardening-iter-77-qa.md` headlines **PASS**. Traced to the
mechanism rather than accepted as a label:

- The LLM lane itself PASSED (`…-ui-test-results.llm.md`, 9/10, 1 skipped) and did exercise all three
  changed surfaces — UT-02 (badge + banner annotation), UT-03/UT-08 (no annotation on a failed poll),
  UT-05 (pill + chip both inside a 1280×800 viewport, `getBoundingClientRect()`), UT-06
  (`scorecard-row-{1,5,10,20,60}d`, count = 5). Those rows are keyed by feature id, not journey id, so the
  merge script's target-journey rule found no `UT-J-04/07/09` row and blocked the headline — the iter-41
  guardrail behaving exactly as designed.
- The fix pass's replay run *does* contain PASS rows for all three, but it was written to
  `reports/qa/goal-ops-hardening-iter-77-evidence/devfix-replay/replay-fast-results.md` (15:03) and never
  merged into the artifact of record; the merged file still carries the 13:41 pre-fix replay.
- The LLM lane also predates the F1 copy change, so its rows quote "as of 0s ago", which no longer ships.

Substantively the DoD item is met — all three surfaces have fresh post-fix live evidence (demo 15:00,
devfix-replay 15:03/15:44, QA 16:02/16:03, all opened above). What is not met is the artifact a downstream
reader parses. I deliberately did **not** re-run the merge myself: generating the verification artifact
that grades my own audit target is exactly the self-verification the model-orchestration rules forbid.
Remedy: re-dispatch the browser lane (or re-merge with the devfix-replay results) against the now-fixed
tree and let that lane own its own verdict.

**T2 — no defect: the demo-recorder fix is real and the goldens were not weakened**

Frame md5s in `reports/demo/goal-ops-hardening-iter-77/`: steps 01-04 share one hash, 05-06 another, 07 is
unique. Cross-checked against `reports/phase-goal-ops-hardening-iter-77-demo.json`: steps 01-04 all resolve
to `/` (step 02's "click" targets the badge, which navigates nowhere) and 05-06 both `goto /backtest` — so
identical frames there are correct, not fabricated difference. The one genuinely state-changing step (07,
`asof-step-prev`) differs from its predecessor. That is the iter-76/d defect closed.

I also checked the obvious way this fix could have cheated the replay lane and it does not: at all three
call sites, grading runs **before** the settle (`demo_runner.py:1810` then `:1819`; `:2062` then `:2071`),
so `_settle_for_capture`'s new `exp` re-poll can never convert a FAIL into a PASS or a soft note into a
pass. The TC-9 fixture asserts the soft note is still emitted, which is what makes it non-tautological.
The generic guards stay bounded (≤20 s, matching `_default_timeout`).

**T3 — no defect: no golden was regenerated.** `J-07.json` step 4 is upgraded to
`[data-testid="scorecard-row-1d"]` exactly as spec'd (the file was reformatted to pretty-printed JSON; I
diffed every step and the other three are semantically identical). `J-06.json` and `J-08.json` are modified
but **notes-only** — appended `_notes` entries, including an honest correction of record retracting the
earlier "host contention" misattribution. Steps, selectors and budgets are byte-identical, so the OUT OF
SCOPE ban on golden regeneration holds. J-09's step-3 selectors (`background-compute-idle`,
`background-compute-active-row`) both ship in `apps/frontend/app/data/page.tsx:3599,3653,3657` — real
shipped selectors, not lint-only.

**T4 — OBSERVATION: small inaccuracies in the delivered artifacts.** The QA report describes
`status.json` as "current_step: dev_complete, next_action: reviewer" (it reads `qa_complete`) and says
`goldens-regen-pending` still lists J-05/J-06/J-08 (the file is empty — fully cleared). `status.json`'s
`changed_files` omits `J-06.json`/`J-08.json`. None changes a verdict; all three make the artifact set
mildly harder to trust on a fast read.

**T5 — no defect: frontend unit tests re-run independently.** I compiled the real
`lib/staleness-annotation.ts` + `.test.ts` with the project's own `tsc` and ran the output: **7 passed**,
including the sub-second boundary and the "large staleness renders honestly (no cap/clamp hiding real
age)" case. I did not re-run `test_start_frontend_script.py` (11 minutes, and running it is precisely what
created B1); its 13-passed result rests on the developer's cited run plus the reviewer's independent
spot-check, with the guard's behaviour independently re-derived by me in B4.

---

## 3. Domain Assessment

The domain logic this round touches is thin by design — no scoring, no evidence, no forward returns — and
that restraint is correct and was honoured: the only new value on screen is a re-format of a field the
backend has computed since iter-71, and no second computation path was introduced. The honesty
conventions that matter in this product are respected precisely: `null` on a failed poll propagates to "no
annotation" rather than a frozen last-known number, negative/NaN payloads render nothing rather than
"as of NaNs ago", and the `/data` fault-injection path still shows the honest fallback copy with no
fabricated coverage figures. AG-2/AG-4 are untouched (no claims, no ranking, no orders).

The genuinely interesting domain-shaped judgement this round is the launcher's: it now treats "the bundle
on disk does not reference the backend this launch configured" as ground truth read from the emitted
chunks, and rebuilds — except when another live server owns the dist dir, where it warns and serves
rather than tearing that server. That trade-off is the right way round (never break a running server to
fix a config mismatch), it is logged loudly rather than silently, and its known one-claimant-per-dist-dir
limitation only bites in a test-only two-servers-one-dist-dir shape.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `apps/frontend/__tc3_intentionally_broken.ts` | Deleted the stray intentionally-broken TypeScript file left by an interrupted `test_start_frontend_script.py` run. With it present, `find`-based staleness classified the build stale, `next build` failed on TS2322, and `start-frontend.sh` exited 1 rather than serving — the delivered tree could not launch a frontend. Verified after the fix: real production build **rc 0**; live `.next/BUILD_ID` byte-identical (`af0fd50b…`); `.next-verify` restored to HEAD and its build residue cleaned. |

No tracked file was modified by this audit. The dev handoff's claims remain accurate as written (its AUDIT
ADDENDUM and Fix Notes already record the corrected root cause), so no handoff claim needed retraction.

---

## 5. Recommended Next Step

Proceed to the next iteration; the phase goal is met and the code lane is demonstrably open again. Before
that iteration's first launch, three things are owed:

1. **Re-dispatch the browser lane (or re-merge) against the fixed tree** so
   `reports/phase-goal-ops-hardening-iter-77-ui-test-results.md` stops reading `BLOCKED` with three
   target journeys marked unexecuted (T1). Do not carry the pre-fix `as of 0s ago` rows forward as
   evidence — that copy no longer ships.
2. **Decide the B2 lane rule** — `test_start_frontend_script.py` must not be dispatched into a
   short-timeout lane again; an interrupted run leaves the live frontend unbuildable with no symptom
   until a launch fails.
3. **Restart the stack** (`scripts/start-backend.sh`, then `scripts/start-frontend.sh`) — both services
   were down at audit close, and the launcher will now rebuild successfully.

Carry F1 (a client-side ticking age, so "as of <1s ago" cannot sit unchanged for a 30-second idle poll
window) and B3 (the concurrent-launcher race remains a hypothesis, not a demonstrated cause) as candidate
items rather than closing them silently.
