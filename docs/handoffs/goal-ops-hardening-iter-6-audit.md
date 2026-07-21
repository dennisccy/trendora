# goal-ops-hardening-iter-6 Audit Report

**Date:** 2026-07-21
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase's primary goal — eliminate the real-browser connection/GIL-contention latency so `GET /api/indexes?full=true` (Dashboard) and `GET /api/data/availability` (Data Manager) fall within their committed ≤1.5s budgets under a real browser — is **genuinely achieved and independently verified**, not just asserted by the dev. The independent browser-qa lane re-measured both target endpoints at 834/885/871ms and 869/985/950ms respectively (3/3 reloads each, within budget), the four required-still-passing journeys (J-01 with its fixed golden script, J-03, J-04, J-05) are green via independent replay/LLM lanes, the diff is verifiably frontend-only (zero backend/config/seed change), and no anti-goal is violated. Two documented gaps keep this from a clean PASS: (a) `/api/evidence`'s pre-existing **one-time cold-miss is ~73s on the accumulated dev DB** (~9.5s on the shipped committed seed) — pre-existing, out of scope for a frontend-only iteration, covered by a pre-existing Item I budget, and gracefully degrading — and (b) the 2500ms availability stagger trades a marginally longer heatmap-visible wait for the in-budget endpoint number. Neither defeats the iteration's purpose.

---

## 2. Findings

### Backend Findings

**B1 — GAP (documented, pre-existing, out of scope): `/api/evidence` one-time cold recompute is ~73s on the accumulated dev DB.**
`docs/handoffs/goal-ops-hardening-iter-6-dev.md` (Fix Notes) and `reports/perf-budgets.md:1246-1261` disclose that on the accumulated live dev DB (`forward_returns` = 1,519,801 rows / 2.55 GB, ~8.9× the committed seed's 170,229 rows) the first `/evidence` view after any dataset change costs **73.3s idle**. The independent browser-qa lane corroborated this with its own measurement — `reports/phase-goal-ops-hardening-iter-6-ui-test-results.llm.md:42` records UT-13 real-browser `GET /api/evidence` at **73.5s**, with a warm direct `curl` at **0.02s**. This is:
- **Pre-existing and NOT this iteration's diff** — `git diff HEAD -- apps/backend` is empty; `/evidence`'s frontend and its serving endpoint were untouched. Confirmed by the browser-qa agent's own `git diff` check.
- **Covered by a pre-existing committed budget** — `reports/perf-budgets.md:525-531` (Item I, iter-41) commits `/api/evidence` as **warm ≤3s (never-regress) + a bounded one-time cold miss** that scales with the deep basis, explicitly stating "if the ledger's claim count grows materially, re-measure this cold-miss bound." Warm is met with wide margin (22-26ms). On the *shipped* committed seed (170,229 rows) the cold miss is the committed ~9.5s; the 73s is the drifted (gitignored) dev DB only.
- **Gracefully degrading** — HTTP 200, valid 7-claim payload, frontend loading state, no crash/OOM (AG-8 satisfied); independently confirmed by UT-13 ("loaded correctly with real, well-formed data").
- **With a named, correctly-deferred remediation** — extend the ingest finalize hook (which already warms the event-study default key at `data_manager.py:3138`) to also warm the 7 evidence `drawdown_expectations` keys, per goal.md improvement-direction item 6.

No fix applied: this is backend, out of scope for a frontend-only iteration, and the spec's own contingent-fix discipline (`docs/phases/goal-ops-hardening-iter-6.md` NOTES) directs that such a discovery be flagged for a fresh decomposer pass, never fixed mid-iteration. Fixing it here would be scope creep.

### Frontend Findings

**F1 — VERIFIED CORRECT: Dashboard `PhaseCrossViewCard` 250ms deferral.**
`apps/frontend/components/phase-cross-view-card.tsx:45,55-87` — `setStatus("loading")` is set synchronously (line 58) before the `window.setTimeout(..., 250)` (line 63) fires the `Promise.all`; the cleanup (lines 83-86) clears the timer AND aborts the controller; the fetch `.catch` guards `if (!controller.signal.aborted)` (line 80) so an aborted in-flight fetch never clobbers a fresh effect's loading state. Loading/ok/empty/error render branches are byte-unchanged. This is the correct implementation of the spec's TC-10 contract, and it was independently exercised (UT-04 PASS: rapid as-of toggle, never blank/frozen).

**F2 — VERIFIED CORRECT: Data Manager `loadAvailability()` 2500ms deferral, mount-effect only.**
`apps/frontend/app/data/page.tsx:102,351-363` — the mount effect fires `loadOverview(controller.signal)` immediately and defers `loadAvailability(controller.signal)` by 2500ms; cleanup clears the timer and aborts. I confirmed by reading the file that the three other `loadAvailability()` call sites (job completion `:402`, retry/dismiss `:449`, removal `:604`) are unchanged and call it together with `loadOverview()` — matching the dev/reviewer claim exactly. The heatmap's own `{ kind: "loading" }` spinner covers the deferral window (UT-07 PASS: "Loading availability…" shown, never blank).

**F3 — GAP (documented): the 2500ms availability stagger increases total mount-to-visible-data wait for the heatmap.**
The endpoint's own measured duration genuinely dropped (~2.9-3.0s contended → ~1.0s uncontended, a real GIL-contention removal, not a measurement trick), meeting the ≤1.5s budget. But the heatmap's spinner now runs ~2.5s longer before the request fires, so the grid appears ~0.5s later in wall-clock than before. The reviewer flagged this as a NOTE (`reports/reviews/goal-ops-hardening-iter-6-review.md:43-50`). Spec-compliant (the budget is on the endpoint's own duration, which is met; the loading affordance honestly covers the window), and the spec explicitly chose the staggering approach — but worth recording as a real trade-off. OBSERVATION/GAP, not a defect.

### Test Findings

**T1 — VERIFIED: J-01 golden-script step 6 rewrite is honest and asserts on data the run produces.**
`runs/goal-session-ops-hardening/journey-scripts/J-01.json:12` — step 6 now re-visits `/data` and expects `"no new snapshots"`, replacing the stale `"2026-05-15"` `/scanner-runs` assertion buried past a 750-row fold. I confirmed both assertion strings are real, run-produced values: `"no new snapshots"` is `runStatusLabel`'s zero-work label (`apps/frontend/app/data/page.tsx:170`) and `"2 non-trading"` (step 5) is the job-outcome summary (`apps/frontend/app/data/page.tsx:2567`). A weekend-only 2026-05-02→2026-05-03 backfill is guaranteed zero-work, so both render deterministically. Independently confirmed: UT-10 (`ui-test-results.llm.md:39`) PASS shows the exact run-history row with status "no new snapshots", and deterministic replay passed 2/2 (`reports/phase-goal-ops-hardening-iter-6-regression-replay-results.md`). Minor residual: `"no new snapshots"` could also be produced by an unrelated prior zero-work run in the growing history list, so it is not perfectly run-isolated — but it IS content this run produces, near the top of a newest-first list, which is exactly what the spec's TC-6 accepted. Adequate.

**T2 — OBSERVATION: on-file QA report marks TC-9 "in progress" yet claims DoD complete.**
`reports/qa/goal-ops-hardening-iter-6-qa.md:31-38,166-175` shows TC-9 pytest "Running" while asserting PASS. Substantively fine — the DoD result (25 passed / 0 failed, 5044s) exists from the initial build, and since zero backend files changed the result cannot have regressed — but the on-file QA verdict was assembled provisionally. The reviewer already flagged the QA FAIL→PASS flip as MINOR (`reports/reviews/...-review.md:23-35`). No product impact.

**T3 — OBSERVATION (honesty): the dev's "all 11 within budget" retraction slightly over-smooths the `/evidence` cold path.**
The dev handoff's DoD self-check first (correctly) recorded 9/11 within budget, then retracted the pessimism to "all 11 within budget." That retraction is true for the warm/steady-state path but leans on reading `/evidence`'s 73s cold as "in budget" via Item I's cold-miss clause. The independent browser-qa framing — "still a real problem worth someone's attention" (`ui-test-results.llm.md:157`) — is more measured. Crucially, the dev did NOT hide the 73s figure: it is disclosed transparently in the handoff and `perf-budgets.md:1246-1254`, characterized honestly as a data-scaling one-time cost. So this is honest-but-optimistic framing, not misrepresentation — recorded so the goal-evaluator weighs the `/evidence` cold path with eyes open (see B1).

---

## 3. Domain Assessment

The core engineering claim is sound and, unusually for a latency fix, independently reproduced by a separate lane rather than taken on the dev's word:

- **Root-cause discipline is real.** The dev refined iter-5's "pure Chrome 6-connection queuing" hypothesis into two distinct mechanisms: connection-queue clearing on the Dashboard (a 250ms stagger sufficed) vs. GIL contention between two CPU-bound Python handlers on the Data Manager (`/api/data/availability` alongside `IndexVendorPanel`'s own `/api/indexes?full=true`), where only a 2500ms stagger past the contender's completion worked — and 1500ms was measured insufficient (1787ms). This is diagnosis, not guesswork, and it is documented with the concurrent-`curl` probe numbers in `perf-budgets.md:1150-1169`.
- **The fix is genuinely frontend-only and byte-identity-safe.** `git diff HEAD -- apps/backend` is empty; the only uncommitted product delta is the two frontend files (67 insertions / 21 deletions). Every serving endpoint runs identical code, so TC-5 payload byte-identity holds by construction. No new whole-table scan, no lookahead, no Data Contract change, no second/combined endpoint (the spec's central prohibition) — verified against the source, not the summary.
- **The measurement is credible in both directions.** The 555s/92s figures in the first handoff were genuinely contaminated (concurrent 84-min pytest + diagnostic curl, both disclosed in Known Issues); the independent browser-qa lane, run under cleaner conditions, got 73.5s for the same `/evidence` cold path and 0.02s warm — corroborating the contamination story while honestly refusing to bless the cold path as fully fine. The two TARGET endpoints (the actual point of the iteration) pass 3/3 in the independent lane.
- **Anti-goals hold.** AG-3 (values unchanged — zero backend diff), AG-5 (no lookahead — no scoring/forward-return code touched), AG-8 (graceful degradation — UT-03/UT-09 confirm honest page-level error, never blank/fabricated; `/evidence` cold degrades to HTTP 200 + loading state), AG-9 (no new network path). The UT-03/UT-09 "FAILs" are a pre-existing page-level error-gating architecture (the below-the-fold cards' own error branches don't fire under a full-outage precondition because the page gates them behind the top-level fetch) — confirmed unrelated to this diff and non-blank; a literal-expected-text mismatch, not a regression.

The domain logic that matters for J-06 — request scheduling behind an unchanged render contract — is correct, minimal, and does exactly what the spec scoped, no more.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT defect exists in this iteration's diff. The two frontend changes are correct, minimal, preserve every loading/error/empty/abort affordance, and are independently verified. The one substantive open item (B1, `/evidence` cold-miss) is backend, pre-existing, out of scope, and covered by a pre-existing committed budget — applying a fix here would be the exact scope creep the spec's contingent-fix discipline forbids mid-iteration. The GAP/OBSERVATION items (F3, T1 residual, T2, T3) are documented, not fixed, per the auditor rules.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied (no in-scope CRITICAL/IMPORTANT findings) |

---

## 5. Recommended Next Step

**Proceed** — this iteration's DoD is met and independently verified. J-06's two previously-violating endpoints are within budget under a real browser (3/3 each, independent lane), and the four required-still-passing journeys are green. Scope is clean and anti-goals hold.

Carry ONE gap forward to the goal-evaluator / a future iteration, not as a blocker of this one:

- **`/api/evidence` cold-miss (B1).** It is pre-existing, out of scope here, and within its committed Item I budget, but it is a real ~73s first-view stall on the accumulated dev DB the live session runs against. The remediation is already named and small: extend the ingest finalize hook to warm the 7 evidence `drawdown_expectations` keys (mirroring the existing event-study warm at `data_manager.py:3138`). This is a natural, self-contained backend iteration — recommend the decomposer schedule it before the session's GOAL_ACHIEVED gate so the last Must-have journey's `/evidence` page is snappy on first view even on a grown basis.

Also outstanding but explicitly out of this iteration's DoD (per the spec's own closure-gate reminder): both J-05's and J-06's `[NEW]`-flagged `demo.sh --session-live` walkthroughs are still owed as session-closeout showcase artifacts, or an explicit human deferral, before GOAL_ACHIEVED.
