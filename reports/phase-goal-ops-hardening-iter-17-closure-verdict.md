# Phase goal-ops-hardening-iter-17 — Closure Verdict

**Phase:** goal-ops-hardening-iter-17
**Date:** 2026-07-24
**Written by:** phase-closure-auditor

---

**Verdict:** CLOSURE-PASS

---

## Standard Pipeline Gate Checks

| Artifact | Status | Verdict |
|----------|--------|---------|
| Review report (`reports/reviews/goal-ops-hardening-iter-17-review.md`) | exists | PASS |
| QA report (`reports/qa/goal-ops-hardening-iter-17-qa.md`) | exists | PASS |
| Audit report (`docs/handoffs/goal-ops-hardening-iter-17-audit.md`) | exists | PASS_WITH_GAPS (accepted — same class as "PASS WITH GAPS") |

All three gates clear per this framework's own verdict semantics (`PASSING_VERDICTS = {PASS, PASS_WITH_NOTES, PASS_WITH_GAPS}`).

- Review is a clean PASS: the B1 cross-`asof_key` fallback, the new `evidence_asof` field, B5's double-read fix, and B3's UTC timestamp were independently re-run by the reviewer (15/15 unit tests, 0 TypeScript errors) before the PASS was issued. Its two issues are both NOTE-severity (an optional future index; TC-7/TC-8 honestly reported as unreachable this session).
- QA is a clean PASS: 15/15 targeted backend tests, 0 TypeScript errors, a full functional test-plan pass (TC-01–TC-11) with fallback-achieved/deferred outcomes clearly labeled, and a UI-evolution audit scoring UI-PASS on all 4 checks.
- Audit's PASS_WITH_GAPS **found and fixed** one IMPORTANT defect during the audit itself (F1 — `EvidenceAggregateSection`'s window copy ("expanding window ≤ D", "Snapshots contributing (≤ D)") was bound to the page's requested as-of instead of the served one, contradicting the new banner two lines above it in exactly the state this iteration introduces) and recorded the remainder as GAP/OBSERVATION-level items explicitly routed to the evaluator (TC-8 unreachable on this data, TC-10 not run by reasoned decision, plus cheap non-blocking follow-ups B1/B2/B3/T1/T2) — not silently absorbed into a false PASS.

**Independently re-verified by this gate, not taken on trust:**
- `git status --porcelain` on the exact files named by the dev/frontend handoffs and `status.json.changed_files` returns precisely those 7 product files (`apps/backend/app/api/backtest.py`, `apps/backend/app/engine/forward_testing.py`, `apps/backend/app/mcp/tools.py`, `apps/backend/tests/test_forward_testing_serving_split.py`, `apps/backend/tests/test_api_backtest.py`, `apps/frontend/app/backtest/page.tsx`, `apps/frontend/lib/api.ts`) plus `reports/perf-budgets.md` — no undisclosed file is touched.
- The audit's F1 fix is genuinely live, not just claimed: `curl http://localhost:8255/api/backtest` right now returns `evidence_status="ready"`, `evidence_asof="2026-07-22"` (identical to `asof_date`, as required for the `ready` state), and the live `/backtest` page (`http://localhost:3255/backtest`) returns HTTP 200 with zero occurrences of "backend unavailable" or "NO-GO" in its server-rendered HTML.
- The browser-QA FAIL on record (UT-01, "Backend unavailable"/NO-GO) does not reproduce right now and is independently re-confirmed as an already-corrected environment defect, not a product regression — see Non-Blocking Note 1 for the specific commands this gate ran itself.
- All screenshots cited by `ui-test-results.md` and the audit exist on disk in `reports/qa/goal-ops-hardening-iter-17-evidence/` at substantial, non-placeholder sizes (88 KB–779 KB): `TC-07-backtest-page.png`, `TC-07-evidence-section.png`, `TC-07-refreshing-banner-with-asof.png`, `TC-09-not-yet-computed-state.png` (+ `-fullpage.png`), `UT-01-top.png` / `UT-01-top-workaround.png`, `UT-04-ready-evidence-bottom-refreshing.png`, `AUDIT-A1-crossboundary-refreshing-after-fix.png`, `AUDIT-A1-ready-state-unchanged.png`, plus the three regression-journey `J-0{1,3,5}-verify.png` files.
- AG-10 host-guard posture on the live throwaway backend the audit flagged as previously non-compliant: checked directly via `/proc` right now, the process currently listening on `:18255` (pid 1245537) and the main backend (`:8255`, pid 1414921) both carry CPU affinity `0-3,8-11` and a 6 GiB (`6442450944`-byte) address-space cap — matching the audit's own `/proc`-derived finding. No live AG-10 regression as of this check.

---

## UI Visibility Artifact Checks

`Frontend Present: yes` per `runs/goal-ops-hardening-iter-17/plan.md` and `docs/phases/goal-ops-hardening-iter-17.md` — and genuinely so: 2 real frontend files changed (`apps/frontend/app/backtest/page.tsx`, `apps/frontend/lib/api.ts`), both exercised live in a browser this session.

| Artifact | Exists | Non-Empty | Non-Vague | Status |
|----------|--------|-----------|-----------|--------|
| implementation-summary.md | yes | yes (80 lines) | yes | OK — see Non-Blocking Note 2 (one stale section) |
| user-visible-changes.md | yes | yes (75 lines) | yes | OK |
| ui-surface-map.md | yes | yes (44 lines) | yes | OK |
| ui-test-plan.md | yes | yes (293 lines) | yes | OK |
| ui-test-results.md | yes | yes (48 lines) | yes | OK — see Non-Blocking Note 1 (overall FAIL, root-caused as environmental) |
| what-to-click.md | yes | yes (87 lines) | yes | OK |

No artifact contains only placeholders, "TBD," or vague steps, and none show "N/A"/"backend-only" for this frontend-present phase. All six describe the same concrete, narrow surface (`/backtest`'s evidence section: `RefreshingEvidenceBanner`'s new `evidenceAsof` label, the reworded `not_yet_computed` `EmptyState`) with specific file paths, line numbers, exact copy text (before/after strings quoted verbatim), and named test IDs. `ui-test-plan.md`'s 6 UT-cases each carry exact URLs, exact expected copy strings, and explicit scope notes distinguishing what each test does and does NOT prove (e.g., UT-03's own "IMPORTANT" callout that it exercises the pre-existing same-`asof_key` mechanism, not the new cross-boundary one — a level of self-policing precision worth noting). `what-to-click.md` carries 7 core numbered steps plus 3 optional ones, each with a concrete "Expect:" line.

---

## Cross-Reference Checks

- [x] `user-visible-changes.md` lists concrete new capabilities a user can try: the evidence section stays populated with a labeled older date instead of going empty during the single most common ingest shape; the refreshing banner now names *which* date's evidence is on screen; the empty-state copy no longer presumes the user hasn't already started an ingest — not "no visible changes."
- [x] `ui-surface-map.md` names specific routes/components: `/backtest` → evidence-section state routing → `RefreshingEvidenceBanner` (`page.tsx:263-282`) / `EmptyState` call site (`page.tsx:236-240`), each row carrying an exact "what to test" command (a `curl` for the JSON shape, a browser navigation for the copy) — not "the whole app."
- [x] `ui-test-plan.md` has fully specific steps: exact URLs for both the main and throwaway service pairs, the literal banner sentence and literal empty-state copy expected, and explicit non-goals (e.g., "do not design or run a test that pretends [the cross-boundary case] is reachable").
- [x] `ui-test-results.md` shows real execution evidence: 8 genuine PASSes with screenshot/DOM evidence (including 3 regression-journey replays, J-01/J-03/J-05), 1 FAIL carrying a full root-cause writeup rather than being smoothed over, 1 SKIPPED with a specific, non-generic justification (this iteration's own binding scope is a non-disruptive health-poll check only, verified instead via a live `/api/health` 200 + a `logs/backend.log` line-count diff showing no new crash/restart banner). Not "all SKIPPED," and the one FAIL is not hidden.
- [x] `what-to-click.md` has 7 numbered core steps (≥3 required) plus 3 optional ones, each with a concrete "Expect:" outcome and a "Confirm neither page ever showed a red 'Backend unavailable' error card" cross-check.
- [x] Implementation claims are consistent with test evidence, **with one specific staleness caveat**: `implementation-summary.md`'s "Incomplete Items"/"Known Limitations" sections say live capture of the empty state and the refreshing-banner text "were not captured this session" and still need a human to run — this was true when written, but by the time the pipeline finished, both HAD been captured live (`UT-02` → PASS with `TC-09-not-yet-computed-state.png`; `UT-03` → PASS with `TC-07-refreshing-banner-with-asof.png`, both confirmed present on disk). The claim direction is conservative, not inflated (it understates completion, never overstates it), and the true state is fully and consistently documented elsewhere (dev handoff's "UPDATE (2026-07-24, operator pass)," the frontend handoff's matching addendum, and the ux-regression report's own "Documentation-freshness aside" note) — see Non-Blocking Note 2.

**Backend-only claim guard (Step 4): does not trigger.** `user-visible-changes.md` does not say "no visible changes" and is not empty beyond its header — it substantively documents three specific UI-visible changes, consistent with `ui-surface-map.md` showing the 2 frontend files actually changed. Browser QA did not skip wholesale for "frontend not running": the merged results show 8 PASS / 1 FAIL / 1 SKIPPED across UT-cases, plus 3 passing regression-journey replays, all with named evidence files — not a blanket skip with no reason given.

---

## Blocking Issues

None.

---

## Non-Blocking Notes

These are carried forward for the evaluator, not re-litigated here — the closure gate's job is artifact hygiene and consistency, and on both counts this iteration passes cleanly. Every item below is already disclosed, at least once and usually at every pipeline stage, not newly discovered by this check; where this gate ran its own independent verification, that is stated explicitly rather than merely repeating an upstream claim.

1. **`ui-test-results.md`'s overall Browser QA Verdict is FAIL, driven entirely by UT-01 — independently re-verified by this gate, not merely accepted, as an already-corrected operator/environment defect, not a product regression.** Root cause per the operator's own write-up (`runs/goal-ops-hardening-iter-17/operator-next-build-collision.md`): two `next dev` servers were run from the same cwd, sharing one `.next` build directory; since `NEXT_PUBLIC_API_URL` is inlined at Next.js compile time, the main app's bundle briefly served a hardcoded pointer to the throwaway backend (`:18255`), producing a permanent "Backend unavailable"/NO-GO state unrelated to any line of product code this or any prior iteration shipped. This gate ran its own fresh checks rather than relying on the auditor's or the ux-regression-reviewer's prior (already-independent) re-verifications:
   - `grep -rlo 'localhost:18255' apps/frontend/.next` → **no matches**; `grep -rlo 'localhost:8255' apps/frontend/.next` → matches in `app/backtest/page.js`, `app/page.js`, `app/layout.js` (the correct backend is what's actually compiled in).
   - Live, at the moment of this check: `GET http://localhost:8255/api/health` → 200; `GET http://localhost:3255/` → 200; `GET http://localhost:3255/backtest` → 200 with the server-rendered HTML containing **zero** occurrences of "backend unavailable" or "NO-GO"; `GET http://localhost:8255/api/backtest` returns a well-formed `evidence_status="ready"`, `evidence_asof="2026-07-22"`.
   - `git status --porcelain` confirms exactly the 7 product files + `reports/perf-budgets.md` this iteration touched — none of the 4 files UT-01's own in-page instrumentation implicated (`readiness-provider.tsx`, `health-badge.tsx`, `preflight-banner.tsx`, `app/data/page.tsx`) are in that set.
   This makes four independent confirmations on record (operator, auditor, ux-regression-reviewer, this gate), each using fresh evidence rather than repeating a single narrative. **Conclusion: this FAIL does not block closure.**

2. **`implementation-summary.md` is stale relative to later developments and should be synced in a future pass — a documentation-timing artifact, not a code or evidence gap.** It states that live capture of the `not_yet_computed` empty state and the refreshing-banner text "were not captured this session," written before the operator's later pass produced exactly those captures (`UT-02`/`UT-03`, both PASS, both with screenshots confirmed present on disk). This is the same "documentation lag in a multi-stage pipeline" pattern iter-16's own closure verdict noted (see Cross-Reference Checks item 6, prior file) — it understates rather than overstates progress, so it does not fit the false-completion pattern this gate exists to block. Recommended remediation (non-blocking): sync `implementation-summary.md`'s "Incomplete Items"/"Known Limitations" sections with the dev/frontend handoffs' operator-pass updates before this iteration's artifacts are relied on by a future one.

3. **Two DEFINITION OF DONE gaps are carried forward, already disclosed and already the audit's/evaluator's call, not reopened by this gate:**
   - **TC-8** (live exercise of the new cross-`asof_key` fallback): unreachable this session because the working DB's price basis ends at `2026-07-22` with no future trading day to backfill into (AG-9 forbids fabricating one). The fix rests on 5 passing unit tests (TC-1/2/4/5/6) plus, now, the audit's own client-side render of a simulated cross-boundary payload — real evidence, but not an end-to-end live exercise.
   - **TC-10** (deep-basis latency re-measurement): not run this session, a reasoned and disclosed decision (no code in this diff touches the write pattern iter-16's baseline measured) rather than an oversight; `reports/perf-budgets.md:2975` still literally reads "PENDING, operator-supervised (not run this session)."
   Both are named explicitly in `status.json`'s `blockers` array and in the audit's "Recommended Next Step" section for the evaluator to weigh. This gate defers to that routing, consistent with its own remit (UI-artifact completeness and pipeline-gate presence, not re-adjudicating DoD lines a PASS_WITH_GAPS audit already covered).

4. **`reports/qa/goal-ops-hardening-iter-17-qa.md`'s own "Browser test result: PASS" line (its Step 4) is chronologically superseded by the later, more rigorous dedicated browser-QA lane recorded in `ui-test-results.md`.** The audit already caught this sequencing gap (§2, finding P3c) and it does not affect the QA gate's own overall PASS verdict, which rests primarily on 15/15 backend unit tests and 0 TypeScript errors, independently re-run by both the reviewer and the auditor. Noted here for completeness only.

Positive continuity note: this iteration directly closed both of iter-16's own UX-regression follow-ups (the "ingest" jargon is gone from the empty-state copy, and `not_yet_computed` now has its first-ever live browser screenshot), and its audit caught and fixed a real user-facing correctness defect (F1) before it reached this gate — the honest-disclosure pattern this framework depends on continues to hold, not the false-completion pattern this gate exists to block.
