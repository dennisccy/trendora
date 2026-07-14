# Phase goal-mcp-loop-iter-33 — Closure Verdict

**Phase:** goal-mcp-loop-iter-33
**Date:** 2026-07-14
**Written by:** phase-closure-auditor

---

**Verdict:** CLOSURE-FAIL

---

## Standard Pipeline Gate Checks

| Artifact | Status | Verdict |
|----------|--------|---------|
| Review report (`reports/reviews/goal-mcp-loop-iter-33-review.md`) | exists | PASS_WITH_NOTES |
| QA report (`reports/qa/goal-mcp-loop-iter-33-qa.md`) | exists | PASS |
| Audit report (`docs/handoffs/goal-mcp-loop-iter-33-audit.md`) | exists | PASS_WITH_GAPS |

All three formal verdicts are at an acceptable label for closure per the standard rule (PASS /
PASS_WITH_NOTES / PASS WITH GAPS). **However**, cross-referencing these reports' own claims against the
artifacts they claim satisfy them (Step 3/Step 4 diligence, below) surfaced a DoD item that none of the
three stages actually verified, despite each asserting or implying that it was — see Blocking Issues.

---

## UI Visibility Artifact Checks

| Artifact | Exists | Non-Empty | Non-Vague | Status |
|----------|--------|-----------|-----------|--------|
| implementation-summary.md | yes | yes (79 lines) | yes — specific features, config changes, limitations | OK |
| user-visible-changes.md | yes | yes (74 lines) | yes — specific capabilities, exact banner text/states | OK |
| ui-surface-map.md | yes | yes (97 lines) | yes — named routes/components, per-file classification table | OK |
| ui-test-plan.md | yes | yes (464 lines) | yes — 20 test cases (UT-01–UT-20) with exact steps/expected results | OK |
| ui-test-results.md | yes | yes (150 lines) | yes — 20/20 executed with evidence, one test disclosed as source-verified rather than screenshot-verified | OK |
| what-to-click.md | yes | yes (63 lines) | yes — 8 numbered steps with exact expected outcomes | OK |

All 6 UI visibility artifacts exist and contain substantive, specific, non-placeholder content. The new
J-20 capability (the `PreflightBanner`) itself is documented and tested to an unusually high standard —
this is not the source of the blocking finding below.

---

## Cross-Reference Checks

- [x] user-visible-changes lists ≥1 specific capability — yes, several, in detail
- [x] ui-surface-map has specific route/component entries — yes, full table with per-route "what to test"
- [x] ui-test-plan has specific steps with exact actions and expected results — yes
- [x] ui-test-results shows execution evidence — yes, 20/20 with screenshots/DOM evidence for the NEW
      capability (J-20)
- [x] what-to-click has ≥3 numbered steps with exact expected outcomes — yes, 8 steps
- [ ] **implementation-summary / QA / ux-regression claims are consistent with actual pipeline evidence —
      FAILS on one specific, material point: the "required-still-passing" deterministic-replay claim.**

### The specific inconsistency (traced end-to-end, not just narrative-level)

The phase spec's DEFINITION OF DONE (`docs/phases/goal-mcp-loop-iter-33.md`) requires:

> **Required-still-passing green:** J-01, J-02, J-04, J-05, J-11, J-13, J-18 re-verified (deterministic
> replay); the GO banner does not disrupt their surfaces. **J-11 gets a dedicated golden replay** ... to
> close the iter-32 6-of-7 replay gap.

QA's own generated functional test plan (`reports/qa/goal-mcp-loop-iter-33-test-plan.md`) correctly
operationalized this into three explicit test cases:
- **TC-24** — replay J-01 via its golden script
- **TC-25** — replay J-02 via its golden script
- **TC-26** — replay J-04, J-05, J-11, J-13, J-18 (5 journeys) via their golden scripts

None of TC-24/TC-25/TC-26 appear in the QA validation report's "Test Cases Executed" table
(`reports/qa/goal-mcp-loop-iter-33-qa.md`, which lists only TC-07, TC-09, TC-15–21, TC-29, TC-30 — 11
cases). They were designed, then silently never run, with no disclosed reason (unlike the pytest-timeout
gap on TC-01–06/08, which QA candidly explained).

Instead, the QA report asserts:
> "**Deterministic replay gate:** Will be executed in the next phase step (goal-iter-lean.sh replay lane)."

and the ux-regression report repeats the same assumption:
> "The full deterministic-replay-lane run itself (`goal-iter-lean.sh`) is noted in
> `reports/qa/goal-mcp-loop-iter-33-qa.md` as executing in the next pipeline step, after this review —
> that is expected pipeline ordering, not a gap in this report."

**I traced this claim against the actual dispatch mechanics and it is false for this iteration:**
- `docs/phases/goal-mcp-loop-iter-33.md` declares `**Depth:** full`.
- `scripts/automation/run-goal.sh` (lines ~1695–1708) routes `Depth: full` iterations through
  `run-phase.sh --no-finalize`, **not** `goal-iter-lean.sh`. Only `Depth: lean` iterations invoke
  `goal-iter-lean.sh`.
- `goal-iter-lean.sh`'s deterministic-replay machinery (`demo_runner.py --mode verify` against
  `runs/goal-session-mcp-loop/journey-scripts/*.json`, writing
  `reports/phase-<iter>-regression-replay-results.md`, merged via `merge_ui_test_results.py`) is the ONLY
  place in this codebase that mechanism lives. `run-phase.sh` has zero references to `REQUIRED_JOURNEYS`,
  `demo_runner`, `journey-scripts`, or "required-still-passing" (confirmed by grep) — it is entirely
  unaware of the concept.
- Confirmed on disk: **no** `reports/phase-goal-mcp-loop-iter-33-regression-replay-results.md` file
  exists; **no** `UT-J-01`/`UT-J-02`/`UT-J-04`/`UT-J-05`/`UT-J-13`/`UT-J-18` row appears anywhere in
  `reports/phase-goal-mcp-loop-iter-33-ui-test-results.md` (that file contains only the J-20-specific
  UT-01–UT-20 rows).
- The browser-qa-agent's **actual dispatch prompt** for this iteration (read directly from
  `runs/goal-session-mcp-loop/trace/trace.jsonl`, step 278) instructs it only to "Execute the test plan:
  For each UT-XX test case..." against `ui-test-plan.md` — it was never asked to replay or verify J-01,
  J-02, J-04, J-05, J-13, or J-18.
- The only one of the seven required-still-passing journeys that received genuine, direct re-verification
  this iteration is **J-11** — the developer ran `demo_runner.py --mode verify --journeys J-11` directly
  and got a real PASS (documented in `docs/handoffs/goal-mcp-loop-iter-33-dev.md`), per the plan's
  explicit instruction to close the iter-32 gap.
- **J-04, J-13, and J-18 specifically were not even incidentally visited this iteration** — none of the 20
  UT-XX browser tests navigate to `/research/registry` (J-18's surface) or exercise `/data`'s
  availability-heatmap legend (J-13's surface) or the regime-conditioned evidence check (J-04's surface;
  `/data` was visited only for a generic "no visual collision" check in UT-08, and `/research` only for a
  banner-presence check in UT-07). J-01/J-02/J-05 got partial, incidental coverage (their pages loaded and
  their badges/tables were confirmed visually un-obscured by the new banner via UT-02/UT-03/UT-05/UT-10),
  which is real but materially short of "re-verified."
- Neither the reviewer nor the auditor caught this. This is a direct repeat of the exact failure class the
  **iter-32 audit** explicitly named and used as its sole reason for a PASS_WITH_GAPS verdict (there, only
  **one** journey, J-11, silently fell through with no test coverage and no disclosed reason; the iter-32
  auditor characterized this as "a real coverage gap" that "should not silently accumulate"). This
  iteration, the same failure mode recurs at a **larger scale** (six journeys, not one) and is compounded
  by an affirmatively incorrect claim about compensating verification that structurally cannot occur in
  this iteration's own dispatch path.

**Risk assessment (why this is fixable, not catastrophic):** the actual product risk is likely low — the
diff this iteration touches only `readiness.py`/`health.py`/`config.py`/`config.yaml` (backend) and
`lib/api.ts`/`readiness-provider.tsx`/`preflight-banner.tsx`/`layout.tsx` (frontend); none of J-01/J-02/
J-04/J-05/J-13/J-18's own business-logic files were touched, and the ux-regression report's diff-level
check on `layout.tsx` (a clean 2-line addition, banner in normal document flow, cannot overlap `<main>`)
is genuine, credible evidence of low risk. This is a **process/evidence gap, not a known or likely
regression** — but the DoD requires the re-verification to actually happen, not merely to be low-risk in
retrospect, and the specific artifacts in this pipeline claim it happened (or will happen) when it
provably did not and structurally cannot in this dispatch path.

---

## Blocking Issues

1. **DoD item "Required-still-passing green ... re-verified (deterministic replay)" was not satisfied for
   6 of 7 journeys (J-01, J-02, J-04, J-05, J-13, J-18), and the QA/ux-regression reports contain a
   materially false claim about why this is acceptable.**

   **Remediation:** Run the deterministic replay against the golden scripts that already exist on disk
   for all six journeys (confirmed present: `runs/goal-session-mcp-loop/journey-scripts/{J-01,J-02,J-04,
   J-05,J-13,J-18}.json`) — this is cheap (a few minutes; not the multi-hour `loaded_engine` pytest cost
   that was reasonably tolerated elsewhere in this iteration). With both services running
   (frontend `http://localhost:3255`, backend `http://localhost:8255`):

   ```bash
   cd /home/dennis-chan/Git/trendora && python3 scripts/automation/lib/demo_runner.py --mode verify \
     --scripts-dir runs/goal-session-mcp-loop/journey-scripts \
     --journeys J-01,J-02,J-04,J-05,J-13,J-18 \
     --results reports/phase-goal-mcp-loop-iter-33-regression-replay-results.md \
     --evidence-dir reports/qa/goal-mcp-loop-iter-33-evidence \
     --base-url http://localhost:3255 \
     --phase-id goal-mcp-loop-iter-33 \
     --repo-root /home/dennis-chan/Git/trendora
   ```

   Exit code `0` = all six pass cleanly. Exit code `5` = one or more flagged a possible regression (the
   flagged journey IDs are extractable from FAIL rows in the results file) — in that case, dispatch
   browser-qa-agent against QA's own pre-written TC-24/TC-25/TC-26 (`reports/qa/
   goal-mcp-loop-iter-33-test-plan.md`) to re-confirm via the LLM lane (mirrors `goal-iter-lean.sh`'s own
   fallback behavior on a replay flag) and have the developer fix any genuine regression found.

   Then fold the result into `reports/phase-goal-mcp-loop-iter-33-ui-test-results.md` (or attach the new
   file alongside it) so the DoD item has real, on-disk evidence, and correct the QA/ux-regression reports'
   "will run in the next phase step (goal-iter-lean.sh replay lane)" claim — that step does not exist for a
   `Depth: full` iteration (which dispatches via `run-phase.sh`, confirmed by reading
   `scripts/automation/run-goal.sh`'s depth-routing logic). Re-run phase-closure-auditor once this evidence
   exists.

---

## Non-Blocking Notes

These are already well-disclosed and reasonably triaged by review/audit; listed here only for
completeness, not as reasons for CLOSURE-FAIL:

- **B1** (review + audit, GAP): `record_verdict_transition` fires unconditionally in `health()`; no
  autouse `conftest.py` fixture redirects `READINESS_VERDICT_HISTORY_PATH`, so ordinary suite runs append
  to the untracked `preflight-verdict-history.jsonl`. Confirmed untracked (not corrupting a committed
  artifact) by the auditor. Recommended follow-up: autouse fixture.
- **B2** (review + audit, GAP): `compute_preflight` re-invokes `compute_readiness` instead of accepting an
  already-computed dict — doubles a bounded, indexed query on the ~2s poll path. Deterministic and
  harmless; auditor confirmed no whole-table load is introduced (anti-goal #8 not violated). Efficiency-only
  follow-up.
- **T1** (review + audit, GAP — closed by independent verification): 18-of-25 new backend tests in
  `test_readiness.py`/`test_health.py` were not formally pytest-confirmed in-session (the shared
  `loaded_engine` fixture takes 30–60+ min, a documented pre-existing project characteristic). The auditor
  independently exercised the real `compute_preflight` against a lightweight substitute engine and
  confirmed all 8 fixture-matrix rows, config-wiring, byte-identity, and error cases match expected
  results exactly, plus ran the 8 non-`loaded_engine` tests directly (8 passed). Recommend backgrounding
  the canonical pytest run to convert this to an in-pipeline PASS on record, but the substantive
  correctness risk is closed.
- **T2** (audit, OBSERVATION): QA report's TC-29 prose overclaims that freshness "uses the SPY trading-day
  calendar" — the implementation actually hardcodes `age_days = 0` against the latest-data reference (a
  correct, in-scope design per the phase's own NOTES on the offline/deterministic seed), so this is a
  prose inaccuracy only, no code impact.
- UT-15 (browser QA) is disclosed as source-verified rather than screenshot-verified (the Chrome MCP tool
  has no network-throttle action to catch the millisecond-scale loading-state window) — transparent,
  reasonable, and structurally well-argued (React's render order guarantees the loading branch on first
  paint).
- A minor, non-reproduced cosmetic screenshot artifact (a stale hover-tooltip fragment on one NO-GO
  capture) — noted by browser-qa as transparency only, not asserted on by any test case.
- ux-regression's own minor stylistic note: loud DEGRADED/NO-GO banners lack an icon, unlike `/data`'s
  error card — cosmetic only, not required by goal.md, explicitly not worth blocking on.
