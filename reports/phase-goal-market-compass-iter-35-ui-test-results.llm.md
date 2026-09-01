# Goal Iteration 35 (market-compass) — UI Test Results

**Phase:** goal-market-compass-iter-35
**Date:** 2026-09-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- Lean goal-mode dispatch: only J-12 (target journey) is browser-driven this run.
     J-01..J-08 (required-still-passing) are covered by deterministic replay per the
     dispatch instructions and are NOT re-tested here. -->

**Overall:** 1/1 tests passed (0 skipped, 0 failed)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-12 | Every frozen selection disposition is true — the leadership floor is the only inclusion gate, and a caution qualifier moves no membership | regression/correctness | P1 | At the frontier as-of (`2026-08-12`, latest manifest v8), the Next-session focus section's candidate count, the summary's focus-count sentence, and `GET /api/compass`'s `selection.candidates` length all agree; the manifest strip's audit table shows zero `comparison_cohort` rows with `leadership_score >= 80.0` labelled `below_selection_floor` (all such rows show `excluded_by_cap`); a candidate that misses an advisory qualifier (entry or risk) renders a caution citing the threshold and actual value, never a false "clears" reason | Verified via Chrome MCP against `http://localhost:3255/`: summary sentence reads "10 names worth monitoring next session."; `GET /api/compass` (port 8255, same backend) returns `selection.candidates` length 10 and `disposition_tally: {below_selection_floor: 502, excluded_by_cap: 27}` (502+27+10=539, matches goal file's predicted partition); HPE (leadership 92.71) renders as a candidate with checklist row `entry_min_score` tagged `gating: false`/verdict `Miss` and caution text "ENTRY_QUALITY_QUALIFIER: Entry Quality score 21.5 is below the 70.0 qualifier (Weak entry) -- advisory only; Leadership alone determines candidacy."; CRL renders as a candidate despite failing BOTH entry and risk qualifiers; opened the "Audit table — comparison cohort (529) + near-threshold shadow (25)" details element and, via DOM query over all 529 rendered rows, confirmed 0 rows have `leadership >= 80.0` AND disposition text containing "below"; DXCM (leadership 85.0) shows disposition "excluded by cap"; belowFloorCount 502 / excludedByCapCount 27 exactly match the API tally | PASS | `reports/qa/goal-market-compass-iter-35-evidence/UT-J-12-result.png` |

---

## Passed Tests

### UT-J-12 — Every frozen selection disposition is true (leadership floor is the only inclusion gate)

**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-35-evidence/UT-J-12-result.png`

**Preconditions:** Backend running on port 8255 (confirmed `/api/health` reachable and serving the same manifest data verified in the dev handoff); frontend running on port 3255 (`FRONTEND_URL`), configured to talk to the same backend. `GET /api/compass` (no `asof`) confirmed the frontier (`2026-08-12`) now serves the newly minted, corrected `v8` manifest (not the pre-fix mislabeled `v7`) — `latest_manifest_for_date` behavior described in the dev handoff.

**Steps executed (journey steps from `docs/goal.md` J-12, mapped to this browser-testable slice — step 7 "Re-verify end to end at the frontier as-of" and the Walkthrough acceptance limb; steps 1-6 and 8 are backend-only engine/test work already covered by the dev handoff and unit-test run):**

1. Navigated to `http://localhost:3255/` (no `asof` param → frontier as-of `2026-08-12`).
2. Confirmed the system strip shows "Data as-of 2026-08-12" and the Summary card's focus-count sentence reads "10 names worth monitoring next session."
3. Queried `GET http://localhost:8255/api/compass` directly (same backend the frontend talks to) and confirmed `selection.candidates` length is 10, `disposition_tally` is `{below_selection_floor: 502, excluded_by_cap: 27}`, and `comparison_cohort` (529 rows) has 0 rows with `leadership_score >= 80.0` AND `selection_disposition == "below_selection_floor"` — the served data is the corrected `v8` manifest, matching the dev handoff's live-verification numbers exactly (502+27+10=539).
4. On the rendered Next-session focus section, inspected the HPE candidate card: Leadership "Elite leader (92.7)", Entry "Weak entry (21.5)", Risk "Very low risk (58.9)"; Why lists only the leadership and risk "clears" statements (no false entry-clears claim); Cautions include "ENTRY_QUALITY_QUALIFIER: Entry Quality score 21.5 is below the 70.0 qualifier (Weak entry) -- advisory only; Leadership alone determines candidacy."; opened HPE's "Eligibility checklist" details and confirmed the `entry_min_score` row shows verdict "Miss" tagged non-gating (advisory) while `leadership_min_score` shows "Pass" (gating) — reproducing J-04's checklist/inclusion contract under the corrected rule.
5. Confirmed CRL (leadership 86.2, entry 23.6 Miss, risk 64.2 Miss — both qualifiers failing) still renders as a candidate, not excluded — proving the leadership floor alone is the gate, per the Error-cases requirement in the iteration spec's Testing Requirements.
6. Opened the manifest strip's "Audit table — comparison cohort (529) + near-threshold shadow (25)" `<details>` element (this is the manifest strip's expanded table referenced in J-12's Acceptance). Programmatically enumerated all 529 rendered `<tbody>` rows (columns: Ticker, Leadership, Entry, Risk, Setup, Sector, Disposition): 0 rows have `leadership >= 80.0` with a "below"-labelled disposition; 502 rows show "below selection floor"; 27 rows show "excluded by cap" — exactly matching the API's `disposition_tally`. Spot-checked DXCM (leadership 85.0, above the floor): disposition cell reads "excluded by cap" — the walkthrough's required example of "an above-floor name no longer labelled 'below the selection floor'".
7. Confirmed the near-miss/why-not list (below the focus cards) explicitly narrates the same fact for cap-excluded names, e.g. "DXCM — passed every qualifier, cut only by the focus-list cap."
8. Took one screenshot at the acceptance state (candidate count sentence + HPE/GRMN/NTAP/ABNB candidate cards with cautions visible), saved to the evidence path above.

**Result:** All observed values match J-12's Acceptance text and the dev handoff's live-verification claims. No mislabeled row found anywhere in the rendered UI or the served API response.

---

## Failed Tests

None.

---

## Skipped Tests

None. J-01 through J-08 (required-still-passing) were intentionally NOT re-driven through the browser this run per the goal-mode lean dispatch instructions — they are covered by a separate deterministic replay pass (evidence already present at `reports/qa/goal-market-compass-iter-35-evidence/J-01-verify.png` … `J-08-verify.png`), not by this browser-qa-agent invocation.

---

## Golden replay script

Wrote a self-contained deterministic replay script for J-12 to
`runs/goal-session-market-compass/journey-scripts/J-12.json` (schema-validated via
`demo_runner.py --mode lint`, result: `J-12 ok`):
- Step 1: `goto /` → expect "10 names worth monitoring next session."
- Step 2: click "Eligibility checklist" → expect "ENTRY_QUALITY_QUALIFIER"
- Step 3: click "Audit table — comparison cohort (529) + near-threshold shadow (25)" → expect "excluded by cap"

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (confirmed via `ps aux`; same port used in the dev handoff's live verification)
- **Browser:** Chrome via MCP (headless, pinned profile)
- **Test Date:** 2026-09-01
- **Evidence directory:** `reports/qa/goal-market-compass-iter-35-evidence/`
