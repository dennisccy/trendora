# UI Test Results (merged)

**Date:** 2026-09-01
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 8/13 journeys passed (0 skipped, 1 required-missing)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-38-evidence/J-01-verify.png |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | Steps 1-5 all render correctly, including the explicit no-prior-run state at the earliest stored session | Steps 1-4 verified correct (header, ordering, thresholds, suppressed-count, spot-checked sector rank + stock bucket move). Step 5 (navigate to the earliest stored run) crashes the entire page with a client-side TypeError instead of rendering the no-prior-run state | FAIL | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-02-fail.png` |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | regression | P1 | Steps 1-2 render correctly on the latest as-of; step 6 (retrospective view) shows the retrospective stamp | Steps 1-2 verified correct (summary sentences render, "Show cited facts" discloses template ids + facts, spot-checked regime_score and severity byte-match `/api/dashboard` and `/api/market-phase`). Step 6 (retrospective as-of, e.g. `?asof=2025-04-15`) crashes the entire page with the same TypeError instead of showing the summary + retrospective stamp | FAIL | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-03-fail.png` |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | happy-path | P1 | Candidate count/detail/checklist/why-not distances match `GET /api/compass`+`/api/stocks`; Risk-off caution renders on candidates at a Risk-off as-of | Verified on frontier (2026-08-12): 10 candidates match; HPE card (Leadership 92.7, Entry 21.5, Risk 58.9) matches `/api/stocks`; checklist shows Pass/Miss verdicts; why-not entries show rank/cap/distances. Risk-off verified at `?asof=2005-04-15`: regime badge "Risk-off", every candidate carries `REGIME_RISK_OFF` caution, "worth monitoring next session" framing, no entry-advice wording | PASS | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-04-result.png`, `UT-J-04-riskoff-result.png` |
| UT-J-05 | Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | happy-path | P1 | Manifest strip shows mode/version/frozen/prospective-eligible/hashes/dataset/universe stamps; requesting an old stored date with no manifest mints exactly one retrospective manifest | Frontier manifest strip shows all required stamps (at ingest, version 10, frozen, not prospective-eligible, engine/candidate/cohort/manifest-config hashes, dataset stamp r3160-f6815424, universe pool 539 members/profile core, Basis: available, versions v1–v10 listed). `GET /api/compass?as_of=2005-04-15` (never-manifested date) minted exactly one manifest: version 1, frozen true, mode retrospective, prospective_eligible false, producer on_demand_get — matches acceptance | PASS | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-05-result.png` |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | happy-path | P1 | Regenerate control opens a confirm dialog stating immutability guarantees; Cancel performs no mutation; multiple versions listed with stamps | Clicked `compass-manifest-regenerate-button` on `?asof=2005-04-15` → dialog "Confirm manifest regenerate" reads "This mints a NEW manifest version... The existing version is never touched, changed, or deleted — it stays byte-identical and readable." Clicked Cancel; re-fetched `/api/compass?as_of=2005-04-15` → version still 1, versions list length still 1 (no mutation). Frontier versions list (v1–v10) already renders with per-version stamps as static, non-interactive `<li>` rows | PASS | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-06-result.png` |
| UT-J-07 | The Today page answers the ten-second read from served values only | happy-path | P1 | Body renders state-band → summary → what-changed → leadership-rotation → focus → manifest strip, in that order, with readiness/preflight in chrome above; tile values match `/api/dashboard` and `/api/market-phase`; cross-view chart absent from `/`, present on `/market` | DOM testid order confirmed exactly: `compass-state-band-card` → `compass-summary-card` → `compass-whatchanged-card` → `compass-leadership-rotation-section` (sector/theme only, no stock-kind row) → `compass-focus-section` → `compass-manifest-strip`, with `readiness-badge`/`preflight-banner` before all of them. Regime 73.18 / Risk-on matches `/api/dashboard`; phase Expansion / severity 25.85 / P(bear) 0.0017 matches `/api/market-phase`. Summary sentence "Universe breadth: 59.8%... 66.4%..." matches served breadth fields verbatim. `phase-cross-view-chart` testid present only on `/market`, absent on `/`, with a "Full market context... →" link-out to `/market` | PASS | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-07-result.png` |
| UT-J-08 | The market surface relocates intact and history never lies | happy-path | P1 | `/market` renders full former dashboard inventory (Top Sectors, Top Themes, Candidate Counts, Market Phase & Severity, breadth cards); sidebar order/highlighting correct; historical `?asof=D` renders D's stored values with a visible retrospective label | `/market` confirmed to contain "Top Sectors", "Top Themes", "Candidate Counts", "Market Phase & Severity", "More detail" (all present in DOM); sidebar Today-then-Market order and `aria-current="page"` highlighting both correct; `/market?asof=2026-08-11` renders fine (no crash — Market page does not touch the new compass fields). **However**, the Today page's (`/`) own required historical-navigation behavior is broken: `/?asof=2026-08-11` (an actual incident date with a real manifest, used by J-11), `/?asof=2025-04-15` (J-05/J-06's own reference date) and `/?asof=2026-03-30` all crash with "Something went wrong on this page" instead of showing D's stored values / retrospective label / predecessor comparison — see Critical Finding above | FAIL | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-11-fail.png` (same crash class, `/?asof=2026-08-11`), `UT-J-08-result.png` (working `/market` page) |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-38-evidence/J-10-verify.png |
| UT-J-11 | Incident-bounded clean regeneration of derived state (serving verification only — J-11 itself is CLOSED/PASSING per owner ruling; this run re-verifies the two-URL basis-disclosure check its own golden script uses) | regression | P1 | `/?asof=2026-08-11` shows "Basis: rebuilt"; `/?asof=2026-08-12` shows "Basis: available" | `/?asof=2026-08-12` (latest) correctly shows "Basis: available" in the manifest strip. `/?asof=2026-08-11` — the actual J-10/J-11 incident date, which does carry a real stored manifest whose API payload correctly reports `basis.status: "rebuilt"` — crashes the page before any content renders (confirmed deterministic: retried via the error boundary's "Try again" button, crashed identically). The basis-disclosure UI cannot be visually verified for this date this iteration | FAIL | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-11-fail.png`, `UT-J-11-retry.png` |
| UT-J-12 | Every frozen selection disposition is true -- the leadership floor is the only inclusion gate, and a caution qualifier moves no membership | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-38-evidence/J-12-verify.png |
| UT-J-13 | "Leadership rotation" says which way, shows both directions, and stops repeating What-changed | happy-path | P1 | Rotation section (sector+theme, no stock row) with signed deltas/direction words/accounting lines matching `/api/sectors`+`/api/themes`; stepping to the earliest stored session renders the rotation block's honest no-prior-run state | On frontier: `compass-leadership-rotation-section` renders exactly as specified — "Sector rotation" gaining (Regional Banks (SPDR) 13→10 (-3)·improving, Bitcoin Miners (Valkyrie), Real Estate, Banks (SPDR), Technology) and losing (Home Construction (iShares) 21→25 (+4)·deteriorating, Materials) sides, "7 of 31 shown · 24 below threshold · 0 beyond the display cap."; "Theme rotation" similarly with "2 of 11 shown · 9 below threshold · 0 beyond the display cap."; no stock-kind row present. **Step 7 fails**: stepping to `?asof=1996-01-02` (the earliest stored session, which also has an empty candidate list / `candidates_empty_reason`) crashes the whole page via the same `selection.why_not_totals` bug described in the Critical Finding — the required no-prior-run rotation state is never reached | FAIL | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-13-result.png` (frontier, passing part), `UT-J-13-fail.png` (step-7 crash) |
| UT-J-14 | "Not priority" names its real reason — the why-not block stops claiming a qualifier pass it never checked, and the actually-near-miss names come back | happy-path | P1 | Zero why-not entries claim "passed every qualifier, cut only by the focus-list cap." when their stored row fails an advisory qualifier; each entry states its true `reason` (`excluded_by_cap`/`below_selection_floor`) with threshold/actual/distance and, for cap-excluded entries, its rank + cap; disclosure header shows both uncapped totals | `GET /api/compass` selection.why_not: 20/20 entries have non-empty `failed_conditions` (was 20/20 empty pre-fix); DXCM entry matches TC-1 exactly (reason excluded_by_cap, cap_rank 11, cap 10, entry_min_score 26.5 vs 70.0 distance 43.5, gating:false); EXPE entry matches TC-3 shape (reason below_selection_floor, leadership_min_score gating:true distance 0.19, plus advisory misses). `why_not_totals`: excluded_by_cap_uncapped=27, below_floor_in_band_uncapped=25 (matches the spec's measured baseline). Rendered page: disclosure header literally reads "Not priority (20 shown of 52 held back — 27 cap-excluded, 25 below-floor near-miss)"; zero occurrences of "passed every qualifier" anywhere on the page (grepped full rendered HTML) | PASS | `reports/qa/goal-market-compass-iter-38-evidence/UT-J-14-result.png` |

## Missing Required Journeys

_Required-still-passing journeys named in the iteration spec that were NOT verified this iteration — either no lane (deterministic replay or LLM browser-qa) produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-40 lesson: this is exactly how required journeys shipped with zero evidence while every gate reported clean)._

- `UT-J-09` — no test case executed for J-09 by any lane

## Failed Tests

### UT-J-02 — "What changed" reports meaningful session-over-session deltas with honest empties

**Verdict:** FAIL
**Failure:** Steps 1-4 verified correct (header, ordering, thresholds, suppressed-count, spot-checked sector rank + stock bucket move). Step 5 (navigate to the earliest stored run) crashes the entire page with a client-side TypeError instead of rendering the no-prior-run state
**Evidence:** ``reports/qa/goal-market-compass-iter-38-evidence/UT-J-02-fail.png``

### UT-J-03 — The plain-English summary is deterministic, cited, and never invents a cause

**Verdict:** FAIL
**Failure:** Steps 1-2 verified correct (summary sentences render, "Show cited facts" discloses template ids + facts, spot-checked regime_score and severity byte-match `/api/dashboard` and `/api/market-phase`). Step 6 (retrospective as-of, e.g. `?asof=2025-04-15`) crashes the entire page with the same TypeError instead of showing the summary + retrospective stamp
**Evidence:** ``reports/qa/goal-market-compass-iter-38-evidence/UT-J-03-fail.png``

### UT-J-08 — The market surface relocates intact and history never lies

**Verdict:** FAIL
**Failure:** `/market` confirmed to contain "Top Sectors", "Top Themes", "Candidate Counts", "Market Phase & Severity", "More detail" (all present in DOM); sidebar Today-then-Market order and `aria-current="page"` highlighting both correct; `/market?asof=2026-08-11` renders fine (no crash — Market page does not touch the new compass fields). **However**, the Today page's (`/`) own required historical-navigation behavior is broken: `/?asof=2026-08-11` (an actual incident date with a real manifest, used by J-11), `/?asof=2025-04-15` (J-05/J-06's own reference date) and `/?asof=2026-03-30` all crash with "Something went wrong on this page" instead of showing D's stored values / retrospective label / predecessor comparison — see Critical Finding above
**Evidence:** ``reports/qa/goal-market-compass-iter-38-evidence/UT-J-11-fail.png` (same crash class, `/?asof=2026-08-11`), `UT-J-08-result.png` (working `/market` page)`

### UT-J-11 — Incident-bounded clean regeneration of derived state (serving verification only — J-11 itself is CLOSED/PASSING per owner ruling; this run re-verifies the two-URL basis-disclosure check its own golden script uses)

**Verdict:** FAIL
**Failure:** `/?asof=2026-08-12` (latest) correctly shows "Basis: available" in the manifest strip. `/?asof=2026-08-11` — the actual J-10/J-11 incident date, which does carry a real stored manifest whose API payload correctly reports `basis.status: "rebuilt"` — crashes the page before any content renders (confirmed deterministic: retried via the error boundary's "Try again" button, crashed identically). The basis-disclosure UI cannot be visually verified for this date this iteration
**Evidence:** ``reports/qa/goal-market-compass-iter-38-evidence/UT-J-11-fail.png`, `UT-J-11-retry.png``

### UT-J-13 — "Leadership rotation" says which way, shows both directions, and stops repeating What-changed

**Verdict:** FAIL
**Failure:** On frontier: `compass-leadership-rotation-section` renders exactly as specified — "Sector rotation" gaining (Regional Banks (SPDR) 13→10 (-3)·improving, Bitcoin Miners (Valkyrie), Real Estate, Banks (SPDR), Technology) and losing (Home Construction (iShares) 21→25 (+4)·deteriorating, Materials) sides, "7 of 31 shown · 24 below threshold · 0 beyond the display cap."; "Theme rotation" similarly with "2 of 11 shown · 9 below threshold · 0 beyond the display cap."; no stock-kind row present. **Step 7 fails**: stepping to `?asof=1996-01-02` (the earliest stored session, which also has an empty candidate list / `candidates_empty_reason`) crashes the whole page via the same `selection.why_not_totals` bug described in the Critical Finding — the required no-prior-run rotation state is never reached
**Evidence:** ``reports/qa/goal-market-compass-iter-38-evidence/UT-J-13-result.png` (frontier, passing part), `UT-J-13-fail.png` (step-7 crash)`

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-09-01


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-09 | J-09 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
