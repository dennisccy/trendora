# Phase goal-ops-hardening-iter-7 — UX Regression Review

**Date:** 2026-07-21

**Verdict:** UX-REGRESSION-FAIL

---

## Summary

This iteration ships zero frontend file changes and zero new user-facing capability — it is a pure
ingest-time warm fix for `/evidence`'s "expected drawdown" panels, and on that narrow scope it is clean:
the fast-first-view improvement and the new "drawdown expectations" phrase in the Data Manager's
"Refreshed:" line both surface automatically through existing generic renderers, with no navigation gap.

However, the browser-qa-agent's own RAW results (`reports/phase-goal-ops-hardening-iter-7-ui-test-results.llm.md`)
record a **confirmed regression** in J-05 ("Aggregates are precomputed at ingest, never on the fly") — a
Required-still-passing journey per this iteration's own phase spec metadata, and a journey whose
`journey-history.json` entry shows `status: "passing"` as of iter-6. During a heavy ingest job, the backend
became **completely unresponsive for 7+ minutes** (`GET /api/health` connection-timeout), a hard, directly
observed violation of J-05's own acceptance clause ("poll GET /api/health; assert it stays responsive
throughout"). The browser-qa-agent explicitly attributes at least partial causation to this iteration's own
diff: the new `drawdown_expectations` warm step adds "one more memory-hungry synchronous computation to the
ingest finalize hot path, making the ingest path more likely to be the trigger" (llm.md, line 124) — and this
iteration's diff is the only change to the exact shared component (`_refresh_ingest_aggregates`,
`apps/backend/app/engine/data_manager.py`) that both J-05's ingest path and J-04's boot/readiness contract
run through.

This finding is being **masked, not surfaced**, in the two downstream artifacts that gate the pipeline:
- The merged `reports/phase-goal-ops-hardening-iter-7-ui-test-results.md` states **`Browser QA Verdict: PASS`**
  and **"11/13 journeys passed"** at the top, even though its own results table three lines down marks
  `UT-J-05` as **FAIL**.
- `reports/qa/goal-ops-hardening-iter-7-qa.md` (written 07:15, after both the raw llm.md at 06:58 and the
  merged file at 06:59) states **`Verdict: PASS`** and does not mention J-05, the health hang, or the
  `MemoryError` anywhere in its 296 lines.

This is precisely the failure mode this session's own accumulated lesson (quoted verbatim in
`docs/phases/goal-ops-hardening-iter-7.md`'s BACKGROUND section) warns against: *"(iter-6) always cross-check
the merged QA verdict against the RAW `ui-test-results.llm.md` browser-qa verdict, and never let a page's
'warm' reading stand in for its FIRST view after a state-changing action."* The raw verdict is FAIL. The
merged and QA verdicts say PASS. That discrepancy, on a journey this severe, is itself a process-integrity
problem on top of the underlying product regression.

---

## New Capability Discoverability

No new capability was shipped this iteration (confirmed by `reports/phase-goal-ops-hardening-iter-7-user-visible-changes.md`
and the plan's own "New user-facing capability: None" line). The two user-visible effects are both
discoverability non-issues:

- **`/evidence` fast first view** — same page, same nav entry (sidebar → Evidence, 1 click), no new
  affordance needed; purely a latency change. Confirmed live by browser-qa (UT-01/UT-02, PASS).
- **"drawdown expectations" phrase in the Data Manager "Refreshed:" line** — appears automatically via the
  pre-existing generic `aggregates_refreshed.map(a => a.replace(/_/g," ")).join(", ")` renderer already
  shipped in `BackfillBreakdown` (per prior-phase work); no frontend code change was needed or made.
  Confirmed live in three places (live Job progress panel UT-02, persisted-run fallback UT-03, Run History
  row UT-04), all PASS, all reachable at the existing `/data` route (sidebar → Data, 1 click).

No hidden or undiscoverable capability to flag here.

---

## Regression Risk

| Shared component | Prior feature it serves | This iteration's change | Risk level | Observed outcome |
|---|---|---|---|---|
| `_refresh_ingest_aggregates` (`apps/backend/app/engine/data_manager.py`), the ingest finalize hook | **J-05** — "Aggregates are precomputed at ingest, never on the fly," specifically its "health stays responsive throughout a heavy ingest" acceptance clause (passing as of iter-6, `journey-history.json`) | Added a new non-fatal per-claim warm step (`drawdown_expectations`) calling `forward_testing.compute_drawdown_expectations_cached` synchronously inside the SAME finalize hook, for every claim in the evidence ledger | **High** | **CONFIRMED FAIL** — `GET /api/health` unresponsive for 7+ min during a heavy ingest; backend needed a manual restart (`reports/phase-goal-ops-hardening-iter-7-ui-test-results.llm.md`, UT-J-05 section) |
| Same finalize hook / boot-readiness health surface | **J-04** — "Non-blocking boot with visible status," specifically its contract that the frontend shows an honest, distinct state ("Backend unavailable" / "NO-GO") whenever the backend is genuinely unreachable | Not directly touched, but exercised as a side effect of the J-05 hang | **Medium** | **Degraded, not broken**: while `/api/health` was hanging (not erroring), `/data`'s badge showed an indefinite **"Checking backend… / Checking board status…"** state rather than the honest "Backend unavailable" state J-04 itself verified minutes earlier in the SAME QA run (llm.md, UT-J-05 step 6). J-04's own steps still passed on their own (a clean kill produces the honest state fast) — but the badge/health-check UI has no observed timeout fallback for the "hanging, not erroring" case, which is exactly the failure shape this iteration's diff produces. |
| `BackfillBreakdown` / `aggregates_refreshed` generic renderer (`/data`) | J-06 (this iteration's own target) and the pre-existing rendering of `latest_snapshot`/`coverage`/`membership_timeline`/`market_phase`/`forward_aggregates`/`research_hot_keys` | Additive list value only, no renderer code change | **Low** | Verified unaffected: UT-03/UT-04 confirm all pre-existing categories render in original order with the new one appended last |

**Attribution note (carried from the QA evidence, not reinterpreted):** the browser-qa-agent itself
documents that the backend's `memory_cap_mb=6144` ceiling was already marginal before this iteration —
earlier, unrelated `MemoryError` tracebacks from `GET /api/backtest` predate this test in the same log. The
regression is therefore **not cleanly proven to be solely caused by this iteration's diff** — but it is
squarely a **regression in this iteration's release**, on the exact shared code path this iteration modified,
observed on the exact journey (J-05) whose passing status this session had already certified. Per this
agent's charter, this is reported as what it is: a directly observed, reproducible failure of a
Required-still-passing journey coincident with a change to the shared component that journey depends on —
attribution ambiguity is not grounds to downgrade the verdict.

---

## UI vs Backend Parity

| Backend capability | UI exposure | Gap? |
|---|---|---|
| `drawdown_expectations` ingest-time warm (new) | `/evidence` first-view latency (implicit, no visible indicator) + `/data` "Refreshed:" line (explicit, all 3 surfaces) | None — both effects are visible where expected |
| `aggregates_refreshed` list gains one new legal value | Picked up automatically by the existing generic renderer, no frontend diff needed | None |

`user-visible-changes.md`'s own "Not Visible Yet" section correctly states "None" — consistent with the
implementation-summary.md's "Backend-Only Items: None." No parity gap on the feature this iteration shipped.

The parity gap that DOES exist is not about a missing feature but about a missing **honest failure state**:
the backend gained new synchronous ingest-time work with no corresponding frontend safeguard (e.g., a health
poll timeout that falls back to the "Backend unavailable" state) for the case where that new work causes the
backend to hang rather than cleanly go down. This is a gap between what J-04 already promises users
("visible, honest status always") and what actually happened under this iteration's load pattern.

---

## Flags

### Hidden Capabilities
- None. No new capability shipped this iteration to hide.

### Undiscoverable Capabilities
- None.

### Potential Regressions
- **CONFIRMED, not merely potential: J-05 ("Aggregates are precomputed at ingest, never on the fly") FAILED
  this iteration's browser QA.** Shared component: `_refresh_ingest_aggregates`
  (`apps/backend/app/engine/data_manager.py`), the ingest finalize hook this iteration extended. Risk
  realized: `GET /api/health` was completely unresponsive for 7+ minutes during a heavy ingest job — a
  direct, explicit violation of J-05's own acceptance clause. Evidence:
  `reports/phase-goal-ops-hardening-iter-7-ui-test-results.llm.md` (UT-J-05 section, lines 105-124),
  screenshot `reports/qa/goal-ops-hardening-iter-7-evidence/J-05-backend-hung-checking.png`. Prior passing
  status confirmed in `runs/goal-session-ops-hardening/state/journey-history.json` (`J-05.status: "passing"`,
  `last_passing_iter: "goal-ops-hardening-iter-6"`).
- **Related UX degradation on J-04's shared health-status surface:** while the backend was hung (not down),
  `/data`'s badge showed an indefinite, non-actionable **"Checking backend… / Checking board status…"** state
  instead of the honest "Backend unavailable / NO-GO" state that the SAME QA run had just verified J-04
  produces on a clean kill. Users have no signal during a hang — a worse experience than an honest error.
  Evidence: `reports/phase-goal-ops-hardening-iter-7-ui-test-results.llm.md`, UT-J-05 step 6 (line 116).
- **Verdict-reporting masking, flagged for process integrity, not as a product defect:** the merged
  `reports/phase-goal-ops-hardening-iter-7-ui-test-results.md` (`Browser QA Verdict: PASS`, "11/13 journeys
  passed") and `reports/qa/goal-ops-hardening-iter-7-qa.md` (`Verdict: PASS`, no mention of J-05 at all) both
  contradict the RAW browser-qa-agent output
  (`reports/phase-goal-ops-hardening-iter-7-ui-test-results.llm.md`, `Browser QA Verdict: FAIL`, with an
  explicit inline comment naming J-05 as the sole cause of the FAIL). This is the exact discrepancy this
  session's own carried-forward lesson (phase spec BACKGROUND, "(iter-6)") instructs every downstream reader
  to catch before trusting a merged/QA verdict.

### Visual Consistency
- Not applicable — zero frontend files changed this iteration (confirmed: `git diff --stat` scope per
  `docs/handoffs/goal-ops-hardening-iter-7-dev.md`'s "Files Changed" list contains no `apps/frontend/**`
  path). No new pages or arbitrary-value styling to assess.

---

## Recommendation

1. **Do not let this iteration's PASS verdict stand as-is.** Route this back through the loop (developer/
   auditor) to investigate and fix the ingest-path memory/hang regression before J-06 (or the session) is
   declared closed. The mechanism this iteration shipped (the `drawdown_expectations` warm step itself) is
   verified correct in isolation (byte-identical output, honest gating, per-claim isolation) — the problem is
   its interaction with an already-marginal memory ceiling under a heavy, back-to-back ingest load pattern,
   which the QA evidence itself flags as "making the ingest path more likely to be the trigger."
2. **Reconcile the verdict-reporting discrepancy as its own action item**, independent of the product fix:
   the merge step that produced `reports/phase-goal-ops-hardening-iter-7-ui-test-results.md`'s "PASS" header
   over a table containing a FAIL row, and the QA step that produced `reports/qa/goal-ops-hardening-iter-7-qa.md`'s
   "PASS" with zero mention of J-05, both need to surface (not average away) a Required-still-passing
   journey's FAIL.
3. **Consider a frontend-side follow-up** (out of THIS iteration's scope, but worth a future decomposer note):
   the health-status badge that already distinguishes "Initializing…" from "Backend unavailable" (J-04) has no
   observed behavior for "health check is hanging, not erroring" — a timeout-based fallback to the honest
   unreachable state would prevent the indefinite "Checking backend…" state users saw during this iteration's
   QA run.

No action is needed on the discoverability or UI-vs-backend-parity dimensions — those are clean this
iteration.
