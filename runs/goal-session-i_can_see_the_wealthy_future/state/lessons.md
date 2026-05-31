# Goal Session i_can_see_the_wealthy_future — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-1 — 2026-05-29T17:04:13Z

**Verdict:** CONTINUE
**Lesson:** Two browser-driven steps disagreed: the dedicated browser-qa report said SKIPPED ("frontend
not running") while the QA mode-2 report said PASS with Chrome MCP screenshots. Both were "true" at
different moments — the managed `next dev` server exited mid-run and QA restarted it. Reconcile by
checking the evidence directory on disk (the 3 PNGs were present), not by trusting either verdict alone.
Separately: the spec named **Stooq** as the seed source, but Stooq now gates bulk CSV behind a
captcha/apikey; the dev correctly pivoted to the no-key Yahoo chart API rather than commit a key — a
pivot that *preserves* the No-secrets anti-goal is the right call, not scope drift.
**Applies to:** any iter whose browser-qa and QA both drive a browser (verify the managed frontend is up
and stable before trusting a SKIP/PASS — inspect the evidence dir); any iter that depends on a specific
named external data source (confirm it is still free/no-key before relying on it, and a key-avoiding
pivot is acceptable and must be documented in handoff + meta provenance).

## iter-2 — 2026-05-29T19:10:15Z

**Verdict:** CONTINUE
**Lesson:** The coherence-auditor caught a *future*-duplicate risk that is invisible today: iter-2 computes
market breadth once in `app.engine.regime:score_regime` and serves it from the canonical `/api/dashboard`
(single source, no violation now), but the blueprint Data Contract registers "market breadth %" under
`app.engine.scanner:summarize_run` — which does not exist until iter-5. If iter-5 builds `summarize_run` to
recompute breadth from setup statuses, it silently creates the exact two-sources-for-one-number the
single-source gate forbids. A WARN about an unbuilt module is a real liability, not noise — reconcile the
contract attribution *before* the second module lands. (Also: the `next dev`/QA browser-qa SKIP-vs-PASS flap
recurred a 2nd time — the iter-1 lesson still applies; consider hardening frontend supervision.)
**Applies to:** any iter that builds `app.engine.scanner` / `summarize_run` or otherwise touches breadth,
new-high/low, or any value the blueprint attributes to a not-yet-built module — make the new module *read*
the existing canonical source, never recompute; and any iter relying on browser evidence (verify the
managed frontend is up and inspect the evidence dir, do not trust a lone SKIP/PASS).

## iter-3 — 2026-05-29T21:48:48Z

**Verdict:** CONTINUE
**Lesson:** The browser-qa SKIP-vs-PASS flap recurred a **3rd** consecutive time — and this time the iter-3
spec had *explicitly instructed the orchestrator to harden `next dev` supervision*, yet the dedicated
browser-qa still probed a dead frontend (HTTP 000) and SKIPPED all 23 cases while QA mode-2 independently
started its own `next dev`, ran the 5 browser cases, and saved 9 PNGs. A spec-level note to "keep the server
up" demonstrably does NOT fix this; the fix must be structural — the dedicated browser-qa agent should
*ensure/own* its frontend (start it if down, like QA mode-2 does) rather than precondition-skip, or the two
browser steps should share one managed server. Until then, evidence lives only in QA's PNGs, so always
reconcile from the on-disk evidence dir. (Also recurring: the **audit handoff was again not produced** at
full depth — 2nd time, iter-2 + iter-3.)
**Applies to:** the browser-qa-agent / orchestrator harness itself (make browser-qa self-heal its frontend
instead of SKIP-on-down); any future iter verified through the browser — trust the PNGs on disk, not a lone
verdict; and the full-depth pipeline (confirm the audit handoff is actually emitted).

## iter-4 — 2026-05-30T03:30:00Z

**Verdict:** CONTINUE
**Lesson:** Two compounding traps. (1) The browser-qa SKIP/PASS flap recurred a **4th** time (dedicated
browser-qa SKIPPED on HTTP 000), but QA mode-2 self-healed and **persisted** TC-10/TC-11 to the evidence
dir, so reconciling J-05 from the on-disk PNGs worked and J-05 passed — the iters-1–3 standing lesson held.
(2) The *real* surprise was an evaluator-side trap: during a transient tool-output outage the Read of those
two PNGs spuriously returned **"files do not exist"**, which nearly drove a wrong `partial` cap on a journey
whose evidence was actually present (the calls were being *queued*, not failed, and flushed later showing the
files + the populated chart). Lesson: under a flaky/queuing harness a **negative existence result is not
trustworthy** — re-confirm with `ls`/Glob/re-read before letting "missing evidence" lower a verdict; and a
Write that returns no confirmation may still have landed (don't blind-retry appends; an overwrite Write can
also be rejected with "file modified since read" if another queued op touched the file first). Also: don't
let the demo-narrator's Playwright soft-notes ("text not found", click timeouts) override the QA evidence —
they are capture-timing artifacts of the non-gating showcase runner. (Audit handoff now missing **4**
full-depth iters running.)
**Applies to:** the goal-evaluator's own process on any flaky-tool run (re-verify negative file-existence
before acting; verify writes landed without double-appending); any canvas/chart-rendered journey
(Lightweight-Charts) — trust the QA evidence PNG over demo soft-notes; and the full-depth pipeline
(browser-qa must own/self-heal its frontend; the audit step must emit its handoff).

## iter-5 — 2026-05-30T05:30:00Z

**Verdict:** CONTINUE
**Lesson:** Spec-text cannot fix runner-level behaviour, and now we have two proofs: iter-3 escalated
the browser-qa self-heal ask to a spec NOTE (failed → flap recurred 4th/5th time), and iter-5 escalated
the audit-handoff ask all the way to the spec's **Definition of Done** (still failed → `reports/audits/`
does not even exist after 5 full-depth iters). When a missing artifact is produced by a pipeline *step*
(audit) or a precondition the *runner* controls (the dedicated browser-qa's frontend), the only durable
fix is editing `scripts/automation/*.sh` — stop re-asking via the iteration spec/DoD, it has demonstrably
no effect. Practical consequence: the evaluator must keep reconciling target journeys from on-disk
evidence PNGs + unit/API proofs + direct source reads, never from a lone browser-qa SKIP verdict.
**Applies to:** every future goal-mode iteration's evaluation while the audit-handoff / browser-qa-self-heal
harness gaps remain unfixed; and any decomposer tempted to fix a harness/runner gap by adding spec or
DoD text instead of a runner-script change.

## iter-6 — 2026-05-30T05:45:00Z

**Verdict:** CONTINUE
**Lesson:** Distinct journey-named evidence PNGs are NOT guaranteed to be distinct captures: this iter
`TC-14-system-health-j09.png` and `TC-16-control-group-j10.png` were byte-identical (same md5) — one
full-page `/system-health` screenshot saved under two journey labels. When a target journey (J-10) is a
sub-panel of a larger page already captured for another journey (J-09), QA tends to reuse the full-page
shot. So `md5sum`/diff the evidence files before treating a per-journey screenshot count as independent
visual proof, and confirm the specific panel is actually present in the shared image (it was, here). The
evidence was sufficient, but the count overstated distinctness.
**Applies to:** any iter whose target journeys are multiple panels of ONE page (e.g. system-health
J-09+J-10, or a future combined dashboard); and any evaluator weighing "N screenshots = N journeys
proven" — hash them first. A decomposer/QA spec can pre-empt this by asking for a focused/cropped capture
per sub-panel journey.

## iter-7 — 2026-05-30T06:29:04Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** The chronic 7-iter dedicated-browser-qa SKIP has a *second* root cause beyond "frontend not
running": a **CORS_ORIGINS mismatch**. The backend's `main.py:_cors_origins()` defaults to
`http://localhost:3000` when `CORS_ORIGINS` is unset, so a frontend on `:3835`/`:3836` is silently
CORS-blocked and the page renders the honest "Backend unavailable" card even though `curl` to the API
succeeds (curl doesn't enforce CORS). When verifying a UI live, launch the backend with
`CORS_ORIGINS=http://localhost:<frontend-port>` and rebuild the frontend with
`NEXT_PUBLIC_API_URL=http://localhost:8835` (it is baked at build time, default `:8000`). Also: Chrome MCP
`await_text "ANET"` false-positived on the ticker input *placeholder* "e.g. ANET" — await on a row-only value
(setup status, invalidation level), never on text that also appears in form placeholders. Most important
takeaway: on a goal-completing iteration with an empty/invalid evidence dir, the evaluator CAN and SHOULD boot
the services and drive Chrome MCP to produce the missing live evidence (incl. a real backend-restart
persistence proof) rather than reconcile from API/unit/source alone — it makes GOAL_ACHIEVED rest on an actual
browser sweep.
**Applies to:** any iter whose UI must be verified live (esp. when browser-qa SKIPs); any new frontend-facing
backend route; the runner-script owner fixing the browser-qa frontend self-heal.

## iter-8 — 2026-05-31T00:54:30Z

**Verdict:** CONTINUE
**Lesson:** To actually PROVE the "No recompute in the read path" anti-goal, the keystone test
(`test_repointed_handlers_serve_persisted_date_without_recompute`) monkeypatches the four canonical
engines (`score_stocks/score_regime/score_sectors/score_themes`, as `run_scan` references them) to
RAISE, then asserts the handlers still serve a persisted date. This is strictly stronger than a
served==stored value-equality check, which would still pass if the endpoint recomputed a value that
happens to match storage — value-equality cannot prove a negative ("did not recompute"); only the
patch-to-raise seam can. Separately, re-pointing 5 long-green journeys onto stored snapshots was
de-risked because the diff only APPENDED the resolver (`run_scan` untouched → create-once/immutable/
no-lookahead inherited) and the iter-5 faithful-equality test made latest payloads byte-identical to
the old on-request compute.
**Applies to:** any future iter that claims an endpoint "serves from storage / cache, not recompute"
(J-14 backtest scorecard, J-16 VCP breakdown, any snapshot-served read) — assert it with a
patch-the-compute-to-raise seam, not value-equality; and prefer append-only changes to the canonical
compute path when migrating a read path that backs already-green journeys.

## iter-9 — 2026-05-31T02:39:03Z

**Verdict:** CONTINUE
**Lesson:** A full-depth iteration can reach the goal-evaluator having produced **zero product code** — the
developer step silently no-op'd: `status.json` stayed at `current_step="starting"`/`changed_files=[]`, and
there was no dev handoff, review, QA, audit, browser-QA, or evidence, yet the pipeline still advanced (the
decomposer wrote the spec + blueprint deltas + reapproval marker and coherence ran on the empty diff and
returned PASS). A COHERENCE-PASS here did NOT mean the feature was built — the coherence file itself warned
"the blueprint is ahead of the code." The evaluator must verify *implementation presence* before trusting
any "achieved/continue" framing: `git status` (no apps/ diff, HEAD unchanged) + `git stash list` + `git
worktree list` + direct file-existence checks (the new module/page/tests) + `grep -rln <feature> apps/`. When
the spec is sound but simply unexecuted, the correct verdict is **CONTINUE (re-run the existing spec)**, NOT
STALLED — STALLED's "edit goal.md / narrow scope" remedy is actively wrong when goal + spec are fine and only
execution failed.
**Applies to:** any iteration where the dev handoff / QA / evidence are missing or `status.json.current_step`
is still "starting" / `changed_files` is empty — never infer the feature exists from the spec, the blueprint,
or a COHERENCE-PASS; confirm code presence from git + filesystem first, and distinguish "not built yet" from
"built but un-verified."

## iter-10 — 2026-05-31T09:10:00Z

**Verdict:** CONTINUE
**Lesson:** The browser-qa SKIP debt got *qualitatively worse* this iter: for the first time since
iter-4 there were **zero evidence PNGs** — QA mode-2 did NOT self-heal/persist shots (the evidence dir
didn't even exist), so the long-standing "reconcile J-14 from QA's persisted PNGs + unit/API + source"
fallback had **nothing to reconcile from**. The right move (per the iter-7 precedent) is to boot the
services and produce the evidence yourself, and it is cheap when the frontend already builds clean and
the data contract is API-proven: `CORS_ORIGINS=http://localhost:3835 uvicorn main:app --port 8835` +
`PORT=3835 npm run start` (build with `NEXT_PUBLIC_API_URL=http://localhost:8835`) → drive Chrome to
`/backtest`, `select` the page's own `aria-label="Backtest as-of date"` picker to a full-window date,
and eval the scorecard `<table>` cells. The strongest single proof of "FE recomputes nothing" was
diffing the rendered cells against the `/api/backtest` payload — they matched **byte-for-byte,
re-formatted to %**. Practical note: the per-fixture walk-forward lifespan boot makes the suite slow
(~230s for just the 17 new J-14 tests; ~885s full) — run the targeted `test_backtest_*.py` files, not
the whole suite, and budget minutes (use a background task; the foreground sleep guard will block
polling loops).
**Applies to:** any iter where the dedicated browser-qa SKIPs AND no QA evidence PNGs exist — do not
down-grade a journey to `partial`/`unknown` reflexively; self-produce live evidence first. Also any iter
touching `apps/backend/app/engine/forward_testing.py` (slow walk-forward boots → target the test files).

## iter-11 — 2026-05-31T14:05:00Z

**Verdict:** CONTINUE
**Lesson:** To prove a NEW additive field on a canonical row does not perturb an EXISTING canonical
value (here: that the VCP flag changes no row's `setup_status`), the strongest test is to monkeypatch
the new computation to its MAXIMAL/forced state and assert the sibling field is byte-identical to a
clean baseline — `test_vcp_is_a_pattern_not_a_status` patches `detect_vcp` to flag EVERY name and
asserts `forced_status == baseline` (+ `"VCP" not in ALL_STATUSES`). This is the additivity dual of the
iter-8 patch-to-RAISE keystone: patch-to-raise proves "the read path recomputes nothing"; patch-to-
forced-value proves "the new field perturbs no existing field on the compute path." A value-equality
check ("statuses look the same") is weaker — it can't distinguish "unaffected" from "coincidentally
equal." Separately: riding a new flag through existing seams (compose onto the `score_stocks` row →
stored in the existing `record_json` + one append-only mirror column → served by the existing endpoints
→ grouped by the existing `_group_means` helper) made the whole feature land with an EMPTY `api/`+`main.py`
diff and an unchanged `setups.py`, which is why J-06/J-09/J-10 could not structurally regress.
**Applies to:** any future iter that adds an additive flag/field onto an already-canonical row (e.g. a
2nd detected pattern, a new badge) — prove non-perturbation with a force-the-new-thing monkeypatch +
byte-equality of the existing field, and prefer composing onto the existing row/endpoint/grouping seams
over adding a parallel path.

## iter-12 — 2026-05-31T16:30:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A goal-completing iteration can legitimately reach GOAL_ACHIEVED on RECONCILED evidence even
though the dedicated browser-qa never ran once across the entire 12-iteration session. What made it sound:
(a) the empty-diff keystone (`git diff --stat HEAD` over the engine + every read router = empty) proving
the 15 carried journeys' canonical computations are byte-identical to when they passed; (b) the
deterministic seed reproducing documented canonical values (dashboard 74.32 / breadth 65.57% /
System Health A +6.00% n=24); and (c) the evaluator INDEPENDENTLY verifying the new feature's
"matching-config" keystone by diffing the live `/api/methodology` payload against `config.yaml`
byte-for-byte — not trusting the unit test alone. For a config-backed glossary, that payload-vs-config
diff is the strongest possible proof the displayed thresholds cannot drift.
**Applies to:** any goal-completing iteration whose diff is provably additive (new read-only surface,
empty-diff on all engines/routers); and any "matching-config / single-source" claim — verify the live
served value against the canonical config block directly, don't rely on the in-suite test. NOTE for the
runner owner: the browser-qa (probes `/health` not `/api/health`; tears services down pre-test) and
audit-handoff gaps were flagged every iter 3–12 via spec text and never fixed — durable fixes belong in
`scripts/automation/*.sh`, not spec prose, and should land EARLY in a session so final sign-off rests on a
live dedicated sweep.
